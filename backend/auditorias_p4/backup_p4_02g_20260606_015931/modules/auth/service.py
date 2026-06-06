from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Auth Module Service
================================
Lógica de negocio para autenticación, usuarios y roles.

FASE 3 DEL REFACTOR MODULAR (Diciembre 2025):
- Lógica de login, registro, CRUD de usuarios y roles
- Usa repository para acceso a datos
- Usa core/security para hashing y JWT

FASE 9: Protección real de endpoints con permisos RBAC
FASE 16: Aplicación de alcance organizacional real en GET /api/users
CIERRE PILOTO RBAC: Alcance real en PUT/DELETE /api/users
"""

from typing import Dict, List, Any
from datetime import datetime, timezone
import uuid
import logging
from fastapi import HTTPException

from core.security import hash_password, verify_password, create_token
from core.rbac_helper import verificar_permiso_rbac  # FASE 9
from core.alcance_helper import resolver_alcance_usuarios, verificar_usuario_en_alcance  # FASE 16 + CIERRE
from modules.auth import repository as repo
from modules.auth.schemas import User, UserCreate, DEFAULT_ROLES

logger = logging.getLogger(__name__)


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


async def get_user_by_id(user_id) -> Dict[str, Any]:
    """
    FASE A P1-REFRESH-TOKENS: Obtiene un usuario por su ID.
    
    Args:
        user_id: ID del usuario (puede ser string o int)
        
    Returns:
        Dict con datos del usuario (sin password) o None si no existe
    """
    try:
        # El ID puede venir como int (de SQL) o como string (MongoDB ObjectId)
        user = await repo.find_user_by_id(str(user_id))
        
        if not user:
            return None
        
        # Retornar sin password
        return {k: v for k, v in user.items() if k != 'password'}
        
    except Exception as e:
        logger.error(f"Error obteniendo usuario por ID {user_id}: {e}")
        return None


# ============================================================================
# USUARIOS CRUD
# ============================================================================

# Jerarquía de roles (mayor número = más privilegios)
ROLE_HIERARCHY = {
    'Usuario': 1,
    'Supervisor': 2,
    'Administrador': 3,
    'SuperAdministrador': 100  # Rol máximo del sistema
}


def _get_role_level(role: str) -> int:
    """Obtiene el nivel de privilegio de un rol."""
    return ROLE_HIERARCHY.get(role, 0)


def _can_manage_user(current_user: Dict, target_user: Dict) -> bool:
    """
    Verifica si el usuario actual puede gestionar al usuario objetivo.
    
    Reglas:
    - SuperAdministrador puede gestionar a cualquiera
    - Administrador puede gestionar a usuarios de menor nivel (no SuperAdministrador)
    - Nadie puede modificar a un SuperAdministrador excepto otro SuperAdministrador
    """
    current_level = _get_role_level(current_user.get('role', ''))
    target_level = _get_role_level(target_user.get('role', ''))
    
    # SuperAdministrador puede gestionar a cualquiera
    if current_level >= 100:
        return True
    
    # Administrador puede gestionar usuarios de menor nivel
    if current_level >= 3 and target_level < 100:
        return True
    
    return False


async def get_users(current_user: Dict) -> List[Dict]:
    """
    Obtiene usuarios con filtrado por alcance organizacional.
    
    FASE 9: Protección con permiso RBAC SISTEMA_USUARIOS_VER + fallback legacy.
    FASE 16: Aplicación de alcance organizacional real.
    
    Orden de acceso:
    1. Si tiene permiso RBAC (sec_permisos/sec_roles/sec_rol/SuperAdmin) → ACCESO
    2. Si NO tiene RBAC pero role_level >= 3 (Administrador+) → ACCESO (fallback legacy)
    3. Si no cumple ninguna → DENEGADO
    
    Orden de filtrado por alcance (FASE 16):
    1. SuperAdministrador → ve todos
    2. sec_roles_alcance con GLOBAL → ve todos
    3. sec_roles_alcance con tipo específico → filtra por empresas del alcance
    4. Sin sec_roles_alcance → fallback a empresas_permitidas
    5. Sin nada → conjunto vacío
    
    Raises:
        HTTPException 403: Si no tiene permisos de gestión de usuarios
    """
    # FASE 9: Verificar permiso RBAC primero (SIN CAMBIOS)
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_USUARIOS_VER')
    
    if not tiene_permiso_rbac:
        # Fallback legacy: verificar nivel de rol
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:  # Mínimo Administrador
            raise HTTPException(status_code=403, detail="No autorizado")
    
    # FASE 16: Aplicar filtrado por alcance organizacional
    db = repo.get_db()
    alcance = await resolver_alcance_usuarios(current_user, db)
    
    # Registrar en log para auditoría
    logger.info(f"GET /api/users - Usuario: {current_user.get('email')}, "
                f"Fuente alcance: {alcance['fuente_alcance']}, "
                f"Global: {alcance['tiene_acceso_global']}, "
                f"Empresas: {len(alcance['empresas_ids'])}")
    
    if alcance['tiene_acceso_global']:
        return await repo.get_all_users()
    
    return await repo.get_users_by_empresas(alcance['empresas_ids'])


async def update_user(user_id: str, user_data: Dict, current_user: Dict) -> Dict:
    """
    Actualiza un usuario.
    
    FASE 10: Protección con permiso RBAC SISTEMA_USUARIOS_EDITAR + fallback legacy.
    CIERRE PILOTO RBAC: Validación de alcance organizacional.
    
    Raises:
        HTTPException 403: Si no tiene permisos, está fuera de alcance, o intenta modificar un SuperAdministrador
        HTTPException 404: Si el usuario no existe
    """
    # FASE 10: Verificar permiso RBAC primero
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_USUARIOS_EDITAR')
    
    if not tiene_permiso_rbac:
        # Fallback legacy: verificar nivel de rol
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:  # Mínimo Administrador
            raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener usuario objetivo
    target_user = await repo.find_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar jerarquía (regla de negocio existente - NO MODIFICAR)
    if not _can_manage_user(current_user, target_user):
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para modificar usuarios SuperAdministrador"
        )
    
    # CIERRE PILOTO RBAC: Verificar alcance organizacional
    db = repo.get_db()
    verificacion_alcance = await verificar_usuario_en_alcance(current_user, target_user, db)
    
    if not verificacion_alcance['permitido']:
        logger.warning(f"PUT /api/users/{user_id} DENEGADO por alcance: actor={current_user.get('email')}, "
                      f"target={target_user.get('email')}, razon={verificacion_alcance['razon']}")
        raise HTTPException(
            status_code=403, 
            detail="No tiene alcance para modificar este usuario"
        )
    
    logger.info(f"PUT /api/users/{user_id} PERMITIDO: actor={current_user.get('email')}, "
               f"target={target_user.get('email')}, razon={verificacion_alcance['razon']}")
    
    # Prevenir que un Administrador asigne el rol SuperAdministrador
    current_level = _get_role_level(current_user.get('role', ''))
    if 'role' in user_data and user_data['role'] == 'SuperAdministrador':
        if current_level < 100:
            raise HTTPException(
                status_code=403,
                detail="Solo un SuperAdministrador puede asignar el rol SuperAdministrador"
            )
    
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
    
    FASE 10: Protección con permiso RBAC SISTEMA_USUARIOS_ELIMINAR + fallback legacy.
    CIERRE PILOTO RBAC: Validación de alcance organizacional.
    
    Raises:
        HTTPException 403: Si no tiene permisos, está fuera de alcance, o intenta eliminar un SuperAdministrador
        HTTPException 404: Si el usuario no existe
    """
    # FASE 10: Verificar permiso RBAC primero
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_USUARIOS_ELIMINAR')
    
    if not tiene_permiso_rbac:
        # Fallback legacy: verificar nivel de rol
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:  # Mínimo Administrador
            raise HTTPException(status_code=403, detail="No autorizado")
    
    # Obtener usuario objetivo
    target_user = await repo.find_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar jerarquía (regla de negocio existente - NO MODIFICAR)
    if not _can_manage_user(current_user, target_user):
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para eliminar usuarios SuperAdministrador"
        )
    
    # CIERRE PILOTO RBAC: Verificar alcance organizacional
    db = repo.get_db()
    verificacion_alcance = await verificar_usuario_en_alcance(current_user, target_user, db)
    
    if not verificacion_alcance['permitido']:
        logger.warning(f"DELETE /api/users/{user_id} DENEGADO por alcance: actor={current_user.get('email')}, "
                      f"target={target_user.get('email')}, razon={verificacion_alcance['razon']}")
        raise HTTPException(
            status_code=403, 
            detail="No tiene alcance para eliminar este usuario"
        )
    
    logger.info(f"DELETE /api/users/{user_id} PERMITIDO: actor={current_user.get('email')}, "
               f"target={target_user.get('email')}, razon={verificacion_alcance['razon']}")
    
    await repo.deactivate_user(user_id)
    return {"message": "Usuario desactivado"}


