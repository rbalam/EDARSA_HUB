from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.agent_capability_policy import BudgetRequest, PolicyContext, PolicyRequest
from core.agent_execution_gate import ExecutionGateDecision, authorize_internal_capability_execution
from modules.agent_harness.transversal_capability_registry import get_domain_capability


class CRMAdapterError(ValueError):
    pass


@dataclass(frozen=True)
class CRMAgentRequest:
    request_id: str
    empresa_id: int
    unidad_id: int
    capability: str = 'CRM_SUMMARIZE'

    def __post_init__(self) -> None:
        if not str(self.request_id or '').strip():
            raise CRMAdapterError('REQUEST_ID_REQUIRED')
        if self.empresa_id <= 0 or self.unidad_id <= 0:
            raise CRMAdapterError('BUSINESS_SCOPE_INVALID')
        spec = get_domain_capability(self.capability)
        if spec.domain != 'CRM':
            raise CRMAdapterError('CRM_CAPABILITY_REQUIRED')
        if spec.side_effect:
            raise CRMAdapterError('SIDE_EFFECT_CAPABILITY_FORBIDDEN')


def _authorization(req: CRMAgentRequest, auth: Mapping[str, object]) -> dict[str, object]:
    spec = get_domain_capability(req.capability)
    if not isinstance(auth, Mapping) or auth.get('allowed') is not True:
        return {'allowed': False, 'reason': 'REQUESTER_RBAC_DENIED'}
    if str(auth.get('permission') or '').strip().upper() != spec.required_permission:
        return {'allowed': False, 'reason': 'REQUESTER_PERMISSION_MISMATCH'}
    if int(auth.get('empresa_id') or 0) != req.empresa_id or int(auth.get('unidad_id') or 0) != req.unidad_id:
        return {'allowed': False, 'reason': 'REQUESTER_BUSINESS_SCOPE_MISMATCH'}
    return {'allowed': True}


def authorize_crm_agent(req: CRMAgentRequest, requester_authorization: Mapping[str, object], context: PolicyContext) -> tuple[ExecutionGateDecision, PolicyRequest]:
    spec = get_domain_capability(req.capability)
    scopes = frozenset({f'empresa:{req.empresa_id}', f'unidad:{req.unidad_id}', 'domain:crm', 'resource:crm'})
    policy = PolicyRequest(
        capabilities=frozenset({spec.code}), scopes=scopes, risk=spec.risk,
        data_classification=spec.data_classification,
        budgets=BudgetRequest(runtime_seconds=30, sql_rows=500, inference_cost_usd=0.10),
        external_egress=False, production_allowed=False, privilege_expansion=False,
        approval_granted=False, procedure=spec.procedure,
    )
    return authorize_internal_capability_execution(_authorization(req, requester_authorization), policy, context), policy
