#!/usr/bin/env python3
"""
BACKFILL OFICIAL: CIENFUEGOS Días 19 y 20 de Mayo 2026
======================================================
Script para ejecutar desde la infraestructura interna de EDARSA.

PREREQUISITOS:
- Acceso de red al servidor SoftRestaurant de CIENFUEGOS (189.162.155.142:6669)
- Variables de entorno configuradas (SERVER_SECRET_KEY, JWT_SECRET, etc.)
- Ejecución desde el directorio /app/backend

USO:
    cd /app/backend
    python3 scripts/backfill_cienfuegos_mayo_2026.py

AUTOR: E1 Agent
FECHA: 2026-05-25
TICKET: P0-B RECONCILIACION CIENFUEGOS
"""

import os
import sys
from pathlib import Path

# Cargar variables de entorno desde .env
env_path = Path('/app/backend/.env')
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

from datetime import date
import uuid
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verificar_prerequisitos():
    """Verifica que el entorno esté correctamente configurado."""
    print('=' * 70)
    print('VERIFICACIÓN DE PREREQUISITOS')
    print('=' * 70)
    
    errores = []
    
    # 1. Verificar variables de entorno
    required_vars = ['JWT_SECRET', 'SERVER_SECRET_KEY', 'EDARSAHUB_HOST']
    for var in required_vars:
        if not os.environ.get(var):
            errores.append(f'Variable de entorno no configurada: {var}')
        else:
            print(f'  ✅ {var}: Configurada')
    
    # 2. Verificar conexión a EDARSAHUB
    try:
        import pymssql
        conn = pymssql.connect(
            server=os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
            port=int(os.environ.get('EDARSAHUB_PORT', 1433)),
            database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
            user=os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
            password=os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
            login_timeout=30
        )
        conn.close()
        print('  ✅ EDARSAHUB: Accesible')
    except Exception as e:
        errores.append(f'No se puede conectar a EDARSAHUB: {e}')
    
    # 3. Verificar módulos
    try:
        from modules.comercial_v2.sync_comercial_edarsahub import (
            sync_softrestaurant_ventas_cerradas,
            get_server_connection_config
        )
        from modules.comercial_v2.schemas import UnidadNegocioConfig, SistemaOrigen
        print('  ✅ Módulos de sync: Cargados')
    except Exception as e:
        errores.append(f'Error cargando módulos: {e}')
    
    if errores:
        print('\n❌ ERRORES ENCONTRADOS:')
        for e in errores:
            print(f'  - {e}')
        return False
    
    print('\n✅ Todos los prerequisitos verificados')
    return True


def verificar_conectividad_cienfuegos():
    """Verifica conectividad al servidor SoftRestaurant de CIENFUEGOS."""
    print('\n' + '=' * 70)
    print('VERIFICACIÓN DE CONECTIVIDAD A CIENFUEGOS')
    print('=' * 70)
    
    from modules.comercial_v2.sync_comercial_edarsahub import get_server_connection_config
    
    server_config = get_server_connection_config('6d053c22-523e-48c0-b72b-96081e2d781b')
    
    if not server_config:
        print('❌ No se pudo obtener configuración del servidor')
        return False, None
    
    print(f'  Host: {server_config.get("host")}')
    print(f'  Puerto: {server_config.get("port")}')
    print(f'  BD: {server_config.get("database_name")}')
    print(f'  Usuario: {server_config.get("username")}')
    
    # Probar conexión
    try:
        import pymssql
        conn = pymssql.connect(
            server=server_config['host'],
            port=server_config['port'],
            database=server_config['database_name'],
            user=server_config['username'],
            password=server_config['password'],
            login_timeout=30
        )
        cursor = conn.cursor(as_dict=True)
        
        # Verificar datos disponibles
        query = """
        SELECT 
            CAST(fecha AS DATE) as fecha_op,
            COUNT(*) as cheques,
            SUM(total) as venta_total
        FROM cheques
        WHERE CAST(fecha AS DATE) IN ('2026-05-19', '2026-05-20')
          AND cancelado = 0
          AND cierre IS NOT NULL
        GROUP BY CAST(fecha AS DATE)
        ORDER BY fecha_op
        """
        cursor.execute(query)
        datos = cursor.fetchall()
        conn.close()
        
        print('\n  ✅ CONEXIÓN EXITOSA')
        print('\n  DATOS DISPONIBLES EN ORIGEN:')
        if datos:
            for d in datos:
                print(f'    {d["fecha_op"]} | Cheques: {d["cheques"]} | Venta: ${float(d["venta_total"]):,.2f}')
            return True, datos
        else:
            print('    ⚠️ No hay cheques cerrados para días 19 y 20')
            return True, []
            
    except Exception as e:
        print(f'\n  ❌ ERROR DE CONEXIÓN: {e}')
        return False, None


