from pathlib import Path
import json
import os
import re

ROOT = Path(__file__).resolve().parents[2]
PROGRAM_PATH = ROOT / 'docs/BOS/PROGRAMA_ESTRATEGICO_BOS_EDARSAHUB_DIRECCION.md'
DOSSIER_PATH = ROOT / 'docs/BOS/certifications/BOS_V1_MASTER_STATUS_GLOBAL_PROGRESS.md'
STATE = Path(str(os.environ.get('EDARSAHUB_ROOT') or '/app')) / '.git/universal-worker-queue'
RUNTIME = STATE / 'results'
PUBLISHED = STATE / 'published'

GATES = {
    'A': {'name': 'Fundacion', 'tokens': ['bos-v1-gate-a', 'gate-a-', 'gate-a0', 'foundation', 'fundacion', 'master-architecture', 'core-slimming']},
    'B': {'name': 'Operacion autonoma', 'tokens': ['bos-v1-gate-b', 'gate-b-', 'universal-worker', 'worker-', 'self-heal', 'zero-touch', 'watchdog', 'orchestrator']},
    'C': {'name': 'Cobertura funcional', 'tokens': ['bos-v1-gate-c-functional-coverage-certification-r3']},
    'D': {'name': 'Gobierno', 'tokens': ['bos-v1-gate-d', 'gate-d-', 'rbac', 'capability-policy', 'procedure-policy', 'policy-engine', 'governance']},
    'E': {'name': 'BOS Ejecutivo', 'tokens': ['bos-v1-gate-e', 'gate-e-', 'bos-ejecutivo', 'executive', 'direccion']},
    'F': {'name': 'Inteligencia', 'tokens': ['bos-v1-gate-f', 'gate-f-', 'inteligencia', 'forecast', 'competitive', 'benchmark']},
    'G': {'name': 'Certificacion V1.0', 'tokens': ['bos-v1-gate-g', 'gate-g-', 'certificacion-v1', 'certification-v1', 'e2e-v1']},
}

CERTIFIED_MARKERS = {'CERTIFIED', 'CERTIFIED_READ_ONLY', 'CERTIFIED_OPERATIONAL'}
TERMINAL_SUCCESS = {'INTEGRATED', 'READ_ONLY_COMPLETE', 'OPERATIONAL_COMPLETE'}


def published_certification(result_path):
    marker = PUBLISHED / result_path.name
    if not marker.is_file():
        return ''
    text = marker.read_text(encoding='utf-8', errors='ignore')
    for line in text.splitlines():
        if line.startswith('certification='):
            return line.split('=', 1)[1].strip()
    return ''


def load_results():
    rows = []
    assert RUNTIME.is_dir(), f'BOS_MASTER_RUNTIME_RESULTS_NOT_FOUND:{RUNTIME}'
    for p in RUNTIME.glob('*.json'):
        try:
            d = json.loads(p.read_text(encoding='utf-8', errors='ignore'))
        except Exception:
            continue
        if d.get('production_touched', False):
            continue
        jid = str(d.get('job_id', p.stem)).lower()
        if jid in {'bos-v1-master-status-global-progress-r2', 'bos-v1-master-status-global-progress-r3', 'bos-v1-master-status-global-progress-r4', 'bos-v1-master-status-global-progress-r5', 'bos-v1-master-status-global-progress-r6'}:
            continue
        status = str(d.get('status', ''))
        tests = str(d.get('tests', ''))
        quality_gate = str(d.get('quality_gate', ''))
        blockers = d.get('blockers') or []
        certification = str(d.get('certification', ''))
        marker_certification = published_certification(p)
        if marker_certification:
            certification = marker_certification
        percent_complete = int(d.get('percent_complete') or 0)
        if (
            certification in CERTIFIED_MARKERS
            and status in TERMINAL_SUCCESS
            and tests == 'PASS'
            and quality_gate in {'PASS', ''}
            and not blockers
            and not d.get('production_touched', False)
        ):
            percent_complete = 100
        rows.append({
            'path': str(p),
            'job_id': jid,
            'status': status,
            'tests': tests,
            'quality_gate': quality_gate,
            'certification': certification,
            'percent_complete': percent_complete,
            'blockers': blockers,
            'production_touched': bool(d.get('production_touched', False)),
            'sha': str(d.get('certified_source_sha') or d.get('development_sha') or d.get('candidate_sha') or ''),
            'raw': d,
        })
    return rows


def gate_matches(gate, row):
    jid = row['job_id']
    return any(t in jid for t in GATES[gate]['tokens'])


def is_closed(row):
    return (
        row['certification'] in CERTIFIED_MARKERS
        and row['percent_complete'] == 100
        and row['tests'] == 'PASS'
        and row['quality_gate'] in {'PASS', ''}
        and not row['blockers']
        and not row['production_touched']
    )


def best_for_gate(gate, rows):
    matches = [r for r in rows if gate_matches(gate, r)]
    closed = [r for r in matches if is_closed(r)]
    if closed:
        best = sorted(closed, key=lambda r: (r['percent_complete'], r['job_id']), reverse=True)[0]
        return 100, 'COMPLETE', best, matches
    if matches:
        best = sorted(matches, key=lambda r: (r['percent_complete'], r['certification'] in CERTIFIED_MARKERS, r['job_id']), reverse=True)[0]
        pct = max(0, min(99, best['percent_complete']))
        state = 'BLOCKED' if best['blockers'] or best['status'] == 'BLOCKED' or best['tests'] == 'FAIL' else 'PARTIAL'
        return pct, state, best, matches
    return 0, 'NOT_STARTED', None, []


