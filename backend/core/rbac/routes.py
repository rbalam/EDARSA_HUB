from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - RBAC Routes
========================
Endpoints de administración del sistema RBAC.

Endpoints:
- GET  /api/v2/rbac/roles            - Lista roles
- POST /api/v2/rbac/roles            - Crear rol
- GET  /api/v2/rbac/roles/{id}       - Obtener rol
- PUT  /api/v2/rbac/roles/{id}       - Actualizar rol
- DELETE /api/v2/rbac/roles/{id}     - Eliminar rol

- GET  /api/v2/rbac/permisos         - Lista permisos

- POST /api/v2/rbac/asignar          - Asignar rol a usuario
- POST /api/v2/rbac/revocar          - Revocar rol de usuario

- GET  /api/v2/rbac/usuario/{id}/permisos  - Permisos de un usuario
- GET  /api/v2/rbac/mis-permisos     - Mis permisos

- GET  /api/v2/rbac/audit            - Logs de auditoría
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
import logging
import os

from core.security import verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .service import RBACService
from .schemas import (
    RolRBACCreate,
    RolRBACUpdate,
    AsignacionRolCreate,
)
from .middleware import require_permission, require_explicit_permission, get_current_user_with_permissions

router = APIRouter(prefix="/rbac", tags=["RBAC"])
logger = logging.getLogger(__name__)
security = HTTPBearer()


def _get_db():
    """
    Parámetro legacy para RBACService.

    MongoDB está eliminado para RBAC; RBACRepository delega a SQL Server e ignora
    este argumento. Retornar None evita fallas por client None.
    """
    return None


