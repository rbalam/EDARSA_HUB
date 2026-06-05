"""
Guardrail P1: Validar que KPIs usen unidad_negocio_pk real
"""
import os
import sys
import pymssql

host = os.getenv('EDARSAHUB_SQL_HOST')
port = int(os.getenv('EDARSAHUB_SQL_PORT', '1433'))
database = os.getenv('EDARSAHUB_SQL_DATABASE')
user = os.getenv('EDARSAHUB_SQL_USER')
password = os.getenv('EDARSAHUB_SQL_PASSWORD')

conn = pymssql.connect(server=host, port=port, user=user, password=password, database=database)
cur = conn.cursor()

errors = []

for table in ["Comercial_KPIs_Diarios_v2", "Comercial_KPIs_Mensuales_v2"]:
    # Verificar columna existe
    cur.execute("""
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME=%s AND COLUMN_NAME='unidad_negocio_pk' AND DATA_TYPE='uniqueidentifier'
    """, (table,))
    if cur.fetchone()[0] == 0:
        errors.append(f"{table} no tiene unidad_negocio_pk UNIQUEIDENTIFIER")
        continue

    # Verificar nulls
    cur.execute(f"SELECT COUNT(*) FROM dbo.{table} WHERE unidad_negocio_pk IS NULL")
    nulls = cur.fetchone()[0]
    if nulls:
        errors.append(f"{table} tiene {nulls} registros sin unidad_negocio_pk")

    # Verificar huérfanos
    cur.execute(f"""
    SELECT COUNT(*)
    FROM dbo.{table} k
    LEFT JOIN dbo.Unidades_Negocio u ON u.id = k.unidad_negocio_pk
    WHERE k.unidad_negocio_pk IS NOT NULL AND u.id IS NULL
    """)
    orphans = cur.fetchone()[0]
    if orphans:
        errors.append(f"{table} tiene {orphans} huérfanos contra Unidades_Negocio.id")

conn.close()

if errors:
    print("FAIL - KPIs no normalizados:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("OK - KPIs normalizados por unidad_negocio_pk real")
sys.exit(0)
