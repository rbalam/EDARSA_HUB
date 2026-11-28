from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKFILL = ROOT / 'backend' / 'scripts' / 'backfill_detalle_producto_pendientes.py'
ROUTES = ROOT / 'backend' / 'modules' / 'inteligencia_comercial' / 'iscam_routes.py'


def test_backfill_aggregates_pax_once_per_ticket():
    text = BACKFILL.read_text(encoding='utf-8')
    block = text.split('def _detalle_existente(', 1)[1].split('def _detalle_concilia(', 1)[0]
    assert 'WITH detalle_ticket AS (' in block
    assert 'GROUP BY fecha_operacion, numero_ticket' in block
    assert 'MAX(CAST(ISNULL(pax, 0) AS bigint)) AS pax_ticket' in block
    assert 'SUM(pax_ticket) AS pax_detalle' in block
    assert 'SUM(\n                CASE\n                    WHEN ISNULL(es_kpi_valido, 1) = 1\n                    THEN ISNULL(pax, 0)' not in block


def test_freshness_aggregates_pax_once_per_ticket():
    text = ROUTES.read_text(encoding='utf-8')
    block = text.split('def _detail_coverage(', 1)[1].split('# ============================================================================\n# 1)', 1)[0]
    assert 'detalle_ticket AS (' in block
    assert 'GROUP BY CAST(fecha_operacion AS date), numero_ticket' in block
    assert 'MAX(CAST(ISNULL(pax,0) AS bigint)) AS pax_ticket' in block
    assert 'SUM(pax_ticket) AS pax_detalle' in block
    assert 'SUM(CAST(ISNULL(pax,0) AS bigint)) AS pax_detalle' not in block
