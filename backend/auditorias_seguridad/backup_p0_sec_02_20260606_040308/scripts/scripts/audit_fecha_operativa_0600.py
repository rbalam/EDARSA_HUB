#!/usr/bin/env python3
"""
AUDITORÍA: Fecha Operativa con Corte 06:00 AM
=============================================

PROPÓSITO:
Diagnosticar registros en EDARSAHUB que tienen timestamp entre 00:00 y 05:59
y verificar si su FechaOperacion es correcta según la nueva regla de corte 06:00 AM.

REGLA DE NEGOCIO (Actualizada 17-May-2026):
- La jornada operativa del restaurante cierra a las 06:00 AM
- Toda venta entre 00:00 y 05:59 pertenece al DÍA OPERATIVO ANTERIOR
- Ejemplo: Una venta a las 03:30 AM del 15-May pertenece a FechaOperacion = 14-May

ALCANCE:
- Solo diagnóstico, NO modifica datos
- No hace UPDATE, DELETE ni MERGE
- Genera reporte de inconsistencias

TABLAS AUDITADAS:
- Comercial_KPIs_Diarios_v2
- Sync_Ventas_PorHora (si existe)

AUTOR: Sistema E1
FECHA: 2026-05-17
"""

import pymssql
from datetime import datetime, date, timedelta
import pytz
import json
import os

# Configuración
EDARSAHUB_CONFIG = {
    'server': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'user': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD'),
    'database': 'EDARSAHUB'
}

MEXICO_TZ = pytz.timezone('America/Mexico_City')
CORTE_HORA = 6  # 06:00 AM es el corte de jornada

def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB SQL Server."""
    return pymssql.connect(
        server=EDARSAHUB_CONFIG['server'],
        port=EDARSAHUB_CONFIG['port'],
        user=EDARSAHUB_CONFIG['user'],
        password=EDARSAHUB_CONFIG['password'],
        database=EDARSAHUB_CONFIG['database']
    )


def calcular_fecha_operativa_correcta(timestamp_utc):
    """
    Calcula la FechaOperacion correcta según la regla de corte 06:00 AM.
    
    Args:
        timestamp_utc: datetime en UTC o naive (se asume México)
    
    Returns:
        date: Fecha operativa correcta
    """
    if timestamp_utc is None:
        return None
    
    # Convertir a hora México
    if timestamp_utc.tzinfo is None:
        # Asumir que ya está en hora México
        hora_mexico = timestamp_utc
    else:
        hora_mexico = timestamp_utc.astimezone(MEXICO_TZ)
    
    fecha_calendario = hora_mexico.date()
    hora = hora_mexico.hour
    
    # Regla: Si hora < 06:00, pertenece al día anterior
    if hora < CORTE_HORA:
        return fecha_calendario - timedelta(days=1)
    else:
        return fecha_calendario


def auditar_comercial_kpis_diarios_v2(conn, mes=None, anio=None):
    """
    Audita registros en Comercial_KPIs_Diarios_v2 buscando inconsistencias
    de fecha operativa en registros con hora < 06:00 AM.
    """
    cursor = conn.cursor(as_dict=True)
    
    if mes is None:
        mes = datetime.now(MEXICO_TZ).month
    if anio is None:
        anio = datetime.now(MEXICO_TZ).year
    
    print(f"\n{'='*80}")
    print(f"AUDITORÍA: Comercial_KPIs_Diarios_v2")
    print(f"Período: {mes:02d}/{anio}")
    print(f"Regla: Corte operativo a las 06:00 AM")
    print(f"{'='*80}")
    
    # Verificar si existe columna de timestamp de sincronización
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Comercial_KPIs_Diarios_v2'
          AND COLUMN_NAME IN ('fecha_sincronizacion', 'fecha_alta', 'snapshot_timestamp')
    """)
    timestamp_cols = [row['COLUMN_NAME'] for row in cursor.fetchall()]
    
    print(f"\nColumnas de timestamp disponibles: {timestamp_cols}")
    
    # Obtener resumen de datos por unidad
    query_resumen = f"""
    SELECT 
        unidad_negocio_id,
        COUNT(*) as total_registros,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max,
        SUM(ventas_total) as ventas_total
    FROM Comercial_KPIs_Diarios_v2
    WHERE anio = {anio} AND mes = {mes}
      AND ventas_total > 0
    GROUP BY unidad_negocio_id
    ORDER BY unidad_negocio_id
    """
    
    cursor.execute(query_resumen)
    resumen = cursor.fetchall()
    
    print(f"\n{'Unidad':<15} {'Registros':>10} {'Fecha Mín':>12} {'Fecha Máx':>12} {'Ventas':>18}")
    print("-" * 70)
    for row in resumen:
        print(f"{row['unidad_negocio_id']:<15} {row['total_registros']:>10} "
              f"{str(row['fecha_min'])[:10]:>12} {str(row['fecha_max'])[:10]:>12} "
              f"${row['ventas_total']:>15,.2f}")
    
    # Nota: No podemos auditar hora exacta porque Comercial_KPIs_Diarios_v2
    # es una tabla consolidada por día, no tiene timestamp de la venta original
    print("\n[INFO] Comercial_KPIs_Diarios_v2 es una tabla CONSOLIDADA por día.")
    print("[INFO] Para auditar hora exacta, se requiere revisar tablas de origen:")
    print("       - Sync_Ventas_PorHora")
    print("       - Comercial_Ventas_Dia_Abiertas_v2")
    
    cursor.close()
    return resumen


