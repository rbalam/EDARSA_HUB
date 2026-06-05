"""
EDARSA HUB - Auth Module
========================
Módulo de autenticación, usuarios y roles.

FASE 3 DEL REFACTOR MODULAR (Diciembre 2025)

Componentes:
- routes.py: Endpoints FastAPI
- schemas.py: Modelos Pydantic
- service.py: Lógica de negocio
- repository.py: Acceso a MongoDB

Inicialización:
    from modules.auth import init_auth_module
    init_auth_module(db)
"""

from modules.auth.repository import init_auth_repository
from modules.auth.schemas import (
    User, UserCreate, UserLogin, UserRole,
    Role, RoleCreate, RoleUpdate,
    MODULOS_DISPONIBLES, DEFAULT_ROLES
)


def get_router():
    """Lazy import del router para evitar circular imports."""
    from modules.auth.routes import router
    return router


def init_auth_module(database) -> None:
    """
    Inicializa el módulo de auth con la conexión a MongoDB.
    
    Args:
        database: Instancia de Any
    """
    init_auth_repository(database)


__all__ = [
    'get_router',
    'init_auth_module',
    # Schemas re-exportados para compatibilidad
    'User',
    'UserCreate',
    'UserLogin',
    'UserRole',
    'Role',
    'RoleCreate',
    'RoleUpdate',
    'MODULOS_DISPONIBLES',
    'DEFAULT_ROLES',
]
