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
