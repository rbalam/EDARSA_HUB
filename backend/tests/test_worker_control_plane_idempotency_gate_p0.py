from __future__ import annotations

import copy

import pytest

from modules.worker_ingress import service


def _admin():
    return {
        "email": "admin@example.invalid",
        "role": "superadmin",
        "permissions": ["worker:submit", "worker:status"],
    }


def _request(objective: str = "Gate2 original"):
    return {
        "objective": objective,
        "bounded_context": "WORKER_CONTROL_PLANE",
        "mode": "READ_ONLY",
        "capability": "READ_ONLY_CANARY",
        "request_key": "P0-GATE2-STABLE-REQUEST-KEY",
        "constraints": {},
    }


def test_request_key_owns_stable_semantic_identity_across_payload_drift():
    first = service._semantic_job_id(
        _request("original"),
        requester_email="admin@example.invalid",
    )
    changed = service._semantic_job_id(
        _request("changed objective"),
        requester_email="admin@example.invalid",
    )
    other = service._semantic_job_id(
        {**_request("changed objective"), "request_key": "OTHER-KEY"},
        requester_email="admin@example.invalid",
    )

    assert first == changed
    assert first.startswith("SEM-REQUEST-")
    assert first != other


def test_same_request_key_same_payload_returns_exists(monkeypatch):
    req = _request()
    canonical = service.build_semantic_job(req, current_user=_admin())

    monkeypatch.setattr(
        service,
        "_find_existing_job_state",
        lambda job_id: "REMOTE_PENDING" if job_id == canonical["job_id"] else None,
    )
    monkeypatch.setattr(
        service,
        "_read_existing_request_job",
        lambda job_id: copy.deepcopy(canonical),
    )

    result = service.preflight_semantic_objective(
        req,
        current_user=_admin(),
    )

    assert result["ok"] is True
    assert result["status"] == "EXISTS"
    assert result["job_id"] == canonical["job_id"]
    assert result["duplicate_prevented"] is True


def test_same_request_key_different_payload_fails_closed(monkeypatch):
    original_req = _request("original")
    changed_req = _request("changed")
    original_job = service.build_semantic_job(original_req, current_user=_admin())
    changed_job = service.build_semantic_job(changed_req, current_user=_admin())

    assert original_job["job_id"] == changed_job["job_id"]

    monkeypatch.setattr(
        service,
        "_find_existing_job_state",
        lambda job_id: "REMOTE_PENDING" if job_id == original_job["job_id"] else None,
    )
    monkeypatch.setattr(
        service,
        "_read_existing_request_job",
        lambda job_id: copy.deepcopy(original_job),
    )

    result = service.preflight_semantic_objective(
        changed_req,
        current_user=_admin(),
    )

    assert result["ok"] is False
    assert result["status"] == "PREFLIGHT_REJECTED"
    assert result["error_code"] == "IDEMPOTENCY_CONFLICT"
    assert result["classification"] == "IDEMPOTENCY_CONFLICT"
    assert result["rejected_field"] == "request_key"
    assert result["http_status"] == 409


def test_submit_conflict_never_reaches_publisher(monkeypatch):
    original_req = _request("original")
    changed_req = _request("changed")
    original_job = service.build_semantic_job(original_req, current_user=_admin())

    monkeypatch.setattr(
        service,
        "_find_existing_job_state",
        lambda job_id: "REMOTE_PENDING" if job_id == original_job["job_id"] else None,
    )
    monkeypatch.setattr(
        service,
        "_read_existing_request_job",
        lambda job_id: copy.deepcopy(original_job),
    )

    published = {"called": False}

    def _forbidden_publish(_job):
        published["called"] = True
        raise AssertionError("publisher must not be called on idempotency conflict")

    monkeypatch.setattr(service, "_submit_through_canonical_publisher", _forbidden_publish)

    with pytest.raises(service.WorkerIngressError, match="IDEMPOTENCY_CONFLICT"):
        service.submit_objective(
            changed_req,
            current_user=_admin(),
        )

    assert published["called"] is False


def test_exact_legacy_retry_resolves_existing_legacy_job(monkeypatch):
    req = _request("legacy exact payload")
    legacy_id = service._legacy_semantic_job_id(
        req,
        requester_email="admin@example.invalid",
    )
    stable = service.build_semantic_job(req, current_user=_admin())
    legacy_job = dict(stable)
    legacy_job["job_id"] = legacy_id

    def _state(job_id):
        if job_id == stable["job_id"]:
            return None
        if job_id == legacy_id:
            return "REMOTE_RESULT"
        return None

    monkeypatch.setattr(service, "_find_existing_job_state", _state)
    monkeypatch.setattr(
        service,
        "_read_existing_request_job",
        lambda job_id: copy.deepcopy(legacy_job) if job_id == legacy_id else None,
    )

    result = service.preflight_semantic_objective(
        req,
        current_user=_admin(),
    )

    assert result["ok"] is True
    assert result["status"] == "EXISTS"
    assert result["job_id"] == legacy_id
    assert result["existing_lifecycle"] == "REMOTE_RESULT"
