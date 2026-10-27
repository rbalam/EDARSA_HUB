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
