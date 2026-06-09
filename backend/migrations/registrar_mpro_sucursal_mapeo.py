"""
Desambiguación MPRO en Sistema_SucursalServidorMapeo — ADITIVO e IDEMPOTENTE.
Solo rellena SucursalOrigenID (NULL) de las 2 filas YA EXISTENTES del server MPRO:
  - SucursalID 1 = ORIGEN   -> SucursalOrigenID '0023'
  - SucursalID 2 = 130QRO   -> SucursalOrigenID '0021'
(SucursalID según Sistema_Sucursales, catálogo limpio y FK del mapeo.)
NO inserta filas. NO cambia SucursalIDs. NO toca otras filas/servers.

MODO por defecto: --validate (aplica en transacción y ROLLBACK, no persiste).
Para PERSISTIR (tabla de control de acceso -> requiere visto bueno explícito):
    python migrations/registrar_mpro_sucursal_mapeo.py --apply
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection

SERVER_MPRO = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
# (SucursalID en Sistema_Sucursales, SucursalOrigenID)
ORIGEN = (1, "0023")
QRO_130 = (2, "0021")


def aplicar(w):
    for suc_id, origen in (ORIGEN, QRO_130):
        w.execute(
            """UPDATE Sistema_SucursalServidorMapeo
               SET SucursalOrigenID = %s
               WHERE ServidorID = %s AND SucursalID = %s AND SucursalOrigenID IS NULL""",
            (origen, SERVER_MPRO, suc_id),
        )


def main():
    apply = "--apply" in sys.argv
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT SucursalID, SucursalOrigenID FROM Sistema_SucursalServidorMapeo WHERE ServidorID=%s ORDER BY SucursalID", (SERVER_MPRO,))
    print("=== ANTES ==="); [print("  ", dict(r)) for r in cur.fetchall()]
    aplicar(conn.cursor())
    cur.execute("SELECT SucursalID, SucursalOrigenID FROM Sistema_SucursalServidorMapeo WHERE ServidorID=%s ORDER BY SucursalID", (SERVER_MPRO,))
    print("=== DESPUÉS (en transacción) ==="); [print("  ", dict(r)) for r in cur.fetchall()]
    if apply:
        conn.commit(); print("[APPLY] PERSISTIDO.")
    else:
        conn.rollback(); print("[VALIDATE] ROLLBACK: cero persistido.")
    conn.close()


if __name__ == "__main__":
    main()
