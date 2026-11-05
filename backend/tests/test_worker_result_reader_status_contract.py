import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from modules.worker_ingress import service
from tools.mirror_sync.worker_result_reader import read_canonical_result
from tools.mirror_sync.worker_result_status import build_job_status


DEV_SHA = "599007ce0984f0be7b80e7ba241d7bfcd9c51a66"
PUB_COMMIT = "33788592e4774f7f0db5e284965162553224d4d8"
CHANGED_FILES = [
    "tools/mirror_sync/worker_result_reader.py",
    "tools/mirror_sync/worker_result_status.py",
]


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


def provisional_mutation_payload(
    job_id: str,
    *,
    development_sha: str = DEV_SHA,
    files_changed: list[str] | None = None,
) -> dict:
    return {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "status": "INTEGRATED",
        "slot_class": "MUTATION",
        "quality_gate": "PASS",
        "tests": "PASS",
        "certification": "PENDING_AUDIT_EVIDENCE",
        "percent_complete": 95,
        "blockers": [],
        "production_touched": False,
        "git_sync_status": "CERTIFIED_GIT_SYNC",
        "development_sha": development_sha,
        "files_changed": list(files_changed if files_changed is not None else CHANGED_FILES),
        "completed_at_utc": "2026-11-05T01:01:53Z",
        "summary_es": "Resultado provisional integrado a la espera de evidencia de certificacion.",
    }


def valid_attestation_payload(
    job_id: str,
    *,
    source_sha: str = DEV_SHA,
    files_changed: list[str] | None = None,
) -> dict:
    return {
        "schema": "edarsahub.test-attestation.v1",
        "job_id": job_id,
        "source_sha": source_sha,
        "tests": "PASS",
        "quality_gate": "PASS",
        "production_touched": False,
        "files_changed": list(files_changed if files_changed is not None else CHANGED_FILES),
        "summary_es": "Atestacion SHA-bound verificada.",
        "generated_at_utc": "2026-11-05T01:04:24Z",
    }


def published_certified_payload(
    job_id: str,
    *,
    development_sha: str = DEV_SHA,
    files_changed: list[str] | None = None,
) -> dict:
    return {
        **provisional_mutation_payload(
            job_id,
            development_sha=development_sha,
            files_changed=files_changed,
        ),
        "certification": "CERTIFIED",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "certified_source_sha": development_sha,
        "converged_head": development_sha,
        "certification_basis": "SHA_BOUND_ATTESTATION_PLUS_ARTIFACT_CONVERGENCE",
    }


