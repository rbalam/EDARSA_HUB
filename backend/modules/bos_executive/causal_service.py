from __future__ import annotations

from .contracts import (
    ConfidenceClass,
    EvidenceKind,
    ExecutiveFindingInput,
    ExecutiveFindingOutput,
    FindingStatus,
)

_KIND_PRIORITY = {
    EvidenceKind.HECHO: 0,
    EvidenceKind.CORRELACION: 1,
    EvidenceKind.INFERENCIA: 2,
}

_CONFIDENCE_BY_KIND = {
    EvidenceKind.HECHO: ConfidenceClass.DETERMINISTA,
    EvidenceKind.CORRELACION: ConfidenceClass.CORRELACIONAL,
    EvidenceKind.INFERENCIA: ConfidenceClass.INFERIDO,
}


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _classify(request: ExecutiveFindingInput) -> EvidenceKind:
    return max(
        (evidence.kind for evidence in request.evidence),
        key=lambda kind: _KIND_PRIORITY[kind],
    )


def _claim(observation: str, classification: EvidenceKind) -> str:
    if classification is EvidenceKind.HECHO:
        return f"Hecho observado y respaldado por evidencia: {observation}"
    if classification is EvidenceKind.CORRELACION:
        return f"Correlacion observada; no prueba causalidad: {observation}"
    return f"Inferencia basada en evidencia disponible; requiere validacion: {observation}"


def explain_causal_finding(request: ExecutiveFindingInput) -> ExecutiveFindingOutput:
    if not request.evidence:
        return ExecutiveFindingOutput(
            finding_id=request.finding_id,
            status=FindingStatus.NOT_ENOUGH_EVIDENCE,
            claim=FindingStatus.NOT_ENOUGH_EVIDENCE.value,
            evidence_refs=(),
            contributing_factors=(),
            classification=None,
            confidence_class=None,
            as_of=None,
            stale=False,
            limitations=_unique(request.limitations + ("NO_EVIDENCE",)),
            suggested_next_checks=_unique(request.suggested_next_checks),
        )

    classification = _classify(request)
    stale = any(evidence.stale for evidence in request.evidence)
    as_of_values = tuple(
        evidence.as_of for evidence in request.evidence if evidence.as_of
    )
    as_of = max(as_of_values) if as_of_values else None

    limitations = request.limitations
    if classification is EvidenceKind.CORRELACION:
        limitations += ("CORRELATION_IS_NOT_CAUSATION",)
    elif classification is EvidenceKind.INFERENCIA:
        limitations += ("INFERENCE_REQUIRES_VALIDATION",)
    if stale:
        limitations += ("STALE_EVIDENCE",)

    return ExecutiveFindingOutput(
        finding_id=request.finding_id,
        status=FindingStatus.EXPLAINED,
        claim=_claim(request.observation, classification),
        evidence_refs=_unique(tuple(evidence.ref for evidence in request.evidence)),
        contributing_factors=_unique(request.contributing_factors),
        classification=classification,
        confidence_class=_CONFIDENCE_BY_KIND[classification],
        as_of=as_of,
        stale=stale,
        limitations=_unique(limitations),
        suggested_next_checks=_unique(request.suggested_next_checks),
    )
