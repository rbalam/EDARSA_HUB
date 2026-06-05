"""
Auditoría KPIs Junio 2026
=========================
Verifica completitud, duplicados y consistencia de datos.
"""
import os
from dotenv import load_dotenv
load_dotenv()

# Usar pymssql que ya está configurado en el proyecto
import pymssql

SERVER = os.getenv("EDARSAHUB_SQL_HOST")
DATABASE = os.getenv("EDARSAHUB_SQL_DATABASE")
USER = os.getenv("EDARSAHUB_SQL_USER")
PASSWORD = os.getenv("EDARSAHUB_SQL_PASSWORD")
PORT = int(os.getenv("EDARSAHUB_SQL_PORT", "1433"))

if not all([SERVER, DATABASE, USER, PASSWORD]):
    raise SystemExit("Faltan variables EDARSAHUB_SQL_HOST, EDARSAHUB_SQL_DATABASE, EDARSAHUB_SQL_USER, EDARSAHUB_SQL_PASSWORD")

conn = pymssql.connect(
    server=SERVER,
    port=PORT,
    database=DATABASE,
    user=USER,
    password=PASSWORD,
    as_dict=True
)

cur = conn.cursor()

print("\n" + "="*80)
print("AUDITORIA KPIS JUNIO 2026 - EDARSA HUB")
print("="*80)

# ============================================================================
# 1. RESUMEN 01-05 JUNIO POR UNIDAD
# ============================================================================
print("\n--- 1. RESUMEN 01-05 JUNIO ---\n")

cur.execute("""
SELECT
    unidad_negocio_nombre AS UnidadNegocio,
    MIN(fecha_operacion) AS PrimeraFecha,
    MAX(fecha_operacion) AS UltimaFecha,
    COUNT(*) AS Dias,
    SUM(ISNULL(ventas_total,0)) AS VentaNeta,
    SUM(ISNULL(tickets_total,0)) AS Cheques,
    SUM(ISNULL(pax_total,0)) AS PAX
FROM Comercial_KPIs_Diarios_v2
WHERE fecha_operacion >= '2026-06-01'
  AND fecha_operacion < '2026-06-06'
GROUP BY unidad_negocio_nombre
ORDER BY unidad_negocio_nombre;
""")

rows = cur.fetchall()
print(f"{'Unidad':<20} | {'Primera':<12} | {'Última':<12} | {'Días':>4} | {'VentaNeta':>14} | {'Cheques':>7} | {'PAX':>5}")
print("-"*90)
total_venta = 0
total_cheques = 0
total_pax = 0
for r in rows:
    venta = r['VentaNeta'] or 0
    cheques = r['Cheques'] or 0
    pax = r['PAX'] or 0
    total_venta += venta
    total_cheques += cheques
    total_pax += pax
    print(f"{r['UnidadNegocio'][:20]:<20} | {str(r['PrimeraFecha']):<12} | {str(r['UltimaFecha']):<12} | {r['Dias']:>4} | ${venta:>13,.2f} | {cheques:>7} | {pax:>5}")
print("-"*90)
print(f"{'TOTAL':<20} | {'':<12} | {'':<12} | {'':<4} | ${total_venta:>13,.2f} | {total_cheques:>7} | {total_pax:>5}")

# ============================================================================
# 2. FECHAS FALTANTES 01-05 JUNIO
# ============================================================================
print("\n--- 2. FECHAS FALTANTES 01-05 JUNIO ---\n")

cur.execute("""
WITH unidades AS (
    SELECT DISTINCT unidad_negocio_nombre
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_nombre IN ('130° MERIDA','130° QUERETARO','CIENFUEGOS','LA ESTELAR','ORIGEN')
),
fechas AS (
    SELECT CAST('2026-06-01' AS date) fecha
    UNION ALL SELECT CAST('2026-06-02' AS date)
    UNION ALL SELECT CAST('2026-06-03' AS date)
    UNION ALL SELECT CAST('2026-06-04' AS date)
    UNION ALL SELECT CAST('2026-06-05' AS date)
),
base AS (
    SELECT
        u.unidad_negocio_nombre,
        f.fecha
    FROM unidades u
    CROSS JOIN fechas f
)
SELECT
    b.unidad_negocio_nombre AS Unidad,
    b.fecha AS Fecha,
    CASE WHEN k.fecha_operacion IS NULL THEN 'FALTA' ELSE 'OK' END AS Estado,
    ISNULL(k.ventas_total,0) AS VentaNeta,
    ISNULL(k.tickets_total,0) AS Cheques,
    ISNULL(k.pax_total,0) AS PAX
FROM base b
LEFT JOIN Comercial_KPIs_Diarios_v2 k
    ON k.unidad_negocio_nombre = b.unidad_negocio_nombre
   AND k.fecha_operacion = b.fecha
ORDER BY b.unidad_negocio_nombre, b.fecha;
""")

