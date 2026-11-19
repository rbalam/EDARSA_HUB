"""Gate B tests: MCP/Semantic declarative Development mutation ingress."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from modules.worker_ingress import service
from modules.worker_ingress import semantic_capabilities as sem_caps


def _admin():
    return {
        "id": "1",
        "email": "ricardo@edarsa.com.mx",
        "role": "SuperAdministrador",
    }


def _operator():
    return {
        "id": "2",
        "email": "operador@edarsa.com.mx",
        "role": "Operador",
    }


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_development_mutation_bounded_registered_and_catalogued():
    assert "DEVELOPMENT_MUTATION_BOUNDED" in sem_caps.registered_capabilities()
    catalog = {item["code"]: item for item in sem_caps.capability_catalog()}
    entry = catalog["DEVELOPMENT_MUTATION_BOUNDED"]
    assert entry["modes"] == ["MUTATION"]
    assert "change_spec" in entry["allowed_constraints"]
    assert entry["raw_worker_fields_forbidden"] is True


def test_development_mutation_builds_valid_v2_job_and_publishes_once(tmp_path, monkeypatch):
    # Setup synthetic isolated repo & queue state
    repo = tmp_path / "repo"
    target = repo / "backend" / "modules" / "demo" / "sample.py"
    target.parent.mkdir(parents=True)
    original = "def hello():\n    return 'v1'\n"
    target.write_text(original, encoding="utf-8")

    state_root = tmp_path / ".git" / "universal-worker-queue"
    (state_root / "results").mkdir(parents=True)
    monkeypatch.setattr(sem_caps, "_DEV_REPO_ROOT", repo)
    monkeypatch.setattr(service, "STATE_ROOT", state_root)

    captured = {}

    def fake_submit(job, *, remote="origin", queue_branch="worker/requests", require_convergence=False):
        captured["job"] = job
        captured["remote"] = remote
        captured["queue_branch"] = queue_branch
        captured["require_convergence"] = require_convergence
        return {
            "status": "SUBMITTED",
            "job_id": job["job_id"],
            "production_touched": False,
        }

    monkeypatch.setattr(service.gate_chain_publisher, "submit", fake_submit)

    req = {
        "objective": "Actualizar retorno de saludo en modulo demo.",
        "bounded_context": "CRM",
        "mode": "MUTATION",
        "capability": "DEVELOPMENT_MUTATION_BOUNDED",
        "constraints": {
            "authorization_ref": "GO-CRM-DEMO-20261119",
            "job_id_override": "EDARSAHUB-DEMO-GATE-B-001",
            "change_spec": [
                {
                    "operation": "replace_text",
                    "path": "backend/modules/demo/sample.py",
                    "source_sha256": _sha256(original),
                    "old_text": "return 'v1'",
                    "replacement": "return 'v2'",
                    "expected_occurrences": 1,
                }
            ],
            "verification_tests": ["backend/tests/test_worker_mcp_dev_ingress_gate_b.py"],
        },
    }
    res = service.submit_objective(req, current_user=_admin())
    assert res["status"] == "SUBMITTED"
    assert res["job_id"] == "EDARSAHUB-DEMO-GATE-B-001"
    assert res["production_touched"] is False
    assert captured["remote"] == "origin"
    assert captured["queue_branch"] == "worker/requests"
    assert captured["require_convergence"] is False
    assert captured["job"]["schema"] == "edarsahub.worker-job.v2"
    assert captured["job"]["production_allowed"] is False
    assert captured["job"]["target_branch"] == "Edarsahub_Desarrollo"
    assert captured["job"]["actions"][0]["type"] == "replace_text"
    check_types = [c["type"] for c in captured["job"]["checks"]]
    assert check_types == ["py_compile", "pytest", "git_diff_check"]

    # Duplicate check: once materialized in local queue, second submit returns EXISTS without publishing
    (state_root / "pending").mkdir(parents=True, exist_ok=True)
    (state_root / "pending" / "EDARSAHUB-DEMO-GATE-B-001.json").write_text("{}", encoding="utf-8")
    dup = service.submit_objective(req, current_user=_admin())
    assert dup["status"] == "EXISTS"
    assert dup["duplicate_prevented"] is True
    assert dup["production_touched"] is False


def test_development_mutation_rejects_stale_sha_forbidden_paths_ops_and_rbac(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    target = repo / "backend" / "modules" / "demo" / "sample.py"
    target.parent.mkdir(parents=True)
    original = "x = 1\n"
    target.write_text(original, encoding="utf-8")
    monkeypatch.setattr(sem_caps, "_DEV_REPO_ROOT", repo)

    # 1. Stale SHA256 -> fail closed
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_SOURCE_SHA256_MISMATCH"):
        service.build_semantic_job(
            {
                "objective": "Bad sha",
                "bounded_context": "CRM",
                "mode": "MUTATION",
                "capability": "DEVELOPMENT_MUTATION_BOUNDED",
                "constraints": {
                    "change_spec": [
                        {
                            "operation": "replace_text",
                            "path": "backend/modules/demo/sample.py",
                            "source_sha256": "0" * 64,
                            "old_text": "x = 1",
                            "replacement": "x = 2",
                        }
                    ]
                },
            },
            current_user=_admin(),
        )

    # 2. Forbidden path (.env / production / outside root)
    for bad_path in (".env", "backend/modules/secret_config.py", "/etc/passwd", "deploy/production.sh"):
        with pytest.raises(service.WorkerIngressError, match="SEMANTIC_DEV_PATH_"):
            service.build_semantic_job(
                {
                    "objective": "Bad path",
                    "bounded_context": "CRM",
                    "mode": "MUTATION",
                    "capability": "DEVELOPMENT_MUTATION_BOUNDED",
                    "constraints": {
                        "change_spec": [
                            {"operation": "write_file", "path": bad_path, "content": "nope"}
                        ]
                    },
                },
                current_user=_admin(),
            )

    # 3. Forbidden operation (delete_file / shell)
    for bad_op in ("delete_file", "run_shell", "execute_sql"):
        with pytest.raises(service.WorkerIngressError, match="SEMANTIC_DEV_OPERATION_FORBIDDEN"):
            service.build_semantic_job(
                {
                    "objective": "Bad op",
                    "bounded_context": "CRM",
                    "mode": "MUTATION",
                    "capability": "DEVELOPMENT_MUTATION_BOUNDED",
                    "constraints": {
                        "change_spec": [
                            {
                                "operation": bad_op,
                                "path": "backend/modules/demo/sample.py",
                                "source_sha256": _sha256(original),
                            }
                        ]
                    },
                },
                current_user=_admin(),
            )

    # 4. Non-admin RBAC rejected
    with pytest.raises(service.WorkerIngressError, match="RBAC_MUTATION_FORBIDDEN"):
        service.build_semantic_job(
            {
                "objective": "Unauthorized mutation",
                "bounded_context": "CRM",
                "mode": "MUTATION",
                "capability": "DEVELOPMENT_MUTATION_BOUNDED",
                "constraints": {
                    "change_spec": [
                        {
                            "operation": "replace_text",
                            "path": "backend/modules/demo/sample.py",
                            "source_sha256": _sha256(original),
                            "old_text": "x = 1",
                            "replacement": "x = 2",
                        }
                    ]
                },
            },
            current_user=_operator(),
        )

    # 5. Raw Worker fields still rejected
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_CONSTRAINTS_UNSUPPORTED"):
        service.build_semantic_job(
            {
                "objective": "Raw fields",
                "bounded_context": "CRM",
                "mode": "MUTATION",
                "capability": "DEVELOPMENT_MUTATION_BOUNDED",
                "constraints": {"actions": [], "production_allowed": True},
            },
            current_user=_admin(),
        )
