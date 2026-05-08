"""
FASE 9: Helper mínimo de verificación RBAC.
Contiene ÚNICAMENTE la función para verificar permisos granulares.

NO es un framework general - es un helper específico para FASE 9.
"""

from motor.motor_asyncio import AsyncIOMotorClient
import os

# Conexión a MongoDB (reutiliza la existente del entorno)
_client = None
_db = None


def _get_db():
    """Obtiene conexión a MongoDB de forma lazy."""
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
        _db = _client[os.environ.get('DB_NAME', 'edarsa_hub')]
    return _db


# Whitelist FASE 11 - NO EXPANDIR sin autorización
PERMISOS_WHITELIST = [
    "SISTEMA_ESTRUCTURA_VER",
    "SISTEMA_USUARIOS_VER",
    "SISTEMA_USUARIOS_CREAR",      # FASE 11
    "SISTEMA_USUARIOS_EDITAR",
    "SISTEMA_USUARIOS_ELIMINAR",
    "SISTEMA_ROLES_VER",
    "SISTEMA_ROLES_CREAR",         # FASE 11
    "SISTEMA_ROLES_EDITAR",
    "SISTEMA_ROLES_ELIMINAR",
    "SCHEDULER_VER",               # Para ver estado del scheduler
    "SCHEDULER_GESTIONAR"          # Para controlar jobs
]
ROLES_WHITELIST = ["VISOR_ESTRUCTURA", "VISOR_SISTEMA", "VISOR_ADMIN", "ADMIN_USUARIOS", "GESTOR_SISTEMA"]


async def verificar_permiso_rbac(user: dict, permiso: str) -> bool:
    """
    FASE 9: Verifica si el usuario tiene un permiso RBAC.
    
    Orden de resolución (4 capas):
    1. Permisos directos (sec_permisos) → FASE 4
    2. Múltiples roles (sec_roles array) → FASE 6
    3. Rol único (sec_rol string) → FASE 5 (compatibilidad)
    4. Fallback SuperAdmin → FASE 3
    
    Args:
        user: Diccionario con datos del usuario (debe incluir sec_permisos, sec_roles, sec_rol, role)
        permiso: Código del permiso a verificar (ej: 'SISTEMA_USUARIOS_VER')
    
    Returns:
        bool: True si tiene el permiso por cualquiera de las 4 capas
    
    NOTA: Esta función NO implementa el fallback legacy (role_level).
          Ese fallback se maneja en el código que llama a esta función.
    """
    db = _get_db()
    
    # 1. Permisos directos (FASE 4)
    permisos_directos = user.get('sec_permisos', [])
    if permiso in permisos_directos:
        return True
    
    # 2. Múltiples roles (FASE 6)
    sec_roles = user.get('sec_roles', [])
    for rol_codigo in sec_roles:
        if rol_codigo in ROLES_WHITELIST:
            rol_doc = await db.sec_roles.find_one({"codigo": rol_codigo, "activo": True})
            if rol_doc and permiso in rol_doc.get('permisos', []):
                return True
    
    # 3. Rol único - compatibilidad FASE 5
    sec_rol = user.get('sec_rol')
    if sec_rol and sec_rol in ROLES_WHITELIST:
        rol_doc = await db.sec_roles.find_one({"codigo": sec_rol, "activo": True})
        if rol_doc and permiso in rol_doc.get('permisos', []):
            return True
    
    # 4. Fallback SuperAdmin (FASE 3)
    if user.get('role') == 'SuperAdministrador':
        return True
    
    return False
