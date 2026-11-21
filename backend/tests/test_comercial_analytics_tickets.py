import os
from datetime import datetime

import pytest

import modules.comercial_analytics.repository_tickets as repository_tickets

os.environ.setdefault(
    "JWT_SECRET",
    "test-ticket-repository-secret",
)
os.environ.setdefault("EDARSAHUB_SQL_HOST", "test.invalid")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "test_readonly")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "test_only")

from modules.comercial_analytics.repository_tickets import (
    get_ticket_detail,
    list_tickets,
)
from modules.comercial_analytics.ticket_identity import (
    create_ticket_pk,
    parse_ticket_pk,
)


def test_list_tickets_paginates_and_emits_ticket_pk():
    calls = []

    def executor(sql, params):
        calls.append((sql, params))

        if "COUNT(*) AS total" in sql:
            return [{"total": 3}]

        return [{
            "unidad_negocio_id": "130MID",
            "unidad": "130° Mérida",
            "sucursal": "Mérida",
            "fecha_operacion": "2026-07-15",
            "numero_ticket": "100",
            "fecha_hora": datetime(2026, 7, 16, 1, 30),
            "pax": 2,
            "lineas": 3,
            "ventas": 500,
            "propina": 50,
        }]

    result = list_tickets(
        fecha_inicio="2026-07-15",
        fecha_fin="2026-07-15",
        allowed_unit_codes=["130MID"],
        page=2,
        page_size=1,
        query_executor=executor,
    )

    assert result["total"] == 3
    assert result["page"] == 2
    assert result["page_size"] == 1
    assert result["has_more"] is True
    assert len(result["items"]) == 1
    assert result["items"][0]["ticket_pk"]

    identity = parse_ticket_pk(
        result["items"][0]["ticket_pk"]
    )

    assert identity.unidad_negocio_id == "130MID"
    assert identity.fecha_operacion == "2026-07-15"
    assert identity.numero_ticket == "100"

    data_sql, data_params = calls[1]

    assert "OFFSET %s ROWS" in data_sql
    assert "FETCH NEXT %s ROWS ONLY" in data_sql
    assert data_params[-2:] == (1, 1)


def test_list_tickets_filters_by_rbac_units():
    calls = []

    def executor(sql, params):
        calls.append((sql, params))

        if "COUNT(*) AS total" in sql:
            return [{"total": 0}]

        return []

    list_tickets(
        fecha_inicio="2026-07-01",
        fecha_fin="2026-07-31",
        allowed_unit_codes=["130MID", "CIENFUEGOS"],
        query_executor=executor,
    )

    count_sql, count_params = calls[0]

    assert "d.unidad_negocio_id IN (%s, %s)" in count_sql
    assert "130MID" in count_params
    assert "CIENFUEGOS" in count_params


def test_rejects_requested_unit_outside_rbac():
    with pytest.raises(PermissionError):
        list_tickets(
            fecha_inicio="2026-07-01",
            fecha_fin="2026-07-31",
            allowed_unit_codes=["130MID"],
            unidad_negocio_id="CIENFUEGOS",
            query_executor=lambda sql, params: [],
        )


def test_ticket_detail_uses_identity_fields():
    captured = {}

    def executor(sql, params):
        captured["sql"] = sql
        captured["params"] = params

        return [{
            "unidad_negocio_id": "130MID",
            "unidad": "130° Mérida",
            "sucursal": "Mérida",
            "fecha_operacion": "2026-07-15",
            "numero_ticket": "100",
            "primera_fecha_hora": datetime(2026, 7, 15, 20, 30),
            "codigo": "P1",
            "producto": "Producto",
            "familia": "Familia",
            "subfamilia": "Subfamilia",
            "clasificacion": "CLASE",
            "casa": "Casa",
            "marca": "Marca",
            "grado_alcohol": None,
            "es_alcoholico": False,
            "cantidad": 2,
            "precio_unitario": 100,
            "importe_bruto": 220,
            "importe": 200,
            "descuento": 20,
            "propina": 20,
            "pax": 3,
        }]

    ticket_pk = create_ticket_pk(
        unidad_negocio_id="130MID",
        fecha_operacion="2026-07-15",
        numero_ticket="100",
    )

    result = get_ticket_detail(
        identity=parse_ticket_pk(ticket_pk),
        allowed_unit_codes=["130MID"],
        query_executor=executor,
    )

    assert captured["params"] == (
        "130MID",
        "2026-07-15",
        "100",
    )
    assert "CONVERT(varchar(128), d.numero_ticket) = %s" in captured["sql"]
    assert result["ticket"]["ventas"] == 200
    assert result["ticket"]["subtotal"] == 220
    assert result["ticket"]["descuento"] == 20
    assert result["ticket"]["estado"] == "CERRADA"
    assert result["ticket"]["fecha_hora"].startswith("2026-07-15 20:30")
    assert result["ticket"]["propina"] == 20
    assert result["ticket"]["pax"] == 3
    assert result["lines"][0]["importe_bruto"] == 220
    assert len(result["lines"]) == 1


