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
import re
import subprocess
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
WORKER_SERVICE = "edarsahub-universal-worker"
LOCK_PATH = Path("/tmp/edarsahub-universal-worker-wake.lock")
COOLDOWN_PATH = Path("/tmp/edarsahub-universal-worker-wake.last")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _remote_queue_sha() -> str:
    try:
        completed = subprocess.run(
            ["git", "ls-remote", "origin", QUEUE_REF],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
            env={"GIT_TERMINAL_PROMPT": "0"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker queue head unavailable",
        ) from exc

    fields = completed.stdout.strip().split()
    if (
        completed.returncode != 0
        or len(fields) < 2
        or fields[1] != QUEUE_REF
        or not _SHA_RE.fullmatch(fields[0])
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker queue head invalid",
        )
    return fields[0].lower()


def _heartbeat_age_seconds() -> float | None:
    try:
        raw = LAST_RECEIVE.read_text(encoding="utf-8").strip().replace("Z", "+00:00")
        value = datetime.fromisoformat(raw)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return max(0.0, time.time() - value.timestamp())
    except (OSError, ValueError):
        return None


def _restart_worker() -> None:
    try:
        completed = subprocess.run(
            ["supervisorctl", "restart", WORKER_SERVICE],
            cwd=str(REPO_ROOT),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker restart unavailable",
        ) from exc

    if completed.returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker restart failed",
        )


@router.post("/internal/worker/wake", status_code=status.HTTP_202_ACCEPTED)
def wake_worker(
    x_worker_queue_sha: str | None = Header(default=None, alias="X-Worker-Queue-Sha"),
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

    heartbeat_age = _heartbeat_age_seconds()
    if heartbeat_age is not None and heartbeat_age <= 90:
        return {
            "accepted": True,
            "action": "already_healthy",
            "queue_sha": current,
            "heartbeat_age_seconds": round(heartbeat_age, 3),
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
            "requested_at_utc": requested_at,
            "production_touched": False,
        },
    )
