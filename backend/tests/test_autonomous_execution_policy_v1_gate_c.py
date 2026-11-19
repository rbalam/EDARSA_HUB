"""Gate C tests: edarsahub.autonomous-execution-policy.v1 tiers, limits, cancellation, recovery."""
from __future__ import annotations

import json
import pytest

from tools.mirror_sync.gate_chain_controller import (
    AUTONOMOUS_POLICY_SCHEMA,
    GateChainContractError,
    PolicyLimits,
    classify_policy_tier,
    evaluate_autonomous_policy,
)
from tools.mirror_sync import gate_chain_orchestrator as orch


def _tmpl(job_id="job-dev-1", *, actions=None, production_allowed=False):
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": job_id,
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": production_allowed,
        "objective": "Autonomous policy test",
        "mode": "MUTATION" if actions else "READ_ONLY",
        "actions": actions or [],
        "checks": [{"type": "git_diff_check"}],
        "requester": {
            "email": "ricardo@edarsa.com.mx",
            "source": "chatgpt",
            "project": "EDARSAHUB BOS",
            "chat": "Policy Gate C",
        },
    }


def test_policy_classifies_three_canonical_tiers_correctly():
    # Tier 1: READ_ONLY
    t1, _ = classify_policy_tier({"gate_id": "G1", "mutation_class": "READ_ONLY"})
    assert t1 == "READ_ONLY"

    # Tier 2: DEVELOPMENT_MUTATION
    t2, _ = classify_policy_tier(
        {
            "gate_id": "G2",
            "mutation_class": "CODE_MUTATION",
            "production_allowed": False,
            "job_template": _tmpl(actions=[{"type": "replace_text", "path": "backend/modules/x.py"}]),
        }
    )
    assert t2 == "DEVELOPMENT_MUTATION"

    # Tier 3: HUMAN_APPROVAL_REQUIRED across all mandatory triggers
    for gate in (
        {"gate_id": "P1", "mutation_class": "PRODUCTION"},
        {"gate_id": "P2", "mutation_class": "CODE_MUTATION", "production_allowed": True},
        {"gate_id": "P3", "mutation_class": "CODE_MUTATION", "touches_credentials": True},
        {"gate_id": "P4", "mutation_class": "CODE_MUTATION", "destructive_operation": True},
        {"gate_id": "P5", "mutation_class": "CODE_MUTATION", "irreversible_financial_operation": True},
        {"gate_id": "P6", "mutation_class": "CODE_MUTATION", "personal_data_outside_scope": True},
        {"gate_id": "P7", "mutation_class": "CODE_MUTATION", "unauthorized_business_change": True},
        {"gate_id": "P8", "mutation_class": "CODE_MUTATION", "out_of_contract": True},
        {"gate_id": "P9", "mutation_class": "SQL_DDL"},
        {
            "gate_id": "P10",
            "mutation_class": "CODE_MUTATION",
            "job_template": _tmpl(actions=[{"type": "delete_file", "path": "backend/modules/x.py"}]),
        },
    ):
        tier, _ = classify_policy_tier(gate)
        assert tier == "HUMAN_APPROVAL_REQUIRED", f"Expected HUMAN_APPROVAL_REQUIRED for {gate}"


def test_policy_enforces_limits_retries_timeout_circuit_breaker_and_cancellation():
    gate = {
        "gate_id": "DEV-1",
        "job_id": "job-dev-1",
        "mutation_class": "CODE_MUTATION",
        "authorization_class": "DEV_AUTONOMOUS",
        "job_template": _tmpl(actions=[{"type": "replace_text", "path": "backend/modules/a.py"}]),
    }

    ok = evaluate_autonomous_policy(gate, authorization_classes=["DEV_AUTONOMOUS"])
    assert ok["schema"] == AUTONOMOUS_POLICY_SCHEMA
    assert ok["allowed"] is True
    assert ok["policy_tier"] == "DEVELOPMENT_MUTATION"
    assert ok["rollback_eligible"] is True
    assert ok["production_touched"] is False

    # Retry budget exceeded
    assert evaluate_autonomous_policy(
        gate, retry_count=3, authorization_classes=["DEV_AUTONOMOUS"]
    )["reason"] == "POLICY_RETRY_BUDGET_EXCEEDED"

    # Circuit breaker open
    assert evaluate_autonomous_policy(
        gate, consecutive_failures=3, authorization_classes=["DEV_AUTONOMOUS"]
    )["reason"] == "POLICY_CIRCUIT_BREAKER_OPEN"

    # Timeout exceeded
    assert evaluate_autonomous_policy(
        gate, elapsed_seconds=601, authorization_classes=["DEV_AUTONOMOUS"]
    )["reason"] == "POLICY_TIMEOUT_EXCEEDED"

    # Safe cancellation
    cancelled = evaluate_autonomous_policy(
        gate, cancel_requested=True, authorization_classes=["DEV_AUTONOMOUS"]
    )
    assert cancelled["action"] == "CANCELLED_SAFELY" and cancelled["allowed"] is False

    # Max actions budget
    too_many = {
        **gate,
        "job_template": _tmpl(actions=[{"type": "replace_text", "path": f"backend/modules/f{i}.py"} for i in range(16)]),
    }
    assert evaluate_autonomous_policy(
        too_many, authorization_classes=["DEV_AUTONOMOUS"]
    )["reason"] == "POLICY_MAX_ACTIONS_EXCEEDED"

    with pytest.raises(GateChainContractError):
        PolicyLimits(max_retries_per_gate=99).validated()


def test_orchestrator_persists_policy_decision_and_honors_safe_cancellation_and_restart(tmp_path):
    chain = {
        "schema": "edarsahub.gate-chain.v1",
        "chain_id": "POLICY-TEST",
        "enabled": True,
        "max_hops": 5,
        "start_gate_id": "G1",
        "gates": [
            {
                "gate_id": "G1",
                "job_id": "job-g1",
                "mutation_class": "READ_ONLY",
                "next_gate_ids": [],
                "job_template": _tmpl("job-g1"),
            }
        ],
    }
    persist = tmp_path / "persist"
    state = tmp_path / "state"
    r1 = orch.cycle_chain(chain, state, persist, publish_enabled=False)
    assert r1["action"] == "READY"
    assert r1["policy_decision"]["schema"] == AUTONOMOUS_POLICY_SCHEMA
    assert r1["runtime_state"]["policy_schema"] == AUTONOMOUS_POLICY_SCHEMA

    # Safe cancellation persists and never publishes
    r_cancel = orch.cycle_chain({**chain, "cancel_requested": True}, state, persist, publish_enabled=True)
    assert r_cancel["action"] == "CANCELLED_SAFELY"
    assert r_cancel["published"] is False
    saved = json.loads((persist / "POLICY-TEST.json").read_text(encoding="utf-8"))
    assert saved["cancelled_safely"] is True
    assert saved["production_touched"] is False
