from decimal import Decimal

from core.scheduler.jobs.sync_comercial_abiertas_v2_job import (
    select_mpro_closed_sales,
)


def test_canonical_wins_when_it_has_tickets():
    canonical = {
        "ventas_cerradas_dia": Decimal("219346.00"),
        "tickets_cerrados_dia": 41,
        "pax_cerrados_dia": 134,
        "propinas_cerradas_dia": Decimal("0.00"),
    }
    provisional = {
        "ventas_cerradas_dia": Decimal("221766.00"),
        "tickets_cerrados_dia": 43,
        "pax_cerrados_dia": 140,
        "propinas_cerradas_dia": Decimal("0.00"),
    }

    result = select_mpro_closed_sales(
        canonical,
        provisional,
    )

    assert result["ventas_cerradas_dia"] == Decimal(
        "219346.00"
    )
    assert result["tickets_cerrados_dia"] == 41
    assert result["closed_sales_source"] == (
        "CANONICAL_VENTA_ENCABEZADO"
    )
    assert result["is_provisional"] is False


def test_provisional_is_used_when_canonical_is_empty():
    canonical = {
        "ventas_cerradas_dia": Decimal("0.00"),
        "tickets_cerrados_dia": 0,
        "pax_cerrados_dia": 0,
        "propinas_cerradas_dia": Decimal("0.00"),
    }
    provisional = {
        "ventas_cerradas_dia": Decimal("84671.00"),
        "tickets_cerrados_dia": 15,
        "pax_cerrados_dia": 51,
        "propinas_cerradas_dia": Decimal("6981.00"),
    }

    result = select_mpro_closed_sales(
        canonical,
        provisional,
    )

    assert result["ventas_cerradas_dia"] == Decimal(
        "84671.00"
    )
    assert result["tickets_cerrados_dia"] == 15
    assert result["pax_cerrados_dia"] == 51
    assert result["propinas_cerradas_dia"] == Decimal(
        "6981.00"
    )
    assert result["closed_sales_source"] == (
        "PROVISIONAL_COMANDA"
    )
    assert result["is_provisional"] is True


def test_sources_are_never_added_together():
    canonical = {
        "ventas_cerradas_dia": Decimal("100.00"),
        "tickets_cerrados_dia": 1,
    }
    provisional = {
        "ventas_cerradas_dia": Decimal("120.00"),
        "tickets_cerrados_dia": 1,
    }

    result = select_mpro_closed_sales(
        canonical,
        provisional,
    )

    assert result["ventas_cerradas_dia"] == Decimal(
        "100.00"
    )
    assert result["ventas_cerradas_dia"] != Decimal(
        "220.00"
    )


def test_origen_validated_case_uses_canonical():
    canonical = {
        "ventas_cerradas_dia": Decimal("24941.51"),
        "tickets_cerrados_dia": 17,
        "pax_cerrados_dia": 41,
        "propinas_cerradas_dia": Decimal("1849.35"),
    }
    provisional = {
        "ventas_cerradas_dia": Decimal("25596.51"),
        "tickets_cerrados_dia": 17,
        "pax_cerrados_dia": 41,
        "propinas_cerradas_dia": Decimal("1849.35"),
    }

    result = select_mpro_closed_sales(
        canonical,
        provisional,
    )

    assert result["ventas_cerradas_dia"] == Decimal(
        "24941.51"
    )
    assert result["closed_sales_source"] == (
        "CANONICAL_VENTA_ENCABEZADO"
    )



def test_scheduler_productive_precedence_structure():
    from pathlib import Path

    source = Path(
        "/app/backend/core/scheduler/jobs/"
        "sync_comercial_abiertas_v2_job.py"
    ).read_text(encoding="utf-8")

    assert source.count(
        "def select_mpro_closed_sales("
    ) == 1

    assert source.count(
        "cerradas_data = select_mpro_closed_sales("
    ) == 1

    assert source.count(
        "query_cerradas_canonical ="
    ) == 1

    assert source.count(
        "query_cerradas_provisional ="
    ) == 1

    assert source.count(
        "if canonical_tickets <= 0:"
    ) == 1


def test_scheduler_uses_provisional_only_after_empty_canonical():
    from pathlib import Path

    source = Path(
        "/app/backend/core/scheduler/jobs/"
        "sync_comercial_abiertas_v2_job.py"
    ).read_text(encoding="utf-8")

    start = source.index(
        "# VENTAS CERRADAS MPRO: "
        "CANONICO CON FALLBACK PROVISIONAL"
    )

    canonical = source.index(
        "query_cerradas_canonical =",
        start,
    )

    condition = source.index(
        "if canonical_tickets <= 0:",
        canonical,
    )

    provisional = source.index(
        "query_cerradas_provisional =",
        condition,
    )

    selector = source.index(
        "cerradas_data = select_mpro_closed_sales(",
        provisional,
    )

    assert canonical < condition
    assert condition < provisional
    assert provisional < selector


def test_scheduler_exposes_selected_closed_sales_source():
    from pathlib import Path

    source = Path(
        "/app/backend/core/scheduler/jobs/"
        "sync_comercial_abiertas_v2_job.py"
    ).read_text(encoding="utf-8")

    selector = source.index(
        "cerradas_data = select_mpro_closed_sales("
    )

    selected_flow = source[selector:]

    assert (
        '"closed_sales_source": closed_sales_source'
        in selected_flow
    )

    assert (
        '"closed_sales_is_provisional": ('
        in selected_flow
    )

    assert (
        "fuente_cerradas=%s"
        in selected_flow
    )

    assert (
        "provisional=%s"
        in selected_flow
    )


def test_scheduler_never_sums_canonical_and_provisional():
    from pathlib import Path

    source = Path(
        "/app/backend/core/scheduler/jobs/"
        "sync_comercial_abiertas_v2_job.py"
    ).read_text(encoding="utf-8")

    start = source.index(
        "# VENTAS CERRADAS MPRO: "
        "CANONICO CON FALLBACK PROVISIONAL"
    )

    end = source.index(
        "# Extraer valores ANTES de decidir",
        start,
    )

    block = source[start:end]

    forbidden = (
        "canonical_closed_data + provisional_closed_data",
        "canonical_result + provisional_result",
        "ventas_canonicas + ventas_provisionales",
    )

    for expression in forbidden:
        assert expression not in block
