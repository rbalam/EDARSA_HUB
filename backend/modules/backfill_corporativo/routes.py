from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from core.security import get_current_user
from .service import ejecutar_backfill, MODULOS_VALIDOS

router = APIRouter(prefix="/admin/backfill", tags=["Backfill Corporativo"])

class BackfillRequest(BaseModel):
    server_id: str
    fecha_inicio: str
    fecha_fin: str
    modulo: str
    dry_run: bool = True

@router.get("/modulos")
async def get_backfill_modulos(current_user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "modulos": sorted(MODULOS_VALIDOS)
    }

@router.post("")
async def post_backfill(req: BackfillRequest, current_user: dict = Depends(get_current_user)):
    return ejecutar_backfill(
        server_id=req.server_id,
        fecha_inicio=req.fecha_inicio,
        fecha_fin=req.fecha_fin,
        modulo=req.modulo,
        dry_run=req.dry_run
    )
