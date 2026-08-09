"""Endpoints internos del dominio Economía."""

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.rbac import require_explicit_permission_dual

from .service import EconomiaService


router = APIRouter(
    prefix="/economia",
    tags=["Economia"],
)


async def require_economia_indicadores_leer(
    current_user: Dict[str, Any] = Depends(
        require_explicit_permission_dual(
            "economia.indicadores.leer"
        )
    ),
) -> Dict[str, Any]:
    return current_user


async def require_economia_series_leer(
    current_user: Dict[str, Any] = Depends(
        require_explicit_permission_dual(
            "economia.series.leer"
        )
    ),
) -> Dict[str, Any]:
    return current_user


async def require_economia_backfill_ejecutar(
    current_user: Dict[str, Any] = Depends(
        require_explicit_permission_dual(
            "economia.backfill.ejecutar"
        )
    ),
) -> Dict[str, Any]:
    return current_user


async def require_economia_contexto_administrar(
    current_user: Dict[str, Any] = Depends(
        require_explicit_permission_dual(
            "economia.contexto.administrar"
        )
    ),
) -> Dict[str, Any]:
    return current_user


@router.get("/series")
async def listar_series(
    activo: Optional[bool] = Query(default=True),
    limite: int = Query(default=500, ge=1, le=5000),
    _: Dict[str, Any] = Depends(
        require_economia_series_leer
    ),
):
    return EconomiaService.listar_series(
        activo=activo,
        limite=limite,
    )


@router.get("/series/{serie_id}")
async def obtener_serie(
    serie_id: str,
    _: Dict[str, Any] = Depends(
        require_economia_series_leer
    ),
):
    row = EconomiaService.obtener_serie(serie_id)

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Serie economica no encontrada",
        )

    return row


@router.get("/series/{serie_id}/valores")
async def listar_valores(
    serie_id: str,
    desde: Optional[date] = Query(default=None),
    hasta: Optional[date] = Query(default=None),
    limite: int = Query(default=500, ge=1, le=5000),
    _: Dict[str, Any] = Depends(
        require_economia_indicadores_leer
    ),
):
    if (
        desde is not None
        and hasta is not None
        and desde > hasta
    ):
        raise HTTPException(
            status_code=422,
            detail="El rango de fechas es invalido",
        )

    return EconomiaService.listar_valores(
        serie_id=serie_id,
        desde=desde,
        hasta=hasta,
        limite=limite,
    )


@router.post("/series/{serie_id}/backfill")
async def ejecutar_backfill(
    serie_id: int,
    desde: date = Query(...),
    hasta: date = Query(...),
    _: Dict[str, Any] = Depends(
        require_economia_backfill_ejecutar
    ),
):
    if desde > hasta:
        raise HTTPException(
            status_code=422,
            detail="El rango de fechas es invalido",
        )

    try:
        return await EconomiaService.backfill_serie(
            serie_id=serie_id,
            desde=desde,
            hasta=hasta,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get("/contextos")
async def listar_contextos(
    _: Dict[str, Any] = Depends(
        require_economia_contexto_administrar
    ),
):
    return EconomiaService.listar_contextos_activos()
