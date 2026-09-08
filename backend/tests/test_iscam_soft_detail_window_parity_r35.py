from datetime import date
from pathlib import Path

from scripts.poblar_ventas_detalle_producto_canonico import _soft_operational_datetime_range

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def test_detail_window_is_same_09_to_09_contract_as_header():
    fi, ff = _soft_operational_datetime_range({}, date(2026, 8, 20))
    assert fi == '2026-08-20 09:00:00'
    assert ff == '2026-08-21 09:00:00'


def test_header_and_detail_both_assign_by_turnos_apertura():
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    assert "inicio_operativo = fecha_actual.strftime('%Y-%m-%d 09:00:00')" in header
    assert "fin_operativo = fecha_siguiente.strftime('%Y-%m-%d 09:00:00')" in header
    assert "AND apertura < '{fin_operativo}'" in header
    block = detail.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'tr.apertura >= %s' in block
    assert 'tr.apertura < %s' in block
    assert 'tr.cierre IS NOT NULL' in block
    assert 'tr.cierre >=' not in block
    assert 'tr.cierre <' not in block


def test_detail_does_not_use_separate_operational_window_service_anymore():
    fn = DETAIL.read_text(encoding='utf-8').split('def _soft_operational_datetime_range', 1)[1].split('def _softrestaurant_empresa_id_for_window', 1)[0]
    assert 'get_operational_datetime_range_for_fecha_operacion' not in fn
    assert 'Sistema_TurnosOperativosUnidad' not in fn