rows = cur.fetchall()
print(f"{'Unidad':<20} | {'Fecha':<12} | {'Estado':<6} | {'VentaNeta':>12} | {'Cheques':>7} | {'PAX':>5}")
print("-"*75)
faltantes = 0
for r in rows:
    estado = r['Estado']
    if estado == 'FALTA':
        faltantes += 1
        marca = "⚠️"
    else:
        marca = "✅"
    venta = r['VentaNeta'] or 0
    print(f"{r['Unidad'][:20]:<20} | {str(r['Fecha']):<12} | {marca} {estado:<4} | ${venta:>11,.2f} | {r['Cheques'] or 0:>7} | {r['PAX'] or 0:>5}")

if faltantes > 0:
    print(f"\n⚠️  ALERTA: {faltantes} fecha(s) faltante(s)")
else:
    print("\n✅ Todas las fechas tienen datos")

# ============================================================================
# 3. DUPLICADOS POR UNIDAD / FECHA
# ============================================================================
print("\n--- 3. DUPLICADOS POR UNIDAD / FECHA ---\n")

cur.execute("""
SELECT
    unidad_negocio_nombre AS Unidad,
    fecha_operacion AS Fecha,
    COUNT(*) AS Registros,
    SUM(ISNULL(ventas_total,0)) AS VentaNeta
FROM Comercial_KPIs_Diarios_v2
WHERE fecha_operacion >= '2026-06-01'
  AND fecha_operacion < '2026-06-06'
GROUP BY unidad_negocio_nombre, fecha_operacion
HAVING COUNT(*) > 1
ORDER BY unidad_negocio_nombre, fecha_operacion;
""")

dups = cur.fetchall()
if not dups:
    print("✅ Sin duplicados en Comercial_KPIs_Diarios_v2 para 01-05 junio.")
else:
    print(f"⚠️  DUPLICADOS ENCONTRADOS:")
    for r in dups:
        print(f"   {r['Unidad']} | {r['Fecha']} | {r['Registros']} registros | ${r['VentaNeta']:,.2f}")

# ============================================================================
# 4. COMPARATIVO DIARIO VS MENSUAL
# ============================================================================
print("\n--- 4. COMPARATIVO DIARIO VS MENSUAL (Junio 2026) ---\n")

cur.execute("""
SELECT
    d.unidad_negocio_nombre AS Unidad,
    SUM(ISNULL(d.ventas_total,0)) AS VentaDiaria_01_05,
    MAX(m.ventas_total) AS VentaMensualTabla,
    SUM(ISNULL(d.tickets_total,0)) AS ChequesDiario,
    MAX(m.tickets_total) AS ChequesMensualTabla,
    SUM(ISNULL(d.pax_total,0)) AS PaxDiario,
    MAX(m.pax_total) AS PaxMensualTabla
FROM Comercial_KPIs_Diarios_v2 d
LEFT JOIN Comercial_KPIs_Mensuales_v2 m
    ON m.unidad_negocio_nombre = d.unidad_negocio_nombre
   AND m.anio = 2026
   AND m.mes = 6
WHERE d.fecha_operacion >= '2026-06-01'
  AND d.fecha_operacion < '2026-06-06'
GROUP BY d.unidad_negocio_nombre
ORDER BY d.unidad_negocio_nombre;
""")

rows = cur.fetchall()
print(f"{'Unidad':<18} | {'Venta Diaria':>14} | {'Venta Mensual':>14} | {'Chq Diario':>10} | {'Chq Mensual':>11}")
print("-"*80)
for r in rows:
    vd = r['VentaDiaria_01_05'] or 0
    vm = r['VentaMensualTabla'] or 0
    cd = r['ChequesDiario'] or 0
    cm = r['ChequesMensualTabla'] or 0
    diff = "⚠️" if vm > 0 and abs(vd - vm) > 1000 else "  "
    print(f"{r['Unidad'][:18]:<18} | ${vd:>13,.2f} | ${vm:>13,.2f} {diff}| {cd:>10} | {cm if cm else 'N/A':>11}")

print("\nNOTA: La tabla mensual se consolida al cierre del mes.")
print("      Si VentaMensual = 0, significa que aún no se ha consolidado.")

conn.close()

print("\n" + "="*80)
print("FIN AUDITORIA")
print("="*80 + "\n")
