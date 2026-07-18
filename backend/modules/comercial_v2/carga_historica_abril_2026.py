"""
CARGA HISTORICA PILOTO - ABRIL 2026
====================================

Subfase 2A: Carga histórica piloto de abril 2026 para las 5 unidades.

AUTORIZADO:
- Rango: 2026-04-01 a 2026-04-30
- Unidades: CIENFUEGOS, LA ESTELAR, 130° MÉRIDA, 130° QRO, ORIGEN
- Destino: Comercial_KPIs_Diarios_v2 en EDARSAHUB

NO AUTORIZADO:
- Carga de 24 meses
- Modificar Comercial actual
- Modificar frontend
- Activar scheduler

VALIDACIÓN ESPECIAL (2026-04-30):
- CIENFUEGOS: $172,765 / 45 cheques / 125 PAX
- LA ESTELAR: $78,795 / 59 cheques / 160 PAX
- 130° MÉRIDA: $89,115 / 26 cheques / 66 PAX
- 130° QRO: $129,257 / 24 folios / 59 PAX
- ORIGEN: $50,411 / 25 folios / 73 PAX
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

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

# Imports del módulo comercial_v2
from core.db import execute_sql_query, parse_sql_server_host
from core.secret_manager import decrypt_secret, reset_fernet_cache

# Resetear cache del secret manager para asegurar que use la clave correcta
reset_fernet_cache()

from .schemas import (
    KPIsDiariosV2,
    SyncLogV2,
    SyncRunType,
    SyncStatus,
    ConnectionStatus,
    UnidadNegocioConfig,
    SistemaOrigen,
    SyncResult,
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
# CONFIGURACIÓN PILOTO ABRIL 2026
# =============================================================================

FECHA_INICIO_PILOTO = date(2026, 4, 1)
FECHA_FIN_PILOTO = date(2026, 4, 30)

# Datos de validación para 2026-04-30 (proporcionados en autorización)
VALIDACION_30_ABRIL = {
    'CIENFUEGOS': {'ventas': 172765.00, 'cheques': 45, 'pax': 125},
    'LA-ESTELAR': {'ventas': 78795.00, 'cheques': 59, 'pax': 160},
    '130-MER': {'ventas': 89115.00, 'cheques': 26, 'pax': 66},
    '130-QRO': {'ventas': 129257.00, 'cheques': 24, 'pax': 59},
    'ORIGEN': {'ventas': 50411.00, 'cheques': 25, 'pax': 73},
}

# Configuración de las 5 unidades autorizadas (IDs verificados de EDARSAHUB)
UNIDADES_AUTORIZADAS = [
    {
        'unidad_negocio_id': 'CIENFUEGOS',
        'unidad_negocio_nombre': 'CIENFUEGOS',
        'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',  # ID correcto de EDARSAHUB
        'sucursal_id': 'DEFAULT',
        'sistema_origen': SistemaOrigen.SOFTRESTAURANT,
    },
    {
        'unidad_negocio_id': 'LA-ESTELAR',
        'unidad_negocio_nombre': 'LA ESTELAR',
        'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f',  # ID correcto de EDARSAHUB
        'sucursal_id': 'DEFAULT',
        'sistema_origen': SistemaOrigen.SOFTRESTAURANT,
    },
    {
        'unidad_negocio_id': '130-MER',
        'unidad_negocio_nombre': '130° MÉRIDA',
        'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',  # ID correcto de EDARSAHUB
        'sucursal_id': 'DEFAULT',
        'sistema_origen': SistemaOrigen.SOFTRESTAURANT,
    },
    {
        'unidad_negocio_id': '130-QRO',
        'unidad_negocio_nombre': '130° QUERETARO',
        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',  # ID correcto de EDARSAHUB (ManagmentPro)
        'sucursal_id': '0021',
        'sistema_origen': SistemaOrigen.MPRO,
    },
    {
        'unidad_negocio_id': 'ORIGEN',
        'unidad_negocio_nombre': 'ORIGEN',
        'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',  # ID correcto de EDARSAHUB (ManagmentPro)
        'sucursal_id': '0023',
        'sistema_origen': SistemaOrigen.MPRO,
    },
]


# =============================================================================
# ESTRUCTURA DE REPORTE
# =============================================================================

@dataclass
class ReporteUnidad:
    """Reporte de carga para una unidad"""
    unidad_negocio_id: str
    server_id: str
    sistema_origen: str
    query_ejecutada: str = ""
    rango_procesado: str = ""
    registros_origen: int = 0
    ventas_origen: Decimal = Decimal("0")
    cheques_origen: int = 0
    pax_origen: int = 0
    registros_insertados: int = 0
    registros_actualizados: int = 0
    registros_omitidos: int = 0
    errores: int = 0
    ventas_edarsahub: Decimal = Decimal("0")
    cheques_edarsahub: int = 0
    pax_edarsahub: int = 0
    diferencia_ventas: Decimal = Decimal("0")
    diferencia_cheques: int = 0
    diferencia_pax: int = 0
    hash_origen_muestra: str = ""
    sync_log_id: str = ""
    fecha_min: str = ""
    fecha_max: str = ""
    validacion_30_abril: Dict = field(default_factory=dict)
    errores_detalle: List[str] = field(default_factory=list)
    duracion_segundos: int = 0


@dataclass  
class ReporteCorrida:
    """Reporte de una corrida completa"""
    corrida_numero: int
    timestamp: str
    unidades: List[ReporteUnidad] = field(default_factory=list)
    total_insertados: int = 0
    total_actualizados: int = 0
    total_omitidos: int = 0
    total_errores: int = 0
    duracion_total_segundos: int = 0


# =============================================================================
# OBTENER CONEXIÓN DE SERVIDOR
# =============================================================================

def get_server_connection(server_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración de conexión usando EDARSAHUB + decrypt_secret.
    Esta es la forma HOMOLOGADA de obtener conexiones.
    """
    query = f"""
    SELECT 
        id,
        nombre,
        host,
        port,
        database_name,
        username,
        password_encrypted,
        system_type,
        activo
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
            logger.error(f"No se encontró servidor {server_id}")
            return None
        
        row = result[0]
        
        # Descifrar password usando SECRET_KEY
        pwd_enc = row.get('password_encrypted', '')
        try:
            password = decrypt_secret(pwd_enc)
        except Exception as e:
            logger.warning(f"Error descifrando password: {e}, usando valor directo")
            password = pwd_enc
        
        # Parsear host (puede incluir puerto e instancia)
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


# =============================================================================
# QUERIES POR SISTEMA
# =============================================================================

QUERY_SOFTRESTAURANT_ABRIL = """
SELECT 
    CAST(fecha AS DATE) as fecha,
    SUM(total) as ventas_total,
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

