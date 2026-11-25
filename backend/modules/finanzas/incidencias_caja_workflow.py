"""Vista de seguimiento de Cajas V1 a partir de estados canonicos.

No crea, resuelve ni reemplaza autorizaciones o tareas.
Los estados provienen del motor de autorizaciones y servicios canonicos.
No ejecuta operaciones externas ni escribe en SQL.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from modules.finanzas.incidencias_caja_policy import (
    MomentoAutorizacion, PermisoOrigen, evaluar_operacion,
)


class EstadoVistoBueno(str, Enum):
    NO_REQUERIDO = "NO_REQUERIDO"
    PENDIENTE = "PENDIENTE"
    OTORGADO = "OTORGADO"
    RECHAZADO = "RECHAZADO"
    OBSERVADO = "OBSERVADO"


class EstadoAutorizacion(str, Enum):
    NO_REQUERIDA = "NO_REQUERIDA"
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    VENCIDA = "VENCIDA"


class EstadoOperacion(str, Enum):
    NO_EJECUTADA = "NO_EJECUTADA"
    REPORTADA_EN_ORIGEN = "REPORTADA_EN_ORIGEN"
    VERIFICADA_EN_ORIGEN = "VERIFICADA_EN_ORIGEN"
    RESULTADO_DESCONOCIDO = "RESULTADO_DESCONOCIDO"
    FALLIDA = "FALLIDA"
    NO_APLICA = "NO_APLICA"


class EstadoConciliacion(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    CONCILIADA = "CONCILIADA"
    CON_DIFERENCIA = "CON_DIFERENCIA"
    NO_APLICA = "NO_APLICA"


@dataclass(frozen=True)
class SituacionIncidenciaCaja:
    """Estados provenientes de repositorios/servicios autorizados."""
    visto_bueno: EstadoVistoBueno
    autorizacion: EstadoAutorizacion
    operacion: EstadoOperacion
    conciliacion: EstadoConciliacion
    momento_autorizacion: MomentoAutorizacion
    diferimiento_permitido: bool
    permiso_origen: PermisoOrigen
    permiso_edarsahub: bool
    alcance_valido: bool
    autorizacion_ref: str | None = None
    visto_bueno_ref: str | None = None


@dataclass(frozen=True)
class SeguimientoIncidenciaCaja:
    puede_consultar: bool
    puede_continuar: bool
    puede_cerrar: bool
    puede_ejecutar_en_origen: bool
    pendiente: str | None
    estado_general: str


def evaluar_seguimiento_v1(s: SituacionIncidenciaCaja) -> SeguimientoIncidenciaCaja:
    """Calcula seguimiento sin alterar el motor canonico ni el POS.

    Autorizaciones posteriores pendientes no se marcan como aprobadas.
    El cierre exige un estado operativo verificable y conciliacion resuelta.
    """
    if not s.permiso_edarsahub or not s.alcance_valido:
        return SeguimientoIncidenciaCaja(False, False, False, False,
                                        "RBAC_RLS_DENEGADO", "ACCESO_DENEGADO")

    if s.visto_bueno in (EstadoVistoBueno.PENDIENTE, EstadoVistoBueno.OBSERVADO):
        return SeguimientoIncidenciaCaja(True, False, False, False,
                                        "VISTO_BUENO_PENDIENTE", "EN_GESTION")
    if s.visto_bueno == EstadoVistoBueno.RECHAZADO:
        return SeguimientoIncidenciaCaja(True, False, False, False,
                                        "VISTO_BUENO_RECHAZADO", "OBSERVADA")
    if s.visto_bueno == EstadoVistoBueno.OTORGADO and not s.visto_bueno_ref:
        return SeguimientoIncidenciaCaja(True, False, False, False,
                                        "VISTO_BUENO_SIN_EVIDENCIA", "EN_GESTION")

    if s.autorizacion in (EstadoAutorizacion.RECHAZADA, EstadoAutorizacion.VENCIDA):
        return SeguimientoIncidenciaCaja(True, False, False, False,
                                        "AUTORIZACION_NO_VIGENTE", "OBSERVADA")
    if s.autorizacion == EstadoAutorizacion.APROBADA and not s.autorizacion_ref:
        return SeguimientoIncidenciaCaja(True, False, False, False,
                                        "AUTORIZACION_SIN_REFERENCIA", "EN_GESTION")

    autorizacion_ok = s.autorizacion in (
        EstadoAutorizacion.APROBADA, EstadoAutorizacion.NO_REQUERIDA
    )
    vb_ok = s.visto_bueno in (
        EstadoVistoBueno.OTORGADO, EstadoVistoBueno.NO_REQUERIDO
    )
    decision = evaluar_operacion(
        permiso_edarsahub=s.permiso_edarsahub,
        permiso_origen=s.permiso_origen,
        tiene_alcance_unidad=s.alcance_valido,
        visto_bueno=vb_ok,
        autorizacion_concedida=autorizacion_ok,
        momento=s.momento_autorizacion,
        diferimiento_permitido=s.diferimiento_permitido
          and s.autorizacion in (EstadoAutorizacion.PENDIENTE, EstadoAutorizacion.EN_PROCESO),
        ejecucion_externa_habilitada=False,
    )
    # El cierre NO esta autorizado con pendiente posterior aun si hay continuidad.
    if not autorizacion_ok:
        return SeguimientoIncidenciaCaja(True, decision.puede_continuar,
                                        False, False,
                                        "AUTORIZACION_POSTERIOR_PENDIENTE"
                                        if decision.puede_continuar else "AUTORIZACION_PENDIENTE",
                                        "EN_GESTION")

    if not decision.puede_continuar:
        return SeguimientoIncidenciaCaja(True, False, False, False,
                                        decision.motivo, "OBSERVADA")

    if s.operacion in (
        EstadoOperacion.NO_EJECUTADA, EstadoOperacion.REPORTADA_EN_ORIGEN,
        EstadoOperacion.RESULTADO_DESCONOCIDO,
    ):
        return SeguimientoIncidenciaCaja(True, True, False, False,
                                        "OPERACION_PENDIENTE_VERIFICACION", "EN_GESTION")
    if s.operacion == EstadoOperacion.FALLIDA:
        return SeguimientoIncidenciaCaja(True, True, False, False,
                                        "OPERACION_FALLIDA", "OBSERVADA")
    if s.conciliacion in (
        EstadoConciliacion.PENDIENTE, EstadoConciliacion.EN_REVISION
    ):
        return SeguimientoIncidenciaCaja(True, True, False, False,
                                        "CONCILIACION_PENDIENTE", "EN_GESTION")
    if s.conciliacion == EstadoConciliacion.CON_DIFERENCIA:
        return SeguimientoIncidenciaCaja(True, True, False, False,
                                        "DIFERENCIA_PENDIENTE_RESOLUCION", "OBSERVADA")
    return SeguimientoIncidenciaCaja(True, True, True, False, None, "LISTA_PARA_CIERRE")
