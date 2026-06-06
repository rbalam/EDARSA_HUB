import os
import sys
sys.path.insert(0, '/app/backend')

import pymssql
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
import uuid

from core.config.edarsahub_config import get_edarsahub_sql_config

OUT_DIR = Path(os.environ["OUT_DIR"])

TABLES = [
    "Comercial_KPIs_Diarios_v2",
    "Sync_Precios_Historicos",
    "Servidores_Conexiones",
    "Sync_Productos",
    "Usuario_Roles",
    "Usuario_Catalogo",
]

cfg = get_edarsahub_sql_config()
cn = pymssql.connect(
    server=cfg.host,
    port=cfg.port,
    database=cfg.database,
    user=cfg.user,
    password=cfg.password,
    timeout=60,
    as_dict=False
)

cur = cn.cursor()

def serialize_value(v):
    if v is None:
        return "NULL"
    elif isinstance(v, bool):
        return "1" if v else "0"
    elif isinstance(v, (int, float, Decimal)):
        return str(v)
    elif isinstance(v, datetime):
        return f"'{v.strftime('%Y-%m-%d %H:%M:%S.%f')[:23]}'"
    elif isinstance(v, date):
        return f"'{v.strftime('%Y-%m-%d')}'"
    elif isinstance(v, uuid.UUID):
        return f"'{str(v)}'"
    elif isinstance(v, bytes):
        return f"0x{v.hex()}"
    else:
        safe = str(v).replace("'", "''")
        return f"N'{safe}'"

summary = []
for table in TABLES:
    print(f"Exportando {table}...")
    
    # Obtener columnas
    cur.execute(f"""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table}' 
        ORDER BY ORDINAL_POSITION
    """)
    cols = [r[0] for r in cur.fetchall()]
    
    # Obtener datos
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()

    file = OUT_DIR / f"{table}.sql"
    with file.open("w", encoding="utf-8") as f:
        f.write(f"-- Backup lógico {table}\n")
        f.write(f"-- Fecha: {datetime.now()}\n")
        f.write(f"-- Registros: {len(rows)}\n\n")

        for row in rows:
            values = [serialize_value(v) for v in row]
            f.write(
                f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(values)});\n"
            )

    summary.append((table, len(rows), str(file)))
    print(f"  -> {len(rows)} registros")

with (OUT_DIR / "RESUMEN_BACKUP.txt").open("w", encoding="utf-8") as f:
    f.write("BACKUP LÓGICO TABLAS CRÍTICAS SQL-FIRST\n")
    f.write(f"Fecha: {datetime.now()}\n\n")
    for t, count, filepath in summary:
        f.write(f"{t}: {count} registros | {filepath}\n")

cn.close()

print(f"\nOK backup generado: {OUT_DIR}")
