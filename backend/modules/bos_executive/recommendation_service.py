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
