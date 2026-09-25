from datetime import date, datetime
from decimal import Decimal

from core.utils import operational_window
from modules.comercial_v2 import sync_comercial_edarsahub as sync_module
from modules.comercial_v2.mappers import map_softrestaurant_ventas_cerradas
from modules.comercial_v2.schemas import SistemaOrigen, UnidadNegocioConfig


def _config():
    return UnidadNegocioConfig(
        unidad_negocio_pk="unit-estelar",
        unidad_negocio_nombre="LA ESTELAR",
        server_id="server-estelar",
        sucursal_id="DEFAULT",
        sucursal_nombre="LA ESTELAR",
        sistema_origen=SistemaOrigen.SOFTRESTAURANT,
        activo=True,
    )


def test_query_matches_official_softrestaurant_turn_contract():
    query = sync_module.build_softrestaurant_ventas_cerradas_query(
        {"unidad_codigo": "ESTELAR"},
        date(2026, 8, 31),
        date(2026, 8, 31),
    )

    assert "INNER JOIN turnos AS tr" in query
    assert "tr.idturno = ch.idturno" in query
    assert "DATEADD(hour, -9, tr.apertura)" in query
    assert "ch.cancelado = 0" in query
    assert "cierre IS NOT NULL" not in query
    assert "idempresa" not in query
    assert "SUM(ch.nopersonas) AS num_personas" in query
    assert "COUNT(DISTINCT ch.folio) AS num_cheques" in query


def test_grouping_preserves_count_rows_for_official_report(monkeypatch):
    monkeypatch.setattr(
        operational_window,
        "get_fecha_operacion",
        lambda unidad_pk, value: date(2026, 8, 31),
    )
    rows = [
        {
            "fecha_hora": datetime(2026, 8, 31, 9, 0),
            "folio": "100",
            "num_cheques": 1,
            "ventas_total": Decimal("100.00"),
            "propinas": Decimal("10.00"),
            "num_personas": 1,
        },
        {
            "fecha_hora": datetime(2026, 8, 31, 9, 1),
            "folio": "100",
            "num_cheques": 1,
            "ventas_total": Decimal("200.00"),
            "propinas": Decimal("20.00"),
            "num_personas": 2,
        },
    ]

    result = sync_module._agrupar_ventas_cerradas_por_fecha_operacion(
        rows,
        _config(),
        fecha_inicio=date(2026, 8, 31),
        fecha_fin=date(2026, 8, 31),
    )

    assert len(result) == 1
    assert result[0]["num_cheques"] == 2
    assert result[0]["num_personas"] == 3
    assert result[0]["ventas_total"] == Decimal("300.00")


def test_mapper_matches_la_estelar_official_summary():
    kpi = map_softrestaurant_ventas_cerradas(
        {
            "fecha": date(2026, 8, 31),
            "ventas_total": Decimal("22345.00"),
            "propinas": Decimal("2232.50"),
            "num_cheques": 22,
            "num_personas": 48,
        },
        _config(),
        "RESYNC-ESTELAR-CONTRACT",
    )

    assert kpi.ventas_total == Decimal("22345.00")
    assert kpi.propinas_total == Decimal("2232.50")
    assert kpi.tickets_total == 22
    assert kpi.pax_total == 48
    assert kpi.ticket_promedio == Decimal("22345.00") / Decimal("22")
    assert kpi.pax_promedio == Decimal("22345.00") / Decimal("48")
