"""
FASE API-UQT1 — Universal Query Tester para Conexiones API
==========================================================
Endpoint AISLADO para probar conexiones API sin afectar servidores SQL.

FASE API-SEC1 — Corrección de Seguridad (Mayo 2026)
===================================================
- Nuevo endpoint /test-connection con query SQL fija controlada por backend
- Bloqueo de parámetros SQL dinámicos en universal-query-test
- Detección de patrones SQL en valores de parámetros

FUENTE: EDARSAHUB.Servidores_Conexiones (tipo_conexion = 'API_LOCAL')
SEGURIDAD: 
- Solo GET permitido
- Headers sensibles enmascarados
- Timeout obligatorio
- Autenticación requerida
- Autorización por EmpresaID/permisos
- BLOQUEO de SQL dinámico vía parámetros

NO MODIFICA:
- MongoDB
- Endpoint SQL: /api/servers/{server_id}/universal-query-test
- QueryConfigWizard
- Módulos: Comercial, Tablero, KPIs, Inventarios, Compras, Finanzas, Operaciones

Fecha: Mayo 2026
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Optional, Any, List
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse
import httpx
import time
import logging
import re

router = APIRouter(tags=["api-connections-universal-test"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES DE SEGURIDAD
# ============================================================================

SENSITIVE_HEADERS = [
    'authorization', 'api-key', 'x-api-key', 'token', 
    'password', 'secret', 'bearer', 'credentials', 'cookie',
    'x-auth-token', 'x-access-token'
]

SENSITIVE_PARAMS = [
    'token', 'key', 'api_key', 'apikey', 'password', 'secret', 
    'auth', 'credential', 'access_token', 'refresh_token'
]

SAFE_RESPONSE_HEADERS = [
    'content-type', 'content-length', 'date', 'server', 
    'cache-control', 'expires', 'last-modified', 'etag',
    'x-request-id', 'x-response-time'
]

ALLOWED_HTTP_METHODS = ['GET']
DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 60
MIN_TIMEOUT = 1

# ============================================================================
# API-SEC1: CONSTANTES DE BLOQUEO SQL
# ============================================================================

# Nombres de parámetros BLOQUEADOS (no se permite usarlos)
BLOCKED_PARAM_NAMES = [
    'sql', 'query', 'consulta', 'statement', 'command', 
    'script', 'exec', 'execute'
]

# Patrones SQL BLOQUEADOS en valores de parámetros
SQL_PATTERNS = [
    r'\bSELECT\b', r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b',
    r'\bDROP\b', r'\bALTER\b', r'\bTRUNCATE\b', r'\bEXEC\b',
    r'\bMERGE\b', r'\bCREATE\b', r'\bUNION\b', r'\bFROM\b',
    r'\bWHERE\b', r'INFORMATION_SCHEMA', r'sys\.tables',
    r'sys\.columns', r'sys\.objects', r'sysobjects', r'syscolumns'
]

# Compilar patrones para eficiencia
SQL_PATTERN_REGEX = re.compile('|'.join(SQL_PATTERNS), re.IGNORECASE)

# Query FIJA para test-connection (hardcodeada, no modificable)
FIXED_TEST_QUERY = "SELECT TOP 1 name FROM sys.tables ORDER BY name"

# ============================================================================
# MODELOS
# ============================================================================

class APIConnectionTestRequest(BaseModel):
    """Request para probar conexión API universal."""
    test_name: str
    test_type: str = "api_rest"
    method: str = "GET"
    endpoint_path: Optional[str] = ""
    query_params: Optional[Dict[str, str]] = {}
    headers: Optional[Dict[str, str]] = {}
    timeout_seconds: int = DEFAULT_TIMEOUT
    module: Optional[str] = None

# ============================================================================
# INYECCIÓN DE AUTENTICACIÓN
# ============================================================================

_verify_token = None

def set_verify_token(func):
    """Inyecta función de verificación de token desde server.py"""
    global _verify_token
    _verify_token = func

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Obtiene usuario autenticado. OBLIGATORIO para todos los endpoints."""
    if _verify_token is None:
        raise HTTPException(status_code=500, detail="Auth not configured")
    return _verify_token(credentials.credentials)

