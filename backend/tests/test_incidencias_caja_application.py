from dataclasses import replace
import pytest

from modules.finanzas.incidencias_caja_application import (
    DependenciasCrearCaja, PersistenciaCajaNoDisponible,
    preparar_expediente_v1, registrar_expediente_v1,
)
from modules.finanzas.incidencias_caja_context import AlcanceCaja, MotivoCajaCatalogo
from modules.finanzas.incidencias_caja_contracts import IncidenciaCajaCreate


def fixtures():
    alcance=AlcanceCaja("empresa1","unidad1","sucursal1",7,"POS","servidor1")
    solicitud=IncidenciaCajaCreate(
        tipo="CANCELACION",motivo_codigo="CAPTURA",descripcion="Cargo duplicado",
        solicitud_idempotencia="solicitud-123"
    )
    deps=DependenciasCrearCaja(
        contextos_permitidos=frozenset({("empresa1","unidad1","sucursal1")}),
        motivos_vigentes=(MotivoCajaCatalogo(
            codigo_canonico="CAPTURA",codigo_origen="01",
            sistema_origen="POS",empresa_id="empresa1",
            unidad_id="unidad1",sucursal_id="sucursal1"),)
    )
    return alcance,solicitud,deps


def test_preparar_expediente_no_persiste():
    ctx,sol,deps=fixtures()
    result=preparar_expediente_v1(sol,ctx,deps)
    assert result.motivo_codigo_origen=="01"
    assert len(result.idempotencia_ambito)==64


def test_no_simula_exito_si_sql_falta():
    ctx,sol,deps=fixtures()
    with pytest.raises(PersistenciaCajaNoDisponible,match="NOT_CERTIFIED"):
        registrar_expediente_v1(sol,ctx,deps)


def test_no_acepta_repositorio_que_devuelve_folio_vacio():
    ctx,sol,deps=fixtures()
    class SinConfirmacion:
        def crear_si_no_existe(self,registro):
            return ""
    with pytest.raises(PersistenciaCajaNoDisponible,match="NOT_CONFIRMED"):
        registrar_expediente_v1(sol,ctx,replace(deps,repositorio=SinConfirmacion()))


def test_delega_clave_al_repositorio_transaccional_sin_generar_folio_local():
    ctx,sol,deps=fixtures()
    class RepositorioPrueba:
        def __init__(self):
            self.registro=None
        def crear_si_no_existe(self,registro):
            self.registro=registro
            return "CAJA-0001"
    repo=RepositorioPrueba()
    assert registrar_expediente_v1(sol,ctx,replace(deps,repositorio=repo))=="CAJA-0001"
    assert repo.registro.alcance.usuario_id==7


def test_no_llama_repositorio_si_rls_rechaza():
    ctx,sol,deps=fixtures()
    class Nunca:
        def crear_si_no_existe(self,registro):
            raise AssertionError("Nunca debe escribir")
    deps=replace(deps,repositorio=Nunca())
    with pytest.raises(ValueError,match="NO_AUTORIZADA"):
        registrar_expediente_v1(sol,replace(ctx,sucursal_id="sucursal_ajena"),deps)
