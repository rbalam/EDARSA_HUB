#!/usr/bin/env python3
"""Low-priority 2026 Commercial history orchestrator.

Business sync logic remains in resync_comercial_range_worker.py. This file only
orchestrates blocks, the canonical SQL lock, checkpointing, retries and audit.
"""
from __future__ import annotations

import argparse
import asyncio
import calendar
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from core.scheduler.locks import get_lock_manager
from core.sql_first.db import get_sql_connection

LOCK_NAME = "sync_comercial_v2"
UNITS = ("ESTELAR", "CIENFUEGOS", "130MID", "ORIGEN", "130QRO")
ENTRYPOINT = Path(__file__).with_name("resync_comercial_range_worker.py")
STATE_FILE = Path("/var/lib/edarsahub-bootstrap/comercial-history-2026/state.json")
LOG_FILE = Path("/var/log/edarsahub/comercial-history-2026.log")
TRANSIENT = ("POS_TIMEOUT", "POS_CONNECTION_UNAVAILABLE", "DEADLOCK", "CONNECTION RESET", "TIMEOUT")


@dataclass(frozen=True)
class Block:
    start: date
    end: date

    @property
    def key(self) -> str:
        return f"{self.start.isoformat()}..{self.end.isoformat()}"


def plan_2026() -> list[Block]:
    blocks = [
        Block(date(2026, 9, 11), date(2026, 9, 15)),
        Block(date(2026, 9, 16), date(2026, 9, 20)),
        Block(date(2026, 9, 21), date(2026, 9, 25)),
        Block(date(2026, 9, 26), date(2026, 9, 30)),
    ]
    for month in range(8, 0, -1):
        last = calendar.monthrange(2026, month)[1]
        month_blocks = []
        day = 1
        while day <= last:
            end = last if day == 26 else min(day + 4, last)
            month_blocks.append(Block(date(2026, month, day), date(2026, month, end)))
            day = end + 1
        blocks.extend(reversed(month_blocks))
    return blocks


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(event: str, **data: Any) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts_utc": now(), "event": event, **data}, ensure_ascii=False, default=str) + "\n")


def save(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(tmp, STATE_FILE)


def load(expected_sha: str) -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {
            "schema": "edarsahub.comercial-history-2026.state.v1",
            "code_sha": expected_sha,
            "next_block_index": 0,
            "blocks": {},
            "pending_failures": [],
            "manual_audit_required": [],
            "updated_at_utc": now(),
        }
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if state.get("schema") != "edarsahub.comercial-history-2026.state.v1":
        raise RuntimeError("STATE_SCHEMA_INVALID")
    if state.get("code_sha") != expected_sha:
        raise RuntimeError("STATE_CODE_SHA_MISMATCH")
    return state


def assert_fixed_sha(expected_sha: str) -> None:
    root = Path(__file__).resolve().parents[2]
    cp = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    actual = cp.stdout.strip()
    if cp.returncode != 0 or actual != expected_sha:
        raise RuntimeError(f"HISTORY_WORKTREE_SHA_MISMATCH expected={expected_sha} actual={actual}")


def parse_summary(text: str) -> dict[str, Any]:
    for line in reversed(text.splitlines()):
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("event") == "comercial_range_summary":
            return row
    return {}


async def sync_once(unit: str, block: Block, timeout: int) -> dict[str, Any]:
    cmd = [
        sys.executable, str(ENTRYPOINT),
        "--unidad", unit,
        "--fecha-inicio", block.start.isoformat(),
        "--fecha-fin", block.end.isoformat(),
        "--commit",
    ]

    def _run():
        return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)

    started = time.monotonic()
    try:
        cp = await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "transient": True, "error": f"POS_TIMEOUT:{exc}"}

    summary = parse_summary(cp.stdout)
    ok = cp.returncode == 0 and bool(summary.get("success")) and bool(summary.get("header_success")) and bool(summary.get("detail_success"))
    combined = (cp.stdout + "\n" + cp.stderr).upper()
    return {
        "ok": ok,
        "transient": any(x in combined for x in TRANSIENT),
        "returncode": cp.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "summary": summary,
        "stderr_tail": cp.stderr[-1500:],
    }


async def sync_with_retries(unit: str, block: Block, args) -> dict[str, Any]:
    attempts = []
    for attempt in range(1, args.max_attempts + 1):
        result = await sync_once(unit, block, args.unit_timeout_seconds)
        result["attempt"] = attempt
        attempts.append(result)
        log("UNIT_ATTEMPT", block=block.key, unit=unit, **result)
        if result["ok"]:
            return {"status": "PASS", "attempts": attempts}
        if not result["transient"] or attempt == args.max_attempts:
            break
        await asyncio.sleep(args.retry_delay_seconds)
    return {"status": "PENDING_RECOVERY", "attempts": attempts}


