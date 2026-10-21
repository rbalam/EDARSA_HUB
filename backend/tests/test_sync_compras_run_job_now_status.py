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
