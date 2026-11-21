from datetime import datetime, timezone

import pytest

from modules.rrr.schemas import AttributionTransactionRequest


def test_attribution_schema_preserves_uuid_and_cliente():
    payload = AttributionTransactionRequest(
        server_id="srv-1",
        agent_id="agent-1",
        source_transaction_uuid="550e8400-e29b-41d4-a716-446655440000",
        source_system="COMANDERO",
        occurred_at_utc=datetime.now(timezone.utc),
        unit_source_id="130MID",
        cliente_id=123,
        commercial_system="SOFTRESTAURANT",
        native_folio="25454",
    )
    assert payload.source_transaction_uuid == "550e8400-e29b-41d4-a716-446655440000"
    assert payload.cliente_id == 123
    assert payload.native_folio == "25454"


def test_attribution_schema_allows_anonymous_transport():
    payload = AttributionTransactionRequest(
        server_id="srv-1",
        source_transaction_uuid="uuid-2",
        source_system="COMANDERO",
        occurred_at_utc=datetime.now(timezone.utc),
        unit_source_id="130MID",
    )
    assert payload.cliente_id is None
