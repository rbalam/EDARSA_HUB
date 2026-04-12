"""
EDARSA HUB - Auth Module Service
================================
Lógica de negocio para autenticación, usuarios y roles.

FASE 3 DEL REFACTOR MODULAR (Diciembre 2025):
- Lógica de login, registro, CRUD de usuarios y roles
- Usa repository para acceso a datos
- Usa core/security para hashing y JWT
"""

from typing import Dict, List, Any
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException

from core.security import hash_password, verify_password, create_token
from modules.auth import repository as repo
from modules.auth.schemas import User, UserCreate, DEFAULT_ROLES


# ============================================================================
# AUTENTICACIÓN
# ============================================================================

async def register_user(user_data: UserCreate) -> Dict[str, Any]:
    """
    Registra un nuevo usuario.
    
    Returns:
        Dict con token y datos del usuario
        
    Raises:
        HTTPException 400: Si el email ya existe
    """
    # Verificar si existe
    existing = await repo.find_user_by_email(user_data.email)
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    # Hash de contraseña
    hashed_pw = hash_password(user_data.password)
    
    # Crear modelo de usuario
    user_dict = user_data.model_dump()
    del user_dict['password']
    user = User(**user_dict)
    
    # Preparar documento para MongoDB
    doc = user.model_dump()
    doc['password'] = hashed_pw
    doc['created_at'] = doc['created_at'].isoformat()
    
    # Insertar
    await repo.create_user(doc)
    
    # Generar token
    token = create_token(user.id, user.email, user.role)
    
    return {"token": token, "user": user.model_dump()}


async def login_user(email: str, password: str) -> Dict[str, Any]:
    """
    Autentica un usuario.
    
    Returns:
        Dict con token y datos del usuario (sin password)
        
    Raises:
        HTTPException 401: Credenciales inválidas o usuario inactivo
    """
    import logging
    logger = logging.getLogger(__name__)
    
    user = await repo.find_user_by_email(email, include_password=True)
    logger.info(f"Login attempt for {email}: user found = {user is not None}")
    
    if not user:
        logger.warning(f"Login failed: user {email} not found")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not verify_password(password, user['password']):
        logger.warning(f"Login failed: invalid password for {email}")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not user.get('active', True):
        raise HTTPException(status_code=401, detail="Usuario inactivo")
    
    # Generar token
    token = create_token(user['id'], user['email'], user['role'])
    
    # Respuesta sin password
    user_response = {k: v for k, v in user.items() if k != 'password'}
    
    return {"token": token, "user": user_response}


# ============================================================================
# USUARIOS CRUD
# ============================================================================

async def get_users(current_user: Dict) -> List[Dict]:
    """
    Obtiene todos los usuarios.
    
    Raises:
        HTTPException 403: Si no es administrador
    """
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    return await repo.get_all_users()


async def update_user(user_id: str, user_data: Dict, current_user: Dict) -> Dict:
    """
    Actualiza un usuario.
    
    Raises:
        HTTPException 403: Si no es administrador
    """
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    update_data = {}
    for field in ['name', 'email', 'role', 'sucursales']:
        if field in user_data:
            update_data[field] = user_data[field]
    
    # Hash de contraseña si se proporciona
    if 'password' in user_data and user_data['password']:
        update_data['password'] = hash_password(user_data['password'])
    
    await repo.update_user(user_id, update_data)
    return {"message": "Usuario actualizado"}


async def delete_user(user_id: str, current_user: Dict) -> Dict:
    """
    Desactiva un usuario (soft delete).
    
    Raises:
        HTTPException 403: Si no es administrador
    """
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    await repo.deactivate_user(user_id)
    return {"message": "Usuario desactivado"}


async def update_user_permissions(user_id: str, permissions: Dict, current_user: Dict) -> Dict:
    """
    Actualiza los permisos de un usuario.
    
    Raises:
        HTTPException 403: Si no es administrador
        HTTPException 404: Si el usuario no existe
    """
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    user = await repo.find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = {}
    for field in ['allowed_servers', 'allowed_sucursales', 'allowed_warehouses']:
        if field in permissions:
            update_data[field] = permissions[field]
    
    await repo.update_user(user_id, update_data)
    return {"message": "Permisos actualizados"}


# ============================================================================
# ROLES CRUD
# ============================================================================

async def get_roles(current_user: Dict) -> List[Dict]:
    """
    Obtiene todos los roles, creando los predeterminados si no existen.
    
    Raises:
        HTTPException 403: Si no es administrador
    """
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    roles = await repo.get_all_roles()
    
    # Si no hay roles, crear los predeterminados
    if not roles:
        roles = await repo.create_default_roles(DEFAULT_ROLES)
    
    return roles


async def create_role(role_data: Dict, current_user: Dict) -> Dict:
    """
    Crea un nuevo rol.
    
    Raises:
        HTTPException 403: Si no es administrador
        HTTPException 400: Si ya existe un rol con ese nombre
    """
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Verificar duplicado
    existing = await repo.find_role_by_name(role_data.get("nombre"))
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
    
    new_role = {
        "id": str(uuid.uuid4()),
        "nombre": role_data.get("nombre", ""),
        "descripcion": role_data.get("descripcion", ""),
        "permisos": role_data.get("permisos", []),
        "es_sistema": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    return await repo.create_role(new_role)


async def update_role(role_id: str, role_data: Dict, current_user: Dict) -> Dict:
    """
    Actualiza un rol existente.
    
    Raises:
        HTTPException 403: Si no es administrador
        HTTPException 404: Si el rol no existe
        HTTPException 400: Si se intenta duplicar nombre
    """
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    existing = await repo.find_role_by_id(role_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    update_data = {}
    if "descripcion" in role_data:
        update_data["descripcion"] = role_data["descripcion"]
    if "permisos" in role_data:
        update_data["permisos"] = role_data["permisos"]
    
    # Solo permitir cambiar nombre si no es rol de sistema
    if not existing.get("es_sistema") and "nombre" in role_data:
        if role_data["nombre"] != existing["nombre"]:
            dup = await repo.find_role_by_name(role_data["nombre"])
            if dup:
                raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
        update_data["nombre"] = role_data["nombre"]
    
    return await repo.update_role(role_id, update_data)


async def delete_role(role_id: str, current_user: Dict) -> Dict:
    """
    Elimina un rol (solo roles no de sistema).
    
    Raises:
        HTTPException 403: Si no es administrador
        HTTPException 404: Si el rol no existe
        HTTPException 400: Si es rol de sistema o tiene usuarios asignados
    """
    if current_user['role'] != 'Administrador':
        raise HTTPException(status_code=403, detail="No autorizado")
    
    existing = await repo.find_role_by_id(role_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    if existing.get("es_sistema"):
        raise HTTPException(status_code=400, detail="No se pueden eliminar roles de sistema")
    
    # Verificar usuarios con este rol
    users_count = await repo.count_users_with_role(existing["nombre"])
    if users_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar: {users_count} usuario(s) tienen este rol asignado"
        )
    
    await repo.delete_role(role_id)
    return {"message": "Rol eliminado"}


__all__ = [
    # Auth
    'register_user',
    'login_user',
    # Users
    'get_users',
    'update_user',
    'delete_user',
    'update_user_permissions',
    # Roles
    'get_roles',
    'create_role',
    'update_role',
    'delete_role',
]
