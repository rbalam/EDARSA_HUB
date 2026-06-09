import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection

c = get_sql_connection().cursor(as_dict=True)

for t in ["Producto_Equivalentes", "Producto_Catalogo"]:
    c.execute(
        """SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE,
                  COLUMNPROPERTY(OBJECT_ID(TABLE_SCHEMA + '.' + TABLE_NAME), COLUMN_NAME, 'IsIdentity') AS is_id
           FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = %s ORDER BY ORDINAL_POSITION""",
        (t,),
    )
    print(f"=== {t} ===")
    for r in c.fetchall():
        print(f"  {r['COLUMN_NAME']:<28}{r['DATA_TYPE']:<14}null={r['IS_NULLABLE']} identity={r['is_id']}")

print("=== FKs relacionadas a Producto_Catalogo ===")
c.execute(
    """SELECT OBJECT_NAME(parent_object_id) AS t, OBJECT_NAME(referenced_object_id) AS ref
       FROM sys.foreign_keys
       WHERE OBJECT_NAME(parent_object_id) = 'Producto_Equivalentes'
          OR OBJECT_NAME(referenced_object_id) = 'Producto_Catalogo'"""
)
for r in c.fetchall():
    print("  ", dict(r))

print("=== Sync_Productos dims pobladas ===")
c.execute(
    "SELECT COUNT(DISTINCT UnidadNegocioID) AS u, COUNT(DISTINCT EmpresaID) AS e, "
    "SUM(CASE WHEN EsInventariable=1 THEN 1 ELSE 0 END) AS inventariables, COUNT(*) AS total "
    "FROM Sync_Productos"
)
print("  ", dict(c.fetchone()))
c.execute("SELECT DISTINCT UnidadNegocioID, ServerID FROM Sync_Productos")
print("  UnidadNegocioID/ServerID distintos en Sync_Productos:")
for r in c.fetchall():
    print("    ", dict(r))
