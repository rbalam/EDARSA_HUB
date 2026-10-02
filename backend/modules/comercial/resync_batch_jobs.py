"""Persistent multi-unit Commercial range resync jobs."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.scheduler.locks import get_lock_manager
from core.sql_first.db import get_sql_connection

JOB_TYPE = "comercial_range_batch"
LOCK_NAME = "sync_comercial_v2"
ACTIVE = ("JOB_QUEUED", "JOB_RUNNING", "JOB_WAITING_LOCK", "JOB_CANCEL_REQUESTED")
RESUMABLE = ("JOB_PARTIAL", "JOB_FAILED", "JOB_STALE", "JOB_CANCELLED")
BLOCK_DAYS = 5
MAX_ATTEMPTS = 3
STALE_SECONDS = 7200
DRY_TIMEOUT_SECONDS = int(os.environ.get("COMERCIAL_RANGE_DRY_TIMEOUT_SECONDS", "300"))
REAL_TIMEOUT_SECONDS = int(os.environ.get("COMERCIAL_RANGE_REAL_TIMEOUT_SECONDS", "900"))
POLL_SECONDS = 5
ENTRYPOINT = Path(__file__).resolve().parents[2] / "scripts" / "resync_comercial_range_worker.py"
TRANSIENT_MARKERS = ("TIMEOUT", "TIMED OUT", "DEADLOCK", "CONNECTION", "API_LOCAL_ERROR", "POS_")

def _now():
    return datetime.now(timezone.utc).isoformat()

def _blocks(start: date, end: date) -> List[Tuple[date, date]]:
    result = []
    cursor = start
    while cursor <= end:
        block_end = min(cursor + timedelta(days=BLOCK_DAYS - 1), end)
        result.append((cursor, block_end))
        cursor = block_end + timedelta(days=1)
    return result

def _key(unit: str, start: date, end: date) -> str:
    return f"{unit}|{start.isoformat()}|{end.isoformat()}"

def _read(job_id: int) -> Optional[Dict[str, Any]]:
    conn = get_sql_connection(); cur = conn.cursor(as_dict=True)
    try:
        cur.execute("""SELECT TOP 1 ResyncLogID, Estado, Mensaje, Payload
                       FROM dbo.Sistema_Sync_ResyncLog
                       WHERE ResyncLogID=%s AND TipoSync=%s""", (job_id, JOB_TYPE))
        row = cur.fetchone()
        if not row: return None
        payload = json.loads(row.get("Payload") or "{}")
        payload["job_id"] = int(row["ResyncLogID"])
        payload["status"] = row.get("Estado")
        payload["message"] = row.get("Mensaje")
        return payload
    finally:
        cur.close(); conn.close()

def _recount(payload: Dict[str, Any]) -> None:
    steps = payload.get("steps") or {}
    values = list(steps.values())
    ok = sum(1 for x in values if x.get("status") == "PASS")
    pending = sum(1 for x in values if x.get("status") == "PENDING_RECOVERY")
    total = int(payload.get("total_steps") or len(values))
    payload["successful_steps"] = ok
    payload["failed_steps"] = pending
    payload["completed_steps"] = ok + pending
    payload["percent_complete"] = round(((ok + pending) * 100.0 / total), 1) if total else 0.0
    progress = {}
    for unit in payload.get("units") or []:
        rows = [x for x in values if x.get("unit") == unit]
        progress[unit] = {
            "total": len(rows),
            "pass": sum(1 for x in rows if x.get("status") == "PASS"),
            "pending_recovery": sum(1 for x in rows if x.get("status") == "PENDING_RECOVERY"),
        }
    payload["unit_progress"] = progress

def _write(job_id: int, payload: Dict[str, Any], status: str, message: str) -> None:
    payload = dict(payload)
    payload["status"] = status
    payload["message"] = message
    payload["updated_at_utc"] = _now()
    _recount(payload)
    conn = get_sql_connection(); cur = conn.cursor()
    try:
        cur.execute("""UPDATE dbo.Sistema_Sync_ResyncLog
                       SET Estado=%s, Mensaje=%s, Payload=%s, RegistrosAfectados=%s
                       WHERE ResyncLogID=%s AND TipoSync=%s""",
                    (status, message[:1990], json.dumps(payload, default=str, ensure_ascii=False),
                     int(payload.get("successful_steps") or 0), job_id, JOB_TYPE))
        conn.commit()
    finally:
        cur.close(); conn.close()

def _compact(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "success": bool(result.get("success")),
        "header_success": bool(result.get("header_success", result.get("success"))),
        "detail_success": bool(result.get("detail_success", False)),
        "payments_success": result.get("payments_success"),
        "records_processed": int(result.get("records_processed") or 0),
        "records_inserted": int(result.get("records_inserted") or 0),
        "records_updated": int(result.get("records_updated") or 0),
        "warning_message": str(result.get("warning_message") or "")[:500],
        "error_message": str(result.get("error_message") or "")[:500],
    }

def _transient(result: Dict[str, Any]) -> bool:
    text = json.dumps(result, default=str, ensure_ascii=False).upper()
    return any(x in text for x in TRANSIENT_MARKERS)


def _summary_from_stdout(stdout: str) -> Dict[str, Any]:
    for line in reversed((stdout or "").splitlines()):
        try:
            item = json.loads(line.strip())
        except Exception:
            continue
        if item.get("event") == "comercial_range_summary":
            return item
    return {}


async def _terminate_process(proc):
    if proc.returncode is not None:
        return
    proc.terminate()
    try:
        await asyncio.wait_for(proc.wait(), timeout=10)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()


async def _run_entrypoint(job_id: int, payload: Dict[str, Any], unit: str, start: date, end: date, commit: bool) -> Dict[str, Any]:
    timeout_seconds = REAL_TIMEOUT_SECONDS if commit else DRY_TIMEOUT_SECONDS
    args = [
        sys.executable, str(ENTRYPOINT),
        "--unidad", unit,
        "--fecha-inicio", start.isoformat(),
        "--fecha-fin", end.isoformat(),
    ]
    if commit:
        args.append("--commit")
    backend_dir = str(ENTRYPOINT.parents[1])
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    pythonpath = backend_dir if not current_pythonpath else backend_dir + os.pathsep + current_pythonpath
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=backend_dir,
        env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONPATH": pythonpath},
    )
    communicate_task = asyncio.create_task(proc.communicate())
    started = datetime.now(timezone.utc)
    while not communicate_task.done():
        if _cancel_requested(job_id):
            await _terminate_process(proc)
            output, _ = await communicate_task
            return {"success": False, "cancelled": True, "error_message": "CANCELLED_BY_USER"}
        elapsed = int((datetime.now(timezone.utc) - started).total_seconds())
        if elapsed >= timeout_seconds:
            await _terminate_process(proc)
            output, _ = await communicate_task
            return {"success": False, "timeout": True, "error_message": f"TIMEOUT_{timeout_seconds}_SECONDS"}
        latest = _read(job_id) or payload
        latest["current_phase"] = "REAL" if commit else "DRY_RUN"
        latest["phase_elapsed_seconds"] = elapsed
        latest["phase_timeout_seconds"] = timeout_seconds
        _write(
            job_id,
            latest,
            "JOB_RUNNING",
            f"{unit}: {'re-sincronizando' if commit else 'validando'} {start} a {end} - {elapsed}s.",
        )
        await asyncio.wait({communicate_task}, timeout=POLL_SECONDS)
    output, _ = await communicate_task
    text = output.decode("utf-8", errors="replace")
    summary = _summary_from_stdout(text)
    summary["returncode"] = proc.returncode
    summary["output_tail"] = text[-1200:]
    if proc.returncode != 0 and not summary.get("error_message"):
        summary["error_message"] = summary.get("error") or f"ENTRYPOINT_RC_{proc.returncode}"
    return summary


def create_job(units: List[str], fecha_inicio: date, fecha_fin: date, motivo: str, requested_by: str):
    normalized = []
    for raw in units:
        unit = str(raw or "").strip().upper()
        if unit and unit not in normalized:
            normalized.append(unit)
    steps = {}
    for start, end in _blocks(fecha_inicio, fecha_fin):
        for unit in normalized:
            steps[_key(unit, start, end)] = {
                "unit": unit, "fecha_inicio": start.isoformat(), "fecha_fin": end.isoformat(),
                "status": "PENDING", "attempts": 0
            }
    payload = {
        "schema": "edarsahub.comercial-range-batch.v1",
        "units": normalized,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "motivo": motivo,
        "force_refresh_existing": True,
        "execution_mode": "DRY_THEN_REAL_SERVER_SIDE",
        "chunk_days": BLOCK_DAYS,
        "max_attempts_per_step": MAX_ATTEMPTS,
        "total_steps": len(steps),
        "steps": steps,
        "current_unit": None,
        "current_block": None,
        "current_phase": "QUEUED",
        "created_at_utc": _now(),
        "updated_at_utc": _now(),
        "requested_by": requested_by,
    }
    _recount(payload)
    conn = get_sql_connection(); cur = conn.cursor(as_dict=True)
    try:
        cur.execute("""INSERT INTO dbo.Sistema_Sync_ResyncLog
                       (TipoSync, ServerID, UnidadCodigo, Estado, Mensaje, Payload, RegistrosAfectados, SolicitadoPor)
                       OUTPUT INSERTED.ResyncLogID AS job_id
                       VALUES (%s,NULL,%s,'JOB_QUEUED',%s,%s,0,%s)""",
                    (JOB_TYPE, ",".join(normalized), "Re-sincronización Comercial por rango en cola.",
                     json.dumps(payload, default=str, ensure_ascii=False), requested_by))
        row = cur.fetchone()
        payload["job_id"] = int(row["job_id"])
        conn.commit()
        return payload
    finally:
        cur.close(); conn.close()

def get_job(job_id: int):
    payload = _read(job_id)
    if not payload: return None
    if payload.get("status") in ACTIVE:
        raw = payload.get("updated_at_utc") or payload.get("created_at_utc")
        try:
            updated = datetime.fromisoformat(str(raw).replace("Z","+00:00"))
            if updated.tzinfo is None: updated = updated.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - updated).total_seconds()
        except Exception:
            age = STALE_SECONDS + 1
        if age > STALE_SECONDS:
            _write(job_id, payload, "JOB_STALE", "Trabajo sin avance reciente; puede reanudarse desde checkpoint.")
            payload = _read(job_id)
    return payload

def find_active():
    conn = get_sql_connection(); cur = conn.cursor(as_dict=True)
    try:
        cur.execute("""SELECT TOP 10 ResyncLogID FROM dbo.Sistema_Sync_ResyncLog
                       WHERE TipoSync=%s AND Estado IN ('JOB_QUEUED','JOB_RUNNING','JOB_WAITING_LOCK')
                       ORDER BY ResyncLogID DESC""", (JOB_TYPE,))
        ids = [int(x["ResyncLogID"]) for x in (cur.fetchall() or [])]
    finally:
        cur.close(); conn.close()
    for job_id in ids:
        payload = get_job(job_id)
        if payload and payload.get("status") in ACTIVE: return payload
    return None

def queue_resume(job_id: int):
    payload = get_job(job_id)
    if not payload: raise ValueError("Trabajo Comercial no encontrado")
    if payload.get("status") == "JOB_SUCCESS": return payload
    if payload.get("status") not in RESUMABLE:
        raise ValueError(f"No se puede reanudar desde {payload.get('status')}")
    payload["cancel_requested"] = False
    payload["cancel_requested_at_utc"] = None
    payload["cancelled_by"] = None
    payload["current_phase"] = "QUEUED_RESUME"
    _write(job_id, payload, "JOB_QUEUED", "Trabajo reanudado desde checkpoint.")
    return _read(job_id)


def request_cancel(job_id: int, requested_by: str):
    payload = get_job(job_id)
    if not payload:
        raise ValueError("Trabajo Comercial no encontrado")
    if payload.get("status") in ("JOB_SUCCESS", "JOB_CANCELLED"):
        return payload
    if payload.get("status") not in ACTIVE:
        raise ValueError(f"No se puede detener desde {payload.get('status')}")
    payload["cancel_requested"] = True
    payload["cancel_requested_at_utc"] = _now()
    payload["cancelled_by"] = requested_by
    payload["current_phase"] = "STOP_REQUESTED"
    _write(
        job_id,
        payload,
        "JOB_CANCEL_REQUESTED",
        "Detención segura solicitada. Se detendrá al finalizar la operación atómica actual.",
    )
    return _read(job_id)


def _cancel_requested(job_id: int) -> bool:
    current = _read(job_id)
    return bool(current and (
        current.get("cancel_requested")
        or current.get("status") == "JOB_CANCEL_REQUESTED"
    ))


def _finish_cancelled(job_id: int, payload: Dict[str, Any]):
    latest = _read(job_id) or payload
    latest["cancel_requested"] = True
    latest["current_unit"] = None
    latest["current_block"] = None
    latest["current_phase"] = "STOPPED_SAFE"
    _write(
        job_id,
        latest,
        "JOB_CANCELLED",
        "Proceso detenido de forma segura. El checkpoint fue conservado y puede reanudarse.",
    )
    return _read(job_id)


async def run_job(job_id: int):
    payload = get_job(job_id)
    if not payload or payload.get("status") == "JOB_SUCCESS": return
    from api.admin_scheduler_resync import _ejecutar_dry_run, _ejecutar_sync_real, _get_unidad_config
    try:
        if _cancel_requested(job_id):
            _finish_cancelled(job_id, payload)
            return
        _write(job_id, payload, "JOB_RUNNING", "Re-sincronización Comercial por rango iniciada.")
        payload = _read(job_id) or payload
        for start, end in _blocks(date.fromisoformat(payload["fecha_inicio"]), date.fromisoformat(payload["fecha_fin"])):
            for unit in payload.get("units") or []:
                if _cancel_requested(job_id):
                    _finish_cancelled(job_id, payload)
                    return
                key = _key(unit, start, end)
                step = payload["steps"][key]
                if step.get("status") == "PASS":
                    continue
                payload["current_unit"] = unit
                payload["current_block"] = f"{start.isoformat()} a {end.isoformat()}"
                payload["current_phase"] = "DRY_RUN"
                step["status"] = "RUNNING"
                _write(job_id, payload, "JOB_RUNNING", f"{unit}: validando {start} a {end}.")
                config = _get_unidad_config(unit)
                final_dry = {}; final_real = {}; passed = False
                if not config:
                    final_dry = {"success": False, "error_message": "UNIT_NOT_FOUND"}
                else:
                    for attempt in range(1, MAX_ATTEMPTS + 1):
                        step["attempts"] = attempt
                        dry = await _run_entrypoint(job_id, payload, unit, start, end, commit=False)
                        final_dry = _compact(dry)
                        if _cancel_requested(job_id):
                            _finish_cancelled(job_id, payload)
                            return
                        if not dry.get("success"):
                            if attempt < MAX_ATTEMPTS and _transient(dry):
                                await asyncio.sleep(30); continue
                            break
                        if _cancel_requested(job_id):
                            _finish_cancelled(job_id, payload)
                            return
                        lock = get_lock_manager().get_lock(LOCK_NAME)
                        if not await lock.acquire(timeout_seconds=600):
                            final_real = {"success": False, "error_message": "LOCK_BUSY"}
                            if attempt < MAX_ATTEMPTS:
                                await asyncio.sleep(30); continue
                            break
                        heartbeat = False
                        try:
                            await lock.start_heartbeat_loop(interval_seconds=30, extend_seconds=600)
                            heartbeat = True
                            payload["current_phase"] = "REAL"
                            _write(job_id, payload, "JOB_RUNNING", f"{unit}: re-sincronizando {start} a {end}.")
                            real = await _run_entrypoint(job_id, payload, unit, start, end, commit=True)
                            final_real = _compact(real)
                        finally:
                            if heartbeat: await lock.stop_heartbeat_loop()
                            await lock.release()
                        passed = bool(final_real.get("success")) and bool(final_real.get("header_success")) and bool(final_real.get("detail_success"))
                        if _cancel_requested(job_id):
                            step["status"] = "PASS" if passed else "PENDING_RECOVERY"
                            step["dry_run"] = final_dry
                            step["real"] = final_real
                            step["completed_at_utc"] = _now()
                            payload["steps"][key] = step
                            _finish_cancelled(job_id, payload)
                            return
                        if passed: break
                        if attempt < MAX_ATTEMPTS and _transient(final_real):
                            await asyncio.sleep(30); continue
                        break

                step["status"] = "PASS" if passed else "PENDING_RECOVERY"
                step["dry_run"] = final_dry
                step["real"] = final_real
                step["completed_at_utc"] = _now()
                step["error_message"] = None if passed else (final_real.get("error_message") or final_dry.get("error_message") or "STEP_NOT_CERTIFIED")
                payload["steps"][key] = step
                payload["current_phase"] = "CHECKPOINT"
                _write(job_id, payload, "JOB_RUNNING", f"{unit}: bloque {start} a {end} {'completado' if passed else 'pendiente de recuperación'}.")
                payload = _read(job_id) or payload

        payload["current_unit"] = None; payload["current_block"] = None; payload["current_phase"] = "DONE"
        _recount(payload)
        if payload.get("failed_steps"):
            _write(job_id, payload, "JOB_PARTIAL", f"Proceso terminado con {payload['failed_steps']} bloque(s) pendiente(s).")
        else:
            _write(job_id, payload, "JOB_SUCCESS", f"Proceso terminado: {payload['successful_steps']}/{payload['total_steps']} bloques.")
    except Exception as exc:
        payload["fatal_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
        _write(job_id, payload, "JOB_FAILED", "Trabajo detenido; puede reanudarse desde checkpoint.")
