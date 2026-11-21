from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / 'backend' / 'modules' / 'inteligencia_comercial' / 'iscam_routes.py'
RESYNC = ROOT / 'backend' / 'api' / 'admin_scheduler_resync.py'
BACKFILL = ROOT / 'backend' / 'scripts' / 'backfill_detalle_producto_pendientes.py'
EXTRACTOR = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'
FRONTEND = ROOT / 'frontend' / 'src' / 'portal-inteligencia' / 'pages' / 'ReportesISCAMPage.jsx'


def test_freshness_compares_detail_against_runtime_per_day():
    text = ROUTES.read_text(encoding='utf-8')
    assert 'def _detail_coverage(' in text
    assert 'dbo.vw_Comercial_KPIs_Diarios_v2_Runtime' in text
    assert 'dbo.Comercial_Inteligencia_VentasDetalleProducto' in text
    assert 'detail_stale' in text
    assert 'detail_sales_gap' in text
    assert 'detail_ticket_gap' in text
    assert 'detail_pax_gap' in text


def test_manual_header_resync_also_dryruns_and_commits_canonical_detail():
    text = RESYNC.read_text(encoding='utf-8')
    assert 'def _ejecutar_backfill_detalle_iscam(' in text
    assert 'commit=False' in text
    assert 'commit=True' in text
    assert 'backfill_detalle_producto_pendientes' in text


def test_days_without_runtime_do_not_block_detail_only_backfill():
    text = BACKFILL.read_text(encoding='utf-8')
    assert 'return (1 if resumen["dias_bloqueados"] else 0), resumen' in text
    assert 'dias_bloqueados"] or resumen["dias_sin_runtime"]' not in text


def test_softrestaurant_detail_keeps_product_amounts_and_reconciles_with_adjustment():
    text = EXTRACTOR.read_text(encoding='utf-8')
    block = text.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'ISNULL(ch.total, 0) AS importe_neto_ticket' in block
    assert 'l.importe_bruto * l.importe_neto_ticket / t.bruto_ticket' not in block
    assert 'CAST(l.importe_bruto AS decimal(18,4)) AS importe_neto' in block
    assert 'SOFT_AJUSTE_CHEQUE' in block
    assert 'totalsrx' not in block
    assert 'subtotalsrx' not in block
    assert 'tr.apertura >=' in block
    assert 'tr.cierre IS NOT NULL' not in block


def test_frontend_warns_and_syncs_detail_gap():
    text = FRONTEND.read_text(encoding='utf-8')
    assert 'freshness?.detail_stale' in text
    assert 'detail_missing_from' in text
    assert 'detail_missing_to' in text
    assert 'Detalle incompleto:' in text
    assert 'iscam-detail-incomplete' in text
    assert 'detalleDependienteIncompleto' in text
