"""Contratos puros del dominio Cavas Corporativas.

No accede a SQL ni a sistemas externos. Modela el motor canonico opt-in de
beneficios y restricciones que despues puede ser persistido por las tablas
CavasCorporativas_* ya certificadas.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum
from typing import FrozenSet, Optional, Tuple


class BenefitKind(str, Enum):
    PERCENT_DISCOUNT = "PERCENT_DISCOUNT"
    FIXED_PRICE = "FIXED_PRICE"
    PRICE_LIST = "PRICE_LIST"
    COURTESY = "COURTESY"
    CORKAGE = "CORKAGE"
    ROOM_ACCESS = "ROOM_ACCESS"
    RESERVATION_PRIORITY = "RESERVATION_PRIORITY"


class ScopeKind(str, Enum):
    SALES_LINE = "SALES_LINE"
    CATEGORY = "CATEGORY"
    FAMILY = "FAMILY"
    SKU = "SKU"


@dataclass(frozen=True)
class BenefitScope:
    kind: ScopeKind
    reference: str


@dataclass(frozen=True)
class PolicyRestrictions:
    allowed_weekdays: FrozenSet[int] = frozenset()
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    requires_reservation: bool = False
    max_guests: Optional[int] = None


@dataclass(frozen=True)
class BenefitRule:
    benefit_id: str
    kind: BenefitKind
    active: bool
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    unit_references: FrozenSet[str] = frozenset()
    scopes: Tuple[BenefitScope, ...] = ()
    restrictions: PolicyRestrictions = PolicyRestrictions()


@dataclass(frozen=True)
class EvaluationContext:
    occurred_at: datetime
    unit_reference: str
    authorized_user: bool
    sales_line_reference: Optional[str] = None
    category_reference: Optional[str] = None
    family_reference: Optional[str] = None
    sku_reference: Optional[str] = None
    has_reservation: bool = False
    guest_count: Optional[int] = None


@dataclass(frozen=True)
class EvaluationDecision:
    applicable: bool
    reason: str
    benefit_id: str


def _within_time_window(value: time, start: Optional[time], end: Optional[time]) -> bool:
    if start is None and end is None:
        return True
    if start is None:
        return value <= end  # type: ignore[operator]
    if end is None:
        return value >= start
    if start <= end:
        return start <= value <= end
    return value >= start or value <= end


def _scope_matches(scope: BenefitScope, context: EvaluationContext) -> bool:
    actual = {
        ScopeKind.SALES_LINE: context.sales_line_reference,
        ScopeKind.CATEGORY: context.category_reference,
        ScopeKind.FAMILY: context.family_reference,
        ScopeKind.SKU: context.sku_reference,
    }[scope.kind]
    return actual is not None and actual == scope.reference


def evaluate_benefit(rule: BenefitRule, context: EvaluationContext) -> EvaluationDecision:
    """Evalua un beneficio con semantica opt-in y sin reglas horarias hardcoded."""
    if not rule.active:
        return EvaluationDecision(False, "BENEFIT_INACTIVE", rule.benefit_id)
    if not context.authorized_user:
        return EvaluationDecision(False, "USER_NOT_AUTHORIZED", rule.benefit_id)
    if not rule.unit_references or context.unit_reference not in rule.unit_references:
        return EvaluationDecision(False, "UNIT_NOT_INCLUDED", rule.benefit_id)
    if not rule.scopes or not any(_scope_matches(scope, context) for scope in rule.scopes):
        return EvaluationDecision(False, "SCOPE_NOT_INCLUDED", rule.benefit_id)

    current_date = context.occurred_at.date()
    if rule.valid_from is not None and current_date < rule.valid_from:
        return EvaluationDecision(False, "NOT_YET_VALID", rule.benefit_id)
    if rule.valid_to is not None and current_date > rule.valid_to:
        return EvaluationDecision(False, "EXPIRED", rule.benefit_id)

    restrictions = rule.restrictions
    if restrictions.allowed_weekdays and context.occurred_at.weekday() not in restrictions.allowed_weekdays:
        return EvaluationDecision(False, "WEEKDAY_NOT_ALLOWED", rule.benefit_id)
    if not _within_time_window(context.occurred_at.time(), restrictions.start_time, restrictions.end_time):
        return EvaluationDecision(False, "TIME_NOT_ALLOWED", rule.benefit_id)
    if restrictions.requires_reservation and not context.has_reservation:
        return EvaluationDecision(False, "RESERVATION_REQUIRED", rule.benefit_id)
    if restrictions.max_guests is not None:
        if context.guest_count is None:
            return EvaluationDecision(False, "GUEST_COUNT_REQUIRED", rule.benefit_id)
        if context.guest_count > restrictions.max_guests:
            return EvaluationDecision(False, "GUEST_LIMIT_EXCEEDED", rule.benefit_id)

    return EvaluationDecision(True, "APPLICABLE", rule.benefit_id)
