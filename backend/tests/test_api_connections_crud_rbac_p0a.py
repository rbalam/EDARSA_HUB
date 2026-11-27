"""Regression checks for SQL_RBAC_019 P0-A API connection CRUD authorization."""
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute

from core.rbac.middleware import RBACExplicitDependency
from modules.api_connections import routes as module


CASES = [
    ("POST", "/api-connections", "create_api_connection", {"name": "P0A", "url": "https://example.invalid"}),
    ("PUT", "/api-connections/11111111-1111-1111-1111-111111111111", "update_api_connection", {"name": "P0A"}),
    ("DELETE", "/api-connections/11111111-1111-1111-1111-111111111111", "delete_api_connection", None),
]


def _app_and_guard(method: str, path: str):
    app = FastAPI()
    app.include_router(module.router)
    route = next(
        r for r in app.routes
        if isinstance(r, APIRoute) and r.path == path.replace(
            "11111111-1111-1111-1111-111111111111", "{api_id}"
        ) and method in r.methods
    )
    guards = [
        dependency.call
        for dependency in route.dependant.dependencies
        if isinstance(dependency.call, RBACExplicitDependency)
    ]
    assert len(guards) == 1
    assert guards[0].permiso == "RBAC_ADMIN"
    return app, guards[0]


@pytest.mark.parametrize("method,path,writer_name,body", CASES)
def test_crud_routes_require_explicit_sql_admin(method, path, writer_name, body):
    _app_and_guard(method, path)


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,writer_name,body", CASES)
async def test_denied_sql_admin_never_calls_writer(monkeypatch, method, path, writer_name, body):
    app, guard = _app_and_guard(method, path)
    writer = AsyncMock()
    monkeypatch.setattr(module, writer_name, writer)

    async def deny_access():
        raise HTTPException(status_code=403, detail="PERMISO_DENEGADO")

    app.dependency_overrides[guard] = deny_access
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.request(method, path, json=body, headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 403
    writer.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,writer_name,body", CASES)
async def test_sql_admin_can_reach_existing_writer(monkeypatch, method, path, writer_name, body):
    app, guard = _app_and_guard(method, path)
    writer = AsyncMock(return_value={"id": "ok"})
    monkeypatch.setattr(module, writer_name, writer)
    monkeypatch.setattr(module, "_verify_token", lambda token: {"email": "admin@example.invalid"})

    async def allow_access():
        return {"email": "admin@example.invalid"}

    app.dependency_overrides[guard] = allow_access
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.request(method, path, json=body, headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    writer.assert_awaited_once()
