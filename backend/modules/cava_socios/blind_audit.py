"""Auditoria ciega y contrato de readiness de vision para Cavas.

Este modulo NO llama modelos de IA, NO accede a object storage y NO conoce
proveedores. Implementa la semantica determinista que posteriormente consumira
core.object_storage + AI Gateway.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Optional, Sequence


class BlindAuditStatus(str, Enum):
    MATCH = "MATCH"
    MISSING = "MISSING"
    UNEXPECTED = "UNEXPECTED"
    QUANTITY_MISMATCH = "QUANTITY_MISMATCH"
    LEVEL_MISMATCH = "LEVEL_MISMATCH"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class ExpectedBottle:
    bottle_id: str
    expected_quantity: int = 1
    expected_level_pct: Optional[float] = None

    def __post_init__(self) -> None:
        _required(self.bottle_id, "bottle_id")
        if self.expected_quantity < 0:
            raise ValueError("expected_quantity no puede ser negativo")
        _validate_pct(self.expected_level_pct, "expected_level_pct")


@dataclass(frozen=True)
class BlindObservation:
    observation_id: str
    observed_reference: str
    observed_quantity: int = 1
    observed_level_pct: Optional[float] = None
    evidence_id: Optional[str] = None
    recognition_confidence: Optional[float] = None

    def __post_init__(self) -> None:
        _required(self.observation_id, "observation_id")
        _required(self.observed_reference, "observed_reference")
        if self.observed_quantity < 0:
            raise ValueError("observed_quantity no puede ser negativo")
        _validate_pct(self.observed_level_pct, "observed_level_pct")
        if self.recognition_confidence is not None and not (0.0 <= self.recognition_confidence <= 1.0):
            raise ValueError("recognition_confidence fuera de rango")


@dataclass(frozen=True)
class AuditFinding:
    status: BlindAuditStatus
    expected_bottle_id: Optional[str]
    observation_id: Optional[str]
    expected_quantity: int
    observed_quantity: int
    expected_level_pct: Optional[float]
    observed_level_pct: Optional[float]
    reason: str


@dataclass(frozen=True)
class BlindAuditResult:
    findings: tuple[AuditFinding, ...]

    @property
    def clean(self) -> bool:
        return bool(self.findings) and all(f.status == BlindAuditStatus.MATCH for f in self.findings)

    @property
    def requires_review(self) -> bool:
        return any(f.status == BlindAuditStatus.REVIEW_REQUIRED for f in self.findings)


@dataclass(frozen=True)
class VisionReadinessRequest:
    evidence_id: str
    storage_reference: str
    required_capabilities: frozenset[str]
    data_classification: str
    max_cost_usd: float
    correlation_id: str

    def __post_init__(self) -> None:
        _required(self.evidence_id, "evidence_id")
        _required(self.storage_reference, "storage_reference")
        _required(self.data_classification, "data_classification")
        _required(self.correlation_id, "correlation_id")
        if not self.required_capabilities:
            raise ValueError("required_capabilities es requerido")
        if self.max_cost_usd < 0:
            raise ValueError("max_cost_usd no puede ser negativo")


@dataclass(frozen=True)
class VisionRecognitionCandidate:
    external_reference: str
    confidence: float
    attributes: Mapping[str, object]

    def __post_init__(self) -> None:
        _required(self.external_reference, "external_reference")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence fuera de rango")


def reconcile_blind_audit(
    expected: Iterable[ExpectedBottle],
    observations: Iterable[BlindObservation],
    *,
    observation_to_bottle: Mapping[str, str],
    level_tolerance_pct: float = 5.0,
    min_recognition_confidence: float = 0.90,
) -> BlindAuditResult:
    """Compara observacion ciega contra esperado DESPUES de capturar.

    observation_to_bottle debe provenir de una etapa de identificacion separada
    (manual o IA autorizada). La captura ciega nunca recibe el esperado.
    """
    if level_tolerance_pct < 0:
        raise ValueError("level_tolerance_pct no puede ser negativo")
    if not (0.0 <= min_recognition_confidence <= 1.0):
        raise ValueError("min_recognition_confidence fuera de rango")

    exp = {item.bottle_id: item for item in expected}
    if len(exp) != len(tuple(expected)):
        raise ValueError("expected contiene bottle_id duplicado")

    obs_list = tuple(observations)
    if len({o.observation_id for o in obs_list}) != len(obs_list):
        raise ValueError("observations contiene observation_id duplicado")

    matched_expected: set[str] = set()
    findings: list[AuditFinding] = []

    for obs in obs_list:
        bottle_id = observation_to_bottle.get(obs.observation_id)
        if not bottle_id or bottle_id not in exp:
            findings.append(AuditFinding(
                BlindAuditStatus.UNEXPECTED, None, obs.observation_id, 0,
                obs.observed_quantity, None, obs.observed_level_pct,
                "observacion sin correspondencia canonica",
            ))
            continue

        item = exp[bottle_id]
        matched_expected.add(bottle_id)

        if obs.recognition_confidence is not None and obs.recognition_confidence < min_recognition_confidence:
            status = BlindAuditStatus.REVIEW_REQUIRED
            reason = "confianza de reconocimiento insuficiente"
        elif item.expected_quantity != obs.observed_quantity:
            status = BlindAuditStatus.QUANTITY_MISMATCH
            reason = "cantidad observada distinta"
        elif _level_mismatch(item.expected_level_pct, obs.observed_level_pct, level_tolerance_pct):
            status = BlindAuditStatus.LEVEL_MISMATCH
            reason = "nivel observado fuera de tolerancia"
        else:
            status = BlindAuditStatus.MATCH
            reason = "coincidencia"

        findings.append(AuditFinding(
            status, bottle_id, obs.observation_id,
            item.expected_quantity, obs.observed_quantity,
            item.expected_level_pct, obs.observed_level_pct, reason,
        ))

    for bottle_id, item in exp.items():
        if bottle_id not in matched_expected:
            findings.append(AuditFinding(
                BlindAuditStatus.MISSING, bottle_id, None,
                item.expected_quantity, 0,
                item.expected_level_pct, None,
                "botella esperada no observada",
            ))

    return BlindAuditResult(findings=tuple(findings))


def validate_vision_candidates(
    candidates: Sequence[VisionRecognitionCandidate],
    *,
    min_confidence: float,
) -> tuple[VisionRecognitionCandidate, ...]:
    """Filtra candidatos para revision; no toma decisiones canonicas."""
    if not (0.0 <= min_confidence <= 1.0):
        raise ValueError("min_confidence fuera de rango")
    return tuple(c for c in candidates if c.confidence >= min_confidence)


def _level_mismatch(expected: Optional[float], observed: Optional[float], tolerance: float) -> bool:
    if expected is None and observed is None:
        return False
    if expected is None or observed is None:
        return True
    return abs(expected - observed) > tolerance


def _validate_pct(value: Optional[float], name: str) -> None:
    if value is not None and not (0.0 <= value <= 100.0):
        raise ValueError(f"{name} fuera de rango")


def _required(value: str, name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{name} es requerido")
    return normalized
