from datetime import date, datetime, time

from modules.cavas_corporativas.domain import (
    BenefitKind,
    BenefitRule,
    BenefitScope,
    EvaluationContext,
    PolicyRestrictions,
    ScopeKind,
    evaluate_benefit,
)


def _rule(**overrides):
    data = dict(
        benefit_id="BEN-1",
        kind=BenefitKind.PERCENT_DISCOUNT,
        active=True,
        valid_from=date(2026, 1, 1),
        valid_to=date(2026, 12, 31),
        unit_references=frozenset({"130MID"}),
        scopes=(BenefitScope(ScopeKind.SALES_LINE, "ALIMENTOS"),),
        restrictions=PolicyRestrictions(),
    )
    data.update(overrides)
    return BenefitRule(**data)


def _context(**overrides):
    data = dict(
        occurred_at=datetime(2026, 9, 8, 18, 0),
        unit_reference="130MID",
        authorized_user=True,
        sales_line_reference="ALIMENTOS",
    )
    data.update(overrides)
    return EvaluationContext(**data)


def test_applicable_requires_explicit_unit_and_scope():
    assert evaluate_benefit(_rule(), _context()).applicable is True
    assert evaluate_benefit(_rule(unit_references=frozenset()), _context()).reason == "UNIT_NOT_INCLUDED"
    assert evaluate_benefit(_rule(scopes=()), _context()).reason == "SCOPE_NOT_INCLUDED"


def test_unauthorized_user_is_rejected():
    decision = evaluate_benefit(_rule(), _context(authorized_user=False))
    assert decision.applicable is False
    assert decision.reason == "USER_NOT_AUTHORIZED"


def test_hierarchy_scope_matches_exact_reference():
    sku_rule = _rule(scopes=(BenefitScope(ScopeKind.SKU, "SKU-99"),))
    assert evaluate_benefit(sku_rule, _context(sku_reference="SKU-99")).applicable is True
    assert evaluate_benefit(sku_rule, _context(sku_reference="SKU-98")).reason == "SCOPE_NOT_INCLUDED"


def test_configurable_same_day_time_window():
    rule = _rule(restrictions=PolicyRestrictions(start_time=time(14, 0), end_time=time(20, 0)))
    assert evaluate_benefit(rule, _context(occurred_at=datetime(2026, 9, 8, 19, 59))).applicable is True
    assert evaluate_benefit(rule, _context(occurred_at=datetime(2026, 9, 8, 20, 1))).reason == "TIME_NOT_ALLOWED"


def test_configurable_overnight_time_window():
    rule = _rule(restrictions=PolicyRestrictions(start_time=time(19, 0), end_time=time(2, 0)))
    assert evaluate_benefit(rule, _context(occurred_at=datetime(2026, 9, 8, 23, 30))).applicable is True
    assert evaluate_benefit(rule, _context(occurred_at=datetime(2026, 9, 9, 1, 30))).applicable is True
    assert evaluate_benefit(rule, _context(occurred_at=datetime(2026, 9, 8, 12, 0))).reason == "TIME_NOT_ALLOWED"


def test_reservation_and_guest_limit_are_policy_driven():
    rule = _rule(restrictions=PolicyRestrictions(requires_reservation=True, max_guests=8))
    assert evaluate_benefit(rule, _context(has_reservation=False, guest_count=4)).reason == "RESERVATION_REQUIRED"
    assert evaluate_benefit(rule, _context(has_reservation=True, guest_count=9)).reason == "GUEST_LIMIT_EXCEEDED"
    assert evaluate_benefit(rule, _context(has_reservation=True, guest_count=8)).applicable is True


def test_validity_and_weekday_are_enforced_without_hardcodes():
    rule = _rule(
        valid_from=date(2026, 9, 1),
        valid_to=date(2026, 9, 30),
        restrictions=PolicyRestrictions(allowed_weekdays=frozenset({1})),
    )
    assert evaluate_benefit(rule, _context(occurred_at=datetime(2026, 9, 8, 18, 0))).applicable is True
    assert evaluate_benefit(rule, _context(occurred_at=datetime(2026, 9, 9, 18, 0))).reason == "WEEKDAY_NOT_ALLOWED"
    assert evaluate_benefit(rule, _context(occurred_at=datetime(2026, 10, 1, 18, 0))).reason == "EXPIRED"