def get_rbac_service():
    """Dependency para obtener el servicio RBAC."""
    db = _get_db()
    return RBACService(db)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Obtiene usuario actual del token."""
    try:
        payload = verify_token(credentials.credentials)
        return {
            "id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


# =============================================================================
# ROLES
# =============================================================================

@router.get("/roles", summary="Listar roles")
async def listar_roles(
    current_user: dict = Depends(require_explicit_permission("RBAC_VER")),
    service: RBACService = Depends(get_rbac_service)
):
    """Lista todos los roles del sistema."""
    roles = service.get_all_roles()
    return {
        "total": len(roles),
        "items": roles
    }


@router.post("/roles", summary="Crear rol")
async def crear_rol(
    data: RolRBACCreate,
    current_user: dict = Depends(require_explicit_permission("RBAC_ADMIN")),
    service: RBACService = Depends(get_rbac_service)
):
    """Crea un nuevo rol."""
    # Verificar que no exista
    existing = service.repo.get_rol_by_nombre(data.nombre)
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")
    
    rol = service.create_rol(data.model_dump(), created_by=current_user.get("id", ""))
    return rol


@router.get("/roles/{rol_id}", summary="Obtener rol")
async def obtener_rol(
    rol_id: str,
    current_user: dict = Depends(require_explicit_permission("RBAC_VER")),
    service: RBACService = Depends(get_rbac_service)
):
    """Obtiene un rol por ID."""
    rol = service.get_rol(rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol


@router.put("/roles/{rol_id}", summary="Actualizar rol")
async def actualizar_rol(
    rol_id: str,
    data: RolRBACUpdate,
    current_user: dict = Depends(require_explicit_permission("RBAC_ADMIN")),
    service: RBACService = Depends(get_rbac_service)
):
    """Actualiza un rol existente."""
    existing = service.get_rol(rol_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    if existing.get("es_sistema") and data.nombre and data.nombre != existing.get("nombre"):
        raise HTTPException(status_code=400, detail="No se puede cambiar el nombre de roles del sistema")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    rol = service.update_rol(rol_id, update_data)
    return rol


@router.delete("/roles/{rol_id}", summary="Eliminar rol")
async def eliminar_rol(
    rol_id: str,
    current_user: dict = Depends(require_explicit_permission("RBAC_ADMIN")),
    service: RBACService = Depends(get_rbac_service)
):
    """Elimina un rol (soft delete)."""
    existing = service.get_rol(rol_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    if existing.get("es_sistema"):
        raise HTTPException(status_code=400, detail="No se pueden eliminar roles del sistema")
    
    success = service.delete_rol(rol_id)
    if not success:
        raise HTTPException(status_code=400, detail="No se pudo eliminar el rol")
    
    return {"message": "Rol eliminado"}


# =============================================================================
# PERMISOS
# =============================================================================

@router.get("/permisos", summary="Listar permisos")
async def listar_permisos(
    modulo: Optional[str] = Query(None, description="Filtrar por módulo"),
    current_user: dict = Depends(require_explicit_permission("RBAC_VER")),
    service: RBACService = Depends(get_rbac_service)
):
    """Lista todos los permisos del sistema."""
    permisos = service.get_all_permisos()
    
    if modulo:
        permisos = [p for p in permisos if p.get("modulo") == modulo]
    
    return {
        "total": len(permisos),
        "items": permisos
    }


# =============================================================================
# ASIGNACIONES
# =============================================================================

@router.post("/asignar", summary="Asignar rol a usuario")
async def asignar_rol(
    data: AsignacionRolCreate,
    current_user: dict = Depends(require_explicit_permission("RBAC_ADMIN")),
    service: RBACService = Depends(get_rbac_service)
):
    """Asigna un rol a un usuario."""
    # Verificar que el rol existe
    rol = service.get_rol(data.rol_id)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    asignacion = service.asignar_rol_a_usuario(
        user_id=data.user_id,
        rol_id=data.rol_id,
        asignado_por=current_user.get("id", ""),
        sucursal_id=data.sucursal_id
    )
    
    return {
        "message": f"Rol {rol.get('nombre')} asignado exitosamente",
        "asignacion": asignacion
    }


@router.post("/revocar", summary="Revocar rol de usuario")
async def revocar_rol(
    user_id: str,
    rol_id: str,
    sucursal_id: Optional[str] = None,
    current_user: dict = Depends(require_explicit_permission("RBAC_ADMIN")),
    service: RBACService = Depends(get_rbac_service)
):
    """Revoca un rol de un usuario."""
    success = service.revocar_rol_de_usuario(user_id, rol_id, sucursal_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="No se encontró la asignación o ya estaba revocada")
    
    return {"message": "Rol revocado exitosamente"}


# =============================================================================
# CONSULTA DE PERMISOS
# =============================================================================

@router.get("/usuario/{user_id}/permisos", summary="Permisos de un usuario")
async def obtener_permisos_usuario(
    user_id: str,
    current_user: dict = Depends(require_explicit_permission("RBAC_ADMIN")),
    service: RBACService = Depends(get_rbac_service)
):
    """Obtiene los permisos efectivos de un usuario."""
    user_data = {"id": user_id}
    permisos = service.get_user_permissions(user_data)
    return permisos


@router.get("/mis-permisos", summary="Mis permisos")
async def obtener_mis_permisos(
    current_user: dict = Depends(get_current_user_with_permissions)
):
    """Obtiene los permisos del usuario autenticado."""
    return {
        "user_id": current_user.get("id"),
        "email": current_user.get("email"),
        "role_legacy": current_user.get("role"),
        "roles_rbac": current_user.get("roles_rbac", []),
        "permisos": current_user.get("permisos", []),
        "nivel_jerarquia": current_user.get("nivel_jerarquia", 0),
        "es_admin": current_user.get("es_admin", False),
    }


# =============================================================================
# AUDITORÍA
# =============================================================================

@router.get("/audit", summary="Logs de auditoría RBAC")
async def obtener_audit_logs(
    user_id: Optional[str] = Query(None),
    resultado: Optional[str] = Query(None, description="PERMITIDO o DENEGADO"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(require_explicit_permission("RBAC_ADMIN")),
    service: RBACService = Depends(get_rbac_service)
):
    """Obtiene logs de auditoría de verificaciones de permisos."""
    logs = service.get_audit_logs(user_id=user_id, resultado=resultado, limit=limit)
    return {
        "total": len(logs),
        "items": logs
    }


# =============================================================================
# VERIFICACIÓN
# =============================================================================

@router.post("/verificar", summary="Verificar permiso")
async def verificar_permiso(
    permiso: str,
    current_user: dict = Depends(get_current_user),
    service: RBACService = Depends(get_rbac_service)
):
    """Verifica si el usuario actual tiene un permiso específico."""
    tiene_permiso = service.check_permission(current_user, permiso, audit=False)
    
    return {
        "permiso": permiso,
        "tiene_permiso": tiene_permiso,
        "user_id": current_user.get("id"),
    }


__all__ = ['router']
