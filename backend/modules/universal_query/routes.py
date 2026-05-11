"""
Universal Query Tester - Módulo Backend
=======================================
Herramienta agnóstica para probar consultas SQL o endpoints API
contra cualquier origen de datos registrado.

AGNÓSTICO:
- NO valida estructura de columnas
- NO asume dominio (no productos, no ventas, no inventarios)
- NO persiste resultado
- Acepta cualquier consulta SELECT válida
- Acepta cualquier módulo libre
- Acepta cualquier parámetro libre
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional, Any, List
from pydantic import BaseModel
import time
import re
import logging
import pymssql
import httpx
from datetime import datetime, date
from decimal import Decimal

router = APIRouter(tags=["universal-query"])

# ============================================================================
# MODELOS
# ============================================================================

class SQLConfig(BaseModel):
    query: str
    max_rows: int = 100
    timeout_seconds: int = 30

class APIConfig(BaseModel):
    method: str = "GET"
    url: str
    headers: Optional[Dict[str, str]] = {}
    query_params: Optional[Dict[str, str]] = {}
    timeout_seconds: int = 30

class UniversalQueryRequest(BaseModel):
    test_name: str
    test_type: str  # sql_libre, api_rest, conexion, diagnostico
    module: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = {}
    sql_config: Optional[SQLConfig] = None
    api_config: Optional[APIConfig] = None

# ============================================================================
# CONSTANTES DE SEGURIDAD
# ============================================================================

BLOCKED_SQL_KEYWORDS = [
    'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'UPDATE', 
    'INSERT', 'MERGE', 'EXEC', 'EXECUTE', 'CREATE',
    'GRANT', 'REVOKE', 'DENY', 'BACKUP', 'RESTORE',
    'SHUTDOWN', 'KILL', 'RECONFIGURE', 'DBCC', 'OPENROWSET',
    'OPENDATASOURCE', 'BULK', 'XP_', 'SP_'
]

SENSITIVE_HEADERS = [
    'authorization', 'api-key', 'x-api-key', 'token', 
    'password', 'secret', 'bearer', 'credentials'
]

ALLOWED_HTTP_METHODS = ['GET']  # Fase 1: solo GET

# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================

def validate_sql_query(sql: str) -> tuple:
    """
    Valida que la consulta SQL sea de solo lectura.
    NO valida estructura de columnas ni dominio.
    Completamente agnóstico.
    """
    if not sql or not sql.strip():
        return False, "La consulta SQL no puede estar vacía"
    
    sql_upper = sql.upper().strip()
    
    # Debe comenzar con SELECT o WITH (para CTEs)
    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
        return False, "Solo se permiten consultas SELECT (lectura)"
    
    # Verificar keywords bloqueados
    for keyword in BLOCKED_SQL_KEYWORDS:
        # Buscar keyword como palabra completa
        if re.search(rf'\b{keyword}\b', sql_upper):
            return False, f"Operación no permitida: {keyword}"
    
    return True, ""

def mask_sensitive_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Enmascara valores de headers sensibles."""
    if not headers:
        return {}
    
    masked = {}
    for key, value in headers.items():
        if any(s in key.lower() for s in SENSITIVE_HEADERS):
            masked[key] = '***MASKED***'
        else:
            masked[key] = value
    return masked

