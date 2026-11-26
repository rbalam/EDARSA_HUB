from dataclasses import replace
import pytest

from modules.finanzas.incidencias_caja_notifications import (
    EventoCajaNotificable, SolicitudNotificacionCaja,
    NotificacionCajaNoAutorizada, preparar_intencion_whatsapp_caja,
)


def request():
    return SolicitudNotificacionCaja(
        evento=EventoCajaNotificable.AUTORIZACION_PENDIENTE,
        folio="CAJA-1", empresa_id="e", unidad_id="u", sucursal_id="s",
        destinatario_usuario_id=22, plantilla_codigo="CAJAS_AUTORIZACION",
        url_expediente="https://bos.example.com/comercial/cajas/CAJA-1",
        idempotencia_evento="CAJA-1:AUTORIZACION_PENDIENTE:1",
    )


def preparar(r=None,**kwargs):
    defaults=dict(
        origen_https_permitido="https://bos.example.com",
        evento_habilitado=True, plantilla_aprobada=True,
        destinatario_autorizado=True, persistencia_sql_certificada=True
    )
    defaults.update(kwargs)
    return preparar_intencion_whatsapp_caja(r or request(), **defaults)


def test_intencion_reutiliza_esquema_canonico_no_envia():
    value=preparar()
    assert value.canal=="whatsapp"
    assert value.modulo=="COMERCIAL_POS"
    assert value.destinatario_usuario_id==22
    assert value.modo_envio=="real"


@pytest.mark.parametrize("flag",[
    "evento_habilitado", "plantilla_aprobada",
    "destinatario_autorizado","persistencia_sql_certificada",
])
def test_denegacion_por_precondiciones(flag):
    with pytest.raises(NotificacionCajaNoAutorizada, match="NO_HABILITADO"):
        preparar(**{flag:False})


@pytest.mark.parametrize("url",[
    "http://bos.example.com/comercial/cajas/CAJA-1",
    "https://evil.example/comercial/cajas/CAJA-1",
    "https://bos.example.com@evil.example/comercial/cajas/CAJA-1",
    "https://bos.example.com/comercial/cajas/CAJA-1?token=secret",
    "https://bos.example.com/otra/ruta",
])
def test_bloquea_url_no_canonica(url):
    with pytest.raises(NotificacionCajaNoAutorizada,match="URL_EXPEDIENTE"):
        preparar(replace(request(),url_expediente=url))


def test_rechaza_falta_destinatario():
    with pytest.raises(NotificacionCajaNoAutorizada,match="INCOMPLETO"):
        preparar(replace(request(),destinatario_usuario_id=0))
