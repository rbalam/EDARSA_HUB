#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CRITICAL_FILES = {
    "backend/server.py",
    "backend/core/security.py",
}

CRITICAL_PREFIXES = (
    "backend/modules/auth/",
    "tools/mirror_sync/",
    "tools/bootstrap/",
)

MAX_CRITICAL_LINE_LOSS_RATIO = 0.30

REQUIRED_SERVER_MARKERS = (
    "include_router",
)

REQUIRED_ROUTE_MARKERS = (
    "/api/auth/login",
    "/api/health",
)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def historical_backup(path: str) -> bool:
    name = Path(path).name.lower()
    return (
        name.endswith(".bak")
        or ".bak_" in name
        or name.endswith(".backup")
        or ".backup_" in name
    )


def critical(path: str) -> bool:
    if historical_backup(path):
        return False
    if path in CRITICAL_FILES:
        return True
    return any(path.startswith(prefix) for prefix in CRITICAL_PREFIXES)


def file_at(ref: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{ref}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="surrogateescape")


def lines(text: str | None) -> int:
    if text is None:
        return 0
    return len(text.splitlines())


def changed_paths(base: str, head: str) -> list[str]:
    out = git("diff", "--name-only", base, head)
    return [line.strip() for line in out.splitlines() if line.strip()]


def validate_file_loss(base: str, head: str, path: str) -> list[str]:
    errors = []

    # Non-runtime artifacts, including arbitrary binaries, are never decoded.
    if not critical(path):
        return errors

    before = file_at(base, path)
    after = file_at(head, path)

    if before is None:
        return errors

    if after is None:
        errors.append(f"CRITICAL_FILE_DELETED:{path}")
        return errors

    before_count = lines(before)
    after_count = lines(after)

    if before_count > 0:
        loss = max(0, before_count - after_count)
        ratio = loss / before_count

        if ratio > MAX_CRITICAL_LINE_LOSS_RATIO:
            errors.append(
                f"CRITICAL_LINE_LOSS:{path}:"
                f"before={before_count}:after={after_count}:"
                f"ratio={ratio:.4f}"
            )

    return errors


def validate_server(base: str, head: str) -> list[str]:
    errors = []

    before = file_at(base, "backend/server.py")
    after = file_at(head, "backend/server.py")

    if before is None or after is None:
        return errors

    for marker in REQUIRED_SERVER_MARKERS:
        if marker in before and marker not in after:
            errors.append(f"SERVER_MARKER_REMOVED:{marker}")

    before_router_count = before.count("include_router")
    after_router_count = after.count("include_router")

    if before_router_count >= 5:
        minimum = max(1, int(before_router_count * 0.70))

        if after_router_count < minimum:
            errors.append(
                "ROUTER_COUNT_COLLAPSE:"
                f"before={before_router_count}:"
                f"after={after_router_count}:"
                f"minimum={minimum}"
            )

    return errors


def validate_repository_markers(head: str) -> list[str]:
    errors = []

    searchable = [
        "backend",
    ]

    for marker in REQUIRED_ROUTE_MARKERS:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "grep",
                "-F",
                marker,
                head,
                "--",
                *searchable,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        if result.returncode != 0:
            errors.append(f"REQUIRED_ROUTE_MISSING:{marker}")

    return errors


def validate(base: str, head: str) -> list[str]:
    errors = []

    for path in changed_paths(base, head):
        errors.extend(validate_file_loss(base, head, path))

    errors.extend(validate_server(base, head))
    errors.extend(validate_repository_markers(head))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    errors = validate(args.base, args.head)

    if errors:
        print("EDARSAHUB_DESTRUCTIVE_DIFF_GUARD=FAIL")
        for error in errors:
            print(error)
        return 1

    print("EDARSAHUB_DESTRUCTIVE_DIFF_GUARD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
