"""
Adaptador de compatibilidad.

La implementacion canonica de reglas de margen pertenece al dominio
modules.costos_margenes.

No agregar logica funcional en este archivo.
"""

from modules.costos_margenes.reglas_margen_repository import (
    listar_reglas,
    obtener_regla_por_id,
    verificar_duplicado_regla,
    crear_regla,
    actualizar_regla,
    desactivar_regla,
    resolver_regla_aplicable,
    obtener_umbrales_severidad,
    determinar_severidad,
    obtener_estadisticas_reglas,
    cargar_reglas_margen_vigentes,
)

__all__ = [
    "listar_reglas",
    "obtener_regla_por_id",
    "verificar_duplicado_regla",
    "crear_regla",
    "actualizar_regla",
    "desactivar_regla",
    "resolver_regla_aplicable",
    "obtener_umbrales_severidad",
    "determinar_severidad",
    "obtener_estadisticas_reglas",
    "cargar_reglas_margen_vigentes",
]
