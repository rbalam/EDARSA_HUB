from pathlib import Path
import importlib.util
import os
import time

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "tools/mirror_sync/git_divergence_guard.py"

def _load_guard():
    spec = importlib.util.spec_from_file_location("git_guard_indexlock_test", GUARD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def test_orphan_index_lock_is_quarantined(tmp_path):
    guard = _load_guard()
    repo = tmp_path / "repo"
    repo.mkdir()
    git_dir = repo / ".git"
    git_dir.mkdir()
    lock = git_dir / "index.lock"
    lock.write_text("", encoding="utf-8")
    old = time.time() - 120
    os.utime(lock, (old, old))
    guard._git_dir = lambda _repo: git_dir
    guard._status_counts = lambda _repo: {"worktree_dirty": False, "staged_count": 0, "unstaged_count": 0, "untracked_count": 0}
    guard._index_lock_owner_pids = lambda _path: []
    result = guard.recover_orphan_index_lock(repo)
    assert result["state"] == "ORPHAN_INDEX_LOCK_QUARANTINED"
    assert not lock.exists()
    assert Path(result["preserved_at"]).is_file()

def test_active_index_lock_fails_closed(tmp_path):
    guard = _load_guard()
    repo = tmp_path / "repo"
    repo.mkdir()
    git_dir = repo / ".git"
    git_dir.mkdir()
    lock = git_dir / "index.lock"
    lock.write_text("", encoding="utf-8")
    old = time.time() - 120
    os.utime(lock, (old, old))
    guard._git_dir = lambda _repo: git_dir
    guard._index_lock_owner_pids = lambda _path: [12345]
    try:
        guard.recover_orphan_index_lock(repo)
    except guard.GitGuardError as exc:
        assert exc.code == "GIT_INDEX_LOCK_BUSY"
        assert exc.evidence["owner_pids"] == [12345]
    else:
        raise AssertionError("active index lock must fail closed")

def test_fresh_index_lock_fails_closed(tmp_path):
    guard = _load_guard()
    repo = tmp_path / "repo"
    repo.mkdir()
    git_dir = repo / ".git"
    git_dir.mkdir()
    lock = git_dir / "index.lock"
    lock.write_text("", encoding="utf-8")
    guard._git_dir = lambda _repo: git_dir
    guard._index_lock_owner_pids = lambda _path: []
    try:
        guard.recover_orphan_index_lock(repo)
    except guard.GitGuardError as exc:
        assert exc.code == "GIT_INDEX_LOCK_BUSY"
        assert exc.evidence["reason"] == "INDEX_LOCK_ACTIVE_OR_FRESH"
    else:
        raise AssertionError("fresh index lock must fail closed")
