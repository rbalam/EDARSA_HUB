"""Modulo Comercial V2 conectado a la fuente canonica EDARSAHUB.

Expone un router agregado para conservar las rutas existentes e incorporar el
contrato dinamico de periodos sin duplicar prefijos ni fuentes de datos.
"""

from fastapi import APIRouter

from .feature_flag import get_v2_status, is_comercial_v2_enabled
from .periodos_routes import router as periodos_router
from .routes import router as comercial_router

__version__ = "0.4.0"
__status__ = "ENDPOINTS_V2_CANONICOS_CON_PERIODOS"


def get_comercial_v2_router() -> APIRouter:
    """Retorna todas las rutas Comercial V2 bajo un unico router registrable."""

    agregado = APIRouter()
    agregado.include_router(comercial_router)
    agregado.include_router(periodos_router)
    return agregado


__all__ = [
    "get_comercial_v2_router",
    "is_comercial_v2_enabled",
    "get_v2_status",
]
