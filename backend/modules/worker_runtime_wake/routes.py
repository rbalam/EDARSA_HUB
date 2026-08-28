"""Internal endpoint used only to wake the universal worker runtime.

Security contract:
- caller must present X-Worker-Queue-Sha;
- value must be a 40-character lowercase/uppercase hex Git SHA;
- value must equal the current remote HEAD of refs/heads/worker/requests;
- endpoint cannot accept commands, paths, branches or arbitrary process names;
- endpoint only emits the fixed local wake signal consumed by the runtime control plane.
"""
from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, status

router = APIRouter(tags=["worker-runtime-internal"])

REPO_ROOT = Path("/app")
WAKE_DIR = REPO_ROOT / ".git" / "universal-worker-queue" / "runtime"
WAKE_SIGNAL = WAKE_DIR / "wake.request"
QUEUE_REF = "refs/heads/worker/requests"
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _remote_queue_sha() -> str:
    try:
        completed = subprocess.run(
            ["git", "ls-remote", "origin", QUEUE_REF],
            cwd=str(REPO_ROOT),
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker queue head unavailable",
        ) from exc

    fields = completed.stdout.strip().split()
    if len(fields) < 2 or fields[1] != QUEUE_REF or not _SHA_RE.fullmatch(fields[0]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="worker queue head invalid",
        )
    return fields[0].lower()


@router.post("/internal/worker/wake", status_code=status.HTTP_202_ACCEPTED)
def wake_worker(x_worker_queue_sha: str | None = Header(default=None, alias="X-Worker-Queue-Sha")):
    supplied = (x_worker_queue_sha or "").strip()
    if not _SHA_RE.fullmatch(supplied):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid worker queue proof")

    current = _remote_queue_sha()
    if supplied.lower() != current:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="stale worker queue proof")

    WAKE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    tmp = WAKE_SIGNAL.with_suffix(".tmp")
    tmp.write_text(f"{timestamp} {current}\n", encoding="utf-8")
    tmp.replace(WAKE_SIGNAL)

    return {
        "accepted": True,
        "action": "worker_wake_signal",
        "queue_sha": current,
        "requested_at_utc": timestamp,
        "production_touched": False,
    }
