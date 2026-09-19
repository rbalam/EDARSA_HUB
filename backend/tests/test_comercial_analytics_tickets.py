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
            "importe": 200,
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
    assert result["ticket"]["ventas"] == 200
    assert result["ticket"]["propina"] == 20
    assert result["ticket"]["pax"] == 3
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
    assert calls[0][-1] == (
        "2026-07-01",
        "2026-07-31",
        "CIENFUEGOS",
    )
