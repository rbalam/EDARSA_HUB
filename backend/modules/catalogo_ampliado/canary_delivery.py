from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from core.communications.dispatcher.dispatcher import NotificationDispatcher
from modules.scheduler_runtime.policy import runtime_environment

MODULE = "catalogo_ampliado"
EVENT_CODE = "DOCUMENTO_VENCIMIENTO"
TEMPLATE_CODE = "catalogo_ampliado_documento_vencimiento"
ALLOWED_ENVIRONMENTS = {"DEVELOPMENT", "PREVIEW"}


def _queue_id(canary_key: str, channel: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"edarsahub:{MODULE}:gate8h-b:{canary_key}:{channel}"))


def _validate_email(value: str) -> str:
    email = str(value or "").strip()
    if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("CANARY_EMAIL_INVALID")
    return email


def _validate_whatsapp(value: str) -> str:
    phone = str(value or "").strip().replace(" ", "")
    if not phone.startswith("+") or not phone[1:].isdigit() or len(phone) < 10:
        raise ValueError("CANARY_WHATSAPP_INVALID")
    return phone


async def run_notification_canary(*, email: str, whatsapp: str, canary_key: str) -> dict:
    environment = runtime_environment()
    if environment not in ALLOWED_ENVIRONMENTS:
        raise RuntimeError(f"CATALOGO_CANARY_ENVIRONMENT_FORBIDDEN:{environment}")

    email = _validate_email(email)
    whatsapp = _validate_whatsapp(whatsapp)
    key = str(canary_key or "").strip()
    if not key or len(key) > 120:
        raise ValueError("CANARY_KEY_INVALID")

    dispatcher = NotificationDispatcher(None)
    await dispatcher.initialize_providers()

    providers = {
        "email": ("smtp", email),
        "whatsapp": ("twilio", whatsapp),
    }
    for channel, (provider_name, _recipient) in providers.items():
        provider = dispatcher.get_provider(provider_name)
        if provider is None:
            raise RuntimeError(f"CANARY_PROVIDER_UNAVAILABLE:{channel}:{provider_name}")
        if hasattr(provider, "is_available") and not provider.is_available():
            raise RuntimeError(f"CANARY_PROVIDER_NOT_READY:{channel}:{provider_name}")

    payload = {
        "titulo": "CANARY Gate 8H-B Catalogo Ampliado",
        "fecha_objetivo": "2099-12-31",
    }
    results = {}

    for channel, (provider_name, recipient) in providers.items():
        reference_id = f"CANARY:{key}:{channel}"
        duplicate = await dispatcher.repository.check_duplicate(
            destinatario=recipient,
            evento=EVENT_CODE,
            dedup_key=reference_id,
            ventana_minutos=1440,
        )
        if duplicate:
            results[channel] = {
                "status": "DUPLICATE_BLOCKED",
                "provider": provider_name,
                "queue_id": _queue_id(key, channel),
            }
            continue

        queue_id = _queue_id(key, channel)
        destination = {"user_id": "gate8h-b-canary", "tipo": "canary"}
        destination["email" if channel == "email" else "telefono"] = recipient
        item = {
            "id": queue_id,
            "canal": channel,
            "modulo": MODULE,
            "evento_negocio": EVENT_CODE,
            "referencia_id": reference_id,
            "workflow_id": key,
            "prioridad": 1,
            "destinatarios": [destination],
            "template_codigo": TEMPLATE_CODE,
            "payload": payload,
            "estado": "pendiente",
            "intentos": 0,
        }

        await dispatcher.repository.enqueue(item)
        locked = await dispatcher.repository.lock_item(queue_id, dispatcher._worker_id)
        if not locked:
            raise RuntimeError(f"CANARY_QUEUE_LOCK_FAILED:{channel}")

        outcome = await dispatcher._process_item(item)
        if outcome.get("all_sent"):
            await dispatcher.repository.mark_sent(queue_id)
            status = "SENT"
        else:
            error_code = str(outcome.get("error_code") or "CANARY_SEND_FAILED")
            await dispatcher.repository.mark_failed(queue_id, error_code)
            status = "FAILED"

        results[channel] = {
            "status": status,
            "provider": provider_name,
            "queue_id": queue_id,
            "duplicates": int(outcome.get("duplicates") or 0),
            "error_code": outcome.get("error_code"),
        }

    return {
        "environment": environment,
        "module": MODULE,
        "event": EVENT_CODE,
        "template": TEMPLATE_CODE,
        "canary_key": key,
        "results": results,
        "production_touched": False,
    }
