from pathlib import Path


def _service_source() -> str:
    return (
        Path(__file__).resolve().parents[1]
        / "modules"
        / "sync_monitor"
        / "service.py"
    ).read_text(encoding="utf-8")


def test_error_kpi_uses_exact_sql_counts_not_truncated_list_length():
    source = _service_source()
    assert "SELECT COUNT(*) AS total" in source
    assert "total_errores_compras_24h" in source
    assert "total_errores_comercial_24h" in source
    assert "total_errores_24h = total_errores_compras_24h + total_errores_comercial_24h" in source
    assert "total_errores_24h = len(errores)" not in source


def test_error_detail_lists_remain_bounded_for_ui():
    source = _service_source()
    assert source.count("SELECT TOP 50") >= 2
    assert '"errores": errores[:20]' in source
