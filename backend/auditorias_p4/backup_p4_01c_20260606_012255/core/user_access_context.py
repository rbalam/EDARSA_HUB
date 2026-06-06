from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - User Access Context Resolver
==========================================
ÚNICA FUENTE DE VERDAD PARA ACCESO EFECTIVO

PROPÓSITO:
Centraliza la resolución del contexto de acceso de cualquier usuario.
NUNCA confiar en parámetros del frontend para determinar alcance.
Este módulo es el ÚNICO responsable de responder:
- ¿Qué empresas puede ver el usuario?
- ¿Qué servidores puede consultar?
- ¿Qué almacenes tiene permitidos?
- ¿Qué permisos funcionales tiene?

REGLAS DE RESOLUCIÓN (en orden de prioridad):
1. SuperAdministrador → acceso global a todo
2. Administrador → acceso global a todo (legacy)
3. RBAC empresas_permitidas → empresas asignadas
4. Fallback legacy allowed_servers → traducir a acceso
5. Sin nada → acceso vacío

ARQUITECTURA:
- Combina modelo RBAC (empresas_permitidas, sec_roles) con legacy (allowed_servers)
- Nunca elimina funcionalidad existente
- Siempre prioriza RBAC sobre legacy cuando ambos existen

MIGRACIÓN FASE 3-D:
====================
Este módulo ha sido migrado de MongoDB a EDARSAHUB SQL.
Tablas SQL utilizadas:
- Usuario_Catalogo
- Usuario_Roles
- Usuario_RolesAsignacion
- Usuario_EmpresasAsignacion
- Usuario_SucursalesAsignacion
- Usuario_AlmacenesAsignacion
- Usuario_ServidoresAsignacion
- Sistema_Empresas
- Sistema_EmpresasMongoMap
- Sistema_Sucursales
- Sistema_SucursalServidorMapeo
- Servidores_Conexiones

MongoDB ya no es fuente de datos para resolución de acceso.
Fecha migración: 2026-05-14
Autor: Agente E1
Régimen: Autorización Controlada

Autor original: Arquitectura de Seguridad Senior
Fecha original: 2026-04-22
Versión: 2.0 (SQL)
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import pymssql

logger = logging.getLogger(__name__)


# =========================================================================
# CONEXIÓN SQL
# =========================================================================

def _get_sql_connection():
    """Obtiene conexión a EDARSAHUB SQL."""
    return pymssql.connect(
        server='<REDACTED_EDARSAHUB_SQL_HOST>',
        port=1433,
        user='<REDACTED_EDARSAHUB_SQL_USER>',
        password='<REDACTED_EDARSAHUB_SQL_PASSWORD>',
        database='EDARSAHUB'
    )


@dataclass
class UserAccessContext:
    """
    Estructura que representa el contexto de acceso efectivo de un usuario.
    Esta es la ÚNICA fuente de verdad para autorización.
    """
    # Identificación
    user_id: str
    email: str
    nombre: str
    
    # Nivel de acceso
    tiene_acceso_global: bool = False
    fuente_acceso: str = "SIN_ACCESO"  # SUPERADMIN, ADMIN, RBAC, LEGACY, MIXTO
    
    # Empresas (modelo RBAC)
    empresas_ids: List[str] = field(default_factory=list)
    empresa_default_id: Optional[str] = None
    
    # Servidores (efectivos, calculados)
    servers_ids: List[str] = field(default_factory=list)
    
    # Almacenes por servidor (efectivos)
    almacenes_por_server: Dict[str, List[str]] = field(default_factory=dict)
    
    # Sucursales por servidor (efectivos)
    sucursales_por_server: Dict[str, List[str]] = field(default_factory=dict)
    
    # Permisos funcionales (combinados de sec_roles y sec_permisos)
    permisos: List[str] = field(default_factory=list)
    
    # Roles asignados
    sec_roles: List[str] = field(default_factory=list)
    sec_perfil: Optional[str] = None
    
    # Permisos de catálogos
    permisos_catalogos: List[str] = field(default_factory=list)
    
    # Capacidades especiales
    puede_autorizar: bool = False
    puede_solicitar: bool = False
    puede_liberar: bool = False
    
    # Metadatos
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "nombre": self.nombre,
            "tiene_acceso_global": self.tiene_acceso_global,
            "fuente_acceso": self.fuente_acceso,
            "empresas_ids": self.empresas_ids,
            "empresa_default_id": self.empresa_default_id,
            "servers_ids": self.servers_ids,
            "almacenes_por_server": self.almacenes_por_server,
            "sucursales_por_server": self.sucursales_por_server,
            "permisos": self.permisos,
            "sec_roles": self.sec_roles,
            "sec_perfil": self.sec_perfil,
            "permisos_catalogos": self.permisos_catalogos,
            "puede_autorizar": self.puede_autorizar,
            "puede_solicitar": self.puede_solicitar,
            "puede_liberar": self.puede_liberar,
            "timestamp": self.timestamp
        }


