import pytest

from modules.cava_socios.blind_audit import (
    BlindAuditStatus,
    BlindObservation,
    ExpectedBottle,
    VisionReadinessRequest,
    VisionRecognitionCandidate,
    reconcile_blind_audit,
    validate_vision_candidates,
)


def test_blind_audit_clean_match():
    result = reconcile_blind_audit(
        [ExpectedBottle("B1", 1, 75.0)],
        [BlindObservation("O1", "photo-1", 1, 73.0, recognition_confidence=0.98)],
        observation_to_bottle={"O1": "B1"},
        level_tolerance_pct=5,
    )
    assert result.clean is True
    assert result.findings[0].status == BlindAuditStatus.MATCH


def test_blind_audit_detects_missing_and_unexpected():
    result = reconcile_blind_audit(
        [ExpectedBottle("B1"), ExpectedBottle("B2")],
        [BlindObservation("O1", "unknown")],
        observation_to_bottle={},
    )
    statuses = {f.status for f in result.findings}
    assert BlindAuditStatus.UNEXPECTED in statuses
    assert BlindAuditStatus.MISSING in statuses


def test_blind_audit_detects_quantity_and_level_mismatch():
    qty = reconcile_blind_audit(
        [ExpectedBottle("B1", 2, 80)],
        [BlindObservation("O1", "x", 1, 80, recognition_confidence=0.99)],
        observation_to_bottle={"O1": "B1"},
    )
    assert qty.findings[0].status == BlindAuditStatus.QUANTITY_MISMATCH

    level = reconcile_blind_audit(
        [ExpectedBottle("B1", 1, 80)],
        [BlindObservation("O1", "x", 1, 60, recognition_confidence=0.99)],
        observation_to_bottle={"O1": "B1"},
        level_tolerance_pct=5,
    )
    assert level.findings[0].status == BlindAuditStatus.LEVEL_MISMATCH


def test_low_recognition_confidence_requires_review_not_auto_match():
    result = reconcile_blind_audit(
        [ExpectedBottle("B1", 1, 80)],
        [BlindObservation("O1", "x", 1, 80, recognition_confidence=0.50)],
        observation_to_bottle={"O1": "B1"},
        min_recognition_confidence=0.90,
    )
    assert result.requires_review is True
    assert result.findings[0].status == BlindAuditStatus.REVIEW_REQUIRED


def test_vision_request_is_provider_neutral():
    req = VisionReadinessRequest(
        evidence_id="E1",
        storage_reference="obj://cavas/e1.jpg",
        required_capabilities=frozenset({"VISION_IMAGE_ANALYSIS", "BOTTLE_RECOGNITION"}),
        data_classification="INTERNAL",
        max_cost_usd=0.25,
        correlation_id="AUD-1",
    )
    assert "VISION_IMAGE_ANALYSIS" in req.required_capabilities


def test_vision_candidate_filter_does_not_make_canonical_decision():
    rows = (
        VisionRecognitionCandidate("sku-a", 0.95, {"label": "A"}),
        VisionRecognitionCandidate("sku-b", 0.40, {"label": "B"}),
    )
    kept = validate_vision_candidates(rows, min_confidence=0.90)
    assert [x.external_reference for x in kept] == ["sku-a"]


def test_invalid_percentages_and_confidence_fail_closed():
    with pytest.raises(ValueError):
        ExpectedBottle("B1", 1, 101)
    with pytest.raises(ValueError):
        BlindObservation("O1", "x", recognition_confidence=1.5)
