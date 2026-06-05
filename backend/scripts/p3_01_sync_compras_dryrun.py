import os
from pathlib import Path
from datetime import datetime
import pymssql

def load_env():
    env = Path("/app/backend/.env")
    if env.exists():
        for line in env.read_text(errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def conn():
    return pymssql.connect(
        server=os.getenv("EDARSAHUB_SQL_HOST"),
        port=int(os.getenv("EDARSAHUB_SQL_PORT", "1433")),
        user=os.getenv("EDARSAHUB_SQL_USER"),
        password=os.getenv("EDARSAHUB_SQL_PASSWORD"),
        database=os.getenv("EDARSAHUB_SQL_DATABASE"),
        login_timeout=10,
        timeout=30
    )

load_env()
cn = conn()
cur = cn.cursor(as_dict=True)

print("P3-01 SYNC_COMPRAS DRY-RUN")
print("Fecha:", datetime.now())
print("Base:", os.getenv("EDARSAHUB_SQL_DATABASE"))
print("Modo: DRY-RUN, NO INSERTA")
print()

targets = [
    "Compras_Sync",
    "Compras_Pedidos",
    "Compras_PedidosDetalle",
    "Compras_Ordenes",
    "Compras_Recepciones",
]

print("=== 1) TABLAS DESTINO ===")
for t in targets:
    try:
        cur.execute("""
        SELECT COUNT(*) AS existe
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME=%s
        """, (t,))
        existe = cur.fetchone()["existe"]
        if not existe:
            print(f"{t}: NO EXISTE")
            continue

        cur.execute(f"SELECT COUNT(*) AS total FROM {t}")
        total = cur.fetchone()["total"]
        print(f"{t}: OK registros={total}")

        cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME=%s
        ORDER BY ORDINAL_POSITION
        """, (t,))
        for c in cur.fetchall():
            print(f"  - {c['COLUMN_NAME']} | {c['DATA_TYPE']} | nullable={c['IS_NULLABLE']}")
    except Exception as e:
        print(f"{t}: ERROR {e}")

print()
print("=== 2) FUENTES SQL DISPONIBLES PARA COMPRAS ===")
cur.execute("""
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE='BASE TABLE'
  AND (
        TABLE_NAME LIKE '%Compra%'
     OR TABLE_NAME LIKE '%Pedido%'
     OR TABLE_NAME LIKE '%Orden%'
     OR TABLE_NAME LIKE '%Recepcion%'
     OR TABLE_NAME LIKE '%Proveedor%'
     OR TABLE_NAME LIKE '%Sync%'
  )
ORDER BY TABLE_NAME
""")
for r in cur.fetchall():
    print(f"{r['TABLE_SCHEMA']}.{r['TABLE_NAME']}")

print()
print("=== 3) SERVIDORES ACTIVOS FUENTE ===")
cur.execute("""
SELECT id, nombre, system_type, tipo_conexion, EmpresaID, database_name
FROM Servidores_Conexiones
WHERE ISNULL(activo,1)=1
ORDER BY nombre
""")
servers = cur.fetchall()
for s in servers:
    print(s)

print()
print("=== 4) VALIDAR TABLAS DESTINO POR CAMPOS CLAVE ===")
expected = {
    "Compras_Pedidos": ["Proveedor", "Fecha", "Total", "Estado", "Empresa", "Sucursal", "Server"],
    "Compras_PedidosDetalle": ["Producto", "Cantidad", "Costo", "Pedido"],
    "Compras_Ordenes": ["Proveedor", "Fecha", "Total", "Estado", "Empresa", "Sucursal"],
    "Compras_Recepciones": ["Proveedor", "Fecha", "Total", "Almacen", "Orden"],
}

for table, keys in expected.items():
    print(f"\n--- {table} ---")
    try:
        cur.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME=%s
        """, (table,))
        cols = [x["COLUMN_NAME"] for x in cur.fetchall()]
        low = [c.lower() for c in cols]
        print("Columnas:", cols)
        for k in keys:
            found = [c for c in cols if k.lower() in c.lower()]
            print(f"{k}: {found if found else 'NO_DETECTADO'}")
    except Exception as e:
        print("ERROR:", e)

print()
print("=== 5) DICTAMEN DRY-RUN ===")
print("No se insertó información.")
print("Si tablas destino existen y campos clave están presentes, siguiente paso: script de sync incremental por servidor.")
cn.close()