# ============================================================================
# FUNCIONES DE ACCESO A DATOS (EDARSAHUB SQL - PARAMETRIZADO)
# ============================================================================

def get_api_connection_raw_for_auth(connection_id: str) -> Optional[Dict]:
    """
    Obtiene conexión API con campos RAW para validación de permisos.
    NO descifra secretos. Solo para validación interna.
    
    USA CONSULTA PARAMETRIZADA para evitar SQL injection.
    """
    import pymssql
    import os
    
    try:
        conn = pymssql.connect(
            server=os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
            port=int(os.environ.get('EDARSAHUB_PORT', '1433')),
            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
            user=os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
            password=os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
            login_timeout=30
        )
        cursor = conn.cursor(as_dict=True)
        
        # CONSULTA PARAMETRIZADA - NO f-string
        query = """
            SELECT id, nombre, system_type, tipo_conexion, api_url, 
                   activo, EmpresaID, visible_en_operaciones
            FROM Servidores_Conexiones
            WHERE id = %s
              AND tipo_conexion = 'API_LOCAL'
        """
        cursor.execute(query, (connection_id,))
        row = cursor.fetchone()
        conn.close()
        
        return row
    except Exception as e:
        logger.error(f"[API-UQT] Error obteniendo conexión RAW: {e}")
        return None


