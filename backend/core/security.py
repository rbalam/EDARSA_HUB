
# P5-05 Auth token compatibility helper
def _p5_extract_usuario_id_from_payload(payload):
    if not isinstance(payload, dict):
        return None
    return (
        payload.get("sub")
        or payload.get("user_id")
        or payload.get("usuario_id")
        or payload.get("IDUsuario")
        or payload.get("id")
    )


# P4-07 SQL-FIRST RBAC SECURITY
from core.access_context.sql_context import (
    build_user_access_context as build_user_access_context_sql,
)

from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
from core.rbac_helper_sql import es_superadmin, es_admin
"""
EDARSA HUB - Seguridad y Autenticación
======================================
Funciones de seguridad, hashing de contraseñas, JWT y permisos.

FASE 2 DEL REFACTOR MODULAR (Diciembre 2025):
- Migrado: hash_password(), verify_password()
- Migrado: create_token(), verify_token()
- Migrado: get_current_user() con inyección de dependencia de DB
- Migrado: user_has_server_access(), filter_servers_by_permissions(), filter_sucursales_by_permissions()

COMPATIBILIDAD:
- server.py importa desde aquí y re-exporta para código existente
- La conexión a MongoDB se inyecta vía init_security()
- Todos los 183 endpoints con Depends(get_current_user) siguen funcionando

USO:
    from core.security import get_current_user, hash_password, verify_password
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import jwt

# ============================================================================
# CONFIGURACIÓN JWT
# ============================================================================

# JWT_SECRET: OBLIGATORIO en .env - Sin fallback inseguro para producción
JWT_SECRET: str = os.environ.get('JWT_SECRET', '')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET no configurado en .env - Requerido para operación")

JWT_ALGORITHM: str = 'HS256'

# JWT_EXPIRATION_HOURS: Configurable vía .env, default 72 horas (3 días)
# NOTA: Este es el valor LEGACY. Para refresh tokens, usar ACCESS_TOKEN_MINUTES
JWT_EXPIRATION_HOURS: int = int(os.environ.get('JWT_EXPIRATION_HOURS', '72'))

# FASE A P1-REFRESH-TOKENS: Nuevas configuraciones para tokens cortos
# ACCESS_TOKEN_MINUTES: Duración del access token (default 15 minutos)
ACCESS_TOKEN_MINUTES: int = int(os.environ.get('ACCESS_TOKEN_MINUTES', '15'))

# HTTPBearer para extraer token de Authorization header
security = HTTPBearer()

# ============================================================================
# FASE 2-D.1: FEATURE FLAG SQL-FIRST AUTH
# ============================================================================
# IMPORTANTE: Este flag DEBE estar apagado hasta que se autorice FASE 2-E.
# Valor por defecto: false (MongoDB sigue siendo la fuente productiva)

AUTH_SQL_FIRST_ENABLED: bool = os.environ.get('AUTH_SQL_FIRST_ENABLED', 'false').lower() == 'true'

# ============================================================================
# INYECCIÓN DE DEPENDENCIA: MongoDB
# ============================================================================
# La conexión a MongoDB se inyecta desde server.py para evitar imports circulares
# y mantener la misma instancia de conexión.

_db = None  # Se inicializa vía init_security()


def init_security(database) -> None:
    """
    Inicializa el módulo de seguridad con la conexión a MongoDB.
    Debe llamarse desde server.py después de crear la conexión.
    
    Args:
        database: Instancia de Any o None para usar stub
    """
    global _db
    if database is None:
        # Usar stub database cuando se pasa None (modo 100% SQL)
        from core.mongo_stub import get_stub_database
        _db = get_stub_database()
        logging.info("[SECURITY] Módulo de seguridad inicializado con StubDatabase (modo SQL)")
    else:
        _db = database
        logging.info("[SECURITY] Módulo de seguridad inicializado con conexión a MongoDB")


def get_db():
    """Obtiene la conexión a MongoDB inyectada."""
    if _db is None:
        raise RuntimeError("Security module not initialized. Call init_security(db) first.")
    return _db


# ============================================================================
# FUNCIONES DE HASHING DE CONTRASEÑAS
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Contraseña hasheada como string
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifica una contraseña contra su hash bcrypt.
    
    Args:
        password: Contraseña en texto plano
        hashed: Hash almacenado en BD
        
    Returns:
        True si coincide, False si no
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ============================================================================
# FUNCIONES JWT
# ============================================================================

def create_token(user_id: str, email: str, role: str) -> str:
    """
    Crea un token JWT firmado con duración LEGACY (72 horas).
    
    NOTA: Esta función se mantiene por compatibilidad.
    Para refresh tokens, usar create_access_token() que usa ACCESS_TOKEN_MINUTES.
    
    Args:
        user_id: ID del usuario
        email: Email del usuario
        role: Rol del usuario (Administrador, Supervisor, Usuario)
        
    Returns:
        Token JWT firmado como string
    """
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: str, email: str, role: str, token_type: str = "internal") -> str:
    """
    FASE A P1-REFRESH-TOKENS: Crea un access token JWT de corta duración.
    
    Args:
        user_id: ID del usuario
        email: Email del usuario
        role: Rol del usuario
        token_type: Tipo de token ('internal' o 'portal_supplier')
        
    Returns:
        Token JWT firmado (duración: ACCESS_TOKEN_MINUTES)
    """
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'type': token_type,  # Para separación interno/portal
        'exp': datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verifica y decodifica un token JWT.
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        Payload decodificado como diccionario
        
    Raises:
        HTTPException 401: Si el token es inválido o expirado
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


# ============================================================================
# DEPENDENCY: GET CURRENT USER
# ============================================================================

# Nombre de la cookie de autenticación
AUTH_COOKIE_NAME = "edarsa_access_token"
# Tiempo de vida de la cookie LEGACY (72 horas)
AUTH_COOKIE_MAX_AGE = JWT_EXPIRATION_HOURS * 60 * 60
# FASE A P1-REFRESH-TOKENS: Tiempo de vida para access tokens cortos (15 min)
AUTH_COOKIE_MAX_AGE_SHORT = ACCESS_TOKEN_MINUTES * 60


def set_auth_cookie(response, token: str, short_lived: bool = False) -> None:
    """
    Establece la cookie de autenticación httpOnly.
    
    FASE AUTH-SECURITY-01: Implementación de cookies seguras.
    FASE A P1-REFRESH-TOKENS: Soporte para access tokens cortos.
    
    Args:
        response: FastAPI Response object
        token: JWT token a guardar en cookie
        short_lived: Si es True, usa ACCESS_TOKEN_MINUTES en vez de JWT_EXPIRATION_HOURS
    """
    # En producción: secure=True (solo HTTPS)
    # En desarrollo: secure=False para localhost
    is_production = os.environ.get("ENV", "production").lower() == "production"
    
    # Determinar max_age según el tipo de token
    max_age = AUTH_COOKIE_MAX_AGE_SHORT if short_lived else AUTH_COOKIE_MAX_AGE
    
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/",
        max_age=max_age
    )


def clear_auth_cookie(response) -> None:
    """
    Elimina la cookie de autenticación.
    
    FASE AUTH-SECURITY-01: Logout con cookies.
    
    Args:
        response: FastAPI Response object
    """
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/"
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI Dependency para obtener el usuario actual desde el token JWT.
    
    FASE 2-G: SQL-only (sin fallback MongoDB).
    
    Flujo:
    1. Verificar token JWT
    2. Buscar usuario en EDARSAHUB SQL
    3. Si no existe en SQL, rechazar con 401
    
    Args:
        credentials: Credenciales HTTP Bearer extraídas automáticamente por FastAPI
        
    Returns:
        Diccionario con datos del usuario (sin _id ni password)
        
    Raises:
        HTTPException 401: Token inválido, expirado o usuario no encontrado
    """
    token = credentials.credentials
    payload = verify_token(token)
    email = payload.get('email')
    user_id_from_token = payload.get('user_id')
    
    # FASE 2-G: SQL-only (sin fallback MongoDB)
    user, auth_source = await _get_user_sql_only(email, user_id_from_token)
    
    if not user:
        logging.warning(f"[AUTH] Usuario no encontrado en SQL: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Usuario no autorizado"
        )
    
    # Verificar si usuario está activo
    if not user.get('active', True):
        logging.warning(f"[AUTH] Usuario inactivo: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario desactivado"
        )
    
    # Log de auditoría seguro (sin secretos)
    logging.info(f"[AUTH] auth_source={auth_source}, email={email}, role={user.get('role', 'N/A')}")
    
    return user


