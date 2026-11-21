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
