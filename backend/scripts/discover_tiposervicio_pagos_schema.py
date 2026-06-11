#!/usr/bin/env python3
"""
DESCUBRIMIENTO DE ESQUEMA (SOLO LECTURA) para enriquecer el sync:
- tipo de servicio por ticket (cheques)
- formas de pago por ticket (cheque)

Inspecciona:
  A) EDARSAHUB: columnas de Sync_Sales y existencia/columnas de Finanzas_CortesCaja_DetallePagos.
  B) POS SoftRestaurant (default ESTELAR): tablas cheques/formas de pago/tipo de servicio.
  C) POS MPRO (default ORIGEN): cheques/comanda + formas de pago.

NO modifica nada. NO imprime passwords.
Uso: python3 scripts/discover_tiposervicio_pagos_schema.py [--sr ESTELAR] [--mpro ORIGEN]
"""
import os
import sys
import json
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
)


def _connect_pos(cfg):
    return pymssql.connect(
        server=cfg["host"], port=int(cfg.get("port") or 1433),
        user=cfg["username"], password=cfg["password"], database=cfg["database"],
        login_timeout=10, timeout=120, tds_version="7.0", as_dict=True,
    )


def cols_of(cur, table):
    try:
        cur.execute(
            "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH "
            "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
            (table,),
        )
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        return [{"error": str(e)}]


def tables_like(cur, like):
    try:
        cur.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME LIKE %s ORDER BY TABLE_NAME",
            (like,),
        )
        return [r["TABLE_NAME"] for r in cur.fetchall()]
    except Exception as e:
        return [f"error: {e}"]


def sample(cur, sql):
    try:
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        return [{"error": str(e)}]


def discover_edarsahub(out):
    out["EDARSAHUB"] = {}
    try:
        conn = get_sql_connection()
        cur = conn.cursor(as_dict=True)
        out["EDARSAHUB"]["Sync_Sales_cols"] = cols_of(cur, "Sync_Sales")
        # ¿Existe la tabla destino de detalle de pagos?
        cur.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'Finanzas_CortesCaja%'"
        )
        out["EDARSAHUB"]["tablas_cortescaja"] = [r["TABLE_NAME"] for r in cur.fetchall()]
        out["EDARSAHUB"]["DetallePagos_cols"] = cols_of(cur, "Finanzas_CortesCaja_DetallePagos")
        cur.close()
        conn.close()
    except Exception as e:
        out["EDARSAHUB"]["error"] = str(e)


def discover_softrestaurant(out, codigo):
    key = f"SOFTRESTAURANT_{codigo}"
    out[key] = {}
    unidades = get_unidades_negocio_pos([codigo])
    if not unidades:
        out[key]["error"] = f"unidad {codigo} no encontrada"
        return
    cfg = get_pos_config_for_unidad(unidades[0])
    out[key]["system_type"] = cfg.get("system_type") if cfg else None
    out[key]["host"] = cfg.get("host") if cfg else None
    out[key]["db"] = cfg.get("database") if cfg else None
    if not cfg or not cfg.get("host"):
        out[key]["error"] = "config no resuelta"
        return
    try:
        conn = _connect_pos(cfg)
        cur = conn.cursor(as_dict=True)
        out[key]["cheques_cols"] = cols_of(cur, "cheques")
        out[key]["tablas_pago"] = tables_like(cur, "%pago%") + tables_like(cur, "%formadepago%")
        out[key]["tablas_servicio"] = tables_like(cur, "%servicio%")
        # Posibles tablas de detalle de pagos
        for t in ("chequespagos", "cheqpagos", "chequepagos"):
            cols = cols_of(cur, t)
            if cols and "error" not in cols[0]:
                out[key][f"{t}_cols"] = cols
        out[key]["formasdepago_cols"] = cols_of(cur, "formasdepago")
        out[key]["tipodeservicio_cols"] = cols_of(cur, "tipodeservicio")
        # Muestra de cheques recientes (campos de interes)
        out[key]["cheques_sample"] = sample(
            cur,
            "SELECT TOP 3 folio, total, idturno, cancelado FROM cheques ORDER BY folio DESC",
        )
        cur.close()
        conn.close()
    except Exception as e:
        out[key]["error"] = str(e)


def discover_mpro(out, codigo):
    key = f"MPRO_{codigo}"
    out[key] = {}
    unidades = get_unidades_negocio_pos([codigo])
    if not unidades:
        out[key]["error"] = f"unidad {codigo} no encontrada"
        return
    cfg = get_pos_config_for_unidad(unidades[0])
    out[key]["system_type"] = cfg.get("system_type") if cfg else None
    out[key]["host"] = cfg.get("host") if cfg else None
    out[key]["db"] = cfg.get("database") if cfg else None
    out[key]["sucursal_origen_id"] = cfg.get("sucursal_origen_id") if cfg else None
    if not cfg or not cfg.get("host"):
        out[key]["error"] = "config no resuelta"
        return
    try:
        conn = _connect_pos(cfg)
        cur = conn.cursor(as_dict=True)
        out[key]["Comanda_cols"] = cols_of(cur, "Comanda")
        out[key]["cheques_tablas"] = tables_like(cur, "%heque%")
        out[key]["pago_tablas"] = tables_like(cur, "%ago%") + tables_like(cur, "%orma%")
        out[key]["servicio_tablas"] = tables_like(cur, "%ervicio%")
        # Encabezado de venta
        out[key]["Venta_Encabezado_cols"] = cols_of(cur, "Venta_Encabezado")
        cur.close()
        conn.close()
    except Exception as e:
        out[key]["error"] = str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", default="ESTELAR")
    ap.add_argument("--mpro", default="ORIGEN")
    args = ap.parse_args()
    out = {}
    discover_edarsahub(out)
    discover_softrestaurant(out, args.sr)
    discover_mpro(out, args.mpro)
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