async def _get_user_sql_only(email: str, user_id_from_token: str = None) -> tuple:
    """
    P5-07: Obtiene usuario SOLO de SQL (Usuario_Catalogo).
    Sin fallback a MongoDB.
    
    Args:
        email: Email del usuario
        user_id_from_token: user_id del JWT (PublicUUID o MongoLegacyID)
        
    Returns:
        tuple: (user_dict, auth_source)
    """
    from modules.auth.repository import AuthRepository
    
    user = None
    auth_source = "SQL_NOT_FOUND"
    
    try:
        # Primero intentar por user_id si existe
        if user_id_from_token:
            user = AuthRepository.get_user_by_id(user_id_from_token)
        
        # Si no encontró por ID, intentar por email
        if not user and email:
            user = AuthRepository.get_user_by_email(email)
        
        if user:
            auth_source = user.get("auth_source", "SQL_USUARIO_CATALOGO")
            logging.debug(f"[AUTH-SQL] Usuario resuelto desde SQL: {email}")
            return user, auth_source
        
        logging.info(f"[AUTH-SQL] Usuario no encontrado en SQL: {email}")
        return None, "SQL_NOT_FOUND"
            
    except Exception as e:
        logging.error(f"[AUTH-SQL] Error SQL: {str(e)[:200]}")
        return None, "SQL_ERROR"