def serialize_value(value: Any) -> Any:
    """Convierte cualquier valor a formato JSON serializable."""
    if value is None:
        return None
    if isinstance(value, (int, float, str, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return "(binary data)"
    return str(value)

def apply_row_limit(sql: str, max_rows: int) -> str:
    """Aplica límite de filas si no tiene TOP."""
    sql_upper = sql.upper().strip()
    
    # Si ya tiene TOP, no modificar
    if 'TOP ' in sql_upper or 'TOP(' in sql_upper:
        return sql
    
    # Insertar TOP después de SELECT
    if sql_upper.startswith('SELECT'):
        return sql[:6] + f' TOP {max_rows} ' + sql[6:]
    
    return sql

def substitute_parameters(sql: str, parameters: Dict[str, Any]) -> str:
    """Sustituye parámetros {key} en la consulta."""
    if not parameters:
        return sql
    
    result = sql
    for key, value in parameters.items():
        # Escapar comillas simples para prevenir SQL injection
        if isinstance(value, str):
            safe_value = value.replace("'", "''")
        else:
            safe_value = str(value)
        result = result.replace(f'{{{key}}}', safe_value)
    
    return result

# ============================================================================
# FUNCIONES DE EJECUCIÓN
# ============================================================================

async def get_server_and_validate(server_id: str, db) -> Dict:
    """Obtiene servidor y valida que existe."""
    from server import decrypt_server_secrets
    
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    return decrypt_server_secrets(server)

def execute_sql_on_server(server: Dict, sql: str, timeout: int) -> tuple:
    """Ejecuta SQL en el servidor y retorna (rows, columns)."""
    conn = None
    try:
        conn = pymssql.connect(
            server=server.get('host'),
            port=int(server.get('port', 1433)),
            user=server.get('username'),
            password=server.get('password'),
            database=server.get('database'),
            login_timeout=timeout,
            timeout=timeout
        )
        cursor = conn.cursor()
        cursor.execute(sql)
        
        # Obtener columnas dinámicamente
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        
        return rows, columns
    finally:
        if conn:
            conn.close()

async def execute_api_request(config: APIConfig) -> Dict:
    """Ejecuta request HTTP."""
    if config.method.upper() not in ALLOWED_HTTP_METHODS:
        raise HTTPException(
            status_code=400, 
            detail=f"Método HTTP no permitido en esta fase. Permitidos: {ALLOWED_HTTP_METHODS}"
        )
    
    async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
        response = await client.request(
            method=config.method.upper(),
            url=config.url,
            headers=config.headers or {},
            params=config.query_params or {}
        )
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "json": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }

# ============================================================================
# ENDPOINT PRINCIPAL
# ============================================================================

@router.post("/servers/{server_id}/universal-query-test")
async def execute_universal_query_test(
    server_id: str,
    request: UniversalQueryRequest
):
    """
    Ejecuta una prueba universal SQL o API contra un servidor.
    
    AGNÓSTICO:
    - NO valida estructura de columnas
    - NO asume dominio (no productos, no ventas, no inventarios)
    - NO persiste resultado
    - Acepta cualquier consulta SELECT válida
    - Acepta cualquier módulo libre
    - Acepta cualquier parámetro libre
    """
    from server import db, decrypt_server_secrets, get_current_user
    
    start_time = time.time()
    
    # Obtener servidor
    server = await db.servers.find_one({"id": server_id, "active": True}, {"_id": 0})
    if not server:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    
    server = decrypt_server_secrets(server)
    
    # Construir respuesta base
    response_base = {
        "test_name": request.test_name,
        "test_type": request.test_type,
        "module": request.module,
        "server": {
            "id": server_id,
            "name": server.get("name"),
            "system_type": server.get("system_type")
        }
    }
    
    try:
        if request.test_type == 'sql_libre':
            return await _execute_sql_test(server, request, start_time, response_base)
        elif request.test_type == 'api_rest':
            return await _execute_api_test(server, request, start_time, response_base)
        elif request.test_type == 'conexion':
            return await _execute_connection_test(server, start_time, response_base)
        elif request.test_type == 'diagnostico':
            return await _execute_diagnostic_test(server, start_time, response_base)
        else:
            raise HTTPException(status_code=400, detail="Tipo de prueba no válido")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[UniversalQuery] Error: {str(e)}")
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error_message": str(e),
                "error_code": "EXECUTION_ERROR"
            }
        }

async def _execute_sql_test(server: Dict, request: UniversalQueryRequest, start_time: float, response_base: Dict) -> Dict:
    """Ejecuta prueba SQL de forma agnóstica."""
    if not request.sql_config:
        raise HTTPException(status_code=400, detail="Configuración SQL requerida para tipo sql_libre")
    
    sql = request.sql_config.query
    max_rows = request.sql_config.max_rows
    timeout = request.sql_config.timeout_seconds
    
    # Validar solo seguridad (NO dominio)
    is_valid, error = validate_sql_query(sql)
    if not is_valid:
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "blocked",
                "response_time_ms": 0,
                "error_message": error,
                "error_code": "BLOCKED_OPERATION"
            }
        }
    
    # Aplicar límite de filas
    sql_with_limit = apply_row_limit(sql, max_rows)
    
    # Sustituir parámetros
    sql_final = substitute_parameters(sql_with_limit, request.parameters or {})
    
    # Ejecutar consulta
    rows, columns = execute_sql_on_server(server, sql_final, timeout)
    
    # Procesar resultado DINÁMICAMENTE (sin asumir estructura)
    preview = []
    for row in rows[:max_rows]:
        row_dict = {}
        for i, col in enumerate(columns):
            row_dict[col] = serialize_value(row[i])
        preview.append(row_dict)
    
    return {
        **response_base,
        "success": True,
        "execution": {
            "status": "success",
            "response_time_ms": int((time.time() - start_time) * 1000),
            "rows_returned": len(preview),
            "query_executed": sql_final,
            "parameters_sent": request.parameters or {}
        },
        "preview": preview,
        "metadata": {
            "columns": columns,
            "total_columns": len(columns)
        }
    }

