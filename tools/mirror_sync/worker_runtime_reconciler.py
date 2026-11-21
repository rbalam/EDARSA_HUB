#!/usr/bin/env python3
"""Safe self-healing reconciler for the EDARSAHUB universal worker.

It never releases a claim based on age alone. A claim is releasable only when
the owning work is terminal/integrated, its worktree is clean (or gone), and
no live process references that worktree. It also recovers orphan processing
jobs so the dispatcher can retry them after a crash.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
RUNTIME = STATE / "runtime"
PENDING = STATE / "pending"
PROCESSING = STATE / "processing"
DONE = STATE / "done"
REJECTED = STATE / "rejected"
RESULTS = STATE / "results"
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
DEV_BRANCH = os.environ.get("EDARSAHUB_DEV_BRANCH", "Edarsahub_Desarrollo")
ORPHAN_SECONDS = int(os.environ.get("EDARSAHUB_PROCESSING_ORPHAN_SECONDS", "2100"))
CLAIM_STALE_SECONDS = int(os.environ.get("EDARSAHUB_CLAIM_STALE_SECONDS", "900"))
GUARD = ROOT / ".git" / "agent-guard" / "bin" / "agent_guard.py"
GUARD_STATE_WORKTREES = ROOT / ".git" / "agent-guard" / "state" / "worktrees"
PYTHON = Path("/root/.venv/bin/python")

_CYCLE_REMOTE_HEAD: str | None = None
_BRANCH_INTEGRATION_CACHE: dict[str, bool] = {}

def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def run(args: list[str], cwd: Path = ROOT, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False, timeout=timeout, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})

def git(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=cwd)

def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True); handle.write("\n"); temp = handle.name
    os.replace(temp, path)

def process_references(path: Path) -> bool:
    proc = Path("/proc")
    if not proc.is_dir(): return True
    needle = str(path)
    for child in proc.iterdir():
        if not child.name.isdigit(): continue
        try: cmdline = (child / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
        except Exception: continue
        if needle and needle in cmdline: return True
    return False

def dispatcher_running() -> bool:
    proc = Path("/proc")
    if not proc.is_dir(): return True
    for child in proc.iterdir():
        if not child.name.isdigit(): continue
        try: cmdline = (child / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
        except Exception: continue
        if "universal_job_dispatcher.py" in cmdline: return True
    return False

def age_seconds(path: Path) -> int: return max(0, int(time.time() - path.stat().st_mtime))

def load_result(job_id: str) -> dict[str, Any] | None:
    path = RESULTS / f"{job_id}.json"
    if not path.is_file(): return None
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except Exception: return None
    return value if isinstance(value, dict) else None

def recover_orphan_processing() -> list[dict[str, Any]]:
    recovered = []
    if not PROCESSING.exists() or dispatcher_running(): return recovered
    PENDING.mkdir(parents=True, exist_ok=True); DONE.mkdir(parents=True, exist_ok=True); REJECTED.mkdir(parents=True, exist_ok=True)
    for path in PROCESSING.glob("*.json"):
        if age_seconds(path) < ORPHAN_SECONDS: continue
        result = load_result(path.stem)
        if result is not None:
            destination = DONE / path.name if result.get("status") == "INTEGRATED" else REJECTED / path.name
            os.replace(path, destination); recovered.append({"job_id": path.stem, "action": "TERMINAL_RECONCILED"})
        else:
            os.replace(path, PENDING / path.name); recovered.append({"job_id": path.stem, "action": "REQUEUED_ORPHAN"})
    return recovered

def parse_guard_claims(text: str) -> list[dict[str, Any]]:
    claims = []
    for line in text.splitlines():
        if "ACTIVE_CLAIM" not in line or "=" not in line: continue
        try: value = json.loads(line.split("=", 1)[1].strip())
        except Exception: continue
        if isinstance(value, dict): claims.append(value)
    return claims

def guard_claims() -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []

    if GUARD.is_file() and PYTHON.is_file():
        try:
            result = run([str(PYTHON), str(GUARD), "status"], timeout=20)
        except Exception:
            result = None

        if result is not None and result.returncode == 0:
            claims.extend(parse_guard_claims(result.stdout))

    claim_state_dir = ROOT / ".git" / "agent-guard" / "state" / "claims"
    if claim_state_dir.is_dir():
        for path in sorted(claim_state_dir.glob("*.json")):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            if not isinstance(value, dict):
                continue

            if str(value.get("status") or "").strip().upper() != "ACTIVE":
                continue

            claim = dict(value)
            claim.setdefault("claim_file", str(path))
            claims.append(claim)

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for claim in claims:
        key = (
            str(claim.get("agent_id") or ""),
            str(claim.get("branch") or ""),
            str(claim.get("worktree") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(claim)

    return deduped

def parse_iso(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text: return None
    try: return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except Exception: return None

def prepare_integration_snapshot() -> bool:
    global _CYCLE_REMOTE_HEAD

    _BRANCH_INTEGRATION_CACHE.clear()
    _CYCLE_REMOTE_HEAD = None

    fetched = git("fetch", REMOTE, DEV_BRANCH)
    if fetched.returncode != 0:
        return False

    remote = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}")
    if remote.returncode != 0:
        return False

    resolved = remote.stdout.strip()
    if not resolved:
        return False

    _CYCLE_REMOTE_HEAD = resolved
    return True


def branch_is_integrated(branch: str) -> bool:
    if not branch:
        return False

    cached = _BRANCH_INTEGRATION_CACHE.get(branch)
    if cached is not None:
        return cached

    if not _CYCLE_REMOTE_HEAD:
        _BRANCH_INTEGRATION_CACHE[branch] = False
        return False

    head = git("rev-parse", "--verify", branch)
    if head.returncode != 0:
        _BRANCH_INTEGRATION_CACHE[branch] = False
        return False

    integrated = (
        git(
            "merge-base",
            "--is-ancestor",
            head.stdout.strip(),
            _CYCLE_REMOTE_HEAD,
        ).returncode
        == 0
    )
    _BRANCH_INTEGRATION_CACHE[branch] = integrated
    return integrated

def worktree_clean(path: Path) -> bool:
    if not path.exists(): return True
    if not (path / ".git").exists(): return False
    status = git("status", "--porcelain=v1", cwd=path); return status.returncode == 0 and not status.stdout.strip()

def claim_task_id(claim: dict[str, Any]) -> str:
    task_id = str(claim.get("task_id") or "").strip()
    if task_id: return task_id
    branch = str(claim.get("branch") or "").strip()
    prefix = "agent/worker/"
    if branch.startswith(prefix) and len(branch) > len(prefix): return branch[len(prefix):]
    agent_id = str(claim.get("agent_id") or "").strip()
    if agent_id.startswith("worker-") and len(agent_id) > len("worker-"): return agent_id[len("worker-"):]
    return ""

def claim_terminal(claim: dict[str, Any]) -> bool:
    task_id = claim_task_id(claim)
    if task_id and ((DONE / f"{task_id}.json").exists() or (REJECTED / f"{task_id}.json").exists() or (RESULTS / f"{task_id}.json").exists()): return True
    return branch_is_integrated(str(claim.get("branch") or ""))

def safe_releasable(claim: dict[str, Any]) -> tuple[bool, str]:
    claim_time = parse_iso(claim.get("heartbeat"))
    if claim_time is None: claim_time = parse_iso(claim.get("registered_at"))
    if claim_time is None: return False, "NO_CLAIM_TIME_EVIDENCE"
    if time.time() - claim_time < CLAIM_STALE_SECONDS: return False, "CLAIM_NOT_STALE"
    worktree = Path(str(claim.get("worktree") or ""))
    if not claim_terminal(claim): return False, "WORK_NOT_TERMINAL_OR_INTEGRATED"
    if process_references(worktree): return False, "LIVE_PROCESS_REFERENCES_WORKTREE"
    if not worktree_clean(worktree): return False, "WORKTREE_NOT_CLEAN"
    return True, "SAFE_TERMINAL_RECONCILIATION"

def release_claim(claim: dict[str, Any]) -> tuple[bool, str]:
    if not GUARD.is_file() or not PYTHON.is_file(): return False, "AGENT_GUARD_UNAVAILABLE"
    agent_id = str(claim.get("agent_id") or "").strip(); task_id = claim_task_id(claim)
    if not agent_id: return False, "CLAIM_IDENTITY_INCOMPLETE"
    commands = []
    if task_id:
        commands.extend(([str(PYTHON), str(GUARD), "claim-release", "--agent-id", agent_id, "--task-id", task_id], [str(PYTHON), str(GUARD), "release", "--agent-id", agent_id, "--task-id", task_id]))
    commands.extend(([str(PYTHON), str(GUARD), "claim-release", "--agent-id", agent_id], [str(PYTHON), str(GUARD), "release", "--agent-id", agent_id]))
    last = ""
    for command in commands:
        result = run(command, timeout=20); last = result.stdout[-800:]
        if result.returncode == 0:
            worktree = Path(str(claim.get("worktree") or ""))
            if worktree.exists():
                git("worktree", "remove", "--force", str(worktree)); shutil.rmtree(worktree, ignore_errors=True)
            branch = str(claim.get("branch") or "").strip()
            if branch and branch_is_integrated(branch): git("branch", "-d", branch)
            return True, "CLAIM_RELEASED"
    return False, "CLAIM_RELEASE_FAILED:" + last

def reconcile_claims() -> list[dict[str, Any]]:
    rows = []
    for claim in guard_claims():
        ok, reason = safe_releasable(claim); row = {"agent_id": claim.get("agent_id"), "task_id": claim.get("task_id"), "worktree": claim.get("worktree"), "decision": reason}
        if ok:
            released, release_reason = release_claim(claim); row["released"] = released; row["release_reason"] = release_reason
        else: row["released"] = False
        rows.append(row)
    return rows

def main() -> int:
    RUNTIME.mkdir(parents=True, exist_ok=True)

    integration_snapshot_ready = prepare_integration_snapshot()

    payload = {
        "schema": "edarsahub.worker-runtime-reconciler.v1",
        "generated_at_utc": now(),
        "integration_snapshot_ready": integration_snapshot_ready,
        "orphan_processing": recover_orphan_processing(),
        "claims": reconcile_claims(),
        "production_touched": False,
    }

    atomic_json(RUNTIME / "reconciler.json", payload)
    (RUNTIME / "last_reconcile_utc").write_text(
        now() + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__": raise SystemExit(main())
