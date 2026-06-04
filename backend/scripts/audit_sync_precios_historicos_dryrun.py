"""
Auditor DRY-RUN para Sync_Precios_Historicos
Verifica estructura de tabla destino y servidores candidatos
"""
import os
import sys

# Usar pymssql en lugar de pyodbc (más estable en este entorno)
import pymssql
from datetime import datetime, timedelta

def conn_edarsa():
    return pymssql.connect(
        server=os.getenv('EDARSAHUB_SQL_HOST'),
        port=int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
        database=os.getenv('EDARSAHUB_SQL_DATABASE'),
        user=os.getenv('EDARSAHUB_SQL_USER'),
        password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
        login_timeout=20
    )

def main():
    cn = conn_edarsa()
    cur = cn.cursor()

    print("=== VALIDAR TABLA DESTINO ===")
    cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME='Sync_Precios_Historicos'
    ORDER BY ORDINAL_POSITION
    """)
    cols = cur.fetchall()
    for c in cols:
        print(f"  {c[0]:30} {c[1]:15} {c[2]}")

    cur.execute("SELECT COUNT(*) FROM Sync_Precios_Historicos")
    print(f"\nREGISTROS ACTUALES: {cur.fetchone()[0]}")

    print("\n=== SERVIDORES ACTIVOS CANDIDATOS ===")
    cur.execute("""
    SELECT id, nombre, system_type, activo
    FROM Servidores_Conexiones
    WHERE activo = 1
    ORDER BY nombre
    """)
    rows = cur.fetchall()
    print(f"Total servidores activos: {len(rows)}")
    for r in rows:
        print(f"  ID={r[0][:20]}... | {r[1]:20} | {r[2]:20} | Activo={r[3]}")

    print("\n=== TABLAS FUENTE POTENCIALES ===")
    cur.execute("""
    SELECT TABLE_NAME, 
           (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c WHERE c.TABLE_NAME = t.TABLE_NAME) as num_cols
    FROM INFORMATION_SCHEMA.TABLES t
    WHERE TABLE_NAME LIKE '%Producto%' OR TABLE_NAME LIKE '%Precio%'
    ORDER BY TABLE_NAME
    """)
    for r in cur.fetchall():
        print(f"  {r[0]:40} ({r[1]} columnas)")

    print("\n=== MUESTRA DE Sync_Productos (fuente de precios) ===")
    cur.execute("""
    SELECT TOP 5 
        ProductoID, Codigo, Descripcion, PrecioVenta, CostoReceta, 
        ServerID, SucursalID, SyncedAtMexico
    FROM Sync_Productos
    WHERE PrecioVenta > 0
    ORDER BY SyncedAtMexico DESC
    """)
    cols = [d[0] for d in cur.description]
    print(f"  Columnas: {cols}")
    for r in cur.fetchall():
        print(f"  {r[2][:30] if r[2] else 'N/A':30} | Precio={r[3]} | Costo={r[4]} | Server={str(r[5])[:15]}...")

    cur.execute("SELECT COUNT(*) FROM Sync_Productos WHERE PrecioVenta > 0")
    print(f"\n  Total productos con precio en Sync_Productos: {cur.fetchone()[0]}")

    print("\nDRY-RUN OK: no se insertó ningún dato.")
    cn.close()

if __name__ == "__main__":
    main()
