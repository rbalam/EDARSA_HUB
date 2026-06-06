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
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)
    ctx = service.get_user_context(current_user, unidad_negocio_id=unidad_negocio_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="No se pudo resolver el contexto del usuario")
    return ctx

@router.post("/auth/access-context/select-unit")
async def select_access_unit(
    body: Dict,
    current_user: Dict = Depends(get_current_user)
):
    current_user = enrich_current_user_with_sql_id(current_user)
    unidad_negocio_id = body.get("unidad_negocio_id")
    ctx = service.get_user_context(current_user, unidad_negocio_id=unidad_negocio_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="No se pudo resolver el contexto de la unidad")
    return ctx
