import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync import worker_control_plane as control
from tools.mirror_sync import worker_maintenance_runtime as runtime


def test_missing_automation_state_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(control, "ROOT", tmp_path)

    state = control.load_repair_automation_state()

    assert state["valid"] is False
    assert state["enabled"] is False
    assert state["production_allowed"] is False


def test_historical_result_is_not_automatically_eligible():
    state = {
        "schema": control.AUTOMATION_STATE_SCHEMA,
        "enabled": True,
        "enabled_at_utc": "2026-09-23T12:30:00Z",
        "enabled_from_development_sha": "a" * 40,
        "adopted_job_ids": [],
        "production_allowed": False,
        "valid": True,
    }

    result = {
        "job_id": "OLD-JOB",
        "completed_at_utc": "2026-09-22T12:00:00Z",
        "production_touched": False,
    }

    allowed, reason = control.automatic_repair_result_is_eligible(
        result,
        state,
    )

    assert allowed is False
    assert reason == "HISTORICAL_RESULT"


def test_post_activation_result_is_eligible():
    state = {
        "schema": control.AUTOMATION_STATE_SCHEMA,
        "enabled": True,
        "enabled_at_utc": "2026-09-23T12:30:00Z",
        "enabled_from_development_sha": "a" * 40,
        "adopted_job_ids": [],
        "production_allowed": False,
        "valid": True,
    }

    result = {
        "job_id": "NEW-JOB",
        "completed_at_utc": "2026-09-23T12:31:00Z",
        "production_touched": False,
    }

    allowed, reason = control.automatic_repair_result_is_eligible(
        result,
        state,
    )

    assert allowed is True
    assert reason == "POST_ACTIVATION_RESULT"


def test_historical_result_requires_explicit_adoption():
    state = {
        "schema": control.AUTOMATION_STATE_SCHEMA,
        "enabled": True,
        "enabled_at_utc": "2026-09-23T12:30:00Z",
        "enabled_from_development_sha": "a" * 40,
        "adopted_job_ids": ["OLD-JOB"],
        "production_allowed": False,
        "valid": True,
    }

    result = {
        "job_id": "OLD-JOB",
        "completed_at_utc": "2026-09-22T12:00:00Z",
        "production_touched": False,
    }

    allowed, reason = control.automatic_repair_result_is_eligible(
        result,
        state,
    )

    assert allowed is True
    assert reason == "EXPLICITLY_ADOPTED"


def test_invalid_timestamp_fails_closed():
    state = {
        "schema": control.AUTOMATION_STATE_SCHEMA,
        "enabled": True,
        "enabled_at_utc": "2026-09-23T12:30:00Z",
        "enabled_from_development_sha": "a" * 40,
        "adopted_job_ids": [],
        "production_allowed": False,
        "valid": True,
    }

    result = {
        "job_id": "BAD-TIME",
        "completed_at_utc": "not-a-date",
        "production_touched": False,
    }

    allowed, reason = control.automatic_repair_result_is_eligible(
        result,
        state,
    )

    assert allowed is False
    assert reason == "RESULT_COMPLETED_AT_INVALID"


def test_production_touch_is_never_eligible():
    state = {
        "schema": control.AUTOMATION_STATE_SCHEMA,
        "enabled": True,
        "enabled_at_utc": "2026-09-23T12:30:00Z",
        "enabled_from_development_sha": "a" * 40,
        "adopted_job_ids": ["PROD-JOB"],
        "production_allowed": False,
        "valid": True,
    }

    result = {
        "job_id": "PROD-JOB",
        "completed_at_utc": "2026-09-23T12:31:00Z",
        "production_touched": True,
    }

    allowed, reason = control.automatic_repair_result_is_eligible(
        result,
        state,
    )

    assert allowed is False
    assert reason == "PRODUCTION_TOUCHED"


