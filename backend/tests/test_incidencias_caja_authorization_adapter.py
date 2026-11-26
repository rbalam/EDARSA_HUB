from dataclasses import replace
import pytest

from modules.finanzas.incidencias_caja_workflow import EstadoAutorizacion
from modules.finanzas.incidencias_caja_authorization_adapter import (
    AutorizacionCajaNoVerificable, proyectar_autorizacion_caja,
)


def fila(estado="PENDIENTE"):
    return {
        "AutorizacionID":42, "EntidadNombre":"CAJAS_EXPEDIENTE",
        "EntidadID":"EXP-1", "Activo":True, "EstatusAutorizacion":estado,
    }


def proyectar(row=None):
    return proyectar_autorizacion_caja(
        fila() if row is None else row,
        entidad_nombre_esperada="CAJAS_EXPEDIENTE",
        entidad_id_esperada="EXP-1",
    )


@pytest.mark.parametrize("source,target",[
    ("PENDIENTE",EstadoAutorizacion.PENDIENTE),
    ("EN_PROCESO",EstadoAutorizacion.EN_PROCESO),
    ("AUTORIZADA",EstadoAutorizacion.APROBADA),
    ("RECHAZADA",EstadoAutorizacion.RECHAZADA),
])
def test_estados_canonicos(source,target):
    assert proyectar(fila(source)).estado == target


@pytest.mark.parametrize("campo,valor",[
    ("AutorizacionID",None),("AutorizacionID",0),("AutorizacionID",True),
    ("Activo",False),("EntidadNombre","OTRO"),("EntidadID","EXP-2"),
    ("EstatusAutorizacion","APROBADA"),
    ("EstatusAutorizacion","DESCONOCIDO"),
])
def test_falla_cerrado_si_evidencia_invalida(campo,valor):
    row=fila()
    row[campo]=valor
    with pytest.raises(AutorizacionCajaNoVerificable):
        proyectar(row)


def test_no_interpreta_ausencia_como_no_requerida():
    with pytest.raises(AutorizacionCajaNoVerificable,match="NO_DISPONIBLE"):
        proyectar_autorizacion_caja(
            None,entidad_nombre_esperada="CAJAS_EXPEDIENTE",
            entidad_id_esperada="EXP-1",
        )


def test_en_proceso_nunca_se_considera_aprobada():
    assert proyectar(fila("EN_PROCESO")).estado != EstadoAutorizacion.APROBADA
