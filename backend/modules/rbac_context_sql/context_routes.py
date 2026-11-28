from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Optional
from core.security import get_current_user
from core.auth.sql_user_identity import enrich_current_user_with_sql_id
from modules.rbac_context_sql.context_service import RBACContextService

router = APIRouter(prefix="/api", tags=["RBAC Context Access"])
service = RBACContextService()


@router.get("/auth/access-context")
async def get_access_context(
    unidad_negocio_id: Optional[str] = None,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    current_user: Dict = Depends(get_current_user),
):
    current_user = enrich_current_user_with_sql_id(current_user)
    if not current_user.get("usuario_id") and not current_user.get("UsuarioID"):
        raise HTTPException(status_code=403, detail="Identidad SQL canónica requerida")
    try:
        ctx = service.get_user_context(
            current_user,
            unidad_negocio_id=unidad_negocio_id,
            empresa_id=empresa_id,
            sucursal_id=sucursal_id,
            raise_on_forbidden=True,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if not ctx:
        raise HTTPException(status_code=404, detail="No se pudo resolver el contexto del usuario")
    return ctx


@router.post("/auth/access-context/select-unit")
async def select_access_unit(
    body: Dict,
    current_user: Dict = Depends(get_current_user),
):
    current_user = enrich_current_user_with_sql_id(current_user)
    if not current_user.get("usuario_id") and not current_user.get("UsuarioID"):
        raise HTTPException(status_code=403, detail="Identidad SQL canónica requerida")
    unidad_negocio_id = body.get("unidad_negocio_id")
    empresa_id = body.get("empresa_id")
    sucursal_id = body.get("sucursal_id")
    if unidad_negocio_id is None and empresa_id is None and sucursal_id is None:
        raise HTTPException(status_code=400, detail="Debe especificar unidad_negocio_id, empresa_id o sucursal_id")
    try:
        ctx = service.get_user_context(
            current_user,
            unidad_negocio_id=unidad_negocio_id,
            empresa_id=empresa_id,
            sucursal_id=sucursal_id,
            raise_on_forbidden=True,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if not ctx:
        raise HTTPException(status_code=404, detail="No se pudo resolver el contexto de la unidad")
    return ctx
