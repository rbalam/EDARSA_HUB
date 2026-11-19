from __future__ import annotations

import pytest

from modules.worker_ingress import service
from modules.worker_ingress.semantic_capabilities import registered_capabilities


def _user():
    return {
        "id": "1",
        "email": "admin@example.com",
        "role": "SuperAdministrador",
    }


def _payload(**overrides):
    payload = {
        "objective": "Ejecutar Gate 6F COA por el canal SQL Development certificado.",
        "bounded_context": "COA",
        "mode": "MUTATION",
        "capability": "COA_FISCAL_STATUS_SEED_DEVELOPMENT",
        "constraints": {
            "authorization_ref": "coa-gate6e-fiscal-status-seed-preflight-readonly-v1-20261027"
        },
        "request_key": "coa-gate6f-test",
    }
    payload.update(overrides)
    return payload


def test_coa_gate6f_capability_registered_and_fixed_scope():
    assert "COA_FISCAL_STATUS_SEED_DEVELOPMENT" in registered_capabilities()
    job = service.build_semantic_job(_payload(), current_user=_user())
    assert job["mode"] == "MUTATION"
    assert job["production_allowed"] is False
    assert [a["path"] for a in job["actions"]] == [
        ".github/workflows/coa-core-development-migration.yml",
        "ops/migrations/requests/COA-FISCAL-STATUS-SEED-20261026.execute",
    ]
    workflow = job["actions"][0]["content"]
    assert "MIGRATION_KIND=CFDI_STATUS_SEED" in workflow
    assert "20261026_coa_fiscal_documentos_emitidos_estatus_seed.sql" in workflow
    assert "COA_STATUS_SEED_POSTCHECK_ROWS_MISMATCH" in workflow
    assert "Edarsahub_Produccion" not in workflow


def test_coa_gate6f_rejects_wrong_authorization():
    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_COA_GATE6F_AUTHORIZATION_REQUIRED",
    ):
        service.build_semantic_job(
            _payload(constraints={"authorization_ref": "wrong-gate"}),
            current_user=_user(),
        )


def test_coa_gate6f_rejects_wrong_context_and_unknown_constraints():
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_BOUNDED_CONTEXT_UNSUPPORTED"):
        service.build_semantic_job(
            _payload(bounded_context="OTHER"),
            current_user=_user(),
        )
    with pytest.raises(service.WorkerIngressError, match="SEMANTIC_CONSTRAINTS_UNSUPPORTED"):
        service.build_semantic_job(
            _payload(
                constraints={
                    "authorization_ref": "coa-gate6e-fiscal-status-seed-preflight-readonly-v1-20261027",
                    "raw_sql": "SELECT 1",
                }
            ),
            current_user=_user(),
        )
