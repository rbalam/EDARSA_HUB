from pathlib import Path


def test_mpro_dry_run_uses_real_handler_contract():
    text = Path('api/admin_scheduler_resync.py').read_text(encoding='utf-8')
    assert 'QUERY_MPRO_VENTAS_CERRADAS' in text
    assert "query_source = 'MPRO_HANDLER_OFICIAL'" in text
    assert "d.get('Vn_Precio_Neto_Importe')" in text
    assert "d.get('num_folios')" in text
    assert "d.get('total_personas')" in text
    assert "0 AS propinas_total" not in text
    assert "mpro-handler-oficial-v1" in text


def test_mpro_official_query_exposes_propina_and_personas():
    text = Path('modules/comercial_v2/sync_comercial_edarsahub.py').read_text(encoding='utf-8')
    assert 'ISNULL(c.Co_Propina, 0) as propinas' in text
    assert 'ISNULL(c.Co_Personas, 1) as total_personas' in text
    assert 've.Vn_Folio as Vn_Folio' in text
