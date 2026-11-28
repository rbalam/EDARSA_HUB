"""Gate 3L isolated security & compatibility suite: OAuth Step-Up Challenge & Runtime Sync.

Validates:
- RFC 7591 client registration scope advertisement without automatic scope grants.
- HTTP 401 WWW-Authenticate scope advertisement through gateway_router.py public HTTPS URL rewrite.
- HTTP 403 insufficient_scope step-up challenge at the MCP HTTP boundary when ChatGPT holds only worker:status.
- Preservation of HTTP 200 for get_job_status with worker:status.
- Full OAuth 2.1 + PKCE S256 step-up re-consent to worker:status worker:submit enabling submit_objective (HTTP 200).
- Explicit differentiation of HTTP 403 authorization errors vs HTTP 422 validation errors (including malformed body precedence at worker_ingress).
- Idempotency, concurrency isolation, and fail-closed non-SUPERADMIN rejection without SQL or network connections.
"""
from __future__ import annotations

import asyncio
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

from modules.worker_ingress import routes as ingress_routes
from modules.worker_ingress import service_credential as svc
from modules.worker_ingress.service import WorkerIngressError
from modules.worker_mcp import client as mcp_client
from modules.worker_mcp import gateway_router, oauth_server
from modules.worker_mcp import server as mcp_server
from modules.worker_mcp.config import WorkerMcpConfig

EMERGENT_ORIGIN = "https://erp-crm-enterprise-1.preview.emergentagent.com"
EMERGENT_RESOURCE = EMERGENT_ORIGIN + "/api/mcp"
EMERGENT_METADATA = EMERGENT_ORIGIN + "/api/mcp/.well-known/oauth-protected-resource"
REDIRECT_URI = "https://chatgpt.com/connector/oauth/test_connector_gate3l"
SUPERADMIN_UUID = "11111111-1111-1111-1111-111111111111"
ADMIN_UUID = "22222222-2222-2222-2222-222222222222"


