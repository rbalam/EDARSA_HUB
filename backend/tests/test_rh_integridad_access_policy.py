"""Offline security regression for confidential RH case authorization."""
from dataclasses import replace
from uuid import UUID
import pytest
from modules.rh.integridad_access_policy import CaseAction, CaseAccessContext, authorize_integrity_case


def allowed(**changes):
    base = CaseAccessContext(
        actor_id=7, case_id=UUID("11111111-1111-4111-8111-111111111111"),
        empresa_id=3, unidad_id=UUID("22222222-2222-4222-8222-222222222222"),
        identity_verified=True, actor_active=True, case_active=True,
        case_confidential=True, empresa_scope_verified=True,
        unidad_scope_verified=True, assignment_verified=True,
        assignment_active=True, conflict_check_verified=True,
        has_conflict=False, sql_permissions_verified=True,
        explicit_permissions=frozenset({CaseAction.VIEW.value}),
        access_revoked=False,
    )
    return replace(base, **changes)


def test_default_denies():
    ctx = CaseAccessContext(7, UUID("11111111-1111-4111-8111-111111111111"), 3, None)
    assert not authorize_integrity_case(ctx, CaseAction.VIEW).allowed


def test_valid_explicit_case_assignment_allows_only_requested_action():
    assert authorize_integrity_case(allowed(), CaseAction.VIEW).allowed
    assert not authorize_integrity_case(allowed(), CaseAction.VIEW_EVIDENCE).allowed
    assert not authorize_integrity_case(allowed(), CaseAction.INVESTIGATE).allowed


@pytest.mark.parametrize("field", [
    "identity_verified", "actor_active", "case_active", "case_confidential",
    "empresa_scope_verified", "unidad_scope_verified", "assignment_verified",
    "assignment_active", "conflict_check_verified", "sql_permissions_verified"
])
def test_missing_verification_denies(field):
    assert not authorize_integrity_case(allowed(**{field: False}), CaseAction.VIEW).allowed


@pytest.mark.parametrize("changes", [
    {"has_conflict": True}, {"access_revoked": True},
    {"assignment_active": False}, {"empresa_scope_verified": False},
    {"unidad_scope_verified": False}, {"sql_permissions_verified": False},
])
def test_conflict_revoke_and_cross_scope_denies(changes):
    assert not authorize_integrity_case(allowed(**changes), CaseAction.VIEW).allowed


@pytest.mark.parametrize("role", ["SUPERADMIN", "ADMINISTRADOR", "RH_ADMIN"])
def test_no_implicit_role_bypass(role):
    ctx = allowed(explicit_permissions=frozenset({role}))
    assert not authorize_integrity_case(ctx, CaseAction.VIEW).allowed


def test_invalid_identity_or_action_denied():
    assert not authorize_integrity_case(allowed(actor_id=0), CaseAction.VIEW).allowed
    assert not authorize_integrity_case(allowed(case_id=UUID(int=0)), CaseAction.VIEW).allowed
    assert not authorize_integrity_case(allowed(), "INTEGRIDAD_CASO_VER").allowed


def test_decision_does_not_contain_case_personal_data():
    result = authorize_integrity_case(allowed(), CaseAction.VIEW)
    assert set(vars(result)) == {"allowed", "reason_code"}
