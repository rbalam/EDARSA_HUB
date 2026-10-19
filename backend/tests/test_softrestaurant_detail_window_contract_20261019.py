from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADER = ROOT / 'backend/modules/comercial_v2/sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend/scripts/poblar_ventas_detalle_producto_canonico.py'
PROTECTED_OPEN = ROOT / 'backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py'


def test_softrestaurant_header_and_detail_share_0900_window_contract():
    header = HEADER.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    helper = detail.split(
        'def _soft_operational_datetime_range', 1
    )[1].split('def _extract_soft(', 1)[0]

    assert 'offset_hours = 9' in header
    assert 'DATEADD(hour, -{offset_hours}, tr.apertura)' in header
    assert 'timedelta(hours=9)' in helper
    assert "== 'ESTELAR'" not in helper
    assert "== 'CIENFUEGOS'" not in helper
    assert "== '130MID'" not in helper


def test_scope_does_not_modify_protected_open_sales_contract():
    text = PROTECTED_OPEN.read_text(encoding='utf-8')
    assert 'PROVISIONAL_COMANDA' in text
    assert 'MPRO ORIGEN/QRO: API local (NO SQL Server central)' in text
