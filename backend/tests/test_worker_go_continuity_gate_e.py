"""Gate E tests: Autonomous cross-chat GO continuity resolver without parallel memory."""
from __future__ import annotations

import json
import pytest
from fastapi import HTTPException

from modules.worker_ingress import routes as ingress_routes
from modules.worker_ingress import service


def _admin():
    return {"id": "1", "email": "ricardo@edarsa.com.mx", "role": "SuperAdministrador"}


def _operator():
    return {"id": "2", "email": "op@edarsa.com.mx", "role": "Operador"}


def _certified_result(job_id: str, domain: str):
    return {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": "READ_ONLY_COMPLETE",
        "certification": "CERTIFIED_READ_ONLY",
        "work_completion": "COMPLETE",
        "quality_gate": "PASS",
        "tests": "PASS",
        "percent_complete": 100,
        "completed_at_utc": "2026-11-19T10:00:00Z",
        "blockers": [],
        "production_touched": False,
        "scheduling": {"bounded_context": domain},
    }


def test_resolve_go_context_fails_closed_on_ambiguous_domain_and_unverified_identity(tmp_path, monkeypatch):
    state = tmp_path / ".git" / "universal-worker-queue"
    (state / "results").mkdir(parents=True)
    monkeypatch.setattr(service, "STATE_ROOT", state)

    # Ambiguous domain -> REQUEST_MINIMUM_INFO, mutation_allowed=False
    for bad in ("", "ALL", "GENERAL", "*"):
        res = service.resolve_go_context(domain=bad, current_user=_admin(), config_dir=tmp_path / "chains")
        assert res["mutation_allowed"] is False
        assert res["next_allowed_action"] == "REQUEST_MINIMUM_INFO"
        assert "domain" in res["missing_fields"]

    # Missing objective & no prior gate -> never implicitly authorizes mutation
    empty = service.resolve_go_context(domain="FINANZAS", current_user=_admin(), config_dir=tmp_path / "chains")
    assert empty["mutation_allowed"] is False
    assert empty["next_allowed_action"] == "REQUEST_MINIMUM_INFO"

    # Unverified identity -> HUMAN_APPROVAL_REQUIRED
    unauth = service.resolve_go_context(
        domain="RH",
        current_user={"id": "x"},
        objective_hint="Remediar aislamiento RBAC",
        config_dir=tmp_path / "chains",
    )
    assert unauth["mutation_allowed"] is False
    assert unauth["next_allowed_action"] == "HUMAN_APPROVAL_REQUIRED"

    # Non-admin operator -> READ_ONLY only, never mutation_allowed
    op = service.resolve_go_context(
        domain="RH",
        current_user=_operator(),
        objective_hint="Auditar RH",
        config_dir=tmp_path / "chains",
    )
    assert op["mutation_allowed"] is False
    assert op["policy_tier"] == "READ_ONLY"


def test_resolve_go_context_isolates_domains_and_waits_for_in_flight_jobs(tmp_path, monkeypatch):
    state = tmp_path / ".git" / "universal-worker-queue"
    (state / "results").mkdir(parents=True)
    (state / "pending").mkdir(parents=True)
    monkeypatch.setattr(service, "STATE_ROOT", state)

    # Write certified RH job & certified CRM job
    (state / "results" / "SEM-RH-AUDIT-001.json").write_text(
        json.dumps(_certified_result("SEM-RH-AUDIT-001", "RH")), encoding="utf-8"
    )
    (state / "results" / "SEM-CRM-AUDIT-001.json").write_text(
        json.dumps(_certified_result("SEM-CRM-AUDIT-001", "CRM")), encoding="utf-8"
    )

    rh_ctx = service.resolve_go_context(
        domain="RH",
        current_user=_admin(),
        objective_hint="Continuar remediacion RH-R1",
        config_dir=tmp_path / "chains",
    )
    assert rh_ctx["last_certified_gate"]["job_id"] == "SEM-RH-AUDIT-001"
    assert rh_ctx["next_allowed_action"] == "CONTINUE_AUTONOMOUS"
    assert rh_ctx["mutation_allowed"] is True
    assert rh_ctx["production_touched"] is False

    crm_ctx = service.resolve_go_context(
        domain="CRM",
        current_user=_admin(),
        objective_hint="Continuar CRM",
        config_dir=tmp_path / "chains",
    )
    assert crm_ctx["last_certified_gate"]["job_id"] == "SEM-CRM-AUDIT-001"

    # Adding an in-flight RH job blocks RH mutations with WAIT, without blocking CRM
    (state / "pending" / "EDARSAHUB-BOS-RH-R1-001.json").write_text(
        json.dumps({"job_id": "EDARSAHUB-BOS-RH-R1-001", "scheduling": {"bounded_context": "RH"}}),
        encoding="utf-8",
    )
    rh_wait = service.resolve_go_context(
        domain="RH",
        current_user=_admin(),
        objective_hint="Continuar RH",
        config_dir=tmp_path / "chains",
    )
    assert rh_wait["next_allowed_action"] == "WAIT_FOR_IN_FLIGHT_JOB"
    assert rh_wait["mutation_allowed"] is False
    assert len(rh_wait["pending_jobs"]) == 1

    crm_still_ok = service.resolve_go_context(
        domain="CRM",
        current_user=_admin(),
        objective_hint="Continuar CRM",
        config_dir=tmp_path / "chains",
    )
    assert crm_still_ok["next_allowed_action"] == "CONTINUE_AUTONOMOUS"
    assert crm_still_ok["pending_jobs"] == []


def test_context_route_enforces_rbac_scope(monkeypatch):
    def deny(**kwargs):
        raise ingress_routes.OAuthValidationError("INSUFFICIENT_SCOPE")

    monkeypatch.setattr(ingress_routes, "enforce_internal_jwt_mcp_scope", deny)
    with pytest.raises(HTTPException) as exc_info:
        ingress_routes.read_worker_go_context(
            domain="RH",
            current_user=_operator(),
            authorization="Bearer bad",
        )
    assert exc_info.value.status_code == 403
