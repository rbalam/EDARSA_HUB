from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUARD_PATH = ROOT / "tools" / "mirror_sync" / "git_divergence_guard.py"


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return proc.stdout.strip()


def _load_guard():
    spec = importlib.util.spec_from_file_location(
        "git_divergence_guard_managed_drift_test",
        GUARD_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / ".emergent").mkdir()
    (repo / ".emergent" / "system_deps.txt").write_text(
        "git\n",
        encoding="utf-8",
    )
    (repo / "keep.txt").write_text("ok\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    return repo


def test_exact_empty_platform_managed_drift_is_ignored(tmp_path):
    guard = _load_guard()
    repo = _repo(tmp_path)

    (repo / ".emergent" / "system_deps.txt").write_text(
        "",
        encoding="utf-8",
    )

    state = guard._status_counts(repo)

    assert state["worktree_dirty"] is False
    assert (
        state["platform_managed_system_deps_drift_ignored"]
        is True
    )


def test_different_system_deps_content_is_not_ignored(tmp_path):
    guard = _load_guard()
    repo = _repo(tmp_path)

    (repo / ".emergent" / "system_deps.txt").write_text(
        "curl\n",
        encoding="utf-8",
    )

    state = guard._status_counts(repo)

    assert state["worktree_dirty"] is True
    assert (
        state["platform_managed_system_deps_drift_ignored"]
        is False
    )


def test_other_dirty_file_still_blocks_with_managed_drift(tmp_path):
    guard = _load_guard()
    repo = _repo(tmp_path)

    (repo / ".emergent" / "system_deps.txt").write_text(
        "",
        encoding="utf-8",
    )
    (repo / "keep.txt").write_text(
        "changed\n",
        encoding="utf-8",
    )

    state = guard._status_counts(repo)

    assert state["worktree_dirty"] is True
    assert state["unstaged_count"] == 1
    assert (
        state["platform_managed_system_deps_drift_ignored"]
        is True
    )


def test_staged_system_deps_change_is_never_ignored(tmp_path):
    guard = _load_guard()
    repo = _repo(tmp_path)

    (repo / ".emergent" / "system_deps.txt").write_text(
        "",
        encoding="utf-8",
    )
    _git(repo, "add", ".emergent/system_deps.txt")

    state = guard._status_counts(repo)

    assert state["worktree_dirty"] is True
    assert state["staged_count"] == 1
    assert (
        state["platform_managed_system_deps_drift_ignored"]
        is False
    )


def test_preview_entrypoints_use_managed_drift_contract():
    shared = (
        ROOT / "tools" / "mirror_sync" / "shared_app_safety_guard.sh"
    ).read_text(encoding="utf-8")
    mirror_start = (
        ROOT / "tools" / "mirror_sync" / "mirror_sync_start.sh"
    ).read_text(encoding="utf-8")
    recovery = (
        ROOT / "tools" / "bootstrap" / "recover_preview_runtime.sh"
    ).read_text(encoding="utf-8")
    wake = (
        ROOT / "backend" / "modules" / "worker_runtime_wake" / "routes.py"
    ).read_text(encoding="utf-8")
    watchdog = (
        ROOT / "tools" / "bootstrap" / "edarsahub_bootstrap_watchdog.py"
    ).read_text(encoding="utf-8")
    control = (
        ROOT / "tools" / "mirror_sync" / "worker_control_plane.py"
    ).read_text(encoding="utf-8")
    publisher = (
        ROOT / "tools" / "mirror_sync" / "publish_local_snapshot.sh"
    ).read_text(encoding="utf-8")

    assert "edarsahub_expected_platform_system_deps_drift" in shared
    assert "edarsahub_effective_status" in mirror_start
    assert "edarsahub_effective_status" in recovery
    assert "_expected_platform_system_deps_drift" in wake
    assert "expected_platform_system_deps_drift" in watchdog
    assert "expected_platform_system_deps_drift" in control
    assert "edarsahub_expected_platform_system_deps_drift" in publisher
    assert "ABORT=UNEXPECTED_PLATFORM_MANAGED_SYSTEM_DEPS_DRIFT" in publisher
    assert "':(exclude).emergent/system_deps.txt'" in publisher


def _load_dispatcher(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tools" / "mirror_sync"))
    spec = importlib.util.spec_from_file_location(
        "universal_job_dispatcher_managed_drift_test",
        ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_dispatcher_readonly_pytest_guard_reuses_platform_managed_drift(
    tmp_path,
    monkeypatch,
):
    dispatcher = _load_dispatcher(monkeypatch)
    repo = _repo(tmp_path)

    # 1. Exact empty platform-managed .emergent/system_deps.txt drift is ignored
    (repo / ".emergent" / "system_deps.txt").write_text("", encoding="utf-8")
    raw_only_managed = _git(repo, "status", "--porcelain=v1", "--untracked-files=no")
    raw_only_managed = " " + raw_only_managed.lstrip()
    assert raw_only_managed == " M .emergent/system_deps.txt"
    assert dispatcher._effective_readonly_tracked_status(repo, raw_only_managed) == ""

    # 2. Any other dirty tracked file still fails closed
    (repo / "keep.txt").write_text("changed\n", encoding="utf-8")
    proc_both = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=no"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    eff_both = dispatcher._effective_readonly_tracked_status(repo, proc_both.stdout)
    assert "keep.txt" in eff_both
    assert ".emergent/system_deps.txt" not in eff_both

    # 3. Non-empty modification to .emergent/system_deps.txt fails closed
    (repo / "keep.txt").write_text("ok\n", encoding="utf-8")
    (repo / ".emergent" / "system_deps.txt").write_text("curl\n", encoding="utf-8")
    proc_nonempty = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=no"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    eff_nonempty = dispatcher._effective_readonly_tracked_status(repo, proc_nonempty.stdout)
    assert ".emergent/system_deps.txt" in eff_nonempty

    # 4. Staged .emergent/system_deps.txt fails closed
    (repo / ".emergent" / "system_deps.txt").write_text("", encoding="utf-8")
    _git(repo, "add", ".emergent/system_deps.txt")
    proc_staged = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=no"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    eff_staged = dispatcher._effective_readonly_tracked_status(repo, proc_staged.stdout)
    assert ".emergent/system_deps.txt" in eff_staged

    # 5. Contract check on universal_job_dispatcher.py source
    src = (
        ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py"
    ).read_text(encoding="utf-8")
    assert "_expected_platform_system_deps_drift" in src
    assert "_effective_readonly_tracked_status" in src
    assert "READONLY_PYTEST_REVISION_MISMATCH:" in src
    assert "if tracked_after != tracked_before:" in src
