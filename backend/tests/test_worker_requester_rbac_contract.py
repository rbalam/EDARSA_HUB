from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools/mirror_sync/universal_job_bridge.py'
RBAC = ROOT / 'tools/mirror_sync/worker_requester_rbac.py'


def read(path):
    return path.read_text(encoding='utf-8')


def test_worker_requester_rbac_is_sql_first_and_not_email_hardcoded():
    text = read(RBAC)
    assert 'AuthRepository.get_user_by_email(email)' in text
    assert 'SQL_USUARIO_CATALOGO' in text
    assert 'carlosruz@edarsa.com.mx' not in text
    assert 'SUPERADMIN_ROLE_CODES' in text
    assert 'REQUESTER_INACTIVE' in text


def test_bridge_tracks_requester_and_preserves_legacy_compatibility():
    text = read(BRIDGE)
    assert 'EDARSAHUB_WORKER_REQUIRE_REQUESTER' in text
    assert 'requester_authorization' in text
    assert 'REQUESTER_RBAC_DENIED' in text
    assert 'LEGACY_REQUESTER_NOT_ENFORCED' in text
    assert 'production_allowed' in text


def test_worker_requester_rbac_loads_canonical_backend_environment():
    text = read(RBAC)

    assert 'from dotenv import load_dotenv' in text
    assert 'EDARSAHUB_WORKER_BACKEND_ENV' in text
    assert 'str(BACKEND / ".env")' in text
    assert 'load_dotenv(BACKEND_ENV, override=False)' in text