# =========================================================================
# HELPERS SQL
# =========================================================================

def _get_user_id_sql(cursor, public_uuid: str) -> Optional[int]:
    """
    Obtiene UsuarioID SQL desde PublicUUID.
    """
    cursor.execute('''
        SELECT UsuarioID
        FROM Usuario_Catalogo
        WHERE LOWER(CAST(PublicUUID AS VARCHAR(36))) = LOWER(%s)
          AND Activo = 1
    ''', (public_uuid,))
    row = cursor.fetchone()
    return row[0] if row else None


def _get_user_role_sql(cursor, usuario_id: int) -> Optional[str]:
    """
    Obtiene código de rol del usuario desde Usuario_RolesAsignacion.
    """
    cursor.execute('''
        SELECT r.CodigoRol
        FROM Usuario_RolesAsignacion ra
        JOIN Usuario_Roles r ON ra.RolID = r.RolID
        WHERE ra.UsuarioID = %s AND ra.Activo = 1
    ''', (usuario_id,))
    row = cursor.fetchone()
    return row[0] if row else None


def _get_all_empresas_sql(cursor) -> List[str]:
    """
    Obtiene todas las empresas activas (UUIDs MongoDB) para acceso global.
    """
    cursor.execute('''
        SELECT m.EmpresaMongoUUID
        FROM Sistema_Empresas e
        JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
        WHERE e.Activo = 1
        ORDER BY e.EmpresaID
    ''')
    return [row[0] for row in cursor.fetchall()]


def _get_all_servers_sql(cursor) -> List[str]:
    """
    Obtiene todos los servidores activos para acceso global.
    """
    cursor.execute('''
        SELECT LOWER(CAST(id AS VARCHAR(36))) as id
        FROM Servidores_Conexiones
        WHERE visible_en_operaciones = 1
        ORDER BY nombre
    ''')
    return [row[0] for row in cursor.fetchall()]


def _get_user_empresas_sql(cursor, usuario_id: int) -> tuple:
    """
    Obtiene empresas asignadas al usuario (UUIDs MongoDB).
    
    Returns:
        tuple: (lista_empresas_uuids, empresa_default_uuid)
    """
    cursor.execute('''
        SELECT 
            m.EmpresaMongoUUID,
            ea.EsPrincipal
        FROM Usuario_EmpresasAsignacion ea
        JOIN Sistema_EmpresasMongoMap m ON ea.EmpresaID = m.EmpresaID_SQL
        WHERE ea.UsuarioID = %s AND ea.Activo = 1
        ORDER BY ea.EsPrincipal DESC, ea.EmpresaID
    ''', (usuario_id,))
    
    empresas = []
    empresa_default = None
    
    for row in cursor.fetchall():
        uuid = row[0]
        es_principal = row[1]
        if uuid:
            empresas.append(uuid)
            if es_principal and not empresa_default:
                empresa_default = uuid
    
    return empresas, empresa_default


def _get_user_servers_sql(cursor, usuario_id: int) -> List[str]:
    """
    Obtiene servidores asignados al usuario desde Usuario_ServidoresAsignacion.
    """
    cursor.execute('''
        SELECT LOWER(CAST(ServidorID AS VARCHAR(36))) as ServidorID
        FROM Usuario_ServidoresAsignacion
        WHERE UsuarioID = %s AND Activo = 1
    ''', (usuario_id,))
    return [row[0] for row in cursor.fetchall()]


