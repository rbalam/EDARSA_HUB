"""Contrato Cajas V1 para canal de comunicaciones corporativo.

No envia mensajes, no guarda colas y no cambia el dispatcher.
La capa de Comunicaciones debe verificar plantilla aprobada, destinatario,
consentimiento y persistencia SQL antes de admitir una entrega real.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlencode, urlsplit

from core.communications.notifications.schemas import ChannelType, SendMode


class EventoCajaNotificable(str, Enum):
    VISTO_BUENO_PENDIENTE = "CAJAS_VISTO_BUENO_PENDIENTE"
    AUTORIZACION_PENDIENTE = "CAJAS_AUTORIZACION_PENDIENTE"
    AUTORIZACION_RECHAZADA = "CAJAS_AUTORIZACION_RECHAZADA"
    SLA_VENCIDO = "CAJAS_SLA_VENCIDO"
    EXPEDIENTE_CERRADO = "CAJAS_EXPEDIENTE_CERRADO"


class NotificacionCajaNoAutorizada(ValueError):
    pass


@dataclass(frozen=True)
class SolicitudNotificacionCaja:
    evento: EventoCajaNotificable
    folio: str
    empresa_id: str
    unidad_id: str
    sucursal_id: str
    destinatario_usuario_id: int
    plantilla_codigo: str
    url_expediente: str
    idempotencia_evento: str


@dataclass(frozen=True)
class IntencionComunicacion:
    modulo: str
    canal: str
    modo_envio: str
    evento: str
    plantilla_codigo: str
    destinatario_usuario_id: int
    folio: str
    url_expediente: str
    idempotencia_evento: str


def preparar_intencion_whatsapp_caja(
    solicitud: SolicitudNotificacionCaja,
    *,
    origen_https_permitido: str,
    evento_habilitado: bool,
    plantilla_aprobada: bool,
    destinatario_autorizado: bool,
    persistencia_sql_certificada: bool,
) -> IntencionComunicacion:
    """Valida una intencion, pero NUNCA despacha WhatsApp.

    No acepta URLs externas y no incluye tokens en enlaces.
    El origen HTTPS debe coincidir exactamente con el configurado por el sistema.
    """
    if not all((
        evento_habilitado, plantilla_aprobada, destinatario_autorizado,
        persistencia_sql_certificada,
    )):
        raise NotificacionCajaNoAutorizada("CANAL_CAJA_NO_HABILITADO")
    if not all((
        solicitud.folio.strip(), solicitud.empresa_id.strip(),
        solicitud.unidad_id.strip(), solicitud.sucursal_id.strip(),
        solicitud.plantilla_codigo.strip(), solicitud.idempotencia_evento.strip(),
        solicitud.destinatario_usuario_id > 0,
    )):
        raise NotificacionCajaNoAutorizada("CONTEXTO_NOTIFICACION_INCOMPLETO")
    expected=urlsplit(origen_https_permitido)
    target=urlsplit(solicitud.url_expediente)
    if (
        expected.scheme != "https" or not expected.netloc
        or expected.username or expected.password
        or expected.path not in ("", "/") or expected.query or expected.fragment
        or target.scheme != "https" or target.netloc != expected.netloc
        or target.username or target.password
        or not target.path.startswith("/comercial/cajas/")
        or target.query or target.fragment
    ):
        raise NotificacionCajaNoAutorizada("URL_EXPEDIENTE_NO_AUTORIZADA")
    return IntencionComunicacion(
        modulo="COMERCIAL_POS",
        canal=ChannelType.WHATSAPP.value,
        modo_envio=SendMode.REAL.value,
        evento=solicitud.evento.value,
        plantilla_codigo=solicitud.plantilla_codigo,
        destinatario_usuario_id=solicitud.destinatario_usuario_id,
        folio=solicitud.folio,
        url_expediente=solicitud.url_expediente,
        idempotencia_evento=solicitud.idempotencia_evento,
    )
