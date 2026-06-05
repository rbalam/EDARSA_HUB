"""
CARGA HISTÓRICA 24 MESES - COMERCIAL V2
========================================

Subfase 2B: Carga histórica de 24 meses para las 5 unidades.

AUTORIZADO:
- Rango: 2024-05-01 a 2026-04-30 (24 meses)
- Unidades: CIENFUEGOS, LA ESTELAR, 130° MÉRIDA, 130° QRO, ORIGEN
- Destino: Comercial_KPIs_Diarios_v2 en EDARSAHUB

EJECUCIÓN POR BLOQUES:
- Bloque 1: Últimos 3 meses (Feb-Abr 2026) - Ya cargado Abril
- Bloque 2: Siguientes 9 meses (May-Ene 2025-2026)
- Bloque 3: Restantes 12 meses (May 2024 - Abr 2025)

REGLAS ESPECIALES:
- MPRO: Nube como fuente principal, local solo para días faltantes
- SoftRestaurant: ventas cerradas en KPIs, temporales en tabla separada

DATOS DE ORIGEN DISPONIBLES (verificado):
- 130° MÉRIDA: desde 2016-06-14
- CIENFUEGOS: desde 2019-12-24
- LA ESTELAR: desde 2025-06-12 (solo ~11 meses disponibles)
- 130° QRO (MPRO 0021): desde 2021-09-18
- ORIGEN (MPRO 0023): desde 2022-05-20
"""

import uuid
import time
import logging
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from dateutil.relativedelta import relativedelta

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

# Imports del módulo comercial_v2
from core.db import execute_sql_query, parse_sql_server_host, reset_server_cache
from core.secret_manager import decrypt_secret, reset_fernet_cache
from core.pool import get_pool_manager

