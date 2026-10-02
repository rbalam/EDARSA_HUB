from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_audit_is_deterministic_and_structured(tmp_path):
    helper = _load("repo_contract_audit", "tools/mirror_sync/repository_contract_audit.py")
    module = tmp_path / "backend" / "modules" / "logistics_demo"
    module.mkdir(parents=True)
    (module / "router.py").write_text(
        "from core.sql_first.db import readonly_sql_connection\n@router.get('/fleet')\ndef fleet():\n    return 'dbo.Inventario_Almacenes'\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("SECRET=must-not-leak", encoding="utf-8")
    request = {
        "paths": ["backend"],
        "search_terms": ["fleet", "Inventario_Almacenes"],
        "include_patterns": ["*.py"],
        "exclude_patterns": [],
        "max_results": 50,
    }
    first = helper.scan_repository(tmp_path, request)
    second = helper.scan_repository(tmp_path, request)
    assert first == second
    assert first["status"] == "PASS"
    assert first["mode"] == "READ_ONLY_REPOSITORY"
    assert first["evidence"][0]["candidate_ownership"] == "backend.modules.logistics_demo"
    assert "Inventario_Almacenes" in first["evidence"][0]["tables_referenced"]
    assert "readonly_sql_connection" in first["evidence"][0]["connections"]


def test_repository_audit_rejects_path_escape():
    helper = _load("repo_contract_audit_escape", "tools/mirror_sync/repository_contract_audit.py")
    try:
        helper.validate_request({"paths": ["../"], "search_terms": ["x"]})
    except ValueError as exc:
        assert str(exc) == "INVALID_PATH"
    else:
        raise AssertionError("path escape accepted")


def test_bridge_accepts_repository_audit_only_inside_read_only():
    bridge = _load("worker_bridge_repo_audit", "tools/mirror_sync/universal_job_bridge.py")
    job = {
        "schema": "edarsahub.worker-job.v2",
        "job_id": "repo-audit-test-v1",
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "production_allowed": False,
        "mode": "READ_ONLY",
        "objective": "test",
        "human_summary_language": "es",
        "requester": {"email": "worker-test@edarsahub.local", "source": "pytest"},
        "actions": [],
        "checks": [{"type": "repository_contract_audit", "request": {"paths": ["backend"], "search_terms": ["inventario"], "include_patterns": ["*.py"], "exclude_patterns": [], "max_results": 100}}],
    }
    assert bridge.validate(job) == []


def test_publisher_certifies_repository_evidence():
    publisher = _load("worker_publisher_repo_audit", "tools/mirror_sync/universal_job_result_publisher.py")
    result = {
        "status": "READ_ONLY_COMPLETE",
        "tests": "PASS",
        "quality_gate": "PASS",
        "production_touched": False,
        "blockers": [],
        "checks": [{"type": "repository_contract_audit", "status": "PASS", "repository_evidence": {"status": "PASS", "mode": "READ_ONLY_REPOSITORY", "summary": {"matched_files": 1}, "truncated": False, "evidence": [{"path": "backend/modules/x/router.py", "matched_terms": ["fleet"], "candidate_ownership": "backend.modules.x", "symbols": ["fleet"], "imports": [], "routes": ["/fleet"], "tables_referenced": ["Inventario_Almacenes"], "helpers": [], "connections": [], "rbac_contracts": [], "scheduler_contracts": [], "integrations": []}]}}],
    }
    evidence = publisher.certification_evidence(result)
    assert evidence["certification"] == "CERTIFIED_READ_ONLY"
    assert evidence["certification_basis"] == "READ_ONLY_REPOSITORY_PASS_PLUS_SANITIZED_EVIDENCE"
    public = publisher.sanitize(result)
    assert public["repository_contract_evidence"]["checks"][0]["evidence"][0]["path"] == "backend/modules/x/router.py"
