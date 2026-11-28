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


def test_coa_gate6f_workflow_write_file_emits_matching_source_and_expected_sha256(
    tmp_path, monkeypatch
):
    import hashlib
    from pathlib import Path
    from modules.worker_ingress import semantic_capabilities as sem_caps

    monkeypatch.syspath_prepend(
        str(Path(__file__).resolve().parents[2] / "tools" / "mirror_sync")
    )
    import universal_job_dispatcher as dispatcher

    workflow_path = sem_caps._DEV_REPO_ROOT / sem_caps._COA_GATE6F_WORKFLOW
    expected_digest = hashlib.sha256(workflow_path.read_bytes()).hexdigest()

    job = service.build_semantic_job(_payload(), current_user=_user())
    workflow_action, trigger_action = job["actions"]

    assert workflow_action["type"] == "write_file"
    assert workflow_action["path"] == sem_caps._COA_GATE6F_WORKFLOW
    assert workflow_action["source_sha256"] == expected_digest
    assert workflow_action["expected_sha256"] == expected_digest
    assert workflow_action["source_sha256"] == workflow_action["expected_sha256"]

    assert trigger_action["type"] == "write_file"
    assert trigger_action["path"] == sem_caps._COA_GATE6F_TRIGGER
    assert "expected_sha256" not in trigger_action
    assert not (sem_caps._DEV_REPO_ROOT / sem_caps._COA_GATE6F_TRIGGER).exists()

    isolated_repo = tmp_path / "repo"
    isolated_wf = isolated_repo / sem_caps._COA_GATE6F_WORKFLOW
    isolated_wf.parent.mkdir(parents=True)
    isolated_wf.write_bytes(workflow_path.read_bytes())

    dispatcher.apply_action(isolated_repo, workflow_action)
    assert isolated_wf.read_text(encoding="utf-8") == workflow_action["content"]
