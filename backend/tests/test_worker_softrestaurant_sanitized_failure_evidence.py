import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'tools' / 'mirror_sync'
DISPATCHER = TOOLS / 'universal_job_dispatcher.py'
PUBLISHER = TOOLS / 'universal_job_result_publisher.py'


def _load_dispatcher():
    sys.path.insert(0, str(TOOLS))
    try:
        spec = importlib.util.spec_from_file_location('dispatcher_soft_summary', DISPATCHER)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)


def test_summary_is_sanitized_and_identifies_failed_unit():
    module = _load_dispatcher()
    output = '{"event":"start","execute":true}\n' + '{"event":"summary","results":[{"unidad":"130MID","status":"FAIL","payment_windows":3,"corte_windows":0,"pagos_insertados":7,"errors":["OperationalError:secret detail must not publish"]}]}\n'
    value = module.summarize_softrestaurant_output(output)
    assert value['results'][0]['unidad'] == '130MID'
    assert value['results'][0]['status'] == 'FAIL'
    assert value['results'][0]['error_types'] == ['OperationalError']
    assert 'secret detail' not in str(value)


def test_iscam_backfill_summary_is_sanitized_and_keeps_day_deltas():
    module = _load_dispatcher()
    output = 'HEADER\n' + '{"run_id":"x","modo":"DRY_RUN","fecha_inicio":"2026-09-11","fecha_fin_exclusivo":"2026-09-12","dias_evaluados":1,"dias_ya_ok":0,"dias_candidatos":1,"dias_reparables":0,"dias_bloqueados":1,"dias_sin_runtime":0,"filas_insertadas":0,"unidades":[{"unidad":"130MID","ya_ok":0,"candidatos":1,"reparables":0,"bloqueados":1,"sin_runtime":0,"filas_insertadas":0,"dias":[{"fecha_operacion":"2026-09-11","status":"NO_CUADRA_REVISAR","ventas_runtime":"133674.00","ventas_pos":"133673.00","delta_ventas":"1.00","tickets_runtime":36,"tickets_pos":36,"delta_tickets":0,"pax_runtime":85,"pax_pos":85,"delta_pax":0,"error":"password=must-not-publish"}]}]}\n'
    value = module.summarize_iscam_detail_backfill_output(output)
    assert value['dias_bloqueados'] == 1
    day = value['unidades'][0]['dias'][0]
    assert day['status'] == 'NO_CUADRA_REVISAR'
    assert day['delta_ventas'] == '1.00'
    assert 'password' not in str(value)
    assert 'must-not-publish' not in str(value)


def test_publisher_allows_summary_but_not_raw_output():
    text = PUBLISHER.read_text(encoding='utf-8')
    assert '"operation_summary"' in text
    allowed_block = text.split('def sanitize', 1)[1].split('public =', 1)[0]
    assert '"operation_output"' not in allowed_block
