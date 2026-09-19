"""Planner/dispatcher controlado de alertas de Gobierno Corporativo.

Gate 8C: no realiza entregas externas. Solo materializa TAREA en el motor
canonico dbo.Sistema_Tareas; EMAIL/WHATSAPP/APP permanecen fail-closed hasta
que un gate posterior autorice la capa canonica de entrega externa.
"""

from . import repository as repo
from .external_delivery import dispatch_external_alert

EXTERNAL_CHANNELS = {"EMAIL", "WHATSAPP", "APP"}


def planificar_alertas() -> dict:
    creadas = repo.plan_alerta_eventos()
    return {"planned": int(creadas or 0)}


def despachar_alertas(limit: int = 50) -> dict:
    limit = max(1, min(int(limit), 200))
    eventos = repo.list_due_alert_events(limit)
    resultados = []
    for evento in eventos:
        canal = str(evento.get("Canal") or "").upper()
        evento_id = int(evento["AlertaEventoID"])
        if canal == "TAREA":
            tarea = repo.ensure_canonical_task_for_alert(evento_id)
            resultados.append({"alerta_evento_id": evento_id, "canal": canal, "status": "GENERADA", "reference": str(tarea.get("TareaSistemaID"))})
            continue
        if canal in EXTERNAL_CHANNELS:
            resultados.append(dispatch_external_alert(evento))
            continue
        resultados.append({"alerta_evento_id": evento_id, "canal": canal, "status": "BLOCKED_UNSUPPORTED_CHANNEL"})
    return {"processed": len(resultados), "items": resultados}
