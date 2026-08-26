#!/usr/bin/env python3
"""Publish sanitized worker results and SHA-bound test attestations.

This closes the runtime -> GitHub result path. It never publishes raw executor
output. Successful integrated jobs create a test attestation consumed by the
existing mirror audit exporter; unsuccessful jobs are still published to the
queue results branch as NOT_CERTIFIED/BLOCKED evidence.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("EDARSAHUB_ROOT", "/app"))
STATE = ROOT / ".git" / "universal-worker-queue"
RESULTS = STATE / "results"
PUBLISHED = STATE / "published"
QUEUE_BRANCH = os.environ.get("EDARSAHUB_QUEUE_BRANCH", "worker/requests")
REMOTE = os.environ.get("EDARSAHUB_QUEUE_REMOTE", "origin")
DEV_BRANCH = "Edarsahub_Desarrollo"
MIRROR_BRANCH = "mirror/emergent-live"
REPORT_DIR = Path(os.environ.get("MIRROR_SYNC_REPORT_STATE_DIR", "/app/.git/mirror-sync/reporting"))
ATTESTATIONS = REPORT_DIR / "test_attestations"
WORKTREE_PARENT = Path(
    os.environ.get(
        "EDARSAHUB_QUEUE_PUBLISH_WORKTREE_PARENT",
        "/tmp",
    )
)


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def git(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = run(["git", *args], cwd=cwd)
    if check and result.returncode != 0:
        raise RuntimeError(f"GIT_FAILED:{' '.join(args)}:{result.stdout[-1500:]}")
    return result


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("RESULT_NOT_OBJECT")
    return value


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp = handle.name
    os.replace(temp, path)


def valid_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(ch in "0123456789abcdef" for ch in value.lower())
    )


def certification_evidence(result: dict[str, Any]) -> dict[str, Any]:
    source_sha = result.get("development_sha")

    pending = {
        "certified": False,
        "certification": "PENDING_AUDIT_EVIDENCE",
        "work_completion": "PENDING_CERTIFICATION",
        "percent_complete": 95,
    }

    if result.get("status") != "INTEGRATED":
        return {
            **pending,
            "certification": "NOT_CERTIFIED",
            "work_completion": "NOT_CERTIFIED",
            "percent_complete": min(
                int(result.get("percent_complete") or 0),
                95,
            ),
        }

    if str(result.get("tests", "")).upper() != "PASS":
        return pending

    if str(result.get("quality_gate", "")).upper() != "PASS":
        return pending

    if result.get("production_touched") is not False:
        return pending

    if not valid_sha(source_sha):
        return pending

    attestation_path = (
        ATTESTATIONS / f"{source_sha}.json"
    )
    if not attestation_path.is_file():
        return pending

    try:
        attestation = load(attestation_path)
    except Exception:
        return pending

    if attestation.get("source_sha") != source_sha:
        return pending
    if attestation.get("job_id") != result.get("job_id"):
        return pending
    if str(attestation.get("tests", "")).upper() != "PASS":
        return pending
    if str(attestation.get("quality_gate", "")).upper() != "PASS":
        return pending
    if attestation.get("production_touched") is not False:
        return pending

    # Certification is allowed against a later converged descendant.
    # This is necessary when infrastructure fixes are integrated after
    # a job but the job's own files remain unchanged.
    git("fetch", REMOTE, DEV_BRANCH)
    git("fetch", REMOTE, MIRROR_BRANCH)

    development_head = git(
        "rev-parse",
        f"{REMOTE}/{DEV_BRANCH}",
    ).stdout.strip()

    mirror_head = git(
        "rev-parse",
        f"{REMOTE}/{MIRROR_BRANCH}",
    ).stdout.strip()

    if development_head != mirror_head:
        return pending

    ancestry = git(
        "merge-base",
        "--is-ancestor",
        source_sha,
        development_head,
        check=False,
    )
    if ancestry.returncode != 0:
        return pending

    files_changed = [
        str(value)
        for value in (result.get("files_changed") or [])
        if isinstance(value, str) and value
    ]

    if not files_changed:
        return pending

    artifact_check = git(
        "diff",
        "--quiet",
        source_sha,
        development_head,
        "--",
        *files_changed,
        check=False,
    )
    if artifact_check.returncode != 0:
        return pending

    return {
        "certified": True,
        "certification": "CERTIFIED",
        "work_completion": "COMPLETE",
        "percent_complete": 100,
        "certified_source_sha": source_sha,
        "converged_head": development_head,
        "certification_basis":
            "SHA_BOUND_ATTESTATION_PLUS_DESCENDANT_CONVERGENCE",
    }


def sanitize(result: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "schema", "job_id", "started_at_utc", "completed_at_utc", "status",
        "executor", "base_sha", "candidate_sha", "development_sha", "tests",
        "quality_gate", "files_changed", "summary_es", "blockers",
        "percent_complete", "certification", "production_touched",
    )
    public = {key: result.get(key) for key in allowed if key in result}
    public["published_at_utc"] = now()
    public["source_repo"] = "rbalam/EDARSA_HUB"
    public["source_branch"] = "Edarsahub_Desarrollo"
    public["human_summary_language"] = "es"
    public["human_summary_level"] = "13yo-non-programmer"
    evidence = certification_evidence(result)

    public["certification"] = evidence["certification"]
    public["work_completion"] = evidence["work_completion"]
    public["percent_complete"] = evidence["percent_complete"]

    for key in (
        "certified_source_sha",
        "converged_head",
        "certification_basis",
    ):
        if key in evidence:
            public[key] = evidence[key]

    return public


def create_attestation(public: dict[str, Any]) -> Path | None:
    sha = public.get("development_sha")
    if public.get("status") != "INTEGRATED" or not isinstance(sha, str) or len(sha) != 40:
        return None
    if str(public.get("tests", "")).upper() != "PASS" or str(public.get("quality_gate", "")).upper() != "PASS":
        return None
    payload = {
        "schema": "edarsahub.test-attestation.v1",
        "job_id": public.get("job_id"),
        "source_sha": sha,
        "tests": "PASS",
        "quality_gate": "PASS",
        "production_touched": public.get("production_touched") is True,
        "summary_es": public.get("summary_es"),
        "files_changed": public.get("files_changed") or [],
        "generated_at_utc": now(),
    }
    path = ATTESTATIONS / f"{sha}.json"
    atomic_json(path, payload)
    return path


def prepare_queue_worktree() -> tuple[Path, str]:
    """Create an isolated temporary checkout without registering a Git worktree.

    worker/requests is an infrastructure queue, not an agent development
    branch. Agent Guard reserves registered worktrees for agent/* branches.
    A temporary clone keeps publication isolated while preserving the
    canonical Agent Guard contract.
    """
    git("fetch", REMOTE, QUEUE_BRANCH)
    base = git("rev-parse", f"{REMOTE}/{QUEUE_BRANCH}").stdout.strip()

    WORKTREE_PARENT.mkdir(parents=True, exist_ok=True)

    worktree_root = Path(
        tempfile.mkdtemp(
            prefix="edarsahub-worker-result-publish-",
            dir=str(WORKTREE_PARENT),
        )
    )

    # git clone requiere que la ruta destino no exista.
    shutil.rmtree(worktree_root)

    origin_url = git("remote", "get-url", REMOTE).stdout.strip()

    clone = run(
        [
            "git",
            "clone",
            "--quiet",
            "--no-checkout",
            origin_url,
            str(worktree_root),
        ],
        cwd=ROOT,
    )

    if clone.returncode != 0 or not worktree_root.is_dir():
        shutil.rmtree(worktree_root, ignore_errors=True)
        raise RuntimeError(
            "RESULT_WORKTREE_NOT_CREATED:"
            + clone.stdout[-1500:]
        )

    git("checkout", "--detach", base, cwd=worktree_root)

    # El clone temporal no hereda la configuracion local de /app.
    # Copiar explicitamente el helper funcional evita caer en el
    # helper global de GitHub CLI, que puede no existir en runtime.
    credential_helper = git(
        "config",
        "--local",
        "--get",
        "credential.helper",
        cwd=ROOT,
        check=False,
    ).stdout.strip()

    if not credential_helper:
        raise RuntimeError("QUEUE_CREDENTIAL_HELPER_NOT_FOUND")

    git(
        "config",
        "--local",
        "credential.helper",
        credential_helper,
        cwd=worktree_root,
    )
    git(
        "config",
        "--local",
        "credential.useHttpPath",
        "true",
        cwd=worktree_root,
    )

    return worktree_root, base


def publish_one(path: Path) -> bool:
    PUBLISHED.mkdir(parents=True, exist_ok=True)
    marker = PUBLISHED / path.name

    result = load(path)
    public = sanitize(result)

    if marker.exists():
        marker_text = marker.read_text(
            encoding="utf-8",
            errors="replace",
        )
        desired = public.get("certification")
        if (
            desired == "CERTIFIED"
            and "certification=CERTIFIED" in marker_text
        ):
            return False
    job_id = str(public.get("job_id") or path.stem)
    if not job_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in job_id):
        raise ValueError("INVALID_JOB_ID")

    worktree, base = prepare_queue_worktree()
    try:
        destination = worktree / "worker_queue" / "results" / f"{job_id}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(public, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        git("add", "--", str(destination.relative_to(worktree)), cwd=worktree)
        staged = git("diff", "--cached", "--quiet", cwd=worktree, check=False)
        if staged.returncode == 0:
            marker.write_text(
                f"already_present={now()}\n"
                f"certification={public.get('certification')}\n",
                encoding="utf-8",
            )
            create_attestation(public)
            return False
        git("-c", "user.name=EDARSAHUB Worker", "-c", "user.email=worker@edarsahub.local", "commit", "-m", f"worker-result({job_id}): publish execution result", cwd=worktree)
        commit = git("rev-parse", "HEAD", cwd=worktree).stdout.strip()
        git("fetch", REMOTE, QUEUE_BRANCH)
        current = git("rev-parse", f"{REMOTE}/{QUEUE_BRANCH}").stdout.strip()
        if current != base:
            raise RuntimeError(f"QUEUE_BRANCH_MOVED:{current}")
        push_env = os.environ.copy()
        push_env["EDARSA_ALLOW_PUSH"] = "1"
        push = subprocess.run(
            ["git", "push", REMOTE, f"{commit}:refs/heads/{QUEUE_BRANCH}"],
            cwd=str(worktree),
            env=push_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if push.returncode != 0:
            raise RuntimeError(f"QUEUE_RESULT_PUSH_FAILED:{push.stdout[-1500:]}")
        create_attestation(public)
        marker.write_text(
            f"published={now()}\n"
            f"commit={commit}\n"
            f"certification={public.get('certification')}\n",
            encoding="utf-8",
        )
        print(f"UNIVERSAL_RESULT_PUBLISHED={job_id}")
        print(f"QUEUE_RESULT_COMMIT={commit}")
        if public.get("development_sha"):
            print(f"RESULT_DEVELOPMENT_SHA={public['development_sha']}")
        return True
    finally:
        shutil.rmtree(worktree, ignore_errors=True)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    count = 0
    errors = 0

    for path in sorted(RESULTS.glob("*.json")):
        try:
            if publish_one(path):
                count += 1
        except Exception as exc:
            errors += 1
            print(
                f"UNIVERSAL_RESULT_PUBLISH_ERROR="
                f"{path.name}:{type(exc).__name__}:{exc}"
            )

    print(f"UNIVERSAL_RESULTS_PUBLISHED_COUNT={count}")
    print(f"UNIVERSAL_RESULTS_PUBLISH_ERROR_COUNT={errors}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
