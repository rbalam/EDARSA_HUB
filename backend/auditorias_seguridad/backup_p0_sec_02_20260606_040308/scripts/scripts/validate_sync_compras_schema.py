import sys
sys.path.insert(0, '/app/backend')

import pymssql
from datetime import datetime
from core.config.edarsahub_config import get_edarsahub_sql_config

TABLE_PATTERNS = [
    "%sync%compra%",
    "%Sync%Compra%",
    "%compras%sync%",
    "%Compras%Sync%",
    "%pedido%",
    "%Pedido%",
    "%orden%compra%",
    "%Orden%Compra%",
    "%recepcion%",
    "%Recepcion%",
    "%requisicion%",
    "%Requisicion%",
]

cfg = get_edarsahub_sql_config()
cn = pymssql.connect(
    server=cfg.host,
    port=cfg.port,
    user=cfg.user,
    password=cfg.password,
    database=cfg.database,
    login_timeout=10,
    timeout=30
)
cur = cn.cursor(as_dict=True)

print("VALIDACIÓN SYNC_COMPRAS")
print("Fecha:", datetime.now())
print("DB:", cfg.database)
print()

print("=== TABLAS CANDIDATAS ===")
tables = set()

for pat in TABLE_PATTERNS:
    cur.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE='BASE TABLE'
      AND TABLE_NAME LIKE %s
    ORDER BY TABLE_NAME
    """, (pat,))
    for r in cur.fetchall():
        tables.add((r["TABLE_SCHEMA"], r["TABLE_NAME"]))

for schema, table in sorted(tables):
    print(f"  {schema}.{table}")

print()
print("=== COLUMNAS POR TABLA ===")

for schema, table in sorted(tables):
    print()
    print(f"--- {schema}.{table} ---")
    cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s
    ORDER BY ORDINAL_POSITION
    """, (schema, table))
    for c in cur.fetchall():
        length = c['CHARACTER_MAXIMUM_LENGTH'] or ''
        print(f"  {c['COLUMN_NAME']:30} | {c['DATA_TYPE']:15} | null={c['IS_NULLABLE']:3} | len={length}")

    try:
        cur.execute(f"SELECT COUNT(*) AS total FROM [{schema}].[{table}]")
        print(f"  REGISTROS: {cur.fetchone()['total']}")
    except Exception as e:
        print(f"  REGISTROS: ERROR {e}")

print()
print("=== REVISIÓN CAMPOS ESPERADOS ===")

expected_groups = {
    "identidad": ["id", "uuid", "folio", "pedido", "orden", "documento"],
    "empresa_unidad": ["empresa", "unidad", "sucursal", "server", "servidor"],
    "proveedor": ["proveedor", "rfc"],
    "fechas": ["fecha", "operacion", "emision", "recepcion", "sync"],
    "importes": ["subtotal", "iva", "impuesto", "total", "importe"],
    "estatus": ["estatus", "estado", "activo"],
}

for schema, table in sorted(tables):
    cur.execute("""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s
    """, (schema, table))
    cols = [r["COLUMN_NAME"].lower() for r in cur.fetchall()]

    print()
    print(f"--- {schema}.{table} ---")
    for group, keys in expected_groups.items():
        found = [c for c in cols if any(k in c for k in keys)]
        status = "✓" if found else "✗"
        print(f"  {status} {group}: {found if found else 'NO_DETECTADO'}")

cn.close()
print()
print("=== FIN VALIDACIÓN ===")
