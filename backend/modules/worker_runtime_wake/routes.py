"""Internal endpoint used only to wake the universal worker runtime.

Security contract:
- caller must present X-Worker-Queue-Sha;
- value must be a 40-character hexadecimal Git SHA;
- value must equal the current remote HEAD of refs/heads/worker/requests;
- endpoint cannot accept commands, paths, branches, or process names;
- endpoint can only restart the fixed supervisor service for the Universal Worker;
- Production is never touched.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import JSONResponse

router = APIRouter(tags=["worker-runtime-internal"])

REPO_ROOT = Path("/app")
RUNTIME_DIR = REPO_ROOT / ".git" / "universal-worker-queue" / "runtime"
LAST_RECEIVE = RUNTIME_DIR / "last_receive_utc"
QUEUE_REF = "refs/heads/worker/requests"
CANONICAL_QUEUE_REMOTE = "https://github.com/rbalam/EDARSA_HUB.git"
DEV_BRANCH = "Edarsahub_Desarrollo"
WORKER_SERVICE = "edarsahub-universal-worker"
LOCK_PATH = Path("/tmp/edarsahub-universal-worker-wake.lock")
COOLDOWN_PATH = Path("/tmp/edarsahub-universal-worker-wake.last")
PREFERRED_JOB_PATH = RUNTIME_DIR / "preferred_job.json"
PREFERRED_JOB_TTL_SECONDS = 300
_JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")
WORKER_TREE_STATE = RUNTIME_DIR / "active_worker_code_tree_sha"
WORKER_CODE_TREE_SPEC = "HEAD:tools/mirror_sync"
GIT_GUARD_PATH = REPO_ROOT / "tools" / "mirror_sync" / "git_divergence_guard.py"
WAKE_ROUTE_VERSION = "r34-startup-selfheal"
# Runtime reload marker: ISCAM R18 recovery after public wake 502/404; no functional change.
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _remote_queue_sha() -> str:
    last_error: Exception | None = None
    attempts: list[str] = []
    for label, remote in (("origin", "origin"), ("canonical", CANONICAL_QUEUE_REMOTE)):
        try:
            completed = subprocess.run(
                ["git", "ls-remote", remote, QUEUE_REF],
                cwd=str(REPO_ROOT),
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
        except subprocess.TimeoutExpired as exc:
            last_error = exc
            attempts.append(f"{label}=timeout")
            continue
        except OSError as exc:
            last_error = exc
            attempts.append(f"{label}=oserror")
            continue

        fields = completed.stdout.strip().split()
        if (
            completed.returncode == 0
            and len(fields) >= 2
            and fields[1] == QUEUE_REF
            and _SHA_RE.fullmatch(fields[0])
        ):
            return fields[0].lower()
        attempts.append(f"{label}=rc{completed.returncode}")

    diagnostic = ",".join(attempts) if attempts else "no-attempt"
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"worker queue head unavailable [{diagnostic}]",
    ) from last_error


def _runtime_git(*args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="worker runtime git unavailable") from exc


def _converge_development_if_safe() -> dict[str, str]:
    fetch = _runtime_git("fetch", "--quiet", "origin", DEV_BRANCH, timeout=90)
    if fetch.returncode != 0:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="worker runtime development fetch failed")
    branch = _runtime_git("branch", "--show-current").stdout.strip()
    local = _runtime_git("rev-parse", "HEAD").stdout.strip().lower()
    remote = _runtime_git("rev-parse", f"origin/{DEV_BRANCH}").stdout.strip().lower()
    if not _SHA_RE.fullmatch(local) or not _SHA_RE.fullmatch(remote):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="worker runtime development sha invalid")
    if local == remote:
        return {"state": "ALIGNED", "local_sha": local, "remote_sha": remote}
    if branch != DEV_BRANCH:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"worker runtime convergence blocked: wrong branch {branch}")
    if _runtime_git("merge-base", "--is-ancestor", local, remote).returncode != 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="worker runtime convergence blocked: non-fast-forward")
    dirty = _runtime_git("status", "--porcelain=v1", "--untracked-files=all")
    if dirty.returncode != 0:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="worker runtime worktree status unavailable")
    if dirty.stdout.strip():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="worker runtime convergence blocked: local worktree dirty")
    if not GIT_GUARD_PATH.is_file():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker runtime canonical git guard unavailable",
        )
    try:
        refresh = subprocess.run(
            [
                sys.executable,
                str(GIT_GUARD_PATH),
                "refresh",
                "--repo",
                str(REPO_ROOT),
                "--expected-remote",
                remote,
                "--job-id",
                f"worker-runtime-wake-{os.getpid()}",
                "--owner",
                "worker-runtime-wake",
                "--owner-pid",
                str(os.getpid()),
            ],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker runtime canonical fast-forward unavailable",
        ) from exc
    if refresh.returncode != 0:
        detail = "canonical refresh failed"
        try:
            payload = json.loads((refresh.stdout or "").strip() or "{}")
            detail = str(payload.get("status") or detail)
        except (TypeError, ValueError):
            pass
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"worker runtime canonical fast-forward failed [{detail}]",
        )
    new_head = _runtime_git("rev-parse", "HEAD").stdout.strip().lower()
    if new_head != remote:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker runtime fast-forward verification failed",
        )
    return {"state": "FF_APPLIED", "local_sha": local, "remote_sha": remote, "new_sha": new_head}


def _current_worker_code_tree() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", WORKER_CODE_TREE_SPEC],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="worker code tree unavailable") from exc
    value = completed.stdout.strip().lower()
    if completed.returncode != 0 or not _SHA_RE.fullmatch(value):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="worker code tree invalid")
    return value


def _active_worker_code_tree() -> str | None:
    try:
        value = WORKER_TREE_STATE.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return None
    return value if _SHA_RE.fullmatch(value) else None


def _heartbeat_age_seconds() -> float | None:
    try:
        raw = LAST_RECEIVE.read_text(encoding="utf-8").strip().replace("Z", "+00:00")
        value = datetime.fromisoformat(raw)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return max(0.0, time.time() - value.timestamp())
    except (OSError, ValueError):
        return None


def _active_job_id() -> str | None:
    try:
        value = (RUNTIME_DIR / "current_job_id").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def _register_preferred_job(job_id: str, queue_sha: str) -> str | None:
    value = (job_id or "").strip()
    if not value:
        return None
    if not _JOB_ID_RE.fullmatch(value):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid preferred worker job id",
        )
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "job_id": value,
        "queue_sha": queue_sha,
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "expires_at_epoch": time.time() + PREFERRED_JOB_TTL_SECONDS,
    }
    temporary = PREFERRED_JOB_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, PREFERRED_JOB_PATH)
    return value


def _run_supervisor_worker_action(action: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["supervisorctl", action, WORKER_SERVICE],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker supervisor unavailable",
        ) from exc


def _restart_worker() -> None:
    completed = _run_supervisor_worker_action("restart")
    if completed.returncode == 0:
        return

    started = _run_supervisor_worker_action("start")
    if started.returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker restart failed",
        )


def _is_production_environment() -> bool:
    env_name = (
        os.environ.get("EDARSA_ENV")
        or os.environ.get("APP_ENV")
        or os.environ.get("ENVIRONMENT")
        or "PREVIEW"
    ).upper()
    return "PROD" in env_name


def ensure_worker_runtime_on_preview_startup() -> dict[str, object]:
    """Recover a stale Universal Worker whenever the Preview backend starts.

    This does not depend on the public wake endpoint. The endpoint cannot
    repair itself when the deployed backend is stale, so backend startup is
    the local recovery boundary.
    """
    if _is_production_environment():
        return {
            "state": "SKIPPED_PRODUCTION_ENV",
            "production_touched": False,
        }

    heartbeat_age = _heartbeat_age_seconds()
    if heartbeat_age is not None and heartbeat_age <= 90:
        return {
            "state": "ALREADY_HEALTHY",
            "heartbeat_age_seconds": round(heartbeat_age, 3),
            "production_touched": False,
        }

    _restart_worker()
    return {
        "state": "WORKER_RESTART_REQUESTED",
        "heartbeat_age_seconds": round(heartbeat_age, 3) if heartbeat_age is not None else None,
        "service": WORKER_SERVICE,
        "production_touched": False,
    }


@router.post("/internal/worker/wake", status_code=status.HTTP_202_ACCEPTED)
def wake_worker(
    x_worker_queue_sha: str | None = Header(default=None, alias="X-Worker-Queue-Sha"),
    x_worker_preferred_job_id: str | None = Header(default=None, alias="X-Worker-Preferred-Job-Id"),
):
    supplied = (x_worker_queue_sha or "").strip()
    if not _SHA_RE.fullmatch(supplied):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid worker queue proof",
        )

    current = _remote_queue_sha()
    if supplied.lower() != current:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="stale worker queue proof",
        )

    preferred_job_id = _register_preferred_job(x_worker_preferred_job_id or "", current)
    heartbeat_age = _heartbeat_age_seconds()
    active_job_id = _active_job_id()
    if active_job_id and heartbeat_age is not None and heartbeat_age <= 90:
        return {
            "accepted": True,
            "action": "active_job_preserved",
            "queue_sha": current,
            "active_job_id": active_job_id,
            "preferred_job_id": preferred_job_id,
            "heartbeat_age_seconds": round(heartbeat_age, 3),
            "runtime_convergence": {"state": "DEFERRED_ACTIVE_JOB"},
            "wake_route_version": WAKE_ROUTE_VERSION,
            "production_touched": False,
        }

    convergence = _converge_development_if_safe()
    current_worker_tree = _current_worker_code_tree()
    active_worker_tree = _active_worker_code_tree()
    worker_code_current = active_worker_tree == current_worker_tree
    if heartbeat_age is not None and heartbeat_age <= 90 and worker_code_current:
        return {
            "accepted": True,
            "action": "already_healthy",
            "queue_sha": current,
            "heartbeat_age_seconds": round(heartbeat_age, 3),
            "preferred_job_id": preferred_job_id,
            "worker_code_tree": current_worker_tree,
            "runtime_convergence": convergence,
            "wake_route_version": WAKE_ROUTE_VERSION,
            "production_touched": False,
        }

    LOCK_PATH.touch(exist_ok=True)
    with LOCK_PATH.open("r+", encoding="utf-8") as lock_handle:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="worker wake already in progress",
            ) from exc

        now = time.time()
        try:
            last = float(COOLDOWN_PATH.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            last = 0.0
        if now - last < 30:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="worker wake cooldown",
            )

        _restart_worker()
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        WORKER_TREE_STATE.write_text(current_worker_tree + "\n", encoding="utf-8")
        COOLDOWN_PATH.write_text(str(now), encoding="utf-8")

    requested_at = datetime.now(timezone.utc).isoformat()
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "accepted": True,
            "action": "worker_restart_accepted",
            "service": WORKER_SERVICE,
            "queue_sha": current,
            "heartbeat_age_seconds": round(heartbeat_age, 3) if heartbeat_age is not None else None,
            "preferred_job_id": preferred_job_id,
            "worker_code_tree": current_worker_tree,
            "worker_code_changed": not worker_code_current,
            "runtime_convergence": convergence,
            "wake_route_version": WAKE_ROUTE_VERSION,
            "requested_at_utc": requested_at,
            "production_touched": False,
        },
    )
