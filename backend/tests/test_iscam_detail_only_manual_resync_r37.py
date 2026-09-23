from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend' / 'api' / 'admin_scheduler_resync.py'
FRONTEND = ROOT / 'frontend' / 'src' / 'portal-inteligencia' / 'pages' / 'ReportesISCAMPage.jsx'


def test_resync_request_exposes_explicit_detail_only_flag():
    text = BACKEND.read_text(encoding='utf-8')
    assert 'detail_only: bool = Field(False' in text


def test_detail_only_bypasses_header_connectivity_and_uses_canonical_backfill():
    text = BACKEND.read_text(encoding='utf-8')
    block = text.split('    if request.detail_only:', 1)[1].split('    if _is_netpay_sync', 1)[0]
    assert '_ejecutar_backfill_detalle_iscam(' in block
    assert 'commit=not request.dry_run' in block
    assert '_validar_conectividad' not in block
    assert "'header_resync_skipped': True" in block
    assert '_registrar_resync_log(' in block


def test_frontend_uses_detail_only_only_when_header_is_current():
    text = FRONTEND.read_text(encoding='utf-8')
    assert 'const detailOnly = detailGap && !headerGap;' in text
    assert 'detail_only: detailOnly' in text
    assert 'splitDateChunks(syncFrom, syncTo, 1)' in text
    assert 'freshness?.detail_missing_from' in text
    assert 'freshness?.detail_missing_to' in text


def test_frontend_surfaces_backend_error_instead_of_generic_dry_run_message():
    text = FRONTEND.read_text(encoding='utf-8')
    assert 'dry.data?.error_message' in text
    assert 'dry.data?.resultado?.error_message' in text
    assert 'real.data?.error_message' in text
    assert 'DRY RUN no aprobado para' not in text