def _get_servers_from_empresas_sql(cursor, empresas_uuids: List[str]) -> List[str]:
    """
    Traduce empresas (UUIDs MongoDB) a servidores vía mapeos SQL.
    
    Usa: Sistema_EmpresasMongoMap → Sistema_Sucursales → Sistema_SucursalServidorMapeo
    """
    if not empresas_uuids:
        return []
    
    placeholders = ', '.join(['%s'] * len(empresas_uuids))
    
    cursor.execute(f'''
        SELECT DISTINCT LOWER(CAST(m.ServidorID AS VARCHAR(36))) as ServidorID
        FROM Sistema_SucursalServidorMapeo m
        JOIN Sistema_Sucursales s ON m.SucursalID = s.SucursalID
        JOIN Sistema_EmpresasMongoMap em ON s.EmpresaID = em.EmpresaID_SQL
        WHERE em.EmpresaMongoUUID IN ({placeholders})
          AND m.Activo = 1
          AND s.Activo = 1
    ''', tuple(empresas_uuids))
    
    return [row[0] for row in cursor.fetchall()]


def _get_user_sucursales_sql(cursor, usuario_id: int) -> Dict[str, List[str]]:
    """
    Obtiene sucursales asignadas al usuario agrupadas por servidor.
    """
    cursor.execute('''
        SELECT 
            LOWER(CAST(ServidorID AS VARCHAR(36))) as ServidorID,
            SucursalCodigo
        FROM Usuario_SucursalesAsignacion
        WHERE UsuarioID = %s AND Activo = 1
    ''', (usuario_id,))
    
    sucursales_por_server: Dict[str, List[str]] = {}
    for row in cursor.fetchall():
        server_id = row[0]
        sucursal_codigo = row[1]
        if server_id not in sucursales_por_server:
            sucursales_por_server[server_id] = []
        sucursales_por_server[server_id].append(sucursal_codigo)
    
    return sucursales_por_server


def _get_user_almacenes_sql(cursor, usuario_id: int) -> Dict[str, List[str]]:
    """
    Obtiene almacenes asignados al usuario agrupados por servidor.
    """
    cursor.execute('''
        SELECT 
            LOWER(CAST(ServidorID AS VARCHAR(36))) as ServidorID,
            AlmacenCodigo
        FROM Usuario_AlmacenesAsignacion
        WHERE UsuarioID = %s AND Activo = 1
    ''', (usuario_id,))
    
    almacenes_por_server: Dict[str, List[str]] = {}
    for row in cursor.fetchall():
        server_id = row[0]
        almacen_codigo = row[1]
        if server_id not in almacenes_por_server:
            almacenes_por_server[server_id] = []
        almacenes_por_server[server_id].append(almacen_codigo)
    
    return almacenes_por_server


# =========================================================================
# FUNCIÓN CENTRAL
# =========================================================================

