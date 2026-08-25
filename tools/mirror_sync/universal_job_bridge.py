#!/usr/bin/env python3
"""Universal GitHub queue bridge for the EDARSAHUB worker.

The queue lives in the dedicated `worker/requests` branch. This program only
receives and validates jobs and materializes them locally for the dispatcher.
It deliberately does not execute arbitrary shell supplied by a request.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
PENDING = STATE / "pending"
PROCESSING = STATE / "processing"
REJECTED = STATE / "rejected"
DONE = STATE / "done"
RESULTS = STATE / "results"
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
QUEUE_BRANCH = os.environ.get("EDARSAHUB_QUEUE_BRANCH", "worker/requests")
SCHEMA = "edarsahub.worker-job.v1"
JOB_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")

# Only explicit destructive instructions are rejected by text inspection.
# Production access is governed by the structured fail-closed field
# `production_allowed`, so phrases such as "NO tocar Produccion" remain valid.
FORBIDDEN_COMMAND_PATTERNS = (
    re.compile(r"\bforce[ -]?push\b", re.IGNORECASE),
    re.compile(r"\bgit\s+push\b[^\n]*(?:--force|-f)\b", re.IGNORECASE),
    re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
    re.compile(r"\bgit\s+clean\s+-[A-Za-z]*f", re.IGNORECASE),
)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def ensure_dirs() -> None:
    for path in (PENDING, PROCESSING, REJECTED, DONE, RESULTS):
        path.mkdir(parents=True, exist_ok=True)


def validate(job: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(job, dict):
        return ["JOB_NOT_OBJECT"]
    if job.get("schema") != SCHEMA:
        errors.append("INVALID_SCHEMA")
    job_id = str(job.get("job_id") or "")
    if not JOB_ID.fullmatch(job_id):
        errors.append("INVALID_JOB_ID")
    if job.get("target_repo") != "rbalam/EDARSA_HUB":
        errors.append("INVALID_TARGET_REPO")
    if job.get("target_branch") != "Edarsahub_Desarrollo":
        errors.append("INVALID_TARGET_BRANCH")
    if job.get("production_allowed") is not False:
        errors.append("PRODUCTION_MUST_BE_FALSE")
    if not str(job.get("objective") or "").strip():
        errors.append("OBJECTIVE_REQUIRED")
    if job.get("human_summary_language") != "es":
        errors.append("SUMMARY_LANGUAGE_MUST_BE_ES")

    raw = json.dumps(job, ensure_ascii=False)
    if any(pattern.search(raw) for pattern in FORBIDDEN_COMMAND_PATTERNS):
        errors.append("FORBIDDEN_DESTRUCTIVE_OPERATION_REQUESTED")
    return errors


def queue_files() -> list[str]:
    git("fetch", "--quiet", REMOTE, QUEUE_BRANCH)
    listing = git(
        "ls-tree",
        "-r",
        "--name-only",
        f"{REMOTE}/{QUEUE_BRANCH}",
        "worker_queue/inbox",
    )
    return [
        line.strip()
        for line in listing.stdout.splitlines()
        if line.strip().startswith("worker_queue/inbox/")
        and line.strip().endswith(".json")
    ]


def read_remote(path: str) -> str:
    return git("show", f"{REMOTE}/{QUEUE_BRANCH}:{path}").stdout


def already_claimed(name: str) -> bool:
    return any((folder / name).exists() for folder in (PENDING, PROCESSING, DONE, REJECTED))


def write_rejection(source: str, reason: list[str], raw: str = "") -> None:
    name = Path(source).name
    payload = {
        "schema": "edarsahub.worker-rejection.v1",
        "job_id": Path(source).stem,
        "source": source,
        "status": "REJECTED",
        "reasons": reason,
        "summary_es": "El worker recibio la orden, pero la rechazo porque no cumple las reglas de seguridad o formato. Consulta 'reasons' para conocer el motivo exacto.",
        "received_at_utc": datetime.now(timezone.utc).isoformat(),
        "production_touched": False,
    }
    (REJECTED / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    # Raw payload remains local for diagnosis and is never published by health.
    if raw:
        (REJECTED / f"{name}.raw").write_text(raw, encoding="utf-8")


def receive() -> int:
    ensure_dirs()
    accepted = rejected = skipped = 0
    for path in queue_files():
        name = Path(path).name
        if already_claimed(name):
            skipped += 1
            continue
        raw = read_remote(path)
        try:
            job = json.loads(raw)
        except json.JSONDecodeError:
            write_rejection(path, ["INVALID_JSON"], raw)
            rejected += 1
            continue
        errors = validate(job)
        if errors:
            write_rejection(path, errors, raw)
            rejected += 1
            continue
        envelope = {
            "received_at_utc": datetime.now(timezone.utc).isoformat(),
            "queue_branch": QUEUE_BRANCH,
            "queue_path": path,
            "job": job,
        }
        (PENDING / name).write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        accepted += 1
    print(f"UNIVERSAL_QUEUE_ACCEPTED={accepted}")
    print(f"UNIVERSAL_QUEUE_REJECTED={rejected}")
    print(f"UNIVERSAL_QUEUE_SKIPPED={skipped}")
    return 0


def status() -> int:
    ensure_dirs()
    print(f"UNIVERSAL_QUEUE_PENDING={len(list(PENDING.glob('*.json')))}")
    print(f"UNIVERSAL_QUEUE_PROCESSING={len(list(PROCESSING.glob('*.json')))}")
    print(f"UNIVERSAL_QUEUE_REJECTED={len(list(REJECTED.glob('*.json')))}")
    print(f"UNIVERSAL_QUEUE_DONE={len(list(DONE.glob('*.json')))}")
    print(f"UNIVERSAL_QUEUE_RESULTS={len(list(RESULTS.glob('*.json')))}")
    return 0


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "receive"
    if command == "receive":
        return receive()
    if command == "status":
        return status()
    print("usage: universal_job_bridge.py [receive|status]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
