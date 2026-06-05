import os
from pathlib import Path
import pymssql

ENV_PATH = Path("/app/backend/.env")

def load_env_file(path: Path):
    if not path.exists():
        return

    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value

load_env_file(ENV_PATH)

required = [
    "EDARSAHUB_SQL_HOST",
    "EDARSAHUB_SQL_PORT",
    "EDARSAHUB_SQL_DATABASE",
    "EDARSAHUB_SQL_USER",
    "EDARSAHUB_SQL_PASSWORD",
]

missing = [k for k in required if not os.getenv(k)]
if missing:
    raise SystemExit(f"Faltan variables: {missing}")

print("ENV OK:")
print({
    "host": os.getenv("EDARSAHUB_SQL_HOST"),
    "port": os.getenv("EDARSAHUB_SQL_PORT"),
    "database": os.getenv("EDARSAHUB_SQL_DATABASE"),
    "user": os.getenv("EDARSAHUB_SQL_USER"),
    "password": "***"
})

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

def try_query(title, sql):
    print(f"\n=== {title} ===")
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        print("registros:", len(rows))
        for r in rows[:50]:
            print(r)
    except Exception as e:
        print("ERROR:", str(e)[:300])

try_query("TABLAS UNIDAD / EMPRESA", """
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE '%Unidad%'
   OR TABLE_NAME LIKE '%Empresa%'
   OR TABLE_NAME LIKE '%Sucursal%'
ORDER BY TABLE_NAME
""")

try_query("COLUMNAS CANDIDATAS UNIDAD / SERVER", """
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%unidad%'
   OR COLUMN_NAME LIKE '%empresa%'
   OR COLUMN_NAME LIKE '%server%'
   OR COLUMN_NAME LIKE '%servidor%'
   OR COLUMN_NAME LIKE '%sucursal%'
ORDER BY TABLE_NAME, ORDINAL_POSITION
""")

# Consultas comunes tolerantes
for table in [
    "Unidades_Negocio",
    "Unidad_Negocio",
    "Empresa_Unidades",
    "Empresas",
    "Empresa_Catalogo",
    "Sucursales",
    "Servidores_Conexiones",
    "Usuario_Catalogo",
    "Usuario_Roles",
]:
    try_query(f"TOP 100 {table}", f"SELECT TOP 100 * FROM {table}")

try_query("BUSCAR 130 / MERIDA / MÉRIDA EN SERVIDORES_CONEXIONES", """
SELECT *
FROM Servidores_Conexiones
WHERE 
    CAST(Nombre AS NVARCHAR(MAX)) LIKE '%130%'
 OR CAST(Nombre AS NVARCHAR(MAX)) LIKE '%MERIDA%'
 OR CAST(Nombre AS NVARCHAR(MAX)) LIKE '%MÉRIDA%'
 OR CAST(CodigoUnidad AS NVARCHAR(MAX)) LIKE '%130%'
 OR CAST(ServerID AS NVARCHAR(MAX)) LIKE '%130%'
""")

try_query("RESUMEN SERVIDORES_CONEXIONES", """
SELECT 
    TipoConexion,
    COUNT(*) AS total
FROM Servidores_Conexiones
GROUP BY TipoConexion
ORDER BY total DESC
""")

cn.close()
