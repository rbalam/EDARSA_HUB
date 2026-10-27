# E3D_TESTS_V1

from core.agent_capability_policy import PolicyContext
from modules.bos_executive import (
    AuthorizedActionRequest,
    ConfidenceClass,
    ExecutiveRecommendation,
    RecommendationRisk,
    authorize_recommended_action,
)


def _context(capability="INVENTORY_ANALYZE", scope="empresa:1"):
    capabilities = frozenset({capability})
    scopes = frozenset({scope})
    return PolicyContext(
        user_allowed_capabilities=capabilities,
        agent_allowed_capabilities=capabilities,
        environment_allowed_capabilities=capabilities,
        policy_allowed_capabilities=capabilities,
        user_allowed_scopes=scopes,
        agent_allowed_scopes=scopes,
        environment_allowed_scopes=scopes,
        policy_allowed_scopes=scopes,
        budget_limits={
            "runtime_seconds": 1000,
            "files_changed": 1000,
            "lines_changed": 100000,
            "external_calls": 1000,
            "sql_rows": 100000,
            "inference_cost_usd": 100.0,
        },
    )


def _recommendation(**overrides):
    values = {
        "recommendation_id": "rec:test",
        "recommendation_type": "ADDRESS_PRIORITY",
        "source_ref": "tarea:T-1",
        "title": "Atender prioridad",
        "rationale": "SLA_VENCIDA",
        "evidence_refs": ("workflow:T-1",),
        "expected_impact": "Reducir riesgo operativo",
        "risk_level": RecommendationRisk.MEDIUM,
        "confidence_class": ConfidenceClass.DETERMINISTA,
        "generated_at": "2026-10-27T00:00:00+00:00",
        "valid_until": "2026-10-28T00:00:00+00:00",
        "required_permissions": ("COMPRAS_INVENTARIOS_VER",),
        "eligible_actions": ("INVENTORY_ANALYZE",),
        "human_confirmation_required": True,
        "stale": False,
        "provenance_refs": ("workflow:T-1",),
    }
    values.update(overrides)
    return ExecutiveRecommendation(**values)


def _request(**overrides):
    values = {
        "recommendation_id": "rec:test",
        "action_type": "INVENTORY_ANALYZE",
        "target_ref": "inventory:1",
        "requested_by": "user:1",
        "acting_scopes": ("empresa:1",),
        "evaluated_at": "2026-10-27T12:00:00+00:00",
        "confirmation_granted": True,
        "policy_approval_granted": False,
        "financial_gate_approved": False,
        "idempotency_key": None,
        "dry_run": True,
    }
    values.update(overrides)
    return AuthorizedActionRequest(**values)


def test_e3d_unknown_capability_is_denied():
    decision = authorize_recommended_action(
        _recommendation(eligible_actions=("UNKNOWN_CAPABILITY",)),
        _request(action_type="UNKNOWN_CAPABILITY"),
        {"allowed": True, "permission": "COMPRAS_INVENTARIOS_VER"},
        _context(),
    )
    assert decision.allowed is False
    assert "CAPABILITY_NOT_REGISTERED" in decision.reasons
    assert decision.outcome_status == "DENIED"


def test_e3d_action_must_be_declared_eligible():
    decision = authorize_recommended_action(
        _recommendation(eligible_actions=()),
        _request(),
        {"allowed": True, "permission": "COMPRAS_INVENTARIOS_VER"},
        _context(),
    )
    assert decision.allowed is False
    assert "ACTION_NOT_ELIGIBLE" in decision.reasons


def test_e3d_expired_recommendation_is_denied():
    decision = authorize_recommended_action(
        _recommendation(valid_until="2026-10-27T10:00:00+00:00"),
        _request(evaluated_at="2026-10-27T12:00:00+00:00"),
        {"allowed": True, "permission": "COMPRAS_INVENTARIOS_VER"},
        _context(),
    )
    assert decision.allowed is False
    assert "RECOMMENDATION_EXPIRED" in decision.reasons


def test_e3d_requester_rbac_denied_is_fail_closed():
    decision = authorize_recommended_action(
        _recommendation(),
        _request(),
        {"allowed": False, "reason": "REQUESTER_RBAC_DENIED"},
        _context(),
    )
    assert decision.allowed is False
    assert "REQUESTER_RBAC_DENIED" in decision.reasons


def test_e3d_allowlisted_action_is_authorized_but_not_executed():
    decision = authorize_recommended_action(
        _recommendation(),
        _request(),
        {"allowed": True, "permission": "COMPRAS_INVENTARIOS_VER"},
        _context(),
    )
    assert decision.allowed is True
    assert decision.reasons == ()
    assert decision.capability == "INVENTORY_ANALYZE"
    assert decision.procedure == "inventory-analyze"
    assert decision.required_permission == "COMPRAS_INVENTARIOS_VER"
    assert decision.execution_channel == "AGENT_HARNESS"
    assert decision.outcome_status == "AUTHORIZED_NOT_EXECUTED"
    assert decision.audit_ref.startswith("bos-action:")
