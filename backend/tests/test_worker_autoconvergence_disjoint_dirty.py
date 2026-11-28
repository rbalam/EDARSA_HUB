"""Regression tests for disjoint-dirty safe runtime autoconvergence in worker_control_plane."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (REPO_ROOT, REPO_ROOT / "tools" / "mirror_sync"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tools.mirror_sync import worker_control_plane as wcp


def _init_repo_with_remote(tmp_path: Path) -> tuple[Path, Path, str]:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    repo = tmp_path / "local"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-b", "Edarsahub_Desarrollo"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@edarsa.com.mx"], check=True)
    (repo / "backend_file.py").write_text("v = 1\n", encoding="utf-8")
    (repo / "other_agent.py").write_text("local = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(remote)], check=True)
    subprocess.run(["git", "-C", str(repo), "push", "-u", "origin", "Edarsahub_Desarrollo"], check=True, capture_output=True)
    sha1 = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return repo, remote, sha1


def _push_upstream_commit(tmp_path: Path, remote: Path, filename: str, content: str) -> str:
    clone = tmp_path / f"upstream_{filename.replace('/', '_')}"
    subprocess.run(["git", "clone", "-b", "Edarsahub_Desarrollo", str(remote), str(clone)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(clone), "config", "user.name", "Worker"], check=True)
    subprocess.run(["git", "-C", str(clone), "config", "user.email", "worker@edarsahub.local"], check=True)
    target = clone / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(clone), "add", filename], check=True)
    subprocess.run(["git", "-C", str(clone), "commit", "-m", f"update {filename}"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(clone), "push", "origin", "Edarsahub_Desarrollo"], check=True, capture_output=True)
    return subprocess.check_output(["git", "-C", str(clone), "rev-parse", "HEAD"], text=True).strip()


def test_01_porcelain_parser_and_prefix_overlap_helpers():
    parsed = wcp._parse_porcelain_dirty_paths(
        "M  tools/mirror_sync/worker_control_plane.py\n"
        " M backend_file.py\n"
        "M stripped_unstaged.py\n"
        "R  old/a.py -> backend/modules/worker_ingress/service.py\n"
    )
    assert parsed == {
        "tools/mirror_sync/worker_control_plane.py",
        "backend_file.py",
        "stripped_unstaged.py",
        "old/a.py",
        "backend/modules/worker_ingress/service.py",
    }
    assert wcp._dirty_paths_overlap_prefixes({"tools/mirror_sync/worker_control_plane.py"}, ("tools/mirror_sync",)) is True
    assert wcp._dirty_paths_overlap_prefixes({"tools/mirror_sync/worker_control_plane.py"}, wcp.MCP_BACKEND_IDENTITY_PATHS) is False
    assert wcp._dirty_paths_overlap_prefixes({"backend/modules/worker_ingress/service.py"}, wcp.MCP_BACKEND_IDENTITY_PATHS) is True


def test_02_preserve_and_fast_forward_advances_disjoint_dirty_and_preserves_staged_change(tmp_path, monkeypatch):
    repo, remote, sha1 = _init_repo_with_remote(tmp_path)
    sha2 = _push_upstream_commit(tmp_path, remote, "backend_file.py", "v = 2\n")

    # Stage a disjoint local change belonging to another agent
    (repo / "other_agent.py").write_text("local = 999\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "other_agent.py"], check=True)

    monkeypatch.setattr(wcp, "ROOT", repo)
    monkeypatch.setattr(wcp, "STATE", repo / ".git" / "universal-worker-queue")
    monkeypatch.setattr(wcp, "AUDIT", repo / ".git" / "universal-worker-queue" / "audit.jsonl")

    res = wcp.preserve_and_fast_forward()
    assert res["ff"] == "APPLIED"
    assert res["from"] == sha1
    assert res["to"] == sha2
    assert res["disjoint_dirty_preserved"] is True
    assert res["dirty_paths_preserved"] == ["other_agent.py"]

    # Local HEAD aligned AND staged disjoint change preserved untouched
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() == sha2
    assert (repo / "backend_file.py").read_text(encoding="utf-8") == "v = 2\n"
    assert (repo / "other_agent.py").read_text(encoding="utf-8") == "local = 999\n"
    staged_diff = subprocess.check_output(["git", "-C", str(repo), "diff", "--cached", "--name-only"], text=True).strip()
    assert staged_diff == "other_agent.py"


def test_03_preserve_and_fast_forward_fails_closed_on_overlapping_dirty_path(tmp_path, monkeypatch):
    repo, remote, sha1 = _init_repo_with_remote(tmp_path)
    _push_upstream_commit(tmp_path, remote, "backend_file.py", "v = 2\n")

    # Local unstaged dirty change overlaps backend_file.py -> MUST fail closed
    (repo / "backend_file.py").write_text("v = 999\n", encoding="utf-8")

    monkeypatch.setattr(wcp, "ROOT", repo)
    monkeypatch.setattr(wcp, "STATE", repo / ".git" / "universal-worker-queue")
    monkeypatch.setattr(wcp, "AUDIT", repo / ".git" / "universal-worker-queue" / "audit.jsonl")

    res = wcp.preserve_and_fast_forward()
    assert res["ff"] == "DEFER_LOCAL_DIRTY"
    assert res["scope_conflicts"] == ["backend_file.py"]
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() == sha1
    assert (repo / "backend_file.py").read_text(encoding="utf-8") == "v = 999\n"


def test_04_converge_runtime_permanently_disjoint_vs_overlapping_dirty(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    monkeypatch.setattr(wcp, "RUNTIME", runtime_dir)
    monkeypatch.setattr(wcp, "STATE", state_dir)
    monkeypatch.setattr(wcp, "AUDIT", state_dir / "audit.jsonl")
    monkeypatch.setattr(wcp, "AUTOCONVERGENCE_STATE", runtime_dir / "autoconvergence_state.json")
    monkeypatch.setattr(wcp, "ACTIVE_MCP_BACKEND_TREE", runtime_dir / "active_mcp_backend_tree_sha")

    head_sha = "a" * 40
    worker_tree = "b" * 40
    (runtime_dir / "active_worker_code_tree_sha").write_text("c" * 40 + "\n", encoding="utf-8")
    (runtime_dir / "active_mcp_backend_tree_sha").write_text("old_mcp_tree\n", encoding="utf-8")

    def fake_run(args, timeout=30, check=False):
        class P:
            returncode = 0
            stdout = ""
        p = P()
        if args[:3] == ["git", "branch", "--show-current"]:
            p.stdout = "Edarsahub_Desarrollo\n"
        elif args[:2] == ["git", "rev-parse"] and args[2] == "HEAD:tools/mirror_sync":
            p.stdout = worker_tree + "\n"
        elif args[:2] == ["git", "rev-parse"]:
            p.stdout = head_sha + "\n"
        return p

    monkeypatch.setattr(wcp, "run", fake_run)
    monkeypatch.setattr(wcp, "_compute_mcp_backend_tree_identity", lambda: "new_mcp_tree")
    monkeypatch.setattr(wcp, "_probe_local_backend_health", lambda: True)
    monkeypatch.setattr(wcp, "_supervisor_service_running", lambda _svc: True)
    restarted = []
    monkeypatch.setattr(wcp, "_restart_service", lambda svc, reason: (restarted.append((svc, reason)), True)[1])

    # Case A: dirty tools/mirror_sync/worker_control_plane.py -> Worker stays DEFERRED (overlap),
    # while Backend+MCP converges cleanly (disjoint!)
    monkeypatch.setattr(wcp, "effective_git_status", lambda: "M  tools/mirror_sync/worker_control_plane.py")
    out_a = wcp.converge_runtime_permanently(ff={"ff": "APPLIED"}, runtime={})
    assert out_a["worker_action"] == "DEFERRED_NON_CANONICAL_CHECKOUT"
    assert out_a["mcp_backend_action"] == "RECOVERED_AUTO"
    assert out_a["mcp_backend_tree_aligned"] is True
    assert out_a["production_touched"] is False
    assert [s for s, _ in restarted] == [wcp.BACKEND_SERVICE, wcp.MCP_SERVICE]

    # Case B: dirty backend/modules/worker_ingress/service.py -> Backend+MCP fails closed (overlap!)
    (runtime_dir / "active_mcp_backend_tree_sha").write_text("old_mcp_tree\n", encoding="utf-8")
    restarted.clear()
    monkeypatch.setattr(wcp, "effective_git_status", lambda: " M backend/modules/worker_ingress/service.py")
    out_b = wcp.converge_runtime_permanently(ff={"ff": "APPLIED"}, runtime={})
    assert out_b["mcp_backend_action"] == "DEFERRED_NON_CANONICAL_CHECKOUT"
    assert out_b["mcp_backend_tree_aligned"] is False
    assert restarted == []
    assert out_b["production_touched"] is False
