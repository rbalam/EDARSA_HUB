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
    return pymssql.connect(
        server=_EDARSAHUB_CONFIG['host'],
        port=_EDARSAHUB_CONFIG['port'],
        database=_EDARSAHUB_CONFIG['database'],
        user=_EDARSAHUB_CONFIG['username'],
        password=_EDARSAHUB_CONFIG['password'],
        timeout=30,
        login_timeout=15
    )


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
        True si el usuario tiene un rol con acceso total
    """
    # Cargar roles dinámicamente
    roles_full_access_codes = get_roles_with_full_access()
    roles_full_access_names = get_role_names_with_full_access()
    
    # 1. Verificar por nombre de rol (campo legacy 'role')
    user_role = user.get('role', '')
    if user_role in roles_full_access_names:
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
