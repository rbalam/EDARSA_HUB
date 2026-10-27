# E3C_RECOMMENDATION_SERVICE_V1

from __future__ import annotations

import hashlib

from .contracts import ConfidenceClass, ExecutiveFindingOutput, FindingStatus
from .priority_contracts import ExecutivePriorityItem, PriorityBand
from .recommendation_contracts import ExecutiveRecommendation, RecommendationRisk


def _unique(values):
    return tuple(dict.fromkeys(value for value in values if value))


def _stable_id(*parts: str) -> str:
    payload = "|".join(parts).encode("utf-8")
    return "rec:" + hashlib.sha256(payload).hexdigest()[:20]


def _priority_risk(band: PriorityBand) -> RecommendationRisk:
    if band is PriorityBand.CRITICA:
        return RecommendationRisk.HIGH
    if band is PriorityBand.ALTA:
        return RecommendationRisk.MEDIUM
    return RecommendationRisk.LOW


def _priority_confidence(item: ExecutivePriorityItem) -> ConfidenceClass:
    if item.priority_score_explanation and "NO_PRIORITY_SIGNAL" not in item.priority_score_explanation:
        return ConfidenceClass.DETERMINISTA
    return ConfidenceClass.INFERIDO


def recommend_from_finding(
    finding: ExecutiveFindingOutput,
    *,
    generated_at: str,
    valid_until: str,
    expected_impact: str,
    required_permissions=(),
    eligible_actions=(),
) -> ExecutiveRecommendation | None:
    if finding.status is not FindingStatus.EXPLAINED or not finding.evidence_refs or finding.confidence_class is None:
        return None
    evidence = _unique(finding.evidence_refs)
    return ExecutiveRecommendation(
        recommendation_id=_stable_id("FINDING", finding.finding_id, finding.claim, generated_at, valid_until),
        recommendation_type="ADDRESS_FINDING",
        source_ref=f"finding:{finding.finding_id}",
        title=f"Atender hallazgo {finding.finding_id}",
        rationale=finding.claim,
        evidence_refs=evidence,
        expected_impact=expected_impact,
        risk_level=RecommendationRisk.MEDIUM,
        confidence_class=finding.confidence_class,
        generated_at=generated_at,
        valid_until=valid_until,
        required_permissions=_unique(required_permissions),
        eligible_actions=_unique(eligible_actions),
        human_confirmation_required=True,
        stale=finding.stale,
        provenance_refs=evidence,
    )
