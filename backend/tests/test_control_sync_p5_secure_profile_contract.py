from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github/workflows/centro-control-sync-monitor-p5-runtime-e2e.yml'
RUNTIME_TEST = ROOT / 'backend/tests/test_control_sync_p5_runtime_secure_e2e.py'
REQUEST = ROOT / 'ops/e2e/requests/CENTRO-CONTROL-SYNC-MONITOR-P5-RUNTIME-SECURE-R1.execute'


def test_secure_profile_contract():
    workflow = WORKFLOW.read_text(encoding='utf-8')
    runtime = RUNTIME_TEST.read_text(encoding='utf-8')
    request = REQUEST.read_text(encoding='utf-8').strip()

    assert 'environment: development' in workflow
    assert 'P5_SECRET_PROFILE: P5_E2E_SUPERADMIN' in workflow
    assert '${{ secrets.TEST_SUPERADMIN_EMAIL }}' in workflow
    assert '${{ secrets.TEST_SUPERADMIN_PASSWORD }}' in workflow
    assert '${{ vars.TEST_BASE_URL }}' in workflow
    assert request == 'P5_E2E_SUPERADMIN'

    assert 'qa.superadmin@edarsa.com' not in workflow
    assert 'qa.superadmin@edarsa.com' not in runtime
    assert 'http://127.0.0.1:8001' not in workflow
    assert 'http://127.0.0.1:8001' not in runtime
    assert '/email/test' not in runtime
    assert '/whatsapp/test' not in runtime
    assert '/alerta-critica' not in runtime
    assert "session.post(\n        f'{BASE_URL}/api/auth/login'" in runtime
    assert runtime.count('session.post(') == 1
    assert "'external_messages_sent': False" in runtime
    assert "'production_touched': False" in runtime
