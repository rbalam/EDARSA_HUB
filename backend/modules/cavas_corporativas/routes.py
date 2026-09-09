"""API backend de Cavas Corporativas.

Expone el dominio B2B sin mezclarlo con las rutas de Cavas Personales. El RBAC
reutiliza permisos SQL canonicos existentes certificados por Gate 5 R2; no crea
un catalogo paralelo ni permite bypass legacy de ADMIN.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.rbac.middleware import require_explicit_permission_dual
from .domain import EvaluationContext
from .service import BenefitEvaluation, CavasCorporativasService

router = APIRouter(prefix="/cavas/corporativas", tags=["Cavas Corporativas"])

# R2 certifico que no existe namespace cavas_corporativas en Usuario_Modulos.
# Reutilizamos permisos efectivos ya existentes en el dominio Cavas, sin sembrar
# ni duplicar RBAC. La API corporativa permanece separada funcionalmente.
CAN_EVALUATE = require_explicit_permission_dual("cava_socios.VER")
CAN_APPLY = require_explicit_permission_dual("cava_socios.consumos.CREAR")


class EvaluateRequest(BaseModel):
    identidad_fuente: str = Field(min_length=1, max_length=50)
    identidad_referencia: str = Field(min_length=1, max_length=150)
    occurred_at: datetime
    unit_reference: str = Field(min_length=1, max_length=100)
    sales_line_reference: Optional[str] = None
    category_reference: Optional[str] = None
    family_reference: Optional[str] = None
    sku_reference: Optional[str] = None
    has_reservation: bool = False
    guest_count: Optional[int] = Field(default=None, ge=0)


class ApplyRequest(EvaluateRequest):
    benefit_id: str = Field(min_length=1, max_length=36)
    operacion_tipo: str = Field(min_length=1, max_length=30)
    operacion_referencia: str = Field(min_length=1, max_length=150)
    importe_base: Optional[Decimal] = None
    importe_beneficio: Optional[Decimal] = None
    moneda_codigo: Optional[str] = Field(default=None, min_length=3, max_length=3)


def get_cavas_corporativas_service() -> CavasCorporativasService:
    return CavasCorporativasService()


def _context(payload: EvaluateRequest) -> EvaluationContext:
    return EvaluationContext(
        occurred_at=payload.occurred_at,
        unit_reference=payload.unit_reference,
        authorized_user=False,
        sales_line_reference=payload.sales_line_reference,
        category_reference=payload.category_reference,
        family_reference=payload.family_reference,
        sku_reference=payload.sku_reference,
        has_reservation=payload.has_reservation,
        guest_count=payload.guest_count,
    )


def _serialize_evaluation(evaluation: BenefitEvaluation) -> dict:
    return {
        "convenio_id": evaluation.convenio_id,
        "autorizado_id": evaluation.autorizado_id,
        "decisions": [
            {
                "benefit_id": item.benefit_id,
                "applicable": item.applicable,
                "reason": item.reason,
            }
            for item in evaluation.decisions
        ],
    }


@router.post("/evaluar")
def evaluate_corporate_benefits(
    payload: EvaluateRequest,
    _rbac: dict = Depends(CAN_EVALUATE),
    service: CavasCorporativasService = Depends(get_cavas_corporativas_service),
):
    evaluation = service.evaluate_for_identity(
        payload.identidad_fuente, payload.identidad_referencia, _context(payload)
    )
    return _serialize_evaluation(evaluation)


@router.post("/aplicar")
def apply_corporate_benefit(
    payload: ApplyRequest,
    current_user: dict = Depends(CAN_APPLY),
    service: CavasCorporativasService = Depends(get_cavas_corporativas_service),
):
    context = _context(payload)
    evaluation = service.evaluate_for_identity(
        payload.identidad_fuente, payload.identidad_referencia, context
    )
    if evaluation.convenio_id is None:
        raise HTTPException(status_code=403, detail="CORPORATE_IDENTITY_NOT_AUTHORIZED")
    try:
        inserted = service.record_applied_benefit(
            evaluation=evaluation,
            benefit_id=payload.benefit_id,
            context=context,
            operacion_tipo=payload.operacion_tipo,
            operacion_referencia=payload.operacion_referencia,
            importe_base=payload.importe_base,
            importe_beneficio=payload.importe_beneficio,
            moneda_codigo=payload.moneda_codigo,
            applied_by_referencia=current_user.get("email") or current_user.get("id"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "inserted": inserted,
        "idempotent_replay": not inserted,
        "benefit_id": payload.benefit_id,
        "convenio_id": evaluation.convenio_id,
    }
