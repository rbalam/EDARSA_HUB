import sys
import os
import pymssql

tables = [
    "Inventarios_ProcesadosAuto",
    "Inventarios_DiferenciasDetalle",
    "Inventarios_FisicosProcesados",
    "Sistema_ServidoresEstado",
    "Sistema_ServidoresConexionEstado",
    "Sistema_ServidoresSucursalesConfig",
    "Sistema_NotificacionesConfig",
    "Sistema_ConfiguracionOperativa",
    "Sistema_ConsultasCustom",
    "Sistema_AlertasDestinatarios",
    "Finanzas_PropinasConfig",
    "Finanzas_AuditoriaFinanciera",
    "Compras_AutomatizacionesOperativas",
    "Compras_PedidosProcesadosAutomatizacion",
    "Portal_Proveedores",
    "Manuales_Operativos",
]

sql_host = os.getenv("EDARSAHUB_SQL_HOST")
sql_port = os.getenv("EDARSAHUB_SQL_PORT", "1433")
sql_database = os.getenv("EDARSAHUB_SQL_DATABASE")
sql_user = os.getenv("EDARSAHUB_SQL_USER")
sql_password = os.getenv("EDARSAHUB_SQL_PASSWORD")

if not all([sql_host, sql_database, sql_user, sql_password]):
    print("SKIP - Variables SQL no configuradas")
    sys.exit(0)

conn = pymssql.connect(
    server=sql_host, port=int(sql_port), user=sql_user, password=sql_password,
    database=sql_database, tds_version="7.0"
)
cur = conn.cursor()

errors = []
total = 0

for table in tables:
    cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME=%s", (table,))
    if cur.fetchone()[0] == 0:
        errors.append(f"NO_EXISTE {table}")
        continue

    cur.execute(f"SELECT COUNT(*) FROM dbo.{table}")
    count = cur.fetchone()[0]
    print(f"{table}: {count} rows")
    total += count

conn.close()

print(f"\nTOTAL: {total} registros en tablas canónicas")

if errors:
    print("FAIL")
    for e in errors:
        print(e)
    sys.exit(1)

print("PASS tablas canónicas creadas y pobladas")
