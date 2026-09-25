#!/usr/bin/env python3
"""Deterministic dispatcher for EDARSAHUB ChatGPT-controlled worker jobs.

ChatGPT decides the exact repository changes and sends them as structured
``edarsahub.worker-job.v2`` actions. This dispatcher applies only those actions,
runs only allow-listed validations, verifies the exact changed-file scope,
creates one commit, and integrates it into ``Edarsahub_Desarrollo``.

No secondary AI executor is called. No shell command supplied by a job is ever
executed.
"""

from __future__ import annotations

# WORKER_DELIVERABLE_IMPORT_COMPAT_V1
try:
    from tools.mirror_sync.worker_deliverable_contract import evaluate_deliverables, materialize_deliverables, normalize_deliverable_specs, normalize_required_deliverables
except ModuleNotFoundError:
    from worker_deliverable_contract import evaluate_deliverables, materialize_deliverables, normalize_deliverable_specs, normalize_required_deliverables

import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from worker_concurrency import evaluate_scope_advance
from worker_scheduling import normalize_metadata
from worker_slot_runtime import create_slot, reclaim_stale_slot, release_slot, update_slot_state
from git_divergence_guard import (GitGuardError, acquire_writer_lock, compare_and_swap, inspect_repository, mutation_policy, post_push_verify, recover_authorized_local_ahead, release_writer_lock, requires_writer_lock, scoped_push_env, validate_commit_scope)

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
PENDING = STATE / "pending"
PROCESSING = STATE / "processing"
DONE = STATE / "done"
REJECTED = STATE / "rejected"
RESULTS = STATE / "results"
RUNTIME = STATE / "runtime"
WORKTREES = Path(os.environ.get("EDARSAHUB_JOB_WORKTREES", "/tmp/edarsahub-worker-jobs"))
LOCK_FILE = STATE / "dispatcher.lock"
PREFERRED_JOB_PATH = RUNTIME / "preferred_job.json"
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
DEV_BRANCH = "Edarsahub_Desarrollo"
MAX_SECONDS = int(os.environ.get("EDARSAHUB_JOB_MAX_SECONDS", "1800"))
MAX_CONCURRENCY_REPLAY_ATTEMPTS = int(os.environ.get("EDARSAHUB_CONCURRENCY_REPLAY_ATTEMPTS", "3"))
JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")
ALLOWED_ACTIONS = {"replace_text", "write_file", "delete_file"}
ALLOWED_CHECKS = {"git_diff_check", "py_compile", "pytest", "frontend_build", "sql_readonly_audit", "repository_contract_audit"}
READ_ONLY_MODE = "READ_ONLY"
READ_ONLY_CHECKS = {"git_diff_check", "py_compile", "pytest", "sql_readonly_audit", "repository_contract_audit"}
SOFTRESTAURANT_FULL_HISTORY_MODE = "SOFTRESTAURANT_FULL_HISTORY_RESYNC"
MPRO_FULL_HISTORY_MODE = "MPRO_FULL_HISTORY_RESYNC"
COMERCIAL_RANGE_RESYNC_MODE = "COMERCIAL_RANGE_RESYNC"
ISCAM_DETAIL_BACKFILL_MODE = "ISCAM_DETAIL_BACKFILL"
ISCAM_PAYMENTS_ONLY_RESYNC_MODE = "ISCAM_PAYMENTS_ONLY_RESYNC"
SQL_MIGRATION_DEVELOPMENT_MODE = "SQL_MIGRATION_DEVELOPMENT"
FRONTEND_BUILD_CERTIFICATION_MODE = "FRONTEND_BUILD_CERTIFICATION"
UNIT_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SOFTRESTAURANT_RESYNC_MAX_SECONDS = int(os.environ.get("EDARSAHUB_SOFTRESTAURANT_RESYNC_MAX_SECONDS", "21600"))

RUNTIME_PYTHON = Path("/root/.venv/bin/python")


def resolve_canonical_python() -> str:
    repo_python = ROOT / ".venv" / "bin" / "python"
    repo_venv_config = ROOT / ".venv" / "pyvenv.cfg"
    if repo_venv_config.is_file() and repo_python.is_file() and os.access(repo_python, os.X_OK):
        return str(repo_python)
    if RUNTIME_PYTHON.is_file() and os.access(RUNTIME_PYTHON, os.X_OK):
        return str(RUNTIME_PYTHON)
    return sys.executable


PYTHON_BIN = resolve_canonical_python()


def load_backend_runtime_env() -> dict[str, str]:
    env_file = ROOT / "backend" / ".env"
    loaded: dict[str, str] = {}
    if not env_file.is_file():
        return loaded
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        if key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        loaded[key] = value
    return loaded


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def summarize_softrestaurant_output(output: str) -> dict[str, Any]:
    summary: dict[str, Any] = {"results": []}
    for raw_line in reversed((output or "").splitlines()):
        try:
            payload = json.loads(raw_line)
        except Exception:
            continue
        if not isinstance(payload, dict) or payload.get("event") != "summary":
            continue
        rows = payload.get("results") or []
        if not isinstance(rows, list):
            return summary
        sanitized = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            error_domains = []
            error_types = []
            errors = row.get("errors") or []
            if isinstance(errors, list):
                for error in errors:
                    if isinstance(error, dict):
                        domain = str(error.get("domain") or "").strip()
                        if domain:
                            error_domains.append(domain)
                        value = error.get("error")
                        error_types.append(type(value).__name__)
                    elif isinstance(error, str):
                        error_types.append(error.split(":", 1)[0][:80])
            sanitized.append({
                "unidad": str(row.get("unidad") or ""),
                "status": str(row.get("status") or ""),
                "payment_windows": int(row.get("payment_windows") or 0),
                "corte_windows": int(row.get("corte_windows") or 0),
                "pagos_insertados": int(row.get("pagos_insertados") or 0),
                "error_domains": sorted(set(error_domains)),
                "error_types": sorted(set(error_types)),
            })
        return {"results": sanitized}
    return summary


def summarize_iscam_detail_backfill_output(output: str) -> dict[str, Any]:
    summary: dict[str, Any] = {"unidades": []}
    for raw_line in reversed((output or "").splitlines()):
        try:
            payload = json.loads(raw_line)
        except Exception:
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("unidades"), list):
            continue
        units = []
        for unit in payload.get("unidades") or []:
            if not isinstance(unit, dict):
                continue
            days = []
            for day in unit.get("dias") or []:
                if not isinstance(day, dict):
                    continue
                days.append({
                    key: day.get(key)
                    for key in (
                        "fecha_operacion", "status",
                        "ventas_runtime", "ventas_pos", "delta_ventas",
                        "tickets_runtime", "tickets_pos", "delta_tickets",
                        "pax_runtime", "pax_pos", "delta_pax",
                        "filas_insertadas", "error_type", "error_code",
                    )
                    if key in day
                })
            units.append({
                "unidad": str(unit.get("unidad") or ""),
                "ya_ok": int(unit.get("ya_ok") or 0),
                "candidatos": int(unit.get("candidatos") or 0),
                "reparables": int(unit.get("reparables") or 0),
                "bloqueados": int(unit.get("bloqueados") or 0),
                "sin_runtime": int(unit.get("sin_runtime") or 0),
                "filas_insertadas": int(unit.get("filas_insertadas") or 0),
                "dias": days,
            })
        return {
            "modo": str(payload.get("modo") or ""),
            "fecha_inicio": str(payload.get("fecha_inicio") or ""),
            "fecha_fin_exclusivo": str(payload.get("fecha_fin_exclusivo") or ""),
            "dias_evaluados": int(payload.get("dias_evaluados") or 0),
            "dias_ya_ok": int(payload.get("dias_ya_ok") or 0),
            "dias_candidatos": int(payload.get("dias_candidatos") or 0),
            "dias_reparables": int(payload.get("dias_reparables") or 0),
            "dias_bloqueados": int(payload.get("dias_bloqueados") or 0),
            "dias_sin_runtime": int(payload.get("dias_sin_runtime") or 0),
            "filas_insertadas": int(payload.get("filas_insertadas") or 0),
            "unidades": units,
        }
    return summary


def run(args: list[str], cwd: Path | None = None, check: bool = False, timeout: int | None = None, env_extra: dict[str, str] | None = None):
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(args, cwd=str(cwd or ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check, timeout=timeout, env=env)


def git(*args: str, cwd: Path | None = None, check: bool = True):
    result = run(["git", *args], cwd=cwd, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{result.stdout[-2000:]}")
    return result


def git_changed_paths(base_sha: str, head_sha: str) -> list[str]:
    result = git("diff", "--name-only", base_sha, head_sha, "--")
    return sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})


def git_is_ancestor(base_sha: str, head_sha: str) -> bool:
    return git("merge-base", "--is-ancestor", base_sha, head_sha, check=False).returncode == 0


