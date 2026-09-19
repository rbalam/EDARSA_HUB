#!/usr/bin/env python3
"""Resincronizacion cerrada de Pagos por Ticket ISCAM.

Solo llama resync_pagos_unidad; no toca Sync_Sales, Cuentas, Comandas ni Cortes.
"""
from __future__ import annotations

import argparse
import json

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", required=True)
    parser.add_argument("--fi", required=True)
    parser.add_argument("--ff", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    unidad = args.unit.strip().upper()
    result = resync_pagos_unidad(unidad, args.fi, args.ff, dry_run=not args.execute)
    print(json.dumps({"event": "resync", "result": result}, ensure_ascii=False, default=str))
    if result.get("error"):
        raise SystemExit(2)
    if args.execute:
        verification = _verify(unidad, args.fi, args.ff)
        print(json.dumps({"event": "verification", "unidad": unidad, "fi": args.fi, "ff": args.ff, "result": verification}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
