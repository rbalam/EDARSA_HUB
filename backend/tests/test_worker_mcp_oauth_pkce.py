"""Security contracts for side-effect-free Worker MCP OAuth PKCE primitives."""
import base64
import hashlib

import pytest

from modules.worker_mcp.oauth_pkce import (
    OAuthValidationError,
    validate_client_id,
    validate_pkce_challenge,
    validate_redirect_uri,
    validate_scopes,
    verify_pkce,
)


def _challenge(verifier):
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")


def test_rfc7636_pkce_round_trip():
    verifier = "a" * 43
    challenge = _challenge(verifier)
    assert validate_pkce_challenge(challenge, "S256") == challenge
    assert verify_pkce(verifier, challenge)
    assert not verify_pkce("b" * 43, challenge)


@pytest.mark.parametrize("method", ["plain", "", "s256", None])
def test_pkce_requires_s256(method):
    with pytest.raises(OAuthValidationError, match="PKCE_S256_REQUIRED"):
        validate_pkce_challenge(_challenge("a" * 43), method)


@pytest.mark.parametrize("verifier", ["short", "a" * 129, "a" * 42 + "!", ""])
def test_pkce_rejects_invalid_verifier(verifier):
    assert not verify_pkce(verifier, _challenge("a" * 43))


def test_redirect_uri_requires_exact_registration_and_https():
    good = "https://chatgpt.com/connector/oauth/registered-id"
    assert validate_redirect_uri(good, (good,)) == good
    with pytest.raises(OAuthValidationError):
        validate_redirect_uri(good + "/extra", (good,))
    with pytest.raises(OAuthValidationError):
        validate_redirect_uri("http://chatgpt.com/cb", ("http://chatgpt.com/cb",))
    with pytest.raises(OAuthValidationError):
        validate_redirect_uri("https://chatgpt.com/cb#fragment", ("https://chatgpt.com/cb#fragment",))


def test_requested_scopes_cannot_escalate_identity():
    assert validate_scopes("worker:status", frozenset({"worker:status"})) == frozenset({"worker:status"})
    with pytest.raises(OAuthValidationError, match="SCOPES_FORBIDDEN"):
        validate_scopes("worker:submit worker:status", frozenset({"worker:status"}))
    with pytest.raises(OAuthValidationError, match="SCOPES_INVALID"):
        validate_scopes("RBAC_ADMIN", frozenset({"RBAC_ADMIN"}))
    with pytest.raises(OAuthValidationError, match="SCOPES_DUPLICATED"):
        validate_scopes("worker:status worker:status", frozenset({"worker:status"}))


def test_client_id_must_be_registered():
    assert validate_client_id("chatgpt-public-client", frozenset({"chatgpt-public-client"})) == "chatgpt-public-client"
    with pytest.raises(OAuthValidationError, match="CLIENT_NOT_REGISTERED"):
        validate_client_id("made-up-client", frozenset({"chatgpt-public-client"}))
