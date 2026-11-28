"""Gate E + WK60 R2-C tests: Canonical cross-chat GO context resolution (fail-closed)."""
from __future__ import annotations

import json
import os
import pytest
from fastapi import HTTPException

from modules.worker_ingress import routes as ingress_routes
from modules.worker_ingress import service


def _admin():
    return {"id": "1", "email": "ricardo@edarsa.com.mx", "role": "SuperAdministrador"}


def _operator():
    return {"id": "2", "email": "op@edarsa.com.mx", "role": "Operador"}


def _certified_result(
    job_id: str,
    domain: str | None = None,
    *,
    completed_at_utc: str = "2026-11-19T10:00:00Z",
    status: str = "READ_ONLY_COMPLETE",
    certification: str = "CERTIFIED_READ_ONLY",
    commit_sha: str | None = None,
):
    is_pending_audit = certification == "PENDING_AUDIT_EVIDENCE"
    payload = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": status,
        "certification": certification,
        "quality_gate": "PASS",
        "tests": "PASS",
        "percent_complete": 95 if is_pending_audit else 100,
        "completed_at_utc": completed_at_utc,
        "blockers": [],
        "production_touched": False,
    }
    if not is_pending_audit:
        payload["work_completion"] = "COMPLETE"
    if domain is not None:
        payload["scheduling"] = {"bounded_context": domain}
    if commit_sha is not None:
        payload["development_sha"] = commit_sha
        payload["candidate_sha"] = commit_sha
        payload["files_changed"] = ["backend/modules/worker_mcp/server.py"]
    return payload


def _explicit_auth(domain: str, *, auth_id: str = "GO-WK60-R2-C-AUTH", revoked: bool = False, expires_at_utc: str = "2099-01-01T00:00:00Z"):
    return {
        "authorization_id": auth_id,
        "mutation_authorized": True,
        "revoked": revoked,
        "expires_at_utc": expires_at_utc,
        "scope": {"domain": domain},
    }


def test_resolve_go_context_fails_closed_on_ambiguous_domain_and_unverified_identity(tmp_path, monkeypatch):
    state = tmp_path / ".git" / "universal-worker-queue"
    (state / "results").mkdir(parents=True)
    monkeypatch.setattr(service, "STATE_ROOT", state)

    # Ambiguous domain -> REQUEST_MINIMUM_INFO, mutation_allowed=False
    for bad in ("", "ALL", "GENERAL", "*"):
        res = service.resolve_go_context(domain=bad, current_user=_admin(), config_dir=tmp_path / "chains")
        assert res["mutation_allowed"] is False
        assert res["next_allowed_action"] == "REQUEST_MINIMUM_INFO"
        assert "domain" in res["missing_fields"]

    # Missing objective & no prior gate -> never implicitly authorizes mutation
    empty = service.resolve_go_context(domain="FINANZAS", current_user=_admin(), config_dir=tmp_path / "chains")
    assert empty["mutation_allowed"] is False
    assert empty["policy_tier"] == "READ_ONLY"
    assert empty["next_allowed_action"] == "REQUEST_MINIMUM_INFO"

    # Unverified identity -> HUMAN_APPROVAL_REQUIRED
    unauth = service.resolve_go_context(
        domain="RH",
        current_user={"id": "x"},
        objective_hint="Remediar aislamiento RBAC",
        config_dir=tmp_path / "chains",
    )
    assert unauth["mutation_allowed"] is False
    assert unauth["next_allowed_action"] == "HUMAN_APPROVAL_REQUIRED"

    # Non-admin operator -> READ_ONLY only, never mutation_allowed
    op = service.resolve_go_context(
        domain="RH",
        current_user=_operator(),
        objective_hint="Auditar RH",
        config_dir=tmp_path / "chains",
    )
    assert op["mutation_allowed"] is False
    assert op["policy_tier"] == "READ_ONLY"