def test_automatic_orchestration_observes_but_does_not_declare_historical(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(control, "ROOT", tmp_path)

    results = (
        tmp_path
        / ".git"
        / "universal-worker-queue"
        / "results"
    )
    maintenance = (
        tmp_path
        / ".git"
        / "universal-worker-queue"
        / "maintenance"
    )

    results.mkdir(parents=True)
    maintenance.mkdir(parents=True)

    (maintenance / "automation_state.json").write_text(
        json.dumps(
            {
                "schema": control.AUTOMATION_STATE_SCHEMA,
                "enabled": True,
                "enabled_at_utc": "2026-09-23T12:30:00Z",
                "enabled_from_development_sha": "a" * 40,
                "adopted_job_ids": [],
                "production_allowed": False,
            }
        ),
        encoding="utf-8",
    )

    (results / "OLD.json").write_text(
        json.dumps(
            {
                "schema": "edarsahub.worker-result.v2",
                "job_id": "OLD",
                "status": "GIT_TESTS_FAILED",
                "certification": "NOT_CERTIFIED",
                "completed_at_utc": "2026-09-22T10:00:00Z",
                "production_touched": False,
                "files_changed": [
                    "tools/mirror_sync/worker_control_plane.py"
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = control.automatic_repair_orchestration()

    assert summary["observed_terminal_results"] == 1
    assert summary["eligible_incidents"] == 0
    assert summary["declared_incidents"] == 0

    assert len(summary["incidents"]) == 1
    incident = summary["incidents"][0]

    assert incident["state"] == "OBSERVED_NOT_ELIGIBLE"
    assert incident["repair_reason"] == "HISTORICAL_RESULT"
    assert incident["publication_required"] is False

    incident_dir = (
        tmp_path
        / ".git"
        / "universal-worker-queue"
        / "maintenance"
        / "incidents"
    )

    assert not incident_dir.exists()


def test_activation_does_not_create_repair_incident(tmp_path, monkeypatch):
    monkeypatch.setattr(control, "ROOT", tmp_path)

    maintenance = (
        tmp_path
        / ".git"
        / "universal-worker-queue"
        / "maintenance"
    )
    maintenance.mkdir(parents=True)

    control.atomic_json(
        maintenance / "automation_state.json",
        {
            "schema": control.AUTOMATION_STATE_SCHEMA,
            "enabled": True,
            "enabled_at_utc": "2026-09-23T12:30:00Z",
            "enabled_from_development_sha": "a" * 40,
            "adopted_job_ids": [],
            "production_allowed": False,
        },
    )

    assert (
        maintenance / "automation_state.json"
    ).is_file()

    assert not (
        maintenance / "incidents"
    ).exists()

def test_superseded_incident_is_not_published(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(control, "ROOT", tmp_path)
    monkeypatch.setattr(
        runtime,
        "STATE_DIR",
        (
            tmp_path
            / ".git"
            / "universal-worker-queue"
            / "maintenance"
        ),
    )
    monkeypatch.setattr(
        runtime,
        "INCIDENT_DIR",
        (
            tmp_path
            / ".git"
            / "universal-worker-queue"
            / "maintenance"
            / "incidents"
        ),
    )

    results = (
        tmp_path
        / ".git"
        / "universal-worker-queue"
        / "results"
    )
    maintenance = (
        tmp_path
        / ".git"
        / "universal-worker-queue"
        / "maintenance"
    )

    results.mkdir(parents=True)
    maintenance.mkdir(parents=True)

    control.atomic_json(
        maintenance / "automation_state.json",
        {
            "schema": control.AUTOMATION_STATE_SCHEMA,
            "enabled": True,
            "enabled_at_utc": "2026-09-23T12:30:00Z",
            "enabled_from_development_sha": "a" * 40,
            "adopted_job_ids": ["STALE"],
            "production_allowed": False,
        },
    )

    target = "tools/mirror_sync/worker_control_plane.py"

    control.atomic_json(
        results / "STALE.json",
        {
            "schema": "edarsahub.worker-result.v2",
            "job_id": "STALE",
            "status": "GIT_TESTS_FAILED",
            "certification": "NOT_CERTIFIED",
            "completed_at_utc": "2026-09-23T12:31:00Z",
            "production_touched": False,
            "development_sha": "1" * 40,
            "files_changed": [target],
        },
    )

    monkeypatch.setattr(
        control,
        "repair_incident_is_superseded",
        lambda result, paths: (
            True,
            "SUPERSEDED_BY_CURRENT_HEAD",
        ),
    )

    summary = control.automatic_repair_orchestration()

    match = [
        item
        for item in summary["incidents"]
        if item.get("source_job_id") == "STALE"
    ]

    assert len(match) == 1

    incident = match[0]

    assert incident["state"] == "SUPERSEDED"
    assert incident["repair_allowed"] is False
    assert incident["publication_required"] is False
    assert (
        incident["repair_reason"]
        == "SUPERSEDED_BY_CURRENT_HEAD"
    )
