"""Gate 3I isolated security suite: OAuth 2.1 + MCP + Worker Ingress scope least-privilege.

Validates positive and negative authorization paths, fail-closed rejections,
PKCE S256, dbo.Sesiones revocation/expiration, Emergent HTTPS/loopback resource
compatibility, direct ingress bypass protection, idempotency, and concurrency
without SQL or network connections.
"""
from __future__ import annotations

import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
from pathlib import Path
import sys
import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

if importlib.util.find_spec("mcp") is None:
    for _candidate in sorted(
        Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")
    ):
        sys.path.append(str(_candidate))

from mcp.server.auth.provider import AccessToken

from modules.worker_ingress import routes as ingress_routes
from modules.worker_ingress import service_credential as svc
from modules.worker_mcp import auth as mcp_auth
from modules.worker_mcp import client as mcp_client
from modules.worker_mcp import oauth_server
from modules.worker_mcp import server as mcp_server
from modules.worker_mcp.config import WorkerMcpConfig
from modules.worker_mcp.oauth_pkce import OAuthValidationError
from modules.worker_mcp.oauth_security import SUPPORTED_SCOPES

EMERGENT_ORIGIN = "https://erp-crm-enterprise-1.preview.emergentagent.com"
EMERGENT_RESOURCE = EMERGENT_ORIGIN + "/api/mcp"
REDIRECT_URI = "https://chatgpt.com/connector_platform_oauth_redirect"
SUPERADMIN_UUID = "11111111-1111-1111-1111-111111111111"
ADMIN_UUID = "22222222-2222-2222-2222-222222222222"


