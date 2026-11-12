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
