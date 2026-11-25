"""Contract tests for WK50 R2-B: 4 READ_ONLY MCP tools, R2-B.1 dynamic catalog, R2-B.2 diagnostics."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from modules.worker_ingress import semantic_capabilities as caps
from modules.worker_ingress import service as ingress_service
from modules.worker_mcp import client as mcp_client
import importlib.util
if importlib.util.find_spec("mcp") is None:
    for _cand in sorted(Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")):
        if str(_cand) not in sys.path:
            sys.path.append(str(_cand))
from modules.worker_mcp import server as mcp_server


EXPECTED_TOOLS = {
    "submit_objective",
    "get_job_status",
    "get_go_context",
    "list_capabilities",
    "preflight_objective",
    "get_runtime_convergence",
}


def _configure_server():
    mcp_server._BACKEND_URL = "https://hub.example.test"


def _mock_token(monkeypatch, scopes: list[str], token: str = "tok-r2b"):
    monkeypatch.setattr(
        mcp_server,
        "get_access_token",
        lambda: SimpleNamespace(token=token, scopes=scopes, expires_at=None),
    )


def test_r2_b_tool_required_scopes_keep_least_privilege():
    assert set(mcp_server.TOOL_REQUIRED_SCOPES) == EXPECTED_TOOLS
    assert mcp_server.TOOL_REQUIRED_SCOPES["submit_objective"] == "worker:submit"
    for ro_tool in EXPECTED_TOOLS - {"submit_objective"}:
        assert mcp_server.TOOL_REQUIRED_SCOPES[ro_tool] == "worker:status"


def test_r2_b_four_new_readonly_tools_work_with_status_only_and_delegate_to_existing_endpoints(monkeypatch):
    _configure_server()
    _mock_token(monkeypatch, ["worker:status"])
    monkeypatch.setattr(mcp_client, "exchange_service_credential", lambda **kw: "internal-jwt")
    seen: list[tuple[str, str, dict | None]] = []

    def fake_request(*, method, url, token, payload=None, timeout=15.0):
        seen.append((method, url, dict(payload) if payload is not None else None))
        if "/api/internal/worker/context?" in url:
            return 200, {"schema": "edarsahub.worker-go-context.v1", "domain": "WORKER_MCP", "production_touched": False}
        if url.endswith("/api/internal/worker/capabilities"):
            return 200, {"schema": "edarsahub.worker-semantic-capabilities.v1", "capabilities": caps.capability_catalog(), "production_allowed": False}
        if url.endswith("/api/internal/worker/objectives/preflight"):
            return 200, {"schema": "edarsahub.worker-semantic-preflight.v1", "ok": True, "status": "PREFLIGHT_READY", "production_touched": False}
        if url.endswith("/api/internal/worker/runtime-convergence"):
            return 200, {"schema": "edarsahub.worker-runtime-convergence.v1", "overall_converged": True, "production_touched": False}
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(mcp_client, "_request_json", fake_request)

    ctx = mcp_server.get_go_context_tool(domain="WORKER_MCP", project="EDARSAHUB")
    assert ctx["domain"] == "WORKER_MCP"
    assert ctx["production_touched"] is False

    cat = mcp_server.list_capabilities_tool()
    assert cat["production_allowed"] is False
    assert any(item["code"] == "DEVELOPMENT_MUTATION_BOUNDED" for item in cat["capabilities"])

    pf = mcp_server.preflight_objective_tool(
        objective="Preflight READ_ONLY check.",
        bounded_context="WORKER_MCP",
        mode="READ_ONLY",
        capability="READ_ONLY_CANARY",
        request_key="r2b-preflight-test-1",
        constraints={},
    )
    assert pf["ok"] is True
    assert pf["status"] == "PREFLIGHT_READY"

    conv = mcp_server.get_runtime_convergence_tool()
    assert conv["overall_converged"] is True

    assert len(seen) == 4
    assert seen[0][0] == "GET" and "/api/internal/worker/context?" in seen[0][1]
    assert seen[1][0] == "GET" and seen[1][1].endswith("/api/internal/worker/capabilities")
    assert seen[2][0] == "POST" and seen[2][1].endswith("/api/internal/worker/objectives/preflight")
    assert seen[3][0] == "GET" and seen[3][1].endswith("/api/internal/worker/runtime-convergence")


def test_r2_b_readonly_tools_fail_closed_without_worker_status_scope(monkeypatch):
    _configure_server()
    _mock_token(monkeypatch, ["worker:submit"])

    for call in (
        lambda: mcp_server.get_go_context_tool(domain="WORKER_MCP"),
        lambda: mcp_server.list_capabilities_tool(),
        lambda: mcp_server.preflight_objective_tool(
            objective="Test",
            bounded_context="WORKER_MCP",
            mode="READ_ONLY",
            capability="READ_ONLY_CANARY",
            constraints={},
        ),
        lambda: mcp_server.get_runtime_convergence_tool(),
    ):
        with pytest.raises(PermissionError, match="MCP_SCOPE_FORBIDDEN:INSUFFICIENT_SCOPE"):
            call()


def test_r2_b_status_only_token_still_denied_submit_objective(monkeypatch):
    _configure_server()
    _mock_token(monkeypatch, ["worker:status"])
    with pytest.raises(PermissionError, match="MCP_SCOPE_FORBIDDEN:INSUFFICIENT_SCOPE"):
        mcp_server.submit_objective_tool(
            objective="Test",
            bounded_context="WORKER_MCP",
            mode="READ_ONLY",
            capability="READ_ONLY_CANARY",
            constraints={},
        )


def test_r2_b_1_dynamic_capability_catalog_covers_contract_fields():
    catalog = caps.capability_catalog()
    assert len(catalog) == len(caps.registered_capabilities())
    by_code = {item["code"]: item for item in catalog}

    required_keys = {
        "code",
        "modes",
        "bounded_context_rule",
        "allowed_constraints",
        "allowed_path_roots",
        "bounded_context_path_ownership",
        "raw_worker_fields_forbidden",
        "required_fields",
        "required_constraints",
        "allowed_operations",
        "formats",
        "limits",
        "ownership",
        "safe_example",
    }
    for code, item in by_code.items():
        assert required_keys.issubset(item.keys()), f"Missing keys for {code}"
        assert item["raw_worker_fields_forbidden"] is True
        assert isinstance(item["safe_example"], dict)
        for forbidden in caps.RAW_WORKER_FIELDS_FORBIDDEN:
            assert forbidden not in item["safe_example"]

    dev = by_code["DEVELOPMENT_MUTATION_BOUNDED"]
    assert dev["required_constraints"] == ["change_spec"]
    assert set(dev["allowed_operations"]) == set(caps._DEV_ALLOWED_OPERATIONS)
    assert dev["limits"]["max_changes"] == caps._DEV_MAX_CHANGES
    assert dev["limits"]["max_verification_tests"] == caps._DEV_MAX_TESTS
    assert dev["limits"]["max_text_bytes"] == caps._DEV_MAX_TEXT_BYTES
    assert dev["ownership"]["bounded_context_path_ownership"]["WORKER_MCP"] == [
        "tools/tests/test_worker_mcp_gate2b.py"
    ]
    assert "source_sha256" in dev["formats"]


@pytest.mark.parametrize(
    "raw_result,expected_category,expected_code,expected_retryable,expected_recovery",
    [
        (
            {
                "status": "RECOVERY_REQUIRED",
                "job_id": "SEM-REQUEST-ED69DAC9190C370E171CE5E0",
                "reason": "RuntimeError:PUSH_FAILED:fatal: could not read Username for 'https://user:gho_TOPSECRET@github.com/rbalam/EDARSA_HUB.git': No such device or address",
            },
            "GIT_AUTH_FAILURE",
            "GIT_AUTH_FAILED",
            False,
            True,
        ),
        (
            {
                "status": "BLOCKED_CONVERGENCE",
                "job_id": "SEM-REQUEST-00000000000000000001",
                "reason": "BLOCKED_DIVERGENCE",
            },
            "CONVERGENCE_FAILURE",
            "BLOCKED_CONVERGENCE",
            False,
            True,
        ),
        (
            {
                "status": "WRITER_BUSY",
                "job_id": "SEM-REQUEST-00000000000000000002",
                "reason": "GIT_LOCK_BUSY",
            },
            "CONFLICT_OR_CONTENTION",
            "WRITER_BUSY",
            True,
            False,
        ),
        (
            {
                "status": "RECOVERY_REQUIRED",
                "job_id": "SEM-REQUEST-00000000000000000003",
                "reason": "RuntimeError:QUEUE_PUBLISHER_RESIDUAL_STATE_INCOMPLETE",
            },
            "CONFLICT_OR_CONTENTION",
            "QUEUE_PUBLISHER_RESIDUAL_STATE_INCOMPLETE",
            False,
            True,
        ),
        (
            {
                "status": "RECOVERY_REQUIRED",
                "job_id": "SEM-REQUEST-00000000000000000004",
                "reason": "RuntimeError:PUSH_FAILED:remote rejected",
            },
            "PUBLICATION_FAILURE",
            "PUSH_FAILED",
            False,
            True,
        ),
    ],
)
def test_r2_b_2_publication_diagnostics_classify_and_sanitize_secrets(
    raw_result,
    expected_category,
    expected_code,
    expected_retryable,
    expected_recovery,
):
    diag = ingress_service.classify_publication_diagnostic(raw_result)
    assert diag["category"] == expected_category
    assert diag["error_code"] == expected_code
    assert diag["job_id"] == raw_result["job_id"]
    assert diag["retryable"] is expected_retryable
    assert diag["recovery_required"] is expected_recovery
    assert diag["production_touched"] is False
    assert "gho_TOPSECRET" not in str(diag)
    assert "https://" not in str(diag)


def test_r2_b_2_mcp_submit_tool_error_exposes_sanitized_category_job_id_and_recoverability(monkeypatch):
    _configure_server()
    _mock_token(monkeypatch, ["worker:submit", "worker:status"])
    monkeypatch.setattr(mcp_client, "exchange_service_credential", lambda **kw: "internal-jwt")
    monkeypatch.setattr(
        mcp_client,
        "_request_json",
        lambda **kw: (
            503,
            {
                "detail": {
                    "status": "RECOVERY_REQUIRED",
                    "job_id": "SEM-REQUEST-ED69DAC9190C370E171CE5E0",
                    "reason": "GIT_AUTH_FAILED",
                    "publication_diagnostic": {
                        "category": "GIT_AUTH_FAILURE",
                        "error_code": "GIT_AUTH_FAILED",
                        "job_id": "SEM-REQUEST-ED69DAC9190C370E171CE5E0",
                        "retryable": False,
                        "recovery_required": True,
                        "recommended_action": "Verify non-interactive Git credential helper without modifying credentials.",
                    },
                }
            },
        ),
    )

    with pytest.raises(mcp_server.ToolError) as exc_info:
        mcp_server.submit_objective_tool(
            objective="Test R2-B.2 diagnostic mapping.",
            bounded_context="WORKER_MCP",
            mode="READ_ONLY",
            capability="READ_ONLY_CANARY",
            request_key="r2b2-diag-test",
            constraints={},
        )
    msg = str(exc_info.value)
    assert "UPSTREAM_UNAVAILABLE_503:RECOVERY_REQUIRED" in msg
    assert "retryable=false" in msg
    assert "category=GIT_AUTH_FAILURE" in msg
    assert "cause=GIT_AUTH_FAILED" in msg
    assert "job_id=SEM-REQUEST-ED69DAC9190C370E171CE5E0" in msg
    assert "recovery_required=true" in msg
    assert "gho_" not in msg
