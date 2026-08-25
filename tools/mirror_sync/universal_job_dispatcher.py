#!/usr/bin/env python3
"""Fail-closed dispatcher for EDARSAHUB universal worker jobs.

The receiver (`universal_job_bridge.py`) only validates and materializes jobs.
This dispatcher claims one pending job, runs an allow-listed local executor in an
isolated git worktree, validates the produced commit, and integrates it into
Edarsahub_Desarrollo only when the branch has not moved and all declared checks
pass. Results are written locally for a separate publisher to send back to the
`worker/requests` branch.

No command supplied by a job is ever executed.
"""

from __future__ import annotations

import fcntl
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
WORKTREES = Path(os.environ.get("EDARSAHUB_JOB_WORKTREES", "/tmp/edarsahub-worker-jobs"))
LOCK_FILE = STATE / "dispatcher.lock"
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
DEV_BRANCH = "Edarsahub_Desarrollo"
EXECUTOR = os.environ.get("EDARSAHUB_JOB_EXECUTOR", "codex")
MAX_SECONDS = int(os.environ.get("EDARSAHUB_JOB_MAX_SECONDS", "1800"))
JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(args: list[str], cwd: Path | None = None, check: bool = False, timeout: int | None = None):
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
        timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def git(*args: str, cwd: Path | None = None, check: bool = True):
    result = run(["git", *args], cwd=cwd, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{result.stdout[-2000:]}")
    return result


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


def resolve_codex() -> str | None:
    explicit = os.environ.get("EDARSAHUB_CODEX_BIN")
    if explicit and Path(explicit).is_file() and os.access(explicit, os.X_OK):
        return explicit
    found = shutil.which("codex")
    if found:
        return found
    candidates = sorted(Path("/root/.local/share/code-server/extensions").glob("openai.chatgpt-*/bin/*/codex"))
    for candidate in reversed(candidates):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def human_prompt(job: dict[str, Any], base_sha: str, job_id: str) -> str:
    acceptance = "\n".join(f"- {x}" for x in (job.get("acceptance") or []))
    constraints = "\n".join(f"- {x}" for x in (job.get("constraints") or []))
    return f"""EDARSAHUB — trabajo autónomo {job_id}

Objetivo:
{job.get('objective', '').strip()}

Condiciones para aceptar el trabajo:
{acceptance or '- Cumplir exactamente el objetivo.'}

Restricciones obligatorias:
{constraints or '- Respetar AGENTS.md y las reglas canónicas del repositorio.'}

Reglas adicionales obligatorias:
- Lee AGENTS.md y la documentación de gobierno aplicable antes de modificar.
- Trabaja únicamente dentro de este checkout aislado.
- Rama objetivo final: {DEV_BRANCH}.
- Base exacta al iniciar: {base_sha}.
- No tocar Producción.
- No force-push, reset --hard ni clean destructivo.
- No exponer secretos.
- Audita antes de crear arquitectura nueva.
- Ejecuta las pruebas relevantes disponibles para el cambio.
- Si existe un bloqueo real, no inventes éxito.
- Al terminar deja TODOS los cambios válidos en un commit local.
- El mensaje del commit debe comenzar con: worker({job_id}):
- No empujes a GitHub; el integrador lo hará después de validar.
- Genera un archivo `.worker-result.json` en la raíz con: summary_es, tests, quality_gate, files_changed, blockers. El resumen debe estar en "español", lenguaje natural, entendible por una persona de 13 años sin conocimientos de programación.
"""


def prepare_worktree(job_id: str, base_sha: str) -> tuple[Path, str]:
    safe_id = re.sub(r"[^A-Za-z0-9._-]", "-", job_id)
    branch = f"worker/job/{safe_id}"
    path = WORKTREES / safe_id
    if path.exists():
        shutil.rmtree(path)
    git("branch", "-D", branch, check=False)
    result = git("worktree", "add", "-b", branch, str(path), base_sha, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"WORKTREE_CREATE_FAILED:{result.stdout[-2000:]}")
    return path, branch


def execute_codex(worktree: Path, prompt: str) -> tuple[int, str]:
    codex = resolve_codex()
    if not codex:
        return 127, "CODEX_EXECUTOR_NOT_AVAILABLE"
    # `codex exec` is non-interactive. The prompt is a single argument, never a shell command.
    cmd = [
        codex,
        "exec",
        "--sandbox",
        "workspace-write",
        "--ask-for-approval",
        "never",
        "-C",
        str(worktree),
        prompt,
    ]
    try:
        result = run(cmd, cwd=worktree, timeout=MAX_SECONDS)
        return result.returncode, result.stdout[-20000:]
    except subprocess.TimeoutExpired as exc:
        text = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        return 124, f"EXECUTOR_TIMEOUT\n{text[-10000:]}"


def validate_result_file(worktree: Path) -> tuple[dict[str, Any] | None, list[str]]:
    path = worktree / ".worker-result.json"
    if not path.is_file():
        return None, ["missing_worker_result"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, ["invalid_worker_result_json"]
    blockers: list[str] = []
    if not str(data.get("summary_es") or "").strip():
        blockers.append("missing_spanish_summary")
    if str(data.get("tests") or "").upper() != "PASS":
        blockers.append("tests_not_pass")
    if str(data.get("quality_gate") or "").upper() != "PASS":
        blockers.append("quality_gate_not_pass")
    if data.get("blockers"):
        blockers.append("executor_reported_blockers")
    return data, blockers


def validate_commit(worktree: Path, base_sha: str, job_id: str) -> tuple[str | None, list[str]]:
    blockers: list[str] = []
    status = git("status", "--porcelain=v1", cwd=worktree).stdout.splitlines()
    # .worker-result.json is metadata and must not enter the product commit.
    product_dirty = [line for line in status if not line.endswith(" .worker-result.json") and ".worker-result.json" not in line]
    if product_dirty:
        blockers.append("uncommitted_product_changes")
    head = git("rev-parse", "HEAD", cwd=worktree).stdout.strip()
    if head == base_sha:
        blockers.append("no_product_commit")
        return None, blockers
    parent = git("rev-parse", f"{head}^", cwd=worktree, check=False)
    if parent.returncode != 0 or parent.stdout.strip() != base_sha:
        blockers.append("job_commit_not_single_fast_forward")
    message = git("log", "-1", "--pretty=%s", cwd=worktree).stdout.strip()
    if not message.startswith(f"worker({job_id}):"):
        blockers.append("invalid_commit_message")
    return head, blockers


def integrate(head: str, base_sha: str) -> tuple[bool, str]:
    git("fetch", REMOTE, DEV_BRANCH)
    remote_dev = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
    if remote_dev != base_sha:
        return False, f"development_moved:{remote_dev}"
    guard = ROOT / "scripts" / "agent_guardrails" / "validate_repository_artifacts.py"
    if guard.is_file():
        check = run([sys.executable, str(guard)], cwd=ROOT)
        if check.returncode != 0:
            return False, "repository_artifact_guard_failed"
    push = run(["git", "push", REMOTE, f"{head}:refs/heads/{DEV_BRANCH}"], cwd=ROOT)
    if push.returncode != 0:
        return False, f"development_push_failed:{push.stdout[-1000:]}"
    git("fetch", REMOTE, DEV_BRANCH)
    after = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
    return after == head, after


def process_one(path: Path) -> int:
    envelope = load_envelope(path)
    job = envelope["job"]
    job_id = str(job.get("job_id") or "")
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("INVALID_JOB_ID")

    processing = PROCESSING / path.name
    os.replace(path, processing)
    result: dict[str, Any] = {
        "schema": "edarsahub.worker-result.v1",
        "job_id": job_id,
        "started_at_utc": now(),
        "status": "BLOCKED",
        "executor": EXECUTOR,
        "production_touched": False,
        "blockers": [],
    }

    worktree: Path | None = None
    branch = ""
    try:
        git("fetch", REMOTE, DEV_BRANCH)
        base_sha = git("rev-parse", f"{REMOTE}/{DEV_BRANCH}").stdout.strip()
        result["base_sha"] = base_sha
        worktree, branch = prepare_worktree(job_id, base_sha)
        result["job_branch"] = branch

        prompt = human_prompt(job, base_sha, job_id)
        if EXECUTOR != "codex":
            result["blockers"].append("unsupported_executor")
            result["executor_output"] = f"Executor no permitido: {EXECUTOR}"
        else:
            rc, output = execute_codex(worktree, prompt)
            result["executor_rc"] = rc
            result["executor_output"] = output
            if rc != 0:
                result["blockers"].append("executor_failed")

        worker_result, report_blockers = validate_result_file(worktree)
        result["blockers"].extend(report_blockers)
        if worker_result:
            result["summary_es"] = worker_result.get("summary_es")
            result["tests"] = worker_result.get("tests")
            result["quality_gate"] = worker_result.get("quality_gate")
            result["files_changed"] = worker_result.get("files_changed") or []

        head, commit_blockers = validate_commit(worktree, base_sha, job_id)
        result["blockers"].extend(commit_blockers)
        if head:
            result["candidate_sha"] = head

        if not result["blockers"] and head:
            ok, detail = integrate(head, base_sha)
            if ok:
                result["status"] = "INTEGRATED"
                result["development_sha"] = head
                result["percent_complete"] = 95
                result["certification"] = "PENDING_AUDIT_EVIDENCE"
            else:
                result["blockers"].append(detail)

        if result["status"] != "INTEGRATED":
            result["percent_complete"] = 0 if "executor_failed" in result["blockers"] else 80
            result["certification"] = "NOT_CERTIFIED"
    except Exception as exc:
        result["blockers"].append(f"dispatcher_exception:{type(exc).__name__}:{exc}")
        result["percent_complete"] = 0
        result["certification"] = "NOT_CERTIFIED"
    finally:
        result["completed_at_utc"] = now()
        write_json(RESULTS / path.name, result)
        target = DONE / path.name if result["status"] == "INTEGRATED" else REJECTED / path.name
        os.replace(processing, target)
        if worktree is not None:
            git("worktree", "remove", "--force", str(worktree), check=False)
        if branch:
            git("branch", "-D", branch, check=False)
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
