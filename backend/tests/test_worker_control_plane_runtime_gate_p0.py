from __future__ import annotations

import pytest

from modules.worker_ingress import service


def _admin():
    return {
        "email": "admin@example.invalid",
        "role": "superadmin",
        "permissions": ["worker:submit", "worker:status"],
    }


def _mutation_request():
    return {
        "objective": "P0 runtime convergence guard regression",
        "bounded_context": "WORKER_CONTROL_PLANE",
        "mode": "MUTATION",
        "capability": "DEVELOPMENT_MUTATION_BOUNDED",
        "request_key": "P0-RUNTIME-GUARD-TEST",
        "constraints": {
            "change_spec": [
                {
                    "operation": "write_file",
                    "path": "backend/tests/_p0_runtime_guard_target.py",
                    "content": "VALUE = 1\n",
                }
            ]
        },
    }


def test_mutation_preflight_fails_closed_when_runtime_not_converged(monkeypatch):
    from tools.mirror_sync import worker_runtime_fingerprint as fp

    monkeypatch.setattr(
        fp,
        "build_mcp_runtime_convergence_report",
        lambda: {
            "overall_converged": False,
            "recommended_action": "RECOVER_PREVIEW_RUNTIME",
            "production_touched": False,
        },
    )

    result = service.preflight_semantic_objective(
        _mutation_request(),
        current_user=_admin(),
        enforce_runtime_convergence=True,
    )

    assert result["ok"] is False
    assert result["status"] == "PREFLIGHT_REJECTED"
    assert result["error_code"] == "RUNTIME_NOT_CONVERGED"
    assert result["classification"] == "RUNTIME_DRIFT_ERROR"
    assert result["rejected_field"] == "runtime_convergence"
    assert result["http_status"] == 409


def test_mutation_submission_never_reaches_publisher_when_runtime_stale(monkeypatch):
    from tools.mirror_sync import worker_runtime_fingerprint as fp

    monkeypatch.setattr(
        fp,
        "build_mcp_runtime_convergence_report",
        lambda: {
            "overall_converged": False,
            "recommended_action": "RECOVER_PREVIEW_RUNTIME",
            "production_touched": False,
        },
    )

    published = {"called": False}

    def _forbidden_publish(_job):
        published["called"] = True
        raise AssertionError("publisher must not be called")

    monkeypatch.setattr(service, "_submit_through_canonical_publisher", _forbidden_publish)

    with pytest.raises(service.WorkerIngressError, match="RUNTIME_NOT_CONVERGED"):
        service.submit_objective(
            _mutation_request(),
            current_user=_admin(),
        )

    assert published["called"] is False


def test_read_only_preflight_does_not_require_runtime_convergence(monkeypatch):
    from tools.mirror_sync import worker_runtime_fingerprint as fp

    def _must_not_run():
        raise AssertionError("READ_ONLY must not invoke mutation runtime gate")

    monkeypatch.setattr(fp, "build_mcp_runtime_convergence_report", _must_not_run)

    result = service.preflight_semantic_objective(
        {
            "objective": "READ_ONLY remains available for diagnosis",
            "bounded_context": "WORKER_CONTROL_PLANE",
            "mode": "READ_ONLY",
            "capability": "READ_ONLY_CANARY",
            "constraints": {},
        },
        current_user=_admin(),
        enforce_runtime_convergence=True,
    )

    assert result["ok"] is True
    assert result["production_touched"] is False
