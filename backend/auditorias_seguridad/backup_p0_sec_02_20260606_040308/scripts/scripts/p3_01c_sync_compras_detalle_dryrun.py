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

def conn_edarsa():
    return pymssql.connect(
        server=os.getenv("EDARSAHUB_SQL_HOST"),
        port=int(os.getenv("EDARSAHUB_SQL_PORT", "1433")),
        user=os.getenv("EDARSAHUB_SQL_USER"),
        password=os.getenv("EDARSAHUB_SQL_PASSWORD"),
        database=os.getenv("EDARSAHUB_SQL_DATABASE"),
        login_timeout=10,
        timeout=30
    )

cn = conn_edarsa()
cur = cn.cursor(as_dict=True)

print("P3-01C SYNC_COMPRAS_DETALLE DRY-RUN")
print("Fecha:", datetime.now())
print("Modo: DRY-RUN, NO INSERTA")
print()

print("=== 1) PEDIDOS SIN DETALLE ===")
cur.execute("""
SELECT TOP 50
    p.PedidoCompraID,
    p.FolioPedido,
    p.EmpresaID,
    p.SucursalID,
    p.ProveedorSugeridoID,
    p.FechaPedido,
    p.Total,
    p.MotivoCompra
FROM Compras_Pedidos p
WHERE NOT EXISTS (
    SELECT 1
    FROM Compras_PedidosDetalle d
    WHERE d.PedidoCompraID = p.PedidoCompraID
)
ORDER BY p.FechaPedido DESC
""")
pedidos = cur.fetchall()
print("Pedidos muestra sin detalle:", len(pedidos))
for p in pedidos[:10]:
    print(p)

print()
print("=== 2) COLUMNAS Compras_PedidosDetalle ===")
cur.execute("""
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME='Compras_PedidosDetalle'
ORDER BY ORDINAL_POSITION
""")
for r in cur.fetchall():
    print(r)

print()
print("=== 3) SERVIDORES FUENTE COMPRAS ===")
cur.execute("""
SELECT id, nombre, system_type, host, port, database_name, username, password_encrypted, EmpresaID
FROM Servidores_Conexiones
WHERE ISNULL(activo,1)=1
  AND tipo_conexion = 'DATA_SOURCE'
  AND (
        nombre LIKE '%130%'
     OR nombre LIKE '%CIENFUEGOS%'
     OR nombre LIKE '%ESTELAR%'
  )
ORDER BY nombre
""")
servers = cur.fetchall()

for s in servers:
    print({
        "id": s["id"],
        "nombre": s["nombre"],
        "system_type": s["system_type"],
        "database_name": s["database_name"],
        "EmpresaID": s["EmpresaID"],
        "password": "***encrypted***"
    })

print()
print("=== 4) DICTAMEN ===")
print("Este dry-run NO inserta.")
print("Las contraseñas están encriptadas en Servidores_Conexiones.")
print("Para sync real se requiere desencriptar usando core.security.crypto.")
print("Siguiente paso: P3-01D crear job que use decrypt + conexión fuente + INSERT idempotente.")

cn.close()