def test_resolve_go_context_isolates_domains_and_never_infers_mutation_from_hint_or_rbac(tmp_path, monkeypatch):
    state = tmp_path / ".git" / "universal-worker-queue"
    (state / "results").mkdir(parents=True)
    (state / "pending").mkdir(parents=True)
    monkeypatch.setattr(service, "STATE_ROOT", state)

    (state / "results" / "SEM-RH-AUDIT-001.json").write_text(
        json.dumps(_certified_result("SEM-RH-AUDIT-001", "RH")), encoding="utf-8"
    )
    (state / "results" / "SEM-CRM-AUDIT-001.json").write_text(
        json.dumps(_certified_result("SEM-CRM-AUDIT-001", "CRM")), encoding="utf-8"
    )

    # Defect 5 & 6: Admin RBAC + objective_hint + prior certified gate MUST NOT imply mutation_allowed=True
    rh_readonly = service.resolve_go_context(
        domain="RH",
        current_user=_admin(),
        objective_hint="Continuar remediacion RH-R1",
        config_dir=tmp_path / "chains",
    )
    assert rh_readonly["last_certified_gate"]["job_id"] == "SEM-RH-AUDIT-001"
    assert rh_readonly["next_allowed_action"] == "CONTINUE_AUTONOMOUS"
    assert rh_readonly["policy_tier"] == "READ_ONLY"
    assert rh_readonly["mutation_allowed"] is False
    assert rh_readonly["production_touched"] is False

    # Even with no hint and a prior certified gate: policy_tier=READ_ONLY MUST imply mutation_allowed=False
    rh_no_hint = service.resolve_go_context(
        domain="RH",
        current_user=_admin(),
        config_dir=tmp_path / "chains",
    )
    assert rh_no_hint["policy_tier"] == "READ_ONLY"
    assert rh_no_hint["mutation_allowed"] is False

    # With explicit traceable domain-scoped authorization + admin RBAC -> DEVELOPMENT_MUTATION & mutation_allowed=True
    rh_authorized = service.resolve_go_context(
        domain="RH",
        current_user=_admin(),
        objective_hint="Continuar remediacion RH-R1",
        authorization_context=_explicit_auth("RH"),
        config_dir=tmp_path / "chains",
    )
    assert rh_authorized["policy_tier"] == "DEVELOPMENT_MUTATION"
    assert rh_authorized["mutation_allowed"] is True
    assert rh_authorized["active_authorizations"]["explicit_mutation_authorized"] is True

    # Cross-domain explicit authorization MUST fail closed
    rh_wrong_scope = service.resolve_go_context(
        domain="RH",
        current_user=_admin(),
        authorization_context=_explicit_auth("CRM"),
        config_dir=tmp_path / "chains",
    )
    assert rh_wrong_scope["mutation_allowed"] is False
    assert rh_wrong_scope["next_allowed_action"] == "HUMAN_APPROVAL_REQUIRED"
    assert rh_wrong_scope["reason"] == "SCOPE_AUTHORIZATION_DENIED"

    # Adding an in-flight RH job blocks RH mutations with WAIT, without blocking CRM
    (state / "pending" / "EDARSAHUB-BOS-RH-R1-001.json").write_text(
        json.dumps({"job_id": "EDARSAHUB-BOS-RH-R1-001", "scheduling": {"bounded_context": "RH"}}),
        encoding="utf-8",
    )
    rh_wait = service.resolve_go_context(
        domain="RH",
        current_user=_admin(),
        authorization_context=_explicit_auth("RH"),
        config_dir=tmp_path / "chains",
    )
    assert rh_wait["next_allowed_action"] == "WAIT_FOR_IN_FLIGHT_JOB"
    assert rh_wait["mutation_allowed"] is False
    assert len(rh_wait["pending_jobs"]) == 1
    assert rh_wait["lifecycle_summary"]["PENDING"] == ["EDARSAHUB-BOS-RH-R1-001"]

    crm_still_ok = service.resolve_go_context(
        domain="CRM",
        current_user=_admin(),
        authorization_context=_explicit_auth("CRM"),
        config_dir=tmp_path / "chains",
    )
    assert crm_still_ok["next_allowed_action"] == "CONTINUE_AUTONOMOUS"
    assert crm_still_ok["mutation_allowed"] is True
    assert crm_still_ok["pending_jobs"] == []


