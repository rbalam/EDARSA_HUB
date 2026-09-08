from core.scheduler.job_logger import _is_success_status


def test_success_statuses_are_true():
    for value in ('success', 'SUCCESS', 'completed', 'COMPLETED', 'completado', 'COMPLETADO', 'ok', 'OK'):
        assert _is_success_status(value) is True


def test_failed_and_partial_statuses_are_false():
    for value in ('failed', 'FAILED', 'fallido', 'FALLIDO', 'partial', 'PARCIAL', 'error', None, ''):
        assert _is_success_status(value) is False
