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
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
DEV_BRANCH = "Edarsahub_Desarrollo"
MAX_SECONDS = int(os.environ.get("EDARSAHUB_JOB_MAX_SECONDS", "1800"))
JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")
ALLOWED_ACTIONS = {"replace_text", "write_file", "delete_file"}
ALLOWED_CHECKS = {"git_diff_check", "py_compile", "pytest", "frontend_build"}


def resolve_canonical_python() -> str:
    """Resolve the interpreter shared by every Python worker subprocess."""
    repo_python = ROOT / ".venv" / "bin" / "python"
    if repo_python.is_file() and os.access(repo_python, os.X_OK):
        return str(repo_python)
    return sys.executable


PYTHON_BIN = resolve_canonical_python()


def load_backend_runtime_env() -> dict[str, str]:
    """Load missing runtime variables from backend/.env without shell evaluation."""
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


def run(
    args: list[str],
    cwd: Path | None = None,
    check: bool = False,
    timeout: int | None = None,
    env_extra: dict[str, str] | None = None,
):
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
        timeout=timeout,
        env=env,
    )


def git(*args: str, cwd: Path | None = None, check: bool = True):
    result = run(["git", *args], cwd=cwd, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{result.stdout[-2000:]}")
    return result


def resolve_repository_credential_helper() -> str:
    result = git(
        "config",
        "--local",
        "--get",
        "credential.helper",
        cwd=ROOT,
        check=False,
    )
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


def prepare_worktree(
    job_id: str,
    base_sha: str,
    allowed_paths: list[str],
) -> tuple[Path, str]:
    safe_id = re.sub(r"[^A-Za-z0-9._-]", "-", job_id)
    branch = f"agent/worker/{safe_id}"
    path = WORKTREES / safe_id
    agent_id = f"worker-{safe_id}"

    if path.exists():
        git("worktree", "remove", "--force", str(path), check=False)
        shutil.rmtree(path, ignore_errors=True)

    git("branch", "-D", branch, check=False)

    # El job debe ejecutarse exactamente sobre el base_sha autorizado.
    # No usar implicitamente el HEAD local, que puede estar atras de Desarrollo.
    git("branch", branch, base_sha)

    guard = ROOT / ".git" / "agent-guard" / "bin" / "agent_guard.py"
    if not guard.is_file():
        raise RuntimeError("AGENT_GUARD_NOT_FOUND")

    if not allowed_paths:
        raise RuntimeError("AGENT_GUARD_PATHS_REQUIRED")

    command = [
        PYTHON_BIN,
        str(guard),
        "worktree-create",
        "--agent-id",
        agent_id,
        "--task-id",
        safe_id,
        "--description",
        f"ChatGPT deterministic worker job {job_id}",
        "--domain",
        f"worker_job_{safe_id}",
        "--branch",
        branch,
        "--directory",
        str(path),
    ]

    for allowed_path in allowed_paths:
        command.extend(["--path", allowed_path])

    created = run(
        command,
        cwd=ROOT,
    )
    if created.returncode != 0:
        raise RuntimeError(
            f"AGENT_GUARD_WORKTREE_CREATE_FAILED:{created.stdout[-2000:]}"
        )

    if not path.is_dir():
        raise RuntimeError("AGENT_GUARD_WORKTREE_NOT_CREATED")

    head = git("rev-parse", "HEAD", cwd=path).stdout.strip()
    if head != base_sha:
        raise RuntimeError(
            f"WORKTREE_BASE_MISMATCH:expected={base_sha}:actual={head}"
        )

    return path, branch


def apply_action(worktree: Path, action: dict[str, Any]) -> str:
    kind = str(action.get("type"))
    if kind not in ALLOWED_ACTIONS:
        raise ValueError(f"UNSUPPORTED_ACTION:{kind}")
    relative = str(action.get("path") or "")
    target = safe_path(worktree, relative)
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
            raise RuntimeError(
                f"REPLACE_COUNT_MISMATCH:{relative}:expected={expected_count}:actual={actual_count}"
            )
        target.write_text(text.replace(old, new), encoding="utf-8")
        return relative

    if kind == "write_file":
        content = action["content"]
        if target.exists():
            if "expected_sha256" not in action:
                raise RuntimeError(
                    f"WRITE_EXISTING_REQUIRES_EXPECTED_SHA256:{relative}"
                )
            current_size = target.stat().st_size
            new_size = len(content.encode("utf-8"))
            if current_size >= 4096 and new_size < int(current_size * 0.75):
                raise RuntimeError(
                    f"WRITE_FILE_LARGE_SHRINK_BLOCKED:{relative}:"
                    f"current={current_size}:new={new_size}"
                )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return relative

    if kind == "delete_file":
        if not target.is_file():
            raise RuntimeError(f"DELETE_TARGET_MISSING:{relative}")
        target.unlink()
        return relative

    raise ValueError(f"UNSUPPORTED_ACTION:{kind}")


def run_check(worktree: Path, check: dict[str, Any]) -> dict[str, Any]:
    kind = str(check.get("type"))
    started = now()
    if kind == "git_diff_check":
        cmd = ["git", "diff", "--check"]
        cwd = worktree
    elif kind == "py_compile":
        paths = [str(p) for p in check.get("paths") or []]
        cmd = [PYTHON_BIN, "-m", "py_compile", *paths]
        cwd = worktree
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

        cmd = [PYTHON_BIN, "-m", "pytest", "-q", *paths]
        cwd = backend
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
        result = run(
            cmd,
            cwd=cwd,
            timeout=MAX_SECONDS,
            env_extra=locals().get("env_extra"),
        )
        output = result.stdout[-12000:]
        return {
            "type": kind,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "returncode": result.returncode,
            "started_at_utc": started,
            "completed_at_utc": now(),
            "output": output,
        }
    except subprocess.TimeoutExpired as exc:
        text = exc.stdout if isinstance(exc.stdout, str) else ""
        return {
            "type": kind,
            "status": "FAIL",
            "returncode": 124,
            "started_at_utc": started,
            "completed_at_utc": now(),
            "output": f"TIMEOUT\n{text[-8000:]}",
        }


def changed_files(worktree: Path, base_sha: str) -> list[str]:
    result = git("diff", "--name-only", base_sha, "--", cwd=worktree)
    staged_or_untracked = git("status", "--porcelain=v1", cwd=worktree).stdout.splitlines()
    names = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    for line in staged_or_untracked:
        if len(line) >= 4:
            name = line[3:]
            if " -> " in name:
                name = name.split(" -> ", 1)[1]
            names.add(name)
    return sorted(names)


def validate_scope(worktree: Path, base_sha: str, allowed: set[str]) -> list[str]:
    actual = set(changed_files(worktree, base_sha))
    extra = sorted(actual - allowed)
    missing = sorted(allowed - actual)
    blockers: list[str] = []
    if extra:
        blockers.append("unexpected_files:" + ",".join(extra))
    if missing:
        blockers.append("expected_files_unchanged:" + ",".join(missing))
    return blockers


def create_commit(worktree: Path, job_id: str, files: list[str]) -> str:
    git("add", "--", *files, cwd=worktree)
    staged = git("diff", "--cached", "--name-only", cwd=worktree).stdout.splitlines()
    if sorted(staged) != sorted(files):
        raise RuntimeError("STAGED_SCOPE_MISMATCH")
    message = f"worker({job_id}): apply ChatGPT deterministic changes"
    git(
        "-c", "user.name=EDARSAHUB Worker",
        "-c", "user.email=worker@edarsahub.local",
        "commit", "-m", message,
        cwd=worktree,
    )
    return git("rev-parse", "HEAD", cwd=worktree).stdout.strip()


def integrate(head: str, base_sha: str) -> tuple[bool, str]:
    git("fetch", REMOTE, DEV_BRANCH)
    remote_dev = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
    if remote_dev != base_sha:
        return False, f"development_moved:{remote_dev}"
    guard = ROOT / "scripts" / "agent_guardrails" / "validate_repository_artifacts.py"
    if guard.is_file():
        check = run(
            [
                PYTHON_BIN,
                str(guard),
                "--range",
                base_sha,
                head,
            ],
            cwd=ROOT,
        )
        if check.returncode != 0:
            return False, (
                "repository_artifact_guard_failed:"
                + check.stdout[-1000:]
            )
    credential_helper = resolve_repository_credential_helper()
    if not credential_helper:
        return False, "development_push_credential_helper_missing"
    push = run(
        [
            "git",
            "-c",
            "credential.helper=",
            "-c",
            f"credential.helper={credential_helper}",
            "push",
            REMOTE,
            f"{head}:refs/heads/{DEV_BRANCH}",
        ],
        cwd=ROOT,
        env_extra={"EDARSA_ALLOW_PUSH": "1"},
    )
    if push.returncode != 0:
        return False, f"development_push_failed:{push.stdout[-1000:]}"
    git("fetch", REMOTE, DEV_BRANCH)
    after = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
    return after == head, after


def release_agent_guard_claim(job_id: str) -> tuple[bool, str]:
    safe_id = re.sub(r"[^A-Za-z0-9._-]", "-", job_id)
    agent_id = f"worker-{safe_id}"
    guard = ROOT / ".git" / "agent-guard" / "bin" / "agent_guard.py"
    if not guard.is_file():
        return False, "AGENT_GUARD_NOT_FOUND"
    released = run(
        [PYTHON_BIN, str(guard), "release", "--agent-id", agent_id],
        cwd=ROOT,
    )
    if released.returncode != 0:
        return False, released.stdout[-1000:]
    return True, released.stdout[-1000:]


def process_one(path: Path) -> int:
    envelope = load_envelope(path)
    job = envelope["job"]
    job_id = str(job.get("job_id") or "")
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("INVALID_JOB_ID")

    processing = PROCESSING / path.name
    os.replace(path, processing)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    (RUNTIME / "current_job_id").write_text(job_id + "\n", encoding="utf-8")
    result: dict[str, Any] = {
        "schema": "edarsahub.worker-result.v2",
        "job_id": job_id,
        "started_at_utc": now(),
        "status": "BLOCKED",
        "executor": "chatgpt-deterministic",
        "production_touched": False,
        "blockers": [],
        "summary_es": "El worker recibio una orden exacta de ChatGPT y la proceso sin pedir instrucciones a otra inteligencia artificial.",
    }

    worktree: Path | None = None
    branch = ""
    agent_guard_claim_created = False
    try:
        if job.get("schema") != "edarsahub.worker-job.v2":
            raise ValueError("UNSUPPORTED_JOB_SCHEMA")
        git("fetch", REMOTE, DEV_BRANCH)
        base_sha = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
        expected_base = job.get("base_sha")
        if expected_base and expected_base != base_sha:
            raise RuntimeError(f"BASE_SHA_MISMATCH:expected={expected_base}:actual={base_sha}")
        result["base_sha"] = base_sha
        requested_paths = sorted(
            {
                str(action.get("path"))
                for action in (job.get("actions") or [])
                if action.get("path")
            }
        )
        worktree, branch = prepare_worktree(
            job_id,
            base_sha,
            requested_paths,
        )
        agent_guard_claim_created = True
        result["job_branch"] = branch

        allowed_files: set[str] = set()
        for action in job.get("actions") or []:
            relative = apply_action(worktree, action)
            allowed_files.add(relative)

        scope_blockers = validate_scope(worktree, base_sha, allowed_files)
        result["blockers"].extend(scope_blockers)
        result["files_changed"] = changed_files(worktree, base_sha)

        check_results: list[dict[str, Any]] = []
        if not result["blockers"]:
            checks = job.get("checks") or [{"type": "git_diff_check"}]
            for check in checks:
                check_result = run_check(worktree, check)
                check_results.append(check_result)
                if check_result["status"] != "PASS":
                    result["blockers"].append(f"check_failed:{check_result['type']}")
                    break
        result["checks"] = check_results
        result["tests"] = "PASS" if check_results and all(x["status"] == "PASS" for x in check_results) else (
            "PASS" if not check_results and not result["blockers"] else "FAIL"
        )
        result["quality_gate"] = "PASS" if not result["blockers"] else "FAIL"

        head: str | None = None
        if not result["blockers"]:
            head = create_commit(worktree, job_id, sorted(allowed_files))
            result["candidate_sha"] = head

        if head:
            ok, detail = integrate(head, base_sha)
            if ok:
                result["status"] = "INTEGRATED"
                result["development_sha"] = head
                result["percent_complete"] = 95
                result["certification"] = "PENDING_AUDIT_EVIDENCE"
                result["summary_es"] = "ChatGPT envio cambios exactos, el worker aplico solamente esos cambios, las validaciones pasaron y el commit quedo integrado en Edarsahub_Desarrollo. Produccion no fue tocada."
            else:
                result["blockers"].append(detail)

        if result["status"] != "INTEGRATED":
            result["percent_complete"] = 80 if result["files_changed"] else 0
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
        if agent_guard_claim_created:
            release_ok, release_detail = release_agent_guard_claim(job_id)
            result["agent_guard_release"] = "PASS" if release_ok else "FAIL"
            if not release_ok:
                result["blockers"].append("agent_guard_release_failed:" + release_detail)
                result["quality_gate"] = "FAIL"
                result["certification"] = "NOT_CERTIFIED"
        else:
            result["agent_guard_release"] = "NOT_REQUIRED"
        if worktree is not None:
            git("worktree", "remove", "--force", str(worktree), check=False)
        if branch:
            git("branch", "-D", branch, check=False)
        result["completed_at_utc"] = now()
        write_json(RESULTS / path.name, result)
        target = DONE / path.name if result["status"] == "INTEGRATED" else REJECTED / path.name
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


def dispatch() -> int:
    ensure_dirs()
    with LOCK_FILE.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("UNIVERSAL_DISPATCHER=BUSY")
            return 0
        jobs = sorted(PENDING.glob("*.json"))
        if not jobs:
            print("UNIVERSAL_DISPATCHER=NO_PENDING_JOBS")
            return 0
        return process_one(jobs[0])


def main() -> int:
    return dispatch()


if __name__ == "__main__":
    raise SystemExit(main())
