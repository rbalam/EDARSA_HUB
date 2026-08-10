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
        "--diff-filter=ACMR",
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
        "--diff-filter=ACMR",
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


def validate(
    changes: list[tuple[str, str]],
    size_resolver,
) -> int:
    violations: list[str] = []
    added_count = 0
    total_added_bytes = 0

    for status, path in changes:
        posix = PurePosixPath(path)
        size = size_resolver(path)

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

    if added_count > NEW_FILE_LIMIT:
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
    return 0


def validate_staged() -> int:
    changes = staged_changes()
    return validate(
        changes,
        lambda path: blob_size(f":{path}"),
    )


def validate_range(base: str, head: str) -> int:
    changes = range_changes(base, head)
    return validate(
        changes,
        lambda path: blob_size(f"{head}:{path}"),
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

        rc = validate_range(base, local_sha)

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
