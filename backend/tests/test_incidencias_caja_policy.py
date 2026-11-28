from modules.finanzas.incidencias_caja_policy import (
    MomentoAutorizacion, PermisoOrigen, evaluar_operacion,
    validar_alcance_empresa_unidad,
)


def _evaluar(**kw):
    data = dict(
        permiso_edarsahub=True,
        permiso_origen=PermisoOrigen.PERMITIDO,
        tiene_alcance_unidad=True,
        visto_bueno=True,
        autorizacion_concedida=False,
        momento=MomentoAutorizacion.POSTERIOR,
        diferimiento_permitido=True,
        ejecucion_externa_habilitada=True,
    )
    data.update(kw)
    return evaluar_operacion(**data)


def test_operacion_posterior_permite_continuidad_sin_ejecutar_origen():
    d = _evaluar()
    assert d.puede_registrar and d.puede_continuar
    assert not d.puede_ejecutar_en_origen
    assert d.motivo == "CONTINUIDAD_POSTERIOR"


def test_autorizacion_previa_obligatoria_bloquea_continuidad():
    d = _evaluar(momento=MomentoAutorizacion.PREVIA)
    assert d.puede_registrar and not d.puede_continuar


def test_origen_denegado_no_se_suple():
    d = _evaluar(permiso_origen=PermisoOrigen.DENEGADO, autorizacion_concedida=True)
    assert d.puede_registrar and not d.puede_continuar
    assert not d.puede_ejecutar_en_origen


def test_origen_desconocido_no_se_suple():
    d = _evaluar(permiso_origen=PermisoOrigen.DESCONOCIDO)
    assert d.puede_registrar and not d.puede_continuar


def test_permiso_inexistente_usa_suplencia_sin_escritura_externa():
    d = _evaluar(permiso_origen=PermisoOrigen.NO_SOPORTADO, autorizacion_concedida=True)
    assert d.puede_registrar and d.puede_continuar
    assert not d.puede_ejecutar_en_origen


def test_permiso_edarsahub_y_rls_son_obligatorios():
    for kw in ({"permiso_edarsahub": False}, {"tiene_alcance_unidad": False}):
        d = _evaluar(**kw)
        assert not d.puede_registrar and not d.puede_continuar


def test_visto_bueno_antecede_autorizacion():
    d = _evaluar(visto_bueno=False, autorizacion_concedida=True)
    assert not d.puede_continuar


def test_ejecucion_origen_solo_autorizada_en_v2():
    d = _evaluar(autorizacion_concedida=True, ejecucion_externa_habilitada=False)
    assert d.puede_continuar and not d.puede_ejecutar_en_origen
    d = _evaluar(autorizacion_concedida=True)
    assert d.puede_ejecutar_en_origen


def test_rls_rechaza_unidad_ajena():
    assert not validar_alcance_empresa_unidad(
        empresa_solicitada="e1", unidad_solicitada="u2",
        empresas_autorizadas=frozenset({"e1"}),
        unidades_autorizadas=frozenset({"u1"}),
    )