def get_api_connection_with_secret(connection_id: str) -> Optional[Dict]:
    """
    Obtiene conexión API con api_key descifrada para uso interno.
    NUNCA exponer api_key en response.
    
    USA CONSULTA PARAMETRIZADA.
    """
    import pymssql
    import os
    
    try:
        conn = pymssql.connect(
            server=os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
            port=int(os.environ.get('EDARSAHUB_PORT', '1433')),
            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
            user=os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
            password=os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
            login_timeout=30
        )
        cursor = conn.cursor(as_dict=True)
        
        # CONSULTA PARAMETRIZADA
        query = """
            SELECT id, nombre, system_type, tipo_conexion, api_url, 
                   api_key_encrypted, activo, EmpresaID
            FROM Servidores_Conexiones
            WHERE id = %s
              AND tipo_conexion = 'API_LOCAL'
        """
        cursor.execute(query, (connection_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Descifrar api_key si existe
        api_key_decrypted = ''
        api_key_encrypted = row.get('api_key_encrypted', '')
        if api_key_encrypted:
            try:
                from core.secret_manager import decrypt_secret, is_encrypted_secret
                if is_encrypted_secret(api_key_encrypted):
                    api_key_decrypted = decrypt_secret(api_key_encrypted)
                else:
                    api_key_decrypted = api_key_encrypted
            except Exception as e:
                logger.warning(f"[API-UQT] Error descifrando API key: {e}")
                api_key_decrypted = ''
        
        return {
            'id': str(row.get('id', '')),
            'name': row.get('nombre', ''),
            'tipo': row.get('system_type', 'UNKNOWN'),
            'tipo_conexion': row.get('tipo_conexion', ''),
            'url': row.get('api_url', ''),
            'api_key': api_key_decrypted,  # Solo para uso interno
            'activo': bool(row.get('activo', False)),
            'EmpresaID': row.get('EmpresaID')
        }
    except Exception as e:
        logger.error(f"[API-UQT] Error obteniendo conexión con secreto: {e}")
        return None

# ============================================================================
# VALIDACIÓN DE AUTORIZACIÓN
# ============================================================================

async def validate_api_connection_access(current_user: Dict, connection_raw: Dict) -> bool:
    """
    Valida que el usuario tiene acceso a la conexión API.
    
    Reglas:
    - SuperAdministrador: acceso total
    - Administrador: acceso a conexiones de su empresa
    - Usuario: acceso según allowed_servers o empresa asignada
    """
    user_role = current_user.get('role', '')
    user_email = current_user.get('email', '')
    
    # SuperAdministrador: acceso total
    if user_role == 'SuperAdministrador':
        logger.info(f"[API-UQT] SuperAdmin {user_email} accede a conexión {connection_raw.get('id')}")
        return True
    
    # Obtener EmpresaID de la conexión
    connection_empresa_id = connection_raw.get('EmpresaID')
    
    # Si la conexión no tiene empresa asignada, solo SuperAdmin puede acceder
    if connection_empresa_id is None:
        logger.warning(f"[API-UQT] Conexión {connection_raw.get('id')} sin EmpresaID. Denegado para {user_email}")
        return False
    
    # Obtener contexto del usuario
    user_empresas = current_user.get('empresas', [])
    user_allowed_servers = current_user.get('allowed_servers', [])
    
    # Convertir EmpresaID a int para comparación
    try:
        connection_empresa_int = int(connection_empresa_id)
    except (ValueError, TypeError):
        connection_empresa_int = None
    
    # Administrador: verificar empresa
    if user_role == 'Administrador':
        if connection_empresa_int in user_empresas or str(connection_empresa_id) in [str(e) for e in user_empresas]:
            return True
        logger.warning(f"[API-UQT] Admin {user_email} sin acceso a empresa {connection_empresa_id}")
        return False
    
    # Usuario normal: verificar allowed_servers o empresa
    connection_id_str = str(connection_raw.get('id', ''))
    if connection_id_str in user_allowed_servers:
        return True
    if connection_empresa_int in user_empresas or str(connection_empresa_id) in [str(e) for e in user_empresas]:
        return True
    
    logger.warning(f"[API-UQT] Usuario {user_email} sin acceso a conexión {connection_raw.get('id')}")
    return False

# ============================================================================
# FUNCIONES DE SEGURIDAD - ENMASCARAMIENTO
# ============================================================================

def _mask_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Enmascara headers sensibles. SIEMPRE."""
    if not headers:
        return {}
    masked = {}
    for key, value in headers.items():
        if any(s in key.lower() for s in SENSITIVE_HEADERS):
            masked[key] = '***MASKED***'
        else:
            masked[key] = value
    return masked


def _mask_params(params: Dict[str, str]) -> Dict[str, str]:
    """Enmascara parámetros sensibles en query string."""
    if not params:
        return {}
    masked = {}
    for key, value in params.items():
        if any(s in key.lower() for s in SENSITIVE_PARAMS):
            masked[key] = '***MASKED***'
        else:
            masked[key] = value
    return masked


def _mask_url_if_sensitive(url: str) -> str:
    """Enmascara tokens o keys en la URL si existen."""
    try:
        parsed = urlparse(url)
        if parsed.query:
            params = parse_qs(parsed.query, keep_blank_values=True)
            masked_params = {}
            for key, values in params.items():
                if any(s in key.lower() for s in SENSITIVE_PARAMS):
                    masked_params[key] = ['***MASKED***']
                else:
                    masked_params[key] = values
            new_query = urlencode(masked_params, doseq=True)
            return urlunparse(parsed._replace(query=new_query))
        return url
    except Exception:
        return url


def _filter_response_headers(headers) -> Dict[str, str]:
    """Filtra response headers para devolver solo los seguros."""
    if not headers:
        return {}
    result = {}
    for k, v in dict(headers).items():
        if k.lower() in SAFE_RESPONSE_HEADERS:
            result[k] = v
    return result

# ============================================================================
# API-SEC1: VALIDACIÓN DE PARÁMETROS SQL
# ============================================================================

def _validate_no_sql_params(query_params: Dict[str, str]) -> tuple:
    """
    Valida que los parámetros NO contengan SQL dinámico.
    
    Returns:
        tuple (is_valid: bool, error_message: str or None)
    """
    if not query_params:
        return True, None
    
    blocked_found = []
    sql_pattern_found = []
    
    for key, value in query_params.items():
        key_lower = key.lower().strip()
        
        # 1. Verificar nombres de parámetros bloqueados
        if key_lower in BLOCKED_PARAM_NAMES:
            blocked_found.append(key)
            continue
        
        # 2. Verificar patrones SQL en valores
        if value and isinstance(value, str):
            if SQL_PATTERN_REGEX.search(value):
                sql_pattern_found.append(key)
    
    if blocked_found or sql_pattern_found:
        error_parts = []
        if blocked_found:
            error_parts.append(f"Parámetros bloqueados: {', '.join(blocked_found)}")
        if sql_pattern_found:
            error_parts.append(f"Contenido SQL detectado en: {', '.join(sql_pattern_found)}")
        
        error_msg = (
            "No se permite enviar SQL o comandos dinámicos mediante parámetros API en esta fase. "
            f"{'. '.join(error_parts)}. "
            "Use el botón 'Probar conexión' para validación técnica controlada."
        )
        return False, error_msg
    
    return True, None


def _validate_no_sql_in_endpoint_path(endpoint_path: str) -> tuple:
    """
    Valida que el endpoint_path no contenga SQL.
    
    Returns:
        tuple (is_valid: bool, error_message: str or None)
    """
    if not endpoint_path:
        return True, None
    
    # Verificar patrones SQL en el path
    if SQL_PATTERN_REGEX.search(endpoint_path):
        return False, "El path del endpoint contiene patrones SQL no permitidos."
    
    # Verificar si el path parece contener un query param con SQL
    if '?' in endpoint_path:
        query_part = endpoint_path.split('?', 1)[1] if '?' in endpoint_path else ''
        for blocked in BLOCKED_PARAM_NAMES:
            if f'{blocked}=' in query_part.lower():
                return False, f"El path contiene el parámetro bloqueado '{blocked}'."
    
    return True, None


# ============================================================================
# CONSTRUCCIÓN SEGURA DE URL
# ============================================================================

def _build_safe_url(base_url: str, endpoint_path: str) -> str:
    """
    Construye URL segura concatenando base_url y endpoint_path.
    
    Reglas:
    - base_url debe ser URL válida
    - endpoint_path debe ser path relativo (NO URL absoluta)
    - Evitar doble slash
    - Preservar path existente en base_url
    """
    # Validar que base_url sea URL válida
    if not base_url:
        raise ValueError("base_url no puede estar vacía")
    
    parsed_base = urlparse(base_url)
    if not parsed_base.scheme or not parsed_base.netloc:
        raise ValueError("base_url debe ser URL válida con protocolo")
    
    # Si no hay endpoint_path, retornar base_url
    if not endpoint_path:
        return base_url
    
    # Limpiar endpoint_path
    endpoint_path = endpoint_path.strip()
    
    # BLOQUEAR: endpoint_path no puede ser URL absoluta
    if endpoint_path.startswith('http://') or endpoint_path.startswith('https://'):
        raise ValueError("endpoint_path no puede ser URL absoluta externa")
    
    # BLOQUEAR: endpoint_path no puede tener protocolo
    if '://' in endpoint_path:
        raise ValueError("endpoint_path no puede contener protocolo")
    
    # BLOQUEAR: intentos de path traversal
    if '..' in endpoint_path:
        raise ValueError("endpoint_path no puede contener path traversal")
    
    # Asegurar que base_url termine con /
    if not base_url.endswith('/'):
        base_url = base_url + '/'
    
    # Asegurar que endpoint_path no comience con /
    endpoint_path = endpoint_path.lstrip('/')
    
    # Usar urljoin para concatenación segura
    full_url = urljoin(base_url, endpoint_path)
    
    return full_url

# ============================================================================
# ENDPOINT PRINCIPAL
# ============================================================================

@router.post("/api-connections/{connection_id}/universal-query-test")
async def execute_api_connection_test(
    connection_id: str,
    request: APIConnectionTestRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Ejecuta una prueba universal contra una conexión API.
    
    FUENTE: EDARSAHUB.Servidores_Conexiones (tipo_conexion = 'API_LOCAL')
    SEGURIDAD: 
    - Autenticación obligatoria
    - Autorización por EmpresaID
    - Solo GET permitido
    - Timeout obligatorio
    - Headers enmascarados
    - API-SEC1: BLOQUEO de SQL dinámico vía parámetros
    """
    start_time = time.time()
    
    # 1. AUTENTICACIÓN OBLIGATORIA
    current_user = get_current_user(credentials)
    user_email = current_user.get('email', 'unknown')
    
    logger.info(f"[API-UQT] Usuario {user_email} solicita test de conexión {connection_id}")
    
    # 2. Obtener conexión RAW para validación de permisos
    connection_raw = get_api_connection_raw_for_auth(connection_id)
    if not connection_raw:
        raise HTTPException(status_code=404, detail="Conexión API no encontrada")
    
    # 3. AUTORIZACIÓN OBLIGATORIA
    if not await validate_api_connection_access(current_user, connection_raw):
        raise HTTPException(status_code=403, detail="Sin permiso para acceder a esta conexión API")
    
    # 4. Validar que esté activa
    if not connection_raw.get('activo'):
        raise HTTPException(status_code=400, detail="Conexión API inactiva")
    
    # 5. Validar tipo de conexión
    if connection_raw.get('tipo_conexion') != 'API_LOCAL':
        raise HTTPException(status_code=400, detail="Esta conexión no es de tipo API_LOCAL")
    
    # 6. Validar método HTTP
    method = request.method.upper()
    if method not in ALLOWED_HTTP_METHODS:
        raise HTTPException(
            status_code=400, 
            detail=f"Método {method} no permitido. Solo permitido: {ALLOWED_HTTP_METHODS}"
        )
    
    # =========================================================================
    # API-SEC1: VALIDACIÓN DE SEGURIDAD SQL
    # =========================================================================
    
    # 6a. Validar que query_params NO contengan SQL
    params_valid, params_error = _validate_no_sql_params(request.query_params or {})
    if not params_valid:
        logger.warning(f"[API-SEC1] Usuario {user_email} intentó enviar SQL vía params: {params_error}")
        raise HTTPException(status_code=400, detail=params_error)
    
    # 6b. Validar que endpoint_path NO contenga SQL
    path_valid, path_error = _validate_no_sql_in_endpoint_path(request.endpoint_path or '')
    if not path_valid:
        logger.warning(f"[API-SEC1] Usuario {user_email} intentó enviar SQL vía path: {path_error}")
        raise HTTPException(status_code=400, detail=path_error)
    
    # 6c. Validar que headers NO contengan SQL en valores
    for header_key, header_value in (request.headers or {}).items():
        if header_value and SQL_PATTERN_REGEX.search(str(header_value)):
            logger.warning(f"[API-SEC1] Usuario {user_email} intentó enviar SQL vía header: {header_key}")
            raise HTTPException(
                status_code=400, 
                detail=f"El header '{header_key}' contiene patrones SQL no permitidos."
            )
    
    # =========================================================================
    # FIN API-SEC1
    # =========================================================================
    
    # 7. Validar timeout
    timeout = max(MIN_TIMEOUT, min(request.timeout_seconds, MAX_TIMEOUT))
    
    # 8. Obtener conexión con secreto descifrado (solo para uso interno)
    connection = get_api_connection_with_secret(connection_id)
    if not connection:
        raise HTTPException(status_code=500, detail="Error obteniendo configuración de conexión")
    
    # 9. Construir URL segura
    base_url = connection.get('url', '')
    try:
        full_url = _build_safe_url(base_url, request.endpoint_path or '')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"URL inválida: {e}")
    
    # 10. Preparar headers (incluir API key si existe, pero NUNCA exponer)
    headers = dict(request.headers or {})
    headers['Content-Type'] = 'application/json'
    api_key = connection.get('api_key', '')
    if api_key:
        headers['x-api-key'] = api_key  # Usar x-api-key en lugar de Bearer para APIs locales
    
    # 11. Response base (sin secretos)
    response_base = {
        "test_name": request.test_name,
        "test_type": request.test_type,
        "module": request.module,
        "connection": {
            "id": connection_id,
            "name": connection.get('name'),
            "system_type": connection.get('tipo'),
            "base_url": base_url  # URL base sin secretos
            # NO incluir: api_key, api_key_encrypted, Authorization
        }
    }
    
    # 12. Ejecutar request
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=full_url,
                headers=headers,
                params=request.query_params or {}
            )
            
            # Parsear respuesta
            try:
                preview = response.json()
            except Exception:
                text = response.text
                preview = text[:1000] if len(text) > 1000 else text
            
            return {
                **response_base,
                "success": response.status_code < 400,
                "execution": {
                    "status": "success" if response.status_code < 400 else "error",
                    "response_time_ms": int((time.time() - start_time) * 1000),
                    "http_status": response.status_code,
                    "url_executed": _mask_url_if_sensitive(full_url),
                    "method": method,
                    "headers_sent": _mask_headers(headers),
                    "params_sent": _mask_params(request.query_params or {})
                },
                "preview": preview,
                "metadata": {
                    "response_headers": _filter_response_headers(response.headers),
                    "content_length": len(response.content)
                }
            }
    
    except httpx.TimeoutException:
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error_message": f"Timeout después de {timeout} segundos",
                "error_code": "TIMEOUT"
            },
            "preview": None,
            "metadata": {}
        }
    
    except httpx.ConnectError:
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error_message": "Error de conexión: No se pudo conectar al servidor",
                "error_code": "CONNECTION_ERROR"
            },
            "preview": None,
            "metadata": {}
        }
    
    except Exception as e:
        logger.error(f"[API-UQT] Error ejecutando test: {e}")
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error_message": str(e),
                "error_code": "EXECUTION_ERROR"
            },
            "preview": None,
            "metadata": {}
        }


