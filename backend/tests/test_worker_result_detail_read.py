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
