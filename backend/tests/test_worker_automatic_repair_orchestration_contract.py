from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]

CONTROL = ROOT / "tools" / "mirror_sync" / "worker_control_plane.py"


def source():
    return CONTROL.read_text(encoding="utf-8")


def function_source(name: str) -> str:
    text = source()
    tree = ast.parse(text)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            lines = text.splitlines()
            return "\n".join(
                lines[node.lineno - 1 : node.end_lineno]
            )

    raise AssertionError(f"missing function: {name}")


def test_automatic_repair_is_part_of_existing_control_plane():
    text = source()

    assert "def automatic_repair_orchestration(" in text
    assert '"automatic_repair": automatic_repair' in text
    assert "automatic_repair_orchestration()" in function_source("cycle")


def test_gate5l_readonly_summary_boundary_remains_intact():
    helper = function_source("maintenance_runtime_summary")

    assert "declare_runtime_incident(" not in helper
    assert "register_repair_attempt(" not in helper
    assert "register_repair_result(" not in helper
    assert "audit_runtime_incident(" not in helper


def test_automatic_repair_uses_existing_maintenance_runtime():
    helper = function_source("automatic_repair_orchestration")

    assert "declare_runtime_incident(" in helper
    assert "repair_attempt_allowed(" in helper

    assert "register_repair_attempt(" not in helper
    assert "register_repair_result(" not in helper
    assert "audit_runtime_incident(" not in helper


def test_automatic_repair_does_not_create_second_dispatcher_or_queue():
    helper = function_source("automatic_repair_orchestration")

    assert "universal_job_dispatcher" not in helper
    assert "dispatch(" not in helper
    assert "subprocess" not in helper
    assert "os.system" not in helper
    assert "shell=True" not in helper
    assert "worker/requests" not in helper


def test_automatic_repair_is_worker_infrastructure_only():
    helper = function_source("automatic_repair_orchestration")

    assert '"tools/mirror_sync/"' in helper
    assert '"backend/tests/test_worker_"' in helper
    assert "frontend/" not in helper
    assert "backend/modules/comercial/" not in helper
    assert "backend/modules/finanzas/" not in helper


def test_automatic_repair_is_fail_closed_for_production():
    helper = function_source("automatic_repair_orchestration")

    assert 'production_touched") is not False' in helper
    assert '"production_touched": False' in helper
    assert "Edarsahub_Produccion" not in helper


def test_incident_identity_is_deterministic_and_scope_bound():
    helper = function_source("automatic_repair_orchestration")

    assert "hashlib.sha256" in helper
    assert "source_job_id" in helper
    assert "status" in helper
    assert "target_paths" in helper


def test_detection_cycle_does_not_execute_or_certify_repair():
    helper = function_source("automatic_repair_orchestration")

    assert '"publication_required": allowed' in helper
    assert "CERTIFIED_WORKER_REPAIR" not in helper
    assert "REPAIRED_PENDING_AUDIT" not in helper

def test_automatic_repair_supports_supersession_before_publication():
    text = source()

    assert "def repair_incident_is_superseded(" in text

    helper = function_source("automatic_repair_orchestration")

    assert "repair_incident_is_superseded(" in helper
    assert "supersede_runtime_incident(" in helper
    assert '"publication_required": False' in helper
    assert '"repair_allowed": False' in helper

def test_automatic_repair_loads_result_corpus_once_per_cycle():
    helper = function_source(
        "automatic_repair_orchestration"
    )

    assert (
        helper.count(
            'results_root.glob("*.json")'
        )
        == 1
    )
    assert "result_corpus" in helper
    assert "result_corpus_tuple" in helper


def test_certified_successor_fallback_is_canonical():
    text = source()

    assert "def automatic_repair_source_anchor(" in text
    assert "def find_certified_successor_result(" in text
    assert (
        "CERTIFIED_SUCCESSOR_RESULT"
        in text
    )

    helper = function_source(
        "automatic_repair_orchestration"
    )

    assert (
        "result_corpus=result_corpus_tuple"
        in helper
    )

def test_git_lock_busy_is_a_repairable_worker_incident():
    text = source()
    helper = function_source("automatic_repair_orchestration")

    assert '"GIT_LOCK_BUSY"' in helper
    assert "GIT_LOCK_BUSY_REPAIR_PATHS" in helper
    assert (
        '"tools/mirror_sync/git_divergence_guard.py"'
        in text
    )
    assert (
        '"tools/mirror_sync/universal_job_dispatcher.py"'
        in text
    )


