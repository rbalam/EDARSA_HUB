#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

APP = Path(os.environ.get("EDARSAHUB_APP", "/app"))
STATE = Path(os.environ.get("EDARSAHUB_BOOTSTRAP_STATE", "/var/lib/edarsahub-bootstrap"))
REMOTE = os.environ.get("EDARSAHUB_REMOTE", "origin")
DEV = os.environ.get("EDARSAHUB_DEV_BRANCH", "Edarsahub_Desarrollo")
SERVICE = os.environ.get("EDARSAHUB_SUPERVISOR_SERVICE", "edarsahub-mirror-sync")
INTERVAL = int(os.environ.get("EDARSAHUB_BOOTSTRAP_INTERVAL", "20"))
MAX_STALE = int(os.environ.get("EDARSAHUB_BOOTSTRAP_MAX_STALE", "90"))
RUNTIME = APP / ".git" / "universal-worker-queue" / "runtime"
STATUS = STATE / "status.json"
AUDIT = STATE / "audit.jsonl"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(args: list[str], cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd or APP), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False, env={**os.environ, "GIT_TERMINAL_PROMPT":"0"})


def audit(event: str, **fields):
    STATE.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as h:
        h.write(json.dumps({"at_utc": now(), "event": event, **fields, "production_touched": False}, ensure_ascii=False, sort_keys=True) + "\n")


def age_seconds(path: Path) -> float | None:
    try:
        raw = path.read_text(encoding="utf-8").strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        return max(0.0, time.time() - dt.timestamp())
    except Exception:
        return None


def supervisor_restart(reason: str) -> bool:
    result = run(["supervisorctl", "restart", SERVICE], cwd=APP, timeout=30)
    ok = result.returncode == 0
    audit("SUPERVISOR_RESTART", reason=reason, ok=ok, output=result.stdout[-1000:])
    return ok


def preserve_dirty_worktree() -> str | None:
    status = run(["git", "status", "--porcelain"], timeout=20)
    if status.returncode != 0 or not status.stdout.strip():
        return None
    label = "bootstrap-preserve-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    result = run(["git", "stash", "push", "--include-untracked", "-m", label], timeout=120)
    if result.returncode != 0:
        raise RuntimeError("STASH_FAILED:" + result.stdout[-1200:])
    audit("WORKTREE_PRESERVED", label=label)
    return label


def safe_fast_forward() -> dict:
    fetch = run(["git", "fetch", "--quiet", REMOTE, DEV], timeout=90)
    if fetch.returncode != 0:
        return {"state":"FETCH_FAILED", "output":fetch.stdout[-800:]}
    branch = run(["git", "branch", "--show-current"], timeout=20).stdout.strip()
    if branch != DEV:
        return {"state":"WRONG_BRANCH", "branch":branch}
    local = run(["git", "rev-parse", "HEAD"], timeout=20).stdout.strip()
    remote = run(["git", "rev-parse", f"{REMOTE}/{DEV}"], timeout=20).stdout.strip()
    if local == remote:
        return {"state":"ALIGNED", "head":local}
    counts = run(["git", "rev-list", "--left-right", "--count", f"HEAD...{REMOTE}/{DEV}"], timeout=20)
    if counts.returncode != 0:
        return {"state":"TOPOLOGY_FAILED"}
    left, right = [int(v) for v in counts.stdout.split()[:2]]
    if left != 0 or right <= 0:
        return {"state":"NON_FF", "local_ahead":left, "remote_ahead":right}
    stash = preserve_dirty_worktree()
    ff = run(["git", "merge", "--ff-only", f"{REMOTE}/{DEV}"], timeout=120)
    if ff.returncode != 0:
        return {"state":"FF_FAILED", "stash":stash, "output":ff.stdout[-800:]}
    new_head = run(["git", "rev-parse", "HEAD"], timeout=20).stdout.strip()
    audit("FAST_FORWARD_APPLIED", from_sha=local, to_sha=new_head, stash=stash)
    return {"state":"FF_APPLIED", "from":local, "to":new_head, "stash":stash}


def cycle() -> dict:
    STATE.mkdir(parents=True, exist_ok=True)
    ff = safe_fast_forward()
    age = age_seconds(RUNTIME / "last_receive_utc")
    stale = age is None or age > MAX_STALE
    restarted = False
    if ff.get("state") == "FF_APPLIED":
        restarted = supervisor_restart("FAST_FORWARD_APPLIED")
    elif stale:
        restarted = supervisor_restart("WORKER_HEARTBEAT_STALE")
    payload = {"schema":"edarsahub.bootstrap-watchdog.v1","at_utc":now(),"ff":ff,"worker_receive_age_seconds":age,"worker_stale":stale,"restart_requested":restarted,"production_touched":False}
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return payload


def main() -> int:
    once = "--once" in os.sys.argv
    while True:
        try:
            print("BOOTSTRAP_WATCHDOG=" + json.dumps(cycle(), ensure_ascii=False, sort_keys=True), flush=True)
        except Exception as exc:
            audit("CYCLE_ERROR", error=str(exc))
            print(f"BOOTSTRAP_WATCHDOG_ERROR={exc}", flush=True)
        if once:
            return 0
        time.sleep(max(10, INTERVAL))


if __name__ == "__main__":
    raise SystemExit(main())
