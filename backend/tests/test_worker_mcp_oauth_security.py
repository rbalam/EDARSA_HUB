"""Contract tests for the internal OAuth grant policy (no MCP SDK needed)."""
from datetime import datetime, timedelta, timezone

import pytest

from modules.worker_mcp.oauth_pkce import OAuthValidationError
from modules.worker_mcp.oauth_security import require_tool_scope, validate_grant

RESOURCE = "https://erp-crm-enterprise-1.preview.emergentagent.com/api/mcp"


def grant(**changes):
    args = dict(
        requested_scopes="worker:status",
        identity_scopes=frozenset({"worker:status"}),
        consented_scopes=frozenset({"worker:status"}),
        resource=RESOURCE,
        registered_resource=RESOURCE,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        revoked=False,
    )
    args.update(changes)
    return validate_grant(**args)


def test_valid_status_grant():
    assert grant() == frozenset({"worker:status"})


@pytest.mark.parametrize("changes", [
    {"revoked": True},
    {"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)},
    {"expires_at": datetime.now() + timedelta(minutes=5)},
    {"consented_scopes": frozenset()},
    {"requested_scopes": "worker:submit"},
    {"resource": "https://example.org/api/mcp"},
    {"resource": "http://example.org/api/mcp", "registered_resource": "http://example.org/api/mcp"},
    {"resource": RESOURCE + "?x=1", "registered_resource": RESOURCE + "?x=1"},
    {"resource": RESOURCE + "/", "registered_resource": RESOURCE + "/"},
])
def test_invalid_grants(changes):
    with pytest.raises(OAuthValidationError):
        grant(**changes)


def test_status_scope_does_not_authorize_submit():
    require_tool_scope("worker:status", frozenset({"worker:status"}))
    with pytest.raises(OAuthValidationError):
        require_tool_scope("worker:submit", frozenset({"worker:status"}))


def test_submit_scope_does_not_authorize_status():
    require_tool_scope("worker:submit", frozenset({"worker:submit"}))
    with pytest.raises(OAuthValidationError):
        require_tool_scope("worker:status", frozenset({"worker:submit"}))


def test_unknown_scope_denied():
    with pytest.raises(OAuthValidationError):
        require_tool_scope("admin:*", frozenset({"admin:*"}))


def test_missing_scope_set_denied():
    with pytest.raises(OAuthValidationError):
        require_tool_scope("worker:status", None)

def test_both_scopes_require_explicit_identity_and_consent():
    both = frozenset({"worker:status", "worker:submit"})
    assert grant(requested_scopes="worker:status worker:submit",
                 identity_scopes=both, consented_scopes=both) == both


def test_submit_without_consent_denied():
    with pytest.raises(OAuthValidationError, match="CONSENT_REQUIRED"):
        grant(requested_scopes="worker:submit",
              identity_scopes=frozenset({"worker:submit"}))


def test_identity_scope_escalation_denied():
    with pytest.raises(OAuthValidationError, match="SCOPES_FORBIDDEN"):
        grant(requested_scopes="worker:submit",
              consented_scopes=frozenset({"worker:submit"}))


def test_non_frozenset_consent_denied():
    with pytest.raises(OAuthValidationError, match="CONSENT_REQUIRED"):
        grant(consented_scopes={"worker:status"})


def test_unknown_tool_scope_denied_even_when_granted():
    with pytest.raises(OAuthValidationError, match="TOOL_SCOPE_NOT_CONFIGURED"):
        require_tool_scope("worker:admin", frozenset({"worker:admin"}))
