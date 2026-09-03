from pathlib import Path


SOURCE = (
    Path(__file__).resolve().parents[1]
    / 'modules'
    / 'comercial_v2'
    / 'sync_comercial_edarsahub.py'
).read_text(encoding='utf-8')


def test_empresa_id_prefers_catalog_and_has_safe_read_only_fallback():
    assert '(server_config or {}).get("empresa_id")' in SOURCE
    assert 'SELECT DISTINCT' in SOURCE
    assert 'FROM turnos AS t' in SOURCE
    assert 't.cierre IS NOT NULL' in SOURCE
    assert 'execute_query_on_server(' in SOURCE
    assert 'len(candidates) == 1' in SOURCE
    assert 'multiples idempresa' in SOURCE


def test_official_query_still_filters_both_cheques_and_turnos():
    assert "ch.idempresa = '{empresa_id}'" in SOURCE
    assert "t.idempresa = '{empresa_id}'" in SOURCE
    assert 'AND ch.cancelado = 0' in SOURCE
