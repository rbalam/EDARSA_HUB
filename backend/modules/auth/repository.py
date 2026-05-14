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
    """
    Busca un usuario por ID.
    
    BUG-RBAC-PERM-001: Búsqueda case-insensitive para PublicUUID.
    SQL devuelve UUIDs en mayúsculas, MongoDB puede tenerlos en minúsculas.
    """
    projection = {"_id": 0}
    if not include_password:
        projection["password"] = 0
    
    # Intentar búsqueda exacta primero (más rápido)
    user = await get_db().users.find_one({"id": user_id}, projection)
    
    if not user:
        # Fallback: búsqueda case-insensitive (UUIDs pueden diferir en case)
        user = await get_db().users.find_one({"id": user_id.lower()}, projection)
    
    if not user:
        # Último intento: uppercase
        user = await get_db().users.find_one({"id": user_id.upper()}, projection)
    
    return user


async def get_all_users() -> List[Dict]:
    """
    Obtiene todos los usuarios sin contraseña.
    
    FASE 2-G / BUG-AUTH-USERS-001: Datos base de EDARSAHUB SQL.
    BUG-RBAC-PERM-001: Permisos legacy (allowed_servers, allowed_sucursales, 
                       allowed_warehouses) se enriquecen desde MongoDB temporalmente
                       hasta migración completa.
    
    Returns:
        Lista de usuarios con estructura compatible con modelo User de Pydantic.
    """
    from core.auth.user_repository_sql import AuthRepositorySQL
    import logging
    
    try:
        repo_sql = AuthRepositorySQL()
        users_sql = repo_sql.list_all_users_sql()
        
        # BUG-RBAC-PERM-001: Obtener permisos legacy de MongoDB para enriquecer
        mongo_perms = {}
        try:
            mongo_users = await get_db().users.find(
                {}, 
                {
                    "_id": 0, 
                    "id": 1, 
                    "allowed_servers": 1, 
                    "allowed_sucursales": 1, 
                    "allowed_warehouses": 1,
                    "telefono": 1,
                    "sec_permisos": 1,
                    "sec_rol": 1,
                    "sec_roles": 1,
                    "sec_perfil": 1,
                    "sec_roles_alcance": 1
                }
            ).to_list(1000)
            
            for mu in mongo_users:
                mongo_id = mu.get('id', '').lower()
                if mongo_id:
                    mongo_perms[mongo_id] = mu
        except Exception as mongo_err:
            logging.warning(f"[AUTH-REPO] No se pudieron leer permisos de MongoDB: {mongo_err}")
        
        # Mapear a estructura compatible con Pydantic User schema
        result = []
        for u in users_sql:
            sql_id = u.get('id', '')
            sql_id_lower = sql_id.lower() if sql_id else ''
            
            # Obtener permisos de MongoDB si existen
            mongo_data = mongo_perms.get(sql_id_lower, {})
            
            # Limpiar allowed_warehouses de None (legacy bug)
            allowed_wh = mongo_data.get('allowed_warehouses', {})
            if isinstance(allowed_wh, dict):
                allowed_wh = {
                    k: [v for v in vals if v is not None] 
                    for k, vals in allowed_wh.items() 
                    if isinstance(vals, list)
                }
            
            user_dict = {
                'id': sql_id,
                'email': u.get('email'),
                'name': u.get('name') or u.get('nombre') or '',
                'role': u.get('role') or u.get('rol') or 'Usuario',
                'telefono': mongo_data.get('telefono'),
                'active': u.get('active', True),
                'sucursales': [],  # Legacy, no usado
                'allowed_servers': mongo_data.get('allowed_servers', []),
                'allowed_sucursales': mongo_data.get('allowed_sucursales', {}),
                'allowed_warehouses': allowed_wh,
                'empresas_permitidas': u.get('empresas_permitidas', []),
                'empresa_default_id': u.get('empresa_default_id'),
                # Campos RBAC piloto (desde MongoDB temporalmente)
                'sec_permisos': mongo_data.get('sec_permisos', []),
                'sec_rol': mongo_data.get('sec_rol'),
                'sec_roles': mongo_data.get('sec_roles', []),
                'sec_perfil': mongo_data.get('sec_perfil'),
                'sec_roles_alcance': mongo_data.get('sec_roles_alcance', {}),
                '_source': 'EDARSAHUB_SQL'
            }
            # Solo incluir usuarios con id válido (PublicUUID)
            if user_dict['id']:
                result.append(user_dict)
        
        return result
        
    except Exception as e:
        import logging
        logging.error(f"[AUTH-REPO] Error obteniendo usuarios de SQL: {e}")
        # NO hacer fallback a MongoDB - reportar error
        raise RuntimeError(f"Error consultando usuarios en EDARSAHUB SQL: {str(e)}")


async def get_users_by_empresas(empresas_ids: List[str]) -> List[Dict]:
    """
    FASE 16 / BUG-AUTH-USERS-001: Obtiene usuarios filtrados por empresas.
    
    Migrado a EDARSAHUB SQL. Filtra usuarios cuyo empresa_default_id 
    esté en la lista proporcionada.
    
    Args:
        empresas_ids: Lista de IDs de empresas permitidas (UUIDs)
        
    Returns:
        Lista de usuarios (sin password) que pertenecen a esas empresas
    """
    if not empresas_ids:
        return []
    
    # Obtener todos los usuarios de SQL y filtrar por empresas
    all_users = await get_all_users()
    
    # Filtrar: incluir usuarios cuya empresa_default_id o cualquier empresa en empresas_permitidas
    # coincida con las empresas del alcance
    empresas_set = set(empresas_ids)
    filtered = []
    for u in all_users:
        emp_default = u.get('empresa_default_id')
        emp_permitidas = set(u.get('empresas_permitidas', []))
        
        # Si tiene empresa_default en el alcance O alguna empresa_permitida
        if emp_default in empresas_set or emp_permitidas.intersection(empresas_set):
            filtered.append(u)
    
    return filtered


async def create_user(user_doc: Dict) -> None:
    """Inserta un nuevo usuario en la BD."""
    await get_db().users.insert_one(user_doc)


async def update_user(user_id: str, update_data: Dict) -> None:
    """
    Actualiza un usuario por ID.
    
    BUG-RBAC-PERM-001: Búsqueda case-insensitive para PublicUUID.
    """
    if update_data:
        # Intentar con ID exacto
        result = await get_db().users.update_one({"id": user_id}, {"$set": update_data})
        
        if result.matched_count == 0:
            # Fallback: intentar con lowercase
            result = await get_db().users.update_one({"id": user_id.lower()}, {"$set": update_data})
        
        if result.matched_count == 0:
            # Fallback: intentar con uppercase
            await get_db().users.update_one({"id": user_id.upper()}, {"$set": update_data})


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
    'get_users_by_empresas',  # FASE 16
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
