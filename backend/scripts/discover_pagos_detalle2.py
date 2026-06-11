#!/usr/bin/env python3
"""Descubrimiento focalizado #2 (SOLO LECTURA):
SR: tabla `tiposervicio` (cols + filas), `chequespagos` join `formasdepago` muestra.
MPRO: `Comanda_Pago`, `POS_Pagos`, `Forma_Pago` cols + muestra; valores de Comanda.Co_Tipo.
"""
import os, sys, json, argparse
from pathlib import Path
BACKEND_DIR = Path("/app/backend"); ENV_PATH = BACKEND_DIR / ".env"
def load_env():
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
load_env(); sys.path.insert(0, str(BACKEND_DIR))
import pymssql
from core.scheduler.jobs.inteligencia_comercial_sync_job import get_unidades_negocio_pos, get_pos_config_for_unidad

def conn_for(codigo):
    u = get_unidades_negocio_pos([codigo]); 
    if not u: return None
    cfg = get_pos_config_for_unidad(u[0])
    if not cfg or not cfg.get("host"): return None
    return pymssql.connect(server=cfg["host"], port=int(cfg.get("port") or 1433), user=cfg["username"],
                           password=cfg["password"], database=cfg["database"], login_timeout=10, timeout=120,
                           tds_version="7.0", as_dict=True), cfg

def cols(cur, t):
    try:
        cur.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=%s ORDER BY ORDINAL_POSITION",(t,))
        return [r["COLUMN_NAME"] for r in cur.fetchall()]
    except Exception as e: return [f"error: {e}"]

def q(cur, sql):
    try:
        cur.execute(sql); return [dict(r) for r in cur.fetchall()]
    except Exception as e: return [{"error": str(e)}]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sr", default="ESTELAR"); ap.add_argument("--mpro", default="ORIGEN")
    a = ap.parse_args(); out = {}
    # SR
    c = conn_for(a.sr)
    if c:
        conn, cfg = c; cur = conn.cursor(as_dict=True); s = {}
        s["tiposervicio_cols"] = cols(cur, "tiposervicio")
        s["tiposervicio_rows"] = q(cur, "SELECT * FROM tiposervicio")
        s["chequespagos_join_sample"] = q(cur, "SELECT TOP 8 cp.folio, cp.idformadepago, fp.descripcion, fp.tipo, cp.importe, cp.propina, cp.referencia FROM chequespagos cp LEFT JOIN formasdepago fp ON cp.idformadepago=fp.idformadepago ORDER BY cp.folio DESC")
        s["cheques_tiposervicio_sample"] = q(cur, "SELECT TOP 8 c.folio, c.tipodeservicio, ts.descripcion FROM cheques c LEFT JOIN tiposervicio ts ON c.tipodeservicio=ts.idtiposervicio ORDER BY c.folio DESC")
        out["SR"] = s; cur.close(); conn.close()
    # MPRO
    c = conn_for(a.mpro)
    if c:
        conn, cfg = c; cur = conn.cursor(as_dict=True); m = {}
        m["Comanda_Pago_cols"] = cols(cur, "Comanda_Pago")
        m["POS_Pagos_cols"] = cols(cur, "POS_Pagos")
        m["Forma_Pago_cols"] = cols(cur, "Forma_Pago")
        m["Co_Tipo_distinct"] = q(cur, "SELECT Co_Tipo, COUNT(*) n FROM Comanda WITH (NOLOCK) GROUP BY Co_Tipo")
        suc = cfg.get("sucursal_origen_id")
        m["Comanda_Pago_sample"] = q(cur, f"SELECT TOP 8 * FROM Comanda_Pago WITH (NOLOCK)")
        m["POS_Pagos_sample"] = q(cur, f"SELECT TOP 5 * FROM POS_Pagos WITH (NOLOCK)")
        out["MPRO"] = m; cur.close(); conn.close()
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__": main()
