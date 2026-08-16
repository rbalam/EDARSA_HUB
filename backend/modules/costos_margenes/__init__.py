"""
EDARSA HUB - Dominio Costos y Margenes.

El paquete no importa routes durante su inicializacion.

Esto permite que repositories y services del propio dominio puedan
importarse sin provocar ciclos por efectos secundarios del package import.

Compatibilidad:
    from modules.costos_margenes import router

continua soportado mediante __getattr__.
"""

__all__ = ["router"]


def __getattr__(name):
    if name == "router":
        from modules.costos_margenes.routes import router

        return router

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
