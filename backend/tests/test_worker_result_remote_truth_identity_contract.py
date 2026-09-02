from __future__ import annotations

import importlib.util
from pathlib import Path

PUB = Path(
    "/app/tools/mirror_sync/universal_job_result_publisher.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "universal_job_result_publisher_identity_contract",
        PUB,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_embedded_job_id_is_authoritative_remote_identity():
    mod = load_module()

    path = Path(
        "/tmp/concurrency-e2e-01-20260827.json"
    )

    payload = {
        "job_id": "concurrency-e2e-controller-20260827",
    }

    assert (
        mod.result_identity(path, payload)
        == "concurrency-e2e-controller-20260827"
    )


def test_filename_is_only_fallback_when_job_id_missing():
    mod = load_module()

    path = Path(
        "/tmp/concurrency-e2e-01-20260827.json"
    )

    assert (
        mod.result_identity(path, {})
        == "concurrency-e2e-01-20260827"
    )


def test_embedded_job_id_can_differ_from_filename():
    mod = load_module()

    path = Path(
        "/tmp/legacy-storage-key.json"
    )

    payload = {
        "job_id": "canonical-job-id",
    }

    assert mod.result_identity(path, payload) == "canonical-job-id"
    assert mod.result_identity(path, payload) != path.stem


def test_invalid_embedded_job_id_is_rejected():
    mod = load_module()

    path = Path("/tmp/safe-file.json")

    payload = {
        "job_id": "../unsafe",
    }

    try:
        mod.result_identity(path, payload)
    except ValueError as exc:
        assert str(exc) == "INVALID_JOB_ID"
    else:
        raise AssertionError("invalid job_id was accepted")
