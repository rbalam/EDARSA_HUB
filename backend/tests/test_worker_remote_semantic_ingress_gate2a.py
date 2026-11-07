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


def _repair_objective(**overrides):
    payload = {
        "objective": "Ejecutar una reparacion Worker acotada.",
        "bounded_context": "WORKER_RUNTIME_CONVERGENCE",
        "mode": "MUTATION",
        "capability": "WORKER_REPAIR_BOUNDED",
        "constraints": {
            "incident_id": "WORKER-ABC123",
            "capability_code": "CANONICAL_JOB_INGRESS",
        },
    }
    payload.update(overrides)
    return payload


def test_worker_repair_bounded_capability_is_registered():
    assert "WORKER_REPAIR_BOUNDED" in registered_capabilities()


def test_worker_repair_bounded_rejects_wrong_context():
    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED",
    ):
        service.submit_objective(
            _repair_objective(bounded_context="RH"),
            current_user=_user(),
        )


def test_worker_repair_bounded_rejects_unknown_constraints():
    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_CONSTRAINTS_UNSUPPORTED",
    ):
        service.submit_objective(
            _repair_objective(
                constraints={
                    "incident_id": "WORKER-ABC123",
                    "capability_code": "CANONICAL_JOB_INGRESS",
                    "actions": [{"type": "write_file"}],
                }
            ),
            current_user=_user(),
        )


def test_worker_repair_bounded_rejects_generic_builder_path():
    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_CAPABILITY_DIRECT_SUBMISSION_REQUIRED",
    ):
        service.build_semantic_job(
            _repair_objective(),
            current_user=_user(),
        )


def test_worker_repair_bounded_delegates_to_canonical_planner(monkeypatch):
    from tools.mirror_sync import worker_repair_planner

    captured = {}

    def fake_publish(
        incident_id,
        *,
        capability_code=None,
        problem_signature=None,
        requester=None,
    ):
        captured["incident_id"] = incident_id
        captured["capability_code"] = capability_code
        captured["requester"] = requester
        return {
            "job": {"job_id": "REPAIR-WORKER-ABC123-A1"},
            "publication": {
                "repair_job_id": "REPAIR-WORKER-ABC123-A1",
                "publication_status": "PUBLISHED",
                "production_touched": False,
            },
            "production_touched": False,
        }

    def forbidden_generic_submit(_job):
        raise AssertionError("generic publisher path must not be used directly")

    monkeypatch.setattr(
        worker_repair_planner,
        "publish_planned_repair",
        fake_publish,
    )
    monkeypatch.setattr(
        service.gate_chain_publisher,
        "submit",
        forbidden_generic_submit,
    )

    result = service.submit_objective(
        _repair_objective(),
        current_user=_user(),
    )

    assert result == {
        "status": "SUBMITTED",
        "job_id": "REPAIR-WORKER-ABC123-A1",
        "production_touched": False,
        "capability": "WORKER_REPAIR_BOUNDED",
        "bounded_context": "WORKER_RUNTIME_CONVERGENCE",
    }
    assert captured["incident_id"] == "WORKER-ABC123"
    assert captured["capability_code"] == "CANONICAL_JOB_INGRESS"
    assert captured["requester"]["email"] == "admin@example.com"


def test_worker_repair_bounded_fails_closed_on_production_violation(monkeypatch):
    from tools.mirror_sync import worker_repair_planner

    def unsafe_publish(*_args, **_kwargs):
        return {
            "job": {"job_id": "REPAIR-WORKER-ABC123-A1"},
            "publication": {
                "repair_job_id": "REPAIR-WORKER-ABC123-A1",
                "publication_status": "PUBLISHED",
                "production_touched": False,
            },
            "production_touched": True,
        }

    monkeypatch.setattr(
        worker_repair_planner,
        "publish_planned_repair",
        unsafe_publish,
    )

    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_REPAIR_PRODUCTION_POLICY_VIOLATION",
    ):
        service.submit_objective(
            _repair_objective(),
            current_user=_user(),
        )