def _pkce_pair(seed: str = "gate3i-pkce-verifier-012345678901234567890123456789") -> tuple[str, str]:
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(seed.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    return seed, challenge


def _superadmin_user() -> dict[str, Any]:
    return {
        "id": SUPERADMIN_UUID,
        "public_uuid": SUPERADMIN_UUID,
        "PublicUUID": SUPERADMIN_UUID,
        "UsuarioID": 8,
        "_sql_usuario_id": 8,
        "usuario_id": 8,
        "email": "superadmin@edarsa.test",
        "role": "SuperAdministrador",
        "role_code": "SUPERADMIN",
        "_sql_rol_codigo": "SUPERADMIN",
        "active": True,
    }


def _rbac_admin_non_superadmin_user() -> dict[str, Any]:
    return {
        "id": ADMIN_UUID,
        "public_uuid": ADMIN_UUID,
        "PublicUUID": ADMIN_UUID,
        "UsuarioID": 19,
        "_sql_usuario_id": 19,
        "usuario_id": 19,
        "email": "rbacadmin@edarsa.test",
        "role": "Administrador",
        "role_code": "ADMIN",
        "_sql_rol_codigo": "ADMIN",
        "active": True,
    }


class _InMemorySesionesStore:
    """In-memory fake matching dbo.Sesiones semantics for offline OAuth/exchange tests."""

    def __init__(self, users_by_id: dict[str, dict[str, Any]]):
        self.rows: dict[str, dict[str, Any]] = {}
        self.users_by_id = users_by_id

    def insert(
        self,
        *,
        user_id: int,
        token: str,
        session_type: str,
        ttl_seconds: int,
        family_id: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, str]:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        user = self.users_by_id[str(user_id)]
        session_id = f"ses-{len(self.rows) + 1}"
        family = family_id or f"fam-{len(self.rows) + 1}"
        # oauth_server inserts integer UsuarioID on code/refresh; service_credential resolves user by UsuarioID
        self.rows[digest] = {
            "SesionID": session_id,
            "UsuarioID": user["id"] if session_type == "mcp_service" else int(user_id),
            "SqlUsuarioID": int(user_id),
            "TipoUsuario": session_type,
            "FamiliaTokenID": family,
            "FechaExpiracion": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
            "EstaActiva": 1,
            "FechaRevocacion": None,
        }
        return {"session_id": session_id, "family_id": family}

    def consume(self, token: str, expected_type: str) -> dict[str, Any]:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        row = self.rows.get(digest)
        now = datetime.now(timezone.utc)
        if (
            not row
            or row["TipoUsuario"].strip().lower() != expected_type
            or row["EstaActiva"] != 1
            or row["FechaRevocacion"] is not None
            or row["FechaExpiracion"] <= now
        ):
            raise oauth_server.OAuthServerError("invalid_grant")
        row["EstaActiva"] = 0
        row["FechaRevocacion"] = now
        return {
            "SesionID": row["SesionID"],
            "UsuarioID": row["SqlUsuarioID"],
            "TipoUsuario": row["TipoUsuario"],
            "FamiliaTokenID": row["FamiliaTokenID"],
        }

    def resolve_active_mcp_service(self, credential: str) -> dict[str, Any]:
        value = str(credential or "").strip()
        if not value:
            raise svc.WorkerServiceCredentialError("SERVICE_CREDENTIAL_REQUIRED")
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        row = self.rows.get(digest)
        now = datetime.now(timezone.utc)
        if (
            not row
            or row["TipoUsuario"].strip().lower() != "mcp_service"
            or row["EstaActiva"] != 1
            or row["FechaRevocacion"] is not None
            or row["FechaExpiracion"] <= now
        ):
            raise svc.WorkerServiceCredentialError("SERVICE_CREDENTIAL_INVALID")
        return {
            "SesionID": row["SesionID"],
            "UsuarioID": row["UsuarioID"],
            "TipoUsuario": row["TipoUsuario"],
            "FechaExpiracion": row["FechaExpiracion"],
            "EstaActiva": row["EstaActiva"],
        }

    def revoke(self, token: str) -> None:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self.rows[digest]["EstaActiva"] = 0
        self.rows[digest]["FechaRevocacion"] = datetime.now(timezone.utc)


@pytest.fixture
def isolated_oauth_and_ingress(monkeypatch):
    superadmin = _superadmin_user()
    admin_only = _rbac_admin_non_superadmin_user()
    users = {
        "8": superadmin,
        SUPERADMIN_UUID: superadmin,
        "19": admin_only,
        ADMIN_UUID: admin_only,
    }
    store = _InMemorySesionesStore(users)
    active_user_holder = {"user": superadmin}

    async def fake_current_user_dual(_request):
        return dict(active_user_holder["user"])

    monkeypatch.setattr(oauth_server, "get_current_user_dual", fake_current_user_dual)
    monkeypatch.setattr(oauth_server, "_insert_session_token", store.insert)
    monkeypatch.setattr(oauth_server, "_consume_session_token", store.consume)
    monkeypatch.setattr(
        oauth_server.AuthRepository,
        "get_user_by_id",
        lambda uid: dict(users[str(uid)]) if str(uid) in users else None,
    )
    monkeypatch.setattr(
        oauth_server.RBACSQLService,
        "can_access_permission",
        lambda uid, perm: perm == "RBAC_ADMIN" and str(uid) in {"8", "19"},
    )
    monkeypatch.setattr(
        svc,
        "_resolve_active_service_session",
        store.resolve_active_mcp_service,
    )
    monkeypatch.setattr(
        svc.AuthRepository,
        "get_user_by_id",
        lambda uid: dict(users[str(uid)]) if str(uid) in users else None,
    )
    monkeypatch.setattr(
        svc.RBACSQLService,
        "can_access_permission",
        lambda uid, perm: perm == "RBAC_ADMIN" and str(uid) in {"8", "19"},
    )

    submitted_objectives: list[dict[str, Any]] = []
    submitted_jobs: list[dict[str, Any]] = []

    def fake_submit_objective(payload, *, current_user):
        submitted_objectives.append({"payload": payload, "user": current_user})
        return {
            "status": "SUBMITTED",
            "job_id": "SEM-GATE3I-001",
            "capability": payload.get("capability"),
            "bounded_context": payload.get("bounded_context"),
            "production_touched": False,
        }

    def fake_submit_job(payload, *, current_user):
        submitted_jobs.append({"payload": payload, "user": current_user})
        return {
            "status": "SUBMITTED",
            "job_id": payload.get("job_id", "JOB-GATE3I-001"),
            "production_touched": False,
        }

    def fake_get_job_status(job_id: str):
        if job_id == "MCP-AUTH-PROBE":
            return {
                "job_id": "MCP-AUTH-PROBE",
                "lifecycle": "NOT_FOUND",
                "status": "NOT_FOUND",
                "production_touched": False,
            }
        return {
            "job_id": job_id,
            "lifecycle": "RESULT",
            "status": "READ_ONLY_COMPLETE",
            "certification": "CERTIFIED_READ_ONLY",
            "quality_gate": "PASS",
            "tests": "PASS",
            "percent_complete": 100,
            "production_touched": False,
        }

    monkeypatch.setattr(ingress_routes, "submit_objective", fake_submit_objective)
    monkeypatch.setattr(ingress_routes, "submit_job", fake_submit_job)
    monkeypatch.setattr(ingress_routes, "get_job_status", fake_get_job_status)

    app = FastAPI()
    app.include_router(oauth_server.router)
    app.include_router(ingress_routes.router, prefix="/api")

    def fake_worker_admin_dep(
        authorization: str | None = ingress_routes.Header(default=None, alias="Authorization"),
    ) -> dict[str, Any]:
        token = ingress_routes._bearer_credential(authorization)
        payload = oauth_server.verify_token(token)
        return {
            "id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }

    app.dependency_overrides[ingress_routes.WORKER_ADMIN_DEPENDENCY] = fake_worker_admin_dep
    client = TestClient(app)

    headers = {
        "x-forwarded-proto": "https",
        "x-forwarded-host": "erp-crm-enterprise-1.preview.emergentagent.com",
    }

    def issue_oauth_tokens(requested_scope: str) -> dict[str, Any]:
        reg = client.post(
            "/api/mcp/oauth/register",
            json={"redirect_uris": [REDIRECT_URI], "client_name": "ChatGPT Gate 3I"},
            headers=headers,
        )
        assert reg.status_code == 201
        client_id = reg.json()["client_id"]
        verifier, challenge = _pkce_pair()

        auth_res = client.post(
            "/api/mcp/oauth/authorize",
            data={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": requested_scope,
                "state": "st-gate3i",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "resource": EMERGENT_RESOURCE,
                "decision": "approve",
            },
            headers=headers,
            follow_redirects=False,
        )
        if auth_res.status_code != 302:
            return {"authorize_status": auth_res.status_code, "authorize_json": auth_res.json()}

        loc = auth_res.headers["location"]
        code = parse_qs(urlsplit(loc).query)["code"][0]
        tok_res = client.post(
            "/api/mcp/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "code": code,
                "code_verifier": verifier,
                "redirect_uri": REDIRECT_URI,
                "resource": EMERGENT_RESOURCE,
            },
            headers=headers,
        )
        assert tok_res.status_code == 200
        data = tok_res.json()
        data["client_id"] = client_id
        return data

    # Bridge mcp_client._request_json directly into FastAPI TestClient (zero sockets!)
    def in_memory_request_json(*, method: str, url: str, token: str, payload=None, timeout: float = 15.0):
        path = urlsplit(url).path
        req_headers = {"Authorization": f"Bearer {token}", **headers}
        resp = client.request(method, path, json=payload, headers=req_headers)
        return resp.status_code, (resp.json() if resp.content else {})

    monkeypatch.setattr(mcp_client, "_request_json", in_memory_request_json)

    return {
        "client": client,
        "headers": headers,
        "store": store,
        "users": users,
        "active_user_holder": active_user_holder,
        "issue_oauth_tokens": issue_oauth_tokens,
        "submitted_objectives": submitted_objectives,
        "submitted_jobs": submitted_jobs,
    }


@pytest.mark.asyncio
async def test_status_only_oauth_token_allows_get_job_status_and_blocks_submit_objective(
    isolated_oauth_and_ingress,
    monkeypatch,
):
    tokens = isolated_oauth_and_ingress["issue_oauth_tokens"]("worker:status")
    assert tokens["scope"] == "worker:status"
    access_token_str = tokens["access_token"]

    # Emergent compatibility: loopback MCP server uses http://127.0.0.1:32913/mcp while OAuth uses HTTPS public resource
    verifier = mcp_auth.EdarsahubTokenVerifier(
        backend_url="http://127.0.0.1:8001",
        resource_url="http://127.0.0.1:32913/mcp",
    )
    verified = await verifier.verify_token(access_token_str)
    assert verified is not None
    assert verified.scopes == ["worker:status"]

    cfg = WorkerMcpConfig(
        issuer_url=EMERGENT_ORIGIN + "/api/mcp/oauth",
        resource_url="http://127.0.0.1:32913/mcp",
        backend_url="http://127.0.0.1:8001",
        allowed_hosts=("127.0.0.1:32913",),
        allowed_origins=(),
    )
    mcp_server.build_mcp_server(cfg)
    monkeypatch.setattr(mcp_server, "get_access_token", lambda: verified)

    # Positive: worker:status permits get_job_status
    status_res = mcp_server.get_job_status_tool("SEM-GATE3I-001")
    assert status_res["status"] == "READ_ONLY_COMPLETE"
    assert status_res["production_touched"] is False

    # Negative (Layer 1 - MCP Server): worker:status NEVER permits submit_objective
    with pytest.raises(PermissionError, match="MCP_SCOPE_FORBIDDEN:INSUFFICIENT_SCOPE"):
        mcp_server.submit_objective_tool(
            objective="Unauthorized objective",
            bounded_context="WORKER_INGRESS",
            mode="READ_ONLY",
            capability="READ_ONLY_CANARY",
        )
    assert isolated_oauth_and_ingress["submitted_objectives"] == []

    # Negative (Layer 2 - Direct Worker Ingress Bypass): exchanging token directly still blocks POST /objectives and POST /jobs
    http = isolated_oauth_and_ingress["client"]
    exch = http.post(
        "/api/internal/worker/auth/exchange",
        headers={"Authorization": f"Bearer {access_token_str}"},
    )
    assert exch.status_code == 200
    exch_body = exch.json()
    assert exch_body["scope"] == "worker:status"
    assert exch_body["scopes"] == ["worker:status"]
    assert exch_body["resource"] == EMERGENT_RESOURCE
    internal_jwt = exch_body["access_token"]

    bypass_obj = http.post(
        "/api/internal/worker/objectives",
        json={
            "objective": "Bypass attempt",
            "bounded_context": "WORKER_INGRESS",
            "mode": "READ_ONLY",
            "capability": "READ_ONLY_CANARY",
        },
        headers={"Authorization": f"Bearer {internal_jwt}"},
    )
    assert bypass_obj.status_code == 403
    assert bypass_obj.json()["detail"]["error"] == "INSUFFICIENT_SCOPE"
    assert bypass_obj.json()["detail"]["required_scope"] == "worker:submit"
    assert isolated_oauth_and_ingress["submitted_objectives"] == []


@pytest.mark.asyncio
async def test_submit_only_oauth_token_allows_submit_and_blocks_get_job_status(
    isolated_oauth_and_ingress,
    monkeypatch,
):
    tokens = isolated_oauth_and_ingress["issue_oauth_tokens"]("worker:submit")
    assert tokens["scope"] == "worker:submit"
    access_token_str = tokens["access_token"]

    verifier = mcp_auth.EdarsahubTokenVerifier(
        backend_url="http://127.0.0.1:8001",
        resource_url="http://127.0.0.1:32913/mcp",
    )
    verified = await verifier.verify_token(access_token_str)
    assert verified is not None
    assert verified.scopes == ["worker:submit"]

    cfg = WorkerMcpConfig(
        issuer_url=EMERGENT_ORIGIN + "/api/mcp/oauth",
        resource_url="http://127.0.0.1:32913/mcp",
        backend_url="http://127.0.0.1:8001",
        allowed_hosts=("127.0.0.1:32913",),
        allowed_origins=(),
    )
    mcp_server.build_mcp_server(cfg)
    monkeypatch.setattr(mcp_server, "get_access_token", lambda: verified)

    # Positive: worker:submit permits submit_objective
    submit_res = mcp_server.submit_objective_tool(
        objective="Authorized canary",
        bounded_context="WORKER_INGRESS",
        mode="READ_ONLY",
        capability="READ_ONLY_CANARY",
    )
    assert submit_res["status"] == "SUBMITTED"
    assert len(isolated_oauth_and_ingress["submitted_objectives"]) == 1

    # Negative (Layer 1 - MCP Server): worker:submit NEVER permits get_job_status
    with pytest.raises(PermissionError, match="MCP_SCOPE_FORBIDDEN:INSUFFICIENT_SCOPE"):
        mcp_server.get_job_status_tool("SEM-GATE3I-001")

    # Negative (Layer 2 - Direct Worker Ingress Bypass): real job status read returns 403 INSUFFICIENT_SCOPE, while MCP-AUTH-PROBE returns 404
    http = isolated_oauth_and_ingress["client"]
    internal_jwt = http.post(
        "/api/internal/worker/auth/exchange",
        headers={"Authorization": f"Bearer {access_token_str}"},
    ).json()["access_token"]

    probe = http.get(
        "/api/internal/worker/jobs/MCP-AUTH-PROBE",
        headers={"Authorization": f"Bearer {internal_jwt}"},
    )
    assert probe.status_code == 404

    real_status = http.get(
        "/api/internal/worker/jobs/SEM-GATE3I-001",
        headers={"Authorization": f"Bearer {internal_jwt}"},
    )
    assert real_status.status_code == 403
    assert real_status.json()["detail"]["required_scope"] == "worker:status"


def test_non_superadmin_rbac_admin_cannot_consent_or_escalate_to_submit(
    isolated_oauth_and_ingress,
):
    isolated_oauth_and_ingress["active_user_holder"]["user"] = (
        isolated_oauth_and_ingress["users"][ADMIN_UUID]
    )

    # Requesting worker:submit as non-SUPERADMIN RBAC_ADMIN fails closed with SCOPES_FORBIDDEN
    denied = isolated_oauth_and_ingress["issue_oauth_tokens"]("worker:status worker:submit")
    assert denied["authorize_status"] == 400
    assert denied["authorize_json"]["error"] == "SCOPES_FORBIDDEN"

    # Requesting worker:status succeeds for active RBAC_ADMIN
    allowed = isolated_oauth_and_ingress["issue_oauth_tokens"]("worker:status")
    assert allowed["scope"] == "worker:status"


def test_refresh_token_allows_downscoping_and_blocks_upscoping(
    isolated_oauth_and_ingress,
):
    http = isolated_oauth_and_ingress["client"]
    headers = isolated_oauth_and_ingress["headers"]

    # 1. Start with both scopes consented -> downscope on refresh to worker:status
    both = isolated_oauth_and_ingress["issue_oauth_tokens"]("worker:status worker:submit")
    assert both["scope"] == "worker:status worker:submit"

    narrowed = http.post(
        "/api/mcp/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": both["client_id"],
            "refresh_token": both["refresh_token"],
            "scope": "worker:status",
        },
        headers=headers,
    )
    assert narrowed.status_code == 200
    narrowed_body = narrowed.json()
    assert narrowed_body["scope"] == "worker:status"

    # 2. Attempting to upscope back to worker:submit from narrowed refresh token fails closed!
    upscope = http.post(
        "/api/mcp/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": both["client_id"],
            "refresh_token": narrowed_body["refresh_token"],
            "scope": "worker:status worker:submit",
        },
        headers=headers,
    )
    assert upscope.status_code == 400
    assert upscope.json()["error"] == "invalid_grant"


