from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from worker_mcp.oauth_discovery import (
    authorization_metadata,
    protected_resource_metadata,
    public_authorization_server_metadata,
)
from worker_mcp.oauth_pkce import validate_pkce_challenge, verify_pkce
from worker_mcp.public_origin import PublicOriginError, public_https_origin

ROOT = Path(__file__).resolve().parents[2]
OAUTH = ROOT / "backend/modules/worker_mcp/oauth_server.py"
GATEWAY = ROOT / "backend/modules/worker_mcp/gateway_router.py"


def test_oauth_discovery_supports_code_refresh_and_pkce():
    meta = authorization_metadata("https://mcp.example.test/api/mcp/oauth")
    assert meta["grant_types_supported"] == ["authorization_code", "refresh_token"]
    assert meta["code_challenge_methods_supported"] == ["S256"]
    prm = protected_resource_metadata(
        "https://mcp.example.test/api/mcp",
        "https://mcp.example.test/api/mcp/oauth",
    )
    assert prm["resource"].endswith("/api/mcp")
    assert prm["authorization_servers"] == ["https://mcp.example.test/api/mcp/oauth"]


def test_pkce_s256_round_trip():
    verifier = "A" * 43
    import base64
    import hashlib
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    assert validate_pkce_challenge(challenge, "S256") == challenge
    assert verify_pkce(verifier, challenge) is True


def test_oauth_server_reuses_canonical_identity_rbac_and_sessions():
    text = OAUTH.read_text(encoding="utf-8")
    assert "get_current_user_dual" in text
    assert "RBACSQLService.can_access_permission" in text
    assert 'REQUIRED_PERMISSION = "RBAC_ADMIN"' in text
    assert "dbo.Sesiones" in text
    assert 'ACCESS_SESSION_TYPE = "mcp_service"' in text
    assert 'REFRESH_SESSION_TYPE = "mcp_oauth_refresh"' in text
    assert 'CODE_SESSION_TYPE = "mcp_oauth_code"' in text


def test_oauth_server_has_consent_dcr_token_and_rotation():
    text = OAUTH.read_text(encoding="utf-8")
    assert '@router.get("/authorize"' in text
    assert '@router.post("/authorize")' in text
    assert '@router.post("/register"' in text
    assert '@router.post("/token")' in text
    assert 'grant_type == "authorization_code"' in text
    assert 'grant_type == "refresh_token"' in text
    assert "validate_redirect_uri" in text
    assert "verify_pkce" in text
    assert "_redirect_with_params" in text
    assert 'RedirectResponse(_redirect_with_params(redirect_uri, query), status_code=302)' in text
    assert 'redirect_uri + "?" + urlencode(query)' not in text
    assert "parse_qsl" in text
    assert "_consume_session_token(refresh_token, REFRESH_SESSION_TYPE)" in text


def test_public_metadata_and_router_mount_are_canonical():
    gateway = GATEWAY.read_text(encoding="utf-8")
    assert 'origin + "/api/mcp"' in gateway
    assert 'origin + "/api/mcp/oauth"' in gateway
    assert "from .oauth_server import router as oauth_router" in gateway
    assert "router.include_router(oauth_router)" in gateway
    assert "public_https_origin(request)" in gateway



def test_proxy_forwarded_origin_resolves_external_https_url():
    request = SimpleNamespace(
        headers={
            "x-forwarded-proto": "https",
            "x-forwarded-host": "erp.example.test",
            "host": "internal:8001",
        },
        url=SimpleNamespace(scheme="http"),
    )
    assert public_https_origin(request) == "https://erp.example.test"


def test_public_origin_fails_closed_without_external_https_proof():
    request = SimpleNamespace(
        headers={"host": "127.0.0.1:8001"},
        url=SimpleNamespace(scheme="http"),
    )
    with pytest.raises(PublicOriginError):
        public_https_origin(request)


def test_public_origin_rejects_header_injection():
    request = SimpleNamespace(
        headers={
            "x-forwarded-proto": "https",
            "x-forwarded-host": "good.example.test/evil",
        },
        url=SimpleNamespace(scheme="http"),
    )
    with pytest.raises(PublicOriginError):
        public_https_origin(request)

def test_oauth_change_does_not_reference_production_or_sales_sync():
    text = OAUTH.read_text(encoding="utf-8").lower()
    assert "edarsahub_produccion" not in text
    assert "sync_comercial_abiertas_v2" not in text
    assert "ventas cerradas" not in text