def verificar_no_duplicados():
    """Verifica que no existan registros para los días a insertar."""
    print('\n' + '=' * 70)
    print('VERIFICACIÓN DE NO DUPLICADOS')
    print('=' * 70)
    
    import pymssql
    conn = pymssql.connect(
        server=os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
        port=int(os.environ.get('EDARSAHUB_PORT', 1433)),
        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
        user=os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
        password=os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
        login_timeout=30
    )
    cursor = conn.cursor(as_dict=True)
    
    query = """
    SELECT fecha_operacion, ventas_total
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = 'CIENFUEGOS'
      AND fecha_operacion IN ('2026-05-19', '2026-05-20')
      AND activo = 1
    """
    cursor.execute(query)
    existentes = cursor.fetchall()
    conn.close()
    
    if existentes:
        print('  ⚠️ Ya existen registros para estas fechas:')
        for e in existentes:
            print(f'    {e["fecha_operacion"]}: ${float(e["ventas_total"]):,.2f}')
        print('\n  El proceso usará UPSERT (actualizar si existe)')
        return True
    else:
        print('  ✅ No existen registros duplicados')
        return True


def ejecutar_backfill():
    """Ejecuta el backfill usando el mecanismo oficial."""
    print('\n' + '=' * 70)
    print('EJECUCIÓN DEL BACKFILL')
    print('=' * 70)
    
    from modules.comercial_v2.sync_comercial_edarsahub import sync_softrestaurant_ventas_cerradas
    from modules.comercial_v2.schemas import UnidadNegocioConfig, SistemaOrigen
    
    config = UnidadNegocioConfig(
        unidad_negocio_id='CIENFUEGOS',
        unidad_negocio_nombre='CIENFUEGOS',
        server_id='6d053c22-523e-48c0-b72b-96081e2d781b',
        sucursal_id='DEFAULT',
        sucursal_nombre='CIENFUEGOS',
        sistema_origen=SistemaOrigen.SOFTRESTAURANT,
        activo=True
    )
    
    fecha_inicio = date(2026, 5, 19)
    fecha_fin = date(2026, 5, 20)
    run_id = f'BACKFILL-20260525-CIENFUEGOS-{str(uuid.uuid4())[:4]}'
    
    print(f'  Configuración: {config.unidad_negocio_id}')
    print(f'  Rango: {fecha_inicio} a {fecha_fin}')
    print(f'  Run ID: {run_id}')
    print('\n  Ejecutando sync...')
    
    resultado = sync_softrestaurant_ventas_cerradas(
        config=config,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        run_id=run_id
    )
    
    return resultado


def validar_resultado():
    """Valida los registros insertados."""
    print('\n' + '=' * 70)
    print('VALIDACIÓN POST-BACKFILL')
    print('=' * 70)
    
    import pymssql
    conn = pymssql.connect(
        server=os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
        port=int(os.environ.get('EDARSAHUB_PORT', 1433)),
        database=os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
        user=os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
        password=os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
        login_timeout=30
    )
    cursor = conn.cursor(as_dict=True)
    
    # Verificar días insertados
    query = """
    SELECT 
        fecha_operacion,
        ventas_total,
        ventas_sin_propina,
        propinas_total,
        tickets_total,
        sync_run_id,
        fecha_sincronizacion
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = 'CIENFUEGOS'
      AND fecha_operacion IN ('2026-05-19', '2026-05-20')
      AND activo = 1
    ORDER BY fecha_operacion
    """
    cursor.execute(query)
    registros = cursor.fetchall()
    
    if registros:
        print('  ✅ REGISTROS ENCONTRADOS:')
        for r in registros:
            print(f'    {r["fecha_operacion"]}:')
            print(f'      Venta Total: ${float(r["ventas_total"]):,.2f}')
            print(f'      Venta sin Propina: ${float(r["ventas_sin_propina"]):,.2f}')
            print(f'      Propinas: ${float(r["propinas_total"]):,.2f}')
            print(f'      Tickets: {r["tickets_total"]}')
            print(f'      Sync Run ID: {r["sync_run_id"]}')
    else:
        print('  ❌ No se encontraron registros para los días 19 y 20')
    
    # Contar total de días de mayo
    query_total = """
    SELECT COUNT(*) as total
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = 'CIENFUEGOS'
      AND fecha_operacion BETWEEN '2026-05-01' AND '2026-05-31'
      AND activo = 1
    """
    cursor.execute(query_total)
    total = cursor.fetchone()
    print(f'\n  Total días mayo 2026: {total["total"]}')
    
    conn.close()
    return len(registros)