def _setup_queue_state(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    state = tmp_path / "universal-worker-queue"
    results = state / "results"
    published = state / "published"
    published_results = state / "published_results"
    attestations = (
        tmp_path
        / "mirror-sync"
        / "reporting"
        / "test_attestations"
    )
    for directory in (results, published, published_results, attestations):
        directory.mkdir(parents=True, exist_ok=True)
    return state, results, published, published_results, attestations


def test_absent_result_is_explicit(tmp_path):
    job = "JOB-ABSENT"
    read = read_canonical_result(
        tmp_path / f"{job}.json",
        expected_job_id=job,
    )
    assert read.state == "RESULT_ABSENT"
    assert read.terminal_result_valid is False

    status = build_job_status(result_read=read)
    assert status["status"] == "RESULT_ABSENT"
    assert status["certification"] == "NOT_CERTIFIED"
    assert status["quality_gate"] == "FAIL"
    assert status["percent_complete"] == 0
    assert status["terminal_result_valid"] is False


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


def test_provisional_mutation_result_remains_pending_until_certified(
    tmp_path,
    monkeypatch,
):
    job = "JOB-PROVISIONAL-95"
    state, results, published, _, attestations = _setup_queue_state(tmp_path)
    monkeypatch.setattr(service, "STATE_ROOT", state)

    (results / f"{job}.json").write_text(
        json.dumps(provisional_mutation_payload(job)),
        encoding="utf-8",
    )

    # Without published marker: provisional 95%
    status_unmarked = service.get_job_status(job)
    assert status_unmarked["lifecycle"] == "RESULT"
    assert status_unmarked["status"] == "INTEGRATED"
    assert status_unmarked["certification"] == "PENDING_AUDIT_EVIDENCE"
    assert status_unmarked["work_completion"] == "PENDING_CERTIFICATION"
    assert status_unmarked["percent_complete"] == 95
    assert status_unmarked["terminal_result_valid"] is True
    assert status_unmarked["commit_sha"] == DEV_SHA
    assert status_unmarked["production_touched"] is False

    # With Pass 1 provisional marker + valid attestation: still provisional 95%
    (published / f"{job}.json").write_text(
        "published=2026-11-05T01:03:00Z\n"
        f"commit={PUB_COMMIT}\n"
        "certification=PENDING_AUDIT_EVIDENCE\n",
        encoding="utf-8",
    )
    (attestations / f"{DEV_SHA}.json").write_text(
        json.dumps(valid_attestation_payload(job)),
        encoding="utf-8",
    )

    status_pass1 = service.get_job_status(job)
    assert status_pass1["certification"] == "PENDING_AUDIT_EVIDENCE"
    assert status_pass1["work_completion"] == "PENDING_CERTIFICATION"
    assert status_pass1["percent_complete"] == 95
    assert status_pass1["terminal_result_valid"] is True


def test_certified_mutation_result_reconciles_from_marker_attestation_and_published_blob(
    tmp_path,
    monkeypatch,
):
    job = "JOB-CERTIFIED-100"
    state, results, published, published_results, attestations = _setup_queue_state(
        tmp_path
    )
    monkeypatch.setattr(service, "STATE_ROOT", state)

    local_raw = (
        json.dumps(provisional_mutation_payload(job), indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    (results / f"{job}.json").write_bytes(local_raw)

    att_raw = (
        json.dumps(valid_attestation_payload(job), indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    (attestations / f"{DEV_SHA}.json").write_bytes(att_raw)

    pub_raw = (
        json.dumps(published_certified_payload(job), indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    (published_results / f"{job}.json").write_bytes(pub_raw)

    (published / f"{job}.json").write_text(
        "published=2026-11-05T01:04:24Z\n"
        f"commit={PUB_COMMIT}\n"
        "certification=CERTIFIED\n",
        encoding="utf-8",
    )

    status = service.get_job_status(job)
    assert status["lifecycle"] == "RESULT"
    assert status["status"] == "INTEGRATED"
    assert status["certification"] == "CERTIFIED"
    assert status["work_completion"] == "COMPLETE"
    assert status["percent_complete"] == 100
    assert status["quality_gate"] == "PASS"
    assert status["tests"] == "PASS"
    assert status["commit_sha"] == DEV_SHA
    assert status["certified_source_sha"] == DEV_SHA
    assert status["converged_head"] == DEV_SHA
    assert (
        status["certification_basis"]
        == "SHA_BOUND_ATTESTATION_PLUS_ARTIFACT_CONVERGENCE"
    )
    assert status["reconciliation_status"] == "RECONCILED_CERTIFIED"
    assert status["published_result_commit"] == PUB_COMMIT
    assert (
        status["published_result_sha256"]
        == hashlib.sha256(pub_raw).hexdigest()
    )
    assert (
        status["attestation_sha256"]
        == hashlib.sha256(att_raw).hexdigest()
    )
    assert status["result_sha"] == hashlib.sha256(local_raw).hexdigest()
    assert status["terminal_result_valid"] is True
    assert status["production_touched"] is False


@pytest.mark.parametrize(
    "tamper_kind",
    [
        "missing_attestation",
        "attestation_wrong_sha",
        "attestation_wrong_job_id",
        "attestation_wrong_files",
        "attestation_tests_fail",
        "attestation_production_touched",
        "published_blob_not_certified",
        "published_blob_wrong_sha",
        "local_contradictory_tests_fail",
        "local_contradictory_production_touched",
    ],
)
def test_contradictory_states_fail_closed(
    tmp_path,
    monkeypatch,
    tamper_kind,
):
    job = f"JOB-CONTRADICT-{tamper_kind.upper().replace('_', '-')}"
    state, results, published, published_results, attestations = _setup_queue_state(
        tmp_path
    )
    monkeypatch.setattr(service, "STATE_ROOT", state)

    local_payload = provisional_mutation_payload(job)
    att_payload = valid_attestation_payload(job)
    pub_payload = published_certified_payload(job)

    if tamper_kind == "local_contradictory_tests_fail":
        local_payload["certification"] = "CERTIFIED"
        local_payload["tests"] = "FAIL"
    elif tamper_kind == "local_contradictory_production_touched":
        local_payload["certification"] = "CERTIFIED"
        local_payload["production_touched"] = True
    elif tamper_kind == "attestation_wrong_sha":
        att_payload["source_sha"] = "a" * 40
    elif tamper_kind == "attestation_wrong_job_id":
        att_payload["job_id"] = "OTHER-JOB-ID"
    elif tamper_kind == "attestation_wrong_files":
        att_payload["files_changed"] = ["backend/server.py"]
    elif tamper_kind == "attestation_tests_fail":
        att_payload["tests"] = "FAIL"
    elif tamper_kind == "attestation_production_touched":
        att_payload["production_touched"] = True
    elif tamper_kind == "published_blob_not_certified":
        pub_payload["certification"] = "PENDING_AUDIT_EVIDENCE"
        pub_payload["percent_complete"] = 95
    elif tamper_kind == "published_blob_wrong_sha":
        pub_payload["development_sha"] = "b" * 40

    (results / f"{job}.json").write_text(
        json.dumps(local_payload),
        encoding="utf-8",
    )
    if tamper_kind != "missing_attestation":
        (attestations / f"{DEV_SHA}.json").write_text(
            json.dumps(att_payload),
            encoding="utf-8",
        )
    (published_results / f"{job}.json").write_text(
        json.dumps(pub_payload),
        encoding="utf-8",
    )
    (published / f"{job}.json").write_text(
        "published=2026-11-05T01:04:24Z\n"
        f"commit={PUB_COMMIT}\n"
        "certification=CERTIFIED\n",
        encoding="utf-8",
    )

    status = service.get_job_status(job)
    assert status["certification"] == "NOT_CERTIFIED"
    assert status["quality_gate"] == "FAIL"
    assert status["tests"] == "FAIL"
    assert status["percent_complete"] == 0
    assert status["terminal_result_valid"] is False
    assert status["blockers"]


@pytest.mark.parametrize(
    "corruption_kind",
    [
        "empty_result_file",
        "corrupt_result_json",
        "job_id_mismatch_in_result",
        "corrupt_published_marker",
        "corrupt_attestation_json",
        "mismatched_marker_result_sha256",
    ],
)
def test_tampered_artifacts_fail_closed(
    tmp_path,
    monkeypatch,
    corruption_kind,
):
    job = f"JOB-TAMPERED-{corruption_kind.upper().replace('_', '-')}"
    state, results, published, published_results, attestations = _setup_queue_state(
        tmp_path
    )
    monkeypatch.setattr(service, "STATE_ROOT", state)

    result_file = results / f"{job}.json"
    result_file.write_text(
        json.dumps(provisional_mutation_payload(job)),
        encoding="utf-8",
    )
    (attestations / f"{DEV_SHA}.json").write_text(
        json.dumps(valid_attestation_payload(job)),
        encoding="utf-8",
    )
    (published_results / f"{job}.json").write_text(
        json.dumps(published_certified_payload(job)),
        encoding="utf-8",
    )
    (published / f"{job}.json").write_text(
        "published=2026-11-05T01:04:24Z\n"
        f"commit={PUB_COMMIT}\n"
        "certification=CERTIFIED\n",
        encoding="utf-8",
    )

    if corruption_kind == "empty_result_file":
        result_file.write_bytes(b"")
    elif corruption_kind == "corrupt_result_json":
        result_file.write_text("{corrupt", encoding="utf-8")
    elif corruption_kind == "job_id_mismatch_in_result":
        result_file.write_text(
            json.dumps(provisional_mutation_payload("OTHER-JOB")),
            encoding="utf-8",
        )
    elif corruption_kind == "corrupt_published_marker":
        (published / f"{job}.json").write_text(
            "not-a-valid-marker-line\n",
            encoding="utf-8",
        )
    elif corruption_kind == "corrupt_attestation_json":
        (attestations / f"{DEV_SHA}.json").write_text(
            "{corrupt-attestation",
            encoding="utf-8",
        )
    elif corruption_kind == "mismatched_marker_result_sha256":
        (published / f"{job}.json").write_text(
            json.dumps(
                {
                    "job_id": job,
                    "status": "PUBLISHED",
                    "certification": "CERTIFIED",
                    "result_sha256": "0" * 64,
                }
            ),
            encoding="utf-8",
        )

    status = service.get_job_status(job)
    assert status["certification"] == "NOT_CERTIFIED"
    assert status["quality_gate"] == "FAIL"
    assert status["tests"] == "FAIL"
    assert status["percent_complete"] == 0
    assert status["terminal_result_valid"] is False


def test_absent_result_with_orphan_published_marker_fails_closed(
    tmp_path,
    monkeypatch,
):
    job = "JOB-ORPHAN-MARKER"
    state, _, published, _, _ = _setup_queue_state(tmp_path)
    monkeypatch.setattr(service, "STATE_ROOT", state)

    (published / f"{job}.json").write_text(
        "published=2026-11-05T01:04:24Z\n"
        f"commit={PUB_COMMIT}\n"
        "certification=CERTIFIED\n",
        encoding="utf-8",
    )

    status = service.get_job_status(job)
    assert status["lifecycle"] == "RESULT"
    assert status["status"] == "RESULT_ABSENT"
    assert status["certification"] == "NOT_CERTIFIED"
    assert status["work_completion"] == "RESULT_ABSENT"
    assert status["quality_gate"] == "FAIL"
    assert status["percent_complete"] == 0
    assert status["terminal_result_valid"] is False
    assert status["result_state"] == "RESULT_ABSENT"
    assert status["production_touched"] is False

    missing = service.get_job_status("JOB-COMPLETELY-ABSENT")
    assert missing == {
        "job_id": "JOB-COMPLETELY-ABSENT",
        "lifecycle": "NOT_FOUND",
        "status": "NOT_FOUND",
        "production_touched": False,
    }


def test_mcp_get_job_status_tool_exposes_reconciled_certification_fields(
    tmp_path,
    monkeypatch,
):
    for candidate in sorted(
        Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")
    ):
        if str(candidate) not in sys.path:
            sys.path.append(str(candidate))

    from mcp.server.auth.provider import AccessToken
    from modules.worker_mcp import server as mcp_server
    from modules.worker_mcp.config import WorkerMcpConfig

    job = "JOB-MCP-RECONCILED-100"
    state, results, published, published_results, attestations = _setup_queue_state(
        tmp_path
    )
    monkeypatch.setattr(service, "STATE_ROOT", state)

    (results / f"{job}.json").write_text(
        json.dumps(provisional_mutation_payload(job)),
        encoding="utf-8",
    )
    (attestations / f"{DEV_SHA}.json").write_text(
        json.dumps(valid_attestation_payload(job)),
        encoding="utf-8",
    )
    (published_results / f"{job}.json").write_text(
        json.dumps(published_certified_payload(job)),
        encoding="utf-8",
    )
    (published / f"{job}.json").write_text(
        "published=2026-11-05T01:04:24Z\n"
        f"commit={PUB_COMMIT}\n"
        "certification=CERTIFIED\n",
        encoding="utf-8",
    )

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
        lambda *, backend_url, token, job_id: service.get_job_status(job_id),
    )

    mcp_response = mcp_server.get_job_status_tool(job)
    assert mcp_response["job_id"] == job
    assert mcp_response["lifecycle"] == "RESULT"
    assert mcp_response["status"] == "INTEGRATED"
    assert mcp_response["certification"] == "CERTIFIED"
    assert mcp_response["work_completion"] == "COMPLETE"
    assert mcp_response["percent_complete"] == 100
    assert mcp_response["quality_gate"] == "PASS"
    assert mcp_response["tests"] == "PASS"
    assert mcp_response["commit_sha"] == DEV_SHA
    assert mcp_response["certified_source_sha"] == DEV_SHA
    assert mcp_response["converged_head"] == DEV_SHA
    assert (
        mcp_response["certification_basis"]
        == "SHA_BOUND_ATTESTATION_PLUS_ARTIFACT_CONVERGENCE"
    )
    assert mcp_response["terminal_result_valid"] is True
    assert mcp_response["result_state"] == "RESULT_TERMINAL_VALID"
    assert mcp_response["production_touched"] is False
