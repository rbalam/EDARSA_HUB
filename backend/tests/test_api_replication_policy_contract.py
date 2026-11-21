from datetime import datetime, timezone
from pathlib import Path

from modules.comercial.adapters import _replication_cutoff_reached


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = ROOT / "backend" / "modules" / "api_connections" / "repository.py"
ROUTES = ROOT / "backend" / "modules" / "api_connections" / "routes.py"
ADAPTERS = ROOT / "backend" / "modules" / "comercial" / "adapters.py"
SERVIDORES = ROOT / "frontend" / "src" / "pages" / "Servidores.js"


def test_replication_policy_uses_config_not_port_alias():
    repo = REPOSITORY.read_text(encoding="utf-8")
    assert "replication_policy" in repo
    assert "get_api_replication_policy" in repo
    assert "update_api_replication_policy" in repo
    assert '"cutoff_time"' in repo
    assert '"timezone"' in repo

    assert "'hora_replica': row.get('port', 4)" not in repo
    assert '"hora_replica": row.get("port", 4)' not in repo


def test_replication_policy_routes_are_admin_guarded():
    routes = ROUTES.read_text(encoding="utf-8")
    assert '@router.get("/{api_id}/replication-policy")' in routes
    assert '@router.put("/{api_id}/replication-policy")' in routes
    assert 'require_explicit_permission("RBAC_ADMIN")' in routes


def test_comercial_uses_iana_timezone_and_no_fixed_utc_minus_six_cutoff():
    text = ADAPTERS.read_text(encoding="utf-8")
    assert "get_api_replication_policy" in text
    assert "_replication_cutoff_reached" in text
    assert "ZoneInfo" in text
    assert "timezone(timedelta(hours=-6))" not in text
    assert '"hora_replica": 4' not in text
    assert 'api_config.get("hora_replica", 4)' not in text


def test_cutoff_is_timezone_aware_and_supports_minutes():
    policy = {
        "enabled": True,
        "cutoff_time": "04:15",
        "timezone": "America/Mexico_City",
    }

    before = datetime(2026, 10, 21, 10, 14, tzinfo=timezone.utc)
    after = datetime(2026, 10, 21, 10, 16, tzinfo=timezone.utc)

    assert _replication_cutoff_reached(policy, before) is False
    assert _replication_cutoff_reached(policy, after) is True


def test_disabled_replication_policy_never_cuts_off_local_api():
    policy = {
        "enabled": False,
        "cutoff_time": "04:00",
        "timezone": "America/Mexico_City",
    }
    now = datetime(2026, 10, 21, 18, 0, tzinfo=timezone.utc)
    assert _replication_cutoff_reached(policy, now) is False


def test_modal_exposes_replication_policy_without_legacy_hour_alias():
    text = SERVIDORES.read_text(encoding="utf-8")
    assert "Política de réplica" in text
    assert "cutoff_time" in text
    assert "timezone" in text
    assert "/replication-policy" in text
    assert "hora_replica" not in text
