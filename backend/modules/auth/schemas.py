"""
EDARSA HUB - Auth Schemas
=========================
Modelos Pydantic para validación de datos de autenticación.

NOTA: Los schemas actuales están en server.py.
Este archivo se usará cuando se autorice la migración.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """Schema para registro de usuario"""
    email: EmailStr
    password: str
    nombre: str
    role: str = "Usuario"


class UserResponse(BaseModel):
    """Schema para respuesta de usuario (sin password)"""
    id: str
    email: str
    nombre: str
    role: str
    active: bool = True
    sucursales: Optional[List[str]] = []
    created_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Schema para respuesta de login con token"""
    token: str
    user: UserResponse


class PermissionsUpdate(BaseModel):
    """Schema para actualizar permisos de usuario"""
    role: Optional[str] = None
    sucursales: Optional[List[str]] = None
    active: Optional[bool] = None
