"""Static contract checks for Worker Console phase 2 proposal (PR #100)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = (ROOT / "frontend/src/pages/WorkerConsole.jsx").read_text(encoding="utf-8")
INGRESS = (ROOT / "backend/modules/worker_ingress/service.py").read_text(encoding="utf-8")
ROUTES = (ROOT / "backend/modules/worker_ingress/routes.py").read_text(encoding="utf-8")


def test_phase2_ui_uses_only_canonical_ingress():
    assert 'const INGRESS = `${API}/api/internal/worker`;' in FRONTEND
    assert 'request("/jobs", { method: "POST"' in FRONTEND
    assert 'request(`/jobs/${encodeURIComponent(result.job_id)}`)' in FRONTEND
    assert "worker_queue/inbox" not in FRONTEND
    assert "worker/requests" not in FRONTEND


def test_phase2_ui_limits_first_release_to_readonly():
    assert 'mode: "READ_ONLY"' in FRONTEND
    assert "actions: []" in FRONTEND
    assert "production_allowed: true" not in FRONTEND
    assert 'schema: "edarsahub.worker-job.v2"' in FRONTEND
    assert "window.confirm" in FRONTEND


def test_server_keeps_permission_and_canonical_publisher():
    assert 'require_explicit_permission("RBAC_ADMIN")' in ROUTES
    assert "gate_chain_publisher.submit(canonical_job)" in INGRESS
    assert "production_allowed" not in FRONTEND
