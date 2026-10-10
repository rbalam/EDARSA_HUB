"""Canonical Universal Worker result reader.

One terminal truth:
worker_queue/results/<job_id>.json

This helper classifies result state through the canonical integrity layer.
It never treats content="" by itself as proof that the canonical terminal
blob is empty.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.mirror_sync.worker_result_integrity import (
    ResultState,
    inspect_result_file,
    validate_terminal_result_file,
)


@dataclass(frozen=True)
class CanonicalResultRead:
    job_id: str
    state: str
    result_path: str
    result_size_bytes: int
    result_sha256: str | None
    terminal_result_valid: bool
    payload: dict[str, Any] | None
    source: str = "worker_queue/results"


def read_canonical_result(
    result_path: str | Path,
    *,
    expected_job_id: str,
) -> CanonicalResultRead:
    path = Path(result_path)

    inspection = inspect_result_file(
        path,
        expected_job_id=expected_job_id,
    )

    if inspection.state is not ResultState.RESULT_TERMINAL_VALID:
        return CanonicalResultRead(
            job_id=expected_job_id,
            state=inspection.state.value,
            result_path=str(path),
            result_size_bytes=inspection.size_bytes,
            result_sha256=inspection.sha256 or None,
            terminal_result_valid=False,
            payload=None,
        )

    identity = validate_terminal_result_file(
        path,
        expected_job_id=expected_job_id,
    )

    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    return CanonicalResultRead(
        job_id=expected_job_id,
        state=ResultState.RESULT_TERMINAL_VALID.value,
        result_path=str(path),
        result_size_bytes=identity.size_bytes,
        result_sha256=identity.sha256,
        terminal_result_valid=True,
        payload=payload,
    )
