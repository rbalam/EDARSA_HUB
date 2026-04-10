"""
EDARSA HUB - Seguridad y Autenticación
======================================
Funciones de seguridad, hashing de contraseñas y JWT.

NOTA: Este archivo es parte del refactor modular.
La lógica de seguridad actual sigue en server.py hasta que se autorice la migración.

USO FUTURO:
    from core.security import hash_password, verify_password, create_token, get_current_user
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import jwt

# Configuración placeholder (se migrará desde server.py)
JWT_SECRET = "placeholder-will-be-migrated"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    
    NOTA: No usar aún - usar hash_password de server.py
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Contraseña hasheada
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña contra su hash.
    
    NOTA: No usar aún - usar verify_password de server.py
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash almacenado
        
    Returns:
        True si coincide, False si no
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_token(user_id: str, email: str, role: str) -> str:
    """
    Crea un token JWT.
    
    NOTA: No usar aún - usar create_token de server.py
    
    Args:
        user_id: ID del usuario
        email: Email del usuario
        role: Rol del usuario
        
    Returns:
        Token JWT firmado
    """
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency para obtener el usuario actual desde el token JWT.
    
    NOTA: No usar aún - usar get_current_user de server.py
    
    Returns:
        Diccionario con datos del usuario
        
    Raises:
        HTTPException: Si el token es inválido o expirado
    """
    raise NotImplementedError("Use get_current_user from server.py until migration is complete.")


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodifica un token JWT.
    
    NOTA: No usar aún - usar lógica de server.py
    
    Args:
        token: Token JWT
        
    Returns:
        Payload decodificado
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