QUERY_MPRO_ABRIL = """
SELECT 
    CAST(ve.Vn_Fecha AS DATE) as fecha,
    SUM(ve.Vn_Precio_Neto_Importe) as Vn_Precio_Neto_Importe,
    COUNT(DISTINCT ve.Vn_Folio) as num_folios,
    SUM(ISNULL(c.Co_Personas, 1)) as total_personas
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE CAST(ve.Vn_Fecha AS DATE) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ISNULL(ve.Es_Cve_Estado, '') IN ('AC', 'FA')
GROUP BY CAST(ve.Vn_Fecha AS DATE)
ORDER BY fecha
"""


# =============================================================================
# EJECUCIÓN DE CARGA POR UNIDAD
# =============================================================================

def cargar_unidad_softrestaurant(
    unidad: Dict,
    run_id: str,
    fecha_inicio: date,
    fecha_fin: date
) -> ReporteUnidad:
    """Carga datos de una unidad SoftRestaurant"""
    
    reporte = ReporteUnidad(
        unidad_negocio_id=unidad['unidad_negocio_id'],
        server_id=unidad['server_id'],
        sistema_origen='SOFTRESTAURANT',
        rango_procesado=f"{fecha_inicio.isoformat()} a {fecha_fin.isoformat()}"
    )
    
    start_time = time.time()
    
    # Obtener conexión
    server = get_server_connection(unidad['server_id'])
    if not server:
        reporte.errores = 1
        reporte.errores_detalle.append("No se pudo obtener configuración del servidor")
        return reporte
    
    # Construir query
    query = QUERY_SOFTRESTAURANT_ABRIL.format(
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat()
    )
    reporte.query_ejecutada = query[:200] + "..."
    
    # Ejecutar query en origen
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
        reporte.errores_detalle.append(f"Error ejecutando query: {str(e)[:200]}")
        return reporte
    
    if not rows:
        reporte.errores_detalle.append("Query retornó 0 registros")
        return reporte
    
    # Procesar registros
    reporte.registros_origen = len(rows)
    
    for row in rows:
        try:
            fecha = row.get('fecha')
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha[:10], '%Y-%m-%d').date()
            
            ventas_total = safe_decimal(row.get('ventas_total', 0))
            propinas = safe_decimal(row.get('propinas', 0))
            tickets = safe_int(row.get('num_cheques', 0))
            pax = safe_int(row.get('num_personas', 0))
            
            # Acumular totales de origen
            reporte.ventas_origen += ventas_total
            reporte.cheques_origen += tickets
            reporte.pax_origen += pax
            
            # Calcular métricas
            ticket_promedio = ventas_total / tickets if tickets > 0 else Decimal("0")
            pax_promedio = ventas_total / pax if pax > 0 else Decimal("0")
            
            # Hash para idempotencia
            hash_origen = calcular_hash_origen(
                unidad['server_id'],
                unidad['sucursal_id'],
                fecha,
                ventas_total,
                tickets,
                pax
            )
            
            if not reporte.hash_origen_muestra:
                reporte.hash_origen_muestra = hash_origen
            
            # Crear KPI
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
            
            # Upsert
            result = upsert_kpi_diario(kpi)
            
            if result['action'] == 'INSERT':
                reporte.registros_insertados += 1
            elif result['action'] == 'UPDATE':
                reporte.registros_actualizados += 1
            else:
                reporte.registros_omitidos += 1
            
            # Actualizar fechas
            fecha_str = fecha.isoformat()
            if not reporte.fecha_min or fecha_str < reporte.fecha_min:
                reporte.fecha_min = fecha_str
            if not reporte.fecha_max or fecha_str > reporte.fecha_max:
                reporte.fecha_max = fecha_str
                
        except Exception as e:
            reporte.errores += 1
            reporte.errores_detalle.append(f"Error en fila: {str(e)[:100]}")
    
    # Registrar en SyncLog
    log = SyncLogV2(
        run_id=run_id,
        run_type=SyncRunType.HISTORICAL,
        unidad_negocio_id=unidad['unidad_negocio_id'],
        server_id=unidad['server_id'],
        sucursal_id=unidad['sucursal_id'],
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        status=SyncStatus.SUCCESS if reporte.errores == 0 else SyncStatus.PARTIAL,
        records_processed=reporte.registros_origen,
        records_inserted=reporte.registros_insertados,
        records_updated=reporte.registros_actualizados,
        records_skipped=reporte.registros_omitidos,
        records_errored=reporte.errores,
        source_connection_status=ConnectionStatus.ONLINE,
        duration_seconds=int(time.time() - start_time)
    )
    reporte.sync_log_id = insert_sync_log(log)
    reporte.duracion_segundos = int(time.time() - start_time)
    
    return reporte


