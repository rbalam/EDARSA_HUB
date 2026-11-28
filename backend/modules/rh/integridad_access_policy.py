"""Fail-closed, pure access policy for RH confidential integrity cases.

Inputs are verified facts supplied by canonical SQL RBAC and case ownership;
this policy never queries SQL, stores records, or sends notifications.
"""
from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet
from uuid import UUID


class CaseAction(str, Enum):
    VIEW = "INTEGRIDAD_CASO_VER"
    INVESTIGATE = "INTEGRIDAD_CASO_INVESTIGAR"
    VIEW_EVIDENCE = "INTEGRIDAD_EVIDENCIA_VER"
    MANAGE_ACCESS = "INTEGRIDAD_CASO_GESTIONAR_ACCESOS"


@dataclass(frozen=True)
class CaseAccessContext:
    actor_id: int
    case_id: UUID
    empresa_id: int
    unidad_id: UUID | None
    identity_verified: bool = False
    actor_active: bool = False
    case_active: bool = False
    case_confidential: bool = False
    empresa_scope_verified: bool = False
    unidad_scope_verified: bool = False
    assignment_verified: bool = False
    assignment_active: bool = False
    conflict_check_verified: bool = False
    has_conflict: bool = True
    sql_permissions_verified: bool = False
    explicit_permissions: FrozenSet[str] = frozenset()
    access_revoked: bool = True


@dataclass(frozen=True)
class CaseAccessDecision:
    allowed: bool
    reason_code: str


def authorize_integrity_case(ctx: CaseAccessContext, action: CaseAction) -> CaseAccessDecision:
    """Requires effective SQL grant, current case assignment and no conflict.

    The future caller must resolve each verification independently, fail closed
    for stale/unknown results, and enforce the decision before reading SQL.
    """
    if not isinstance(ctx, CaseAccessContext) or not isinstance(action, CaseAction):
        return CaseAccessDecision(False, "INVALID_CONTEXT_OR_ACTION")
    if (type(ctx.actor_id) is not int or ctx.actor_id <= 0 or
        not isinstance(ctx.case_id, UUID) or ctx.case_id.int == 0 or
        type(ctx.empresa_id) is not int or ctx.empresa_id <= 0 or
        (ctx.unidad_id is not None and not isinstance(ctx.unidad_id, UUID))):
        return CaseAccessDecision(False, "INVALID_CANONICAL_IDENTITY")
    verified = (
        ctx.identity_verified, ctx.actor_active, ctx.case_active,
        ctx.case_confidential, ctx.empresa_scope_verified,
        ctx.unidad_scope_verified, ctx.assignment_verified,
        ctx.assignment_active, ctx.conflict_check_verified,
        ctx.sql_permissions_verified,
    )
    if any(value is not True for value in verified):
        return CaseAccessDecision(False, "REQUIRED_VERIFICATION_MISSING")
    if ctx.has_conflict is not False or ctx.access_revoked is not False:
        return CaseAccessDecision(False, "CONFLICT_OR_REVOKED")
    if not isinstance(ctx.explicit_permissions, frozenset):
        return CaseAccessDecision(False, "INVALID_PERMISSIONS")
    if action.value not in ctx.explicit_permissions:
        return CaseAccessDecision(False, "EXPLICIT_PERMISSION_DENIED")
    return CaseAccessDecision(True, "ACCESS_GRANTED")