# ============================================================================
# API-SEC1: ENDPOINT SEGURO DE TEST DE CONEXIÓN
# ============================================================================

@router.post("/api-connections/{connection_id}/test-connection")
async def test_api_connection_secure(
    connection_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    API-SEC1: Test de conexión API con consulta SQL FIJA.
    
    Este endpoint ejecuta una consulta técnica fija y segura definida por backend.
    El usuario NO puede enviar SQL, headers, ni parámetros arbitrarios.
    
    Query fija: SELECT TOP 1 name FROM sys.tables ORDER BY name
    
    SEGURIDAD:
    - Autenticación obligatoria
    - Autorización por EmpresaID
    - SQL hardcodeado en backend (NO viene de frontend)
    - API key obtenida internamente (NO viene de frontend)
    - Response NO expone secretos
    
    Response exitoso:
    {
        "success": true,
        "connection": {"id": "...", "name": "..."},
        "execution": {"status": "success", "http_status": 200, "response_time_ms": ...},
        "preview": {"table_sample": "NombreTabla"},
        "message": "Conexión validada correctamente"
    }
    """
    start_time = time.time()
    
    # 1. AUTENTICACIÓN OBLIGATORIA
    current_user = get_current_user(credentials)
    user_email = current_user.get('email', 'unknown')
    
    logger.info(f"[API-SEC1] Usuario {user_email} solicita test-connection para {connection_id}")
    
    # 2. Obtener conexión RAW para validación de permisos
    connection_raw = get_api_connection_raw_for_auth(connection_id)
    if not connection_raw:
        raise HTTPException(status_code=404, detail="Conexión API no encontrada")
    
    # 3. AUTORIZACIÓN OBLIGATORIA
    if not await validate_api_connection_access(current_user, connection_raw):
        raise HTTPException(status_code=403, detail="Sin permiso para acceder a esta conexión API")
    
    # 4. Validar que esté activa
    if not connection_raw.get('activo'):
        raise HTTPException(status_code=400, detail="Conexión API inactiva")
    
    # 5. Validar tipo de conexión
    if connection_raw.get('tipo_conexion') != 'API_LOCAL':
        raise HTTPException(status_code=400, detail="Esta conexión no es de tipo API_LOCAL")
    
    # 6. Obtener conexión con secreto descifrado (solo para uso interno)
    connection = get_api_connection_with_secret(connection_id)
    if not connection:
        raise HTTPException(status_code=500, detail="Error obteniendo configuración de conexión")
    
    # 7. Construir URL para el endpoint /query de la API local
    base_url = connection.get('url', '')
    if not base_url:
        raise HTTPException(status_code=400, detail="URL de la conexión no configurada")
    
    # La URL base debería apuntar al endpoint /query
    # Si ya termina en /query, usarla directamente
    # Si no, asumimos que es la base y agregamos /query
    if not base_url.endswith('/query'):
        if base_url.endswith('/'):
            base_url = base_url + 'query'
        else:
            base_url = base_url  # Asumir que ya es el endpoint correcto
    
    # 8. Preparar headers con API key (obtenida internamente, NO de frontend)
    headers = {
        'Content-Type': 'application/json'
    }
    api_key = connection.get('api_key', '')
    if api_key:
        headers['x-api-key'] = api_key  # API key desde secret manager, NO de frontend
    
    # 9. Preparar parámetros con la query FIJA (hardcodeada, NO de frontend)
    # FIXED_TEST_QUERY = "SELECT TOP 1 name FROM sys.tables ORDER BY name"
    query_params = {
        'sql': FIXED_TEST_QUERY  # Query fija definida en constantes
    }
    
    # 10. Response base (sin secretos)
    response_base = {
        "connection": {
            "id": connection_id,
            "name": connection.get('name', 'Unknown')
            # NO incluir: api_key, url completa con secretos, etc.
        }
    }
    
    # 11. Ejecutar request a la API local
    timeout = 30  # Timeout fijo para test de conexión
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                base_url,
                headers=headers,
                params=query_params
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Parsear respuesta
            preview_data = None
            table_sample = None
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    # Extraer el nombre de la primera tabla como sample
                    if isinstance(json_response, list) and len(json_response) > 0:
                        first_row = json_response[0]
                        if isinstance(first_row, dict) and 'name' in first_row:
                            table_sample = first_row['name']
                    elif isinstance(json_response, dict):
                        # Podría venir en otro formato
                        if 'data' in json_response and isinstance(json_response['data'], list):
                            if len(json_response['data']) > 0:
                                first_row = json_response['data'][0]
                                if isinstance(first_row, dict) and 'name' in first_row:
                                    table_sample = first_row['name']
                except Exception:
                    pass
                
                preview_data = {"table_sample": table_sample} if table_sample else {"raw_status": "OK"}
                
                logger.info(f"[API-SEC1] Test exitoso para {connection_id}. Tabla sample: {table_sample}")
                
                return {
                    **response_base,
                    "success": True,
                    "execution": {
                        "status": "success",
                        "http_status": response.status_code,
                        "response_time_ms": response_time_ms
                    },
                    "preview": preview_data,
                    "message": "Conexión validada correctamente"
                }
            else:
                # Error HTTP pero la API respondió
                error_text = response.text[:200] if response.text else "Sin detalles"
                
                logger.warning(f"[API-SEC1] Test fallido para {connection_id}. HTTP {response.status_code}")
                
                return {
                    **response_base,
                    "success": False,
                    "execution": {
                        "status": "error",
                        "http_status": response.status_code,
                        "response_time_ms": response_time_ms,
                        "error_message": f"HTTP {response.status_code}: {error_text}",
                        "error_code": "HTTP_ERROR"
                    },
                    "preview": None,
                    "message": f"Error HTTP {response.status_code}"
                }
    
    except httpx.TimeoutException:
        response_time_ms = int((time.time() - start_time) * 1000)
        logger.warning(f"[API-SEC1] Timeout para {connection_id} después de {timeout}s")
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": response_time_ms,
                "error_message": f"Timeout después de {timeout} segundos",
                "error_code": "TIMEOUT"
            },
            "preview": None,
            "message": "Timeout de conexión"
        }
    
    except httpx.ConnectError:
        response_time_ms = int((time.time() - start_time) * 1000)
        logger.warning(f"[API-SEC1] Error de conexión para {connection_id}")
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": response_time_ms,
                "error_message": "No se pudo conectar al servidor",
                "error_code": "CONNECTION_ERROR"
            },
            "preview": None,
            "message": "Error de conexión"
        }
    
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"[API-SEC1] Error inesperado para {connection_id}: {e}")
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": response_time_ms,
                "error_message": str(e)[:200],
                "error_code": "EXECUTION_ERROR"
            },
            "preview": None,
            "message": "Error de ejecución"
        }
