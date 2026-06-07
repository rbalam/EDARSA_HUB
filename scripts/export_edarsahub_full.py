#!/usr/bin/env python3
"""
ZIP COMBINADO LIMPIO (Opción C): BD EDARSAHUB (auditoria JSON) + codigo backend + frontend.
- BD: solo lectura, sin temporales, sin modificar datos, credenciales REDACTADAS.
- Codigo: sin node_modules/venv/__pycache__/.git/.env/build/cache/auditorias/backups/zips.
- Un solo ZIP final, sin ZIPs anidados.
"""
import os, re, json, shutil, zipfile, decimal, datetime, uuid
from core.sql_first.db import get_sql_connection

CAP = 2000
TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
DB = os.environ.get("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
WORK = f"/tmp/edarsahub_full_{TS}"
DBDIR = os.path.join(WORK, "database_audit")
DATA_DIR = os.path.join(DBDIR, "data")
PUBLIC_DIR = "/app/frontend/public"
ZIP_NAME = f"EDARSAHUB_FULL_AUDITORIA_LIMPIO_{TS}.zip"
ZIP_PATH = os.path.join(PUBLIC_DIR, ZIP_NAME)

SENSITIVE = ["password", "passwd", "pwd", "contrasena", "contrase\u00f1a", "hash",
             "token", "secret", "apikey", "api_key", "claveacceso", "clave_acceso",
             "privatekey", "private_key", "secretkey", "salt"]
def is_sensitive(c): 
    c = c.lower(); return any(s in c for s in SENSITIVE)

EXCL_SUBSTR = ["backup", "bkp", "_old", "_tmp", "temp_", "_copia", "_copy", "_respaldo"]
def is_excluded_table(n):
    n = n.lower()
    return any(s in n for s in EXCL_SUBSTR) or bool(re.search(r"_\d{8}", n))

def jdefault(o):
    if isinstance(o, decimal.Decimal): return float(o)
    if isinstance(o, (datetime.datetime, datetime.date)): return o.isoformat()
    if isinstance(o, (bytes, bytearray)): return f"<binary {len(o)} bytes>"
    if isinstance(o, uuid.UUID): return str(o)
    return str(o)

# ---------- 1) EXPORT BD ----------
def export_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_sql_connection(); cur = conn.cursor()
    cur.execute("""SELECT t.name, SUM(p.rows) FROM sys.tables t
        JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN (0,1)
        GROUP BY t.name ORDER BY t.name""")
    all_tables = [(r[0], int(r[1] or 0)) for r in cur.fetchall()]
    cur.execute("""SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE,IS_NULLABLE,CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS ORDER BY TABLE_NAME,ORDINAL_POSITION""")
    schema = {}
    for tn, cn, dt, nn, ml in cur.fetchall():
        schema.setdefault(tn, []).append({"columna": cn, "tipo": dt, "nullable": nn == "YES",
                                          "max_len": ml, "sensible_redactada": is_sensitive(cn)})
    catalogo, errores, omitidas = [], [], []
    n_exp = filas_exp = 0
    for tabla, filas in all_tables:
        if is_excluded_table(tabla):
            omitidas.append({"tabla": tabla, "filas": filas, "motivo": "backup/duplicado/temporal"}); continue
        cm = schema.get(tabla, [])
        sens = [c["columna"] for c in cm if c["sensible_redactada"]]
        reg = {"tabla": tabla, "filas_totales": filas, "columnas": cm, "columnas_redactadas": sens,
               "truncado": filas > CAP, "filas_exportadas": 0, "datos": []}
        try:
            c2 = conn.cursor(); c2.execute(f"SELECT TOP ({CAP}) * FROM [dbo].[{tabla}]")
            cols = [d[0] for d in c2.description]
            data = [{c: ("***REDACTED***" if (v is not None and is_sensitive(c)) else v)
                     for c, v in zip(cols, row)} for row in c2.fetchall()]
            reg["datos"] = data; reg["filas_exportadas"] = len(data)
            n_exp += 1; filas_exp += len(data)
        except Exception as e:
            reg["error"] = str(e)[:300]; errores.append({"tabla": tabla, "error": str(e)[:300]})
        with open(os.path.join(DATA_DIR, f"{tabla}.json"), "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, default=jdefault, indent=1)
        catalogo.append({"tabla": tabla, "filas_totales": filas, "filas_exportadas": reg["filas_exportadas"],
                         "truncado": reg["truncado"], "con_error": "error" in reg})
    conn.close()
    total = sum(f for _, f in all_tables)
    with open(os.path.join(DBDIR, "_RESUMEN_BACKUP.json"), "w", encoding="utf-8") as f:
        json.dump({"base_exportada": DB, "generado": datetime.datetime.now().isoformat(),
                   "limite_filas_por_tabla": CAP, "tablas_en_bd": len(all_tables),
                   "tablas_exportadas": n_exp, "tablas_omitidas_backup_dup": len(omitidas),
                   "tablas_con_error": len(errores), "filas_totales_bd_aprox": total,
                   "filas_exportadas_muestra": filas_exp,
                   "redaccion": "password/hash/token/secret/key -> ***REDACTED***"}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DBDIR, "_CATALOGO_TABLAS.json"), "w", encoding="utf-8") as f:
        json.dump(catalogo, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DBDIR, "_TABLAS_OMITIDAS.json"), "w", encoding="utf-8") as f:
        json.dump(omitidas, f, ensure_ascii=False, indent=2)
    if errores:
        with open(os.path.join(DBDIR, "_ERRORES_EXPORTACION.json"), "w", encoding="utf-8") as f:
            json.dump(errores, f, ensure_ascii=False, indent=2)
    return {"tablas_exportadas": n_exp, "tablas_omitidas": len(omitidas),
            "tablas_con_error": len(errores), "filas_muestra": filas_exp, "filas_bd_aprox": total}