@pytest.mark.asyncio
async def test_sql_session_revocation_tampering_and_expiration_fail_closed(
    isolated_oauth_and_ingress,
    monkeypatch,
):
    tokens = isolated_oauth_and_ingress["issue_oauth_tokens"]("worker:status")
    access_token_str = tokens["access_token"]
    verifier = mcp_auth.EdarsahubTokenVerifier(
        backend_url="http://127.0.0.1:8001",
        resource_url="http://127.0.0.1:32913/mcp",
    )

    # Tampered JWT payload/signature fails closed
    parts = access_token_str.split(".")
    tampered = parts[0] + "." + parts[1] + ".tamperedsig"
    assert await verifier.verify_token(tampered) is None

    # Revoking session in dbo.Sesiones immediately invalidates token
    isolated_oauth_and_ingress["store"].revoke(access_token_str)
    assert await verifier.verify_token(access_token_str) is None

    # Expired AccessToken in MCP server fails closed even if context still holds it
    expired_token = AccessToken(
        token="expired-test-token",
        client_id="edarsahub-authenticated-user",
        scopes=["worker:status", "worker:submit"],
        expires_at=int(time.time()) - 5,
        resource="http://127.0.0.1:32913/mcp",
    )
    monkeypatch.setattr(mcp_server, "_BACKEND_URL", "http://127.0.0.1:8001")
    monkeypatch.setattr(mcp_server, "get_access_token", lambda: expired_token)
    with pytest.raises(PermissionError, match="MCP_TOKEN_EXPIRED"):
        mcp_server.get_job_status_tool("SEM-1")


