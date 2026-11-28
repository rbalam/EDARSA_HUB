"""Bounded, fail-closed SEC_RBAC Gate 1B SQL audit capability."""
import pytest

from modules.integrations_runtime.read_only_sql import validate_readonly_sql
from modules.worker_ingress import service
from modules.worker_ingress.semantic_capabilities import capability_catalog
from tools.mirror_sync.gate_chain_publisher import validate_template

USER = {"id": "1", "email": "test-admin@example.invalid", "role": "SuperAdministrador"}


def req(**changes):
    p = {
        "objective": "Auditar permisos SQL Seguridad RBAC sin modificaciones.",
        "bounded_context": "SEC_RBAC",
        "capability": "SEC_RBAC_SQL_PERMISSION_MATRIX_READONLY",
        "mode": "READ_ONLY_SQL",
        "constraints": {},
    }
    p.update(changes)
    return p


def test_gate1b_validated_envelope():
    job = service.build_semantic_job(req(), current_user=USER)
    assert validate_template(job)["schema"] == "edarsahub.worker-job.v2"
    assert job["mode"] == "READ_ONLY_SQL"
    assert job["actions"] == []
    assert job["production_allowed"] is False
    assert job["checks"][0]["source"] == "EDARSAHUB"
    assert job["checks"][0]["type"] == "sql_readonly_audit"
    assert len(job["checks"][0]["queries"]) == 3


def test_gate1b_sql_is_sealed_and_select_only():
    queries = service.build_semantic_job(req(), current_user=USER)["checks"][0]["queries"]
    for query in queries:
        sql = query["sql"]
        assert sql.startswith("SELECT ")
        assert validate_readonly_sql(sql) == sql
        assert not any(token in sql.lower() for token in (
            "email", "password", "api_key", "jwt_secret", "refresh_token"
        ))


@pytest.mark.parametrize("changes", [
    {"mode": "MUTATION"}, {"mode": "READ_ONLY"},
])
def test_gate1b_rejects_mode_changes(changes):
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_CAPABILITY_MODE_MISMATCH"):
        service.build_semantic_job(req(**changes), current_user=USER)


@pytest.mark.parametrize("changes", [
    {"bounded_context": "OTHER"},
    {"constraints": {"paths": ["backend/.env"]}},
    {"constraints": {"queries": [{"name": "a", "sql": "SELECT 1"}]}},
    {"constraints": {"sql": "SELECT 1"}},
    {"constraints": {"user_id": "1"}},
    {"constraints": {"actions": []}},
    {"constraints": {"source": "SERVER"}},
])
def test_gate1b_rejects_external_query_and_selectors(changes):
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_"):
        service.build_semantic_job(req(**changes), current_user=USER)


def test_gate1b_registry_isolated_from_existing_repo_audit():
    catalog = {c["code"]: c for c in capability_catalog()}
    item = catalog["SEC_RBAC_SQL_PERMISSION_MATRIX_READONLY"]
    assert item["modes"] == ["READ_ONLY_SQL"]
    assert item["bounded_context_rule"] == "SEC_RBAC"
    assert item["allowed_constraints"] == []
    assert item["allowed_path_roots"] == []
    assert "backend/core/" in catalog["REPOSITORY_CONTRACT_AUDIT_BOUNDED"]["allowed_path_roots"]


def test_gate1b_submit_goes_through_canonical_publisher(monkeypatch):
    jobs = []
    def submit(job):
        jobs.append(job)
        return {"status": "SUBMITTED", "job_id": job["job_id"], "production_touched": False}
    monkeypatch.setattr(service.gate_chain_publisher, "submit", submit)
    result = service.submit_objective(req(), current_user=USER)
    assert result["status"] == "SUBMITTED"
    assert len(jobs) == 1
    assert jobs[0]["actions"] == []
    assert jobs[0]["mode"] == "READ_ONLY_SQL"
