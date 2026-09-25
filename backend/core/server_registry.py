"""
EDARSA HUB - Server Registry Central
====================================

FASE 3B: Registry centralizado para resolución de servidores.

PRINCIPIOS:
1. EDARSAHUB SQL es la fuente primaria de configuración de servidores
2. EDARSAHUB SQL es la única fuente operativa para configuración de servidores
3. No usar MongoDB como fallback operativo
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
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.db import get_sql_connection

# Configuración EDARSAHUB SQL
# P2-01: Config centralizado
_cfg = get_edarsahub_sql_config()
EDARSAHUB_CONFIG = {
    'host': _cfg.host,
    'port': _cfg.port,
    'database': _cfg.database,
    'username': _cfg.user,
    'password': _cfg.password
}

# Flag para habilitar/deshabilitar lectura desde SQL (para rollback rápido)
USE_SQL_FOR_SERVERS = True  # SQL-only operativo; sin rollback a Mongo

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


def _parse_tipos_movimiento(value) -> List:
    """
    FASE T3.4-B4 / P1: Parsea tipos_movimiento desde SQL.
    
    Soporta dos formatos:
    A) Lista de strings: '["ECA", "EDE", ...]' → devuelve como está para compatibilidad
    B) Lista de objetos: '[{"codigo":"ECA","descripcion":"...","tipo":"EN"}, ...]' → devuelve objetos
    
    Returns:
        Lista de tipos de movimiento (strings u objetos según formato guardado)
    """
    import json
    
    if value is None:
        return []
    
    if isinstance(value, list):
        # Ya es una lista, devolver como está
        return value
    
    if isinstance(value, str):
        if not value.strip():
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed  # Devolver lista tal cual (strings u objetos)
            else:
                logger.warning(f"[SERVER_REGISTRY] tipos_movimiento no es array: {type(parsed)}")
                return []
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"[SERVER_REGISTRY] Error parseando tipos_movimiento: {e}")
            return []
    
    logger.warning(f"[SERVER_REGISTRY] tipos_movimiento tipo inesperado: {type(value)}")
    return []


def _serialize_catalog_field(value, field_name: str) -> Optional[str]:
    """
    P0: Serializa un campo de catálogo (tipos_movimiento, categorias, departamentos) a JSON string.
    
    Args:
        value: Puede ser lista, dict, string JSON, o None
        field_name: Nombre del campo para logging
    
    Returns:
        String JSON válido o None si el valor no es serializable
    """
    if value is None:
        return None
    
    # Si ya es string, validar que sea JSON válido
    if isinstance(value, str):
        if not value.strip():
            return '[]'  # String vacío → array vacío
        try:
            # Validar JSON
            json.loads(value)
            return value  # Ya es JSON válido
        except json.JSONDecodeError:
            logger.warning(f"[SERVER_REGISTRY] {field_name}: string no es JSON válido, ignorando")
            return None
    
    # Si es lista o dict, serializar
    if isinstance(value, (list, dict)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.warning(f"[SERVER_REGISTRY] {field_name}: error serializando: {e}")
            return None
    
    logger.warning(f"[SERVER_REGISTRY] {field_name}: tipo no soportado {type(value)}")
    return None


# ============================================================================
# LECTURA DESDE EDARSAHUB SQL
# ============================================================================

def _sql_row_to_server_dict(row: Dict, source: str = "EDARSAHUB_SQL") -> Dict:
    """
    Convierte una fila de Servidores_Conexiones (SQL) al formato del sistema.
    Garantiza paridad con el esquema de MongoDB.
    
    FASE T3.4-B4: Agregado parsing de tipos_movimiento desde SQL.
    FIX 2026-05: Garantiza valores por defecto para campos requeridos por Pydantic.
    """
    system_type_raw = row.get('system_type', '')
    
    # FASE T3.4-B4: Parsear tipos_movimiento desde SQL (NVARCHAR JSON -> list)
    tipos_movimiento_raw = row.get('tipos_movimiento')
    tipos_movimiento = _parse_tipos_movimiento(tipos_movimiento_raw)
    
    # FIX 2026-05: Parsear campos JSON y garantizar valores por defecto
    sucursales_parsed = _parse_json_field(row.get('sucursales'))
    categorias_parsed = _parse_json_field(row.get('categorias'))
    departamentos_parsed = _parse_json_field(row.get('departamentos'))
    
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
        # FIX 2026-05: Garantizar lista vacía si NULL (Pydantic requiere List, no None)
        'sucursales': sucursales_parsed if isinstance(sucursales_parsed, list) else [],
        'categorias': categorias_parsed if isinstance(categorias_parsed, list) else [],
        'departamentos': departamentos_parsed if isinstance(departamentos_parsed, list) else [],
        'tipos_movimiento': tipos_movimiento,  # FASE T3.4-B4: Nuevo campo
        # FIX 2026-05: Garantizar string por defecto si NULL (Pydantic requiere str, no None)
        'date_calculation_method': row.get('date_calculation_method') or 'inventory_dates',
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
        # R10A: El listado administrativo debe incluir API_LOCAL cuando visible_en_listado=true.
        # Operaciones conserva su filtro propio en get_visible_servers_for_operaciones().
        
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
# FUNCIONES PÚBLICAS DEL REGISTRY
# ============================================================================

async def get_server_by_id(
    server_id: str,
    db=None,
    prefer_sql: bool = True,
    allow_mongo_fallback: bool = False,
    mask_secrets: bool = True
) -> Optional[Dict]:
    """
    Obtiene un servidor por ID usando el registry central.
    
    ORDEN DE CONSULTA:
    1. EDARSAHUB SQL (si prefer_sql=True y USE_SQL_FOR_SERVERS=True)
    2. Sin fallback MongoDB operativo
    
    Args:
        server_id: ID del servidor (UUID)
        db: Ignorado; compatibilidad de firma
        prefer_sql: Consultar SQL primero
        allow_mongo_fallback: Ignorado; MongoDB deshabilitado
        mask_secrets: Enmascarar passwords y api_keys
    
    Returns:
        Dict con datos del servidor o None si no se encuentra
    """
    server = None
    
    # Intentar SQL primero
    if prefer_sql and USE_SQL_FOR_SERVERS:
        server = _get_server_by_id_from_sql(server_id)
    
    # MongoDB fallback deshabilitado por política SQL-only.
    allow_mongo_fallback = False
    
    # Enmascarar secretos si es necesario
    if server and mask_secrets:
        server = mask_sensitive_fields(server)
    
    return server


async def list_servers(
    db=None,
    user: Optional[Dict] = None,
    prefer_sql: bool = True,
    allow_mongo_fallback: bool = False,
    filter_active: bool = True,
    filter_visible_listado: bool = True,
    exclude_core: bool = True,
    mask_secrets: bool = True
) -> List[Dict]:
    """
    Lista servidores usando el registry central.
    
    ORDEN DE CONSULTA:
    1. EDARSAHUB SQL (si prefer_sql=True y USE_SQL_FOR_SERVERS=True)
    2. Sin fallback MongoDB operativo
    
    Args:
        db: Ignorado; compatibilidad de firma
        user: Usuario actual para filtrar por permisos (opcional)
        prefer_sql: Consultar SQL primero
        allow_mongo_fallback: Ignorado; MongoDB deshabilitado
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
    
    # MongoDB fallback deshabilitado por política SQL-only.
    allow_mongo_fallback = False
    
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
    unidad_negocio_pk: Optional[str] = None,
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
        'tipos_movimiento': server.get('tipos_movimiento', []),  # FASE T3.4-B4
        **credentials
    }


