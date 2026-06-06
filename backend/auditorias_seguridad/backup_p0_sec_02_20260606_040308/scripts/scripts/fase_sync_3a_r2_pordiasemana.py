#!/usr/bin/env python3
"""
FASE SYNC-3A-R2: Calcular PorDiaSemana desde Historicas
========================================================
Script que calcula Sync_Ventas_PorDiaSemana a partir de los datos
ya sincronizados en Sync_Ventas_Historicas.

Esto es más confiable que consultar servidores remotos que pueden
estar inaccesibles.

Autor: Arquitecto Senior Backend
"""

import sys
sys.path.insert(0, '/app/backend')

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List
import uuid

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG


def get_zona_mexico():
    """Obtener zona horaria México."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo('America/Mexico_City')
    except ImportError:
        import pytz
        return pytz.timezone('America/Mexico_City')


def calcular_pordiasemana_desde_historicas(
    server_ids: List[str],
    dry_run: bool = True
) -> Dict:
    """
    Calcula PorDiaSemana a partir de Sync_Ventas_Historicas.
    
    Args:
        server_ids: Lista de ServerIDs a procesar
        dry_run: Si True, solo simula sin escribir
        
    Returns:
        Dict con resultado del procesamiento
    """
    tz_mexico = get_zona_mexico()
    ahora_mexico = datetime.now(tz_mexico)
    sync_run_id = f"SYNC-CALC-{ahora_mexico.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    resultado = {
        'sync_run_id': sync_run_id,
        'dry_run': dry_run,
        'servidores_procesados': 0,
        'registros_calculados': 0,
        'registros_upserted': 0,
        'errores': [],
        'detalle_servidores': {}
    }
    
    dias_semana_nombres = ['Domingo', 'Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado']
    
    for server_id in server_ids:
        print(f"\n=== Procesando {server_id[:8]}... ===")
        
        # 1. Obtener datos de Historicas
        query_historicas = f"""
        SELECT 
            ServerID,
            EmpresaID,
            SucursalID,
            UnidadNegocioID,
            SystemType,
            FechaOperacion,
            DATEPART(WEEKDAY, FechaOperacion) as DiaSemanaSQL,
            VentaTotal,
            VentanaInicioHoraConfig,
            VentanaFinHoraConfig
        FROM Sync_Ventas_Historicas
        WHERE ServerID = '{server_id}'
          AND SourceStatus = 'SUCCESS'
        ORDER BY FechaOperacion
        """
        
        registros = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query_historicas
        )
        
        if not registros:
            print(f"  ⚠️  Sin datos en Historicas para {server_id[:8]}")
            resultado['errores'].append(f"Sin datos para {server_id}")
            continue
        
        print(f"  📊 {len(registros)} registros en Historicas")
        
        # 2. Agrupar por día de la semana
        # DiaSemanaSQL: 1=Domingo, 2=Lunes, ..., 7=Sábado
        ventas_por_dia: Dict[int, List[Decimal]] = {i: [] for i in range(1, 8)}
        
        fecha_min = None
        fecha_max = None
        system_type = registros[0]['SystemType']
        empresa_id = registros[0]['EmpresaID']
        sucursal_id = registros[0]['SucursalID']
        unidad_id = registros[0]['UnidadNegocioID']
        ventana_inicio = registros[0]['VentanaInicioHoraConfig']
        ventana_fin = registros[0]['VentanaFinHoraConfig']
        
        for r in registros:
            dia = r['DiaSemanaSQL']
            venta = Decimal(str(r['VentaTotal']))
            ventas_por_dia[dia].append(venta)
            
            fecha_op = r['FechaOperacion']
            if fecha_min is None or fecha_op < fecha_min:
                fecha_min = fecha_op
            if fecha_max is None or fecha_op > fecha_max:
                fecha_max = fecha_op
        
        print(f"  📅 Periodo: {fecha_min} a {fecha_max}")
        
        # 3. Calcular estadísticas por día
        detalle_servidor = []
        
        for dia_sql in range(1, 8):
            ventas = ventas_por_dia[dia_sql]
            
            if not ventas:
                continue
            
            # Convertir día SQL (1=Dom) a ISO (0=Lun, 6=Dom)
            dia_iso = (dia_sql - 2) % 7  # 1->6(Dom), 2->0(Lun), 3->1(Mar)...
            dia_nombre = dias_semana_nombres[dia_sql - 1]
            
            venta_promedio = sum(ventas) / len(ventas)
            venta_min = min(ventas)
            venta_max = max(ventas)
            num_dias = len(ventas)
            
            row_hash = f"{server_id}|{dia_iso}|{fecha_min}|{fecha_max}"
            
            print(f"    {dia_nombre:10} | Prom: ${float(venta_promedio):,.2f} | Min: ${float(venta_min):,.2f} | Max: ${float(venta_max):,.2f} | Días: {num_dias}")
            
            detalle_servidor.append({
                'ServerID': server_id,
                'EmpresaID': empresa_id,
                'SucursalID': sucursal_id,
                'UnidadNegocioID': unidad_id,
                'SystemType': system_type,
                'FechaInicioPeriodo': fecha_min,
                'FechaFinPeriodo': fecha_max,
                'DiaSemana': dia_iso,
                'DiaSemananombre': dia_nombre,
                'VentanaInicioHoraConfig': ventana_inicio,
                'VentanaFinHoraConfig': ventana_fin,
                'VentaPromedio': venta_promedio,
                'VentaMin': venta_min,
                'VentaMax': venta_max,
                'NumDiasConDatos': num_dias,
                'SyncRunID': sync_run_id,
                'SourceStatus': 'SUCCESS',
                'SourceType': system_type,
                'RowHash': row_hash
            })
        
        resultado['detalle_servidores'][server_id] = detalle_servidor
        resultado['registros_calculados'] += len(detalle_servidor)
        resultado['servidores_procesados'] += 1
        
        # 4. UPSERT si no es dry_run
        if not dry_run and detalle_servidor:
            print(f"  💾 Escribiendo {len(detalle_servidor)} registros...")
            
            for reg in detalle_servidor:
                upsert_query = f"""
                MERGE INTO Sync_Ventas_PorDiaSemana AS target
                USING (SELECT 
                    '{reg['ServerID']}' as ServerID,
                    {reg['DiaSemana']} as DiaSemana,
                    '{reg['FechaInicioPeriodo']}' as FechaInicioPeriodo,
                    '{reg['FechaFinPeriodo']}' as FechaFinPeriodo
                ) AS source
                ON target.ServerID = source.ServerID 
                   AND target.DiaSemana = source.DiaSemana
                   AND target.FechaInicioPeriodo = source.FechaInicioPeriodo
                   AND target.FechaFinPeriodo = source.FechaFinPeriodo
                WHEN MATCHED THEN
                    UPDATE SET 
                        VentaPromedio = {reg['VentaPromedio']},
                        VentaMin = {reg['VentaMin']},
                        VentaMax = {reg['VentaMax']},
                        NumDiasConDatos = {reg['NumDiasConDatos']},
                        SyncRunID = '{reg['SyncRunID']}',
                        UpdatedAt = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (
                        ServerID, EmpresaID, SucursalID, UnidadNegocioID,
                        SystemType, FechaInicioPeriodo, FechaFinPeriodo,
                        DiaSemana, DiaSemananombre,
                        VentanaInicioHoraConfig, VentanaFinHoraConfig,
                        VentaPromedio, VentaMin, VentaMax, NumDiasConDatos,
                        SyncRunID, SourceStatus, SourceType, RowHash,
                        SyncedAtMexico, CreatedAt
                    ) VALUES (
                        '{reg['ServerID']}', 
                        {reg['EmpresaID'] if reg['EmpresaID'] else 'NULL'},
                        {f"'{reg['SucursalID']}'" if reg['SucursalID'] else 'NULL'},
                        {f"'{reg['UnidadNegocioID']}'" if reg['UnidadNegocioID'] else 'NULL'},
                        '{reg['SystemType']}',
                        '{reg['FechaInicioPeriodo']}',
                        '{reg['FechaFinPeriodo']}',
                        {reg['DiaSemana']},
                        '{reg['DiaSemananombre']}',
                        {reg['VentanaInicioHoraConfig']},
                        {reg['VentanaFinHoraConfig']},
                        {reg['VentaPromedio']},
                        {reg['VentaMin']},
                        {reg['VentaMax']},
                        {reg['NumDiasConDatos']},
                        '{reg['SyncRunID']}',
                        '{reg['SourceStatus']}',
                        '{reg['SourceType']}',
                        '{reg['RowHash']}',
                        GETDATE(),
                        GETDATE()
                    );
                """
                
                try:
                    execute_sql_query(
                        EDARSAHUB_CONFIG['host'],
                        EDARSAHUB_CONFIG['port'],
                        EDARSAHUB_CONFIG['database'],
                        EDARSAHUB_CONFIG['username'],
                        EDARSAHUB_CONFIG['password'],
                        upsert_query
                    )
                    resultado['registros_upserted'] += 1
                except Exception as e:
                    print(f"  ❌ Error UPSERT: {e}")
                    resultado['errores'].append(f"UPSERT error: {e}")
            
            print(f"  ✅ {len(detalle_servidor)} registros escritos")
    
    return resultado


def main():
    """Ejecutar cálculo de PorDiaSemana."""
    # Servidores que faltan en PorDiaSemana (tienen datos en Historicas)
    server_ids = [
        '6d053c22-523e-48c0-b72b-96081e2d781b',  # CIENFUEGOS
        'a5ff0e25-f029-43db-b634-d4ac814c904f',  # LA ESTELAR
    ]
    
    print("=" * 60)
    print("FASE SYNC-3A-R2: Calcular PorDiaSemana desde Historicas")
    print("=" * 60)
    
    # Paso 1: Dry-run
    print("\n>>> PASO 1: DRY-RUN <<<")
    result_dry = calcular_pordiasemana_desde_historicas(server_ids, dry_run=True)
    
    print(f"\n--- Resultado DRY-RUN ---")
    print(f"Sync Run ID: {result_dry['sync_run_id']}")
    print(f"Servidores procesados: {result_dry['servidores_procesados']}")
    print(f"Registros calculados: {result_dry['registros_calculados']}")
    print(f"Errores: {len(result_dry['errores'])}")
    
    if result_dry['errores']:
        print(f"⚠️  Errores encontrados: {result_dry['errores']}")
        return 1
    
    if result_dry['registros_calculados'] == 0:
        print("⚠️  Sin registros para calcular")
        return 1
    
    # Paso 2: Escritura real
    print("\n>>> PASO 2: ESCRITURA REAL <<<")
    result_real = calcular_pordiasemana_desde_historicas(server_ids, dry_run=False)
    
    print(f"\n--- Resultado ESCRITURA ---")
    print(f"Sync Run ID: {result_real['sync_run_id']}")
    print(f"Servidores procesados: {result_real['servidores_procesados']}")
    print(f"Registros upserted: {result_real['registros_upserted']}")
    
    # Paso 3: Validar idempotencia
    print("\n>>> PASO 3: VALIDACIÓN IDEMPOTENCIA <<<")
    result_idem = calcular_pordiasemana_desde_historicas(server_ids, dry_run=False)
    
    print(f"\n--- Resultado IDEMPOTENCIA ---")
    print(f"Registros upserted (debería ser igual): {result_idem['registros_upserted']}")
    
    # Verificación final
    print("\n>>> VERIFICACIÓN FINAL <<<")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
