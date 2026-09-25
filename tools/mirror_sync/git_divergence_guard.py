#!/usr/bin/env python3
"""Canonical Git divergence/writer guard for EDARSAHUB Development."""
from __future__ import annotations
import argparse, json, os, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEV_BRANCH = "Edarsahub_Desarrollo"
REMOTE = "origin"
LOCK_NAME = "git-writer.lock.d"
DEFAULT_LOCK_TTL_SECONDS = 7200
AUTHORIZED_LOCAL_AHEAD_EMAILS = {
    "worker-publisher@edarsahub.local",
    "worker@edarsahub.local",
}
MAX_AUTHORIZED_LOCAL_AHEAD_COMMITS = 20

class GitGuardError(RuntimeError):
    def __init__(self, code: str, evidence: dict[str, Any] | None = None):
        super().__init__(code); self.code = code; self.evidence = evidence or {}

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _run(repo: Path, *args: str, check: bool = True, env: dict[str, str] | None = None):
    r = subprocess.run(["git", *args], cwd=str(repo), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, check=False)
    if check and r.returncode != 0:
        raise GitGuardError("GIT_COMMAND_FAILED", {"args": list(args), "returncode": r.returncode, "output": (r.stdout or "")[-2000:]})
    return r

def _git_dir(repo: Path) -> Path:
    raw = _run(repo, "rev-parse", "--git-dir").stdout.strip(); p = Path(raw)
    return (repo / p).resolve() if not p.is_absolute() else p.resolve()

