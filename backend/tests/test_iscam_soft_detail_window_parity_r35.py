from datetime import date
from pathlib import Path

from scripts.poblar_ventas_detalle_producto_canonico import _soft_operational_datetime_range

ROOT = Path(__file__).resolve().parents[2]
SYNC = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'
DETAIL = ROOT / 'backend' / 'scripts' / 'poblar_ventas_detalle_producto_canonico.py'


def test_detail_window_uses_canonical_operational_window(monkeypatch):
    import core.utils.operational_window as ow

    monkeypatch.setattr(
        ow,
        'get_operational_datetime_range_for_fecha_operacion',
        lambda unidad, dia: (
            __import__('datetime').datetime(2026, 8, 20, 12, 55),
            __import__('datetime').datetime(2026, 8, 21, 12, 55),
            {'unidad': unidad},
        ),
    )
    fi, ff = _soft_operational_datetime_range(
        {'unidad_codigo': 'ESTELAR'}, date(2026, 8, 20)
    )
    assert fi == '2026-08-20 12:55:00'
    assert ff == '2026-08-21 12:55:00'


def test_header_and_detail_both_use_operational_service_and_turnos_join():
    header = SYNC.read_text(encoding='utf-8')
    detail = DETAIL.read_text(encoding='utf-8')
    assert 'get_operational_datetime_range_for_fecha_operacion' in header
    assert "INNER JOIN turnos AS tr" in header
    assert "tr.apertura >= '{inicio_operativo}'" in header
    assert "tr.apertura < '{fin_operativo}'" in header
    block = detail.split('def _extract_soft(', 1)[1].split('def _mpro_operational_datetime_range', 1)[0]
    assert 'tr.apertura >= %s' in block
    assert 'tr.apertura < %s' in block
    assert 'tr.cierre IS NOT NULL' in block
    assert 'tr.cierre >=' not in block
    assert 'tr.cierre <' not in block


def test_detail_does_not_hardcode_a_second_window():
    fn = DETAIL.read_text(encoding='utf-8').split('def _soft_operational_datetime_range', 1)[1].split('def _softrestaurant_empresa_id_for_window', 1)[0]
    assert 'get_operational_datetime_range_for_fecha_operacion' in fn
    assert 'replace(hour=9)' not in fn
    assert '09:00:00' not in fn
