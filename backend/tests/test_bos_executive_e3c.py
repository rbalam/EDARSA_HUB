# E3C_TESTS_V1

from modules.bos_executive import (
    ConfidenceClass,
    ExecutiveFindingOutput,
    FindingStatus,
    RecommendationRisk,
    adapt_operational_task,
    recommend_from_finding,
    recommend_from_priority,
)


def _finding(**overrides):
    values = {
        "finding_id": "finding-1",
        "status": FindingStatus.EXPLAINED,
        "claim": "Hecho observado",
        "evidence_refs": ("sql:kpi:ventas",),
        "contributing_factors": (),
        "classification": None,
        "confidence_class": ConfidenceClass.DETERMINISTA,
        "as_of": "2026-10-26T23:59:59Z",
        "stale": False,
        "limitations": (),
        "suggested_next_checks": (),
    }
    values.update(overrides)
    return ExecutiveFindingOutput(**values)


def test_e3c_finding_without_evidence_fails_closed():
    finding = _finding(status=FindingStatus.NOT_ENOUGH_EVIDENCE, evidence_refs=(), confidence_class=None)
    result = recommend_from_finding(
        finding,
        generated_at="2026-10-27T00:00:00Z",
        valid_until="2026-10-28T00:00:00Z",
        expected_impact="N/A",
    )
    assert result is None


def test_e3c_finding_recommendation_is_deterministic():
    kwargs = {
        "generated_at": "2026-10-27T00:00:00Z",
        "valid_until": "2026-10-28T00:00:00Z",
        "expected_impact": "Reducir desviacion",
        "eligible_actions": ("REQUEST_EXISTING_WORKFLOW", "REQUEST_EXISTING_WORKFLOW"),
    }
    first = recommend_from_finding(_finding(), **kwargs)
    second = recommend_from_finding(_finding(), **kwargs)
    assert first is not None and second is not None
    assert first == second
    assert first.recommendation_id == second.recommendation_id
    assert first.eligible_actions == ("REQUEST_EXISTING_WORKFLOW",)
    assert first.human_confirmation_required is True


def test_e3c_priority_requires_evidence_and_propagates_controls():
    item = adapt_operational_task({
        "id": "T-88",
        "estado_sla": "VENCIDA",
        "impacto": "riesgo_operativo_alto",
        "permission_refs": ["OPERATIVO_VER", "OPERATIVO_ATENDER"],
        "stale": True,
    })
    assert item is not None
    missing = recommend_from_priority(
        item,
        evidence_refs=(),
        generated_at="2026-10-27T00:00:00Z",
        valid_until="2026-10-28T00:00:00Z",
    )
    assert missing is None
    result = recommend_from_priority(
        item,
        evidence_refs=("workflow:tarea:T-88",),
        generated_at="2026-10-27T00:00:00Z",
        valid_until="2026-10-28T00:00:00Z",
        eligible_actions=("REQUEST_EXISTING_WORKFLOW",),
    )
    assert result is not None
    assert result.risk_level is RecommendationRisk.HIGH
    assert result.required_permissions == ("OPERATIVO_VER", "OPERATIVO_ATENDER")
    assert result.eligible_actions == ("REQUEST_EXISTING_WORKFLOW",)
    assert result.human_confirmation_required is True
    assert result.stale is True
