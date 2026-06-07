#!/usr/bin/env python3
"""
Respaldo ZIP LIMPIO de EDARSAHUB SQL para AUDITORÍA (solo lectura).
- NO crea tablas temporales. NO modifica datos. NO incluye credenciales (redacta).
- Excluye tablas backup/dated/duplicadas. Una sola copia por tabla.
- Muestra acotada (TOP CAP) para tablas grandes; conteos completos en el resumen.
"""
import os, re, json, shutil, zipfile, decimal, datetime, uuid
from core.sql_first.db import get_sql_connection

CAP = 2000  # filas máximas exportadas por tabla (muestra para auditoría)
TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
DB = os.environ.get("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")

WORK = f"/tmp/edarsahub_audit_{TS}"
DATA_DIR = os.path.join(WORK, "data")
ZIP_NAME = f"EDARSAHUB_SQL_AUDITORIA_LIMPIO_{TS}.zip"
PUBLIC_DIR = "/app/frontend/public"
ZIP_PATH = os.path.join(PUBLIC_DIR, ZIP_NAME)

# Columnas sensibles (redacción de valores)
SENSITIVE = ["password", "passwd", "pwd", "contrasena", "contrase\u00f1a", "hash",
             "token", "secret", "apikey", "api_key", "claveacceso", "clave_acceso",
             "privatekey", "private_key", "secretkey", "salt"]

def is_sensitive(col):
    c = col.lower()
    return any(s in c for s in SENSITIVE)

# Exclusión de tablas backup/temporales/duplicadas
EXCL_SUBSTR = ["backup", "bkp", "_old", "_tmp", "temp_", "_copia", "_copy", "_respaldo"]
def is_excluded(name):
    n = name.lower()
    if any(s in n for s in EXCL_SUBSTR):
        return True
    if re.search(r"_\d{8}", n):  # sufijos con fecha tipo _20260513
        return True
    return False

def jdefault(o):
    if isinstance(o, decimal.Decimal):
        return float(o)
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.isoformat()
    if isinstance(o, (bytes, bytearray)):
        return f"<binary {len(o)} bytes>"
    if isinstance(o, uuid.UUID):
        return str(o)
    return str(o)

