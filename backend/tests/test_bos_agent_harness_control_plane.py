from __future__ import annotations

import pytest

from modules.agent_harness.control_plane import (
    BudgetEnvelope, ControlPlane, ControlPlaneError, EvidenceSummary, GateState,
)


def test_snapshot_is_deterministic_and_read_only_composition():
    snapshot = ControlPlane().snapshot(
        gates=[GateState('AH2', 'CERTIFIED', 100), GateState('AH1', 'CERTIFIED_READ_ONLY', 100)],
        budgets=[BudgetEnvelope('ai_cost', 100.0, 25.0)],
        evidence=[EvidenceSummary('req-1', 'job-1', True, False)],
    )
    assert tuple(g.gate_id for g in snapshot.gates) == ('AH1', 'AH2')
    assert snapshot.certified_gates == ('AH1', 'AH2')
    assert snapshot.budgets[0].remaining == 75.0
    assert snapshot.healthy is True


def test_nonterminal_gate_is_rejected():
    with pytest.raises(ControlPlaneError, match='GATE_STATUS_NOT_TERMINAL'):
        GateState('AH9', 'RUNNING', 50)


def test_certified_gate_must_be_complete_and_blocker_free():
    with pytest.raises(ControlPlaneError, match='CERTIFIED_GATE_NOT_COMPLETE'):
        GateState('AH1', 'CERTIFIED', 80)
    with pytest.raises(ControlPlaneError, match='CERTIFIED_GATE_HAS_BLOCKERS'):
        GateState('AH1', 'CERTIFIED', 100, ('x',))


def test_production_touched_is_fail_closed():
    with pytest.raises(ControlPlaneError, match='PRODUCTION_TOUCHED_FORBIDDEN'):
        GateState('AH1', 'BLOCKED', 80, production_touched=True)
    with pytest.raises(ControlPlaneError, match='EVIDENCE_PRODUCTION_TOUCHED'):
        EvidenceSummary('req', 'job', False, True)


def test_budget_overrun_is_fail_closed():
    with pytest.raises(ControlPlaneError, match='BUDGET_EXCEEDED'):
        BudgetEnvelope('ai_cost', 10.0, 11.0)


def test_duplicate_gate_and_budget_names_are_rejected():
    with pytest.raises(ControlPlaneError, match='DUPLICATE_GATE_ID'):
        ControlPlane().snapshot(gates=[GateState('AH1', 'CERTIFIED', 100), GateState('AH1', 'CERTIFIED', 100)])
    with pytest.raises(ControlPlaneError, match='DUPLICATE_BUDGET_NAME'):
        ControlPlane().snapshot(
            gates=[GateState('AH1', 'CERTIFIED', 100)],
            budgets=[BudgetEnvelope('ai', 10, 1), BudgetEnvelope('ai', 10, 2)],
        )


def test_blocked_gate_surfaces_blockers_and_health():
    snapshot = ControlPlane().snapshot(gates=[GateState('AH9', 'BLOCKED', 80, ('pytest',))])
    assert snapshot.blockers == ('pytest',)
    assert snapshot.healthy is False
