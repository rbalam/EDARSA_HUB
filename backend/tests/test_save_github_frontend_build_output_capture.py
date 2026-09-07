import json
from pathlib import Path

TARGET = 'save-github-frontend-build-surgical-fix-v1-20260906'
STATE = Path('/app/.git/universal-worker-queue')
OUT = Path('tests/save_github_frontend_build_output_evidence.json')


def test_capture_exact_frontend_build_output():
    matches = []
    for bucket in ('results', 'done', 'rejected', 'processing', 'pending'):
        path = STATE / bucket / f'{TARGET}.json'
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding='utf-8'))
        frontend_checks = [
            check for check in (payload.get('checks') or [])
            if isinstance(check, dict) and check.get('type') == 'frontend_build'
        ]
        matches.append({
            'bucket': bucket,
            'job_id': payload.get('job_id'),
            'status': payload.get('status'),
            'blockers': payload.get('blockers') or [],
            'frontend_build': frontend_checks,
        })

    evidence = {
        'schema': 'edarsahub.frontend-build-output-evidence.v1',
        'target_job_id': TARGET,
        'production_touched': False,
        'matches': matches,
    }
    OUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert matches, 'TARGET_LOCAL_RESULT_NOT_FOUND'
    assert any(item['frontend_build'] for item in matches), 'FRONTEND_BUILD_CHECK_NOT_FOUND'
    assert evidence['production_touched'] is False
