"""
EDARSA HUB - Server Registry Central
====================================

FASE 3B: Registry centralizado para resolución de servidores.

PRINCIPIOS:
1. EDARSAHUB SQL es la fuente primaria de configuración de servidores
2. MongoDB queda como fallback legacy temporal
3. Todo fallback debe quedar marcado con config_origin = "MONGODB_LEGACY"
4. Nunca exponer secretos (passwords, api_keys) al frontend
5. Normalizar system_type usando core.system_type_utils

CONSUMIDORES:
- /api/servers endpoint
- Módulo Comercial (repository.py)
- Módulo Compras
- Módulo Finanzas
- Módulo Operaciones/Inventarios
- RBAC / Alcance de usuarios

CREADO: FASE 3B - Diciembre 2025
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

# Configuración EDARSAHUB SQL
EDARSAHUB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
}

# Flag para habilitar/deshabilitar lectura desde SQL (para rollback rápido)
USE_SQL_FOR_SERVERS = os.environ.get('USE_SQL_FOR_SERVERS', 'true').lower() == 'true'

logger = logging.getLogger(__name__)


# ============================================================================
# NORMALIZACIÓN Y MASCAREO
# ============================================================================

def normalize_system_type(system_type: str) -> str:
    """
    Normaliza system_type usando la fuente central.
    Import diferido para evitar circular imports.
    """
    try:
        from core.system_type_utils import normalize_system_type as _normalize
        return _normalize(system_type)
    except ImportError:
        # Fallback básico si no está disponible
        if not system_type:
            return "UNKNOWN"
        st_upper = system_type.upper().strip()
        if st_upper in ['MPRO', 'MANAGMENTPRO', 'MANAGEMENTPRO', 'MANAGEMENT_PRO']:
            return "MANAGEMENTPRO"
        elif st_upper in ['SOFTRESTAURANT', 'SR', 'SOFT']:
            return "SOFTRESTAURANT"
        elif st_upper in ['API', 'API_LOCAL', 'API_MPRO']:
            return "API"
        return st_upper


def mask_sensitive_fields(server: Dict, include_configured_flags: bool = True) -> Dict:
    """
    Enmascara campos sensibles para respuestas al frontend.
    
    FASE 3C: Integrado con secret_manager para indicar estado de cifrado.
    
    NUNCA devolver:
    - password
    - password_encrypted
    - api_key
    - api_key_encrypted
    
    En su lugar, devolver:
    - password_configured: bool
    - api_key_configured: bool
    - secrets_encrypted: bool (nuevo en FASE 3C)
    """
    from core.secret_manager import is_encrypted_secret, get_secret_status
    
    masked = {k: v for k, v in server.items() 
              if k not in ['password', 'password_encrypted', 'api_key', 'api_key_encrypted']}
    
    if include_configured_flags:
        # Obtener valores de secretos
        pwd = server.get('password') or server.get('password_encrypted')
        api = server.get('api_key') or server.get('api_key_encrypted')
        
        masked['password_configured'] = bool(pwd)
        masked['api_key_configured'] = bool(api)
        
        # FASE 3C: Indicar si los secretos están cifrados
        pwd_encrypted = is_encrypted_secret(pwd) if pwd else False
        api_encrypted = is_encrypted_secret(api) if api else False
        
        # Solo true si todos los secretos configurados están cifrados
        if pwd or api:
            masked['secrets_encrypted'] = (
                (not pwd or pwd_encrypted) and 
                (not api or api_encrypted)
            )
        else:
            masked['secrets_encrypted'] = True  # No hay secretos que cifrar
    
    return masked


def _parse_json_field(value) -> Any:
    """Parsea un campo JSON desde SQL."""
    import json
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value) if value else None
    except (json.JSONDecodeError, TypeError):
        return None


# ============================================================================
# LECTURA DESDE EDARSAHUB SQL
# ============================================================================

def _sql_row_to_server_dict(row: Dict, source: str = "EDARSAHUB_SQL") -> Dict:
    """
    Convierte una fila de Servidores_Conexiones (SQL) al formato del sistema.
    Garantiza paridad con el esquema de MongoDB.
    """
    system_type_raw = row.get('system_type', '')
    
    return {
        'id': str(row.get('id', '')),
        'mongodb_id': str(row.get('mongodb_id', '')) if row.get('mongodb_id') else None,
        'name': row.get('nombre', ''),
        'system_type': system_type_raw,
        'system_type_normalized': normalize_system_type(system_type_raw),
        'tipo_conexion': row.get('tipo_conexion', 'DATA_SOURCE'),
        'host': row.get('host', ''),
        'port': row.get('port', 1433),
        'database': row.get('database_name', ''),
        'username': row.get('username', ''),
        'password': row.get('password_encrypted', ''),  # Se enmascara después
        'api_url': row.get('api_url', ''),
        'api_key': row.get('api_key_encrypted', ''),  # Se enmascara después
        'active': bool(row.get('activo', False)),
        'visible_en_operaciones': bool(row.get('visible_en_operaciones', True)),
        'visible_en_listado': bool(row.get('visible_en_listado', True)),
        'es_editable_ui': bool(row.get('es_editable_ui', True)),
        'es_eliminable_ui': bool(row.get('es_eliminable_ui', True)),
        'empresa_id': str(row.get('empresa_id', '')) if row.get('empresa_id') else None,
        'sucursales': _parse_json_field(row.get('sucursales')),
        'categorias': _parse_json_field(row.get('categorias')),
        'departamentos': _parse_json_field(row.get('departamentos')),
        'date_calculation_method': row.get('date_calculation_method'),
        'queries_configured': bool(row.get('queries_configured', False)),
        'query_ventas': _parse_json_field(row.get('query_ventas')),
        'query_inventario': _parse_json_field(row.get('query_inventario')),
        'query_movimientos': _parse_json_field(row.get('query_movimientos')),
        'created_at': row.get('created_at'),
        'updated_at': row.get('updated_at'),
        'config_origin': source,
        'warnings': []
    }


def _get_servers_from_sql(
    filter_active: bool = True,
    filter_visible_listado: bool = True,
    exclude_core: bool = True
) -> List[Dict]:
    """
    Obtiene servidores desde EDARSAHUB SQL.
    
    Args:
        filter_active: Solo servidores activos
        filter_visible_listado: Solo visibles en listado UI
        exclude_core: Excluir conexiones CORE del sistema
    
    Returns:
        Lista de servidores o lista vacía si hay error
    """
    try:
        from core.db import execute_sql_query
        
        conditions = []
        if filter_active:
            conditions.append("activo = 1")
        if filter_visible_listado:
            conditions.append("(visible_en_listado = 1 OR visible_en_listado IS NULL)")
        if exclude_core:
            conditions.append("(tipo_conexion != 'CORE' OR tipo_conexion IS NULL)")
        
        # Excluir conexiones API_LOCAL (tienen su propio endpoint /api/api-connections)
        conditions.append("(tipo_conexion != 'API_LOCAL' OR tipo_conexion IS NULL)")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
        SELECT * FROM Servidores_Conexiones
        WHERE {where_clause}
        ORDER BY nombre
        """
        
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        servers = [_sql_row_to_server_dict(row) for row in results]
        logger.info(f"[SERVER_REGISTRY][SQL_HIT] Obtenidos {len(servers)} servidores desde EDARSAHUB SQL")
        return servers
        
    except Exception as e:
        logger.warning(f"[SERVER_REGISTRY][SQL_MISS] Error obteniendo servidores desde SQL: {e}")
        return []


