from datetime import date
from pathlib import Path

from scripts.poblar_ventas_detalle_producto_canonico import _soft_operational_datetime_range

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def test_detail_day_is_calendar_apertura_day():
    fi, ff = _soft_operational_datetime_range({}, date(2026, 9, 5))
    assert fi == '2026-09-05 00:00:00'
    assert ff == '2026-09-06 00:00:00'


def test_header_and_detail_select_by_turnos_apertura_only():
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    query_block = header.split('QUERY_SOFTRESTAURANT_VENTAS_CERRADAS_DIA =', 1)[1].split('def build_softrestaurant_ventas_cerradas_query', 1)[0]
    assert "CONVERT(varchar, tr.apertura, 112) = '{fecha_operacion_sql}'" in query_block
    assert 'ch.cancelado = 0' in query_block
    assert 'cierre IS NOT NULL' not in query_block
    assert 'idempresa' not in query_block
    block = detail.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'tr.apertura >= %s' in block
    assert 'tr.apertura < %s' in block
    assert 'ISNULL(ch.cancelado, 0) = 0' in block
    assert 'tr.cierre IS NOT NULL' not in block
    assert 'idempresa' not in block


def test_soft_daily_range_does_not_use_operational_turn_service():
    fn = DETAIL.read_text(encoding='utf-8').split('def _soft_operational_datetime_range', 1)[1].split('def _extract_soft(', 1)[0]
    assert 'get_operational_datetime_range_for_fecha_operacion' not in fn
    assert 'Sistema_TurnosOperativosUnidad' not in fn
