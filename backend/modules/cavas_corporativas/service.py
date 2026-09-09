"""Capa de servicio de Cavas Corporativas.

Orquesta identidad corporativa, reglas persistidas y el motor puro del dominio.
No conoce HTTP ni duplica reglas de negocio en frontend.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .domain import EvaluationContext, EvaluationDecision, evaluate_benefit
from .repository import ApplicationRecord, CavasCorporativasRepository


@dataclass(frozen=True)
class BenefitEvaluation:
    convenio_id: Optional[str]
    autorizado_id: Optional[str]
    decisions: tuple[EvaluationDecision, ...]

    @property
    def applicable(self) -> tuple[EvaluationDecision, ...]:
        return tuple(item for item in self.decisions if item.applicable)


class CavasCorporativasService:
    def __init__(self, repository: Optional[CavasCorporativasRepository] = None):
        self.repository = repository or CavasCorporativasRepository()

    def evaluate_for_identity(
        self, identidad_fuente: str, identidad_referencia: str, context: EvaluationContext
    ) -> BenefitEvaluation:
        auth = self.repository.find_active_authorized(identidad_fuente, identidad_referencia, context.occurred_at)
        if auth is None:
            return BenefitEvaluation(None, None, ())
        normalized_context = EvaluationContext(
            occurred_at=context.occurred_at,
            unit_reference=context.unit_reference,
            authorized_user=True,
            sales_line_reference=context.sales_line_reference,
            category_reference=context.category_reference,
            family_reference=context.family_reference,
            sku_reference=context.sku_reference,
            has_reservation=context.has_reservation,
            guest_count=context.guest_count,
        )
        rules = self.repository.load_benefit_rules(auth.convenio_id)
        decisions = tuple(evaluate_benefit(rule, normalized_context) for rule in rules)
        return BenefitEvaluation(auth.convenio_id, auth.autorizado_id, decisions)

    def record_applied_benefit(
        self, evaluation: BenefitEvaluation, benefit_id: str, context: EvaluationContext,
        operacion_tipo: str, operacion_referencia: str, importe_base: Optional[Decimal] = None,
        importe_beneficio: Optional[Decimal] = None, moneda_codigo: Optional[str] = None,
        applied_by_referencia: Optional[str] = None,
    ) -> bool:
        if evaluation.convenio_id is None:
            raise ValueError("CONVENIO_REQUIRED")
        decision = next((d for d in evaluation.applicable if d.benefit_id == benefit_id), None)
        if decision is None:
            raise ValueError("BENEFIT_NOT_APPLICABLE")
        return self.repository.record_application(ApplicationRecord(
            convenio_id=evaluation.convenio_id,
            beneficio_id=benefit_id,
            autorizado_id=evaluation.autorizado_id,
            unidad_referencia=context.unit_reference,
            operacion_tipo=operacion_tipo,
            operacion_referencia=operacion_referencia,
            evento_temporal_tipo="EVALUACION",
            evento_temporal_utc=context.occurred_at,
            importe_base=importe_base,
            importe_beneficio=importe_beneficio,
            moneda_codigo=moneda_codigo,
            evaluacion={"applicable": decision.applicable, "reason": decision.reason, "benefit_id": decision.benefit_id},
            applied_by_referencia=applied_by_referencia,
        ))
