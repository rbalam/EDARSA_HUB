from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceKind(str, Enum):
    HECHO = "HECHO"
    CORRELACION = "CORRELACION"
    INFERENCIA = "INFERENCIA"


class ConfidenceClass(str, Enum):
    DETERMINISTA = "determinista"
    CORRELACIONAL = "correlacional"
    INFERIDO = "inferido"


class FindingStatus(str, Enum):
    EXPLAINED = "EXPLAINED"
    NOT_ENOUGH_EVIDENCE = "NOT_ENOUGH_EVIDENCE"


@dataclass(frozen=True)
class EvidenceRef:
    ref: str
    kind: EvidenceKind
    as_of: str | None = None
    stale: bool = False
    provenance: str | None = None


@dataclass(frozen=True)
class ExecutiveFindingInput:
    finding_id: str
    metric_id: str
    scope_ref: str
    period_ref: str
    observation: str
    evidence: tuple[EvidenceRef, ...] = ()
    contributing_factors: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    suggested_next_checks: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutiveFindingOutput:
    finding_id: str
    status: FindingStatus
    claim: str
    evidence_refs: tuple[str, ...]
    contributing_factors: tuple[str, ...]
    classification: EvidenceKind | None
    confidence_class: ConfidenceClass | None
    as_of: str | None
    stale: bool
    limitations: tuple[str, ...]
    suggested_next_checks: tuple[str, ...]