async def update_user_permissions(user_id: str, permissions: Dict, current_user: Dict) -> Dict:
    """
    RBAC-SCOPE-E: Actualiza los permisos operativos de un usuario en EDARSAHUB SQL.
    
    Ya NO escribe en MongoDB. Los permisos operativos se guardan en:
    - Usuario_ServidoresAsignacion
    - Usuario_SucursalesAsignacion
    - Usuario_AlmacenesAsignacion
    
    Raises:
        HTTPException 403: Si no tiene permisos o intenta modificar un SuperAdministrador
        HTTPException 404: Si el usuario no existe
    """
    import pymssql
    import logging
    
    current_level = _get_role_level(current_user.get('role', ''))
    if current_level < 3:  # Mínimo Administrador
        raise HTTPException(status_code=403, detail="No autorizado")
    
    user = await repo.find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar jerarquía
    if not _can_manage_user(current_user, user):
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para modificar permisos de usuarios SuperAdministrador"
        )
    
    # RBAC-SCOPE-E: Escribir permisos en EDARSAHUB SQL
    try:
        conn = pymssql.connect(
            server=os.getenv('EDARSAHUB_SQL_HOST'),
            port=1433,
            user=os.getenv('EDARSAHUB_SQL_USER'),
            password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
            database='EDARSAHUB'
        )
        cursor = conn.cursor()
        
        # Resolver UsuarioID SQL desde PublicUUID
        user_id_lower = user_id.lower()
        cursor.execute("""
            SELECT UsuarioID 
            FROM Usuario_Catalogo 
            WHERE LOWER(CAST(PublicUUID AS VARCHAR(36))) = %s AND Activo = 1
        """, (user_id_lower,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Usuario no encontrado en SQL")
        
        usuario_id_sql = row[0]
        modificado_por = None  # TODO: Obtener UsuarioID del current_user si se desea
        
        # 1. ACTUALIZAR SERVIDORES
        if 'allowed_servers' in permissions:
            allowed_servers = permissions['allowed_servers'] or []
            
            # Desactivar asignaciones anteriores
            cursor.execute("""
                UPDATE Usuario_ServidoresAsignacion 
                SET Activo = 0, FechaModificacion = GETDATE(), ModificadoPor = %s,
                    Observaciones = CONCAT(ISNULL(Observaciones, ''), ' | Desactivado RBAC-SCOPE-E')
                WHERE UsuarioID = %s AND Activo = 1
            """, (modificado_por, usuario_id_sql))
            
            # Insertar nuevas asignaciones
            for server_uuid in allowed_servers:
                # Verificar que el servidor existe
                cursor.execute("""
                    SELECT id FROM Servidores_Conexiones 
                    WHERE LOWER(CAST(id AS VARCHAR(36))) = %s AND activo = 1
                """, (server_uuid.lower(),))
                
                if cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO Usuario_ServidoresAsignacion 
                        (UsuarioID, ServidorID, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
                        VALUES (%s, %s, %s, 1, GETDATE(), 'RBAC-SCOPE-E: Escritura SQL productiva')
                    """, (usuario_id_sql, server_uuid, server_uuid))
                else:
                    logging.warning(f"[RBAC-SCOPE-E] Servidor no encontrado: {server_uuid}")
        
        # 2. ACTUALIZAR SUCURSALES
        if 'allowed_sucursales' in permissions:
            allowed_sucursales = permissions['allowed_sucursales'] or {}
            
            # Desactivar asignaciones anteriores
            cursor.execute("""
                UPDATE Usuario_SucursalesAsignacion 
                SET Activo = 0, FechaModificacion = GETDATE(), ModificadoPor = %s,
                    Observaciones = CONCAT(ISNULL(Observaciones, ''), ' | Desactivado RBAC-SCOPE-E')
                WHERE UsuarioID = %s AND Activo = 1
            """, (modificado_por, usuario_id_sql))
            
            # Insertar nuevas asignaciones
            for server_uuid, sucursales in allowed_sucursales.items():
                # Verificar que el servidor existe
                cursor.execute("""
                    SELECT id FROM Servidores_Conexiones 
                    WHERE LOWER(CAST(id AS VARCHAR(36))) = %s AND activo = 1
                """, (server_uuid.lower(),))
                
                if cursor.fetchone():
                    for suc_codigo in (sucursales or []):
                        if suc_codigo:
                            cursor.execute("""
                                INSERT INTO Usuario_SucursalesAsignacion 
                                (UsuarioID, ServidorID, SucursalCodigo, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
                                VALUES (%s, %s, %s, %s, 1, GETDATE(), 'RBAC-SCOPE-E: Escritura SQL productiva')
                            """, (usuario_id_sql, server_uuid, suc_codigo, suc_codigo))
                else:
                    logging.warning(f"[RBAC-SCOPE-E] Servidor no encontrado para sucursales: {server_uuid}")
        
        # 3. ACTUALIZAR ALMACENES
        if 'allowed_warehouses' in permissions:
            allowed_warehouses = permissions['allowed_warehouses'] or {}
            
            # Desactivar asignaciones anteriores
            cursor.execute("""
                UPDATE Usuario_AlmacenesAsignacion 
                SET Activo = 0, FechaModificacion = GETDATE(), ModificadoPor = %s,
                    Observaciones = CONCAT(ISNULL(Observaciones, ''), ' | Desactivado RBAC-SCOPE-E')
                WHERE UsuarioID = %s AND Activo = 1
            """, (modificado_por, usuario_id_sql))
            
            # Insertar nuevas asignaciones
            for server_uuid, almacenes in allowed_warehouses.items():
                # Verificar que el servidor existe
                cursor.execute("""
                    SELECT id FROM Servidores_Conexiones 
                    WHERE LOWER(CAST(id AS VARCHAR(36))) = %s AND activo = 1
                """, (server_uuid.lower(),))
                
                if cursor.fetchone():
                    for alm_codigo in (almacenes or []):
                        if alm_codigo:
                            cursor.execute("""
                                INSERT INTO Usuario_AlmacenesAsignacion 
                                (UsuarioID, ServidorID, AlmacenCodigo, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
                                VALUES (%s, %s, %s, %s, 1, GETDATE(), 'RBAC-SCOPE-E: Escritura SQL productiva')
                            """, (usuario_id_sql, server_uuid, alm_codigo, alm_codigo))
                else:
                    logging.warning(f"[RBAC-SCOPE-E] Servidor no encontrado para almacenes: {server_uuid}")
        
        conn.commit()
        conn.close()
        
        logging.info(f"[RBAC-SCOPE-E] Permisos actualizados en SQL para usuario {user_id}")
        return {"message": "Permisos actualizados"}
        
    except pymssql.Error as e:
        logging.error(f"[RBAC-SCOPE-E] Error SQL al actualizar permisos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al guardar permisos en SQL: {str(e)}")


async def create_user_admin(user_data: Dict, current_user: Dict) -> Dict:
    """
    FASE 11: Crea un usuario desde administración (endpoint administrativo).
    
    Este endpoint es DIFERENTE de POST /auth/register:
    - Requiere autenticación
    - Requiere permiso SISTEMA_USUARIOS_CREAR o fallback legacy
    - NO genera token JWT (el usuario nuevo debe hacer login)
    - Respeta jerarquía de roles (no puede crear SuperAdmin sin ser SuperAdmin)
    
    Orden de acceso:
    1. Si tiene permiso RBAC (sec_permisos/sec_roles/sec_rol/SuperAdmin) → ACCESO
    2. Si NO tiene RBAC pero role_level >= 3 (Administrador+) → ACCESO (fallback legacy)
    3. Si no cumple ninguna → DENEGADO
    
    Args:
        user_data: Dict con email, name, password, role y permisos opcionales
        current_user: Usuario que realiza la creación
        
    Returns:
        Dict con datos del usuario creado (sin password ni token)
        
    Raises:
        HTTPException 403: Si no tiene permisos o intenta crear SuperAdmin sin serlo
        HTTPException 400: Si el email ya existe o datos inválidos
    """
    # FASE 11: Verificar permiso RBAC primero
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_USUARIOS_CREAR')
    
    if not tiene_permiso_rbac:
        # Fallback legacy: verificar nivel de rol
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:  # Mínimo Administrador
            raise HTTPException(status_code=403, detail="No autorizado para crear usuarios")
    
    # Validar campos requeridos
    email = user_data.get('email')
    name = user_data.get('name')
    password = user_data.get('password')
    role = user_data.get('role', 'Usuario')
    
    if not email or not name or not password:
        raise HTTPException(status_code=400, detail="Email, nombre y contraseña son requeridos")
    
    # Regla de jerarquía: solo SuperAdmin puede crear SuperAdmin
    current_level = _get_role_level(current_user.get('role', ''))
    if role == 'SuperAdministrador' and current_level < 100:
        raise HTTPException(
            status_code=403,
            detail="Solo un SuperAdministrador puede crear usuarios SuperAdministrador"
        )
    
    # Verificar si el email ya existe
    existing = await repo.find_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Hash de contraseña
    hashed_pw = hash_password(password)
    
    # Crear usuario
    new_user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "name": name,
        "role": role,
        "telefono": user_data.get('telefono'),
        "sucursales": user_data.get('sucursales', []),
        "allowed_servers": user_data.get('allowed_servers', []),
        "allowed_sucursales": user_data.get('allowed_sucursales', {}),
        "allowed_warehouses": user_data.get('allowed_warehouses', {}),
        "active": True,
        "password": hashed_pw,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get('id')  # Trazabilidad
    }
    
    await repo.create_user(new_user)
    
    # Retornar sin password ni _id (MongoDB agrega _id al dict después de insert)
    user_response = {k: v for k, v in new_user.items() if k not in ('password', '_id')}
    
    return {"message": "Usuario creado exitosamente", "user": user_response}


# ============================================================================
# ROLES CRUD
# ============================================================================

async def get_roles(current_user: Dict) -> List[Dict]:
    """
    Obtiene todos los roles, creando los predeterminados si no existen.
    
    FASE 9: Protección con permiso RBAC SISTEMA_ROLES_VER + fallback legacy.
    
    Orden de acceso:
    1. Si tiene permiso RBAC (sec_permisos/sec_roles/sec_rol/SuperAdmin) → ACCESO
    2. Si NO tiene RBAC pero role_level >= 3 (Administrador+) → ACCESO (fallback legacy)
    3. Si no cumple ninguna → DENEGADO
    
    Raises:
        HTTPException 403: Si no tiene permisos de gestión de roles
    """
    # FASE 9: Verificar permiso RBAC primero
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_ROLES_VER')
    
    if not tiene_permiso_rbac:
        # Fallback legacy: verificar nivel de rol
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:  # Mínimo Administrador
            raise HTTPException(status_code=403, detail="No autorizado")
    
    roles = await repo.get_all_roles()
    
    # Si no hay roles, crear los predeterminados
    if not roles:
        roles = await repo.create_default_roles(DEFAULT_ROLES)
    
    return roles


async def create_role(role_data: Dict, current_user: Dict) -> Dict:
    """
    Crea un nuevo rol.
    
    FASE 11: Protección con permiso RBAC SISTEMA_ROLES_CREAR + fallback legacy.
    
    Orden de acceso:
    1. Si tiene permiso RBAC (sec_permisos/sec_roles/sec_rol/SuperAdmin) → ACCESO
    2. Si NO tiene RBAC pero role_level >= 3 (Administrador+) → ACCESO (fallback legacy)
    3. Si no cumple ninguna → DENEGADO
    
    Raises:
        HTTPException 403: Si no tiene permisos
        HTTPException 400: Si ya existe un rol con ese nombre
    """
    # FASE 11: Verificar permiso RBAC primero
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_ROLES_CREAR')
    
    if not tiene_permiso_rbac:
        # Fallback legacy: verificar nivel de rol
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:  # Mínimo Administrador
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
    
    FASE 10: Protección con permiso RBAC SISTEMA_ROLES_EDITAR + fallback legacy.
    
    Raises:
        HTTPException 403: Si no tiene permisos
        HTTPException 404: Si el rol no existe
        HTTPException 400: Si se intenta duplicar nombre
    """
    # FASE 10: Verificar permiso RBAC primero
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_ROLES_EDITAR')
    
    if not tiene_permiso_rbac:
        # Fallback legacy: verificar nivel de rol
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:  # Mínimo Administrador
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
    
    FASE 10: Protección con permiso RBAC SISTEMA_ROLES_ELIMINAR + fallback legacy.
    
    Raises:
        HTTPException 403: Si no tiene permisos
        HTTPException 404: Si el rol no existe
        HTTPException 400: Si es rol de sistema o tiene usuarios asignados
    """
    # FASE 10: Verificar permiso RBAC primero
    tiene_permiso_rbac = await verificar_permiso_rbac(current_user, 'SISTEMA_ROLES_ELIMINAR')
    
    if not tiene_permiso_rbac:
        # Fallback legacy: verificar nivel de rol
        current_level = _get_role_level(current_user.get('role', ''))
        if current_level < 3:  # Mínimo Administrador
            raise HTTPException(status_code=403, detail="No autorizado")
    
    existing = await repo.find_role_by_id(role_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Reglas de negocio existentes - NO MODIFICAR
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
    'create_user_admin',  # FASE 11
    'update_user',
    'delete_user',
    'update_user_permissions',
    # Roles
    'get_roles',
    'create_role',
    'update_role',
    'delete_role',
]
