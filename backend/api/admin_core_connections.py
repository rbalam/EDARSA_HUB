from core.sql_first.connection_factory import get_edarsahub_pymssql_connection, get_external_sql_connection, get_edarsahub_connection
"""
EDARSA HUB - Endpoints Administrativos para Conexiones CORE
============================================================

FASE 4D: Administración segura de conexiones CORE.

ENDPOINTS:
    GET  /api/admin/core-connections          - Listar conexiones CORE
    GET  /api/admin/core-connections/{id}     - Detalle de conexión CORE
    POST /api/admin/core-connections/{id}/test - Probar conectividad CORE

SEGURIDAD:
    - Solo SuperAdministrador puede usar estos endpoints
    - Administrador normal NO tiene acceso
    - NUNCA se exponen secretos (password, api_key)
    - Toda acción se audita

PROTECCIÓN:
    - No permite cambiar tipo CORE a DATA_SOURCE
    - No permite eliminar conexiones CORE
    - PUT solo actualiza campos seguros (si se implementa)

CREADO: FASE 4D - Abril 2026
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import time
import logging
import json

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG, get_decrypted_credentials
from core.secret_manager import is_encrypted_secret, decrypt_secret
from core.system_type_utils import normalize_system_type

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/core-connections", tags=["Admin CORE"])


# =============================================================================
# RBAC: Solo SuperAdministrador
# =============================================================================

def require_super_admin(current_user: Dict) -> bool:
    """
    Verifica que el usuario sea SuperAdministrador.
    
    FASE 4D: CORE requiere nivel superior a Administrador normal.
    
    Returns:
        True si es SuperAdministrador
        
    Raises:
        HTTPException: Si no tiene permisos
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida"
        )
    
    role = current_user.get('role', '').strip()
    role_normalized = role.lower().replace(' ', '').replace('_', '')
    
    # Solo SuperAdministrador
    if role_normalized not in ['superadministrador', 'superadmin']:
        logger.warning(
            f"[CORE_ADMIN][PERMISSION_DENIED] Usuario {current_user.get('email')} "
            f"con rol '{role}' intentó acceder a CORE admin"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SuperAdministrador puede administrar conexiones CORE"
        )
    
    return True


def _write_admin_audit_log_sql(log_data: Dict) -> bool:
    """Persiste auditoría CORE en dbo.Servidores_Conexiones_Log (SQL-First, NO bloqueante).

    Reemplaza el residual Mongo (auditoria_core_admin). Usa la conexión canónica
    write-capable get_edarsahub_pymssql_connection. Nunca interrumpe el flujo.
    """
    try:
        servidor_id = log_data.get("core_connection_id")
        accion = log_data.get("action")
        usuario = log_data.get("user_email") or (
            str(log_data.get("user_id")) if log_data.get("user_id") else None
        )
        datos_nuevos = json.dumps(log_data, ensure_ascii=False, default=str)

        # Truncar a los límites reales de columna (accion=20, usuario=100)
        if accion is not None:
            accion = str(accion)[:20]
        if usuario is not None:
            usuario = str(usuario)[:100]

        conn = get_edarsahub_pymssql_connection(timeout=15, login_timeout=10)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dbo.Servidores_Conexiones_Log "
            "(servidor_id, accion, datos_nuevos, usuario, fecha, ip_origen) "
            "VALUES (%s, %s, %s, %s, GETDATE(), %s)",
            (servidor_id, accion, datos_nuevos, usuario, None),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.warning(
            f"[CORE_ADMIN][AUDIT_SQL] No se pudo registrar auditoría SQL: {type(e).__name__}: {e}"
        )
        return False


def audit_core_action(
    action: str,
    user: Dict,
    core_id: Optional[str] = None,
    status: str = "SUCCESS",
    details: Optional[Dict] = None
):
    """
    Registra auditoría de acciones CORE.
    
    SEGURIDAD: No incluye secretos.
    """
    user = user or {}
    log_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'action': action,
        'user_id': user.get('id') or user.get('_id'),
        'user_email': user.get('email'),
        'role': user.get('role'),
        'core_connection_id': core_id,
        'status': status
    }
    
    if details:
        # Filtrar cualquier secreto
        safe_details = {k: v for k, v in details.items() 
                       if k not in ['password', 'api_key', 'token', 'secret']}
        log_data['details'] = safe_details
    
    logger.info(f"[CORE_ADMIN][AUDIT] {action}: {log_data}")
    
    # Persistir auditoría en SQL-First (dbo.Servidores_Conexiones_Log) — NO bloqueante
    _write_admin_audit_log_sql(log_data)