def _get_server_by_id_from_sql(server_id: str) -> Optional[Dict]:
    """
    Obtiene un servidor específico por ID desde EDARSAHUB SQL.
    Busca tanto por id como por mongodb_id para compatibilidad.
    """
    try:
        from core.db import execute_sql_query
        
        # Escapar el ID para prevenir SQL injection básico
        safe_id = server_id.replace("'", "''")
        
        query = f"""
        SELECT * FROM Servidores_Conexiones
        WHERE (CAST(id AS VARCHAR(50)) = '{safe_id}' OR mongodb_id = '{safe_id}')
          AND activo = 1
        """
        
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        if results:
            logger.info(f"[SERVER_REGISTRY][SQL_HIT] Servidor {server_id} obtenido desde SQL")
            return _sql_row_to_server_dict(results[0])
        
        logger.debug(f"[SERVER_REGISTRY][SQL_MISS] Servidor {server_id} no encontrado en SQL")
        return None
        
    except Exception as e:
        logger.warning(f"[SERVER_REGISTRY][SQL_ERROR] Error buscando servidor {server_id}: {e}")
        return None


# ============================================================================
# LECTURA DESDE MONGODB (FALLBACK LEGACY)
# ============================================================================

def _mongo_row_to_server_dict(row: Dict) -> Dict:
    """
    Convierte un documento MongoDB al formato normalizado.
    Agrega config_origin y system_type_normalized.
    """
    system_type_raw = row.get('system_type', '')
    
    server = {
        **row,
        'system_type_normalized': normalize_system_type(system_type_raw),
        'config_origin': 'MONGODB_LEGACY',
        'warnings': ['Servidor obtenido desde MongoDB legacy; migrar a EDARSAHUB SQL.']
    }
    
    # Asegurar que no haya _id de MongoDB
    server.pop('_id', None)
    
    return server


async def _get_servers_from_mongo(
    db,
    filter_active: bool = True,
    filter_visible_listado: bool = True,
    exclude_core: bool = True
) -> List[Dict]:
    """
    Obtiene servidores desde MongoDB (fallback legacy).
    """
    try:
        query = {}
        
        if filter_active:
            query['active'] = True
        
        if filter_visible_listado:
            query['$or'] = [
                {'visible_en_listado': {'$exists': False}},
                {'visible_en_listado': True}
            ]
        
        cursor = db.servers.find(query, {'_id': 0})
        servers = await cursor.to_list(1000)
        
        # Filtrar CORE si es necesario
        if exclude_core:
            servers = [s for s in servers if s.get('tipo_conexion') != 'CORE']
        
        # Excluir conexiones API_LOCAL (tienen su propio endpoint)
        servers = [s for s in servers if s.get('tipo_conexion') != 'API_LOCAL']
        
        # Normalizar cada servidor
        normalized = [_mongo_row_to_server_dict(s) for s in servers]
        
        logger.warning(f"[SERVER_REGISTRY][MONGODB_FALLBACK_USED] Obtenidos {len(normalized)} servidores desde MongoDB legacy")
        return normalized
        
    except Exception as e:
        logger.error(f"[SERVER_REGISTRY][MONGODB_ERROR] Error obteniendo servidores desde MongoDB: {e}")
        return []


async def _get_server_by_id_from_mongo(db, server_id: str) -> Optional[Dict]:
    """
    Obtiene un servidor específico por ID desde MongoDB (fallback legacy).
    """
    try:
        server = await db.servers.find_one(
            {'id': server_id, 'active': True},
            {'_id': 0}
        )
        
        if server:
            logger.warning(f"[SERVER_REGISTRY][MONGODB_FALLBACK_USED] Servidor {server_id} obtenido desde MongoDB legacy")
            return _mongo_row_to_server_dict(server)
        
        return None
        
    except Exception as e:
        logger.error(f"[SERVER_REGISTRY][MONGODB_ERROR] Error buscando servidor {server_id}: {e}")
        return None


# ============================================================================
# FUNCIONES PÚBLICAS DEL REGISTRY
# ============================================================================

async def get_server_by_id(
    server_id: str,
    db=None,
    prefer_sql: bool = True,
    allow_mongo_fallback: bool = True,
    mask_secrets: bool = True
) -> Optional[Dict]:
    """
    Obtiene un servidor por ID usando el registry central.
    
    ORDEN DE CONSULTA:
    1. EDARSAHUB SQL (si prefer_sql=True y USE_SQL_FOR_SERVERS=True)
    2. MongoDB (si allow_mongo_fallback=True y no se encontró en SQL)
    
    Args:
        server_id: ID del servidor (UUID)
        db: Conexión a MongoDB (requerido si allow_mongo_fallback=True)
        prefer_sql: Consultar SQL primero
        allow_mongo_fallback: Permitir fallback a MongoDB
        mask_secrets: Enmascarar passwords y api_keys
    
    Returns:
        Dict con datos del servidor o None si no se encuentra
    """
    server = None
    
    # Intentar SQL primero
    if prefer_sql and USE_SQL_FOR_SERVERS:
        server = _get_server_by_id_from_sql(server_id)
    
    # Fallback a MongoDB
    if not server and allow_mongo_fallback and db is not None:
        server = await _get_server_by_id_from_mongo(db, server_id)
    
    # Enmascarar secretos si es necesario
    if server and mask_secrets:
        server = mask_sensitive_fields(server)
    
    return server


async def list_servers(
    db=None,
    user: Optional[Dict] = None,
    prefer_sql: bool = True,
    allow_mongo_fallback: bool = True,
    filter_active: bool = True,
    filter_visible_listado: bool = True,
    exclude_core: bool = True,
    mask_secrets: bool = True
) -> List[Dict]:
    """
    Lista servidores usando el registry central.
    
    ORDEN DE CONSULTA:
    1. EDARSAHUB SQL (si prefer_sql=True y USE_SQL_FOR_SERVERS=True)
    2. MongoDB (si allow_mongo_fallback=True y SQL devuelve vacío)
    
    Args:
        db: Conexión a MongoDB (requerido si allow_mongo_fallback=True)
        user: Usuario actual para filtrar por permisos (opcional)
        prefer_sql: Consultar SQL primero
        allow_mongo_fallback: Permitir fallback a MongoDB
        filter_active: Solo servidores activos
        filter_visible_listado: Solo visibles en listado UI
        exclude_core: Excluir conexiones CORE
        mask_secrets: Enmascarar passwords y api_keys
    
    Returns:
        Lista de servidores
    """
    servers = []
    
    # Intentar SQL primero
    if prefer_sql and USE_SQL_FOR_SERVERS:
        servers = _get_servers_from_sql(
            filter_active=filter_active,
            filter_visible_listado=filter_visible_listado,
            exclude_core=exclude_core
        )
    
    # Fallback a MongoDB si SQL está vacío
    if not servers and allow_mongo_fallback and db is not None:
        servers = await _get_servers_from_mongo(
            db,
            filter_active=filter_active,
            filter_visible_listado=filter_visible_listado,
            exclude_core=exclude_core
        )
    
    # Enmascarar secretos
    if mask_secrets:
        servers = [mask_sensitive_fields(s) for s in servers]
    
    # Filtrar por permisos de usuario (si se proporciona)
    if user:
        servers = filter_servers_by_user_permissions(servers, user)
    
    return servers


