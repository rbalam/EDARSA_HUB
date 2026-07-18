from __future__ import annotations

import ast
import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT = Path(
    __file__
).resolve().parents[2]

BACKEND = ROOT / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND),
    )

for key, value in {
    "EDARSAHUB_SQL_HOST": "localhost",
    "EDARSAHUB_SQL_DATABASE": "EDARSAHUB",
    "EDARSAHUB_SQL_USER": "test",
    "EDARSAHUB_SQL_PASSWORD": "test",
    "JWT_SECRET": "test-secret-for-ia-assistant-contract",
}.items():
    os.environ.setdefault(key, value)

from modules.ia_assistant import repository  # noqa: E402
from modules.ia_assistant import routes  # noqa: E402
from modules.ia_assistant import service  # noqa: E402


def test_all_endpoints_require_explicit_ia_permission():
    source = (
        BACKEND
        / "modules/ia_assistant/routes.py"
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    methods = {
        "get",
        "post",
        "delete",
        "put",
        "patch",
    }

    endpoints = []

    for node in tree.body:
        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        is_endpoint = any(
            isinstance(
                decorator,
                ast.Call,
            )
            and isinstance(
                decorator.func,
                ast.Attribute,
            )
            and decorator.func.attr
            in methods
            for decorator
            in node.decorator_list
        )

        if is_endpoint:
            endpoints.append(
                ast.get_source_segment(
                    source,
                    node,
                )
                or ""
            )

    assert len(endpoints) == 6

    for endpoint in endpoints:
        assert (
            "require_explicit_permission("
            in endpoint
        )
        assert (
            "IA_PERMISSION"
            in endpoint
        )


def test_identity_fails_closed_without_email():
    with pytest.raises(
        HTTPException
    ) as exc:
        routes._current_email(
            {
                "role": "ADMIN",
            }
        )

    assert exc.value.status_code == 403


def test_identity_is_normalized():
    result = routes._current_email(
        {
            "email": (
                "  USER@EXAMPLE.COM "
            )
        }
    )

    assert result == "user@example.com"


def test_create_session_response_matches_frontend_contract(
    monkeypatch,
):
    session_payload = {
        "sesion_id": (
            "00000000-0000-0000-"
            "0000-000000000001"
        ),
        "titulo": "Nueva conversación",
        "modelo": service.MODELO_IA,
    }

    monkeypatch.setattr(
        service,
        "crear_sesion",
        lambda *_args, **_kwargs: session_payload,
    )

    result = asyncio.run(
        routes.crear_sesion(
            routes.CrearSesionRequest(),
            {
                "email": "user@example.com",
            },
        )
    )

    assert result["success"] is True
    assert result["sesion"] == session_payload
    assert (
        result["sesion"]["sesion_id"]
        == session_payload["sesion_id"]
    )
    assert (
        result["sesion_id"]
        == session_payload["sesion_id"]
    )


def test_repository_has_no_dynamic_sql_execute():
    path = (
        BACKEND
        / "modules/ia_assistant/repository.py"
    )

    source = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    assert "_esc(" not in source

    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        if not isinstance(
            node.func,
            ast.Attribute,
        ):
            continue

        if (
            node.func.attr != "execute"
            or not node.args
        ):
            continue

        sql_arg = node.args[0]

        assert not isinstance(
            sql_arg,
            ast.JoinedStr,
        )

        assert not isinstance(
            sql_arg,
            ast.BinOp,
        )


def test_foreign_session_is_not_disclosed(
    monkeypatch,
):
    monkeypatch.setattr(
        repository,
        "session_exists_for_user",
        lambda *_args, **_kwargs: False,
    )

    with pytest.raises(
        service.SessionNotFoundError
    ):
        service.obtener_mensajes(
            (
                "00000000-0000-0000-"
                "0000-000000000001"
            ),
            "a@example.com",
        )


def test_provider_failure_does_not_persist(
    monkeypatch,
):
    monkeypatch.setattr(
        repository,
        "session_exists_for_user",
        lambda *_args, **_kwargs: True,
    )

    saved = []

    monkeypatch.setattr(
        repository,
        "save_exchange",
        lambda **kwargs: saved.append(
            kwargs
        ),
    )

    async def fail_provider(
        *_args,
        **_kwargs,
    ):
        raise service.LLMTimeoutError(
            "timeout"
        )

    monkeypatch.setattr(
        service,
        "_send_llm",
        fail_provider,
    )

    with pytest.raises(
        service.LLMTimeoutError
    ):
        asyncio.run(
            service.enviar_mensaje(
                (
                    "00000000-0000-0000-"
                    "0000-000000000001"
                ),
                "a@example.com",
                "hola",
            )
        )

    assert saved == []


def test_success_persists_atomic_exchange(
    monkeypatch,
):
    monkeypatch.setattr(
        repository,
        "session_exists_for_user",
        lambda *_args, **_kwargs: True,
    )

    captured = {}

    def save_exchange(**kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr(
        repository,
        "save_exchange",
        save_exchange,
    )

    async def answer(
        *_args,
        **_kwargs,
    ):
        return "respuesta controlada"

    monkeypatch.setattr(
        service,
        "_send_llm",
        answer,
    )

    result = asyncio.run(
        service.enviar_mensaje(
            (
                "00000000-0000-0000-"
                "0000-000000000001"
            ),
            "a@example.com",
            "hola",
        )
    )

    assert (
        result["respuesta"]
        == "respuesta controlada"
    )

    assert (
        captured["user_text"]
        == "hola"
    )

    assert (
        captured["assistant_text"]
        == "respuesta controlada"
    )


def test_llm_call_has_timeout():
    source = (
        BACKEND
        / "modules/ia_assistant/service.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "asyncio.wait_for(" in source
    assert "LLM_TIMEOUT_SECONDS" in source


def test_frontend_uses_canonical_api_client():
    source = (
        ROOT
        / "frontend/src/services/"
        "iaAssistantApi.js"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "import api from '../lib/api'"
        in source
    )

    assert "fetch(" not in source
    assert "getToken" not in source
    assert "api.post(" in source


def test_menu_permission_map_contains_ia():
    source = (
        BACKEND
        / "modules/auth/routes.py"
    ).read_text(
        encoding="utf-8"
    )

    assert '"ia": [' in source

    assert (
        '"IA_ASSISTANT_VER"'
        in source
    )


def test_layout_has_no_hardcoded_ia_menu():
    source = (
        ROOT
        / "frontend/src/pages/Layout.js"
    ).read_text(
        encoding="utf-8"
    )

    assert "name: 'IA'" not in source
    assert 'name: "IA"' not in source


def test_enterprise_menu_knows_ia_sql_icon():
    source = (
        ROOT
        / "frontend/src/components/navigation/"
        "EnterpriseSidebarMenu.jsx"
    ).read_text(
        encoding="utf-8"
    )

    assert "Sparkles" in source
    assert "const ICONS" in source
