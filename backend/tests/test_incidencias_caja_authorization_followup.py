from dataclasses import replace

import pytest

from modules.finanzas.incidencias_caja_authorization_adapter import AutorizacionCajaNoVerificable
from modules.finanzas.incidencias_caja_authorization_followup import evaluar_seguimiento_con_autorizacion_sql
from modules.finanzas.incidencias_caja_policy import MomentoAutorizacion, PermisoOrigen
from modules.finanzas.incidencias_caja_workflow import (
    EstadoVistoBueno, EstadoAutorizacion, EstadoOperacion,
    EstadoConciliacion, SituacionIncidenciaCaja,
)


def expediente():
    return SituacionIncidenciaCaja(
        visto_bueno=EstadoVistoBueno.OTORGADO,
        autorizacion=EstadoAutorizacion.PENDIENTE,
        operacion=EstadoOperacion.VERIFICADA_EN_ORIGEN,
        conciliacion=EstadoConciliacion.CONCILIADA,
        momento_autorizacion=MomentoAutorizacion.PREVIA,
        diferimiento_permitido=False,
        permiso_origen=PermisoOrigen.PERMITIDO,
        permiso_edarsahub=True, alcance_valido=True,
        visto_bueno_ref="VB-1",
    )


def row(estado):
    return {
        "AutorizacionID": 91, "EntidadNombre": "CAJAS_EXPEDIENTE",
        "EntidadID": "EXP-123", "Activo": 1, "EstatusAutorizacion": estado,
    }


def evaluar(s=None,fila=None):
    return evaluar_seguimiento_con_autorizacion_sql(
        expediente=s or expediente(), fila_autorizacion=fila,
        entidad_nombre="CAJAS_EXPEDIENTE", entidad_id="EXP-123",
    )


def test_autorizada_canonica_permite_cierre_si_todo_resuelto():
    v=evaluar(fila=row("AUTORIZADA"))
    assert v.puede_cerrar and v.puede_continuar
    assert not v.puede_ejecutar_en_origen


def test_pendiente_no_cierra():
    assert not evaluar(fila=row("PENDIENTE")).puede_cerrar


def test_en_proceso_no_cierra():
    assert not evaluar(fila=row("EN_PROCESO")).puede_cerrar


def test_rechazada_no_cierra_ni_continua():
    v=evaluar(fila=row("RECHAZADA"))
    assert not v.puede_cerrar and not v.puede_continuar


def test_fila_ajena_no_autoriza():
    r=row("AUTORIZADA")
    r["EntidadID"]="OTRA"
    with pytest.raises(AutorizacionCajaNoVerificable):
        evaluar(fila=r)


def test_sin_fila_no_infiere_no_requerida():
    with pytest.raises(AutorizacionCajaNoVerificable):
        evaluar(fila=None)


def test_cliente_no_puede_forzar_aprobada():
    s=replace(expediente(),autorizacion=EstadoAutorizacion.APROBADA,autorizacion_ref="FALSO")
    assert not evaluar(s=s,fila=row("PENDIENTE")).puede_cerrar


def test_rls_falla_antes_de_proyectar_autorizacion():
    s=replace(expediente(),alcance_valido=False)
    v=evaluar(s=s,fila=None)
    assert not v.puede_consultar and not v.puede_cerrar
