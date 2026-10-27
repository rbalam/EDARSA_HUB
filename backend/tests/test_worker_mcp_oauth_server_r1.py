from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OAUTH = ROOT / "backend/modules/worker_mcp/oauth_server.py"
GATEWAY = ROOT / "backend/modules/worker_mcp/gateway_router.py"
SERVER = ROOT / "backend/server.py"
DISCOVERY = ROOT / "backend/modules/worker_mcp/oauth_discovery.py"


def test_oauth_server_reuses_canonical_auth_rbac_and_sessions():
    text = OAUTH.read_text(encoding="utf-8")
    assert "get_current_user_dual" in text
    assert "RBACSQLService.can_access_permission" in text
    assert 'REQUIRED_PERMISSION = "RBAC_ADMIN"' in text
    assert "dbo.Sesiones" in text
    assert 'ACCESS_SESSION_TYPE = "mcp_service"' in text
    assert 'REFRESH_SESSION_TYPE = "mcp_oauth_refresh"' in text
    assert 'CODE_SESSION_TYPE = "mcp_oauth_code"' in text


def test_oauth_server_requires_pkce_s256_and_exact_redirects():
    text = OAUTH.read_text(encoding="utf-8")
    assert "validate_pkce_challenge" in text
    assert "verify_pkce" in text
    assert "validate_redirect_uri" in text
    assert '"code_challenge_method"' in text
    assert '"redirect_uri"' in text


def test_oauth_server_has_consent_register_token_and_refresh_rotation():
    text = OAUTH.read_text(encoding="utf-8")
    assert '@router.get("/authorize"' in text
    assert '@router.post("/authorize")' in text
    assert '@router.post("/register"' in text
    assert '@router.post("/token")' in text
    assert 'grant_type == "authorization_code"' in text
    assert 'grant_type == "refresh_token"' in text
    assert "_consume_session_token(refresh_token, REFRESH_SESSION_TYPE)" in text
    assert "_issue_refresh_token(" in text


def test_oauth_metadata_is_public_and_bound_to_mcp_resource():
    gateway = GATEWAY.read_text(encoding="utf-8")
    discovery = DISCOVERY.read_text(encoding="utf-8")
    assert 'origin + "/api/mcp"' in gateway
    assert 'origin + "/api/mcp/oauth"' in gateway
    assert '"/api/mcp/.well-known/oauth-protected-resource"' in gateway
    assert '"refresh_token"' in discovery


def test_oauth_router_is_mounted_once_and_production_not_referenced():
    server = SERVER.read_text(encoding="utf-8")
    oauth = OAUTH.read_text(encoding="utf-8").lower()
    assert server.count("worker_mcp_oauth_router") == 2
    assert "edarsahub_produccion" not in oauth
    assert "sync_comercial_abiertas_v2" not in oauth
    assert "ventas cerradas" not in oauth
