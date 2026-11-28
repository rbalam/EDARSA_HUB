"""Orquestacion de preparacion de incidencias con alcance SQL canónico.

Los resolutores provienen de servicios existentes, nunca del body HTTP.
No registra nada, no conecta a POS externo y no crea fuentes de datos.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from modules.finanzas.incidencias_caja_access import validar_acceso_creacion_caja
from modules.finanzas.incidencias_caja_application import (
    DependenciasCrearCaja, preparar_expediente_v1,
)
from modules.finanzas.incidencias_caja_context import (
    AlcanceCaja, MotivoCajaCatalogo, RegistroCajaValidado,
)
from modules.finanzas.incidencias_caja_contracts import IncidenciaCajaCreate


class CatalogoCajaNoVerificable(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolutoresCajaCanonicos:
    """Adaptadores de lectura hacia RBAC/Unidades/Catálogos ya existentes."""
    relaciones_usuario: Callable[[int], Iterable[tuple[str, str, str]]]
    motivos_contextuales: Callable[[AlcanceCaja], Iterable[MotivoCajaCatalogo]]


def preparar_caja_autenticada_v1(
    *,
    usuario_autenticado: Mapping[str, Any],
    alcance_resuelto: AlcanceCaja,
    solicitud: IncidenciaCajaCreate,
    resolutores: ResolutoresCajaCanonicos,
) -> RegistroCajaValidado:
    """Primero autoriza, después lee catálogo y prepara.

    La integración HTTP futura debe obtener alcance_resuelto a partir de la
    sesión y selectores corporativos validados en servidor, no del formulario.
    """
    acceso = validar_acceso_creacion_caja(
        usuario_autenticado=usuario_autenticado,
        alcance_resuelto=alcance_resuelto,
        obtener_relaciones_canonicas=resolutores.relaciones_usuario,
    )
    try:
        motivos = tuple(resolutores.motivos_contextuales(acceso.alcance))
    except Exception:
        raise CatalogoCajaNoVerificable("CATALOGO_CANONICO_NO_VERIFICABLE") from None
    if not motivos:
        raise CatalogoCajaNoVerificable("CATALOGO_CANONICO_NO_DISPONIBLE")
    return preparar_expediente_v1(
        solicitud,
        acceso.alcance,
        DependenciasCrearCaja(
            contextos_permitidos=acceso.relaciones_permitidas,
            motivos_vigentes=motivos,
            repositorio=None,
        ),
    )
