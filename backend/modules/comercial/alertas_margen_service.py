"""
Adaptador de compatibilidad del antiguo dominio Comercial.

La implementacion canonica de reglas y resolucion de margen pertenece a:

    modules.costos_margenes.reglas_margen_service

Este archivo NO contiene logica funcional.

Puede eliminarse cuando no queden consumidores del path legacy.
"""

from modules.costos_margenes.reglas_margen_service import (
    AlertasMargenError,
    actualizar_regla_margen,
    crear_regla_margen,
    desactivar_regla_margen,
    evaluar_margen_producto,
    listar_reglas_margen,
    obtener_estadisticas,
    obtener_regla,
    obtener_umbrales,
    resolver_margen_esperado,
    resolver_margenes_esperados_batch,
)

__all__ = [
    "AlertasMargenError",
    "actualizar_regla_margen",
    "crear_regla_margen",
    "desactivar_regla_margen",
    "evaluar_margen_producto",
    "listar_reglas_margen",
    "obtener_estadisticas",
    "obtener_regla",
    "obtener_umbrales",
    "resolver_margen_esperado",
    "resolver_margenes_esperados_batch",
]
