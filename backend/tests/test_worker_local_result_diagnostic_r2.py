import json
import subprocess
from pathlib import Path

OUT = Path('tests/worker_local_result_diagnostic_r2_evidence.json')
STATE = Path('/app/.git/universal-worker-queue')
TARGETS = {
    'EDARSAHUB-ISCAM-DETAIL-REPORTS-AUDIT-R1-CARLOS-20260905T160000Z',
    'EDARSAHUB-WORKER-RESULT-PUBLISHER-AUTH-RECOVERY-R1-CARLOS-20260905T163200Z',
}


def _cmd(args):
    p = subprocess.run(args, cwd='/app', text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {'returncode': p.returncode, 'output': p.stdout[-12000:]}


def _load_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return {'_error': f'{type(exc).__name__}: {exc}', '_path': str(path)}


def test_capture_worker_local_result_state_r2():
    matches = []
    for sub in ('results', 'rejected', 'done', 'processing', 'pending'):
        root = STATE / sub
        if not root.exists():
            continue
        for path in root.glob('*.json'):
            payload = _load_json(path)
            job_id = str(payload.get('job_id') or path.stem)
            if job_id in TARGETS:
                matches.append({'bucket': sub, 'path': str(path), 'payload': payload})

    published = []
    pubdir = STATE / 'published'
    if pubdir.exists():
        for path in pubdir.iterdir():
            if any(job in path.name for job in TARGETS):
                published.append({'path': str(path), 'content': path.read_text(encoding='utf-8', errors='replace')})

    runtime_files = {}
    runtime = STATE / 'runtime'
    if runtime.exists():
        for name in ('last_cycle_utc', 'last_receive_utc', 'last_terminal_utc', 'pid', 'generation'):
            p = runtime / name
            if p.exists():
                runtime_files[name] = p.read_text(encoding='utf-8', errors='replace').strip()

    payload = {
        'schema': 'edarsahub.worker-local-result-diagnostic.v2',
        'production_touched': False,
        'targets': sorted(TARGETS),
        'matches': matches,
        'published_markers': published,
        'runtime': runtime_files,
        'git_status': _cmd(['git', 'status', '--porcelain=v1', '--untracked-files=all']),
        'publisher_diff': _cmd(['git', 'diff', '--', 'tools/mirror_sync/universal_job_result_publisher.py']),
        'head': _cmd(['git', 'rev-parse', 'HEAD']),
        'remote_dev': _cmd(['git', 'rev-parse', 'origin/Edarsahub_Desarrollo']),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    assert payload['production_touched'] is False
    assert matches, 'No se localizaron resultados locales para los jobs objetivo'
