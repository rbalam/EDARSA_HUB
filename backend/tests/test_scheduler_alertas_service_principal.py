from pathlib import Path

import pytest

import core.auth.sql_user_identity as identity


class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows
        self.executed = None

    def execute(self, sql, params):
        self.executed = (sql, params)

    def fetchall(self):
        return self._rows


class _FakeConnection:
    def __init__(self, rows):
        self.cursor_obj = _FakeCursor(rows)

    def cursor(self):
        return self.cursor_obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_system_principal_resolves_unique_noninteractive_user(monkeypatch):
    conn = _FakeConnection([(27,)])

    monkeypatch.setattr(
        identity,
        "get_sql_connection",
        lambda: conn,
    )

    result = identity.resolve_system_principal_current_user(
        "SYS-SCHED-ALERTAS"
    )

    assert result == {
        "UsuarioID": 27,
        "CodigoUsuario": "SYS-SCHED-ALERTAS",
    }

    sql, params = conn.cursor_obj.executed

    assert "EsUsuarioPortal" in sql
    assert "Bloqueado" in sql
    assert "Activo" in sql
    assert params == ("SYS-SCHED-ALERTAS",)


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [(27,), (28,)],
    ],
)
def test_system_principal_fails_closed_when_not_unique(
    monkeypatch,
    rows,
):
    monkeypatch.setattr(
        identity,
        "get_sql_connection",
        lambda: _FakeConnection(rows),
    )

    with pytest.raises(
        identity.SystemPrincipalResolutionError
    ):
        identity.resolve_system_principal_current_user(
            "SYS-SCHED-ALERTAS"
        )


def test_alertas_scheduler_uses_canonical_code(monkeypatch):
    captured = {}

    def fake_resolver(code):
        captured["code"] = code
        return {
            "UsuarioID": 999,
            "CodigoUsuario": code,
        }

    monkeypatch.setattr(
        identity,
        "resolve_system_principal_current_user",
        fake_resolver,
    )

    result = identity.resolve_alertas_scheduler_current_user()

    assert captured["code"] == (
        identity.ALERTAS_SCHEDULER_PRINCIPAL_CODE
    )
    assert result["UsuarioID"] == 999


def test_scheduler_jobs_do_not_call_fastapi_route_or_empty_user():
    root = Path("/app/backend/core/scheduler/jobs")

    paths = (
        root / "alertas_excepciones_job.py",
        root / "resumen_diario_excepciones_job.py",
    )

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in paths
    )

    assert "current_user={}" not in combined

    assert (
        "modules.alertas_estrategicas.routes "
        "import resumen_alertas"
        not in combined
    )

    assert (
        "modules.alertas_estrategicas.service "
        "import obtener_resumen_alertas"
        in combined
    )

    assert (
        "resolve_alertas_scheduler_current_user"
        in combined
    )

    assert "UsuarioID=27" not in combined
    assert '"UsuarioID": 27' not in combined
