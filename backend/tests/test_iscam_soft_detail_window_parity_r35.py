from datetime import date
from pathlib import Path

from scripts.poblar_ventas_detalle_producto_canonico import _soft_operational_datetime_range

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def test_detail_day_matches_validated_apertura_window():
    fi, ff = _soft_operational_datetime_range({}, date(2026, 9, 5))
    assert fi == '2026-09-05 09:00:00'
    assert ff == '2026-09-06 09:00:00'


def test_header_and_detail_select_by_same_apertura_window():
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    query_block = header.split('QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA =', 1)[1].split('def _resolve_softrestaurant_empresa_id_for_window', 1)[0]
    assert "apertura >= '{inicio_operativo}'" in query_block
    assert "apertura < '{fin_operativo}'" in query_block
    assert 'cancelado = 0' in query_block
    assert 'cierre IS NOT NULL' in query_block
    assert 'idempresa' in query_block
    block = detail.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'tr.apertura >= %s' in block
    assert 'tr.apertura < %s' in block
    assert 'tr.cierre IS NOT NULL' in block
    assert 'ch.idempresa = %s' in block
    assert 'tr.idempresa = %s' in block


def test_soft_daily_range_does_not_call_operational_turn_service():
    fn = DETAIL.read_text(encoding='utf-8').split('def _soft_operational_datetime_range', 1)[1].split('def _extract_soft(', 1)[0]
    assert 'get_operational_datetime_range_for_fecha_operacion' not in fn
    assert 'from core.utils.operational_window import' not in fn