def test_r2c_request_result_association_timestamp_ordering_and_certified_successors(tmp_path, monkeypatch):
    state = tmp_path / ".git" / "universal-worker-queue"
    for sub in ("done", "drafts", "results", "published"):
        (state / sub).mkdir(parents=True)
    monkeypatch.setattr(service, "STATE_ROOT", state)

    # Older job with HIGHER mtime vs newer SEM-REQUEST-* job (without domain in filename) with LOWER mtime
    old_id = "SEM-WORKER_REPAIR_KNOWLEDGE_LOOP-OLD-001"
    new_id = "SEM-REQUEST-14446006023FD9F0BD75B226"
    other_domain_id = "SEM-REQUEST-8B9212718BB0F4281173735D"

    old_res = state / "results" / f"{old_id}.json"
    old_res.write_text(
        json.dumps(_certified_result(old_id, None, completed_at_utc="2026-11-24T04:07:15Z")),
        encoding="utf-8",
    )
    # Canonical request in done/ binds SEM-REQUEST-14446006023FD9F0BD75B226 to WORKER_REPAIR_KNOWLEDGE_LOOP
    (state / "done" / f"{new_id}.json").write_text(
        json.dumps({"job": {"job_id": new_id, "mode": "READ_ONLY", "scheduling": {"bounded_context": "WORKER_REPAIR_KNOWLEDGE_LOOP"}}}),
        encoding="utf-8",
    )
    new_res = state / "results" / f"{new_id}.json"
    new_res.write_text(
        json.dumps(_certified_result(new_id, None, completed_at_utc="2026-11-25T06:47:41Z")),
        encoding="utf-8",
    )
    (state / "published" / f"{new_id}.json").write_text(
        "published=2026-11-25T06:49:10Z\ncommit=9e2b8c2e1ae55de42847fe803af71b912042deaf\ncertification=CERTIFIED_READ_ONLY\n",
        encoding="utf-8",
    )

    # Another domain (WORKER_MCP) job promoted via published marker from PENDING_AUDIT_EVIDENCE -> CERTIFIED
    (state / "done" / f"{other_domain_id}.json").write_text(
        json.dumps({"job": {"job_id": other_domain_id, "mode": "MUTATION", "scheduling": {"bounded_context": "WORKER_MCP"}}}),
        encoding="utf-8",
    )
    (state / "results" / f"{other_domain_id}.json").write_text(
        json.dumps(_certified_result(
            other_domain_id,
            None,
            completed_at_utc="2026-11-25T05:46:55Z",
            status="INTEGRATED",
            certification="PENDING_AUDIT_EVIDENCE",
            commit_sha="690c3b9dcf2bee179fd3b31211b37f56ed0e3ef3",
        )),
        encoding="utf-8",
    )
    (state / "published" / f"{other_domain_id}.json").write_text(
        "published=2026-11-25T06:28:12Z\ncommit=ee607043b37ab0ac8f82a4fb34c05b396c76b811\ncertification=CERTIFIED\n",
        encoding="utf-8",
    )
    att_dir = tmp_path / ".git" / "mirror-sync" / "reporting" / "test_attestations"
    att_dir.mkdir(parents=True)
    (att_dir / "690c3b9dcf2bee179fd3b31211b37f56ed0e3ef3.json").write_text(
        json.dumps({
            "schema": "edarsahub.test-attestation.v1",
            "job_id": other_domain_id,
            "source_sha": "690c3b9dcf2bee179fd3b31211b37f56ed0e3ef3",
            "tests": "PASS",
            "quality_gate": "PASS",
            "production_touched": False,
            "files_changed": ["backend/modules/worker_mcp/server.py"],
        }),
        encoding="utf-8",
    )

    # Deliberately set old_res mtime NEWER than new_res mtime to prove mtime is ignored!
    os.utime(new_res, (1700000000, 1700000000))
    os.utime(old_res, (1900000000, 1900000000))

    kl_ctx = service.resolve_go_context(
        domain="WORKER_REPAIR_KNOWLEDGE_LOOP",
        current_user=_admin(),
        config_dir=tmp_path / "chains",
    )
    assert kl_ctx["last_certified_gate"]["job_id"] == new_id
    assert kl_ctx["last_certified_gate"]["certified_at_utc"] == "2026-11-25T06:49:10Z"
    assert kl_ctx["last_certified_gate"]["certification_source"] == "PUBLISHED_MARKER"
    assert kl_ctx["last_certified_gate"]["domain_binding_source"] == "REQUEST_SCHEDULING"
    assert [r["job_id"] for r in kl_ctx["certified_successors"]] == [new_id, old_id]
    assert kl_ctx["policy_tier"] == "READ_ONLY"
    assert kl_ctx["mutation_allowed"] is False

    mcp_ctx = service.resolve_go_context(
        domain="WORKER_MCP",
        current_user=_admin(),
        config_dir=tmp_path / "chains",
    )
    assert mcp_ctx["last_certified_gate"]["job_id"] == other_domain_id
    assert mcp_ctx["last_certified_gate"]["certification"] == "CERTIFIED"
    assert mcp_ctx["last_certified_gate"]["commit_sha"] == "690c3b9dcf2bee179fd3b31211b37f56ed0e3ef3"
    assert mcp_ctx["policy_tier"] == "READ_ONLY"
    assert mcp_ctx["mutation_allowed"] is False


