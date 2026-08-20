from pathlib import Path


JOB = Path(
    "/app/backend/core/scheduler/jobs/"
    "sync_comercial_v2_job.py"
)


def _source():
    return JOB.read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_global_civil_end_date_is_removed():
    text = _source()

    assert "fecha_fin = date.today()" not in text


def test_canonical_operational_date_is_used():
    text = _source()

    assert (
        "from core.utils.operational_window "
        "import get_fecha_operacion"
    ) in text

    assert (
        text.count(
            'fecha_fin = get_fecha_operacion('
        )
        == 2
    )


def test_range_is_calculated_per_unit():
    text = _source()

    assert (
        text.count(
            'unidad["unidad_negocio_pk"]'
        )
        >= 2
    )

    assert (
        text.count(
            "- timedelta(days=SYNC_INCREMENTAL_DAYS)"
        )
        == 2
    )


def test_global_result_does_not_lie_about_single_range():
    text = _source()

    assert '"fecha_inicio": None' in text
    assert '"fecha_fin": None' in text

    assert (
        '"rango_fecha_operacion_por_unidad": True'
        in text
    )


def test_each_unit_exposes_its_effective_range():
    text = _source()

    assert (
        text.count(
            '"fecha_inicio": fecha_inicio.isoformat()'
        )
        >= 2
    )

    assert (
        text.count(
            '"fecha_fin": fecha_fin.isoformat()'
        )
        >= 2
    )


def test_no_new_civil_calendar_source():
    text = _source()

    assert "datetime.today()" not in text
    assert "datetime.now().date()" not in text
