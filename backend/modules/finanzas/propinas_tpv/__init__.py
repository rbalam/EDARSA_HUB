from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
# Modulo de Control y Cuadre de Propinas TPV.
#
# El router principal de la aplicacion debe usar get_router_edarsahub().
# Los routers legacy quedan en lazy import para no cargar dependencias de
# cache/live durante el arranque normal del menu financiero.


def get_router_sql():
    """Lazy import del router SQL para evitar circular imports."""
    from .routes_sql import router_sql
    return router_sql


def get_router():
    """Lazy import del router para evitar circular imports."""
    from .routes import router
    return router


def get_router_edarsahub():
    """
    SUBFASE 3.4: Router EDARSAHUB v2 para Propinas TPV.
    Fuente de verdad: EDARSAHUB.propinas_tpv_control
    """
    from .routes_edarsahub import router
    return router


__all__ = [
    'get_router_sql',
    'get_router',
    'get_router_edarsahub',
]