def filter_servers_by_user_permissions(servers: List[Dict], user: Dict) -> List[Dict]:
    """
    Filtra servidores según los permisos del usuario.
    
    - SuperAdministrador/Administrador: Ve todos los servidores
    - Otros: Solo ve servidores en allowed_servers
    """
    if not user:
        return servers
    
    role = user.get('role', '')
    
    # Roles con acceso completo (FASE 3B.2: Corregido para usar nombre correcto)
    if role in ['SuperAdministrador', 'Administrador']:
        return servers
    
    # Roles limitados: filtrar por allowed_servers
    allowed_ids = set(user.get('allowed_servers', []))
    
    if not allowed_ids:
        logger.warning(f"[SERVER_REGISTRY][RBAC] Usuario {user.get('email')} sin servidores permitidos")
        return []
    
    filtered = [s for s in servers if s.get('id') in allowed_ids or s.get('mongodb_id') in allowed_ids]
    
    logger.debug(f"[SERVER_REGISTRY][RBAC] Filtrados {len(filtered)}/{len(servers)} servidores para {user.get('email')}")
    
    return filtered


# ============================================================================
# HELPERS PARA CONTEXTO
# ============================================================================

async def resolve_server_context(
    server_id: Optional[str] = None,
    sucursal_id: Optional[str] = None,
    unidad_negocio_id: Optional[str] = None,
    user: Optional[Dict] = None,
    db=None
) -> Dict:
    """
    Resuelve el contexto completo de un servidor para operaciones.
    
    Returns:
        Dict con server, sucursal, unidad_negocio y metadata
    """
    context = {
        'server': None,
        'sucursal': None,
        'unidad_negocio': None,
        'config_origin': None,
        'system_type_normalized': None,
        'warnings': [],
        'errors': []
    }
    
    if not server_id:
        context['errors'].append('server_id es requerido')
        return context
    
    # Obtener servidor
    server = await get_server_by_id(server_id, db=db, mask_secrets=False)
    
    if not server:
        context['errors'].append(f'Servidor {server_id} no encontrado')
        return context
    
    context['server'] = server
    context['config_origin'] = server.get('config_origin', 'UNKNOWN')
    context['system_type_normalized'] = server.get('system_type_normalized', 'UNKNOWN')
    
    # Agregar warnings del servidor
    if server.get('warnings'):
        context['warnings'].extend(server['warnings'])
    
    # Verificar permisos si hay usuario
    if user:
        role = user.get('role', '')
        # FASE 3B.2: Corregido para usar nombre correcto del rol
        if role not in ['SuperAdministrador', 'Administrador']:
            allowed = set(user.get('allowed_servers', []))
            if server.get('id') not in allowed and server.get('mongodb_id') not in allowed:
                context['errors'].append('No tiene permisos para acceder a este servidor')
    
    return context



def get_decrypted_credentials(server: Dict) -> Dict:
    """
    Obtiene las credenciales descifradas de un servidor para uso interno.
    
    FASE 3C: Descifra secretos para conexiones reales.
    
    IMPORTANTE: Esta función es solo para uso interno del backend.
    NUNCA exponer el resultado al frontend o logs.
    
    Args:
        server: Dict con datos del servidor (debe tener secretos sin enmascarar)
        
    Returns:
        Dict con password y api_key descifrados (o valores legacy si no están cifrados)
    """
    from core.secret_manager import decrypt_secret, is_encrypted_secret
    
    credentials = {
        'host': server.get('host', ''),
        'port': server.get('port', 1433),
        'database': server.get('database') or server.get('database_name', ''),
        'username': server.get('username', ''),
        'password': None,
        'api_key': None,
        'api_url': server.get('api_url', ''),
        'was_encrypted': False
    }
    
    # Obtener password
    pwd = server.get('password') or server.get('password_encrypted')
    if pwd:
        try:
            credentials['password'] = decrypt_secret(pwd)
            credentials['was_encrypted'] = is_encrypted_secret(pwd)
        except Exception as e:
            logger.error(f"[SERVER_REGISTRY][DECRYPT_ERROR] Error descifrando password: {type(e).__name__}")
            # Si falla descifrado, asumir que es legacy text plano
            credentials['password'] = pwd
    
    # Obtener api_key
    api = server.get('api_key') or server.get('api_key_encrypted')
    if api:
        try:
            credentials['api_key'] = decrypt_secret(api)
        except Exception as e:
            logger.error(f"[SERVER_REGISTRY][DECRYPT_ERROR] Error descifrando api_key: {type(e).__name__}")
            credentials['api_key'] = api
    
    return credentials


