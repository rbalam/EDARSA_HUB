"""Worker Repair authority boundary.

Worker Repair is a maintenance-plane component for repairing Universal Worker
infrastructure. It does not participate in normal EDARSAHUB code creation.

This foundation intentionally contains validation/planning only. Git mutation
and runtime supervision are wired in later gates through existing canonical
lower-level guards rather than duplicating Universal Worker.
"""
from __future__ import annotations

from dataclasses import dataclass

from tools.mirror_sync.worker_maintenance_contract import (
    PROTECTED_UNIVERSAL_COMPONENTS,
    REPAIR_AUTHORITY,
    repair_scope_allowed,
)


@dataclass(frozen=True)
class RepairPlan:
    incident_id: str
    paths: tuple[str, ...]
    authority: str = REPAIR_AUTHORITY.role
    production_allowed: bool = False


def build_repair_plan(
    incident_id: str,
    paths: list[str] | tuple[str, ...],
) -> RepairPlan:
    incident = str(incident_id or "").strip()

    if not incident:
        raise ValueError("REPAIR_INCIDENT_ID_REQUIRED")

    clean_paths = tuple(str(path).strip() for path in paths)

    if not repair_scope_allowed(clean_paths):
        raise ValueError("REPAIR_SCOPE_FORBIDDEN")

    return RepairPlan(
        incident_id=incident,
        paths=clean_paths,
    )


def touches_protected_universal_component(plan: RepairPlan) -> bool:
    return bool(
        set(plan.paths).intersection(PROTECTED_UNIVERSAL_COMPONENTS)
    )


def repair_requires_independent_audit(plan: RepairPlan) -> bool:
    # Every Worker Repair mutation requires Worker Auditor certification.
    return True
