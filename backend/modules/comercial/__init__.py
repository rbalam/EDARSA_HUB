"""EDARSA HUB Comercial module.

The module is SQL-first. The canonical detail route replaces the duplicated
legacy GET route while every other Comercial route remains registered without
changing public URLs.
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
from modules.comercial.router_filter import without_legacy_detail_route


def get_router():
    """Return Comercial routes with one canonical daily-detail GET route."""

    from modules.comercial.canonical_detail_routes import (
        router as canonical_detail_router,
    )
    from modules.comercial.routes import router as legacy_router

    router = APIRouter()
    router.include_router(canonical_detail_router)
    router.routes.extend(without_legacy_detail_route(legacy_router.routes))
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
