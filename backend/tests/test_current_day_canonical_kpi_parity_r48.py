from modules.comercial_analytics import repository_tickets as repo


def test_current_day_summary_uses_exact_detail_items(monkeypatch):
    monkeypatch.setattr(
        repo,
        "_list_current_day_with_comercial_merge",
        lambda **kwargs: {
            "items": [
                {"ventas": 1535.0, "pax": 1},
                {"ventas": 6675.0, "pax": 2},
                {"ventas": 1177.0, "pax": 3},
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
    assert result["ventas"] == 9387.0
    assert result["ticket_promedio"] == 3129.0
    assert result["pax_promedio"] == 1564.5
    assert result["traceability"]["contract"] == (
        "DETALLE_VENTAS_CANONICO_ATOMICO_TRANSVERSAL"
    )


def test_cienfuegos_reference_values_are_mathematically_consistent():
    # Captura de validacion del 08-oct-2026:
    # Detalle canonico = 14 folios, 27 PAX, $28,715.
    ventas = 28715.0
    cheques = 14
    pax = 27

    assert round(ventas / cheques, 2) == 2051.07
    assert round(ventas / pax, 2) == 1063.52
