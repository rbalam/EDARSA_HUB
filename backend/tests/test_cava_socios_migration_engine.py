from datetime import datetime, timezone

import pytest

from modules.cava_socios.domain import BottleOrigin, validate_origin_evidence
from modules.cava_socios.migration_engine import (
    ExternalRecord,
    MappingDecision,
    MappingStatus,
    MigrationMode,
    SourceIdentity,
    canonical_payload_checksum,
    historical_origin_evidence,
    plan_dry_run,
    reconcile_counts,
)


def _record(record_id: str = "B-1", payload=None):
    return ExternalRecord(
        identity=SourceIdentity(
            source_instance_id="legacy-130mid",
            entity_type="BOTTLE",
            source_record_id=record_id,
            source_transaction_id="TX-10",
            source_line_id="1",
        ),
        source_system="LEGACY_CAVA",
        payload=payload or {"nivel": 75, "producto": "VINO-X"},
        original_occurred_at=datetime(2021, 5, 4, 18, 30, tzinfo=timezone.utc),
    )


def test_idempotency_key_is_provider_neutral_and_stable():
    identity = _record().identity
    assert identity.idempotency_key() == "legacy-130mid|BOTTLE|B-1|TX-10|1"


def test_checksum_is_order_independent():
    a = canonical_payload_checksum({"b": 2, "a": 1})
    b = canonical_payload_checksum({"a": 1, "b": 2})
    assert a == b


def test_original_occurred_at_requires_timezone():
    with pytest.raises(ValueError, match="zona horaria"):
        ExternalRecord(
            identity=SourceIdentity("i", "BOTTLE", "1"),
            source_system="LEGACY",
            payload={},
            original_occurred_at=datetime(2020, 1, 1),
        )


def test_dry_run_is_ready_only_without_unresolved_records():
    rows = [_record("1"), _record("2")]
    summary = plan_dry_run(
        rows,
        mode=MigrationMode.HISTORICAL_MIGRATION,
        resolver=lambda row: MappingDecision(
            MappingStatus.EXACT_MATCH,
            canonical_entity_type="BOTTLE",
            canonical_entity_id=f"CAN-{row.identity.source_record_id}",
        ),
    )
    assert summary.received == 2
    assert summary.accepted == 2
    assert summary.execution_ready is True


def test_dry_run_requires_review_for_probable_match():
    summary = plan_dry_run(
        [_record()],
        mode=MigrationMode.MANUAL_FILE_IMPORT,
        resolver=lambda _: MappingDecision(MappingStatus.PROBABLE_MATCH),
    )
    assert summary.review_required == 1
    assert summary.execution_ready is False


def test_dry_run_rejects_duplicate_external_identity():
    row = _record()
    with pytest.raises(ValueError, match="duplicadas"):
        plan_dry_run(
            [row, row],
            mode=MigrationMode.HISTORICAL_MIGRATION,
            resolver=lambda _: MappingDecision(MappingStatus.EXACT_MATCH),
        )


def test_reconciliation_requires_explicitly_approved_difference():
    failed = reconcile_counts(
        {"botellas": 10, "movimientos": 20},
        {"botellas": 9, "movimientos": 20},
    )
    assert failed.certifiable is False

    approved = reconcile_counts(
        {"botellas": 10, "movimientos": 20},
        {"botellas": 9, "movimientos": 20},
        approved_differences={"botellas": -1},
    )
    assert approved.certifiable is True


def test_historical_projection_preserves_existing_cavas_contract():
    evidence = historical_origin_evidence(
        _record(),
        historical_reference="legacy:cava:B-1",
    )
    assert evidence.origin == BottleOrigin.REGULARIZACION_HISTORICA
    assert evidence.source_system == "LEGACY_CAVA"
    assert evidence.source_transaction_id == "TX-10"
    assert evidence.historical_reference == "legacy:cava:B-1"
    validate_origin_evidence(evidence)
