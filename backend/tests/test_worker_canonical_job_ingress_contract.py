from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.mirror_sync import gate_chain_publisher as ingress


def requester():
    return {
        "email": "test@example.invalid",
        "source": "pytest",
        "project": "EDARSAHUB",
        "chat": "canonical-ingress",
    }


def readonly_job(job_id):
    return {
        "job_id": job_id,
        "objective": "Test canonical ingress.",
        "requester": requester(),
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [
            {
                "type": "git_diff_check",
            }
        ],
    }


def readonly_sql_job(job_id):
    return {
        "job_id": job_id,
        "objective": "Test READ_ONLY_SQL ingress.",
        "requester": requester(),
        "mode": "READ_ONLY_SQL",
        "actions": [],
        "checks": [
            {
                "type": "sql_readonly_audit",
                "source": "EDARSAHUB",
                "queries": [
                    {
                        "name": "identity",
                        "sql": (
                            "SELECT DB_NAME() "
                            "AS database_name"
                        ),
                    }
                ],
            }
        ],
    }


def redirect_state(
    tmp_path,
    monkeypatch,
):
    for name in (
        "DRAFTS",
        "PENDING",
        "PROCESSING",
        "RESULTS",
        "DONE",
        "REJECTED",
    ):
        path = (
            tmp_path
            / name.lower()
        )

        path.mkdir()

        monkeypatch.setattr(
            ingress,
            name,
            path,
        )


def test_submit_exists():
    assert callable(
        ingress.submit
    )


def test_readonly_sql_allowed_only_in_query():
    result = ingress.validate_template(
        readonly_sql_job(
            "INGRESS-SQL-1"
        )
    )

    assert (
        result["mode"]
        == "READ_ONLY_SQL"
    )

    bad = readonly_sql_job(
        "INGRESS-SQL-2"
    )

    bad["requester"]["sql"] = (
        "SELECT 1"
    )

    with pytest.raises(
        ValueError,
        match="FORBIDDEN_TEMPLATE_KEY:sql",
    ):
        ingress.validate_template(
            bad
        )


def test_completed_idempotency(
    tmp_path,
    monkeypatch,
):
    redirect_state(
        tmp_path,
        monkeypatch,
    )

    (
        ingress.RESULTS
        / "INGRESS-DONE.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = ingress.submit(
        readonly_job(
            "INGRESS-DONE"
        )
    )

    assert (
        result["status"]
        == "ALREADY_COMPLETED"
    )


def test_processing_idempotency(
    tmp_path,
    monkeypatch,
):
    redirect_state(
        tmp_path,
        monkeypatch,
    )

    (
        ingress.PROCESSING
        / "INGRESS-PROCESSING.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = ingress.submit(
        readonly_job(
            "INGRESS-PROCESSING"
        )
    )

    assert (
        result["status"]
        == "ALREADY_PROCESSING"
    )


def test_pending_idempotency(
    tmp_path,
    monkeypatch,
):
    redirect_state(
        tmp_path,
        monkeypatch,
    )

    (
        ingress.PENDING
        / "INGRESS-PENDING.json"
    ).write_text(
        "{}\n",
        encoding="utf-8",
    )

    result = ingress.submit(
        readonly_job(
            "INGRESS-PENDING"
        )
    )

    assert (
        result["status"]
        == "ALREADY_SUBMITTED"
    )


def test_queue_paths_are_repo_scoped():
    assert "universal-worker-queue" in str(
        ingress.DRAFTS
    )
    assert str(ingress.DRAFTS).endswith(
        ".git/universal-worker-queue/drafts"
    )


