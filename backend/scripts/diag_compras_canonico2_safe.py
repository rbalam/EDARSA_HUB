import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection

c = get_sql_connection().cursor(as_dict=True)

def info(t):
    try:
        c.execute(f"SELECT COUNT(*) n FROM [{t}]"); n = c.fetchone()["n"]
        c.execute(
            "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME=%s AND (COLUMN_NAME LIKE '%Producto%' OR COLUMN_NAME LIKE '%Almacen%' "
            "OR COLUMN_NAME LIKE '%Insumo%' OR COLUMN_NAME LIKE '%Codigo%' OR COLUMN_NAME LIKE '%Sucursal%')",
            (t,),
        )
        idc = [(r["COLUMN_NAME"], r["DATA_TYPE"]) for r in c.fetchall()]
        print(f"  {t}: filas={n}")
        for col, dt in idc:
            print(f"        {col} ({dt})")
    except Exception as e:
        print(f"  {t}: ERROR {str(e)[:80]}")

print("=== Tablas inventario/compras canónicas ===")
for t in ["Sync_Inventory", "Sync_Purchases", "Compras_Inventarios_Fisicos_Sync",
          "Compras_Requisiciones_Sync", "Compras_Pedidos", "Compras_PedidosDetalle",
          "Producto_Presentaciones", "RH_Cat_Sucursales"]:
    info(t)