def test_r2c_detects_unpublished_drafts_and_distinguishes_lifecycles(tmp_path, monkeypatch):
    state = tmp_path / ".git" / "universal-worker-queue"
    for sub in ("drafts", "pending", "processing", "results"):
        (state / sub).mkdir(parents=True)
    monkeypatch.setattr(service, "STATE_ROOT", state)

    draft_id = "SEM-REQUEST-DRAFT-RECOVERY-001"
    (state / "drafts" / f"{draft_id}.json").write_text(
        json.dumps({
            "schema": "edarsahub.worker-job.v2",
            "job_id": draft_id,
            "objective": "Recover unpublished draft",
            "mode": "READ_ONLY",
            "actions": [],
            "checks": [{"type": "git_diff_check"}],
            "requester": {"email": "ricardo@edarsa.com.mx", "source": "edarsahub-worker-ingress"},
            "scheduling": {"bounded_context": "WORKER_CONTROL_PLANE"},
            "target_repo": "rbalam/EDARSA_HUB",
            "target_branch": "Edarsahub_Desarrollo",
            "production_allowed": False,
        }),
        encoding="utf-8",
    )

    ctx = service.resolve_go_context(
        domain="WORKER_CONTROL_PLANE",
        current_user=_admin(),
        authorization_context=_explicit_auth("WORKER_CONTROL_PLANE"),
        config_dir=tmp_path / "chains",
    )
    assert ctx["next_allowed_action"] == "RECOVER_PENDING_DRAFT"
    assert ctx["reason"] == "DOMAIN_HAS_UNPUBLISHED_DRAFT_PENDING_RECOVERY"
    assert ctx["policy_tier"] == "READ_ONLY"
    assert ctx["mutation_allowed"] is False
    assert len(ctx["pending_drafts"]) == 1
    assert ctx["pending_drafts"][0]["job_id"] == draft_id
    assert ctx["pending_drafts"][0]["lifecycle"] == "DRAFT"
    assert ctx["pending_drafts"][0]["recovery_required"] is True
    assert ctx["lifecycle_summary"]["DRAFT"] == [draft_id]
    assert ctx["lifecycle_summary"]["PENDING"] == []
    assert ctx["lifecycle_summary"]["PROCESSING"] == []


