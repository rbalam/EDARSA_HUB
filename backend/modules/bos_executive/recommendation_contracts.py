# E3C_RECOMMENDATION_CONTRACT_V1

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import ConfidenceClass


class RecommendationRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class ExecutiveRecommendation:
    recommendation_id: str
    recommendation_type: str
    source_ref: str
    title: str
    rationale: str
    evidence_refs: tuple[str, ...]
    expected_impact: str
    risk_level: RecommendationRisk
    confidence_class: ConfidenceClass
    generated_at: str
    valid_until: str
    required_permissions: tuple[str, ...] = ()
    eligible_actions: tuple[str, ...] = ()
    human_confirmation_required: bool = True
    stale: bool = False
    provenance_refs: tuple[str, ...] = ()
