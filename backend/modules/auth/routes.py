"""
EDARSA HUB - Auth Module Routes
===============================
Endpoints de autenticación, usuarios y roles.

FASE 3 DEL REFACTOR MODULAR (Diciembre 2025):
- Migrado desde server.py
- Mismas rutas, mismas respuestas, misma funcionalidad
- Sin cambios en URLs para compatibilidad con frontend

ENDPOINTS:
- POST /auth/register - Registro de usuario
- POST /auth/login - Login
- GET /auth/me - Usuario actual
- GET /users - Lista de usuarios
- PUT /users/{user_id} - Actualizar usuario
- DELETE /users/{user_id} - Desactivar usuario
- PUT /users/{user_id}/permissions - Actualizar permisos
- GET /roles/modulos - Módulos disponibles
- GET /roles - Lista de roles
- POST /roles - Crear rol
- PUT /roles/{role_id} - Actualizar rol
- DELETE /roles/{role_id} - Eliminar rol
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException

from core.security import get_current_user
from modules.auth import service
from modules.auth import context_service
from modules.auth.schemas import User, UserCreate, UserLogin, MODULOS_DISPONIBLES

# Router sin prefix - se agregará en server.py como /api
router = APIRouter(tags=["auth"])


# ============================================================================
# AUTENTICACIÓN
# ============================================================================

@router.post("/auth/register")
async def register(user_data: UserCreate):
    """Registra un nuevo usuario."""
    return await service.register_user(user_data)


@router.post("/auth/login")
async def login(credentials: UserLogin):
    """Autentica un usuario y retorna token JWT."""
    return await service.login_user(credentials.email, credentials.password)


@router.get("/auth/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    """Retorna los datos del usuario autenticado."""
    return current_user


# ============================================================================
# CONTEXTO DE USUARIO (FASE 2)
# ============================================================================

@router.get("/auth/me/context")
async def get_my_context(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el contexto completo del usuario actual.
    Incluye empresas permitidas, rol RBAC, permisos y sucursales.
    
    FASE 2: Endpoint nuevo, no reemplaza /auth/me
    """
    context = await context_service.get_user_context(current_user['id'])
    if not context:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return context


@router.post("/auth/context")
async def change_context(
    data: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Cambia el contexto activo del usuario (empresa/sucursal).
    
    Body:
        empresa_id: UUID de la empresa a activar
        sucursal_id: UUID de la sucursal (opcional)
    
    FASE 2: Endpoint nuevo para cambio de contexto sin re-login
    """
    empresa_id = data.get('empresa_id')
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id requerido")
    
    context = await context_service.get_user_context_for_empresa(
        current_user['id'],
        empresa_id
    )
    
    if not context:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if 'error' in context:
        raise HTTPException(status_code=403, detail=context['error'])
    
    return context


@router.get("/auth/empresas")
async def get_my_empresas(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene las empresas disponibles para el usuario actual.
    
    FASE 2: Endpoint nuevo para selector de empresa en frontend
    """
    empresas = await context_service.get_empresas_disponibles(current_user['id'])
    return empresas


# ============================================================================
# USUARIOS CRUD
# ============================================================================

@router.get("/users", response_model=List[User])
async def get_users(current_user: Dict = Depends(get_current_user)):
    """Obtiene todos los usuarios (solo admin)."""
    return await service.get_users(current_user)


@router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: Dict, current_user: Dict = Depends(get_current_user)):
    """Actualiza un usuario (solo admin)."""
    return await service.update_user(user_id, user_data, current_user)


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: Dict = Depends(get_current_user)):
    """Desactiva un usuario (solo admin)."""
    return await service.delete_user(user_id, current_user)


@router.put("/users/{user_id}/permissions")
async def update_user_permissions(user_id: str, permissions: Dict, current_user: Dict = Depends(get_current_user)):
    """Actualiza los permisos de un usuario (solo admin)."""
    return await service.update_user_permissions(user_id, permissions, current_user)


# ============================================================================
# ROLES CRUD
# ============================================================================

@router.get("/roles/modulos")
async def get_modulos_disponibles(current_user: Dict = Depends(get_current_user)):
    """Obtiene la lista de módulos disponibles para asignar permisos."""
    if current_user['role'] != 'Administrador':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No autorizado")
    return MODULOS_DISPONIBLES


@router.get("/roles")
async def get_roles(current_user: Dict = Depends(get_current_user)):
    """Obtiene todos los roles del sistema (solo admin)."""
    return await service.get_roles(current_user)


@router.post("/roles")
async def create_role(role_data: Dict, current_user: Dict = Depends(get_current_user)):
    """Crea un nuevo rol (solo admin)."""
    return await service.create_role(role_data, current_user)


@router.put("/roles/{role_id}")
async def update_role(role_id: str, role_data: Dict, current_user: Dict = Depends(get_current_user)):
    """Actualiza un rol existente (solo admin)."""
    return await service.update_role(role_id, role_data, current_user)


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, current_user: Dict = Depends(get_current_user)):
    """Elimina un rol (solo admin, no roles de sistema)."""
    return await service.delete_role(role_id, current_user)


__all__ = ['router']