def test_r2c_enforces_chain_domain_validation_and_authorized_chain_compatibility(tmp_path, monkeypatch):
    state = tmp_path / ".git" / "universal-worker-queue"
    chains_dir = tmp_path / "chains"
    (state / "results").mkdir(parents=True)
    chains_dir.mkdir(parents=True)
    monkeypatch.setattr(service, "STATE_ROOT", state)

    # Seed certified G1 for RH chain
    (state / "results" / "RH-GATE1-JOB.json").write_text(
        json.dumps(_certified_result("RH-GATE1-JOB", "RH")), encoding="utf-8"
    )

    chain_cfg = {
        "schema": "edarsahub.gate-chain.v1",
        "chain_id": "CHAIN-RH-V1",
        "domain": "RH",
        "enabled": True,
        "max_hops": 5,
        "start_gate_id": "G1",
        "authorization_classes": ["PREAUTHORIZED_CODE_MUTATION"],
        "gates": [
            {"gate_id": "G1", "job_id": "RH-GATE1-JOB", "mutation_class": "READ_ONLY", "next_gate_ids": ["G2"]},
            {"gate_id": "G2", "job_id": "RH-GATE2-JOB", "mutation_class": "CODE_MUTATION", "authorization_class": "PREAUTHORIZED_CODE_MUTATION", "next_gate_ids": []},
        ],
    }
    (chains_dir / "chain_rh.json").write_text(json.dumps(chain_cfg), encoding="utf-8")

    # Wrong domain requesting CHAIN-RH-V1 -> fail closed CHAIN_DOMAIN_MISMATCH
    mismatch = service.resolve_go_context(
        domain="CRM",
        chain_id="CHAIN-RH-V1",
        current_user=_admin(),
        config_dir=chains_dir,
    )
    assert mismatch["mutation_allowed"] is False
    assert mismatch["next_allowed_action"] == "HUMAN_APPROVAL_REQUIRED"
    assert mismatch["reason"] == "CHAIN_DOMAIN_MISMATCH"

    # Unknown chain_id -> fail closed CHAIN_NOT_FOUND
    missing = service.resolve_go_context(
        domain="RH",
        chain_id="CHAIN-DOES-NOT-EXIST",
        current_user=_admin(),
        config_dir=chains_dir,
    )
    assert missing["mutation_allowed"] is False
    assert missing["reason"] == "CHAIN_NOT_FOUND"
    assert "chain_id" in missing["missing_fields"]

    # Valid domain + authorized chain -> compatible DEVELOPMENT_MUTATION with verified dependency
    ok = service.resolve_go_context(
        domain="RH",
        chain_id="CHAIN-RH-V1",
        current_user=_admin(),
        config_dir=chains_dir,
    )
    assert ok["chain_id"] == "CHAIN-RH-V1"
    assert ok["policy_tier"] == "DEVELOPMENT_MUTATION"
    assert ok["mutation_allowed"] is True
    assert ok["next_allowed_action"] == "CONTINUE_AUTONOMOUS"
    assert ok["reason"] == "CHAIN_TRANSITION_READY"
    assert len(ok["gate_dependencies"]) == 1
    assert ok["gate_dependencies"][0]["requires_certified_gate"] == "G1"
    assert ok["gate_dependencies"][0]["predecessor_verified"] is True
    assert ok["gate_dependencies"][0]["next_gate_id"] == "G2"

    # Ambiguous multiple enabled chains in same domain without chain_id -> fail closed
    chain_cfg_2 = {**chain_cfg, "chain_id": "CHAIN-RH-V2"}
    (chains_dir / "chain_rh_2.json").write_text(json.dumps(chain_cfg_2), encoding="utf-8")
    ambig = service.resolve_go_context(
        domain="RH",
        current_user=_admin(),
        config_dir=chains_dir,
    )
    assert ambig["mutation_allowed"] is False
    assert ambig["reason"] == "AMBIGUOUS_DOMAIN_CHAINS"
    assert "chain_id" in ambig["missing_fields"]


def test_context_route_enforces_rbac_scope(monkeypatch):
    def deny(**kwargs):
        raise ingress_routes.OAuthValidationError("INSUFFICIENT_SCOPE")

    monkeypatch.setattr(ingress_routes, "enforce_internal_jwt_mcp_scope", deny)
    with pytest.raises(HTTPException) as exc_info:
        ingress_routes.read_worker_go_context(
            domain="RH",
            current_user=_operator(),
            authorization="Bearer bad",
        )
    assert exc_info.value.status_code == 403
