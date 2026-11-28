import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync.worker_result_integrity import (
    ResultState,
    classify_source_consistency,
    compare_result_identity,
    inspect_result_file,
    result_identity_from_bytes,
    validate_terminal_result_payload,
)


def readonly_result():
    return {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "JOB-1",
        "status": "READ_ONLY_COMPLETE",
        "quality_gate": "PASS",
        "certification": "CERTIFIED_READ_ONLY",
        "percent_complete": 100,
        "blockers": [],
        "production_touched": False,
        "files_changed": [],
        "completed_at_utc": "2026-09-23T00:00:00Z",
        "slot_class": "READ_ONLY",
    }


def mutation_result():
    return {
        "schema": "edarsahub.worker-result.v2",
        "job_id": "JOB-MUTATION",
        "status": "INTEGRATED",
        "quality_gate": "PASS",
        "certification": "PENDING_AUDIT_EVIDENCE",
        "percent_complete": 95,
        "blockers": [],
        "production_touched": False,
        "files_changed": [
            "tools/mirror_sync/example.py",
        ],
        "completed_at_utc": "2026-09-23T00:00:00Z",
        "slot_class": "MUTATION",
    }


def test_valid_readonly_terminal_contract():
    value = readonly_result()

    assert validate_terminal_result_payload(value) is value


@pytest.mark.parametrize(
    "field",
    [
        "schema",
        "job_id",
        "status",
        "quality_gate",
        "certification",
        "blockers",
        "production_touched",
        "completed_at_utc",
    ],
)
def test_required_terminal_fields(field):
    value = readonly_result()
    value.pop(field)

    with pytest.raises(ValueError):
        validate_terminal_result_payload(value)


def test_readonly_cannot_report_changed_files():
    value = readonly_result()
    value["files_changed"] = ["frontend/src/App.jsx"]

    with pytest.raises(
        ValueError,
        match="READ_ONLY_FILES_CHANGED",
    ):
        validate_terminal_result_payload(value)


def test_readonly_cannot_report_production_touch():
    value = readonly_result()
    value["production_touched"] = True

    with pytest.raises(
        ValueError,
        match="READ_ONLY_PRODUCTION_TOUCHED",
    ):
        validate_terminal_result_payload(value)


@pytest.mark.parametrize(
    "field",
    [
        "mutations_executed",
        "ddl_executed",
        "dml_executed",
        "backend_touched",
        "frontend_touched",
    ],
)
def test_readonly_mutation_flags_cannot_be_true(field):
    value = readonly_result()
    value[field] = True

    with pytest.raises(ValueError):
        validate_terminal_result_payload(value)


def test_nonterminal_status_is_rejected():
    value = readonly_result()
    value["status"] = "PROCESSING"

    with pytest.raises(
        ValueError,
        match="RESULT_NON_TERMINAL",
    ):
        validate_terminal_result_payload(value)


def test_job_id_mismatch_is_rejected():
    value = readonly_result()

    with pytest.raises(
        ValueError,
        match="RESULT_JOB_ID_MISMATCH",
    ):
        validate_terminal_result_payload(
            value,
            expected_job_id="OTHER-JOB",
        )


def test_empty_file_has_explicit_state(tmp_path):
    path = tmp_path / "results" / "JOB-1.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")

    result = inspect_result_file(path)

    assert result.state is ResultState.RESULT_EMPTY


def test_absent_file_has_explicit_state(tmp_path):
    path = tmp_path / "results" / "JOB-1.json"

    result = inspect_result_file(path)

    assert result.state is ResultState.RESULT_ABSENT


def test_invalid_json_has_explicit_state(tmp_path):
    path = tmp_path / "results" / "JOB-1.json"
    path.parent.mkdir(parents=True)
    path.write_text("{", encoding="utf-8")

    result = inspect_result_file(path)

    assert result.state is ResultState.RESULT_INVALID_JSON


def test_nonterminal_file_never_looks_empty(tmp_path):
    value = readonly_result()
    value["status"] = "PROCESSING"

    path = tmp_path / "results" / "JOB-1.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(value),
        encoding="utf-8",
    )

    result = inspect_result_file(path)

    assert result.state is ResultState.RESULT_NON_TERMINAL


def test_valid_terminal_result_has_identity():
    raw = (
        json.dumps(
            readonly_result(),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")

    identity = result_identity_from_bytes(
        raw,
        path="worker_queue/results/JOB-1.json",
        expected_job_id="JOB-1",
    )

    assert identity.job_id == "JOB-1"
    assert identity.size_bytes == len(raw)
    assert len(identity.sha256) == 64
    assert identity.status == "READ_ONLY_COMPLETE"


def test_identity_detects_sha_mismatch():
    raw = json.dumps(readonly_result()).encode("utf-8")

    identity = result_identity_from_bytes(
        raw,
        path="worker_queue/results/JOB-1.json",
    )

    assert (
        compare_result_identity(
            identity=identity,
            expected_sha256="0" * 64,
        )
        is ResultState.RESULT_SHA_MISMATCH
    )


def test_identity_detects_size_mismatch():
    raw = json.dumps(readonly_result()).encode("utf-8")

    identity = result_identity_from_bytes(
        raw,
        path="worker_queue/results/JOB-1.json",
    )

    assert (
        compare_result_identity(
            identity=identity,
            expected_size_bytes=identity.size_bytes + 1,
        )
        is ResultState.RESULT_SIZE_MISMATCH
    )


def test_identity_detects_status_mismatch():
    raw = json.dumps(readonly_result()).encode("utf-8")

    identity = result_identity_from_bytes(
        raw,
        path="worker_queue/results/JOB-1.json",
    )

    assert (
        compare_result_identity(
            identity=identity,
            expected_status="INTEGRATED",
        )
        is ResultState.RESULT_STATUS_MISMATCH
    )


def test_multi_source_mismatch_is_not_reported_as_empty():
    state = classify_source_consistency(
        canonical_sha256="a" * 64,
        observed_sha256="b" * 64,
    )

    assert state is ResultState.READ_SOURCE_MISMATCH


def test_mutation_terminal_contract_remains_supported():
    value = mutation_result()

    assert validate_terminal_result_payload(value) is value
