from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

JOB = (
    ROOT
    / "backend"
    / "core"
    / "scheduler"
    / "jobs"
    / "sync_comercial_v2_job.py"
)

SYNC = (
    ROOT
    / "backend"
    / "modules"
    / "comercial_v2"
    / "sync_comercial_edarsahub.py"
)


def _inclusive_days(fecha_inicio, fecha_fin):
    return [
        fecha_inicio + timedelta(days=offset)
        for offset in range(
            (fecha_fin - fecha_inicio).days + 1
        )
    ]


def test_header_operational_range_is_inclusive():
    text = SYNC.read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert (
        "if fecha_inicio_op and "
        "fecha_operacion < fecha_inicio_op:"
        in text
    )

    assert (
        "if fecha_fin_op and "
        "fecha_operacion > fecha_fin_op:"
        in text
    )


def test_scheduler_detail_range_matches_header_inclusive_contract():
    inicio = date(2026, 8, 15)
    fin = date(2026, 8, 18)

    assert _inclusive_days(inicio, fin) == [
        date(2026, 8, 15),
        date(2026, 8, 16),
        date(2026, 8, 17),
        date(2026, 8, 18),
    ]


def test_scheduler_source_uses_inclusive_detail_iteration():
    text = JOB.read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert (
        "(fecha_fin - fecha_inicio).days + 1"
        in text
    )

    assert (
        "detail_day = ("
        in text
    )

    assert (
        "fecha_inicio"
        in text
    )

    assert (
        "_sync_detalle_post_header("
        in text
    )


def test_zero_day_range_still_processes_one_operational_day():
    dia = date(2026, 8, 18)

    assert _inclusive_days(dia, dia) == [dia]


def test_three_incremental_days_means_four_inclusive_dates():
    fecha_fin = date(2026, 8, 18)
    fecha_inicio = fecha_fin - timedelta(days=3)

    days = _inclusive_days(
        fecha_inicio,
        fecha_fin,
    )

    assert days == [
        date(2026, 8, 15),
        date(2026, 8, 16),
        date(2026, 8, 17),
        date(2026, 8, 18),
    ]


def test_scheduler_uses_per_unit_operational_end_date():
    text = JOB.read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert "fecha_fin = date.today()" not in text

    assert (
        "from core.utils.operational_window "
        "import get_fecha_operacion"
    ) in text

    assert (
        text.count(
            "fecha_fin = get_fecha_operacion("
        )
        == 2
    )

    assert (
        '"rango_fecha_operacion_por_unidad": True'
        in text
    )
