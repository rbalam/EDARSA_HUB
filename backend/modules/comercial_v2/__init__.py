"""Modulo Comercial V2 conectado a la fuente canonica EDARSAHUB.

Expone un router agregado para conservar las rutas existentes e incorporar el
contrato dinamico de periodos sin duplicar prefijos ni fuentes de datos.

Los routers se importan de forma diferida dentro de ``get_comercial_v2_router``.
Esto evita que importar funciones puras del paquete durante pruebas unitarias
active configuracion SQL, seguridad o conexiones antes de tiempo.
"""

from fastapi import APIRouter

from .feature_flag import get_v2_status, is_comercial_v2_enabled

__version__ = "0.4.1"
__status__ = "ENDPOINTS_V2_CANONICOS_CON_PERIODOS"


def get_comercial_v2_router() -> APIRouter:
    """Retorna todas las rutas Comercial V2 bajo un unico router registrable.

    Los imports diferidos son intencionales: en runtime el servidor ya cargo la
    configuracion requerida; en pruebas de reglas puras no se deben exigir
    secretos ni una conexion SQL.
    """

    from .periodos_routes import router as periodos_router
    from .routes import router as comercial_router

    agregado = APIRouter()
    agregado.include_router(comercial_router)
    agregado.include_router(periodos_router)

    from modules.comercial_analytics import router as analytics_router
    agregado.include_router(analytics_router)
    return agregado


__all__ = [
    "get_comercial_v2_router",
    "is_comercial_v2_enabled",
    "get_v2_status",
]
