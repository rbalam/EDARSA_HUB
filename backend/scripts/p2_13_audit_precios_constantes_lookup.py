import os
from pathlib import Path
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

print("=== SERVIDORES_CONEXIONES 130 / MERIDA ===")
cur.execute("""
SELECT id, nombre, system_type, tipo_conexion, EmpresaID
FROM Servidores_Conexiones
WHERE nombre LIKE '%130%'
   OR nombre LIKE '%MERIDA%'
   OR nombre LIKE '%MÉRIDA%'
ORDER BY nombre
""")
for r in cur.fetchall():
    print(r)

print("\n=== UNIDADES_NEGOCIO 130 / MERIDA ===")
cur.execute("""
SELECT id, codigo, nombre, server_id, system_type
FROM Unidades_Negocio
WHERE codigo LIKE '%130%'
   OR nombre LIKE '%130%'
   OR nombre LIKE '%MERIDA%'
   OR nombre LIKE '%MÉRIDA%'
ORDER BY nombre
""")
for r in cur.fetchall():
    print(r)

print("\n=== PRECIOS HISTÓRICOS POR SERVER 130 ===")
cur.execute("""
SELECT ServerID, COUNT(*) total
FROM Sync_Precios_Historicos
WHERE ServerID LIKE '%130%'
   OR ServerID IN (
        SELECT CAST(server_id AS NVARCHAR(100))
        FROM Unidades_Negocio
        WHERE codigo LIKE '%130%' OR nombre LIKE '%130%' OR nombre LIKE '%MERIDA%' OR nombre LIKE '%MÉRIDA%'
   )
GROUP BY ServerID
ORDER BY total DESC
""")
for r in cur.fetchall():
    print(r)

cn.close()