def audit(unit: str, block: Block) -> dict[str, Any]:
    sql = """
    SELECT COUNT(*) filas,
           COUNT(DISTINCT fecha_operacion) dias,
           COUNT(DISTINCT numero_ticket) tickets,
           SUM(CASE WHEN producto_codigo_fuente NOT LIKE '__ISCAM_AJUSTE_%' THEN 1 ELSE 0 END) lineas_reales,
           SUM(CASE WHEN producto_codigo_fuente NOT LIKE '__ISCAM_AJUSTE_%'
                     AND NULLIF(LTRIM(RTRIM(vendedor_nombre)),'') IS NOT NULL THEN 1 ELSE 0 END) lineas_con_vendedor,
           SUM(CASE WHEN producto_codigo_fuente NOT LIKE '__ISCAM_AJUSTE_%'
                     AND descuento_pct IS NOT NULL THEN 1 ELSE 0 END) lineas_con_descuento_pct,
           SUM(CASE WHEN producto_codigo_fuente NOT LIKE '__ISCAM_AJUSTE_%'
                     AND ISNULL(descuento,0) > 0.0001 THEN 1 ELSE 0 END) lineas_con_descuento_positivo,
           CAST(SUM(CASE WHEN producto_codigo_fuente NOT LIKE '__ISCAM_AJUSTE_%'
                         THEN ISNULL(descuento,0) ELSE 0 END) AS decimal(18,2)) descuento_producto_total,
           MAX(UPPER(LTRIM(RTRIM(ISNULL(sistema_origen,''))))) sistema_origen
    FROM dbo.Comercial_Inteligencia_VentasDetalleProducto WITH (NOLOCK)
    WHERE unidad_negocio_id=%s AND fecha_operacion >= %s AND fecha_operacion <= %s
      AND ISNULL(activo,1)=1
    """
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute(sql, (unit, block.start, block.end))
        row = dict(cur.fetchone() or {})
    finally:
        cur.close()
        conn.close()
    passed = int(row.get("filas") or 0) > 0 and int(row.get("tickets") or 0) > 0
    real = int(row.get("lineas_reales") or 0)
    if str(row.get("sistema_origen") or "").upper() == "SOFTRESTAURANT" and real:
        passed = passed and int(row.get("lineas_con_vendedor") or 0) == real
        passed = passed and int(row.get("lineas_con_descuento_pct") or 0) == real
    row["pass"] = bool(passed)
    return row


def must_defer(unit: str, block: Block) -> str | None:
    if unit == "130QRO" and block.start.month == 6:
        return "130QRO_JUNE_2026_REQUIRES_ISOLATED_AUDIT_KNOWN_17_DAY_DIFFERENCE"
    return None


async def process_block(block: Block, state: dict[str, Any], args) -> str:
    lock = get_lock_manager().get_lock(LOCK_NAME)
    if not await lock.acquire(timeout_seconds=600):
        log("LOCK_BUSY", block=block.key)
        return "LOCK_BUSY"
    heartbeat = False
    try:
        await lock.start_heartbeat_loop(interval_seconds=30, extend_seconds=600)
        heartbeat = True
        log("BLOCK_START", block=block.key)
        slot = state["blocks"].setdefault(block.key, {"units": {}, "status": "RUNNING"})
        for unit in UNITS:
            if slot["units"].get(unit, {}).get("status") in {"PASS", "DEFERRED_MANUAL_AUDIT", "PENDING_RECOVERY"}:
                continue
            reason = must_defer(unit, block)
            if reason:
                slot["units"][unit] = {"status": "DEFERRED_MANUAL_AUDIT", "reason": reason}
                state["manual_audit_required"].append({"block": block.key, "unit": unit, "reason": reason})
                save(state)
                log("UNIT_DEFERRED", block=block.key, unit=unit, reason=reason)
                continue
            result = await sync_with_retries(unit, block, args)
            try:
                sql_audit = audit(unit, block)
            except Exception as exc:
                sql_audit = {"pass": False, "error": str(exc)}
            status = "PASS" if result["status"] == "PASS" and sql_audit.get("pass") else "PENDING_RECOVERY"
            slot["units"][unit] = {"status": status, "result": result, "audit": sql_audit}
            if status == "PENDING_RECOVERY":
                state["pending_failures"].append({"block": block.key, "unit": unit, "result": result, "audit": sql_audit})
            state["updated_at_utc"] = now()
            save(state)
            log("UNIT_COMPLETE", block=block.key, unit=unit, status=status, audit=sql_audit)
        statuses = {u: slot["units"].get(u, {}).get("status", "MISSING") for u in UNITS}
        if "PENDING_RECOVERY" in statuses.values():
            final = "COMPLETE_WITH_PENDING_RECOVERY"
        elif "DEFERRED_MANUAL_AUDIT" in statuses.values():
            final = "COMPLETE_WITH_MANUAL_AUDIT"
        else:
            final = "PASS"
        slot["status"] = final
        slot["unit_statuses"] = statuses
        slot["completed_at_utc"] = now()
        log("BLOCK_COMPLETE", block=block.key, status=final, unit_statuses=statuses)
        save(state)
        return final
    finally:
        if heartbeat:
            await lock.stop_heartbeat_loop()
        await lock.release()


async def run(args) -> int:
    assert_fixed_sha(args.expected_sha)
    if not ENTRYPOINT.exists():
        raise RuntimeError("CERTIFIED_ENTRYPOINT_MISSING")
    state = load(args.expected_sha)
    plan = plan_2026()
    while state["next_block_index"] < len(plan):
        assert_fixed_sha(args.expected_sha)
        idx = state["next_block_index"]
        status = await process_block(plan[idx], state, args)
        if status == "LOCK_BUSY":
            if args.once:
                return 10
            await asyncio.sleep(args.lock_retry_seconds)
            continue
        state["next_block_index"] = idx + 1
        state["updated_at_utc"] = now()
        save(state)
        if args.once:
            return 0
        await asyncio.sleep(args.yield_seconds)
    log("HISTORY_COMPLETE", pending=len(state["pending_failures"]), manual=len(state["manual_audit_required"]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--max-attempts", type=int, default=3, choices=(1, 2, 3))
    parser.add_argument("--unit-timeout-seconds", type=int, default=3600)
    parser.add_argument("--retry-delay-seconds", type=int, default=30)
    parser.add_argument("--lock-retry-seconds", type=int, default=120)
    parser.add_argument("--yield-seconds", type=int, default=120)
    args = parser.parse_args()
    try:
        return asyncio.run(run(args))
    except Exception as exc:
        log("FATAL", error=str(exc))
        print(f"COMERCIAL_HISTORY_2026_FATAL={exc}", file=sys.stderr)
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