async def resolve_user_access_context(user: Dict[str, Any]) -> UserAccessContext:
    """
    FUNCIÓN CENTRAL: Resuelve el contexto de acceso efectivo de un usuario.
    
    MIGRACIÓN FASE 3-D: Ahora lee desde EDARSAHUB SQL en lugar de MongoDB.
    
    Esta función es la ÚNICA fuente de verdad para determinar:
    - A qué empresas tiene acceso
    - A qué servidores puede consultar
    - Qué almacenes puede ver
    - Qué permisos funcionales tiene
    
    Args:
        user: Diccionario del usuario (como viene de get_current_user)
        
    Returns:
        UserAccessContext con todo el acceso efectivo calculado
    
    IMPORTANTE: El backend SIEMPRE debe usar esta función para validar acceso.
    NUNCA confiar en parámetros enviados por el frontend.
    """
    context = UserAccessContext(
        user_id=user.get('id', ''),
        email=user.get('email', ''),
        nombre=user.get('name', user.get('nombre', ''))
    )
    
    role_legacy = user.get('role', '')
    
    # =========================================================================
    # PASO 1: Verificar acceso global (SuperAdministrador / Administrador)
    # =========================================================================
    if role_legacy == 'SuperAdministrador':
        context.tiene_acceso_global = True
        context.fuente_acceso = "SUPERADMIN"
        _resolver_acceso_global_sql(context)
        logger.info(f"[AccessContext] {context.email}: Acceso GLOBAL (SuperAdmin)")
        return context
    
    if role_legacy == 'Administrador':
        context.tiene_acceso_global = True
        context.fuente_acceso = "ADMIN"
        _resolver_acceso_global_sql(context)
        logger.info(f"[AccessContext] {context.email}: Acceso GLOBAL (Admin)")
        return context
    
    # =========================================================================
    # PASO 2: Resolver por modelo RBAC desde SQL
    # =========================================================================
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        
        # Obtener UsuarioID SQL
        usuario_id = _get_user_id_sql(cursor, context.user_id)
        
        if usuario_id:
            # Obtener empresas asignadas
            empresas_rbac, empresa_default = _get_user_empresas_sql(cursor, usuario_id)
            
            if empresas_rbac:
                context.empresas_ids = empresas_rbac
                context.empresa_default_id = empresa_default
                context.fuente_acceso = "RBAC"
                
                # Traducir empresas a servidores via mapeos SQL
                servers_from_empresas = _get_servers_from_empresas_sql(cursor, empresas_rbac)
                context.servers_ids = servers_from_empresas
            
            # =========================================================================
            # PASO 3: Complementar con servidores asignados directamente
            # =========================================================================
            servers_directos = _get_user_servers_sql(cursor, usuario_id)
            
            if servers_directos:
                # Agregar servidores directos que no estén ya incluidos
                servers_existentes = set(context.servers_ids)
                for srv in servers_directos:
                    if srv not in servers_existentes:
                        context.servers_ids.append(srv)
                
                # Actualizar fuente si hay servidores directos además de RBAC
                if not empresas_rbac:
                    context.fuente_acceso = "LEGACY"
                elif servers_directos:
                    context.fuente_acceso = "MIXTO"
            
            # =========================================================================
            # PASO 4: Resolver sucursales permitidas desde SQL
            # =========================================================================
            sucursales = _get_user_sucursales_sql(cursor, usuario_id)
            for server_id, suc_list in sucursales.items():
                if suc_list:
                    context.sucursales_por_server[server_id] = suc_list
            
            # =========================================================================
            # PASO 5: Resolver almacenes permitidos desde SQL
            # =========================================================================
            almacenes = _get_user_almacenes_sql(cursor, usuario_id)
            for server_id, alm_list in almacenes.items():
                if alm_list:
                    context.almacenes_por_server[server_id] = alm_list
        
    finally:
        conn.close()
    
    # =========================================================================
    # PASO 6: Resolver permisos funcionales desde user dict
    # (Los sec_roles y sec_permisos vienen del usuario ya resuelto)
    # =========================================================================
    sec_roles = user.get('sec_roles') or []
    sec_permisos_directos = user.get('sec_permisos') or []
    
    context.sec_roles = sec_roles
    context.sec_perfil = user.get('sec_perfil')
    
    # Agregar permisos directos
    permisos_set: Set[str] = set(sec_permisos_directos)
    
    # Los permisos de roles se resuelven desde el user dict que ya viene poblado
    # Si se necesita resolver desde SQL, se agregaría aquí
    context.permisos = list(permisos_set)
    
    # =========================================================================
    # PASO 7: Otros atributos del usuario
    # =========================================================================
    context.permisos_catalogos = user.get('permisos_catalogos') or []
    context.puede_autorizar = user.get('puede_autorizar', False)
    context.puede_solicitar = user.get('puede_solicitar', False)
    context.puede_liberar = user.get('puede_liberar', False)
    
    # =========================================================================
    # LOG FINAL
    # =========================================================================
    logger.info(
        f"[AccessContext] {context.email}: "
        f"Fuente={context.fuente_acceso}, "
        f"Empresas={len(context.empresas_ids)}, "
        f"Servers={len(context.servers_ids)}, "
        f"Permisos={len(context.permisos)}"
    )
    
    return context


