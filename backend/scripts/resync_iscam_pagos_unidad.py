#!/usr/bin/env python3
"""Resincronizacion cerrada de Pagos por Ticket ISCAM.

Acepta un rango amplio, lo divide internamente en ventanas diarias y llama
resync_pagos_unidad para evitar timeouts. No toca Sync_Sales, Cuentas,
Comandas ni Cortes.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta

from core.scheduler.jobs.inteligencia_comercial_enrich import resync_pagos_unidad
from core.sql_first.db import fetch_all_dict


def _verify(unidad: str, fi: str, ff: str):
    rows = fetch_all_dict(
        "SELECT COUNT(*) AS filas, COUNT(DISTINCT NumeroTicket) AS tickets, "
        "CAST(ISNULL(SUM(Importe),0) AS decimal(18,2)) AS importe, "
        "CAST(ISNULL(SUM(Propina),0) AS decimal(18,2)) AS propina "
        "FROM dbo.Finanzas_CortesCaja_DetallePagos "
        "WHERE UnidadNegocio=%s AND FechaHora >= %s AND FechaHora < %s AND ISNULL(Activo,1)=1",
        (unidad, fi, ff),
    )
    return rows[0] if rows else {}


def _daily_windows(fi: str, ff: str):
    start = datetime.strptime(fi, "%Y-%m-%d")
    end = datetime.strptime(ff, "%Y-%m-%d")
    if end <= start:
        raise ValueError("fecha_fin debe ser mayor a fecha_inicio")
    current = start
    while current < end:
        nxt = min(current + timedelta(days=1), end)
        yield current.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")
        current = nxt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", required=True)
    parser.add_argument("--fi", required=True)
    parser.add_argument("--ff", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    unidad = args.unit.strip().upper()
    totals = {
        "unidad": unidad,
        "periodo": f"{args.fi}..{args.ff}",
        "dry_run": not args.execute,
        "dias": 0,
        "pagos_extraidos": 0,
        "pagos_insertados": 0,
        "pagos_eliminados": 0,
    }
    errors = []

    for fi, ff in _daily_windows(args.fi, args.ff):
        result = resync_pagos_unidad(
            unidad,
            fi,
            ff,
            dry_run=not args.execute,
        )
        totals["dias"] += 1
        totals["pagos_extraidos"] += int(result.get("pagos_extraidos") or 0)
        totals["pagos_insertados"] += int(result.get("pagos_insertados") or 0)
        totals["pagos_eliminados"] += int(result.get("pagos_eliminados") or 0)
        if result.get("sistema"):
            totals["sistema"] = result.get("sistema")

        print(json.dumps(
            {"event": "window", "fi": fi, "ff": ff, "result": result},
            ensure_ascii=False,
            default=str,
        ))

        if result.get("error"):
            errors.append({
                "fi": fi,
                "ff": ff,
                "error_type": str(result.get("error")).split(":", 1)[0][:80],
            })
            break

    if errors:
        totals["error"] = "daily_window_failed"
        totals["error_count"] = len(errors)

    print(json.dumps(
        {"event": "resync", "result": totals},
        ensure_ascii=False,
        default=str,
    ))

    if errors:
        raise SystemExit(2)

    if args.execute:
        verification = _verify(unidad, args.fi, args.ff)
        print(json.dumps({
            "event": "verification",
            "unidad": unidad,
            "fi": args.fi,
            "ff": args.ff,
            "result": verification,
        }, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
