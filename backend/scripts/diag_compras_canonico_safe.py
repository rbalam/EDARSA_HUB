"""
Diagnóstico SEGURO de tablas canónicas de Compras/Inventario en EDARSAHUB.
NO imprime credenciales, host, usuario, base ni longitudes.
Solo reporta: existencia de tabla, conteo de filas y nombres de columnas.
"""
import sys
from pathlib import Path
sys.path.insert(0, "/app/backend")

from dotenv import load_dotenv
load_dotenv(Path("/app/backend/.env"))

from core.sql_first.db import get_sql_connection


def tabla_existe(cur, nombre):
    cur.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = %s",
        (nombre,),
    )
    return cur.fetchone()[0] > 0


def columnas(cur, nombre):
    cur.execute(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
        (nombre,),
    )
    return [r[0] for r in cur.fetchall()]


def conteo(cur, nombre):
    cur.execute(f"SELECT COUNT(*) FROM [{nombre}]")
    return cur.fetchone()[0]


def main():
    conn = get_sql_connection()
    cur = conn.cursor()

    tablas = [
        "Inventario_Movimientos",
        "Inventario_MovimientosDetalle",
        "Inventario_TipoMovimiento",
        "Comercial_TiposMovimiento",
        "Sistema_TiposMovimiento",
    ]
    for t in tablas:
        if tabla_existe(cur, t):
            print(f"[OK] {t}: filas={conteo(cur, t)} | cols={columnas(cur, t)}")
        else:
            print(f"[--] {t}: NO EXISTE")

    # Mapeo de unidades (sin secretos)
    print("\n=== Unidades_Negocio (mapeo canónico, sin secretos) ===")
    if tabla_existe(cur, "Unidades_Negocio"):
        cols = columnas(cur, "Unidades_Negocio")
        print(f"cols Unidades_Negocio = {cols}")
        sel = [c for c in ["id", "codigo", "nombre", "server_id", "sucursal_origen_id", "empresa_id", "activo"] if c in cols]
        cur.execute(f"SELECT {', '.join(sel)} FROM Unidades_Negocio")
        for r in cur.fetchall():
            print(dict(zip(sel, r)))

    conn.close()


if __name__ == "__main__":
    main()
