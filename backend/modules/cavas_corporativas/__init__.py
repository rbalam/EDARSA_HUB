"""Core backend de Cavas Corporativas."""

from .domain import (
    BenefitKind,
    BenefitRule,
    BenefitScope,
    EvaluationContext,
    EvaluationDecision,
    PolicyRestrictions,
    ScopeKind,
    evaluate_benefit,
)

__all__ = [
    "BenefitKind",
    "BenefitRule",
    "BenefitScope",
    "EvaluationContext",
    "EvaluationDecision",
    "PolicyRestrictions",
    "ScopeKind",
    "evaluate_benefit",
]
