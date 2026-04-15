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
JWT_EXPIRATION_HOURS: int = int(os.environ.get('JWT_EXPIRATION_HOURS', '72'))

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
    Crea un token JWT firmado.
    
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


# ============================================================================
# FUNCIONES DE PERMISOS
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
    if user.get('role') == 'Administrador':
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
    
    if role == 'Administrador':
        logging.info("Usuario es Admin, retornando todos los servidores")
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
    if user.get('role') == 'Administrador':
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
    # Permisos
    'user_has_server_access',
    'filter_servers_by_permissions',
    'filter_sucursales_by_permissions',
]
