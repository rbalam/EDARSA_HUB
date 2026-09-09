from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = ROOT / 'docs' / 'BOS' / 'PROGRAMA_ESTRATEGICO_BOS_EDARSAHUB_DIRECCION.md'
STATUS = ROOT / 'docs' / 'BOS' / 'STATUS_PROGRAMA_ESTRATEGICO_BOS_DIRECCION.md'
COMERCIAL = ROOT / 'backend' / 'modules' / 'comercial_v2' / 'sync_comercial_edarsahub.py'

def test_gate_a_contract_and_existing_canonical_foundation():
    program = PROGRAM.read_text(encoding='utf-8')
    status = STATUS.read_text(encoding='utf-8')
    comercial = COMERCIAL.read_text(encoding='utf-8')
    assert 'Gate A - Fundacion' in program
    for token in ('SQL-first', 'multiempresa', 'multiunidad', 'multisoftware', 'zonas horarias', 'monedas', 'internacionalizacion', 'integraciones desacopladas', 'sin hardcodes estructurales'):
        assert token in program
    assert '| Fundacion tecnologica y arquitectura BOS | 100% |' in status
    assert 'Servidores_Conexiones' in comercial
    assert 'Sistema_TurnosOperativosUnidad' in comercial
