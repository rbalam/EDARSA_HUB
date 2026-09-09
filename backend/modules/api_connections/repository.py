from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Repositorio de Conexiones API Locales
=====================================
ARQUITECTURA:
- Fuente primaria de verdad: EDARSAHUB SQL (tabla Servidores_Conexiones)
- MongoDB: Solo caché/log/estado auxiliar (NO autoritativo)
- Sincronización: EDARSAHUB SQL → MongoDB (nunca al revés)

REGLAS:
1. Toda escritura va primero a EDARSAHUB SQL
2. Si EDARSAHUB SQL falla, NO se guarda en MongoDB
3. Si MongoDB falla después de EDARSAHUB SQL, la operación es exitosa
4. Toda operación se registra en Servidores_Conexiones_Log
5. Se respetan usuarios, roles y alcance por empresa/sucursal
"""

import logging
import os
import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from core.db import execute_sql_query

# Configuración de EDARSAHUB SQL - FUENTE PRIMARIA
EDARSAHUB_CONFIG = {
    'host': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
}

# Referencia a MongoDB (solo para caché, NO autoritativo)
_db = None


def init_api_connections_repository(database) -> None:
    """Inicializa el repositorio con la conexión a MongoDB (solo caché)."""
    global _db
    _db = database
    logging.info("[API_CONNECTIONS] Repositorio inicializado - Fuente primaria: EDARSAHUB SQL")


def _escape_sql(value: str) -> str:
    """Escapa caracteres especiales para SQL."""
    if value is None:
        return ''
    return str(value).replace("'", "''")


def _log_operation(servidor_id: str, accion: str, datos_anteriores: Dict, datos_nuevos: Dict, usuario: str) -> bool:
    """
    Registra operación en la bitácora Servidores_Conexiones_Log.
    Retorna True si el log fue exitoso.
    """
    try:
        datos_ant_json = json.dumps(datos_anteriores or {}, default=str)
        datos_new_json = json.dumps(datos_nuevos or {}, default=str)
        
        query = f"""
        INSERT INTO Servidores_Conexiones_Log 
        (servidor_id, accion, datos_anteriores, datos_nuevos, usuario, fecha, ip_origen)
        VALUES (
            '{servidor_id}',
            N'{_escape_sql(accion)}',
            N'{_escape_sql(datos_ant_json)}',
            N'{_escape_sql(datos_new_json)}',
            N'{_escape_sql(usuario)}',
            GETDATE(),
            N'API_SERVER'
        )
        """
        execute_sql_query(
            EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'], EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'], query
        )
        logging.info(f"[API_CONNECTIONS][LOG] {accion} para {servidor_id} por {usuario}")
        return True
    except Exception as e:
        logging.error(f"[API_CONNECTIONS][LOG_ERROR] Error registrando bitácora: {e}")
        return False


def _sql_row_to_api_dict(row: Dict) -> Dict:
    """
    Convierte una fila de Servidores_Conexiones (tipo API_LOCAL) al formato de respuesta.
    """
    # Descifrar API key si está cifrada
    api_key_encrypted = row.get('api_key_encrypted', '')
    api_key_decrypted = ''
    if api_key_encrypted:
        try:
            from core.secret_manager import decrypt_secret, is_encrypted_secret
            if is_encrypted_secret(api_key_encrypted):
                api_key_decrypted = decrypt_secret(api_key_encrypted)
            else:
                api_key_decrypted = api_key_encrypted
        except Exception as e:
            logging.warning(f"[API_CONNECTIONS] Error descifrando API key: {e}")
            api_key_decrypted = ''  # No exponer el valor cifrado
    
    # Parsear campos JSON
    def parse_json(val):
        if val is None:
            return None
        if isinstance(val, (list, dict)):
            return val
        try:
            return json.loads(val) if val else None
        except Exception:
            return None
    
    # API-SEC1: NO exponer api_key descifrada en el listado
    # Solo indicar si existe o no
    api_key_masked = '***CONFIGURED***' if api_key_decrypted else ''
    
    return {
        'id': str(row.get('id', '')),
        'name': row.get('nombre', ''),
        'url': row.get('api_url', ''),
        'api_key': api_key_masked,  # API-SEC1: Enmascarado por seguridad
        'tipo': row.get('system_type', 'MPRO'),
        'tipo_conexion': row.get('tipo_conexion', 'API_LOCAL'),
        'servidor_padre': row.get('host', ''),
        'servidor_padre_id': row.get('empresa_id', ''),
        'sucursal_destino': row.get('database_name', ''),
        'hora_replica': row.get('port', 4),  # Reutilizado para hora de réplica
        'solo_ventas_dia': bool(row.get('queries_configured', True)),
        'activo': bool(row.get('activo', True)),
        'visible_en_operaciones': bool(row.get('visible_en_operaciones', False)),
        'config': parse_json(row.get('sucursales')),
        'created_at': row.get('created_at'),
        'updated_at': row.get('updated_at'),
        'created_by': row.get('created_by'),
        'updated_by': row.get('updated_by'),
        'source': 'EDARSAHUB_SQL'
    }


# ============================================================================
# LECTURA - SIEMPRE DESDE EDARSAHUB SQL
# ============================================================================

def list_api_connections_sql(include_inactive: bool = False) -> List[Dict]:
    """
    Lista conexiones API desde EDARSAHUB SQL (fuente primaria).
    """
    try:
        where_clause = "WHERE tipo_conexion = 'API_LOCAL'"
        if not include_inactive:
            where_clause += " AND activo = 1"
        
        query = f"""
        SELECT * FROM Servidores_Conexiones
        {where_clause}
        ORDER BY nombre
        """
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'], EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'], query
        )
        apis = [_sql_row_to_api_dict(row) for row in results]
        logging.info(f"[API_CONNECTIONS] Listadas {len(apis)} conexiones desde EDARSAHUB SQL")
        return apis
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error listando desde SQL: {e}")
        raise RuntimeError(f"Error accediendo a EDARSAHUB SQL: {e}")


async def list_api_connections(include_inactive: bool = False) -> List[Dict]:
    """
    Lista todas las conexiones API.
    FUENTE: EDARSAHUB SQL (primaria y única autoritativa).
    """
    return list_api_connections_sql(include_inactive)


def get_api_connection_sql(api_id: str) -> Optional[Dict]:
    """
    Obtiene una conexión API por ID desde EDARSAHUB SQL.
    """
    try:
        query = f"""
        SELECT * FROM Servidores_Conexiones
        WHERE id = '{_escape_sql(api_id)}'
          AND tipo_conexion = 'API_LOCAL'
        """
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'], EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'], query
        )
        if results:
            return _sql_row_to_api_dict(results[0])
        return None
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error obteniendo {api_id} desde SQL: {e}")
        raise RuntimeError(f"Error accediendo a EDARSAHUB SQL: {e}")


async def get_api_connection(api_id: str) -> Optional[Dict]:
    """
    Obtiene una conexión API por ID.
    FUENTE: EDARSAHUB SQL.
    """
    return get_api_connection_sql(api_id)


def check_duplicate_api(name: str, url: str, exclude_id: str = None) -> Optional[Dict]:
    """
    Verifica si ya existe una conexión API con el mismo nombre o URL.
    Retorna la conexión duplicada si existe.
    """
    try:
        exclude_clause = f"AND id != '{_escape_sql(exclude_id)}'" if exclude_id else ""
        query = f"""
        SELECT id, nombre, api_url FROM Servidores_Conexiones
        WHERE tipo_conexion = 'API_LOCAL'
          AND (nombre = N'{_escape_sql(name)}' OR api_url = N'{_escape_sql(url)}')
          {exclude_clause}
        """
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'], EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'], query
        )
        if results:
            return results[0]
        return None
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error verificando duplicados: {e}")
        return None


# ============================================================================
# ESCRITURA - EDARSAHUB SQL COMO FUENTE UNICA
# ============================================================================

async def create_api_connection(data: Dict, created_by: str = "system") -> Dict:
    """
    Crea una nueva conexión API.
    
    FLUJO:
    1. Verificar duplicados en EDARSAHUB SQL
    2. Cifrar API key
    3. INSERT en EDARSAHUB SQL
    4. Registrar en bitácora
    5. Finalizar operación en EDARSAHUB SQL
    
    Si EDARSAHUB SQL falla, NO se guarda nada.
    """
    # 1. Verificar duplicados
    duplicate = check_duplicate_api(data.get('name', ''), data.get('url', ''))
    if duplicate:
        raise ValueError(f"Ya existe una conexión con nombre '{duplicate.get('nombre')}' o URL similar")
    
    # 2. Generar ID y cifrar API key
    api_id = str(uuid.uuid4())
    api_key = data.get('api_key', '')
    api_key_encrypted = api_key
    try:
        from core.secret_manager import encrypt_secret
        if api_key:
            api_key_encrypted = encrypt_secret(api_key)
    except Exception as e:
        logging.warning(f"[API_CONNECTIONS] No se pudo cifrar API key: {e}")
    
    # 3. Preparar datos
    hora_replica = data.get('hora_replica', '04:00')
    if isinstance(hora_replica, str):
        try:
            hora_replica = int(hora_replica.split(':')[0])
        except Exception:
            hora_replica = 4
    
    config_json = json.dumps(data.get('config') or {})
    
    # 4. INSERT en EDARSAHUB SQL
    insert_query = f"""
    INSERT INTO Servidores_Conexiones (
        id, nombre, system_type, tipo_conexion, host, port, database_name,
        api_url, api_key_encrypted, activo, visible_en_operaciones,
        visible_en_listado, es_editable_ui, es_eliminable_ui,
        EmpresaID, sucursales, queries_configured,
        created_at, updated_at, created_by
    ) VALUES (
        '{api_id}',
        N'{_escape_sql(data.get("name", ""))}',
        N'{_escape_sql(data.get("tipo", "MPRO"))}',
        'API_LOCAL',
        N'{_escape_sql(data.get("servidor_padre", ""))}',
        {hora_replica},
        N'{_escape_sql(data.get("sucursal_destino", ""))}',
        N'{_escape_sql(data.get("url", ""))}',
        N'{_escape_sql(api_key_encrypted)}',
        {1 if data.get("activo", True) else 0},
        {1 if data.get("visible_en_operaciones", False) else 0},
        1, 1, 1,
        N'{_escape_sql(data.get("servidor_padre_id", ""))}',
        N'{_escape_sql(config_json)}',
        {1 if data.get("solo_ventas_dia", True) else 0},
        GETDATE(), GETDATE(),
        N'{_escape_sql(created_by)}'
    )
    """
    
    try:
        execute_sql_query(
            EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'], EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'], insert_query
        )
        logging.info(f"[API_CONNECTIONS] Conexión {api_id} creada en EDARSAHUB SQL")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error INSERT en SQL: {e}")
        raise RuntimeError(f"Error guardando en EDARSAHUB SQL: {e}")
    
    # 5. Registrar en bitácora
    _log_operation(api_id, 'CREATE', None, data, created_by)
    
    # 6. Sin persistencia secundaria: SQL es fuente única
    
    # 7. Retornar datos guardados
    return get_api_connection_sql(api_id)


async def update_api_connection(api_id: str, data: Dict, updated_by: str = "system") -> Optional[Dict]:
    """
    Actualiza una conexión API existente.
    
    FLUJO:
    1. Verificar que existe en EDARSAHUB SQL
    2. Verificar duplicados (si cambia nombre/URL)
    3. Cifrar API key si se proporciona
    4. UPDATE en EDARSAHUB SQL
    5. Registrar en bitácora
    6. Finalizar operación en EDARSAHUB SQL
    """
    # 1. Verificar que existe
    existing = get_api_connection_sql(api_id)
    if not existing:
        raise ValueError(f"Conexión API {api_id} no encontrada")
    
    # 2. Verificar duplicados si cambia nombre o URL
    new_name = data.get('name', existing['name'])
    new_url = data.get('url', existing['url'])
    if new_name != existing['name'] or new_url != existing['url']:
        duplicate = check_duplicate_api(new_name, new_url, exclude_id=api_id)
        if duplicate:
            raise ValueError(f"Ya existe una conexión con nombre o URL similar")
    
    # 3. Cifrar API key si se proporciona
    api_key_encrypted = None
    if 'api_key' in data and data['api_key']:
        try:
            from core.secret_manager import encrypt_secret
            api_key_encrypted = encrypt_secret(data['api_key'])
        except Exception:
            api_key_encrypted = data['api_key']
    
    # 4. Construir UPDATE dinámico
    set_parts = []
    if 'name' in data:
        set_parts.append(f"nombre = N'{_escape_sql(data['name'])}'")
    if 'url' in data:
        set_parts.append(f"api_url = N'{_escape_sql(data['url'])}'")
    if api_key_encrypted:
        set_parts.append(f"api_key_encrypted = N'{_escape_sql(api_key_encrypted)}'")
    if 'tipo' in data:
        set_parts.append(f"system_type = N'{_escape_sql(data['tipo'])}'")
    if 'servidor_padre' in data:
        set_parts.append(f"host = N'{_escape_sql(data['servidor_padre'])}'")
    if 'servidor_padre_id' in data:
        set_parts.append(f"empresa_id = N'{_escape_sql(data['servidor_padre_id'])}'")
    if 'sucursal_destino' in data:
        set_parts.append(f"database_name = N'{_escape_sql(data['sucursal_destino'])}'")
    if 'hora_replica' in data:
        hr = data['hora_replica']
        hr_int = int(hr.split(':')[0]) if isinstance(hr, str) else hr
        set_parts.append(f"port = {hr_int}")
    if 'solo_ventas_dia' in data:
        set_parts.append(f"queries_configured = {1 if data['solo_ventas_dia'] else 0}")
    if 'activo' in data:
        set_parts.append(f"activo = {1 if data['activo'] else 0}")
    if 'visible_en_operaciones' in data:
        set_parts.append(f"visible_en_operaciones = {1 if data['visible_en_operaciones'] else 0}")
    if 'config' in data:
        config_json = json.dumps(data['config'] or {})
        set_parts.append(f"sucursales = N'{_escape_sql(config_json)}'")
    
    set_parts.append("updated_at = GETDATE()")
    set_parts.append(f"updated_by = N'{_escape_sql(updated_by)}'")
    
    # 5. UPDATE en EDARSAHUB SQL
    update_query = f"""
    UPDATE Servidores_Conexiones
    SET {', '.join(set_parts)}
    WHERE id = '{_escape_sql(api_id)}'
    """
    
    try:
        execute_sql_query(
            EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'], EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'], update_query
        )
        logging.info(f"[API_CONNECTIONS] Conexión {api_id} actualizada en EDARSAHUB SQL")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error UPDATE en SQL: {e}")
        raise RuntimeError(f"Error actualizando en EDARSAHUB SQL: {e}")
    
    # 6. Registrar en bitácora
    _log_operation(api_id, 'UPDATE', existing, data, updated_by)
    
    # 7. Sin persistencia secundaria: SQL es fuente única
    
    return get_api_connection_sql(api_id)


async def delete_api_connection(api_id: str, deleted_by: str = "system") -> bool:
    """
    Elimina (soft delete) una conexión API.
    
    FLUJO:
    1. Verificar que existe en EDARSAHUB SQL
    2. Soft delete en EDARSAHUB SQL (activo = 0)
    3. Registrar en bitácora
    4. Eliminar de caché MongoDB
    """
    # 1. Verificar que existe
    existing = get_api_connection_sql(api_id)
    if not existing:
        raise ValueError(f"Conexión API {api_id} no encontrada")
    
    # 2. Soft delete en EDARSAHUB SQL
    delete_query = f"""
    UPDATE Servidores_Conexiones
    SET activo = 0, updated_at = GETDATE(), updated_by = N'{_escape_sql(deleted_by)}'
    WHERE id = '{_escape_sql(api_id)}'
    """
    
    try:
        execute_sql_query(
            EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'], EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'], delete_query
        )
        logging.info(f"[API_CONNECTIONS] Conexión {api_id} eliminada (soft) en EDARSAHUB SQL")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error DELETE en SQL: {e}")
        raise RuntimeError(f"Error eliminando en EDARSAHUB SQL: {e}")
    
    # 3. Registrar en bitácora
    _log_operation(api_id, 'DELETE', existing, {'activo': False}, deleted_by)
    
    return True


# ============================================================================
# COMPATIBILIDAD PUBLICA LEGACY SQL-ONLY
# ============================================================================



async def sync_all_to_mongo_cache() -> Dict:
    """
    Compatibilidad pública legacy para /api-connections/sync-cache.

    EDARSAHUB SQL es la única fuente canónica.
    No existe caché ni sincronización secundaria MongoDB.
    Esta función valida las conexiones activas presentes en SQL
    sin realizar IO adicional.
    """
    try:
        apis = list_api_connections_sql(
            include_inactive=False
        )
        total = len(apis)

        return {
            "synced": total,
            "errors": 0,
            "total": total,
        }

    except Exception as e:
        logging.error(
            "[API_CONNECTIONS] Error consultando "
            f"conexiones SQL: {e}"
        )
        raise RuntimeError(
            f"Error consultando conexiones API: {e}"
        )


# ============================================================================
# PRUEBA DE CONEXIÓN
# ============================================================================

async def test_api_connection_health(api_id: str = None, url: str = None, api_key: str = None) -> Dict:
    """
    Prueba la conexión a una API local.
    Devuelve el resultado de salud sin persistencia MongoDB.
    """
    import requests
    
    # Si se proporciona api_id, obtener config desde EDARSAHUB SQL
    if api_id:
        api = get_api_connection_sql(api_id)
        if not api:
            return {"success": False, "error": "API no encontrada en EDARSAHUB SQL"}
        url = api.get('url')
        api_key = api.get('api_key')
    
    if not url:
        return {"success": False, "error": "URL no proporcionada"}
    
    result = {}
    try:
        headers = {"x-api-key": api_key} if api_key else {}
        response = requests.get(
            url,
            headers=headers,
            params={"sql": "SELECT 1 as test"},
            timeout=5
        )
        
        if response.status_code == 200:
            result = {
                "success": True,
                "status_code": 200,
                "message": "Conexión exitosa",
                "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
            }
        else:
            result = {
                "success": False,
                "status_code": response.status_code,
                "error": f"HTTP {response.status_code}"
            }
    except requests.exceptions.Timeout:
        result = {"success": False, "error": "Timeout (5s)"}
    except requests.exceptions.ConnectionError:
        result = {"success": False, "error": "Sin conexión"}
    except Exception as e:
        result = {"success": False, "error": str(e)}

    # Gate 5C: solo una prueba asociada a ConexionID canonico persiste health.
    # Las pruebas ad-hoc por URL siguen siendo efimeras y no fabrican identidad.
    if api_id:
        try:
            from modules.integrations_runtime.health import persist_connection_health
            persist_connection_health(
                api_id,
                success=bool(result.get("success")),
                latency_ms=result.get("response_time_ms"),
                error_code=None if result.get("success") else (
                    f"HTTP_{result.get('status_code')}" if result.get("status_code") else "API_CONNECTION_ERROR"
                ),
                error_message=None if result.get("success") else result.get("error"),
            )
            result["health_persisted"] = True
        except Exception as health_exc:
            logging.error(
                "[API_CONNECTIONS][HEALTH] No se pudo persistir health: %s",
                type(health_exc).__name__,
            )
            result["health_persisted"] = False

    return result


# ============================================================================
# TEST QUERY - EJECUCIÓN DE CONSULTAS SQL CONTROLADAS
# ============================================================================

def get_api_connection_with_decrypted_key(api_id: str) -> Optional[Dict]:
    """
    Obtiene una conexión API con la API key descifrada.
    SOLO PARA USO INTERNO EN TEST-QUERY.
    NUNCA exponer en responses de API.
    """
    try:
        query = f"""
        SELECT * FROM Servidores_Conexiones
        WHERE id = '{_escape_sql(api_id)}'
          AND tipo_conexion = 'API_LOCAL'
        """
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'], EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'], query
        )
        if not results:
            return None
        
        row = results[0]
        
        # Descifrar API key
        api_key_encrypted = row.get('api_key_encrypted', '')
        api_key_decrypted = ''
        if api_key_encrypted:
            try:
                from core.secret_manager import decrypt_secret, is_encrypted_secret
                if is_encrypted_secret(api_key_encrypted):
                    api_key_decrypted = decrypt_secret(api_key_encrypted)
                else:
                    api_key_decrypted = api_key_encrypted
            except Exception as e:
                logging.warning(f"[API_CONNECTIONS] Error descifrando API key: {e}")
                return None
        
        return {
            'id': str(row.get('id', '')),
            'name': row.get('nombre', ''),
            'url': row.get('api_url', ''),
            'api_key_decrypted': api_key_decrypted,  # SOLO USO INTERNO
            'tipo': row.get('system_type', 'MPRO'),
            'activo': bool(row.get('activo', True)),
        }
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error obteniendo conexión con key: {e}")
        return None


async def get_api_connection_by_id_full(api_id: str) -> Optional[Dict]:
    """
    Obtiene una conexión API_LOCAL completa por ID.
    
    CORRECCIÓN P1 (2026-05-15): Para uso del Explorador de BD multisistema.
    Retorna todos los campos necesarios para exploración de tablas.
    """
    try:
        query = f"""
        SELECT * FROM Servidores_Conexiones
        WHERE id = '{_escape_sql(api_id)}'
          AND tipo_conexion = 'API_LOCAL'
          AND activo = 1
        """
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'], EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'], query
        )
        if not results:
            return None
        
        row = results[0]
        return {
            'id': str(row.get('id', '')),
            'nombre': row.get('nombre', ''),
            'name': row.get('nombre', ''),
            'url': row.get('api_url', ''),
            'api_url': row.get('api_url', ''),
            'api_key_encrypted': row.get('api_key_encrypted', ''),
            'tipo': row.get('system_type', ''),
            'system_type': row.get('system_type', ''),
            'tipo_conexion': row.get('tipo_conexion', 'API_LOCAL'),
            'sucursal_destino': row.get('sucursal_destino', ''),
            'activo': bool(row.get('activo', True)),
        }
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error obteniendo API conn {api_id}: {e}")
        return None


async def get_decrypted_api_key(api_conn: Dict) -> str:
    """
    Descifra la API key de una conexión.
    
    CORRECCIÓN P1 (2026-05-15): Para uso seguro en Explorador BD.
    """
    api_key_encrypted = api_conn.get('api_key_encrypted', '')
    if not api_key_encrypted:
        return ''
    
    try:
        from core.secret_manager import decrypt_secret, is_encrypted_secret
        if is_encrypted_secret(api_key_encrypted):
            return decrypt_secret(api_key_encrypted)
        return api_key_encrypted
    except Exception as e:
        logging.warning(f"[API_CONNECTIONS] Error descifrando API key: {e}")
        return ''


async def execute_test_query(
    api_id: str,
    sql_query: str,
    timeout: int = 30,
    executed_by: str = "system",
    limit: Optional[int] = 20
) -> Dict:
    """
    Ejecuta una consulta SQL de prueba contra una conexión API registrada.
    
    SEGURIDAD:
    1. Valida SQL con SQLValidator
    2. Solo permite SELECT
    3. Usa credenciales cifradas de la conexión
    4. No expone API key en respuesta
    5. Registra en auditoría
    
    Args:
        api_id: ID de la conexión API
        sql_query: Consulta SQL a ejecutar
        timeout: Timeout en segundos
        executed_by: Usuario que ejecuta
        
    Returns:
        Dict con resultado o error
    """
    import time
    import requests
    from modules.consultas_sql.validator import get_validator
    
    start_time = time.time()
    
    # 1. Validar SQL
    validator = get_validator()
    validation = validator.validate_sql_text(sql_query, strict_mode=True)
    
    if not validation.is_valid:
        errors = [e['message'] for e in validation.errors]
        logging.warning(f"[API_CONNECTIONS][TEST-QUERY] SQL rechazado: {errors}")
        return {
            "success": False,
            "error": "SQL no válido",
            "validation_errors": errors,
            "sql_blocked": True
        }
    
    # 2. Obtener conexión con API key descifrada
    connection = get_api_connection_with_decrypted_key(api_id)
    if not connection:
        return {
            "success": False,
            "error": "Conexión API no encontrada o API key no descifrable"
        }
    
    if not connection.get('activo'):
        return {
            "success": False,
            "error": "Conexión API inactiva"
        }
    
    url = connection.get('url')
    api_key = connection.get('api_key_decrypted', '')
    
    if not url:
        return {
            "success": False,
            "error": "URL de API no configurada"
        }
    
    # 3. Ejecutar consulta
    try:
        headers = {"x-api-key": api_key} if api_key else {}
        
        response = requests.get(
            url,
            headers=headers,
            params={"sql": sql_query},
            timeout=timeout
        )
        
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Extraer datos de respuesta
                rows = []
                columns = []
                
                # CORRECCIÓN P1: Usar parámetro limit configurable (None = sin límite)
                max_rows = limit if limit is not None else None
                
                if isinstance(data, list):
                    rows = data[:max_rows] if max_rows else data
                    if rows:
                        columns = list(rows[0].keys()) if isinstance(rows[0], dict) else []
                elif isinstance(data, dict):
                    if 'data' in data:
                        raw_data = data['data'] if isinstance(data['data'], list) else []
                        rows = raw_data[:max_rows] if max_rows else raw_data
                        if rows and isinstance(rows[0], dict):
                            columns = list(rows[0].keys())
                    elif 'results' in data:
                        raw_results = data['results'] if isinstance(data['results'], list) else []
                        rows = raw_results[:max_rows] if max_rows else raw_results
                        if rows and isinstance(rows[0], dict):
                            columns = list(rows[0].keys())
                
                result = {
                    "success": True,
                    "status_code": 200,
                    "response_time_ms": elapsed_ms,
                    "rows_count": len(rows),
                    "columns": columns,
                    "preview_data": rows,
                    "data": rows,  # CORRECCIÓN P1: Agregar 'data' para compatibilidad con Explorador
                    "message": f"Consulta ejecutada exitosamente ({len(rows)} filas)"
                }
                
            except Exception as parse_error:
                result = {
                    "success": True,
                    "status_code": 200,
                    "response_time_ms": elapsed_ms,
                    "message": "Respuesta recibida pero no es JSON válido",
                    "raw_response_preview": response.text[:500] if response.text else ""
                }
        else:
            # Extraer mensaje de error sin exponer detalles sensibles
            error_msg = f"HTTP {response.status_code}"
            try:
                err_json = response.json()
                if isinstance(err_json, dict) and 'error' in err_json:
                    error_msg = str(err_json['error'])[:200]
                elif isinstance(err_json, dict) and 'detail' in err_json:
                    error_msg = str(err_json['detail'])[:200]
            except Exception:
                pass
            
            result = {
                "success": False,
                "status_code": response.status_code,
                "response_time_ms": elapsed_ms,
                "error": error_msg
            }
            
    except requests.exceptions.Timeout:
        result = {
            "success": False,
            "error": f"Timeout ({timeout}s)",
            "response_time_ms": timeout * 1000
        }
    except requests.exceptions.ConnectionError as conn_err:
        result = {
            "success": False,
            "error": "Sin conexión a la API"
        }
    except Exception as e:
        logging.error(f"[API_CONNECTIONS][TEST-QUERY] Error: {e}")
        result = {
            "success": False,
            "error": "Error ejecutando consulta"
        }
    
    # 4. Registrar en auditoría (sin exponer SQL completo)
    try:
        _log_operation(
            api_id,
            'TEST_QUERY',
            {},
            {
                'sql_length': len(sql_query),
                'sql_preview': sql_query[:50] + '...' if len(sql_query) > 50 else sql_query,
                'result_success': result.get('success', False),
                'response_time_ms': result.get('response_time_ms'),
                'rows_count': result.get('rows_count', 0)
            },
            executed_by
        )
    except Exception:
        pass
    
    return result


# ============================================================================
# COMPATIBILIDAD CON ADAPTERS.PY (LECTURA PARA VENTAS DEL DÍA)
# ============================================================================

def get_api_connections_for_adapters() -> List[Dict]:
    """
    Retorna conexiones API activas para uso en adapters.py.
    Lee directamente de EDARSAHUB SQL.
    """
    return list_api_connections_sql(include_inactive=False)