def cargar_unidad_mpro(
    unidad: Dict,
    run_id: str,
    fecha_inicio: date,
    fecha_fin: date
) -> ReporteUnidad:
    """Carga datos de una unidad MPRO"""
    
    reporte = ReporteUnidad(
        unidad_negocio_id=unidad['unidad_negocio_id'],
        server_id=unidad['server_id'],
        sistema_origen='MPRO',
        rango_procesado=f"{fecha_inicio.isoformat()} a {fecha_fin.isoformat()}"
    )
    
    start_time = time.time()
    
    # Obtener conexión
    server = get_server_connection(unidad['server_id'])
    if not server:
        reporte.errores = 1
        reporte.errores_detalle.append("No se pudo obtener configuración del servidor")
        return reporte
    
    # Construir query con sucursal
    query = QUERY_MPRO_ABRIL.format(
        fecha_inicio=fecha_inicio.isoformat(),
        fecha_fin=fecha_fin.isoformat(),
        sucursal_id=unidad['sucursal_id']
    )
    reporte.query_ejecutada = query[:200] + "..."
    
    # Ejecutar query en origen
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
        reporte.errores_detalle.append(f"Error ejecutando query: {str(e)[:200]}")
        return reporte
    
    if not rows:
        reporte.errores_detalle.append("Query retornó 0 registros")
        return reporte
    
    # Procesar registros
    reporte.registros_origen = len(rows)
    
    for row in rows:
        try:
            fecha = row.get('fecha')
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha[:10], '%Y-%m-%d').date()
            
            ventas_total = safe_decimal(row.get('Vn_Precio_Neto_Importe', 0))
            propinas = Decimal("0")
            tickets = safe_int(row.get('num_folios', 0))
            pax = safe_int(row.get('total_personas', 0))
            
            # Acumular totales de origen
            reporte.ventas_origen += ventas_total
            reporte.cheques_origen += tickets
            reporte.pax_origen += pax
            
            # Calcular métricas
            ticket_promedio = ventas_total / tickets if tickets > 0 else Decimal("0")
            pax_promedio = ventas_total / pax if pax > 0 else Decimal("0")
            
            # Hash para idempotencia
            hash_origen = calcular_hash_origen(
                unidad['server_id'],
                unidad['sucursal_id'],
                fecha,
                ventas_total,
                tickets,
                pax
            )
            
            if not reporte.hash_origen_muestra:
                reporte.hash_origen_muestra = hash_origen
            
            # Crear KPI
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
            
            # Upsert
            result = upsert_kpi_diario(kpi)
            
            if result['action'] == 'INSERT':
                reporte.registros_insertados += 1
            elif result['action'] == 'UPDATE':
                reporte.registros_actualizados += 1
            else:
                reporte.registros_omitidos += 1
            
            # Actualizar fechas
            fecha_str = fecha.isoformat()
            if not reporte.fecha_min or fecha_str < reporte.fecha_min:
                reporte.fecha_min = fecha_str
            if not reporte.fecha_max or fecha_str > reporte.fecha_max:
                reporte.fecha_max = fecha_str
                
        except Exception as e:
            reporte.errores += 1
            reporte.errores_detalle.append(f"Error en fila: {str(e)[:100]}")
    
    # Registrar en SyncLog
    log = SyncLogV2(
        run_id=run_id,
        run_type=SyncRunType.HISTORICAL,
        unidad_negocio_id=unidad['unidad_negocio_id'],
        server_id=unidad['server_id'],
        sucursal_id=unidad['sucursal_id'],
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        status=SyncStatus.SUCCESS if reporte.errores == 0 else SyncStatus.PARTIAL,
        records_processed=reporte.registros_origen,
        records_inserted=reporte.registros_insertados,
        records_updated=reporte.registros_actualizados,
        records_skipped=reporte.registros_omitidos,
        records_errored=reporte.errores,
        source_connection_status=ConnectionStatus.ONLINE,
        duration_seconds=int(time.time() - start_time)
    )
    reporte.sync_log_id = insert_sync_log(log)
    reporte.duracion_segundos = int(time.time() - start_time)
    
    return reporte


