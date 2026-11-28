"""Reglas puras de seguridad para incidencias de caja complementarias.

No consulta sistemas de origen, no concede permisos tecnicos externos y no escribe SQL.
El llamador debe resolver identidad, alcances y permisos desde servicios canonicos.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PermisoOrigen(str, Enum):
    PERMITIDO = "PERMITIDO"
    DENEGADO = "DENEGADO"
    NO_SOPORTADO = "NO_SOPORTADO"
    DESCONOCIDO = "DESCONOCIDO"


class MomentoAutorizacion(str, Enum):
    PREVIA = "PREVIA"
    POSTERIOR = "POSTERIOR"


@dataclass(frozen=True)
class DecisionOperacionCaja:
    puede_registrar: bool
    puede_continuar: bool
    puede_ejecutar_en_origen: bool
    motivo: str


def evaluar_operacion(
    *,
    permiso_edarsahub: bool,
    permiso_origen: PermisoOrigen,
    tiene_alcance_unidad: bool,
    visto_bueno: bool,
    autorizacion_concedida: bool,
    momento: MomentoAutorizacion,
    diferimiento_permitido: bool,
    ejecucion_externa_habilitada: bool = False,
) -> DecisionOperacionCaja:
    """Evalua continuidad y ejecucion por separado; nunca autoriza escritura por si sola."""
    if not permiso_edarsahub or not tiene_alcance_unidad:
        return DecisionOperacionCaja(False, False, False, "EDARSAHUB_RBAC_RLS_DENEGADO")
    # El registro interno puede permitirse aun cuando la operacion externa este bloqueada.
    if permiso_origen == PermisoOrigen.DENEGADO:
        return DecisionOperacionCaja(True, False, False, "ORIGEN_DENEGADO")
    if permiso_origen == PermisoOrigen.DESCONOCIDO:
        return DecisionOperacionCaja(True, False, False, "ORIGEN_NO_VERIFICABLE")
    if not visto_bueno:
        return DecisionOperacionCaja(True, False, False, "VISTO_BUENO_PENDIENTE")
    autorizado = autorizacion_concedida or (
        momento == MomentoAutorizacion.POSTERIOR and diferimiento_permitido
    )
    if not autorizado:
        return DecisionOperacionCaja(True, False, False, "AUTORIZACION_REQUERIDA")
    # NO_SOPORTADO habilita suplencia funcional de EDARSAHUB, no poderes externos.
    ejecutar = (
        ejecucion_externa_habilitada
        and autorizacion_concedida
        and permiso_origen == PermisoOrigen.PERMITIDO
    )
    return DecisionOperacionCaja(
        True,
        True,
        ejecutar,
        "CONTINUIDAD_POSTERIOR" if not autorizacion_concedida else "AUTORIZACION_VIGENTE",
    )


def validar_alcance_empresa_unidad(
    *,
    empresa_solicitada: str,
    unidad_solicitada: str,
    empresas_autorizadas: frozenset[str],
    unidades_autorizadas: frozenset[str],
) -> bool:
    """Alcances provenientes de servicios RBAC, nunca del formulario del cliente."""
    return bool(
        empresa_solicitada
        and unidad_solicitada
        and empresa_solicitada in empresas_autorizadas
        and unidad_solicitada in unidades_autorizadas
    )
