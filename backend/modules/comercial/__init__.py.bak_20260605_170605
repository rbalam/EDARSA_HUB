"""
EDARSA HUB - Comercial Module
=============================
Módulo comercial: dashboards, ventas, metas, ticket perfecto.

FASE 5B DEL REFACTOR MODULAR (Diciembre 2025)

Componentes:
- routes.py: Endpoints de comercial (migrados de server.py)
- schemas.py: Modelos Pydantic definidos
- service.py: Lógica de negocio y helpers
- repository.py: Queries SQL y acceso a MongoDB
- adapters.py: Integración con APIs locales MPRO

Estado: MIGRACIÓN EN PROGRESO (Fase 5B)

Funciones migradas en Fase 5B:
- APIS_MPRO_LOCALES (configuración)
- query_api_mpro_local()
- obtener_ventas_dia_api_local()
- sumar_ventas_api_local_a_sucursal()

Inicialización:
    from modules.comercial import init_comercial_module
    init_comercial_module(db)
"""

from modules.comercial.repository import init_comercial_repository
from modules.comercial.schemas import (
    VentaSucursal,
    MetaSucursal,
    TicketPerfecto,
    DashboardComercialResponse,
    TableroEjecutivoResponse,
    ReportePaxRequest,
)
from modules.comercial.adapters import (
    APIS_MPRO_LOCALES,
    query_api_mpro_local,
    obtener_ventas_dia_api_local,
    sumar_ventas_api_local_a_sucursal,
)


def get_router():
    """Lazy import del router para evitar circular imports."""
    from modules.comercial.routes import router
    return router


def init_comercial_module(database) -> None:
    """
    Inicializa el módulo comercial con la conexión a MongoDB.
    
    Args:
        database: Instancia de Any
    """
    init_comercial_repository(database)


__all__ = [
    'get_router',
    'init_comercial_module',
    # Schemas
    'VentaSucursal',
    'MetaSucursal',
    'TicketPerfecto',
    'DashboardComercialResponse',
    'TableroEjecutivoResponse',
    'ReportePaxRequest',
    # Adapters (APIs locales MPRO)
    'APIS_MPRO_LOCALES',
    'query_api_mpro_local',
    'obtener_ventas_dia_api_local',
    'sumar_ventas_api_local_a_sucursal',
]