# =============================================================================
# VALIDACIÓN ESPECIAL 30 DE ABRIL
# =============================================================================

def validar_dia_30_abril(reporte: ReporteUnidad) -> Dict:
    """Valida los datos del 30 de abril contra los valores esperados"""
    
    unidad_id = reporte.unidad_negocio_id
    esperado = VALIDACION_30_ABRIL.get(unidad_id, {})
    
    if not esperado:
        return {'validado': False, 'mensaje': 'No hay datos de validación para esta unidad'}
    
    # Query para obtener solo el día 30
    query = f"""
    SELECT 
        ventas_total,
        tickets_total,
        pax_total
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = '{unidad_id}'
      AND fecha_operacion = '2026-04-30'
      AND activo = 1
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
            return {'validado': False, 'mensaje': 'No hay registro para 2026-04-30'}
        
        row = result[0]
        ventas_real = float(row.get('ventas_total', 0))
        cheques_real = int(row.get('tickets_total', 0))
        pax_real = int(row.get('pax_total', 0))
        
        ventas_esperado = esperado['ventas']
        cheques_esperado = esperado['cheques']
        pax_esperado = esperado['pax']
        
        # Calcular diferencias (tolerancia de 1% para ventas)
        diff_ventas = abs(ventas_real - ventas_esperado)
        diff_cheques = abs(cheques_real - cheques_esperado)
        diff_pax = abs(pax_real - pax_esperado)
        
        tolerancia_ventas = ventas_esperado * 0.01  # 1%
        
        validado = (
            diff_ventas <= tolerancia_ventas and
            diff_cheques == 0 and
            diff_pax == 0
        )
        
        return {
            'validado': validado,
            'esperado': esperado,
            'real': {
                'ventas': ventas_real,
                'cheques': cheques_real,
                'pax': pax_real
            },
            'diferencia': {
                'ventas': diff_ventas,
                'cheques': diff_cheques,
                'pax': diff_pax
            }
        }
        
    except Exception as e:
        return {'validado': False, 'mensaje': f'Error en validación: {str(e)[:200]}'}


# =============================================================================
# VERIFICACIÓN DE EDARSAHUB V2
# =============================================================================

def verificar_datos_edarsahub_v2(unidad_id: str) -> Dict:
    """Verifica los datos cargados en EDARSAHUB v2 para una unidad"""
    
    query = f"""
    SELECT 
        COUNT(*) as registros,
        SUM(ventas_total) as ventas_total,
        SUM(tickets_total) as tickets_total,
        SUM(pax_total) as pax_total,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = '{unidad_id}'
      AND fecha_operacion BETWEEN '2026-04-01' AND '2026-04-30'
      AND activo = 1
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
        
        if result:
            return result[0]
        return {}
        
    except Exception as e:
        logger.error(f"Error verificando EDARSAHUB: {e}")
        return {}


