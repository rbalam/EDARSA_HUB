#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import PurePosixPath

NORMAL_FILE_LIMIT = 5 * 1024 * 1024
HARD_FILE_LIMIT = 20 * 1024 * 1024
CHANGE_LIMIT = 25 * 1024 * 1024
NEW_FILE_LIMIT = 50
DELETE_FILE_LIMIT = 10
DELETE_BYTES_LIMIT = 5 * 1024 * 1024
SHRINK_MIN_BASE_SIZE = 4 * 1024
SHRINK_RATIO = 0.75

CRITICAL_DELETE_PATHS = {
    "backend/server.py",
    "tools/mirror_sync/universal_job_bridge.py",
    "tools/mirror_sync/universal_job_dispatcher.py",
    "tools/mirror_sync/shared_app_safety_guard.sh",
    "tools/mirror_sync/apply_remote_update.sh",
    "scripts/agent_guardrails/validate_repository_artifacts.py",
}

ROOT_BLOCKED_EXTENSIONS = {
    ".txt",
    ".json",
    ".patch",
    ".sql",
    ".log",
    ".csv",
}

GENERATED_ROOT_PREFIXES = (
    "edarsahub_",
    "v1_",
    "auditoria_",
    "AUDITORIA_",
    "economia_",
    "joblogger_",
)

ZERO_SHA = "0" * 40


def run_git(*args: str, text: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    )
    return result.stdout


def fail(message: str) -> None:
    print(f"REPOSITORY_ARTIFACT_GUARD_BLOCKED: {message}", file=sys.stderr)


def blob_size(spec: str) -> int:
    try:
        value = run_git("cat-file", "-s", spec).strip()
        return int(value)
    except Exception:
        return 0


def staged_changes() -> list[tuple[str, str]]:
    raw = run_git(
        "diff",
        "--cached",
        "--name-status",
        "--diff-filter=ACMRD",
        "-z",
    )

    parts = raw.split("\0")
    changes: list[tuple[str, str]] = []
    i = 0

    while i < len(parts):
        if not parts[i]:
            break

        status = parts[i]
        i += 1

        if status.startswith("R") or status.startswith("C"):
            if i + 1 >= len(parts):
                break
            i += 1
            path = parts[i]
            i += 1
        else:
            if i >= len(parts):
                break
            path = parts[i]
            i += 1

        changes.append((status[:1], path))

    return changes


def range_changes(base: str, head: str) -> list[tuple[str, str]]:
    raw = run_git(
        "diff",
        "--name-status",
        "--diff-filter=ACMRD",
        "-z",
        base,
        head,
    )

    parts = raw.split("\0")
    changes: list[tuple[str, str]] = []
    i = 0

    while i < len(parts):
        if not parts[i]:
            break

        status = parts[i]
        i += 1

        if status.startswith("R") or status.startswith("C"):
            if i + 1 >= len(parts):
                break
            i += 1
            path = parts[i]
            i += 1
        else:
            if i >= len(parts):
                break
            path = parts[i]
            i += 1

        changes.append((status[:1], path))

    return changes



# EDARSA_MIRROR_RESEED_GUARD_V3
def _edarsa_parse_pre_push_updates(pre_push_path):
    """Parse canonical Git pre-push input without hidden global state."""
    from pathlib import Path

    if not pre_push_path:
        return []

    path = Path(pre_push_path)

    if not path.is_file():
        return []

    updates = []

    for raw in path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        parts = raw.split()

        if len(parts) != 4:
            continue

        updates.append(
            {
                "local_ref": parts[0],
                "local_sha": parts[1],
                "remote_ref": parts[2],
                "remote_sha": parts[3],
            }
        )

    return updates