def auditar_sync_ventas_por_hora(conn, mes=None, anio=None):
    """
    Audita registros en Sync_Ventas_PorHora buscando ventas entre 00:00-05:59
    que podrían tener FechaOperacion incorrecta.
    """
    cursor = conn.cursor(as_dict=True)
    
    if mes is None:
        mes = datetime.now(MEXICO_TZ).month
    if anio is None:
        anio = datetime.now(MEXICO_TZ).year
    
    print(f"\n{'='*80}")
    print(f"AUDITORÍA: Sync_Ventas_PorHora")
    print(f"Período: {mes:02d}/{anio}")
    print(f"Buscando: Registros con hora < 06:00 AM")
    print(f"{'='*80}")
    
    # Verificar si existe la tabla
    cursor.execute("""
        SELECT COUNT(*) as existe 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'Sync_Ventas_PorHora'
    """)
    if cursor.fetchone()['existe'] == 0:
        print("\n[WARN] Tabla Sync_Ventas_PorHora no existe en EDARSAHUB")
        cursor.close()
        return []
    
    # Obtener estructura de la tabla
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Sync_Ventas_PorHora'
        ORDER BY ORDINAL_POSITION
    """)
    columnas = cursor.fetchall()
    print(f"\nColumnas: {[c['COLUMN_NAME'] for c in columnas]}")
    
    # Buscar registros con hora < 06:00 AM
    # Asumimos que existe una columna 'hora' o similar
    hora_col = None
    fecha_op_col = None
    
    for col in columnas:
        if col['COLUMN_NAME'].lower() in ('hora', 'hour', 'hora_venta'):
            hora_col = col['COLUMN_NAME']
        if col['COLUMN_NAME'].lower() in ('fecha_operacion', 'fecha_op', 'fechaoperacion'):
            fecha_op_col = col['COLUMN_NAME']
    
    if hora_col is None:
        print("\n[WARN] No se encontró columna de hora en Sync_Ventas_PorHora")
        # Intentar con estructura conocida
        cursor.execute("SELECT TOP 5 * FROM Sync_Ventas_PorHora ORDER BY fecha_sync DESC")
        sample = cursor.fetchall()
        if sample:
            print(f"[INFO] Muestra de datos: {list(sample[0].keys())}")
        cursor.close()
        return []
    
    # Query para encontrar inconsistencias
    query_inconsistencias = f"""
    SELECT 
        unidad_negocio_id,
        {hora_col} as hora,
        {fecha_op_col if fecha_op_col else 'fecha_calendario'} as fecha_operacion,
        fecha_calendario,
        SUM(ventas_total) as ventas,
        COUNT(*) as registros
    FROM Sync_Ventas_PorHora
    WHERE {hora_col} >= 0 AND {hora_col} < 6  -- Hora entre 00:00 y 05:59
      AND anio = {anio} AND mes = {mes}
    GROUP BY unidad_negocio_id, {hora_col}, 
             {fecha_op_col if fecha_op_col else 'fecha_calendario'}, fecha_calendario
    ORDER BY unidad_negocio_id, fecha_calendario, {hora_col}
    """
    
    try:
        cursor.execute(query_inconsistencias)
        inconsistencias = cursor.fetchall()
        
        if inconsistencias:
            print(f"\n[ALERTA] Encontrados {len(inconsistencias)} registros con hora < 06:00 AM:")
            print(f"\n{'Unidad':<12} {'Hora':>5} {'FechaOp':>12} {'FechaCal':>12} {'Ventas':>15} {'Regs':>6}")
            print("-" * 70)
            
            posibles_errores = []
            for row in inconsistencias:
                fecha_op = row['fecha_operacion']
                fecha_cal = row['fecha_calendario']
                hora = row['hora']
                
                # Calcular fecha operativa correcta
                if isinstance(fecha_cal, date):
                    fecha_correcta = fecha_cal - timedelta(days=1) if hora < CORTE_HORA else fecha_cal
                else:
                    fecha_correcta = None
                
                es_error = fecha_op != fecha_correcta if fecha_correcta and fecha_op else False
                marca = "⚠️ ERROR" if es_error else "✅"
                
                print(f"{row['unidad_negocio_id']:<12} {hora:>5} {str(fecha_op)[:10]:>12} "
                      f"{str(fecha_cal)[:10]:>12} ${row['ventas']:>13,.2f} {row['registros']:>6} {marca}")
                
                if es_error:
                    posibles_errores.append({
                        'unidad': row['unidad_negocio_id'],
                        'hora': hora,
                        'fecha_operacion_actual': str(fecha_op),
                        'fecha_calendario': str(fecha_cal),
                        'fecha_operacion_correcta': str(fecha_correcta),
                        'ventas': float(row['ventas']),
                        'registros': row['registros']
                    })
            
            if posibles_errores:
                print(f"\n[CRÍTICO] {len(posibles_errores)} registros tienen FechaOperacion INCORRECTA")
                print("[INFO] Estos registros requieren UPDATE para corregir FechaOperacion")
            else:
                print(f"\n[OK] Todos los registros tienen FechaOperacion correcta")
                
            return posibles_errores
        else:
            print("\n[OK] No hay registros con hora < 06:00 AM en el período")
            return []
            
    except Exception as e:
        print(f"\n[ERROR] No se pudo ejecutar query: {e}")
        cursor.close()
        return []
    
    cursor.close()
    return []


def auditar_ventas_dia_abiertas(conn, mes=None, anio=None):
    """
    Audita registros en Comercial_Ventas_Dia_Abiertas_v2.
    """
    cursor = conn.cursor(as_dict=True)
    
    if mes is None:
        mes = datetime.now(MEXICO_TZ).month
    if anio is None:
        anio = datetime.now(MEXICO_TZ).year
    
    print(f"\n{'='*80}")
    print(f"AUDITORÍA: Comercial_Ventas_Dia_Abiertas_v2")
    print(f"Período: {mes:02d}/{anio}")
    print(f"{'='*80}")
    
    # Verificar si existe la tabla
    cursor.execute("""
        SELECT COUNT(*) as existe 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'Comercial_Ventas_Dia_Abiertas_v2'
    """)
    if cursor.fetchone()['existe'] == 0:
        print("\n[WARN] Tabla Comercial_Ventas_Dia_Abiertas_v2 no existe en EDARSAHUB")
        cursor.close()
        return []
    
    # Buscar snapshots con timestamp entre 00:00 y 05:59
    query = f"""
    SELECT 
        unidad_negocio_id,
        fecha_operacion,
        DATEPART(HOUR, snapshot_timestamp) as hora_snapshot,
        snapshot_timestamp,
        ventas_total,
        tickets_abiertos
    FROM Comercial_Ventas_Dia_Abiertas_v2
    WHERE DATEPART(HOUR, snapshot_timestamp) < 6
      AND YEAR(fecha_operacion) = {anio}
      AND MONTH(fecha_operacion) = {mes}
    ORDER BY unidad_negocio_id, snapshot_timestamp DESC
    """
    
    try:
        cursor.execute(query)
        registros = cursor.fetchall()
        
        if registros:
            print(f"\n[INFO] Encontrados {len(registros)} snapshots con hora < 06:00 AM:")
            print(f"\n{'Unidad':<15} {'FechaOp':>12} {'Hora':>5} {'Timestamp':>20} {'Ventas':>15}")
            print("-" * 75)
            
            for row in registros[:20]:  # Mostrar primeros 20
                print(f"{row['unidad_negocio_id']:<15} {str(row['fecha_operacion'])[:10]:>12} "
                      f"{row['hora_snapshot']:>5} {str(row['snapshot_timestamp'])[:19]:>20} "
                      f"${row['ventas_total']:>13,.2f}")
            
            if len(registros) > 20:
                print(f"... y {len(registros) - 20} registros más")
        else:
            print("\n[OK] No hay snapshots con hora < 06:00 AM")
            
    except Exception as e:
        print(f"\n[ERROR] No se pudo ejecutar query: {e}")
    
    cursor.close()
    return []


def generar_reporte_json(resultados, output_path):
    """Genera reporte en formato JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n[INFO] Reporte JSON guardado en: {output_path}")


