import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync.worker_result_reader import read_canonical_result
from tools.mirror_sync.worker_result_status import build_job_status


def valid_payload(job_id: str) -> dict:
    return {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": "READ_ONLY_COMPLETE",
        "quality_gate": "PASS",
        "certification": "CERTIFIED_READ_ONLY",
        "percent_complete": 100,
        "blockers": [],
        "production_touched": False,
        "files_changed": [],
        "tests": "PASS",
        "work_completion": "COMPLETE",
        "completed_at_utc": "2026-09-23T00:00:00Z",
    }


def test_absent_result_is_explicit(tmp_path):
    job = "JOB-ABSENT"
    read = read_canonical_result(
        tmp_path / f"{job}.json",
        expected_job_id=job,
    )
    assert read.state == "RESULT_ABSENT"
    assert read.terminal_result_valid is False


def test_empty_result_is_explicit(tmp_path):
    job = "JOB-EMPTY"
    path = tmp_path / f"{job}.json"
    path.write_bytes(b"")

    read = read_canonical_result(
        path,
        expected_job_id=job,
    )

    assert read.state == "RESULT_EMPTY"
    assert read.terminal_result_valid is False


def test_valid_terminal_result_is_canonical(tmp_path):
    job = "JOB-VALID"
    path = tmp_path / f"{job}.json"
    path.write_text(
        json.dumps(valid_payload(job)),
        encoding="utf-8",
    )

    read = read_canonical_result(
        path,
        expected_job_id=job,
    )

    assert read.state == "RESULT_TERMINAL_VALID"
    assert read.terminal_result_valid is True
    assert read.result_size_bytes > 0
    assert read.result_sha256


def test_job_id_mismatch_fails_closed(tmp_path):
    path = tmp_path / "JOB-A.json"
    path.write_text(
        json.dumps(valid_payload("JOB-B")),
        encoding="utf-8",
    )

    read = read_canonical_result(
        path,
        expected_job_id="JOB-A",
    )

    assert read.state == "RESULT_JOB_ID_MISMATCH"
    assert read.terminal_result_valid is False


def test_status_is_derived_reference_not_terminal_copy(tmp_path):
    job = "JOB-STATUS"
    path = tmp_path / f"{job}.json"
    path.write_text(
        json.dumps(valid_payload(job)),
        encoding="utf-8",
    )

    read = read_canonical_result(
        path,
        expected_job_id=job,
    )
    status = build_job_status(result_read=read)

    assert status["job_id"] == job
    assert status["result_path"] == str(path)
    assert status["result_sha"] == read.result_sha256
    assert status["result_size_bytes"] == read.result_size_bytes
    assert status["terminal_result_valid"] is True
    assert status["read_contract_version"] == "v1"
    assert "checks" not in status