# =============================================================================
# EJECUCIÓN DE CARGA COMPLETA
# =============================================================================

def ejecutar_carga_piloto_abril_2026(corrida_numero: int = 1) -> ReporteCorrida:
    """
    Ejecuta la carga piloto de abril 2026 para las 5 unidades.
    
    Args:
        corrida_numero: 1 para primera corrida, 2 para idempotencia
    
    Returns:
        ReporteCorrida con todos los detalles
    """
    
    run_id = f"PILOTO-ABR26-{corrida_numero}-{str(uuid.uuid4())[:8]}"
    
    reporte = ReporteCorrida(
        corrida_numero=corrida_numero,
        timestamp=datetime.utcnow().isoformat()
    )
    
    start_time = time.time()
    
    print(f"\n{'='*70}")
    print(f"CARGA PILOTO ABRIL 2026 - CORRIDA {corrida_numero}")
    print(f"Run ID: {run_id}")
    print(f"Rango: {FECHA_INICIO_PILOTO} a {FECHA_FIN_PILOTO}")
    print(f"{'='*70}\n")
    
    for unidad in UNIDADES_AUTORIZADAS:
        print(f"\n[{unidad['unidad_negocio_id']}] Procesando {unidad['unidad_negocio_nombre']}...")
        
        # Cargar según sistema
        if unidad['sistema_origen'] == SistemaOrigen.SOFTRESTAURANT:
            reporte_unidad = cargar_unidad_softrestaurant(
                unidad, run_id, FECHA_INICIO_PILOTO, FECHA_FIN_PILOTO
            )
        else:
            reporte_unidad = cargar_unidad_mpro(
                unidad, run_id, FECHA_INICIO_PILOTO, FECHA_FIN_PILOTO
            )
        
        # Verificar datos en EDARSAHUB
        datos_edarsahub = verificar_datos_edarsahub_v2(unidad['unidad_negocio_id'])
        if datos_edarsahub:
            reporte_unidad.ventas_edarsahub = safe_decimal(datos_edarsahub.get('ventas_total', 0))
            reporte_unidad.cheques_edarsahub = safe_int(datos_edarsahub.get('tickets_total', 0))
            reporte_unidad.pax_edarsahub = safe_int(datos_edarsahub.get('pax_total', 0))
            
            # Calcular diferencias
            reporte_unidad.diferencia_ventas = reporte_unidad.ventas_origen - reporte_unidad.ventas_edarsahub
            reporte_unidad.diferencia_cheques = reporte_unidad.cheques_origen - reporte_unidad.cheques_edarsahub
            reporte_unidad.diferencia_pax = reporte_unidad.pax_origen - reporte_unidad.pax_edarsahub
        
        # Validar día 30
        reporte_unidad.validacion_30_abril = validar_dia_30_abril(reporte_unidad)
        
        # Agregar al reporte
        reporte.unidades.append(reporte_unidad)
        
        # Acumular totales
        reporte.total_insertados += reporte_unidad.registros_insertados
        reporte.total_actualizados += reporte_unidad.registros_actualizados
        reporte.total_omitidos += reporte_unidad.registros_omitidos
        reporte.total_errores += reporte_unidad.errores
        
        # Imprimir resumen
        print(f"  - Registros origen: {reporte_unidad.registros_origen}")
        print(f"  - Insertados: {reporte_unidad.registros_insertados}")
        print(f"  - Actualizados: {reporte_unidad.registros_actualizados}")
        print(f"  - Omitidos: {reporte_unidad.registros_omitidos}")
        print(f"  - Errores: {reporte_unidad.errores}")
        print(f"  - Ventas origen: ${reporte_unidad.ventas_origen:,.2f}")
        print(f"  - Ventas EDARSAHUB: ${reporte_unidad.ventas_edarsahub:,.2f}")
        
        val_30 = reporte_unidad.validacion_30_abril
        if val_30.get('validado'):
            print(f"  - Validación 30-Abr: ✅ OK")
        else:
            print(f"  - Validación 30-Abr: ⚠️ {val_30.get('mensaje', 'Ver detalles')}")
    
    reporte.duracion_total_segundos = int(time.time() - start_time)
    
    print(f"\n{'='*70}")
    print(f"RESUMEN CORRIDA {corrida_numero}")
    print(f"{'='*70}")
    print(f"Total insertados: {reporte.total_insertados}")
    print(f"Total actualizados: {reporte.total_actualizados}")
    print(f"Total omitidos: {reporte.total_omitidos}")
    print(f"Total errores: {reporte.total_errores}")
    print(f"Duración: {reporte.duracion_total_segundos} segundos")
    print(f"{'='*70}\n")
    
    return reporte


