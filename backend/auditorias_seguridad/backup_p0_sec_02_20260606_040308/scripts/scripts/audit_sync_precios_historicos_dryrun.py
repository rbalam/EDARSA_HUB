"""
Auditor DRY-RUN para Sync_Precios_Historicos
Verifica estructura de tabla destino y servidores candidatos
"""
import os
import sys

# Usar pymssql (pyodbc tiene issues con libodbc en este entorno)
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
        print(f"  ID={str(r[0]):36} | {r[1]:25} | {r[2]:20} | Activo={r[3]}")

    print("\n=== PRODUCTOS EN Sync_Productos (fuente) ===")
    cur.execute("SELECT COUNT(*) FROM Sync_Productos WHERE PrecioVenta > 0")
    print(f"  Total productos con precio: {cur.fetchone()[0]}")
    
    cur.execute("""
    SELECT ServerID, COUNT(*) as productos, 
           SUM(CASE WHEN PrecioVenta > 0 THEN 1 ELSE 0 END) as con_precio
    FROM Sync_Productos
    GROUP BY ServerID
    """)
    print("\n  Por servidor:")
    for r in cur.fetchall():
        print(f"    ServerID={str(r[0]):36} | {r[1]:5} productos | {r[2]:5} con precio")

    print("\nDRY-RUN OK: no se insertó ningún dato.")
    cn.close()

if __name__ == "__main__":
    main()