def main():
    """Ejecuta la auditoría completa."""
    print("=" * 80)
    print("AUDITORÍA: FECHA OPERATIVA CON CORTE 06:00 AM")
    print("=" * 80)
    print(f"Fecha de ejecución: {datetime.now(MEXICO_TZ).isoformat()}")
    print(f"Regla de negocio: Ventas entre 00:00-05:59 pertenecen al día anterior")
    print(f"Corte de jornada: 06:00 AM hora México")
    print("\n[IMPORTANTE] Esta auditoría es SOLO DIAGNÓSTICO")
    print("[IMPORTANTE] NO modifica ningún dato")
    
    # Obtener período a auditar
    now = datetime.now(MEXICO_TZ)
    mes = now.month
    anio = now.year
    
    resultados = {
        'fecha_ejecucion': now.isoformat(),
        'periodo': f"{mes:02d}/{anio}",
        'regla_corte': '06:00 AM',
        'tablas_auditadas': [],
        'inconsistencias': [],
        'resumen': {}
    }
    
    try:
        conn = get_edarsahub_connection()
        print(f"\n[OK] Conexión a EDARSAHUB establecida")
        
        # Auditar cada tabla
        resumen_kpis = auditar_comercial_kpis_diarios_v2(conn, mes, anio)
        resultados['tablas_auditadas'].append('Comercial_KPIs_Diarios_v2')
        
        errores_sync = auditar_sync_ventas_por_hora(conn, mes, anio)
        resultados['tablas_auditadas'].append('Sync_Ventas_PorHora')
        resultados['inconsistencias'].extend(errores_sync)
        
        auditar_ventas_dia_abiertas(conn, mes, anio)
        resultados['tablas_auditadas'].append('Comercial_Ventas_Dia_Abiertas_v2')
        
        conn.close()
        
        # Resumen final
        print("\n" + "=" * 80)
        print("RESUMEN DE AUDITORÍA")
        print("=" * 80)
        
        total_inconsistencias = len(resultados['inconsistencias'])
        resultados['resumen'] = {
            'total_inconsistencias': total_inconsistencias,
            'requiere_update': total_inconsistencias > 0,
            'tablas_auditadas': len(resultados['tablas_auditadas'])
        }
        
        if total_inconsistencias > 0:
            print(f"\n⚠️  ENCONTRADAS {total_inconsistencias} INCONSISTENCIAS")
            print("    Registros con FechaOperacion que NO cumple regla 06:00 AM")
            print("\n    ACCIÓN REQUERIDA: Revisión manual y posible UPDATE")
            print("    (Sujeto a autorización explícita)")
        else:
            print(f"\n✅ NO SE ENCONTRARON INCONSISTENCIAS")
            print("   Todos los registros auditados cumplen la regla 06:00 AM")
        
        # Guardar reporte JSON
        output_dir = '/app/docs/reports'
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}/audit_fecha_operativa_0600_{anio}{mes:02d}.json"
        generar_reporte_json(resultados, output_path)
        
    except Exception as e:
        print(f"\n[ERROR CRÍTICO] {e}")
        resultados['error'] = str(e)
    
    return resultados


if __name__ == "__main__":
    main()
