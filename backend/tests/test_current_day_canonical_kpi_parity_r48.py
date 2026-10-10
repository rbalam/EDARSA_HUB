from pathlib import Path

from modules.comercial import ticket_service
from modules.comercial_analytics import repository_tickets as repo


def test_current_day_summary_uses_exact_detail_items(monkeypatch):
    monkeypatch.setattr(
        repo,
        "_list_current_day_with_comercial_merge",
        lambda **kwargs: {
            "items": [
                {"ventas": 1535.0, "pax": 1},
                {"ventas": 6675.0, "pax": 2},
                {"ventas": 1385.0, "pax": 3},
            ],
            "traceability": {"source": "detalle"},
        },
    )

    result = repo.summarize_current_day_tickets(
        operation_date="2026-10-08",
        unit_code="CIENFUEGOS",
    )

    assert result["cheques"] == 3
    assert result["pax"] == 6
    assert result["ventas"] == 9595.0
    assert result["ticket_promedio"] == 3198.33
    assert result["pax_promedio"] == 1599.17
    assert result["traceability"]["contract"] == (
        "DETALLE_VENTAS_CANONICO_ATOMICO_TRANSVERSAL"
    )


def test_softrestaurant_snapshot_sale_keeps_propina_inside_visible_total():
    row = {
        "sistema_origen": "SOFTRESTAURANT",
        "total_ticket": 1385.0,
        "propina": 208.0,
    }
    assert ticket_service._snapshot_sales_amount(row) == 1385.0


def test_current_day_closed_ticket_adds_propina_once_contract():
    text = Path(repo.__file__).read_text(encoding="utf-8")
    assert "SUM(ISNULL(d.importe_neto, 0)) AS ventas_sin_propina" in text
    assert "MAX(ISNULL(d.propina, 0)) AS propina" in text
    assert 'float(row.get("ventas_sin_propina") or 0)' in text
    assert '+ float(row.get("propina") or 0)' in text
