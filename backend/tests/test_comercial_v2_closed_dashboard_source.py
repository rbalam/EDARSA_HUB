from datetime import date

from modules.comercial_v2 import repository_readonly as module


def _install_capture(monkeypatch, rows):
    queries = []

    monkeypatch.setattr(
        module,
        'runtime_dia_operativo_actual_predicate',
        lambda alias, mode: '1 = 1',
    )
    monkeypatch.setattr(
        module,
        '_execute_readonly_query',
        lambda query: queries.append(query) or rows,
    )
    return queries


def test_closed_dashboard_totals_use_persisted_base_table(monkeypatch):
    queries = _install_capture(monkeypatch, [{}])

    module.get_kpis_diarios_agregados(
        date(2026, 8, 31),
        date(2026, 8, 31),
        excluir_dia_operativo_actual=True,
    )

    query = queries[0]
    assert 'FROM dbo.Comercial_KPIs_Diarios_v2 AS k' in query
    assert 'ISNULL(k.activo, 1) = 1' in query
    assert 'ISNULL(k.es_demo, 0) = 0' in query
    assert 'vw_Comercial_KPIs_Diarios_v2_Runtime AS k' not in query


def test_closed_dashboard_cards_use_persisted_base_table(monkeypatch):
    queries = _install_capture(monkeypatch, [])

    module.get_kpis_por_unidad(
        date(2026, 8, 31),
        date(2026, 8, 31),
        excluir_dia_operativo_actual=True,
    )

    query = queries[0]
    assert 'FROM dbo.Comercial_KPIs_Diarios_v2 AS k' in query
    assert 'ISNULL(k.activo, 1) = 1' in query
    assert 'ISNULL(k.es_demo, 0) = 0' in query
    assert 'vw_Comercial_KPIs_Diarios_v2_Runtime AS k' not in query


def test_runtime_source_remains_for_non_closed_read(monkeypatch):
    queries = _install_capture(monkeypatch, [{}])

    module.get_kpis_diarios_agregados(
        date(2026, 8, 31),
        date(2026, 8, 31),
        excluir_dia_operativo_actual=False,
    )

    query = queries[0]
    assert 'FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime AS k' in query
    assert 'ISNULL(k.activo, 1) = 1' not in query
    assert 'ISNULL(k.es_demo, 0) = 0' not in query
