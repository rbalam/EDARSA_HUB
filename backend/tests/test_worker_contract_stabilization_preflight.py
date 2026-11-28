"""Contract Stabilization Program: Canonical Semantic Preflight, Diagnostics & 8-Domain Cases."""
from __future__ import annotations

import hashlib
from pathlib import Path
import pytest

from modules.worker_ingress import service
from modules.worker_ingress import semantic_capabilities as sem_caps
from modules.worker_mcp import client as mcp_client


def _admin():
    return {"id": "1", "email": "ricardo@edarsa.com.mx", "role": "SuperAdministrador"}


def _operator():
    return {"id": "2", "email": "op@edarsa.com.mx", "role": "Operador"}


def test_rejected_preflight_keeps_reserved_fields_over_diagnostics(monkeypatch):
    diagnostics = {
        "error_code": "OBJECTIVE_REQUIRED",
        "rejected_field": "objective",
        "classification": "CONTRACT_VALIDATION_ERROR",
        "allowed_correction": "Provide an objective",
        "schema": "diagnostic-schema",
        "ok": True,
        "status": "PREFLIGHT_READY",
    }
    monkeypatch.setattr(service, "build_semantic_diagnostic", lambda *args, **kwargs: diagnostics)

    result = service.preflight_semantic_objective({}, current_user=_admin())

    assert result == {
        **diagnostics,
        "schema": "edarsahub.worker-semantic-preflight.v1",
        "ok": False,
        "status": "PREFLIGHT_REJECTED",
    }


def test_cavas_constraints_and_bounded_context_diagnostics():
    # Cavas: passing raw actions/sql in constraints -> structured CONTRACT_VALIDATION_ERROR
    r1 = service.preflight_semantic_objective(
        {
            "objective": "Auditar contratos Cavas",
            "bounded_context": "CAVAS",
            "mode": "READ_ONLY",
            "capability": "REPOSITORY_CONTRACT_AUDIT_BOUNDED",
            "constraints": {"paths": ["backend/modules/"], "search_terms": ["cavas"], "actions": []},
        },
        current_user=_admin(),
    )
    assert r1["ok"] is False
    assert r1["error_code"] == "SEMANTIC_CONSTRAINTS_UNSUPPORTED"
    assert r1["classification"] == "CONTRACT_VALIDATION_ERROR"
    assert r1["rejected_field"] == "constraints"
    assert "paths" in r1["allowed_constraints"]
    assert r1["production_touched"] is False

    # Cavas: calling RH-only legacy REPOSITORY_CONTRACT_AUDIT -> clear bounded_context diagnostic
    r2 = service.preflight_semantic_objective(
        {
            "objective": "Auditar Cavas con capacidad RH",
            "bounded_context": "CAVAS",
            "mode": "READ_ONLY",
            "capability": "REPOSITORY_CONTRACT_AUDIT",
            "constraints": {},
        },
        current_user=_admin(),
    )
    assert r2["ok"] is False
    assert r2["error_code"] == "SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED"
    assert r2["rejected_field"] == "bounded_context"
    assert r2["allowed_bounded_context"] == "RH"


def test_bos_v1_gate_e_contractual_rejection_and_rls_gate0_unknown_capability():
    # BOS V1 Gate E: mode mismatch -> structured diagnostic with allowed_modes
    r_mode = service.preflight_semantic_objective(
        {
            "objective": "BOS V1 Gate E intento mutacion con capacidad READ_ONLY",
            "bounded_context": "BOS_V1_GATE_E",
            "mode": "MUTATION",
            "capability": "READ_ONLY_CANARY",
            "constraints": {},
        },
        current_user=_admin(),
    )
    assert r_mode["ok"] is False
    assert r_mode["error_code"] == "SEMANTIC_CAPABILITY_MODE_MISMATCH"
    assert r_mode["rejected_field"] == "mode"
    assert r_mode["allowed_modes"] == ["READ_ONLY"]

    # RLS Gate 0: domain-specific unregistered capability -> SEMANTIC_CAPABILITY_UNKNOWN + catalog hint
    r_rls = service.preflight_semantic_objective(
        {
            "objective": "RLS Gate 0 auditoria especifica",
            "bounded_context": "RLS_GATE0",
            "mode": "READ_ONLY",
            "capability": "RLS_GATE0_UNREGISTERED_CAP",
            "constraints": {},
        },
        current_user=_admin(),
    )
    assert r_rls["ok"] is False
    assert r_rls["error_code"] == "SEMANTIC_CAPABILITY_UNKNOWN"
    assert r_rls["rejected_field"] == "capability"
    assert "REPOSITORY_CONTRACT_AUDIT_BOUNDED" in r_rls["registered_capabilities"]
    assert r_rls["runtime_diagnosis"] == "CAPABILITY_UNKNOWN"

    # Runtime drift differentiation: registered in code but missing in loaded_capabilities
    r_drift = service.preflight_semantic_objective(
        {
            "objective": "Runtime drift test",
            "bounded_context": "RLS_GATE0",
            "mode": "READ_ONLY",
            "capability": "READ_ONLY_CANARY",
            "constraints": {},
        },
        current_user=_admin(),
        loaded_capabilities=[],
    )
    assert r_drift["ok"] is False
    assert r_drift["classification"] == "RUNTIME_DRIFT_ERROR"
    assert r_drift["runtime_diagnosis"] == "CAPABILITY_NOT_LOADED_STALE_RUNTIME"


