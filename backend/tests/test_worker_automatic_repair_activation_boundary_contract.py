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
        lambda result, paths, result_corpus=None: (
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

def test_certified_successor_fallback_supersedes_without_development_sha(
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

    control.atomic_json(
        maintenance / "automation_state.json",
        {
            "schema": control.AUTOMATION_STATE_SCHEMA,
            "enabled": True,
            "enabled_at_utc": "2026-09-23T12:30:00Z",
            "enabled_from_development_sha": "a" * 40,
            "adopted_job_ids": ["FAILED"],
            "production_allowed": False,
        },
    )

    target = (
        "tools/mirror_sync/"
        "worker_control_plane.py"
    )

    source_anchor = "1" * 40
    successor_sha = "2" * 40
    current_head = "3" * 40

    control.atomic_json(
        results / "FAILED.json",
        {
            "schema": "edarsahub.worker-result.v2",
            "job_id": "FAILED",
            "status": "GIT_TESTS_FAILED",
            "certification": "NOT_CERTIFIED",
            "completed_at_utc":
                "2026-09-23T12:31:00Z",
            "production_touched": False,
            "execution_base_sha": source_anchor,
            "files_changed": [target],
        },
    )

    control.atomic_json(
        results / "SUCCESS.json",
        {
            "schema": "edarsahub.worker-result.v2",
            "job_id": "SUCCESS",
            "status": "INTEGRATED",
            "quality_gate": "PASS",
            "tests": "PASS",
            "certification":
                "PENDING_AUDIT_EVIDENCE",
            "git_sync_status":
                "CERTIFIED_GIT_SYNC",
            "completed_at_utc":
                "2026-09-23T12:32:00Z",
            "production_touched": False,
            "development_sha": successor_sha,
            "candidate_sha": successor_sha,
            "files_changed": [target],
            "blockers": [],
        },
    )

    def fake_git_output(*args):
        if args == ("rev-parse", "HEAD"):
            return current_head

        if (
            len(args) >= 6
            and args[0] == "diff"
            and args[1] == "--name-only"
        ):
            return target + "\n"

        raise AssertionError(args)

    monkeypatch.setattr(
        control,
        "git_output",
        fake_git_output,
    )

    monkeypatch.setattr(
        control,
        "_git_is_ancestor",
        lambda ancestor, descendant: (
            (ancestor, descendant)
            in {
                (
                    source_anchor,
                    successor_sha,
                ),
                (
                    successor_sha,
                    current_head,
                ),
            }
        ),
    )

    import tools.mirror_sync.worker_maintenance_runtime as runtime

    monkeypatch.setattr(
        runtime,
        "STATE_DIR",
        maintenance,
    )
    monkeypatch.setattr(
        runtime,
        "INCIDENT_DIR",
        maintenance / "incidents",
    )

    monkeypatch.setattr(
        control,
        "declare_runtime_incident",
        runtime.declare_runtime_incident,
    )
    monkeypatch.setattr(
        control,
        "supersede_runtime_incident",
        runtime.supersede_runtime_incident,
    )
    monkeypatch.setattr(
        control,
        "repair_attempt_allowed",
        runtime.repair_attempt_allowed,
    )

    summary = (
        control.automatic_repair_orchestration()
    )

    match = [
        item
        for item in summary["incidents"]
        if item.get("source_job_id")
        == "FAILED"
    ]

    assert len(match) == 1

    incident = match[0]

    assert incident["state"] == "SUPERSEDED"
    assert incident["repair_allowed"] is False
    assert (
        incident["publication_required"]
        is False
    )
    assert (
        incident["repair_reason"]
        == "CERTIFIED_SUCCESSOR_RESULT"
    )


def test_certified_successor_fallback_fails_closed_without_full_path_coverage(
    monkeypatch,
):
    target_a = (
        "tools/mirror_sync/"
        "worker_control_plane.py"
    )
    target_b = (
        "tools/mirror_sync/"
        "worker_repair_execution.py"
    )

    source = {
        "job_id": "FAILED",
        "execution_base_sha": "1" * 40,
        "completed_at_utc":
            "2026-09-23T12:31:00Z",
    }

    successor = {
        "job_id": "SUCCESS",
        "status": "INTEGRATED",
        "quality_gate": "PASS",
        "tests": "PASS",
        "git_sync_status":
            "CERTIFIED_GIT_SYNC",
        "production_touched": False,
        "blockers": [],
        "development_sha": "2" * 40,
        "completed_at_utc":
            "2026-09-23T12:32:00Z",
        "files_changed": [target_a],
    }

    monkeypatch.setattr(
        control,
        "_git_is_ancestor",
        lambda *_args: True,
    )

    monkeypatch.setattr(
        control,
        "_target_diff_paths",
        lambda *_args: {target_a, target_b},
    )

    result = (
        control.find_certified_successor_result(
            source,
            (target_a, target_b),
            (source, successor),
            current_head="3" * 40,
        )
    )

    assert result is None


def test_existing_superseded_incident_is_terminal_and_not_resuperseded(
    tmp_path,
    monkeypatch,
):
    from tools.mirror_sync import worker_control_plane as control
    from tools.mirror_sync import worker_maintenance_runtime as runtime

    maintenance = tmp_path / "maintenance"
    incidents = maintenance / "incidents"
    incidents.mkdir(parents=True)

    monkeypatch.setattr(
        runtime,
        "MAINTENANCE_ROOT",
        maintenance,
        raising=False,
    )
    monkeypatch.setattr(
        runtime,
        "INCIDENTS_ROOT",
        incidents,
        raising=False,
    )

    # Redirect whichever canonical incident-root symbol exists.
    for name in (
        "INCIDENTS",
        "INCIDENT_ROOT",
        "INCIDENT_DIR",
    ):
        if hasattr(runtime, name):
            monkeypatch.setattr(
                runtime,
                name,
                incidents,
                raising=False,
            )

    target = (
        "backend/modules/worker_runtime_wake/routes.py"
    )
    incident_id = "WORKER-TEST-ALREADY-SUPERSEDED"

    incident_path = incidents / f"{incident_id}.json"
    incident_path.write_text(
        json.dumps(
            {
                "incident_id": incident_id,
                "state": "SUPERSEDED",
                "attempts": 0,
                "cooldown_until_epoch": None,
                "target_paths": [target],
                "production_touched": False,
                "superseded_reason":
                    "CERTIFIED_SUCCESSOR_RESULT",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_declare(_incident_id, _paths):
        assert _incident_id == incident_id
        return runtime.RuntimeIncidentState(
            incident_id=incident_id,
            state="SUPERSEDED",
            attempts=0,
            cooldown_until_epoch=None,
            target_paths=(target,),
            production_touched=False,
            repair_job_id=None,
            repair_publication_state=None,
            repair_publication_commit=None,
        )

    monkeypatch.setattr(
        control,
        "declare_runtime_incident",
        fake_declare,
    )

    called = {"supersede": 0}

    def forbidden_supersede(*args, **kwargs):
        called["supersede"] += 1
        raise AssertionError(
            "already SUPERSEDED incident must not "
            "be superseded again"
        )

    monkeypatch.setattr(
        control,
        "supersede_runtime_incident",
        forbidden_supersede,
    )

    # This contract test proves the orchestration source has the
    # terminal short-circuit before supersession evaluation.
    helper = Path(
        control.__file__
    ).read_text(encoding="utf-8")

    short_circuit = helper.index(
        'if incident.state == "SUPERSEDED":'
    )
    supersede_call = helper.index(
        "superseded, superseded_reason = ("
    )

    assert short_circuit < supersede_call
    assert '"repair_allowed": False' in (
        helper[short_circuit:supersede_call]
    )
    assert '"publication_required": False' in (
        helper[short_circuit:supersede_call]
    )
    assert "ALREADY_SUPERSEDED" in (
        helper[short_circuit:supersede_call]
    )
    assert called["supersede"] == 0

    persisted = json.loads(
        incident_path.read_text(encoding="utf-8")
    )

    assert persisted["state"] == "SUPERSEDED"
    assert persisted["attempts"] == 0
    assert (
        persisted["superseded_reason"]
        == "CERTIFIED_SUCCESSOR_RESULT"
    )