def _validate_sql_user_structure(user: Dict[str, Any]) -> bool:
    """
    Valida que el usuario SQL tiene la estructura mínima requerida.
    
    Args:
        user: Dict del usuario de SQL
        
    Returns:
        True si la estructura es válida
    """
    if not user:
        return False
    
    # Campos obligatorios
    required_fields = ['id', 'email', 'role']
    
    for field in required_fields:
        if not user.get(field):
            logging.warning(f"[AUTH-SQL] Usuario SQL sin campo obligatorio: {field}")
            return False
    
    # Validar que 'id' parece un UUID (no un int)
    user_id = user.get('id', '')
    if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()):
        logging.warning(f"[AUTH-SQL] user['id'] no es UUID: {user_id}")
        return False
    
    return True


async def get_current_user_dual(request) -> Dict[str, Any]:
    """
    FastAPI Dependency DUAL para obtener el usuario desde Header O Cookie.
    
    FASE AUTH-SECURITY-01: Soporte dual para transición gradual.
    
    Prioridad de lectura:
    1. Header Authorization: Bearer <token> (si existe)
    2. Cookie edarsa_access_token (si existe)
    3. 401 Unauthorized (si ninguno existe)
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Diccionario con datos del usuario (sin _id ni password)
        
    Raises:
        HTTPException 401: Sin autenticación o token inválido
        HTTPException 404: Usuario no encontrado en BD
    """
    token = None
    
    # Prioridad 1: Header Authorization
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        extracted_token = auth_header.replace("Bearer ", "").strip()
        # FASE AUTH-SECURITY-01 FASE 4: Ignorar tokens inválidos del frontend legacy
        # que envían "null", "undefined" o string vacío
        if extracted_token and extracted_token not in ("null", "undefined", ""):
            token = extracted_token
    
    # Prioridad 2: Cookie (si no hay header válido)
    if not token:
        token = request.cookies.get(AUTH_COOKIE_NAME)
    
    # Sin autenticación
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Verificar token
    try:
        payload = verify_token(token)
    except HTTPException:
        raise  # Re-lanzar 401 de verify_token
    
    email = payload.get('email')
    user_id_from_token = payload.get('user_id')
    
    # FASE 2-G: SQL-only (sin fallback MongoDB)
    user, auth_source = await _get_user_sql_only(email, user_id_from_token)
    
    if not user:
        logging.warning(f"[AUTH-DUAL] Usuario no encontrado en SQL: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Usuario no autorizado"
        )
    
    # Verificar si usuario está activo
    if not user.get('active', True):
        logging.warning(f"[AUTH-DUAL] Usuario inactivo: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario desactivado"
        )
    
    # Log de auditoría seguro
    logging.info(f"[AUTH-DUAL] auth_source={auth_source}, email={email}")
    
    return user


