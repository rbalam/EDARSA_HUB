#!/usr/bin/env python3
"""Closed Worker entrypoint for the official Comercial range resync."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import date

from api.admin_scheduler_resync import (
    _ejecutar_dry_run,
    _ejecutar_sync_real,
    _get_unidad_config,
)


def _safe_summary(result: dict, unit: str, fi: date, ff: date, committed: bool) -> dict:
    return {
        "event": "comercial_range_summary",
        "unidad": unit,
        "fecha_inicio": fi.isoformat(),
        "fecha_fin": ff.isoformat(),
        "committed": committed,
        "success": bool(result.get("success")),
        "stage": result.get("stage"),
        "header_success": bool(result.get("header_success", result.get("success"))),
        "detail_success": bool(result.get("detail_success", False)),
        "records_processed": int(result.get("records_processed") or 0),
        "records_inserted": int(result.get("records_inserted") or 0),
        "records_updated": int(result.get("records_updated") or 0),
        "records_skipped": int(result.get("records_skipped") or 0),
        "records_errored": int(result.get("records_errored") or 0),
        "warning": str(result.get("warning_message") or "")[:500],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unidad", required=True)
    parser.add_argument("--fecha-inicio", required=True)
    parser.add_argument("--fecha-fin", required=True)
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    unit = args.unidad.strip().upper()
    fi = date.fromisoformat(args.fecha_inicio)
    ff = date.fromisoformat(args.fecha_fin)
    days = (ff - fi).days + 1
    if days < 1 or days > 31:
        print(json.dumps({"event": "comercial_range_summary", "unidad": unit, "success": False, "error": "RANGE_INVALID"}))
        return 2

    config = _get_unidad_config(unit)
    if not config:
        print(json.dumps({"event": "comercial_range_summary", "unidad": unit, "success": False, "error": "UNIT_NOT_FOUND"}))
        return 3
    sistema = str(config.get("sistema") or "").strip().upper()
    if sistema not in {"SOFTRESTAURANT", "MPRO"}:
        print(json.dumps({
            "event": "comercial_range_summary",
            "unidad": unit,
            "success": False,
            "error": "SYSTEM_NOT_SUPPORTED",
            "system_type": sistema or "UNKNOWN",
        }))
        return 4

    if args.commit:
        run_id = f"WORKER-COMERCIAL-{unit}-{fi:%Y%m%d}-{ff:%Y%m%d}-{uuid.uuid4().hex[:8]}"
        result = asyncio.run(_ejecutar_sync_real(unit, config, fi, ff, run_id))
    else:
        result = asyncio.run(_ejecutar_dry_run(unit, config, fi, ff))

    summary = _safe_summary(result, unit, fi, ff, args.commit)
    print(json.dumps(summary, ensure_ascii=False, default=str))
    return 0 if summary["success"] and summary["header_success"] and summary["detail_success"] else 5


if __name__ == "__main__":
    sys.exit(main())
