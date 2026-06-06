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

print("P3-01C BLOQUEO COMPRAS SIN LIVE")
print("Fecha:", datetime.now())
print("Regla: NO LIVE, NO desencriptar credenciales, NO tocar servidores fuente")
print()

def q(title, sql):
    print("\n" + "="*100)
    print(title)
    print("="*100)
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        print("registros:", len(rows))
        for r in rows[:80]:
            print(r)
    except Exception as e:
        print("ERROR:", str(e)[:500])

q("1) ENCABEZADOS COMPRAS_PEDIDOS RESUMEN", """
SELECT
    COUNT(*) AS total_pedidos,
    SUM(CASE WHEN ISNULL(Total,0)=0 THEN 1 ELSE 0 END) AS pedidos_total_cero,
    SUM(CASE WHEN EXISTS (
        SELECT 1 FROM Compras_PedidosDetalle d
        WHERE d.PedidoCompraID = p.PedidoCompraID
    ) THEN 1 ELSE 0 END) AS pedidos_con_detalle,
    SUM(CASE WHEN NOT EXISTS (
        SELECT 1 FROM Compras_PedidosDetalle d
        WHERE d.PedidoCompraID = p.PedidoCompraID
    ) THEN 1 ELSE 0 END) AS pedidos_sin_detalle
FROM Compras_Pedidos p
""")

q("2) PEDIDOS SYNC SIN DETALLE / TOTAL CERO", """
SELECT TOP 100
    p.PedidoCompraID,
    p.FolioPedido,
    p.EmpresaID,
    p.SucursalID,
    p.ProveedorSugeridoID,
    p.FechaPedido,
    p.Total,
    p.MotivoCompra,
    p.CreatedAt,
    p.ModifiedAt
FROM Compras_Pedidos p
WHERE ISNULL(p.Total,0)=0
  AND NOT EXISTS (
      SELECT 1 FROM Compras_PedidosDetalle d
      WHERE d.PedidoCompraID = p.PedidoCompraID
  )
ORDER BY p.FechaPedido DESC
""")

q("3) LOGS COMPRAS SYNC RECIENTES", """
SELECT TOP 120 *
FROM Compras_Sync_Log
ORDER BY id DESC
""")

q("4) CHECKPOINTS COMPRAS", """
SELECT *
FROM Compras_Sync_Checkpoint
ORDER BY CheckpointID DESC
""")

q("5) COLUMNAS EXACTAS Compras_Sync_Log", """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME='Compras_Sync_Log'
ORDER BY ORDINAL_POSITION
""")

q("6) COLUMNAS EXACTAS Compras_Pedidos", """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME='Compras_Pedidos'
ORDER BY ORDINAL_POSITION
""")

q("7) COLUMNAS EXACTAS Compras_PedidosDetalle", """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME='Compras_PedidosDetalle'
ORDER BY ORDINAL_POSITION
""")

q("8) BUSCAR TABLAS STAGING/LEGACY CON DETALLES YA SINCRONIZADOS EN EDARSAHUB", """
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE='BASE TABLE'
AND (
       TABLE_NAME LIKE '%Detalle%'
    OR TABLE_NAME LIKE '%Pedido%'
    OR TABLE_NAME LIKE '%Compra%'
    OR TABLE_NAME LIKE '%Requisicion%'
    OR TABLE_NAME LIKE '%Inventario%'
    OR TABLE_NAME LIKE '%Sync%'
)
ORDER BY TABLE_NAME
""")

q("9) BUSCAR COLUMNAS CON FOLIOPEDIDO / PEDIDO / PRODUCTO EN TODA LA BD", """
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%Pedido%'
   OR COLUMN_NAME LIKE '%Folio%'
   OR COLUMN_NAME LIKE '%Producto%'
   OR COLUMN_NAME LIKE '%Cantidad%'
   OR COLUMN_NAME LIKE '%Precio%'
   OR COLUMN_NAME LIKE '%Costo%'
ORDER BY TABLE_NAME, ORDINAL_POSITION
""")

print("\n" + "="*100)
print("DICTAMEN")
print("="*100)
print("Si hay Compras_Sync_Log con errores o logs de encabezado solamente, corregir job de sync existente.")
print("Si existen tablas staging con detalle, poblar desde EDARSAHUB SQL.")
print("NO conectar a fuentes live ni desencriptar credenciales hasta agotar evidencia interna.")
print("Los 172 encabezados Total=0 sin detalle deben tratarse como sync incompleto, no como datos válidos.")

cn.close()
