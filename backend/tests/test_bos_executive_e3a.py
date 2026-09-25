from modules.bos_executive import (
    ConfidenceClass,
    EvidenceKind,
    EvidenceRef,
    ExecutiveFindingInput,
    FindingStatus,
    explain_causal_finding,
)


def _request(*evidence, **overrides):
    values = {
        "finding_id": "finding-1",
        "metric_id": "ventas_sin_propina",
        "scope_ref": "empresa:1/unidad:ESTELAR",
        "period_ref": "2026-09",
        "observation": "La venta disminuyo frente al periodo comparable.",
        "evidence": tuple(evidence),
        "contributing_factors": ("trafico_menor",),
        "limitations": (),
        "suggested_next_checks": ("validar_eventos_calendario",),
    }
    values.update(overrides)
    return ExecutiveFindingInput(**values)


def test_e3a_fails_closed_without_evidence():
    result = explain_causal_finding(_request())

    assert result.status is FindingStatus.NOT_ENOUGH_EVIDENCE
    assert result.claim == "NOT_ENOUGH_EVIDENCE"
    assert result.evidence_refs == ()
    assert result.contributing_factors == ()
    assert result.classification is None
    assert result.confidence_class is None
    assert "NO_EVIDENCE" in result.limitations


def test_e3a_fact_is_deterministic_when_all_evidence_is_fact():
    result = explain_causal_finding(
        _request(
            EvidenceRef(
                ref="sql:kpi:ventas:2026-09",
                kind=EvidenceKind.HECHO,
                as_of="2026-09-18T23:59:59Z",
                provenance="EDARSAHUB_SQL",
            )
        )
    )

    assert result.status is FindingStatus.EXPLAINED
    assert result.classification is EvidenceKind.HECHO
    assert result.confidence_class is ConfidenceClass.DETERMINISTA
    assert result.stale is False
    assert result.evidence_refs == ("sql:kpi:ventas:2026-09",)


def test_e3a_correlation_never_becomes_causality():
    result = explain_causal_finding(
        _request(
            EvidenceRef(ref="sql:kpi:ventas", kind=EvidenceKind.HECHO),
            EvidenceRef(ref="audit:traffic", kind=EvidenceKind.CORRELACION),
        )
    )

    assert result.classification is EvidenceKind.CORRELACION
    assert result.confidence_class is ConfidenceClass.CORRELACIONAL
    assert "no prueba causalidad" in result.claim
    assert "CORRELATION_IS_NOT_CAUSATION" in result.limitations


def test_e3a_inference_is_conservative_and_requires_validation():
    result = explain_causal_finding(
        _request(
            EvidenceRef(ref="workflow:event-1", kind=EvidenceKind.INFERENCIA)
        )
    )

    assert result.classification is EvidenceKind.INFERENCIA
    assert result.confidence_class is ConfidenceClass.INFERIDO
    assert "requiere validacion" in result.claim
    assert "INFERENCE_REQUIRES_VALIDATION" in result.limitations


def test_e3a_marks_stale_if_any_evidence_is_stale():
    result = explain_causal_finding(
        _request(
            EvidenceRef(
                ref="sql:kpi:ventas",
                kind=EvidenceKind.HECHO,
                as_of="2026-09-17T23:59:59Z",
                stale=True,
            ),
            EvidenceRef(
                ref="audit:ops",
                kind=EvidenceKind.HECHO,
                as_of="2026-09-18T23:59:59Z",
            ),
        )
    )

    assert result.stale is True
    assert result.as_of == "2026-09-18T23:59:59Z"
    assert "STALE_EVIDENCE" in result.limitations
