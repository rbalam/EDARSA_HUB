"""EDARSA HUB Comercial module.

The module is SQL-first. The canonical detail router is registered before the
legacy router so the existing public path resolves to the canonical handler
without changing frontend URLs.
"""

from fastapi import APIRouter

from modules.comercial.repository import init_comercial_repository
from modules.comercial.schemas import (
    DashboardComercialResponse,
    MetaSucursal,
    ReportePaxRequest,
    TableroEjecutivoResponse,
    TicketPerfecto,
    VentaSucursal,
)
from modules.comercial.adapters import (
    APIS_MPRO_LOCALES,
    obtener_ventas_dia_api_local,
    query_api_mpro_local,
    sumar_ventas_api_local_a_sucursal,
)


def get_router():
    """Return Comercial routes with canonical overrides registered first."""

    from modules.comercial.canonical_detail_routes import (
        router as canonical_detail_router,
    )
    from modules.comercial.routes import router as legacy_router

    router = APIRouter()
    router.include_router(canonical_detail_router)
    router.include_router(legacy_router)
    return router


def init_comercial_module(database=None) -> None:
    """Initialize the SQL-only Comercial repository.

    ``database`` remains accepted only for backward-compatible startup calls.
    The repository does not retain or use a MongoDB connection.
    """

    del database
    init_comercial_repository(None)


__all__ = [
    "get_router",
    "init_comercial_module",
    "VentaSucursal",
    "MetaSucursal",
    "TicketPerfecto",
    "DashboardComercialResponse",
    "TableroEjecutivoResponse",
    "ReportePaxRequest",
    "APIS_MPRO_LOCALES",
    "query_api_mpro_local",
    "obtener_ventas_dia_api_local",
    "sumar_ventas_api_local_a_sucursal",
]