def test_ticket_detail_rejects_unit_outside_rbac():
    ticket_pk = create_ticket_pk(
        unidad_negocio_id="CIENFUEGOS",
        fecha_operacion="2026-07-15",
        numero_ticket="100",
    )

    with pytest.raises(PermissionError):
        get_ticket_detail(
            identity=parse_ticket_pk(ticket_pk),
            allowed_unit_codes=["130MID"],
            query_executor=lambda sql, params: [],
        )


def test_ticket_detail_returns_not_found():
    ticket_pk = create_ticket_pk(
        unidad_negocio_id="130MID",
        fecha_operacion="2026-07-15",
        numero_ticket="999",
    )

    with pytest.raises(LookupError):
        get_ticket_detail(
            identity=parse_ticket_pk(ticket_pk),
            allowed_unit_codes=["130MID"],
            query_executor=lambda sql, params: [],
        )


def test_default_executor_uses_parameterized_edarsahub_query(monkeypatch):
    calls = []

    def fake_execute_sql_query_params(
        host, port, database, username, password, query, params
    ):
        calls.append((host, port, database, username, password, query, params))
        if "COUNT(*) AS total" in query:
            return [{"total": 0}]
        return []

    monkeypatch.setattr(
        repository_tickets,
        "execute_sql_query_params",
        fake_execute_sql_query_params,
    )

    result = repository_tickets.list_tickets(
        fecha_inicio="2026-07-01",
        fecha_fin="2026-07-31",
        allowed_unit_codes=["CIENFUEGOS"],
        unidad_negocio_id="CIENFUEGOS",
    )

    assert result["total"] == 0
    assert len(calls) == 2
    # Para rangos históricos de una unidad, el contrato canónico primero
    # resuelve si existe una jornada activa en snapshot y después ejecuta el
    # conteo histórico parametrizado. Ambas llamadas son EDARSAHUB read-only.
    assert calls[0][-1] == ("CIENFUEGOS",)
    assert calls[1][-1] == (
        "2026-07-01",
        "2026-07-31",
        "CIENFUEGOS",
    )


def test_ticket_detail_falls_back_to_certified_comercial_ticket(monkeypatch):
    ticket_pk = create_ticket_pk(
        unidad_negocio_id="CIENFUEGOS",
        fecha_operacion="2026-09-01",
        numero_ticket="105118",
    )

    def fallback(identity):
        assert identity.unidad_negocio_id == "CIENFUEGOS"
        assert identity.fecha_operacion == "2026-09-01"
        assert identity.numero_ticket == "105118"
        return {
            "ticket": {
                "unidad_negocio_id": "CIENFUEGOS",
                "unidad": "CIENFUEGOS",
                "fecha_operacion": "2026-09-01",
                "fecha": "2026-09-01",
                "fecha_hora": "2026-09-01 14:08:07",
                "numero_ticket": "105118",
                "estado": "CERRADA",
                "pax": 10,
                "lineas": 1,
                "subtotal": 13710,
                "descuento": 0,
                "impuesto": None,
                "ventas": 13710,
                "total": 13710,
                "propina": 0,
            },
            "lines": [{
                "linea_pk": "105118:fallback:1",
                "producto": "PRODUCTO",
                "cantidad": 1,
                "precio_unitario": 13710,
                "importe_bruto": 13710,
                "importe": 13710,
                "pax": 10,
            }],
            "lineas": [],
            "traceability": {
                "source": "modules.comercial.ticket_service",
                "live": False,
                "fallback": "COMERCIAL_TICKET_CERTIFIED_PATH",
            },
        }

    monkeypatch.setattr(
        repository_tickets,
        "_fallback_ticket_from_comercial",
        fallback,
    )

    result = get_ticket_detail(
        identity=parse_ticket_pk(ticket_pk),
        allowed_unit_codes=["CIENFUEGOS"],
    )

    assert result["ticket"]["numero_ticket"] == "105118"
    assert result["ticket"]["total"] == 13710
    assert result["traceability"]["fallback"] == (
        "COMERCIAL_TICKET_CERTIFIED_PATH"
    )
    assert result["traceability"]["contract"] == (
        "TABLERO_COMERCIAL_TICKET_CERTIFIED_PATH"
    )


