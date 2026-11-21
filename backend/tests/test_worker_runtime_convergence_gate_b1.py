"""Gate B.1 tests: Runtime MCP & Capability Catalog convergence diagnostics."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from tools.mirror_sync import worker_runtime_fingerprint as fp
from modules.worker_ingress import routes as ingress_routes


def test_diagnose_capability_failure_differentiates_all_8_classes():
    reg = ("READ_ONLY_CANARY", "DEVELOPMENT_MUTATION_BOUNDED")
    loaded = ("READ_ONLY_CANARY",)

    # 1. Capability registered in code but not loaded in active runtime
    d1 = fp.diagnose_capability_failure(
        capability_code="DEVELOPMENT_MUTATION_BOUNDED",
        registered_capabilities=reg,
        loaded_capabilities=loaded,
        runtime_aligned=True,
    )
    assert d1["classification"] == "CAPABILITY_NOT_LOADED_STALE_RUNTIME"
    assert d1["requires_runtime_recovery"] is True

    # 2. Capability genuinely unknown
    d2 = fp.diagnose_capability_failure(
        capability_code="NONEXISTENT_CAP",
        registered_capabilities=reg,
        loaded_capabilities=reg,
        runtime_aligned=True,
    )
    assert d2["classification"] == "CAPABILITY_UNKNOWN"
    assert d2["requires_runtime_recovery"] is False

    # 3. INVALID_ARGUMENT MUST NEVER be misclassified as stale runtime
    d3 = fp.diagnose_capability_failure(
        capability_code="DEVELOPMENT_MUTATION_BOUNDED",
        registered_capabilities=reg,
        loaded_capabilities=loaded,
        runtime_aligned=False,
        error_code="INVALID_ARGUMENT",
    )
    assert d3["classification"] == "INVALID_REQUEST"
    assert d3["requires_runtime_recovery"] is False

    # 4. Contract incompatible
    d4 = fp.diagnose_capability_failure(
        capability_code="READ_ONLY_CANARY",
        registered_capabilities=reg,
        loaded_capabilities=reg,
        runtime_aligned=True,
        error_code="SEMANTIC_CONSTRAINTS_UNSUPPORTED",
    )
    assert d4["classification"] == "CONTRACT_INCOMPATIBLE"

    # 5. RBAC insufficient
    d5 = fp.diagnose_capability_failure(
        capability_code="DEVELOPMENT_MUTATION_BOUNDED",
        registered_capabilities=reg,
        loaded_capabilities=reg,
        runtime_aligned=True,
        error_code="RBAC_MUTATION_FORBIDDEN",
    )
    assert d5["classification"] == "RBAC_INSUFFICIENT"

    # 6. Context invalid
    d6 = fp.diagnose_capability_failure(
        capability_code="REPOSITORY_CONTRACT_AUDIT",
        registered_capabilities=reg,
        loaded_capabilities=reg,
        runtime_aligned=True,
        error_code="SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED",
    )
    assert d6["classification"] == "CONTEXT_INVALID"

    # 7. Transient error
    d7 = fp.diagnose_capability_failure(
        capability_code="READ_ONLY_CANARY",
        registered_capabilities=reg,
        loaded_capabilities=reg,
        runtime_aligned=True,
        error_code="GIT_LOCK_BUSY",
    )
    assert d7["classification"] == "TRANSIENT_ERROR"

    # 8. Runtime stale when code tree drifted
    d8 = fp.diagnose_capability_failure(
        capability_code="READ_ONLY_CANARY",
        registered_capabilities=reg,
        loaded_capabilities=reg,
        runtime_aligned=False,
    )
    assert d8["classification"] == "RUNTIME_STALE"
    assert d8["requires_runtime_recovery"] is True


def test_build_mcp_runtime_convergence_report_detects_missing_runtime_capability(monkeypatch):
    sha = "a" * 40
    monkeypatch.setattr(
        fp,
        "build_runtime_fingerprint",
        lambda: {
            "schema": "edarsahub.worker-runtime-fingerprint.v1",
            "branch": "Edarsahub_Desarrollo",
            "development_sha": sha,
            "worker_code_tree_sha": "b" * 40,
            "active_worker_code_tree_sha": "b" * 40,
            "worker_code_tree_aligned": True,
            "expected_generation": "v4",
            "actual_generation": "v4",
            "generation_aligned": True,
            "required_capabilities": [],
            "production_touched": False,
        },
    )
    monkeypatch.setattr(fp, "_git", lambda *args: sha)

    report = fp.build_mcp_runtime_convergence_report(loaded_capabilities=["READ_ONLY_CANARY"])
    assert report["schema"] == "edarsahub.worker-runtime-convergence.v1"
    assert report["head_aligned"] is True
    assert report["catalog_aligned"] is False
    assert "DEVELOPMENT_MUTATION_BOUNDED" in report["missing_in_runtime"]
    assert report["overall_converged"] is False
    assert report["recommended_action"] == "RECOVER_PREVIEW_RUNTIME"
    assert report["production_touched"] is False


def test_runtime_convergence_route_enforces_rbac_scope(monkeypatch):
    def deny(**kwargs):
        raise ingress_routes.OAuthValidationError("INSUFFICIENT_SCOPE")

    monkeypatch.setattr(ingress_routes, "enforce_internal_jwt_mcp_scope", deny)
    with pytest.raises(HTTPException) as exc_info:
        ingress_routes.read_worker_runtime_convergence(
            current_user={"id": "2", "email": "op@example.com", "role": "Operador"},
            authorization="Bearer invalid",
        )
    assert exc_info.value.status_code == 403


def test_gate_m4_convergence_report_fails_closed_when_catalog_unavailable(monkeypatch):
    sha = "a" * 40
    monkeypatch.setattr(
        fp,
        "build_runtime_fingerprint",
        lambda: {
            "schema": "edarsahub.worker-runtime-fingerprint.v1",
            "branch": "Edarsahub_Desarrollo",
            "development_sha": sha,
            "worker_code_tree_sha": "b" * 40,
            "active_worker_code_tree_sha": "b" * 40,
            "worker_code_tree_aligned": True,
            "expected_generation": "v4",
            "actual_generation": "v4",
            "generation_aligned": True,
            "required_capabilities": [],
            "production_touched": False,
        },
    )
    monkeypatch.setattr(fp, "_git", lambda *args: sha)
    monkeypatch.setattr(
        fp,
        "_load_registered_capabilities",
        lambda: ((), "CAPABILITY_CATALOG_LOAD_FAILED:RuntimeError"),
    )

    report = fp.build_mcp_runtime_convergence_report()
    assert report["registered_capabilities"] == []
    assert report["catalog_load_error"] == "CAPABILITY_CATALOG_LOAD_FAILED:RuntimeError"
    assert report["catalog_aligned"] is False
    assert report["overall_converged"] is False
    assert report["recommended_action"] == "RECOVER_PREVIEW_RUNTIME"
    assert report["production_touched"] is False


def test_gate_m4_convergence_report_loads_catalog_standalone(monkeypatch):
    sha = "a" * 40
    monkeypatch.setattr(
        fp,
        "build_runtime_fingerprint",
        lambda: {
            "schema": "edarsahub.worker-runtime-fingerprint.v1",
            "branch": "Edarsahub_Desarrollo",
            "development_sha": sha,
            "worker_code_tree_sha": "b" * 40,
            "active_worker_code_tree_sha": "b" * 40,
            "worker_code_tree_aligned": True,
            "expected_generation": "v4",
            "actual_generation": "v4",
            "generation_aligned": True,
            "required_capabilities": [],
            "production_touched": False,
        },
    )
    monkeypatch.setattr(fp, "_git", lambda *args: sha)

    report = fp.build_mcp_runtime_convergence_report()
    assert report["catalog_load_error"] is None
    assert len(report["registered_capabilities"]) >= 12
    assert "REPOSITORY_CONTRACT_AUDIT_BOUNDED" in report["registered_capabilities"]
    assert "SEC_RBAC_SQL_PERMISSION_MATRIX_READONLY" in report["registered_capabilities"]
    assert report["catalog_aligned"] is True
    assert report["overall_converged"] is True


def test_gate_m4_capability_catalog_and_mcp_docstring_full_parity():
    import ast
    from pathlib import Path
    from modules.worker_ingress import semantic_capabilities as sem_caps

    catalog = {item["code"]: item for item in sem_caps.capability_catalog()}
    registered = set(sem_caps.registered_capabilities())
    assert set(catalog) == registered

    # WORKER_PYTEST_CERTIFICATION_READONLY metadata must reflect every allowed suite context
    pytest_meta = catalog["WORKER_PYTEST_CERTIFICATION_READONLY"]
    for ctx in sem_caps._WORKER_PYTEST_FIXED_SUITES:
        assert ctx in pytest_meta["bounded_context_rule"].split("|")

    # REPOSITORY_CONTRACT_AUDIT must remain strictly restricted to RH
    assert catalog["REPOSITORY_CONTRACT_AUDIT"]["bounded_context_rule"] == "RH"
    # REPOSITORY_CONTRACT_AUDIT_BOUNDED includes backend/core/, mutation does not
    assert "backend/core/" in catalog["REPOSITORY_CONTRACT_AUDIT_BOUNDED"]["allowed_path_roots"]
    assert "backend/core/" not in catalog["DEVELOPMENT_MUTATION_BOUNDED"]["allowed_path_roots"]

    # Extract submit_objective_tool docstring and tool registrations via AST (no mcp venv needed)
    server_path = Path(__file__).resolve().parents[1] / "modules" / "worker_mcp" / "server.py"
    tree = ast.parse(server_path.read_text(encoding="utf-8"))
    submit_doc = ""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "submit_objective_tool":
            submit_doc = ast.get_docstring(node) or ""
            break
    assert submit_doc
    for code in registered:
        assert code in submit_doc, f"MCP submit_objective docstring missing capability: {code}"
    assert "backend/core/" in submit_doc
    assert "IA_ASSISTANT" in submit_doc


def test_gate_m4_preserves_capability_restrictions_fail_closed():
    from modules.worker_ingress import semantic_capabilities as sem_caps

    with pytest.raises(sem_caps.SemanticCapabilityError, match="SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED"):
        sem_caps.resolve_capability("REPOSITORY_CONTRACT_AUDIT").builder(
            {"bounded_context": "WORKER_OPERATIONS", "constraints": {}}
        )

    with pytest.raises(sem_caps.SemanticCapabilityError, match="SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED"):
        sem_caps.resolve_capability("WORKER_PYTEST_CERTIFICATION_READONLY").builder(
            {"bounded_context": "RH", "constraints": {}}
        )
