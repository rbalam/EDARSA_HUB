"""
EDARSA HUB - Auth Module Repository
===================================
RBAC-SCOPE-G: Repositorio de usuarios migrado a EDARSAHUB SQL.

MongoDB ya NO es fuente productiva para operaciones de usuarios.
Las funciones de usuarios ahora delegan a user_repository_sql.py.

FASE 3 DEL REFACTOR MODULAR (Diciembre 2025):
- Encapsula operaciones para auth
- RBAC-SCOPE-G: Migrado a SQL (14-May-2026)
"""

from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime, timezone


# ============================================================================
# INYECCIÓN DE DEPENDENCIA: MongoDB (Legacy - solo para roles)
# ============================================================================

_db = None


def init_auth_repository(database) -> None:
    """
    Inicializa el repositorio con la conexión a MongoDB.
    
    RBAC-SCOPE-G: MongoDB solo se usa para roles (db.roles).
    Usuarios se manejan 100% desde SQL.
    
    Args:
        database: Instancia de AsyncIOMotorDatabase
    """
    global _db
    _db = database


def get_db():
    """
    Obtiene la conexión a MongoDB inyectada.
    
    RBAC-SCOPE-G: Solo usada para operaciones de roles.
    """
    if _db is None:
        raise RuntimeError("Auth repository not initialized. Call init_auth_repository(db) first.")
    return _db


# ============================================================================
# USUARIOS - RBAC-SCOPE-G: 100% SQL
# ============================================================================

async def find_user_by_email(email: str, include_password: bool = False) -> Optional[Dict]:
    """
    RBAC-SCOPE-G: Busca un usuario por email en EDARSAHUB SQL.
    MongoDB ya NO es fuente productiva.
    """
    from core.auth.user_repository_sql import find_user_by_email_sql
    return find_user_by_email_sql(email, include_password)


async def find_user_by_id(user_id: str, include_password: bool = False) -> Optional[Dict]:
    """
    RBAC-SCOPE-G: Busca un usuario por PublicUUID en EDARSAHUB SQL.
    MongoDB ya NO es fuente productiva.
    """
    from core.auth.user_repository_sql import find_user_by_id_sql
    return find_user_by_id_sql(user_id, include_password)


