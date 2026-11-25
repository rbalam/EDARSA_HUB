"""Security and ingress contract for WORKER_RESULT_DETAIL_READ."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules.worker_ingress import service
from modules.worker_ingress.semantic_capabilities import (
    registered_capabilities,
)
from tools.mirror_sync import (
    gate_chain_publisher as publisher,
)
from tools.mirror_sync import (
    universal_job_bridge as bridge,
)
from tools.mirror_sync import (
    worker_result_detail_read as detail,
)


SOURCE_JOB = (
    "EDARSAHUB-WORKER-TEST-"
    "FAILED-R1"
)


def _write_result(
    directory: Path,
    payload: dict,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        directory
        / f"{SOURCE_JOB}.json"
    ).write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_detail_reader_returns_only_bounded_failure_evidence(
    tmp_path,
    monkeypatch,
):
    results = tmp_path / "results"

    _write_result(
        results,
        {
            "schema": "edarsahub.worker-result.v2",
            "job_id": SOURCE_JOB,
            "status": "GIT_TESTS_FAILED",
            "quality_gate": "FAIL",
            "tests": "FAIL",
            "certification": "NOT_CERTIFIED",
            "work_completion": "NOT_CERTIFIED",
            "percent_complete": 80,
            "blockers": [
                "check_failed:pytest",
            ],
            "files_changed": [
                "backend/tests/test_x.py",
            ],
            "checks": [
                {
                    "type": "pytest",
                    "status": "FAIL",
                    "returncode": 1,
                    "output": (
                        "FAILED test_x.py::test_x\\n"
                        "E   AssertionError: expected R2\\n"
                    ),
                },
            ],
            "production_touched": False,
            "arbitrary_private_payload": {
                "do_not_export": "PRIVATE"
            },
        },
    )

    monkeypatch.setattr(
        detail,
        "RESULTS",
        results,
    )

    report = detail.collect(
        SOURCE_JOB
    )

    assert report["status"] == "PASS"
    assert report["result_status"] == (
        "GIT_TESTS_FAILED"
    )
    assert report["failed_check_count"] == 1
    assert report["failed_checks"][0][
        "type"
    ] == "pytest"

    assert (
        "AssertionError"
        in report["failed_checks"][0][
            "output"
        ]
    )

    serialized = json.dumps(report)

    assert "PRIVATE" not in serialized
    assert (
        "arbitrary_private_payload"
        not in serialized
    )


def test_detail_reader_redacts_sensitive_output(
    tmp_path,
    monkeypatch,
):
    results = tmp_path / "results"

    fake_secret = (
        "tok"
        "en=FICTITIOUS_SECRET_123456"
    )

    _write_result(
        results,
        {
            "status": "GIT_TESTS_FAILED",
            "checks": [
                {
                    "type": "pytest",
                    "status": "FAIL",
                    "returncode": 1,
                    "output": (
                        "normal line\\n"
                        + fake_secret
                        + "\\n"
                    ),
                },
            ],
            "production_touched": False,
        },
    )

    monkeypatch.setattr(
        detail,
        "RESULTS",
        results,
    )

    report = detail.collect(
        SOURCE_JOB
    )

    serialized = json.dumps(report)

    assert "FICTITIOUS_SECRET_123456" not in serialized
    assert "[REDACTED]" in serialized


def test_detail_reader_rejects_arbitrary_identifier():
    with pytest.raises(
        ValueError,
        match="RESULT_DETAIL_JOB_ID_INVALID",
    ):
        detail.collect("../../etc/passwd")


def test_detail_check_is_strictly_bounded():
    check = {
        "type": "worker_result_detail_read",
        "request": {
            "job_id": SOURCE_JOB,
        },
    }

    assert bridge.validate_check(
        check,
        0,
    ) == []

    assert bridge.validate_check(
        {
            **check,
            "path": "/etc/passwd",
        },
        0,
    )

    assert bridge.validate_check(
        {
            "type": "worker_result_detail_read",
            "request": {
                "job_id": SOURCE_JOB,
                "path": "/etc/passwd",
            },
        },
        0,
    )

    assert (
        "worker_result_detail_read"
        in bridge.READ_ONLY_CHECKS
    )

    assert (
        "worker_result_detail_read"
        in bridge.ALLOWED_CHECKS
    )

    assert (
        "worker_result_detail_read"
        in publisher.ALLOWED_CHECKS
    )


def test_detail_semantic_capability_registered():
    assert (
        "WORKER_RESULT_DETAIL_READ"
        in registered_capabilities()
    )


def test_detail_semantic_expansion_is_read_only():
    job = service.build_semantic_job(
        {
            "objective": (
                "Leer detalle sanitizado "
                "de resultado Worker."
            ),
            "bounded_context": "WORKER_REPAIR",
            "mode": "READ_ONLY",
            "capability": (
                "WORKER_RESULT_DETAIL_READ"
            ),
            "constraints": {
                "source_job_id": SOURCE_JOB,
            },
        },
        current_user={
            "id": "1",
            "email": "admin@example.com",
            "role": "SuperAdministrador",
        },
    )

    assert job["mode"] == "READ_ONLY"
    assert job["actions"] == []
    assert job["production_allowed"] is False

    assert job["checks"] == [
        {
            "type": "worker_result_detail_read",
            "request": {
                "job_id": SOURCE_JOB,
            },
        }
    ]


def test_detail_capability_rejects_extra_constraints():
    with pytest.raises(
        service.WorkerIngressError,
        match="SEMANTIC_CONSTRAINTS_UNSUPPORTED",
    ):
        service.build_semantic_job(
            {
                "objective": "Read failure.",
                "bounded_context": "WORKER_REPAIR",
                "mode": "READ_ONLY",
                "capability": (
                    "WORKER_RESULT_DETAIL_READ"
                ),
                "constraints": {
                    "source_job_id": SOURCE_JOB,
                    "path": "/etc/passwd",
                },
            },
            current_user={
                "id": "1",
                "email": "admin@example.com",
                "role": "SuperAdministrador",
            },
        )


def test_dispatcher_registers_detail_evidence():
    dispatcher = (
        Path(__file__)
        .resolve()
        .parents[2]
        / "tools"
        / "mirror_sync"
        / "universal_job_dispatcher.py"
    )

    source = dispatcher.read_text(
        encoding="utf-8"
    )

    assert (
        'elif kind == "worker_result_detail_read":'
        in source
    )

    assert (
        'response["result_detail_evidence"]'
        in source
    )


def test_result_detail_is_safe_status_field():
    from modules.worker_ingress import service as ingress_service

    assert (
        "result_detail_evidence"
        in ingress_service._SAFE_RESULT_KEYS
    )


def test_get_job_status_promotes_nested_result_detail_evidence(tmp_path, monkeypatch):
    import subprocess
    from modules.worker_ingress import service as ingress_service

    git_dir = tmp_path / ".git"
    state_root = git_dir / "universal-worker-queue"
    results_dir = state_root / "results"
    results_dir.mkdir(parents=True)
    (git_dir / "HEAD").write_text("ref: refs/heads/Edarsahub_Desarrollo\n", encoding="utf-8")

    job_id = "SEM-CRM-WORKER_RESULT_DETAIL_READ-TEST123456"
    payload = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": "READ_ONLY_COMPLETE",
        "certification": "CERTIFIED_READ_ONLY",
        "work_completion": "COMPLETE",
        "quality_gate": "PASS",
        "tests": "PASS",
        "percent_complete": 100,
        "production_touched": False,
        "completed_at_utc": "2026-11-19T08:00:00Z",
        "files_changed": [],
        "blockers": [],
        "checks": [
            {
                "type": "worker_result_detail_read",
                "status": "PASS",
                "result_detail_evidence": {
                    "schema": "edarsahub.worker-result-detail-read.v1",
                    "mode": "READ_ONLY",
                    "status": "PASS",
                    "source_job_id": "SRC-JOB-1",
                    "result_status": "BLOCKED",
                    "quality_gate": "FAIL",
                    "tests": "FAIL",
                    "certification": "NOT_CERTIFIED",
                    "percent_complete": 0,
                    "blockers": ["check_failed:pytest"],
                    "files_changed": [],
                    "failed_checks": [],
                    "production_touched": False,
                },
            }
        ],
    }
    (results_dir / f"{job_id}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    monkeypatch.setattr(ingress_service, "STATE_ROOT", state_root)

    status = ingress_service.get_job_status(job_id)
    assert status["lifecycle"] == "RESULT"
    assert status["certification"] == "CERTIFIED_READ_ONLY"
    assert status["result_detail_evidence"] is not None
    assert status["result_detail_evidence"]["checks"][0]["source_job_id"] == "SRC-JOB-1"
    assert status["production_touched"] is False

    # Remote-only origin/worker/results fallback works read-only and preserves fail-closed on missing jobs
    remote_job_id = "EDARSAHUB-REMOTE-ONLY-READ-TEST-20261119"
    remote_payload = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": remote_job_id,
        "status": "READ_ONLY_COMPLETE",
        "certification": "CERTIFIED_READ_ONLY",
        "work_completion": "COMPLETE",
        "quality_gate": "PASS",
        "tests": "PASS",
        "percent_complete": 100,
        "production_touched": False,
        "completed_at_utc": "2026-11-19T08:05:00Z",
        "blockers": [],
    }

    def fake_run(cmd, **kwargs):
        if remote_job_id in cmd[-1]:
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(remote_payload).encode("utf-8"), stderr=b"")
        return subprocess.CompletedProcess(cmd, 128, stdout=b"", stderr=b"not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    remote_status = ingress_service.get_job_status(remote_job_id)
    assert remote_status["lifecycle"] == "RESULT"
    assert remote_status["certification"] == "CERTIFIED_READ_ONLY"
    assert remote_status["reconciliation_status"] == "REMOTE_RESULTS_VERIFIED"
    assert remote_status["production_touched"] is False

    missing_status = ingress_service.get_job_status("EDARSAHUB-NONEXISTENT-JOB-99999")
    assert missing_status["lifecycle"] == "NOT_FOUND"
    assert missing_status["status"] == "NOT_FOUND"


def _make_repo_audit_payload(
    job_id: str,
    *,
    status: str = "READ_ONLY_COMPLETE",
    certification: str = "CERTIFIED_READ_ONLY",
    quality_gate: str = "PASS",
    tests: str = "PASS",
    percent_complete: int = 100,
    entries: list[dict] | None = None,
    summary: dict | None = None,
    truncated: bool = False,
    extra_checks: list[dict] | None = None,
) -> dict:
    checks: list[dict] = [
        {
            "type": "repository_contract_audit",
            "status": "PASS",
            "repository_evidence": {
                "status": "PASS",
                "mode": "READ_ONLY_REPOSITORY",
                "summary": summary
                or {
                    "scanned_files": 25,
                    "matched_files": 2,
                    "skipped_sensitive": 3,
                },
                "truncated": truncated,
                "evidence": entries
                if entries is not None
                else [
                    {
                        "path": "backend/modules/worker_ingress/service.py",
                        "candidate_ownership": "backend",
                        "matched_terms": ["worker_result_detail_read"],
                        "symbols": ["get_job_status"],
                    }
                ],
            },
        }
    ]
    if extra_checks:
        checks.extend(extra_checks)
    return {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": status,
        "quality_gate": quality_gate,
        "tests": tests,
        "certification": certification,
        "work_completion": "COMPLETE" if status == "READ_ONLY_COMPLETE" else "NOT_CERTIFIED",
        "percent_complete": percent_complete,
        "completed_at_utc": "2026-11-19T09:00:00Z",
        "blockers": [] if status == "READ_ONLY_COMPLETE" else ["check_failed:pytest"],
        "files_changed": [],
        "production_touched": False,
        "checks": checks,
    }


def test_detail_reader_recovers_pass_audit_evidence_and_mcp_exposes_it(tmp_path, monkeypatch):
    import sys
    from modules.worker_ingress import service as ingress_service
    from tools.mirror_sync import universal_job_result_publisher as pub

    state_root = tmp_path / ".git" / "universal-worker-queue"
    results = state_root / "results"
    results.mkdir(parents=True)
    source_id = "SEM-COMPAT-REPO-PASS-001"
    source_payload = _make_repo_audit_payload(source_id)
    (results / f"{source_id}.json").write_text(json.dumps(source_payload), encoding="utf-8")
    monkeypatch.setattr(detail, "RESULTS", results)
    monkeypatch.setattr(ingress_service, "STATE_ROOT", state_root)

    report = detail.collect(source_id)
    assert report["status"] == "PASS"
    assert report["source_job_id"] == source_id
    assert report["source_terminal"] is True
    assert report["evidence_status"] == "COMPLETE"
    assert report["evidence_truncated"] is False
    assert report["evidence_summary"]["scanned_files"] == 25
    assert report["evidence_summary"]["entries_returned"] == 1
    assert report["repository_contract_evidence"]["checks"][0]["evidence"][0]["path"] == (
        "backend/modules/worker_ingress/service.py"
    )
    assert report["production_allowed"] is False

    # Publisher preserves sanitized repository_contract_evidence inside result_detail_evidence
    wrapper = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "SEM-COMPAT-DETAIL-WRAPPER-001",
        "status": "READ_ONLY_COMPLETE",
        "quality_gate": "PASS",
        "tests": "PASS",
        "certification": "CERTIFIED_READ_ONLY",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "completed_at_utc": "2026-11-19T09:01:00Z",
        "blockers": [],
        "files_changed": [],
        "production_touched": False,
        "checks": [
            {
                "type": "worker_result_detail_read",
                "status": "PASS",
                "result_detail_evidence": report,
            }
        ],
    }
    sanitized_detail = pub.sanitize_result_detail_evidence(wrapper)
    assert sanitized_detail is not None
    chk0 = sanitized_detail["checks"][0]
    assert chk0["source_job_id"] == source_id
    assert chk0["evidence_status"] == "COMPLETE"
    assert chk0["repository_contract_evidence"]["checks"][0]["evidence"][0]["path"] == (
        "backend/modules/worker_ingress/service.py"
    )

    # Direct get_job_status + MCP get_job_status_tool recover original audit evidence without re-running
    direct = ingress_service.get_job_status(source_id)
    assert direct["certification"] == "CERTIFIED_READ_ONLY"
    assert direct["evidence_status"] == "COMPLETE"
    assert direct["evidence_truncated"] is False
    assert direct["repository_contract_evidence"]["checks"][0]["evidence"][0]["path"] == (
        "backend/modules/worker_ingress/service.py"
    )

    for candidate in sorted(
        Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")
    ):
        if str(candidate) not in sys.path:
            sys.path.append(str(candidate))
    from mcp.server.auth.provider import AccessToken
    from modules.worker_mcp import server as mcp_server
    from modules.worker_mcp.config import WorkerMcpConfig

    mcp_server.build_mcp_server(
        WorkerMcpConfig(
            issuer_url="https://auth.example.test",
            resource_url="https://mcp.example.test/mcp",
            backend_url="https://hub.example.test",
            allowed_hosts=("mcp.example.test",),
            allowed_origins=("https://chat.example.test",),
        )
    )
    monkeypatch.setattr(
        mcp_server,
        "get_access_token",
        lambda: AccessToken(
            token="opaque-test-token",
            client_id="edarsahub-authenticated-user",
            scopes=["worker:status"],
            resource="https://mcp.example.test/mcp",
        ),
    )
    monkeypatch.setattr(
        mcp_server,
        "backend_get_job_status",
        lambda *, backend_url, token, job_id: ingress_service.get_job_status(job_id),
    )
    mcp_res = mcp_server.get_job_status_tool(source_id)
    assert mcp_res["evidence_status"] == "COMPLETE"
    assert mcp_res["evidence_truncated"] is False
    assert mcp_res["repository_contract_evidence"]["checks"][0]["evidence"][0]["path"] == (
        "backend/modules/worker_ingress/service.py"
    )


def test_detail_reader_recovers_fail_audit_with_evidence_and_failures(tmp_path, monkeypatch):
    results = tmp_path / "results"
    results.mkdir(parents=True)
    job_id = "SEM-COMPAT-REPO-FAIL-001"
    payload = _make_repo_audit_payload(
        job_id,
        status="GIT_TESTS_FAILED",
        certification="NOT_CERTIFIED",
        quality_gate="FAIL",
        tests="FAIL",
        percent_complete=50,
        extra_checks=[
            {
                "type": "pytest",
                "status": "FAIL",
                "returncode": 1,
                "output": "FAILED test_x.py::test_a\nE   AssertionError: boom\n",
            }
        ],
    )
    (results / f"{job_id}.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(detail, "RESULTS", results)

    report = detail.collect(job_id)
    assert report["evidence_status"] == "PARTIAL_WITH_FAILURES"
    assert report["failed_check_count"] == 1
    assert report["failed_checks"][0]["type"] == "pytest"
    assert report["repository_contract_evidence"] is not None
    assert report["evidence_summary"]["entries_returned"] == 1


def test_detail_reader_differentiates_absent_truncated_sensitive_oversized_missing_nonterminal(
    tmp_path, monkeypatch
):
    from tools.mirror_sync import worker_result_semantic_extract as ex

    results = tmp_path / "results"
    results.mkdir(parents=True)
    monkeypatch.setattr(detail, "RESULTS", results)

    # 1. Absent evidence (explicit ABSENT, no invented data)
    absent_id = "SEM-COMPAT-ABSENT-001"
    (results / f"{absent_id}.json").write_text(
        json.dumps(
            {
                "schema": "edarsahub.worker-result.v2",
                "job_id": absent_id,
                "status": "READ_ONLY_COMPLETE",
                "quality_gate": "PASS",
                "tests": "PASS",
                "certification": "CERTIFIED_READ_ONLY",
                "work_completion": "COMPLETE",
                "percent_complete": 100,
                "completed_at_utc": "2026-11-19T09:00:00Z",
                "blockers": [],
                "files_changed": [],
                "production_touched": False,
                "checks": [{"type": "py_compile", "status": "PASS"}],
            }
        ),
        encoding="utf-8",
    )
    absent_report = detail.collect(absent_id)
    assert absent_report["evidence_status"] == "ABSENT"
    assert absent_report["repository_contract_evidence"] is None
    assert absent_report["evidence_truncated"] is False

    # 2. Truncated evidence (> 64KB, counts & truncated flag preserved)
    trunc_id = "SEM-COMPAT-TRUNC-001"
    large_entries = [
        {
            "path": f"backend/modules/mod_{i}/routes.py",
            "candidate_ownership": "backend",
            "matched_terms": ["worker", "contract"],
            "symbols": [f"sym_{i}_{j}_padding_for_budget_test" for j in range(25)],
        }
        for i in range(100)
    ]
    (results / f"{trunc_id}.json").write_text(
        json.dumps(
            _make_repo_audit_payload(
                trunc_id,
                entries=large_entries,
                summary={"scanned_files": 229, "matched_files": 100, "skipped_sensitive": 70},
                truncated=True,
            )
        ),
        encoding="utf-8",
    )
    trunc_report = detail.collect(trunc_id)
    assert trunc_report["evidence_status"] == "TRUNCATED"
    assert trunc_report["evidence_truncated"] is True
    assert trunc_report["evidence_summary"]["scanned_files"] == 229
    assert trunc_report["evidence_summary"]["matched_files"] == 100
    assert trunc_report["evidence_summary"]["skipped_sensitive"] == 70
    assert 0 < trunc_report["evidence_summary"]["entries_returned"] < 100
    assert (
        len(json.dumps(trunc_report["repository_contract_evidence"], ensure_ascii=False, sort_keys=True).encode("utf-8"))
        <= ex.MAX_SERIALIZED_BYTES
    )

    # 3. Sensitive evidence (fail-closed, zero leakage)
    sens_id = "SEM-COMPAT-SENSITIVE-001"
    (results / f"{sens_id}.json").write_text(
        json.dumps(
            _make_repo_audit_payload(
                sens_id,
                entries=[{"path": "backend/x.py", "matched_terms": ["password=SUPER_SECRET_999"]}],
            )
        ),
        encoding="utf-8",
    )
    sens_report = detail.collect(sens_id)
    assert sens_report["evidence_status"] == "REJECTED_UNSAFE_OR_OVERSIZED"
    assert sens_report["repository_contract_evidence"] is None
    assert "SUPER_SECRET_999" not in json.dumps(sens_report)

    # 4. Oversized result file (> MAX_RESULT_BYTES) -> controlled error
    big_id = "SEM-COMPAT-OVERSIZED-001"
    (results / f"{big_id}.json").write_text(" " * (detail.MAX_RESULT_BYTES + 10), encoding="utf-8")
    with pytest.raises(ValueError, match="RESULT_DETAIL_RESULT_TOO_LARGE"):
        detail.collect(big_id)

    # 5. Missing job -> controlled error
    with pytest.raises(ValueError, match="RESULT_DETAIL_RESULT_NOT_FOUND"):
        detail.collect("SEM-COMPAT-DOES-NOT-EXIST-999")

    # 6. Non-terminal job -> never presented as certified
    nonterm_id = "SEM-COMPAT-NONTERM-001"
    (results / f"{nonterm_id}.json").write_text(
        json.dumps(
            _make_repo_audit_payload(
                nonterm_id,
                status="PROCESSING",
                certification="CERTIFIED_READ_ONLY",
                percent_complete=100,
            )
        ),
        encoding="utf-8",
    )
    nonterm_report = detail.collect(nonterm_id)
    assert nonterm_report["source_terminal"] is False
    assert nonterm_report["certification"] == "NOT_CERTIFIED"
    assert nonterm_report["work_completion"] == "NON_TERMINAL"
    assert nonterm_report["evidence_status"] == "NON_TERMINAL_SOURCE"
    assert nonterm_report["repository_contract_evidence"] is None


def test_legacy_detail_reader_compatibility_and_rbac_scope_rejection(monkeypatch):
    from fastapi import HTTPException
    from modules.worker_ingress import routes as ingress_routes
    from tools.mirror_sync import universal_job_result_publisher as pub

    # Historical legacy detail payload (without new evidence_status / repository_contract_evidence keys)
    legacy_wrapper = {
        "checks": [
            {
                "type": "worker_result_detail_read",
                "status": "PASS",
                "result_detail_evidence": {
                    "schema": "edarsahub.worker-result-detail-read.v1",
                    "mode": "READ_ONLY",
                    "status": "PASS",
                    "source_job_id": "SEM-LEGACY-001",
                    "result_status": "READ_ONLY_COMPLETE",
                    "quality_gate": "PASS",
                    "tests": "PASS",
                    "certification": "CERTIFIED_READ_ONLY",
                    "percent_complete": 100,
                    "blockers": [],
                    "files_changed": [],
                    "failed_checks": [],
                    "production_touched": False,
                },
            }
        ]
    }
    sanitized = pub.sanitize_result_detail_evidence(legacy_wrapper)
    assert sanitized is not None
    assert sanitized["checks"][0]["source_job_id"] == "SEM-LEGACY-001"
    assert sanitized["checks"][0]["certification"] == "CERTIFIED_READ_ONLY"

    # Unauthorized / insufficient-scope request rejected by RBAC/scope guard
    def deny_scope(**kwargs):
        raise ingress_routes.OAuthValidationError("INSUFFICIENT_SCOPE")

    monkeypatch.setattr(ingress_routes, "enforce_internal_jwt_mcp_scope", deny_scope)
    with pytest.raises(HTTPException) as exc_info:
        ingress_routes.read_worker_job_status(
            "SEM-COMPAT-REPO-PASS-001",
            current_user={"id": "99", "email": "user@example.com", "role": "Operador"},
            authorization="Bearer invalid-scope-token",
        )
    assert exc_info.value.status_code == 403


def _make_sql_audit_payload(
    job_id: str,
    *,
    published_shape: bool = False,
    rows: list[list] | None = None,
    columns: list[str] | None = None,
    mode: str = "READ_ONLY_SQL",
    connection: str = "readonly_sql_connection:default",
    extra_entry_fields: dict | None = None,
) -> dict:
    entry = {
        "name": "sensitive_role_permissions",
        "columns": columns if columns is not None else ["CodigoRol", "PermissionCode", "PermisoActivo"],
        "rows": rows if rows is not None else [["SUPERADMIN", "RBAC_ADMIN", 1], ["ADMIN", "RBAC_ADMIN", 0]],
        "row_count_returned": len(rows) if rows is not None else 2,
        "truncated": False,
    }
    if extra_entry_fields:
        entry.update(extra_entry_fields)
    sql_block = {
        "status": "PASS",
        "mode": mode,
        "connection": connection,
        "evidence": [entry],
    }
    base = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": "READ_ONLY_COMPLETE",
        "quality_gate": "PASS",
        "tests": "PASS",
        "certification": "CERTIFIED_READ_ONLY",
        "certification_basis": "READ_ONLY_SQL_PASS_PLUS_SANITIZED_EVIDENCE",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "completed_at_utc": "2026-11-21T04:00:00Z",
        "blockers": [],
        "files_changed": [],
        "production_touched": False,
    }
    if published_shape:
        base["sql_readonly_evidence"] = {"checks": [sql_block]}
    else:
        base["checks"] = [
            {
                "type": "sql_readonly_audit",
                "status": "PASS",
                "returncode": 0,
                "sql_evidence": sql_block,
            }
        ]
    return base


def _make_semantic_extract_payload(
    job_id: str,
    *,
    published_shape: bool = False,
) -> dict:
    sem_payload = {
        "status": "PASS",
        "mode": "READ_ONLY_WORKER_RESULT_SEMANTIC_EXTRACT",
        "bridge_verdict": "SOURCE_SEMANTIC_FIELDS_DERIVED_FAIL_CLOSED",
        "runtime_gap_confirmed": False,
        "can_emit_semantic_fields_from_source_result": True,
        "can_read_worker_results_by_branch_path": True,
        "can_read_worker_results_by_blob_sha": False,
        "source_semantic_fields_complete": False,
        "semantic_fields_complete": True,
        "missing_semantic_fields": [],
        "source_missing_semantic_fields": ["gate3_allowed", "real_implementation_percent"],
        "source_explicit_missing_semantic_fields": ["gate3_allowed", "real_implementation_percent"],
        "semantic_field_provenance": {
            "gate3_allowed": {
                "status": "MISSING_IN_SOURCE",
                "source_key": None,
                "derivation": "FAIL_CLOSED_DEFAULT",
            },
            "real_implementation_percent": {
                "status": "MISSING_IN_SOURCE",
                "source_key": None,
                "derivation": "FAIL_CLOSED_DEFAULT",
            },
        },
        "semantic_fields": {
            "gate3_allowed": False,
            "last_gate_executed": "SRC-GATE-R1",
            "last_gate_certified": False,
            "real_implementation_percent": None,
            "next_allowed_gate": "GATE3_HOLD_PENDING_EXPLICIT_SEMANTIC_FIELDS",
            "blocking_reason_if_any": "SOURCE_SEMANTIC_FIELDS_MISSING",
        },
        "gate3_allowed": False,
        "source_status": "GIT_TESTS_FAILED",
        "source_quality_gate": "FAIL",
        "source_certification": "NOT_CERTIFIED",
        "source_work_completion": "NOT_CERTIFIED",
        "source_percent_complete": 80,
        "source_production_touched": False,
        "source_result_read_status": "RESULT_READ_OK",
        "source_result_branch": "worker/results",
        "source_result_path": "worker_queue/results/SRC-GATE-R1.json",
        "source_result_size_bytes": 1229,
        "read_attempts": [{"method": "git_show", "detail": "raw internal log must not be exported"}],
    }
    base = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": "READ_ONLY_COMPLETE",
        "quality_gate": "PASS",
        "tests": "PASS",
        "certification": "CERTIFIED_READ_ONLY",
        "certification_basis": "READ_ONLY_SEMANTIC_EXTRACT_PASS_PLUS_SANITIZED_EVIDENCE",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "completed_at_utc": "2026-11-24T04:06:35Z",
        "blockers": [],
        "files_changed": [],
        "production_touched": False,
    }
    if published_shape:
        base["worker_result_semantic_evidence"] = {
            "checks": [{"status": "PASS", "returncode": 0, "payload": sem_payload}],
            "bridge_verdict": sem_payload["bridge_verdict"],
            "gate3_allowed": False,
        }
    else:
        base["checks"] = [
            {
                "type": "worker_result_semantic_extract",
                "status": "PASS",
                "returncode": 0,
                "output": json.dumps(sem_payload),
            }
        ]
    return base


def test_r2_d2_recovers_sql_and_semantic_evidence_local_and_published_and_mcp(tmp_path, monkeypatch):
    import sys
    from modules.worker_ingress import service as ingress_service
    from tools.mirror_sync import universal_job_result_publisher as pub

    state_root = tmp_path / ".git" / "universal-worker-queue"
    results = state_root / "results"
    results.mkdir(parents=True)
    monkeypatch.setattr(detail, "RESULTS", results)
    monkeypatch.setattr(ingress_service, "STATE_ROOT", state_root)

    sql_local_id = "SEM-SEC_RBAC-SQL-LOCAL-001"
    sql_pub_id = "SEM-SEC_RBAC-SQL-PUB-001"
    sem_local_id = "SEM-WORKER_REPAIR_KNOWLEDGE_LOOP-SEM-LOCAL-001"
    sem_pub_id = "SEM-WORKER_REPAIR_KNOWLEDGE_LOOP-SEM-PUB-001"

    sql_local_raw = json.dumps(_make_sql_audit_payload(sql_local_id, published_shape=False))
    (results / f"{sql_local_id}.json").write_text(sql_local_raw, encoding="utf-8")
    (results / f"{sql_pub_id}.json").write_text(
        json.dumps(_make_sql_audit_payload(sql_pub_id, published_shape=True)), encoding="utf-8"
    )
    (results / f"{sem_local_id}.json").write_text(
        json.dumps(_make_semantic_extract_payload(sem_local_id, published_shape=False)), encoding="utf-8"
    )
    (results / f"{sem_pub_id}.json").write_text(
        json.dumps(_make_semantic_extract_payload(sem_pub_id, published_shape=True)), encoding="utf-8"
    )

    # Local + Published SQL recovery + NOT_APPLICABLE vs COMPLETE differentiation
    for jid in (sql_local_id, sql_pub_id):
        rep = detail.collect(jid)
        assert rep["evidence_status"] == "COMPLETE"
        assert rep["evidence_availability"]["sql_readonly_evidence"] == "COMPLETE"
        assert rep["evidence_availability"]["repository_contract_evidence"] == "NOT_APPLICABLE"
        assert rep["evidence_availability"]["worker_result_semantic_evidence"] == "NOT_APPLICABLE"
        assert rep["evidence_availability"]["maintenance_history_evidence"] == "NOT_APPLICABLE"
        assert rep["sql_readonly_evidence"]["checks"][0]["evidence"][0]["rows"][0] == ["SUPERADMIN", "RBAC_ADMIN", 1]

        st = ingress_service.get_job_status(jid, current_user={"email": "admin@edarsa.mx", "role": "SUPERADMIN"})
        assert st["evidence_status"] == "COMPLETE"
        assert st["evidence_availability"]["sql_readonly_evidence"] == "COMPLETE"
        assert st["evidence_availability"]["repository_contract_evidence"] == "NOT_APPLICABLE"
        assert st["sql_readonly_evidence"]["checks"][0]["evidence"][0]["name"] == "sensitive_role_permissions"

    # Historical artifact immutability guaranteed
    assert (results / f"{sql_local_id}.json").read_text(encoding="utf-8") == sql_local_raw

    # Local + Published Semantic recovery preserves provenance, unknown None, and certification
    for jid in (sem_local_id, sem_pub_id):
        rep = detail.collect(jid)
        assert rep["evidence_status"] == "COMPLETE"
        assert rep["evidence_availability"]["worker_result_semantic_evidence"] == "COMPLETE"
        assert rep["evidence_availability"]["sql_readonly_evidence"] == "NOT_APPLICABLE"
        sem = rep["worker_result_semantic_evidence"]
        assert sem["bridge_verdict"] == "SOURCE_SEMANTIC_FIELDS_DERIVED_FAIL_CLOSED"
        assert sem["gate3_allowed"] is False
        assert sem["source_certification"] == "NOT_CERTIFIED"
        assert sem["semantic_fields"]["real_implementation_percent"] is None
        assert sem["semantic_field_provenance"]["gate3_allowed"]["status"] == "MISSING_IN_SOURCE"
        assert "read_attempts" not in json.dumps(sem)

        st = ingress_service.get_job_status(jid, current_user={"email": "admin@edarsa.mx", "role": "SUPERADMIN"})
        assert st["evidence_status"] == "COMPLETE"
        assert st["worker_result_semantic_evidence"]["source_certification"] == "NOT_CERTIFIED"

    # Generic non-audit job differentiates NOT_APPLICABLE on get_job_status vs ABSENT when audit check lacks payload
    gen_id = "SEM-CAVA_SOCIOS-GENERIC-PYTEST-001"
    (results / f"{gen_id}.json").write_text(
        json.dumps({
            "schema": "edarsahub.worker-result.v2",
            "job_id": gen_id,
            "status": "READ_ONLY_COMPLETE",
            "quality_gate": "PASS",
            "tests": "PASS",
            "certification": "CERTIFIED_READ_ONLY",
            "work_completion": "COMPLETE",
            "percent_complete": 100,
            "completed_at_utc": "2026-11-25T07:00:00Z",
            "blockers": [],
            "files_changed": [],
            "production_touched": False,
            "checks": [{"type": "pytest", "status": "PASS"}],
        }),
        encoding="utf-8",
    )
    st_gen = ingress_service.get_job_status(gen_id)
    assert st_gen["evidence_status"] == "NOT_APPLICABLE"
    assert all(v == "NOT_APPLICABLE" for v in st_gen["evidence_availability"].values())

    absent_sql_id = "SEM-SEC_RBAC-SQL-ABSENT-001"
    (results / f"{absent_sql_id}.json").write_text(
        json.dumps({
            "schema": "edarsahub.worker-result.v2",
            "job_id": absent_sql_id,
            "status": "READ_ONLY_COMPLETE",
            "quality_gate": "PASS",
            "tests": "PASS",
            "certification": "CERTIFIED_READ_ONLY",
            "work_completion": "COMPLETE",
            "percent_complete": 100,
            "completed_at_utc": "2026-11-25T07:00:00Z",
            "blockers": [],
            "files_changed": [],
            "production_touched": False,
            "checks": [{"type": "sql_readonly_audit", "status": "PASS"}],
        }),
        encoding="utf-8",
    )
    st_abs = ingress_service.get_job_status(absent_sql_id)
    assert st_abs["evidence_status"] == "ABSENT"
    assert st_abs["evidence_availability"]["sql_readonly_evidence"] == "ABSENT"
    assert st_abs["evidence_availability"]["repository_contract_evidence"] == "NOT_APPLICABLE"

    # MCP get_job_status_tool exposes sql_readonly_evidence, worker_result_semantic_evidence, evidence_availability
    for candidate in sorted(Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")):
        if str(candidate) not in sys.path:
            sys.path.append(str(candidate))
    from mcp.server.auth.provider import AccessToken
    from modules.worker_mcp import server as mcp_server
    from modules.worker_mcp.config import WorkerMcpConfig

    mcp_server.build_mcp_server(
        WorkerMcpConfig(
            issuer_url="https://auth.example.test",
            resource_url="https://mcp.example.test/mcp",
            backend_url="https://hub.example.test",
            allowed_hosts=("mcp.example.test",),
            allowed_origins=("https://chat.example.test",),
        )
    )
    monkeypatch.setattr(
        mcp_server,
        "get_access_token",
        lambda: AccessToken(
            token="opaque-test-token",
            client_id="edarsahub-authenticated-user",
            scopes=["worker:status"],
            resource="https://mcp.example.test/mcp",
        ),
    )
    monkeypatch.setattr(
        mcp_server,
        "backend_get_job_status",
        lambda *, backend_url, token, job_id: ingress_service.get_job_status(job_id),
    )
    mcp_sql = mcp_server.get_job_status_tool(sql_pub_id)
    assert mcp_sql["evidence_status"] == "COMPLETE"
    assert mcp_sql["sql_readonly_evidence"]["checks"][0]["evidence"][0]["rows"][0] == ["SUPERADMIN", "RBAC_ADMIN", 1]
    assert mcp_sql["evidence_availability"]["sql_readonly_evidence"] == "COMPLETE"

    mcp_sem = mcp_server.get_job_status_tool(sem_pub_id)
    assert mcp_sem["evidence_status"] == "COMPLETE"
    assert mcp_sem["worker_result_semantic_evidence"]["source_certification"] == "NOT_CERTIFIED"
    assert mcp_sem["evidence_availability"]["worker_result_semantic_evidence"] == "COMPLETE"

    # Verify sanitize_result_detail_evidence preserves typed SQL & semantic evidence
    pub_detail = pub.sanitize_result_detail_evidence({
        "checks": [{
            "type": "worker_result_detail_read",
            "status": "PASS",
            "result_detail_evidence": detail.collect(sql_local_id),
        }]
    })
    assert pub_detail is not None
    assert pub_detail["checks"][0]["sql_readonly_evidence"] is not None
    assert pub_detail["checks"][0]["evidence_availability"]["sql_readonly_evidence"] == "COMPLETE"


def test_r2_d2_sql_strict_allowlist_rejects_unsafe_values_nested_types_and_truncates_oversized(tmp_path, monkeypatch):
    from modules.worker_ingress import service as ingress_service

    state_root = tmp_path / ".git" / "universal-worker-queue"
    results = state_root / "results"
    results.mkdir(parents=True)
    monkeypatch.setattr(detail, "RESULTS", results)
    monkeypatch.setattr(ingress_service, "STATE_ROOT", state_root)

    # 1. Secret embedded in innocent column name -> REJECTED fail-closed (not reliant on column name!)
    leak_id = "SEM-SEC_RBAC-SQL-LEAK-001"
    (results / f"{leak_id}.json").write_text(
        json.dumps(_make_sql_audit_payload(
            leak_id,
            columns=["nota_publica"],
            rows=[["token=SUPER_LEAKED_VALUE_999"]],
        )),
        encoding="utf-8",
    )
    st_leak = ingress_service.get_job_status(leak_id)
    assert st_leak["evidence_status"] == "REJECTED_UNSAFE_OR_OVERSIZED"
    assert st_leak["evidence_availability"]["sql_readonly_evidence"] == "REJECTED_UNSAFE_OR_OVERSIZED"
    assert "sql_readonly_evidence" not in st_leak
    assert "SUPER_LEAKED_VALUE_999" not in json.dumps(st_leak)

    # 2. Nested dict/list cell or unknown extra key or unsafe connection string -> REJECTED
    for suffix, kw in (
        ("NESTED", {"columns": ["col"], "rows": [[{"nested": "bad"}]]}),
        ("EXTRAKEY", {"extra_entry_fields": {"raw_sql": "SELECT 1"}}),
        ("BADCONN", {"connection": "mssql://sa:Pass123@10.0.0.1/db"}),
        ("BADMODE", {"mode": "READ_WRITE_SQL"}),
    ):
        jid = f"SEM-SEC_RBAC-SQL-{suffix}-001"
        (results / f"{jid}.json").write_text(json.dumps(_make_sql_audit_payload(jid, **kw)), encoding="utf-8")
        st = ingress_service.get_job_status(jid)
        assert st["evidence_status"] == "REJECTED_UNSAFE_OR_OVERSIZED", suffix
        assert "sql_readonly_evidence" not in st

    # 3. Large safe SQL rows (> 64KB) -> truncated cleanly with TRUNCATED status
    big_id = "SEM-SEC_RBAC-SQL-TRUNC-001"
    big_rows = [[f"ROLE_{i}", "PERM_" + ("X" * 180), i] for i in range(450)]
    (results / f"{big_id}.json").write_text(
        json.dumps(_make_sql_audit_payload(big_id, rows=big_rows)),
        encoding="utf-8",
    )
    st_big = ingress_service.get_job_status(big_id)
    assert st_big["evidence_status"] == "TRUNCATED"
    assert st_big["evidence_truncated"] is True
    assert st_big["sql_readonly_evidence"]["checks"][0]["evidence"][0]["truncated"] is True
    assert 0 < len(st_big["sql_readonly_evidence"]["checks"][0]["evidence"][0]["rows"]) < 450


def test_r2_d2_rbac_and_domain_access_enforcement(tmp_path, monkeypatch):
    from modules.worker_ingress import service as ingress_service

    state_root = tmp_path / ".git" / "universal-worker-queue"
    results = state_root / "results"
    results.mkdir(parents=True)
    monkeypatch.setattr(ingress_service, "STATE_ROOT", state_root)

    sql_id = "SEM-SEC_RBAC-SQL-RBAC-001"
    (results / f"{sql_id}.json").write_text(
        json.dumps(_make_sql_audit_payload(sql_id)), encoding="utf-8"
    )

    # Unprivileged operator without worker:status -> forbidden
    with pytest.raises(ingress_service.WorkerIngressError, match="RBAC_STATUS_READ_FORBIDDEN"):
        ingress_service.get_job_status(sql_id, current_user={"email": "op@edarsa.mx", "role": "Operador"})

    # Non-admin with worker:status still denied restricted SEC_RBAC / SQL domain
    with pytest.raises(ingress_service.WorkerIngressError, match="RBAC_DOMAIN_ACCESS_FORBIDDEN"):
        ingress_service.get_job_status(
            sql_id,
            current_user={"email": "viewer@edarsa.mx", "role": "Analista", "permissions": ["worker:status"]},
        )

    # Admin with domain restriction excluding SEC_RBAC -> denied
    with pytest.raises(ingress_service.WorkerIngressError, match="RBAC_DOMAIN_ACCESS_FORBIDDEN"):
        ingress_service.get_job_status(
            sql_id,
            current_user={"email": "admin@edarsa.mx", "role": "SUPERADMIN", "allowed_domains": ["CAVA_SOCIOS"]},
        )

    # Authorized SUPERADMIN -> succeeds
    ok = ingress_service.get_job_status(
        sql_id,
        current_user={"email": "admin@edarsa.mx", "role": "SUPERADMIN"},
    )
    assert ok["evidence_status"] == "COMPLETE"