def test_source_anchor_prioritizes_base_commits_before_candidate_sha(
    tmp_path,
    monkeypatch,
):
    import json
    from tools.mirror_sync import worker_control_plane as control

    base_sha = "1" * 40
    candidate_sha = "2" * 40
    anchor, field = control.automatic_repair_source_anchor(
        {
            "job_id": "JOB-ANCHOR-ORDER",
            "candidate_sha": candidate_sha,
            "execution_base_sha": base_sha,
        }
    )
    assert anchor == base_sha
    assert field == "execution_base_sha"

    queue_done = (
        tmp_path / ".git" / "universal-worker-queue" / "done"
    )
    queue_done.mkdir(parents=True, exist_ok=True)
    envelope_sha = "3" * 40
    (queue_done / "JOB-ENVELOPE-FALLBACK.json").write_text(
        json.dumps({"job": {"base_sha": envelope_sha}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(control, "ROOT", tmp_path)
    anchor2, field2 = control.automatic_repair_source_anchor(
        {"job_id": "JOB-ENVELOPE-FALLBACK"}
    )
    assert anchor2 == envelope_sha
    assert field2 == "job_envelope_base_sha"


def test_find_certified_successor_supports_preworktree_git_lock_busy(
    monkeypatch,
):
    from tools.mirror_sync import worker_control_plane as control

    monkeypatch.setattr(
        control,
        "_git_is_ancestor",
        lambda _a, _b: True,
    )
    monkeypatch.setattr(
        control,
        "_target_diff_paths",
        lambda _a, _b, paths: set(paths),
    )

    source_res = {
        "job_id": "OLD-LOCK-BUSY-JOB",
        "status": "GIT_LOCK_BUSY",
        "completed_at_utc": "2026-09-25T02:16:37Z",
        "production_touched": False,
    }
    target_paths = (
        "tools/mirror_sync/git_divergence_guard.py",
        "tools/mirror_sync/universal_job_dispatcher.py",
    )
    successor_res = {
        "job_id": "LATER-CERTIFIED-REPAIR",
        "status": "INTEGRATED",
        "certification": "CERTIFIED",
        "quality_gate": "PASS",
        "tests": "PASS",
        "git_sync_status": "CERTIFIED_GIT_SYNC",
        "production_touched": False,
        "completed_at_utc": "2026-10-01T21:11:12Z",
        "execution_base_sha": "a" * 40,
        "development_sha": "b" * 40,
        "files_changed": list(target_paths),
    }

    matched = control.find_certified_successor_result(
        source_res,
        target_paths,
        (successor_res,),
        current_head="c" * 40,
    )
    assert matched is not None
    assert matched["job_id"] == "LATER-CERTIFIED-REPAIR"


def _duplicate_cause_env(
    tmp_path,
    monkeypatch,
    jobs,
    *,
    omit_job_id_for: set[str] | None = None,
):
    import json
    from tools.mirror_sync import worker_control_plane as control
    from tools.mirror_sync import worker_maintenance_runtime as maintenance

    omit = set(omit_job_id_for or ())
    state = tmp_path / ".git" / "universal-worker-queue" / "maintenance"
    monkeypatch.setattr(control, "ROOT", tmp_path)
    monkeypatch.setattr(maintenance, "STATE_DIR", state)
    monkeypatch.setattr(maintenance, "INCIDENT_DIR", state / "incidents")
    monkeypatch.setattr(
        control,
        "load_repair_automation_state",
        lambda: {"valid": True, "enabled": True, "production_allowed": False},
    )
    monkeypatch.setattr(
        control,
        "automatic_repair_result_is_eligible",
        lambda result, state: (True, "POST_ACTIVATION_RESULT"),
    )
    monkeypatch.setattr(
        control,
        "repair_incident_is_superseded",
        lambda result, paths, result_corpus=(): (
            False,
            "SOURCE_IS_CURRENT_HEAD",
        ),
    )

    results = tmp_path / ".git" / "universal-worker-queue" / "results"
    results.mkdir(parents=True, exist_ok=True)
    for job_id, completed_at in jobs:
        payload = {
            "status": "GIT_LOCK_BUSY",
            "certification": "NOT_CERTIFIED",
            "completed_at_utc": completed_at,
            "production_touched": False,
            "blockers": ["dispatcher_exception:RuntimeError:GIT_LOCK_BUSY"],
        }
        if job_id not in omit:
            payload["job_id"] = job_id
        (results / f"{job_id}.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
    return control, maintenance


def test_duplicate_root_cause_selects_one_repair_incident(
    tmp_path,
    monkeypatch,
):
    control, maintenance = _duplicate_cause_env(
        tmp_path,
        monkeypatch,
        (
            ("LOCK-BUSY-OLDER", "2026-10-21T10:00:00Z"),
            ("LOCK-BUSY-NEWER", "2026-10-21T11:00:00Z"),
        ),
        omit_job_id_for={"LOCK-BUSY-OLDER"},
    )

    summary = control.automatic_repair_orchestration()
    selected = [
        i
        for i in summary["incidents"]
        if i.get("publication_required") is True
    ]
    suppressed = [
        i
        for i in summary["incidents"]
        if i.get("repair_reason") == "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
    ]

    assert len(selected) == 1
    assert selected[0]["source_job_id"] == "LOCK-BUSY-NEWER"
    assert len(suppressed) == 1
    assert suppressed[0]["source_job_id"] == "LOCK-BUSY-OLDER"
    assert suppressed[0]["state"] == "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
    assert suppressed[0]["repair_allowed"] is False
    assert suppressed[0]["publication_required"] is False
    assert (
        suppressed[0]["selected_incident_id"]
        == selected[0]["incident_id"]
    )
    assert summary["selected_incidents"] == 1
    assert summary["declared_incidents"] == 1
    assert (
        maintenance.read_runtime_incident(
            suppressed[0]["incident_id"]
        )
        is None
    )

    # Second cycle must remain idempotent with identical winner and zero
    # persisted incident creation for suppressed duplicates.
    second_summary = control.automatic_repair_orchestration()
    assert second_summary["selected_incidents"] == 1
    assert second_summary["declared_incidents"] == 1
    assert (
        maintenance.read_runtime_incident(
            suppressed[0]["incident_id"]
        )
        is None
    )


def test_duplicate_root_cause_preserves_incident_with_linked_repair_job(
    tmp_path,
    monkeypatch,
):
    import hashlib

    control, maintenance = _duplicate_cause_env(
        tmp_path,
        monkeypatch,
        (
            ("LOCK-BUSY-LINKED", "2026-10-21T10:00:00Z"),
            ("LOCK-BUSY-NEWER", "2026-10-21T11:00:00Z"),
        ),
    )
    paths = list(control.GIT_LOCK_BUSY_REPAIR_PATHS)
    digest = hashlib.sha256(
        (
            "LOCK-BUSY-LINKED\nGIT_LOCK_BUSY\n"
            + "\n".join(sorted(paths))
        ).encode("utf-8")
    ).hexdigest()[:20]
    linked_id = f"WORKER-{digest}"

    maintenance.declare_runtime_incident(linked_id, paths)
    maintenance.register_published_repair_attempt(
        linked_id,
        "WORKER-REPAIR-LINKED-A1",
        {"status": "PUBLISHED", "commit_sha": "a" * 40},
    )

    summary = control.automatic_repair_orchestration()
    by_source = {i["source_job_id"]: i for i in summary["incidents"]}

    assert (
        by_source["LOCK-BUSY-NEWER"]["repair_reason"]
        == "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
    )
    assert by_source["LOCK-BUSY-NEWER"]["selected_incident_id"] == linked_id
    assert by_source["LOCK-BUSY-LINKED"]["incident_id"] == linked_id
    assert (
        by_source["LOCK-BUSY-LINKED"]["state"]
        != "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
    )
    assert (
        maintenance.read_runtime_incident(linked_id).repair_job_id
        == "WORKER-REPAIR-LINKED-A1"
    )


def test_duplicate_root_cause_shares_learned_capability_paths_and_fails_closed_on_ambiguity(
    tmp_path,
    monkeypatch,
):
    import json
    from types import SimpleNamespace
    from tools.mirror_sync import worker_control_plane as control
    from tools.mirror_sync import worker_maintenance_runtime as maintenance

    state = tmp_path / ".git" / "universal-worker-queue" / "maintenance"
    results = tmp_path / ".git" / "universal-worker-queue" / "results"
    results.mkdir(parents=True)

    monkeypatch.setattr(control, "ROOT", tmp_path)
    monkeypatch.setattr(maintenance, "STATE_DIR", state)
    monkeypatch.setattr(maintenance, "INCIDENT_DIR", state / "incidents")
    monkeypatch.setattr(
        control,
        "load_repair_automation_state",
        lambda: {"valid": True, "enabled": True, "production_allowed": False},
    )
    monkeypatch.setattr(
        control,
        "automatic_repair_result_is_eligible",
        lambda result, st: (True, "POST_ACTIVATION_RESULT"),
    )
    monkeypatch.setattr(
        control,
        "repair_incident_is_superseded",
        lambda result, paths, result_corpus=(): (
            False,
            "SOURCE_IS_CURRENT_HEAD",
        ),
    )

    cap_v1 = SimpleNamespace(
        code="CAP_DEDUP_SHARED_V1",
        reusable=True,
        problem_signature="CAP_DEDUP_SIG",
        required_paths=("tools/mirror_sync/worker_control_plane.py",),
        evidence={"blocker_signature": "KNOWN_WORKER_BLOCKER_V1"},
        supersedes=(),
    )
    monkeypatch.setattr(
        control.learned_registry,
        "iter_learned_capabilities",
        lambda: [cap_v1],
    )
    monkeypatch.setattr(
        control.learned_registry,
        "_filter_superseded_capabilities",
        lambda items: list(items),
    )

    # Neither result provides files_changed or expected_scope; paths must come
    # from learned_capability.required_paths, and CAP-OLDER omits job_id to
    # exercise result_path.stem fallback.
    (results / "CAP-OLDER.json").write_text(
        json.dumps(
            {
                "status": "BLOCKED",
                "certification": "NOT_CERTIFIED",
                "completed_at_utc": "2026-10-21T09:00:00Z",
                "production_touched": False,
                "blockers": [
                    "known_worker_blocker_v1",
                    "extra_diagnostic_context_a",
                ],
            }
        ),
        encoding="utf-8",
    )
    (results / "CAP-NEWER.json").write_text(
        json.dumps(
            {
                "job_id": "CAP-NEWER",
                "status": "BLOCKED",
                "certification": "NOT_CERTIFIED",
                "completed_at_utc": "2026-10-21T10:00:00Z",
                "production_touched": False,
                "blockers": [
                    "KNOWN_WORKER_BLOCKER_V1",
                    "extra_diagnostic_context_b",
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = control.automatic_repair_orchestration()
    by_source = {row["source_job_id"]: row for row in summary["incidents"]}

    assert summary["selected_incidents"] == 1
    assert summary["declared_incidents"] == 1
    assert by_source["CAP-NEWER"]["publication_required"] is True
    assert by_source["CAP-NEWER"]["target_paths"] == [
        "tools/mirror_sync/worker_control_plane.py"
    ]
    assert by_source["CAP-NEWER"]["capability_code"] == "CAP_DEDUP_SHARED_V1"
    assert (
        by_source["CAP-OLDER"]["state"]
        == "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
    )
    assert (
        by_source["CAP-OLDER"]["selected_incident_id"]
        == by_source["CAP-NEWER"]["incident_id"]
    )
    assert by_source["CAP-OLDER"]["target_paths"] == [
        "tools/mirror_sync/worker_control_plane.py"
    ]

    # Ambiguous capability match must fail closed with selected_incidents == 0.
    cap_v2 = SimpleNamespace(
        code="CAP_DEDUP_SHARED_V2",
        reusable=True,
        problem_signature="CAP_DEDUP_SIG_2",
        required_paths=("tools/mirror_sync/worker_repair_auto_loop.py",),
        evidence={"blocker_signature": "KNOWN_WORKER_BLOCKER_V1"},
        supersedes=(),
    )
    monkeypatch.setattr(
        control.learned_registry,
        "iter_learned_capabilities",
        lambda: [cap_v1, cap_v2],
    )

    ambiguous_summary = control.automatic_repair_orchestration()
    assert ambiguous_summary["selected_incidents"] == 0
    assert ambiguous_summary["declared_incidents"] == 0
    assert ambiguous_summary["blocked_incidents"] == 2
    assert all(
        row["repair_reason"] == "KNOWN_BLOCKER_CAPABILITY_AMBIGUOUS"
        and row["repair_allowed"] is False
        and row["publication_required"] is False
        for row in ambiguous_summary["incidents"]
    )


def test_duplicate_root_cause_excludes_persisted_and_dynamic_superseded_before_winner_election(
    tmp_path,
    monkeypatch,
):
    import hashlib

    control, maintenance = _duplicate_cause_env(
        tmp_path,
        monkeypatch,
        (
            ("LOCK-BUSY-ACTIVE", "2026-10-21T10:00:00Z"),
            ("LOCK-BUSY-PERSISTED-SUPERSEDED", "2026-10-21T12:00:00Z"),
            ("LOCK-BUSY-DYNAMIC-SUPERSEDED", "2026-10-21T13:00:00Z"),
        ),
    )
    paths = sorted(control.GIT_LOCK_BUSY_REPAIR_PATHS)

    def _inc_id(job_id: str) -> str:
        digest = hashlib.sha256(
            (
                f"{job_id}\nGIT_LOCK_BUSY\n" + "\n".join(paths)
            ).encode("utf-8")
        ).hexdigest()[:20]
        return f"WORKER-{digest}"

    persisted_sup_id = _inc_id("LOCK-BUSY-PERSISTED-SUPERSEDED")
    active_id = _inc_id("LOCK-BUSY-ACTIVE")

    maintenance.declare_runtime_incident(persisted_sup_id, paths)
    maintenance.supersede_runtime_incident(
        persisted_sup_id,
        reason="CERTIFIED_SUCCESSOR_RESULT",
    )

    monkeypatch.setattr(
        control,
        "repair_incident_is_superseded",
        lambda result, target_paths, result_corpus=(): (
            (True, "CERTIFIED_SUCCESSOR_RESULT")
            if result.get("job_id") == "LOCK-BUSY-DYNAMIC-SUPERSEDED"
            else (False, "SOURCE_IS_CURRENT_HEAD")
        ),
    )

    summary = control.automatic_repair_orchestration()
    by_source = {row["source_job_id"]: row for row in summary["incidents"]}

    assert summary["selected_incidents"] == 1
    assert summary["declared_incidents"] == 1
    assert by_source["LOCK-BUSY-ACTIVE"]["incident_id"] == active_id
    assert by_source["LOCK-BUSY-ACTIVE"]["publication_required"] is True
    assert (
        by_source["LOCK-BUSY-PERSISTED-SUPERSEDED"]["state"]
        == "SUPERSEDED"
    )
    assert (
        by_source["LOCK-BUSY-PERSISTED-SUPERSEDED"]["repair_reason"]
        == "ALREADY_SUPERSEDED"
    )
    assert (
        by_source["LOCK-BUSY-DYNAMIC-SUPERSEDED"]["state"]
        == "SUPERSEDED"
    )
    assert (
        by_source["LOCK-BUSY-DYNAMIC-SUPERSEDED"]["repair_reason"]
        == "CERTIFIED_SUCCESSOR_RESULT"
    )


def test_duplicate_root_cause_preserves_cooldown_and_max_attempts_owner(
    tmp_path,
    monkeypatch,
):
    import hashlib
    import json
    import time

    control, maintenance = _duplicate_cause_env(
        tmp_path,
        monkeypatch,
        (
            ("LOCK-BUSY-OWNER", "2026-10-21T10:00:00Z"),
            ("LOCK-BUSY-FRESH-NEWER", "2026-10-21T11:00:00Z"),
        ),
    )
    paths = sorted(control.GIT_LOCK_BUSY_REPAIR_PATHS)
    owner_digest = hashlib.sha256(
        ("LOCK-BUSY-OWNER\nGIT_LOCK_BUSY\n" + "\n".join(paths)).encode(
            "utf-8"
        )
    ).hexdigest()[:20]
    owner_id = f"WORKER-{owner_digest}"

    maintenance.declare_runtime_incident(owner_id, paths)
    maintenance.register_published_repair_attempt(
        owner_id,
        "WORKER-REPAIR-OWNER-A1",
        {"status": "PUBLISHED", "commit_sha": "1" * 40},
        now_epoch=time.time(),
    )
    # Rejecting attempt 1 clears repair_job_id and starts the 300s cooldown.
    maintenance.register_repair_result(
        owner_id,
        {
            "job_id": "WORKER-REPAIR-OWNER-A1",
            "status": "GIT_TESTS_FAILED",
            "production_touched": False,
        },
        now_epoch=time.time(),
    )
    owner_state = maintenance.read_runtime_incident(owner_id)
    assert owner_state.repair_job_id is None
    assert owner_state.attempts == 1

    cooldown_summary = control.automatic_repair_orchestration()
    by_source = {
        row["source_job_id"]: row for row in cooldown_summary["incidents"]
    }
    assert cooldown_summary["selected_incidents"] == 1
    assert cooldown_summary["declared_incidents"] == 0
    assert by_source["LOCK-BUSY-OWNER"]["repair_allowed"] is False
    assert (
        by_source["LOCK-BUSY-OWNER"]["repair_reason"]
        == "REPAIR_COOLDOWN_ACTIVE"
    )
    assert (
        by_source["LOCK-BUSY-FRESH-NEWER"]["state"]
        == "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
    )
    assert (
        by_source["LOCK-BUSY-FRESH-NEWER"]["selected_incident_id"]
        == owner_id
    )

    # Expire cooldown -> owner gets attempt #2, fresh duplicate stays suppressed.
    owner_path = maintenance.INCIDENT_DIR / f"{owner_id}.json"
    raw = json.loads(owner_path.read_text(encoding="utf-8"))
    raw["cooldown_until_epoch"] = time.time() - 10
    owner_path.write_text(json.dumps(raw), encoding="utf-8")

    retry_summary = control.automatic_repair_orchestration()
    retry_by_source = {
        row["source_job_id"]: row for row in retry_summary["incidents"]
    }
    assert retry_summary["declared_incidents"] == 1
    assert retry_by_source["LOCK-BUSY-OWNER"]["publication_required"] is True
    assert (
        retry_by_source["LOCK-BUSY-FRESH-NEWER"]["repair_reason"]
        == "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
    )

    # Exhaust MAX_REPAIR_ATTEMPTS = 2 and expire cooldown -> owner stays
    # exhausted and fresh duplicate still cannot bypass MAX_REPAIR_ATTEMPTS.
    maintenance.register_published_repair_attempt(
        owner_id,
        "WORKER-REPAIR-OWNER-A2",
        {"status": "PUBLISHED", "commit_sha": "2" * 40},
        now_epoch=time.time(),
    )
    maintenance.register_repair_result(
        owner_id,
        {
            "job_id": "WORKER-REPAIR-OWNER-A2",
            "status": "GIT_TESTS_FAILED",
            "production_touched": False,
        },
        now_epoch=time.time() - 400,
    )
    exhausted_summary = control.automatic_repair_orchestration()
    exhausted_by_source = {
        row["source_job_id"]: row for row in exhausted_summary["incidents"]
    }
    assert exhausted_summary["selected_incidents"] == 1
    assert exhausted_summary["declared_incidents"] == 0
    assert (
        exhausted_by_source["LOCK-BUSY-OWNER"]["repair_reason"]
        == "REPAIR_ATTEMPTS_EXHAUSTED"
    )
    assert (
        exhausted_by_source["LOCK-BUSY-FRESH-NEWER"]["state"]
        == "DUPLICATE_ROOT_CAUSE_SUPPRESSED"
    )
    assert (
        exhausted_by_source["LOCK-BUSY-FRESH-NEWER"]["selected_incident_id"]
        == owner_id
    )


def test_distinct_root_causes_remain_independent_in_selection(
    tmp_path,
    monkeypatch,
):
    import json

    control, _ = _duplicate_cause_env(
        tmp_path,
        monkeypatch,
        (("LOCK-BUSY-CAUSE-A", "2026-10-21T10:00:00Z"),),
    )
    results = tmp_path / ".git" / "universal-worker-queue" / "results"
    (results / "TEST-FAIL-CAUSE-B.json").write_text(
        json.dumps(
            {
                "job_id": "TEST-FAIL-CAUSE-B",
                "status": "GIT_TESTS_FAILED",
                "certification": "NOT_CERTIFIED",
                "completed_at_utc": "2026-10-21T10:05:00Z",
                "production_touched": False,
                "files_changed": [
                    "backend/tests/test_worker_control_plane_contract.py"
                ],
                "blockers": ["pytest_failed:contract"],
            }
        ),
        encoding="utf-8",
    )

    summary = control.automatic_repair_orchestration()
    assert summary["selected_incidents"] == 2
    assert summary["declared_incidents"] == 2
    assert all(
        row["publication_required"] is True
        for row in summary["incidents"]
    )
