"""Discovery metadata for isolated Worker MCP OAuth, no live server activated."""
import pytest

from modules.worker_mcp.oauth_discovery import (
    DiscoveryConfigurationError,
    authorization_metadata,
    protected_resource_metadata,
    public_authorization_server_metadata,
    validate_public_mcp_origin,
)


def test_authorization_discovery_advertises_code_and_s256_only():
    result = authorization_metadata("https://auth.example.test")
    assert result["issuer"] == "https://auth.example.test"
    assert result["authorization_endpoint"] == "https://auth.example.test/authorize"
    assert result["token_endpoint"] == "https://auth.example.test/token"
    assert result["code_challenge_methods_supported"] == ["S256"]
    assert result["grant_types_supported"] == ["authorization_code", "refresh_token"]
    assert result["token_endpoint_auth_methods_supported"] == ["none"]


def test_protected_resource_metadata_uses_exact_resource():
    result = protected_resource_metadata(
        "https://mcp.example.test/api/mcp", "https://auth.example.test"
    )
    assert result["resource"] == "https://mcp.example.test/api/mcp"
    assert result["authorization_servers"] == ["https://auth.example.test"]
    assert result["bearer_methods_supported"] == ["header"]


@pytest.mark.parametrize("value", [
    "http://auth.example.test", "https://user:pass@auth.example.test",
    "https://auth.example.test/", "https://auth.example.test?x=1",
    "https://auth.example.test#frag", "",
])
def test_rejects_invalid_https_urls(value):
    with pytest.raises(DiscoveryConfigurationError):
        authorization_metadata(value)


def test_public_origin_must_match_resource_origin():
    validate_public_mcp_origin(
        "https://mcp.example.test/api/mcp", "https://mcp.example.test"
    )
    with pytest.raises(DiscoveryConfigurationError):
        validate_public_mcp_origin(
            "https://mcp.example.test/api/mcp", "https://other.example.test"
        )
    with pytest.raises(DiscoveryConfigurationError):
        validate_public_mcp_origin(
            "https://mcp.example.test/api/mcp", "https://mcp.example.test/path"
        )


def test_public_authorization_server_metadata_reuses_canonical_contract_with_dcr():
    issuer = "https://mcp.example.test/api/mcp/oauth"
    base = authorization_metadata(issuer)
    published = public_authorization_server_metadata(issuer)

    assert "registration_endpoint" not in base
    assert published == {
        **base,
        "registration_endpoint": "https://mcp.example.test/api/mcp/oauth/register",
    }
    assert published["code_challenge_methods_supported"] == ["S256"]
    assert published["scopes_supported"] == ["worker:status", "worker:submit"]
    assert published["token_endpoint_auth_methods_supported"] == ["none"]

    with pytest.raises(DiscoveryConfigurationError):
        public_authorization_server_metadata("http://mcp.example.test/api/mcp/oauth")
