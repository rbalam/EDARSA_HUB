from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "tools" / "mirror_sync" / "universal_job_worker.sh"
RECONCILER = ROOT / "tools" / "mirror_sync" / "worker_runtime_reconciler.py"
DISPATCHER = ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py"
PUBLISHER = ROOT / "tools" / "mirror_sync" / "universal_job_result_publisher.py"
HEALTH = ROOT / "tools" / "mirror_sync" / "runtime_health_publisher.py"

def text(path): return path.read_text(encoding="utf-8")

def test_property_1_intake_is_independent_and_fast():
    source = text(WORKER); assert 'INTAKE_SECONDS="${UNIVERSAL_WORKER_INTAKE_SECONDS:-10}"' in source; assert "intake_loop &" in source; assert "dispatch_loop &" in source; assert "result_loop &" in source; assert "receive_once" in source

def test_property_2_self_heal_is_safe_not_age_only():
    source = text(RECONCILER)
    for marker in ("recover_orphan_processing","reconcile_claims","claim_terminal","process_references","worktree_clean","CLAIM_NOT_STALE","WORK_NOT_TERMINAL_OR_INTEGRATED","LIVE_PROCESS_REFERENCES_WORKTREE","WORKTREE_NOT_CLEAN"): assert marker in source
    assert "reconcile_loop &" in text(WORKER)

def test_property_3_terminal_result_pipeline_is_mandatory():
    dispatcher = text(DISPATCHER); publisher = text(PUBLISHER); assert '"status": "BLOCKED"' in dispatcher; assert "RESULTS" in dispatcher and "write_json" in dispatcher; assert "UNIVERSAL_RESULTS_PUBLISH_ERROR_COUNT" in publisher; assert "return 1 if errors else 0" in publisher

def test_remote_health_exposes_runtime_and_blocking_state():
    health = text(HEALTH)
    for marker in ("last_cycle_utc","last_receive_utc",'"BLOCKED"','"REJECTED"','"RESULT_READY"'): assert marker in health


def test_property_3b_terminal_success_moves_processing_to_done():
    dispatcher = text(DISPATCHER)

    assert 'DONE = STATE / "done"' in dispatcher
    assert 'RESULTS = STATE / "results"' in dispatcher
    assert 'result["completed_at_utc"] = now()' in dispatcher
    assert 'write_json(RESULTS / path.name, result)' in dispatcher
    assert (
        'target = DONE / path.name if result["status"] in '
        '{"INTEGRATED", "READ_ONLY_COMPLETE", "OPERATIONAL_COMPLETE"} '
        'else REJECTED / path.name'
    ) in dispatcher
    assert 'os.replace(processing, target)' in dispatcher


def test_submit_convergence_equal_refs_passes():
    from tools.mirror_sync.git_divergence_guard import (
        classify_submit_convergence,
    )

    result = classify_submit_convergence(
        local="A",
        development="A",
        mirror="A",
        local_merge_base="A",
        mirror_merge_base="A",
        worktree_dirty=False,
    )

    assert result["status"] == "CONVERGED_PASS"
    assert result["converged"] is True
    assert result["safe"] is True


def test_submit_convergence_mirror_ancestor_is_safe_fast_forward():
    from tools.mirror_sync.git_divergence_guard import (
        classify_submit_convergence,
    )

    result = classify_submit_convergence(
        local="A",
        development="D",
        mirror="M",
        local_merge_base="A",
        mirror_merge_base="M",
        worktree_dirty=False,
    )

    assert result["status"] == "SAFE_FAST_FORWARD"
    assert result["mirror_fast_forward_safe"] is True


def test_submit_convergence_mirror_ahead_blocks():
    from tools.mirror_sync.git_divergence_guard import (
        classify_submit_convergence,
    )

    result = classify_submit_convergence(
        local="D",
        development="D",
        mirror="M",
        local_merge_base="D",
        mirror_merge_base="D",
        worktree_dirty=False,
    )

    assert result["status"] == "BLOCKED_MIRROR_AHEAD"


def test_submit_convergence_divergence_blocks():
    from tools.mirror_sync.git_divergence_guard import (
        classify_submit_convergence,
    )

    result = classify_submit_convergence(
        local="L",
        development="D",
        mirror="M",
        local_merge_base="X",
        mirror_merge_base="X",
        worktree_dirty=False,
    )

    assert result["status"] == "BLOCKED_DIVERGENCE"


def test_submit_convergence_dirty_worktree_blocks():
    from tools.mirror_sync.git_divergence_guard import (
        classify_submit_convergence,
    )

    result = classify_submit_convergence(
        local="A",
        development="D",
        mirror="M",
        local_merge_base="A",
        mirror_merge_base="M",
        worktree_dirty=True,
    )

    assert result["status"] == "BLOCKED_LOCAL_DIRTY"


def test_submit_publisher_uses_canonical_convergence_preflight():
    guard = text(
        ROOT
        / "tools"
        / "mirror_sync"
        / "git_divergence_guard.py"
    )
    publisher = text(
        ROOT
        / "tools"
        / "mirror_sync"
        / "gate_chain_publisher.py"
    )

    assert "def ensure_submit_convergence(" in guard
    assert "ensure_submit_convergence(" in publisher
    assert "preflight_convergence" in publisher
    assert "BLOCKED_MIRROR_AHEAD" in guard
    assert "BLOCKED_PUSH_REJECTED" in guard


def test_submit_convergence_never_uses_destructive_git_commands():
    guard = text(
        ROOT
        / "tools"
        / "mirror_sync"
        / "git_divergence_guard.py"
    ).lower()

    for forbidden in (
        "git reset",
        "git clean",
        "git stash",
        "--force",
        "--force-with-lease",
    ):
        assert forbidden not in guard


def test_convergence_doctor_is_canonical_guard_subcommand():
    guard = text(
        ROOT
        / "tools"
        / "mirror_sync"
        / "git_divergence_guard.py"
    )

    assert 'sub.add_parser("doctor")' in guard
    assert '--auto-fix' in guard
    assert '--json' in guard
