"""Motor puro de migracion e historia para Cavas.

No accede a SQL, no resuelve conexiones, no conoce proveedores y no escribe
entidades canonicas. Implementa contratos deterministas de Gate 16B para que
adapters y servicios posteriores puedan reutilizar una sola semantica.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any, Callable, Iterable, Mapping, Optional

from .domain import BottleOrigin, BottleOriginEvidence


class MigrationMode(str, Enum):
    CONTINUOUS_SYNC = "CONTINUOUS_SYNC"
    HISTORICAL_MIGRATION = "HISTORICAL_MIGRATION"
    HYBRID_CUTOVER = "HYBRID_CUTOVER"
    MANUAL_FILE_IMPORT = "MANUAL_FILE_IMPORT"


class MappingStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    APPROVED_EQUIVALENCE = "APPROVED_EQUIVALENCE"
    PROBABLE_MATCH = "PROBABLE_MATCH"
    NEW_CANONICAL_REQUIRED = "NEW_CANONICAL_REQUIRED"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class SourceIdentity:
    source_instance_id: str
    entity_type: str
    source_record_id: str
    source_transaction_id: Optional[str] = None
    source_line_id: Optional[str] = None

    def idempotency_key(self) -> str:
        parts = [
            _required(self.source_instance_id, "source_instance_id"),
            _required(self.entity_type, "entity_type"),
            _required(self.source_record_id, "source_record_id"),
            (self.source_transaction_id or "").strip(),
            (self.source_line_id or "").strip(),
        ]
        return "|".join(parts)


@dataclass(frozen=True)
class ExternalRecord:
    identity: SourceIdentity
    source_system: str
    payload: Mapping[str, Any]
    original_occurred_at: datetime
    original_created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        _required(self.source_system, "source_system")
        _require_aware(self.original_occurred_at, "original_occurred_at")
        if self.original_created_at is not None:
            _require_aware(self.original_created_at, "original_created_at")

    @property
    def checksum(self) -> str:
        return canonical_payload_checksum(self.payload)


@dataclass(frozen=True)
class MappingDecision:
    status: MappingStatus
    canonical_entity_type: Optional[str] = None
    canonical_entity_id: Optional[str] = None
    reason: Optional[str] = None

    @property
    def requires_review(self) -> bool:
        return self.status in {MappingStatus.PROBABLE_MATCH, MappingStatus.CONFLICT}

    @property
    def accepted_for_execution(self) -> bool:
        return self.status in {
            MappingStatus.EXACT_MATCH,
            MappingStatus.APPROVED_EQUIVALENCE,
            MappingStatus.NEW_CANONICAL_REQUIRED,
        }


@dataclass(frozen=True)
class DryRunItem:
    record: ExternalRecord
    decision: MappingDecision


@dataclass(frozen=True)
class DryRunSummary:
    mode: MigrationMode
    items: tuple[DryRunItem, ...]
    received: int
    accepted: int
    review_required: int
    rejected: int

    @property
    def execution_ready(self) -> bool:
        return self.received > 0 and self.review_required == 0 and self.rejected == 0


@dataclass(frozen=True)
class ReconciliationMetric:
    name: str
    source_count: int
    canonical_count: int
    difference: int
    approved_difference: int

    @property
    def reconciled(self) -> bool:
        return self.difference == self.approved_difference


@dataclass(frozen=True)
class ReconciliationResult:
    metrics: tuple[ReconciliationMetric, ...]

    @property
    def certifiable(self) -> bool:
        return bool(self.metrics) and all(metric.reconciled for metric in self.metrics)


def canonical_payload_checksum(payload: Mapping[str, Any]) -> str:
    """Checksum estable para detectar replay/cambio del mismo registro externo."""
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def plan_dry_run(
    records: Iterable[ExternalRecord],
    *,
    mode: MigrationMode,
    resolver: Callable[[ExternalRecord], MappingDecision],
) -> DryRunSummary:
    """Clasifica registros sin escribir datos operativos."""
    items = tuple(DryRunItem(record=record, decision=resolver(record)) for record in records)
    keys = [item.record.identity.idempotency_key() for item in items]
    if len(keys) != len(set(keys)):
        raise ValueError("dry-run contiene identidades externas duplicadas")

    accepted = sum(1 for item in items if item.decision.accepted_for_execution)
    review_required = sum(1 for item in items if item.decision.requires_review)
    rejected = sum(1 for item in items if item.decision.status == MappingStatus.REJECTED)

    return DryRunSummary(
        mode=mode,
        items=items,
        received=len(items),
        accepted=accepted,
        review_required=review_required,
        rejected=rejected,
    )


def reconcile_counts(
    source_counts: Mapping[str, int],
    canonical_counts: Mapping[str, int],
    *,
    approved_differences: Optional[Mapping[str, int]] = None,
) -> ReconciliationResult:
    """Reconcilia conteos; toda diferencia no cero debe estar aprobada explicitamente."""
    approved = approved_differences or {}
    names = sorted(set(source_counts) | set(canonical_counts))
    metrics = []
    for name in names:
        source = _non_negative_int(source_counts.get(name, 0), f"source_counts[{name}]")
        canonical = _non_negative_int(canonical_counts.get(name, 0), f"canonical_counts[{name}]")
        approved_difference = int(approved.get(name, 0))
        metrics.append(
            ReconciliationMetric(
                name=name,
                source_count=source,
                canonical_count=canonical,
                difference=canonical - source,
                approved_difference=approved_difference,
            )
        )
    return ReconciliationResult(metrics=tuple(metrics))


def historical_origin_evidence(
    record: ExternalRecord,
    *,
    historical_reference: str,
    source_unit_id: Optional[str] = None,
) -> BottleOriginEvidence:
    """Proyecta procedencia externa al contrato historico ya existente de Cavas."""
    return BottleOriginEvidence(
        origin=BottleOrigin.REGULARIZACION_HISTORICA,
        source_unit_id=source_unit_id,
        source_transaction_id=record.identity.source_transaction_id,
        source_line_id=record.identity.source_line_id,
        source_system=record.source_system,
        historical_reference=_required(historical_reference, "historical_reference"),
    )


def _required(value: str, name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{name} es requerido")
    return normalized


def _require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} debe incluir zona horaria")


def _non_negative_int(value: Any, name: str) -> int:
    number = int(value)
    if number < 0:
        raise ValueError(f"{name} no puede ser negativo")
    return number


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime en payload debe incluir zona horaria")
        return value.isoformat()
    raise TypeError(f"tipo no serializable para checksum: {type(value).__name__}")