def test_cxp_pcid_stale_sha_and_services_forbidden_paths_and_sql_rbac_019_security_denial(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    target = repo / "backend" / "modules" / "cxp" / "pcid.py"
    target.parent.mkdir(parents=True)
    target.write_text("PC_ID = 1\n", encoding="utf-8")
    monkeypatch.setattr(sem_caps, "_DEV_REPO_ROOT", repo)

    # CxP Pc_ID: stale SHA-256 -> structured diagnostic without leaking file contents
    r_cxp = service.preflight_semantic_objective(
        {
            "objective": "CxP Pc_ID actualizacion con SHA desactualizado",
            "bounded_context": "CXP_PCID",
            "mode": "MUTATION",
            "capability": "DEVELOPMENT_MUTATION_BOUNDED",
            "constraints": {
                "change_spec": [
                    {
                        "operation": "replace_text",
                        "path": "backend/modules/cxp/pcid.py",
                        "source_sha256": "0" * 64,
                        "old_text": "PC_ID = 1",
                        "replacement": "PC_ID = 2",
                    }
                ]
            },
        },
        current_user=_admin(),
    )
    assert r_cxp["ok"] is False
    assert r_cxp["error_code"] == "SEMANTIC_SOURCE_SHA256_MISMATCH"
    assert r_cxp["rejected_field"] == "constraints.change_spec[].source_sha256"
    assert "PC_ID = 1" not in str(r_cxp)

    # Services: disallowed audit path -> SECURITY_DENIAL_EXPECTED
    r_svc = service.preflight_semantic_objective(
        {
            "objective": "Services auditoria ruta fuera de allowlist",
            "bounded_context": "SERVICES",
            "mode": "READ_ONLY",
            "capability": "REPOSITORY_CONTRACT_AUDIT_BOUNDED",
            "constraints": {"paths": ["deploy/secrets/"], "search_terms": ["service"]},
        },
        current_user=_admin(),
    )
    assert r_svc["ok"] is False
    assert r_svc["error_code"] == "SEMANTIC_PATH_FORBIDDEN"
    assert r_svc["classification"] == "SECURITY_DENIAL_EXPECTED"
    assert r_svc["rejected_field"] == "constraints.paths"

    # SQL/RBAC 019: out-of-scope empresa/domain & non-admin mutation -> SECURITY_DENIAL_EXPECTED
    r_scope = service.preflight_semantic_objective(
        {
            "objective": "SQL/RBAC 019 consulta fuera de alcance",
            "bounded_context": "SQL_RBAC_019",
            "mode": "READ_ONLY",
            "capability": "READ_ONLY_CANARY",
            "constraints": {},
        },
        current_user=_admin(),
        authorization_scope={"allowed_empresa_ids": ["1"], "requested_empresa_id": "99"},
    )
    assert r_scope["ok"] is False
    assert r_scope["error_code"] == "SCOPE_AUTHORIZATION_DENIED"
    assert r_scope["classification"] == "SECURITY_DENIAL_EXPECTED"

    r_rbac = service.preflight_semantic_objective(
        {
            "objective": "SQL/RBAC 019 mutacion sin rol admin",
            "bounded_context": "SQL_RBAC_019",
            "mode": "MUTATION",
            "capability": "DEVELOPMENT_MUTATION_BOUNDED",
            "constraints": {
                "change_spec": [
                    {
                        "operation": "replace_text",
                        "path": "backend/modules/cxp/pcid.py",
                        "source_sha256": hashlib.sha256(b"PC_ID = 1\n").hexdigest(),
                        "old_text": "PC_ID = 1",
                        "replacement": "PC_ID = 2",
                    }
                ]
            },
        },
        current_user=_operator(),
    )
    assert r_rbac["ok"] is False
    assert r_rbac["error_code"] == "RBAC_MUTATION_FORBIDDEN"
    assert r_rbac["classification"] == "SECURITY_DENIAL_EXPECTED"


def test_agentes_ia_gate5_authorized_preflight_dedup_and_mcp_schema_diagnostic(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    target = repo / "backend" / "modules" / "agentes_ia" / "gate5.py"
    target.parent.mkdir(parents=True)
    src = "VERSION = 4\n"
    target.write_text(src, encoding="utf-8")

    state_root = tmp_path / ".git" / "universal-worker-queue"
    (state_root / "results").mkdir(parents=True)
    monkeypatch.setattr(sem_caps, "_DEV_REPO_ROOT", repo)
    monkeypatch.setattr(service, "STATE_ROOT", state_root)

    req = {
        "objective": "Agentes IA Gate5 mutacion autorizada en Desarrollo",
        "bounded_context": "AGENTES_IA_GATE5",
        "mode": "MUTATION",
        "capability": "DEVELOPMENT_MUTATION_BOUNDED",
        "constraints": {
            "job_id_override": "EDARSAHUB-AGENTES-IA-GATE5-TEST-001",
            "change_spec": [
                {
                    "operation": "replace_text",
                    "path": "backend/modules/agentes_ia/gate5.py",
                    "source_sha256": hashlib.sha256(src.encode("utf-8")).hexdigest(),
                    "old_text": "VERSION = 4",
                    "replacement": "VERSION = 5",
                }
            ],
        },
    }
    ok = service.preflight_semantic_objective(req, current_user=_admin())
    assert ok["ok"] is True
    assert ok["status"] == "PREFLIGHT_READY"
    assert ok["duplicate_detected"] is False
    assert ok["production_allowed"] is False

    # Equivalent/existing job detected cleanly as EXISTS (no duplicates)
    (state_root / "results" / "EDARSAHUB-AGENTES-IA-GATE5-TEST-001.json").write_text("{}", encoding="utf-8")
    dup = service.preflight_semantic_objective(req, current_user=_admin())
    assert dup["ok"] is True
    assert dup["status"] == "EXISTS"
    assert dup["duplicate_prevented"] is True

    # MCP client extracts structured diagnostic from Pydantic SCHEMA_VALIDATION_ERROR list
    pydantic_422 = {
        "detail": [
            {"loc": ["body", "constraints"], "msg": "Input should be a valid dictionary", "type": "dict_type"}
        ]
    }
    assert mcp_client._extract_validation_reason(pydantic_422) == "SCHEMA_VALIDATION_ERROR"
    diag = mcp_client.extract_safe_validation_diagnostic(pydantic_422)
    assert diag["rejected_field"] == "constraints"
    assert "WorkerObjectiveRequest" in diag["allowed_correction"]


def test_gate_b_precise_diagnostics_for_dev_mutation_and_semantic_extract(tmp_path, monkeypatch, caplog):
    repo = tmp_path / "repo"
    target = repo / "backend" / "modules" / "demo" / "sample.py"
    target.parent.mkdir(parents=True)
    src = "VALUE = 1\n"
    target.write_text(src, encoding="utf-8")
    live_sha = hashlib.sha256(src.encode("utf-8")).hexdigest()
    monkeypatch.setattr(sem_caps, "_DEV_REPO_ROOT", repo)

    # 1. WORKER_RESULT_SEMANTIC_EXTRACT invalid source_job_id -> precise field constraints.source_job_id + http_status 422
    r_sj = service.preflight_semantic_objective(
        {
            "objective": "Extract semantic result",
            "bounded_context": "WORKER_OPERATIONS",
            "mode": "READ_ONLY",
            "capability": "WORKER_RESULT_SEMANTIC_EXTRACT",
            "request_key": "corr-gate-b-001",
            "constraints": {"source_job_id": "bad job id!!"},
        },
        current_user=_admin(),
    )
    assert r_sj["ok"] is False
    assert r_sj["error_code"] == "SEMANTIC_SOURCE_JOB_INVALID"
    assert r_sj["rejected_field"] == "constraints.source_job_id"
    assert r_sj["http_status"] == 422

    # 2. DEVELOPMENT_MUTATION_BOUNDED empty change_spec -> constraints.change_spec
    r_cs = service.preflight_semantic_objective(
        {
            "objective": "Invalid empty change_spec",
            "bounded_context": "WORKER_OPERATIONS",
            "mode": "MUTATION",
            "capability": "DEVELOPMENT_MUTATION_BOUNDED",
            "constraints": {"change_spec": []},
        },
        current_user=_admin(),
    )
    assert r_cs["ok"] is False
    assert r_cs["error_code"] == "SEMANTIC_DEV_CHANGE_SPEC_INVALID"
    assert r_cs["rejected_field"] == "constraints.change_spec"
    assert r_cs["http_status"] == 422

    # 3. DEVELOPMENT_MUTATION_BOUNDED unsupported item key -> constraints.change_spec[]
    r_keys = service.preflight_semantic_objective(
        {
            "objective": "Invalid item key in change_spec",
            "bounded_context": "WORKER_OPERATIONS",
            "mode": "MUTATION",
            "capability": "DEVELOPMENT_MUTATION_BOUNDED",
            "constraints": {
                "change_spec": [{"operation": "replace_text", "path": "backend/modules/demo/sample.py", "bogus": 1}]
            },
        },
        current_user=_admin(),
    )
    assert r_keys["error_code"] == "SEMANTIC_DEV_CHANGE_KEYS_UNSUPPORTED"
    assert r_keys["rejected_field"] == "constraints.change_spec[]"

    # 4. DEVELOPMENT_MUTATION_BOUNDED missing source_sha256 -> constraints.change_spec[].source_sha256
    r_nosha = service.preflight_semantic_objective(
        {
            "objective": "Missing source_sha256",
            "bounded_context": "WORKER_OPERATIONS",
            "mode": "MUTATION",
            "capability": "DEVELOPMENT_MUTATION_BOUNDED",
            "constraints": {
                "change_spec": [
                    {
                        "operation": "replace_text",
                        "path": "backend/modules/demo/sample.py",
                        "old_text": "VALUE = 1",
                        "replacement": "VALUE = 2",
                    }
                ]
            },
        },
        current_user=_admin(),
    )
    assert r_nosha["error_code"] == "SEMANTIC_SOURCE_SHA256_REQUIRED"
    assert r_nosha["rejected_field"] == "constraints.change_spec[].source_sha256"

    # 5. DEVELOPMENT_MUTATION_BOUNDED old_text mismatch -> constraints.change_spec[].old_text
    r_old = service.preflight_semantic_objective(
        {
            "objective": "Mismatched old_text",
            "bounded_context": "WORKER_OPERATIONS",
            "mode": "MUTATION",
            "capability": "DEVELOPMENT_MUTATION_BOUNDED",
            "constraints": {
                "change_spec": [
                    {
                        "operation": "replace_text",
                        "path": "backend/modules/demo/sample.py",
                        "source_sha256": live_sha,
                        "old_text": "DOES_NOT_EXIST_SECRET_PAYLOAD",
                        "replacement": "VALUE = 2",
                    }
                ]
            },
        },
        current_user=_admin(),
    )
    assert r_old["error_code"] == "SEMANTIC_DEV_OLD_TEXT_OCCURRENCE_MISMATCH"
    assert r_old["rejected_field"] == "constraints.change_spec[].old_text"

    # 6. Structured log must never expose change_spec text or sensitive tokens
    with caplog.at_level("WARNING", logger="edarsahub.worker_ingress"):
        service.build_semantic_diagnostic(
            "SEMANTIC_DEV_OLD_TEXT_OCCURRENCE_MISMATCH",
            request_payload={
                "capability": "DEVELOPMENT_MUTATION_BOUNDED",
                "request_key": "bearer-super-secret-value",
                "constraints": {"change_spec": [{"old_text": "NEVER_LOG_THIS_BODY"}]},
            },
        )
    joined_logs = " ".join(rec.getMessage() for rec in caplog.records)
    assert "worker_ingress_semantic_rejected" in joined_logs
    assert "SEMANTIC_DEV_OLD_TEXT_OCCURRENCE_MISMATCH" in joined_logs
    assert "NEVER_LOG_THIS_BODY" not in joined_logs
    assert "bearer-super-secret-value" not in joined_logs


def test_gate_b_mcp_503_timeout_and_observability_no_duplicate_retries(monkeypatch, caplog):
    import importlib.util
    import sys

    if importlib.util.find_spec("mcp") is None:
        for candidate in sorted(Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")):
            sys.path.append(str(candidate))

    from modules.worker_mcp import server as mcp_server
    from modules.worker_mcp.config import WorkerMcpConfig

    cfg = WorkerMcpConfig(
        issuer_url="https://hub.example.test/api/mcp/oauth",
        resource_url="https://hub.example.test/api/mcp",
        backend_url="https://hub.example.test",
        allowed_hosts=("hub.example.test",),
        allowed_origins=(),
    )
    mcp_server.build_mcp_server(cfg)
    orig_request_json = mcp_client._request_json
    monkeypatch.setattr(mcp_server, "_authorized_bearer_token", lambda scope: "fake-bearer-jwt-never-log")
    monkeypatch.setattr(mcp_client, "exchange_service_credential", lambda *, backend_url, credential: "fake-internal-jwt")

    # 1. HTTP 503 WRITER_BUSY / CLAIM_BUSY -> explicit retryable=true ToolError, strictly 1 call (no auto-retry)
    for busy_state in ("WRITER_BUSY", "CLAIM_BUSY"):
        calls = []

        def _fake_503(**kwargs):
            calls.append(kwargs)
            return 503, {"detail": {"status": busy_state}}

        monkeypatch.setattr(mcp_client, "_request_json", _fake_503)
        with caplog.at_level("WARNING", logger="edarsahub.worker_mcp"):
            with pytest.raises(mcp_server.ToolError) as exc_info:
                mcp_server.submit_objective_tool(
                    objective="Gate B 503 test",
                    bounded_context="WORKER_OPERATIONS",
                    mode="MUTATION",
                    capability="DEVELOPMENT_MUTATION_BOUNDED",
                    request_key="corr-503-test",
                    constraints={"change_spec": [{"operation": "replace_text", "old_text": "SECRET_SPEC_BODY"}]},
                )
        msg = str(exc_info.value)
        assert f"UPSTREAM_UNAVAILABLE_503:{busy_state}" in msg
        assert "retryable=true" in msg
        assert "DEVELOPMENT_MUTATION_BOUNDED" in msg
        assert len(calls) == 1

    # 2. HTTP 503 RECOVERY_REQUIRED -> retryable=false ToolError, strictly 1 call
    calls_rec = []

    def _fake_rec(**kwargs):
        calls_rec.append(kwargs)
        return 503, {"detail": {"status": "RECOVERY_REQUIRED"}}

    monkeypatch.setattr(mcp_client, "_request_json", _fake_rec)
    with pytest.raises(mcp_server.ToolError) as exc_rec:
        mcp_server.submit_objective_tool(
            objective="Gate B recovery test",
            bounded_context="WORKER_OPERATIONS",
            mode="MUTATION",
            capability="DEVELOPMENT_MUTATION_BOUNDED",
            request_key="corr-rec-test",
            constraints={},
        )
    assert "UPSTREAM_UNAVAILABLE_503:RECOVERY_REQUIRED" in str(exc_rec.value)
    assert "retryable=false" in str(exc_rec.value)
    assert len(calls_rec) == 1

    # 3. Upstream TimeoutError -> UPSTREAM_TIMEOUT_504 ToolError, strictly 1 call (no auto-retry)
    calls_to = []

    def _fake_urlopen(req, timeout=15.0):
        calls_to.append(req.full_url)
        raise TimeoutError("timed out")

    monkeypatch.setattr(mcp_client.urllib.request, "urlopen", _fake_urlopen)
    monkeypatch.setattr(mcp_client, "_request_json", orig_request_json)
    with pytest.raises(mcp_server.ToolError) as exc_to:
        mcp_server.submit_objective_tool(
            objective="Gate B timeout test",
            bounded_context="WORKER_OPERATIONS",
            mode="READ_ONLY",
            capability="READ_ONLY_CANARY",
            request_key="corr-timeout-test",
            constraints={},
        )
    assert "UPSTREAM_TIMEOUT_504:UPSTREAM_TIMEOUT" in str(exc_to.value)
    assert "retryable=true" in str(exc_to.value)
    assert len(calls_to) == 1

    # 3b. HTTP 422 validation error -> ToolError with precise field and http_status=422 logged
    monkeypatch.setattr(
        mcp_client,
        "_request_json",
        lambda **kwargs: (
            422,
            {
                "detail": {
                    "error_code": "SEMANTIC_CONSTRAINTS_UNSUPPORTED",
                    "rejected_field": "constraints",
                    "capability": "WORKER_RESULT_SEMANTIC_EXTRACT",
                    "http_status": 422,
                    "allowed_correction": "Use only allowed key: source_job_id.",
                }
            },
        ),
    )
    with pytest.raises(mcp_server.ToolError) as exc_422:
        mcp_server.submit_objective_tool(
            objective="Gate B 422 test",
            bounded_context="WORKER_OPERATIONS",
            mode="READ_ONLY",
            capability="WORKER_RESULT_SEMANTIC_EXTRACT",
            request_key="corr-422-test",
            constraints={"bad_key": "x"},
        )
    assert "VALIDATION_ERROR_422:SEMANTIC_CONSTRAINTS_UNSUPPORTED" in str(exc_422.value)
    assert "field=constraints" in str(exc_422.value)

    # 3c. HTTP 403 insufficient scope -> PermissionError without leaking token
    monkeypatch.setattr(
        mcp_client,
        "_request_json",
        lambda **kwargs: (
            403,
            {"detail": {"error": "INSUFFICIENT_SCOPE", "required_scope": "worker:submit", "code": "INSUFFICIENT_SCOPE"}},
        ),
    )
    with pytest.raises(PermissionError, match="MCP_SCOPE_FORBIDDEN:INSUFFICIENT_SCOPE"):
        mcp_server.submit_objective_tool(
            objective="Gate B 403 scope test",
            bounded_context="WORKER_OPERATIONS",
            mode="READ_ONLY",
            capability="READ_ONLY_CANARY",
            request_key="corr-403-test",
            constraints={},
        )

    # 4. get_job_status remains intact on HTTP 200
    monkeypatch.setattr(
        mcp_client,
        "_request_json",
        lambda **kwargs: (200, {"job_id": "JOB-1", "lifecycle": "RESULT", "status": "INTEGRATED", "certification": "CERTIFIED", "production_touched": False}),
    )
    st = mcp_server.get_job_status_tool("JOB-1")
    assert st["job_id"] == "JOB-1"
    assert st["certification"] == "CERTIFIED"
    assert st["production_touched"] is False

    # 5. Logs never leak tokens, JWTs, or change_spec contents
    joined_mcp = " ".join(rec.getMessage() for rec in caplog.records)
    assert "worker_mcp_tool_error" in joined_mcp
    assert "timestamp_utc=" in joined_mcp
    assert "http_status=503" in joined_mcp
    assert "fake-bearer-jwt-never-log" not in joined_mcp
    assert "fake-internal-jwt" not in joined_mcp
    assert "SECRET_SPEC_BODY" not in joined_mcp


def test_mcp_submit_objective_handles_409_unreachable_and_timeout_budget(monkeypatch):
    """MCP submit_objective maps HTTP 409, backend unreachable, and 5xx to structured ToolError."""
    import importlib.util
    import sys
    import urllib.error

    if importlib.util.find_spec("mcp") is None:
        for candidate in sorted(Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")):
            sys.path.append(str(candidate))

    from modules.worker_mcp import server as mcp_server
    from modules.worker_mcp.config import WorkerMcpConfig

    cfg = WorkerMcpConfig(
        issuer_url="https://hub.example.test/api/mcp/oauth",
        resource_url="https://hub.example.test/api/mcp",
        backend_url="https://hub.example.test",
        allowed_hosts=("hub.example.test",),
        allowed_origins=(),
    )
    mcp_server.build_mcp_server(cfg)
    orig_request_json = mcp_client._request_json
    monkeypatch.setattr(mcp_server, "_authorized_bearer_token", lambda scope: "fake-bearer-jwt-never-log")
    monkeypatch.setattr(mcp_client, "exchange_service_credential", lambda **kw: "fake-internal-jwt")
    monkeypatch.setattr(mcp_server, "backend_submit_objective", mcp_client.submit_objective)

    # 1. submit_objective passes an extended timeout budget (>= 45s) for GitHub queue publication
    captured_timeouts = []

    def _fake_ok(**kwargs):
        captured_timeouts.append(kwargs.get("timeout"))
        return 202, {
            "status": "SUBMITTED",
            "job_id": "SEM-REQUEST-TIMEOUT-BUDGET",
            "capability": "READ_ONLY_CANARY",
            "bounded_context": "WORKER_CONTROL_PLANE",
            "production_touched": False,
        }

    monkeypatch.setattr(mcp_client, "_request_json", _fake_ok)
    ok_res = mcp_server.submit_objective_tool(
        objective="Timeout budget regression",
        bounded_context="WORKER_CONTROL_PLANE",
        mode="READ_ONLY",
        capability="READ_ONLY_CANARY",
        request_key="corr-timeout-budget",
        constraints={},
    )
    assert ok_res["status"] == "SUBMITTED"
    assert captured_timeouts == [45.0]

    # 2. HTTP 409 RUNTIME_NOT_CONVERGED -> structured VALIDATION_ERROR_409 ToolError (never raw internal error)
    monkeypatch.setattr(
        mcp_client,
        "_request_json",
        lambda **kwargs: (
            409,
            {
                "detail": {
                    "error_code": "RUNTIME_NOT_CONVERGED",
                    "rejected_field": "runtime_convergence",
                    "capability": "DEVELOPMENT_MUTATION_BOUNDED",
                    "http_status": 409,
                    "allowed_correction": "Reconcile GET /api/internal/worker/runtime-convergence before retrying.",
                }
            },
        ),
    )
    with pytest.raises(mcp_server.ToolError) as exc_409:
        mcp_server.submit_objective_tool(
            objective="Gate 3 convergence conflict test",
            bounded_context="WORKER_CONTROL_PLANE",
            mode="MUTATION",
            capability="DEVELOPMENT_MUTATION_BOUNDED",
            request_key="corr-409-test",
            constraints={},
        )
    assert "VALIDATION_ERROR_409:RUNTIME_NOT_CONVERGED" in str(exc_409.value)
    assert "field=runtime_convergence" in str(exc_409.value)

    # 3. URLError connection refused -> UPSTREAM_UNAVAILABLE_503:BACKEND_UNREACHABLE (1 call, no auto-retry)
    unreachable_calls = []

    def _fake_urlopen_refused(req, timeout=15.0):
        unreachable_calls.append((req.full_url, timeout))
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(mcp_client.urllib.request, "urlopen", _fake_urlopen_refused)
    monkeypatch.setattr(mcp_client, "_request_json", orig_request_json)
    with pytest.raises(mcp_server.ToolError) as exc_unreach:
        mcp_server.submit_objective_tool(
            objective="Backend restart window test",
            bounded_context="WORKER_CONTROL_PLANE",
            mode="READ_ONLY",
            capability="READ_ONLY_CANARY",
            request_key="corr-unreachable-test",
            constraints={},
        )
    assert "UPSTREAM_UNAVAILABLE_503:BACKEND_UNREACHABLE" in str(exc_unreach.value)
    assert "retryable=true" in str(exc_unreach.value)
    assert len(unreachable_calls) == 1
    assert unreachable_calls[0][1] == 45.0

    # 4. Unexpected HTTP 500 -> structured UPSTREAM_ERROR_500 ToolError (never unhandled WorkerMcpBackendError)
    monkeypatch.setattr(
        mcp_client,
        "_request_json",
        lambda **kwargs: (500, {"detail": "internal"}),
    )
    with pytest.raises(mcp_server.ToolError) as exc_500:
        mcp_server.submit_objective_tool(
            objective="Unexpected 500 mapping test",
            bounded_context="WORKER_CONTROL_PLANE",
            mode="READ_ONLY",
            capability="READ_ONLY_CANARY",
            request_key="corr-500-test",
            constraints={},
        )
    assert "UPSTREAM_ERROR_500:SEMANTIC_SUBMIT_FAILED" in str(exc_500.value)
    assert "retryable=false" in str(exc_500.value)
