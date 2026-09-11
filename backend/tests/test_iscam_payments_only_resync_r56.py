from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENRICH = ROOT / 'backend' / 'core' / 'scheduler' / 'jobs' / 'inteligencia_comercial_enrich.py'
SCRIPT = ROOT / 'backend' / 'scripts' / 'resync_iscam_pagos_unidad.py'


def _payments_only_block():
    text = ENRICH.read_text(encoding='utf-8')
    return text.split('def _write_payments_only', 1)[1].split('def resync_pagos_unidad', 1)[0]


def test_payments_only_writer_mutates_only_payment_table():
    block = _payments_only_block()
    sql_lines = [line.strip() for line in block.splitlines() if 'DELETE FROM dbo.' in line or 'INSERT INTO dbo.' in line or 'UPDATE ' in line]
    assert any('DELETE FROM dbo.Finanzas_CortesCaja_DetallePagos' in line for line in sql_lines)
    assert any('INSERT INTO dbo.Finanzas_CortesCaja_DetallePagos' in line for line in sql_lines)
    assert not any('Sync_Sales' in line for line in sql_lines)
    assert not any('Finanzas_CortesCaja ' in line for line in sql_lines)
    assert not any('Comercial_Inteligencia_VentasDetalleProducto' in line for line in sql_lines)


def test_payments_only_resync_reuses_r54_fx_extractor():
    text = ENRICH.read_text(encoding='utf-8')
    fn = text.split('def resync_pagos_unidad', 1)[1]
    assert '_extract_softrestaurant(cfg, fecha_inicio, fecha_fin)' in fn
    assert '_write_payments_only' in fn
    assert 'COALESCE(NULLIF(cp.tipodecambio, 0), NULLIF(fp.tipodecambio, 0), 1)' in text


def test_cli_is_closed_to_payment_resync_function():
    text = SCRIPT.read_text(encoding='utf-8')
    assert 'resync_pagos_unidad' in text
    assert 'enrich_unidad' not in text
    assert 'sync_cortes' not in text
