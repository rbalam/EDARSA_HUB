"""
EDARSA HUB - RBAC (Role-Based Access Control) Core Module
==========================================================
FASE 4B-RBAC: Sistema de control de acceso granular basado en roles.

MIGRACIÓN COMPLETADA: RBAC ahora usa EDARSAHUB SQL Server como fuente única.
MongoDB ya NO es fuente de datos para RBAC.

Componentes:
- schemas.py: Modelos Pydantic para roles, permisos y asignaciones
- repository.py: Proxy que delega a repository_sql.py
- repository_sql.py: Acceso a datos EDARSAHUB SQL Server
- service.py: Motor de autorización central
- middleware.py: Decoradores y middleware para FastAPI
- routes.py: Endpoints de administración RBAC

Tablas SQL:
- Usuario_Roles
- Usuario_RolesAsignacion
- Usuario_Modulos
- Usuario_Acciones
- Usuario_PermisosRolModulo
- Usuario_LogRBACVerificacion
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
