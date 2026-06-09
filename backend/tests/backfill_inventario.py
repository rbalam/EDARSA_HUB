"""
Backfill histórico ENFOCADO de inventario (almacenes + movimientos + requisiciones)
para las unidades activas que conectan: 130MID, ESTELAR, ORIGEN, 130QRO.
Reutiliza las mismas funciones canónicas del job sync_compras.

Uso: python tests/backfill_inventario.py [dias_atras]
Idempotente (MERGE/NOT EXISTS). CIENFUEGOS se omite (DDNS caído).
"""
import sys, time
sys.path.insert(0, "/app/backend")
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
from datetime import datetime
from core.sql_first.db import get_sql_connection
from core.secret_manager import decrypt_secret
from modules.compras.sync_service import (
    sync_almacenes_from_server, sync_requisiciones_from_server,
)
from core.inventarios.sync_movimientos_canonico import sync_movimientos_canonico
from core.inventarios.resolver_canonico import clear_resolver_caches
from core.scheduler.jobs.sync_compras_job import _execute_sql_with_timeout

DIAS = int(sys.argv[1]) if len(sys.argv) > 1 else 365
UNIDADES = sys.argv[2].split(",") if len(sys.argv) > 2 else ["130MID", "ESTELAR", "ORIGEN", "130QRO"]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    conn = get_sql_connection(); cur = conn.cursor()
    _ph = ",".join(["%s"] * len(UNIDADES))
    cur.execute(f"""
      SELECT s.id,s.host,s.port,s.database_name,s.username,s.password_encrypted,s.system_type,
             u.id uid,u.codigo uc,u.nombre un,u.sucursal_origen_id soi
      FROM Servidores_Conexiones s JOIN Unidades_Negocio u ON u.server_id=CAST(s.id AS NVARCHAR(36))
      WHERE u.codigo IN ({_ph})
    """, tuple(UNIDADES))
    cols = [d[0] for d in cur.description]
    by_code = {r[cols.index('uc')]: dict(zip(cols, r)) for r in cur.fetchall()}
    conn.close()

    log(f"==== BACKFILL INVENTARIO (dias_atras={DIAS}) ====")
    for code in UNIDADES:
        r = by_code.get(code)
        if not r:
            log(f"{code}: NO encontrada en BD, omitida"); continue
        clear_resolver_caches()  # caches frescos por unidad
        si = {'id': str(r['id']), 'host': r['host'], 'port': int(r['port'] or 1433),
              'database': r['database_name'], 'username': r['username'],
              'password': decrypt_secret(r['password_encrypted'] or ''), 'system_type': r['system_type']}
        ui = {'id': str(r['uid']), 'codigo': r['uc'], 'nombre': r['un'], 'sucursal_origen_id': r['soi']}
        log(f"---- {code} ({r['system_type']}) sucursal_origen={r['soi']} ----")
        t0 = time.time()
        try:
            log(f"{code} ALMACENES: {sync_almacenes_from_server(si, ui, _execute_sql_with_timeout)}")
        except Exception as e:
            log(f"{code} ALMACENES ERROR: {str(e)[:160]}")
        try:
            res = sync_movimientos_canonico(si, ui, _execute_sql_with_timeout, dias_atras=DIAS)
            log(f"{code} MOVIMIENTOS: {res}")
        except Exception as e:
            log(f"{code} MOVIMIENTOS ERROR: {str(e)[:160]}")
        try:
            log(f"{code} REQUISICIONES: {sync_requisiciones_from_server(si, ui, _execute_sql_with_timeout)}")
        except Exception as e:
            log(f"{code} REQUISICIONES ERROR: {str(e)[:160]}")
        log(f"{code} terminado en {time.time()-t0:.0f}s")

    # Totales finales
    conn = get_sql_connection(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM Inventario_Almacenes"); a = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM Inventario_Movimientos"); m = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM Inventario_MovimientosDetalle"); d = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM Compras_Requisiciones_Sync WHERE sync_status='ACTIVE'"); q = c.fetchone()[0]
    conn.close()
    log(f"==== TOTALES EDARSAHUB: Almacenes={a} Movimientos={m} Detalle={d} Requisiciones={q} ====")
    log("==== BACKFILL COMPLETO ====")


if __name__ == "__main__":
    main()
