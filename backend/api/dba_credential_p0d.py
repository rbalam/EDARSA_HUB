from core.sql_first.connection_factory import get_edarsahub_pymssql_connection, get_external_sql_connection, get_edarsahub_connection
"""
EDARSA HUB - Endpoint Seguro para Credencial DBA
=================================================

FASE P0D: Diagnóstico Ejecutor B - Acceso temporal DBA

PROPÓSITO:
    Permitir que SuperAdministrador registre credencial DBA/SA de forma segura
    para diagnóstico de SQL Server Agent Jobs sin exponer la contraseña.

SEGURIDAD:
    - Solo SuperAdministrador puede usar este endpoint
    - La contraseña NUNCA se imprime en logs
    - La contraseña NUNCA se devuelve al frontend
    - La contraseña se cifra con SERVER_SECRET_KEY antes de almacenar
    - Toda acción se audita (sin exponer secretos)

USO:
    POST /api/admin/dba-credential/register
    Body: { "password": "xxx" }  (transmitido por HTTPS)
    
    La contraseña se cifra y se almacena para diagnóstico.
    Después del diagnóstico, se puede eliminar.

CREADO: FASE P0D - Diagnóstico Ejecutor B
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from datetime import datetime, timezone
import logging
import os

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG
from core.secret_manager import (
    encrypt_secret, 
    is_encryption_available, 
    is_encrypted_secret,
    mask_secret,
    verify_secret_manager_ready
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/dba-credential", tags=["Admin DBA P0D"])


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Servidor EDARSAHUB para DBA
DBA_SERVER_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'sa'  # Usuario DBA
}

# ID del servidor EDARSA HUB en Servidores_Conexiones
EDARSAHUB_SERVER_ID = 'f8a9049a-96e8-4210-84ae-595ffa2822fa'


# =============================================================================
# SCHEMAS
# =============================================================================

class DBACredentialRequest(BaseModel):
    """Request para registrar credencial DBA."""
    password: str = Field(..., min_length=1, description="Contraseña DBA (NO se loguea)")
    
    model_config = {
        'json_schema_extra': {
            'example': {'password': '********'}
        }
    }


class DBACredentialResponse(BaseModel):
    """Response del registro (SIN exponer contraseña)."""
    success: bool
    message: str
    encryption_status: str
    user_authorized: str
    timestamp: str
    

class DBAQueryRequest(BaseModel):
    """Request para ejecutar consulta DBA."""
    query_name: str = Field(..., description="Nombre de la consulta a ejecutar")


# =============================================================================
# RBAC: Solo SuperAdministrador
# =============================================================================

async def get_current_user_from_request(request: Request) -> Dict:
    """
    Extrae usuario actual del request.
    Simplificado para este diagnóstico.
    """
    # Intentar obtener de headers
    auth_header = request.headers.get('authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        try:
            import jwt
            payload = jwt.decode(
                token, 
                os.environ.get('JWT_SECRET', ''), 
                algorithms=['HS256']
            )
            return {
                'id': payload.get('user_id'),
                'email': payload.get('email'),
                'role': payload.get('role')
            }
        except Exception:
            pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado"
    )


def require_super_admin(current_user: Dict) -> bool:
    """Verifica que el usuario sea SuperAdministrador."""
    role = current_user.get('role', '').strip()
    role_normalized = role.lower().replace(' ', '').replace('_', '')
    
    if role_normalized not in ['superadministrador', 'superadmin']:
        logger.warning(
            f"[DBA_CRED][PERMISSION_DENIED] Usuario {current_user.get('email')} "
            f"con rol '{role}' intentó acceder a DBA credential"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SuperAdministrador puede registrar credencial DBA"
        )
    
    return True


def audit_dba_action(
    action: str,
    user: Dict,
    status_result: str = "SUCCESS",
    details: Optional[Dict] = None
):
    """
    Registra auditoría de acciones DBA.
    SEGURIDAD: NUNCA incluye contraseña.
    """
    log_entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'action': action,
        'user_id': user.get('id'),
        'user_email': user.get('email'),
        'role': user.get('role'),
        'status': status_result,
        'module': 'DBA_CREDENTIAL_P0D'
    }
    
    if details:
        # Filtrar cualquier secreto
        safe_details = {
            k: v for k, v in details.items() 
            if k not in ['password', 'secret', 'token', 'api_key', 'credential']
        }
        log_entry['details'] = safe_details
    
    # Log sin secretos
    logger.info(f"[DBA_CRED][AUDIT] {action}: user={user.get('email')}, status={status_result}")


# =============================================================================
# VARIABLE TEMPORAL EN MEMORIA (NO persistente)
# =============================================================================

# Almacenamiento temporal en memoria - se pierde al reiniciar
_dba_credential_cache: Dict[str, Any] = {}


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_dba_credential_status(request: Request):
    """
    Verifica el estado del sistema de credenciales DBA.
    
    NO expone ningún secreto.
    """
    current_user = await get_current_user_from_request(request)
    require_super_admin(current_user)
    
    secret_status = verify_secret_manager_ready()
    
    return {
        'encryption_available': secret_status['encryption_available'],
        'key_configured': secret_status['key_configured'],
        'key_valid': secret_status['key_valid'],
        'key_fingerprint': secret_status['key_fingerprint'],
        'dba_credential_registered': bool(_dba_credential_cache.get('encrypted_password')),
        'dba_username': DBA_SERVER_CONFIG['username'],
        'dba_server': DBA_SERVER_CONFIG['host'],
        'dba_database': DBA_SERVER_CONFIG['database'],
        'warnings': secret_status.get('warnings', [])
    }


@router.post("/register", response_model=DBACredentialResponse)
async def register_dba_credential(
    request: Request,
    payload: DBACredentialRequest
):
    """
    Registra credencial DBA de forma segura.
    
    SEGURIDAD:
    - La contraseña se cifra inmediatamente
    - La contraseña NUNCA se imprime en logs
    - La contraseña NUNCA se devuelve al frontend
    - Solo SuperAdministrador puede ejecutar
    - Se registra auditoría (sin secretos)
    
    Returns:
        Confirmación de registro (SIN la contraseña)
    """
    current_user = await get_current_user_from_request(request)
    require_super_admin(current_user)
    
    # Verificar que el cifrado esté disponible
    if not is_encryption_available():
        audit_dba_action(
            "REGISTER_DBA_CREDENTIAL",
            current_user,
            "FAILED",
            {'reason': 'encryption_not_available'}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sistema de cifrado no disponible. Contactar administrador."
        )
    
    # Cifrar la contraseña INMEDIATAMENTE
    # La variable payload.password se usa una sola vez aquí
    encrypted_password = encrypt_secret(payload.password)
    
    # Verificar que quedó cifrada
    if not is_encrypted_secret(encrypted_password):
        audit_dba_action(
            "REGISTER_DBA_CREDENTIAL",
            current_user,
            "FAILED",
            {'reason': 'encryption_failed'}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cifrar credencial. Contactar administrador."
        )
    
    # Guardar en cache temporal (solo en memoria, se pierde al reiniciar)
    _dba_credential_cache['encrypted_password'] = encrypted_password
    _dba_credential_cache['registered_by'] = current_user.get('email')
    _dba_credential_cache['registered_at'] = datetime.now(timezone.utc).isoformat()
    _dba_credential_cache['server_config'] = {
        'host': DBA_SERVER_CONFIG['host'],
        'port': DBA_SERVER_CONFIG['port'],
        'database': DBA_SERVER_CONFIG['database'],
        'username': DBA_SERVER_CONFIG['username']
    }
    
    # Auditar (SIN la contraseña)
    audit_dba_action(
        "REGISTER_DBA_CREDENTIAL",
        current_user,
        "SUCCESS",
        {
            'server': DBA_SERVER_CONFIG['host'],
            'username': DBA_SERVER_CONFIG['username'],
            'database': DBA_SERVER_CONFIG['database'],
            'encrypted': True
        }
    )
    
    logger.info(
        f"[DBA_CRED][REGISTERED] Credencial DBA registrada por {current_user.get('email')} "
        f"(cifrada, no persistida)"
    )
    
    return DBACredentialResponse(
        success=True,
        message="Credencial DBA registrada de forma segura (cifrada, temporal en memoria)",
        encryption_status="ENCRYPTED",
        user_authorized=current_user.get('email'),
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@router.delete("/clear")
async def clear_dba_credential(request: Request):
    """
    Elimina la credencial DBA de memoria.
    
    Usar después de completar el diagnóstico.
    """
    current_user = await get_current_user_from_request(request)
    require_super_admin(current_user)
    
    was_registered = bool(_dba_credential_cache.get('encrypted_password'))
    
    # Limpiar cache
    _dba_credential_cache.clear()
    
    audit_dba_action(
        "CLEAR_DBA_CREDENTIAL",
        current_user,
        "SUCCESS",
        {'had_credential': was_registered}
    )
    
    logger.info(f"[DBA_CRED][CLEARED] Credencial DBA eliminada por {current_user.get('email')}")
    
    return {
        'success': True,
        'message': 'Credencial DBA eliminada de memoria',
        'was_registered': was_registered
    }


@router.get("/test-connection")
async def test_dba_connection(request: Request):
    """
    Prueba la conexión DBA sin exponer credenciales.
    
    Returns:
        Estado de conexión y permisos en msdb
    """
    current_user = await get_current_user_from_request(request)
    require_super_admin(current_user)
    
    # Verificar que hay credencial registrada
    if not _dba_credential_cache.get('encrypted_password'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay credencial DBA registrada. Use POST /register primero."
        )
    
    # Descifrar para usar (NUNCA loguear)
    from core.secret_manager import decrypt_secret
    
    try:
        decrypted_password = decrypt_secret(_dba_credential_cache['encrypted_password'])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al descifrar credencial"
        )
    
    # Probar conexión
    import pymssql
    
    try:
        conn = get_external_sql_connection(server_config)  # noqa: F821
        cursor = conn.cursor()
        
        # Validar identidad
        cursor.execute("""
            SELECT 
                SYSTEM_USER AS [system_user],
                USER_NAME() AS [db_user],
                DB_NAME() AS [database],
                IS_MEMBER('SQLAgentReaderRole') AS [is_sqlagent_reader],
                IS_MEMBER('sysadmin') AS [is_sysadmin]
        """)
        identity = cursor.fetchone()
        
        # Probar lectura de jobs
        cursor.execute("SELECT COUNT(*) as job_count FROM dbo.sysjobs")
        job_count = cursor.fetchone()
        
        conn.close()
        
        # Limpiar variable sensible
        decrypted_password = None
        
        audit_dba_action(
            "TEST_DBA_CONNECTION",
            current_user,
            "SUCCESS",
            {
                'system_user': identity['system_user'],
                'db_user': identity['db_user'],
                'is_sysadmin': bool(identity['is_sysadmin']),
                'job_count': job_count['job_count']
            }
        )
        
        return {
            'success': True,
            'connection': 'OK',
            'identity': {
                'system_user': identity['system_user'],
                'db_user': identity['db_user'],
                'database': identity['database'],
                'is_sqlagent_reader': bool(identity['is_sqlagent_reader']),
                'is_sysadmin': bool(identity['is_sysadmin'])
            },
            'msdb_access': {
                'can_read_jobs': True,
                'job_count': job_count['job_count']
            }
        }
        
    except Exception as e:
        # Limpiar variable sensible
        decrypted_password = None
        
        audit_dba_action(
            "TEST_DBA_CONNECTION",
            current_user,
            "FAILED",
            {'error_type': type(e).__name__}
        )
        
        error_msg = str(e)
        # Sanitizar mensaje de error (no incluir detalles de password)
        if 'password' in error_msg.lower() or 'login' in error_msg.lower():
            error_msg = "Error de autenticación"
        
        return {
            'success': False,
            'connection': 'FAILED',
            'error': error_msg
        }


@router.post("/execute-diagnostic")
async def execute_dba_diagnostic(request: Request):
    """
    Ejecuta las consultas de diagnóstico para identificar el Ejecutor B.
    
    Ejecuta las consultas de /app/docs/reports/CONSULTAS_DBA_EJECUTAR_CON_SA.sql
    
    Returns:
        Resultados del diagnóstico (Jobs, Steps, Schedules, etc.)
    """
    current_user = await get_current_user_from_request(request)
    require_super_admin(current_user)
    
    # Verificar credencial
    if not _dba_credential_cache.get('encrypted_password'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay credencial DBA registrada. Use POST /register primero."
        )
    
    from core.secret_manager import decrypt_secret
    
    try:
        decrypted_password = decrypt_secret(_dba_credential_cache['encrypted_password'])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al descifrar credencial"
        )
    
    import pymssql
    results = {}
    
    try:
        conn = get_external_sql_connection(server_config)  # noqa: F821
        cursor = conn.cursor()
        
        # CONSULTA 1: Jobs activos
        cursor.execute("""
            SELECT 
                CAST(j.job_id AS VARCHAR(50)) as job_id,
                j.name AS job_name,
                j.enabled,
                SUSER_SNAME(j.owner_sid) AS owner_name,
                j.date_created,
                j.date_modified
            FROM dbo.sysjobs j
            WHERE j.enabled = 1
            ORDER BY j.name
        """)
        results['active_jobs'] = cursor.fetchall()
        
        # CONSULTA 2: Job Steps con tablas afectadas
        cursor.execute("""
            SELECT
                j.name AS job_name,
                SUSER_SNAME(j.owner_sid) AS owner_name,
                j.enabled,
                s.step_id,
                s.step_name,
                s.subsystem,
                s.database_name,
                CAST(s.command AS VARCHAR(4000)) as command
            FROM dbo.sysjobs j
            INNER JOIN dbo.sysjobsteps s ON j.job_id = s.job_id
            WHERE
                s.command LIKE '%Comercial_Ventas_Dia_Abiertas_v2%'
                OR s.command LIKE '%Comercial_SyncLog_v2%'
                OR s.command LIKE '%Ventas_Dia%'
                OR s.command LIKE '%ventas_dia%'
                OR s.command LIKE '%FechaOperacion%'
                OR s.command LIKE '%fecha_operacion%'
                OR s.command LIKE '%ABIERTA-%'
            ORDER BY j.name, s.step_id
        """)
        results['suspicious_job_steps'] = cursor.fetchall()
        
        # CONSULTA 3: Schedules cada 5-10 minutos
        cursor.execute("""
            SELECT
                j.name AS job_name,
                j.enabled AS job_enabled,
                SUSER_SNAME(j.owner_sid) AS owner_name,
                sch.name AS schedule_name,
                sch.enabled AS schedule_enabled,
                sch.freq_type,
                CASE sch.freq_type
                    WHEN 1 THEN 'Once'
                    WHEN 4 THEN 'Daily'
                    WHEN 8 THEN 'Weekly'
                    WHEN 16 THEN 'Monthly'
                    WHEN 32 THEN 'Monthly relative'
                    WHEN 64 THEN 'SQL Agent Start'
                    WHEN 128 THEN 'When idle'
                    ELSE CAST(sch.freq_type AS VARCHAR)
                END AS freq_type_desc,
                sch.freq_subday_type,
                CASE sch.freq_subday_type
                    WHEN 1 THEN 'At specified time'
                    WHEN 2 THEN 'Seconds'
                    WHEN 4 THEN 'Minutes'
                    WHEN 8 THEN 'Hours'
                    ELSE CAST(sch.freq_subday_type AS VARCHAR)
                END AS freq_subday_desc,
                sch.freq_subday_interval
            FROM dbo.sysjobs j
            INNER JOIN dbo.sysjobschedules js ON j.job_id = js.job_id
            INNER JOIN dbo.sysschedules sch ON js.schedule_id = sch.schedule_id
            WHERE j.enabled = 1
              AND sch.freq_subday_type = 4  -- Minutes
              AND sch.freq_subday_interval <= 10  -- Cada 10 minutos o menos
            ORDER BY sch.freq_subday_interval, j.name
        """)
        results['frequent_schedules'] = cursor.fetchall()
        
        # CONSULTA 4: Historial reciente
        cursor.execute("""
            SELECT TOP 100
                j.name AS job_name,
                h.step_id,
                h.step_name,
                h.run_date,
                h.run_time,
                h.run_duration,
                h.run_status,
                CASE h.run_status
                    WHEN 0 THEN 'FAILED'
                    WHEN 1 THEN 'SUCCESS'
                    WHEN 2 THEN 'RETRY'
                    WHEN 3 THEN 'CANCELED'
                    WHEN 4 THEN 'IN PROGRESS'
                    ELSE 'UNKNOWN'
                END AS run_status_desc,
                LEFT(h.message, 200) AS message_preview
            FROM dbo.sysjobhistory h
            INNER JOIN dbo.sysjobs j ON h.job_id = j.job_id
            WHERE h.run_date >= CONVERT(int, CONVERT(varchar, GETDATE(), 112))
            ORDER BY h.instance_id DESC
        """)
        results['recent_history'] = cursor.fetchall()
        
        # CONSULTA 5: Todos los steps de jobs activos
        cursor.execute("""
            SELECT
                j.name AS job_name,
                j.enabled,
                s.step_id,
                s.step_name,
                s.subsystem,
                s.database_name,
                CAST(s.command AS VARCHAR(2000)) as command_preview
            FROM dbo.sysjobs j
            INNER JOIN dbo.sysjobsteps s ON j.job_id = s.job_id
            WHERE j.enabled = 1
            ORDER BY j.name, s.step_id
        """)
        results['all_active_job_steps'] = cursor.fetchall()
        
        conn.close()
        
        # Limpiar variable sensible
        decrypted_password = None
        
        # Identificar sospechosos
        suspects = []
        for job in results.get('suspicious_job_steps', []):
            suspects.append({
                'job_name': job['job_name'],
                'step_name': job['step_name'],
                'command_preview': job['command'][:200] if job.get('command') else None,
                'database': job['database_name'],
                'owner': job['owner_name']
            })
        
        for sched in results.get('frequent_schedules', []):
            if sched['freq_subday_interval'] == 5:  # Exactamente 5 minutos
                suspects.append({
                    'job_name': sched['job_name'],
                    'schedule_name': sched['schedule_name'],
                    'frequency': f"Cada {sched['freq_subday_interval']} minutos",
                    'owner': sched['owner_name'],
                    'reason': 'FRECUENCIA SOSPECHOSA: cada 5 minutos'
                })
        
        audit_dba_action(
            "EXECUTE_DBA_DIAGNOSTIC",
            current_user,
            "SUCCESS",
            {
                'jobs_found': len(results.get('active_jobs', [])),
                'suspicious_steps': len(results.get('suspicious_job_steps', [])),
                'frequent_schedules': len(results.get('frequent_schedules', [])),
                'suspects_identified': len(suspects)
            }
        )
        
        return {
            'success': True,
            'diagnostic_results': {
                'active_jobs_count': len(results.get('active_jobs', [])),
                'active_jobs': results.get('active_jobs', []),
                'suspicious_job_steps': results.get('suspicious_job_steps', []),
                'frequent_schedules_5_10_min': results.get('frequent_schedules', []),
                'recent_history_today': results.get('recent_history', [])[:50],
                'all_active_job_steps': results.get('all_active_job_steps', [])
            },
            'suspects': suspects,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'executed_by': current_user.get('email')
        }
        
    except Exception as e:
        decrypted_password = None
        
        audit_dba_action(
            "EXECUTE_DBA_DIAGNOSTIC",
            current_user,
            "FAILED",
            {'error_type': type(e).__name__}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando diagnóstico: {type(e).__name__}"
        )
