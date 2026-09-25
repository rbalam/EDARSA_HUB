#!/usr/bin/env python3
"""Idempotent publisher for declared EDARSAHUB gate-chain jobs.

Publication is opt-in with --publish. Default behavior is plan-only.

Canonical publication invariants:
- Worker requests are written only through a registered Agent Guard worktree.
- The publisher claim is limited to exactly one worker_queue/inbox/<job>.json.
- Push authorization is delegated to git_divergence_guard.authorized_push.
- worker/requests is updated only when its remote tip has not moved.
- No force push, hook bypass, Production mutation, SQL, or arbitrary shell.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mirror_sync.gate_chain_controller import validate_chain
from tools.mirror_sync.git_divergence_guard import (
    authorized_push,
    validate_commit_scope,
)
from tools.mirror_sync.worker_job_factory import canonicalize_job

JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")

ALLOWED_ACTIONS = {
    "replace_text",
    "write_file",
    "delete_file",
}

ALLOWED_CHECKS = {
    "git_diff_check",
    "py_compile",
    "pytest",
    "frontend_build",
    "sql_readonly_audit",
    "repository_contract_audit",
}

FORBIDDEN_KEYS = {
    "sql",
    "command",
    "commands",
    "shell",
    "script_body",
    "password",
    "passwd",
    "secret",
    "token",
    "credential",
}

AGENT_GUARD = ROOT / ".git" / "agent-guard" / "bin" / "agent_guard.py"
AGENT_WORKTREES = ROOT / ".git" / "agent-worktrees"

VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
PYTHON_BIN = str(VENV_PYTHON if VENV_PYTHON.is_file() else Path(sys.executable))


def _walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).lower(), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def validate_template(template: dict[str, Any]) -> dict[str, Any]:
    template = canonicalize_job(template)

    if template.get("schema") != "edarsahub.worker-job.v2":
        raise ValueError("INVALID_JOB_TEMPLATE_SCHEMA")

    job_id = str(template.get("job_id") or "").strip()

    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("INVALID_JOB_ID")

    if template.get("production_allowed") is not False:
        raise ValueError("PRODUCTION_FORBIDDEN")

    for key, _ in _walk(template):
        if key in FORBIDDEN_KEYS:
            raise ValueError(f"FORBIDDEN_TEMPLATE_KEY:{key}")

    for action in template.get("actions") or []:
        if (
            not isinstance(action, dict)
            or str(action.get("type")) not in ALLOWED_ACTIONS
        ):
            raise ValueError("UNSUPPORTED_ACTION")

    for check in template.get("checks") or []:
        if (
            not isinstance(check, dict)
            or str(check.get("type")) not in ALLOWED_CHECKS
        ):
            raise ValueError("UNSUPPORTED_CHECK")

    return template


def gate_for(
    chain: dict[str, Any],
    gate_id: str,
) -> dict[str, Any]:
    validate_chain(chain)

    for gate in chain.get("gates") or []:
        if str(gate.get("gate_id") or "").strip() == gate_id:
            return gate

    raise ValueError("NEXT_GATE_NOT_DECLARED")


def build_plan(
    chain: dict[str, Any],
    decision: dict[str, Any],
    existing_job_ids: set[str],
) -> dict[str, Any]:
    if str(
        decision.get("state")
        or decision.get("action")
        or ""
    ).upper() != "READY":
        raise ValueError("DECISION_NOT_READY")

    gate_id = str(decision.get("next_gate_id") or "").strip()
    gate = gate_for(chain, gate_id)
    template = validate_template(gate.get("job_template"))

    job_id = str(template["job_id"])

    if job_id in existing_job_ids:
        return {
            "status": "EXISTS",
            "job_id": job_id,
            "gate_id": gate_id,
            "publish": False,
        }

    return {
        "status": "READY_TO_PUBLISH",
        "job_id": job_id,
        "gate_id": gate_id,
        "publish": True,
        "template": template,
    }


def run(
    args: list[str],
    cwd: Path | None = None,
):
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def git(
    *args: str,
    cwd: Path | None = None,
    check: bool = True,
):
    result = run(["git", *args], cwd)

    if check and result.returncode:
        raise RuntimeError(
            f"GIT_FAILED:{' '.join(args)}:{result.stdout[-1200:]}"
        )

    return result


def _safe_id(job_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "-", job_id)


def _queue_remote_head(
    remote: str,
    queue_branch: str,
) -> str:
    result = git(
        "ls-remote",
        remote,
        f"refs/heads/{queue_branch}",
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"QUEUE_REMOTE_HEAD_UNAVAILABLE:{result.stdout[-1200:]}"
        )

    fields = result.stdout.strip().split()

    if not fields or not re.fullmatch(r"[0-9a-f]{40}", fields[0]):
        raise RuntimeError("QUEUE_REMOTE_HEAD_INVALID")

    return fields[0]


def _release_agent_guard(agent_id: str) -> tuple[bool, str]:
    if not AGENT_GUARD.is_file():
        return False, "AGENT_GUARD_NOT_FOUND"

    released = run(
        [
            PYTHON_BIN,
            str(AGENT_GUARD),
            "release",
            "--agent-id",
            agent_id,
        ],
        ROOT,
    )

    return (
        released.returncode == 0,
        (released.stdout or "")[-1500:],
    )


def _prepare_queue_worktree(
    *,
    job_id: str,
    queue_base: str,
    rel: str,
) -> tuple[Path, str, str, str]:
    if not AGENT_GUARD.is_file():
        raise RuntimeError("AGENT_GUARD_NOT_FOUND")

    safe_id = _safe_id(job_id)

    branch = f"agent/queue-publisher/{safe_id}"
    agent_id = f"queue-publisher-{safe_id}"
    task_id = f"QUEUE-PUBLISH-{safe_id}"

    worktree = AGENT_WORKTREES / f"queue-publisher-{safe_id}"

    branch_ref = f"refs/heads/{branch}"

    branch_exists = git(
        "show-ref",
        "--verify",
        "--quiet",
        branch_ref,
        check=False,
    ).returncode == 0

    worktree_exists = worktree.exists()

    if branch_exists or worktree_exists:
        if not (branch_exists and worktree_exists):
            raise RuntimeError(
                "QUEUE_PUBLISHER_RESIDUAL_STATE_INCOMPLETE"
            )

        branch_sha = git(
            "rev-parse",
            branch,
        ).stdout.strip()

        worktree_sha = git(
            "rev-parse",
            "HEAD",
            cwd=worktree,
        ).stdout.strip()

        if branch_sha != worktree_sha:
            raise RuntimeError(
                "QUEUE_PUBLISHER_RESIDUAL_HEAD_MISMATCH"
            )

        status = git(
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            cwd=worktree,
            check=False,
        ).stdout.strip()

        if status:
            raise RuntimeError(
                "QUEUE_PUBLISHER_RESIDUAL_WORKTREE_DIRTY"
            )

        parent = git(
            "rev-parse",
            f"{worktree_sha}^",
            cwd=worktree,
            check=False,
        ).stdout.strip()

        if parent != queue_base:
            raise RuntimeError(
                "QUEUE_PUBLISHER_RESIDUAL_LINEAGE_INVALID"
            )

        target = worktree / rel

        if not target.is_file():
            raise RuntimeError(
                "QUEUE_PUBLISHER_RESIDUAL_REQUEST_MISSING"
            )

        validate_commit_scope(
            worktree,
            queue_base,
            worktree_sha,
            {rel},
        )

        return (
            worktree,
            branch,
            agent_id,
            task_id,
        )

    git("branch", branch, queue_base)

    command = [
        PYTHON_BIN,
        str(AGENT_GUARD),
        "worktree-create",
        "--agent-id",
        agent_id,
        "--task-id",
        task_id,
        "--description",
        f"Publish Universal Worker Gate request {job_id}",
        "--domain",
        "worker_queue_publication",
        "--branch",
        branch,
        "--directory",
        str(worktree),
        "--path",
        rel,
    ]

    created = run(command, ROOT)

    if created.returncode != 0:
        git("branch", "-D", branch, check=False)
        raise RuntimeError(
            "AGENT_GUARD_WORKTREE_CREATE_FAILED:"
            + (created.stdout or "")[-2000:]
        )

    if not worktree.is_dir():
        _release_agent_guard(agent_id)
        git("branch", "-D", branch, check=False)
        raise RuntimeError("AGENT_GUARD_WORKTREE_NOT_CREATED")

    actual = git(
        "rev-parse",
        "HEAD",
        cwd=worktree,
    ).stdout.strip()

    if actual != queue_base:
        _release_agent_guard(agent_id)
        raise RuntimeError(
            f"WORKTREE_BASE_MISMATCH:"
            f"expected={queue_base}:actual={actual}"
        )

    return worktree, branch, agent_id, task_id


def _cleanup_queue_worktree(
    *,
    worktree: Path,
    branch: str,
    agent_id: str,
    success: bool,
) -> list[str]:
    errors: list[str] = []

    released, release_output = _release_agent_guard(agent_id)

    if not released:
        errors.append(
            "AGENT_GUARD_RELEASE_FAILED:"
            + release_output[-800:]
        )

    if worktree.is_dir():
        status = git(
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            cwd=worktree,
            check=False,
        ).stdout.strip()

        if status:
            errors.append(
                "QUEUE_PUBLISHER_WORKTREE_DIRTY_PRESERVED"
            )
        else:
            removed = git(
                "worktree",
                "remove",
                str(worktree),
                check=False,
            )

            if removed.returncode != 0:
                errors.append(
                    "QUEUE_PUBLISHER_WORKTREE_REMOVE_FAILED:"
                    + (removed.stdout or "")[-800:]
                )

    if success and not worktree.exists():
        deleted = git(
            "branch",
            "-D",
            branch,
            check=False,
        )

        if deleted.returncode != 0:
            errors.append(
                "QUEUE_PUBLISHER_BRANCH_REMOVE_FAILED:"
                + (deleted.stdout or "")[-800:]
            )

    return errors


def publish(
    plan: dict[str, Any],
    remote: str = "origin",
    queue_branch: str = "worker/requests",
) -> dict[str, Any]:
    if plan.get("status") == "EXISTS":
        return {
            **plan,
            "result": "REMOTE_JOB=EXISTS",
        }

    if plan.get("status") != "READY_TO_PUBLISH":
        raise ValueError("PLAN_NOT_PUBLISHABLE")

    job_id = str(plan["job_id"])
    template = validate_template(plan["template"])

    rel = f"worker_queue/inbox/{job_id}.json"

    git("fetch", remote, queue_branch)

    queue_base = git(
        "rev-parse",
        f"{remote}/{queue_branch}",
    ).stdout.strip()

    if not re.fullmatch(r"[0-9a-f]{40}", queue_base):
        raise RuntimeError("QUEUE_BASE_SHA_INVALID")

    if git(
        "cat-file",
        "-e",
        f"{remote}/{queue_branch}:{rel}",
        check=False,
    ).returncode == 0:
        return {
            "status": "EXISTS",
            "job_id": job_id,
            "publish": False,
            "result": "REMOTE_JOB=EXISTS",
        }

    worktree, branch, agent_id, task_id = _prepare_queue_worktree(
        job_id=job_id,
        queue_base=queue_base,
        rel=rel,
    )

    current_head = git(
        "rev-parse",
        "HEAD",
        cwd=worktree,
    ).stdout.strip()

    resumed_existing = current_head != queue_base

    success = False
    cleanup_errors: list[str] = []

    try:
        target = worktree / rel

        expected_payload = (
            json.dumps(
                template,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        if resumed_existing:
            if not target.is_file():
                raise RuntimeError(
                    "QUEUE_PUBLISHER_RESIDUAL_REQUEST_MISSING"
                )

            actual_payload = target.read_text(
                encoding="utf-8",
            )

            if actual_payload != expected_payload:
                raise RuntimeError(
                    "QUEUE_PUBLISHER_RESIDUAL_REQUEST_MISMATCH"
                )
        else:
            if target.exists():
                return {
                    "status": "EXISTS",
                    "job_id": job_id,
                    "publish": False,
                    "result": "REMOTE_JOB=EXISTS",
                }

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            target.write_text(
                expected_payload,
                encoding="utf-8",
            )

            git(
                "add",
                "--",
                rel,
                cwd=worktree,
            )

        staged = [
            line.strip()
            for line in git(
                "diff",
                "--cached",
                "--name-only",
                cwd=worktree,
            ).stdout.splitlines()
            if line.strip()
        ]

        if resumed_existing:
            if staged:
                raise RuntimeError(
                    f"RESUME_STAGED_SCOPE_NOT_EMPTY:{staged}"
                )

            candidate = current_head
        else:
            if staged != [rel]:
                raise RuntimeError(
                    f"STAGED_SCOPE_MISMATCH:{staged}"
                )

            git(
                "commit",
                "-m",
                f"orchestrator: enqueue {job_id}",
                cwd=worktree,
            )

            candidate = git(
                "rev-parse",
                "HEAD",
                cwd=worktree,
            ).stdout.strip()

        if not re.fullmatch(r"[0-9a-f]{40}", candidate):
            raise RuntimeError("INVALID_COMMIT_SHA")

        parent = git(
            "rev-parse",
            f"{candidate}^",
            cwd=worktree,
        ).stdout.strip()

        if parent != queue_base:
            raise RuntimeError(
                "QUEUE_PUBLISHER_LINEAGE_INVALID"
            )

        validate_commit_scope(
            worktree,
            queue_base,
            candidate,
            {rel},
        )

        remote_now = _queue_remote_head(
            remote,
            queue_branch,
        )

        if remote_now != queue_base:
            raise RuntimeError(
                "REMOTE_MOVED_RETRY_REQUIRED:"
                f"start={queue_base}:now={remote_now}"
            )

        pushed = authorized_push(
            worktree,
            args=[
                "push",
                remote,
                f"{candidate}:refs/heads/{queue_branch}",
            ],
            job_id=task_id,
            owner="edarsahub-gate-publisher",
        )

        if pushed.returncode != 0:
            raise RuntimeError(
                "PUSH_FAILED:"
                + (pushed.stdout or "")[-1200:]
            )

        remote_after = _queue_remote_head(
            remote,
            queue_branch,
        )

        if remote_after != candidate:
            raise RuntimeError(
                "REMOTE_COMMIT_MISMATCH:"
                f"expected={candidate}:actual={remote_after}"
            )

        git(
            "fetch",
            remote,
            queue_branch,
        )

        if git(
            "cat-file",
            "-e",
            f"{remote}/{queue_branch}:{rel}",
            check=False,
        ).returncode != 0:
            raise RuntimeError("REMOTE_JOB_MISSING")

        success = True

        return {
            "status": "PUBLISHED",
            "job_id": job_id,
            "commit_sha": candidate,
            "queue_base_sha": queue_base,
            "remote_after": remote_after,
            "agent_guard_registered_worktree": True,
            "exact_scope": [rel],
            "authorized_push": True,
            "resumed_existing_publication": resumed_existing,
            "production_touched": False,
            "result": (
                "GATE_RESUMED_AND_ENQUEUED=PASS"
                if resumed_existing
                else "GATE_ENQUEUED=PASS"
            ),
        }

    finally:
        cleanup_errors = _cleanup_queue_worktree(
            worktree=worktree,
            branch=branch,
            agent_id=agent_id,
            success=success,
        )

        if cleanup_errors and success:
            raise RuntimeError(
                "QUEUE_PUBLISHER_CLEANUP_FAILED:"
                + "|".join(cleanup_errors)
            )


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--chain-json",
        required=True,
    )

    parser.add_argument(
        "--decision-json",
        required=True,
    )

    parser.add_argument(
        "--existing-job-ids-json",
        default="[]",
    )

    parser.add_argument(
        "--publish",
        action="store_true",
    )

    args = parser.parse_args()

    chain = json.loads(
        Path(args.chain_json).read_text(
            encoding="utf-8",
        )
    )

    decision = json.loads(
        Path(args.decision_json).read_text(
            encoding="utf-8",
        )
    )

    existing = set(
        json.loads(args.existing_job_ids_json)
    )

    plan = build_plan(
        chain,
        decision,
        existing,
    )

    result = (
        publish(plan)
        if args.publish
        else plan
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
