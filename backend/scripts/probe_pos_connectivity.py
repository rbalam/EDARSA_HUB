#!/usr/bin/env python3
"""
P1-OPCION-A · PRUEBA DE CONECTIVIDAD POS (solo lectura, sin cargar datos).

- Resuelve config canónica por unidad (Unidades_Negocio + Servidores_Conexiones).
- Intenta abrir conexión y ejecutar 'SELECT 1' con timeout CORTO.
- NO carga datos. NO imprime password ni password_encrypted.
- Reporta: unidad, host, puerto, db, alcanzable (True/False), tipo de error.

Uso: python3 /app/backend/scripts/probe_pos_connectivity.py
"""
import os
import sys
import json
import time
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
from core.scheduler.jobs.inteligencia_comercial_sync_job import (
    get_unidades_negocio_pos,
    get_pos_config_for_unidad,
)

LOGIN_TIMEOUT = 8   # segundos para conectar (falla rápido si no alcanza)
QUERY_TIMEOUT = 8


def probe_one(cfg):
    t0 = time.time()
    conn = None
    try:
        conn = pymssql.connect(
            server=cfg["host"],
            port=int(cfg.get("port") or 1433),
            user=cfg["username"],
            password=cfg["password"],
            database=cfg["database"],
            login_timeout=LOGIN_TIMEOUT,
            timeout=QUERY_TIMEOUT,
            tds_version="7.0",
        )
        cur = conn.cursor()
        cur.execute("SELECT 1 AS ok")
        row = cur.fetchone()
        cur.close()
        return {"reachable": bool(row), "error_type": None, "elapsed_s": round(time.time() - t0, 1)}
    except Exception as e:
        msg = str(e).lower()
        if "timeout" in msg or "timed out" in msg or "unable to connect" in msg:
            etype = "TIMEOUT/RED (no alcanza el host)"
        elif "login" in msg or "password" in msg or "18456" in msg:
            etype = "AUTENTICACION (host alcanzable, credencial falla)"
        else:
            etype = f"OTRO: {type(e).__name__}"
        return {"reachable": False, "error_type": etype, "elapsed_s": round(time.time() - t0, 1)}
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def main():
    resultados = []
    for unidad in get_unidades_negocio_pos(None):
        cfg = get_pos_config_for_unidad(unidad)
        if not cfg or not cfg.get("host"):
            resultados.append({
                "unidad": unidad.get("unidad_codigo"),
                "resolved": False,
                "host": None,
            })
            continue
        res = probe_one(cfg)
        resultados.append({
            "unidad": unidad.get("unidad_codigo"),
            "system_type": unidad.get("system_type"),
            "host": cfg.get("host"),
            "port": cfg.get("port"),
            "database": cfg.get("database"),
            "username": cfg.get("username"),
            "has_password": bool(cfg.get("password")),
            **res,
        })

    alcanzables = [r["unidad"] for r in resultados if r.get("reachable")]
    print(json.dumps({
        "resumen": {
            "total": len(resultados),
            "alcanzables": alcanzables,
            "no_alcanzables": [r["unidad"] for r in resultados if not r.get("reachable")],
        },
        "detalle": resultados,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