def _edarsa_is_certified_mirror_reseed(pre_push_path):
    """
    Permit only the specific non-destructive canonical mirror reseed.

    Requirements:
      - exactly one mirror/emergent-live update;
      - candidate has exactly two parents;
      - parent 1 is current origin/Edarsahub_Desarrollo;
      - parent 2 is current remote mirror SHA;
      - candidate tree equals Development tree;
      - old mirror is ancestor of candidate.

    This does not disable Agent Guard and does not permit force-push.
    """
    import subprocess

    updates = _edarsa_parse_pre_push_updates(
        pre_push_path
    )

    matching = [
        row
        for row in updates
        if row["remote_ref"]
        == "refs/heads/mirror/emergent-live"
    ]

    if len(matching) != 1:
        return False

    update = matching[0]

    local_sha = update["local_sha"]
    remote_sha = update["remote_sha"]

    zero_sha = "0" * 40

    if local_sha == zero_sha or remote_sha == zero_sha:
        return False

    def git(*args):
        proc = subprocess.run(
            ["git", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

        if proc.returncode != 0:
            return None

        return proc.stdout.strip()

    development = git(
        "rev-parse",
        "origin/Edarsahub_Desarrollo",
    )

    if not development:
        return False

    parents_raw = git(
        "show",
        "-s",
        "--format=%P",
        local_sha,
    )

    if not parents_raw:
        return False

    parents = parents_raw.split()

    if len(parents) != 2:
        return False

    if parents[0] != development:
        return False

    if parents[1] != remote_sha:
        return False

    candidate_tree = git(
        "rev-parse",
        f"{local_sha}^{{tree}}",
    )

    development_tree = git(
        "rev-parse",
        f"{development}^{{tree}}",
    )

    if not candidate_tree or not development_tree:
        return False

    if candidate_tree != development_tree:
        return False

    ancestor = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            remote_sha,
            local_sha,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    return ancestor.returncode == 0
# /EDARSA_MIRROR_RESEED_GUARD_V3


def validate(
    changes: list[tuple[str, str]],
    size_resolver,
    previous_size_resolver=None,
    pre_push_path: str | None = None,
) -> int:
    violations: list[str] = []
    added_count = 0
    total_added_bytes = 0
    deleted_count = 0
    total_deleted_bytes = 0

    for status, path in changes:
        posix = PurePosixPath(path)
        size = size_resolver(path)
        previous_size = previous_size_resolver(path) if previous_size_resolver else 0

        if status == "D":
            deleted_count += 1
            total_deleted_bytes += previous_size
            if path in CRITICAL_DELETE_PATHS:
                violations.append(f"archivo critico no puede eliminarse: {path}")
            continue

        if (
            status in {"M", "R"}
            and previous_size >= SHRINK_MIN_BASE_SIZE
            and size < int(previous_size * SHRINK_RATIO)
        ):
            violations.append(
                f"reduccion destructiva bloqueada: {path} "
                f"({previous_size} -> {size} bytes)"
            )

        if status == "A":
            added_count += 1
            total_added_bytes += size

        if len(posix.parts) == 1:
            if posix.suffix.lower() in ROOT_BLOCKED_EXTENSIONS:
                violations.append(
                    f"artefacto generado en raiz prohibido: {path}"
                )

            if path.startswith(GENERATED_ROOT_PREFIXES):
                violations.append(
                    f"patron de salida generada en raiz: {path}"
                )

        if size > HARD_FILE_LIMIT:
            violations.append(
                f"archivo supera limite fuerte de 20 MiB: "
                f"{path} ({size} bytes)"
            )
        elif size > NORMAL_FILE_LIMIT:
            violations.append(
                f"archivo supera limite normal de 5 MiB: "
                f"{path} ({size} bytes)"
            )

    if deleted_count > DELETE_FILE_LIMIT:
        violations.append(
            f"demasiados archivos eliminados: {deleted_count} > {DELETE_FILE_LIMIT}"
        )

    if total_deleted_bytes > DELETE_BYTES_LIMIT:
        violations.append(
            f"bytes eliminados superan 5 MiB: {total_deleted_bytes} bytes"
        )

    if added_count > NEW_FILE_LIMIT:
        if _edarsa_is_certified_mirror_reseed(pre_push_path):
            pass
        else:
            violations.append(
                f"demasiados archivos nuevos: "
                f"{added_count} > {NEW_FILE_LIMIT}"
            )

    if total_added_bytes > CHANGE_LIMIT:
        violations.append(
            f"crecimiento agregado supera 25 MiB: "
            f"{total_added_bytes} bytes"
        )

    if violations:
        for item in violations:
            fail(item)
        return 1

    print("REPOSITORY_ARTIFACT_GUARD=PASS")
    print(f"FILES_CHECKED={len(changes)}")
    print(f"NEW_FILES={added_count}")
    print(f"NEW_BYTES={total_added_bytes}")
    print(f"DELETED_FILES={deleted_count}")
    print(f"DELETED_BYTES={total_deleted_bytes}")
    return 0


def validate_staged() -> int:
    changes = staged_changes()
    return validate(
        changes,
        lambda path: blob_size(f":{path}"),
        lambda path: blob_size(f"HEAD:{path}"),
    )


def validate_range(base: str, head: str,
    pre_push_path: str | None = None,
) -> int:
    changes = range_changes(base, head)
    return validate(
        changes,
        lambda path: blob_size(f"{head}:{path}"),
        lambda path: blob_size(f"{base}:{path}"),
        pre_push_path=pre_push_path,
    )


def validate_pre_push_input(path: str) -> int:
    with open(path, "r", encoding="utf-8") as handle:
        lines = [
            line.strip()
            for line in handle
            if line.strip()
        ]

    for line in lines:
        fields = line.split()

        if len(fields) != 4:
            fail("entrada pre-push invalida")
            return 1

        _local_ref, local_sha, _remote_ref, remote_sha = fields

        if local_sha == ZERO_SHA:
            continue

        if remote_sha == ZERO_SHA:
            try:
                base = run_git(
                    "merge-base",
                    local_sha,
                    "origin/Edarsahub_Desarrollo",
                ).strip()
            except Exception:
                fail("no fue posible resolver base para nueva referencia")
                return 1
        else:
            base = remote_sha

        rc = validate_range(base, local_sha, pre_push_path=path)

        if rc != 0:
            return rc

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--staged",
        action="store_true",
    )

    group.add_argument(
        "--range",
        nargs=2,
        metavar=("BASE", "HEAD"),
    )

    group.add_argument(
        "--pre-push-input",
    )

    args = parser.parse_args()

    if args.staged:
        return validate_staged()

    if args.range:
        return validate_range(
            args.range[0],
            args.range[1],
        )

    if args.pre_push_input:
        return validate_pre_push_input(
            args.pre_push_input
        )

    return 2


if __name__ == "__main__":
    sys.exit(main())