def build_status():
    program = PROGRAM_PATH.read_text(encoding='utf-8', errors='ignore')
    for gate in GATES:
        assert re.search(rf'Gate {gate}\s*-', program, flags=re.I), f'BOS_MASTER_PROGRAM_GATE_MISSING:{gate}'

    rows = load_results()
    matrix = {}
    for gate in GATES:
        pct, state, best, matches = best_for_gate(gate, rows)
        matrix[gate] = {
            'name': GATES[gate]['name'],
            'percent': pct,
            'state': state,
            'matched_job_id': best['job_id'] if best else '',
            'certification': best['certification'] if best else '',
            'tests': best['tests'] if best else '',
            'quality_gate': best['quality_gate'] if best else '',
            'blockers': best['blockers'] if best else [],
            'sha': best['sha'] if best else '',
            'candidate_results': len(matches),
        }

    c = matrix['C']
    assert c['percent'] == 100 and c['state'] == 'COMPLETE', 'BOS_MASTER_GATE_C_R3_NOT_CLOSED'

    values = [matrix[g]['percent'] for g in GATES]
    global_pct = round(sum(values) / len(values), 2)
    certified_pct = round(sum(100 for g in GATES if matrix[g]['state'] == 'COMPLETE') / len(GATES), 2)
    functional_evidence_pct = global_pct

    counts = {
        'gates_total': len(GATES),
        'gates_complete': sum(1 for g in GATES if matrix[g]['state'] == 'COMPLETE'),
        'gates_partial': sum(1 for g in GATES if matrix[g]['state'] == 'PARTIAL'),
        'gates_blocked': sum(1 for g in GATES if matrix[g]['state'] == 'BLOCKED'),
        'gates_not_started': sum(1 for g in GATES if matrix[g]['state'] == 'NOT_STARTED'),
    }

    open_gates = [g for g in GATES if matrix[g]['state'] != 'COMPLETE']
    next_gate = open_gates[0] if open_gates else 'NONE'
    blockers = [f"Gate {g}: {matrix[g]['blockers']}" for g in GATES if matrix[g]['blockers']]

    return matrix, counts, global_pct, certified_pct, functional_evidence_pct, blockers, next_gate


def render_dossier(matrix, counts, global_pct, certified_pct, functional_evidence_pct, blockers, next_gate):
    lines = [
        '# BOS V1 - Master Status Global Progress R6',
        '',
        'Evidence-only. No functional changes.',
        '',
        '## Metodo',
        '- Program scope: Gates A-G definidos por el Programa Estrategico BOS V1.',
        '- Weighting method: uniforme, 1/7 por Gate; el programa no define pesos numericos diferentes.',
        '- COMPLETE: resultado terminal identificable, CERTIFIED/CERTIFIED_READ_ONLY, percent_complete=100, tests=PASS, quality_gate=PASS (o no informado), blockers=[], production_touched=false.',
        '- PARTIAL/BLOCKED: mejor percent_complete terminal verificable asociado al Gate, limitado a 99 hasta certificacion completa.',
        '- NOT_STARTED: sin evidencia terminal asociable.',
        '- Sin doble conteo de subgates: cada Gate aporta una sola cifra final.',
        '',
        '## Matriz A-G',
        '',
        '| Gate | Nombre | Estado | Avance | Evidencia terminal | Certificacion | Tests | Blockers |',
        '|---|---|---|---:|---|---|---|---|',
    ]
    for g in GATES:
        r = matrix[g]
        lines.append(f"| {g} | {r['name']} | {r['state']} | {r['percent']}% | `{r['matched_job_id']}` | {r['certification'] or '-'} | {r['tests'] or '-'} | {json.dumps(r['blockers'], ensure_ascii=False)} |")

    lines += [
        '',
        '## Resultado maestro',
        f"- gates_total: {counts['gates_total']}",
        f"- gates_complete: {counts['gates_complete']}",
        f"- gates_partial: {counts['gates_partial']}",
        f"- gates_blocked: {counts['gates_blocked']}",
        f"- gates_not_started: {counts['gates_not_started']}",
        f'- global_percent_complete: {global_pct}%',
        f'- certified_percent_complete: {certified_pct}%',
        f'- functional_evidence_percent_complete: {functional_evidence_pct}%',
        f'- blockers: {json.dumps(blockers, ensure_ascii=False)}',
        f'- next_gate: Gate {next_gate}' if next_gate != 'NONE' else '- next_gate: NONE',
        '- production_touched: false',
        '',
        '## Resumen',
    ]
    for g in GATES:
        lines.append(f"Gate {g} = {matrix[g]['percent']}%")
    lines.append(f'BOS V1 GLOBAL = {global_pct}%')
    lines.append('')
    return '\n'.join(lines)


def test_bos_v1_master_status_global_progress_is_materialized():
    matrix, counts, global_pct, certified_pct, functional_evidence_pct, blockers, next_gate = build_status()
    dossier = render_dossier(matrix, counts, global_pct, certified_pct, functional_evidence_pct, blockers, next_gate)
    DOSSIER_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOSSIER_PATH.write_text(dossier, encoding='utf-8')

    print('BOS_V1_GATE_MATRIX=' + json.dumps(matrix, ensure_ascii=False, sort_keys=True))
    print('BOS_V1_GLOBAL_PERCENT=' + str(global_pct))
    print('BOS_V1_CERTIFIED_PERCENT=' + str(certified_pct))
    print('BOS_V1_NEXT_GATE=' + str(next_gate))

    assert counts['gates_total'] == 7
    assert all(g in matrix for g in 'ABCDEFG')
    assert 0 <= global_pct <= 100
    assert 'Gate A =' in dossier and 'Gate G =' in dossier
    assert re.search(r'BOS V1 GLOBAL = \d+(?:\.\d+)?%', dossier), 'BOS_MASTER_GLOBAL_PERCENT_NOT_MATERIALIZED'
