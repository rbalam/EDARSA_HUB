#!/usr/bin/env python3
"""Pure scope-aware concurrency policy for the EDARSAHUB Universal Worker."""

from __future__ import annotations

from typing import Iterable


def normalize_paths(paths: Iterable[str]) -> list[str]:
    return sorted({str(path).strip() for path in paths if str(path).strip()})


def evaluate_scope_advance(
    requested_base_sha: str | None,
    actual_head_sha: str,
    write_scope: Iterable[str],
    changed_paths: Iterable[str],
    *,
    allow_empty_scope_advance: bool = False,
) -> dict[str, object]:
    """Classify whether HEAD drift is safe for a deterministic job.

    This function does not inspect Git. The caller supplies the files changed
    between the requested base and the actual HEAD. A write job may continue
    only when those changes do not intersect its declared write scope.
    Read-only jobs can opt into empty-scope advancement explicitly.
    """
    scope = normalize_paths(write_scope)
    changed = normalize_paths(changed_paths)
    requested = str(requested_base_sha or "").strip() or None
    actual = str(actual_head_sha).strip()

    if not requested:
        return {
            "decision": "NO_REQUESTED_BASE",
            "requested_base_sha": None,
            "execution_base_sha": actual,
            "base_advanced": False,
            "changed_since_requested_base": [],
            "job_write_scope": scope,
            "scope_conflicts": [],
        }

    if requested == actual:
        return {
            "decision": "EXACT_BASE",
            "requested_base_sha": requested,
            "execution_base_sha": actual,
            "base_advanced": False,
            "changed_since_requested_base": [],
            "job_write_scope": scope,
            "scope_conflicts": [],
        }

    conflicts = sorted(set(scope).intersection(changed))
    if conflicts:
        decision = "SCOPE_CONFLICT"
    elif scope or allow_empty_scope_advance:
        decision = "SAFE_REPLAY"
    else:
        decision = "EMPTY_SCOPE_STRICT"

    return {
        "decision": decision,
        "requested_base_sha": requested,
        "execution_base_sha": actual,
        "base_advanced": True,
        "changed_since_requested_base": changed,
        "job_write_scope": scope,
        "scope_conflicts": conflicts,
    }