async def get_all_users() -> List[Dict]:
    """
    Obtiene todos los usuarios sin contraseña.
    
    RBAC-SCOPE-G: Datos base de EDARSAHUB SQL.
    Permisos operativos (allowed_servers, allowed_sucursales, 
    allowed_warehouses) se leen desde EDARSAHUB SQL.
    
    MongoDB solo se consulta para campos RBAC piloto (sec_*, telefono)
    que son metadatos no productivos.
    
    Returns:
        Lista de usuarios con estructura compatible con modelo User de Pydantic.
    """
    from core.auth.user_repository_sql import AuthRepositorySQL
    import logging
    import pymssql
    
    try:
        repo_sql = AuthRepositorySQL()
        users_sql = repo_sql.list_all_users_sql()
        
        # RBAC-SCOPE-D: Obtener permisos operativos desde EDARSAHUB SQL
        # Conexión directa para queries de permisos
        conn = pymssql.connect(
            server='54.39.104.176',
            port=1433,
            user='HRLectura',
            password='National09$',
            database='EDARSAHUB'
        )
        cursor = conn.cursor()
        
        # Obtener mapeo UsuarioID SQL → permisos
        sql_perms = {}
        
        # 1. Servidores asignados por usuario
        cursor.execute("""
            SELECT 
                u.UsuarioID,
                LOWER(CAST(u.PublicUUID AS VARCHAR(36))) as PublicUUID,
                LOWER(CAST(s.ServidorID AS VARCHAR(36))) as ServidorUUID
            FROM Usuario_Catalogo u
            LEFT JOIN Usuario_ServidoresAsignacion s ON u.UsuarioID = s.UsuarioID AND s.Activo = 1
            WHERE u.Activo = 1
        """)
        for row in cursor.fetchall():
            usuario_id, public_uuid, servidor_uuid = row
            if public_uuid not in sql_perms:
                sql_perms[public_uuid] = {
                    'allowed_servers': [],
                    'allowed_sucursales': {},
                    'allowed_warehouses': {}
                }
            if servidor_uuid:
                sql_perms[public_uuid]['allowed_servers'].append(servidor_uuid)
        
        # 2. Sucursales asignadas por usuario/servidor
        cursor.execute("""
            SELECT 
                LOWER(CAST(u.PublicUUID AS VARCHAR(36))) as PublicUUID,
                LOWER(CAST(s.ServidorID AS VARCHAR(36))) as ServidorUUID,
                s.SucursalCodigo
            FROM Usuario_Catalogo u
            JOIN Usuario_SucursalesAsignacion s ON u.UsuarioID = s.UsuarioID AND s.Activo = 1
            WHERE u.Activo = 1
        """)
        for row in cursor.fetchall():
            public_uuid, servidor_uuid, suc_codigo = row
            if public_uuid in sql_perms:
                if servidor_uuid not in sql_perms[public_uuid]['allowed_sucursales']:
                    sql_perms[public_uuid]['allowed_sucursales'][servidor_uuid] = []
                sql_perms[public_uuid]['allowed_sucursales'][servidor_uuid].append(suc_codigo)
        
        # 3. Almacenes asignados por usuario/servidor
        cursor.execute("""
            SELECT 
                LOWER(CAST(u.PublicUUID AS VARCHAR(36))) as PublicUUID,
                LOWER(CAST(a.ServidorID AS VARCHAR(36))) as ServidorUUID,
                a.AlmacenCodigo
            FROM Usuario_Catalogo u
            JOIN Usuario_AlmacenesAsignacion a ON u.UsuarioID = a.UsuarioID AND a.Activo = 1
            WHERE u.Activo = 1
        """)
        for row in cursor.fetchall():
            public_uuid, servidor_uuid, alm_codigo = row
            if public_uuid in sql_perms:
                if servidor_uuid not in sql_perms[public_uuid]['allowed_warehouses']:
                    sql_perms[public_uuid]['allowed_warehouses'][servidor_uuid] = []
                sql_perms[public_uuid]['allowed_warehouses'][servidor_uuid].append(alm_codigo)
        
        conn.close()
        
        # RBAC-SCOPE-D: MongoDB solo para campos RBAC piloto (sec_*), NO para permisos operativos
        mongo_rbac_data = {}
        try:
            mongo_users = await get_db().users.find(
                {}, 
                {
                    "_id": 0, 
                    "id": 1, 
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
                    mongo_rbac_data[mongo_id] = mu
        except Exception as mongo_err:
            logging.warning(f"[AUTH-REPO] No se pudieron leer campos RBAC piloto de MongoDB: {mongo_err}")
        
        # Mapear a estructura compatible con Pydantic User schema
        result = []
        for u in users_sql:
            sql_id = u.get('id', '')
            sql_id_lower = sql_id.lower() if sql_id else ''
            
            # Obtener permisos desde SQL (RBAC-SCOPE-D)
            perms = sql_perms.get(sql_id_lower, {
                'allowed_servers': [],
                'allowed_sucursales': {},
                'allowed_warehouses': {}
            })
            
            # Obtener campos RBAC piloto de MongoDB (solo metadatos, no permisos operativos)
            rbac_data = mongo_rbac_data.get(sql_id_lower, {})
            
            user_dict = {
                'id': sql_id,
                'email': u.get('email'),
                'name': u.get('name') or u.get('nombre') or '',
                'role': u.get('role') or u.get('rol') or 'Usuario',
                'telefono': rbac_data.get('telefono'),
                'active': u.get('active', True),
                'sucursales': [],  # Legacy, no usado
                # RBAC-SCOPE-D: Permisos operativos desde SQL
                'allowed_servers': perms.get('allowed_servers', []),
                'allowed_sucursales': perms.get('allowed_sucursales', {}),
                'allowed_warehouses': perms.get('allowed_warehouses', {}),
                'empresas_permitidas': u.get('empresas_permitidas', []),
                'empresa_default_id': u.get('empresa_default_id'),
                # Campos RBAC piloto (desde MongoDB - solo metadatos)
                'sec_permisos': rbac_data.get('sec_permisos', []),
                'sec_rol': rbac_data.get('sec_rol'),
                'sec_roles': rbac_data.get('sec_roles', []),
                'sec_perfil': rbac_data.get('sec_perfil'),
                'sec_roles_alcance': rbac_data.get('sec_roles_alcance', {}),
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
    """
    RBAC-SCOPE-G: Inserta un nuevo usuario en EDARSAHUB SQL.
    MongoDB ya NO es fuente productiva.
    """
    from core.auth.user_repository_sql import create_user_sql
    create_user_sql(user_doc)


async def update_user(user_id: str, update_data: Dict) -> None:
    """
    RBAC-SCOPE-G: Actualiza un usuario en EDARSAHUB SQL.
    MongoDB ya NO es fuente productiva.
    """
    from core.auth.user_repository_sql import update_user_sql
    update_user_sql(user_id, update_data)


async def deactivate_user(user_id: str) -> None:
    """
    RBAC-SCOPE-G: Desactiva un usuario en EDARSAHUB SQL (soft delete).
    MongoDB ya NO es fuente productiva.
    """
    from core.auth.user_repository_sql import deactivate_user_sql
    deactivate_user_sql(user_id)


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
