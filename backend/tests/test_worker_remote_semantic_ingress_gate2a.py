from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from modules.worker_ingress import service
from modules.worker_ingress.schemas import WorkerObjectiveRequest
from modules.worker_ingress.semantic_capabilities import registered_capabilities


ROOT = Path(__file__).resolve().parents[2]
ROUTES = (ROOT / "backend/modules/worker_ingress/routes.py").read_text(encoding="utf-8")


def _user():
    return {
        "id": "1",
        "email": "admin@example.com",
        "role": "SuperAdministrador",
    }


def _objective(**overrides):
    payload = {
        "objective": "Certificar la capa semantica global.",
        "bounded_context": "WORKER_INGRESS",
        "mode": "READ_ONLY",
        "capability": "READ_ONLY_CANARY",
        "constraints": {},
    }
    payload.update(overrides)
    return payload


def test_semantic_schema_rejects_raw_worker_language():
    bad = {
        **_objective(),
        "actions": [{"type": "write_file"}],
        "checks": [{"type": "git_diff_check"}],
        "requester": {"email": "other@example.com"},
        "production_allowed": True,
    }
    with pytest.raises(ValidationError):
        WorkerObjectiveRequest.model_validate(bad)


def test_read_only_canary_capability_is_registered():
    assert "READ_ONLY_CANARY" in registered_capabilities()


def test_unknown_capability_fails_closed():
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_CAPABILITY_UNKNOWN"):
        service.build_semantic_job(
            _objective(capability="UNKNOWN"),
            current_user=_user(),
        )


def test_capability_mode_mismatch_fails_closed():
    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_CAPABILITY_MODE_MISMATCH",
    ):
        service.build_semantic_job(
            _objective(mode="MUTATION"),
            current_user=_user(),
        )


def test_semantic_expansion_builds_internal_worker_contract():
    job = service.build_semantic_job(
        _objective(),
        current_user=_user(),
    )
    assert job["mode"] == "READ_ONLY"
    assert job["actions"] == []
    assert job["checks"] == [{"type": "git_diff_check"}]
    assert job["production_allowed"] is False
    assert job["requester"]["email"] == "admin@example.com"
    assert job["scheduling"]["bounded_context"] == "WORKER_INGRESS"


def test_semantic_job_id_is_deterministic_and_requester_bound():
    first = service.build_semantic_job(_objective(), current_user=_user())
    second = service.build_semantic_job(_objective(), current_user=_user())
    assert first["job_id"] == second["job_id"]

    other = service.build_semantic_job(
        _objective(),
        current_user={**_user(), "email": "other@example.com"},
    )
    assert other["job_id"] != first["job_id"]


def test_request_key_changes_idempotency_identity():
    first = service.build_semantic_job(
        _objective(request_key="run-001"),
        current_user=_user(),
    )
    second = service.build_semantic_job(
        _objective(request_key="run-002"),
        current_user=_user(),
    )
    assert first["job_id"] != second["job_id"]


def test_constraints_are_capability_owned_and_fail_closed():
    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_CONSTRAINTS_UNSUPPORTED",
    ):
        service.build_semantic_job(
            _objective(constraints={"raw_sql": "SELECT 1"}),
            current_user=_user(),
        )


def test_submit_objective_reuses_canonical_publisher(monkeypatch):
    captured = {}

    def fake_submit(job):
        captured["job"] = job
        return {
            "status": "SUBMITTED",
            "job_id": job["job_id"],
            "production_touched": False,
        }

    monkeypatch.setattr(service.gate_chain_publisher, "submit", fake_submit)
    result = service.submit_objective(
        _objective(),
        current_user=_user(),
    )

    assert result["status"] == "SUBMITTED"
    assert result["capability"] == "READ_ONLY_CANARY"
    assert captured["job"]["production_allowed"] is False


def test_objective_route_is_exposed_and_jobs_route_remains_internal():
    assert '@router.post("/objectives"' in ROUTES
    assert '@router.post("/jobs"' in ROUTES
    assert '@router.get("/jobs/{job_id}")' in ROUTES
