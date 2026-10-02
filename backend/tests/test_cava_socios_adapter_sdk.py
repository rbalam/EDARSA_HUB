from datetime import datetime, timezone

import pytest

from modules.cava_socios.adapter_sdk import (
    AdapterCapabilities,
    AdapterCheckpoint,
    AdapterContext,
    AdapterHealth,
    ExtractionBatch,
    adapter_manifest,
    validate_adapter_contract,
    validate_extraction,
)
from modules.cava_socios.migration_engine import ExternalRecord, SourceIdentity


class FakeAdapter:
    adapter_code = "FAKE"
    adapter_version = "1.0"

    def capabilities(self):
        return AdapterCapabilities(
            full_extract=True,
            delta_extract=True,
            supports_checkpoint=True,
        )

    def validate_context(self, context):
        return None

    def health(self, context):
        return AdapterHealth(ok=True)

    def discover(self, context):
        return {"entities": ["BOTTLE"]}

    def extract_full(self, context):
        return ExtractionBatch((_record(context.source_instance_id),))

    def extract_delta(self, context, checkpoint):
        return ExtractionBatch(
            (_record(context.source_instance_id),),
            next_checkpoint=AdapterCheckpoint("2"),
        )


def _record(source_instance_id="source-1"):
    return ExternalRecord(
        identity=SourceIdentity(source_instance_id, "BOTTLE", "B-1"),
        source_system="FAKE",
        payload={"nivel": 100},
        original_occurred_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def test_adapter_contract_and_manifest():
    adapter = FakeAdapter()
    validate_adapter_contract(adapter)
    manifest = adapter_manifest(adapter)
    assert manifest["adapter_code"] == "FAKE"
    assert manifest["capabilities"]["supports_checkpoint"] is True


def test_delta_requires_checkpoint_capability():
    class Invalid(FakeAdapter):
        def capabilities(self):
            return AdapterCapabilities(full_extract=True, delta_extract=True, supports_checkpoint=False)

    with pytest.raises(ValueError, match="supports_checkpoint"):
        validate_adapter_contract(Invalid())


def test_context_requires_timezone_and_instance():
    with pytest.raises(ValueError, match="source_instance_id"):
        AdapterContext("", None, "America/Merida")
    with pytest.raises(ValueError, match="timezone"):
        AdapterContext("x", None, "")


def test_batch_rejects_duplicate_external_identity():
    row = _record()
    with pytest.raises(ValueError, match="duplicadas"):
        ExtractionBatch((row, row))


def test_validate_extraction_rejects_cross_instance_mix():
    batch = ExtractionBatch((_record("other"),))
    with pytest.raises(ValueError, match="otra source_instance"):
        validate_extraction(batch, expected_source_instance_id="source-1")


def test_fake_adapter_full_and_delta_are_provider_neutral():
    adapter = FakeAdapter()
    context = AdapterContext("source-1", "connection-uuid", "America/Merida", "MXN", "es-MX")
    adapter.validate_context(context)
    assert adapter.health(context).ok is True
    full = adapter.extract_full(context)
    validate_extraction(full, expected_source_instance_id="source-1")
    delta = adapter.extract_delta(context, AdapterCheckpoint("1"))
    validate_extraction(delta, expected_source_instance_id="source-1")
    assert delta.next_checkpoint.value == "2"
