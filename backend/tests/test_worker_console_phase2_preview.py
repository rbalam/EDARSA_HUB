"""Phase 2 canonical preview: functional, read-only unit checks."""
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from modules.worker_ingress.routes import preview_worker_job
from modules.worker_ingress.schemas import WorkerSubmitRequest


USER = {"email": "admin@example.com"}


def payload(**overrides):
    result = {
        "job_id": "BOS-CONSOLE-PREVIEW-TEST",
        "objective": "Verify canonical ingress without side effects",
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [{"type": "git_diff_check"}],
    }
    result.update(overrides)
    return WorkerSubmitRequest.model_validate(result)


def test_preview_accepts_canonical_read_only_without_publishing():
    with patch("modules.worker_ingress.service.gate_chain_publisher.submit") as publisher:
        result = preview_worker_job(payload(), current_user=USER)
    assert result["valid"] is True
    assert result["schema"] == "edarsahub.worker-job.v2"
    assert result["mode"] == "READ_ONLY"
    publisher.assert_not_called()


@pytest.mark.parametrize("request", [
    {"mode": "MUTATION"},
    {"actions": [{"type": "shell", "command": "echo unsafe"}]},
])
def test_preview_rejects_mutations(request):
    with pytest.raises(HTTPException) as error:
        preview_worker_job(payload(**request), current_user=USER)
    assert error.value.status_code == 422


def test_preview_rejects_missing_authenticated_requester():
    with pytest.raises(HTTPException) as error:
        preview_worker_job(payload(), current_user={})
    assert error.value.status_code == 422
