"""
CENTRO DE CONTROL EDARSA - Servicio de Notificaciones por WhatsApp
===================================================================
Envío de mensajes WhatsApp para alertas ultra-críticas usando Twilio.

Los destinatarios se obtienen de:
1. MongoDB (colección alert_recipients) - Prioridad
2. Variable de entorno ALERT_WHATSAPP_TO - Fallback

Configuración requerida en backend/.env:
- TWILIO_ACCOUNT_SID: Account SID de Twilio
- TWILIO_AUTH_TOKEN: Auth Token de Twilio
- TWILIO_WHATSAPP_FROM: Número de WhatsApp de Twilio (formato: +14155238886)

IMPORTANTE: Para usar WhatsApp con Twilio Sandbox:
1. Los destinatarios deben enviar "join <sandbox-keyword>" al número de WhatsApp
2. Para producción, se requiere WhatsApp Business API aprobado

Uso:
    from core.centro_control.whatsapp_notifications import send_critical_alert_whatsapp
    
    await send_critical_alert_whatsapp(alerta_data)
"""

import os
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

# Configuración Twilio desde .env
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', '')

# Destinatarios de alertas críticas por WhatsApp (fallback desde .env)
ALERT_WHATSAPP_TO = os.environ.get('ALERT_WHATSAPP_TO', '')

# Habilitar/deshabilitar WhatsApp
WHATSAPP_ENABLED = os.environ.get('WHATSAPP_ENABLED', 'true').lower() == 'true'

# Thread pool para envío asíncrono
_executor = ThreadPoolExecutor(max_workers=2)

# Cliente Twilio (lazy initialization)
_twilio_client = None


def _get_twilio_client() -> Client:
    """Obtiene el cliente Twilio (singleton)"""
    global _twilio_client
    if _twilio_client is None and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client


def get_whatsapp_recipients() -> List[str]:
    """
    Obtiene la lista de números WhatsApp destinatarios.
    Prioridad: MongoDB > Variable de entorno
    """
    # Intentar obtener de MongoDB primero
    try:
        from core.centro_control.recipients_manager import get_whatsapp_recipients as get_db_recipients
        db_recipients = get_db_recipients()
        if db_recipients:
            return db_recipients
    except Exception as e:
        logger.debug(f"[WHATSAPP] No se pudo obtener recipients de MongoDB: {e}")
    
    # Fallback a variable de entorno
    if not ALERT_WHATSAPP_TO:
        return []
    # Limpiar y formatear números
    recipients = []
    for num in ALERT_WHATSAPP_TO.split(','):
        num = num.strip()
        if num:
            # Asegurar formato E.164
            if not num.startswith('+'):
                num = '+' + num
            recipients.append(num)
    return recipients


def is_whatsapp_configured() -> bool:
    """Verifica si el servicio de WhatsApp está configurado"""
    return bool(
        WHATSAPP_ENABLED and
        TWILIO_ACCOUNT_SID and
        TWILIO_AUTH_TOKEN and
        TWILIO_WHATSAPP_FROM and
        get_whatsapp_recipients()
    )


def generate_alert_message(alerta: Dict[str, Any]) -> str:
    """Genera el mensaje de texto para la alerta WhatsApp"""
    
    severidad = alerta.get('severidad', 'critical').upper()
    modulo = alerta.get('modulo', 'Sistema')
    titulo = alerta.get('titulo', 'Alerta Crítica Detectada')
    detalle = alerta.get('detalle', alerta.get('mensaje', 'Sin detalles'))
    timestamp = alerta.get('timestamp', datetime.now(timezone.utc).isoformat())
    alerta_id = alerta.get('id', 'N/A')
    
    # Formatear timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        fecha_formateada = dt.strftime('%d/%m/%Y %H:%M')
    except Exception:
        fecha_formateada = timestamp[:16] if len(timestamp) > 16 else timestamp
    
    # Emoji según severidad
    emoji_map = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🔵'
    }
    emoji = emoji_map.get(severidad, '🔴')
    
    message = f"""
{emoji} *ALERTA {severidad}* {emoji}
━━━━━━━━━━━━━━━━━━━━

*{titulo}*

📦 *Módulo:* {modulo}
🕐 *Fecha:* {fecha_formateada}

📋 *Detalle:*
{detalle[:300]}{'...' if len(detalle) > 300 else ''}

━━━━━━━━━━━━━━━━━━━━
_Centro de Control EDARSA_
ID: {alerta_id}
""".strip()
    
    return message