def verificar_duplicados() -> Dict:
    """Verifica que no haya duplicados en la tabla v2"""
    
    query = """
    SELECT 
        unidad_negocio_id,
        sucursal_id,
        fecha_operacion,
        COUNT(*) as count
    FROM Comercial_KPIs_Diarios_v2
    WHERE fecha_operacion BETWEEN '2026-04-01' AND '2026-04-30'
    GROUP BY unidad_negocio_id, sucursal_id, fecha_operacion
    HAVING COUNT(*) > 1
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
        
        return {
            'tiene_duplicados': len(result) > 0,
            'duplicados': result
        }
        
    except Exception as e:
        return {'error': str(e)}


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================

def ejecutar_subfase_2a_completa():
    """
    Ejecuta la Subfase 2A completa:
    1. Corrida 1: Carga inicial
    2. Corrida 2: Prueba de idempotencia
    3. Verificación de duplicados
    4. Genera reporte final
    """
    
    print("\n" + "="*80)
    print("SUBFASE 2A - CARGA HISTÓRICA PILOTO ABRIL 2026")
    print("="*80)
    print("Fecha: " + datetime.utcnow().isoformat())
    print("Rango autorizado: 2026-04-01 a 2026-04-30")
    print("Unidades: CIENFUEGOS, LA ESTELAR, 130° MÉRIDA, 130° QRO, ORIGEN")
    print("="*80 + "\n")
    
    # Corrida 1
    print("\n>>> INICIANDO CORRIDA 1 (Carga inicial)...")
    corrida1 = ejecutar_carga_piloto_abril_2026(corrida_numero=1)
    
    # Corrida 2
    print("\n>>> INICIANDO CORRIDA 2 (Prueba de idempotencia)...")
    corrida2 = ejecutar_carga_piloto_abril_2026(corrida_numero=2)
    
    # Verificar duplicados
    print("\n>>> VERIFICANDO DUPLICADOS...")
    duplicados = verificar_duplicados()
    
    if duplicados.get('tiene_duplicados'):
        print("⚠️ SE ENCONTRARON DUPLICADOS:")
        for dup in duplicados['duplicados']:
            print(f"  - {dup}")
    else:
        print("✅ 0 duplicados encontrados")
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN FINAL SUBFASE 2A")
    print("="*80)
    print(f"\nCORRIDA 1:")
    print(f"  - Insertados: {corrida1.total_insertados}")
    print(f"  - Actualizados: {corrida1.total_actualizados}")
    print(f"  - Omitidos: {corrida1.total_omitidos}")
    print(f"  - Errores: {corrida1.total_errores}")
    
    print(f"\nCORRIDA 2 (Idempotencia):")
    print(f"  - Insertados: {corrida2.total_insertados} (debería ser 0)")
    print(f"  - Actualizados: {corrida2.total_actualizados} (debería ser 0)")
    print(f"  - Omitidos: {corrida2.total_omitidos} (todos deberían estar aquí)")
    print(f"  - Errores: {corrida2.total_errores}")
    
    # Verificar idempotencia
    idempotencia_ok = (
        corrida2.total_insertados == 0 and
        corrida2.total_actualizados == 0 and
        corrida2.total_omitidos == corrida1.total_insertados
    )
    
    print(f"\n{'='*80}")
    if idempotencia_ok:
        print("✅ IDEMPOTENCIA VERIFICADA: Corrida 2 omitió todos los registros")
    else:
        print("⚠️ IDEMPOTENCIA NO VERIFICADA: Revisar resultados")
    
    print("="*80 + "\n")
    
    return {
        'corrida1': corrida1,
        'corrida2': corrida2,
        'duplicados': duplicados,
        'idempotencia_ok': idempotencia_ok
    }


# =============================================================================
# EJECUCIÓN DIRECTA
# =============================================================================

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    print("SCRIPT DE CARGA PILOTO - SUBFASE 2A")
    print("="*80)
    print("\nEste script ejecuta la carga piloto de abril 2026.")
    print("Para ejecutar, usa:")
    print("  cd /app/backend && python -m modules.comercial_v2.carga_historica_abril_2026")
    print("\nO desde Python:")
    print("  from modules.comercial_v2.carga_historica_abril_2026 import ejecutar_subfase_2a_completa")
    print("  resultado = ejecutar_subfase_2a_completa()")
    print("="*80 + "\n")
