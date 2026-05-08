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

Autor: Arquitectura de Seguridad Senior
Fecha: 2026-04-22
Versión: 1.0
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Conexión lazy a MongoDB
_db = None


def _get_db():
    """Obtiene conexión a MongoDB de forma lazy."""
    global _db
    if _db is None:
        import os
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'edarsa_hub')
        client = AsyncIOMotorClient(mongo_url)
        _db = client[db_name]
    return _db


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


async def resolve_user_access_context(user: Dict[str, Any]) -> UserAccessContext:
    """
    FUNCIÓN CENTRAL: Resuelve el contexto de acceso efectivo de un usuario.
    
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
    db = _get_db()
    
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
        await _resolver_acceso_global(context)
        logger.info(f"[AccessContext] {context.email}: Acceso GLOBAL (SuperAdmin)")
        return context
    
    if role_legacy == 'Administrador':
        context.tiene_acceso_global = True
        context.fuente_acceso = "ADMIN"
        await _resolver_acceso_global(context)
        logger.info(f"[AccessContext] {context.email}: Acceso GLOBAL (Admin)")
        return context
    
    # =========================================================================
    # PASO 2: Resolver por modelo RBAC (empresas_permitidas)
    # =========================================================================
    empresas_rbac = user.get('empresas_permitidas') or []
    empresa_default = user.get('empresa_default_id')
    
    if empresas_rbac:
        context.empresas_ids = empresas_rbac
        context.empresa_default_id = empresa_default
        context.fuente_acceso = "RBAC"
        
        # Traducir empresas a servidores
        await _resolver_servers_desde_empresas(context, empresas_rbac)
    
    # =========================================================================
    # PASO 3: Complementar con modelo legacy (allowed_servers)
    # =========================================================================
    allowed_servers = user.get('allowed_servers') or []
    allowed_sucursales = user.get('allowed_sucursales') or {}
    allowed_warehouses = user.get('allowed_warehouses') or {}
    
    if allowed_servers:
        # Agregar servidores legacy que no estén ya incluidos
        servers_existentes = set(context.servers_ids)
        for srv in allowed_servers:
            if srv not in servers_existentes:
                context.servers_ids.append(srv)
        
        # Actualizar fuente si solo hay legacy
        if not empresas_rbac:
            context.fuente_acceso = "LEGACY"
        elif allowed_servers:
            context.fuente_acceso = "MIXTO"
    
    # =========================================================================
    # PASO 4: Resolver sucursales permitidas
    # =========================================================================
    for server_id, sucursales in allowed_sucursales.items():
        if sucursales:
            context.sucursales_por_server[server_id] = sucursales
    
    # =========================================================================
    # PASO 5: Resolver almacenes permitidos
    # =========================================================================
    for server_id, almacenes in allowed_warehouses.items():
        if almacenes:
            context.almacenes_por_server[server_id] = almacenes
    
    # =========================================================================
    # PASO 6: Resolver permisos funcionales desde sec_roles
    # =========================================================================
    sec_roles = user.get('sec_roles') or []
    sec_rol_unico = user.get('sec_rol')
    sec_permisos_directos = user.get('sec_permisos') or []
    
    context.sec_roles = sec_roles
    context.sec_perfil = user.get('sec_perfil')
    
    # Agregar permisos directos
    permisos_set: Set[str] = set(sec_permisos_directos)
    
    # Resolver permisos de cada rol
    for rol_codigo in sec_roles:
        rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
        if rol_doc:
            for perm in rol_doc.get('permisos', []):
                permisos_set.add(perm)
    
    # Fallback: rol único legacy
    if sec_rol_unico and sec_rol_unico not in sec_roles:
        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol_unico, "activo": True})
        if rol_doc:
            for perm in rol_doc.get('permisos', []):
                permisos_set.add(perm)
    
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


async def _resolver_acceso_global(context: UserAccessContext) -> None:
    """Resuelve acceso global: todas las empresas y servidores."""
    db = _get_db()
    
    # Todas las empresas activas
    empresas = await db.empresas.find({'activa': True}, {'id': 1, '_id': 0}).to_list(100)
    context.empresas_ids = [e['id'] for e in empresas]
    
    # Todos los servidores activos
    servers = await db.servers.find({'active': True}, {'id': 1, '_id': 0}).to_list(100)
    context.servers_ids = [s['id'] for s in servers]
    
    # Todos los permisos
    permisos = await db.sec_permisos_catalogo.find({}, {'codigo': 1, '_id': 0}).to_list(200)
    context.permisos = [p['codigo'] for p in permisos]


async def _resolver_servers_desde_empresas(context: UserAccessContext, empresas_ids: List[str]) -> None:
    """Traduce empresas a servidores vía sucursales_catalogo y mapeos."""
    db = _get_db()
    
    # Obtener sucursales de las empresas
    sucursales = await db.sucursales_catalogo.find(
        {'empresa_id': {'$in': empresas_ids}, 'activa': True},
        {'id': 1, '_id': 0}
    ).to_list(100)
    
    sucursal_ids = [s['id'] for s in sucursales]
    
    if not sucursal_ids:
        return
    
    # Obtener mapeos a servidores
    mapeos = await db.sucursal_servidor_map.find(
        {'sucursal_id': {'$in': sucursal_ids}, 'activo': True},
        {'server_id': 1, '_id': 0}
    ).to_list(100)
    
    context.servers_ids = list(set(m['server_id'] for m in mapeos if m.get('server_id')))


# =============================================================================
# FUNCIONES DE VALIDACIÓN
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
    return server_id in context.servers_ids


def has_empresa_access(context: UserAccessContext, empresa_id: str) -> bool:
    """
    Verifica si el contexto tiene acceso a una empresa.
    """
    if context.tiene_acceso_global:
        return True
    return empresa_id in context.empresas_ids


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
    almacenes_permitidos = context.almacenes_por_server.get(server_id)
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
    return [s for s in servers if s.get('id') in context.servers_ids]


def filter_empresas(context: UserAccessContext, empresas: List[Dict]) -> List[Dict]:
    """
    Filtra una lista de empresas según el contexto de acceso.
    """
    if context.tiene_acceso_global:
        return empresas
    return [e for e in empresas if e.get('id') in context.empresas_ids]


# =============================================================================
# FUNCIONES DE FILTRADO SQL PARA ALMACENES
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
    
    return context.almacenes_por_server.get(server_id, [])


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
    
    almacenes = context.almacenes_por_server.get(server_id, [])
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
    
    almacenes = context.almacenes_por_server.get(server_id, [])
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
    
    almacenes_permitidos = context.almacenes_por_server.get(server_id, [])
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
    
    almacenes_permitidos = context.almacenes_por_server.get(server_id, [])
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
