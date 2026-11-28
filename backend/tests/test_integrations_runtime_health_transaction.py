from modules.integrations_runtime import health


class FakeCursor:
    def __init__(self, row=None):
        self.row = row
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row=None):
        self.cursor_obj = FakeCursor(row=row)
        self.commit_calls = 0
        self.rollback_calls = 0
        self.close_calls = 0

    def cursor(self, as_dict=False):
        return self.cursor_obj

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1

    def close(self):
        self.close_calls += 1


def test_health_persistence_uses_single_driver_owned_transaction(monkeypatch):
    conn = FakeConnection(row=None)

    monkeypatch.setattr(
        health,
        "open_validated_writer_connection",
        lambda: (conn, object()),
    )

    health.persist_connection_health(
        "00000000-0000-4000-8000-000000000641",
        success=True,
        latency_ms=1,
    )

    sql = "\n".join(call[0] for call in conn.cursor_obj.calls)

    assert "SET XACT_ABORT ON" in sql
    assert "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE" in sql
    assert "BEGIN TRANSACTION" not in sql
    assert "INSERT INTO dbo.Servidores_ConexionEstado" in sql
    assert conn.commit_calls == 1
    assert conn.rollback_calls == 0
    assert conn.close_calls == 1


def test_health_persistence_rolls_back_on_failure(monkeypatch):
    conn = FakeConnection(row=None)

    def failing_execute(sql, params=None):
        conn.cursor_obj.calls.append((sql, params))
        if "INSERT INTO dbo.Servidores_ConexionEstado" in sql:
            raise RuntimeError("simulated insert failure")

    conn.cursor_obj.execute = failing_execute

    monkeypatch.setattr(
        health,
        "open_validated_writer_connection",
        lambda: (conn, object()),
    )

    try:
        health.persist_connection_health(
            "00000000-0000-4000-8000-000000000642",
            success=True,
            latency_ms=1,
        )
    except RuntimeError as exc:
        assert "simulated insert failure" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")

    assert conn.commit_calls == 0
    assert conn.rollback_calls == 1
    assert conn.close_calls == 1
