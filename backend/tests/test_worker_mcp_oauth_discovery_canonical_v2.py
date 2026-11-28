"""Gate OAuth Discovery Canonical V2 — Discovery, Authorization, Regression & MCP Compatibility Suite.

Validates:
- Single canonical metadata contract across:
  1. /api/mcp/oauth/.well-known/openid-configuration (OIDC Discovery 1.0 §4.1 path-appending)
  2. /api/mcp/oauth/.well-known/oauth-authorization-server (legacy EDARSAHUB path)
  3. /.well-known/oauth-authorization-server/api/mcp/oauth (RFC 8414 §3.1 path-insertion)
  4. /.well-known/openid-configuration/api/mcp/oauth (RFC 8414 §5 path-insertion)
- Preflight OPTIONS -> 204 and Cache-Control: no-store on all discovery routes.
- Fail-closed HTTP 503 temporarily_unavailable when external HTTPS proof is absent or injected.
- End-to-end MCP SDK discovery -> Dynamic Client Registration (POST /api/mcp/oauth/register)
  without automatic grant of worker:submit -> PKCE S256 /authorize & /token -> dbo.Sesiones ->
  MCP HTTP boundary enforcement (get_job_status 200 with worker:status; submit_objective 403
  insufficient_scope with worker:status; submit_objective 200 only after SUPERADMIN consent
  to worker:status worker:submit; 400 SCOPES_FORBIDDEN for non-SUPERADMIN).
"""
from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx
import pytest

if importlib.util.find_spec("mcp") is None:
    for _candidate in sorted(
        Path("/app/.runtime/worker_mcp/venv/lib").glob("python*/site-packages")
    ):
        sys.path.append(str(_candidate))

from httpx2 import Response as Httpx2Response
from mcp.client.auth.utils import (
    build_oauth_authorization_server_metadata_discovery_urls,
    create_client_registration_request,
    handle_auth_metadata_response,
    handle_protected_resource_response,
    validate_metadata_issuer,
)
from mcp.shared.auth import OAuthClientMetadata

from modules.worker_ingress import routes as ingress_routes
from modules.worker_ingress import service_credential as svc
from modules.worker_mcp import client as mcp_client
from modules.worker_mcp import gateway_router, oauth_server
from modules.worker_mcp import server as mcp_server
from modules.worker_mcp.config import WorkerMcpConfig
from modules.worker_mcp.oauth_discovery import public_authorization_server_metadata

EMERGENT_HOST = "erp-crm-enterprise-1.preview.emergentagent.com"
EMERGENT_ORIGIN = f"https://{EMERGENT_HOST}"
EMERGENT_ISSUER = f"{EMERGENT_ORIGIN}/api/mcp/oauth"
EMERGENT_RESOURCE = f"{EMERGENT_ORIGIN}/api/mcp"
REDIRECT_URI = "https://chatgpt.com/connector_platform_oauth_redirect"
SUPERADMIN_UUID = "11111111-1111-1111-1111-111111111111"
ADMIN_UUID = "22222222-2222-2222-2222-222222222222"

DISCOVERY_PATHS = (
    "/api/mcp/oauth/.well-known/openid-configuration",
    "/api/mcp/oauth/.well-known/oauth-authorization-server",
    "/.well-known/oauth-authorization-server/api/mcp/oauth",
    "/.well-known/openid-configuration/api/mcp/oauth",
)


