#!/usr/bin/env python3
"""Publica salud y estados de la cola universal en worker/requests sin secretos."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
import tempfile

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
BRANCH = os.environ.get("EDARSAHUB_QUEUE_BRANCH", "worker/requests")
WT = Path(tempfile.mkdtemp(prefix="edarsahub-worker-health-publish-"))
MIN_INTERVAL = int(os.environ.get("EDARSAHUB_HEARTBEAT_SECONDS", "60"))
STALE_SECONDS = int(os.environ.get("EDARSAHUB_JOB_STALE_SECONDS", "180"))
STAMP = STATE / "last_health_publish_epoch"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(args, cwd=ROOT):
    return subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def git(*args, cwd=ROOT, check=True):
    result = run(["git", *args], cwd)
    if check and result.returncode:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{result.stdout[-800:]}")
    return result


def age_seconds(path: Path) -> int:
    return max(0, int(time.time() - path.stat().st_mtime))


def public_rejection(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    return {
        "job_id": data.get("job_id") or path.stem,
        "state": "REJECTED",
        "age_seconds": age_seconds(path),
        "reasons": data.get("reasons") or ["REJECTION_DETAILS_UNAVAILABLE"],
        "summary_es": data.get("summary_es") or "La orden fue rechazada por las reglas del worker.",
    }


def queue_jobs() -> list[dict]:
    pending = STATE / "pending"
    processing = STATE / "processing"
    rejected = STATE / "rejected"
    done = STATE / "done"
    results = STATE / "results"

    result_ids = {p.stem for p in results.glob("*.json")} if results.exists() else set()
    rows: list[dict] = []

    for folder, state in ((pending, "PENDING"), (processing, "RUNNING")):
        if not folder.exists():
            continue
        for path in folder.glob("*.json"):
            if path.stem in result_ids:
                continue
            age = age_seconds(path)
            effective_state = "BLOCKED" if age >= STALE_SECONDS else state
            rows.append(
                {
                    "job_id": path.stem,
                    "state": effective_state,
                    "age_seconds": age,
                    "reason": (
                        "El worker no termino esta orden dentro del tiempo esperado."
                        if effective_state == "BLOCKED"
                        else None
                    ),
                }
            )

    if rejected.exists():
        rows.extend(public_rejection(path) for path in rejected.glob("*.json"))

    if done.exists():
        for path in done.glob("*.json"):
            if path.stem in result_ids:
                continue
            rows.append(
                {
                    "job_id": path.stem,
                    "state": "DONE_LOCAL",
                    "age_seconds": age_seconds(path),
                    "reason": "El trabajo termino localmente; falta confirmar/publicar su resultado en GitHub.",
                }
            )

    if results.exists():
        for path in results.glob("*.json"):
            rows.append(
                {
                    "job_id": path.stem,
                    "state": "RESULT_READY",
                    "age_seconds": age_seconds(path),
                    "reason": None,
                }
            )

    return sorted(rows, key=lambda row: (row["state"], row["job_id"]))


def payload() -> dict:
    head = git("rev-parse", "HEAD").stdout.strip()
    jobs = queue_jobs()
    return {
        "schema": "edarsahub.worker-health.v2",
        "generated_at_utc": now(),
        "worker": "ONLINE",
        "development_sha": head,
        "branch": git("branch", "--show-current").stdout.strip(),
        "queue_pending": sum(j["state"] == "PENDING" for j in jobs),
        "queue_running": sum(j["state"] == "RUNNING" for j in jobs),
        "queue_blocked": sum(j["state"] == "BLOCKED" for j in jobs),
        "queue_rejected": sum(j["state"] == "REJECTED" for j in jobs),
        "queue_done_local": sum(j["state"] == "DONE_LOCAL" for j in jobs),
        "queue_result_ready": sum(j["state"] == "RESULT_READY" for j in jobs),
        "jobs": jobs,
        "summary_es": "El worker esta activo. Este estado muestra ordenes pendientes, trabajando, bloqueadas, rechazadas y terminadas para que el recorrido pueda comprobarse desde GitHub.",
        "production_touched": False,
    }


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    last = (
        int(STAMP.read_text().strip())
        if STAMP.exists() and STAMP.read_text().strip().isdigit()
        else 0
    )
    if int(time.time()) - last < MIN_INTERVAL:
        print("WORKER_HEALTH_PUBLISH=SKIPPED_INTERVAL")
        return 0

    git("fetch", REMOTE, BRANCH)
    base = git("rev-parse", f"{REMOTE}/{BRANCH}").stdout.strip()
    if WT.exists():
        shutil.rmtree(WT, ignore_errors=True)

    WT.parent.mkdir(parents=True, exist_ok=True)

    origin_url = git("remote", "get-url", REMOTE).stdout.strip()

    run(
        [
            "git",
            "clone",
            "--quiet",
            "--no-checkout",
            origin_url,
            str(WT),
        ],
        ROOT,
    )

    if not WT.is_dir():
        raise RuntimeError(
            "HEALTH_WORKTREE_NOT_CREATED: temporary clone failed"
        )

    git("checkout", "--detach", base, cwd=WT)
    try:
        dst = WT / "worker_queue" / "status" / "latest.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(
            json.dumps(payload(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        git("add", "--", str(dst.relative_to(WT)), cwd=WT)
        if git("diff", "--cached", "--quiet", cwd=WT, check=False).returncode == 0:
            STAMP.write_text(str(int(time.time())))
            print("WORKER_HEALTH_PUBLISH=NO_CHANGE")
            return 0
        git(
            "-c",
            "user.name=EDARSAHUB Worker",
            "-c",
            "user.email=worker@edarsahub.local",
            "commit",
            "-m",
            "worker-health: publish runtime heartbeat",
            cwd=WT,
        )
        commit = git("rev-parse", "HEAD", cwd=WT).stdout.strip()
        git("fetch", REMOTE, BRANCH)
        if git("rev-parse", f"{REMOTE}/{BRANCH}").stdout.strip() != base:
            raise RuntimeError("QUEUE_BRANCH_MOVED")
        push_env = os.environ.copy()
        push_env["EDARSA_ALLOW_PUSH"] = "1"
        push = subprocess.run(
            ["git", "push", REMOTE, f"{commit}:refs/heads/{BRANCH}"],
            cwd=str(WT),
            env=push_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if push.returncode:
            raise RuntimeError(f"HEALTH_PUSH_FAILED:{push.stdout[-800:]}")
        STAMP.write_text(str(int(time.time())))
        print(f"WORKER_HEALTH_PUBLISHED={commit}")
    finally:
        shutil.rmtree(WT, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
