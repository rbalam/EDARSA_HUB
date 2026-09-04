import json
import subprocess
from pathlib import Path

EVIDENCE = Path('tests/preview_dirty_capture_iscam_estelar_r4_evidence.json')

def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, cwd='/app', text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return {'returncode': p.returncode, 'output': p.stdout}
    except Exception as exc:
        return {'returncode': -999, 'output': f'{type(exc).__name__}:{exc}'}

def test_capture_preview_dirty_state_r4():
    diff = run(['git','diff','--','tools/mirror_sync/universal_job_result_publisher.py'])
    untracked = Path('/app/backend/tests/test_universal_job_result_publisher_git_auth_contract.py')
    payload = {
        'schema': 'edarsahub.preview-dirty-capture.v1',
        'production_touched': False,
        'git_diff_returncode': diff['returncode'],
        'git_diff_universal_job_result_publisher': diff['output'],
        'untracked_test_exists': untracked.exists(),
        'untracked_test_content': untracked.read_text(encoding='utf-8') if untracked.exists() else '',
        'status_porcelain': run(['git','status','--porcelain=v1','--untracked-files=all'])['output']
    }
    EVIDENCE.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    assert payload['production_touched'] is False
    assert diff['returncode'] == 0
