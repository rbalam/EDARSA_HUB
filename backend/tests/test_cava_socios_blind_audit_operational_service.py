from modules.cava_socios.blind_audit_operational_service import (
    CavaBlindAuditOperationalService,
)


def _service():
    return CavaBlindAuditOperationalService()


def test_gate16i_clean_audit_is_confirmed_and_non_mutating():
    result = _service().reconcile(
        inventory_rows=[
            {"botella_id": "B1", "porcentaje_restante": 75.0},
        ],
        observations=[
            {
                "observation_id": "O1",
                "observed_reference": "manual:B1",
                "observed_quantity": 1,
                "observed_level_pct": 74.0,
            }
        ],
        observation_to_bottle={"O1": "B1"},
        idempotency_key="audit-001",
    )
    assert result["outcome"] == "CONFIRMED"
    assert result["clean"] is True
    assert result["automatic_inventory_adjustment"] is False
    assert result["automatic_inventory_movement"] is False


def test_gate16i_difference_never_adjusts_inventory():
    result = _service().reconcile(
        inventory_rows=[
            {"botella_id": "B1", "porcentaje_restante": 80.0},
        ],
        observations=[
            {
                "observation_id": "O1",
                "observed_reference": "manual:B1",
                "observed_quantity": 1,
                "observed_level_pct": 40.0,
            }
        ],
        observation_to_bottle={"O1": "B1"},
        idempotency_key="audit-002",
    )
    assert result["outcome"] == "DIFFERENCE"
    assert result["automatic_inventory_adjustment"] is False
    assert result["automatic_inventory_movement"] is False


def test_gate16i_low_confidence_requires_review():
    result = _service().reconcile(
        inventory_rows=[
            {"botella_id": "B1", "porcentaje_restante": 80.0},
        ],
        observations=[
            {
                "observation_id": "O1",
                "observed_reference": "candidate:B1",
                "observed_quantity": 1,
                "observed_level_pct": 80.0,
                "recognition_confidence": 0.25,
            }
        ],
        observation_to_bottle={"O1": "B1"},
        idempotency_key="audit-003",
    )
    assert result["outcome"] == "REVIEW_REQUIRED"
    assert result["requires_review"] is True


def test_gate16i_same_request_has_same_fingerprint():
    kwargs = dict(
        inventory_rows=[{"botella_id": "B1", "porcentaje_restante": 100.0}],
        observations=[
            {
                "observation_id": "O1",
                "observed_reference": "manual:B1",
                "observed_quantity": 1,
                "observed_level_pct": 100.0,
            }
        ],
        observation_to_bottle={"O1": "B1"},
        idempotency_key="audit-idempotent",
    )
    first = _service().reconcile(**kwargs)
    second = _service().reconcile(**kwargs)
    assert first["request_fingerprint"] == second["request_fingerprint"]