async def _execute_api_test(server: Dict, request: UniversalQueryRequest, start_time: float, response_base: Dict) -> Dict:
    """Ejecuta prueba API REST."""
    if not request.api_config:
        raise HTTPException(status_code=400, detail="Configuración API requerida para tipo api_rest")
    
    config = request.api_config
    
    # Validar método
    if config.method.upper() not in ALLOWED_HTTP_METHODS:
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "blocked",
                "response_time_ms": 0,
                "error_message": f"Método {config.method} no permitido. Solo: {ALLOWED_HTTP_METHODS}",
                "error_code": "METHOD_NOT_ALLOWED"
            }
        }
    
    # Ejecutar request
    result = await execute_api_request(config)
    
    return {
        **response_base,
        "success": result["status_code"] < 400,
        "execution": {
            "status": "success" if result["status_code"] < 400 else "error",
            "response_time_ms": int((time.time() - start_time) * 1000),
            "http_status": result["status_code"],
            "url_executed": config.url,
            "method": config.method.upper(),
            "headers_sent": mask_sensitive_headers(config.headers or {}),
            "params_sent": config.query_params or {}
        },
        "preview": result.get("json") or result.get("body", "")[:1000],
        "metadata": {
            "response_headers": dict(result.get("headers", {})),
            "content_type": result.get("headers", {}).get("content-type", "unknown")
        }
    }

async def _execute_connection_test(server: Dict, start_time: float, response_base: Dict) -> Dict:
    """Prueba de conexión básica."""
    try:
        rows, columns = execute_sql_on_server(server, "SELECT 1 AS conexion_ok", 10)
        
        return {
            **response_base,
            "success": True,
            "execution": {
                "status": "success",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "message": "Conexión exitosa"
            },
            "preview": [{"conexion_ok": 1}],
            "metadata": {
                "server_name": server.get("name"),
                "host": server.get("host"),
                "database": server.get("database")
            }
        }
    except Exception as e:
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error_message": str(e),
                "error_code": "CONNECTION_FAILED"
            }
        }

async def _execute_diagnostic_test(server: Dict, start_time: float, response_base: Dict) -> Dict:
    """Diagnóstico técnico del servidor."""
    diagnostics = {}
    
    try:
        # Versión del servidor
        rows, _ = execute_sql_on_server(server, "SELECT @@VERSION AS version", 10)
        diagnostics["version"] = rows[0][0] if rows else "Unknown"
        
        # Nombre del servidor
        rows, _ = execute_sql_on_server(server, "SELECT @@SERVERNAME AS server_name", 10)
        diagnostics["server_name"] = rows[0][0] if rows else "Unknown"
        
        # Base de datos actual
        rows, _ = execute_sql_on_server(server, "SELECT DB_NAME() AS current_database", 10)
        diagnostics["current_database"] = rows[0][0] if rows else "Unknown"
        
        # Conteo de tablas
        rows, _ = execute_sql_on_server(
            server, 
            "SELECT COUNT(*) AS table_count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'", 
            10
        )
        diagnostics["table_count"] = rows[0][0] if rows else 0
        
        return {
            **response_base,
            "success": True,
            "execution": {
                "status": "success",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "message": "Diagnóstico completado"
            },
            "preview": [diagnostics],
            "metadata": {
                "diagnostics_performed": ["version", "server_name", "current_database", "table_count"]
            }
        }
    except Exception as e:
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error_message": str(e),
                "error_code": "DIAGNOSTIC_FAILED"
            }
        }
