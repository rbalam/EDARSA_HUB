import os
import sys
sys.path.insert(0, '/app/backend')

import pymssql
from core.config.edarsahub_config import get_edarsahub_sql_config

cfg = get_edarsahub_sql_config()

cn = pymssql.connect(
    server=cfg.host,
    port=cfg.port,
    database=cfg.database,
    user=cfg.user,
    password=cfg.password,
    timeout=30,
    as_dict=True
)

cur = cn.cursor()

print("=== BASE ACTUAL ===")
cur.execute("SELECT DB_NAME() AS db")
print(cur.fetchone()['db'])

print("\n=== TABLAS CRÍTICAS SQL-FIRST ===")
tables = [
    "Comercial_KPIs_Diarios_v2",
    "Sync_Precios_Historicos",
    "Servidores_Conexiones",
    "Servidores_Conexiones_Log",
    "Sync_Productos",
    "Usuario_Roles",
    "Usuario_Permisos", 
    "Usuario_Catalogo",
]

for t in tables:
    cur.execute("""
    SELECT COUNT(*) AS cnt
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_NAME = %s
    """, (t,))
    exists = cur.fetchone()['cnt']

    if not exists:
        print(f"{t}: NO EXISTE")
        continue

    cur.execute(f"SELECT COUNT(*) AS cnt FROM {t}")
    count = cur.fetchone()['cnt']
    print(f"{t}: OK | registros={count}")

print("\n=== ESQUEMA Servidores_Conexiones ===")
cur.execute("""
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Servidores_Conexiones'
ORDER BY ORDINAL_POSITION
""")
for r in cur.fetchall():
    print(f"  {r['COLUMN_NAME']}: {r['DATA_TYPE']}")

print("\n=== SERVIDORES_CONEXIONES (TOP 20) ===")
cur.execute("SELECT TOP 20 * FROM Servidores_Conexiones ORDER BY 1 DESC")
for r in cur.fetchall():
    # Mostrar solo campos clave sin password
    safe = {k: v for k, v in r.items() if 'password' not in k.lower() and 'pwd' not in k.lower()}
    print(safe)

print("\n=== PRECIOS HISTÓRICOS POR SERVER ===")
cur.execute("""
SELECT ServerID, COUNT(*) AS productos
FROM Sync_Precios_Historicos
GROUP BY ServerID
ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"  {r['ServerID']}: {r['productos']} productos")

print("\n=== COMERCIAL KPIS JUNIO 2026 ===")
cur.execute("""
SELECT 
    server_id,
    unidad_negocio_id,
    COUNT(*) AS dias,
    SUM(ventas_netas) AS ventas,
    SUM(num_cheques) AS cheques,
    SUM(pax) AS pax
FROM Comercial_KPIs_Diarios_v2
WHERE fecha >= '2026-06-01'
  AND fecha <= '2026-06-30'
GROUP BY server_id, unidad_negocio_id
ORDER BY SUM(ventas_netas) DESC
""")
for r in cur.fetchall():
    print(f"  {r['server_id'][:8]}... | UN={r['unidad_negocio_id']} | {r['dias']} días | ${r['ventas']:,.0f} | {r['cheques']} tickets | {r['pax']} PAX")

cn.close()
print("\n=== AUDITORÍA COMPLETADA ===")
