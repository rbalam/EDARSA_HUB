"""Contrato estático de ventas para los cinco consumidores comerciales."""
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
BACKFILL = BACKEND / "modules/backfill_corporativo/service.py"
SHORT_JOB = BACKEND / "core/scheduler/jobs/sync_short_comercial_job.py"
NIGHTLY_JOB = BACKEND / "core/scheduler/jobs/sync_nightly_comercial_job.py"
HISTORICA_24M = BACKEND / "modules/comercial_v2/carga_historica_24_meses.py"
HISTORICA_ABRIL = BACKEND / "modules/comercial_v2/carga_historica_abril_2026.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_backfill_softrestaurant_usa_ventas_total_y_propina_separada():
    source = _source(BACKFILL)

    assert "SUM(ISNULL(c.total,0)) AS ventas_total" in source
    assert "SUM(ISNULL(c.propina,0)) AS propinas_total" in source
    assert "c.total,0) - ISNULL(c.propina" not in source
    assert "propinas_total = %s" in source
    assert '"propinas_total": propinas' in source


def test_backfill_calcula_ratios_desde_ventas_total():
    source = _source(BACKFILL)

    assert "ticket_promedio = ventas / cheques if cheques else 0" in source
    assert "pax_promedio = ventas / pax if pax else 0" in source


def test_jobs_no_construyen_ventas_netas():
    for path in (SHORT_JOB, NIGHTLY_JOB):
        source = _source(path)
        assert '"ventas_netas"' not in source, path
        assert '"ventas": float(' in source, path
        assert '"propina": float(' in source, path


def test_carga_24_meses_no_lee_ni_construye_ventas_sin_propina():
    source = _source(HISTORICA_24M)

    assert "ventas_sin_propina" not in source
    assert "SUM(total) as ventas_total" in source
    assert "SUM(ISNULL(propina, 0)) as propinas" in source
    assert source.count(
        'ticket_promedio = ventas_total / tickets if tickets > 0 else Decimal("0")'
    ) == 2
    assert source.count(
        'pax_promedio = ventas_total / pax if pax > 0 else Decimal("0")'
    ) == 2
    assert "propinas_total=propinas" in source
    assert 'propinas_total=Decimal("0")' in source


def test_carga_abril_no_lee_ni_construye_ventas_sin_propina():
    source = _source(HISTORICA_ABRIL)

    assert "ventas_sin_propina" not in source
    assert "SUM(total) as ventas_total" in source
    assert "SUM(ISNULL(propina, 0)) as propinas" in source
    assert source.count(
        'ticket_promedio = ventas_total / tickets if tickets > 0 else Decimal("0")'
    ) == 2
    assert source.count(
        'pax_promedio = ventas_total / pax if pax > 0 else Decimal("0")'
    ) == 2
    assert "propinas_total=propinas" in source


def test_cinco_consumidores_permanecen_en_el_alcance_contractual():
    consumers = (BACKFILL, SHORT_JOB, NIGHTLY_JOB, HISTORICA_24M, HISTORICA_ABRIL)

    assert len(consumers) == 5
    assert all(path.is_file() for path in consumers)
