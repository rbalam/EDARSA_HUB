from __future__ import annotations

import json
from pathlib import Path

from core.commercial_sales_contract import (
    fiscal_breakdown,
    snapshot_visible_sales,
)
from modules.comercial import ticket_service
from modules.comercial_v2 import repository_readonly


ROOT = Path(__file__).resolve().parents[2]


def test_la_estelar_evidence_softrestaurant_total_is_18405_not_minus_tip():
    persisted_legacy = 17972.25
    propina = 432.75

    assert snapshot_visible_sales(
        persisted_legacy,
        propina,
        "SOFTRESTAURANT",
    ) == 18405.0


def test_intraday_softrestaurant_detail_uses_pos_total_atomically():
    row = {
        "sistema_origen": "SOFTRESTAURANT",
        "ventas_abiertas": 17972.25,
        "tickets_abiertos": 2,
        "pax_abiertos": 16,
        "ventas_cerradas_dia": 0,
        "tickets_cerrados_dia": 0,
        "pax_cerrados_dia": 0,
        "propinas_abiertas": 432.75,
        "propinas_cerradas_dia": 0,
        "propinas_total": 432.75,
        "detalle_abiertas_json": json.dumps([
            {
                "folio": "26524",
                "folio_origen": "26524",
                "total_ticket": 9000.0,
                "propina": 200.0,
                "pax": 8,
            },
            {
                "folio": "26525",
                "folio_origen": "26525",
                "total_ticket": 9405.0,
                "propina": 232.75,
                "pax": 8,
            },
        ]),
    }

    out = repository_readonly._overlay_softrestaurant_intraday_from_detail_json(
        row
    )

    assert out["ventas_abiertas"] == 18405.0
    assert out["total_estimado_dia"] == 18405.0
    assert out["propinas_total"] == 432.75
    assert out["tickets_abiertos"] == 2
    assert out["pax_abiertos"] == 16


def test_softrestaurant_after_cut_restores_closed_total_without_detail_json():
    row = {
        "sistema_origen": "SOFTRESTAURANT",
        "ventas_abiertas": 0,
        "tickets_abiertos": 0,
        "pax_abiertos": 0,
        "ventas_cerradas_dia": 17972.25,
        "tickets_cerrados_dia": 10,
        "pax_cerrados_dia": 16,
        "propinas_abiertas": 0,
        "propinas_cerradas_dia": 432.75,
        "propinas_total": 432.75,
        "detalle_abiertas_json": "[]",
    }

    out = repository_readonly._overlay_softrestaurant_intraday_from_detail_json(
        row
    )

    assert out["ventas_cerradas_dia"] == 18405.0
    assert out["total_estimado_dia"] == 18405.0
    assert out["propinas_total"] == 432.75
    assert out["tickets_cerrados_dia"] == 10
    assert out["pax_cerrados_dia"] == 16


def test_ticket_total_never_turns_softrestaurant_tip_into_discount():
    row = {
        "sistema_origen": "SOFTRESTAURANT",
        "total_ticket": 1055.0,
        "propina": 158.25,
    }

    assert ticket_service._snapshot_sales_amount(row) == 1055.0


def test_ticket_fiscal_breakdown_matches_example_without_changing_total():
    subtotal, impuestos = fiscal_breakdown(1055.0)

    assert subtotal == 909.48
    assert impuestos == 145.52
    assert round(subtotal + impuestos, 2) == 1055.0


def test_mpro_visible_total_is_not_changed_by_tip_contract():
    assert snapshot_visible_sales(
        4780.0,
        500.0,
        "MPRO",
    ) == 4780.0


def test_protected_scheduler_remains_untouched_legacy_writer():
    protected = (
        ROOT
        / "backend"
        / "core"
        / "scheduler"
        / "jobs"
        / "sync_comercial_abiertas_v2_job.py"
    ).read_text(encoding="utf-8")

    assert "ISNULL(total, 0) - ISNULL(propina, 0)" in protected
