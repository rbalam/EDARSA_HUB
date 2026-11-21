from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENRICH = ROOT / 'backend/core/scheduler/jobs/inteligencia_comercial_enrich.py'
BACKEND = ROOT / 'backend/api/admin_scheduler_resync.py'
PORTAL = ROOT / 'frontend/src/portal-inteligencia/pages/ReportesISCAMPage.jsx'
PANEL = ROOT / 'frontend/src/components/admin/ResyncPanel.jsx'


def test_payments_only_supports_managementpro_and_softrestaurant():
    text = ENRICH.read_text(encoding='utf-8')
    block = text.split('def resync_pagos_unidad', 1)[1]
    assert '_extract_mpro(cfg, fecha_inicio, fecha_fin)' in block
    assert '_extract_softrestaurant(cfg, fecha_inicio, fecha_fin)' in block
    assert 'payments-only R56 autorizado solo para SoftRestaurant' not in block
    assert '_write_payments_only(' in block


def test_mpro_payment_extractor_uses_explicit_calendar_date_conversion():
    text = ENRICH.read_text(encoding='utf-8')
    block = text.split('def _extract_mpro', 1)[1].split('def _write_enrichment', 1)[0]
    assert block.count("WHERE CONVERT(date, v.Vn_Fecha) >= CONVERT(date, '{fi}')") == 2
    assert block.count("AND CONVERT(date, v.Vn_Fecha) < CONVERT(date, '{ff}')") == 2
    assert "WHERE v.Vn_Fecha >= '{fi}'" not in block


def test_real_sales_resync_also_refreshes_canonical_ticket_payments():
    text = BACKEND.read_text(encoding='utf-8')
    block = text.split('async def _ejecutar_sync_real', 1)[1]
    assert 'resync_pagos_unidad' in block
    assert 'fecha_fin + timedelta(days=1)' in block
    assert "'payments_success': pagos_success" in block
    assert "'pagos_ticket': pagos_ticket" in block


def test_iscam_missing_sync_always_chunks_one_day():
    text = PORTAL.read_text(encoding='utf-8')
    assert 'splitDateChunks(syncFrom, syncTo, 1)' in text
    assert 'splitDateChunks(syncFrom, syncTo, detailOnly ? 1 : 30)' not in text


def test_scheduler_manual_sales_resync_builds_daily_execution_plan():
    text = PANEL.read_text(encoding='utf-8')
    assert 'const splitDailyDateRange = (start, end) =>' in text
    assert "executionCodigo !== 'comercial_ventas_cerradas'" in text
    assert 'splitDailyDateRange(fi, ff)' in text
    assert 'fecha_inicio: fechaInicioItem' in text
    assert 'fecha_fin: fechaFinItem' in text
    assert 'total: executionPlan.length' in text
    assert 'del día ${fechaInicioItem} superó 120 segundos' in text
