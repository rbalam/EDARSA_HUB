from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from modules.auth.repository import AuthRepository
from tools.mirror_sync import gate_chain_publisher as publisher
from tools.mirror_sync.gate_chain_publisher import (
    build_plan,
    publish,
    submit,
    validate_template,
)
from tools.mirror_sync.worker_job_factory import canonicalize_job
from tools.mirror_sync.worker_requester_rbac import authorize_requester


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------

def valid_raw_job(
    job_id: str = "FLOW-CERT-001",
    email: str = "superadmin@edarsa.com.mx",
) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "objective": "Certificar flujo canonico universal worker",
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [
            {
                "type": "git_diff_check",
            }
        ],
        "requester": {
            "email": email,
            "source": "chatgpt-worker-cert",
            "project": "EDARSAHUB",
            "chat": "universal-worker-flow",
        },
    }


def superadmin_user(email: str = "superadmin@edarsa.com.mx") -> dict[str, Any]:
    return {
        "UsuarioID": 42,
        "_sql_usuario_id": 42,
        "email": email,
        "role_code": "SUPERADMIN",
        "_sql_rol_codigo": "SUPERADMIN",
        "role": "SUPERADMINISTRADOR",
        "active": True,
        "auth_source": "SQL_USUARIO_CATALOGO",
    }


def non_superadmin_user(
    email: str = "operador@edarsa.com.mx",
    role_code: str = "OPERADOR",
) -> dict[str, Any]:
    return {
        "UsuarioID": 99,
        "_sql_usuario_id": 99,
        "email": email,
        "role_code": role_code,
        "_sql_rol_codigo": role_code,
        "role": role_code,
        "active": True,
        "auth_source": "SQL_USUARIO_CATALOGO",
    }


@pytest.fixture
def isolated_queue_dirs(tmp_path, monkeypatch):
    """Redirect publisher queue directories into tmp_path to prevent side-effects."""
    dirs = {}
    for name in (
        "DRAFTS",
        "PENDING",
        "PROCESSING",
        "RESULTS",
        "DONE",
        "REJECTED",
    ):
        path = tmp_path / "queue" / name.lower()
        path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(publisher, name, path)
        dirs[name] = path
    return dirs


# ---------------------------------------------------------------------------
# 1. Flujo real: canonicalize_job -> validate -> authorize_requester -> publish
# ---------------------------------------------------------------------------

