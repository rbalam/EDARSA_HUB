import pytest

from modules.finanzas.incidencias_caja_contracts import IncidenciaCajaCreate
from modules.finanzas.incidencias_caja_context import (
    AlcanceCaja, CajasContextError, MotivoCajaCatalogo, preparar_registro_caja
)


def _context(**kw):
    fields=dict(empresa_id="e1", unidad_id="u1", sucursal_id="s1",
                usuario_id=42, sistema_origen="POS", server_id="srv1")
    fields.update(kw)
    return AlcanceCaja(**fields)


def _solicitud(**kw):
    fields=dict(tipo="CANCELACION", motivo_codigo="ERROR_CAPTURA",
                descripcion="Incidencia de prueba", solicitud_idempotencia="request-123")
    fields.update(kw)
    return IncidenciaCajaCreate(**fields)


def _motivo(**kw):
    fields=dict(codigo_canonico="ERROR_CAPTURA", codigo_origen="C01",
                sistema_origen="POS", empresa_id="e1", unidad_id="u1",
                sucursal_id=None, activo=True)
    fields.update(kw)
    return MotivoCajaCatalogo(**fields)


def _preparar(**kw):
    fields=dict(solicitud=_solicitud(), alcance=_context(),
                contextos_permitidos=[("e1", "u1", "s1")],
                motivos_vigentes=[_motivo()])
    fields.update(kw)
    return preparar_registro_caja(**fields)


def test_registro_validado_preserva_equivalencia_y_solicitud():
    result=_preparar()
    assert result.motivo_codigo_canonico=="ERROR_CAPTURA"
    assert result.motivo_codigo_origen=="C01"
    assert result.solicitud.tipo.value=="CANCELACION"
    assert len(result.idempotencia_ambito)==64


def test_sucursal_ajena_se_rechaza_aunque_empresa_y_unidad_coincidan():
    with pytest.raises(CajasContextError, match="NO_AUTORIZADA"):
        _preparar(alcance=_context(sucursal_id="s2"))


def test_motivo_de_otro_origen_no_se_puede_utilizar():
    with pytest.raises(CajasContextError, match="MOTIVO_NO_DISPONIBLE"):
        _preparar(motivos_vigentes=[_motivo(sistema_origen="OTRO_POS")])


def test_motivo_inactivo_rechazado():
    with pytest.raises(CajasContextError, match="MOTIVO_NO_DISPONIBLE"):
        _preparar(motivos_vigentes=[_motivo(activo=False)])


def test_duplicidad_equivalencia_ambigua_bloquea():
    with pytest.raises(CajasContextError, match="AMBIGUA"):
        _preparar(motivos_vigentes=[_motivo(codigo_origen="C01"), _motivo(codigo_origen="C99")])


def test_catalogo_especifico_prevalece_sobre_global():
    result=_preparar(motivos_vigentes=[
        _motivo(empresa_id=None, unidad_id=None, sistema_origen=None, codigo_origen=None),
        _motivo(codigo_origen="C01")])
    assert result.motivo_codigo_origen=="C01"


def test_idempotencia_estable_y_aislada_por_usuario_y_contexto():
    a=_preparar().idempotencia_ambito
    assert a==_preparar().idempotencia_ambito
    assert a!=_preparar(alcance=_context(usuario_id=43)).idempotencia_ambito
    assert a!=_preparar(solicitud=_solicitud(solicitud_idempotencia="request-456")).idempotencia_ambito


def test_identidad_invalida_rechazada():
    with pytest.raises(CajasContextError, match="INCOMPLETO"):
        _preparar(alcance=_context(usuario_id=0))
