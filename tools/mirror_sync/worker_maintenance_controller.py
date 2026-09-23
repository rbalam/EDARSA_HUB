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
from typing import Any

from tools.mirror_sync.worker_auditor import audit_repair_result
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


@dataclass(frozen=True)
class MaintenanceIncident:
    incident_id: str
    paths: tuple[str, ...]
    state: MaintenanceState
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
) -> MaintenanceIncident:
    plan = build_repair_plan(
        incident_id,
        paths,
    )

    return MaintenanceIncident(
        incident_id=plan.incident_id,
        paths=plan.paths,
        state=MaintenanceState.REPAIR_REQUIRED,
    )


def repair_plan_for(
    incident: MaintenanceIncident,
) -> RepairPlan:
    if incident.state is not MaintenanceState.REPAIR_REQUIRED:
        raise ValueError("MAINTENANCE_INCIDENT_NOT_REPAIRABLE")

    return build_repair_plan(
        incident.incident_id,
        incident.paths,
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

    return MaintenanceDecision(
        incident_id=incident.incident_id,
        state=MaintenanceState.REPAIRED_PENDING_AUDIT,
        reason="REPAIR_EVIDENCE_READY",
    )


def audit_incident(
    incident: MaintenanceIncident,
    repair_result: dict[str, Any],
) -> MaintenanceDecision:
    audit = audit_repair_result(repair_result)

    if not audit.certified:
        return MaintenanceDecision(
            incident_id=incident.incident_id,
            state=MaintenanceState.REJECTED,
            reason=audit.reason,
            certified=False,
        )

    return MaintenanceDecision(
        incident_id=incident.incident_id,
        state=MaintenanceState.CERTIFIED,
        reason="CERTIFIED_WORKER_REPAIR",
        certified=True,
    )
