from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = (ROOT / 'docs/BOS/PROGRAMA_ESTRATEGICO_BOS_EDARSAHUB_DIRECCION.md').read_text(encoding='utf-8', errors='ignore').lower()

GROUPS = {
    'comercial': ['comercial', 'ventas'],
    'costos_margenes': ['costos', 'margen'],
    'finanzas_tesoreria': ['finanzas', 'tesoreria', 'cxp', 'pago'],
    'inventarios': ['inventario', 'almacen'],
    'clientes_crm': ['cliente', 'crm'],
    'operaciones': ['operacion', 'operaciones'],
    'administracion': ['administracion', 'admin'],
}


def repository_corpus():
    parts = []
    for base in (ROOT / 'backend', ROOT / 'docs'):
        if not base.exists():
            continue
        for p in base.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in {'.py', '.md', '.json'}:
                continue
            if p.name == 'test_bos_v1_gate_c_functional_coverage_certification.py':
                continue
            try:
                parts.append(p.read_text(encoding='utf-8', errors='ignore').lower())
            except Exception:
                pass
    return '\n'.join(parts)


def certified_results():
    edarsahub_root = Path(str(os.environ.get('EDARSAHUB_ROOT') or '/app'))
    runtime = edarsahub_root / '.git/universal-worker-queue/results'
    rows = []
    if not runtime.is_dir():
        return rows
    for p in runtime.glob('*.json'):
        try:
            raw = p.read_text(encoding='utf-8', errors='ignore')
            d = json.loads(raw)
        except Exception:
            continue
        if d.get('certification') not in {'CERTIFIED', 'CERTIFIED_READ_ONLY'}:
            continue
        if d.get('percent_complete') != 100:
            continue
        if d.get('production_touched', False):
            continue
        jid = str(d.get('job_id', '')).lower()
        evidence_text = json.dumps(d, ensure_ascii=False, sort_keys=True).lower()
        rows.append({'job_id': jid, 'evidence_text': evidence_text, 'path': str(p)})
    return rows


def build_matrix():
    text = repository_corpus()
    results = certified_results()
    matrix = {}
    for name, tokens in GROUPS.items():
        repository_ok = any(t in text for t in tokens)
        jobid_matches = [(r['job_id'], t) for r in results for t in tokens if t in r['job_id']]
        evidence_matches = [(r['job_id'], t) for r in results for t in tokens if t in r['evidence_text']]
        terminal_jobid_ok = bool(jobid_matches)
        terminal_evidence_ok = bool(evidence_matches)
        matched = jobid_matches[0] if jobid_matches else (evidence_matches[0] if evidence_matches else ('', ''))
        if repository_ok and terminal_evidence_ok:
            classification = 'PASS' if terminal_jobid_ok else 'TEST_FALSE_NEGATIVE'
        else:
            classification = 'REAL_MISSING_EVIDENCE'
        matrix[name] = {
            'repository_ok': repository_ok,
            'terminal_jobid_ok': terminal_jobid_ok,
            'terminal_evidence_ok': terminal_evidence_ok,
            'matched_token': matched[1],
            'matched_job_id': matched[0],
            'classification': classification,
        }
    return matrix


def test_gate_c_existing_coverage_is_complete():
    assert 'gate c - cobertura funcional' in PROGRAM, 'GATE_C_PROGRAM_MARKER_MISSING'
    matrix = build_matrix()
    print('GATE_C_MATRIX=' + json.dumps(matrix, ensure_ascii=False, sort_keys=True))
    false_negatives = [name for name, row in matrix.items() if row['classification'] == 'TEST_FALSE_NEGATIVE']
    missing = [name for name, row in matrix.items() if row['classification'] == 'REAL_MISSING_EVIDENCE']
    print('GATE_C_TEST_FALSE_NEGATIVES=' + json.dumps(false_negatives, ensure_ascii=False))
    print('GATE_C_MISSING=' + json.dumps(missing, ensure_ascii=False))
    assert not missing, 'GATE_C_MISSING_EVIDENCE:' + ','.join(missing)
