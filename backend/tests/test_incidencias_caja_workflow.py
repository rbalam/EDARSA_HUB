from dataclasses import replace

from modules.finanzas.incidencias_caja_policy import MomentoAutorizacion, PermisoOrigen
from modules.finanzas.incidencias_caja_workflow import (
    EstadoVistoBueno, EstadoAutorizacion, EstadoOperacion,
    EstadoConciliacion, SituacionIncidenciaCaja, evaluar_seguimiento_v1,
)


def base():
    return SituacionIncidenciaCaja(
        visto_bueno=EstadoVistoBueno.OTORGADO,
        autorizacion=EstadoAutorizacion.APROBADA,
        operacion=EstadoOperacion.VERIFICADA_EN_ORIGEN,
        conciliacion=EstadoConciliacion.CONCILIADA,
        momento_autorizacion=MomentoAutorizacion.PREVIA,
        diferimiento_permitido=False,
        permiso_origen=PermisoOrigen.PERMITIDO,
        permiso_edarsahub=True,
        alcance_valido=True,
        autorizacion_ref="auth-1",
        visto_bueno_ref="vb-1",
    )


def test_cierre_solo_si_verificado_y_conciliado():
    d=evaluar_seguimiento_v1(base())
    assert d.puede_cerrar and d.puede_consultar
    assert not d.puede_ejecutar_en_origen


def test_autorizacion_posterior_no_es_aprobacion_ni_cierre():
    s=replace(base(), autorizacion=EstadoAutorizacion.PENDIENTE,
              autorizacion_ref=None, momento_autorizacion=MomentoAutorizacion.POSTERIOR,
              diferimiento_permitido=True)
    d=evaluar_seguimiento_v1(s)
    assert d.puede_continuar and not d.puede_cerrar
    assert d.pendiente=="AUTORIZACION_POSTERIOR_PENDIENTE"


def test_previa_pendiente_bloquea_continuidad():
    s=replace(base(), autorizacion=EstadoAutorizacion.PENDIENTE,
              autorizacion_ref=None)
    assert not evaluar_seguimiento_v1(s).puede_continuar


def test_autorizacion_rechazada_no_se_convierte_en_aprobacion():
    s=replace(base(), autorizacion=EstadoAutorizacion.RECHAZADA,
              momento_autorizacion=MomentoAutorizacion.POSTERIOR,
              diferimiento_permitido=True)
    d=evaluar_seguimiento_v1(s)
    assert not d.puede_cerrar and not d.puede_continuar


def test_no_requerida_es_estado_explicito():
    s=replace(base(), autorizacion=EstadoAutorizacion.NO_REQUERIDA,
              autorizacion_ref=None)
    assert evaluar_seguimiento_v1(s).puede_cerrar


def test_vobo_rechazado_bloquea_cierre():
    s=replace(base(), visto_bueno=EstadoVistoBueno.RECHAZADO)
    assert not evaluar_seguimiento_v1(s).puede_cerrar


def test_vobo_otorgado_sin_evidencia_bloquea():
    s=replace(base(), visto_bueno_ref=None)
    assert evaluar_seguimiento_v1(s).pendiente=="VISTO_BUENO_SIN_EVIDENCIA"


def test_autorizacion_aprobada_sin_referencia_bloquea():
    s=replace(base(), autorizacion_ref=None)
    assert evaluar_seguimiento_v1(s).pendiente=="AUTORIZACION_SIN_REFERENCIA"


def test_rls_denegado_niega_hasta_lectura():
    s=replace(base(), alcance_valido=False)
    d=evaluar_seguimiento_v1(s)
    assert not d.puede_consultar and not d.puede_cerrar


def test_origen_desconocido_no_es_inexistente():
    s=replace(base(), permiso_origen=PermisoOrigen.DESCONOCIDO)
    d=evaluar_seguimiento_v1(s)
    assert not d.puede_cerrar and not d.puede_continuar


def test_resultado_origen_no_confirmado_impide_cerrar():
    s=replace(base(), operacion=EstadoOperacion.RESULTADO_DESCONOCIDO)
    assert evaluar_seguimiento_v1(s).pendiente=="OPERACION_PENDIENTE_VERIFICACION"


def test_diferencia_no_conciliada_impide_cerrar():
    s=replace(base(), conciliacion=EstadoConciliacion.CON_DIFERENCIA)
    assert not evaluar_seguimiento_v1(s).puede_cerrar


def test_v1_nunca_ejecuta_pos_externo():
    for estado in EstadoOperacion:
        s=replace(base(), operacion=estado)
        assert not evaluar_seguimiento_v1(s).puede_ejecutar_en_origen
