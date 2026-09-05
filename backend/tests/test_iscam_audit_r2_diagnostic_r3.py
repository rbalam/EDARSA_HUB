import json
from pathlib import Path

OUT = Path('tests/iscam_audit_r2_diagnostic_r3_evidence.json')
STATE = Path('/app/.git/universal-worker-queue')
TARGET = 'EDARSAHUB-ISCAM-DETAIL-REPORTS-AUDIT-R2-CARLOS-20260905T215500Z'


def _load(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return {'_error': f'{type(exc).__name__}: {exc}', '_path': str(path)}


def test_capture_iscam_audit_r2_result():
    matches = []
    for bucket in ('results', 'rejected', 'done', 'processing', 'pending'):
        root = STATE / bucket
        if not root.exists():
            continue
        for path in root.glob('*.json'):
            payload = _load(path)
            job_id = str(payload.get('job_id') or path.stem)
            embedded = payload.get('job') if isinstance(payload, dict) else None
            embedded_id = str((embedded or {}).get('job_id') or '') if isinstance(embedded, dict) else ''
            if job_id == TARGET or embedded_id == TARGET or path.stem == TARGET:
                matches.append({'bucket': bucket, 'path': str(path), 'payload': payload})

    evidence = {
        'schema': 'edarsahub.iscam-audit-r2-diagnostic.v1',
        'target': TARGET,
        'production_touched': False,
        'matches': matches,
    }
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    assert matches, 'No se localizó el resultado local del audit R2'
    assert evidence['production_touched'] is False