def test_flow_step_by_step_canonicalize_to_publish_success(tmp_path, monkeypatch):
    raw = valid_raw_job("FLOW-STEP-001")

    # Step 1: canonicalize_job supplies canonical invariants
    canonical = canonicalize_job(raw)
    assert canonical["schema"] == "edarsahub.worker-job.v2"
    assert canonical["target_repo"] == "rbalam/EDARSA_HUB"
    assert canonical["target_branch"] == "Edarsahub_Desarrollo"
    assert canonical["production_allowed"] is False
    assert canonical["human_summary_language"] == "es"
    assert canonical["scheduling"]["conflict_domains"] == ["GLOBAL_GIT_WRITER"]

    # Step 2: validate_template validates structure and safe checks
    validated = validate_template(canonical)
    assert validated["job_id"] == "FLOW-STEP-001"
    assert validated["mode"] == "READ_ONLY"

    # Step 3: authorize_requester validates requester RBAC via SQL user catalog
    monkeypatch.setattr(
        AuthRepository,
        "get_user_by_email",
        lambda email: superadmin_user(email),
    )
    auth = authorize_requester(validated["requester"])
    assert auth["allowed"] is True
    assert auth["reason"] == "SUPERADMIN_CANONICAL"
    assert auth["usuario_id"] == 42

    # Step 4: publish execution with mocked git boundaries
    plan = {
        "status": "READY_TO_PUBLISH",
        "job_id": validated["job_id"],
        "template": validated,
    }

    mock_wt = tmp_path / "mock_wt"
    mock_wt.mkdir(parents=True, exist_ok=True)

    base_sha = "1111111111111111111111111111111111111111"
    candidate_sha = "2222222222222222222222222222222222222222"

    state = {
        "rev_parse_head_calls": 0,
        "pushed": False,
    }

    def fake_git(*args, **kwargs):
        cwd = kwargs.get("cwd")
        cmd = args[0] if args else ""
        res = MagicMock(returncode=0, stdout="")

        if cmd == "fetch":
            return res
        if cmd == "rev-parse":
            target = args[1] if len(args) > 1 else ""
            if target == "HEAD" and cwd == mock_wt:
                state["rev_parse_head_calls"] += 1
                # First call before commit returns base_sha, subsequent returns candidate_sha
                res.stdout = candidate_sha if state["rev_parse_head_calls"] > 1 else base_sha
            elif target == f"{candidate_sha}^":
                res.stdout = base_sha
            elif "worker/requests" in target:
                res.stdout = base_sha
            else:
                res.stdout = base_sha
            return res
        if cmd == "cat-file":
            # Before push, file doesn't exist on remote; after push, it does
            if "-e" in args:
                res.returncode = 0 if state["pushed"] else 1
            return res
        if cmd == "add":
            return res
        if cmd == "diff":
            res.stdout = f"worker_queue/inbox/{validated['job_id']}.json\n"
            return res
        if cmd == "commit":
            return res
        return res

    monkeypatch.setattr(publisher, "git", fake_git)
    monkeypatch.setattr(
        publisher,
        "_prepare_queue_worktree",
        lambda job_id, queue_base, rel: (mock_wt, f"agent/queue-publisher/{job_id}", f"agent-{job_id}", f"task-{job_id}"),
    )
    monkeypatch.setattr(
        publisher,
        "validate_commit_scope",
        lambda wt, base, cand, scope: None,
    )

    push_called = []
    def fake_push(*args, **kwargs):
        push_called.append((args, kwargs))
        state["pushed"] = True
        res = MagicMock()
        res.returncode = 0
        res.stdout = "pushed"
        return res

    monkeypatch.setattr(publisher, "authorized_push", fake_push)
    monkeypatch.setattr(publisher, "_cleanup_queue_worktree", lambda **kwargs: [])

    # Remote head before push is base_sha, after push is candidate_sha
    def fake_remote_head(remote, queue_branch):
        return candidate_sha if state["pushed"] else base_sha

    monkeypatch.setattr(publisher, "_queue_remote_head", fake_remote_head)

    publication = publish(plan)
    assert publication["status"] == "PUBLISHED"
    assert publication["job_id"] == "FLOW-STEP-001"
    assert publication["commit_sha"] == candidate_sha
    assert publication["production_touched"] is False
    assert publication["result"] == "GATE_ENQUEUED=PASS"
    assert len(push_called) == 1


