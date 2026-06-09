"""
PRUEBA (solo lectura, sin escritura) de que NO existe una tabla puente
equivalente POS->ProductoID(int) keyed por (ServerID/Origen + CodigoFuente).

Criterio de "puente equivalente":
  - tener una columna ProductoID de tipo int (no GUID), Y
  - tener alguna columna de codigo de origen (Codigo*/CodigoFuente/idinsumo...), Y
  - tener alguna columna de dimension de origen (ServerID/Server/Origen/SystemType/Unidad).
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection

c = get_sql_connection().cursor(as_dict=True)

# 1) Tablas que tienen ProductoID de tipo INT
c.execute("""
    SELECT TABLE_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE COLUMN_NAME = 'ProductoID'
""")
prod_int = {r["TABLE_NAME"] for r in c.fetchall() if r["DATA_TYPE"] in ("int", "bigint", "smallint")}
print(f"Tablas con ProductoID int/bigint: {sorted(prod_int)}")

# 2) De esas, cuales tambien tienen columna de codigo de origen Y dimension de origen
print("\n=== Evaluacion de cada candidata como PUENTE POS->int ===")
puentes = []
for t in sorted(prod_int):
    c.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=%s", (t,))
    cols = [r["COLUMN_NAME"].lower() for r in c.fetchall()]
    tiene_codigo = any(k in col for col in cols for k in ["codigofuente", "codigoorigen", "idinsumo", "codigopos", "claveorigen"])
    tiene_dim = any(k in col for col in cols for k in ["serverid", "servidorid", "origensistema", "systemtype", "unidadnegocio"])
    es_puente = tiene_codigo and tiene_dim
    print(f"  {t:<38} codigo_origen={tiene_codigo} dim_origen={tiene_dim} -> {'PUENTE' if es_puente else 'no'}")
    if es_puente:
        puentes.append(t)

print("\n=== RESULTADO ===")
if puentes:
    print(f"  EXISTE puente potencial: {puentes}")
else:
    print("  NO existe ninguna tabla puente equivalente POS->ProductoID(int). Confirmado.")

# 3) Mostrar tablas *Mapeo*/*Equivalent*/*Origen* para descartar manualmente
print("\n=== Tablas candidatas por nombre (Mapeo/Equivalent/Origen) ===")
c.execute("""
    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE='BASE TABLE' AND (
        TABLE_NAME LIKE '%Mapeo%' OR TABLE_NAME LIKE '%Equivalent%' OR TABLE_NAME LIKE '%Origen%')
    ORDER BY TABLE_NAME
""")
for r in c.fetchall():
    print("  ", r["TABLE_NAME"])