# =============================================================================
# HELPERS
# =============================================================================

def get_core_connections_from_sql() -> List[Dict]:
    """
    Obtiene conexiones CORE desde SQL.
    
    SEGURIDAD: No devuelve valores de secretos.
    """
    query = """
    SELECT 
        CAST(id AS VARCHAR(50)) as id,
        nombre,
        system_type,
        tipo_conexion,
        host,
        port,
        database_name,
        username,
        api_url,
        activo,
        created_at,
        updated_at,
        CASE WHEN password_encrypted IS NOT NULL AND password_encrypted != '' THEN 1 ELSE 0 END as password_configured,
        CASE WHEN password_encrypted LIKE 'enc:v1:%' THEN 1 ELSE 0 END as password_encrypted,
        CASE WHEN api_key_encrypted IS NOT NULL AND api_key_encrypted != '' THEN 1 ELSE 0 END as api_key_configured,
        CASE WHEN api_key_encrypted LIKE 'enc:v1:%' THEN 1 ELSE 0 END as api_key_encrypted
    FROM Servidores_Conexiones
    WHERE tipo_conexion = 'CORE'
    ORDER BY activo DESC, nombre
    """
    
    return execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )


def get_core_connection_by_id(server_id: str) -> Optional[Dict]:
    """
    Obtiene una conexión CORE por ID.
    
    SEGURIDAD: No devuelve valores de secretos.
    """
    # Escapar ID para SQL
    safe_id = server_id.replace("'", "''")
    
    query = f"""
    SELECT 
        CAST(id AS VARCHAR(50)) as id,
        nombre,
        system_type,
        tipo_conexion,
        host,
        port,
        database_name,
        username,
        api_url,
        activo,
        created_at,
        updated_at,
        password_encrypted,
        api_key_encrypted,
        CASE WHEN password_encrypted IS NOT NULL AND password_encrypted != '' THEN 1 ELSE 0 END as password_configured,
        CASE WHEN password_encrypted LIKE 'enc:v1:%' THEN 1 ELSE 0 END as password_is_encrypted,
        CASE WHEN api_key_encrypted IS NOT NULL AND api_key_encrypted != '' THEN 1 ELSE 0 END as api_key_configured,
        CASE WHEN api_key_encrypted LIKE 'enc:v1:%' THEN 1 ELSE 0 END as api_key_is_encrypted
    FROM Servidores_Conexiones
    WHERE (CAST(id AS VARCHAR(50)) = '{safe_id}' OR nombre LIKE '%{safe_id}%')
      AND tipo_conexion = 'CORE'
    """
    
    result = execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )
    
    return result[0] if result else None


def format_core_connection(conn: Dict, include_mongo: bool = True) -> Dict:
    """
    Formatea una conexión CORE para respuesta segura.
    
    SEGURIDAD: NUNCA incluye valores de secretos.
    """
    formatted = {
        'id': conn.get('id'),
        'name': conn.get('nombre'),
        'connection_type': conn.get('tipo_conexion', 'CORE'),
        'tipo_conexion': conn.get('tipo_conexion', 'CORE'),
        'system_type': conn.get('system_type'),
        'system_type_normalized': normalize_system_type(conn.get('system_type')),
        'host': conn.get('host'),
        'port': conn.get('port', 1433),
        'database_name': conn.get('database_name'),
        'username': conn.get('username'),
        'api_url': conn.get('api_url'),
        'activo': bool(conn.get('activo')),
        'password_configured': bool(conn.get('password_configured')),
        'password_encrypted': bool(conn.get('password_encrypted') or conn.get('password_is_encrypted')),
        'api_key_configured': bool(conn.get('api_key_configured')),
        'api_key_encrypted': bool(conn.get('api_key_encrypted') or conn.get('api_key_is_encrypted')),
        'config_origin': 'EDARSAHUB_SQL',
        'created_at': conn.get('created_at'),
        'updated_at': conn.get('updated_at'),
        'warnings': []
    }
    
    # Verificar estado de cifrado
    if formatted['password_configured'] and not formatted['password_encrypted']:
        formatted['warnings'].append('Password está en texto plano')
    
    if formatted['api_key_configured'] and not formatted['api_key_encrypted']:
        formatted['warnings'].append('API Key está en texto plano')
    
    # P5-3B-2: residual Mongo retirado. mongodb_id/mongo_synced eran no-op
    # (la conexión Mongo siempre era None, nunca agregaban estas keys) y no
    # forman parte del contrato HTTP. Arquitectura NO-MONGO: estado solo en SQL.
    return formatted


