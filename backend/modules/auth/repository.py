"""
EDARSA HUB - Auth Module Repository
===================================
Acceso a datos para usuarios y roles en MongoDB.

FASE 3 DEL REFACTOR MODULAR (Diciembre 2025):
- Encapsula operaciones de MongoDB para auth
- Inyección de dependencia de DB
"""

from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime, timezone


# ============================================================================
# INYECCIÓN DE DEPENDENCIA: MongoDB
# ============================================================================

_db = None


def init_auth_repository(database) -> None:
    """
    Inicializa el repositorio con la conexión a MongoDB.
    
    Args:
        database: Instancia de AsyncIOMotorDatabase
    """
    global _db
    _db = database


def get_db():
    """Obtiene la conexión a MongoDB inyectada."""
    if _db is None:
        raise RuntimeError("Auth repository not initialized. Call init_auth_repository(db) first.")
    return _db


# ============================================================================
# USUARIOS
# ============================================================================

async def find_user_by_email(email: str, include_password: bool = False) -> Optional[Dict]:
    """Busca un usuario por email."""
    projection = {"_id": 0}
    if not include_password:
        projection["password"] = 0
    return await get_db().users.find_one({"email": email}, projection)


async def find_user_by_id(user_id: str, include_password: bool = False) -> Optional[Dict]:
    """Busca un usuario por ID."""
    projection = {"_id": 0}
    if not include_password:
        projection["password"] = 0
    return await get_db().users.find_one({"id": user_id}, projection)


async def get_all_users() -> List[Dict]:
    """Obtiene todos los usuarios sin contraseña."""
    return await get_db().users.find({}, {"_id": 0, "password": 0}).to_list(1000)


async def create_user(user_doc: Dict) -> None:
    """Inserta un nuevo usuario en la BD."""
    await get_db().users.insert_one(user_doc)


async def update_user(user_id: str, update_data: Dict) -> None:
    """Actualiza un usuario por ID."""
    if update_data:
        await get_db().users.update_one({"id": user_id}, {"$set": update_data})


async def deactivate_user(user_id: str) -> None:
    """Desactiva un usuario (soft delete)."""
    await get_db().users.update_one({"id": user_id}, {"$set": {"active": False}})


# ============================================================================
# ROLES
# ============================================================================

async def get_all_roles() -> List[Dict]:
    """Obtiene todos los roles."""
    return await get_db().roles.find({}, {"_id": 0}).to_list(100)


async def find_role_by_id(role_id: str) -> Optional[Dict]:
    """Busca un rol por ID."""
    return await get_db().roles.find_one({"id": role_id}, {"_id": 0})


async def find_role_by_name(nombre: str) -> Optional[Dict]:
    """Busca un rol por nombre."""
    return await get_db().roles.find_one({"nombre": nombre}, {"_id": 0})


async def create_role(role_doc: Dict) -> Dict:
    """Crea un nuevo rol."""
    await get_db().roles.insert_one(role_doc)
    # Retornar sin _id
    if "_id" in role_doc:
        del role_doc["_id"]
    return role_doc


async def create_default_roles(default_roles: List[Dict]) -> List[Dict]:
    """Crea los roles predeterminados del sistema."""
    roles_to_insert = []
    for role in default_roles:
        role_doc = {
            "id": str(uuid.uuid4()),
            **role,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        roles_to_insert.append(role_doc)
    
    await get_db().roles.insert_many(roles_to_insert)
    return roles_to_insert


async def update_role(role_id: str, update_data: Dict) -> Optional[Dict]:
    """Actualiza un rol y retorna el rol actualizado."""
    if update_data:
        await get_db().roles.update_one({"id": role_id}, {"$set": update_data})
    return await get_db().roles.find_one({"id": role_id}, {"_id": 0})


async def delete_role(role_id: str) -> None:
    """Elimina un rol por ID."""
    await get_db().roles.delete_one({"id": role_id})


async def count_users_with_role(role_name: str) -> int:
    """Cuenta usuarios que tienen un rol específico."""
    return await get_db().users.count_documents({"role": role_name})


__all__ = [
    'init_auth_repository',
    'get_db',
    # Usuarios
    'find_user_by_email',
    'find_user_by_id',
    'get_all_users',
    'create_user',
    'update_user',
    'deactivate_user',
    # Roles
    'get_all_roles',
    'find_role_by_id',
    'find_role_by_name',
    'create_role',
    'create_default_roles',
    'update_role',
    'delete_role',
    'count_users_with_role',
]
