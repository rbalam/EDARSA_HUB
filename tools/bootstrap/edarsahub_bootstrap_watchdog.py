#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

APP = Path(os.environ.get("EDARSAHUB_APP", "/app"))
STATE = Path(os.environ.get("EDARSAHUB_BOOTSTRAP_STATE", "/var/lib/edarsahub-bootstrap"))
REMOTE = os.environ.get("EDARSAHUB_REMOTE", "origin")
DEV = os.environ.get("EDARSAHUB_DEV_BRANCH", "Edarsahub_Desarrollo")
SERVICE = os.environ.get("EDARSAHUB_SUPERVISOR_SERVICE", "edarsahub-mirror-sync")
WORKER_SERVICE = os.environ.get("EDARSAHUB_UNIVERSAL_WORKER_SERVICE", "edarsahub-universal-worker")
BACKEND_SERVICE = os.environ.get("EDARSAHUB_BACKEND_SERVICE", "backend")
BACKEND_WAKE_URL = os.environ.get("EDARSAHUB_BACKEND_WAKE_URL", "http://127.0.0.1:8001/api/internal/worker/wake")
INTERVAL = int(os.environ.get("EDARSAHUB_BOOTSTRAP_INTERVAL", "20"))
MAX_STALE = int(os.environ.get("EDARSAHUB_BOOTSTRAP_MAX_STALE", "60"))
BACKEND_RECOVERY_COOLDOWN = int(os.environ.get("EDARSAHUB_BACKEND_RECOVERY_COOLDOWN", "120"))
RUNTIME = APP / ".git" / "universal-worker-queue" / "runtime"
MIRROR_STATE = APP / ".git" / "mirror-sync"
MIRROR_ENABLE = MIRROR_STATE / "ENABLED"
MIRROR_STOP = MIRROR_STATE / "STOP"
SYNC_PAUSE = APP / ".git" / "EDARSAHUB_SYNC_PAUSED"
STATUS = STATE / "status.json"
AUDIT = STATE / "audit.jsonl"
BACKEND_RECOVERY_STAMP = STATE / "backend_recovery_epoch"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(args: list[str], cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd or APP),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def audit(event: str, **fields):
    STATE.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as h:
        h.write(
            json.dumps(
                {"at_utc": now(), "event": event, **fields, "production_touched": False},
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )


def age_seconds(path: Path) -> float | None:
    try:
        raw = path.read_text(encoding="utf-8").strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        return max(0.0, time.time() - dt.timestamp())
    except Exception:
        return None


def is_production_environment() -> bool:
    env_name = (
        os.environ.get("EDARSA_ENV")
        or os.environ.get("APP_ENV")
        or os.environ.get("ENVIRONMENT")
        or "PREVIEW"
    ).upper()
    return "PROD" in env_name


def backend_wake_route_health() -> dict:
    """Probe the local route without a queue proof.

    A healthy mounted route must reject the request with 401. 404 means the
    running backend is stale and does not have the router mounted.
    """
    try:
        result = run(
            [
                "curl",
                "--silent",
                "--show-error",
                "--connect-timeout",
                "2",
                "--max-time",
                "5",
                "--output",
                "/tmp/edarsahub-bootstrap-wake-probe.json",
                "--write-out",
                "%{http_code}",
                "--request",
                "POST",
                BACKEND_WAKE_URL,
                "--header",
                "Content-Type: application/json",
                "--data",
                "{}",
            ],
            timeout=8,
        )
        code = (result.stdout or "").strip()[-3:]
        healthy = result.returncode == 0 and code == "401"
        return {"healthy": healthy, "http_code": code or "000", "returncode": result.returncode}
    except Exception as exc:
        return {"healthy": False, "http_code": "000", "error": str(exc)}


def maybe_recover_backend() -> dict:
    if is_production_environment():
        audit("BACKEND_RECOVERY_BLOCKED_PRODUCTION_ENV", service=BACKEND_SERVICE)
        return {"state": "BLOCKED_PRODUCTION_ENV", "restarted": False}

    probe = backend_wake_route_health()
    if probe.get("healthy"):
        return {"state": "HEALTHY", "probe": probe, "restarted": False}

    now_epoch = int(time.time())
    try:
        last_epoch = int(BACKEND_RECOVERY_STAMP.read_text(encoding="utf-8").strip())
    except Exception:
        last_epoch = 0
    if now_epoch - last_epoch < BACKEND_RECOVERY_COOLDOWN:
        audit("BACKEND_RECOVERY_COOLDOWN", probe=probe, service=BACKEND_SERVICE)
        return {"state": "COOLDOWN", "probe": probe, "restarted": False}

    STATE.mkdir(parents=True, exist_ok=True)
    BACKEND_RECOVERY_STAMP.write_text(str(now_epoch) + "\n", encoding="utf-8")
    restarted = supervisor_restart("WAKE_ROUTE_UNHEALTHY", BACKEND_SERVICE)
    audit(
        "PREVIEW_BACKEND_STALE_RECOVERY",
        probe=probe,
        action="SUPERVISOR_RESTART",
        service=BACKEND_SERVICE,
        restarted=restarted,
    )
    return {
        "state": "RESTART_REQUESTED" if restarted else "RESTART_FAILED",
        "probe": probe,
        "restarted": restarted,
    }


def mirror_authorization() -> dict:
    """Fail closed: sync needs explicit ENABLED and no persistent pause/stop."""
    branch = run(["git", "branch", "--show-current"], timeout=20).stdout.strip()
    env_name = (
        os.environ.get("EDARSA_ENV")
        or os.environ.get("APP_ENV")
        or os.environ.get("ENVIRONMENT")
        or "PREVIEW"
    ).upper()
    if "PROD" in env_name:
        return {"authorized": False, "state": "BLOCKED_PRODUCTION_ENV"}
    if branch != DEV:
        return {"authorized": False, "state": "BLOCKED_WRONG_BRANCH", "branch": branch}
    if SYNC_PAUSE.exists():
        return {"authorized": False, "state": "SYNC_PAUSED"}
    if MIRROR_STOP.exists():
        return {"authorized": False, "state": "PERSISTENT_KILL_SWITCH"}
    if not MIRROR_ENABLE.exists():
        return {"authorized": False, "state": "EXPLICIT_ENABLE_REQUIRED"}
    dirty = run(["git", "status", "--porcelain=v1", "--untracked-files=all"], timeout=20)
    if dirty.stdout.strip():
        return {"authorized": False, "state": "DEFERRED_LOCAL_DIRTY"}
    return {"authorized": True, "state": "AUTHORIZED"}


def supervisor_restart(reason: str, service: str = SERVICE) -> bool:
    if is_production_environment():
        audit("SUPERVISOR_RESTART_BLOCKED_PRODUCTION_ENV", reason=reason, service=service)
        return False
    result = run(["supervisorctl", "restart", service], cwd=APP, timeout=30)
    ok = result.returncode == 0
    audit("SUPERVISOR_RESTART", reason=reason, service=service, ok=ok, output=result.stdout[-1000:])
    return ok


def safe_fast_forward() -> dict:
    auth = mirror_authorization()
    if not auth["authorized"]:
        audit("FAST_FORWARD_DEFERRED", reason=auth["state"])
        return {"state": auth["state"], "preserved": True}

    fetch = run(["git", "fetch", "--quiet", REMOTE, DEV], timeout=90)
    if fetch.returncode != 0:
        return {"state": "FETCH_FAILED", "output": fetch.stdout[-800:]}
    branch = run(["git", "branch", "--show-current"], timeout=20).stdout.strip()
    if branch != DEV:
        return {"state": "WRONG_BRANCH", "branch": branch}
    local = run(["git", "rev-parse", "HEAD"], timeout=20).stdout.strip()
    remote = run(["git", "rev-parse", f"{REMOTE}/{DEV}"], timeout=20).stdout.strip()
    if local == remote:
        return {"state": "ALIGNED", "head": local}
    counts = run(["git", "rev-list", "--left-right", "--count", f"HEAD...{REMOTE}/{DEV}"], timeout=20)
    if counts.returncode != 0:
        return {"state": "TOPOLOGY_FAILED"}
    left, right = [int(v) for v in counts.stdout.split()[:2]]
    if left != 0 or right <= 0:
        return {"state": "NON_FF", "local_ahead": left, "remote_ahead": right}

    # Re-check immediately before mutation. Never stash/reset/clean/restore.
    dirty = run(["git", "status", "--porcelain=v1", "--untracked-files=all"], timeout=20)
    if dirty.stdout.strip():
        audit("FAST_FORWARD_DEFERRED", reason="LOCAL_WORK_DIRTY", local=local, remote=remote)
        return {"state": "DEFERRED_LOCAL_DIRTY", "local": local, "remote": remote, "preserved": True}

    ff = run(["git", "merge", "--ff-only", f"{REMOTE}/{DEV}"], timeout=120)
    if ff.returncode != 0:
        return {"state": "FF_FAILED", "output": ff.stdout[-800:]}
    new_head = run(["git", "rev-parse", "HEAD"], timeout=20).stdout.strip()
    audit("FAST_FORWARD_APPLIED", from_sha=local, to_sha=new_head)
    return {"state": "FF_APPLIED", "from": local, "to": new_head}


def cycle() -> dict:
    STATE.mkdir(parents=True, exist_ok=True)
    auth = mirror_authorization()
    ff = safe_fast_forward()
    backend = maybe_recover_backend()
    age = age_seconds(RUNTIME / "last_receive_utc")
    stale = age is None or age > MAX_STALE
    restarted = False

    # Mirror lifecycle is enabled only after explicit authorization. Pod restart
    # itself is never authorization.
    if auth["authorized"] and ff.get("state") == "FF_APPLIED":
        restarted = supervisor_restart("FAST_FORWARD_APPLIED")
    if stale:
        restarted = supervisor_restart("WORKER_HEARTBEAT_STALE", WORKER_SERVICE) or restarted
        audit(
            "UNIVERSAL_WORKER_STALE_RECOVERY",
            worker_receive_age_seconds=age,
            action="SUPERVISOR_RESTART",
            service=WORKER_SERVICE,
            restarted=restarted,
        )

    payload = {
        "schema": "edarsahub.bootstrap-watchdog.v2",
        "at_utc": now(),
        "mirror_authorization": auth,
        "ff": ff,
        "backend_recovery": backend,
        "worker_receive_age_seconds": age,
        "worker_stale": stale,
        "restart_requested": restarted,
        "worker_restart_owner": "BOOTSTRAP_WATCHDOG_SUPERVISOR_FALLBACK",
        "production_touched": False,
    }
    STATUS.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    once = "--once" in os.sys.argv
    while True:
        try:
            print(
                "BOOTSTRAP_WATCHDOG="
                + json.dumps(cycle(), ensure_ascii=False, sort_keys=True),
                flush=True,
            )
        except Exception as exc:
            audit("CYCLE_ERROR", error=str(exc))
            print(f"BOOTSTRAP_WATCHDOG_ERROR={exc}", flush=True)
        if once:
            return 0
        time.sleep(max(10, INTERVAL))


if __name__ == "__main__":
    raise SystemExit(main())
