# E3D_AUTHORIZED_ACTION_BRIDGE_SERVICE_V1

from __future__ import annotations

from datetime import datetime
import hashlib
from typing import Mapping

from core.agent_capability_policy import BudgetRequest, PolicyContext, PolicyRequest
from core.agent_execution_gate import authorize_internal_capability_execution
from core.agent_procedure_policy import ProcedureSpec, evaluate_procedure
from modules.agent_harness.transversal_capability_registry import CapabilityRegistryError, get_domain_capability

from .action_bridge_contracts import AuthorizedActionDecision, AuthorizedActionRequest
from .recommendation_contracts import ExecutiveRecommendation


def _unique(values):
    return tuple(dict.fromkeys(value for value in values if value))


def _parse_time(value: str):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo is not None else None


def _audit_ref(request: AuthorizedActionRequest) -> str:
    payload = "|".join((request.recommendation_id, request.action_type, request.target_ref, request.requested_by)).encode("utf-8")
    return "bos-action:" + hashlib.sha256(payload).hexdigest()[:20]


def _requester_reasons(required_permission: str, authorization: Mapping[str, object]) -> tuple[str, ...]:
    if not isinstance(authorization, Mapping) or authorization.get("allowed") is not True:
        return ("REQUESTER_RBAC_DENIED",)
    raw = authorization.get("permissions")
    if raw is None:
        raw = (authorization.get("permission"),)
    elif isinstance(raw, str):
        raw = (raw,)
    permissions = {str(item or "").strip().upper() for item in raw}
    if required_permission.upper() not in permissions:
        return ("REQUESTER_PERMISSION_MISMATCH",)
    return ()


def _deny(request: AuthorizedActionRequest, reasons, *, capability=None, procedure=None, required_permission=None) -> AuthorizedActionDecision:
    return AuthorizedActionDecision(
        allowed=False,
        reasons=_unique(tuple(reasons)),
        recommendation_id=request.recommendation_id,
        action_type=request.action_type,
        target_ref=request.target_ref,
        capability=capability,
        procedure=procedure,
        required_permission=required_permission,
        execution_channel=None,
        idempotency_key=request.idempotency_key,
        audit_ref=_audit_ref(request),
        outcome_status="DENIED",
    )


def _precondition_reasons(
    recommendation: ExecutiveRecommendation,
    request: AuthorizedActionRequest,
    spec,
) -> tuple[str, ...]:
    reasons = []
    if request.recommendation_id != recommendation.recommendation_id:
        reasons.append("RECOMMENDATION_ID_MISMATCH")
    if request.action_type not in recommendation.eligible_actions:
        reasons.append("ACTION_NOT_ELIGIBLE")
    if not str(request.target_ref or "").strip():
        reasons.append("TARGET_REF_REQUIRED")
    if not str(request.requested_by or "").strip():
        reasons.append("REQUESTED_BY_REQUIRED")
    if not request.acting_scopes:
        reasons.append("ACTING_SCOPE_REQUIRED")

    generated_at = _parse_time(recommendation.generated_at)
    valid_until = _parse_time(recommendation.valid_until)
    evaluated_at = _parse_time(request.evaluated_at)
    if generated_at is None or valid_until is None or evaluated_at is None:
        reasons.append("RECOMMENDATION_TIME_INVALID")
    else:
        if evaluated_at < generated_at:
            reasons.append("RECOMMENDATION_NOT_YET_VALID")
        if evaluated_at >= valid_until:
            reasons.append("RECOMMENDATION_EXPIRED")

    if recommendation.human_confirmation_required and not request.confirmation_granted:
        reasons.append("HUMAN_CONFIRMATION_REQUIRED")
    if spec.required_permission not in recommendation.required_permissions:
        reasons.append("RECOMMENDATION_PERMISSION_CONTRACT_MISSING")
    if spec.side_effect and not str(request.idempotency_key or "").strip():
        reasons.append("IDEMPOTENCY_KEY_REQUIRED")
    if spec.side_effect and spec.approval_required and not request.confirmation_granted:
        reasons.append("CAPABILITY_APPROVAL_REQUIRED")
    if spec.side_effect and spec.domain == "FINANZAS" and not request.financial_gate_approved:
        reasons.append("FINANCIAL_GATE_REQUIRED")
    return _unique(tuple(reasons))


def authorize_recommended_action(
    recommendation: ExecutiveRecommendation,
    request: AuthorizedActionRequest,
    requester_authorization: Mapping[str, object],
    context: PolicyContext,
) -> AuthorizedActionDecision:
    try:
        spec = get_domain_capability(request.action_type)
    except CapabilityRegistryError:
        return _deny(request, ("CAPABILITY_NOT_REGISTERED",))

    reasons = list(_precondition_reasons(recommendation, request, spec))
    reasons.extend(_requester_reasons(spec.required_permission, requester_authorization))
    if reasons:
        return _deny(
            request,
            reasons,
            capability=spec.code,
            procedure=spec.procedure,
            required_permission=spec.required_permission,
        )

    policy_request = PolicyRequest(
        capabilities=frozenset({spec.code}),
        scopes=frozenset(request.acting_scopes),
        risk=spec.risk,
        data_classification=spec.data_classification,
        budgets=BudgetRequest(),
        external_egress=False,
        production_allowed=False,
        privilege_expansion=False,
        approval_granted=request.policy_approval_granted,
        procedure=spec.procedure,
    )
    procedure_spec = ProcedureSpec(
        name=spec.procedure,
        required_capabilities=frozenset({spec.code}),
        max_risk=spec.risk,
        external_egress_allowed=False,
    )
    procedure_decision = evaluate_procedure(procedure_spec, policy_request, context)
    execution_gate = authorize_internal_capability_execution(
        requester_authorization,
        policy_request,
        context,
    )
    reasons = _unique(procedure_decision.reasons + execution_gate.reasons)
    if not procedure_decision.allowed or not execution_gate.allowed or reasons:
        return _deny(
            request,
            reasons or ("POLICY_DENIED",),
            capability=spec.code,
            procedure=spec.procedure,
            required_permission=spec.required_permission,
        )

    return AuthorizedActionDecision(
        allowed=True,
        reasons=(),
        recommendation_id=request.recommendation_id,
        action_type=request.action_type,
        target_ref=request.target_ref,
        capability=spec.code,
        procedure=spec.procedure,
        required_permission=spec.required_permission,
        execution_channel="AGENT_HARNESS",
        idempotency_key=request.idempotency_key,
        audit_ref=_audit_ref(request),
        outcome_status="AUTHORIZED_NOT_EXECUTED",
    )
