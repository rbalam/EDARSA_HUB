from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = ROOT / 'docs' / 'BOS' / 'PROGRAMA_ESTRATEGICO_BOS_EDARSAHUB_DIRECCION.md'
STATUS = ROOT / 'docs' / 'BOS' / 'STATUS_PROGRAMA_ESTRATEGICO_BOS_DIRECCION.md'
WORKER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_worker.sh'

def test_gate_b_contract_and_existing_autonomous_worker():
    program = PROGRAM.read_text(encoding='utf-8')
    status = STATUS.read_text(encoding='utf-8')
    worker = WORKER.read_text(encoding='utf-8')
    assert 'Gate B - Operacion autonoma' in program
    for token in ('Universal Worker', 'mirror', 'watchdog', 'self-healing', 'cola', 'evidencias', 'idempotencia', 'gates', 'proteccion contra cambios destructivos'):
        assert token in program
    assert '| Automatizacion / Worker / self-healing | 100% |' in status
    assert 'intake_loop &' in worker
    assert 'dispatch_loop &' in worker
    assert 'result_loop &' in worker
    assert 'health_loop &' in worker
