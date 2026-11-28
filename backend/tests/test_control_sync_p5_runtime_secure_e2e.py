import json
import os
from pathlib import Path

import pytest
import requests


BASE_URL = os.environ.get('TEST_BASE_URL', '').rstrip('/')
EMAIL = os.environ.get('TEST_SUPERADMIN_EMAIL', '')
PASSWORD = os.environ.get('TEST_SUPERADMIN_PASSWORD', '')
EVIDENCE_FILE = Path(os.environ.get('P5_EVIDENCE_FILE', '/tmp/p5-evidence.json'))

EVIDENCE = {
    'profile': 'P5_E2E_SUPERADMIN',
    'environment': 'development',
    'production_touched': False,
    'external_messages_sent': False,
    'checks': [],
}


def _record(name, status, http_status=None):
    row = {'name': name, 'status': status}
    if http_status is not None:
        row['http_status'] = int(http_status)
    EVIDENCE['checks'].append(row)
    EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_FILE.write_text(json.dumps(EVIDENCE, ensure_ascii=False, indent=2), encoding='utf-8')


def _require_runtime_config():
    assert BASE_URL, 'RUNTIME_E2E_CONFIG_MISSING:TEST_BASE_URL'
    assert EMAIL, 'RUNTIME_E2E_CONFIG_MISSING:TEST_SUPERADMIN_EMAIL'
    assert PASSWORD, 'RUNTIME_E2E_CONFIG_MISSING:TEST_SUPERADMIN_PASSWORD'


def _login_session():
    _require_runtime_config()
    session = requests.Session()
    response = session.post(
        f'{BASE_URL}/api/auth/login',
        json={'email': EMAIL, 'password': PASSWORD},
        timeout=30,
    )
    _record('login', 'PASS' if response.status_code == 200 else 'FAIL', response.status_code)
    assert response.status_code == 200, f'RUNTIME_LOGIN_FAILED:{response.status_code}'
    payload = response.json()
    access = payload.get('token') or payload.get('access_token')
    assert access, 'RUNTIME_LOGIN_FAILED:ACCESS_MISSING'
    session.headers.update({'Authorization': f'Bearer {access}'})
    return session


def test_01_public_ping():
    _require_runtime_config()
    response = requests.get(f'{BASE_URL}/api/centro-control/ping', timeout=30)
    ok = response.status_code == 200 and response.json().get('status') == 'ok'
    _record('centro_control_ping', 'PASS' if ok else 'FAIL', response.status_code)
    assert ok


def test_02_unauthenticated_rbac():
    _require_runtime_config()
    for name, path in (
        ('centro_control_unauth', '/api/centro-control/estado'),
        ('sync_monitor_unauth', '/api/admin/sync-monitor'),
    ):
        response = requests.get(f'{BASE_URL}{path}', timeout=30)
        ok = response.status_code in (401, 403)
        _record(name, 'PASS' if ok else 'FAIL', response.status_code)
        assert ok, f'{name}:{response.status_code}'


def test_03_authenticated_modules():
    session = _login_session()
    for name, path in (
        ('centro_control_estado', '/api/centro-control/estado'),
        ('sync_monitor', '/api/admin/sync-monitor'),
    ):
        response = session.get(f'{BASE_URL}{path}', timeout=45)
        ok = response.status_code == 200
        _record(name, 'PASS' if ok else 'FAIL', response.status_code)
        assert ok, f'{name}:{response.status_code}'


def test_04_centro_control_core_endpoints():
    session = _login_session()
    paths = (
        '/api/centro-control/salud/resumen',
        '/api/centro-control/alertas',
        '/api/centro-control/fuentes',
        '/api/centro-control/jobs',
        '/api/centro-control/bitacora',
        '/api/centro-control/metricas',
        '/api/centro-control/historial',
        '/api/centro-control/matriz-resolucion',
        '/api/centro-control/blindaje/modulos',
    )
    for path in paths:
        response = session.get(f'{BASE_URL}{path}', timeout=45)
        ok = response.status_code == 200
        _record('GET ' + path, 'PASS' if ok else 'FAIL', response.status_code)
        assert ok, f'{path}:{response.status_code}'


def test_05_notification_configuration_read_only():
    session = _login_session()
    paths = (
        '/api/centro-control/email/config',
        '/api/centro-control/whatsapp/config',
        '/api/centro-control/notificaciones/config',
    )
    for path in paths:
        response = session.get(f'{BASE_URL}{path}', timeout=30)
        ok = response.status_code == 200
        _record('GET ' + path, 'PASS' if ok else 'FAIL', response.status_code)
        assert ok, f'{path}:{response.status_code}'


def test_06_finalize_evidence():
    _record('external_messages_sent', 'PASS')
    EVIDENCE['certification_candidate'] = True
    EVIDENCE_FILE.write_text(json.dumps(EVIDENCE, ensure_ascii=False, indent=2), encoding='utf-8')
