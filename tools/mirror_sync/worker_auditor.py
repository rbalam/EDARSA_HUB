"""Independent READ_ONLY Worker Auditor authority boundary.

Worker Auditor certifies Worker Repair evidence. It never mutates the
repository, Worker runtime, services, SQL, Production, or application code.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.mirror_sync.worker_maintenance_contract import (
    AUDITOR_AUTHORITY,
    PROTECTED_UNIVERSAL_COMPONENTS,
    auditor_scope_allowed,
    normalize_repo_path,
)
from tools.mirror_sync.worker_result_reader import (
    read_canonical_result,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_DIR = (
    ROOT / ".git" / "universal-worker-queue" / "results"
)
GIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class AuditDecision:
    certified: bool
    reason: str
    production_touched: bool = False
    mutation_performed: bool = False


def _is_valid_git_sha(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and GIT_SHA_RE.fullmatch(value.strip())
    )


def verify_git_commit_diff(
    base_sha: str,
    commit_sha: str,
    *,
    repo_root: Path | None = None,
) -> tuple[bool, str, tuple[str, ...]]:
    root = repo_root or ROOT
    base = str(base_sha or "").strip()
    commit = str(commit_sha or "").strip()

    if not _is_valid_git_sha(base) or not _is_valid_git_sha(commit):
        return (
            False,
            "REPAIR_GIT_COMMIT_METADATA_MISSING",
            (),
        )

    for ref in (base, commit):
        verified = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "cat-file",
                "-e",
                f"{ref}^{{commit}}",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if verified.returncode != 0:
            return (
                False,
                "REPAIR_GIT_COMMIT_NOT_FOUND",
                (),
            )

    lineage = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "merge-base",
            "--is-ancestor",
            base,
            commit,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if lineage.returncode != 0:
        return (
            False,
            "REPAIR_GIT_LINEAGE_INVALID",
            (),
        )

    diff = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "diff",
            "--name-only",
            base,
            commit,
            "--",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if diff.returncode != 0:
        return (
            False,
            "REPAIR_GIT_DIFF_FAILED",
            (),
        )

    try:
        committed_paths = tuple(
            sorted(
                {
                    normalize_repo_path(line)
                    for line in (
                        diff.stdout or ""
                    ).splitlines()
                    if line.strip()
                }
            )
        )
    except ValueError:
        return (
            False,
            "REPAIR_SCOPE_OUTSIDE_WORKER_INFRASTRUCTURE",
            (),
        )

    return (
        True,
        "GIT_DIFF_VERIFIED",
        committed_paths,
    )


def read_independent_canonical_result(
    job_id: str,
    *,
    results_dir: Path | None = None,
) -> tuple[bool, str, dict[str, Any] | None, str | None]:
    clean_job_id = str(job_id or "").strip()
    if not clean_job_id:
        return (
            False,
            "REPAIR_JOB_ID_MISSING",
            None,
            None,
        )

    target_dir = (
        DEFAULT_RESULTS_DIR
        if results_dir is None
        else results_dir
    )
    result_path = (
        target_dir / f"{clean_job_id}.json"
    )
    canonical = read_canonical_result(
        result_path,
        expected_job_id=clean_job_id,
    )
    if (
        not canonical.terminal_result_valid
        or not isinstance(canonical.payload, dict)
    ):
        return (
            False,
            f"CANONICAL_RESULT_INVALID:{canonical.state}",
            None,
            None,
        )

    payload = dict(canonical.payload)
    payload["result_sha256"] = (
        canonical.result_sha256
    )

    if (
        payload.get("certification")
        == "PENDING_AUDIT_EVIDENCE"
    ):
        published_path = (
            target_dir.parent
            / "published"
            / f"{clean_job_id}.json"
        )
        if published_path.is_file():
            try:
                published = json.loads(
                    published_path.read_text(
                        encoding="utf-8"
                    )
                )
            except (
                OSError,
                json.JSONDecodeError,
            ):
                published = None
            if (
                isinstance(published, dict)
                and published.get("status")
                == "PUBLISHED"
                and published.get(
                    "certification"
                )
                == "CERTIFIED"
                and str(
                    published.get("job_id")
                    or clean_job_id
                )
                == clean_job_id
                and (
                    not published.get(
                        "result_sha256"
                    )
                    or str(
                        published.get(
                            "result_sha256"
                        )
                    ).lower()
                    == str(
                        canonical.result_sha256
                        or ""
                    ).lower()
                )
            ):
                payload["certification"] = (
                    "CERTIFIED"
                )
                payload[
                    "published_certification_verified"
                ] = True

    return (
        True,
        "CANONICAL_RESULT_VERIFIED",
        payload,
        canonical.result_sha256,
    )


def audit_repair_result(
    result: dict[str, Any],
    *,
    authorized_paths: list[str] | tuple[str, ...] | None = None,
    expected_job_id: str | None = None,
    expected_result_sha256: str | None = None,
    expected_commit_sha: str | None = None,
    verify_canonical_result: bool = False,
    results_dir: Path | None = None,
    verify_git_diff: bool = False,
    repo_root: Path | None = None,
    require_protected_authorization: bool = False,
    incident_id: str | None = None,
    capability_code: str | None = None,
) -> AuditDecision:
    if not isinstance(result, dict):
        return AuditDecision(
            certified=False,
            reason="INVALID_RESULT_PAYLOAD",
        )

    if verify_canonical_result:
        target_job_id = str(
            expected_job_id
            or result.get("job_id")
            or ""
        ).strip()
        ok, reason, canonical_payload, canonical_sha = (
            read_independent_canonical_result(
                target_job_id,
                results_dir=results_dir,
            )
        )
        if not ok or canonical_payload is None:
            return AuditDecision(
                certified=False,
                reason=reason,
            )
        caller_sha = (
            str(
                expected_result_sha256
                or result.get("result_sha256")
                or ""
            )
            .strip()
            .lower()
        )
        if (
            caller_sha
            and caller_sha
            != str(canonical_sha or "").lower()
        ):
            return AuditDecision(
                certified=False,
                reason="REPAIR_RESULT_SHA256_MISMATCH",
            )
        result = canonical_payload

    if result.get("production_touched") is not False:
        return AuditDecision(
            certified=False,
            reason="PRODUCTION_TOUCHED",
            production_touched=True,
        )

    if expected_job_id is not None:
        actual_job_id = str(
            result.get("job_id") or ""
        ).strip()
        if (
            actual_job_id
            and actual_job_id
            != str(expected_job_id).strip()
        ):
            return AuditDecision(
                certified=False,
                reason="REPAIR_JOB_ID_MISMATCH",
            )
        if (
            not actual_job_id
            and "job_id" in result
        ):
            return AuditDecision(
                certified=False,
                reason="REPAIR_JOB_ID_MISMATCH",
            )

    if expected_result_sha256 is not None:
        actual_sha = (
            str(result.get("result_sha256") or "")
            .strip()
            .lower()
        )
        if (
            not actual_sha
            or actual_sha
            != str(expected_result_sha256)
            .strip()
            .lower()
        ):
            return AuditDecision(
                certified=False,
                reason="REPAIR_RESULT_SHA256_MISMATCH",
            )

    if expected_commit_sha is not None:
        actual_commit = (
            str(
                result.get("development_sha")
                or result.get("candidate_sha")
                or result.get("commit_created")
                or ""
            )
            .strip()
            .lower()
        )
        if (
            not actual_commit
            or actual_commit
            != str(expected_commit_sha)
            .strip()
            .lower()
        ):
            return AuditDecision(
                certified=False,
                reason="REPAIR_COMMIT_SHA_MISMATCH",
            )

    paths = tuple(result.get("files_changed") or ())

    if not paths:
        return AuditDecision(
            certified=False,
            reason="NO_REPAIR_MUTATION_EVIDENCE",
        )

    try:
        normalized_paths = tuple(
            normalize_repo_path(str(path))
            for path in paths
        )
    except ValueError:
        return AuditDecision(
            certified=False,
            reason="REPAIR_SCOPE_OUTSIDE_WORKER_INFRASTRUCTURE",
        )

    if not auditor_scope_allowed(
        normalized_paths,
        incident_id=incident_id,
        capability_code=capability_code,
    ):
        return AuditDecision(
            certified=False,
            reason="REPAIR_SCOPE_OUTSIDE_WORKER_INFRASTRUCTURE",
        )

    normalized_authorized: tuple[str, ...] | None = None
    if authorized_paths is not None:
        try:
            normalized_authorized = tuple(
                normalize_repo_path(str(path))
                for path in authorized_paths
            )
        except ValueError:
            return AuditDecision(
                certified=False,
                reason="REPAIR_SCOPE_OUTSIDE_INCIDENT_AUTHORIZATION",
            )
        if (
            not normalized_authorized
            or not set(normalized_paths).issubset(
                set(normalized_authorized)
            )
        ):
            return AuditDecision(
                certified=False,
                reason="REPAIR_SCOPE_OUTSIDE_INCIDENT_AUTHORIZATION",
            )

    if "status" in result and result.get("status") != "INTEGRATED":
        return AuditDecision(
            certified=False,
            reason="RESULT_NOT_INTEGRATED",
        )

    if (
        "certification" in result
        and result.get("certification") != "CERTIFIED"
    ):
        return AuditDecision(
            certified=False,
            reason="RESULT_NOT_CERTIFIED",
        )

    if result.get("quality_gate") != "PASS":
        return AuditDecision(
            certified=False,
            reason="QUALITY_GATE_NOT_PASS",
        )

    if result.get("tests") != "PASS":
        return AuditDecision(
            certified=False,
            reason="TESTS_NOT_PASS",
        )

    if result.get("blockers") not in ([], None):
        return AuditDecision(
            certified=False,
            reason="BLOCKERS_PRESENT",
        )

    if result.get("git_sync_status") != "CERTIFIED_GIT_SYNC":
        return AuditDecision(
            certified=False,
            reason="GIT_SYNC_NOT_CERTIFIED",
        )

    touches_protected = any(
        path in PROTECTED_UNIVERSAL_COMPONENTS
        for path in normalized_paths
    )
    if touches_protected:
        if (
            result.get(
                "protected_component_authorized"
            )
            is False
        ):
            return AuditDecision(
                certified=False,
                reason="PROTECTED_COMPONENT_UNAUTHORIZED",
            )
        if (
            require_protected_authorization
            and result.get(
                "protected_component_authorized"
            )
            is not True
        ):
            return AuditDecision(
                certified=False,
                reason="PROTECTED_COMPONENT_AUTHORIZATION_REQUIRED",
            )

    if verify_git_diff:
        base_sha = str(
            result.get("execution_base_sha")
            or result.get("base_sha")
            or ""
        ).strip()
        commit_sha = str(
            result.get("development_sha")
            or result.get("candidate_sha")
            or result.get("commit_created")
            or ""
        ).strip()
        diff_ok, diff_reason, committed_paths = (
            verify_git_commit_diff(
                base_sha,
                commit_sha,
                repo_root=repo_root,
            )
        )
        if not diff_ok:
            return AuditDecision(
                certified=False,
                reason=diff_reason,
            )
        if set(committed_paths) != set(
            normalized_paths
        ):
            return AuditDecision(
                certified=False,
                reason="REPAIR_GIT_DIFF_MISMATCH",
            )
        if not auditor_scope_allowed(
            committed_paths,
            incident_id=incident_id,
            capability_code=capability_code,
        ):
            return AuditDecision(
                certified=False,
                reason="REPAIR_SCOPE_OUTSIDE_WORKER_INFRASTRUCTURE",
            )
        if (
            normalized_authorized is not None
            and not set(
                committed_paths
            ).issubset(
                set(normalized_authorized)
            )
        ):
            return AuditDecision(
                certified=False,
                reason="REPAIR_SCOPE_OUTSIDE_INCIDENT_AUTHORIZATION",
            )

    return AuditDecision(
        certified=True,
        reason="CERTIFIED_WORKER_REPAIR",
    )


def auditor_can_mutate() -> bool:
    return AUDITOR_AUTHORITY.mutation_allowed