def _status_counts(repo: Path) -> dict[str, Any]:
    staged = unstaged = untracked = 0
    for line in _run(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout.splitlines():
        if line.startswith("??"): untracked += 1; continue
        if len(line) >= 2:
            if line[0] != " ": staged += 1
            if line[1] != " ": unstaged += 1
    return {"worktree_dirty": bool(staged or unstaged or untracked), "staged_count": staged, "unstaged_count": unstaged, "untracked_count": untracked}

def inspect_repository(repo: Path, *, fetch: bool = True) -> dict[str, Any]:
    repo = repo.resolve()
    if fetch: _run(repo, "fetch", REMOTE, DEV_BRANCH)
    branch = _run(repo, "branch", "--show-current").stdout.strip(); local = _run(repo, "rev-parse", "HEAD").stdout.strip(); remote = _run(repo, "rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
    mb = _run(repo, "merge-base", local, remote, check=False); merge_base = mb.stdout.strip() if mb.returncode == 0 else ""
    counts = _run(repo, "rev-list", "--left-right", "--count", f"{local}...{remote}").stdout.split(); ahead, behind = (int(counts[0]), int(counts[1])) if len(counts) == 2 else (0,0)
    dirty = _status_counts(repo)
    if dirty["worktree_dirty"]: classification = "DIRTY_WORKTREE"
    elif ahead == 0 and behind == 0: classification = "SYNC"
    elif ahead > 0 and behind == 0: classification = "LOCAL_AHEAD_ONLY"
    elif ahead == 0 and behind > 0: classification = "REMOTE_AHEAD_ONLY"
    else: classification = "DIVERGED"
    local_only = _run(repo, "log", "--format=%H", "--max-count=20", local, "--not", remote, check=False).stdout.splitlines(); remote_only = _run(repo, "log", "--format=%H", "--max-count=20", remote, "--not", local, check=False).stdout.splitlines()
    return {"current_branch": branch, "local_head": local, "remote_head": remote, "merge_base": merge_base, "ahead_count": ahead, "behind_count": behind, **dirty, "classification": classification, "local_only_commits": local_only, "remote_only_commits": remote_only}

def mutation_policy(state: dict[str, Any], *, allow_local_ahead: bool = False) -> dict[str, Any]:
    if state.get("current_branch") != DEV_BRANCH: return {"allowed": False, "terminal_status": "GIT_DIVERGENCE_BLOCKED", "reason": "WRONG_CANONICAL_BRANCH"}
    if state.get("worktree_dirty"): return {"allowed": False, "terminal_status": "GIT_WORKTREE_NOT_CLEAN", "reason": "GIT_WORKTREE_NOT_CLEAN"}
    c = state.get("classification")
    if c == "SYNC": return {"allowed": True, "terminal_status": "CERTIFIED_GIT_SYNC", "reason": "SYNC"}
    if c == "LOCAL_AHEAD_ONLY":
        if allow_local_ahead: return {"allowed": True, "terminal_status": "LOCAL_AHEAD_ONLY", "reason": "EXPLICIT_LOCAL_OWNER_POLICY"}
        return {"allowed": False, "terminal_status": "GIT_DIVERGENCE_BLOCKED", "reason": "LOCAL_AHEAD_OWNERSHIP_UNPROVEN"}
    if c == "REMOTE_AHEAD_ONLY": return {"allowed": False, "terminal_status": "GIT_DIVERGENCE_BLOCKED", "reason": "NEEDS_FAST_FORWARD_REFRESH"}
    if c == "DIVERGED": return {"allowed": False, "terminal_status": "GIT_DIVERGENCE_BLOCKED", "reason": "GIT_DIVERGENCE_BLOCKED"}
    return {"allowed": False, "terminal_status": "GIT_DIVERGENCE_BLOCKED", "reason": "UNKNOWN_GIT_STATE"}

def requires_writer_lock(mode: str) -> bool:
    return str(mode or "MUTATION") not in {"READ_ONLY","READ_ONLY_SQL","SOFTRESTAURANT_FULL_HISTORY_RESYNC","MPRO_FULL_HISTORY_RESYNC","ISCAM_DETAIL_BACKFILL","ISCAM_PAYMENTS_ONLY_RESYNC","SQL_MIGRATION_DEVELOPMENT","FRONTEND_BUILD_CERTIFICATION"}

def _pid_alive(pid: int) -> bool:
    if pid <= 0: return False
    try: os.kill(pid,0); return True
    except OSError: return False

def _read_json(path: Path) -> dict[str, Any]:
    try:
        d=json.loads(path.read_text(encoding="utf-8")); return d if isinstance(d,dict) else {}
    except Exception: return {}

def acquire_writer_lock(repo: Path, *, job_id: str, owner: str, owner_pid: int | None = None, stale_after_seconds: int = DEFAULT_LOCK_TTL_SECONDS) -> dict[str, Any]:
    lock_dir = _git_dir(repo.resolve()) / "universal-worker-queue" / LOCK_NAME
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    pid = int(owner_pid or os.getpid())
    stale_evidence = None

    if lock_dir.exists():
        previous = _read_json(lock_dir / "owner.json")
        created = float(previous.get("created_epoch") or 0)
        previous_pid = int(previous.get("owner_pid") or 0)
        previous_pid_alive = _pid_alive(previous_pid)
        age = (
            max(0.0, time.time() - created)
            if created
            else float("inf")
        )

        # A process-owned lock cannot remain valid after its owner PID dies.
        # Recover it immediately instead of forcing unrelated Worker jobs to
        # wait for the full TTL. Locks without a trustworthy PID retain the
        # conservative TTL policy.
        dead_process_owner = previous_pid > 0 and not previous_pid_alive
        ttl_expired_unknown_owner = (
            previous_pid <= 0 and age >= stale_after_seconds
        )
        stale = dead_process_owner or ttl_expired_unknown_owner

        if not stale:
            raise GitGuardError(
                "GIT_LOCK_BUSY",
                {
                    "lock_owner": previous,
                    "lock_dir": str(lock_dir),
                    "age_seconds": age,
                    "owner_pid_alive": previous_pid_alive,
                },
            )

        recovery_reason = (
            "OWNER_PID_DEAD"
            if dead_process_owner
            else "TTL_EXPIRED_OWNER_UNKNOWN"
        )
        preserved = lock_dir.with_name(
            "git-writer.lock.stale."
            f"{int(time.time())}."
            f"{previous.get('job_id', 'unknown')}"
        )
        os.replace(lock_dir, preserved)
        stale_evidence = {
            "previous": previous,
            "preserved_at": str(preserved),
            "age_seconds": age,
            "recovery_reason": recovery_reason,
        }

    try:
        lock_dir.mkdir()
    except FileExistsError as exc:
        raise GitGuardError(
            "GIT_LOCK_BUSY",
            {"lock_dir": str(lock_dir)},
        ) from exc

    token = {
        "job_id": job_id,
        "owner": owner,
        "owner_pid": pid,
        "created_at_utc": utc_now(),
        "created_epoch": time.time(),
        "lock_dir": str(lock_dir),
        "stale_lock_recovered": stale_evidence,
    }
    (lock_dir / "owner.json").write_text(
        json.dumps(token, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return token

def release_writer_lock(repo: Path, token: dict[str, Any]) -> None:
    lock_dir=Path(str(token.get("lock_dir") or "")); current=_read_json(lock_dir/"owner.json") if lock_dir.is_dir() else {}
    if not lock_dir.is_dir(): raise GitGuardError("GIT_LOCK_BUSY", {"reason":"LOCK_DIRECTORY_MISSING"})
    if current.get("job_id") != token.get("job_id") or current.get("owner") != token.get("owner"): raise GitGuardError("GIT_LOCK_BUSY", {"reason":"LOCK_OWNERSHIP_MISMATCH","current":current})
    (lock_dir/"owner.json").unlink()
    try: lock_dir.rmdir()
    except OSError as exc: raise GitGuardError("GIT_LOCK_BUSY", {"reason":"LOCK_DIRECTORY_NOT_EMPTY","lock_dir":str(lock_dir)}) from exc

def prove_authorized_local_ahead(repo: Path, state: dict[str, Any]) -> dict[str, Any]:
    if state.get("current_branch") != DEV_BRANCH:
        raise GitGuardError("LOCAL_AHEAD_OWNERSHIP_UNPROVEN", {"reason": "WRONG_CANONICAL_BRANCH"})
    if state.get("worktree_dirty"):
        raise GitGuardError("GIT_WORKTREE_NOT_CLEAN", state)
    if state.get("classification") != "LOCAL_AHEAD_ONLY":
        raise GitGuardError("LOCAL_AHEAD_OWNERSHIP_UNPROVEN", {"reason": "NOT_LOCAL_AHEAD_ONLY", "classification": state.get("classification")})
    if state.get("merge_base") != state.get("remote_head"):
        raise GitGuardError("LOCAL_AHEAD_OWNERSHIP_UNPROVEN", {"reason": "REMOTE_NOT_ANCESTOR", "state": state})
    ahead = int(state.get("ahead_count") or 0)
    commits = list(state.get("local_only_commits") or [])
    if ahead < 1 or ahead > MAX_AUTHORIZED_LOCAL_AHEAD_COMMITS or len(commits) != ahead:
        raise GitGuardError("LOCAL_AHEAD_OWNERSHIP_UNPROVEN", {"reason": "UNSAFE_AHEAD_COUNT", "ahead_count": ahead, "enumerated_commits": len(commits)})
    evidence = []
    for sha in commits:
        parents = _run(repo, "rev-list", "--parents", "-n", "1", sha).stdout.strip().split()
        if len(parents) != 2:
            raise GitGuardError("LOCAL_AHEAD_OWNERSHIP_UNPROVEN", {"reason": "NON_LINEAR_LOCAL_COMMIT", "commit": sha, "parent_count": max(0, len(parents) - 1)})
        meta = _run(repo, "show", "-s", "--format=%H%x00%ae%x00%ce", sha).stdout.rstrip("\n").split("\x00")
        if len(meta) != 3:
            raise GitGuardError("LOCAL_AHEAD_OWNERSHIP_UNPROVEN", {"reason": "COMMIT_IDENTITY_UNREADABLE", "commit": sha})
        _, author_email, committer_email = meta
        author_email = author_email.strip().lower()
        committer_email = committer_email.strip().lower()
        if author_email not in AUTHORIZED_LOCAL_AHEAD_EMAILS or committer_email not in AUTHORIZED_LOCAL_AHEAD_EMAILS:
            raise GitGuardError("LOCAL_AHEAD_OWNERSHIP_UNPROVEN", {
                "reason": "UNAUTHORIZED_COMMIT_IDENTITY",
                "commit": sha,
                "author_email": author_email,
                "committer_email": committer_email,
            })
        evidence.append({"commit": sha, "author_email": author_email, "committer_email": committer_email})
    return {"classification":"LOCAL_AHEAD_ONLY","ownership":"AUTHORIZED_EDARSAHUB_WRITER","ahead_count":ahead,"remote_head":state["remote_head"],"local_head":state["local_head"],"commits":evidence}

def recover_authorized_local_ahead(repo: Path, state: dict[str, Any], *, job_id: str, owner: str) -> dict[str, Any]:
    lock_dir = _git_dir(repo.resolve()) / "universal-worker-queue" / LOCK_NAME
    current_lock = _read_json(lock_dir / "owner.json")
    if current_lock.get("job_id") != job_id or current_lock.get("owner") != owner:
        raise GitGuardError("GIT_LOCK_BUSY", {"reason": "LOCAL_AHEAD_RECOVERY_REQUIRES_OWNED_WRITER_LOCK", "current": current_lock})
    proof = prove_authorized_local_ahead(repo, state)
    local, remote = proof["local_head"], proof["remote_head"]
    recovery_branch = f"recovery/authorized-local-ahead/{local[:12]}"
    remote_recovery = _run(repo, "ls-remote", REMOTE, f"refs/heads/{recovery_branch}", check=False).stdout.strip().split()
    if remote_recovery:
        if remote_recovery[0] != local:
            raise GitGuardError("LOCAL_AHEAD_OWNERSHIP_UNPROVEN", {"reason": "RECOVERY_BRANCH_COLLISION", "branch": recovery_branch, "remote_sha": remote_recovery[0], "local_sha": local})
    else:
        preserved = authorized_push(repo,args=["push", REMOTE, f"{local}:refs/heads/{recovery_branch}"],job_id=job_id,owner=owner)
        if preserved.returncode != 0:
            raise GitGuardError("GIT_PUSH_FAILED", {"reason": "RECOVERY_REF_PUSH_FAILED", "branch": recovery_branch, "output": (preserved.stdout or "")[-2000:]})
    compare_and_swap(repo, remote)
    published = authorized_push(repo,args=["push", REMOTE, f"{local}:refs/heads/{DEV_BRANCH}"],job_id=job_id,owner=owner)
    if published.returncode != 0:
        raise GitGuardError("GIT_PUSH_FAILED", {"reason": "LOCAL_AHEAD_FAST_FORWARD_PUSH_FAILED", "output": (published.stdout or "")[-2000:]})
    post = post_push_verify(repo, local)
    return {"proof": proof, "recovery_branch": recovery_branch, "post_push": post}

def compare_and_swap(repo: Path, remote_at_start: str) -> str:
    _run(repo,"fetch",REMOTE,DEV_BRANCH); now=_run(repo,"rev-parse",f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
    if now != remote_at_start: raise GitGuardError("REMOTE_MOVED_RETRY_REQUIRED", {"remote_at_start":remote_at_start,"remote_now":now})
    return now

def validate_commit_scope(repo: Path, base_sha: str, candidate_sha: str, allowed_paths: set[str]) -> list[str]:
    dirty=_run(repo,"status","--porcelain=v1","--untracked-files=all").stdout.strip()
    if dirty: raise GitGuardError("GIT_SCOPE_VIOLATION", {"reason":"POST_COMMIT_WORKTREE_NOT_CLEAN","status":dirty.splitlines()[:50]})
    actual={x.strip() for x in _run(repo,"diff","--name-only",base_sha,candidate_sha,"--").stdout.splitlines() if x.strip()}
    if actual != set(allowed_paths): raise GitGuardError("GIT_SCOPE_VIOLATION", {"allowed":sorted(allowed_paths),"actual":sorted(actual)})
    head=_run(repo,"rev-parse","HEAD").stdout.strip()
    if head != candidate_sha: raise GitGuardError("GIT_SCOPE_VIOLATION", {"reason":"JOB_HEAD_MISMATCH","head":head,"candidate":candidate_sha})
    return sorted(actual)

def scoped_push_env(job_id: str, owner: str, base: dict[str,str] | None=None) -> dict[str,str]:
    env=dict(base or os.environ); env["EDARSA_ALLOW_PUSH"]="1"; env["EDARSA_PUSH_JOB_ID"]=job_id; env["EDARSA_PUSH_OWNER"]=owner; return env

def authorized_push(repo: Path, *, args: list[str], job_id: str, owner: str, env_base: dict[str,str] | None=None):
    return _run(repo,*args,check=False,env=scoped_push_env(job_id,owner,env_base))

def post_push_verify(repo: Path, expected_sha: str) -> dict[str,Any]:
    _run(repo,"fetch",REMOTE,DEV_BRANCH); local=_run(repo,"rev-parse","HEAD").stdout.strip(); remote=_run(repo,"rev-parse",f"{REMOTE}/{DEV_BRANCH}").stdout.strip(); counts=_run(repo,"rev-list","--left-right","--count",f"{local}...{remote}").stdout.split(); ahead,behind=(int(counts[0]),int(counts[1])) if len(counts)==2 else (-1,-1); evidence={"local_after":local,"remote_after_push":remote,"ahead_after":ahead,"behind_after":behind,"topology":f"{ahead}/{behind}"}
    if local != expected_sha or remote != expected_sha or ahead != 0 or behind != 0: raise GitGuardError("GIT_PUSH_FAILED", evidence)
    evidence["terminal_status"]="CERTIFIED_GIT_SYNC"; return evidence

def fast_forward_refresh(repo: Path, *, expected_remote: str, job_id: str, owner: str, owner_pid: int | None=None) -> dict[str,Any]:
    token=acquire_writer_lock(repo,job_id=job_id,owner=owner,owner_pid=owner_pid)
    try:
        state=inspect_repository(repo,fetch=True)
        if state["remote_head"] != expected_remote: raise GitGuardError("REMOTE_MOVED_RETRY_REQUIRED", {"expected_remote":expected_remote,"actual_remote":state["remote_head"]})
        if state["worktree_dirty"]: raise GitGuardError("GIT_WORKTREE_NOT_CLEAN", state)
        if state["classification"] == "SYNC": return state
        if state["classification"] != "REMOTE_AHEAD_ONLY" or state["merge_base"] != state["local_head"]: raise GitGuardError("GIT_DIVERGENCE_BLOCKED", state)
        local=state["local_head"]; remote=state["remote_head"]; rt=_run(repo,"read-tree","-u","-m",local,remote,check=False)
        if rt.returncode != 0: raise GitGuardError("GIT_DIVERGENCE_BLOCKED", {"reason":"FAST_FORWARD_WORKTREE_APPLY_FAILED","output":(rt.stdout or "")[-2000:]})
        ur=_run(repo,"update-ref",f"refs/heads/{DEV_BRANCH}",remote,local,check=False)
        if ur.returncode != 0:
            _run(repo,"read-tree","-u","-m",remote,local,check=False); raise GitGuardError("GIT_DIVERGENCE_BLOCKED", {"reason":"FAST_FORWARD_REF_CAS_FAILED","output":(ur.stdout or "")[-2000:]})
        final=inspect_repository(repo,fetch=False)
        if final["classification"] != "SYNC" or final["worktree_dirty"]: raise GitGuardError("GIT_DIVERGENCE_BLOCKED", {"reason":"FAST_FORWARD_POSTCHECK_FAILED","state":final})
        return final
    finally: release_writer_lock(repo,token)

def main() -> int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    i=sub.add_parser("inspect"); i.add_argument("--repo",default="/app"); i.add_argument("--no-fetch",action="store_true")
    a=sub.add_parser("acquire-lock"); a.add_argument("--repo",default="/app"); a.add_argument("--job-id",required=True); a.add_argument("--owner",required=True); a.add_argument("--owner-pid",type=int,default=0)
    r=sub.add_parser("release-lock"); r.add_argument("--repo",default="/app"); r.add_argument("--job-id",required=True); r.add_argument("--owner",required=True)
    f=sub.add_parser("refresh"); f.add_argument("--repo",default="/app"); f.add_argument("--expected-remote",required=True); f.add_argument("--job-id",required=True); f.add_argument("--owner",required=True); f.add_argument("--owner-pid",type=int,default=0)
    args=p.parse_args(); repo=Path(args.repo).resolve()
    try:
        if args.command=="inspect": payload=inspect_repository(repo,fetch=not args.no_fetch)
        elif args.command=="acquire-lock": payload=acquire_writer_lock(repo,job_id=args.job_id,owner=args.owner,owner_pid=args.owner_pid or None)
        elif args.command=="release-lock":
            ld=_git_dir(repo)/"universal-worker-queue"/LOCK_NAME; cur=_read_json(ld/"owner.json"); token={**cur,"job_id":args.job_id,"owner":args.owner,"lock_dir":str(ld)}; release_writer_lock(repo,token); payload={"released":True}
        else: payload=fast_forward_refresh(repo,expected_remote=args.expected_remote,job_id=args.job_id,owner=args.owner,owner_pid=args.owner_pid or None)
    except GitGuardError as exc:
        print(json.dumps({"status":exc.code,"evidence":exc.evidence},ensure_ascii=False)); return 1
    print(json.dumps(payload,ensure_ascii=False)); return 0
if __name__=="__main__": raise SystemExit(main())
