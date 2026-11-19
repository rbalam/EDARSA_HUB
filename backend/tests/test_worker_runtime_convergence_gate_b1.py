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
