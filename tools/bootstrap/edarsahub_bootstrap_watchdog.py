#!/usr/bin/env python3
from __future__ import annotations

import hashlib
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

CONTROL_PLANE_SERVICE = os.environ.get(
    "EDARSAHUB_CONTROL_PLANE_SERVICE",
    "edarsahub-worker-control-plane",
)
CONTROL_PLANE_RUNTIME_STATE = (
    STATE / "control_plane_runtime.json"
)
CONTROL_PLANE_ACTIVE_MARKER = (
    STATE / "control_plane_active_runtime.json"
)
CONTROL_PLANE_RESTART_COOLDOWN_SECONDS = int(
    os.environ.get(
        "EDARSAHUB_CONTROL_PLANE_RESTART_COOLDOWN_SECONDS",
        "60",
    )
)
CONTROL_PLANE_MAX_RESTART_ATTEMPTS = int(
    os.environ.get(
        "EDARSAHUB_CONTROL_PLANE_MAX_RESTART_ATTEMPTS",
        "2",
    )
)
CONTROL_PLANE_IDENTITY_PATHS = (
    "tools/mirror_sync/worker_control_plane.py",
    "tools/mirror_sync/worker_maintenance_runtime.py",
    "tools/mirror_sync/worker_maintenance_controller.py",
    "tools/mirror_sync/worker_maintenance_contract.py",
    "tools/mirror_sync/worker_auditor.py",
    "tools/mirror_sync/worker_repair.py",
)


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


def atomic_state_json(
    path: Path,
    payload: dict,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(
        path.name + ".tmp-" + str(os.getpid())
    )
    temp.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\\n",
        encoding="utf-8",
    )
    os.replace(temp, path)


def read_json(path: Path) -> dict | None:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return None

    return payload if isinstance(payload, dict) else None


def control_plane_expected_identity() -> str | None:
    components: list[str] = []

    for rel in CONTROL_PLANE_IDENTITY_PATHS:
        proc = run(
            [
                "git",
                "rev-parse",
                f"HEAD:{rel}",
            ],
            timeout=20,
        )
        blob = proc.stdout.strip()

        if (
            proc.returncode != 0
            or len(blob) != 40
            or any(
                char not in "0123456789abcdef"
                for char in blob.lower()
            )
        ):
            return None

        components.append(
            f"{rel}={blob.lower()}"
        )

    return hashlib.sha256(
        ("\\n".join(components) + "\\n").encode(
            "utf-8"
        )
    ).hexdigest()


def control_plane_repo_is_canonical() -> tuple[bool, str]:
    branch = run(
        ["git", "branch", "--show-current"],
        timeout=20,
    ).stdout.strip()

    if branch != DEV:
        return False, "WRONG_BRANCH"

    dirty = run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        timeout=20,
    )

    if dirty.returncode != 0:
        return False, "STATUS_FAILED"

    if dirty.stdout.strip():
        return False, "LOCAL_WORK_DIRTY"

    local = run(
        ["git", "rev-parse", "HEAD"],
        timeout=20,
    ).stdout.strip()
    remote = run(
        [
            "git",
            "rev-parse",
            f"{REMOTE}/{DEV}",
        ],
        timeout=20,
    ).stdout.strip()

    if not local or local != remote:
        return False, "DEVELOPMENT_NOT_CONVERGED"

    return True, "CANONICAL"


