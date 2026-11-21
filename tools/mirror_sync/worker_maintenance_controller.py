"""Canonical maintenance-plane lifecycle for Universal Worker repair.

This module coordinates maintenance incidents only.

It does not:
- consume normal EDARSAHUB development jobs,
- touch Production,
- execute arbitrary shell or SQL,
- duplicate Universal Worker dispatching,
- bypass Agent Guard or Git Divergence Guard.

Lifecycle:
DECLARED -> REPAIR_REQUIRED -> REPAIRED_PENDING_AUDIT ->
CERTIFIED | REJECTED
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from tools.mirror_sync.worker_auditor import audit_repair_result
from tools.mirror_sync.worker_maintenance_contract import (
    PROTECTED_UNIVERSAL_COMPONENTS,
    auditor_scope_allowed,
    normalize_repo_path,
)
from tools.mirror_sync.worker_repair import (
    RepairPlan,
    build_repair_plan,
    repair_requires_independent_audit,
)


class MaintenanceState(str, Enum):
    DECLARED = "DECLARED"
    REPAIR_REQUIRED = "REPAIR_REQUIRED"
    REPAIRED_PENDING_AUDIT = "REPAIRED_PENDING_AUDIT"
    CERTIFIED = "CERTIFIED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class MaintenanceIncident:
    incident_id: str
    paths: tuple[str, ...]
    state: MaintenanceState
    capability_code: str | None = None
    production_allowed: bool = False


@dataclass(frozen=True)
class MaintenanceDecision:
    incident_id: str
    state: MaintenanceState
    reason: str
    certified: bool = False
    production_touched: bool = False


def declare_incident(
    incident_id: str,
    paths: list[str] | tuple[str, ...],
    *,
    capability_code: str | None = None,
) -> MaintenanceIncident:
    plan = build_repair_plan(
        incident_id,
        paths,
        capability_code=capability_code,
    )

    return MaintenanceIncident(
        incident_id=plan.incident_id,
        paths=plan.paths,
        state=MaintenanceState.REPAIR_REQUIRED,
        capability_code=plan.capability_code,
    )


def repair_plan_for(
    incident: MaintenanceIncident,
) -> RepairPlan:
    if incident.state is not MaintenanceState.REPAIR_REQUIRED:
        raise ValueError("MAINTENANCE_INCIDENT_NOT_REPAIRABLE")

    return build_repair_plan(
        incident.incident_id,
        incident.paths,
        capability_code=incident.capability_code,
    )


def repaired_pending_audit(
    incident: MaintenanceIncident,
    repair_result: dict[str, Any],
) -> MaintenanceDecision:
    if incident.state is not MaintenanceState.REPAIR_REQUIRED:
        raise ValueError("MAINTENANCE_INCIDENT_INVALID_STATE")

    if not repair_requires_independent_audit(
        repair_plan_for(incident)
    ):
        raise RuntimeError("INDEPENDENT_AUDIT_REQUIRED")

    if repair_result.get("production_touched") is not False:
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="PRODUCTION_TOUCHED",
            production_touched=True,
        )

    if repair_result.get("git_sync_status") != "CERTIFIED_GIT_SYNC":
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="REPAIR_NOT_GIT_CERTIFIED",
        )

    if repair_result.get("quality_gate") != "PASS":
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="QUALITY_GATE_NOT_PASS",
        )

    if repair_result.get("tests") != "PASS":
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="TESTS_NOT_PASS",
        )

    if repair_result.get("blockers") not in ([], None):
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="BLOCKERS_PRESENT",
        )

    files_changed = tuple(
        repair_result.get("files_changed") or ()
    )
    if not files_changed:
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="NO_REPAIR_MUTATION_EVIDENCE",
        )

    try:
        normalized_changed = tuple(
            normalize_repo_path(str(path))
            for path in files_changed
        )
        normalized_incident = tuple(
            normalize_repo_path(str(path))
            for path in incident.paths
        )
    except ValueError:
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="REPAIR_SCOPE_OUTSIDE_WORKER_INFRASTRUCTURE",
        )

    if not auditor_scope_allowed(
        normalized_changed,
        incident_id=incident.incident_id,
        capability_code=incident.capability_code,
    ):
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="REPAIR_SCOPE_OUTSIDE_WORKER_INFRASTRUCTURE",
        )

    if not set(normalized_changed).issubset(
        set(normalized_incident)
    ):
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="REPAIR_SCOPE_OUTSIDE_INCIDENT_AUTHORIZATION",
        )

    if (
        any(
            path
            in PROTECTED_UNIVERSAL_COMPONENTS
            for path in normalized_changed
        )
        and repair_result.get(
            "protected_component_authorized"
        )
        is False
    ):
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="PROTECTED_COMPONENT_UNAUTHORIZED",
        )

    return MaintenanceDecision(
        incident_id=incident.incident_id,
        state=MaintenanceState.REPAIRED_PENDING_AUDIT,
        reason="REPAIR_EVIDENCE_READY",
    )


def audit_incident(
    incident: MaintenanceIncident,
    repair_result: dict[str, Any],
    *,
    require_pending_audit_state: bool = False,
    expected_job_id: str | None = None,
    expected_result_sha256: str | None = None,
    expected_commit_sha: str | None = None,
    verify_canonical_result: bool = False,
    results_dir: Path | None = None,
    verify_git_diff: bool = False,
    repo_root: Path | None = None,
    require_protected_authorization: bool = False,
) -> MaintenanceDecision:
    if (
        isinstance(repair_result, dict)
        and repair_result.get(
            "production_touched"
        )
        is not False
    ):
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="PRODUCTION_TOUCHED",
            certified=False,
            production_touched=True,
        )

    if incident.state in {
        MaintenanceState.REJECTED,
        MaintenanceState.SUPERSEDED,
    }:
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="INCIDENT_STATE_NOT_AUDITABLE",
            certified=False,
        )

    if (
        require_pending_audit_state
        and incident.state
        is not MaintenanceState.REPAIRED_PENDING_AUDIT
    ):
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason="INCIDENT_NOT_PENDING_AUDIT",
            certified=False,
        )

    audit = audit_repair_result(
        repair_result,
        authorized_paths=incident.paths,
        expected_job_id=expected_job_id,
        expected_result_sha256=expected_result_sha256,
        expected_commit_sha=expected_commit_sha,
        verify_canonical_result=verify_canonical_result,
        results_dir=results_dir,
        verify_git_diff=verify_git_diff,
        repo_root=repo_root,
        require_protected_authorization=require_protected_authorization,
        incident_id=incident.incident_id,
        capability_code=incident.capability_code,
    )

    if not audit.certified:
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason=audit.reason,
            certified=False,
            production_touched=audit.production_touched,
        )

    return MaintenanceDecision(
        incident_id=incident.incident_id,
        state=MaintenanceState.CERTIFIED,
        reason="CERTIFIED_WORKER_REPAIR",
        certified=True,
    )
