"""Canonical SQL RBAC boundary for private worktree diagnostics."""
from pathlib import Path

import pytest
from fastapi import HTTPException

from modules.worker_ingress import routes, service

ROOT = Path(__file__).resolve().parents[2]


def test_get_worktree_route_has_canonical_explicit_rbac_dependency():
    from fastapi.routing import APIRoute
    endpoints = [
        route for route in routes.router.routes
        if isinstance(route, APIRoute)
        and route.path == "/internal/worker/worktree-diagnostic"
    ]
    assert len(endpoints) == 1
    route = endpoints[0]
    assert "GET" in route.methods
    assert any(
        dependency.call is routes.WORKER_ADMIN_DEPENDENCY
        for dependency in route.dependant.dependencies
    )
    assert 'require_explicit_permission("RBAC_ADMIN")' in (
        (ROOT / "backend/modules/worker_ingress/routes.py").read_text()
    )


def test_private_result_reads_only_canonical_snapshot(monkeypatch):
    import tools.mirror_sync.runtime_health_publisher as health
    monkeypatch.setattr(health, "read_private_worktree_snapshot", lambda: {
        "schema": "edarsahub.worker-worktree-evidence.v1",
        "generated_at_utc": "2026-11-10T00:00:00Z",
        "staged": ["src/one.py"],
        "unstaged": ["src/two.py"],
        "untracked": ["src/three.py"],
        "renamed_from": [],
        "platform_managed_exception_applied": False,
    })
    result = service.get_shared_worktree_diagnostic()
    assert result["mode"] == "READ_ONLY"
    assert result["state"] == "DIRTY"
    assert result["production_touched"] is False
    assert result["staged"] == ["src/one.py"]


def test_unavailable_private_evidence_is_sanitized(monkeypatch):
    import tools.mirror_sync.runtime_health_publisher as health
    def fail():
        raise RuntimeError("PRIVATE_PATH=/root/.ssh/id_rsa")
    monkeypatch.setattr(health, "read_private_worktree_snapshot", fail)
    with pytest.raises(service.WorkerIngressError, match="WORKTREE_DIAGNOSTIC_UNAVAILABLE") as exc:
        service.get_shared_worktree_diagnostic()
    assert "/root/.ssh/id_rsa" not in str(exc.value)


def test_route_does_not_fall_back_to_public_health(monkeypatch):
    monkeypatch.setattr(routes, "get_shared_worktree_diagnostic",
                        lambda: (_ for _ in ()).throw(service.WorkerIngressError("WORKTREE_DIAGNOSTIC_UNAVAILABLE")))
    with pytest.raises(HTTPException) as exc:
        routes.read_shared_worktree_diagnostic(current_user={"email": "admin@example.com"})
    assert exc.value.status_code == 503
    assert exc.value.detail == "WORKTREE_DIAGNOSTIC_UNAVAILABLE"