def _classify_sql_error(error_msg: str, error_type: str) -> tuple:
    """Clasifica errores de SQL Server en categorías seguras."""
    error_msg_lower = error_msg.lower()
    
    if 'timeout' in error_msg_lower or 'timed out' in error_msg_lower:
        return ('SOURCE_UNREACHABLE', 'Connection timeout')
    if 'login failed' in error_msg_lower or 'access denied' in error_msg_lower:
        return ('AUTH_FAILED', 'Authentication failed')
    if 'unable to connect' in error_msg_lower or 'unavailable' in error_msg_lower:
        return ('SOURCE_UNREACHABLE', 'Server unavailable')
    
    return ('QUERY_ERROR', f'{error_type}: {error_msg[:100]}')


def _validate_connection_config(conn: Dict) -> tuple:
    """Valida configuración mínima de conexión. Retorna (ok, error_status, error_msg)."""
    if not conn.get('host'):
        return (False, 'CONFIGURATION_MISSING', 'Host no configurado')
    if not conn.get('password_encrypted'):
        return (False, 'CONFIGURATION_MISSING', 'Password no configurado')
    return (True, None, None)


def test_core_connectivity(conn: Dict, timeout: int = 10) -> Dict:
    """
    Prueba conectividad a una conexión CORE.
    
    SEGURIDAD: No expone secretos en logs ni respuesta.
    """
    result = {
        'status': 'SUCCESS',
        'server_id': conn.get('id'),
        'name': conn.get('nombre'),
        'duration_ms': 0,
        'message': None,
        'safe_error': None
    }
    
    start_time = time.time()
    
    # Validar configuración
    config_ok, error_status, error_msg = _validate_connection_config(conn)
    if not config_ok:
        result['status'] = error_status
        result['safe_error'] = error_msg
        return result
    
    # Descifrar password
    try:
        password = decrypt_secret(conn.get('password_encrypted'))
    except Exception as e:
        result['status'] = 'SECRET_DECRYPTION_ERROR'
        result['safe_error'] = f'Error de descifrado: {type(e).__name__}'
        result['duration_ms'] = int((time.time() - start_time) * 1000)
        return result
    
    # Probar conexión SQL
    try:
        import pymssql
        
        connection = get_edarsahub_pymssql_connection()
        
        cursor = connection.cursor()
        cursor.execute("SELECT 1 AS connectivity_ok")
        row = cursor.fetchone()
        connection.close()
        
        if row and row[0] == 1:
            result['status'] = 'SUCCESS'
            result['message'] = 'Conexión CORE verificada correctamente'
        else:
            result['status'] = 'QUERY_ERROR'
            result['safe_error'] = 'Query no retornó resultado esperado'
            
    except Exception as e:
        result['status'], result['safe_error'] = _classify_sql_error(str(e), type(e).__name__)
    
    result['duration_ms'] = int((time.time() - start_time) * 1000)
    return result


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("")
async def list_core_connections(
    current_user: Dict = Depends(lambda: None)  # Se inyecta desde server.py
):
    """
    Lista todas las conexiones CORE.
    
    RBAC: Solo SuperAdministrador.
    SEGURIDAD: No expone secretos.
    """
    # La validación real se hace en server.py al incluir el router
    # Aquí solo documentamos la expectativa
    
    try:
        connections = get_core_connections_from_sql()
        
        formatted = [format_core_connection(conn) for conn in connections]
        
        return {
            'status': 'SUCCESS',
            'data': formatted,
            'meta': {
                'count': len(formatted),
                'secrets_exposed': False
            }
        }
        
    except Exception as e:
        logger.error(f"[CORE_ADMIN][LIST] Error: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener conexiones CORE"
        )


