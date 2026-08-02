from modules.comercial_analytics.temporal_selection import (
    resolve_temporal_selection,
)


def test_api_contract_can_resolve_configurable_weekend():
    result = resolve_temporal_selection(
        selection={
            "mode": "date_rules",
            "selection_label": "Fin de semana",
            "scope": {
                "start_date": "2026-07-01",
                "end_date": "2026-07-12",
            },
            "rules": [{
                "type": "weekdays",
                "weekdays": [4, 5, 6, 7],
            }],
        },
        minimum_date="2026-01-01",
        maximum_date="2026-08-02",
    )

    assert result["resolved_dates"] == [
        "2026-07-02",
        "2026-07-03",
        "2026-07-04",
        "2026-07-05",
        "2026-07-09",
        "2026-07-10",
        "2026-07-11",
        "2026-07-12",
    ]

    assert result["selection_semantics"]["sales_label"] == (
        "Ventas de fin de semana"
    )


def test_api_contract_rejects_future_date():
    try:
        resolve_temporal_selection(
            selection={
                "mode": "specific_dates",
                "dates": ["2026-09-01"],
            },
            minimum_date="2026-01-01",
            maximum_date="2026-08-02",
        )
    except ValueError as exc:
        assert "fuera de cobertura" in str(exc)
    else:
        raise AssertionError(
            "Debía rechazar fecha futura"
        )
