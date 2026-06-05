"""Guardrail: Verificar que las vistas Runtime existen en SQL"""
import pymssql
import os
import sys

host = os.getenv('EDARSAHUB_SQL_HOST')
port = int(os.getenv('EDARSAHUB_SQL_PORT', '1433'))
database = os.getenv('EDARSAHUB_SQL_DATABASE')
user = os.getenv('EDARSAHUB_SQL_USER')
password = os.getenv('EDARSAHUB_SQL_PASSWORD')

conn = pymssql.connect(server=host, port=port, user=user, password=password, database=database)
cur = conn.cursor()

errors = []
for v in ["vw_Comercial_KPIs_Diarios_v2_Runtime", "vw_Comercial_KPIs_Mensuales_v2_Runtime", 
          "vw_Comercial_KPIs_Diarios_v2_Canonica", "vw_Comercial_KPIs_Mensuales_v2_Canonica"]:
    cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME=%s", (v,))
    if cur.fetchone()[0] == 0:
        errors.append(f"Vista {v} no existe")

conn.close()

if errors:
    print("FAIL - Vistas faltantes:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("OK - Todas las vistas Runtime y Canónicas existen")