# ---------- 2) COPIA CODIGO (con exclusiones) ----------
BACK_SKIP_DIR = {"__pycache__", ".git", "node_modules", "htmlcov", ".ruff_cache",
                 ".pytest_cache", "venv", ".venv"}
def ig_backend(d, names):
    skip = set()
    for n in names:
        low = n.lower()
        if n in BACK_SKIP_DIR or n.startswith("auditorias_") or n.startswith("backup_") \
           or n == ".env" or low.endswith(".pyc") or low.endswith(".log") or low.endswith(".zip"):
            skip.add(n)
    return skip

FRONT_SKIP_DIR = {"node_modules", "build", "dist", "coverage", ".git", ".turbo", ".cache"}
def ig_frontend(d, names):
    skip = set()
    for n in names:
        low = n.lower()
        if n in FRONT_SKIP_DIR or n == ".env" or low.endswith(".zip") \
           or n.startswith("EDARSAHUB_"):
            skip.add(n)
    return skip

def main():
    for d in os.listdir("/tmp"):
        if d.startswith("edarsahub_full_"):
            shutil.rmtree(os.path.join("/tmp", d), ignore_errors=True)
    for f in os.listdir(PUBLIC_DIR):
        if f.startswith("EDARSAHUB_FULL_AUDITORIA_LIMPIO_") and f.endswith(".zip"):
            os.remove(os.path.join(PUBLIC_DIR, f))
    os.makedirs(WORK, exist_ok=True)

    db_stats = export_db()
    shutil.copytree("/app/backend", os.path.join(WORK, "backend"), ignore=ig_backend)
    shutil.copytree("/app/frontend", os.path.join(WORK, "frontend"), ignore=ig_frontend)

    # Barrido final anti-secretos: borrar cualquier .env que se haya colado
    env_found = []
    for root, dirs, files in os.walk(WORK):
        for fn in files:
            if fn == ".env" or fn.endswith(".env"):
                os.remove(os.path.join(root, fn)); env_found.append(os.path.relpath(os.path.join(root, fn), WORK))
            if fn.lower().endswith(".zip"):
                os.remove(os.path.join(root, fn))

    with open(os.path.join(WORK, "_MANIFIESTO.json"), "w", encoding="utf-8") as f:
        json.dump({"generado": datetime.datetime.now().isoformat(),
                   "contenido": ["database_audit/ (JSON BD EDARSAHUB, credenciales redactadas)",
                                 "backend/ (codigo .py, sin __pycache__/.env/auditorias/backups/logs)",
                                 "frontend/ (sin node_modules/build/.env/zips)"],
                   "db": db_stats, "env_eliminados": env_found,
                   "nota": "Sin ZIPs anidados. Sin credenciales."}, f, ensure_ascii=False, indent=2)

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, dirs, files in os.walk(WORK):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, WORK))
    size = os.path.getsize(ZIP_PATH)
    # contar archivos
    with zipfile.ZipFile(ZIP_PATH) as z:
        nfiles = len(z.namelist())
        nested = [x for x in z.namelist() if x.lower().endswith(".zip")]
        envs = [x for x in z.namelist() if x.endswith(".env")]
    shutil.rmtree(WORK, ignore_errors=True)
    print(json.dumps({"zip": ZIP_PATH, "tamano_mb": round(size/1024/1024, 2), "archivos": nfiles,
                      "zips_anidados": nested, "envs_en_zip": envs, "db": db_stats,
                      "env_eliminados": env_found}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
