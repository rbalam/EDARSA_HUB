from datetime import datetime, timezone

import pytest

from modules.cava_socios.evidence_chain import (
    EvidenceKind,
    EvidenceReference,
    build_evidence,
    historical_evidence_metadata,
    sha256_bytes,
    verify_chain,
    verify_content,
)


NOW = datetime(2026, 9, 19, 20, 0, tzinfo=timezone.utc)


def test_build_and_verify_content():
    content = b"photo-bytes"
    ref = build_evidence(
        evidence_id="E1",
        kind=EvidenceKind.BOTTLE_ENTRY,
        subject_type="BOTTLE",
        subject_id="B1",
        occurred_at=NOW,
        captured_at=NOW,
        storage_reference="legacy-url://photo/1",
        content=content,
        mime_type="image/jpeg",
    )
    assert ref.content_sha256 == sha256_bytes(content)
    assert verify_content(ref, content) is True
    assert verify_content(ref, b"tampered") is False


def test_chain_detects_reordering_or_missing_link():
    first = build_evidence(
        evidence_id="E1",
        kind=EvidenceKind.BOTTLE_ENTRY,
        subject_type="BOTTLE",
        subject_id="B1",
        occurred_at=NOW,
        captured_at=NOW,
        storage_reference="ref://1",
        content=b"1",
        mime_type="image/jpeg",
    )
    second = build_evidence(
        evidence_id="E2",
        kind=EvidenceKind.CONSUMPTION,
        subject_type="BOTTLE",
        subject_id="B1",
        occurred_at=NOW,
        captured_at=NOW,
        storage_reference="ref://2",
        content=b"2",
        mime_type="image/jpeg",
        previous=first,
    )
    assert verify_chain(first, second) is True
    assert verify_chain(second, first) is False


def test_metadata_change_changes_chain_hash():
    base = dict(
        evidence_id="E1",
        kind=EvidenceKind.AUDIT,
        subject_type="BOTTLE",
        subject_id="B1",
        occurred_at=NOW,
        captured_at=NOW,
        storage_reference="ref://1",
        content_sha256=sha256_bytes(b"x"),
        mime_type="image/jpeg",
    )
    a = EvidenceReference(**base, metadata={"nivel": 75})
    b = EvidenceReference(**base, metadata={"nivel": 50})
    assert a.chain_hash != b.chain_hash


def test_timestamps_must_be_timezone_aware():
    with pytest.raises(ValueError, match="zona horaria"):
        EvidenceReference(
            evidence_id="E1",
            kind=EvidenceKind.AUDIT,
            subject_type="BOTTLE",
            subject_id="B1",
            occurred_at=datetime(2026, 1, 1),
            captured_at=NOW,
            storage_reference="ref://1",
            content_sha256=sha256_bytes(b"x"),
            mime_type="image/jpeg",
        )


def test_historical_metadata_preserves_source_and_import_time():
    meta = historical_evidence_metadata(
        source_system="LEGACY_CAVA",
        source_record_id="PHOTO-99",
        imported_at=NOW,
        migration_batch_id="MIG-1",
    )
    assert meta["source_system"] == "LEGACY_CAVA"
    assert meta["source_record_id"] == "PHOTO-99"
    assert meta["migration_batch_id"] == "MIG-1"


def test_invalid_hash_rejected():
    with pytest.raises(ValueError, match="SHA-256"):
        EvidenceReference(
            evidence_id="E1",
            kind=EvidenceKind.AUDIT,
            subject_type="BOTTLE",
            subject_id="B1",
            occurred_at=NOW,
            captured_at=NOW,
            storage_reference="ref://1",
            content_sha256="abc",
            mime_type="image/jpeg",
        )