def _pkce_pair(seed: str) -> tuple[str, str]:
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(seed.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    return seed, challenge


class _InMemorySesionesStore:
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


@pytest.fixture
def canonical_v2_stack(monkeypatch):
    superadmin = {
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
    admin_only = {
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
    monkeypatch.setattr(svc, "_resolve_active_service_session", store.resolve_active_mcp_service)
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

    def fake_submit_objective(payload, *, current_user):
        submitted_objectives.append({"payload": payload, "user": current_user})
        return {
            "status": "ALREADY_SUBMITTED",
            "job_id": "SEM-WORKER_INGRESS-READ_ONLY_CANARY-CANONICALV2",
            "capability": payload.get("capability"),
            "bounded_context": payload.get("bounded_context"),
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
    monkeypatch.setattr(ingress_routes, "get_job_status", fake_get_job_status)

    backend_app = FastAPI()
    backend_app.include_router(gateway_router.router)
    backend_app.include_router(ingress_routes.router, prefix="/api")

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

    backend_app.dependency_overrides[ingress_routes.WORKER_ADMIN_DEPENDENCY] = fake_worker_admin_dep
    backend_client = TestClient(backend_app)

    forwarded_headers = {
        "x-forwarded-proto": "https",
        "x-forwarded-host": EMERGENT_HOST,
    }

    def in_memory_request_json(*, method: str, url: str, token: str, payload=None, timeout: float = 15.0):
        path = urlsplit(url).path
        req_headers = {"Authorization": f"Bearer {token}", **forwarded_headers}
        resp = backend_client.request(method, path, json=payload, headers=req_headers)
        return resp.status_code, (resp.json() if resp.content else {})

    monkeypatch.setattr(mcp_client, "_request_json", in_memory_request_json)

    cfg = WorkerMcpConfig(
        issuer_url=EMERGENT_ISSUER,
        resource_url="http://127.0.0.1:32913/mcp",
        backend_url="http://127.0.0.1:8001",
        allowed_hosts=("127.0.0.1:32913", EMERGENT_HOST),
        allowed_origins=(),
    )
    mcp_srv = mcp_server.build_mcp_server(cfg)
    mcp_asgi_app = mcp_srv.streamable_http_app(
        json_response=True,
        stateless_http=True,
        transport_security=mcp_server.build_transport_security(cfg),
        host="127.0.0.1",
    )

    monkeypatch.setenv("EDARSAHUB_MCP_UPSTREAM_URL", "http://127.0.0.1:32913")
    monkeypatch.setenv("EDARSAHUB_MCP_INPROCESS", "0")

    orig_async_client = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        if "transport" not in kwargs:
            kwargs["transport"] = httpx.ASGITransport(app=mcp_asgi_app)
        return orig_async_client(*args, **kwargs)

    monkeypatch.setattr(gateway_router.httpx, "AsyncClient", fake_async_client)

    return {
        "backend_app": backend_app,
        "client": backend_client,
        "mcp_srv": mcp_srv,
        "headers": forwarded_headers,
        "users": users,
        "store": store,
        "active_user_holder": active_user_holder,
        "submitted_objectives": submitted_objectives,
    }


@pytest.mark.parametrize("path", DISCOVERY_PATHS)
def test_all_oauth_discovery_routes_return_identical_canonical_metadata_and_options_204(
    canonical_v2_stack,
    path: str,
):
    http = canonical_v2_stack["client"]
    headers = canonical_v2_stack["headers"]
    expected = public_authorization_server_metadata(EMERGENT_ISSUER)

    opt = http.options(path, headers=headers)
    assert opt.status_code == 204

    res = http.get(path, headers=headers)
    assert res.status_code == 200
    assert res.headers.get("cache-control") == "no-store"
    assert res.json() == expected


@pytest.mark.parametrize("path", DISCOVERY_PATHS)
def test_all_oauth_discovery_routes_fail_closed_503_without_https_proof_or_on_header_injection(
    canonical_v2_stack,
    path: str,
):
    http = canonical_v2_stack["client"]

    # Plain HTTP without external HTTPS forwarded proof -> fail-closed 503
    no_https = http.get(path, headers={"host": "127.0.0.1:8001"})
    assert no_https.status_code == 503
    assert no_https.json() == {"error": "temporarily_unavailable"}
    assert "no-store" in (no_https.headers.get("cache-control") or "")

    # Injected path in x-forwarded-host -> fail-closed 503
    injected = http.get(
        path,
        headers={
            "x-forwarded-proto": "https",
            "x-forwarded-host": "erp.example.test/injected",
        },
    )
    assert injected.status_code == 503
    assert injected.json() == {"error": "temporarily_unavailable"}


@pytest.mark.asyncio
async def test_e2e_canonical_v2_discovery_dcr_pkce_rbac_and_mcp_compatibility(
    canonical_v2_stack,
):
    backend_app = canonical_v2_stack["backend_app"]
    headers = canonical_v2_stack["headers"]
    mcp_srv = canonical_v2_stack["mcp_srv"]

    async with mcp_srv.session_manager.run(), httpx.AsyncClient(
        transport=httpx.ASGITransport(app=backend_app),
        base_url="http://backend.local",
    ) as http:
        # 1. Protected Resource Metadata discovery on /api/mcp/.well-known/oauth-protected-resource
        prm_http = await http.get("/api/mcp/.well-known/oauth-protected-resource", headers=headers)
        assert prm_http.status_code == 200
        prm = await handle_protected_resource_response(
            Httpx2Response(prm_http.status_code, headers=dict(prm_http.headers), content=prm_http.content)
        )
        assert prm is not None
        auth_server_url = str(prm.authorization_servers[0])
        assert auth_server_url == EMERGENT_ISSUER

        # 2. Authorization Server Metadata discovery using MCP SDK candidate URLs
        #    Simulate Emergent proxy where only /api/* routes reach FastAPI backend (candidate #3)
        candidates = build_oauth_authorization_server_metadata_discovery_urls(
            auth_server_url, EMERGENT_RESOURCE
        )
        assert candidates[-1] == f"{EMERGENT_ORIGIN}/api/mcp/oauth/.well-known/openid-configuration"

        discovered_asm = None
        for candidate in candidates:
            path = urlsplit(candidate).path
            if not path.startswith("/api/"):
                wire_resp = Httpx2Response(404, content=b"Not Found")
            else:
                r = await http.get(path, headers=headers)
                wire_resp = Httpx2Response(r.status_code, headers=dict(r.headers), content=r.content)
            should_continue, asm = await handle_auth_metadata_response(wire_resp)
            if asm is not None:
                discovered_asm = asm
                break
            assert should_continue is True

        assert discovered_asm is not None
        validate_metadata_issuer(discovered_asm, auth_server_url)
        assert str(discovered_asm.registration_endpoint) == f"{EMERGENT_ISSUER}/register"
        assert discovered_asm.code_challenge_methods_supported == ["S256"]
        assert discovered_asm.scopes_supported == ["worker:status", "worker:submit"]

        # 3. Dynamic Client Registration for "Canonical V2" via discovered registration_endpoint
        dcr_sdk_req = create_client_registration_request(
            discovered_asm,
            OAuthClientMetadata(
                redirect_uris=[REDIRECT_URI],
                client_name="Canonical V2",
                token_endpoint_auth_method="none",
            ),
            EMERGENT_ORIGIN,
        )
        reg_path = urlsplit(str(dcr_sdk_req.url)).path
        assert reg_path == "/api/mcp/oauth/register"

        reg_res = await http.post(
            reg_path,
            content=dcr_sdk_req.content,
            headers={**headers, "Content-Type": "application/json"},
        )
        assert reg_res.status_code == 201
        reg_body = reg_res.json()
        client_id = reg_body["client_id"]
        assert reg_body["scope"] == "worker:status worker:submit"

        # 4. Security check: worker:submit is NEVER auto-granted if omitted on /authorize
        _, empty_challenge = _pkce_pair("empty-scope-pkce-verifier-012345678901234567890123")
        omitted_scope = await http.post(
            urlsplit(str(discovered_asm.authorization_endpoint)).path,
            data={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": "",
                "state": "st-empty",
                "code_challenge": empty_challenge,
                "code_challenge_method": "S256",
                "resource": EMERGENT_RESOURCE,
                "decision": "approve",
            },
            headers=headers,
            follow_redirects=False,
        )
        assert omitted_scope.status_code == 400
        assert omitted_scope.json()["error"] == "SCOPES_INVALID"

        # 5. PKCE S256 plain downgrade is rejected fail-closed
        plain_attempt = await http.post(
            urlsplit(str(discovered_asm.authorization_endpoint)).path,
            data={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": "worker:status",
                "state": "st-plain",
                "code_challenge": empty_challenge,
                "code_challenge_method": "plain",
                "resource": EMERGENT_RESOURCE,
                "decision": "approve",
            },
            headers=headers,
            follow_redirects=False,
        )
        assert plain_attempt.status_code == 400

        async def mint_token(requested_scope: str, seed_tag: str) -> dict[str, Any]:
            verifier, challenge = _pkce_pair(f"{seed_tag}-pkce-verifier-012345678901234567890123456")
            auth_res = await http.post(
                urlsplit(str(discovered_asm.authorization_endpoint)).path,
                data={
                    "response_type": "code",
                    "client_id": client_id,
                    "redirect_uri": REDIRECT_URI,
                    "scope": requested_scope,
                    "state": f"st-{seed_tag}",
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                    "resource": EMERGENT_RESOURCE,
                    "decision": "approve",
                },
                headers=headers,
                follow_redirects=False,
            )
            assert auth_res.status_code == 302
            code = parse_qs(urlsplit(auth_res.headers["location"]).query)["code"][0]
            tok_res = await http.post(
                urlsplit(str(discovered_asm.token_endpoint)).path,
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
            return tok_res.json()

        # 6. Narrow scope token (worker:status): get_job_status -> 200, submit_objective -> 403 insufficient_scope
        status_tok = await mint_token("worker:status", "narrow")
        assert status_tok["scope"] == "worker:status"

        mcp_status_ok = await http.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_job_status", "arguments": {"job_id": "SEM-CANONICALV2"}},
            },
            headers={
                **headers,
                "Authorization": f"Bearer {status_tok['access_token']}",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert mcp_status_ok.status_code == 200
        assert mcp_status_ok.json()["result"]["structuredContent"]["status"] == "READ_ONLY_COMPLETE"

        mcp_sub_403 = await http.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "submit_objective",
                    "arguments": {
                        "objective": "Denied without worker:submit",
                        "bounded_context": "WORKER_INGRESS",
                        "mode": "READ_ONLY",
                        "capability": "READ_ONLY_CANARY",
                    },
                },
            },
            headers={
                **headers,
                "Authorization": f"Bearer {status_tok['access_token']}",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert mcp_sub_403.status_code == 403
        assert 'error="insufficient_scope"' in mcp_sub_403.headers["www-authenticate"]
        assert canonical_v2_stack["submitted_objectives"] == []

        # 7. Explicit SUPERADMIN consent for "worker:status worker:submit" -> submit_objective 200
        full_tok = await mint_token("worker:status worker:submit", "superadmin")
        assert full_tok["scope"] == "worker:status worker:submit"

        mcp_sub_200 = await http.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "submit_objective",
                    "arguments": {
                        "objective": "Authorized Canonical V2 canary",
                        "bounded_context": "WORKER_INGRESS",
                        "mode": "READ_ONLY",
                        "capability": "READ_ONLY_CANARY",
                    },
                },
            },
            headers={
                **headers,
                "Authorization": f"Bearer {full_tok['access_token']}",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert mcp_sub_200.status_code == 200
        assert (
            mcp_sub_200.json()["result"]["structuredContent"]["job_id"]
            == "SEM-WORKER_INGRESS-READ_ONLY_CANARY-CANONICALV2"
        )
        assert len(canonical_v2_stack["submitted_objectives"]) == 1

        # 8. Non-SUPERADMIN RBAC_ADMIN cannot consent to worker:submit (400 SCOPES_FORBIDDEN)
        canonical_v2_stack["active_user_holder"]["user"] = canonical_v2_stack["users"][ADMIN_UUID]
        _, admin_challenge = _pkce_pair("admin-denied-pkce-verifier-0123456789012345678901234")
        denied_admin = await http.post(
            urlsplit(str(discovered_asm.authorization_endpoint)).path,
            data={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": "worker:status worker:submit",
                "state": "st-admin-denied",
                "code_challenge": admin_challenge,
                "code_challenge_method": "S256",
                "resource": EMERGENT_RESOURCE,
                "decision": "approve",
            },
            headers=headers,
            follow_redirects=False,
        )
        assert denied_admin.status_code == 400
        assert denied_admin.json()["error"] == "SCOPES_FORBIDDEN"
