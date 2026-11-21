from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOB = ROOT / "core/scheduler/jobs/sync_comercial_v2_job.py"
MANAGER = ROOT / "core/scheduler/scheduler_manager.py"

def test_closed_sales_headers_are_completed_before_enrichment():
    text = JOB.read_text(encoding="utf-8")
    assert "post_header_queue = []" in text
    assert text.count("post_header_queue.append((") == 2
    marker = "# FASE P1: ENRIQUECER PAGOS Y DETALLE DESPUES DE TODOS LOS HEADERS"
    assert marker in text
    phase = text.split(marker, 1)[1]
    assert "_sync_pagos_post_header(" in phase
    assert "_sync_detalle_post_header(" in phase

def test_automatic_closed_sales_lock_has_heartbeat():
    text = MANAGER.read_text(encoding="utf-8")
    start = text.index("async def _run_sync_comercial_v2_job")
    end = text.index("async def _run_sync_comercial_abiertas_v2_job")
    block = text[start:end]
    assert "await lock.start_heartbeat_loop(" in block
    assert "interval_seconds=30" in block
    assert "extend_seconds=600" in block