async def get_server_connection_info(
    server_id: str,
    db=None,
    user: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Obtiene información de conexión de un servidor con secretos descifrados.
    
    FASE 3C: Función de alto nivel para obtener datos de conexión.
    
    IMPORTANTE: Esta función es solo para uso interno del backend.
    NUNCA exponer el resultado al frontend.
    
    Args:
        server_id: ID del servidor
        db: Conexión MongoDB (opcional)
        user: Usuario para validar permisos (opcional)
        
    Returns:
        Dict con información de conexión incluyendo credenciales descifradas,
        o None si no se encuentra el servidor
    """
    # Obtener servidor sin enmascarar
    server = await get_server_by_id(server_id, db=db, mask_secrets=False)
    
    if not server:
        return None
    
    # Validar permisos si hay usuario
    if user:
        role = user.get('role', '')
        if role not in ['SuperAdministrador', 'Administrador']:
            allowed = set(user.get('allowed_servers', []))
            if server.get('id') not in allowed and server.get('mongodb_id') not in allowed:
                logger.warning(f"[SERVER_REGISTRY][ACCESS_DENIED] Usuario sin permisos para servidor {server_id}")
                return None
    
    # Obtener credenciales descifradas
    credentials = get_decrypted_credentials(server)
    
    return {
        'id': server.get('id'),
        'name': server.get('name'),
        'system_type': server.get('system_type'),
        'system_type_normalized': server.get('system_type_normalized'),
        'config_origin': server.get('config_origin'),
        **credentials
    }


# ============================================================================
# SUCURSALES POR SERVIDOR
# ============================================================================

async def get_server_sucursales(
    server_id: str,
    db=None,
    prefer_sql: bool = True,
    allow_mongo_fallback: bool = True
) -> List[Dict]:
    """
    Obtiene las sucursales configuradas para un servidor.
    
    ORDEN DE CONSULTA:
    1. EDARSAHUB SQL (campo `sucursales` JSON en Servidores_Conexiones)
    2. MongoDB collection `server_sucursales_config` (fallback)
    
    Args:
        server_id: ID del servidor
        db: Conexión a MongoDB
        prefer_sql: Consultar SQL primero
        allow_mongo_fallback: Permitir fallback a MongoDB
    
    Returns:
        Lista de sucursales configuradas
    """
    sucursales = []
    source = None
    
    # Intentar desde SQL primero (sucursales están en el registro del servidor)
    if prefer_sql and USE_SQL_FOR_SERVERS:
        server = _get_server_by_id_from_sql(server_id)
        if server and server.get('sucursales'):
            sucursales = server['sucursales'] if isinstance(server['sucursales'], list) else []
            source = 'EDARSAHUB_SQL'
            logger.info(f"[SERVER_REGISTRY][SUCURSALES][SQL_HIT] {len(sucursales)} sucursales para servidor {server_id}")
    
    # Fallback a MongoDB si no hay sucursales en SQL
    if not sucursales and allow_mongo_fallback and db is not None:
        try:
            # Buscar en colección dedicada
            cursor = db.server_sucursales_config.find(
                {'server_id': server_id, 'activo': {'$ne': False}},
                {'_id': 0}
            )
            sucursales = await cursor.to_list(100)
            
            if not sucursales:
                # Fallback al campo sucursales del servidor en MongoDB
                server_mongo = await _get_server_by_id_from_mongo(db, server_id)
                if server_mongo and server_mongo.get('sucursales'):
                    sucursales = server_mongo['sucursales'] if isinstance(server_mongo['sucursales'], list) else []
            
            if sucursales:
                source = 'MONGODB_LEGACY'
                logger.warning(f"[SERVER_REGISTRY][SUCURSALES][MONGODB_FALLBACK] {len(sucursales)} sucursales para servidor {server_id}")
        except Exception as e:
            logger.error(f"[SERVER_REGISTRY][SUCURSALES][MONGODB_ERROR] Error obteniendo sucursales: {e}")
    
    # Normalizar cada sucursal
    normalized = []
    for suc in sucursales:
        if isinstance(suc, dict):
            suc['config_origin'] = source or 'UNKNOWN'
            normalized.append(suc)
        elif isinstance(suc, str):
            # Si es solo un ID de sucursal
            normalized.append({
                'id': suc,
                'codigo': suc,
                'config_origin': source or 'UNKNOWN'
            })
    
    return normalized


# ============================================================================
# NORMALIZACIÓN DE REGISTROS
# ============================================================================

def normalize_server_record(record: Dict, source: str = "UNKNOWN") -> Dict:
    """
    Normaliza un registro de servidor para garantizar campos consistentes.
    
    Garantiza que existan todos los campos esperados por frontend y backend,
    incluyendo aliases legacy (_id, server_id, nombre, etc.)
    
    Args:
        record: Registro original del servidor
        source: Fuente del registro ("EDARSAHUB_SQL" o "MONGODB_LEGACY")
    
    Returns:
        Registro normalizado con todos los campos esperados
    """
    if not record:
        return None
    
    system_type_raw = record.get('system_type', '')
    
    normalized = {
        # IDs - mantener compatibilidad con múltiples formatos
        'id': str(record.get('id', '')),
        '_id': str(record.get('id', record.get('_id', ''))),  # Alias para frontend legacy
        'server_id': str(record.get('id', record.get('server_id', ''))),  # Alias backend
        'mongodb_id': record.get('mongodb_id'),  # Mapeo a MongoDB si existe
        
        # Nombres - mantener ambos formatos
        'name': record.get('name', record.get('nombre', '')),
        'nombre': record.get('nombre', record.get('name', '')),
        
        # Tipo de sistema - original y normalizado
        'system_type': system_type_raw,
        'system_type_normalized': normalize_system_type(system_type_raw),
        
        # Tipo de conexión
        'tipo_conexion': record.get('tipo_conexion', 'DATA_SOURCE'),
        'connection_type': record.get('tipo_conexion', record.get('connection_type', 'DATA_SOURCE')),
        
        # Conexión SQL
        'host': record.get('host', ''),
        'port': record.get('port', 1433),
        'database': record.get('database', record.get('database_name', '')),
        'database_name': record.get('database_name', record.get('database', '')),
        'username': record.get('username', ''),
        
        # API (si aplica)
        'api_url': record.get('api_url', ''),
        
        # Estado
        'active': bool(record.get('active', record.get('activo', False))),
        'activo': bool(record.get('activo', record.get('active', False))),
        'visible_en_operaciones': bool(record.get('visible_en_operaciones', True)),
        'visible_en_listado': bool(record.get('visible_en_listado', True)),
        'es_editable_ui': bool(record.get('es_editable_ui', True)),
        'es_eliminable_ui': bool(record.get('es_eliminable_ui', True)),
        
        # Relaciones
        'empresa_id': record.get('empresa_id'),
        
        # Configuración
        'sucursales': record.get('sucursales'),
        'categorias': record.get('categorias'),
        'departamentos': record.get('departamentos'),
        'date_calculation_method': record.get('date_calculation_method'),
        'queries_configured': bool(record.get('queries_configured', False)),
        'query_ventas': record.get('query_ventas'),
        'query_inventario': record.get('query_inventario'),
        'query_movimientos': record.get('query_movimientos'),
        
        # Timestamps
        'created_at': record.get('created_at'),
        'updated_at': record.get('updated_at'),
        
        # Metadatos de registro
        'config_origin': source,
        'warnings': record.get('warnings', [])
    }
    
    return normalized


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'get_server_by_id',
    'list_servers',
    'get_server_sucursales',
    'filter_servers_by_user_permissions',
    'resolve_server_context',
    'normalize_server_record',
    'mask_sensitive_fields',
    'normalize_system_type',
    # FASE 3B.1: Funciones de escritura
    'create_server',
    'update_server',
    'delete_server',
    'sync_server_to_mongo',
    'validate_server_payload',
    'USE_SQL_FOR_SERVERS',
    'EDARSAHUB_CONFIG'
]


# ============================================================================
# FASE 3B.1: FUNCIONES DE ESCRITURA SQL-FIRST
# ============================================================================

def validate_server_payload(payload: Dict, mode: str = "create") -> Dict:
    """
    Valida el payload de un servidor antes de crear/actualizar.
    
    Args:
        payload: Datos del servidor
        mode: "create" o "update"
    
    Returns:
        Dict con errores o payload validado
    
    Raises:
        ValueError: Si hay errores de validación
    """
    errors = []
    warnings = []
    
    # Campos requeridos para crear
    if mode == "create":
        required = ['name', 'system_type', 'host']
        for field in required:
            if not payload.get(field) and not payload.get('nombre'):
                if field == 'name' and payload.get('nombre'):
                    continue
                errors.append(f"Campo requerido faltante: {field}")
    
    # Normalizar system_type
    system_type = payload.get('system_type', '')
    if system_type:
        normalized = normalize_system_type(system_type)
        if normalized == 'UNKNOWN':
            warnings.append(f"system_type '{system_type}' no reconocido, se guardará como UNKNOWN")
        payload['system_type_normalized'] = normalized
    elif mode == "create":
        errors.append("system_type es requerido")
    
    # Validar tipo_conexion
    tipo_conexion = payload.get('tipo_conexion', 'DATA_SOURCE')
    if tipo_conexion not in ['DATA_SOURCE', 'CORE', 'API']:
        warnings.append(f"tipo_conexion '{tipo_conexion}' no estándar, usando DATA_SOURCE")
        payload['tipo_conexion'] = 'DATA_SOURCE'
    
    # No permitir crear CORE desde API normal
    if mode == "create" and tipo_conexion == 'CORE':
        errors.append("No se puede crear conexión tipo CORE desde API estándar")
    
    # Validar password - no sobrescribir si viene enmascarado
    password = payload.get('password', '')
    if password in ['********', '••••••••', '*****', '']:
        payload.pop('password', None)  # No actualizar password
        if mode == "create":
            warnings.append("Password vacío o enmascarado, servidor puede no conectar")
    
    if errors:
        raise ValueError("; ".join(errors))
    
    payload['_validation_warnings'] = warnings
    return payload


def _execute_sql_write(query: str, params: tuple = None) -> bool:
    """
    Ejecuta una query de escritura en EDARSAHUB SQL.
    
    Returns:
        True si éxito, False si error
    """
    try:
        import pymssql
        conn = pymssql.connect(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            EDARSAHUB_CONFIG['database'],
            port=EDARSAHUB_CONFIG['port'],
            timeout=30
        )
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"[SERVER_REGISTRY][SQL_WRITE_ERROR] {e}")
        return False


async def create_server(
    payload: Dict,
    db=None,
    user: Optional[Dict] = None,
    sync_mongo: bool = True
) -> Dict:
    """
    Crea un servidor en EDARSAHUB SQL primero, luego sincroniza a MongoDB.
    
    FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.
    
    Args:
        payload: Datos del servidor
        db: Conexión MongoDB (para sync)
        user: Usuario que crea (para auditoría)
        sync_mongo: Si True, sincroniza a MongoDB después
    
    Returns:
        Dict con servidor creado y status de sync
    """
    import uuid
    
    logger.info(f"[SERVER_REGISTRY][CREATE_SQL_START] Creando servidor: {payload.get('name', payload.get('nombre', 'N/A'))}")
    
    # Validar payload
    try:
        payload = validate_server_payload(payload, mode="create")
    except ValueError as e:
        return {
            'success': False,
            'error': str(e),
            'config_origin': None,
            'sync_status': 'VALIDATION_ERROR'
        }
    
    # Generar ID (formato UUID sin guiones para SQL Server uniqueidentifier)
    server_id = str(uuid.uuid4())
    # Formato datetime compatible con SQL Server: YYYY-MM-DD HH:MM:SS
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    # Preparar datos para SQL
    nombre = payload.get('name') or payload.get('nombre', '')
    system_type = payload.get('system_type', 'UNKNOWN')
    system_type_normalized = payload.get('system_type_normalized', normalize_system_type(system_type))
    
    # Query de inserción SQL
    query = """
    INSERT INTO Servidores_Conexiones (
        id, nombre, system_type, tipo_conexion, host, port, database_name,
        username, password_encrypted, api_url, api_key_encrypted,
        activo, visible_en_operaciones, visible_en_listado, es_editable_ui, es_eliminable_ui,
        created_at, updated_at, mongodb_id
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s
    )
    """
    
    # FASE 3C: Cifrar secretos antes de guardar
    from core.secret_manager import encrypt_secret
    
    password_to_store = encrypt_secret(payload.get('password', '')) if payload.get('password') else ''
    api_key_to_store = encrypt_secret(payload.get('api_key', '')) if payload.get('api_key') else ''
    
    params = (
        server_id,
        nombre,
        system_type,
        payload.get('tipo_conexion', 'DATA_SOURCE'),
        payload.get('host', ''),
        payload.get('port', 1433),
        payload.get('database') or payload.get('database_name', ''),
        payload.get('username', ''),
        password_to_store,  # FASE 3C: Cifrado
        payload.get('api_url', ''),
        api_key_to_store,  # FASE 3C: Cifrado
        True,  # activo
        payload.get('visible_en_operaciones', True),
        payload.get('visible_en_listado', True),
        payload.get('es_editable_ui', True),
        payload.get('es_eliminable_ui', True),
        now,
        now,
        server_id  # mongodb_id será el mismo inicialmente
    )
    
    # Ejecutar en SQL
    sql_success = _execute_sql_write(query, params)
    
    if not sql_success:
        logger.error("[SERVER_REGISTRY][CREATE_SQL_ERROR] Falló creación en SQL")
        return {
            'success': False,
            'error': 'Error al crear servidor en base de datos principal',
            'config_origin': None,
            'sync_status': 'SQL_ERROR'
        }
    
    logger.info(f"[SERVER_REGISTRY][CREATE_SQL_SUCCESS] Servidor creado en SQL: {server_id}")
    
    # Sincronizar a MongoDB
    sync_status = 'SYNCED'
    sync_warnings = []
    
    if sync_mongo and db is not None:
        try:
            mongo_doc = {
                'id': server_id,
                'name': nombre,
                'system_type': system_type,
                'tipo_conexion': payload.get('tipo_conexion', 'DATA_SOURCE'),
                'host': payload.get('host', ''),
                'port': payload.get('port', 1433),
                'database': payload.get('database') or payload.get('database_name', ''),
                'username': payload.get('username', ''),
                'password': payload.get('password', ''),
                'api_url': payload.get('api_url', ''),
                'active': True,
                'visible_en_operaciones': payload.get('visible_en_operaciones', True),
                'visible_en_listado': payload.get('visible_en_listado', True),
                'es_editable_ui': payload.get('es_editable_ui', True),
                'es_eliminable_ui': payload.get('es_eliminable_ui', True),
                'created_at': now
            }
            await db.servers.insert_one(mongo_doc)
            logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")
        except Exception as e:
            sync_status = 'PARTIAL_SYNC'
            sync_warnings.append(f"SQL exitoso pero MongoDB falló: {str(e)}")
            logger.warning(f"[SERVER_REGISTRY][SYNC_MONGO_ERROR] {e}")
    
    # Construir respuesta
    result = {
        'success': True,
        'id': server_id,
        'name': nombre,
        'system_type': system_type,
        'system_type_normalized': system_type_normalized,
        'config_origin': 'EDARSAHUB_SQL',
        'sync_status': sync_status,
        'warnings': payload.get('_validation_warnings', []) + sync_warnings
    }
    
    return result


async def update_server(
    server_id: str,
    payload: Dict,
    db=None,
    user: Optional[Dict] = None,
    sync_mongo: bool = True
) -> Dict:
    """
    Actualiza un servidor en EDARSAHUB SQL primero, luego sincroniza a MongoDB.
    
    FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.
    
    Args:
        server_id: ID del servidor (SQL id o mongodb_id)
        payload: Datos a actualizar
        db: Conexión MongoDB (para sync y para obtener password existente)
        user: Usuario que actualiza (para auditoría)
        sync_mongo: Si True, sincroniza a MongoDB después
    
    Returns:
        Dict con resultado de actualización
    """
    logger.info(f"[SERVER_REGISTRY][UPDATE_SQL_START] Actualizando servidor: {server_id}")
    
    # Validar payload
    try:
        payload = validate_server_payload(payload, mode="update")
    except ValueError as e:
        return {
            'success': False,
            'error': str(e),
            'sync_status': 'VALIDATION_ERROR'
        }
    
    # Verificar que existe en SQL
    existing = _get_server_by_id_from_sql(server_id)
    if not existing:
        return {
            'success': False,
            'error': f'Servidor {server_id} no encontrado en base de datos principal',
            'sync_status': 'NOT_FOUND'
        }
    
    # Protección CORE
    if existing.get('tipo_conexion') == 'CORE':
        return {
            'success': False,
            'error': 'No se puede modificar conexión tipo CORE desde API estándar',
            'sync_status': 'PROTECTED'
        }
    
    # Preparar campos a actualizar
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    update_fields = []
    update_values = []
    processed_sql_fields = set()  # Evitar duplicados
    
    field_mapping = {
        'name': 'nombre',
        'nombre': 'nombre',
        'system_type': 'system_type',
        'host': 'host',
        'port': 'port',
        'database': 'database_name',
        'database_name': 'database_name',
        'username': 'username',
        'api_url': 'api_url',
        'visible_en_operaciones': 'visible_en_operaciones',
        'visible_en_listado': 'visible_en_listado'
    }
    
    for api_field, sql_field in field_mapping.items():
        if api_field in payload and payload[api_field] is not None:
            # Evitar duplicados (ej: name y nombre mapean a mismo campo)
            if sql_field not in processed_sql_fields:
                update_fields.append(f"{sql_field} = %s")
                update_values.append(payload[api_field])
                processed_sql_fields.add(sql_field)
    
    # FASE 3C: Password solo si viene explícito y no enmascarado
    from core.secret_manager import should_preserve_existing_secret, encrypt_secret
    
    if 'password' in payload:
        if not should_preserve_existing_secret(payload['password']):
            # Cifrar nuevo password
            encrypted_pwd = encrypt_secret(payload['password'])
            update_fields.append("password_encrypted = %s")
            update_values.append(encrypted_pwd)
    
    # FASE 3C: API Key solo si viene explícito y no enmascarado
    if 'api_key' in payload:
        if not should_preserve_existing_secret(payload['api_key']):
            # Cifrar nueva api_key
            encrypted_api = encrypt_secret(payload['api_key'])
            update_fields.append("api_key_encrypted = %s")
            update_values.append(encrypted_api)
    
    # Siempre actualizar timestamp
    update_fields.append("updated_at = %s")
    update_values.append(now)
    
    if not update_fields:
        return {
            'success': False,
            'error': 'No hay campos válidos para actualizar',
            'sync_status': 'NO_CHANGES'
        }
    
    # Construir y ejecutar query
    update_values.append(server_id)  # Para WHERE
    update_values.append(server_id)  # Para mongodb_id fallback
    
    query = f"""
    UPDATE Servidores_Conexiones
    SET {', '.join(update_fields)}
    WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s
    """
    
    sql_success = _execute_sql_write(query, tuple(update_values))
    
    if not sql_success:
        logger.error("[SERVER_REGISTRY][UPDATE_SQL_ERROR] Falló actualización en SQL")
        return {
            'success': False,
            'error': 'Error al actualizar servidor en base de datos principal',
            'sync_status': 'SQL_ERROR'
        }
    
    logger.info(f"[SERVER_REGISTRY][UPDATE_SQL_SUCCESS] Servidor actualizado en SQL: {server_id}")
    
    # Sincronizar a MongoDB
    sync_status = 'SYNCED'
    sync_warnings = []
    
    if sync_mongo and db is not None:
        try:
            mongo_update = {k: v for k, v in payload.items() if k not in ['_validation_warnings'] and v is not None}
            mongo_update['updated_at'] = now
            
            # Mapear campos
            if 'nombre' in mongo_update:
                mongo_update['name'] = mongo_update.pop('nombre')
            if 'database_name' in mongo_update:
                mongo_update['database'] = mongo_update.pop('database_name')
            
            await db.servers.update_one(
                {'id': server_id},
                {'$set': mongo_update}
            )
            logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")
        except Exception as e:
            sync_status = 'PARTIAL_SYNC'
            sync_warnings.append(f"SQL actualizado pero MongoDB falló: {str(e)}")
            logger.warning(f"[SERVER_REGISTRY][SYNC_MONGO_ERROR] {e}")
    
    return {
        'success': True,
        'id': server_id,
        'config_origin': 'EDARSAHUB_SQL',
        'sync_status': sync_status,
        'warnings': payload.get('_validation_warnings', []) + sync_warnings,
        'message': 'Servidor actualizado'
    }


async def delete_server(
    server_id: str,
    db=None,
    user: Optional[Dict] = None,
    sync_mongo: bool = True,
    soft_delete: bool = True
) -> Dict:
    """
    Desactiva (soft delete) un servidor en EDARSAHUB SQL, luego sincroniza a MongoDB.
    
    FASE 3B.1: SQL-first con sync a MongoDB como espejo legacy.
    Por default usa soft delete (activo=false) en lugar de borrado físico.
    
    Args:
        server_id: ID del servidor
        db: Conexión MongoDB (para sync)
        user: Usuario que elimina (para auditoría)
        sync_mongo: Si True, sincroniza a MongoDB después
        soft_delete: Si True, solo marca activo=false; si False, borra físicamente
    
    Returns:
        Dict con resultado de eliminación
    """
    logger.info(f"[SERVER_REGISTRY][DELETE_SQL_START] {'Desactivando' if soft_delete else 'Eliminando'} servidor: {server_id}")
    
    # Verificar que existe en SQL
    existing = _get_server_by_id_from_sql(server_id)
    if not existing:
        return {
            'success': False,
            'error': f'Servidor {server_id} no encontrado',
            'sync_status': 'NOT_FOUND'
        }
    
    # Protección CORE
    if existing.get('tipo_conexion') == 'CORE':
        return {
            'success': False,
            'error': 'No se puede eliminar conexión tipo CORE',
            'sync_status': 'PROTECTED'
        }
    
    # Ejecutar en SQL
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    if soft_delete:
        query = """
        UPDATE Servidores_Conexiones
        SET activo = 0, updated_at = %s
        WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s
        """
        params = (now, server_id, server_id)
    else:
        query = """
        DELETE FROM Servidores_Conexiones
        WHERE CAST(id AS VARCHAR(50)) = %s OR mongodb_id = %s
        """
        params = (server_id, server_id)
    
    sql_success = _execute_sql_write(query, params)
    
    if not sql_success:
        logger.error("[SERVER_REGISTRY][DELETE_SQL_ERROR] Falló eliminación en SQL")
        return {
            'success': False,
            'error': 'Error al eliminar servidor en base de datos principal',
            'sync_status': 'SQL_ERROR'
        }
    
    logger.info(f"[SERVER_REGISTRY][DELETE_SQL_SUCCESS] Servidor {'desactivado' if soft_delete else 'eliminado'} en SQL: {server_id}")
    
    # Sincronizar a MongoDB
    sync_status = 'SYNCED'
    sync_warnings = []
    
    if sync_mongo and db is not None:
        try:
            if soft_delete:
                await db.servers.update_one(
                    {'id': server_id},
                    {'$set': {'active': False, 'updated_at': now}}
                )
            else:
                await db.servers.delete_one({'id': server_id})
            logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado a MongoDB: {server_id}")
        except Exception as e:
            sync_status = 'PARTIAL_SYNC'
            sync_warnings.append(f"SQL actualizado pero MongoDB falló: {str(e)}")
            logger.warning(f"[SERVER_REGISTRY][SYNC_MONGO_ERROR] {e}")
    
    return {
        'success': True,
        'id': server_id,
        'action': 'soft_delete' if soft_delete else 'hard_delete',
        'config_origin': 'EDARSAHUB_SQL',
        'sync_status': sync_status,
        'warnings': sync_warnings,
        'message': 'Servidor desactivado' if soft_delete else 'Servidor eliminado'
    }


async def sync_server_to_mongo(sql_server_id: str, db=None) -> Dict:
    """
    Sincroniza un servidor específico desde SQL hacia MongoDB.
    
    Útil para reconciliación manual o después de cambios directos en SQL.
    
    Args:
        sql_server_id: ID del servidor en SQL
        db: Conexión MongoDB
    
    Returns:
        Dict con resultado de sincronización
    """
    if db is None:
        return {
            'success': False,
            'error': 'Conexión MongoDB no disponible',
            'sync_status': 'NO_DB'
        }
    
    # Obtener servidor desde SQL
    server = _get_server_by_id_from_sql(sql_server_id)
    if not server:
        return {
            'success': False,
            'error': f'Servidor {sql_server_id} no encontrado en SQL',
            'sync_status': 'NOT_FOUND'
        }
    
    logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_START] Sincronizando servidor: {sql_server_id}")
    
    try:
        # Construir documento MongoDB
        mongo_doc = {
            'id': server['id'],
            'name': server['name'],
            'system_type': server['system_type'],
            'tipo_conexion': server['tipo_conexion'],
            'host': server['host'],
            'port': server['port'],
            'database': server['database'],
            'username': server['username'],
            'password': server.get('password', ''),
            'api_url': server.get('api_url', ''),
            'active': server['active'],
            'visible_en_operaciones': server.get('visible_en_operaciones', True),
            'visible_en_listado': server.get('visible_en_listado', True),
            'es_editable_ui': server.get('es_editable_ui', True),
            'es_eliminable_ui': server.get('es_eliminable_ui', True),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Upsert en MongoDB
        await db.servers.update_one(
            {'id': server['id']},
            {'$set': mongo_doc},
            upsert=True
        )
        
        logger.info(f"[SERVER_REGISTRY][SYNC_MONGO_SUCCESS] Servidor sincronizado: {sql_server_id}")
        
        return {
            'success': True,
            'id': server['id'],
            'sync_status': 'SYNCED',
            'message': 'Servidor sincronizado a MongoDB'
        }
        
    except Exception as e:
        logger.error(f"[SERVER_REGISTRY][SYNC_MONGO_ERROR] {e}")
        return {
            'success': False,
            'error': str(e),
            'sync_status': 'SYNC_ERROR'
        }


# ============================================================================
# FASE 3B.1: FUNCIONES DE MAPEO Y RECONCILIACIÓN
# ============================================================================

def build_legacy_mongo_server_document(sql_record: Dict) -> Dict:
    """
    Construye un documento MongoDB legacy a partir de un registro SQL.
    
    Usado para sincronizar servidores de SQL hacia MongoDB manteniendo
    compatibilidad con el esquema legacy de MongoDB.
    
    Args:
        sql_record: Registro del servidor desde SQL
    
    Returns:
        Dict compatible con colección MongoDB servers
    """
    if not sql_record:
        return None
    
    return {
        'id': sql_record.get('id', ''),
        'name': sql_record.get('name') or sql_record.get('nombre', ''),
        'system_type': sql_record.get('system_type', ''),
        'tipo_conexion': sql_record.get('tipo_conexion', 'DATA_SOURCE'),
        'host': sql_record.get('host', ''),
        'port': sql_record.get('port', 1433),
        'database': sql_record.get('database') or sql_record.get('database_name', ''),
        'username': sql_record.get('username', ''),
        'password': sql_record.get('password', ''),  # Solo para sync interno, nunca exponer
        'api_url': sql_record.get('api_url', ''),
        'api_key': sql_record.get('api_key', ''),  # Solo para sync interno, nunca exponer
        'active': bool(sql_record.get('active', sql_record.get('activo', False))),
        'visible_en_operaciones': bool(sql_record.get('visible_en_operaciones', True)),
        'visible_en_listado': bool(sql_record.get('visible_en_listado', True)),
        'es_editable_ui': bool(sql_record.get('es_editable_ui', True)),
        'es_eliminable_ui': bool(sql_record.get('es_eliminable_ui', True)),
        'sucursales': sql_record.get('sucursales'),
        'categorias': sql_record.get('categorias'),
        'departamentos': sql_record.get('departamentos'),
        'date_calculation_method': sql_record.get('date_calculation_method'),
        'queries_configured': bool(sql_record.get('queries_configured', False)),
        'query_ventas': sql_record.get('query_ventas'),
        'query_inventario': sql_record.get('query_inventario'),
        'query_movimientos': sql_record.get('query_movimientos'),
        'created_at': sql_record.get('created_at'),
        'updated_at': sql_record.get('updated_at')
    }


def map_sql_to_api_server_response(sql_record: Dict, mask_secrets: bool = True) -> Dict:
    """
    Mapea un registro SQL al formato de respuesta API.
    
    Garantiza campos compatibles con frontend y nunca expone secretos.
    
    Args:
        sql_record: Registro del servidor desde SQL
        mask_secrets: Si True, enmascara passwords y api_keys
    
    Returns:
        Dict con formato de respuesta API
    """
    if not sql_record:
        return None
    
    system_type = sql_record.get('system_type', '')
    
    response = {
        # IDs - múltiples formatos para compatibilidad
        'id': str(sql_record.get('id', '')),
        '_id': str(sql_record.get('id', '')),  # Alias legacy
        'server_id': str(sql_record.get('id', '')),  # Alias backend
        'mongodb_id': sql_record.get('mongodb_id'),
        
        # Nombres
        'name': sql_record.get('name') or sql_record.get('nombre', ''),
        'nombre': sql_record.get('nombre') or sql_record.get('name', ''),
        
        # System type
        'system_type': system_type,
        'system_type_normalized': normalize_system_type(system_type),
        
        # Conexión
        'tipo_conexion': sql_record.get('tipo_conexion', 'DATA_SOURCE'),
        'connection_type': sql_record.get('tipo_conexion', 'DATA_SOURCE'),
        'host': sql_record.get('host', ''),
        'port': sql_record.get('port', 1433),
        'database': sql_record.get('database') or sql_record.get('database_name', ''),
        'database_name': sql_record.get('database_name') or sql_record.get('database', ''),
        'username': sql_record.get('username', ''),
        'api_url': sql_record.get('api_url', ''),
        
        # Estado
        'active': bool(sql_record.get('active', sql_record.get('activo', False))),
        'activo': bool(sql_record.get('activo', sql_record.get('active', False))),
        'visible_en_operaciones': bool(sql_record.get('visible_en_operaciones', True)),
        'visible_en_listado': bool(sql_record.get('visible_en_listado', True)),
        'es_editable_ui': bool(sql_record.get('es_editable_ui', True)),
        'es_eliminable_ui': bool(sql_record.get('es_eliminable_ui', True)),
        
        # Configuración
        'sucursales': sql_record.get('sucursales'),
        'categorias': sql_record.get('categorias'),
        'departamentos': sql_record.get('departamentos'),
        'queries_configured': bool(sql_record.get('queries_configured', False)),
        
        # Metadatos
        'config_origin': 'EDARSAHUB_SQL',
        'created_at': sql_record.get('created_at'),
        'updated_at': sql_record.get('updated_at')
    }
    
    # Enmascarar secretos
    if mask_secrets:
        response['password_configured'] = bool(sql_record.get('password') or sql_record.get('password_encrypted'))
        response['api_key_configured'] = bool(sql_record.get('api_key') or sql_record.get('api_key_encrypted'))
    else:
        response['password'] = sql_record.get('password', '')
        response['api_key'] = sql_record.get('api_key', '')
    
    return response


async def reconcile_sql_mongo_servers(db=None, dry_run: bool = True) -> Dict:
    """
    Reconcilia servidores entre SQL y MongoDB.
    
    Compara ambas fuentes y reporta diferencias. En modo apply,
    sincroniza MongoDB para que sea espejo de SQL.
    
    Args:
        db: Conexión MongoDB
        dry_run: Si True, solo reporta diferencias sin modificar
    
    Returns:
        Dict con reporte de reconciliación
    """
    logger.info(f"[SERVER_REGISTRY][RECONCILIATION_START] dry_run={dry_run}")
    
    report = {
        'status': 'SUCCESS',
        'dry_run': dry_run,
        'sql_count': 0,
        'mongo_count': 0,
        'matched': 0,
        'sql_only': [],
        'mongo_only': [],
        'diffs': [],
        'synced': [],
        'warnings': [],
        'errors': []
    }
    
    try:
        # Obtener servidores de SQL
        sql_servers = _get_servers_from_sql(filter_active=False, filter_visible_listado=False, exclude_core=False)
        report['sql_count'] = len(sql_servers)
        
        # Crear índice por ID y mongodb_id
        sql_by_id = {s['id']: s for s in sql_servers}
        sql_by_mongodb_id = {s['mongodb_id']: s for s in sql_servers if s.get('mongodb_id')}
        
        # Obtener servidores de MongoDB
        if db is None:
            report['warnings'].append('No se puede verificar MongoDB sin conexión')
            return report
        
        mongo_cursor = db.servers.find({}, {'_id': 0})
        mongo_servers = await mongo_cursor.to_list(1000)
        report['mongo_count'] = len(mongo_servers)
        
        # Crear índice por ID
        mongo_by_id = {s['id']: s for s in mongo_servers}
        
        # Comparar: SQL que no están en Mongo
        for sql_id, sql_server in sql_by_id.items():
            mongo_server = mongo_by_id.get(sql_id) or mongo_by_id.get(sql_server.get('mongodb_id'))
            
            if not mongo_server:
                report['sql_only'].append({
                    'id': sql_id,
                    'name': sql_server.get('name', 'N/A'),
                    'system_type': sql_server.get('system_type', 'N/A')
                })
                
                # Sincronizar si no es dry_run
                if not dry_run:
                    try:
                        mongo_doc = build_legacy_mongo_server_document(sql_server)
                        await db.servers.insert_one(mongo_doc)
                        report['synced'].append(sql_id)
                        logger.info(f"[SERVER_REGISTRY][RECONCILIATION_SYNC] Creado en MongoDB: {sql_id}")
                    except Exception as e:
                        report['errors'].append(f"Error sincronizando {sql_id}: {str(e)}")
            else:
                report['matched'] += 1
                
                # Verificar diferencias de campos críticos
                diffs = []
                if sql_server.get('name') != mongo_server.get('name'):
                    diffs.append(f"name: SQL='{sql_server.get('name')}' vs Mongo='{mongo_server.get('name')}'")
                if sql_server.get('system_type') != mongo_server.get('system_type'):
                    diffs.append(f"system_type: SQL='{sql_server.get('system_type')}' vs Mongo='{mongo_server.get('system_type')}'")
                if sql_server.get('active') != mongo_server.get('active'):
                    diffs.append(f"active: SQL={sql_server.get('active')} vs Mongo={mongo_server.get('active')}")
                
                if diffs:
                    report['diffs'].append({
                        'id': sql_id,
                        'name': sql_server.get('name', 'N/A'),
                        'differences': diffs
                    })
                    
                    # Actualizar si no es dry_run
                    if not dry_run:
                        try:
                            mongo_doc = build_legacy_mongo_server_document(sql_server)
                            await db.servers.update_one({'id': sql_id}, {'$set': mongo_doc})
                            report['synced'].append(sql_id)
                            logger.info(f"[SERVER_REGISTRY][RECONCILIATION_SYNC] Actualizado en MongoDB: {sql_id}")
                        except Exception as e:
                            report['errors'].append(f"Error actualizando {sql_id}: {str(e)}")
        
        # Comparar: Mongo que no están en SQL
        for mongo_id, mongo_server in mongo_by_id.items():
            if mongo_id not in sql_by_id and mongo_id not in sql_by_mongodb_id:
                report['mongo_only'].append({
                    'id': mongo_id,
                    'name': mongo_server.get('name', 'N/A'),
                    'system_type': mongo_server.get('system_type', 'N/A')
                })
                report['warnings'].append(f"Servidor {mongo_id} existe en MongoDB pero no en SQL")
        
        # Determinar status final
        if report['errors']:
            report['status'] = 'ERROR'
        elif report['sql_only'] or report['mongo_only'] or report['diffs']:
            report['status'] = 'DIFFS_FOUND'
        
        logger.info(f"[SERVER_REGISTRY][RECONCILIATION_COMPLETE] matched={report['matched']}, sql_only={len(report['sql_only'])}, mongo_only={len(report['mongo_only'])}, diffs={len(report['diffs'])}")
        
    except Exception as e:
        report['status'] = 'ERROR'
        report['errors'].append(str(e))
        logger.error(f"[SERVER_REGISTRY][RECONCILIATION_ERROR] {e}")
    
    return report


# ============================================================================
# EXPORTS ACTUALIZADOS
# ============================================================================

__all__ = [
    # Lectura
    'get_server_by_id',
    'list_servers',
    'get_server_sucursales',
    'filter_servers_by_user_permissions',
    'resolve_server_context',
    'normalize_server_record',
    'mask_sensitive_fields',
    'normalize_system_type',
    # FASE 3B.1: Escritura
    'create_server',
    'update_server',
    'delete_server',
    'sync_server_to_mongo',
    'validate_server_payload',
    # FASE 3B.1: Mapeo y reconciliación
    'build_legacy_mongo_server_document',
    'map_sql_to_api_server_response',
    'reconcile_sql_mongo_servers',
    # Config
    'USE_SQL_FOR_SERVERS',
    'EDARSAHUB_CONFIG'
]