def test_worker_repair_bounded_rejects_uncommitted_publication(monkeypatch):
    from tools.mirror_sync import worker_repair_planner

    def not_committed(*_args, **_kwargs):
        return {
            "job": {"job_id": "REPAIR-WORKER-ABC123-A1"},
            "publication": {
                "repair_job_id": "REPAIR-WORKER-ABC123-A1",
                "publication_status": "READY_TO_PUBLISH",
                "production_touched": False,
            },
            "production_touched": False,
        }

    monkeypatch.setattr(
        worker_repair_planner,
        "publish_planned_repair",
        not_committed,
    )

    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_REPAIR_PUBLICATION_NOT_COMMITTED",
    ):
        service.submit_objective(
            _repair_objective(),
            current_user=_user(),
        )

def test_g4_maintenance_history_capability_registered_and_bounded():
    assert "WORKER_MAINTENANCE_HISTORY_READONLY" in registered_capabilities()
    job = service.build_semantic_job(
        _objective(
            bounded_context="WORKER_REPAIR_KNOWLEDGE_LOOP",
            capability="WORKER_MAINTENANCE_HISTORY_READONLY",
            constraints={},
        ),
        current_user=_user(),
    )
    assert job["mode"] == "READ_ONLY"
    assert job["actions"] == []
    assert job["production_allowed"] is False
    assert job["checks"] == [{"type": "worker_maintenance_history_readonly"}]
    assert job["scheduling"]["bounded_context"] == "WORKER_REPAIR_KNOWLEDGE_LOOP"


@pytest.mark.parametrize("override", [
    {"mode": "MUTATION"},
    {"bounded_context": "OTHER_DOMAIN"},
    {"constraints": {"paths": ["/app/.git"]}},
    {"constraints": {"actions": []}},
    {"constraints": {"checks": [{"type": "git_diff_check"}]}},
])
def test_g4_maintenance_history_fails_closed(override):
    payload = _objective(
        bounded_context="WORKER_REPAIR_KNOWLEDGE_LOOP",
        capability="WORKER_MAINTENANCE_HISTORY_READONLY",
        constraints={},
    )
    payload.update(override)
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_"):
        service.build_semantic_job(payload, current_user=_user())


def test_g4_semantic_submission_uses_existing_publisher(monkeypatch):
    captured = {}
    def fake_submit(job):
        captured["job"] = job
        return {"status": "SUBMITTED", "job_id": job["job_id"], "production_touched": False}
    monkeypatch.setattr(service.gate_chain_publisher, "submit", fake_submit)
    payload = _objective(
        bounded_context="WORKER_REPAIR_KNOWLEDGE_LOOP",
        capability="WORKER_MAINTENANCE_HISTORY_READONLY",
        constraints={},
        request_key="g4-maintenance-r1",
    )
    result = service.submit_objective(payload, current_user=_user())
    assert result["status"] == "SUBMITTED"
    assert result["production_touched"] is False
    assert captured["job"]["checks"] == [{"type": "worker_maintenance_history_readonly"}]
    assert captured["job"]["actions"] == []
    assert captured["job"]["requester"]["email"] == _user()["email"]


def test_g4_semantic_schema_rejects_raw_job_fields():
    payload = _objective(
        bounded_context="WORKER_REPAIR_KNOWLEDGE_LOOP",
        capability="WORKER_MAINTENANCE_HISTORY_READONLY",
        constraints={},
    )
    for field, value in (
        ("actions", [{"type": "write_file", "path": "backend/unsafe.py"}]),
        ("checks", [{"type": "git_diff_check"}]),
        ("production_allowed", True),
        ("requester", {"email": "other@example.com"}),
    ):
        with pytest.raises(ValidationError):
            WorkerObjectiveRequest.model_validate({**payload, field: value})
