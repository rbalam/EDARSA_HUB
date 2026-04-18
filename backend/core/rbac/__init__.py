"""
EDARSA HUB - RBAC (Role-Based Access Control) Core Module
==========================================================
Fase 2D - Sistema de control de acceso granular basado en roles.

Componentes:
- schemas.py: Modelos Pydantic para roles, permisos y asignaciones
- repository.py: Acceso a datos MongoDB
- service.py: Motor de autorización central
- middleware.py: Decoradores y middleware para FastAPI
- routes.py: Endpoints de administración RBAC
"""

from .schemas import (
    Permiso,
    PermisoCreate,
    RolRBAC,
    RolRBACCreate,
    AsignacionRol,
    AsignacionRolCreate,
    PermisoUsuarioResponse,
    PERMISOS_SISTEMA,
    ROLES_SISTEMA,
)

from .service import (
    RBACService,
    check_permission,
    get_user_permissions,
    PermisoDenegadoError,
)

from .middleware import (
    require_permission,
    require_any_permission,
    require_all_permissions,
)

__all__ = [
    # Schemas
    'Permiso',
    'PermisoCreate',
    'RolRBAC',
    'RolRBACCreate',
    'AsignacionRol',
    'AsignacionRolCreate',
    'PermisoUsuarioResponse',
    'PERMISOS_SISTEMA',
    'ROLES_SISTEMA',
    # Service
    'RBACService',
    'check_permission',
    'get_user_permissions',
    'PermisoDenegadoError',
    # Middleware
    'require_permission',
    'require_any_permission',
    'require_all_permissions',
]
