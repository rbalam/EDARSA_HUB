import asyncio

from core.scheduler.job_logger import JobExecutionLog, JobLogger


def _capture_finish_status(status):
    logger = JobLogger()
    captured = []

    def fake_insert_bitacora(**kwargs):
        captured.append(kwargs)

    logger._insert_bitacora = fake_insert_bitacora

    log_entry = JobExecutionLog(
        job_name="test_status_semantics",
        started_at="2026-08-09T00:00:00+00:00",
        status="running",
    )

    asyncio.run(
        logger.finish_execution(
            log_entry=log_entry,
            status=status,
        )
    )

    assert len(captured) == 1
    return captured[0]


def test_success_is_successful():
    row = _capture_finish_status("success")
    assert row["exito"] is True


def test_completed_is_successful():
    row = _capture_finish_status("completed")
    assert row["exito"] is True


def test_partial_is_not_full_success():
    row = _capture_finish_status("partial")
    assert row["exito"] is False


def test_failed_is_not_successful():
    row = _capture_finish_status("failed")
    assert row["exito"] is False
