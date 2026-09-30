from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

for key, value in {
    "EDARSAHUB_SQL_HOST": "localhost",
    "EDARSAHUB_SQL_DATABASE": "EDARSAHUB",
    "EDARSAHUB_SQL_USER": "test",
    "EDARSAHUB_SQL_PASSWORD": "test",
    "JWT_SECRET": "test-secret-for-ia-system-access",
}.items():
    os.environ.setdefault(key, value)

from modules.ia_assistant import query_bridge  # noqa: E402
from modules.ia_assistant import repository  # noqa: E402
from modules.ia_assistant import service  # noqa: E402
from modules.ia_assistant import worker_routes  # noqa: E402


def _demo_app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/demo/{item_id}", operation_id="read_demo")
    async def read_demo(item_id: str, q: str | None = None):
        return {
            "item_id": item_id,
            "q": q,
            "password": "never-expose",
            "nested": {"api_key": "never-expose-either"},
        }

    @app.post("/api/demo", operation_id="write_demo")
    async def write_demo():
        return {"ok": True}

    @app.get("/api/sql/catalog", operation_id="sql_catalog")
    async def sql_catalog():
        return {"ok": True}

    @app.get("/api/admin/status", operation_id="admin_status")
    async def admin_status():
        return {"ok": True}

    @app.get("/api/demo/run", operation_id="run_demo")
    async def run_demo():
        return {"ok": True}

    return app


def test_catalog_is_internal_get_only_and_fail_closed():
    catalog = query_bridge.build_readonly_catalog(_demo_app())
    operation_ids = {row["operation_id"] for row in catalog}

    assert "read_demo" in operation_ids
    assert "write_demo" not in operation_ids
    assert "sql_catalog" not in operation_ids
    assert "admin_status" not in operation_ids
    assert "run_demo" not in operation_ids


def test_executor_rejects_unknown_operation():
    app = _demo_app()
    catalog = query_bridge.build_readonly_catalog(app)

    result = asyncio.run(
        query_bridge.execute_catalog_operation(
            app,
            catalog,
            {"operation_id": "not_catalogued"},
        )
    )

    assert result["ok"] is False
    assert result["error"] == "OPERACION_NO_AUTORIZADA"


def test_executor_redacts_sensitive_fields():
    app = _demo_app()
    catalog = query_bridge.build_readonly_catalog(app)

    result = asyncio.run(
        query_bridge.execute_catalog_operation(
            app,
            catalog,
            {
                "operation_id": "read_demo",
                "path_params": {"item_id": "abc"},
                "query_params": {"q": "visible"},
            },
        )
    )

    assert result["ok"] is True
    assert result["data"]["q"] == "visible"
    assert result["data"]["password"] == "***REDACTED***"
    assert result["data"]["nested"]["api_key"] == "***REDACTED***"


def test_worker_bearer_is_environment_backed(monkeypatch):
    monkeypatch.setenv("EDARSA_AI_API_KEY", "configured-secret")

    worker_routes._validate_worker_bearer("Bearer configured-secret")

    with pytest.raises(HTTPException) as exc:
        worker_routes._validate_worker_bearer("Bearer wrong-secret")

    assert exc.value.status_code == 401
    assert exc.value.detail == worker_routes.AUTH_ERROR


def test_worker_bearer_fails_closed_without_environment(monkeypatch):
    monkeypatch.delenv("EDARSA_AI_API_KEY", raising=False)

    with pytest.raises(HTTPException) as exc:
        worker_routes._validate_worker_bearer("Bearer anything")

    assert exc.value.status_code == 401
    assert exc.value.detail == worker_routes.AUTH_ERROR


def test_service_persists_original_message_not_system_context(monkeypatch):
    monkeypatch.setattr(
        repository,
        "session_exists_for_user",
        lambda *_args, **_kwargs: True,
    )

    saved = {}
    monkeypatch.setattr(
        repository,
        "save_exchange",
        lambda **kwargs: saved.update(kwargs) or True,
    )

    captured = {}

    async def fake_llm(_session_id, text, **_kwargs):
        captured["text"] = text
        return "respuesta con datos"

    monkeypatch.setattr(service, "_send_llm", fake_llm)

    result = asyncio.run(
        service.enviar_mensaje(
            "00000000-0000-0000-0000-000000000001",
            "user@example.com",
            "consulta las ventas",
            system_context=[
                {
                    "operation_id": "read_demo",
                    "ok": True,
                    "data": {"total": 10},
                }
            ],
        )
    )

    assert "DATOS AUTORIZADOS" in captured["text"]
    assert saved["user_text"] == "consulta las ventas"
    assert saved["assistant_text"] == "respuesta con datos"
    assert result["data_sources"] == ["read_demo"]
