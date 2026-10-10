from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from modules.worker_ingress import service
from modules.worker_ingress.schemas import WorkerSubmitRequest
from tools.mirror_sync.worker_job_factory import (
    CANONICAL_TARGET_BRANCH,
    CANONICAL_TARGET_REPO,
)


ROOT = Path(__file__).resolve().parents[2]
ROUTES = (ROOT / "backend/modules/worker_ingress/routes.py").read_text(encoding="utf-8")
SERVICE = (ROOT / "backend/modules/worker_ingress/service.py").read_text(encoding="utf-8")
SERVER = (ROOT / "backend/server.py").read_text(encoding="utf-8")


def _payload():
    return {
        "job_id": "REMOTE-INGRESS-G1-TEST",
        "objective": "Canonical ingress contract test.",
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [{"type": "git_diff_check"}],
        "scheduling": {
            "project_id": "TEST",
            "bounded_context": "TEST",
            "resource_claims": [],
            "conflict_domains": ["TEST"],
        },
    }


def test_schema_rejects_transport_and_requester_overrides():
    bad = {
        **_payload(),
        "requester": {"email": "attacker@example.com"},
        "production_allowed": True,
        "target_repo": "other/repo",
    }
    with pytest.raises(ValidationError):
        WorkerSubmitRequest.model_validate(bad)


def test_job_is_canonical_and_requester_comes_from_authenticated_user():
    job = service.build_canonical_job(
        _payload(),
        current_user={
            "id": "1",
            "email": "admin@example.com",
            "role": "SuperAdministrador",
        },
    )
    assert job["target_repo"] == CANONICAL_TARGET_REPO
    assert job["target_branch"] == CANONICAL_TARGET_BRANCH
    assert job["production_allowed"] is False
    assert job["requester"]["email"] == "admin@example.com"
    assert job["requester"]["source"] == "edarsahub-worker-ingress"


def test_sensitive_keys_are_rejected_before_publisher():
    bad = _payload()
    bad["actions"] = [{"type": "noop", "password": "never"}]
    with pytest.raises(service.WorkerIngressError, match="SENSITIVE_FIELD_FORBIDDEN"):
        service.build_canonical_job(
            bad,
            current_user={"email": "admin@example.com"},
        )


def test_submit_reuses_gate_chain_publisher(monkeypatch):
    captured = {}

    def fake_submit(job):
        captured["job"] = job
        return {
            "status": "SUBMITTED",
            "job_id": job["job_id"],
            "production_touched": False,
        }

    monkeypatch.setattr(service.gate_chain_publisher, "submit", fake_submit)

    result = service.submit_job(
        _payload(),
        current_user={"email": "admin@example.com"},
    )
    assert result["status"] == "SUBMITTED"
    assert captured["job"]["production_allowed"] is False


def test_status_reads_canonical_terminal_result(tmp_path, monkeypatch):
    state = tmp_path / "universal-worker-queue"
    results = state / "results"
    results.mkdir(parents=True)
    payload = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "REMOTE-INGRESS-G1-RESULT",
        "status": "READ_ONLY_COMPLETE",
        "quality_gate": "PASS",
        "certification": "CERTIFIED_READ_ONLY",
        "tests": "PASS",
        "percent_complete": 100,
        "blockers": [],
        "production_touched": False,
        "completed_at_utc": "2026-10-05T15:45:00Z",
    }
    (results / "REMOTE-INGRESS-G1-RESULT.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    monkeypatch.setattr(service, "STATE_ROOT", state)

    result = service.get_job_status("REMOTE-INGRESS-G1-RESULT")
    assert result["lifecycle"] == "RESULT"
    assert result["status"] == "READ_ONLY_COMPLETE"
    assert result["production_touched"] is False


def test_routes_use_existing_rbac_and_no_custom_auth_system():
    assert 'require_explicit_permission("RBAC_ADMIN")' in ROUTES
    assert "verify_token" not in ROUTES
    assert "JWT_SECRET" not in ROUTES


def test_ingress_does_not_implement_git_or_shell_transport():
    assert "create_file" not in SERVICE
    assert "subprocess" not in SERVICE
    assert "git push" not in SERVICE
    assert "force push" not in SERVICE.lower()
    assert "gate_chain_publisher.submit" in SERVICE


def test_router_is_mounted_once_under_api():
    marker = 'app.include_router(worker_ingress_router, prefix="/api")'
    assert SERVER.count(marker) == 1


def test_ingress_does_not_extend_wake_endpoint():
    assert "worker_runtime_wake" not in ROUTES
    assert "supervisorctl" not in SERVICE
