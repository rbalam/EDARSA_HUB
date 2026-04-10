"""
EDARSA HUB - Comercial Module
=============================
Módulo comercial: dashboards, ventas, metas, ticket perfecto.

FASE 5 DEL REFACTOR MODULAR (Diciembre 2025)

Componentes:
- routes.py: Router vacío (endpoints en server.py)
- schemas.py: Modelos Pydantic definidos
- service.py: Funciones auxiliares
- repository.py: Queries SQL y acceso a MongoDB

Estado: ESTRUCTURA LISTA, ENDPOINTS PENDIENTES EN SERVER.PY

Razón: Los endpoints de comercial (~3300 líneas) tienen lógica
de homologación multi-origen muy compleja que requiere:
- Funciones globales de APIs locales
- Tests exhaustivos antes de migrar
- Validación de la regla J de homologación

Inicialización:
    from modules.comercial import init_comercial_module
    init_comercial_module(db)
"""

from modules.comercial.routes import router
from modules.comercial.repository import init_comercial_repository
from modules.comercial.schemas import (
    VentaSucursal,
    MetaSucursal,
    TicketPerfecto,
    DashboardComercialResponse,
    TableroEjecutivoResponse,
    ReportePaxRequest,
)


def init_comercial_module(database) -> None:
    """
    Inicializa el módulo comercial con la conexión a MongoDB.
    
    Args:
        database: Instancia de AsyncIOMotorDatabase
    """
    init_comercial_repository(database)


__all__ = [
    'router',
    'init_comercial_module',
    # Schemas
    'VentaSucursal',
    'MetaSucursal',
    'TicketPerfecto',
    'DashboardComercialResponse',
    'TableroEjecutivoResponse',
    'ReportePaxRequest',
]
