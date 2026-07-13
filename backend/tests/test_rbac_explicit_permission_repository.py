from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import core.connections.rbac_explicit_permission_repository as repository
from core.connections.rbac_explicit_permission_repository import (
    AuthenticatedEmailRequired,
    EXPLICIT_PERMISSION_SQL,
    InvalidPermissionConnectionFactory,
    PermissionCodeRequired,
    PermissionConnectionNotCreated,
    has_explicit_permission_readonly,
)


class FakeCursor:
    def __init__(
        self,
        *,
        row: Any,
        events: list[str],
    ) -> None:
        self.row = row
        self.events = events
        self.executions: list[
            tuple[str, tuple[Any, ...]]
        ] = []
        self.closed = False

    def execute(
        self,
        sql: str,
        params: tuple[Any, ...],
    ) -> None:
        self.events.append("permission_query")
        self.executions.append((sql, params))

    def fetchone(self) -> Any:
        return self.row

    def close(self) -> None:
        self.closed = True
        self.events.append("cursor_close")


class FakeConnection:
    def __init__(
        self,
        *,
        row: Any,
        events: list[str],
    ) -> None:
        self.events = events
        self.cursor_instance = FakeCursor(
            row=row,
            events=events,
        )
        self.closed = False

    def cursor(self) -> FakeCursor:
        self.events.append("cursor")
        return self.cursor_instance

    def close(self) -> None:
        self.closed = True
        self.events.append("connection_close")


def test_grants_explicit_permission_after_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    connection = FakeConnection(
        row=(1,),
        events=events,
    )

    def validate_identity(candidate: Any) -> None:
        assert candidate is connection
        events.append("identity")

    monkeypatch.setattr(
        repository,
        "validate_readonly_identity",
        validate_identity,
    )

    def connection_factory() -> FakeConnection:
        events.append("open")
        return connection

    result = has_explicit_permission_readonly(
        user={"email": "persona@example.com"},
        permission="CONEXIONES_VER",
        connection_factory=connection_factory,
    )

    assert result is True
    assert events == [
        "open",
        "identity",
        "cursor",
        "permission_query",
        "cursor_close",
        "connection_close",
    ]

    sql, params = (
        connection.cursor_instance.executions[0]
    )

    assert sql == EXPLICIT_PERMISSION_SQL
    assert params == (
        "persona@example.com",
        "CONEXIONES_VER",
        "CONEXIONES_VER",
    )


def test_returns_false_when_permission_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    connection = FakeConnection(
        row=None,
        events=events,
    )

    monkeypatch.setattr(
        repository,
        "validate_readonly_identity",
        lambda candidate: events.append("identity"),
    )

    result = has_explicit_permission_readonly(
        user={"email": "persona@example.com"},
        permission="CONEXIONES_VER",
        connection_factory=lambda: connection,
    )

    assert result is False
    assert connection.closed is True
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    "invalid_user",
    [
        None,
        {},
        {"email": ""},
    ],
)
def test_rejects_missing_authenticated_email_before_opening(
    invalid_user: Any,
) -> None:
    calls: list[str] = []

    with pytest.raises(AuthenticatedEmailRequired):
        has_explicit_permission_readonly(
            user=invalid_user,
            permission="CONEXIONES_VER",
            connection_factory=lambda: calls.append(
                "open"
            ),
        )

    assert calls == []


@pytest.mark.parametrize(
    "invalid_permission",
    [
        None,
        "",
        "   ",
    ],
)
def test_rejects_missing_permission_before_opening(
    invalid_permission: Any,
) -> None:
    calls: list[str] = []

    with pytest.raises(PermissionCodeRequired):
        has_explicit_permission_readonly(
            user={"email": "persona@example.com"},
            permission=invalid_permission,
            connection_factory=lambda: calls.append(
                "open"
            ),
        )

    assert calls == []


@pytest.mark.parametrize(
    "invalid_factory",
    [
        object(),
        "",
        False,
        0,
    ],
)
def test_requires_callable_connection_factory(
    invalid_factory: Any,
) -> None:
    with pytest.raises(
        InvalidPermissionConnectionFactory,
        match="connection_factory debe ser invocable",
    ):
        has_explicit_permission_readonly(
            user={"email": "persona@example.com"},
            permission="CONEXIONES_VER",
            connection_factory=invalid_factory,
        )


def test_aborts_when_factory_returns_none() -> None:
    with pytest.raises(PermissionConnectionNotCreated):
        has_explicit_permission_readonly(
            user={"email": "persona@example.com"},
            permission="CONEXIONES_VER",
            connection_factory=lambda: None,
        )


def test_uses_parameters_without_interpolating_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    connection = FakeConnection(
        row=(1,),
        events=events,
    )

    monkeypatch.setattr(
        repository,
        "validate_readonly_identity",
        lambda candidate: None,
    )

    hostile_email = (
        "x@example.com'; DROP TABLE dbo.Usuario_Catalogo;--"
    )
    hostile_permission = (
        "CONEXIONES_VER'; DELETE FROM dbo.Usuario_Roles;--"
    )

    assert has_explicit_permission_readonly(
        user={"email": hostile_email},
        permission=hostile_permission,
        connection_factory=lambda: connection,
    )

    sql, params = (
        connection.cursor_instance.executions[0]
    )

    assert hostile_email not in sql
    assert hostile_permission not in sql
    assert params == (
        hostile_email,
        hostile_permission,
        hostile_permission,
    )


def test_closes_connection_when_identity_validation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    connection = FakeConnection(
        row=(1,),
        events=events,
    )

    def reject_identity(candidate: Any) -> None:
        events.append("identity")
        raise RuntimeError("identidad inválida")

    monkeypatch.setattr(
        repository,
        "validate_readonly_identity",
        reject_identity,
    )

    with pytest.raises(
        RuntimeError,
        match="identidad inválida",
    ):
        has_explicit_permission_readonly(
            user={"email": "persona@example.com"},
            permission="CONEXIONES_VER",
            connection_factory=lambda: connection,
        )

    assert connection.closed is True
    assert "cursor" not in events
    assert "permission_query" not in events


def test_production_module_has_no_legacy_dependencies() -> None:
    path = Path(repository.__file__)
    source = path.read_text(encoding="utf-8")
    lowered = source.casefold()

    forbidden_tokens = (
        "pymssql",
        "pyodbc",
        "pymongo",
        "motor",
        "mongodb",
        "mongodb_id",
        "load_dotenv",
        "os.getenv",
        "get_sql_connection",
        "repository_sql",
        "rbac.middleware",
        "server_registry",
        "context_resolver",
        "user_access_context",
        "password",
        "api_key",
        "decrypt",
    )

    for token in forbidden_tokens:
        assert token not in lowered

    forbidden_sql = (
        " update ",
        " insert ",
        " delete ",
        " merge ",
        " exec ",
        " execute ",
        " commit ",
        " rollback ",
    )

    normalized_sql = (
        " "
        + " ".join(
            EXPLICIT_PERMISSION_SQL
            .casefold()
            .split()
        )
        + " "
    )

    for token in forbidden_sql:
        assert token not in normalized_sql

    assert normalized_sql.count(" select ") == 1
    assert "%s" in EXPLICIT_PERMISSION_SQL