def resolve_repository_credential_helper() -> str:
    result = git("config", "--local", "--get", "credential.helper", cwd=ROOT, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def ensure_dirs() -> None:
    for path in (PENDING, PROCESSING, DONE, REJECTED, RESULTS, WORKTREES):
        path.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def load_envelope(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("job"), dict):
        raise ValueError("INVALID_PENDING_ENVELOPE")
    return data


def safe_path(worktree: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or (rel.parts and rel.parts[0] == ".git"):
        raise ValueError(f"UNSAFE_PATH:{relative}")
    target = (worktree / rel).resolve()
    root = worktree.resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"PATH_ESCAPES_WORKTREE:{relative}")
    return target


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_expected_hash(path: Path, action: dict[str, Any]) -> None:
    expected = action.get("expected_sha256")
    if expected is None:
        return
    if not path.is_file():
        raise RuntimeError(f"EXPECTED_FILE_MISSING:{action['path']}")
    actual = sha256_file(path)
    if actual != expected:
        raise RuntimeError(f"EXPECTED_SHA256_MISMATCH:{action['path']}:{actual}")


def prepare_worktree(job_id: str, base_sha: str, allowed_paths: list[str]) -> tuple[Path, str]:
    safe_id = re.sub(r"[^A-Za-z0-9._-]", "-", job_id)
    branch = f"agent/worker/{safe_id}"
    path = WORKTREES / safe_id
    agent_id = f"worker-{safe_id}"
    if path.exists():
        git("worktree", "remove", "--force", str(path), check=False)
        shutil.rmtree(path, ignore_errors=True)
    git("branch", "-D", branch, check=False)
    git("branch", branch, base_sha)
    guard = ROOT / ".git" / "agent-guard" / "bin" / "agent_guard.py"
    if not guard.is_file():
        raise RuntimeError("AGENT_GUARD_NOT_FOUND")
    if not allowed_paths:
        raise RuntimeError("AGENT_GUARD_PATHS_REQUIRED")
    command = [PYTHON_BIN, str(guard), "worktree-create", "--agent-id", agent_id, "--task-id", safe_id, "--description", f"ChatGPT deterministic worker job {job_id}", "--domain", f"worker_job_{safe_id}", "--branch", branch, "--directory", str(path)]
    for allowed_path in allowed_paths:
        command.extend(["--path", allowed_path])
    created = run(command, cwd=ROOT)
    if created.returncode != 0:
        raise RuntimeError(f"AGENT_GUARD_WORKTREE_CREATE_FAILED:{created.stdout[-2000:]}")
    if not path.is_dir():
        raise RuntimeError("AGENT_GUARD_WORKTREE_NOT_CREATED")
    head = git("rev-parse", "HEAD", cwd=path).stdout.strip()
    if head != base_sha:
        raise RuntimeError(f"WORKTREE_BASE_MISMATCH:expected={base_sha}:actual={head}")
    return path, branch


def apply_action(worktree: Path, action: dict[str, Any]) -> str:
    kind = str(action.get("type"))
    if kind not in ALLOWED_ACTIONS:
        raise ValueError(f"UNSUPPORTED_ACTION:{kind}")
    relative = str(action.get("path") or "")
    target = safe_path(worktree, relative)
    repo_path = Path(relative)
    if (
        kind == "write_file"
        and repo_path.parts[:2] == ("backend", "core")
        and not target.exists()
    ):
        raise RuntimeError(f"CORE_GROWTH_FORBIDDEN:{relative}")
    verify_expected_hash(target, action)
    if kind == "replace_text":
        if not target.is_file():
            raise RuntimeError(f"REPLACE_TARGET_MISSING:{relative}")
        old = action["old"]
        new = action["new"]
        expected_count = int(action.get("expected_count", 1))
        text = target.read_text(encoding="utf-8")
        actual_count = text.count(old)
        if actual_count != expected_count:
            raise RuntimeError(f"REPLACE_COUNT_MISMATCH:{relative}:expected={expected_count}:actual={actual_count}")
        target.write_text(text.replace(old, new), encoding="utf-8")
        return relative
    if kind == "write_file":
        content = action["content"]
        if target.exists():
            if "expected_sha256" not in action:
                raise RuntimeError(f"WRITE_EXISTING_REQUIRES_EXPECTED_SHA256:{relative}")
            current_size = target.stat().st_size
            new_size = len(content.encode("utf-8"))
            if current_size >= 4096 and new_size < int(current_size * 0.75):
                raise RuntimeError(f"WRITE_FILE_LARGE_SHRINK_BLOCKED:{relative}:current={current_size}:new={new_size}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return relative
    if kind == "delete_file":
        if not target.is_file():
            raise RuntimeError(f"DELETE_TARGET_MISSING:{relative}")
        target.unlink()
        return relative
    raise ValueError(f"UNSUPPORTED_ACTION:{kind}")


def run_check(worktree: Path, check: dict[str, Any], readonly: bool = False) -> dict[str, Any]:
    kind = str(check.get("type"))
    started = now()
    env_extra: dict[str, str] = {}
    if kind == "git_diff_check":
        cmd = ["git", "diff", "--check"]
        cwd = worktree
    elif kind == "py_compile":
        paths = [str(p) for p in check.get("paths") or []]
        cmd = [PYTHON_BIN, "-m", "py_compile", *paths]
        cwd = worktree
        if readonly:
            env_extra["PYTHONPYCACHEPREFIX"] = str(Path(tempfile.gettempdir()) / "edarsahub-worker-readonly-pyc")
    elif kind == "pytest":
        backend = worktree / "backend"
        if not backend.is_dir():
            raise RuntimeError("PYTEST_BACKEND_NOT_FOUND")
        paths = []
        for raw_path in check.get("paths") or []:
            path = str(raw_path)
            if path == "backend":
                path = "."
            elif path.startswith("backend/"):
                path = path[len("backend/"):]
            paths.append(path)
        pytest_args = ["-q"]
        if readonly:
            pytest_args.extend(["-p", "no:cacheprovider"])
        cmd = [PYTHON_BIN, "-m", "pytest", *pytest_args, *paths]
        cwd = backend
        python_path = os.pathsep.join(
            (
                str(backend),
                str(worktree),
            )
        )
        env_extra = {
            **load_backend_runtime_env(),
            "PYTHONPATH": python_path,
        }
        if readonly:
            env_extra["PYTHONDONTWRITEBYTECODE"] = "1"
    elif kind == "repository_contract_audit":
        helper = worktree / "tools" / "mirror_sync" / "repository_contract_audit.py"
        if not helper.is_file():
            helper = ROOT / "tools" / "mirror_sync" / "repository_contract_audit.py"
        cmd = [PYTHON_BIN, str(helper), "--request-json", json.dumps(check.get("request") or {}, ensure_ascii=False)]
        cwd = worktree
        env_extra = {"PYTHONDONTWRITEBYTECODE": "1"}
    elif kind == "sql_readonly_audit":
        helper = worktree / "tools" / "mirror_sync" / "sql_readonly_audit.py"
        if not helper.is_file():
            helper = ROOT / "tools" / "mirror_sync" / "sql_readonly_audit.py"
        backend = worktree / "backend"
        if not backend.is_dir():
            backend = ROOT / "backend"
        cmd = [PYTHON_BIN, str(helper), "--queries-json", json.dumps(check.get("queries") or [], ensure_ascii=False)]
        source = str(check.get("source") or "EDARSAHUB").strip().upper()
        cmd.extend(["--source", source])
        if check.get("units") is not None:
            cmd.extend(["--units-json", json.dumps(check.get("units"), ensure_ascii=False)])
        if check.get("system_types") is not None:
            cmd.extend(["--system-types-json", json.dumps(check.get("system_types"), ensure_ascii=False)])
        cwd = worktree
        env_extra = {**load_backend_runtime_env(), "PYTHONPATH": str(backend)}
    elif kind == "frontend_build":
        directory = safe_path(worktree, str(check.get("directory", "frontend")))
        canonical_node_modules = ROOT / "frontend" / "node_modules"
        canonical_bin = canonical_node_modules / ".bin"
        env_extra = {}
        if canonical_node_modules.is_dir():
            env_extra["NODE_PATH"] = str(canonical_node_modules)
        if canonical_bin.is_dir():
            current_path = os.environ.get("PATH", "")
            env_extra["PATH"] = f"{canonical_bin}:{current_path}" if current_path else str(canonical_bin)
        cmd = ["yarn", "build"]
        cwd = directory
    else:
        raise ValueError(f"UNSUPPORTED_CHECK:{kind}")
    try:
        result = run(cmd, cwd=cwd, timeout=MAX_SECONDS, env_extra=env_extra or None)
        full_output = result.stdout or ""
        response = {"type": kind, "status": "PASS" if result.returncode == 0 else "FAIL", "returncode": result.returncode, "started_at_utc": started, "completed_at_utc": now(), "output": full_output[-12000:]}
        if kind in {"sql_readonly_audit", "repository_contract_audit"}:
            try:
                structured_evidence = json.loads(full_output.strip())
            except (json.JSONDecodeError, TypeError):
                structured_evidence = None
            if isinstance(structured_evidence, dict):
                if kind == "sql_readonly_audit":
                    response["sql_evidence"] = structured_evidence
                else:
                    response["repository_evidence"] = structured_evidence
        return response
    except subprocess.TimeoutExpired as exc:
        text = exc.stdout if isinstance(exc.stdout, str) else ""
        return {"type": kind, "status": "FAIL", "returncode": 124, "started_at_utc": started, "completed_at_utc": now(), "output": f"TIMEOUT\n{text[-8000:]}"}


def changed_files(worktree: Path, base_sha: str) -> list[str]:
    result = git("diff", "--name-only", base_sha, "--", cwd=worktree)
    staged_or_untracked = git("status", "--porcelain=v1", "--untracked-files=all", cwd=worktree).stdout.splitlines()
    names = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    for line in staged_or_untracked:
        if len(line) >= 4:
            name = line[3:]
            if " -> " in name:
                name = name.split(" -> ", 1)[1]
            names.add(name)
    return sorted(names)


def validate_scope(worktree: Path, base_sha: str, allowed: set[str]) -> list[str]:
    actual = set(changed_files(worktree, base_sha)); extra = sorted(actual - allowed); missing = sorted(allowed - actual); blockers: list[str] = []
    if extra or missing: blockers.append("GIT_SCOPE_VIOLATION:extra=" + ",".join(extra) + ";missing=" + ",".join(missing))
    return blockers


def create_commit(worktree: Path, job_id: str, files: list[str]) -> str:
    git("add", "--", *files, cwd=worktree)
    staged = git("diff", "--cached", "--name-only", cwd=worktree).stdout.splitlines()
    if sorted(staged) != sorted(files):
        raise RuntimeError("STAGED_SCOPE_MISMATCH")
    message = f"worker({job_id}): apply ChatGPT deterministic changes"
    git("-c", "user.name=EDARSAHUB Worker", "-c", "user.email=worker@edarsahub.local", "commit", "-m", message, cwd=worktree)
    return git("rev-parse", "HEAD", cwd=worktree).stdout.strip()


def integrate(worktree: Path, branch: str, head: str, base_sha: str, write_scope: set[str], job_id: str, remote_at_start: str) -> tuple[bool, str, str, list[dict[str, Any]]]:
    candidate=head; evidence=[]; credential_helper=resolve_repository_credential_helper()
    if not credential_helper: return False,"GIT_PUSH_FAILED:credential_helper_missing",candidate,evidence
    step={"candidate_base_sha":base_sha,"candidate_sha_before":candidate,"remote_at_start":remote_at_start,"push_attempted":False}
    try: remote_dev=compare_and_swap(ROOT,remote_at_start)
    except GitGuardError as exc:
        step["decision"]=exc.code; step.update(exc.evidence); evidence.append(step); return False,exc.code,candidate,evidence
    step["remote_before_push"]=remote_dev
    if remote_dev != base_sha: step["decision"]="GIT_DIVERGENCE_BLOCKED"; evidence.append(step); return False,"GIT_DIVERGENCE_BLOCKED:base_no_longer_remote_tip",candidate,evidence
    merge_base=git("merge-base",remote_dev,candidate,check=False).stdout.strip(); step["merge_base_before_push"]=merge_base
    if merge_base != remote_dev: step["decision"]="GIT_DIVERGENCE_BLOCKED"; evidence.append(step); return False,"GIT_DIVERGENCE_BLOCKED:candidate_not_fast_forward",candidate,evidence
    try: validate_commit_scope(worktree,base_sha,candidate,write_scope)
    except GitGuardError as exc:
        step["decision"]=exc.code; step["scope_evidence"]=exc.evidence; evidence.append(step); return False,exc.code,candidate,evidence
    guard=ROOT/"scripts"/"agent_guardrails"/"validate_repository_artifacts.py"
    if guard.is_file():
        check=run([PYTHON_BIN,str(guard),"--range",base_sha,candidate],cwd=ROOT)
        if check.returncode != 0: step["artifact_guard"]="FAIL"; step["artifact_guard_output"]=check.stdout[-1000:]; evidence.append(step); return False,"GIT_SCOPE_VIOLATION:repository_artifact_guard_failed",candidate,evidence
        step["artifact_guard"]="PASS"
    push_env=scoped_push_env(job_id,"universal-worker",os.environ); push=run(["git","-c","credential.helper=","-c",f"credential.helper={credential_helper}","push",REMOTE,f"{candidate}:refs/heads/{DEV_BRANCH}"],cwd=ROOT,env_extra={k:push_env[k] for k in ("EDARSA_ALLOW_PUSH","EDARSA_PUSH_JOB_ID","EDARSA_PUSH_OWNER")})
    step["push_attempted"]=True; step["push_returncode"]=push.returncode; step["push_result"]="PASS" if push.returncode==0 else "FAIL"
    if push.returncode != 0: step["push_output"]=(push.stdout or "")[-1000:]; step["decision"]="GIT_PUSH_FAILED"; evidence.append(step); return False,"GIT_PUSH_FAILED",candidate,evidence
    try: post=post_push_verify(worktree,candidate)
    except GitGuardError as exc:
        step["decision"]=exc.code; step.update(exc.evidence); evidence.append(step); return False,exc.code,candidate,evidence
    step.update(post); step["decision"]="CERTIFIED_GIT_SYNC"; evidence.append(step); return True,candidate,candidate,evidence


def release_agent_guard_claim(job_id: str) -> tuple[bool, str]:
    safe_id = re.sub(r"[^A-Za-z0-9._-]", "-", job_id)
    agent_id = f"worker-{safe_id}"
    guard = ROOT / ".git" / "agent-guard" / "bin" / "agent_guard.py"
    if not guard.is_file():
        return False, "AGENT_GUARD_NOT_FOUND"
    released = run([PYTHON_BIN, str(guard), "release", "--agent-id", agent_id], cwd=ROOT)
    if released.returncode != 0:
        return False, released.stdout[-1000:]
    return True, released.stdout[-1000:]


def process_one(path: Path, *, already_claimed: bool = False) -> int:
    envelope = load_envelope(path)
    job = envelope["job"]
    job_id = str(job.get("job_id") or "")
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("INVALID_JOB_ID")
    processing = path if already_claimed else PROCESSING / path.name
    if already_claimed:
        if path.parent != PROCESSING:
            raise ValueError("CLAIMED_JOB_NOT_IN_PROCESSING")
    else:
        os.replace(path, processing)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    (RUNTIME / "current_job_id").write_text(job_id + "\n", encoding="utf-8")
    result: dict[str, Any] = {"schema": "edarsahub.worker-result.v2", "job_id": job_id, "started_at_utc": now(), "status": "BLOCKED", "executor": "chatgpt-deterministic", "production_touched": False, "blockers": [], "summary_es": "El worker recibio una orden exacta de ChatGPT y la proceso sin pedir instrucciones a otra inteligencia artificial."}

    if "required_deliverables" in job:
        result["required_deliverables"] = list(
            normalize_required_deliverables(
                job.get("required_deliverables")
            )
        )
        result["deliverables"] = {}
        result["missing_deliverables"] = list(
            result["required_deliverables"]
        )

        if "deliverable_specs" in job:
            result["deliverable_specs"] = (
                normalize_deliverable_specs(
                    job.get("deliverable_specs"),
                    job.get("required_deliverables"),
                )
            )
    worktree: Path | None = None
    branch = ""
    agent_guard_claim_created = False
    git_writer_lock: dict[str, Any] | None = None
    slot_id: str | None = None
    try:
        if job.get("schema") != "edarsahub.worker-job.v2":
            raise ValueError("UNSUPPORTED_JOB_SCHEMA")

        requested_paths = sorted({str(action.get("path")) for action in (job.get("actions") or []) if action.get("path")})
        mode = str(job.get("mode") or "")
        scheduling = normalize_metadata(job)
        slot_class = "READ_ONLY" if mode in {READ_ONLY_MODE, "READ_ONLY_SQL", FRONTEND_BUILD_CERTIFICATION_MODE} else "MUTATION"
        slot_id = "readonly-1" if slot_class == "READ_ONLY" else "mutation-1"
        result["slot_recovery"] = reclaim_stale_slot(
            slot_id,
            heartbeat_stale_seconds=90,
        )
        create_slot(
            slot_id=slot_id,
            slot_class=slot_class,
            job_id=job_id,
            mode=mode,
            project_id=scheduling.project_id,
            bounded_context=scheduling.bounded_context,
            resource_claims=list(scheduling.resource_claims),
            conflict_domains=list(scheduling.conflict_domains),
            worker_pid=os.getpid(),
            execution_pid=os.getpid(),
            legacy_defaults=scheduling.legacy_defaults,
        )
        update_slot_state(slot_id, "RUNNING", execution_pid=os.getpid())
        result["slot_id"] = slot_id
        result["slot_class"] = slot_class
        result["parallel_execution_enabled"] = False
        git_mutating = requires_writer_lock(mode)
        if mode in {READ_ONLY_MODE, "READ_ONLY_SQL", FRONTEND_BUILD_CERTIFICATION_MODE}:
            current_head = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
        elif git_mutating:
            try:
                git_writer_lock = acquire_writer_lock(ROOT, job_id=job_id, owner="universal-worker", owner_pid=os.getpid())
            except GitGuardError as exc:
                result["status"] = exc.code; result["git_guard_error"] = exc.evidence; raise RuntimeError(exc.code) from exc
            git_state = inspect_repository(ROOT, fetch=True)
            result.update({"git_guard_start":git_state,"branch":git_state["current_branch"],"remote_at_start":git_state["remote_head"],"local_at_start":git_state["local_head"],"merge_base_at_start":git_state["merge_base"],"ahead_at_start":git_state["ahead_count"],"behind_at_start":git_state["behind_count"],"dirty_state":{"worktree_dirty":git_state["worktree_dirty"],"staged_count":git_state["staged_count"],"unstaged_count":git_state["unstaged_count"],"untracked_count":git_state["untracked_count"]},"lock_owner":{k:git_writer_lock.get(k) for k in ("job_id","owner","owner_pid","created_at_utc")}})
            if git_state["classification"] == "LOCAL_AHEAD_ONLY":
                try:
                    result["local_ahead_recovery"] = recover_authorized_local_ahead(ROOT, git_state, job_id=job_id, owner="universal-worker")
                    git_state = inspect_repository(ROOT, fetch=True)
                except GitGuardError as exc:
                    result["status"] = exc.code
                    result["git_guard_error"] = exc.evidence
                    raise RuntimeError(exc.code) from exc
            git_policy = mutation_policy(git_state)
            if not git_policy["allowed"]:
                result["status"] = git_policy["terminal_status"]; result["git_guard_reason"] = git_policy["reason"]; raise RuntimeError(git_policy["reason"])
            current_head = git_state["remote_head"]
        else:
            git("fetch", REMOTE, DEV_BRANCH); current_head = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
        expected_base = str(job.get("base_sha") or "").strip() or None
        pickup_policy: dict[str, Any]
        if expected_base and expected_base != current_head:
            if not git_is_ancestor(expected_base, current_head):
                raise RuntimeError(f"BASE_NOT_ANCESTOR:expected={expected_base}:actual={current_head}")
            changed = git_changed_paths(expected_base, current_head)
            pickup_policy = evaluate_scope_advance(expected_base, current_head, requested_paths, changed, allow_empty_scope_advance=(mode in {"READ_ONLY_SQL", READ_ONLY_MODE, FRONTEND_BUILD_CERTIFICATION_MODE}))
            if pickup_policy["decision"] not in {"SAFE_REPLAY", "EXACT_BASE"}:
                conflicts = ",".join(pickup_policy.get("scope_conflicts") or [])
                raise RuntimeError(f"CONCURRENT_SCOPE_CONFLICT:expected={expected_base}:actual={current_head}:paths={conflicts}")
        else:
            pickup_policy = evaluate_scope_advance(expected_base, current_head, requested_paths, [], allow_empty_scope_advance=(mode in {"READ_ONLY_SQL", READ_ONLY_MODE, FRONTEND_BUILD_CERTIFICATION_MODE}))
        base_sha = current_head
        result["requested_base_sha"] = expected_base
        result["base_sha"] = base_sha
        result["initial_base_sha"] = expected_base or base_sha
        result["execution_base_sha"] = base_sha
        result["integration_attempts"] = 0
        result["concurrency_replays"] = 0
        result["concurrent_head_changes"] = []
        result["concurrency"] = {"pickup": pickup_policy, "integration": []}

        if mode == READ_ONLY_MODE:
            if job.get("actions") != []:
                raise RuntimeError("READ_ONLY_ACTIONS_MUST_BE_EMPTY_LIST")
            checks = job.get("checks") or []
            if not checks or any(not isinstance(c, dict) or c.get("type") not in READ_ONLY_CHECKS for c in checks):
                raise RuntimeError("READ_ONLY_ONLY_NON_MUTATING_CHECKS_ALLOWED")
            readonly_head_before = git("rev-parse", "HEAD", cwd=ROOT).stdout.strip()
            tracked_before = git("status", "--porcelain=v1", "--untracked-files=no", cwd=ROOT).stdout
            readonly_tracked_before = tracked_before
            check_results = []
            for check in checks:
                check_result = run_check(ROOT, check, readonly=True)
                check_results.append(check_result)
                if check_result["status"] != "PASS":
                    result["blockers"].append(f"check_failed:{check.get('type')}")
                    break
            readonly_head_after = git("rev-parse", "HEAD", cwd=ROOT).stdout.strip()
            tracked_after = git("status", "--porcelain=v1", "--untracked-files=no", cwd=ROOT).stdout
            readonly_tracked_after = tracked_after
            if tracked_after != tracked_before:
                result["readonly_mutation_evidence"] = {
                    "version": "r1",
                    "head_before": readonly_head_before,
                    "head_after": readonly_head_after,
                    "tracked_before": readonly_tracked_before,
                    "tracked_after": readonly_tracked_after,
                    "diff_names": git("diff", "--name-only", cwd=ROOT, check=False).stdout,
                    "diff_stat": git("diff", "--stat", cwd=ROOT, check=False).stdout,
                    "diff_porcelain": readonly_tracked_after,
                    "check_types": [str(c.get("type")) for c in checks if isinstance(c, dict)],
                    "cwd": str(ROOT),
                }
                result["blockers"].append("readonly_tracked_repo_mutation_detected")
            result["checks"] = check_results
            if (
                result.get("required_deliverables")
                and result.get("deliverable_specs")
            ):
                try:
                    result["deliverables"] = (
                        materialize_deliverables(
                            result.get(
                                "required_deliverables"
                            ),
                            result.get(
                                "deliverable_specs"
                            ),
                            check_results,
                        )
                    )
                except ValueError as exc:
                    result["blockers"].append(
                        "deliverable_materialization_failed:"
                        + str(exc)
                    )
            result["files_changed"] = []
            result["tests"] = "PASS" if check_results and all(x["status"] == "PASS" for x in check_results) else "FAIL"
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            result["work_completion"] = "COMPLETE" if not result["blockers"] else "INCOMPLETE"
            if result.get("required_deliverables"):
                deliverable_evaluation = evaluate_deliverables(
                    result.get("required_deliverables"),
                    result.get("deliverables"),
                )
                result["missing_deliverables"] = list(
                    deliverable_evaluation.missing
                )
                if not deliverable_evaluation.complete:
                    result["work_completion"] = "PENDING_DELIVERABLES"
            deliverables_complete = (
                not result.get("required_deliverables")
                or not result.get("missing_deliverables")
            )
            if not result["blockers"] and deliverables_complete:
                result["status"] = "READ_ONLY_COMPLETE"
                result["percent_complete"] = 100
                result["certification"] = "CERTIFIED_READ_ONLY"
                result["certification_basis"] = "NON_MUTATING_CHECKS_PLUS_DELIVERABLES"
                result["summary_es"] = "El Worker universal ejecuto exclusivamente checks genericos de solo lectura permitidos, materializo todos los entregables requeridos, no cambio archivos tracked y no toco Produccion."
            elif not result["blockers"]:
                result["status"] = "READ_ONLY_COMPLETE"
                result["percent_complete"] = 95
                result["certification"] = "PENDING_DELIVERABLES"
                result["work_completion"] = "PENDING_DELIVERABLES"
                result["summary_es"] = "Los checks de solo lectura terminaron, pero faltan entregables requeridos; el resultado no se certifica."
            else:
                result["percent_complete"] = 0
                result["certification"] = "NOT_CERTIFIED"
            return 0

        if mode == "READ_ONLY_SQL":
            if job.get("actions") not in (None, []):
                raise RuntimeError("READ_ONLY_SQL_ACTIONS_FORBIDDEN")
            checks = job.get("checks") or []
            if not checks or any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
                raise RuntimeError("READ_ONLY_SQL_ONLY_AUDIT_CHECKS_ALLOWED")
            check_results = []
            for check in checks:
                check_result = run_check(ROOT, check)
                check_results.append(check_result)
                if check_result["status"] != "PASS":
                    result["blockers"].append("check_failed:sql_readonly_audit")
                    break
            result["checks"] = check_results
            if (
                result.get("required_deliverables")
                and result.get("deliverable_specs")
            ):
                try:
                    result["deliverables"] = (
                        materialize_deliverables(
                            result.get(
                                "required_deliverables"
                            ),
                            result.get(
                                "deliverable_specs"
                            ),
                            check_results,
                        )
                    )
                except ValueError as exc:
                    result["blockers"].append(
                        "deliverable_materialization_failed:"
                        + str(exc)
                    )
            result["files_changed"] = []
            result["tests"] = "PASS" if check_results and all(x["status"] == "PASS" for x in check_results) else "FAIL"
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            if result.get("required_deliverables"):
                deliverable_evaluation = evaluate_deliverables(
                    result.get("required_deliverables"),
                    result.get("deliverables"),
                )
                result["missing_deliverables"] = list(
                    deliverable_evaluation.missing
                )
            else:
                deliverable_evaluation = None

            deliverables_complete = (
                deliverable_evaluation is None
                or deliverable_evaluation.complete
            )

            if not result["blockers"] and deliverables_complete:
                result["status"] = "READ_ONLY_COMPLETE"
                result["percent_complete"] = 100
                result["certification"] = "CERTIFIED_READ_ONLY"
                result["work_completion"] = "COMPLETE"
                result["summary_es"] = "El Worker universal ejecuto exclusivamente auditorias SQL de solo lectura mediante la conexion canonica HRLectura, materializo todos los entregables requeridos y no modifico repositorio, base ni Produccion."
            elif not result["blockers"]:
                result["status"] = "READ_ONLY_COMPLETE"
                result["percent_complete"] = 95
                result["certification"] = "PENDING_DELIVERABLES"
                result["work_completion"] = "PENDING_DELIVERABLES"
                result["summary_es"] = "Las auditorias SQL terminaron, pero faltan entregables requeridos; el resultado no se certifica."
            else:
                result["percent_complete"] = 0
                result["certification"] = "NOT_CERTIFIED"
            return 0

        if mode == FRONTEND_BUILD_CERTIFICATION_MODE:
            if job.get("actions") not in (None, []):
                raise RuntimeError("FRONTEND_BUILD_CERTIFICATION_ACTIONS_FORBIDDEN")
            checks = job.get("checks") or []
            allowed_frontend_cert_checks = {"frontend_build", "git_diff_check", "repository_contract_audit"}
            if not checks:
                raise RuntimeError("FRONTEND_BUILD_CERTIFICATION_CHECK_REQUIRED")
            if not any(isinstance(c, dict) and c.get("type") == "frontend_build" for c in checks):
                raise RuntimeError("FRONTEND_BUILD_CERTIFICATION_FRONTEND_BUILD_REQUIRED")
            if any(not isinstance(c, dict) or c.get("type") not in allowed_frontend_cert_checks for c in checks):
                raise RuntimeError("FRONTEND_BUILD_CERTIFICATION_ONLY_ALLOWED_CHECKS")
            status_before = git("status", "--porcelain=v1", "--untracked-files=all", cwd=ROOT).stdout
            check_results = []
            for check in checks:
                check_result = run_check(ROOT, check, readonly=True)
                check_results.append(check_result)
                if check_result["status"] != "PASS":
                    result["blockers"].append(f"check_failed:{check.get('type')}")
                    break
            status_after = git("status", "--porcelain=v1", "--untracked-files=all", cwd=ROOT).stdout
            if status_after != status_before:
                result["blockers"].append("frontend_build_certification_repo_mutation_detected")
            result["checks"] = check_results
            if (
                result.get("required_deliverables")
                and result.get("deliverable_specs")
            ):
                try:
                    result["deliverables"] = (
                        materialize_deliverables(
                            result.get(
                                "required_deliverables"
                            ),
                            result.get(
                                "deliverable_specs"
                            ),
                            check_results,
                        )
                    )
                except ValueError as exc:
                    result["blockers"].append(
                        "deliverable_materialization_failed:"
                        + str(exc)
                    )
            result["files_changed"] = []
            result["tests"] = "PASS" if check_results and all(x["status"] == "PASS" for x in check_results) else "FAIL"
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            result["work_completion"] = "COMPLETE" if not result["blockers"] else "INCOMPLETE"
            if not result["blockers"]:
                result["status"] = "FRONTEND_BUILD_CERTIFIED"
                result["percent_complete"] = 100
                result["certification"] = "CERTIFIED_FRONTEND_BUILD"
                result["certification_basis"] = "FRONTEND_BUILD_CERTIFICATION_NON_PRODUCT_MUTATING"
                result["summary_es"] = "El Worker universal ejecuto frontend_build como certificacion no mutante de frontend, sin acciones de producto, sin cambios tracked/untracked del repositorio y sin tocar Produccion."
            else:
                result["status"] = "FRONTEND_BUILD_FAILED"
                result["percent_complete"] = 0
                result["certification"] = "NOT_CERTIFIED"
            return 0

        if mode == COMERCIAL_RANGE_RESYNC_MODE:
            if expected_base and expected_base != current_head:
                raise RuntimeError(f"BASE_SHA_MISMATCH_OPERATIONAL_MODE:expected={expected_base}:actual={current_head}")
            if job.get("actions") not in (None, []):
                raise RuntimeError("COMERCIAL_RANGE_RESYNC_ACTIONS_FORBIDDEN")
            units = job.get("units", [])
            if not isinstance(units, list) or not units or len(units) > 32 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
                raise RuntimeError("COMERCIAL_RANGE_RESYNC_UNITS_INVALID")
            fecha_inicio = str(job.get("fecha_inicio") or "")
            fecha_fin = str(job.get("fecha_fin") or "")
            if not DATE_RE.fullmatch(fecha_inicio) or not DATE_RE.fullmatch(fecha_fin):
                raise RuntimeError("COMERCIAL_RANGE_RESYNC_DATES_INVALID")
            inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
            dias = (fin_dt - inicio_dt).days + 1
            if dias < 1 or dias > 31:
                raise RuntimeError("COMERCIAL_RANGE_RESYNC_DATE_RANGE_INVALID")
            dry_run = job.get("dry_run", True)
            if not isinstance(dry_run, bool):
                raise RuntimeError("COMERCIAL_RANGE_RESYNC_DRY_RUN_INVALID")
            if dry_run is False and job.get("confirm_comercial_range_resync") is not True:
                raise RuntimeError("COMERCIAL_RANGE_RESYNC_CONFIRMATION_REQUIRED")
            checks = job.get("checks") or []
            if not checks or any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
                raise RuntimeError("COMERCIAL_RANGE_RESYNC_SQL_AUDIT_REQUIRED")
            script = ROOT / "backend" / "scripts" / "resync_comercial_range_worker.py"
            if not script.is_file():
                raise RuntimeError("COMERCIAL_RANGE_RESYNC_SCRIPT_NOT_FOUND")

            normalized_units = [u.strip().upper() for u in units]
            backend = ROOT / "backend"
            unit_results = []
            operation_outputs = []
            failed_units = []

            for unit in normalized_units:
                cmd = [PYTHON_BIN, str(script), "--unidad", unit, "--fecha-inicio", fecha_inicio, "--fecha-fin", fecha_fin]
                if dry_run is False:
                    cmd.append("--commit")
                execution = run(
                    cmd,
                    cwd=ROOT,
                    timeout=SOFTRESTAURANT_RESYNC_MAX_SECONDS,
                    env_extra={**load_backend_runtime_env(), "PYTHONPATH": str(backend)},
                )
                summary = {}
                for raw_line in reversed((execution.stdout or "").splitlines()):
                    try:
                        candidate = json.loads(raw_line)
                    except Exception:
                        continue
                    if isinstance(candidate, dict) and candidate.get("event") == "comercial_range_summary":
                        summary = candidate
                        break
                unit_results.append({
                    "unidad": unit,
                    "returncode": execution.returncode,
                    "success": bool(summary.get("success")),
                    "header_success": bool(summary.get("header_success")),
                    "detail_success": bool(summary.get("detail_success")),
                    "records_processed": int(summary.get("records_processed") or 0),
                    "records_inserted": int(summary.get("records_inserted") or 0),
                    "records_updated": int(summary.get("records_updated") or 0),
                    "records_skipped": int(summary.get("records_skipped") or 0),
                    "records_errored": int(summary.get("records_errored") or 0),
                    "stage": summary.get("stage"),
                    "warning": str(summary.get("warning") or ""),
                })
                operation_outputs.append(f"===== {unit} =====\n{(execution.stdout or '')[-12000:]}")
                if execution.returncode != 0:
                    failed_units.append(unit)

            result["operation"] = COMERCIAL_RANGE_RESYNC_MODE
            result["dry_run"] = dry_run
            result["units"] = normalized_units
            result["canonical_sql_mutation"] = not dry_run
            result["operation_output"] = "\n".join(operation_outputs)[-40000:]
            result["operation_summary"] = {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "unidades": unit_results,
                "unidades_total": len(normalized_units),
                "unidades_ok": len(normalized_units) - len(failed_units),
                "unidades_fallidas": failed_units,
            }
            result["files_changed"] = []
            if failed_units:
                result["blockers"].append(
                    "comercial_range_resync_failed_units:" + ",".join(failed_units)
                )

            check_results = []
            if not result["blockers"]:
                for check in checks:
                    check_result = run_check(ROOT, check)
                    check_results.append(check_result)
                    if check_result["status"] != "PASS":
                        result["blockers"].append("check_failed:sql_readonly_audit")
                        break
            result["checks"] = check_results
            result["tests"] = "PASS" if not failed_units and check_results and all(x["status"] == "PASS" for x in check_results) else "FAIL"
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            if not result["blockers"]:
                result["status"] = "OPERATIONAL_COMPLETE"
                result["percent_complete"] = 100
                result["certification"] = "CERTIFIED_OPERATIONAL"
                result["summary_es"] = "El Worker ejecuto la re-sincronizacion comercial cerrada para todas las unidades y el rango autorizados usando el handler oficial; proceso cada sucursal de forma secuencial, valido header KPI y detalle ISCAM y certifico el bloque con SQL de solo lectura. No toco Produccion."
            else:
                result["status"] = "BLOCKED"
                result["percent_complete"] = int(100 * (len(normalized_units) - len(failed_units)) / len(normalized_units))
                result["certification"] = "NOT_CERTIFIED"
            return 0

        if mode == ISCAM_DETAIL_BACKFILL_MODE:
            if expected_base and expected_base != current_head:
                raise RuntimeError(f"BASE_SHA_MISMATCH_OPERATIONAL_MODE:expected={expected_base}:actual={current_head}")
            if job.get("actions") not in (None, []):
                raise RuntimeError("ISCAM_DETAIL_BACKFILL_ACTIONS_FORBIDDEN")
            units = job.get("units", [])
            if not isinstance(units, list) or not units or len(units) > 32 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
                raise RuntimeError("ISCAM_DETAIL_BACKFILL_UNITS_INVALID")
            fecha_inicio = str(job.get("fecha_inicio") or "")
            fecha_fin = str(job.get("fecha_fin") or "")
            if not DATE_RE.fullmatch(fecha_inicio) or not DATE_RE.fullmatch(fecha_fin):
                raise RuntimeError("ISCAM_DETAIL_BACKFILL_DATES_INVALID")
            inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
            if fin_dt <= inicio_dt:
                raise RuntimeError("ISCAM_DETAIL_BACKFILL_DATE_RANGE_INVALID")
            dry_run = job.get("dry_run", True)
            if not isinstance(dry_run, bool):
                raise RuntimeError("ISCAM_DETAIL_BACKFILL_DRY_RUN_INVALID")
            if dry_run is False and job.get("confirm_detail_backfill") is not True:
                raise RuntimeError("ISCAM_DETAIL_BACKFILL_CONFIRMATION_REQUIRED")
            checks = job.get("checks") or []
            if not checks or any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
                raise RuntimeError("ISCAM_DETAIL_BACKFILL_SQL_AUDIT_REQUIRED")
            script = ROOT / "backend" / "scripts" / "backfill_detalle_producto_pendientes.py"
            if not script.is_file():
                raise RuntimeError("ISCAM_DETAIL_BACKFILL_SCRIPT_NOT_FOUND")
            cmd = [PYTHON_BIN, str(script), "--fecha-inicio", fecha_inicio, "--fecha-fin", fecha_fin]
            for unit in units:
                cmd.extend(["--unidad", unit.strip().upper()])
            if dry_run is False:
                cmd.append("--commit")
            backend = ROOT / "backend"
            execution = run(cmd, cwd=ROOT, timeout=SOFTRESTAURANT_RESYNC_MAX_SECONDS, env_extra={**load_backend_runtime_env(), "PYTHONPATH": str(backend)})
            result["operation"] = ISCAM_DETAIL_BACKFILL_MODE
            result["dry_run"] = dry_run
            result["units"] = [u.strip().upper() for u in units]
            result["fecha_inicio"] = fecha_inicio
            result["fecha_fin"] = fecha_fin
            result["operation_output"] = execution.stdout[-20000:]
            result["operation_summary"] = summarize_iscam_detail_backfill_output(execution.stdout or "")
            result["files_changed"] = []
            if execution.returncode != 0:
                result["blockers"].append(f"iscam_detail_backfill_failed:rc={execution.returncode}")
            check_results = []
            if not result["blockers"]:
                for check in checks:
                    check_result = run_check(ROOT, check)
                    check_results.append(check_result)
                    if check_result["status"] != "PASS":
                        result["blockers"].append("check_failed:sql_readonly_audit")
                        break
            result["checks"] = check_results
            result["tests"] = "PASS" if check_results and all(x["status"] == "PASS" for x in check_results) else "FAIL"
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            if not result["blockers"]:
                result["status"] = "OPERATIONAL_COMPLETE"
                result["percent_complete"] = 100
                result["certification"] = "CERTIFIED_OPERATIONAL"
                result["summary_es"] = "El Worker ejecuto el backfill cerrado de detalle ISCAM para las unidades y fechas autorizadas y certifico el resultado con SQL de solo lectura. No acepto shell, rutas ni comandos externos y no toco Produccion."
            else:
                result["percent_complete"] = 0
                result["certification"] = "NOT_CERTIFIED"
            return 0

        if mode == ISCAM_PAYMENTS_ONLY_RESYNC_MODE:
            if expected_base and expected_base != current_head:
                raise RuntimeError(f"BASE_SHA_MISMATCH_OPERATIONAL_MODE:expected={expected_base}:actual={current_head}")
            if job.get("actions") not in (None, []):
                raise RuntimeError("ISCAM_PAYMENTS_ONLY_ACTIONS_FORBIDDEN")
            units = job.get("units", [])
            if not isinstance(units, list) or len(units) != 1 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
                raise RuntimeError("ISCAM_PAYMENTS_ONLY_EXACTLY_ONE_UNIT_REQUIRED")
            fecha_inicio = str(job.get("fecha_inicio") or "")
            fecha_fin = str(job.get("fecha_fin") or "")
            if not DATE_RE.fullmatch(fecha_inicio) or not DATE_RE.fullmatch(fecha_fin):
                raise RuntimeError("ISCAM_PAYMENTS_ONLY_DATES_INVALID")
            inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
            if fin_dt <= inicio_dt:
                raise RuntimeError("ISCAM_PAYMENTS_ONLY_DATE_RANGE_INVALID")
            dry_run = job.get("dry_run", True)
            if not isinstance(dry_run, bool):
                raise RuntimeError("ISCAM_PAYMENTS_ONLY_DRY_RUN_INVALID")
            if dry_run is False and job.get("confirm_payments_only_resync") is not True:
                raise RuntimeError("ISCAM_PAYMENTS_ONLY_CONFIRMATION_REQUIRED")
            checks = job.get("checks") or []
            if not checks or any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
                raise RuntimeError("ISCAM_PAYMENTS_ONLY_SQL_AUDIT_REQUIRED")
            script = ROOT / "backend" / "scripts" / "resync_iscam_pagos_unidad.py"
            if not script.is_file():
                raise RuntimeError("ISCAM_PAYMENTS_ONLY_SCRIPT_NOT_FOUND")
            unit = units[0].strip().upper()
            cmd = [PYTHON_BIN, str(script), "--unit", unit, "--fi", fecha_inicio, "--ff", fecha_fin]
            if dry_run is False:
                cmd.append("--execute")
            backend = ROOT / "backend"
            execution = run(cmd, cwd=ROOT, timeout=SOFTRESTAURANT_RESYNC_MAX_SECONDS, env_extra={**load_backend_runtime_env(), "PYTHONPATH": str(backend)})
            result["operation"] = ISCAM_PAYMENTS_ONLY_RESYNC_MODE
            result["dry_run"] = dry_run
            result["units"] = [unit]
            result["fecha_inicio"] = fecha_inicio
            result["fecha_fin"] = fecha_fin
            result["canonical_sql_mutation"] = not dry_run
            result["operation_output"] = execution.stdout[-20000:]
            result["files_changed"] = []
            if execution.returncode != 0:
                result["blockers"].append(f"iscam_payments_only_resync_failed:rc={execution.returncode}")
            check_results = []
            if not result["blockers"]:
                for check in checks:
                    check_result = run_check(ROOT, check)
                    check_results.append(check_result)
                    if check_result["status"] != "PASS":
                        result["blockers"].append("check_failed:sql_readonly_audit")
                        break
            result["checks"] = check_results
            result["tests"] = "PASS" if check_results and all(x["status"] == "PASS" for x in check_results) else "FAIL"
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            if not result["blockers"]:
                result["status"] = "OPERATIONAL_COMPLETE"
                result["percent_complete"] = 100
                result["certification"] = "CERTIFIED_OPERATIONAL"
                result["summary_es"] = "El Worker resincronizo exclusivamente Pagos por Ticket para una unidad y rango autorizados y certifico el resultado con SQL de solo lectura. No modifico Sync_Sales, Cuentas, Comandas, Cortes ni Produccion."
            else:
                result["percent_complete"] = 0
                result["certification"] = "NOT_CERTIFIED"
            return 0

        if mode == SQL_MIGRATION_DEVELOPMENT_MODE:
            if expected_base and expected_base != current_head:
                raise RuntimeError(f"BASE_SHA_MISMATCH_OPERATIONAL_MODE:expected={expected_base}:actual={current_head}")
            if job.get("actions") not in (None, []):
                raise RuntimeError("SQL_MIGRATION_ACTIONS_FORBIDDEN")
            for forbidden_field in ("sql", "command", "shell", "script", "path"):
                if job.get(forbidden_field) is not None:
                    raise RuntimeError(f"SQL_MIGRATION_FORBIDDEN_FIELD:{forbidden_field}")
            migration_path = str(job.get("migration_path") or "")
            migration_parts = Path(migration_path).parts
            if (
                not migration_path
                or Path(migration_path).is_absolute()
                or ".." in migration_parts
                or len(migration_parts) < 4
                or migration_parts[:3] != ("backend", "database", "migrations")
                or not migration_path.lower().endswith(".sql")
            ):
                raise RuntimeError("SQL_MIGRATION_PATH_INVALID")
            migration_sha256 = str(job.get("migration_sha256") or "").lower()
            if not re.fullmatch(r"[0-9a-f]{64}", migration_sha256):
                raise RuntimeError("SQL_MIGRATION_SHA256_INVALID")
            if job.get("confirm_sql_migration") is not True:
                raise RuntimeError("SQL_MIGRATION_CONFIRMATION_REQUIRED")
            use_existing_sql_writer = job.get("confirm_use_existing_sql_writer") is True
            preflight_checks = job.get("preflight_checks") or []
            checks = job.get("checks") or []
            if not preflight_checks or any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in preflight_checks):
                raise RuntimeError("SQL_MIGRATION_PREFLIGHT_SQL_AUDIT_REQUIRED")
            if not checks or any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
                raise RuntimeError("SQL_MIGRATION_POST_SQL_AUDIT_REQUIRED")
            preflight_results = []
            for check in preflight_checks:
                check_result = run_check(ROOT, check)
                preflight_results.append(check_result)
                if check_result["status"] != "PASS":
                    result["blockers"].append("check_failed:sql_migration_preflight")
                    break
            result["preflight_checks"] = preflight_results
            result["operation"] = SQL_MIGRATION_DEVELOPMENT_MODE
            result["migration_path"] = migration_path
            result["migration_sha256"] = migration_sha256
            result["canonical_sql_mutation"] = True
            result["files_changed"] = []
            if result["blockers"]:
                result["checks"] = []
                result["tests"] = "FAIL"
                result["quality_gate"] = "FAIL"
                result["percent_complete"] = 0
                result["certification"] = "NOT_CERTIFIED"
                return 0
            helper = ROOT / "tools" / "mirror_sync" / "sql_migration_development.py"
            if not helper.is_file():
                raise RuntimeError("SQL_MIGRATION_HELPER_NOT_FOUND")
            backend = ROOT / "backend"
            migration_cmd = [PYTHON_BIN, str(helper), "--migration-path", migration_path, "--migration-sha256", migration_sha256, "--confirm"]
            if use_existing_sql_writer:
                migration_cmd.append("--allow-canonical-sql-writer")
            result["use_existing_sql_writer"] = use_existing_sql_writer
            execution = run(
                migration_cmd,
                cwd=ROOT,
                timeout=MAX_SECONDS,
                env_extra={**load_backend_runtime_env(), "PYTHONPATH": str(backend)},
            )
            raw_migration_output = execution.stdout or ""
            result["operation_output"] = raw_migration_output[-12000:]
            safe_migration_summary = {"returncode": execution.returncode}
            for raw_line in reversed(raw_migration_output.splitlines()):
                try:
                    payload = json.loads(raw_line)
                except (json.JSONDecodeError, TypeError):
                    continue
                if not isinstance(payload, dict):
                    continue
                status = str(payload.get("status") or "").upper()
                if status in {"PASS", "FAIL"}:
                    safe_migration_summary["status"] = status
                credential_source = str(payload.get("credential_source") or "").strip().lower()
                if credential_source in {"dedicated", "canonical"}:
                    safe_migration_summary["credential_source"] = credential_source
                error = str(payload.get("error") or "")
                if error.startswith("MigrationContractError:"):
                    error_code = error.split(":", 1)[1].split(":", 1)[0]
                    if re.fullmatch(r"[A-Z0-9_]+", error_code):
                        safe_migration_summary["error_code"] = error_code
                if isinstance(payload.get("returncode"), int):
                    safe_migration_summary["returncode"] = payload["returncode"]
                break
            result["operation_summary"] = safe_migration_summary
            if execution.returncode != 0:
                result["blockers"].append(f"sql_migration_failed:rc={execution.returncode}")
            check_results = []
            if not result["blockers"]:
                for check in checks:
                    check_result = run_check(ROOT, check)
                    check_results.append(check_result)
                    if check_result["status"] != "PASS":
                        result["blockers"].append("check_failed:sql_migration_post_audit")
                        break
            result["checks"] = check_results
            result["tests"] = "PASS" if (preflight_results and check_results and all(x["status"] == "PASS" for x in preflight_results + check_results)) else "FAIL"
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            if not result["blockers"]:
                result["status"] = "OPERATIONAL_COMPLETE"
                result["percent_complete"] = 100
                result["certification"] = "CERTIFIED_OPERATIONAL"
                result["summary_es"] = "El Worker ejecuto preflight SQL HRLectura, una migracion Development versionada y SHA-bound mediante writer dedicado, y post-audit SQL HRLectura. No acepto SQL inline, shell arbitrario ni toco Produccion."
            else:
                result["percent_complete"] = 0
                result["certification"] = "NOT_CERTIFIED"
            return 0

        if mode == MPRO_FULL_HISTORY_MODE:
            if expected_base and expected_base != current_head:
                raise RuntimeError(f"BASE_SHA_MISMATCH_OPERATIONAL_MODE:expected={expected_base}:actual={current_head}")
            if job.get("actions") not in (None, []):
                raise RuntimeError("MPRO_RESYNC_ACTIONS_FORBIDDEN")
            units = job.get("units", [])
            if not isinstance(units, list) or len(units) != 1 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
                raise RuntimeError("MPRO_RESYNC_EXACTLY_ONE_UNIT_REQUIRED")
            dry_run = job.get("dry_run", True)
            if not isinstance(dry_run, bool):
                raise RuntimeError("MPRO_RESYNC_DRY_RUN_INVALID")
            if dry_run is False and job.get("confirm_full_history_resync") is not True:
                raise RuntimeError("MPRO_RESYNC_CONFIRMATION_REQUIRED")
            checks = job.get("checks") or []
            if not checks or any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
                raise RuntimeError("MPRO_RESYNC_SQL_AUDIT_REQUIRED")
            script = ROOT / "backend" / "scripts" / "resync_mpro_full_history.py"
            if not script.is_file():
                raise RuntimeError("MPRO_RESYNC_SCRIPT_NOT_FOUND")
            cmd = [PYTHON_BIN, str(script), "--unit", units[0].strip().upper()]
            if dry_run is False:
                cmd.append("--execute")
            backend = ROOT / "backend"
            execution = run(cmd, cwd=ROOT, timeout=SOFTRESTAURANT_RESYNC_MAX_SECONDS, env_extra={**load_backend_runtime_env(), "PYTHONPATH": str(backend)})
            result["operation"] = MPRO_FULL_HISTORY_MODE
            result["dry_run"] = dry_run
            result["units"] = [units[0].strip().upper()]
            result["canonical_sql_mutation"] = not dry_run
            result["operation_output"] = execution.stdout[-20000:]
            result["files_changed"] = []
            if execution.returncode != 0:
                result["blockers"].append(f"mpro_resync_failed:rc={execution.returncode}")
            check_results = []
            if not result["blockers"]:
                for check in checks:
                    check_result = run_check(ROOT, check)
                    check_results.append(check_result)
                    if check_result["status"] != "PASS":
                        result["blockers"].append("check_failed:sql_readonly_audit")
                        break
            result["checks"] = check_results
            result["tests"] = "PASS" if check_results and all(x["status"] == "PASS" for x in check_results) else "FAIL"
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            if not result["blockers"]:
                result["status"] = "OPERATIONAL_COMPLETE"
                result["percent_complete"] = 100
                result["certification"] = "CERTIFIED_OPERATIONAL"
                result["summary_es"] = "El Worker ejecuto la capability cerrada de resync historico MPRO para una sola unidad y certifico el resultado con SQL READ_ONLY. No acepto shell, rutas ni comandos externos y no toco Produccion."
            else:
                result["percent_complete"] = 0
                result["certification"] = "NOT_CERTIFIED"
            return 0

        if mode == SOFTRESTAURANT_FULL_HISTORY_MODE:
            if expected_base and expected_base != current_head:
                raise RuntimeError(f"BASE_SHA_MISMATCH_OPERATIONAL_MODE:expected={expected_base}:actual={current_head}")
            if job.get("actions") not in (None, []):
                raise RuntimeError("SOFTRESTAURANT_RESYNC_ACTIONS_FORBIDDEN")
            units = job.get("units", [])
            if not isinstance(units, list) or len(units) > 32 or not all(isinstance(u, str) and UNIT_CODE_RE.fullmatch(u.strip()) for u in units):
                raise RuntimeError("SOFTRESTAURANT_RESYNC_UNITS_INVALID")
            dry_run = job.get("dry_run", True)
            if not isinstance(dry_run, bool):
                raise RuntimeError("SOFTRESTAURANT_RESYNC_DRY_RUN_INVALID")
            if dry_run is False and job.get("confirm_full_history_resync") is not True:
                raise RuntimeError("SOFTRESTAURANT_RESYNC_CONFIRMATION_REQUIRED")
            checks = job.get("checks") or []
            if not checks or any(not isinstance(c, dict) or c.get("type") != "sql_readonly_audit" for c in checks):
                raise RuntimeError("SOFTRESTAURANT_RESYNC_SQL_AUDIT_REQUIRED")
            script = ROOT / "backend" / "scripts" / "resync_softrestaurant_full_history.py"
            if not script.is_file():
                raise RuntimeError("SOFTRESTAURANT_RESYNC_SCRIPT_NOT_FOUND")
            cmd = [PYTHON_BIN, str(script)]
            if dry_run is False:
                cmd.append("--execute")
            for unit in units:
                cmd.extend(["--unit", unit.strip().upper()])
            backend = ROOT / "backend"
            execution = run(cmd, cwd=ROOT, timeout=SOFTRESTAURANT_RESYNC_MAX_SECONDS, env_extra={**load_backend_runtime_env(), "PYTHONPATH": str(backend)})
            result["operation"] = SOFTRESTAURANT_FULL_HISTORY_MODE
            result["dry_run"] = dry_run
            result["units"] = [u.strip().upper() for u in units]
            result["canonical_sql_mutation"] = not dry_run
            result["operation_output"] = execution.stdout[-20000:]
            result["operation_summary"] = summarize_softrestaurant_output(execution.stdout)
            result["files_changed"] = []
            if execution.returncode != 0:
                result["blockers"].append(f"softrestaurant_resync_failed:rc={execution.returncode}")
            check_results = []
            if not result["blockers"]:
                for check in checks:
                    check_result = run_check(ROOT, check)
                    check_results.append(check_result)
                    if check_result["status"] != "PASS":
                        result["blockers"].append("check_failed:sql_readonly_audit")
                        break
            result["checks"] = check_results
            result["tests"] = "PASS" if check_results and all(x["status"] == "PASS" for x in check_results) else "FAIL"
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            if not result["blockers"]:
                result["status"] = "OPERATIONAL_COMPLETE"
                result["percent_complete"] = 100
                result["certification"] = "CERTIFIED_OPERATIONAL"
                result["summary_es"] = "El Worker universal ejecuto la capacidad cerrada de resync historico SoftRestaurant y despues certifico el resultado mediante auditoria SQL de solo lectura. No ejecuto shell arbitrario ni acepto rutas o comandos externos."
            else:
                result["percent_complete"] = 0
                result["certification"] = "NOT_CERTIFIED"
            return 0

        execution_base_sha = base_sha
        accumulated_integration: list[dict[str, Any]] = []
        for replay_attempt in range(1, MAX_CONCURRENCY_REPLAY_ATTEMPTS + 1):
            if replay_attempt > 1:
                if agent_guard_claim_created:
                    release_ok, release_detail = release_agent_guard_claim(job_id)
                    if not release_ok:
                        result["blockers"].append("agent_guard_release_failed_before_replay:" + release_detail)
                        break
                    agent_guard_claim_created = False
                if worktree is not None:
                    git("worktree", "remove", "--force", str(worktree), check=False)
                    worktree = None
                if branch:
                    git("branch", "-D", branch, check=False)
                    branch = ""
                result["concurrency_replays"] += 1

            result["execution_base_sha"] = execution_base_sha
            worktree, branch = prepare_worktree(job_id, execution_base_sha, requested_paths)
            agent_guard_claim_created = True
            result["job_branch"] = branch
            allowed_files: set[str] = set()
            for action in job.get("actions") or []:
                relative = apply_action(worktree, action)
                allowed_files.add(relative)
            scope_blockers = validate_scope(worktree, execution_base_sha, allowed_files)
            if scope_blockers:
                result["status"] = "GIT_SCOPE_VIOLATION"
                result["blockers"].extend(scope_blockers)
                break
            result["files_changed"] = changed_files(worktree, execution_base_sha)
            check_results: list[dict[str, Any]] = []
            checks = job.get("checks") or [{"type": "git_diff_check"}]
            for check in checks:
                check_result = run_check(worktree, check)
                check_results.append(check_result)
                if check_result["status"] != "PASS":
                    result["status"] = "GIT_TESTS_FAILED"
                    result["blockers"].append(f"check_failed:{check_result['type']}")
                    break
            result["checks"] = check_results
            if (
                result.get("required_deliverables")
                and result.get("deliverable_specs")
            ):
                try:
                    result["deliverables"] = (
                        materialize_deliverables(
                            result.get("required_deliverables"),
                            result.get("deliverable_specs"),
                            check_results,
                        )
                    )
                except ValueError as exc:
                    result["blockers"].append(
                        "deliverable_materialization_failed:"
                        + str(exc)
                    )
            result["tests"] = "PASS" if check_results and all(x["status"] == "PASS" for x in check_results) else ("PASS" if not check_results and not result["blockers"] else "FAIL")
            result["build"] = next((x["status"] for x in check_results if x.get("type") == "frontend_build"), "NOT_REQUESTED")
            result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"
            if result["blockers"]:
                break

            head = create_commit(worktree, job_id, sorted(allowed_files))
            result["candidate_sha"] = head
            result["commit_created"] = head
            ok, detail, final_head, integration_evidence = integrate(worktree, branch, head, execution_base_sha, allowed_files, job_id, result["remote_at_start"])
            accumulated_integration.extend(integration_evidence)
            result["concurrency"]["integration"] = accumulated_integration
            result["integration_attempts"] = len(accumulated_integration)
            result["concurrent_head_changes"] = sorted({p for step in accumulated_integration for p in (step.get("concurrent_head_changes") or [])})
            if integration_evidence:
                last_git = integration_evidence[-1]
                for field in ("remote_before_push","remote_after_push","local_after","ahead_after","behind_after","push_attempted","push_result"):
                    if field in last_git: result[field]=last_git[field]
            if ok:
                result["status"] = "INTEGRATED"; result["git_sync_status"] = "CERTIFIED_GIT_SYNC"; result["development_sha"] = final_head; result["percent_complete"] = 95; result["certification"] = "PENDING_AUDIT_EVIDENCE"; result["summary_es"] = "ChatGPT envio cambios exactos; el Worker uso worktree aislado, writer lock y compare-and-swap remoto, publico solo fast-forward y certifico topology 0/0 sin merge, rebase ni force. Produccion no fue tocada."; break
            terminal = detail.split(":",1)[0]
            if terminal in {"REMOTE_MOVED_RETRY_REQUIRED", "GIT_PUSH_FAILED"}:
                git("fetch", REMOTE, DEV_BRANCH)
                remote_now = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
                if remote_now != execution_base_sha:
                    if not git_is_ancestor(execution_base_sha, remote_now):
                        result["status"] = "GIT_DIVERGENCE_BLOCKED"
                        result["blockers"].append(
                            f"REMOTE_ADVANCE_NOT_DESCENDANT:base={execution_base_sha}:remote={remote_now}"
                        )
                        break
                    concurrent_paths = git_changed_paths(execution_base_sha, remote_now)
                    replay_policy = evaluate_scope_advance(
                        execution_base_sha,
                        remote_now,
                        requested_paths,
                        concurrent_paths,
                    )
                    accumulated_integration.append({
                        "decision": replay_policy.get("decision"),
                        "remote_after_failed_push": remote_now,
                        "concurrent_head_changes": concurrent_paths,
                        "replay_attempt": replay_attempt,
                    })
                    result["concurrency"]["integration"] = accumulated_integration
                    result["concurrent_head_changes"] = sorted({
                        p
                        for step in accumulated_integration
                        for p in (step.get("concurrent_head_changes") or [])
                    })
                    if replay_policy.get("decision") == "SAFE_REPLAY":
                        execution_base_sha = remote_now
                        result["remote_at_start"] = remote_now
                        continue
                    conflicts = ",".join(replay_policy.get("scope_conflicts") or [])
                    result["status"] = "CONCURRENT_SCOPE_CONFLICT"
                    result["blockers"].append(
                        f"CONCURRENT_SCOPE_CONFLICT:base={execution_base_sha}:remote={remote_now}:paths={conflicts}"
                    )
                    break
            if terminal in {"REMOTE_MOVED_RETRY_REQUIRED","GIT_DIVERGENCE_BLOCKED","GIT_SCOPE_VIOLATION","GIT_PUSH_FAILED","GIT_LOCK_BUSY"}:
                result["status"] = terminal
            result["blockers"].append(detail)
            break
        else:
            result["blockers"].append("CONCURRENT_REPLAY_EXHAUSTED")

        if result["status"] != "INTEGRATED":
            result["percent_complete"] = 80 if result.get("files_changed") else 0
            result["certification"] = "NOT_CERTIFIED"
            result["quality_gate"] = "FAIL"
            result["summary_es"] = "La orden de ChatGPT no se integro porque una validacion o candado fallo. El worker se detuvo sin ampliar el alcance y sin tocar Produccion."
    except Exception as exc:
        result["blockers"].append(f"dispatcher_exception:{type(exc).__name__}:{exc}")
        result["percent_complete"] = 0
        result["certification"] = "NOT_CERTIFIED"
        result["quality_gate"] = "FAIL"
        result["summary_es"] = "El worker se detuvo por un error verificable antes de certificar el trabajo. No invento una solucion adicional y Produccion no fue tocada."
    finally:
        if slot_id is not None:
            try:
                update_slot_state(slot_id, "TERMINALIZING", execution_pid=os.getpid())
                release_slot(slot_id)
                result["slot_release"] = "PASS"
            except Exception as exc:
                result["slot_release"] = "FAIL"
                result["blockers"].append(f"slot_release_failed:{type(exc).__name__}:{exc}")
                result["quality_gate"] = "FAIL"
                result["certification"] = "NOT_CERTIFIED"
        else:
            result["slot_release"] = "NOT_REQUIRED"
        if agent_guard_claim_created:
            release_ok, release_detail = release_agent_guard_claim(job_id)
            result["agent_guard_release"] = "PASS" if release_ok else "FAIL"
            if not release_ok:
                result["blockers"].append("agent_guard_release_failed:" + release_detail)
                result["quality_gate"] = "FAIL"
                result["certification"] = "NOT_CERTIFIED"
        else:
            result["agent_guard_release"] = "NOT_REQUIRED"
        if git_writer_lock is not None:
            try:
                release_writer_lock(ROOT, git_writer_lock); result["git_writer_lock_release"] = "PASS"
            except GitGuardError as exc:
                result["git_writer_lock_release"] = "FAIL"; result["blockers"].append("git_writer_lock_release_failed:" + exc.code); result["quality_gate"] = "FAIL"; result["certification"] = "NOT_CERTIFIED"
        else:
            result["git_writer_lock_release"] = "NOT_REQUIRED"
        if worktree is not None:
            git("worktree", "remove", "--force", str(worktree), check=False)
        if branch:
            git("branch", "-D", branch, check=False)
        result["completed_at_utc"] = now()
        write_json(RESULTS / path.name, result)
        target = DONE / path.name if result["status"] in {"INTEGRATED", "READ_ONLY_COMPLETE", "OPERATIONAL_COMPLETE"} else REJECTED / path.name
        os.replace(processing, target)
        (RUNTIME / "last_terminal_utc").write_text(result["completed_at_utc"] + "\n", encoding="utf-8")
        current_job = RUNTIME / "current_job_id"
        try:
            if current_job.read_text(encoding="utf-8").strip() == job_id:
                current_job.unlink()
        except OSError:
            pass
    print(json.dumps({"job_id": job_id, "status": result["status"], "blockers": result["blockers"]}, ensure_ascii=False))
    return 0


def _load_preferred_job() -> dict[str, Any] | None:
    try:
        payload = json.loads(PREFERRED_JOB_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    job_id = str(payload.get("job_id") or "").strip()
    try:
        expires_at = float(payload.get("expires_at_epoch") or 0)
    except (TypeError, ValueError):
        expires_at = 0
    if not JOB_ID_RE.fullmatch(job_id) or expires_at <= datetime.now(timezone.utc).timestamp():
        try:
            PREFERRED_JOB_PATH.unlink()
        except OSError:
            pass
        return None
    return payload


def _select_pending_job(jobs: list[Path]) -> tuple[Path | None, bool]:
    preferred = _load_preferred_job()
    if preferred is not None:
        preferred_id = str(preferred["job_id"])
        for path in jobs:
            if path.stem == preferred_id:
                print(f"UNIVERSAL_DISPATCHER=PREFERRED_JOB_SELECTED JOB_ID={preferred_id}")
                return path, True
        try:
            PREFERRED_JOB_PATH.unlink()
        except OSError:
            pass
        print(f"UNIVERSAL_DISPATCHER=PREFERRED_JOB_STALE_IGNORED JOB_ID={preferred_id}")
    if not jobs:
        return None, False
    return jobs[0], False


def claim_one() -> Path | None:
    with LOCK_FILE.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("UNIVERSAL_DISPATCHER=BUSY")
            return None

        jobs = sorted(PENDING.glob("*.json"))
        selected, is_preferred = _select_pending_job(jobs)

        if selected is None:
            print("UNIVERSAL_DISPATCHER=NO_PENDING_JOBS")
            return None

        processing = PROCESSING / selected.name
        os.replace(selected, processing)

        if is_preferred:
            try:
                PREFERRED_JOB_PATH.unlink()
            except OSError:
                pass

        print(f"UNIVERSAL_DISPATCHER=CLAIMED JOB_ID={selected.stem}")
        return processing


def dispatch() -> int:
    ensure_dirs()
    claimed = claim_one()
    if claimed is None:
        return 0
    return process_one(claimed, already_claimed=True)


def main() -> int:
    return dispatch()


if __name__ == "__main__":
    raise SystemExit(main())
