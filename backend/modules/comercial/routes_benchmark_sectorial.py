"""
Benchmark Sectorial - Endpoints (SOLO LECTURA, NO-LIVE)
=======================================================
Reporte sectorial de precios derivado de tablas canonicas EDARSAHUB.
RBAC: comercial.benchmark.ver (sembrado en DB).
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from core.rbac.middleware import require_permission
from modules.comercial.services import benchmark_sectorial_service as svc

router = APIRouter(prefix="/comercial/benchmark-sectorial", tags=["Comercial - Benchmark Sectorial"])


@router.get("/sectores", summary="Catalogo de sectores/segmentos disponibles")
async def get_sectores(
    empresa_id: int = Query(..., description="Empresa comercial"),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver")),
):
    return svc.sectores_disponibles(empresa_id)


@router.get("/vs-sector", summary="Vista A: nuestra unidad vs promedio del sector")
async def get_vs_sector(
    empresa_id: int = Query(...),
    unidad_negocio_pk: Optional[int] = Query(None),
    segmento: Optional[str] = Query(None, description="Filtrar por SegmentoPrecio"),
    giro: Optional[str] = Query(None, description="Filtrar por TipoRestaurante"),
    umbral_pct: float = Query(15.0, ge=0, le=100, description="Umbral % para el semaforo de oportunidad"),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver")),
):
    return svc.vista_vs_sector(empresa_id, unidad_negocio_pk, segmento, giro, umbral_pct)


@router.get("/interno", summary="Vista B: comparativa interna entre nuestras unidades")
async def get_interno(
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver")),
):
    return svc.vista_interno()


@router.get("/por-segmento", summary="Vista C: nuestra unidad vs promedio por segmento")
async def get_por_segmento(
    empresa_id: int = Query(...),
    unidad_negocio_pk: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver")),
):
    return svc.vista_por_segmento(empresa_id, unidad_negocio_pk)