def _resolver_acceso_global_sql(context: UserAccessContext) -> None:
    """
    Resuelve acceso global desde SQL: todas las empresas y servidores.
    
    MIGRACIÓN FASE 3-D: Ahora lee desde EDARSAHUB SQL.
    """
    conn = _get_sql_connection()
    try:
        cursor = conn.cursor()
        
        # Todas las empresas activas (UUIDs MongoDB)
        context.empresas_ids = _get_all_empresas_sql(cursor)
        
        # Todos los servidores activos
        context.servers_ids = _get_all_servers_sql(cursor)
        
        # Para acceso global, no hay restricciones de almacenes/sucursales
        # Los permisos completos vendrían del catálogo si se implementa en SQL
        context.permisos = []
        
    finally:
        conn.close()


# =============================================================================
# FUNCIONES DE VALIDACIÓN (Sin cambios - usan el contexto ya resuelto)
# =============================================================================

def has_server_access(context: UserAccessContext, server_id: str) -> bool:
    """
    Verifica si el contexto tiene acceso a un servidor.
    
    Args:
        context: Contexto de acceso resuelto
        server_id: ID del servidor a verificar
        
    Returns:
        True si tiene acceso, False si no
    """
    if context.tiene_acceso_global:
        return True
    return server_id.lower() in [s.lower() for s in context.servers_ids]


def has_empresa_access(context: UserAccessContext, empresa_id: str) -> bool:
    """
    Verifica si el contexto tiene acceso a una empresa.
    """
    if context.tiene_acceso_global:
        return True
    return empresa_id.lower() in [e.lower() for e in context.empresas_ids]


def has_almacen_access(context: UserAccessContext, server_id: str, almacen_id: str) -> bool:
    """
    Verifica si el contexto tiene acceso a un almacén específico.
    """
    if context.tiene_acceso_global:
        return True
    
    # Primero verificar acceso al servidor
    if not has_server_access(context, server_id):
        return False
    
    # Si no hay restricción de almacenes para este servidor, permitir todos
    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower())
    if not almacenes_permitidos:
        return True
    
    return almacen_id in almacenes_permitidos


def has_permiso(context: UserAccessContext, permiso: str) -> bool:
    """
    Verifica si el contexto tiene un permiso funcional.
    """
    if context.tiene_acceso_global:
        return True
    return permiso in context.permisos


def filter_servers(context: UserAccessContext, servers: List[Dict]) -> List[Dict]:
    """
    Filtra una lista de servidores según el contexto de acceso.
    """
    if context.tiene_acceso_global:
        return servers
    servers_lower = [s.lower() for s in context.servers_ids]
    return [s for s in servers if s.get('id', '').lower() in servers_lower]


def filter_empresas(context: UserAccessContext, empresas: List[Dict]) -> List[Dict]:
    """
    Filtra una lista de empresas según el contexto de acceso.
    """
    if context.tiene_acceso_global:
        return empresas
    empresas_lower = [e.lower() for e in context.empresas_ids]
    return [e for e in empresas if e.get('id', '').lower() in empresas_lower]


# =============================================================================
# FUNCIONES DE FILTRADO SQL PARA ALMACENES (Sin cambios - usan contexto)
# =============================================================================

def get_almacenes_permitidos(context: UserAccessContext, server_id: str) -> List[str]:
    """
    Obtiene la lista de almacenes permitidos para un servidor.
    Si el usuario tiene acceso global o no hay restricción, devuelve lista vacía
    (indicando que puede ver todos).
    
    Args:
        context: Contexto de acceso resuelto
        server_id: ID del servidor
        
    Returns:
        Lista de IDs de almacenes permitidos, o lista vacía si puede ver todos
    """
    if context.tiene_acceso_global:
        return []  # Sin restricción
    
    return context.almacenes_por_server.get(server_id.lower(), [])


