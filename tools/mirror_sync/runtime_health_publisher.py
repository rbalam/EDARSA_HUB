#!/usr/bin/env python3
"""Publica salud operativa de la cola universal sin perder evidencia historica."""
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
HEALTH_BRANCH = os.environ.get(
    "EDARSAHUB_HEALTH_BRANCH",
    "worker/health",
)
MIN_INTERVAL = int(os.environ.get("EDARSAHUB_HEARTBEAT_SECONDS", "60"))
STALE_SECONDS = int(os.environ.get("EDARSAHUB_JOB_STALE_SECONDS", "180"))
TERMINAL_RETENTION_SECONDS = int(
    os.environ.get("EDARSAHUB_HEALTH_TERMINAL_RETENTION_SECONDS", "3600")
)
STAMP = STATE / "last_health_publish_epoch"
RUNTIME = STATE / "runtime"


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


def read_text(path: Path) -> str | None:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    return value or None


def terminal_visible(path: Path) -> bool:
    return age_seconds(path) <= TERMINAL_RETENTION_SECONDS


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


def directory_ids(name: str) -> set[str]:
    folder = STATE / name
    if not folder.exists():
        return set()
    return {path.stem for path in folder.glob("*.json")}


def queue_jobs() -> list[dict]:
    pending = STATE / "pending"
    processing = STATE / "processing"
    rejected = STATE / "rejected"
    done = STATE / "done"
    results = STATE / "results"

    result_ids = directory_ids("results")
    processing_ids = directory_ids("processing")
    pending_ids = directory_ids("pending")
    rows: list[dict] = []

    # Estados activos siempre se muestran. PROCESSING tiene precedencia sobre
    # PENDING para evitar duplicados transitorios durante movimientos atomicos.
    if processing.exists():
        for path in processing.glob("*.json"):
            if path.stem in result_ids:
                continue
            age = age_seconds(path)
            effective_state = "BLOCKED" if age >= STALE_SECONDS else "RUNNING"
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

    if pending.exists():
        for path in pending.glob("*.json"):
            if path.stem in result_ids or path.stem in processing_ids:
                continue
            age = age_seconds(path)
            effective_state = "BLOCKED" if age >= STALE_SECONDS else "PENDING"
            rows.append(
                {
                    "job_id": path.stem,
                    "state": effective_state,
                    "age_seconds": age,
                    "reason": (
                        "El worker no reclamo esta orden dentro del tiempo esperado."
                        if effective_state == "BLOCKED"
                        else None
                    ),
                }
            )

    # Los terminales son observabilidad reciente, no historial infinito.
    # El JSON original permanece en disco/worker_queue para auditoria.
    if rejected.exists():
        for path in rejected.glob("*.json"):
            if path.stem in result_ids or not terminal_visible(path):
                continue
            rows.append(public_rejection(path))

    if done.exists():
        for path in done.glob("*.json"):
            if (
                path.stem in result_ids
                or path.stem in processing_ids
                or path.stem in pending_ids
                or not terminal_visible(path)
            ):
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
            if not terminal_visible(path):
                continue
            rows.append(
                {
                    "job_id": path.stem,
                    "state": "RESULT_READY",
                    "age_seconds": age_seconds(path),
                    "reason": None,
                }
            )

    return sorted(rows, key=lambda row: (row["state"], row["job_id"]))


def history_summary() -> dict[str, int]:
    return {
        "pending_total_local": len(directory_ids("pending")),
        "processing_total_local": len(directory_ids("processing")),
        "done_total_local": len(directory_ids("done")),
        "rejected_total_local": len(directory_ids("rejected")),
        "results_total_local": len(directory_ids("results")),
    }


def runtime_summary() -> dict[str, str | None]:
    return {
        "pid": read_text(RUNTIME / "pid"),
        "generation": read_text(RUNTIME / "generation"),
        "last_cycle_utc": read_text(RUNTIME / "last_cycle_utc"),
        "last_receive_utc": read_text(RUNTIME / "last_receive_utc"),
        "current_job_id": read_text(RUNTIME / "current_job_id"),
        "last_terminal_utc": read_text(RUNTIME / "last_terminal_utc"),
    }


def payload() -> dict:
    head = git("rev-parse", "HEAD").stdout.strip()
    jobs = queue_jobs()
    active = [job for job in jobs if job["state"] in {"PENDING", "RUNNING", "BLOCKED"}]
    pending_only = [job for job in jobs if job["state"] == "PENDING"]
    oldest_pending_age = max((int(job.get("age_seconds") or 0) for job in pending_only), default=0)
    intake_sla_seconds = 30
    return {
        "schema": "edarsahub.worker-health.v3",
        "generated_at_utc": now(),
        "worker": "ONLINE",
        "development_sha": head,
        "branch": git("branch", "--show-current").stdout.strip(),
        "queue_pending": sum(j["state"] == "PENDING" for j in jobs),
        "queue_depth": len(active),
        "oldest_pending_age_seconds": oldest_pending_age,
        "intake_sla_seconds": intake_sla_seconds,
        "intake_sla_breached": oldest_pending_age > intake_sla_seconds,
        "queue_running": sum(j["state"] == "RUNNING" for j in jobs),
        "queue_blocked": sum(j["state"] == "BLOCKED" for j in jobs),
        "queue_rejected_recent": sum(j["state"] == "REJECTED" for j in jobs),
        "queue_done_local_recent": sum(j["state"] == "DONE_LOCAL" for j in jobs),
        "queue_result_ready_recent": sum(j["state"] == "RESULT_READY" for j in jobs),
        "terminal_retention_seconds": TERMINAL_RETENTION_SECONDS,
        "jobs": jobs,
        "history": history_summary(),
        "runtime": runtime_summary(),
        "summary_es": (
            "Estado operativo del worker. Los trabajos activos siempre se muestran; "
            "los terminales se muestran solo durante la ventana de retencion. La evidencia "
            "historica permanece conservada fuera de latest.json."
        ),
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

    git("fetch", REMOTE, HEALTH_BRANCH)
    base = git("rev-parse", f"{REMOTE}/{HEALTH_BRANCH}").stdout.strip()

    WT = Path(tempfile.mkdtemp(prefix="edarsahub-worker-health-publish-"))
    shutil.rmtree(WT, ignore_errors=True)
    origin_url = git("remote", "get-url", REMOTE).stdout.strip()
    clone = run(["git", "clone", "--quiet", "--no-checkout", origin_url, str(WT)], ROOT)
    if clone.returncode != 0 or not WT.is_dir():
        raise RuntimeError(f"HEALTH_WORKTREE_NOT_CREATED:{clone.stdout[-800:]}")

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
            "worker-health: publish operational runtime heartbeat",
            cwd=WT,
        )
        commit = git("rev-parse", "HEAD", cwd=WT).stdout.strip()
        git("fetch", REMOTE, HEALTH_BRANCH)
        if git("rev-parse", f"{REMOTE}/{HEALTH_BRANCH}").stdout.strip() != base:
            raise RuntimeError("QUEUE_BRANCH_MOVED")
        push_env = os.environ.copy()
        push_env["EDARSA_ALLOW_PUSH"] = "1"
        push = subprocess.run(
            ["git", "push", REMOTE, f"{commit}:refs/heads/{HEALTH_BRANCH}"],
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
