#!/usr/bin/env python3
"""
Repair controlado de dbo.Sync_Sales.items para MPRO.

Reglas:
- Solo branch 130QRO / ORIGEN.
- Solo actualiza registros existentes con items NULL, '' o '[]'.
- No inserta tickets.
- No toca total, MontoTotal, Pax ni FechaHora.
- Match por branch + NumeroTicket.
- Excluye 130QRO / 21-0037776 por ser ANTICIPO no-Comanda sin detalle Comanda.
- Por defecto corre en dry-run. Para escribir requiere --execute.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, "/app/backend")

from core.db import execute_sql_query
from tools import sync_sales_dry_run as dry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("repair_sync_sales_items_mpro")

EDARSAHUB_CONFIG = {
    "host": os.getenv("EDARSAHUB_SQL_HOST"),
    "port": 1433,
    "database": "EDARSAHUB",
    "username": os.getenv("EDARSAHUB_SQL_USER"),
    "password": os.getenv("EDARSAHUB_SQL_PASSWORD"),
}

EXCLUDED = {
    ("130QRO", "21-0037776"): "ANTICIPO CONSUMO DE ALIMENTOS Y BEBIDAS; Vn_Tabla vacía; sin Comanda",
}

def sql_escape(value):
    if value is None:
        return ""
    return str(value).replace("'", "''")

def q(sql):
    rows = execute_sql_query(
        EDARSAHUB_CONFIG["host"],
        EDARSAHUB_CONFIG["port"],
        EDARSAHUB_CONFIG["database"],
        EDARSAHUB_CONFIG["username"],
        EDARSAHUB_CONFIG["password"],
        sql,
    )
    return rows or []

def d(value):
    if value is None:
        return Decimal("0")
    return Decimal(str(value))

def get_sale_ticket(s):
    for key in ("NumeroTicket", "numero_ticket", "Ticket", "ticket", "Folio", "folio"):
        if key in s and s[key] is not None:
            return str(s[key]).strip()
    return None

def get_sale_items(s):
    for key in ("items", "Items", "ItemsJSON", "items_json"):
        if key in s:
            return s.get(key)
    return None

def get_sale_total(s):
    for key in ("MontoTotal", "monto_total", "total", "Total"):
        if key in s and s[key] is not None:
            return d(s[key])
    return Decimal("0")

def normalize_items_json(raw):
    if raw is None:
        return None, 0

    if isinstance(raw, list):
        data = raw
    elif isinstance(raw, str):
        txt = raw.strip()
        if not txt or txt in ("[]", "null", "None"):
            return None, 0
        data = json.loads(txt)
    else:
        return None, 0

    if not isinstance(data, list) or len(data) == 0:
        return None, 0

    return json.dumps(data, ensure_ascii=False, separators=(",", ":")), len(data)

def load_empty_rows(branch, fecha_inicio, fecha_fin):
    branch_sql = sql_escape(branch)
    return q(f"""
    SELECT
        CAST(id AS VARCHAR(100)) AS sync_id,
        CAST(branch AS NVARCHAR(100)) AS branch,
        CAST(NumeroTicket AS VARCHAR(100)) AS NumeroTicket,
        FechaHora,
        MontoTotal,
        total
    FROM dbo.Sync_Sales
    WHERE branch = '{branch_sql}'
      AND CAST(FechaHora AS DATE) >= '{fecha_inicio}'
      AND CAST(FechaHora AS DATE) <= '{fecha_fin}'
      AND (
          items IS NULL
          OR LTRIM(RTRIM(CAST(items AS NVARCHAR(MAX)))) = ''
          OR LTRIM(RTRIM(CAST(items AS NVARCHAR(MAX)))) = '[]'
      )
      AND ISNULL(MontoTotal, total) > 0
    ORDER BY FechaHora, NumeroTicket;
    """)

def update_items(sync_id, items_json):
    sync_id_sql = sql_escape(sync_id)
    items_sql = sql_escape(items_json)

    sql = f"""
    UPDATE dbo.Sync_Sales
    SET
        items = N'{items_sql}'
    WHERE id = '{sync_id_sql}'
      AND (
          items IS NULL
          OR LTRIM(RTRIM(CAST(items AS NVARCHAR(MAX)))) = ''
          OR LTRIM(RTRIM(CAST(items AS NVARCHAR(MAX)))) = '[]'
      );
    SELECT @@ROWCOUNT AS rows_updated;
    """
    rows = q(sql)
    if rows:
        return int(rows[0].get("rows_updated") or 0)
    return 0

def repair_branch(branch, fecha_inicio, fecha_fin, execute=False, tolerance=Decimal("1.00")):
    config = dry.get_unidad_config(branch)
    if not config:
        raise RuntimeError(f"No se pudo obtener configuración de {branch}")

    logger.info("Extrayendo POS branch=%s rango=%s..%s", branch, fecha_inicio, fecha_fin)
    sales, status = dry.extract_sales_from_pos(config, fecha_inicio, fecha_fin)
    if status != "OK":
        raise RuntimeError(f"POS status no OK para {branch}: {status}")

    source = {}
    for sale in sales:
        ticket = get_sale_ticket(sale)
        if not ticket:
            continue

        try:
            items_json, items_count = normalize_items_json(get_sale_items(sale))
        except Exception as exc:
            logger.warning("Items inválidos en source branch=%s ticket=%s error=%s", branch, ticket, exc)
            continue

        if items_count <= 0 or not items_json:
            continue

        source[ticket] = {
            "items_json": items_json,
            "items_count": items_count,
            "total": get_sale_total(sale),
        }

    empty_rows = load_empty_rows(branch, fecha_inicio, fecha_fin)

    stats = {
        "branch": branch,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "pos_status": status,
        "source_tickets": len(sales),
        "source_with_items": len(source),
        "empty_rows": len(empty_rows),
        "repairable": 0,
        "excluded": 0,
        "not_found": 0,
        "amount_mismatch": 0,
        "updated": 0,
        "errors": 0,
    }

    samples_repair = []
    samples_skip = []

    for row in empty_rows:
        sync_id = str(row.get("sync_id"))
        ticket = str(row.get("NumeroTicket") or "").strip()

        if (branch, ticket) in EXCLUDED:
            stats["excluded"] += 1
            samples_skip.append((ticket, "EXCLUDED", EXCLUDED[(branch, ticket)]))
            continue

        src = source.get(ticket)
        if not src:
            stats["not_found"] += 1
            samples_skip.append((ticket, "NOT_FOUND", "No aparece en extracción POS con items"))
            continue

        sync_total = d(row.get("MontoTotal") or row.get("total"))
        if abs(sync_total - src["total"]) > tolerance:
            stats["amount_mismatch"] += 1
            samples_skip.append((ticket, "AMOUNT_MISMATCH", f"sync={sync_total} source={src['total']}"))
            continue

        stats["repairable"] += 1

        if len(samples_repair) < 15:
            samples_repair.append((ticket, str(row.get("FechaHora")), sync_total, src["items_count"]))

        if execute:
            try:
                stats["updated"] += update_items(sync_id, src["items_json"])
            except Exception as exc:
                stats["errors"] += 1
                samples_skip.append((ticket, "UPDATE_ERROR", str(exc)))

    return stats, samples_repair, samples_skip[:20]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fecha-inicio", required=True)
    parser.add_argument("--fecha-fin", required=True)
    parser.add_argument("--unidad", choices=["130QRO", "ORIGEN"], help="Opcional: limitar a una unidad")
    parser.add_argument("--execute", action="store_true", help="Ejecuta UPDATE real. Sin esto es dry-run.")
    args = parser.parse_args()

    branches = [args.unidad] if args.unidad else ["130QRO", "ORIGEN"]

    print("=" * 90)
    print("REPAIR Sync_Sales.items MPRO")
    print("MODO:", "EXECUTE" if args.execute else "DRY-RUN")
    print("RANGO:", args.fecha_inicio, "a", args.fecha_fin)
    print("=" * 90)

    totals = {
        "empty_rows": 0,
        "repairable": 0,
        "excluded": 0,
        "not_found": 0,
        "amount_mismatch": 0,
        "updated": 0,
        "errors": 0,
    }

    for branch in branches:
        stats, samples_repair, samples_skip = repair_branch(
            branch,
            args.fecha_inicio,
            args.fecha_fin,
            execute=args.execute,
        )

        print()
        print("-" * 90)
        print("BRANCH:", branch)
        print("-" * 90)
        for key, value in stats.items():
            print(f"{key}={value}")

        print()
        print("MUESTRA_REPAIRABLE:")
        for ticket, fecha, total, items_count in samples_repair:
            print(f"  {ticket} | {fecha} | total={total} | items_count={items_count}")

        print()
        print("MUESTRA_SKIP:")
        for ticket, code, reason in samples_skip:
            print(f"  {ticket} | {code} | {reason}")

        for key in totals:
            totals[key] += int(stats.get(key) or 0)

    print()
    print("=" * 90)
    print("TOTALES")
    print("=" * 90)
    for key, value in totals.items():
        print(f"{key}={value}")

    if not args.execute:
        print()
        print("DRY-RUN: no se actualizó dbo.Sync_Sales.")

if __name__ == "__main__":
    main()