def test_submit_reuses_canonical_publisher():
    source = Path(
        ingress.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "def submit(" in source
    assert "publication = publish(" in source


def test_not_certified_slot_claim_block_is_retryable(
    tmp_path,
    monkeypatch,
):

    redirect_state(
        tmp_path,
        monkeypatch,
    )
    result_path = (
        ingress.RESULTS
        / "INGRESS-SLOT-BLOCKED.json"
    )

    result_path.write_text(
        json.dumps(
            {
                "status": "BLOCKED",
                "certification": "NOT_CERTIFIED",
                "percent_complete": 0,
                "production_touched": False,
                "blockers": [
                    "dispatcher_exception:"
                    "SlotRuntimeError:"
                    "SLOT_ALREADY_CLAIMED"
                ],
            }
        ),
        encoding="utf-8",
    )

    result = ingress._submit_local_lifecycle(
        "INGRESS-SLOT-BLOCKED"
    )

    assert result is None


def _bridge_redirect_state(tmp_path, monkeypatch):
    from tools.mirror_sync import universal_job_bridge as bridge

    for name in (
        "PENDING",
        "PROCESSING",
        "REJECTED",
        "REJECTED_HISTORY",
        "DONE",
        "RESULTS",
    ):
        path = tmp_path / ("bridge-" + name.lower())
        path.mkdir()
        monkeypatch.setattr(bridge, name, path)

    monkeypatch.setattr(bridge, "REQUIRE_REQUESTER", False)
    return bridge


def _bridge_readonly_job(job_id):
    return {
        "schema": "edarsahub.worker-job.v2",
        "job_id": job_id,
        "target_repo": "rbalam/EDARSA_HUB",
        "target_branch": "Edarsahub_Desarrollo",
        "objective": "Canonical bridge same-job retry contract.",
        "production_allowed": False,
        "human_summary_language": "es",
        "mode": "READ_ONLY",
        "actions": [],
        "checks": [{"type": "git_diff_check"}],
    }


def _write_bridge_result(bridge, name, **overrides):
    payload = {
        "status": "BLOCKED",
        "certification": "NOT_CERTIFIED",
        "percent_complete": 0,
        "production_touched": False,
        "blockers": [
            "dispatcher_exception:SlotRuntimeError:SLOT_ALREADY_CLAIMED"
        ],
    }
    payload.update(overrides)
    path = bridge.RESULTS / name
    path.write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def test_bridge_slot_claim_block_reenters_same_job_and_preserves_evidence(
    tmp_path,
    monkeypatch,
):
    bridge = _bridge_redirect_state(tmp_path, monkeypatch)
    name = "INGRESS-SLOT-BLOCKED.json"
    result_path = _write_bridge_result(bridge, name)
    result_before = result_path.read_bytes()

    rejected_path = bridge.REJECTED / name
    rejected_raw = bridge.REJECTED / f"{name}.raw"
    rejected_path.write_text('{"status":"REJECTED"}\n', encoding="utf-8")
    rejected_raw.write_text('{"historical":true}\n', encoding="utf-8")
    rejected_before = rejected_path.read_bytes()
    rejected_raw_before = rejected_raw.read_bytes()

    job = _bridge_readonly_job("INGRESS-SLOT-BLOCKED")
    raw = json.dumps(job)
    monkeypatch.setattr(
        bridge,
        "queue_files",
        lambda: ["worker_queue/inbox/" + name],
    )
    monkeypatch.setattr(bridge, "read_remote", lambda path: raw)

    assert bridge.already_claimed(name) is False
    assert bridge.receive() == 0

    pending = bridge.PENDING / name
    assert pending.is_file()
    envelope = json.loads(pending.read_text(encoding="utf-8"))
    assert envelope["job"]["job_id"] == "INGRESS-SLOT-BLOCKED"
    assert envelope["_worker_slot_claim_retry"]["same_job_id"] is True
    assert envelope["_worker_slot_claim_retry"]["evidence_preserved"] is True

    assert result_path.read_bytes() == result_before
    assert rejected_path.read_bytes() == rejected_before
    assert rejected_raw.read_bytes() == rejected_raw_before


def test_bridge_certified_result_remains_terminal(
    tmp_path,
    monkeypatch,
):
    bridge = _bridge_redirect_state(tmp_path, monkeypatch)
    name = "INGRESS-CERTIFIED.json"
    _write_bridge_result(
        bridge,
        name,
        status="INTEGRATED",
        certification="CERTIFIED",
        percent_complete=100,
        blockers=[],
    )
    assert bridge.already_claimed(name) is True


def test_bridge_other_not_certified_blocker_remains_terminal(
    tmp_path,
    monkeypatch,
):
    bridge = _bridge_redirect_state(tmp_path, monkeypatch)
    name = "INGRESS-OTHER-BLOCKER.json"
    _write_bridge_result(
        bridge,
        name,
        blockers=["dispatcher_exception:RuntimeError:OTHER_BLOCKER"],
    )
    assert bridge.already_claimed(name) is True


def test_bridge_slot_claim_with_extra_blocker_remains_terminal(
    tmp_path,
    monkeypatch,
):
    bridge = _bridge_redirect_state(tmp_path, monkeypatch)
    name = "INGRESS-EXTRA-BLOCKER.json"
    _write_bridge_result(
        bridge,
        name,
        blockers=[
            "dispatcher_exception:SlotRuntimeError:SLOT_ALREADY_CLAIMED",
            "another_blocker",
        ],
    )
    assert bridge.already_claimed(name) is True


def test_bridge_not_certified_nonzero_progress_remains_terminal(
    tmp_path,
    monkeypatch,
):
    bridge = _bridge_redirect_state(tmp_path, monkeypatch)
    name = "INGRESS-NONZERO.json"
    _write_bridge_result(
        bridge,
        name,
        percent_complete=1,
    )
    assert bridge.already_claimed(name) is True


def test_bridge_production_touched_result_remains_terminal(
    tmp_path,
    monkeypatch,
):
    bridge = _bridge_redirect_state(tmp_path, monkeypatch)
    name = "INGRESS-PRODUCTION.json"
    _write_bridge_result(
        bridge,
        name,
        production_touched=True,
    )
    assert bridge.already_claimed(name) is True
