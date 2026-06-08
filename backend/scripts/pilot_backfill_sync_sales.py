#!/usr/bin/env python3
"""
PILOTO Opción A · Backfill de DETALLE a Sync_Sales (staging) — SOLO LECTURA del POS.

ALCANCE PILOTO (autorizado): 1 unidad, 1 mes reciente, solo Sync_Sales.
PROHIBIDO: tocar Comercial_KPIs_Diarios_v2 / vw_* / recalcular KPIs / Venta_Encabezado/Detalle
de EDARSAHUB / Mongo / usuarios. NO imprime passwords.

Características:
- Credenciales 100% canónicas (get_pos_connection_config vía helper Comercial V2).
- Extracción read-only del POS.
- Inserción a Sync_Sales por LOTES (executemany), idempotente por (NumeroTicket, UnidadNegocio, fecha).
- Transacción con rollback lógico si falla.
- Bitácora en Sistema_SyncPOS_Bitacora.
- Reporte: tickets/líneas extraídas, venta detalle, duplicados, tickets sin detalle, tiempo,
  comparación vs KPI canónico del mismo periodo (solo lectura), recomendación.

Uso (defaults = piloto):
  python3 scripts/pilot_backfill_sync_sales.py
  python3 scripts/pilot_backfill_sync_sales.py --unidad ESTELAR --fecha-inicio 2026-05-01 --fecha-fin 2026-06-01
  (agrega --dry-run para extraer y medir SIN insertar)
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path

BACKEND_DIR = Path("/app/backend")
ENV_PATH = BACKEND_DIR / ".env"


def load_env():
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
sys.path.insert(0, str(BACKEND_DIR))

import pymssql
from core.sql_first.db import get_sql_connection, fetch_all_dict
from core.scheduler.jobs.inteligencia_comercial_sync_job import (
    get_unidades_negocio_pos,
    get_pos_config_for_unidad,
    get_softrestaurant_query,
    get_mpro_query,
    registrar_syncpos_bitacora,
)

BATCH_SIZE = 500


def _count_items(items_json):
    if not items_json:
        return 0, True
    try:
        data = json.loads(items_json)
        if not data:
            return 0, True
        return len(data), False
    except Exception:
        return 0, True


def extract_from_pos(unidad_row, cfg, fi, ff):
    """Lee tickets del POS (read-only). Devuelve (rows, elapsed)."""
    t0 = time.time()
    system_type = (cfg.get("system_type") or "").upper()
    query = get_mpro_query(fi, ff) if system_type == "MPRO" else get_softrestaurant_query(fi, ff)
    conn = pymssql.connect(
        server=cfg["host"], port=int(cfg.get("port") or 1433),
        user=cfg["username"], password=cfg["password"], database=cfg["database"],
        login_timeout=10, timeout=240, tds_version="7.0",
    )
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(query)
        rows = cur.fetchall() or []
        cur.close()
    finally:
        conn.close()
    codigo = unidad_row.get("unidad_codigo")
    for r in rows:
        r["UnidadNegocio"] = codigo
    return rows, round(time.time() - t0, 1)


def load_to_sync_sales(rows, unidad_codigo, fi, ff, dry_run=False):
    """Inserta a Sync_Sales por lotes, idempotente, transaccional. Devuelve métricas."""
    conn = get_sql_connection()
    metrics = {
        "tickets_extraidos": len(rows),
        "tickets_nuevos": 0,
        "tickets_duplicados": 0,
        "lineas_extraidas": 0,
        "tickets_sin_detalle": 0,
        "venta_detalle_total": 0.0,
        "inserted": 0,
        "dry_run": dry_run,
    }
    try:
        # 1) Pre-cargar claves existentes del periodo (una sola query, no fila-por-fila)
        cur = conn.cursor()
        cur.execute(
            "SELECT NumeroTicket, CONVERT(VARCHAR(10), CAST(FechaHora AS DATE), 120) AS d "
            "FROM Sync_Sales WHERE UnidadNegocio=%s AND FechaHora >= %s AND FechaHora < %s",
            (unidad_codigo, fi, ff),
        )
        existing = set((str(t), str(d)) for (t, d) in cur.fetchall())
        cur.close()

        seen = set()
        to_insert = []
        for s in rows:
            n_lineas, sin_detalle = _count_items(s.get("items"))
            metrics["lineas_extraidas"] += n_lineas
            if sin_detalle:
                metrics["tickets_sin_detalle"] += 1
            try:
                metrics["venta_detalle_total"] += float(s.get("MontoTotal") or 0)
            except Exception:
                pass

            fh = s.get("FechaHora")
            fecha = str(fh)[:10] if fh else None
            key = (str(s.get("NumeroTicket")), fecha)
            if key in existing or key in seen:
                metrics["tickets_duplicados"] += 1
                continue
            seen.add(key)
            to_insert.append((
                s.get("IdTransaccion") or str(time.time()),
                unidad_codigo,                      # branch
                unidad_codigo,                      # UnidadNegocio
                str(s.get("NumeroTicket")),
                s.get("MontoTotal"),
                s.get("Pax"),
                s.get("FechaHora"),
                s.get("status", "COMPLETED"),
                s.get("items") or "[]",
                s.get("MontoTotal"),                # total
            ))

        metrics["tickets_nuevos"] = len(to_insert)

        if dry_run:
            conn.close()
            return metrics

        # 2) Inserción por lotes (executemany) dentro de una transacción
        insert_sql = (
            "INSERT INTO Sync_Sales (id, branch, UnidadNegocio, NumeroTicket, MontoTotal, "
            "Pax, FechaHora, status, items, created_at, total) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), %s)"
        )
        cur = conn.cursor()
        for i in range(0, len(to_insert), BATCH_SIZE):
            batch = to_insert[i:i + BATCH_SIZE]
            cur.executemany(insert_sql, batch)
            metrics["inserted"] += len(batch)
        cur.close()
        conn.commit()
        return metrics
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        metrics["error"] = f"{type(e).__name__}: {e}"
        metrics["inserted"] = 0
        return metrics
    finally:
        try:
            conn.close()
        except Exception:
            pass


def kpi_canonical_compare(unidad_nombre, fi, ff):
    """SOLO LECTURA: compara contra Comercial_KPIs_Diarios_v2 (NO modifica)."""
    try:
        rows = fetch_all_dict(
            "SELECT SUM(ventas_total) AS ventas, SUM(tickets_total) AS tickets "
            "FROM Comercial_KPIs_Diarios_v2 "
            "WHERE unidad_negocio_nombre = %s AND fecha_operacion >= %s AND fecha_operacion < %s",
            (unidad_nombre, fi, ff),
        )
        r = rows[0] if rows else {}
        return {
            "unidad_nombre_kpi": unidad_nombre,
            "ventas_kpi_canonico": float(r.get("ventas") or 0),
            "tickets_kpi_canonico": int(r.get("tickets") or 0),
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unidad", default="ESTELAR")
    ap.add_argument("--fecha-inicio", default="2026-05-01")
    ap.add_argument("--fecha-fin", default="2026-06-01", help="exclusivo")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    t_start = time.time()
    unidades = get_unidades_negocio_pos([args.unidad])
    if not unidades:
        print(json.dumps({"error": f"Unidad '{args.unidad}' no encontrada en canónico"}, ensure_ascii=False))
        return
    unidad_row = unidades[0]
    cfg = get_pos_config_for_unidad(unidad_row)
    if not cfg or not cfg.get("host"):
        print(json.dumps({"error": f"No se resolvió config canónica para '{args.unidad}'"}, ensure_ascii=False))
        return

    registrar_syncpos_bitacora("BACKFILL", "INICIO",
                               f"Piloto {args.unidad} {args.fecha_inicio}..{args.fecha_fin} dry_run={args.dry_run}",
                               unidad=args.unidad, fecha_inicio=args.fecha_inicio, fecha_fin=args.fecha_fin)

    rows, extract_s = extract_from_pos(unidad_row, cfg, args.fecha_inicio, args.fecha_fin)
    metrics = load_to_sync_sales(rows, unidad_row.get("unidad_codigo"), args.fecha_inicio, args.fecha_fin, args.dry_run)
    kpi = kpi_canonical_compare(unidad_row.get("unidad_nombre"), args.fecha_inicio, args.fecha_fin)

    estado = "ERROR" if metrics.get("error") else ("DRY_RUN" if args.dry_run else "OK")
    registrar_syncpos_bitacora("BACKFILL", estado,
                               json.dumps({k: metrics.get(k) for k in ("tickets_extraidos", "inserted", "error")}, ensure_ascii=False),
                               unidad=args.unidad, fecha_inicio=args.fecha_inicio, fecha_fin=args.fecha_fin,
                               tickets=metrics.get("inserted"), lineas=metrics.get("lineas_extraidas"),
                               venta=round(metrics.get("venta_detalle_total", 0), 2))

    venta_det = metrics.get("venta_detalle_total", 0.0)
    ventas_kpi = kpi.get("ventas_kpi_canonico", 0.0)
    report = {
        "piloto": {
            "unidad": args.unidad,
            "unidad_nombre": unidad_row.get("unidad_nombre"),
            "system_type": cfg.get("system_type"),
            "host": cfg.get("host"),
            "database": cfg.get("database"),
            "has_password": bool(cfg.get("password")),
            "periodo": f"{args.fecha_inicio} .. {args.fecha_fin} (fin exclusivo)",
            "dry_run": args.dry_run,
        },
        "extraccion": {
            "tickets_extraidos": metrics["tickets_extraidos"],
            "lineas_extraidas": metrics["lineas_extraidas"],
            "venta_detalle_total": round(venta_det, 2),
            "tickets_sin_detalle": metrics["tickets_sin_detalle"],
            "tiempo_extraccion_s": extract_s,
        },
        "carga_sync_sales": {
            "tickets_nuevos": metrics["tickets_nuevos"],
            "tickets_duplicados": metrics["tickets_duplicados"],
            "insertados": metrics["inserted"],
            "error": metrics.get("error"),
        },
        "comparacion_kpi_canonico_solo_lectura": {
            **kpi,
            "venta_detalle_sync_sales": round(venta_det, 2),
            "diferencia_venta_vs_kpi": round(venta_det - ventas_kpi, 2),
            "nota": "Solo comparación. PROHIBIDO sobrescribir/re-derivar KPIs.",
        },
        "tiempo_total_s": round(time.time() - t_start, 1),
        "recomendacion_escalado": None,
    }

    # Recomendación de escalado (estimación lineal a 24 meses × 5 unidades)
    if not metrics.get("error") and extract_s >= 0:
        tickets_mes = metrics["tickets_extraidos"]
        est_tickets_24m_5u = tickets_mes * 24 * 5
        report["recomendacion_escalado"] = {
            "tickets_este_mes_1u": tickets_mes,
            "estimado_tickets_24m_x5u": est_tickets_24m_5u,
            "estrategia": "Cargar por lotes mes×unidad (idempotente), commit por mes, bitácora por corrida.",
        }

    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
