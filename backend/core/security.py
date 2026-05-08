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
        database: Instancia de AsyncIOMotorDatabase
    """
    global _db
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
    
    Este es el punto de entrada de autenticación para todos los endpoints protegidos.
    Extrae el token del header Authorization, lo verifica, y busca el usuario en MongoDB.
    
    Args:
        credentials: Credenciales HTTP Bearer extraídas automáticamente por FastAPI
        
    Returns:
        Diccionario con datos del usuario (sin _id ni password)
        
    Raises:
        HTTPException 401: Token inválido o expirado
        HTTPException 404: Usuario no encontrado en BD
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    db = get_db()
    user = await db.users.find_one({"email": payload['email']}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user


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
    
    # Buscar usuario
    db = get_db()
    user = await db.users.find_one({"email": payload['email']}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
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
    FASE 3: Usa el nuevo modelo de contexto.
    
    Returns:
        Lista de empresa_ids permitidos
    """
    # SuperAdministrador tiene acceso a todas las empresas
    if user.get('role') == 'SuperAdministrador':
        db = get_db()
        empresas = await db.empresas.find({'activa': True}, {'id': 1}).to_list(100)
        return [e['id'] for e in empresas]
    
    # Nuevo modelo: empresas_permitidas
    if user.get('empresas_permitidas'):
        return user['empresas_permitidas']
    
    # Fallback legacy: Si es Administrador, todas las empresas
    if user.get('role') in ['Administrador', 'admin', 'Admin']:
        db = get_db()
        empresas = await db.empresas.find({'activa': True}, {'id': 1}).to_list(100)
        return [e['id'] for e in empresas]
    
    # Sin acceso
    return []


async def get_servers_for_empresas(empresa_ids: List[str]) -> List[str]:
    """
    Obtiene los server_ids asociados a una lista de empresas.
    FASE 3: Traduce empresas → servidores para compatibilidad.
    
    Returns:
        Lista de server_ids
    """
    if not empresa_ids:
        return []
    
    db = get_db()
    # Obtener sucursales de las empresas
    sucursales = await db.sucursales_catalogo.find(
        {'empresa_id': {'$in': empresa_ids}},
        {'id': 1}
    ).to_list(100)
    
    sucursal_ids = [s['id'] for s in sucursales]
    
    # Obtener mapeos a servidores
    mapeos = await db.sucursal_servidor_map.find(
        {'sucursal_id': {'$in': sucursal_ids}},
        {'server_id': 1}
    ).to_list(100)
    
    return list(set(m['server_id'] for m in mapeos))


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
    
    # SuperAdministrador y Administrador tienen acceso full
    if role in ['SuperAdministrador', 'Administrador']:
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
]