def test_oauth_register_advertises_scopes_without_auto_granting_and_runtime_syncs_mcp():
    oauth_text = OAUTH.read_text(encoding="utf-8")
    recovery_text = (ROOT / "tools/bootstrap/recover_preview_runtime.sh").read_text(
        encoding="utf-8"
    )
    assert '"scope": advertised_scope' in oauth_text
    assert '" ".join(MCP_SCOPES)' in oauth_text
    assert 'validate_scopes(\n        values.get("scope", ""),\n        identity_scopes,\n    )' in oauth_text
    assert 'MCP_SERVICE="edarsahub-worker-mcp"' in recovery_text
    assert 'supervisorctl restart "$MCP_SERVICE"' in recovery_text


def test_canonical_v2_discovery_routes_reuse_single_canonical_metadata_source():
    oauth_text = OAUTH.read_text(encoding="utf-8")
    gateway_text = GATEWAY.read_text(encoding="utf-8")

    assert '@router.api_route("/.well-known/oauth-authorization-server", methods=["GET", "OPTIONS"])' in oauth_text
    assert '@router.api_route("/.well-known/openid-configuration", methods=["GET", "OPTIONS"])' in oauth_text
    assert "payload = public_authorization_server_metadata(issuer)" in oauth_text
    assert oauth_text.count("async def oauth_authorization_metadata(") == 1

    assert '"/.well-known/oauth-authorization-server/api/mcp/oauth"' in gateway_text
    assert '"/.well-known/openid-configuration/api/mcp/oauth"' in gateway_text
    assert "return await oauth_authorization_metadata(request)" in gateway_text


@pytest.mark.asyncio
async def test_mcp_sdk_discovery_succeeds_via_openid_configuration_behind_api_ingress():
    import json
    from httpx2 import Response as Httpx2Response
    from mcp.client.auth.utils import (
        build_oauth_authorization_server_metadata_discovery_urls,
        create_client_registration_request,
        handle_auth_metadata_response,
        validate_metadata_issuer,
    )
    from mcp.shared.auth import OAuthClientMetadata

    origin = "https://erp-crm-enterprise-1.preview.emergentagent.com"
    issuer = origin + "/api/mcp/oauth"
    resource = origin + "/api/mcp"

    candidates = build_oauth_authorization_server_metadata_discovery_urls(issuer, resource)
    assert candidates == [
        origin + "/.well-known/oauth-authorization-server/api/mcp/oauth",
        origin + "/.well-known/openid-configuration/api/mcp/oauth",
        origin + "/api/mcp/oauth/.well-known/openid-configuration",
    ]

    canonical_payload = public_authorization_server_metadata(issuer)

    # Simulate Emergent reverse proxy: non-/api root .well-known paths return SPA HTML / 404,
    # while /api/mcp/oauth/.well-known/openid-configuration reaches FastAPI backend.
    simulated_wire = {
        candidates[0]: Httpx2Response(200, headers={"content-type": "text/html"}, content=b"<!doctype html><html></html>"),
        candidates[1]: Httpx2Response(404, headers={"content-type": "application/json"}, content=b'{"detail":"Not Found"}'),
        candidates[2]: Httpx2Response(
            200,
            headers={"content-type": "application/json", "cache-control": "no-store"},
            content=json.dumps(canonical_payload).encode("utf-8"),
        ),
    }

    discovered = None
    visited: list[str] = []
    for url in candidates:
        visited.append(url)
        should_continue, asm = await handle_auth_metadata_response(simulated_wire[url])
        if asm is not None:
            discovered = asm
            break
        assert should_continue is True

    assert visited == candidates
    assert discovered is not None
    validate_metadata_issuer(discovered, issuer)
    assert str(discovered.registration_endpoint) == issuer + "/register"
    assert discovered.code_challenge_methods_supported == ["S256"]
    assert discovered.scopes_supported == ["worker:status", "worker:submit"]
    assert discovered.token_endpoint_auth_methods_supported == ["none"]

    dcr_req = create_client_registration_request(
        discovered,
        OAuthClientMetadata(
            redirect_uris=["https://chatgpt.com/connector_platform_oauth_redirect"],
            client_name="Canonical V2",
            token_endpoint_auth_method="none",
        ),
        origin,
    )
    assert str(dcr_req.url) == issuer + "/register"
    assert dcr_req.method == "POST"