def _pkce_pair(seed: str = "gate3l-pkce-verifier-012345678901234567890123456789") -> tuple[str, str]:
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
def isolated_full_gateway_stack(monkeypatch):
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
        if payload.get("capability") == "UNAPPROVED_CAPABILITY":
            raise WorkerIngressError("SEMANTIC_CAPABILITY_UNKNOWN")
        submitted_objectives.append({"payload": payload, "user": current_user})
        return {
            "status": "ALREADY_SUBMITTED",
            "job_id": "SEM-WORKER_INGRESS-READ_ONLY_CANARY-GATE3L001",
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
        "x-forwarded-host": "erp-crm-enterprise-1.preview.emergentagent.com",
    }

    def in_memory_request_json(*, method: str, url: str, token: str, payload=None, timeout: float = 15.0):
        path = urlsplit(url).path
        req_headers = {"Authorization": f"Bearer {token}", **forwarded_headers}
        resp = backend_client.request(method, path, json=payload, headers=req_headers)
        return resp.status_code, (resp.json() if resp.content else {})

    monkeypatch.setattr(mcp_client, "_request_json", in_memory_request_json)

    # Wire gateway_router upstream to an in-memory ASGITransport of the isolated MCP loopback service!
    cfg = WorkerMcpConfig(
        issuer_url=EMERGENT_ORIGIN + "/api/mcp/oauth",
        resource_url="http://127.0.0.1:32913/mcp",
        backend_url="http://127.0.0.1:8001",
        allowed_hosts=("127.0.0.1:32913", "erp-crm-enterprise-1.preview.emergentagent.com"),
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


def test_register_advertises_available_scopes_without_granting_automatically(
    isolated_full_gateway_stack,
):
    http = isolated_full_gateway_stack["client"]
    headers = isolated_full_gateway_stack["headers"]

    # 1. Omitted scope in DCR -> advertises "worker:status worker:submit"
    reg_default = http.post(
        "/api/mcp/oauth/register",
        json={"redirect_uris": [REDIRECT_URI], "client_name": "ChatGPT Connector"},
        headers=headers,
    )
    assert reg_default.status_code == 201
    reg_body = reg_default.json()
    assert reg_body["scope"] == "worker:status worker:submit"

    # 2. Explicit narrow scope in DCR -> preserves narrow scope advertisement
    reg_narrow = http.post(
        "/api/mcp/oauth/register",
        json={
            "redirect_uris": [REDIRECT_URI],
            "client_name": "ReadOnly Client",
            "scope": "worker:status",
        },
        headers=headers,
    )
    assert reg_narrow.status_code == 201
    assert reg_narrow.json()["scope"] == "worker:status"

    # 3. Unknown or non-string scope in DCR -> rejected 400 invalid_client_metadata
    for bad_scope in ("worker:admin", "worker:status worker:status", 123):
        bad = http.post(
            "/api/mcp/oauth/register",
            json={"redirect_uris": [REDIRECT_URI], "scope": bad_scope},
            headers=headers,
        )
        assert bad.status_code == 400
        assert bad.json()["error"] == "invalid_client_metadata"

    # 4. Crucial security invariant: omitting scope in /authorize STILL fails closed (never grants automatically!)
    _, challenge = _pkce_pair()
    no_scope_auth = http.post(
        "/api/mcp/oauth/authorize",
        data={
            "response_type": "code",
            "client_id": reg_body["client_id"],
            "redirect_uri": REDIRECT_URI,
            "scope": "",
            "state": "st-no-scope",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "resource": EMERGENT_RESOURCE,
            "decision": "approve",
        },
        headers=headers,
        follow_redirects=False,
    )
    assert no_scope_auth.status_code == 400
    assert no_scope_auth.json()["error"] == "SCOPES_INVALID"


@pytest.mark.asyncio
async def test_e2e_chatgpt_stepup_401_403_reconsent_submit_status_and_422_separation(
    isolated_full_gateway_stack,
):
    backend_app = isolated_full_gateway_stack["backend_app"]
    headers = isolated_full_gateway_stack["headers"]
    mcp_srv = isolated_full_gateway_stack["mcp_srv"]

    async with mcp_srv.session_manager.run(), httpx.AsyncClient(
        transport=httpx.ASGITransport(app=backend_app),
        base_url="http://backend.local",
    ) as http:
        async def mint_token_via_pkce(
            client_id: str,
            requested_scope: str,
        ) -> dict[str, Any]:
            safe_seed = (
                "verifier-"
                + requested_scope.replace(" ", "-").replace(":", "-")
                + "-012345678901234567890123456"
            )
            verifier, challenge = _pkce_pair(safe_seed)
            auth_res = await http.post(
                "/api/mcp/oauth/authorize",
                data={
                    "response_type": "code",
                    "client_id": client_id,
                    "redirect_uri": REDIRECT_URI,
                    "scope": requested_scope,
                    "state": "st-3l",
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
            return tok_res.json()

        # Step A: Unauthenticated POST /api/mcp -> HTTP 401 with public HTTPS resource_metadata + scope="worker:status worker:submit"
        r401 = await http.post(
            "/api/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={**headers, "Accept": "application/json, text/event-stream"},
        )
        assert r401.status_code == 401
        www_401 = r401.headers["www-authenticate"]
        assert f'resource_metadata="{EMERGENT_METADATA}"' in www_401
        assert 'scope="worker:status worker:submit"' in www_401
        assert "127.0.0.1" not in www_401

        # Step B: Register client & simulate legacy ChatGPT token holding ONLY worker:status
        reg = await http.post(
            "/api/mcp/oauth/register",
            json={"redirect_uris": [REDIRECT_URI], "client_name": "ChatGPT"},
            headers=headers,
        )
        client_id = reg.json()["client_id"]
        legacy_tok = await mint_token_via_pkce(client_id, "worker:status")
        assert legacy_tok["scope"] == "worker:status"

        # Step C: get_job_status with worker:status succeeds with HTTP 200 OK
        r_status_ok = await http.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_job_status",
                    "arguments": {"job_id": "SEM-WORKER_INGRESS-READ_ONLY_CANARY-GATE3L001"},
                },
            },
            headers={
                **headers,
                "Authorization": f"Bearer {legacy_tok['access_token']}",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert r_status_ok.status_code == 200
        assert r_status_ok.json()["result"]["structuredContent"]["status"] == "READ_ONLY_COMPLETE"

        # Step D: submit_objective with worker:status returns HTTP 403 insufficient_scope (NOT 200 UnexpectedToolError!)
        r_sub_403 = await http.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "submit_objective",
                    "arguments": {
                        "objective": "Attempt with status-only token",
                        "bounded_context": "WORKER_INGRESS",
                        "mode": "READ_ONLY",
                        "capability": "READ_ONLY_CANARY",
                    },
                },
            },
            headers={
                **headers,
                "Authorization": f"Bearer {legacy_tok['access_token']}",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert r_sub_403.status_code == 403
        www_403 = r_sub_403.headers["www-authenticate"]
        assert 'error="insufficient_scope"' in www_403
        assert f'resource_metadata="{EMERGENT_METADATA}"' in www_403
        assert 'scope="worker:status worker:submit"' in www_403
        assert "127.0.0.1" not in www_403
        assert r_sub_403.json()["error"] == "insufficient_scope"
        assert r_sub_403.json()["required_scope"] == "worker:submit"
        assert isolated_full_gateway_stack["submitted_objectives"] == []

        # Step E: Direct ingress bypass with worker:status internal JWT + malformed empty body {} STILL returns 403 BEFORE 422!
        exch_res = await http.post(
            "/api/internal/worker/auth/exchange",
            headers={**headers, "Authorization": f"Bearer {legacy_tok['access_token']}"},
        )
        internal_status_jwt = exch_res.json()["access_token"]
        r_direct_malformed = await http.post(
            "/api/internal/worker/objectives",
            json={},
            headers={**headers, "Authorization": f"Bearer {internal_status_jwt}"},
        )
        assert r_direct_malformed.status_code == 403
        assert r_direct_malformed.json()["detail"]["error"] == "INSUFFICIENT_SCOPE"

        # Step F: Step-up OAuth 2.1 + PKCE S256 consent for "worker:status worker:submit"
        stepup_tok = await mint_token_via_pkce(client_id, "worker:status worker:submit")
        assert stepup_tok["scope"] == "worker:status worker:submit"

        # Step G: Validation failure (HTTP 422) with worker:submit token returns HTTP 200 deterministic ToolError (differentiated from 403!)
        r_val_422 = await http.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "submit_objective",
                    "arguments": {
                        "objective": "Bad capability check",
                        "bounded_context": "WORKER_INGRESS",
                        "mode": "READ_ONLY",
                        "capability": "UNAPPROVED_CAPABILITY",
                    },
                },
            },
            headers={
                **headers,
                "Authorization": f"Bearer {stepup_tok['access_token']}",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert r_val_422.status_code == 200
        assert "www-authenticate" not in r_val_422.headers
        assert r_val_422.json()["result"]["isError"] is True
        assert (
            "VALIDATION_ERROR_422:SEMANTIC_CAPABILITY_UNKNOWN"
            in r_val_422.json()["result"]["content"][0]["text"]
        )

        # Step H: Concurrent mixed requests preserve strict isolation (403 vs 200 status vs 200 submit)
        conc_403, conc_stat, conc_sub = await asyncio.gather(
            http.post(
                "/api/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 10,
                    "method": "tools/call",
                    "params": {
                        "name": "submit_objective",
                        "arguments": {
                            "objective": "Concurrent blocked",
                            "bounded_context": "WORKER_INGRESS",
                            "mode": "READ_ONLY",
                            "capability": "READ_ONLY_CANARY",
                        },
                    },
                },
                headers={
                    **headers,
                    "Authorization": f"Bearer {legacy_tok['access_token']}",
                    "Accept": "application/json, text/event-stream",
                },
            ),
            http.post(
                "/api/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 11,
                    "method": "tools/call",
                    "params": {
                        "name": "get_job_status",
                        "arguments": {"job_id": "SEM-WORKER_INGRESS-READ_ONLY_CANARY-GATE3L001"},
                    },
                },
                headers={
                    **headers,
                    "Authorization": f"Bearer {legacy_tok['access_token']}",
                    "Accept": "application/json, text/event-stream",
                },
            ),
            http.post(
                "/api/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 12,
                    "method": "tools/call",
                    "params": {
                        "name": "submit_objective",
                        "arguments": {
                            "objective": "Authorized canary after step-up",
                            "bounded_context": "WORKER_INGRESS",
                            "mode": "READ_ONLY",
                            "capability": "READ_ONLY_CANARY",
                        },
                    },
                },
                headers={
                    **headers,
                    "Authorization": f"Bearer {stepup_tok['access_token']}",
                    "Accept": "application/json, text/event-stream",
                },
            ),
        )
        assert conc_403.status_code == 403
        assert conc_stat.status_code == 200
        assert conc_sub.status_code == 200
        assert conc_sub.json()["result"].get("isError") is not True
        assert (
            conc_sub.json()["result"]["structuredContent"]["job_id"]
            == "SEM-WORKER_INGRESS-READ_ONLY_CANARY-GATE3L001"
        )
        assert len(isolated_full_gateway_stack["submitted_objectives"]) == 1

        # Step H2: Idempotent replay of identical submit_objective returns HTTP 200 ALREADY_SUBMITTED with identical job_id
        replay_sub = await http.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {
                    "name": "submit_objective",
                    "arguments": {
                        "objective": "Authorized canary after step-up",
                        "bounded_context": "WORKER_INGRESS",
                        "mode": "READ_ONLY",
                        "capability": "READ_ONLY_CANARY",
                    },
                },
            },
            headers={
                **headers,
                "Authorization": f"Bearer {stepup_tok['access_token']}",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert replay_sub.status_code == 200
        assert (
            replay_sub.json()["result"]["structuredContent"]["status"]
            == "ALREADY_SUBMITTED"
        )
        assert (
            replay_sub.json()["result"]["structuredContent"]["job_id"]
            == "SEM-WORKER_INGRESS-READ_ONLY_CANARY-GATE3L001"
        )

        # Step H3: Revoking dbo.Sesiones row for stepup_tok fails closed with HTTP 401 WWW-Authenticate on subsequent submit_objective
        tok_digest = hashlib.sha256(stepup_tok["access_token"].encode("utf-8")).hexdigest()
        isolated_full_gateway_stack["store"].rows[tok_digest]["EstaActiva"] = 0
        post_rev = await http.post(
            "/api/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {
                    "name": "submit_objective",
                    "arguments": {
                        "objective": "Blocked after revocation",
                        "bounded_context": "WORKER_INGRESS",
                        "mode": "READ_ONLY",
                        "capability": "READ_ONLY_CANARY",
                    },
                },
            },
            headers={
                **headers,
                "Authorization": f"Bearer {stepup_tok['access_token']}",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert post_rev.status_code == 401
        assert 'scope="worker:status worker:submit"' in post_rev.headers["www-authenticate"]

        # Step I: Non-SUPERADMIN RBAC_ADMIN cannot step-up consent to worker:submit (fails closed 400 SCOPES_FORBIDDEN)
        isolated_full_gateway_stack["active_user_holder"]["user"] = (
            isolated_full_gateway_stack["users"][ADMIN_UUID]
        )
        _, non_sup_challenge = _pkce_pair("non-sup-verifier-012345678901234567890123456789")
        denied_stepup = await http.post(
            "/api/mcp/oauth/authorize",
            data={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": "worker:status worker:submit",
                "state": "st-denied",
                "code_challenge": non_sup_challenge,
                "code_challenge_method": "S256",
                "resource": EMERGENT_RESOURCE,
                "decision": "approve",
            },
            headers=headers,
            follow_redirects=False,
        )
        assert denied_stepup.status_code == 400
        assert denied_stepup.json()["error"] == "SCOPES_FORBIDDEN"
