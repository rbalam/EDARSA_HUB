import asyncio

from core.scheduler.scheduler_manager import SchedulerManager


def _manager_with_sync_result(result):
    manager = object.__new__(SchedulerManager)

    async def _fake_sync():
        return result

    manager._run_sync_compras_job = _fake_sync
    return manager


def test_run_job_now_sync_compras_propagates_disabled_status():
    manager = _manager_with_sync_result(
        {
            "status": "DISABLED",
            "reason": "execution_guard",
        }
    )

    result = asyncio.run(manager.run_job_now("sync_compras"))

    assert result == {
        "job_id": "sync_compras",
        "status": "DISABLED",
        "reason": "execution_guard",
    }


def test_run_job_now_sync_compras_propagates_success_payload():
    manager = _manager_with_sync_result(
        {
            "status": "COMPLETED",
            "total_processed": 42,
            "total_errors": 0,
        }
    )

    result = asyncio.run(manager.run_job_now("sync_compras"))

    assert result["job_id"] == "sync_compras"
    assert result["status"] == "COMPLETED"
    assert result["total_processed"] == 42
    assert result["total_errors"] == 0


def test_sync_compras_lock_uses_writer_profile(monkeypatch):
    from core.scheduler.jobs import sync_compras_job

    calls = []

    class FakeCursor:
        rowcount = 0

        def execute(self, query, params=None):
            calls.append(("execute", query, params))

        def fetchone(self):
            return None

        def close(self):
            pass

    class FakeConnection:
        def __init__(self):
            self.cursor_obj = FakeCursor()

        def cursor(self, as_dict=False):
            return self.cursor_obj

        def commit(self):
            calls.append(("commit",))

        def rollback(self):
            calls.append(("rollback",))

        def close(self):
            pass

    def fake_connection(*, timeout, login_timeout, profile="default", **kwargs):
        calls.append(("profile", profile))
        return FakeConnection()

    monkeypatch.setattr(
        sync_compras_job,
        "get_edarsahub_pymssql_connection",
        fake_connection,
    )
    monkeypatch.setattr(
        sync_compras_job,
        "enrich_sync_start",
        lambda *args, **kwargs: None,
    )

    assert sync_compras_job._acquire_sync_lock("TEST-RUN") is True
    assert ("profile", "writer") in calls


def test_inventory_query_timeout_is_dedicated(monkeypatch):
    from core.scheduler.jobs import sync_compras_job

    monkeypatch.setenv(
        "SYNC_INVENTARIOS_FISICOS_QUERY_TIMEOUT_SECONDS",
        "150",
    )

    calls = []

    def fake_execute(
        host,
        port,
        database,
        username,
        password,
        query,
        timeout_seconds=45,
    ):
        calls.append(timeout_seconds)
        return []

    monkeypatch.setattr(
        sync_compras_job,
        "_execute_sql_with_timeout",
        fake_execute,
    )

    result = sync_compras_job._execute_inventory_sql_with_timeout(
        "host",
        1433,
        "db",
        "user",
        "password",
        "SELECT 1",
    )

    assert result == []
    assert calls == [150]


def test_sync_compras_lock_timeout_default_covers_long_execution(monkeypatch):
    from core.scheduler.jobs import sync_compras_job

    monkeypatch.delenv(
        "SCHEDULER_SYNC_COMPRAS_LOCK_TIMEOUT_MINUTES",
        raising=False,
    )

    assert sync_compras_job._sync_compras_lock_timeout_minutes() >= 90


def test_extended_sync_steps_can_be_disabled(monkeypatch):
    from core.scheduler.jobs import sync_compras_job

    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMPRAS_EXTENDED_ENABLED",
        "false",
    )

    assert sync_compras_job._extended_sync_steps() == []


def test_extended_sync_steps_default_preserves_compatibility(monkeypatch):
    from core.scheduler.jobs import sync_compras_job

    monkeypatch.delenv(
        "SCHEDULER_SYNC_COMPRAS_EXTENDED_ENABLED",
        raising=False,
    )

    steps = sync_compras_job._extended_sync_steps()

    assert [name for name, _, _ in steps] == [
        "almacenes",
        "existencias",
        "movimientos",
        "pedidos",
        "ordenes",
        "recepciones",
    ]


def test_extended_sync_steps_default_disabled_in_preview(monkeypatch):
    from core.scheduler.jobs import sync_compras_job

    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.delenv(
        "SCHEDULER_SYNC_COMPRAS_EXTENDED_ENABLED",
        raising=False,
    )

    assert sync_compras_job._extended_sync_steps() == []


def test_extended_sync_steps_can_be_explicitly_enabled_in_preview(monkeypatch):
    from core.scheduler.jobs import sync_compras_job

    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.setenv(
        "SCHEDULER_SYNC_COMPRAS_EXTENDED_ENABLED",
        "true",
    )

    assert len(sync_compras_job._extended_sync_steps()) == 6
