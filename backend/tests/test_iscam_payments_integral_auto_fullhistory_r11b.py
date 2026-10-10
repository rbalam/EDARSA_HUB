from pathlib import Path

from core.scheduler.jobs.sync_comercial_v2_job import _resolve_estatus_general
from scripts.resync_iscam_pagos_unidad import _daily_windows

ROOT = Path(__file__).resolve().parents[2]
JOB = ROOT / "backend/core/scheduler/jobs/sync_comercial_v2_job.py"
MPRO = ROOT / "backend/scripts/resync_mpro_full_history.py"


def test_large_payment_range_is_chunked_daily():
    windows = list(_daily_windows("2026-08-01", "2026-09-01"))
    assert len(windows) == 31
    assert windows[0] == ("2026-08-01", "2026-08-02")
    assert windows[-1] == ("2026-08-31", "2026-09-01")


def test_payment_failures_prevent_completed_scheduler_status():
    assert _resolve_estatus_general({
        "unidades_fallidas": 0,
        "unidades_exitosas": 5,
        "detalle_producto_fallidos": 0,
        "pagos_iscam_fallidos": 1,
    }) == "PARCIAL"


def test_clean_scheduler_with_payments_is_completed():
    assert _resolve_estatus_general({
        "unidades_fallidas": 0,
        "unidades_exitosas": 5,
        "detalle_producto_fallidos": 0,
        "pagos_iscam_fallidos": 0,
    }) == "COMPLETADO"


def test_incremental_scheduler_syncs_payments_for_both_pos_families():
    text = JOB.read_text(encoding="utf-8")
    assert "def _sync_pagos_post_header" in text
    assert text.count("_sync_pagos_post_header(") == 3
    assert "resync_pagos_unidad" in text


def test_mpro_full_history_discovers_payment_bounds_and_backfills_daily():
    text = MPRO.read_text(encoding="utf-8")
    assert "def _payment_bounds" in text
    assert "FROM Venta_Encabezado" in text
    assert "resync_pagos_unidad(" in text
    assert "payment_windows" in text
