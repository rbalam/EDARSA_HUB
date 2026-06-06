import os
from pathlib import Path
import pymssql
from datetime import datetime

def load_env():
    env = Path("/app/backend/.env")
    if env.exists():
        for line in env.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k,v = line.split("=",1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

cn = pymssql.connect(
    server=os.getenv("EDARSAHUB_SQL_HOST"),
    port=int(os.getenv("EDARSAHUB_SQL_PORT","1433")),
    user=os.getenv("EDARSAHUB_SQL_USER"),
    password=os.getenv("EDARSAHUB_SQL_PASSWORD"),
    database=os.getenv("EDARSAHUB_SQL_DATABASE"),
    login_timeout=10,
    timeout=60
)
cur = cn.cursor(as_dict=True)

print("P3-07B COSTO RECETA SQL-FIRST")
print("Fecha:", datetime.now())
print("Modo: SQL-FIRST, NO LIVE")
print()

print("=== 1) Buscar tablas candidatas de receta/costo ===")
cur.execute("""
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE='BASE TABLE'
  AND (
        TABLE_NAME LIKE '%Receta%'
     OR TABLE_NAME LIKE '%Costo%'
     OR TABLE_NAME LIKE '%Margen%'
     OR TABLE_NAME LIKE '%Producto%'
  )
ORDER BY TABLE_NAME
""")
tables = [r["TABLE_NAME"] for r in cur.fetchall()]
for t in tables:
    print(t)

print()
print("=== 2) Columnas candidatas por tabla ===")
candidates = []
for t in tables:
    cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME=%s
    ORDER BY ORDINAL_POSITION
    """, (t,))
    cols = cur.fetchall()
    colnames = [c["COLUMN_NAME"] for c in cols]
    score = 0
    for k in ["ProductoID", "producto", "Costo", "costo", "Receta", "receta", "ServerID", "server"]:
        if any(k.lower() in c.lower() for c in colnames):
            score += 1
    if score >= 3:
        candidates.append((t, colnames))
        print()
        print("---", t, "---")
        print(colnames)

print()
print("=== 3) Estado actual Sync_Productos.CostoReceta ===")
cur.execute("""
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN ISNULL(CostoReceta,0)=0 THEN 1 ELSE 0 END) AS sin_costo,
    SUM(CASE WHEN ISNULL(CostoReceta,0)>0 THEN 1 ELSE 0 END) AS con_costo
FROM Sync_Productos
""")
print(cur.fetchone())

print()
print("=== 4) Intentar fuentes internas conocidas ===")

# Fuente 1: si existe Sync_Recetas con costo por producto
def table_exists(t):
    cur.execute("SELECT COUNT(*) AS cnt FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s", (t,))
    return cur.fetchone()["cnt"] > 0

def columns(t):
    cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=%s", (t,))
    return {r["COLUMN_NAME"] for r in cur.fetchall()}

updated = 0
source_used = None

if table_exists("Sync_Recetas"):
    cols = columns("Sync_Recetas")
    print("Sync_Recetas existe:", cols)

    producto_col = "ProductoID" if "ProductoID" in cols else "producto_id" if "producto_id" in cols else None
    server_col = "ServerID" if "ServerID" in cols else "server_id" if "server_id" in cols else None
    costo_col = None
    for c in ["CostoReceta", "CostoTotal", "Costo", "CostoUnitario", "costo_receta"]:
        if c in cols:
            costo_col = c
            break

    if producto_col and server_col and costo_col:
        cur.execute(f"""
        UPDATE sp
        SET
            sp.CostoReceta = x.CostoReceta,
            sp.FechaSync = GETDATE()
        FROM Sync_Productos sp
        INNER JOIN (
            SELECT
                CAST({server_col} AS NVARCHAR(100)) AS ServerID,
                CAST({producto_col} AS NVARCHAR(100)) AS ProductoID,
                MAX(CAST({costo_col} AS DECIMAL(18,4))) AS CostoReceta
            FROM Sync_Recetas
            WHERE ISNULL(CAST({costo_col} AS DECIMAL(18,4)),0) > 0
            GROUP BY CAST({server_col} AS NVARCHAR(100)), CAST({producto_col} AS NVARCHAR(100))
        ) x
          ON CAST(sp.ServerID AS NVARCHAR(100)) = x.ServerID
         AND CAST(sp.ProductoID AS NVARCHAR(100)) = x.ProductoID
        WHERE ISNULL(sp.CostoReceta,0)=0
        """)
        updated = cur.rowcount if cur.rowcount is not None else 0
        source_used = "Sync_Recetas"

# Fuente 2: buscar tabla con ProductoID/ServerID/CostoReceta
if not source_used:
    for t, colnames in candidates:
        cols = set(colnames)
        producto_col = "ProductoID" if "ProductoID" in cols else None
        server_col = "ServerID" if "ServerID" in cols else None
        costo_col = None
        for c in ["CostoReceta", "CostoTotal", "Costo", "CostoUnitario"]:
            if c in cols:
                costo_col = c
                break

        if producto_col and server_col and costo_col and t != "Sync_Productos":
            print("Probando fuente:", t, producto_col, server_col, costo_col)
            try:
                cur.execute(f"""
                UPDATE sp
                SET
                    sp.CostoReceta = x.CostoReceta,
                    sp.FechaSync = GETDATE()
                FROM Sync_Productos sp
                INNER JOIN (
                    SELECT
                        CAST({server_col} AS NVARCHAR(100)) AS ServerID,
                        CAST({producto_col} AS NVARCHAR(100)) AS ProductoID,
                        MAX(CAST({costo_col} AS DECIMAL(18,4))) AS CostoReceta
                    FROM {t}
                    WHERE ISNULL(CAST({costo_col} AS DECIMAL(18,4)),0) > 0
                    GROUP BY CAST({server_col} AS NVARCHAR(100)), CAST({producto_col} AS NVARCHAR(100))
                ) x
                  ON CAST(sp.ServerID AS NVARCHAR(100)) = x.ServerID
                 AND CAST(sp.ProductoID AS NVARCHAR(100)) = x.ProductoID
                WHERE ISNULL(sp.CostoReceta,0)=0
                """)
                updated = cur.rowcount if cur.rowcount is not None else 0
                if updated and updated > 0:
                    source_used = t
                    break
            except Exception as e:
                print("No aplicó", t, str(e)[:250])

if source_used:
    cn.commit()
else:
    cn.rollback()

print()
print("=== 5) Resultado actualización ===")
print({
    "source_used": source_used,
    "updated": updated
})

print()
print("=== 6) Estado final Sync_Productos.CostoReceta ===")
cur.execute("""
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN ISNULL(CostoReceta,0)=0 THEN 1 ELSE 0 END) AS sin_costo,
    SUM(CASE WHEN ISNULL(CostoReceta,0)>0 THEN 1 ELSE 0 END) AS con_costo
FROM Sync_Productos
""")
print(cur.fetchone())

print()
print("=== 7) Por servidor ===")
cur.execute("""
SELECT
    ServerID,
    COUNT(*) AS total,
    SUM(CASE WHEN ISNULL(CostoReceta,0)=0 THEN 1 ELSE 0 END) AS sin_costo,
    SUM(CASE WHEN ISNULL(CostoReceta,0)>0 THEN 1 ELSE 0 END) AS con_costo
FROM Sync_Productos
GROUP BY ServerID
ORDER BY total DESC
""")
for r in cur.fetchall():
    print(r)

cn.close()