def test_executive_ticket_visual_contract_matches_comercial():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    executive = (
        root
        / "frontend/src/components/comercial/TicketVentaModal.jsx"
    ).read_text(encoding="utf-8")

    assert "VENDEDOR:" in executive
    assert "replace('T', ' ').slice(0, 19)" in executive
    assert "item.descuento_importe" in executive
    assert "item.descuento_pct" in executive
    assert "TOTAL PROD." in executive
    assert "DESC. PRODUCTOS" in executive
    assert "DESC. CUENTA" in executive
    assert "text-red-600 font-semibold" in executive



def test_historical_range_replaces_active_day_with_atomic_snapshot(monkeypatch):
    monkeypatch.setattr(
        repository_tickets,
        "_latest_snapshot_operation_date",
        lambda unit_code: "2026-10-09",
    )
    monkeypatch.setattr(
        repository_tickets,
        "_list_current_day_with_comercial_merge",
        lambda **kwargs: {
            "items": [
                {
                    "ticket_pk": "today-1",
                    "unidad_negocio_id": "ORIGEN",
                    "fecha_operacion": "2026-10-09",
                    "numero_ticket": "SB-0055609",
                    "pax": 1,
                    "ventas": 130.0,
                    "propina": 0.0,
                },
                {
                    "ticket_pk": "today-2",
                    "unidad_negocio_id": "ORIGEN",
                    "fecha_operacion": "2026-10-09",
                    "numero_ticket": "SB-0055610",
                    "pax": 2,
                    "ventas": 535.0,
                    "propina": 0.0,
                },
            ]
        },
    )

    calls = []

    def fake_execute(sql, params, query_executor=None):
        calls.append((sql, params))
        if "COUNT(*) AS total" in sql:
            return [{"total": 2}]
        return [{
            "unidad_negocio_id": "ORIGEN",
            "unidad": "ORIGEN",
            "sucursal": "ORIGEN",
            "fecha_operacion": "2026-10-01",
            "numero_ticket": "SB-0050312",
            "fecha_hora": datetime(2026, 10, 1, 12, 0),
            "pax": 1,
            "lineas": 1,
            "ventas": 45.0,
            "propina": 0.0,
        }]

    monkeypatch.setattr(
        repository_tickets,
        "_execute",
        fake_execute,
    )

    result = repository_tickets.list_tickets(
        fecha_inicio="2026-10-01",
        fecha_fin="2026-10-31",
        allowed_unit_codes=["ORIGEN"],
        unidad_negocio_id="ORIGEN",
        page=1,
        page_size=200,
    )

    assert result["total"] == 4
    assert result["items"][0]["numero_ticket"] == "SB-0055609"
    assert result["items"][1]["numero_ticket"] == "SB-0055610"
    assert result["items"][2]["numero_ticket"] == "SB-0050312"
    assert result["traceability"]["contract"] == (
        "HISTORICO_CON_DIA_OPERATIVO_ATOMICO"
    )
    assert result["traceability"]["snapshot_operation_date"] == "2026-10-09"

    count_sql, count_params = calls[0]
    assert "d.fecha_operacion <> %s" in count_sql
    assert count_params[-1] == "2026-10-09"
