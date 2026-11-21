import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync import universal_job_result_publisher as publisher
from tools.mirror_sync import worker_result_integrity as integrity


def test_empty_terminal_result_file_is_result_empty(tmp_path):
    path = tmp_path / "worker_queue" / "results" / "EMPTY-JOB.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")

    inspection = integrity.inspect_result_file(path)

    assert inspection.state == integrity.ResultState.RESULT_EMPTY
    assert inspection.reason == "ZERO_BYTE_RESULT"

    with pytest.raises(ValueError, match="RESULT_EMPTY"):
        integrity.validate_terminal_result_file(path)


def test_publisher_turns_empty_local_result_into_invalid_artifact(tmp_path):
    path = tmp_path / "results" / "EMPTY-JOB.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")

    payload = publisher.load_publishable_result(path)

    assert payload["schema"] == "edarsahub.worker-result.v2"
    assert payload["job_id"] == "EMPTY-JOB"
    assert payload["status"] == "INVALID_RESULT_ARTIFACT"
    assert payload["quality_gate"] == "FAIL"
    assert payload["certification"] == "NOT_CERTIFIED"
    assert payload["production_touched"] is False
    assert payload["files_changed"] == []
    assert payload["invalid_result_artifact"] is True
    assert payload["result_integrity_state"] == "RESULT_EMPTY"

    public = publisher.sanitize(payload)

    assert public["certification"] == "NOT_CERTIFIED"
    assert public["work_completion"] == "INVALID_RESULT_ARTIFACT"
    assert public["percent_complete"] == 0
    assert public["certification_basis"] == "INVALID_RESULT_ARTIFACT_FAIL_CLOSED"
    assert public["invalid_result_artifact"] is True
