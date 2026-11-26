from dataclasses import replace
from unittest.mock import patch

import pytest
from modules.finanzas.incidencias_caja_access import (
    CAJAS_INCIDENCIAS_CREAR, AccesoCajaDenegado,
    validar_acceso_creacion_caja,
)
from modules.finanzas.incidencias_caja_context import AlcanceCaja


def scope():
    return AlcanceCaja("empresa", "unidad", "sucursal", 17, "POS", "srv")


def verificar(permissions=None, uid=17, ctx=None, resolver=None):
    usuario={"_sql_usuario_id":uid}
    ctx=scope() if ctx is None else ctx
    resolver=resolver or (lambda x: [("empresa","unidad","sucursal")])
    with patch(
        "modules.finanzas.incidencias_caja_access.RBACSQLService.get_permission_scope_by_code",
        return_value=permissions,
    ) as rb:
        result=validar_acceso_creacion_caja(
            usuario_autenticado=usuario,alcance_resuelto=ctx,
            obtener_relaciones_canonicas=resolver,
        )
        rb.assert_called_once_with(17,CAJAS_INCIDENCIAS_CREAR)
        return result


def test_permite_solo_scope_sql_y_relacion_canonica():
    r=verificar({"permitido":True})
    assert r.alcance.sucursal_id=="sucursal"
    assert r.relaciones_permitidas==frozenset({("empresa","unidad","sucursal")})


def test_no_autorizado_por_defecto():
    for permiso in (None, {}, {"permitido":False}, {"permitido":"true"}):
        with pytest.raises(AccesoCajaDenegado):
            verificar(permiso)


def test_no_confunde_usuario_o_id_invalido():
    for uid,ctx in [(99,scope()),(True,scope()),(None,scope()),(17,replace(scope(),usuario_id=18))]:
        with pytest.raises(AccesoCajaDenegado):
            verificar({"permitido":True},uid=uid,ctx=ctx)


def test_no_acepta_sucursal_ajena():
    with pytest.raises(AccesoCajaDenegado,match="ALCANCE"):
        verificar({"permitido":True},ctx=replace(scope(),sucursal_id="otra"))


def test_no_convierte_error_canonico_en_acceso_global():
    def resolver(_):
        raise RuntimeError("SQL indisponible")
    with pytest.raises(AccesoCajaDenegado,match="NO_VERIFICABLES"):
        verificar({"permitido":True},resolver=resolver)


def test_error_rbac_sql_denegado():
    with patch(
        "modules.finanzas.incidencias_caja_access.RBACSQLService.get_permission_scope_by_code",
        side_effect=RuntimeError("conexion"),
    ):
        with pytest.raises(AccesoCajaDenegado,match="NO_VERIFICABLE"):
            validar_acceso_creacion_caja(
                usuario_autenticado={"_sql_usuario_id":17},
                alcance_resuelto=scope(),
                obtener_relaciones_canonicas=lambda _: [("empresa","unidad","sucursal")],
            )
