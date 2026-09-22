"""Independent READ_ONLY Worker Auditor authority boundary.

Worker Auditor certifies Worker Repair evidence. It never mutates the
repository, Worker runtime, services, SQL, Production, or application code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.mirror_sync.worker_maintenance_contract import (
    AUDITOR_AUTHORITY,
    auditor_scope_allowed,
)


@dataclass(frozen=True)
class AuditDecision:
    certified: bool
    reason: str
    production_touched: bool = False
    mutation_performed: bool = False


def audit_repair_result(result: dict[str, Any]) -> AuditDecision:
    paths = tuple(result.get("files_changed") or ())

    if result.get("production_touched") is not False:
        return AuditDecision(
            certified=False,
            reason="PRODUCTION_TOUCHED",
        )

    if not paths:
        return AuditDecision(
            certified=False,
            reason="NO_REPAIR_MUTATION_EVIDENCE",
        )

    if not auditor_scope_allowed(paths):
        return AuditDecision(
            certified=False,
            reason="REPAIR_SCOPE_OUTSIDE_WORKER_INFRASTRUCTURE",
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

    return AuditDecision(
        certified=True,
        reason="CERTIFIED_WORKER_REPAIR",
    )


def auditor_can_mutate() -> bool:
    return AUDITOR_AUTHORITY.mutation_allowed
