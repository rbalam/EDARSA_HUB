#!/usr/bin/env python3
"""Autonomous control plane for the EDARSAHUB universal worker.

This process is intentionally independent from the deterministic job executor.
It repairs recoverable runtime/control-plane failures without routing the repair
through the same job/claim path that may be unhealthy.

Safety invariants:
- never touches Production;
- never force-pushes;
- never destroys local changes (dirty state is stashed before safe FF only);
- Agent Guard orphan claims are quarantined, never deleted;
- live PIDs are always preserved;
- stale processing jobs are requeued only after a conservative grace period.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
GIT = ROOT / ".git"
STATE = GIT / "universal-worker-queue"
RUNTIME = STATE / "runtime"
PROCESSING = STATE / "processing"
PENDING = STATE / "pending"
RESULTS = STATE / "results"
REJECTED = STATE / "rejected"
PUBLISHED = STATE / "published"
AGENT_GUARD = GIT / "agent-guard"
AGENT_QUARANTINE = GIT / "agent-guard-quarantine"
AUDIT = STATE / "control-plane-audit.jsonl"
STATUS = RUNTIME / "control_plane_status.json"
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
DEV_BRANCH = "Edarsahub_Desarrollo"
INTERVAL = int(os.environ.get("EDARSAHUB_CONTROL_PLANE_INTERVAL", "15"))
HEARTBEAT_STALE = int(os.environ.get("EDARSAHUB_WORKER_HEARTBEAT_STALE_SECONDS", "60"))
CLAIM_GRACE = int(os.environ.get("EDARSAHUB_AGENT_CLAIM_GRACE_SECONDS", "90"))
PROCESSING_GRACE = int(os.environ.get("EDARSAHUB_PROCESSING_REQUEUE_SECONDS", "120"))
WORKER_SERVICE = os.environ.get("EDARSAHUB_UNIVERSAL_WORKER_SERVICE", "edarsahub-universal-worker")
EXPECTED_GENERATION_RE = re.compile(r'^RUNTIME_GENERATION="([^"]+)"', re.MULTILINE)
PID_RE = re.compile(r'(?i)["\']?pid["\']?\s*[:=]\s*["\']?(\d+)')
WORKER_TOKEN_RE = re.compile(r"worker-[A-Za-z0-9._-]{3,160}")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch() -> float:
    return time.time()


def run(args: list[str], timeout: int = 30, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"COMMAND_FAILED:{args}:{result.stdout[-1500:]}")
    return result


def audit(event: str, **fields: Any) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    payload = {"at_utc": utc_now(), "event": event, **fields, "production_touched": False}
    with AUDIT.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def pid_alive(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def parse_iso_age(value: str) -> float | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return max(0.0, epoch() - dt.timestamp())
    except ValueError:
        return None


def expected_generation() -> str:
    script = ROOT / "tools" / "mirror_sync" / "universal_job_worker.sh"
    match = EXPECTED_GENERATION_RE.search(read_text(script))
    return match.group(1) if match else ""


def request_universal_restart(reason: str) -> bool:
    env_name = (
        os.environ.get("EDARSA_ENV")
        or os.environ.get("APP_ENV")
        or os.environ.get("ENVIRONMENT")
        or "PREVIEW"
    ).upper()
    if "PROD" in env_name:
        audit("UNIVERSAL_RESTART_BLOCKED_PRODUCTION_ENV", reason=reason, environment=env_name)
        return False
    result = run(["supervisorctl", "restart", WORKER_SERVICE], timeout=30)
    ok = result.returncode == 0
    audit(
        "UNIVERSAL_RESTART_REQUESTED",
        reason=reason,
        service=WORKER_SERVICE,
        ok=ok,
        output=result.stdout[-1000:],
    )
    return ok


def heal_runtime_generation_and_heartbeat() -> dict[str, Any]:
    expected = expected_generation()
    actual = read_text(RUNTIME / "generation")
    pid_raw = read_text(RUNTIME / "pid")
    pid = int(pid_raw) if pid_raw.isdigit() else 0
    receive = read_text(RUNTIME / "last_receive_utc")
    receive_age = parse_iso_age(receive)

    generation_stale = bool(expected and actual != expected)
    heartbeat_stale = receive_age is None or receive_age > HEARTBEAT_STALE
    pid_dead = not pid_alive(pid)

    if generation_stale or heartbeat_stale or pid_dead:
        reason = ",".join(
            name
            for name, active in (
                ("GENERATION_STALE", generation_stale),
                ("HEARTBEAT_STALE", heartbeat_stale),
                ("PID_DEAD", pid_dead),
            )
            if active
        )
        request_universal_restart(reason)

    return {
        "expected_generation": expected,
        "actual_generation": actual,
        "pid": pid,
        "pid_alive": not pid_dead,
        "last_receive_utc": receive or None,
        "last_receive_age_seconds": receive_age,
        "runtime_repair_needed": generation_stale or heartbeat_stale or pid_dead,
    }


def git_output(*args: str) -> str:
    result = run(["git", *args], timeout=45)
    if result.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{args}:{result.stdout[-1200:]}")
    return result.stdout.strip()


def preserve_and_fast_forward() -> dict[str, Any]:
    """Converge only when remote is a strict FF and local has no unique commits."""
    try:
        run(["git", "fetch", "--quiet", REMOTE, DEV_BRANCH], timeout=60, check=True)
        branch = git_output("branch", "--show-current")
        if branch != DEV_BRANCH:
            return {"ff": "SKIP_WRONG_BRANCH", "branch": branch}
        local = git_output("rev-parse", "HEAD")
        remote = git_output("rev-parse", f"{REMOTE}/{DEV_BRANCH}")
        if local == remote:
            return {"ff": "ALREADY_ALIGNED", "local": local}
        counts = git_output("rev-list", "--left-right", "--count", f"HEAD...{REMOTE}/{DEV_BRANCH}").split()
        local_ahead, remote_ahead = (int(counts[0]), int(counts[1]))
        if local_ahead != 0 or remote_ahead <= 0:
            return {"ff": "SKIP_NON_FF", "local_ahead": local_ahead, "remote_ahead": remote_ahead}

        dirty = run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            timeout=20,
        ).stdout.strip()
        stash_ref = None
        if dirty:
            audit("FAST_FORWARD_DEFERRED_LOCAL_DIRTY")
            return {"ff": "DEFER_LOCAL_DIRTY"}

        ff = run(["git", "merge", "--ff-only", f"{REMOTE}/{DEV_BRANCH}"], timeout=60)
        if ff.returncode != 0:
            audit("FAST_FORWARD_FAILED", output=ff.stdout[-1200:], stash=stash_ref)
            return {"ff": "FAILED", "stash": stash_ref}
        new_head = git_output("rev-parse", "HEAD")
        audit("FAST_FORWARD_APPLIED", from_sha=local, to_sha=new_head)
        return {"ff": "APPLIED", "from": local, "to": new_head}
    except Exception as exc:
        audit("FAST_FORWARD_EXCEPTION", error=str(exc))
        return {"ff": "ERROR", "error": str(exc)}


def claim_candidates() -> list[Path]:
    if not AGENT_GUARD.is_dir():
        return []
    candidates: list[Path] = []
    for path in AGENT_GUARD.rglob("*"):
        if not path.is_file():
            continue
        lowered = "/".join(part.lower() for part in path.parts)
        if not any(token in lowered for token in ("claim", "claims", "lock", "locks")):
            continue
        try:
            if path.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue
        text = read_text(path)
        if WORKER_TOKEN_RE.search(path.name) or WORKER_TOKEN_RE.search(text):
            candidates.append(path)
    return candidates


def reconcile_agent_guard_orphans() -> dict[str, int]:
    live = recent = quarantined = 0
    now_ts = epoch()
    for path in claim_candidates():
        try:
            age = now_ts - path.stat().st_mtime
        except OSError:
            continue
        text = read_text(path)
        pids = {int(value) for value in PID_RE.findall(text)}
        if any(pid_alive(pid) for pid in pids):
            live += 1
            continue
        if age < CLAIM_GRACE:
            recent += 1
            continue
        try:
            rel = path.relative_to(AGENT_GUARD)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
            destination = AGENT_QUARANTINE / stamp / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(destination))
            quarantined += 1
            audit(
                "AGENT_GUARD_ORPHAN_QUARANTINED",
                source=str(path),
                destination=str(destination),
                age_seconds=int(age),
                pids=sorted(pids),
            )
        except Exception as exc:
            audit("AGENT_GUARD_QUARANTINE_FAILED", source=str(path), error=str(exc))
    return {"live": live, "recent": recent, "quarantined": quarantined}


def requeue_stale_processing() -> int:
    PENDING.mkdir(parents=True, exist_ok=True)
    PROCESSING.mkdir(parents=True, exist_ok=True)
    REJECTED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    requeued = 0
    for path in PROCESSING.glob("*.json"):
        try:
            age = epoch() - path.stat().st_mtime
        except OSError:
            continue
        if age < PROCESSING_GRACE:
            continue
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            audit("STALE_PROCESSING_INVALID_ENVELOPE", job_file=path.name, error=str(exc))
            continue
        retry_count = int(envelope.get("_worker_stale_requeue_count") or 0)
        if retry_count >= 1:
            job = envelope.get("job") if isinstance(envelope.get("job"), dict) else {}
            job_id = str(job.get("job_id") or path.stem)
            completed = utc_now()
            result = {
                "schema": "edarsahub.worker-result.v2",
                "job_id": job_id,
                "status": "BLOCKED",
                "quality_gate": "FAIL",
                "certification": "NOT_CERTIFIED",
                "percent_complete": 0,
                "production_touched": False,
                "blockers": ["processing_stale_after_single_requeue"],
                "completed_at_utc": completed,
                "summary_es": "El job excedio el SLA de processing despues de un unico reintento seguro y fue cerrado terminalmente para no bloquear la cola."
            }
            atomic_json(RESULTS / path.name, result)
            os.replace(path, REJECTED / path.name)
            (RUNTIME / "last_terminal_utc").write_text(completed + "\n", encoding="utf-8")
            audit("STALE_PROCESSING_TERMINATED", job_file=path.name, age_seconds=int(age))
            continue
        target = PENDING / path.name
        if target.exists():
            continue
        envelope["_worker_stale_requeue_count"] = retry_count + 1
        atomic_json(path, envelope)
        os.replace(path, target)
        requeued += 1
        audit("STALE_PROCESSING_REQUEUED", job_file=path.name, age_seconds=int(age), retry_count=retry_count + 1)
    return requeued


def cycle() -> dict[str, Any]:
    ff = preserve_and_fast_forward()
    runtime = heal_runtime_generation_and_heartbeat()
    claims = reconcile_agent_guard_orphans()
    requeued = requeue_stale_processing()
    payload = {
        "schema": "edarsahub.worker-control-plane.v1",
        "at_utc": utc_now(),
        "ff": ff,
        "runtime": runtime,
        "agent_guard": claims,
        "stale_processing_requeued": requeued,
        "production_touched": False,
    }
    atomic_json(STATUS, payload)
    return payload


def main() -> int:
    once = "--once" in os.sys.argv
    while True:
        try:
            payload = cycle()
            print("CONTROL_PLANE_STATE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        except Exception as exc:
            audit("CONTROL_PLANE_CYCLE_EXCEPTION", error=str(exc))
            print(f"CONTROL_PLANE_ERROR={exc}", flush=True)
        if once:
            return 0
        time.sleep(max(5, INTERVAL))


if __name__ == "__main__":
    raise SystemExit(main())
