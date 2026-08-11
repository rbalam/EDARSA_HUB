from fastapi import APIRouter, Depends, Query, HTTPException
from core.security import get_current_user
from modules.alertas_estrategicas.service import obtener_resumen_alertas


router = APIRouter(
    prefix="/api/alertas-estrategicas",
    tags=["Alertas Estratégicas"],
)


@router.get("/resumen")
async def resumen_alertas(
    server_id: str = Query(default=""),
    limite: int = Query(default=200, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    return await obtener_resumen_alertas(
        server_id=server_id,
        limite=limite,
        current_user=current_user,
    )