def _send_whatsapp_sync(recipient: str, message: str) -> Dict[str, Any]:
    """
    Envía un mensaje WhatsApp de forma síncrona (para usar en thread pool).
    
    Returns:
        Dict con resultado del envío
    """
    result = {
        "success": False,
        "recipient": recipient,
        "message_sid": None,
        "error": None
    }
    
    try:
        client = _get_twilio_client()
        if not client:
            result["error"] = "Cliente Twilio no inicializado"
            return result
        
        # Formatear números para WhatsApp
        from_whatsapp = f"whatsapp:{TWILIO_WHATSAPP_FROM}"
        to_whatsapp = f"whatsapp:{recipient}"
        
        # Enviar mensaje
        message_response = client.messages.create(
            body=message,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        
        result["success"] = True
        result["message_sid"] = message_response.sid
        logger.info(f"[WHATSAPP] Mensaje enviado a {recipient}: {message_response.sid}")
        
    except TwilioRestException as e:
        result["error"] = f"Error Twilio: {e.msg}"
        logger.error(f"[WHATSAPP] Error Twilio enviando a {recipient}: {e}")
    except Exception as e:
        result["error"] = f"Error: {str(e)[:100]}"
        logger.error(f"[WHATSAPP] Error enviando a {recipient}: {e}")
    
    return result


async def send_critical_alert_whatsapp(alerta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía un mensaje WhatsApp de alerta crítica a los destinatarios configurados.
    
    Args:
        alerta: Diccionario con datos de la alerta
        
    Returns:
        Dict con resultado del envío
    """
    result = {
        "success": False,
        "message": "",
        "recipients": [],
        "enviados": 0,
        "message_sids": [],
        "errors": []
    }
    
    # Verificar si está habilitado
    if not WHATSAPP_ENABLED:
        result["message"] = "Servicio de WhatsApp deshabilitado (WHATSAPP_ENABLED=false)"
        logger.info("[WHATSAPP] Servicio de WhatsApp deshabilitado")
        return result
    
    # Verificar configuración
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        result["message"] = "Credenciales Twilio no configuradas"
        logger.warning("[WHATSAPP] Credenciales Twilio no configuradas")
        return result
    
    if not TWILIO_WHATSAPP_FROM:
        result["message"] = "Número de WhatsApp origen no configurado (TWILIO_WHATSAPP_FROM)"
        logger.warning("[WHATSAPP] Número origen no configurado")
        return result
    
    recipients = get_whatsapp_recipients()
    if not recipients:
        result["message"] = "No hay destinatarios configurados (ALERT_WHATSAPP_TO)"
        logger.warning("[WHATSAPP] No hay destinatarios configurados")
        return result
    
    result["recipients"] = recipients
    
    # Generar mensaje
    message_text = generate_alert_message(alerta)
    
    # Enviar mensajes en paralelo usando thread pool
    loop = asyncio.get_event_loop()
    tasks = []
    
    for recipient in recipients:
        task = loop.run_in_executor(
            _executor,
            _send_whatsapp_sync,
            recipient,
            message_text
        )
        tasks.append(task)
    
    # Esperar resultados
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for res in results:
        if isinstance(res, Exception):
            result["errors"].append(str(res)[:100])
        elif isinstance(res, dict):
            if res.get("success"):
                result["enviados"] += 1
                if res.get("message_sid"):
                    result["message_sids"].append(res["message_sid"])
            elif res.get("error"):
                result["errors"].append(f"{res.get('recipient')}: {res.get('error')}")
    
    if result["enviados"] > 0:
        result["success"] = True
        result["message"] = f"WhatsApp enviado a {result['enviados']}/{len(recipients)} destinatarios"
    else:
        result["message"] = "No se pudo enviar a ningún destinatario"
    
    return result


def get_whatsapp_config_status() -> Dict[str, Any]:
    """Retorna el estado de configuración del servicio de WhatsApp"""
    recipients = get_whatsapp_recipients()
    
    return {
        "configured": is_whatsapp_configured(),
        "enabled": WHATSAPP_ENABLED,
        "twilio_configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
        "from_number": TWILIO_WHATSAPP_FROM if TWILIO_WHATSAPP_FROM else None,
        "recipients_count": len(recipients),
        "recipients": [r[:5] + "***" + r[-4:] if len(r) > 9 else "***" for r in recipients],
        "sandbox_note": "Los destinatarios deben unirse al sandbox de Twilio enviando 'join <keyword>' al número de WhatsApp"
    }


async def send_test_whatsapp(recipient: str = None) -> Dict[str, Any]:
    """
    Envía un mensaje WhatsApp de prueba para verificar la configuración.
    
    Args:
        recipient: Número destino (opcional, usa el primero configurado si no se especifica)
        
    Returns:
        Dict con resultado del envío
    """
    recipients = get_whatsapp_recipients()
    
    if not recipient:
        if recipients:
            recipient = recipients[0]
        else:
            return {
                "success": False,
                "message": "No hay destinatarios configurados"
            }
    
    # Asegurar formato
    if not recipient.startswith('+'):
        recipient = '+' + recipient
    
    test_alerta = {
        "id": f"test_{datetime.now(timezone.utc).strftime('%H%M%S')}",
        "titulo": "Prueba de Notificaciones WhatsApp",
        "severidad": "medium",
        "modulo": "Centro de Control",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detalle": "Este es un mensaje de prueba para verificar que las notificaciones por WhatsApp están funcionando correctamente."
    }
    
    message_text = generate_alert_message(test_alerta)
    
    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(
            _executor,
            _send_whatsapp_sync,
            recipient,
            message_text
        )
        
        return {
            "success": res.get("success", False),
            "message": "WhatsApp de prueba enviado" if res.get("success") else res.get("error", "Error desconocido"),
            "recipient": recipient,
            "message_sid": res.get("message_sid")
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)[:200]}",
            "recipient": recipient
        }
