"""Guardrail: Verificar que KPIs tienen unidad_negocio_pk poblado"""
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
for table in ["Comercial_KPIs_Diarios_v2", "Comercial_KPIs_Mensuales_v2"]:
    cur.execute(f"SELECT COUNT(*) FROM dbo.{table} WHERE unidad_negocio_pk IS NULL")
    nulls = cur.fetchone()[0]
    if nulls > 0:
        errors.append(f"{table}: {nulls} registros sin unidad_negocio_pk")

conn.close()

if errors:
    print("FAIL - KPIs sin PK:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("OK - Todos los KPIs tienen unidad_negocio_pk")
