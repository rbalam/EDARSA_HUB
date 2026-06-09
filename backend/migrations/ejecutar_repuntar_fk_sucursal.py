"""
EJECUCIÓN AUTORIZADA - Re-apuntar FK_Inventario_Movimientos_Sucursal
de RH_Cat_Sucursales -> Sistema_Sucursales (decisión 🅐).
Transaccional. Pre-check de integridad. Validación posterior. Rollback documentado.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection

FK = "FK_Inventario_Movimientos_Sucursal"


def fk_ref(cur):
    cur.execute(
        "SELECT OBJECT_NAME(referenced_object_id) ref FROM sys.foreign_keys WHERE name=%s", (FK,)
    )
    r = cur.fetchone()
    return r[0] if r else None


def main():
    conn = get_sql_connection()
    cur = conn.cursor()

    print(f"[ANTES] {FK} -> {fk_ref(cur)}")

    # Pre-check: filas que violarían el nuevo FK
    cur.execute(
        """SELECT COUNT(*) FROM Inventario_Movimientos m
           WHERE NOT EXISTS (SELECT 1 FROM Sistema_Sucursales s WHERE s.SucursalID = m.SucursalID)"""
    )
    violan = cur.fetchone()[0]
    print(f"[PRE-CHECK] filas que violarían el nuevo FK: {violan} (debe ser 0)")
    if violan > 0:
        print("[ABORT] Hay datos incompatibles. No se ejecuta DDL.")
        conn.close(); return

    try:
        cur.execute(f"ALTER TABLE dbo.Inventario_Movimientos DROP CONSTRAINT {FK}")
        cur.execute(
            f"""ALTER TABLE dbo.Inventario_Movimientos WITH CHECK
                ADD CONSTRAINT {FK} FOREIGN KEY (SucursalID)
                REFERENCES dbo.Sistema_Sucursales (SucursalID)"""
        )
        conn.commit()
        print("[COMMIT] FK re-apuntado.")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] rollback. {str(e)[:200]}")
        conn.close(); return

    # Validación posterior
    ref = fk_ref(cur)
    print(f"[DESPUÉS] {FK} -> {ref}")
    print("[OK]" if ref == "Sistema_Sucursales" else "[FALLO] FK no apunta a Sistema_Sucursales")
    conn.close()


if __name__ == "__main__":
    main()
