"""
FASE API-UQT1 — Universal Query Tester para Conexiones API
==========================================================
Endpoint AISLADO para probar conexiones API sin afectar servidores SQL.

FUENTE: EDARSAHUB.Servidores_Conexiones (tipo_conexion = 'API_LOCAL')
SEGURIDAD: 
- Solo GET permitido
- Headers sensibles enmascarados
- Timeout obligatorio
- Autenticación requerida
- Autorización por EmpresaID/permisos

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
        headers['Authorization'] = f'Bearer {api_key}'
    
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
    
    except httpx.ConnectError as e:
        return {
            **response_base,
            "success": False,
            "execution": {
                "status": "error",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error_message": f"Error de conexión: No se pudo conectar al servidor",
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
