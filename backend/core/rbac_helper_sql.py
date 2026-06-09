from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - RBAC Helper SQL
============================
Funciones helper para verificación de roles dinámicamente desde EDARSAHUB SQL.

MÁXIMAS CUMPLIDAS:
- SQL-First: Lee roles y jerarquías desde Usuario_Roles
- Sin Hardcodeo: Los roles con acceso total se determinan por NivelJerarquia
- Cache: TTL de 5 minutos para evitar consultas repetidas
"""

import os
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timezone
import pymssql
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACIÓN (P2-01: Centralizado)
# =============================================================================

_cfg = get_edarsahub_sql_config()
_EDARSAHUB_CONFIG = {
    'host': _cfg.host,
    'port': _cfg.port,
    'database': _cfg.database,
    'username': _cfg.user,
    'password': _cfg.password,
}

# Umbral de jerarquía para "acceso total a unidades"
# Roles con NivelJerarquia >= este valor tienen acceso a TODAS las unidades
NIVEL_ACCESO_TOTAL = 80  # SUPERADMIN(100), DIRECCION(80)

# Cache
_roles_cache: Dict = {}
_cache_timestamp: Optional[datetime] = None
_CACHE_TTL_SECONDS = 300  # 5 minutos


def _get_connection():
    """Obtiene conexión a EDARSAHUB SQL."""
    return get_sql_connection()


def _is_cache_valid() -> bool:
    """Verifica si el cache está vigente."""
    global _cache_timestamp
    if not _cache_timestamp:
        return False
    elapsed = (datetime.now(timezone.utc) - _cache_timestamp).total_seconds()
    return elapsed < _CACHE_TTL_SECONDS


def _load_roles_from_sql() -> Dict[str, Dict]:
    """
    Carga todos los roles activos desde SQL.
    
    Returns:
        Dict con CodigoRol como key y datos del rol como value
    """
    global _roles_cache, _cache_timestamp
    
    if _is_cache_valid() and _roles_cache:
        return _roles_cache
    
    try:
        conn = _get_connection()
        cursor = conn.cursor(as_dict=True)
        
        cursor.execute('''
            SELECT 
                RolID, CodigoRol, NombreRol, NivelJerarquia, EsRolSistema
            FROM Usuario_Roles
            WHERE Activo = 1
            ORDER BY NivelJerarquia DESC
        ''')
        
        roles = {}
        for row in cursor.fetchall():
            codigo = row['CodigoRol']
            roles[codigo] = {
                'id': row['RolID'],
                'codigo': codigo,
                'nombre': row['NombreRol'],
                'nivel': row['NivelJerarquia'],
                'es_sistema': row['EsRolSistema'],
            }
            # También indexar por nombre para compatibilidad legacy
            nombre_upper = row['NombreRol'].upper() if row['NombreRol'] else ''
            roles[nombre_upper] = roles[codigo]
        
        conn.close()
        
        _roles_cache = roles
        _cache_timestamp = datetime.now(timezone.utc)
        logger.debug(f"[RBAC-SQL] Cargados {len(roles)//2} roles desde EDARSAHUB")
        
        return roles
        
    except Exception as e:
        logger.error(f"[RBAC-SQL] Error cargando roles: {e}")
        # Retornar cache viejo si existe, o dict vacío
        return _roles_cache if _roles_cache else {}


def get_roles_with_full_access() -> Set[str]:
    """
    Obtiene los códigos de roles que tienen acceso total a todas las unidades.
    
    Criterio: NivelJerarquia >= NIVEL_ACCESO_TOTAL (80)
    
    Returns:
        Set con códigos de roles (ej: {'SUPERADMIN', 'DIRECCION'})
    """
    roles = _load_roles_from_sql()
    full_access = set()
    
    for codigo, data in roles.items():
        if isinstance(data, dict) and data.get('nivel', 0) >= NIVEL_ACCESO_TOTAL:
            # Solo agregar códigos, no nombres duplicados
            if codigo == data.get('codigo'):
                full_access.add(codigo)
    
    return full_access


def get_role_names_with_full_access() -> Set[str]:
    """
    Obtiene los NOMBRES de roles que tienen acceso total.
    Útil para compatibilidad con el campo 'role' legacy de usuarios.
    
    Returns:
        Set con nombres de roles (ej: {'SuperAdministrador', 'Dirección'})
    """
    roles = _load_roles_from_sql()
    full_access = set()
    
    seen_ids = set()
    for codigo, data in roles.items():
        if isinstance(data, dict):
            rol_id = data.get('id')
            if rol_id and rol_id not in seen_ids:
                seen_ids.add(rol_id)
                if data.get('nivel', 0) >= NIVEL_ACCESO_TOTAL:
                    full_access.add(data['nombre'])
    
    return full_access


def has_full_access(user: Dict) -> bool:
    """
    Verifica si un usuario tiene acceso total a todas las unidades.
    
    Chequea múltiples campos del usuario para compatibilidad:
    - role (nombre legacy)
    - _sql_rol_codigo (código SQL)
    - sec_roles (array de códigos)
    
    Args:
        user: Dict con datos del usuario
        
    Returns:
        True si el usuario tiene un rol con acceso total (NivelJerarquia >= 80)
    """
    # Cargar roles dinámicamente desde SQL (cacheado)
    roles_full_access_codes = get_roles_with_full_access()
    roles_full_access_names = get_role_names_with_full_access()
    
    # 1. Verificar por nombre de rol (campo legacy 'role')
    # NOTA: el JWT guarda el CÓDIGO de rol (p.ej. 'SUPERADMIN') en el claim 'role',
    # por eso se compara contra NOMBRES y CÓDIGOS de acceso total.
    user_role = user.get('role', '') or user.get('rol', '')
    if user_role in roles_full_access_names or user_role in roles_full_access_codes:
        return True
    
    # 2. Verificar por código SQL (_sql_rol_codigo)
    sql_rol_codigo = user.get('_sql_rol_codigo', '')
    if sql_rol_codigo in roles_full_access_codes:
        return True
    
    # 3. Verificar por array de roles (sec_roles)
    sec_roles = user.get('sec_roles', [])
    for rol in sec_roles:
        if rol in roles_full_access_codes or rol in roles_full_access_names:
            return True
    
    return False


def get_role_level(user: Dict) -> int:
    """
    Obtiene el nivel jerárquico del rol del usuario.
    
    Args:
        user: Dict con datos del usuario
        
    Returns:
        Nivel jerárquico (0-100), 0 si no se encuentra
    """
    roles = _load_roles_from_sql()
    
    # Intentar por código SQL
    sql_rol = user.get('_sql_rol_codigo', '')
    if sql_rol and sql_rol in roles:
        return roles[sql_rol].get('nivel', 0)
    
    # Intentar por nombre legacy
    user_role = user.get('role', '').upper()
    if user_role and user_role in roles:
        return roles[user_role].get('nivel', 0)
    
    return 0


def invalidate_cache():
    """Fuerza la recarga del cache de roles."""
    global _roles_cache, _cache_timestamp
    _roles_cache = {}
    _cache_timestamp = None
    logger.info("[RBAC-SQL] Cache de roles invalidado")


# =============================================================================
# HELPERS DE AUTORIZACIÓN CANÓNICOS (consolidación de porteros)
# =============================================================================
# Regla: la autorización backend se decide por el CÓDIGO canónico de rol,
# resuelto dinámicamente desde SQL (Usuario_Roles, 23 roles). El NombreRol legacy
# y la clave 'rol' quedan solo como compatibilidad de lectura. Sin hardcodear
# niveles jerárquicos (esos viven en SQL). Mapeos explícitos de conjuntos para
# preservar exactamente la semántica legacy de los gates existentes.

# Fallback mínimo SOLO para los 5 roles de sistema, por resiliencia si SQL no
# responde en el instante del check. SQL sigue siendo la fuente primaria.
_CODE_FALLBACK = {
    "SUPERADMIN": "SUPERADMIN", "SUPERADMINISTRADOR": "SUPERADMIN",
    "ADMIN": "ADMIN", "ADMINISTRADOR": "ADMIN",
    "SUPERVISOR": "SUPERVISOR",
    "USUARIO": "USUARIO", "USER": "USUARIO",
    "VISOR": "VISOR", "VIEWER": "VISOR",
}


def get_role_code(user: Optional[Dict]) -> str:
    """Resuelve el CÓDIGO canónico de rol (ej. 'SUPERADMIN') desde múltiples
    campos de compatibilidad (role_code, _sql_rol_codigo, CodigoRol, role,
    NombreRol, rol), usando el catálogo SQL (23 roles) + fallback de sistema."""
    if not user:
        return ""
    roles = _load_roles_from_sql()
    for key in ("role_code", "_sql_rol_codigo", "CodigoRol", "codigo_rol",
                "role", "NombreRol", "nombre_rol", "rol"):
        v = user.get(key)
        if not v:
            continue
        v = str(v).strip()
        if not v:
            continue
        if v in roles and isinstance(roles[v], dict):
            return roles[v]["codigo"]
        vu = v.upper()
        if vu in roles and isinstance(roles[vu], dict):
            return roles[vu]["codigo"]
        if vu in _CODE_FALLBACK:
            return _CODE_FALLBACK[vu]
    return ""


def es_superadmin(user: Optional[Dict]) -> bool:
    """True si el rol canónico es SUPERADMIN."""
    return get_role_code(user) == "SUPERADMIN"


def es_admin(user: Optional[Dict]) -> bool:
    """Administrador o SuperAdministrador. Equivale a los gates legacy
    ['SuperAdministrador','Administrador'] y '== Administrador' (este último
    ahora también admite al SUPERADMIN, corrigiendo la negación falsa previa)."""
    return get_role_code(user) in ("SUPERADMIN", "ADMIN")


def es_supervisor_o_superior(user: Optional[Dict]) -> bool:
    """Supervisor, Administrador o SuperAdministrador. Equivale a los gates
    legacy ['Administrador','Supervisor'] (ahora también admite al SUPERADMIN)."""
    return get_role_code(user) in ("SUPERADMIN", "ADMIN", "SUPERVISOR")


# =============================================================================
# Conjuntos canónicos de roles por TIER FUNCIONAL (CodigoRol)
# -----------------------------------------------------------------------------
# Reemplazan las listas legacy por NombreRol (['Gerente','Comercial','Ventas',
# 'Usuario'...]) en el módulo costos_margenes. Derivados del catálogo
# dbo.Usuario_Roles. Mapeo legacy -> canónico:
#   'Gerente'/'Supervisor'      -> ROLES_APROBADORES
#   'Comercial'/'Ventas'        -> ROLES_COMERCIAL_OPERATIVO
#   'Usuario'                   -> ROLES_LECTORES
# =============================================================================
ROLES_APROBADORES = frozenset({
    "GERENTE", "GERENTE_OPS", "GERENTE_UNIDAD", "DIRECCION", "SUPERVISOR",
})
ROLES_COMERCIAL_OPERATIVO = frozenset({
    "VENTAS", "ANALISTA_COMERCIAL", "ADMIN_COMERCIAL", "CONFIGURADOR_COMERCIAL",
})
ROLES_LECTORES = frozenset({
    "USUARIO", "VISOR", "VISOR_COMERCIAL", "OPERADOR",
})


def es_aprobador(user: Optional[Dict]) -> bool:
    """Puede aprobar (Admin/SuperAdmin o gerencias/supervisión canónicas)."""
    return es_admin(user) or get_role_code(user) in ROLES_APROBADORES


def puede_solicitar_comercial(user: Optional[Dict]) -> bool:
    """Puede solicitar cambios comerciales (aprobadores + comercial operativo)."""
    return es_aprobador(user) or get_role_code(user) in ROLES_COMERCIAL_OPERATIVO


def tiene_acceso_lectura_comercial(user: Optional[Dict]) -> bool:
    """Acceso de lectura a costos/márgenes: cualquier rol canónico del staff
    (aprobadores + comercial operativo + lectores). Reemplaza la lista legacy
    ['Supervisor','Comercial','Gerente','Usuario']."""
    return puede_solicitar_comercial(user) or get_role_code(user) in ROLES_LECTORES
