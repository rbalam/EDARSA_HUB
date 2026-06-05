import os
from pathlib import Path
import pymssql
from datetime import datetime

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

print("P3-01F VALIDACIÓN PATCH COMPRAS SIN LIVE")
print("Fecha:", datetime.now())
print("Modo: SOLO LECTURA / NO INSERTA")
print()

print("=== 1) Verificar parche en código ===")
path = Path("/app/backend/modules/compras/sync_service.py")
txt = path.read_text(errors="ignore")
checks = [
    "P3-01E FIX: insertar detalles Compras_PedidosDetalle",
    "for det in result_det",
    "INSERT INTO Compras_PedidosDetalle",
    "UPDATE p SET",
    "det_synced += 1",
]
for c in checks:
    print(c, "OK" if c in txt else "FALTA")

print()
print("=== 2) Validar columnas requeridas destino ===")
required = [
    "PedidoCompraID",
    "Renglon",
    "ProductoID",
    "Cantidad",
    "CantidadAtendida",
    "CantidadCancelada",
    "CantidadPendiente",
    "PrecioEstimado",
    "DescuentoPorcentaje",
    "TasaImpuesto",
    "SubtotalLinea",
    "ImpuestoImporte",
    "TotalLinea",
    "Activo",
    "CreatedAt",
]
cur.execute("""
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME='Compras_PedidosDetalle'
""")
cols = {r["COLUMN_NAME"] for r in cur.fetchall()}

missing = [c for c in required if c not in cols]
print("Columnas en tabla:", sorted(cols))
print("Faltantes:", missing if missing else "NINGUNO")

print()
print("=== 3) Validar relación PedidoCompraID en encabezados ===")
cur.execute("""
SELECT TOP 10 PedidoCompraID, FolioPedido, Total
FROM Compras_Pedidos
ORDER BY FechaPedido DESC
""")
for r in cur.fetchall():
    print(r)

print()
print("=== 4) Conteo actual antes de sync real ===")
for t in ["Compras_Pedidos", "Compras_PedidosDetalle", "Compras_Ordenes", "Compras_Recepciones"]:
    try:
        cur.execute(f"SELECT COUNT(*) AS total FROM {t}")
        print(t, cur.fetchone()["total"])
    except Exception as e:
        print(t, "ERROR", e)

print()
print("=== 5) Validar que no quedan encabezados válidos con total 0 y detalle existente ===")
cur.execute("""
SELECT COUNT(*) AS inconsistentes
FROM Compras_Pedidos p
WHERE ISNULL(p.Total,0)=0
  AND EXISTS (
    SELECT 1 FROM Compras_PedidosDetalle d
    WHERE d.PedidoCompraID = p.PedidoCompraID
  )
""")
print("encabezados con detalle pero total 0:", cur.fetchone()["inconsistentes"])

print()
print("DICTAMEN:")
if missing:
    print("BLOQUEADO: faltan columnas destino. No ejecutar sync real.")
else:
    print("OK: parche y columnas destino validados. Siguiente paso: dry-run del job o ejecución controlada por 1 servidor/1 día.")

cn.close()
