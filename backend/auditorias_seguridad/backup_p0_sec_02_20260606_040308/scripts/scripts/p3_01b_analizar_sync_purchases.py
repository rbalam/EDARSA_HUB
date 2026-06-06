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
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

cn = pymssql.connect(
    server=os.getenv("EDARSAHUB_SQL_HOST"),
    port=int(os.getenv("EDARSAHUB_SQL_PORT", "1433")),
    user=os.getenv("EDARSAHUB_SQL_USER"),
    password=os.getenv("EDARSAHUB_SQL_PASSWORD"),
    database=os.getenv("EDARSAHUB_SQL_DATABASE"),
    login_timeout=10,
    timeout=30
)

cur = cn.cursor(as_dict=True)

print("P3-01B ANALISIS Sync_Purchases")
print("Fecha:", datetime.now())
print()

tables = ["Sync_Purchases", "Compras", "Compras_Detalle", "Compras_Pedidos", "Compras_PedidosDetalle", "Compras_Ordenes", "Compras_Recepciones", "Compras_Sync_Checkpoint", "Compras_Sync_Log"]

for t in tables:
    print("\n" + "="*100)
    print(t)
    print("="*100)

    cur.execute("""
    SELECT COUNT(*) AS existe
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_NAME=%s
    """, (t,))
    if not cur.fetchone()["existe"]:
        print("NO EXISTE")
        continue

    cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME=%s
    ORDER BY ORDINAL_POSITION
    """, (t,))
    cols = cur.fetchall()
    print("COLUMNAS:")
    for c in cols:
        print(f"- {c['COLUMN_NAME']} | {c['DATA_TYPE']} | nullable={c['IS_NULLABLE']}")

    try:
        cur.execute(f"SELECT COUNT(*) AS total FROM {t}")
        total = cur.fetchone()["total"]
        print("REGISTROS:", total)
    except Exception as e:
        print("COUNT ERROR:", e)
        continue

    if total:
        try:
            cur.execute(f"SELECT TOP 5 * FROM {t}")
            print("MUESTRA:")
            for r in cur.fetchall():
                print(r)
        except Exception as e:
            print("MUESTRA ERROR:", e)

print("\n=== DICTAMEN AUTOMÁTICO ===")
try:
    cur.execute("SELECT COUNT(*) AS total FROM Sync_Purchases")
    total_sync = cur.fetchone()["total"]
except Exception:
    total_sync = -1

try:
    cur.execute("SELECT COUNT(*) AS total FROM Compras_Pedidos")
    total_pedidos = cur.fetchone()["total"]
except Exception:
    total_pedidos = -1

print("Sync_Purchases registros:", total_sync)
print("Compras_Pedidos registros:", total_pedidos)

if total_sync > 0:
    print("RECOMENDACIÓN: usar Sync_Purchases como fuente staging para poblar/actualizar Compras_Pedidos y detalles.")
else:
    print("RECOMENDACIÓN: construir sync incremental desde fuentes externas hacia tablas Compras_* existentes.")

cn.close()