# ============================================================================
# SUCURSALES POR SERVIDOR
# ============================================================================

async def get_server_sucursales(
    server_id: str,
    db=None,
    prefer_sql: bool = True,
    allow_mongo_fallback: bool = False
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
        allow_mongo_fallback: Ignorado; MongoDB deshabilitado
    
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
    
    # MongoDB fallback deshabilitado por política SQL-only.
    allow_mongo_fallback = False
    
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
        source: Fuente del registro ("EDARSAHUB_SQL")
    
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
        conn = get_sql_connection()
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
    sync_mongo: bool = False
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
    sync_status = 'SQL_ONLY'
    sync_warnings = []
    sync_mongo = False

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
    sync_mongo: bool = False
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
    
    # P0: Campos JSON de catálogos (requieren serialización)
    json_field_mapping = {
        'tipos_movimiento': 'tipos_movimiento',
        'categorias': 'categorias',
        'departamentos': 'departamentos',
        # P1.4-B: Campos de queries configuradas
        'query_inventario': 'query_inventario',
        'query_ventas': 'query_ventas',
        'query_movimientos': 'query_movimientos'
    }
    
    # P1.4-B: Campo booleano queries_configured
    if 'queries_configured' in payload:
        if 'queries_configured' not in processed_sql_fields:
            update_fields.append("queries_configured = %s")
            update_values.append(1 if payload['queries_configured'] else 0)
            processed_sql_fields.add('queries_configured')
    
    for api_field, sql_field in field_mapping.items():
        if api_field in payload and payload[api_field] is not None:
            # Evitar duplicados (ej: name y nombre mapean a mismo campo)
            if sql_field not in processed_sql_fields:
                update_fields.append(f"{sql_field} = %s")
                update_values.append(payload[api_field])
                processed_sql_fields.add(sql_field)
    
    # P0: Procesar campos JSON de catálogos
    for api_field, sql_field in json_field_mapping.items():
        if api_field in payload:
            value = payload[api_field]
            if sql_field not in processed_sql_fields:
                json_value = _serialize_catalog_field(value, api_field)
                if json_value is not None:  # Solo actualizar si hay valor válido
                    update_fields.append(f"{sql_field} = %s")
                    update_values.append(json_value)
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
    sync_status = 'SQL_ONLY'
    sync_warnings = []
    sync_mongo = False

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
    sync_mongo: bool = False,
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
    sync_status = 'SQL_ONLY'
    sync_warnings = []
    sync_mongo = False

    return {
        'success': True,
        'id': server_id,
        'action': 'soft_delete' if soft_delete else 'hard_delete',
        'config_origin': 'EDARSAHUB_SQL',
        'sync_status': sync_status,
        'warnings': sync_warnings,
        'message': 'Servidor desactivado' if soft_delete else 'Servidor eliminado'
    }




# ============================================================================
# FASE 3B.1: FUNCIONES DE MAPEO Y RECONCILIACIÓN
# ============================================================================

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


# ============================================================================
# FASE M1: FUNCIONES DE UNIDADES DE NEGOCIO (EDARSAHUB-ONLY)
# Agregadas: 13-Mayo-2026
# MÁXIMA: EDARSAHUB es el cerebro del sistema. No usar MongoDB.
# ============================================================================

# Mapeo de compatibilidad defensiva para códigos legacy
# NOTA: Usar valores directos para evitar ciclo de dependencia con UnidadesService
_LEGACY_TO_CANONICAL = {
    '130-MER': '130MID',
    '130-QRO': '130QRO',
    'LA-ESTELAR': 'ESTELAR',
    # Códigos oficiales (identidad)
    '130MID': '130MID',
    '130QRO': '130QRO',
    'CIENFUEGOS': 'CIENFUEGOS',
    'ESTELAR': 'ESTELAR',
    'ORIGEN': 'ORIGEN',
}

# Códigos canónicos oficiales
CODIGOS_CANONICOS_OFICIALES = ['130MID', '130QRO', 'CIENFUEGOS', 'ESTELAR', 'ORIGEN']


def normalize_unidad_codigo(codigo: str) -> str:
    """
    Normaliza un código de unidad de negocio a su forma canónica.
    
    FASE M1: Compatibilidad defensiva para traducir códigos legacy.
    NO debe reinsertar ni promover códigos legacy.
    
    Args:
        codigo: Código de unidad (puede ser legacy o canónico)
    
    Returns:
        Código canónico oficial
    
    Examples:
        normalize_unidad_codigo('130-MER') -> UnidadesService.resolver_codigo('130MID') or '130MID'
        normalize_unidad_codigo('LA-ESTELAR') -> UnidadesService.resolver_codigo('ESTELAR') or 'ESTELAR'
        normalize_unidad_codigo(UnidadesService.resolver_codigo('130MID') or '130MID') -> UnidadesService.resolver_codigo('130MID') or '130MID'
    """
    if not codigo:
        return codigo
    
    codigo_upper = codigo.upper().strip()
    return _LEGACY_TO_CANONICAL.get(codigo_upper, codigo_upper)


def _get_unidades_from_sql(active_only: bool = True) -> List[Dict]:
    """
    Obtiene unidades de negocio desde EDARSAHUB SQL.
    
    FASE M1: Fuente única EDARSAHUB, sin MongoDB.
    
    Args:
        active_only: Solo unidades activas
    
    Returns:
        Lista de unidades de negocio
    """
    try:
        from core.db import execute_sql_query
        
        where_clause = "WHERE activo = 1" if active_only else ""
        
        query = f"""
        SELECT 
            CAST(id AS VARCHAR(50)) as id,
            codigo,
            nombre,
            CAST(server_id AS VARCHAR(50)) as server_id,
            sucursal_origen_id,
            system_type,
            activo,
            orden,
            created_at,
            updated_at
        FROM Unidades_Negocio
        {where_clause}
        ORDER BY orden, codigo
        """
        
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        unidades = []
        for row in results:
            unidades.append({
                'id': str(row.get('id', '')),
                'codigo': row.get('codigo', ''),
                'nombre': row.get('nombre', ''),
                'server_id': str(row.get('server_id', '')),
                'sucursal_origen_id': row.get('sucursal_origen_id'),
                'system_type': row.get('system_type', ''),
                'activo': bool(row.get('activo', False)),
                'orden': row.get('orden', 0),
                'created_at': row.get('created_at'),
                'updated_at': row.get('updated_at'),
                'fuente': 'EDARSAHUB'
            })
        
        logger.info(f"[SERVER_REGISTRY][UNIDADES][SQL_HIT] Obtenidas {len(unidades)} unidades desde EDARSAHUB")
        return unidades
        
    except Exception as e:
        logger.error(f"[SERVER_REGISTRY][UNIDADES][SQL_ERROR] Error obteniendo unidades: {e}")
        return []


def list_unidades_negocio(active_only: bool = True) -> List[Dict]:
    """
    Lista todas las unidades de negocio desde EDARSAHUB.
    
    FASE M1: EDARSAHUB es el cerebro del sistema. No usa MongoDB.
    
    Args:
        active_only: Solo unidades activas (default True)
    
    Returns:
        Lista de unidades de negocio con campos:
        - codigo: Código canónico oficial
        - nombre: Nombre de la unidad
        - server_id: ID del servidor asociado
        - sucursal_origen_id: Sucursal para MPRO (0021, 0023)
        - system_type: SoftRestaurant o MPRO
        - activo: Estado activo
        - orden: Orden de visualización
        - fuente: "EDARSAHUB"
    
    Example:
        >>> unidades = list_unidades_negocio()
        >>> len(unidades)
        5
        >>> unidades[0]['codigo']
        UnidadesService.resolver_codigo('130MID') or '130MID'
    """
    return _get_unidades_from_sql(active_only=active_only)


def get_server_by_unidad_codigo(codigo: str) -> Optional[Dict]:
    """
    Obtiene la configuración completa de servidor por código de unidad.
    
    FASE M1: Resuelve servidor usando Unidades_Negocio.codigo como llave.
    
    Args:
        codigo: Código de unidad (se normaliza automáticamente)
    
    Returns:
        Dict con configuración de servidor y unidad, o None si no existe
    
    Example:
        >>> server = get_server_by_unidad_codigo(UnidadesService.resolver_codigo('130MID') or '130MID')
        >>> server['unidad_negocio_codigo']
        UnidadesService.resolver_codigo('130MID') or '130MID'
        >>> server['host']
        'servidor-pos-ejemplo.local'
    """
    if not codigo:
        return None
    
    # Normalizar código defensivamente
    codigo_normalizado = normalize_unidad_codigo(codigo)
    
    try:
        from core.db import execute_sql_query
        
        # Escapar para SQL
        safe_codigo = codigo_normalizado.replace("'", "''")
        
        query = f"""
        SELECT 
            u.codigo as unidad_negocio_codigo,
            u.nombre as unidad_negocio_nombre,
            CAST(u.id AS VARCHAR(50)) as unidad_negocio_pk,
            CAST(u.server_id AS VARCHAR(50)) as server_id,
            u.sucursal_origen_id,
            u.system_type as unidad_system_type,
            u.activo as unidad_activo,
            u.orden,
            s.nombre as servidor_nombre,
            s.host,
            s.port,
            s.database_name,
            s.username,
            s.system_type as servidor_system_type,
            s.activo as servidor_activo,
            s.visible_en_operaciones,
            s.empresa_id
        FROM Unidades_Negocio u
        LEFT JOIN Servidores_Conexiones s ON CAST(u.server_id AS uniqueidentifier) = s.id
        WHERE u.codigo = '{safe_codigo}'
          AND u.activo = 1
        """
        
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        
        if not results:
            logger.warning(f"[SERVER_REGISTRY][UNIDADES] Código {codigo_normalizado} no encontrado")
            return None
        
        row = results[0]
        
        server_config = {
            'unidad_negocio_codigo': row.get('unidad_negocio_codigo'),
            'unidad_negocio_nombre': row.get('unidad_negocio_nombre'),
            'unidad_negocio_pk': str(row.get('unidad_negocio_pk', '')),
            'server_id': str(row.get('server_id', '')),
            'sucursal_origen_id': row.get('sucursal_origen_id'),
            'system_type': row.get('unidad_system_type'),
            'orden': row.get('orden'),
            # Datos del servidor
            'servidor_nombre': row.get('servidor_nombre'),
            'host': row.get('host'),
            'port': row.get('port', 1433),
            'database': row.get('database_name'),
            'username': row.get('username'),
            'servidor_system_type': row.get('servidor_system_type'),
            'servidor_activo': bool(row.get('servidor_activo', False)),
            'visible_en_operaciones': bool(row.get('visible_en_operaciones', False)),
            'empresa_id': row.get('empresa_id'),
            # Metadata
            'fuente': 'EDARSAHUB',
            'config_origin': 'EDARSAHUB_SQL'
        }
        
        logger.info(f"[SERVER_REGISTRY][UNIDADES][SQL_HIT] Servidor resuelto para {codigo_normalizado}")
        return server_config
        
    except Exception as e:
        logger.error(f"[SERVER_REGISTRY][UNIDADES][SQL_ERROR] Error obteniendo servidor por código {codigo}: {e}")
        return None


def resolve_unidad_by_server_sucursal(server_id: str, sucursal_id: Optional[str] = None) -> Optional[Dict]:
    """
    Resuelve la unidad de negocio por server_id y sucursal_id.
    
    FASE M1: Crítico para MPRO donde múltiples unidades comparten servidor.
    
    Args:
        server_id: ID del servidor
        sucursal_id: ID de sucursal (requerido para MPRO)
    
    Returns:
        Dict con datos de la unidad o None si no se encuentra
    
    Examples:
        # SoftRestaurant (sin sucursal)
        >>> resolve_unidad_by_server_sucursal('a5547321-...')
        {'codigo': UnidadesService.resolver_codigo('130MID') or '130MID', ...}
        
        # MPRO con sucursal 0021
        >>> resolve_unidad_by_server_sucursal('1b230a06-...', '0021')
        {'codigo': UnidadesService.resolver_codigo('130QRO') or '130QRO', ...}
        
        # MPRO con sucursal 0023
        >>> resolve_unidad_by_server_sucursal('1b230a06-...', '0023')
        {'codigo': UnidadesService.resolver_codigo('ORIGEN') or 'ORIGEN', ...}
    """
    if not server_id:
        return None
    
    try:
        from core.db import execute_sql_query
        
        # Escapar para SQL
        safe_server_id = server_id.replace("'", "''")
        
        # Si hay sucursal, buscar coincidencia exacta
        if sucursal_id:
            safe_sucursal = sucursal_id.replace("'", "''")
            query = f"""
            SELECT 
                CAST(id AS VARCHAR(50)) as id,
                codigo,
                nombre,
                CAST(server_id AS VARCHAR(50)) as server_id,
                sucursal_origen_id,
                system_type,
                activo,
                orden
            FROM Unidades_Negocio
            WHERE (CAST(server_id AS VARCHAR(50)) = '{safe_server_id}' 
                   OR server_id = '{safe_server_id}')
              AND sucursal_origen_id = '{safe_sucursal}'
              AND activo = 1
            """
        else:
            # Sin sucursal, buscar por server_id donde sucursal sea null (SoftRestaurant)
            query = f"""
            SELECT 
                CAST(id AS VARCHAR(50)) as id,
                codigo,
                nombre,
                CAST(server_id AS VARCHAR(50)) as server_id,
                sucursal_origen_id,
                system_type,
                activo,
                orden
            FROM Unidades_Negocio
            WHERE (CAST(server_id AS VARCHAR(50)) = '{safe_server_id}' 
                   OR server_id = '{safe_server_id}')
              AND (sucursal_origen_id IS NULL OR sucursal_origen_id = '')
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
        
        if not results:
            # Si no encontró con sucursal null, intentar sin ese filtro
            if not sucursal_id:
                query_fallback = f"""
                SELECT 
                    CAST(id AS VARCHAR(50)) as id,
                    codigo,
                    nombre,
                    CAST(server_id AS VARCHAR(50)) as server_id,
                    sucursal_origen_id,
                    system_type,
                    activo,
                    orden
                FROM Unidades_Negocio
                WHERE (CAST(server_id AS VARCHAR(50)) = '{safe_server_id}' 
                       OR server_id = '{safe_server_id}')
                  AND activo = 1
                ORDER BY orden
                """
                results = execute_sql_query(
                    EDARSAHUB_CONFIG['host'],
                    EDARSAHUB_CONFIG['port'],
                    EDARSAHUB_CONFIG['database'],
                    EDARSAHUB_CONFIG['username'],
                    EDARSAHUB_CONFIG['password'],
                    query_fallback
                )
        
        if not results:
            logger.warning(f"[SERVER_REGISTRY][RESOLVE] No se encontró unidad para server={server_id}, sucursal={sucursal_id}")
            return None
        
        row = results[0]
        
        unidad = {
            'id': str(row.get('id', '')),
            'codigo': row.get('codigo', ''),
            'nombre': row.get('nombre', ''),
            'server_id': str(row.get('server_id', '')),
            'sucursal_origen_id': row.get('sucursal_origen_id'),
            'system_type': row.get('system_type', ''),
            'activo': bool(row.get('activo', False)),
            'orden': row.get('orden', 0),
            'fuente': 'EDARSAHUB'
        }
        
        logger.info(f"[SERVER_REGISTRY][RESOLVE][SQL_HIT] Unidad {unidad['codigo']} resuelta para server={server_id}, sucursal={sucursal_id}")
        return unidad
        
    except Exception as e:
        logger.error(f"[SERVER_REGISTRY][RESOLVE][SQL_ERROR] Error resolviendo unidad: {e}")
        return None


def validate_registry_integrity() -> Dict:
    """
    Valida la integridad del registro de unidades y servidores.
    
    FASE M1: Verificación de consistencia EDARSAHUB.
    
    Validaciones:
    - Existen las 5 unidades oficiales
    - No hay códigos legacy activos
    - Cada unidad tiene server_id
    - MPRO tiene sucursal_origen_id correcta (130QRO=0021, ORIGEN=0023)
    - No hay códigos duplicados activos
    - Servidores asociados existen
    
    Returns:
        Dict con:
        - ok: bool
        - errors: list
        - warnings: list
        - unidades_detectadas: list
        - fuente: "EDARSAHUB"
    
    Example:
        >>> result = validate_registry_integrity()
        >>> result['ok']
        True
        >>> len(result['unidades_detectadas'])
        5
    """
    result = {
        'ok': True,
        'errors': [],
        'warnings': [],
        'unidades_detectadas': [],
        'servidores_asociados': [],
        'fuente': 'EDARSAHUB',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    try:
        # Obtener todas las unidades activas
        unidades = _get_unidades_from_sql(active_only=True)
        result['unidades_detectadas'] = [u['codigo'] for u in unidades]
        
        # 1. Verificar que existen las 5 unidades oficiales
        for codigo_oficial in CODIGOS_CANONICOS_OFICIALES:
            if codigo_oficial not in result['unidades_detectadas']:
                result['errors'].append(f"Unidad oficial faltante: {codigo_oficial}")
                result['ok'] = False
        
        # 2. Verificar que no hay códigos legacy activos
        codigos_legacy = ['130-MER', '130-QRO', 'LA-ESTELAR']
        for codigo_legacy in codigos_legacy:
            if codigo_legacy in result['unidades_detectadas']:
                result['errors'].append(f"Código legacy activo detectado: {codigo_legacy}")
                result['ok'] = False
        
        # 3. Verificar que cada unidad tiene server_id
        for u in unidades:
            if not u.get('server_id'):
                result['errors'].append(f"Unidad {u['codigo']} sin server_id")
                result['ok'] = False
        
        # 4. Verificar sucursales MPRO
        for u in unidades:
            if u['codigo'] == '130QRO' and u.get('sucursal_origen_id') != '0021':
                result['errors'].append(f"130QRO debe tener sucursal_origen_id='0021', tiene '{u.get('sucursal_origen_id')}'")
                result['ok'] = False
            
            if u['codigo'] == 'ORIGEN' and u.get('sucursal_origen_id') != '0023':
                result['errors'].append(f"ORIGEN debe tener sucursal_origen_id='0023', tiene '{u.get('sucursal_origen_id')}'")
                result['ok'] = False
        
        # 5. Verificar duplicados
        codigos_count = {}
        for u in unidades:
            codigo = u['codigo']
            codigos_count[codigo] = codigos_count.get(codigo, 0) + 1
        
        for codigo, count in codigos_count.items():
            if count > 1:
                result['errors'].append(f"Código duplicado: {codigo} ({count} veces)")
                result['ok'] = False
        
        # 6. Verificar que los servidores asociados existen
        server_ids = set(u['server_id'] for u in unidades if u.get('server_id'))
        
        for server_id in server_ids:
            server = _get_server_by_id_from_sql(server_id)
            if server:
                result['servidores_asociados'].append({
                    'id': server_id,
                    'nombre': server.get('name', 'N/A'),
                    'activo': server.get('active', False)
                })
                if not server.get('active'):
                    result['warnings'].append(f"Servidor {server_id} ({server.get('name')}) está inactivo")
            else:
                result['errors'].append(f"Servidor no encontrado: {server_id}")
                result['ok'] = False
        
        # Resumen
        if result['ok']:
            logger.info(f"[SERVER_REGISTRY][INTEGRITY] Validación exitosa: {len(unidades)} unidades, {len(server_ids)} servidores")
        else:
            logger.warning(f"[SERVER_REGISTRY][INTEGRITY] Validación fallida: {len(result['errors'])} errores")
        
    except Exception as e:
        result['ok'] = False
        result['errors'].append(f"Error ejecutando validación: {str(e)}")
        logger.error(f"[SERVER_REGISTRY][INTEGRITY][ERROR] {e}")
    
    return result


# ============================================================================
# FASE M1: WRAPPERS MÍNIMOS (Opcionales)
# ============================================================================

def list_operational_servers(system_type_filter: str = None) -> List[Dict]:
    """
    Lista servidores operacionales activos desde EDARSAHUB.
    
    Wrapper sobre _get_servers_from_sql.
    
    Args:
        system_type_filter: Opcional. Filtra por system_type (ej: 'SoftRestaurant', 'MPRO')
    """
    servers = _get_servers_from_sql(filter_active=True, filter_visible_listado=False, exclude_core=True)
    
    if system_type_filter:
        filter_upper = system_type_filter.upper()
        servers = [s for s in servers if filter_upper in (s.get('system_type', '') or '').upper()]
    
    return servers


def get_visible_servers_for_operaciones() -> List[Dict]:
    """
    Lista servidores visibles en módulo de operaciones.
    
    Filtra por visible_en_operaciones=True.
    """
    servers = _get_servers_from_sql(filter_active=True, filter_visible_listado=False, exclude_core=True)
    return [s for s in servers if s.get('visible_en_operaciones', False)]


def get_connection_config(server_id: str) -> Optional[Dict]:
    """
    Obtiene configuración de conexión de un servidor.
    
    Wrapper sobre _get_server_by_id_from_sql con solo datos de conexión.
    """
    server = _get_server_by_id_from_sql(server_id)
    if not server:
        return None
    
    return {
        'id': server.get('id'),
        'name': server.get('name'),
        'host': server.get('host'),
        'port': server.get('port', 1433),
        'database': server.get('database'),
        'username': server.get('username'),
        'system_type': server.get('system_type'),
        'system_type_normalized': server.get('system_type_normalized'),
        'config_origin': 'EDARSAHUB_SQL'
    }


def get_server_connection_info_with_secrets(server_id: str) -> Optional[Dict]:
    """
    USO INTERNO BACKEND - Obtiene configuración completa de conexión incluyendo credenciales.
    
    FASE P1.3 (Dic 2025): Función pública controlada para casos de uso internos
    que requieren ejecutar conexiones SQL (ej: Universal Query, sincronización).
    
    FUENTE: EDARSAHUB.dbo.Servidores_Conexiones
    NO FUENTE: MongoDB db.servers
    
    SEGURIDAD:
    - NO exponer como endpoint público
    - NO imprimir password en logs
    - NO devolver password al frontend
    - Solo usar internamente para ejecutar conexión SQL
    
    Returns:
        Dict con campos compatibles con decrypt_server_secrets():
        - id, mongodb_id, name, system_type
        - host, port, database, username, password
        - active
        O None si no existe
    """
    server = _get_server_by_id_from_sql(server_id)
    if not server:
        logger.debug(f"[SERVER_REGISTRY] Servidor {server_id} no encontrado para conexión")
        return None
    
    # Retornar estructura completa compatible con decrypt_server_secrets()
    return {
        'id': server.get('id'),
        'mongodb_id': server.get('mongodb_id'),
        'name': server.get('name'),
        'system_type': server.get('system_type'),
        'system_type_normalized': server.get('system_type_normalized'),
        'host': server.get('host'),
        'port': server.get('port', 1433),
        'database': server.get('database'),
        'username': server.get('username'),
        'password': server.get('password'),  # password_encrypted desde SQL
        'api_key': server.get('api_key'),    # api_key_encrypted desde SQL
        'active': server.get('active', False),
        # FIX 2026-06: incluir metadata de configuración de consultas (antes se
        # omitía → el Dashboard de Métricas descartaba servidores YA configurados
        # con el mensaje "No hay servidores configurados con consultas SQL").
        'queries_configured': server.get('queries_configured', False),
        'departamentos': server.get('departamentos', []),
        'categorias': server.get('categorias', []),
        'visible_en_operaciones': server.get('visible_en_operaciones', True),
        'config_origin': 'EDARSAHUB_SQL'
    }


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
    'validate_server_payload',
    # FASE 3B.1: Mapeo y reconciliación
        'map_sql_to_api_server_response',
        # FASE M1: Unidades de Negocio (EDARSAHUB-ONLY)
    'list_unidades_negocio',
    'get_server_by_unidad_codigo',
    'resolve_unidad_by_server_sucursal',
    'normalize_unidad_codigo',
    'validate_registry_integrity',
    'list_operational_servers',
    'get_visible_servers_for_operaciones',
    'get_connection_config',
    # FASE P1.3: Conexión con secretos para uso interno backend
    'get_server_connection_info_with_secrets',
    'CODIGOS_CANONICOS_OFICIALES',
    # Config
    'USE_SQL_FOR_SERVERS',
    'EDARSAHUB_CONFIG'
]

