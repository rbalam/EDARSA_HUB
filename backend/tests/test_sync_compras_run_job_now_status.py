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
