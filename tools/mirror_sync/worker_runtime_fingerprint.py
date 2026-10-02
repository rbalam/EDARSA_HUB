"""Canonical runtime fingerprint for the EDARSAHUB Universal Worker.

This module is read-only. It computes identity and capability evidence from
the local Preview repository and runtime markers. It never mutates Git,
restarts services, touches databases, or touches Production.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
RUNTIME = ROOT / ".git" / "universal-worker-queue" / "runtime"
DEV_BRANCH = "Edarsahub_Desarrollo"
WORKER_TREE_SPEC = "HEAD:tools/mirror_sync"
WORKER_SCRIPT = ROOT / "tools" / "mirror_sync" / "universal_job_worker.sh"
ACTIVE_WORKER_TREE = RUNTIME / "active_worker_code_tree_sha"
GENERATION_FILE = RUNTIME / "generation"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_GENERATION_RE = re.compile(r'^RUNTIME_GENERATION="([^"]+)"', re.MULTILINE)

REQUIRED_CAPABILITIES = (
    "canonical_git_guard_refresh",
    "runtime_code_tree_identity",
    "runtime_generation_identity",
    "worker_heartbeat",
    "startup_selfheal",
    "wake_proof",
    "production_fail_closed",
)


class RuntimeFingerprintError(RuntimeError):
    pass


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if completed.returncode != 0:
        raise RuntimeFingerprintError("RUNTIME_FINGERPRINT_GIT_FAILED")
    return completed.stdout.strip()


def _read(path: Path) -> str | None:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def expected_generation() -> str | None:
    source = _read(WORKER_SCRIPT)
    if not source:
        return None
    match = _GENERATION_RE.search(source)
    return match.group(1) if match else None


def build_runtime_fingerprint() -> dict[str, Any]:
    branch = _git("branch", "--show-current")
    development_sha = _git("rev-parse", "HEAD").lower()
    worker_code_tree_sha = _git("rev-parse", WORKER_TREE_SPEC).lower()

    if branch != DEV_BRANCH:
        raise RuntimeFingerprintError("RUNTIME_FINGERPRINT_WRONG_BRANCH")
    if not _SHA_RE.fullmatch(development_sha):
        raise RuntimeFingerprintError("RUNTIME_FINGERPRINT_HEAD_INVALID")
    if not _SHA_RE.fullmatch(worker_code_tree_sha):
        raise RuntimeFingerprintError("RUNTIME_FINGERPRINT_WORKER_TREE_INVALID")

    active_worker_code_tree_sha = (_read(ACTIVE_WORKER_TREE) or "").lower() or None
    if active_worker_code_tree_sha and not _SHA_RE.fullmatch(active_worker_code_tree_sha):
        raise RuntimeFingerprintError("RUNTIME_FINGERPRINT_ACTIVE_TREE_INVALID")

    expected = expected_generation()
    actual = _read(GENERATION_FILE)

    return {
        "schema": "edarsahub.worker-runtime-fingerprint.v1",
        "branch": branch,
        "development_sha": development_sha,
        "worker_code_tree_sha": worker_code_tree_sha,
        "active_worker_code_tree_sha": active_worker_code_tree_sha,
        "worker_code_tree_aligned": active_worker_code_tree_sha == worker_code_tree_sha,
        "expected_generation": expected,
        "actual_generation": actual,
        "generation_aligned": bool(expected and actual == expected),
        "required_capabilities": list(REQUIRED_CAPABILITIES),
        "production_touched": False,
    }
