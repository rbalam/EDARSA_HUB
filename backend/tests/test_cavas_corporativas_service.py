from datetime import datetime, time
from decimal import Decimal

import pytest

from modules.cavas_corporativas.domain import (
    BenefitKind, BenefitRule, BenefitScope, EvaluationContext, PolicyRestrictions, ScopeKind
)
from modules.cavas_corporativas.repository import AuthorizedReference
from modules.cavas_corporativas.service import CavasCorporativasService


class FakeRepository:
    def __init__(self, authorized=True):
        self.authorized = authorized
        self.records = []

    def find_active_authorized(self, fuente, referencia, occurred_at):
        if not self.authorized:
            return None
        return AuthorizedReference("auth-1", "conv-1")

    def load_benefit_rules(self, convenio_id):
        return [BenefitRule(
            benefit_id="benefit-1", kind=BenefitKind.PERCENT_DISCOUNT, active=True,
            unit_references=frozenset({"130MID"}),
            scopes=(BenefitScope(ScopeKind.SALES_LINE, "ALIMENTOS"),),
            restrictions=PolicyRestrictions(start_time=time(14, 0), end_time=time(21, 59)),
        )]

    def record_application(self, record):
        duplicate = any(
            r.beneficio_id == record.beneficio_id and r.unidad_referencia == record.unidad_referencia
            and r.operacion_tipo == record.operacion_tipo and r.operacion_referencia == record.operacion_referencia
            for r in self.records
        )
        if duplicate:
            return False
        self.records.append(record)
        return True


def context(hour=17):
    return EvaluationContext(
        occurred_at=datetime(2026, 9, 9, hour, 0), unit_reference="130MID", authorized_user=False,
        sales_line_reference="ALIMENTOS", has_reservation=True, guest_count=4,
    )


def test_service_uses_canonical_authorization_and_rule_engine():
    result = CavasCorporativasService(FakeRepository()).evaluate_for_identity("USUARIO", "42", context())
    assert result.convenio_id == "conv-1"
    assert len(result.applicable) == 1
    assert result.applicable[0].benefit_id == "benefit-1"


def test_service_returns_no_benefits_for_unknown_identity():
    result = CavasCorporativasService(FakeRepository(authorized=False)).evaluate_for_identity("USUARIO", "404", context())
    assert result.convenio_id is None
    assert result.applicable == ()


def test_record_application_is_idempotent_through_repository_contract():
    repo = FakeRepository()
    service = CavasCorporativasService(repo)
    ctx = context()
    evaluation = service.evaluate_for_identity("USUARIO", "42", ctx)
    args = dict(
        evaluation=evaluation, benefit_id="benefit-1", context=ctx, operacion_tipo="TICKET",
        operacion_referencia="ticket-100", importe_base=Decimal("100.00"),
        importe_beneficio=Decimal("10.00"), moneda_codigo="MXN",
    )
    assert service.record_applied_benefit(**args) is True
    assert service.record_applied_benefit(**args) is False
    assert len(repo.records) == 1


def test_cannot_record_non_applicable_benefit():
    repo = FakeRepository()
    service = CavasCorporativasService(repo)
    ctx = context(hour=23)
    evaluation = service.evaluate_for_identity("USUARIO", "42", ctx)
    with pytest.raises(ValueError, match="BENEFIT_NOT_APPLICABLE"):
        service.record_applied_benefit(evaluation, "benefit-1", ctx, "TICKET", "ticket-101")
