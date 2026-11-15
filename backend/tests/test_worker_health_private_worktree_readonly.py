"""Fail-closed contract for shared worktree health without publishing filenames."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
PUBLISHER = ROOT / "tools" / "mirror_sync" / "runtime_health_publisher.py"


def publisher(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("runtime_health_private_test", PUBLISHER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    repo = tmp_path / "app"
    repo.mkdir()
    state = repo / ".git" / "universal-worker-queue"
    state.mkdir(parents=True)
    directory = state / "private_health"
    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "STATE", state)
    monkeypatch.setattr(module, "PRIVATE_WORKTREE_DIR", directory)
    monkeypatch.setattr(module, "PRIVATE_WORKTREE_FILE", directory / "shared_worktree.json")
    return module


def fake_git_status(monkeypatch, module, output: bytes, returncode: int = 0):
    calls = []
    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(stdout=output, returncode=returncode)
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    return calls


def test_dirty_status_stays_private_and_counts_are_public(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    calls = fake_git_status(
        monkeypatch,
        module,
        b"M  src/staged.py\0 M private/unstaged.env\0?? secret/key.txt\0",
    )
    monkeypatch.setattr(module, "_expected_platform_managed_drift", lambda: False)

    public = module._worktree_public_status()
    private = json.loads(module.PRIVATE_WORKTREE_FILE.read_text(encoding="utf-8"))

    assert public == {
        "state": "DIRTY",
        "staged_count": 1,
        "unstaged_count": 1,
        "untracked_count": 1,
        "platform_managed_exception_applied": False,
        "private_evidence": "LOCAL_RESTRICTED",
    }
    assert private["staged"] == ["src/staged.py"]
    assert private["unstaged"] == ["private/unstaged.env"]
    assert private["untracked"] == ["secret/key.txt"]
    assert "secret/key.txt" not in json.dumps(public)
    assert not any(path in json.dumps(public) for path in private["staged"] + private["unstaged"])
    assert module.PRIVATE_WORKTREE_DIR.stat().st_mode & 0o777 == 0o700
    assert module.PRIVATE_WORKTREE_FILE.stat().st_mode & 0o777 == 0o600
    assert calls[0][0] == [
        "git", "--no-optional-locks", "status",
        "--porcelain=v1", "-z", "--untracked-files=all",
    ]
    assert calls[0][1]["cwd"] == str(module.ROOT)
    assert calls[0][1]["env"]["GIT_OPTIONAL_LOCKS"] == "0"


def test_clean_status_is_clean_and_writes_no_paths(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b"")
    public = module._worktree_public_status()
    assert public["state"] == "CLEAN"
    assert public["staged_count"] == public["unstaged_count"] == public["untracked_count"] == 0
    assert json.loads(module.PRIVATE_WORKTREE_FILE.read_text())["staged"] == []


def test_exact_expected_platform_drift_is_ignored(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b" M .emergent/system_deps.txt\0")
    monkeypatch.setattr(module, "_expected_platform_managed_drift", lambda: True)
    public = module._worktree_public_status()
    assert public["state"] == "CLEAN"
    assert public["platform_managed_exception_applied"] is True
    assert json.loads(module.PRIVATE_WORKTREE_FILE.read_text())["unstaged"] == []


@pytest.mark.parametrize("status_line", [
    b"M  .emergent/system_deps.txt\0",
    b"MM .emergent/system_deps.txt\0",
    b"?? .emergent/system_deps.txt\0",
])
def test_platform_exception_never_hides_staged_or_untracked(monkeypatch, tmp_path, status_line):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, status_line)
    monkeypatch.setattr(module, "_expected_platform_managed_drift", lambda: True)
    assert module._worktree_public_status()["state"] == "DIRTY"


def test_platform_exception_requires_canonical_validation(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b" M .emergent/system_deps.txt\0")
    monkeypatch.setattr(module, "_expected_platform_managed_drift", lambda: False)
    assert module._worktree_public_status()["state"] == "DIRTY"


@pytest.mark.parametrize("output,returncode", [
    (b"?? path-without-terminator", 0),
    (b"nonsense\0", 0),
    (b"", 128),
    (b"R  new-name.txt\0", 0),
])
def test_status_failures_do_not_falsely_report_clean(
    monkeypatch, tmp_path, output, returncode
):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, output, returncode)
    assert module._worktree_public_status()["state"] == "UNAVAILABLE"
    assert not module.PRIVATE_WORKTREE_FILE.exists()


def test_rename_paths_remain_private(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b"R  new-name.txt\0old-name.txt\0")
    public = module._worktree_public_status()
    assert public["state"] == "DIRTY"
    assert public["staged_count"] == 1
    private = json.loads(module.PRIVATE_WORKTREE_FILE.read_text())
    assert private["staged"] == ["new-name.txt"]
    assert private["renamed_from"] == ["old-name.txt"]
    assert "old-name" not in json.dumps(public)


def test_private_directory_symlink_is_rejected(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b"?? file.txt\0")
    outside = tmp_path / "outside"
    outside.mkdir()
    module.PRIVATE_WORKTREE_DIR.symlink_to(outside, target_is_directory=True)
    public = module._worktree_public_status()
    assert public["state"] == "UNAVAILABLE"
    assert not (outside / "shared_worktree.json").exists()


def test_private_evidence_symlink_is_rejected(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b"?? file.txt\0")
    module.PRIVATE_WORKTREE_DIR.mkdir(mode=0o700)
    outside = tmp_path / "outside.json"
    outside.write_text("preserve")
    module.PRIVATE_WORKTREE_FILE.symlink_to(outside)
    public = module._worktree_public_status()
    assert public["state"] == "UNAVAILABLE"
    assert outside.read_text() == "preserve"


def test_public_status_never_echoes_private_exception(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    def fail():
        raise RuntimeError("secret=/root/credentials.ini")
    monkeypatch.setattr(module, "_read_only_worktree_snapshot", fail)
    public = module._worktree_public_status()
    assert public == {"state": "UNAVAILABLE", "private_evidence": "UNAVAILABLE"}
    assert "/root/credentials.ini" not in json.dumps(public)


def test_health_payload_uses_only_aggregate_snapshot():
    text = PUBLISHER.read_text(encoding="utf-8")
    assert '"shared_worktree": _worktree_public_status()' in text
    assert '"private_health"' in text
    assert '"worker/health"' in text
    assert '"--no-optional-locks"' in text
    assert 'git("reset"' not in text
    assert 'git("clean"' not in text
    assert '"private_evidence": "LOCAL_RESTRICTED"' in text


def test_private_snapshot_reader_requires_fresh_owner_only_evidence(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b"?? src/local-change.txt\0")
    assert module._worktree_public_status()["state"] == "DIRTY"
    snapshot = module.read_private_worktree_snapshot()
    assert snapshot["untracked"] == ["src/local-change.txt"]


def test_private_snapshot_reader_rejects_stale_evidence(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b"?? src/local-change.txt\0")
    module._worktree_public_status()
    monkeypatch.setattr(module.time, "time", lambda: module.PRIVATE_WORKTREE_FILE.stat().st_mtime + 1000)
    with pytest.raises(RuntimeError, match="STALE_OR_INVALID"):
        module.read_private_worktree_snapshot()


def test_private_snapshot_reader_rejects_broad_file_permissions(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b"?? src/local-change.txt\0")
    module._worktree_public_status()
    module.PRIVATE_WORKTREE_FILE.chmod(0o644)
    with pytest.raises(RuntimeError, match="PERMISSIONS"):
        module.read_private_worktree_snapshot()


def test_private_snapshot_reader_rejects_git_parent_symlink(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    # Make the real Git directory elsewhere, replacing .git with a symlink.
    import shutil
    git_dir = module.ROOT / ".git"
    relocated = tmp_path / "git-storage"
    shutil.move(str(git_dir), str(relocated))
    git_dir.symlink_to(relocated, target_is_directory=True)
    fake_git_status(monkeypatch, module, b"?? src/local-change.txt\0")
    assert module._worktree_public_status()["state"] == "UNAVAILABLE"
    with pytest.raises(RuntimeError, match="PARENT_UNSAFE"):
        module.read_private_worktree_snapshot()


def test_private_snapshot_reader_rejects_file_symlink(monkeypatch, tmp_path):
    module = publisher(monkeypatch, tmp_path)
    fake_git_status(monkeypatch, module, b"?? src/local-change.txt\0")
    module._worktree_public_status()
    target = tmp_path / "sensitive.json"
    target.write_text('{"secret":"not-to-be-read"}')
    module.PRIVATE_WORKTREE_FILE.unlink()
    module.PRIVATE_WORKTREE_FILE.symlink_to(target)
    with pytest.raises(RuntimeError, match="UNAVAILABLE"):
        module.read_private_worktree_snapshot()


def test_worker_health_private_reader_is_not_published_on_worker_health():
    text = PUBLISHER.read_text(encoding="utf-8")
    assert '"shared_worktree": _worktree_public_status()' in text
    assert "read_private_worktree_snapshot()" not in text.split("def runtime_summary()")[1]