def test_flow_integrated_submit_success(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-INTEGRATED-001")

    monkeypatch.setattr(
        AuthRepository,
        "get_user_by_email",
        lambda email: superadmin_user(email),
    )
    monkeypatch.setattr(
        publisher,
        "_submit_remote_exists",
        lambda job_id, **kw: False,
    )
    monkeypatch.setattr(
        publisher,
        "_submit_convergence",
        lambda **kw: {"converged": True, "status": "CONVERGED"},
    )

    fake_publication = {
        "status": "PUBLISHED",
        "job_id": "FLOW-INTEGRATED-001",
        "commit_sha": "3333333333333333333333333333333333333333",
        "production_touched": False,
        "result": "GATE_ENQUEUED=PASS",
    }
    monkeypatch.setattr(
        publisher,
        "publish",
        lambda plan, **kw: fake_publication,
    )

    result = submit(raw)

    assert result["status"] == "SUBMITTED"
    assert result["job_id"] == "FLOW-INTEGRATED-001"
    assert result["production_touched"] is False
    assert result["preflight_convergence"]["converged"] is True

    draft_path = Path(result["draft_path"])
    assert draft_path.is_file()
    draft_data = json.loads(draft_path.read_text(encoding="utf-8"))
    assert draft_data["job_id"] == "FLOW-INTEGRATED-001"
    assert draft_data["production_allowed"] is False
    assert draft_data["schema"] == "edarsahub.worker-job.v2"


# ---------------------------------------------------------------------------
# 2. Rechazo de JOB inválido
# ---------------------------------------------------------------------------

def test_invalid_job_rejected_non_dict(isolated_queue_dirs):
    result = submit("NOT_A_DICT")  # type: ignore
    assert result["status"] == "INVALID_JOB"
    assert result["production_touched"] is False


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_match"),
    [
        ("target_repo", "evil/repo", "CANONICAL_FIELD_CONFLICT:target_repo"),
        ("target_branch", "main", "CANONICAL_FIELD_CONFLICT:target_branch"),
        ("target_branch", "Edarsahub_Produccion", "CANONICAL_FIELD_CONFLICT:target_branch"),
        ("production_allowed", True, "CANONICAL_FIELD_CONFLICT:production_allowed"),
        ("human_summary_language", "en", "CANONICAL_FIELD_CONFLICT:human_summary_language"),
        ("schema", "invalid.schema.v1", "CANONICAL_FIELD_CONFLICT:schema"),
    ],
)
def test_invalid_job_rejected_transport_drift(isolated_queue_dirs, field, bad_value, expected_match):
    raw = valid_raw_job("FLOW-BAD-TRANSPORT")
    raw[field] = bad_value

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert expected_match in result["reason"]
    assert result["production_touched"] is False


@pytest.mark.parametrize(
    "bad_job_id",
    [
        "",
        "   ",
        "-bad-start",
        ".bad-start",
        "bad spaces in id",
        "x" * 125,
        "bad$char",
    ],
)
def test_invalid_job_rejected_bad_job_id(isolated_queue_dirs, bad_job_id):
    raw = valid_raw_job("VALID")
    raw["job_id"] = bad_job_id

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert result["production_touched"] is False


def test_invalid_job_rejected_missing_objective(isolated_queue_dirs):
    raw = valid_raw_job("FLOW-NO-OBJ")
    raw["objective"] = ""

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert "OBJECTIVE_REQUIRED" in result["reason"]
    assert result["production_touched"] is False


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "sql",
        "command",
        "commands",
        "shell",
        "script_body",
        "password",
        "passwd",
        "secret",
        "token",
        "credential",
    ],
)
def test_invalid_job_rejected_forbidden_keys(isolated_queue_dirs, forbidden_key):
    raw = valid_raw_job("FLOW-FORBIDDEN-KEY")
    raw[forbidden_key] = "malicious_payload"

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert f"FORBIDDEN_TEMPLATE_KEY:{forbidden_key}" in result["reason"]
    assert result["production_touched"] is False


def test_invalid_job_rejected_nested_forbidden_key(isolated_queue_dirs):
    raw = valid_raw_job("FLOW-FORBIDDEN-NESTED")
    raw["requester"]["sql"] = "SELECT * FROM users"

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert "FORBIDDEN_TEMPLATE_KEY:sql" in result["reason"]
    assert result["production_touched"] is False


def test_invalid_job_rejected_unsupported_action(isolated_queue_dirs):
    raw = valid_raw_job("FLOW-BAD-ACTION")
    raw["actions"] = [{"type": "run_shell_arbitrary"}]

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert "UNSUPPORTED_ACTION" in result["reason"]
    assert result["production_touched"] is False


def test_invalid_job_rejected_unsupported_check(isolated_queue_dirs):
    raw = valid_raw_job("FLOW-BAD-CHECK")
    raw["checks"] = [{"type": "arbitrary_remote_exec"}]

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert "UNSUPPORTED_CHECK" in result["reason"]
    assert result["production_touched"] is False


def test_invalid_job_rejected_by_bridge_validation(isolated_queue_dirs):
    raw = valid_raw_job("FLOW-BAD-BRIDGE")
    raw["checks"] = [{"type": "pytest", "paths": []}]

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert "errors" in result
    assert any("INVALID_PATHS" in err for err in result["errors"])
    assert result["production_touched"] is False


