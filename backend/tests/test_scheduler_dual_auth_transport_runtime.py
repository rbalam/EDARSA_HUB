import pytest

from fastapi import HTTPException
from starlette.requests import Request

from core.rbac.middleware import (
    RBACExplicitDualDependency,
)


def _request(
    *,
    authorization=None,
    cookie_name=None,
    cookie_value=None,
):
    headers = []

    if authorization is not None:
        headers.append(
            (
                b"authorization",
                authorization.encode("utf-8"),
            )
        )

    if (
        cookie_name is not None
        and cookie_value is not None
    ):
        cookie = (
            f"{cookie_name}={cookie_value}"
        )

        headers.append(
            (
                b"cookie",
                cookie.encode("utf-8"),
            )
        )

    scope = {
        "type": "http",
        "method": "POST",
        "path": (
            "/api/v2/scheduler/jobs/"
            "sync_comercial_v2/pause"
        ),
        "headers": headers,
        "client": (
            "127.0.0.1",
            12345,
        ),
        "query_string": b"",
        "server": (
            "127.0.0.1",
            8001,
        ),
        "scheme": "http",
    }

    return Request(scope)


@pytest.mark.asyncio
async def test_dual_dependency_uses_cookie():
    import core.security as security

    dep = RBACExplicitDualDependency(
        "SCHEDULER_GESTIONAR"
    )

    captured = {}

    async def fake_current_user(request):
        return {
            "id": "test",
            "email": "test@example.com",
            "role": "SUPERADMIN",
        }

    async def fake_delegate(
        request,
        credentials,
    ):
        captured["scheme"] = (
            credentials.scheme
        )
        captured["token"] = (
            credentials.credentials
        )

        return {
            "ok": True,
        }

    dep._delegate = fake_delegate

    original = (
        security.get_current_user_dual
    )

    security.get_current_user_dual = (
        fake_current_user
    )

    try:
        request = _request(
            cookie_name=(
                security.AUTH_COOKIE_NAME
            ),
            cookie_value=(
                "cookie-token-test"
            ),
        )

        result = await dep(request)

    finally:
        security.get_current_user_dual = (
            original
        )

    assert result == {
        "ok": True,
    }

    assert captured == {
        "scheme": "Bearer",
        "token": "cookie-token-test",
    }


@pytest.mark.asyncio
async def test_dual_dependency_prefers_bearer():
    import core.security as security

    dep = RBACExplicitDualDependency(
        "SCHEDULER_GESTIONAR"
    )

    captured = {}

    async def fake_current_user(request):
        return {
            "id": "test",
            "email": "test@example.com",
            "role": "SUPERADMIN",
        }

    async def fake_delegate(
        request,
        credentials,
    ):
        captured["token"] = (
            credentials.credentials
        )

        return True

    dep._delegate = fake_delegate

    original = (
        security.get_current_user_dual
    )

    security.get_current_user_dual = (
        fake_current_user
    )

    try:
        request = _request(
            authorization=(
                "Bearer header-token-test"
            ),
            cookie_name=(
                security.AUTH_COOKIE_NAME
            ),
            cookie_value=(
                "cookie-token-test"
            ),
        )

        result = await dep(request)

    finally:
        security.get_current_user_dual = (
            original
        )

    assert result is True

    assert captured["token"] == (
        "header-token-test"
    )


@pytest.mark.asyncio
async def test_dual_dependency_rejects_no_token():
    import core.security as security

    dep = RBACExplicitDualDependency(
        "SCHEDULER_GESTIONAR"
    )

    async def fake_current_user(request):
        return {
            "id": "test",
            "email": "test@example.com",
            "role": "SUPERADMIN",
        }

    original = (
        security.get_current_user_dual
    )

    security.get_current_user_dual = (
        fake_current_user
    )

    try:
        with pytest.raises(
            HTTPException
        ) as exc:
            await dep(
                _request()
            )

    finally:
        security.get_current_user_dual = (
            original
        )

    assert exc.value.status_code == 401


def test_scheduler_routes_use_dual_dependency():
    from pathlib import Path

    text = Path(
        "/app/backend/core/scheduler/"
        "routes.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        'require_explicit_permission_dual('
        '"SCHEDULER_GESTIONAR")'
        in text
    )

    assert text.count(
        'require_explicit_permission_dual('
        '"SCHEDULER_GESTIONAR")'
    ) == 2

    assert text.count(
        'require_explicit_permission_dual('
        '"SCHEDULER_ADMIN")'
    ) == 3

    assert (
        'require_explicit_permission("'
        not in text
    )