def main():
    """Función principal."""
    print('\n' + '=' * 70)
    print('BACKFILL CIENFUEGOS - DÍAS 19 Y 20 DE MAYO 2026')
    print('=' * 70)
    print('Ticket: P0-B RECONCILIACIÓN CIENFUEGOS')
    print('Fecha ejecución: 2026-05-25')
    print('=' * 70)
    
    # Paso 1: Verificar prerequisitos
    if not verificar_prerequisitos():
        print('\n❌ ABORTADO: Prerequisitos no cumplidos')
        sys.exit(1)
    
    # Paso 2: Verificar conectividad
    conectado, datos_origen = verificar_conectividad_cienfuegos()
    if not conectado:
        print('\n❌ ABORTADO: No hay conectividad al servidor CIENFUEGOS')
        print('   Este script debe ejecutarse desde un entorno con acceso a la red interna.')
        sys.exit(1)
    
    if not datos_origen:
        print('\n⚠️ ADVERTENCIA: No hay datos disponibles en origen para los días 19 y 20')
        respuesta = input('   ¿Desea continuar de todos modos? (s/N): ')
        if respuesta.lower() != 's':
            print('   Abortado por el usuario')
            sys.exit(0)
    
    # Paso 3: Verificar no duplicados
    verificar_no_duplicados()
    
    # Paso 4: Confirmar ejecución
    print('\n' + '-' * 70)
    respuesta = input('¿Ejecutar backfill? (s/N): ')
    if respuesta.lower() != 's':
        print('Abortado por el usuario')
        sys.exit(0)
    
    # Paso 5: Ejecutar backfill
    resultado = ejecutar_backfill()
    
    # Mostrar resultado
    print('\n' + '=' * 70)
    print('RESULTADO DEL BACKFILL')
    print('=' * 70)
    print(f'  Éxito: {resultado.success}')
    print(f'  Procesados: {resultado.records_processed}')
    print(f'  Insertados: {resultado.records_inserted}')
    print(f'  Actualizados: {resultado.records_updated}')
    print(f'  Omitidos: {resultado.records_skipped}')
    print(f'  Errores: {resultado.records_errored}')
    print(f'  Duración: {resultado.duration_seconds} seg')
    
    if resultado.error_message:
        print(f'  Error: {resultado.error_message}')
    
    # Paso 6: Validar resultado
    registros = validar_resultado()
    
    # Resumen final
    print('\n' + '=' * 70)
    print('RESUMEN FINAL')
    print('=' * 70)
    
    if resultado.success and registros == 2:
        print('✅ BACKFILL COMPLETADO EXITOSAMENTE')
        print('   - 2 días insertados (19 y 20 de mayo)')
        print('   - KPI de ventas sin propinas disponible')
        print('   - Trazabilidad completa con sync_run_id')
    elif resultado.success and registros < 2:
        print('⚠️ BACKFILL COMPLETADO CON ADVERTENCIAS')
        print(f'   - Solo {registros} días insertados de 2 esperados')
        print('   - Verificar datos en origen')
    else:
        print('❌ BACKFILL FALLIDO')
        print(f'   - Error: {resultado.error_message}')
    
    return resultado.success


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print('\n\nAbortado por el usuario')
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ ERROR INESPERADO: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