def control_plane_runtime_convergence() -> dict:
    expected = control_plane_expected_identity()
    active = read_json(
        CONTROL_PLANE_ACTIVE_MARKER
    ) or {}
    state = read_json(
        CONTROL_PLANE_RUNTIME_STATE
    ) or {}

    active_identity = str(
        active.get("active_identity") or ""
    ).strip()
    active_pid = int(
        active.get("pid") or 0
    )

    base = {
        "expected_identity": expected,
        "active_identity": active_identity or None,
        "active_pid": active_pid or None,
        "production_touched": False,
    }

    if not expected:
        return {
            **base,
            "state": "IDENTITY_UNAVAILABLE",
            "restart_requested": False,
        }

    if (
        active_identity == expected
        and active_pid > 1
    ):
        return {
            **base,
            "state": "CONVERGED",
            "restart_requested": False,
        }

    canonical, canonical_reason = (
        control_plane_repo_is_canonical()
    )

    if not canonical:
        return {
            **base,
            "state": "DEFERRED",
            "reason": canonical_reason,
            "restart_requested": False,
        }

    attempts = int(
        state.get("restart_attempts") or 0
    )
    cooldown_until = float(
        state.get("cooldown_until_epoch") or 0
    )
    now_epoch = time.time()

    if now_epoch < cooldown_until:
        return {
            **base,
            "state": "COOLDOWN",
            "restart_attempts": attempts,
            "cooldown_until_epoch": cooldown_until,
            "restart_requested": False,
        }

    if attempts >= CONTROL_PLANE_MAX_RESTART_ATTEMPTS:
        return {
            **base,
            "state": "ATTEMPTS_EXHAUSTED",
            "restart_attempts": attempts,
            "restart_requested": False,
        }

    previous_pid = active_pid

    request_state = {
        "schema": (
            "edarsahub.control-plane-runtime.v1"
        ),
        "expected_identity": expected,
        "active_identity": (
            active_identity or None
        ),
        "last_restart_requested_at_utc": now(),
        "last_restart_reason": (
            "CONTROL_PLANE_CODE_STALE"
        ),
        "last_successful_activation_at_utc": (
            state.get(
                "last_successful_activation_at_utc"
            )
        ),
        "restart_attempts": attempts + 1,
        "cooldown_until_epoch": (
            now_epoch
            + CONTROL_PLANE_RESTART_COOLDOWN_SECONDS
        ),
        "production_touched": False,
    }

    atomic_state_json(
        CONTROL_PLANE_RUNTIME_STATE,
        request_state,
    )

    restarted = supervisor_restart(
        "CONTROL_PLANE_CODE_STALE",
        CONTROL_PLANE_SERVICE,
    )

    if not restarted:
        return {
            **base,
            "state": "RESTART_FAILED",
            "restart_attempts": attempts + 1,
            "restart_requested": True,
            "restart_succeeded": False,
        }

    deadline = time.time() + 20

    while time.time() < deadline:
        time.sleep(0.5)

        activated = read_json(
            CONTROL_PLANE_ACTIVE_MARKER
        ) or {}

        new_identity = str(
            activated.get("active_identity") or ""
        ).strip()
        new_pid = int(
            activated.get("pid") or 0
        )

        if (
            new_identity == expected
            and new_pid > 1
            and new_pid != previous_pid
        ):
            success = {
                "schema": (
                    "edarsahub.control-plane-runtime.v1"
                ),
                "expected_identity": expected,
                "active_identity": expected,
                "last_restart_requested_at_utc": (
                    request_state[
                        "last_restart_requested_at_utc"
                    ]
                ),
                "last_restart_reason": (
                    "CONTROL_PLANE_CODE_STALE"
                ),
                "last_successful_activation_at_utc": (
                    now()
                ),
                "restart_attempts": 0,
                "cooldown_until_epoch": None,
                "active_pid": new_pid,
                "production_touched": False,
            }

            atomic_state_json(
                CONTROL_PLANE_RUNTIME_STATE,
                success,
            )

            return {
                **base,
                "state": "CONVERGED_AFTER_RESTART",
                "active_identity": expected,
                "active_pid": new_pid,
                "restart_requested": True,
                "restart_succeeded": True,
            }

    return {
        **base,
        "state": "ACTIVATION_ACK_TIMEOUT",
        "restart_attempts": attempts + 1,
        "restart_requested": True,
        "restart_succeeded": True,
    }


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
    control_plane_runtime = (
        control_plane_runtime_convergence()
    )
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
        "control_plane_runtime": control_plane_runtime,
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