@pytest.mark.asyncio
async def test_legacy_opaque_superadmin_and_admin_sessions_preserve_emergent_compatibility(
    isolated_oauth_and_ingress,
):
    store = isolated_oauth_and_ingress["store"]
    store.insert(
        user_id=8,
        token="legacy-opaque-superadmin-session",
        session_type="mcp_service",
        ttl_seconds=900,
    )
    store.insert(
        user_id=19,
        token="legacy-opaque-admin-session",
        session_type="mcp_service",
        ttl_seconds=900,
    )
    verifier = mcp_auth.EdarsahubTokenVerifier(
        backend_url="http://127.0.0.1:8001",
        resource_url="http://127.0.0.1:32913/mcp",
    )

    sup_verified = await verifier.verify_token("legacy-opaque-superadmin-session")
    assert sup_verified is not None
    assert set(sup_verified.scopes) == SUPPORTED_SCOPES

    adm_verified = await verifier.verify_token("legacy-opaque-admin-session")
    assert adm_verified is not None
    assert adm_verified.scopes == ["worker:status"]


@pytest.mark.asyncio
async def test_idempotency_and_concurrent_scope_verification(
    isolated_oauth_and_ingress,
):
    status_tok = isolated_oauth_and_ingress["issue_oauth_tokens"]("worker:status")["access_token"]
    both_tok = isolated_oauth_and_ingress["issue_oauth_tokens"]("worker:status worker:submit")["access_token"]

    # Thread-safe idempotent credential exchange
    def exchange_pair(idx: int) -> tuple[str, str]:
        r1 = svc.exchange_service_credential(status_tok)
        r2 = svc.exchange_service_credential(both_tok)
        return r1["scope"], r2["scope"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        pairs = list(pool.map(exchange_pair, range(16)))
    assert all(p == ("worker:status", "worker:status worker:submit") for p in pairs)

    # Concurrent async MCP token verifications preserve strict scope isolation without cross-talk
    verifier = mcp_auth.EdarsahubTokenVerifier(
        backend_url="http://127.0.0.1:8001",
        resource_url="http://127.0.0.1:32913/mcp",
    )
    results = await asyncio.gather(
        *[
            verifier.verify_token(status_tok if i % 2 == 0 else both_tok)
            for i in range(12)
        ]
    )
    for idx, tok in enumerate(results):
        assert tok is not None
        if idx % 2 == 0:
            assert tok.scopes == ["worker:status"]
        else:
            assert tok.scopes == ["worker:submit", "worker:status"]


def test_mint_scoped_internal_token_rejects_empty_or_unknown_scopes():
    with pytest.raises(OAuthValidationError, match="SCOPES_FORBIDDEN"):
        oauth_server.mint_scoped_internal_access_token(
            user_id=SUPERADMIN_UUID,
            email="superadmin@edarsa.test",
            role="SuperAdministrador",
            scopes=frozenset(),
        )
    with pytest.raises(OAuthValidationError, match="SCOPES_FORBIDDEN"):
        oauth_server.mint_scoped_internal_access_token(
            user_id=SUPERADMIN_UUID,
            email="superadmin@edarsa.test",
            role="SuperAdministrador",
            scopes=frozenset({"worker:admin"}),
        )
