from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from modules.rrr import attribution_service as svc
from modules.rrr.schemas import AttributionTransactionRequest


def _payload(server_id="server-1", unit_source_id="130MID"):
    return AttributionTransactionRequest(
        server_id=server_id,
        source_transaction_uuid="uuid-org-test",
        source_system="COMANDERO",
        occurred_at_utc=datetime.now(timezone.utc),
        unit_source_id=unit_source_id,
    )


def test_resolve_org_uses_canonical_unit_and_company(monkeypatch):
    unidad_pk = "11111111-1111-1111-1111-111111111111"
    monkeypatch.setattr(
        svc.CorporateFilterService,
        "resolver_unidad",
        lambda value: {"pk": unidad_pk, "codigo": "130MID", "nombre": "130 MERIDA"},
    )
    monkeypatch.setattr(
        svc.UnidadesService,
        "get_by_pk",
        lambda value: {"unidad_negocio_pk": unidad_pk, "codigo": "130MID", "server_id": "server-1"},
    )
    monkeypatch.setattr(
        svc,
        "resolve_empresa_by_alias",
        lambda codigo: SimpleNamespace(empresa_id=7),
    )

    resolved = svc._resolve_org(_payload())

    assert resolved == {"empresa_id": 7, "unidad_negocio_id": unidad_pk}


def test_resolve_org_rejects_server_mismatch(monkeypatch):
    unidad_pk = "11111111-1111-1111-1111-111111111111"
    monkeypatch.setattr(
        svc.CorporateFilterService,
        "resolver_unidad",
        lambda value: {"pk": unidad_pk, "codigo": "130MID", "nombre": "130 MERIDA"},
    )
    monkeypatch.setattr(
        svc.UnidadesService,
        "get_by_pk",
        lambda value: {"unidad_negocio_pk": unidad_pk, "codigo": "130MID", "server_id": "server-2"},
    )

    with pytest.raises(svc.AttributionOrgScopeError, match="server_id no corresponde"):
        svc._resolve_org(_payload(server_id="server-1"))
