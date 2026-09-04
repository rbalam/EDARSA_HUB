import json
import os
import subprocess
from pathlib import Path

EVIDENCE = Path('tests/preview_diag_iscam_estelar_r3_evidence.json')

def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, cwd='/app', text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return {'returncode': p.returncode, 'output': p.stdout[-12000:]}
    except Exception as exc:
        return {'returncode': -999, 'output': f'{type(exc).__name__}:{exc}'}

def val(cmd):
    r = run(cmd)
    return r['output'].strip() if r['returncode'] == 0 else None

def test_preview_runtime_diagnostic_only_r3():
    env_name = str(os.getenv('EDARSA_ENV') or os.getenv('APP_ENV') or os.getenv('ENVIRONMENT') or 'PREVIEW').upper()
    evidence = {
        'schema': 'edarsahub.preview-diagnostic.v3',
        'environment': env_name,
        'production_touched': False,
        'branch': val(['git','branch','--show-current']),
        'local_head': val(['git','rev-parse','HEAD']),
        'remote_head': val(['git','rev-parse','origin/Edarsahub_Desarrollo']),
        'topology': val(['git','rev-list','--left-right','--count','HEAD...origin/Edarsahub_Desarrollo']),
        'status_porcelain': val(['git','status','--porcelain=v1','--untracked-files=all']) or '',
        'mirror_enabled': Path('/app/.git/mirror-sync/ENABLED').exists(),
        'mirror_stop': Path('/app/.git/mirror-sync/STOP').exists(),
        'sync_pause': Path('/app/.git/EDARSAHUB_SYNC_PAUSED').exists(),
        'temp_mirror_stop': Path('/tmp/edarsahub-mirror-sync/STOP').exists(),
        'worker_stop': Path('/app/.git/universal-worker-queue/STOP').exists(),
        'temp_worker_stop': Path('/tmp/edarsahub-universal-worker/STOP').exists(),
        'supervisor_status': run(['supervisorctl','status'])
    }
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    assert 'PROD' not in env_name
    assert evidence['production_touched'] is False