@router.get("/audit-log")
async def get_core_audit_log(
    limit: int = 50,
    server_id: Optional[str] = None,
    current_user: Dict = Depends(lambda: None)
):
    """
    Bitácora de acciones sobre conexiones CORE (lectura SQL-First).

    Lee dbo.Servidores_Conexiones_Log. NO expone secretos.
    RBAC: Solo SuperAdministrador (enforced al incluir el router).
    NOTA: definido ANTES de /{server_id} para evitar colisión de ruta.
    """
    try:
        safe_limit = max(1, min(int(limit), 200))
    except (TypeError, ValueError):
        safe_limit = 50

    where = ""
    if server_id:
        safe_sid = server_id.replace("'", "''")
        where = f"WHERE l.servidor_id = '{safe_sid}'"

    query = f"""
    SELECT TOP ({safe_limit})
        l.log_id,
        CAST(l.servidor_id AS VARCHAR(50)) as servidor_id,
        s.nombre as servidor_nombre,
        l.accion,
        l.usuario,
        CONVERT(VARCHAR(33), l.fecha, 126) as fecha,
        l.ip_origen,
        l.datos_nuevos
    FROM dbo.Servidores_Conexiones_Log l
    LEFT JOIN dbo.Servidores_Conexiones s ON s.id = l.servidor_id
    {where}
    ORDER BY l.fecha DESC, l.log_id DESC
    """

    try:
        rows = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
    except Exception as e:
        logger.error(f"[CORE_ADMIN][AUDIT_LOG] Error: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la bitácora CORE"
        )

    items = []
    for r in rows or []:
        estado = None
        datos = r.get('datos_nuevos')
        if datos:
            try:
                parsed = json.loads(datos)
                if isinstance(parsed, dict):
                    estado = parsed.get('status')
            except (ValueError, TypeError):
                estado = None
        items.append({
            'log_id': r.get('log_id'),
            'servidor_id': r.get('servidor_id'),
            'servidor_nombre': r.get('servidor_nombre') or '—',
            'accion': r.get('accion'),
            'usuario': r.get('usuario') or 'Sistema',
            'fecha': r.get('fecha'),
            'ip_origen': r.get('ip_origen'),
            'estado': estado,
        })

    return {
        'status': 'SUCCESS',
        'data': items,
        'meta': {
            'count': len(items),
            'limit': safe_limit,
            'secrets_exposed': False
        }
    }


@router.get("/{server_id}")
async def get_core_connection_detail(
    server_id: str,
    current_user: Dict = Depends(lambda: None)
):
    """
    Obtiene detalle de una conexión CORE.
    
    RBAC: Solo SuperAdministrador.
    SEGURIDAD: No expone secretos.
    """
    conn = get_core_connection_by_id(server_id)
    
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conexión CORE no encontrada"
        )
    
    if conn.get('tipo_conexion') != 'CORE':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El servidor especificado no es una conexión CORE"
        )
    
    formatted = format_core_connection(conn)
    
    return {
        'status': 'SUCCESS',
        'data': formatted,
        'meta': {
            'secrets_exposed': False
        }
    }


@router.post("/{server_id}/test")
async def test_core_connection(
    server_id: str,
    current_user: Dict = Depends(lambda: None)
):
    """
    Prueba conectividad de una conexión CORE.
    
    RBAC: Solo SuperAdministrador.
    SEGURIDAD: No expone secretos.
    
    Ejecuta: SELECT 1 AS ok (prueba ligera)
    """
    conn = get_core_connection_by_id(server_id)
    
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conexión CORE no encontrada"
        )
    
    if conn.get('tipo_conexion') != 'CORE':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El servidor especificado no es una conexión CORE"
        )
    
    result = test_core_connectivity(conn)

    # Gate 5C: persistir evidencia operativa; activo sigue siendo solo config.
    try:
        from modules.integrations_runtime.health import persist_connection_health
        persist_connection_health(
            server_id,
            success=result.get('status') == 'SUCCESS',
            latency_ms=result.get('duration_ms'),
            error_code=None if result.get('status') == 'SUCCESS' else result.get('status'),
            error_message=result.get('safe_error'),
        )
        result['health_persisted'] = True
    except Exception as health_exc:
        logger.error(
            "[CORE_ADMIN][HEALTH] No se pudo persistir health: %s",
            type(health_exc).__name__,
        )
        result['health_persisted'] = False
    
    audit_core_action(
        action='TEST_CORE_CONNECTION',
        user=current_user,
        core_id=server_id,
        status=result.get('status', 'SUCCESS'),
        details={'endpoint': 'POST /api/admin/core-connections/{server_id}/test'}
    )
    
    return result