def get_almacenes_sql_filter(context: UserAccessContext, server_id: str, column_name: str) -> str:
    """
    Genera cláusula SQL WHERE para filtrar por almacenes permitidos.
    
    Args:
        context: Contexto de acceso resuelto
        server_id: ID del servidor
        column_name: Nombre de la columna SQL a filtrar (ej: 'A.Al_Cve_Almacen')
        
    Returns:
        Cláusula SQL como " AND column IN ('001','002')" o vacío si puede ver todos
    """
    if context.tiene_acceso_global:
        return ""  # Sin restricción
    
    almacenes = context.almacenes_por_server.get(server_id.lower(), [])
    if not almacenes:
        return ""  # Sin restricción para este servidor
    
    # Escapar comillas simples en IDs
    safe_almacenes = [str(a).replace("'", "''") for a in almacenes]
    almacenes_str = "','".join(safe_almacenes)
    return f" AND {column_name} IN ('{almacenes_str}')"


def get_almacenes_sql_filter_like(context: UserAccessContext, server_id: str, column_name: str) -> str:
    """
    Genera cláusula SQL WHERE para filtrar por nombres de almacén usando LIKE.
    Útil cuando la tabla usa descripción en lugar de código.
    
    Args:
        context: Contexto de acceso resuelto
        server_id: ID del servidor
        column_name: Nombre de la columna SQL (ej: 'A.Al_Descripcion')
        
    Returns:
        Cláusula SQL como " AND (col LIKE '%001%' OR col LIKE '%002%')" o vacío
    """
    if context.tiene_acceso_global:
        return ""
    
    almacenes = context.almacenes_por_server.get(server_id.lower(), [])
    if not almacenes:
        return ""
    
    # Construir condiciones LIKE
    conditions = []
    for alm in almacenes:
        safe_alm = str(alm).replace("'", "''")
        conditions.append(f"{column_name} LIKE '%{safe_alm}%'")
    
    return f" AND ({' OR '.join(conditions)})"


def validate_almacen_in_scope(context: UserAccessContext, server_id: str, almacen_id: str) -> bool:
    """
    Valida que un almacén específico esté dentro del alcance del usuario.
    
    Args:
        context: Contexto de acceso
        server_id: ID del servidor
        almacen_id: ID del almacén a validar
        
    Returns:
        True si tiene acceso, False si no
    """
    if context.tiene_acceso_global:
        return True
    
    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower(), [])
    if not almacenes_permitidos:
        return True  # Sin restricción para este servidor
    
    return almacen_id in almacenes_permitidos


def filter_results_by_almacen(
    context: UserAccessContext, 
    server_id: str, 
    results: List[Dict],
    almacen_field: str = 'almacen'
) -> List[Dict]:
    """
    Filtra resultados post-query por almacenes permitidos.
    Útil cuando la query SQL no puede filtrarse fácilmente.
    
    Args:
        context: Contexto de acceso
        server_id: ID del servidor
        results: Lista de diccionarios a filtrar
        almacen_field: Nombre del campo que contiene el almacén
        
    Returns:
        Lista filtrada
    """
    if context.tiene_acceso_global:
        return results
    
    almacenes_permitidos = context.almacenes_por_server.get(server_id.lower(), [])
    if not almacenes_permitidos:
        return results  # Sin restricción
    
    # Filtrar por coincidencia parcial (para nombres de almacén)
    filtered = []
    for r in results:
        almacen_value = str(r.get(almacen_field, '')).strip().upper()
        for permitido in almacenes_permitidos:
            if str(permitido).upper() in almacen_value or almacen_value in str(permitido).upper():
                filtered.append(r)
                break
    
    return filtered


# =============================================================================
# EXPORTACIONES
# =============================================================================

__all__ = [
    'UserAccessContext',
    'resolve_user_access_context',
    'has_server_access',
    'has_empresa_access',
    'has_almacen_access',
    'has_permiso',
    'filter_servers',
    'filter_empresas',
    # Nuevas funciones FASE 8 - Enforcement de Almacenes
    'get_almacenes_permitidos',
    'get_almacenes_sql_filter',
    'get_almacenes_sql_filter_like',
    'validate_almacen_in_scope',
    'filter_results_by_almacen',
]