def get_current_user_dual_dependency():
    """
    Factory para crear la dependencia dual.
    
    Uso:
        @router.get("/protected")
        async def endpoint(user: Dict = Depends(get_current_user_dual_dependency())):
    """
    from fastapi import Request
    
    async def dependency(request: Request) -> Dict[str, Any]:
        return await get_current_user_dual(request)
    
    return dependency


# ============================================================================
# FUNCIONES DE PERMISOS - MODELO NUEVO (FASE 3)
# ============================================================================

async def get_user_empresas_permitidas(user: Dict[str, Any]) -> List[str]:
    """
    Obtiene las empresas permitidas para un usuario.
    FASE 3-H: Migrado a EDARSAHUB SQL.
    
    Returns:
        Lista de empresa_ids permitidos (UUIDs MongoDB para compatibilidad)
    """
    import pymssql
    
    def _get_all_empresas_sql() -> List[str]:
        """Obtiene todas las empresas activas desde SQL."""
        conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.EmpresaMongoUUID
                FROM Sistema_Empresas e
                JOIN Sistema_EmpresasMongoMap m ON e.EmpresaID = m.EmpresaID_SQL
                WHERE e.Activo = 1
                ORDER BY e.EmpresaID
            ''')
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # SuperAdministrador tiene acceso a todas las empresas (RBAC canónico)
    if es_superadmin(user):
        return _get_all_empresas_sql()
    
    # Nuevo modelo: empresas_permitidas (ya viene del user dict resuelto desde SQL)
    if user.get('empresas_permitidas'):
        return user['empresas_permitidas']
    
    # Fallback legacy: Si es Administrador (canónico ADMIN/SUPERADMIN), todas las empresas
    if es_admin(user):
        return _get_all_empresas_sql()
    
    # Sin acceso
    return []


async def get_servers_for_empresas(empresa_ids: List[str]) -> List[str]:
    """
    Obtiene los server_ids asociados a una lista de empresas.
    FASE 3-H: Migrado a EDARSAHUB SQL.
    
    Returns:
        Lista de server_ids (UUIDs lowercase)
    """
    if not empresa_ids:
        return []
    
    import pymssql
    
    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    try:
        cursor = conn.cursor()
        
        # Construir IN clause para empresas (UUIDs MongoDB)
        placeholders = ', '.join(['%s'] * len(empresa_ids))
        
        cursor.execute(f'''
            SELECT DISTINCT LOWER(CAST(m.ServidorID AS VARCHAR(36))) as ServidorID
            FROM Sistema_SucursalServidorMapeo m
            JOIN Sistema_Sucursales s ON m.SucursalID = s.SucursalID
            JOIN Sistema_EmpresasMongoMap em ON s.EmpresaID = em.EmpresaID_SQL
            WHERE em.EmpresaMongoUUID IN ({placeholders})
              AND m.Activo = 1
              AND s.Activo = 1
        ''', tuple(empresa_ids))
        
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


async def user_has_empresa_access(user: Dict[str, Any], empresa_id: str) -> bool:
    """
    Verifica si un usuario tiene acceso a una empresa específica.
    FASE 3: Autorización basada en empresas.
    
    Returns:
        True si tiene acceso, False si no
    """
    empresas_permitidas = await get_user_empresas_permitidas(user)
    return empresa_id in empresas_permitidas


async def filter_by_user_context(
    user: Dict[str, Any],
    items: List[Dict],
    entity_type: str = 'empresa'
) -> List[Dict]:
    """
    Filtra items según el contexto del usuario.
    FASE 3: Filtrado basado en empresas/sucursales.
    
    Args:
        user: Diccionario del usuario
        items: Lista de items a filtrar
        entity_type: 'empresa', 'sucursal' o 'server'
    
    Returns:
        Lista filtrada
    """
    empresas_permitidas = await get_user_empresas_permitidas(user)
    
    if not empresas_permitidas:
        return []
    
    if entity_type == 'empresa':
        return [i for i in items if i.get('id') in empresas_permitidas or i.get('empresa_id') in empresas_permitidas]
    
    elif entity_type == 'sucursal':
        return [i for i in items if i.get('empresa_id') in empresas_permitidas]
    
    elif entity_type == 'server':
        # Traducir empresas a servidores permitidos
        servers_permitidos = await get_servers_for_empresas(empresas_permitidas)
        return [i for i in items if i.get('id') in servers_permitidos or i.get('server_id') in servers_permitidos]
    
    return items


# ============================================================================
# FUNCIONES DE PERMISOS - MODELO LEGACY (compatibilidad)
# ============================================================================

def user_has_server_access(user: Dict[str, Any], server_id: str) -> bool:
    """
    Verifica si un usuario tiene acceso a un servidor específico.
    
    Args:
        user: Diccionario del usuario
        server_id: ID del servidor a verificar
        
    Returns:
        True si tiene acceso, False si no
    """
    # SuperAdministrador y Administrador tienen acceso full
    if user.get('role') in ['SuperAdministrador', 'Administrador']:
        return True
    allowed = user.get('allowed_servers', [])
    return server_id in allowed if allowed else False


def filter_servers_by_permissions(servers: List[Dict], user: Dict[str, Any]) -> List[Dict]:
    """
    Filtra una lista de servidores según los permisos del usuario.
    
    Args:
        servers: Lista de servidores
        user: Diccionario del usuario
        
    Returns:
        Lista filtrada de servidores a los que el usuario tiene acceso
    """
    role = user.get('role', '')
    logging.info(f"filter_servers: role={role}, total_servers={len(servers)}")
    
    # SuperAdministrador y Administrador tienen acceso full (canónico SQL)
    from core.rbac_helper_sql import es_admin
    if es_admin(user):
        logging.info(f"Usuario es {role}, retornando todos los servidores")
        return servers
    
    allowed = user.get('allowed_servers', [])
    if not allowed:
        logging.info("Usuario sin servidores asignados, retornando lista vacía")
        return []
    
    filtered = [s for s in servers if s.get('id') in allowed]
    logging.info(f"Filtrado: {len(filtered)} servidores")
    return filtered


def filter_sucursales_by_permissions(
    sucursales: List[Dict], 
    user: Dict[str, Any], 
    server_id: str
) -> List[Dict]:
    """
    Filtra sucursales según permisos del usuario para un servidor específico.
    
    Args:
        sucursales: Lista de sucursales
        user: Diccionario del usuario
        server_id: ID del servidor
        
    Returns:
        Lista filtrada de sucursales
    """
    # SuperAdministrador y Administrador tienen acceso full
    if user.get('role') in ['SuperAdministrador', 'Administrador']:
        return sucursales
    
    allowed_suc = user.get('allowed_sucursales', {})
    if server_id not in allowed_suc or not allowed_suc[server_id]:
        return sucursales  # Sin restricción = ver todas
    
    return [s for s in sucursales if s.get('id') in allowed_suc[server_id]]


# ============================================================================
# EXPORTACIONES PÚBLICAS
# ============================================================================

__all__ = [
    # Inicialización
    'init_security',
    'get_db',
    # Configuración (para portal_proveedores que necesita JWT_SECRET)
    'JWT_SECRET',
    'JWT_ALGORITHM',
    'JWT_EXPIRATION_HOURS',
    'security',
    # Hashing
    'hash_password',
    'verify_password',
    # JWT
    'create_token',
    'verify_token',
    # Dependency
    'get_current_user',
    # FASE AUTH-SECURITY-01: Soporte dual cookie + header
    'AUTH_COOKIE_NAME',
    'AUTH_COOKIE_MAX_AGE',
    'set_auth_cookie',
    'clear_auth_cookie',
    'get_current_user_dual',
    'get_current_user_dual_dependency',
    # Permisos - Nuevo modelo FASE 3
    'get_user_empresas_permitidas',
    'get_servers_for_empresas',
    'user_has_empresa_access',
    'filter_by_user_context',
    # Permisos - Legacy (compatibilidad)
    'user_has_server_access',
    'filter_servers_by_permissions',
    'filter_sucursales_by_permissions',
    # FASE 2-D.1: Preflight SQL-First (legacy - ya no usado)
    'AUTH_SQL_FIRST_ENABLED',
    'compare_user_mongo_vs_sql_passive',
    'log_auth_preflight_status',
    # FASE 2-G: SQL-Only (sin fallback MongoDB)
    '_get_user_sql_only',
    '_validate_sql_user_structure',
]


# ============================================================================
# FASE 2-D.1: PREFLIGHT SQL-FIRST AUTH (COMPARACIÓN PASIVA)
# ============================================================================
# IMPORTANTE:
# - Estas funciones NO cambian el comportamiento productivo
# - MongoDB sigue siendo la fuente de autenticación
# - Solo comparan de forma pasiva para validar que SQL está listo
# - NO loggear passwords, hashes ni tokens completos

def _safe_user_for_log(user: Optional[Dict[str, Any]], source: str) -> Dict[str, Any]:
    """
    Genera versión segura de usuario para logging (sin secretos).
    """
    if not user:
        return {'source': source, 'exists': False}
    
    return {
        'source': source,
        'exists': True,
        'id': user.get('id', 'N/A'),
        'email': user.get('email', 'N/A'),
        'role': user.get('role', user.get('rol', 'N/A')),
        'active': user.get('active', user.get('activo', 'N/A')),
        'empresas_count': len(user.get('empresas_permitidas', [])),
        'empresa_default': user.get('empresa_default_id', 'N/A'),
        'has_password_hash': bool(user.get('password')),
    }


def compare_user_mongo_vs_sql_passive(user_mongo: Dict[str, Any], email: str) -> Dict[str, Any]:
    """
    FASE 2-D.1: Comparación pasiva MongoDB vs SQL.
    
    NO cambia el comportamiento productivo.
    NO loggea secretos (password, hash, token).
    
    Args:
        user_mongo: Usuario obtenido de MongoDB (actual productivo)
        email: Email para buscar en SQL
        
    Returns:
        Dict con resultado de comparación
    """
    from core.auth.user_repository_sql import AuthRepositorySQL
    
    result = {
        'email': email,
        'auth_source': 'MONGODB_CURRENT',
        'auth_sql_ready': False,
        'auth_sql_diff': False,
        'differences': [],
        'mongo': _safe_user_for_log(user_mongo, 'MONGODB'),
        'sql': None,
    }
    
    try:
        repo_sql = AuthRepositorySQL()
        user_sql = repo_sql.get_user_by_email_sql(email)
        
        if not user_sql:
            result['differences'].append('Usuario no existe en SQL')
            result['sql'] = _safe_user_for_log(None, 'SQL')
            return result
        
        result['sql'] = _safe_user_for_log(user_sql, 'SQL')
        result['auth_sql_ready'] = True
        
        # Comparar campos críticos
        differences = []
        
        # ID (PublicUUID vs MongoDB id)
        mongo_id = user_mongo.get('id')
        sql_id = user_sql.get('id')
        if mongo_id != sql_id:
            differences.append(f'id: mongo={mongo_id} vs sql={sql_id}')
        
        # Role
        mongo_role = user_mongo.get('role', user_mongo.get('rol'))
        sql_role = user_sql.get('role')
        if mongo_role != sql_role:
            differences.append(f'role: mongo={mongo_role} vs sql={sql_role}')
        
        # Active
        mongo_active = user_mongo.get('active', user_mongo.get('activo', False))
        sql_active = user_sql.get('active', False)
        if bool(mongo_active) != bool(sql_active):
            differences.append(f'active: mongo={mongo_active} vs sql={sql_active}')
        
        # Empresas permitidas (contar, no listar UUIDs completos)
        mongo_empresas = set(user_mongo.get('empresas_permitidas', []))
        sql_empresas = set(user_sql.get('empresas_permitidas', []))
        if mongo_empresas != sql_empresas:
            only_mongo = len(mongo_empresas - sql_empresas)
            only_sql = len(sql_empresas - mongo_empresas)
            if only_mongo > 0:
                differences.append(f'empresas: {only_mongo} solo en mongo')
            if only_sql > 0:
                differences.append(f'empresas: {only_sql} solo en sql')
        
        # Empresa default
        mongo_default = user_mongo.get('empresa_default_id')
        sql_default = user_sql.get('empresa_default_id')
        if mongo_default != sql_default:
            differences.append(f'empresa_default: mongo={mongo_default} vs sql={sql_default}')
        
        # Password hash presente (no comparar el hash en sí)
        mongo_has_hash = bool(user_mongo.get('password'))
        sql_has_hash = bool(user_sql.get('password'))
        if mongo_has_hash != sql_has_hash:
            differences.append(f'has_password: mongo={mongo_has_hash} vs sql={sql_has_hash}')
        
        if differences:
            result['auth_sql_diff'] = True
            result['differences'] = differences
        
        return result
        
    except Exception as e:
        result['differences'].append(f'Error SQL: {str(e)[:100]}')
        return result


def log_auth_preflight_status(user_mongo: Dict[str, Any], email: str) -> None:
    """
    FASE 2-D.1: Loggea estado de preflight de forma segura.
    
    NO loggea:
    - Passwords o hashes
    - Tokens completos
    - UUIDs de empresas (solo conteos)
    
    Args:
        user_mongo: Usuario de MongoDB
        email: Email del usuario
    """
    if not AUTH_SQL_FIRST_ENABLED:
        # Flag apagado: comparación pasiva en background
        try:
            comparison = compare_user_mongo_vs_sql_passive(user_mongo, email)
            
            # Log estructurado sin secretos
            log_data = {
                'event': 'auth_preflight',
                'email': email,
                'auth_source': comparison['auth_source'],
                'auth_sql_ready': comparison['auth_sql_ready'],
                'auth_sql_diff': comparison['auth_sql_diff'],
                'diff_count': len(comparison['differences']),
            }
            
            if comparison['auth_sql_diff']:
                log_data['differences'] = comparison['differences']
            
            logging.info(f"[AUTH-PREFLIGHT] {log_data}")
            
        except Exception as e:
            logging.warning(f"[AUTH-PREFLIGHT] Error en comparación pasiva: {str(e)[:100]}")
    else:
        # Flag encendido: esto solo debería pasar en FASE 2-E
        logging.info(f"[AUTH-SQL-FIRST] ACTIVO para {email} (requiere FASE 2-E)")


# ============================================================================
# FASE 1B: SQL SANITIZER - Sanitización de SQL
# ============================================================================
"""
Sanitizador SQL centralizado para prevenir SQL Injection.
Valida y bloquea SQL peligroso antes de ejecución.
"""

import re
from dataclasses import dataclass, field
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection, get_external_sql_connection, get_edarsahub_connection

# Palabras clave peligrosas (operaciones de escritura/admin)
DANGEROUS_SQL_KEYWORDS = [
    'DELETE', 'UPDATE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE',
    'EXEC', 'EXECUTE', 'CREATE', 'MERGE', 'GRANT', 'REVOKE',
    'DENY', 'BACKUP', 'RESTORE', 'DBCC', 'KILL', 'SHUTDOWN',
    'RECONFIGURE', 'WAITFOR', 'OPENROWSET', 'OPENDATASOURCE',
    'BULK', 'WRITETEXT', 'UPDATETEXT', 'READTEXT',
]

# Prefijos de procedimientos peligrosos
DANGEROUS_SQL_PREFIXES = ['xp_', 'sp_', 'fn_']


@dataclass
class SQLValidationResult:
    """Resultado de validación SQL."""
    is_safe: bool
    sql: str
    normalized_sql: Optional[str] = None
    blocked_reason: Optional[str] = None
    blocked_keyword: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    validation_timestamp: Optional[str] = None
    
    def to_dict(self):
        return {
            'is_safe': self.is_safe,
            'blocked_reason': self.blocked_reason,
            'blocked_keyword': self.blocked_keyword,
            'warnings': self.warnings,
        }


class SQLSanitizer:
    """Sanitizador SQL centralizado."""
    
    _dangerous_pattern = re.compile(
        r'\b(' + '|'.join(DANGEROUS_SQL_KEYWORDS) + r')\b',
        re.IGNORECASE
    )
    _prefix_patterns = [
        re.compile(rf'\b{prefix}', re.IGNORECASE)
        for prefix in DANGEROUS_SQL_PREFIXES
    ]
    _multi_statement_pattern = re.compile(r';\s*\S', re.MULTILINE)
    _comment_patterns = [r'/\*', r'\*/', r'--']
    
    @classmethod
    def _normalize_sql(cls, sql: str) -> str:
        if not sql:
            return ""
        return re.sub(r'\s+', ' ', sql).strip()
    
    @classmethod
    def validate(cls, sql: str, allow_comments: bool = False, strict_mode: bool = True) -> SQLValidationResult:
        """Valida una consulta SQL."""
        result = SQLValidationResult(
            is_safe=True,
            sql=sql,
            validation_timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        if not sql or not sql.strip():
            result.is_safe = False
            result.blocked_reason = "SQL vacío o nulo"
            return result
        
        normalized = cls._normalize_sql(sql)
        result.normalized_sql = normalized
        upper_sql = normalized.upper().lstrip()
        
        # Verificar inicio con SELECT o WITH
        if not (upper_sql.startswith('SELECT') or upper_sql.startswith('WITH')):
            first_word = upper_sql.split()[0] if upper_sql.split() else "EMPTY"
            result.is_safe = False
            result.blocked_reason = f"Solo SELECT o WITH permitidos. Encontrado: {first_word}"
            return result
        
        # WITH debe ser CTE válido
        if upper_sql.startswith('WITH') and not re.match(r'^WITH\s+\w+\s+AS\s*\(', upper_sql, re.IGNORECASE):
            result.is_safe = False
            result.blocked_reason = "WITH clause malformado"
            return result
        
        # Buscar palabras peligrosas
        match = cls._dangerous_pattern.search(sql)
        if match:
            result.is_safe = False
            result.blocked_reason = f"Palabra peligrosa detectada: {match.group(1).upper()}"
            result.blocked_keyword = match.group(1).upper()
            return result
        
        # Buscar prefijos peligrosos
        for pattern in cls._prefix_patterns:
            match = pattern.search(sql)
            if match:
                result.is_safe = False
                result.blocked_reason = f"Prefijo de procedimiento peligroso: {match.group(0)}"
                result.blocked_keyword = match.group(0)
                return result
        
        # Detectar comentarios
        if not allow_comments:
            for pattern_str in cls._comment_patterns:
                if re.search(pattern_str, sql):
                    if strict_mode:
                        result.is_safe = False
                        result.blocked_reason = "Comentarios SQL no permitidos (pueden ocultar código)"
                        return result
                    result.warnings.append("SQL contiene comentarios")
        
        # Detectar múltiples statements
        if cls._multi_statement_pattern.search(sql):
            result.is_safe = False
            result.blocked_reason = "Múltiples statements no permitidos"
        
        return result
    
    @classmethod
    def validate_for_catalog(cls, sql: str, allow_parameters: bool = True) -> SQLValidationResult:
        """Validación para consultas del catálogo."""
        result = cls.validate(sql, allow_comments=False, strict_mode=True)
        if result.is_safe and allow_parameters:
            placeholders = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', sql)
            if placeholders:
                result.warnings.append(f"Placeholders encontrados: {placeholders}")
        return result
    
    @classmethod
    def validate_for_explorer(cls, sql: str, user_role: str = None) -> SQLValidationResult:
        """Validación para el Explorador BD."""
        result = cls.validate(sql, allow_comments=False, strict_mode=True)
        if user_role:
            from core.rbac_helper_sql import get_role_code
            if get_role_code({'role': user_role}) not in ('SUPERADMIN', 'ADMIN'):
                result.is_safe = False
                result.blocked_reason = "Solo administradores pueden usar el explorador SQL"
        return result
    
    @classmethod
    def quick_validate(cls, sql: str) -> bool:
        """Validación rápida."""
        if not sql or not sql.strip():
            return False
        normalized = cls._normalize_sql(sql).upper()
        if not (normalized.startswith('SELECT') or normalized.startswith('WITH')):
            return False
        if cls._dangerous_pattern.search(sql):
            return False
        for pattern in cls._prefix_patterns:
            if pattern.search(sql):
                return False
        if cls._multi_statement_pattern.search(sql):
            return False
        return True


def validate_sql_safe(sql: str) -> bool:
    """Función helper para validación rápida."""
    return SQLSanitizer.quick_validate(sql)


def validate_sql_detailed(sql: str) -> SQLValidationResult:
    """Función helper para validación detallada."""
    return SQLSanitizer.validate(sql)


def log_blocked_sql(result: SQLValidationResult, endpoint: str = None, user_email: str = None):
    """Registra intento de SQL bloqueado."""
    logging.warning(
        f"[SQL-BLOCKED] endpoint={endpoint or 'unknown'}, "
        f"user={user_email or 'unknown'}, "
        f"reason={result.blocked_reason}, "
        f"keyword={result.blocked_keyword or 'none'}"
    )

