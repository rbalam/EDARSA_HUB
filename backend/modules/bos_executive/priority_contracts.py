from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PriorityBand(str, Enum):
    CRITICA = "CRITICA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    SIN_PRIORIDAD = "SIN_PRIORIDAD"


@dataclass(frozen=True)
class ExecutivePriorityItem:
    source_domain: str
    source_object_ref: str
    title: str
    priority_band: PriorityBand
    priority_score_explanation: tuple[str, ...] = ()
    sla_state: str | None = None
    due_at: str | None = None
    impact: str | None = None
    owner_ref: str | None = None
    permission_refs: tuple[str, ...] = ()
    as_of: str | None = None
    stale: bool = False


@dataclass(frozen=True)
class ExecutivePriorityAggregate:
    items: tuple[ExecutivePriorityItem, ...]
    total: int
    domains: tuple[str, ...]
    stale: bool
