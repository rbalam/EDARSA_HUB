from dataclasses import replace
from unittest.mock import patch
import pytest

from modules.finanzas.incidencias_caja_access import AccesoCajaDenegado
from modules.finanzas.incidencias_caja_context import AlcanceCaja, MotivoCajaCatalogo, CajasContextError
from modules.finanzas.incidencias_caja_contracts import IncidenciaCajaCreate
from modules.finanzas.incidencias_caja_orchestration import (
    CatalogoCajaNoVerificable, ResolutoresCajaCanonicos, preparar_caja_autenticada_v1,
)


def datos():
    alcance=AlcanceCaja("e1","u1","s1",21,"POS","servidor")
    solicitud=IncidenciaCajaCreate(tipo="CANCELACION",motivo_codigo="CAPTURA",
                                   descripcion="Error al cerrar la cuenta",
                                   solicitud_idempotencia="incidencia-123")
    motivo=MotivoCajaCatalogo("CAPTURA","OR01","POS","e1","u1","s1")
    return alcance,solicitud,motivo


def ejecutar(alcance=None, permiso=True, relaciones=None, motivos=None):
    ctx,sol,motivo=datos()
    ctx=alcance or ctx
    relaciones=relaciones or (lambda usuario: [("e1","u1","s1")])
    motivos=motivos or (lambda scope: [motivo])
    resolver=ResolutoresCajaCanonicos(relaciones, motivos)
    with patch(
        "modules.finanzas.incidencias_caja_access.RBACSQLService.get_permission_scope_by_code",
        return_value={"permitido":permiso},
    ) as rbac:
        result=preparar_caja_autenticada_v1(
            usuario_autenticado={"_sql_usuario_id":21},
            alcance_resuelto=ctx,
            solicitud=sol,
            resolutores=resolver,
        )
        rbac.assert_called_once()
        return result


def test_orquestacion_prepara_sin_guardar():
    result=ejecutar()
    assert result.motivo_codigo_origen=="OR01"
    assert len(result.idempotencia_ambito)==64


def test_rbac_denegado_no_consulta_catalogos():
    n=[]
    def catalogo(_):
        n.append("consultado")
        return []
    with pytest.raises(AccesoCajaDenegado):
        ejecutar(permiso=False,motivos=catalogo)
    assert n==[]


def test_rango_sucursal_no_autorizado():
    ctx,_,_=datos()
    with pytest.raises(AccesoCajaDenegado):
        ejecutar(alcance=replace(ctx,sucursal_id="otra"))


def test_catalogo_error_falla_cerrado():
    def catalogo(_):
        raise ConnectionError("SQL")
    with pytest.raises(CatalogoCajaNoVerificable,match="NO_VERIFICABLE"):
        ejecutar(motivos=catalogo)


def test_catalogo_vacio_falla_cerrado():
    with pytest.raises(CatalogoCajaNoVerificable,match="NO_DISPONIBLE"):
        ejecutar(motivos=lambda _: [])


def test_catalogo_de_empresa_ajena_rechazado():
    _,_,motivo=datos()
    with pytest.raises(CajasContextError,match="MOTIVO_NO_DISPONIBLE"):
        ejecutar(motivos=lambda _: [replace(motivo,empresa_id="otra")])
