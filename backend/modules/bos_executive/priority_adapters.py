from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .priority_contracts import ExecutivePriorityItem, PriorityBand


_TEXT_PRIORITY = {
    "CRITICA": PriorityBand.CRITICA,
    "CRITICAL": PriorityBand.CRITICA,
    "URGENTE": PriorityBand.ALTA,
    "ALTA": PriorityBand.ALTA,
    "HIGH": PriorityBand.ALTA,
    "MEDIA": PriorityBand.MEDIA,
    "MEDIUM": PriorityBand.MEDIA,
    "NORMAL": PriorityBand.MEDIA,
    "BAJA": PriorityBand.BAJA,
    "LOW": PriorityBand.BAJA,
}

_OPERATIONAL_SLA_PRIORITY = {
    "ESCALADA": PriorityBand.CRITICA,
    "VENCIDA": PriorityBand.CRITICA,
    "URGENTE": PriorityBand.ALTA,
    "ADVERTENCIA": PriorityBand.MEDIA,
}

_CRM_SLA_PRIORITY = {
    "VENCIDO": PriorityBand.CRITICA,
    "PROXIMO": PriorityBand.ALTA,
}


def _first(record: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _priority_from_text(value: Any) -> PriorityBand:
    normalized = str(value or "").strip().upper()
    return _TEXT_PRIORITY.get(normalized, PriorityBand.SIN_PRIORIDAD)


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _permissions(record: Mapping[str, Any]) -> tuple[str, ...]:
    raw = _first(record, "permission_refs", "permisos", "permissions")
    if raw is None:
        return ()
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, (list, tuple, set)):
        return _unique(tuple(str(value) for value in raw if value not in (None, "")))
    return (str(raw),)


def adapt_operational_task(record: Mapping[str, Any]) -> ExecutivePriorityItem | None:
    task_id = _first(record, "id", "tarea_id", "TareaID", "TareaId")
    if task_id is None:
        return None

    sla_state = str(_first(record, "estado_sla", "EstadoSLA") or "").strip().upper() or None
    source_priority = _priority_from_text(_first(record, "prioridad", "Prioridad"))
    sla_priority = _OPERATIONAL_SLA_PRIORITY.get(sla_state or "")
    band = sla_priority or source_priority

    reasons: tuple[str, ...] = ()
    if sla_priority:
        reasons += (f"SLA_{sla_state}",)
    if source_priority is not PriorityBand.SIN_PRIORIDAD:
        reasons += (f"SOURCE_PRIORITY_{source_priority.value}",)
    if not reasons:
        reasons = ("NO_PRIORITY_SIGNAL",)

    return ExecutivePriorityItem(
        source_domain="OPERATIVO",
        source_object_ref=f"tarea:{task_id}",
        title=str(_first(record, "titulo", "Titulo", "descripcion", "Descripcion") or f"Tarea {task_id}"),
        priority_band=band,
        priority_score_explanation=_unique(reasons),
        sla_state=sla_state,
        due_at=_text(_first(record, "fecha_limite", "FechaLimite")),
        impact=_text(_first(record, "impacto", "Impacto")),
        owner_ref=_text(_first(record, "responsable_id", "ResponsableID", "usuario_responsable_id")),
        permission_refs=_permissions(record),
        as_of=_text(_first(record, "as_of", "fecha_actualizacion", "FechaActualizacion")),
        stale=bool(_first(record, "stale", "es_stale") or False),
    )


def adapt_crm_opportunity(record: Mapping[str, Any]) -> ExecutivePriorityItem | None:
    opportunity_id = _first(record, "OportunidadID", "oportunidad_id", "id")
    if opportunity_id is None:
        return None

    sla_state = str(_first(record, "EstatusSLA", "estatus_sla", "estado_sla") or "").strip().upper() or None
    source_priority = _priority_from_text(_first(record, "Prioridad", "prioridad"))
    sla_priority = _CRM_SLA_PRIORITY.get(sla_state or "")
    band = sla_priority or source_priority

    reasons: tuple[str, ...] = ()
    if sla_priority:
        reasons += (f"CRM_SLA_{sla_state}",)
    if source_priority is not PriorityBand.SIN_PRIORIDAD:
        reasons += (f"SOURCE_PRIORITY_{source_priority.value}",)
    if not reasons:
        reasons = ("NO_PRIORITY_SIGNAL",)

    amount = _first(record, "MontoEstimado", "monto_estimado")
    impact = f"monto_estimado:{amount}" if amount not in (None, "") else None

    return ExecutivePriorityItem(
        source_domain="CRM",
        source_object_ref=f"oportunidad:{opportunity_id}",
        title=str(_first(record, "Nombre", "NombreOportunidad", "nombre") or f"Oportunidad {opportunity_id}"),
        priority_band=band,
        priority_score_explanation=_unique(reasons),
        sla_state=sla_state,
        due_at=_text(_first(record, "fecha_limite", "FechaLimite")),
        impact=impact,
        owner_ref=_text(_first(record, "ResponsableID", "responsable_id")),
        permission_refs=_permissions(record),
        as_of=_text(_first(record, "as_of", "FechaUltimaActividad", "fecha_ultima_actividad")),
        stale=bool(_first(record, "stale", "es_stale") or False),
    )
