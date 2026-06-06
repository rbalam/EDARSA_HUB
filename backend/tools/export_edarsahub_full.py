"""
export_edarsahub_full.py - EDARSAHUB

Exporta TODAS las tablas base de EDARSAHUB SQL a JSON y genera un ZIP descargable.

Arquitectura (MÁXIMA DE ORO):
- Usa la conexión canónica `core.sql_first.db` (pymssql). NO duplica conexiones ni drivers.
- Solo lectura (SELECT). No modifica la base.
- Escritura incremental por lotes (fetchmany) para no cargar tablas enormes en memoria.

Salida:
- JSON por tabla + _RESUMEN_BACKUP.json en un directorio temporal.
- ZIP final en /app/backend/static/downloads (servido en /static/downloads/...).
"""
import os
import sys
import json
import zipfile
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Permitir importar el paquete `core` del backend
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from core.sql_first.db import get_sql_connection  # conexión canónica

BATCH = 2000
STATIC_DOWNLOADS = BACKEND_DIR / "static" / "downloads"
STATIC_DOWNLOADS.mkdir(parents=True, exist_ok=True)


def _conv(val):
    if isinstance(val, (datetime,)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (bytes, bytearray)):
        try:
            return val.decode("utf-8", errors="replace")
        except Exception:
            return val.hex()
    return val


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmpdir = Path(tempfile.mkdtemp(prefix="edarsahub_sql_export_"))
    zip_path = STATIC_DOWNLOADS / f"EDARSAHUB_SQL_COMPLETO_LIMPIO_{ts}.zip"

    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
    )
    tables = cur.fetchall()
    print(f"Total tablas base: {len(tables)}", flush=True)

    summary = []
    for schema, table in tables:
        full_name = f"[{schema}].[{table}]"
        safe_name = f"{schema}.{table}.json"
        file_path = tmpdir / safe_name
        total = 0
        try:
            c2 = conn.cursor()
            c2.execute(f"SELECT * FROM {full_name}")
            cols = [d[0] for d in c2.description]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("[")
                first = True
                while True:
                    rows = c2.fetchmany(BATCH)
                    if not rows:
                        break
                    for r in rows:
                        item = {cols[i]: _conv(r[i]) for i in range(len(cols))}
                        if not first:
                            f.write(",")
                        f.write(json.dumps(item, ensure_ascii=False, default=str))
                        first = False
                        total += 1
                f.write("]")
            summary.append({"schema": schema, "table": table, "rows": total, "file": safe_name})
            print(f"OK {schema}.{table} -> {total} rows", flush=True)
        except Exception as e:
            summary.append({"schema": schema, "table": table, "rows": None, "file": None, "error": str(e)})
            print(f"ERROR {schema}.{table}: {e}", flush=True)

    with open(tmpdir / "_RESUMEN_BACKUP.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    conn.close()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(tmpdir.glob("*.json")):
            zf.write(p, arcname=p.name)

    # limpieza del temporal
    for p in tmpdir.glob("*"):
        p.unlink()
    tmpdir.rmdir()

    ok = sum(1 for s in summary if s.get("rows") is not None)
    err = len(summary) - ok
    rows_total = sum(s["rows"] for s in summary if s.get("rows"))
    print("==== EXPORT TERMINADO ====", flush=True)
    print(f"Tablas OK: {ok} | Tablas con error: {err} | Filas totales: {rows_total}", flush=True)
    print(f"ZIP: {zip_path}", flush=True)
    print(f"ZIP_NAME={zip_path.name}", flush=True)


if __name__ == "__main__":
    main()