# ---------------------------------------------------------------------------
# 3. RBAC denegado
# ---------------------------------------------------------------------------

def test_rbac_denied_missing_requester(isolated_queue_dirs):
    raw = valid_raw_job("FLOW-NO-REQ")
    del raw["requester"]

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert "REQUESTER_REQUIRED" in result["reason"]


def test_rbac_denied_invalid_requester_email(isolated_queue_dirs):
    raw = valid_raw_job("FLOW-BAD-EMAIL")
    raw["requester"]["email"] = "not-an-email"

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert "REQUESTER_EMAIL_INVALID" in result["reason"]


def test_rbac_denied_missing_requester_source(isolated_queue_dirs):
    raw = valid_raw_job("FLOW-NO-SRC")
    raw["requester"]["source"] = ""

    result = submit(raw)
    assert result["status"] == "INVALID_JOB"
    assert "REQUESTER_SOURCE_REQUIRED" in result["reason"]


def test_rbac_denied_user_not_found(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-NOT-FOUND", email="unknown@edarsa.com.mx")
    monkeypatch.setattr(AuthRepository, "get_user_by_email", lambda email: None)

    auth = authorize_requester(raw["requester"])
    assert auth["allowed"] is False
    assert auth["reason"] == "REQUESTER_NOT_FOUND"

    result = submit(raw)
    assert result["status"] == "REQUESTER_DENIED"
    assert result["reason"] == "REQUESTER_NOT_FOUND"
    assert result["production_touched"] is False


def test_rbac_denied_user_inactive(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-INACTIVE", email="inactive@edarsa.com.mx")
    user = superadmin_user(email="inactive@edarsa.com.mx")
    user["active"] = False

    monkeypatch.setattr(AuthRepository, "get_user_by_email", lambda email: user)

    auth = authorize_requester(raw["requester"])
    assert auth["allowed"] is False
    assert auth["reason"] == "REQUESTER_INACTIVE"

    result = submit(raw)
    assert result["status"] == "REQUESTER_DENIED"
    assert result["reason"] == "REQUESTER_INACTIVE"
    assert result["production_touched"] is False


@pytest.mark.parametrize(
    "role_code",
    ["OPERADOR", "AUDITOR", "GERENTE", "CONSULTA", "ADMINISTRADOR"],
)
def test_rbac_denied_user_not_superadmin(isolated_queue_dirs, monkeypatch, role_code):
    raw = valid_raw_job("FLOW-NON-SUPERADMIN", email=f"{role_code.lower()}@edarsa.com.mx")
    user = non_superadmin_user(email=raw["requester"]["email"], role_code=role_code)

    monkeypatch.setattr(AuthRepository, "get_user_by_email", lambda email: user)

    auth = authorize_requester(raw["requester"])
    assert auth["allowed"] is False
    assert auth["reason"] == "REQUESTER_NOT_SUPERADMIN"
    assert auth["role_code"] == role_code

    result = submit(raw)
    assert result["status"] == "REQUESTER_DENIED"
    assert result["reason"] == "REQUESTER_NOT_SUPERADMIN"
    assert result["production_touched"] is False


# ---------------------------------------------------------------------------
# 4. Errores de autorización
# ---------------------------------------------------------------------------

def test_authorization_error_db_lookup_failed(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-DB-FAIL")

    def raise_db_error(email):
        raise RuntimeError("SQL_SERVER_CONNECTION_TIMEOUT")

    monkeypatch.setattr(AuthRepository, "get_user_by_email", raise_db_error)

    auth = authorize_requester(raw["requester"])
    assert auth["allowed"] is False
    assert auth["reason"] == "REQUESTER_RBAC_LOOKUP_FAILED"

    result = submit(raw)
    assert result["status"] == "REQUESTER_DENIED"
    assert result["reason"] == "REQUESTER_RBAC_LOOKUP_FAILED"
    assert result["production_touched"] is False


def test_authorization_error_unexpected_exception(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-AUTH-EXC")

    import tools.mirror_sync.worker_requester_rbac as rbac_mod
    monkeypatch.setattr(
        rbac_mod,
        "authorize_requester",
        MagicMock(side_effect=TypeError("UNEXPECTED_AUTHORIZATION_FAULT")),
    )

    result = submit(raw)
    assert result["status"] == "REQUESTER_DENIED"
    assert "TypeError:UNEXPECTED_AUTHORIZATION_FAULT" in result["reason"]
    assert result["production_touched"] is False


# ---------------------------------------------------------------------------
# 5. Duplicados
# ---------------------------------------------------------------------------

def test_duplicate_local_results_already_completed(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-DUP-DONE")
    (isolated_queue_dirs["RESULTS"] / "FLOW-DUP-DONE.json").write_text("{}", encoding="utf-8")

    result = submit(raw)
    assert result["status"] == "ALREADY_COMPLETED"
    assert result["job_id"] == "FLOW-DUP-DONE"
    assert result["production_touched"] is False


def test_duplicate_local_processing_already_processing(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-DUP-PROCESSING")
    (isolated_queue_dirs["PROCESSING"] / "FLOW-DUP-PROCESSING.json").write_text("{}", encoding="utf-8")

    result = submit(raw)
    assert result["status"] == "ALREADY_PROCESSING"
    assert result["job_id"] == "FLOW-DUP-PROCESSING"
    assert result["production_touched"] is False


def test_duplicate_local_pending_already_submitted(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-DUP-PENDING")
    (isolated_queue_dirs["PENDING"] / "FLOW-DUP-PENDING.json").write_text("{}", encoding="utf-8")

    result = submit(raw)
    assert result["status"] == "ALREADY_SUBMITTED"
    assert result["job_id"] == "FLOW-DUP-PENDING"
    assert result["production_touched"] is False


def test_duplicate_remote_exists(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-DUP-REMOTE")
    monkeypatch.setattr(publisher, "_submit_remote_exists", lambda job_id, **kw: True)

    result = submit(raw)
    assert result["status"] == "ALREADY_SUBMITTED"
    assert result["job_id"] == "FLOW-DUP-REMOTE"
    assert result["production_touched"] is False


def test_duplicate_in_build_plan():
    chain = {
        "schema": "edarsahub.gate-chain.v1",
        "chain_id": "TEST-CHAIN",
        "enabled": True,
        "max_hops": 3,
        "start_gate_id": "GATE-1",
        "gates": [
            {
                "gate_id": "GATE-1",
                "job_id": "ALREADY-EXISTS-ID",
                "mutation_class": "READ_ONLY",
                "next_gate_ids": [],
                "job_template": valid_raw_job("ALREADY-EXISTS-ID"),
            }
        ],
    }
    decision = {"state": "READY", "next_gate_id": "GATE-1"}

    plan = build_plan(chain, decision, {"ALREADY-EXISTS-ID"})
    assert plan["status"] == "EXISTS"
    assert plan["publish"] is False
    assert plan["job_id"] == "ALREADY-EXISTS-ID"


def test_duplicate_plan_publish_returns_remote_job_exists():
    plan = {
        "status": "EXISTS",
        "job_id": "DUP-PLAN-001",
        "publish": False,
    }
    res = publish(plan)
    assert res["result"] == "REMOTE_JOB=EXISTS"
    assert res["status"] == "EXISTS"
    assert res["publish"] is False


def test_duplicate_detected_inside_publish_cat_file(tmp_path, monkeypatch):
    raw = valid_raw_job("DUP-INSIDE-PUB")
    plan = {
        "status": "READY_TO_PUBLISH",
        "job_id": raw["job_id"],
        "template": raw,
    }

    base_sha = "4444444444444444444444444444444444444444"

    def fake_git(*args, **kwargs):
        cmd = args[0] if args else ""
        res = MagicMock(returncode=0)
        if cmd == "rev-parse":
            res.stdout = base_sha
            return res
        if cmd == "cat-file":
            res.returncode = 0
            return res
        return res

    monkeypatch.setattr(publisher, "git", fake_git)

    res = publish(plan)
    assert res["status"] == "EXISTS"
    assert res["publish"] is False
    assert res["result"] == "REMOTE_JOB=EXISTS"


# ---------------------------------------------------------------------------
# 6. Concurrencia Git
# ---------------------------------------------------------------------------

def test_git_concurrency_remote_moved_retryable(tmp_path, isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-REMOTE-MOVED")

    monkeypatch.setattr(AuthRepository, "get_user_by_email", lambda email: superadmin_user(email))
    monkeypatch.setattr(publisher, "_submit_remote_exists", lambda job_id, **kw: False)
    monkeypatch.setattr(publisher, "_submit_convergence", lambda **kw: {"converged": True, "status": "CONVERGED"})

    def mock_publish_remote_moved(plan, **kwargs):
        raise RuntimeError("REMOTE_MOVED_RETRY_REQUIRED:start=1111:now=2222")

    monkeypatch.setattr(publisher, "publish", mock_publish_remote_moved)

    result = submit(raw)
    assert result["status"] == "REMOTE_MOVED_RETRYABLE"
    assert result["job_id"] == "FLOW-REMOTE-MOVED"
    assert result["production_touched"] is False
    assert "REMOTE_MOVED_RETRY_REQUIRED" in result["reason"]


def test_git_concurrency_preflight_divergence_blocked(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-DIVERGENCE")

    monkeypatch.setattr(AuthRepository, "get_user_by_email", lambda email: superadmin_user(email))
    monkeypatch.setattr(publisher, "_submit_remote_exists", lambda job_id, **kw: False)

    monkeypatch.setattr(
        publisher,
        "_submit_convergence",
        lambda **kw: {"converged": False, "status": "GIT_DIVERGENCE_BLOCKED"},
    )

    publish_called = []
    monkeypatch.setattr(publisher, "publish", lambda *args, **kw: publish_called.append(args))

    result = submit(raw)
    assert result["status"] == "GIT_DIVERGENCE_BLOCKED"
    assert result["job_id"] == "FLOW-DIVERGENCE"
    assert result["production_touched"] is False
    assert len(publish_called) == 0


def test_submit_decoupled_from_mirror_divergence_by_default(isolated_queue_dirs, monkeypatch):
    """Certify that submit() does not block queue requests on code-branch mirror divergence."""
    raw = valid_raw_job("FLOW-DECOUPLED-CONV")

    monkeypatch.setattr(AuthRepository, "get_user_by_email", lambda email: superadmin_user(email))
    monkeypatch.setattr(publisher, "_submit_remote_exists", lambda job_id, **kw: False)

    fake_publication = {
        "status": "PUBLISHED",
        "job_id": "FLOW-DECOUPLED-CONV",
        "commit_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "production_touched": False,
        "result": "GATE_ENQUEUED=PASS",
    }
    monkeypatch.setattr(publisher, "publish", lambda plan, **kw: fake_publication)

    # Note: _submit_convergence is NOT mocked here! Real _submit_convergence runs.
    result = submit(raw)
    assert result["status"] == "SUBMITTED"
    assert result["job_id"] == "FLOW-DECOUPLED-CONV"
    assert result["preflight_convergence"]["converged"] is True
    assert result["preflight_convergence"]["status"] == "QUEUE_CONVERGED"
    assert result["production_touched"] is False


def test_submit_enforces_mirror_convergence_when_explicitly_requested(isolated_queue_dirs, monkeypatch):
    """Certify that submit(require_convergence=True) calls ensure_submit_convergence."""
    raw = valid_raw_job("FLOW-REQ-CONV")

    monkeypatch.setattr(AuthRepository, "get_user_by_email", lambda email: superadmin_user(email))
    monkeypatch.setattr(publisher, "_submit_remote_exists", lambda job_id, **kw: False)

    # When require_convergence=True is explicitly passed, real ensure_submit_convergence runs
    result = submit(raw, require_convergence=True)
    # In an agent worktree, convergence fails with BLOCKED status (e.g. BLOCKED_LOCAL_NOT_DEVELOPMENT or BLOCKED_DIVERGENCE_CONFLICT)
    assert result["status"].startswith("BLOCKED")
    assert result["preflight_convergence"]["converged"] is False
    assert result["production_touched"] is False


def test_submit_enforces_mirror_convergence_via_env_var(isolated_queue_dirs, monkeypatch):
    """Certify that EDARSAHUB_WORKER_SUBMIT_REQUIRE_CONVERGENCE=1 activates convergence check."""
    raw = valid_raw_job("FLOW-ENV-CONV")

    monkeypatch.setattr(AuthRepository, "get_user_by_email", lambda email: superadmin_user(email))
    monkeypatch.setattr(publisher, "_submit_remote_exists", lambda job_id, **kw: False)
    monkeypatch.setenv("EDARSAHUB_WORKER_SUBMIT_REQUIRE_CONVERGENCE", "1")

    result = submit(raw)
    assert result["status"].startswith("BLOCKED")
    assert result["preflight_convergence"]["converged"] is False
    assert result["production_touched"] is False


def test_git_concurrency_writer_busy(isolated_queue_dirs, monkeypatch):
    raw = valid_raw_job("FLOW-WRITER-BUSY")

    monkeypatch.setattr(AuthRepository, "get_user_by_email", lambda email: superadmin_user(email))
    monkeypatch.setattr(publisher, "_submit_remote_exists", lambda job_id, **kw: False)
    monkeypatch.setattr(publisher, "_submit_convergence", lambda **kw: {"converged": True, "status": "CONVERGED"})

    monkeypatch.setattr(
        publisher,
        "publish",
        MagicMock(side_effect=RuntimeError("GIT_LOCK_BUSY: locked by another process")),
    )

    result = submit(raw)
    assert result["status"] == "WRITER_BUSY"
    assert result["production_touched"] is False


def test_git_concurrency_staged_scope_mismatch(tmp_path, monkeypatch):
    raw = valid_raw_job("FLOW-SCOPE-MISMATCH")
    plan = {
        "status": "READY_TO_PUBLISH",
        "job_id": raw["job_id"],
        "template": raw,
    }

    mock_wt = tmp_path / "mock_wt_scope"
    mock_wt.mkdir(parents=True, exist_ok=True)
    base_sha = "5555555555555555555555555555555555555555"

    def fake_git(*args, **kwargs):
        cmd = args[0] if args else ""
        res = MagicMock(returncode=0)
        if cmd == "rev-parse":
            res.stdout = base_sha
            return res
        if cmd == "cat-file":
            res.returncode = 1
            return res
        if cmd == "diff":
            # Extra file staged
            res.stdout = f"worker_queue/inbox/{raw['job_id']}.json\nextra_unauthorized_file.py\n"
            return res
        return res

    monkeypatch.setattr(publisher, "git", fake_git)
    monkeypatch.setattr(
        publisher,
        "_prepare_queue_worktree",
        lambda job_id, queue_base, rel: (mock_wt, f"agent/{job_id}", f"agent-{job_id}", f"task-{job_id}"),
    )
    monkeypatch.setattr(publisher, "_cleanup_queue_worktree", lambda **kw: [])

    with pytest.raises(RuntimeError, match="STAGED_SCOPE_MISMATCH"):
        publish(plan)


def test_git_concurrency_lineage_invalid(tmp_path, monkeypatch):
    raw = valid_raw_job("FLOW-LINEAGE-FAIL")
    plan = {
        "status": "READY_TO_PUBLISH",
        "job_id": raw["job_id"],
        "template": raw,
    }

    mock_wt = tmp_path / "mock_wt_lineage"
    mock_wt.mkdir(parents=True, exist_ok=True)
    base_sha = "6666666666666666666666666666666666666666"
    candidate_sha = "7777777777777777777777777777777777777777"
    bad_parent_sha = "8888888888888888888888888888888888888888"

    rev_parse_head_count = {"count": 0}

    def fake_git(*args, **kwargs):
        cmd = args[0] if args else ""
        res = MagicMock(returncode=0)
        if cmd == "rev-parse":
            target = args[1] if len(args) > 1 else ""
            if target == "HEAD" and kwargs.get("cwd") == mock_wt:
                rev_parse_head_count["count"] += 1
                # Before commit: current_head == base_sha (so resumed_existing is False)
                # After commit: candidate == candidate_sha
                res.stdout = candidate_sha if rev_parse_head_count["count"] > 1 else base_sha
                return res
            if target == f"{candidate_sha}^":
                res.stdout = bad_parent_sha  # Doesn't match base_sha
                return res
            res.stdout = base_sha
            return res
        if cmd == "cat-file":
            res.returncode = 1
            return res
        if cmd == "diff":
            res.stdout = f"worker_queue/inbox/{raw['job_id']}.json\n"
            return res
        return res

    monkeypatch.setattr(publisher, "git", fake_git)
    monkeypatch.setattr(
        publisher,
        "_prepare_queue_worktree",
        lambda job_id, queue_base, rel: (mock_wt, f"agent/{job_id}", f"agent-{job_id}", f"task-{job_id}"),
    )
    monkeypatch.setattr(publisher, "_cleanup_queue_worktree", lambda **kw: [])

    with pytest.raises(RuntimeError, match="QUEUE_PUBLISHER_LINEAGE_INVALID"):
        publish(plan)


# ---------------------------------------------------------------------------
# 7. Invariantes de Seguridad y Producción Intacta
# ---------------------------------------------------------------------------

def test_production_allowed_never_permitted():
    job = valid_raw_job("FLOW-PROD-GUARD")
    job["production_allowed"] = True

    with pytest.raises(ValueError, match="CANONICAL_FIELD_CONFLICT:production_allowed"):
        canonicalize_job(job)

    with pytest.raises(ValueError, match="CANONICAL_FIELD_CONFLICT:production_allowed"):
        validate_template(job)


def test_system_deps_file_remains_untouched():
    """Verify system_deps.txt is never referenced or modified by publisher flow."""
    source = Path(publisher.__file__).read_text(encoding="utf-8")
    assert "system_deps.txt" not in source
    assert ".emergent" not in source


# ---------------------------------------------------------------------------
# 8. Contrato y Validación de JOB Usuarios/RBAC Preparado
# ---------------------------------------------------------------------------

def test_prepared_usuarios_rbac_readiness_job_contract():
    """Certify that the prepared Usuarios/RBAC readiness job is valid and compliant."""
    from tools.mirror_sync.universal_job_bridge import validate as validate_bridge

    root = Path(__file__).resolve().parents[2]
    job_path = root / "worker_queue" / "triggers" / "BOS-USUARIOS-RBAC-IMPLEMENTATION-READINESS-R1-20261020.json"
    assert job_path.is_file(), f"Prepared job file not found at {job_path}"

    payload = json.loads(job_path.read_text(encoding="utf-8"))

    # Canonicalize and validate
    canonical = validate_template(payload)
    assert canonical["schema"] == "edarsahub.worker-job.v2"
    assert canonical["job_id"] == "BOS-USUARIOS-RBAC-IMPLEMENTATION-READINESS-R1-20261020"
    assert canonical["target_repo"] == "rbalam/EDARSA_HUB"
    assert canonical["target_branch"] == "Edarsahub_Desarrollo"
    assert canonical["production_allowed"] is False
    assert canonical["mode"] == "READ_ONLY"
    assert canonical["actions"] == []

    # Bridge validation
    errors = validate_bridge(canonical)
    assert not errors, f"Bridge validation failed with errors: {errors}"

    # Verify structured readiness proposals
    proposals = canonical.get("readiness_proposals") or {}
    assert len(proposals) == 6
    expected_areas = [
        "1_autenticacion_identidad",
        "2_jerarquia_empresas_unidades_sucursales",
        "3_contexto_roles_alcance",
        "4_permisos_efectivos",
        "5_aislamiento_corporativo",
        "6_menu_usuarios",
    ]
    for area in expected_areas:
        assert area in proposals, f"Missing proposal area: {area}"
        data = proposals[area]
        assert "estado_actual" in data
        assert "fuente_canonica" in data
        assert "propuesta_correccion" in data