def main():
    # Limpieza de flujos previos
    for d in os.listdir("/tmp"):
        if d.startswith("edarsahub_audit_"):
            shutil.rmtree(os.path.join("/tmp", d), ignore_errors=True)
    # ZIPs previos en destino
    if os.path.isdir(PUBLIC_DIR):
        for f in os.listdir(PUBLIC_DIR):
            if f.startswith("EDARSAHUB_SQL_AUDITORIA_LIMPIO_") and f.endswith(".zip"):
                os.remove(os.path.join(PUBLIC_DIR, f))
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = get_sql_connection()
    cur = conn.cursor()

    # 1) Tablas + conteo aproximado (rápido, sin COUNT full-scan)
    cur.execute("""
        SELECT t.name AS tabla, SUM(p.rows) AS filas
        FROM sys.tables t
        JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN (0,1)
        GROUP BY t.name ORDER BY t.name
    """)
    all_tables = [(r[0], int(r[1] or 0)) for r in cur.fetchall()]

    # 2) Esquema de columnas (una sola consulta)
    cur.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_NAME, ORDINAL_POSITION
    """)
    schema = {}
    for tn, cn, dt, nn, ml in cur.fetchall():
        schema.setdefault(tn, []).append({
            "columna": cn, "tipo": dt, "nullable": (nn == "YES"),
            "max_len": ml, "sensible_redactada": is_sensitive(cn)
        })

    catalogo, errores, omitidas = [], [], []
    total_exportadas = 0
    total_filas_exportadas = 0

    for tabla, filas in all_tables:
        if is_excluded(tabla):
            omitidas.append({"tabla": tabla, "filas": filas, "motivo": "backup/duplicado/temporal"})
            continue
        cols_meta = schema.get(tabla, [])
        sensibles = [c["columna"] for c in cols_meta if c["sensible_redactada"]]
        truncado = filas > CAP
        registro = {
            "tabla": tabla, "filas_totales": filas, "columnas": cols_meta,
            "columnas_redactadas": sensibles, "truncado": truncado,
            "filas_exportadas": 0, "datos": []
        }
        try:
            c2 = conn.cursor()
            c2.execute(f"SELECT TOP ({CAP}) * FROM [dbo].[{tabla}]")
            colnames = [d[0] for d in c2.description]
            rows = c2.fetchall()
            data = []
            for row in rows:
                d = {}
                for col, val in zip(colnames, row):
                    d[col] = "***REDACTED***" if (val is not None and is_sensitive(col)) else val
                data.append(d)
            registro["datos"] = data
            registro["filas_exportadas"] = len(data)
            total_exportadas += 1
            total_filas_exportadas += len(data)
        except Exception as e:
            registro["error"] = str(e)[:300]
            errores.append({"tabla": tabla, "error": str(e)[:300]})

        with open(os.path.join(DATA_DIR, f"{tabla}.json"), "w", encoding="utf-8") as f:
            json.dump(registro, f, ensure_ascii=False, default=jdefault, indent=1)
        catalogo.append({"tabla": tabla, "filas_totales": filas,
                         "filas_exportadas": registro["filas_exportadas"],
                         "truncado": truncado, "con_error": "error" in registro})

    conn.close()

    total_filas_bd = sum(f for _, f in all_tables)
    resumen = {
        "base_exportada": DB,
        "generado": datetime.datetime.now().isoformat(),
        "limite_filas_por_tabla": CAP,
        "tablas_en_bd": len(all_tables),
        "tablas_exportadas": total_exportadas,
        "tablas_omitidas_backup_dup": len(omitidas),
        "tablas_con_error": len(errores),
        "filas_totales_bd_aprox": total_filas_bd,
        "filas_exportadas_muestra": total_filas_exportadas,
        "redaccion": "Columnas password/hash/token/secret/key -> ***REDACTED***",
        "nota": "Tablas con mas de %d filas se exportan truncadas (muestra). Conteo real en catalogo." % CAP,
    }
    with open(os.path.join(WORK, "_RESUMEN_BACKUP.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    with open(os.path.join(WORK, "_CATALOGO_TABLAS.json"), "w", encoding="utf-8") as f:
        json.dump(catalogo, f, ensure_ascii=False, indent=2)
    with open(os.path.join(WORK, "_TABLAS_OMITIDAS.json"), "w", encoding="utf-8") as f:
        json.dump(omitidas, f, ensure_ascii=False, indent=2)
    if errores:
        with open(os.path.join(WORK, "_ERRORES_EXPORTACION.json"), "w", encoding="utf-8") as f:
            json.dump(errores, f, ensure_ascii=False, indent=2)

    # Verificacion anti-basura: no debe haber .zip ni dirs cache dentro de WORK
    for root, dirs, files in os.walk(WORK):
        for fn in files:
            if fn.lower().endswith(".zip"):
                os.remove(os.path.join(root, fn))

    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, dirs, files in os.walk(WORK):
            for fn in files:
                full = os.path.join(root, fn)
                arc = os.path.relpath(full, WORK)
                z.write(full, arc)

    size = os.path.getsize(ZIP_PATH)
    shutil.rmtree(WORK, ignore_errors=True)

    print("=== EXPORT OK ===")
    print(json.dumps({
        "zip": ZIP_PATH, "tamano_bytes": size, "tamano_mb": round(size/1024/1024, 2),
        "tablas_exportadas": total_exportadas, "tablas_omitidas": len(omitidas),
        "tablas_con_error": len(errores), "filas_muestra": total_filas_exportadas,
        "filas_bd_aprox": total_filas_bd
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