from .schemas import (
    KPIsDiariosV2,
    SyncLogV2,
    SyncRunType,
    SyncStatus,
    ConnectionStatus,
    SistemaOrigen,
    FuenteOriginal
)
from .mappers import calcular_hash_origen, safe_decimal, safe_int
from .repository_comercial_edarsahub import (
    EDARSAHUB_CONFIG,
    upsert_kpi_diario,
    insert_sync_log,
    get_stats_by_unidad_v2
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACIÓN DE BLOQUES
# =============================================================================

# Fecha de referencia (fin de Subfase 2A)
FECHA_FIN_HISTORICO = date(2026, 4, 30)

# Bloques de ejecución
BLOQUES = {
    1: {
        'nombre': 'Bloque 1: Últimos 3 meses',
        'fecha_inicio': date(2026, 2, 1),
        'fecha_fin': date(2026, 4, 30),
        'descripcion': 'Feb-Abr 2026 (Abril ya cargado en Subfase 2A)'
    },
    2: {
        'nombre': 'Bloque 2: Meses 4-12',
        'fecha_inicio': date(2025, 5, 1),
        'fecha_fin': date(2026, 1, 31),
        'descripcion': 'May 2025 - Ene 2026'
    },
    3: {
        'nombre': 'Bloque 3: Meses 13-24',
        'fecha_inicio': date(2024, 5, 1),
        'fecha_fin': date(2025, 4, 30),
        'descripcion': 'May 2024 - Abr 2025'
    }
}

# Configuración de las 5 unidades con fechas de inicio de datos
UNIDADES_CONFIG = [
    {
        'unidad_negocio_id': 'CIENFUEGOS',
        'unidad_negocio_nombre': 'CIENFUEGOS',
        'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',
        'sucursal_id': 'DEFAULT',
        'sistema_origen': SistemaOrigen.SOFTRESTAURANT,
        'fecha_datos_desde': date(2019, 12, 24),
    },
    {
        'unidad_negocio_id': 'LA-ESTELAR',
        'unidad_negocio_nombre': 'LA ESTELAR',
        'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f',
        'sucursal_id': 'DEFAULT',
        'sistema_origen': SistemaOrigen.SOFTRESTAURANT,
        'fecha_datos_desde': date(2025, 6, 12),  # Solo ~11 meses disponibles
    },
    {
        'unidad_negocio_id': '130-MER',
        'unidad_negocio_nombre': '130° MÉRIDA',
        'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',
        'sucursal_id': 'DEFAULT',
        'sistema_origen': SistemaOrigen.SOFTRESTAURANT,
        'fecha_datos_desde': date(2016, 6, 14),
    },
    {
        'unidad_negocio_id': '130-QRO',
        'unidad_negocio_nombre': '130° QUERETARO',
        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
        'sucursal_id': '0021',
        'sistema_origen': SistemaOrigen.MPRO,
        'fecha_datos_desde': date(2021, 9, 18),
    },
    {
        'unidad_negocio_id': 'ORIGEN',
        'unidad_negocio_nombre': 'ORIGEN',
        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
        'sucursal_id': '0023',
        'sistema_origen': SistemaOrigen.MPRO,
        'fecha_datos_desde': date(2022, 5, 20),
    },
]


# =============================================================================
# ESTRUCTURA DE REPORTES
# =============================================================================

@dataclass
class ReporteMes:
    """Reporte de carga para un mes específico"""
    unidad_negocio_id: str
    mes: int
    anio: int
    dias_esperados: int = 0
    dias_cargados: int = 0
    registros_origen: int = 0
    ventas_origen: Decimal = Decimal("0")
    cheques_origen: int = 0
    pax_origen: int = 0
    registros_insertados: int = 0
    registros_actualizados: int = 0
    registros_omitidos: int = 0
    errores: int = 0
    ventas_edarsahub: Decimal = Decimal("0")
    diferencia_ventas: Decimal = Decimal("0")
    mes_sin_datos: bool = False
    fuente_usada: str = ""
    notas: str = ""


@dataclass
class ReporteBloque:
    """Reporte de un bloque completo"""
    bloque_numero: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    meses: List[ReporteMes] = field(default_factory=list)
    total_registros_insertados: int = 0
    total_registros_actualizados: int = 0
    total_registros_omitidos: int = 0
    total_errores: int = 0
    total_ventas: Decimal = Decimal("0")
    duracion_segundos: int = 0


# =============================================================================
# QUERIES
# =============================================================================

QUERY_SR_MENSUAL = """
SELECT 
    CAST(fecha AS DATE) as fecha,
    SUM(total) as ventas_total,
    SUM(total - ISNULL(propina, 0)) as ventas_sin_propina,
    SUM(ISNULL(propina, 0)) as propinas,
    COUNT(DISTINCT folio) as num_cheques,
    SUM(ISNULL(nopersonas, 1)) as num_personas
FROM cheques
WHERE CAST(fecha AS DATE) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
  AND cancelado = 0
  AND cierre IS NOT NULL
GROUP BY CAST(fecha AS DATE)
ORDER BY fecha
"""

QUERY_MPRO_MENSUAL = """
SELECT 
    CAST(ve.Vn_Fecha AS DATE) as fecha,
    SUM(ve.Vn_Precio_Neto_Importe) as Vn_Precio_Neto_Importe,
    COUNT(DISTINCT ve.Vn_Folio) as num_folios,
    SUM(ISNULL(c.Co_Personas, 1)) as total_personas
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE CAST(ve.Vn_Fecha AS DATE) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
GROUP BY CAST(ve.Vn_Fecha AS DATE)
ORDER BY fecha
"""


# =============================================================================
# CONEXIÓN A SERVIDOR
# =============================================================================

def get_server_connection(server_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene configuración de conexión usando EDARSAHUB + decrypt_secret."""
    query = f"""
    SELECT 
        id, nombre, host, port, database_name, username, password_encrypted, system_type, activo
    FROM Servidores_Conexiones
    WHERE id = '{id}'
    """
    
    try:
        result = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        if not result:
            return None
        
        row = result[0]
        pwd_enc = row.get('password_encrypted', '')
        try:
            password = decrypt_secret(pwd_enc)
        except Exception:
            password = pwd_enc
        
        host_raw = row.get('host', '')
        default_port = row.get('port') or 1433
        hostname, parsed_port, instance = parse_sql_server_host(host_raw, default_port)
        
        return {
            'id': str(row['id']),
            'nombre': row['nombre'],
            'host': hostname,
            'host_raw': host_raw,
            'port': parsed_port,
            'instance': instance,
            'database_name': row['database_name'],
            'username': row['username'],
            'password': password,
            'system_type': row['system_type'],
            'activo': row['activo']
        }
    except Exception as e:
        logger.error(f"Error obteniendo config de servidor {server_id}: {e}")
        return None


def limpiar_caches():
    """Limpia caches antes de iniciar carga."""
    reset_fernet_cache()
    reset_server_cache()
    try:
        pm = get_pool_manager()
        # Cerrar pools de unidades problemáticas
        pm.close_pool('serverestelar.ddns.net', 6969, 'softrestaurant12')
    except:
        pass


# =============================================================================
# CARGA POR MES
# =============================================================================

def cargar_mes_softrestaurant(
    unidad: Dict,
    run_id: str,
    mes: int,
    anio: int
) -> ReporteMes:
    """Carga un mes específico de datos SoftRestaurant."""
    
    reporte = ReporteMes(
        unidad_negocio_id=unidad['unidad_negocio_id'],
        mes=mes,
        anio=anio,
        fuente_usada='SOFTRESTAURANT'
    )
    
    # Calcular fechas del mes
    fecha_inicio = date(anio, mes, 1)
    if mes == 12:
        fecha_fin = date(anio, 12, 31)
    else:
        fecha_fin = date(anio, mes + 1, 1) - timedelta(days=1)
    
    # Verificar si el mes tiene datos (fecha_datos_desde)
    if fecha_fin < unidad.get('fecha_datos_desde', date(2000, 1, 1)):
        reporte.mes_sin_datos = True
        reporte.notas = f"Mes anterior a inicio de datos ({unidad['fecha_datos_desde']})"
        return reporte
    
    # Ajustar fecha_inicio si es anterior al inicio de datos
    if fecha_inicio < unidad.get('fecha_datos_desde', date(2000, 1, 1)):
        fecha_inicio = unidad['fecha_datos_desde']
    
    reporte.dias_esperados = (fecha_fin - fecha_inicio).days + 1
    
    # Obtener conexión
    server = get_server_connection(unidad['server_id'])
    if not server:
        reporte.errores = 1
        reporte.notas = "No se pudo obtener configuración del servidor"
        return reporte
    
    # Construir y ejecutar query
    query = QUERY_SR_MENSUAL.format(
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat()
    )
    
    try:
        rows = execute_sql_query(
            server['host'],
            server['port'],
            server['database_name'],
            server['username'],
            server['password'],
            query
        )
    except Exception as e:
        reporte.errores = 1
        reporte.notas = f"Error query: {str(e)[:100]}"
        return reporte
    
    if not rows:
        reporte.mes_sin_datos = True
        reporte.notas = "Query retornó 0 registros (mes sin operación)"
        return reporte
    
    # Procesar registros
    reporte.registros_origen = len(rows)
    
    for row in rows:
        try:
            fecha = row.get('fecha')
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha[:10], '%Y-%m-%d').date()
            
            ventas_total = safe_decimal(row.get('ventas_total', 0))
            ventas_sin_propina = safe_decimal(row.get('ventas_sin_propina', 0))
            propinas = safe_decimal(row.get('propinas', 0))
            tickets = safe_int(row.get('num_cheques', 0))
            pax = safe_int(row.get('num_personas', 0))
            
            reporte.ventas_origen += ventas_total
            reporte.cheques_origen += tickets
            reporte.pax_origen += pax
            
            ticket_promedio = ventas_total / tickets if tickets > 0 else Decimal("0")
            pax_promedio = Decimal(str(pax / tickets)) if tickets > 0 else Decimal("0")
            
            # Hash estable basado en datos de negocio
            hash_origen = calcular_hash_origen(
                unidad['server_id'],
                unidad['sucursal_id'],
                fecha,
                ventas_total,
                tickets,
                pax
            )
            
            kpi = KPIsDiariosV2(
                unidad_negocio_id=unidad['unidad_negocio_id'],
                unidad_negocio_nombre=unidad['unidad_negocio_nombre'],
                server_id=unidad['server_id'],
                sucursal_id=unidad['sucursal_id'],
                sucursal_nombre=unidad['unidad_negocio_nombre'],
                sistema_origen=SistemaOrigen.SOFTRESTAURANT,
                
                fecha_operacion=fecha,
                anio=fecha.year,
                mes=fecha.month,
                dia=fecha.day,
                
                ventas_total=ventas_total,
                ventas_sin_propina=ventas_sin_propina,
                propinas_total=propinas,
                tickets_total=tickets,
                pax_total=pax,
                ticket_promedio=ticket_promedio,
                pax_promedio=pax_promedio,
                
                ventas_cerradas=ventas_total,
                ventas_abiertas=Decimal("0"),
                total_estimado_dia=ventas_total,
                
                es_venta_abierta=False,
                es_corte_cerrado=True,
                es_demo=False,
                activo=True,
                
                fuente_original=FuenteOriginal.SQL_LIVE,
                hash_origen=hash_origen,
                sync_run_id=run_id
            )
            
            result = upsert_kpi_diario(kpi)
            
            if result['action'] == 'INSERT':
                reporte.registros_insertados += 1
            elif result['action'] == 'UPDATE':
                reporte.registros_actualizados += 1
            else:
                reporte.registros_omitidos += 1
            
            reporte.dias_cargados += 1
                
        except Exception as e:
            reporte.errores += 1
    
    return reporte


def cargar_mes_mpro(
    unidad: Dict,
    run_id: str,
    mes: int,
    anio: int
) -> ReporteMes:
    """Carga un mes específico de datos MPRO."""
    
    reporte = ReporteMes(
        unidad_negocio_id=unidad['unidad_negocio_id'],
        mes=mes,
        anio=anio,
        fuente_usada='MPRO_NUBE'
    )
    
    # Calcular fechas del mes
    fecha_inicio = date(anio, mes, 1)
    if mes == 12:
        fecha_fin = date(anio, 12, 31)
    else:
        fecha_fin = date(anio, mes + 1, 1) - timedelta(days=1)
    
    # Verificar si el mes tiene datos
    if fecha_fin < unidad.get('fecha_datos_desde', date(2000, 1, 1)):
        reporte.mes_sin_datos = True
        reporte.notas = f"Mes anterior a inicio de datos ({unidad['fecha_datos_desde']})"
        return reporte
    
    if fecha_inicio < unidad.get('fecha_datos_desde', date(2000, 1, 1)):
        fecha_inicio = unidad['fecha_datos_desde']
    
    reporte.dias_esperados = (fecha_fin - fecha_inicio).days + 1
    
    # Obtener conexión
    server = get_server_connection(unidad['server_id'])
    if not server:
        reporte.errores = 1
        reporte.notas = "No se pudo obtener configuración del servidor"
        return reporte
    
    # Construir y ejecutar query
    query = QUERY_MPRO_MENSUAL.format(
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        sucursal_id=unidad['sucursal_id']
    )
    
    try:
        rows = execute_sql_query(
            server['host'],
            server['port'],
            server['database_name'],
            server['username'],
            server['password'],
            query
        )
    except Exception as e:
        reporte.errores = 1
        reporte.notas = f"Error query: {str(e)[:100]}"
        return reporte
    
    if not rows:
        reporte.mes_sin_datos = True
        reporte.notas = "Query retornó 0 registros (mes sin operación)"
        return reporte
    
    # Procesar registros
    reporte.registros_origen = len(rows)
    
    for row in rows:
        try:
            fecha = row.get('fecha')
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha[:10], '%Y-%m-%d').date()
            
            ventas_total = safe_decimal(row.get('Vn_Precio_Neto_Importe', 0))
            tickets = safe_int(row.get('num_folios', 0))
            pax = safe_int(row.get('total_personas', 0))
            
            reporte.ventas_origen += ventas_total
            reporte.cheques_origen += tickets
            reporte.pax_origen += pax
            
            ticket_promedio = ventas_total / tickets if tickets > 0 else Decimal("0")
            pax_promedio = Decimal(str(pax / tickets)) if tickets > 0 else Decimal("0")
            
            # Hash estable basado en datos de negocio (no depende de fuente)
            hash_origen = calcular_hash_origen(
                unidad['server_id'],
                unidad['sucursal_id'],
                fecha,
                ventas_total,
                tickets,
                pax
            )
            
            kpi = KPIsDiariosV2(
                unidad_negocio_id=unidad['unidad_negocio_id'],
                unidad_negocio_nombre=unidad['unidad_negocio_nombre'],
                server_id=unidad['server_id'],
                sucursal_id=unidad['sucursal_id'],
                sucursal_nombre=unidad['unidad_negocio_nombre'],
                sistema_origen=SistemaOrigen.MPRO,
                
                fecha_operacion=fecha,
                anio=fecha.year,
                mes=fecha.month,
                dia=fecha.day,
                
                ventas_total=ventas_total,
                ventas_sin_propina=ventas_total,
                propinas_total=Decimal("0"),
                tickets_total=tickets,
                pax_total=pax,
                ticket_promedio=ticket_promedio,
                pax_promedio=pax_promedio,
                
                ventas_cerradas=ventas_total,
                ventas_abiertas=Decimal("0"),
                total_estimado_dia=ventas_total,
                
                es_venta_abierta=False,
                es_corte_cerrado=True,
                es_demo=False,
                activo=True,
                
                fuente_original=FuenteOriginal.SQL_LIVE,
                hash_origen=hash_origen,
                sync_run_id=run_id
            )
            
            result = upsert_kpi_diario(kpi)
            
            if result['action'] == 'INSERT':
                reporte.registros_insertados += 1
            elif result['action'] == 'UPDATE':
                reporte.registros_actualizados += 1
            else:
                reporte.registros_omitidos += 1
            
            reporte.dias_cargados += 1
                
        except Exception as e:
            reporte.errores += 1
    
    return reporte


# =============================================================================
# CARGA POR BLOQUE
# =============================================================================

def ejecutar_bloque(bloque_num: int) -> ReporteBloque:
    """Ejecuta la carga de un bloque completo."""
    
    bloque_config = BLOQUES[bloque_num]
    
    reporte = ReporteBloque(
        bloque_numero=bloque_num,
        nombre=bloque_config['nombre'],
        fecha_inicio=bloque_config['fecha_inicio'],
        fecha_fin=bloque_config['fecha_fin']
    )
    
    start_time = time.time()
    run_id = f"HIST-B{bloque_num}-{str(uuid.uuid4())[:8]}"
    
    print(f"\n{'='*80}")
    print(f"{bloque_config['nombre']}")
    print(f"Run ID: {run_id}")
    print(f"Rango: {bloque_config['fecha_inicio']} a {bloque_config['fecha_fin']}")
    print(f"{'='*80}")
    
    # Limpiar caches antes de cada bloque
    limpiar_caches()
    
    # Iterar por cada unidad
    for unidad in UNIDADES_CONFIG:
        print(f"\n[{unidad['unidad_negocio_id']}] Procesando {unidad['unidad_negocio_nombre']}...")
        
        # Generar lista de meses en el bloque
        fecha_actual = bloque_config['fecha_inicio']
        while fecha_actual <= bloque_config['fecha_fin']:
            mes = fecha_actual.month
            anio = fecha_actual.year
            
            # Cargar según sistema
            if unidad['sistema_origen'] == SistemaOrigen.SOFTRESTAURANT:
                reporte_mes = cargar_mes_softrestaurant(unidad, run_id, mes, anio)
            else:
                reporte_mes = cargar_mes_mpro(unidad, run_id, mes, anio)
            
            reporte.meses.append(reporte_mes)
            
            # Acumular totales
            reporte.total_registros_insertados += reporte_mes.registros_insertados
            reporte.total_registros_actualizados += reporte_mes.registros_actualizados
            reporte.total_registros_omitidos += reporte_mes.registros_omitidos
            reporte.total_errores += reporte_mes.errores
            reporte.total_ventas += reporte_mes.ventas_origen
            
            # Imprimir resumen del mes
            status = "✅" if reporte_mes.errores == 0 and not reporte_mes.mes_sin_datos else "⚠️"
            if reporte_mes.mes_sin_datos:
                status = "📭"
            print(f"  {anio}-{mes:02d}: {status} {reporte_mes.dias_cargados} días, ${float(reporte_mes.ventas_origen):,.0f}")
            if reporte_mes.notas:
                print(f"         Nota: {reporte_mes.notas}")
            
            # Avanzar al siguiente mes
            if mes == 12:
                fecha_actual = date(anio + 1, 1, 1)
            else:
                fecha_actual = date(anio, mes + 1, 1)
    
    # Registrar SyncLog general del bloque
    log = SyncLogV2(
        run_id=run_id,
        run_type=SyncRunType.HISTORICAL,
        unidad_negocio_id="TODAS",
        server_id="MULTIPLE",
        sucursal_id="MULTIPLE",
        fecha_inicio=bloque_config['fecha_inicio'],
        fecha_fin=bloque_config['fecha_fin'],
        status=SyncStatus.SUCCESS if reporte.total_errores == 0 else SyncStatus.PARTIAL,
        records_processed=reporte.total_registros_insertados + reporte.total_registros_actualizados + reporte.total_registros_omitidos,
        records_inserted=reporte.total_registros_insertados,
        records_updated=reporte.total_registros_actualizados,
        records_skipped=reporte.total_registros_omitidos,
        records_errored=reporte.total_errores,
        source_connection_status=ConnectionStatus.ONLINE,
        duration_seconds=int(time.time() - start_time)
    )
    insert_sync_log(log)
    
    reporte.duracion_segundos = int(time.time() - start_time)
    
    print(f"\n{'='*80}")
    print(f"RESUMEN {bloque_config['nombre']}")
    print(f"{'='*80}")
    print(f"Insertados: {reporte.total_registros_insertados}")
    print(f"Actualizados: {reporte.total_registros_actualizados}")
    print(f"Omitidos: {reporte.total_registros_omitidos}")
    print(f"Errores: {reporte.total_errores}")
    print(f"Ventas totales: ${float(reporte.total_ventas):,.2f}")
    print(f"Duración: {reporte.duracion_segundos} segundos")
    
    return reporte


def verificar_bloque(bloque_num: int) -> Dict:
    """Verifica los datos cargados en un bloque."""
    
    bloque_config = BLOQUES[bloque_num]
    
    query = f"""
    SELECT 
        unidad_negocio_id,
        COUNT(*) as registros,
        SUM(ventas_total) as ventas,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM Comercial_KPIs_Diarios_v2
    WHERE fecha_operacion BETWEEN '{bloque_config['fecha_inicio']}' AND '{bloque_config['fecha_fin']}'
      AND activo = 1
    GROUP BY unidad_negocio_id
    ORDER BY unidad_negocio_id
    """
    
    result = execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )
    
    return {
        'bloque': bloque_num,
        'rango': f"{bloque_config['fecha_inicio']} a {bloque_config['fecha_fin']}",
        'unidades': result
    }


def verificar_abril_2026() -> Dict:
    """Verifica que abril 2026 siga igual que Subfase 2A."""
    
    query = """
    SELECT 
        COUNT(*) as registros,
        SUM(ventas_total) as ventas_total,
        COUNT(DISTINCT unidad_negocio_id) as unidades
    FROM Comercial_KPIs_Diarios_v2
    WHERE fecha_operacion BETWEEN '2026-04-01' AND '2026-04-30'
      AND activo = 1
    """
    
    result = execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )
    
    if result:
        return {
            'registros': result[0]['registros'],
            'ventas': float(result[0]['ventas_total']),
            'unidades': result[0]['unidades'],
            'esperado_registros': 148,
            'esperado_ventas': 15755816.55,
            'coincide': (
                result[0]['registros'] == 148 and
                abs(float(result[0]['ventas_total']) - 15755816.55) < 1
            )
        }
    return {'error': 'No hay datos'}


def verificar_duplicados_global() -> Dict:
    """Verifica duplicados en toda la tabla v2."""
    
    query = """
    SELECT 
        unidad_negocio_id,
        sucursal_id,
        fecha_operacion,
        COUNT(*) as count
    FROM Comercial_KPIs_Diarios_v2
    GROUP BY unidad_negocio_id, sucursal_id, fecha_operacion
    HAVING COUNT(*) > 1
    """
    
    result = execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )
    
    return {
        'tiene_duplicados': len(result) > 0,
        'duplicados': result
    }


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

def ejecutar_subfase_2b_bloque(bloque_num: int, corrida: int = 1):
    """
    Ejecuta un bloque específico de la Subfase 2B.
    
    Args:
        bloque_num: 1, 2 o 3
        corrida: 1 para carga inicial, 2 para idempotencia
    """
    
    print(f"\n{'#'*80}")
    print(f"# SUBFASE 2B - CARGA HISTÓRICA 24 MESES - CORRIDA {corrida}")
    print(f"# BLOQUE {bloque_num}")
    print(f"{'#'*80}")
    
    # Ejecutar bloque
    reporte = ejecutar_bloque(bloque_num)
    
    # Verificar datos
    print(f"\n{'='*80}")
    print("VERIFICACIÓN DEL BLOQUE")
    print(f"{'='*80}")
    
    verificacion = verificar_bloque(bloque_num)
    for u in verificacion['unidades']:
        print(f"  {u['unidad_negocio_id']}: {u['registros']} registros, ${float(u['ventas']):,.2f}")
    
    # Verificar abril 2026 no cambió
    if bloque_num == 1:
        print(f"\n{'='*80}")
        print("VALIDACIÓN ABRIL 2026 (Subfase 2A)")
        print(f"{'='*80}")
        val_abril = verificar_abril_2026()
        print(f"  Registros: {val_abril.get('registros')} (esperado: 148)")
        print(f"  Ventas: ${val_abril.get('ventas'):,.2f} (esperado: $15,755,816.55)")
        print(f"  Coincide: {'✅' if val_abril.get('coincide') else '❌'}")
    
    # Verificar duplicados
    print(f"\n{'='*80}")
    print("VERIFICACIÓN DE DUPLICADOS")
    print(f"{'='*80}")
    dups = verificar_duplicados_global()
    print(f"  Duplicados: {len(dups['duplicados']) if dups['duplicados'] else 0}")
    
    return reporte


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SCRIPT DE CARGA HISTÓRICA 24 MESES - SUBFASE 2B")
    print("="*80)
    print("\nUso:")
    print("  from modules.comercial_v2.carga_historica_24_meses import ejecutar_subfase_2b_bloque")
    print("  ejecutar_subfase_2b_bloque(1)  # Bloque 1: Feb-Abr 2026")
    print("  ejecutar_subfase_2b_bloque(2)  # Bloque 2: May 2025 - Ene 2026")
    print("  ejecutar_subfase_2b_bloque(3)  # Bloque 3: May 2024 - Abr 2025")
    print("="*80)
