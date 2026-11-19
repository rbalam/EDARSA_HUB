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


def diagnose_capability_failure(
    *,
    capability_code: str,
    registered_capabilities: tuple[str, ...] | list[str] | set[str],
    loaded_capabilities: tuple[str, ...] | list[str] | set[str],
    runtime_aligned: bool,
    error_code: str = "",
) -> dict[str, Any]:
    """Differentiate capability, runtime drift, contract, request, RBAC, context, and transient errors.

    Never misclassifies INVALID_ARGUMENT as stale runtime.
    """
    code = str(capability_code or "").strip().upper()
    err = str(error_code or "").strip().upper()
    reg = {str(c).strip().upper() for c in registered_capabilities if str(c).strip()}
    loaded = {str(c).strip().upper() for c in loaded_capabilities if str(c).strip()}

    if any(tok in err for tok in ("RBAC", "INSUFFICIENT_SCOPE", "FORBIDDEN", "UNAUTHORIZED", "ACCESS_DENIED")):
        classification = "RBAC_INSUFFICIENT"
        requires_runtime_recovery = False
    elif any(tok in err for tok in ("BOUNDED_CONTEXT", "CONTEXT_INVALID")):
        classification = "CONTEXT_INVALID"
        requires_runtime_recovery = False
    elif any(tok in err for tok in ("CONSTRAINTS_UNSUPPORTED", "MODE_MISMATCH", "SCHEMA", "CONTRACT")):
        classification = "CONTRACT_INCOMPATIBLE"
        requires_runtime_recovery = False
    elif any(tok in err for tok in ("INVALID_ARGUMENT", "INVALID_JOB_ID", "JOB_ID_INVALID", "OBJECTIVE_REQUIRED", "VALIDATION_ERROR")):
        classification = "INVALID_REQUEST"
        requires_runtime_recovery = False
    elif any(tok in err for tok in ("TIMEOUT", "CONNECTION", "LOCK_BUSY", "TEMPORARY", "TRANSIENT")):
        classification = "TRANSIENT_ERROR"
        requires_runtime_recovery = False
    elif code and code in reg and code not in loaded:
        classification = "CAPABILITY_NOT_LOADED_STALE_RUNTIME"
        requires_runtime_recovery = True
    elif code and code not in reg:
        classification = "CAPABILITY_UNKNOWN"
        requires_runtime_recovery = False
    elif not runtime_aligned:
        classification = "RUNTIME_STALE"
        requires_runtime_recovery = True
    else:
        classification = "HEALTHY_OR_UNCLASSIFIED"
        requires_runtime_recovery = False

    return {
        "capability_code": code,
        "error_code": err,
        "classification": classification,
        "requires_runtime_recovery": requires_runtime_recovery,
        "in_registered_catalog": code in reg if code else False,
        "in_loaded_runtime": code in loaded if code else False,
        "runtime_aligned": bool(runtime_aligned),
        "production_touched": False,
    }


def build_mcp_runtime_convergence_report(
    *,
    loaded_capabilities: tuple[str, ...] | list[str] | set[str] | None = None,
) -> dict[str, Any]:
    """Read-only convergence snapshot across Git HEAD, Worker runtime, Python import tree, and MCP catalog."""
    import sys

    fp = build_runtime_fingerprint()

    def _safe_rev(ref: str) -> str | None:
        try:
            val = _git("rev-parse", ref).lower()
            return val if _SHA_RE.fullmatch(val) else None
        except RuntimeFingerprintError:
            return None

    remote_dev_sha = _safe_rev(f"origin/{DEV_BRANCH}")
    worker_health_sha = _safe_rev("origin/worker/health")
    head_aligned = bool(remote_dev_sha and fp["development_sha"] == remote_dev_sha)

    try:
        from modules.worker_ingress.semantic_capabilities import registered_capabilities as _reg_caps

        registered = tuple(sorted(_reg_caps()))
    except Exception:
        registered = ()

    loaded = (
        tuple(sorted({str(c).strip().upper() for c in loaded_capabilities if str(c).strip()}))
        if loaded_capabilities is not None
        else registered
    )
    missing_in_runtime = sorted(set(registered) - set(loaded))
    catalog_aligned = len(missing_in_runtime) == 0

    overall_converged = bool(
        head_aligned
        and fp["worker_code_tree_aligned"]
        and fp["generation_aligned"]
        and catalog_aligned
    )
    if overall_converged:
        recommended_action = "NONE"
    elif not head_aligned:
        recommended_action = "ALIGN_HEAD_FIRST"
    else:
        recommended_action = "RECOVER_PREVIEW_RUNTIME"

    return {
        "schema": "edarsahub.worker-runtime-convergence.v1",
        "branch": fp["branch"],
        "local_head": fp["development_sha"],
        "remote_development_head": remote_dev_sha,
        "head_aligned": head_aligned,
        "worker_code_tree_sha": fp["worker_code_tree_sha"],
        "active_worker_code_tree_sha": fp["active_worker_code_tree_sha"],
        "worker_code_tree_aligned": fp["worker_code_tree_aligned"],
        "expected_generation": fp["expected_generation"],
        "actual_generation": fp["actual_generation"],
        "generation_aligned": fp["generation_aligned"],
        "worker_health_ref": worker_health_sha,
        "python_executable": sys.executable,
        "pythonpath": os.environ.get("PYTHONPATH", ""),
        "virtual_env": os.environ.get("VIRTUAL_ENV", ""),
        "import_root": str(ROOT),
        "registered_capabilities": list(registered),
        "loaded_capabilities": list(loaded),
        "missing_in_runtime": missing_in_runtime,
        "catalog_aligned": catalog_aligned,
        "overall_converged": overall_converged,
        "recommended_action": recommended_action,
        "recovery_script": "tools/bootstrap/recover_preview_runtime.sh",
        "production_touched": False,
    }
