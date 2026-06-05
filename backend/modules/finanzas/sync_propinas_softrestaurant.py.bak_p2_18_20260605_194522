"""
SUBFASE 3.2 - Sincronización de Propinas TPV desde SoftRestaurant hacia EDARSAHUB

Este módulo extrae propinas pagadas con tarjeta (propinatarjeta) de SoftRestaurant
y las sincroniza hacia EDARSAHUB.propinas_tpv_control.

Unidades soportadas:
- 130° MERIDA
- CIENFUEGOS
- LA ESTELAR

Fuente:
- tabla `cheques` campo `propinatarjeta`

Destino:
- EDARSAHUB.propinas_tpv_control
- EDARSAHUB.Finanzas_PropinasTPV_SyncLog

NOTA: NO MODIFICA repository_softrestaurant.py ni CxP (BLINDADOS)

Autor: E1 Agent
Fecha: 1 Mayo 2026
Fase: Finanzas Fase 3 - Propinas TPV
"""

import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
from pathlib import Path

import pymssql

from core.system_type_utils import build_system_type_sql_filter
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


# ============================================================================
# CARGAR VARIABLES DE ENTORNO
# ============================================================================

def _load_env():
    """Carga variables de entorno desde /app/backend/.env"""
    env_file = Path('/app/backend/.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value

_load_env()

# Configuración de logging
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN EDARSAHUB
# ============================================================================

EDARSAHUB_CONFIG = {
    'server': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'user': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}

# Unidades SoftRestaurant autorizadas para Propinas TPV
UNIDADES_SR_AUTORIZADAS = ['130° MERIDA', 'CIENFUEGOS', 'LA ESTELAR']


# ============================================================================
# FUNCIONES DE CONEXIÓN
# ============================================================================

def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB"""
    return pymssql.connect(
        server=EDARSAHUB_CONFIG['server'],
        port=EDARSAHUB_CONFIG['port'],
        database=EDARSAHUB_CONFIG['database'],
        user=EDARSAHUB_CONFIG['user'],
        password=EDARSAHUB_CONFIG['password'],
        login_timeout=30,
        autocommit=False
    )


def get_unidad_connection_info(unidad_nombre: str) -> Optional[Dict]:
    """
    Obtiene información de conexión para una unidad SoftRestaurant desde EDARSAHUB.
    
    Usa la misma lógica segura que sync_cortes_softrestaurant.py (Fase 2).
    """
    try:
        from core.secret_manager import decrypt_secret
    except ImportError:
        decrypt_secret = lambda x: x
    
    try:
        from core.db import parse_sql_server_host
    except ImportError:
        def parse_sql_server_host(host, default_port):
            return (host, default_port, None)
    
    conn = get_edarsahub_connection()
    cursor = conn.cursor(as_dict=True)
    
    try:
        # CORRECCIÓN 2026-06-05: El system_type en EDARSAHUB es 'SOFTRESTAURANT_PRO'
        # Se agregan todas las variantes conocidas para evitar fallos de lookup
        cursor.execute("""
            SELECT 
                u.id as unidad_negocio_id,
                u.nombre as unidad_nombre,
                u.codigo as unidad_codigo,
                u.server_id,
                s.nombre as servidor_nombre,
                s.host,
                s.port,
                s.database_name,
                s.username,
                s.password_encrypted,
                s.system_type
            FROM Unidades_Negocio u
            LEFT JOIN Servidores_Conexiones s 
                ON CAST(u.server_id AS NVARCHAR(100)) = CAST(s.id AS NVARCHAR(100))
            WHERE u.nombre = %s
              AND u.activo = 1
              AND {sr_filter}
        """.format(sr_filter=build_system_type_sql_filter('s.system_type', 'SOFTRESTAURANT')), (unidad_nombre,))
        
        unidad = cursor.fetchone()
        
        if not unidad:
            logger.warning(f"[SYNC_PROPINAS_SR] Unidad no encontrada: {unidad_nombre}")
            return None
        
        host_raw = unidad['host'] or ''
        default_port = unidad['port'] or 1433
        
        hostname, parsed_port, instance = parse_sql_server_host(host_raw, default_port)
        
        logger.info(f"[SYNC_PROPINAS_SR] Conexión parseada para {unidad_nombre}: "
                    f"host={hostname}, port={parsed_port}, instance={instance}")
        
        password_enc = unidad['password_encrypted'] or ''
        try:
            password = decrypt_secret(password_enc)
        except Exception:
            password = password_enc
        
        return {
            'unidad_negocio_id': str(unidad['unidad_negocio_id']),
            'unidad_nombre': unidad['unidad_nombre'],
            'unidad_codigo': unidad['unidad_codigo'],
            'server_id': str(unidad['server_id']),
            'servidor_nombre': unidad['servidor_nombre'],
            'host': hostname,
            'host_raw': host_raw,
            'port': parsed_port,
            'instance': instance,
            'database': unidad['database_name'],
            'user': unidad['username'],
            'password': password,
            'system_type': unidad['system_type']
        }
        
    finally:
        conn.close()


def get_softrestaurant_connection(conn_info: Dict):
    """
    Obtiene conexión a SoftRestaurant usando info de EDARSAHUB.
    Misma lógica que sync_cortes_softrestaurant.py (Fase 2).
    """
    import pytds
    
    host = conn_info['host']
    port = conn_info['port']
    instance = conn_info.get('instance')
    database = conn_info['database']
    user = conn_info['user']
    password = conn_info['password']
    
    try:
        conn = pytds.connect(
            server=host,
            port=port,
            database=database,
            user=user,
            password=password,
            timeout=30,
            login_timeout=30
        )
        logger.info(f"[SYNC_PROPINAS_SR] Conexión pytds exitosa a {host}:{port}/{database}")
        conn._driver_name = 'pytds'
        return conn
    except Exception as pytds_error:
        logger.warning(f"[SYNC_PROPINAS_SR] pytds falló: {pytds_error}, intentando pymssql...")
        
        server_string = f"{host}\\{instance}" if instance else host
        conn = pymssql.connect(
            server=server_string,
            port=port,
            database=database,
            user=user,
            password=password,
            login_timeout=15
        )
        conn._driver_name = 'pymssql'
        return conn


def execute_sr_query(conn, query: str, params: tuple = None) -> List[Dict]:
    """Ejecuta query en conexión SoftRestaurant"""
    driver = getattr(conn, '_driver_name', 'unknown')
    
    if driver == 'pymssql':
        cursor = conn.cursor(as_dict=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return list(cursor.fetchall())
    else:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        return []


# ============================================================================
# FUNCIONES DE HASH E IDEMPOTENCIA
# ============================================================================

def calcular_hash_propina(registro: Dict) -> str:
    """
    Calcula SHA256 para idempotencia de propinas TPV.
    
    Componentes:
    - SistemaOrigen
    - ServerID
    - IdOrigen (idcheque)
    - FolioOrigen (folio)
    - FechaOperacion
    - ImportePropinaTPV
    """
    componentes = [
        str(registro.get('SistemaOrigen', 'SoftRestaurant')),
        str(registro.get('ServerID', '')),
        str(registro.get('IdOrigen', '')),
        str(registro.get('FolioOrigen', '')),
        str(registro.get('FechaOperacion', '')),
        str(float(registro.get('ImportePropinaTPV', 0) or 0)),
    ]
    cadena = '|'.join(componentes)
    return hashlib.sha256(cadena.encode()).hexdigest()


# ============================================================================
# EXTRACCIÓN DESDE SOFTRESTAURANT
# ============================================================================

def extraer_propinas_tpv_softrestaurant(
    conn_info: Dict,
    fecha_desde: datetime,
    fecha_hasta: datetime
) -> List[Dict]:
    """
    Extrae propinas pagadas con tarjeta de SoftRestaurant.
    
    Fuente: cheques.propinatarjeta
    
    Args:
        conn_info: Información de conexión de EDARSAHUB
        fecha_desde: Fecha inicio del rango
        fecha_hasta: Fecha fin del rango
        
    Returns:
        Lista de registros transformados listos para EDARSAHUB
    """
    logger.info(f"[SYNC_PROPINAS_SR] Extrayendo propinas TPV de {conn_info['unidad_nombre']} "
                f"desde {fecha_desde.date()} hasta {fecha_hasta.date()}")
    
    try:
        sr_conn = get_softrestaurant_connection(conn_info)
    except Exception as e:
        logger.error(f"[SYNC_PROPINAS_SR] Error conectando a {conn_info['unidad_nombre']}: {e}")
        raise
    
    try:
        # Query para extraer propinas TPV (propinatarjeta > 0)
        # NOTA: Nombres de columnas correctos de SoftRestaurant:
        # - folio (no idcheque)
        # - idturno (no turession)
        # - estacion (no idestacion)
        # - nopersonas (no numpersonas)
        query = """
            SELECT 
                c.folio,
                c.numcheque,
                c.seriefolio,
                c.fecha,
                c.total,
                c.propina,
                c.propinatarjeta,
                c.tarjeta,
                c.efectivo,
                c.descuento,
                c.numerotarjeta,
                c.nopersonas,
                c.idmesero,
                c.estacion,
                c.idturno,
                c.cierre
            FROM cheques c
            WHERE c.fecha >= %s
              AND c.fecha < %s
              AND c.propinatarjeta > 0
              AND c.cancelado = 0
            ORDER BY c.fecha, c.folio
        """
        
        rows = execute_sr_query(
            sr_conn, 
            query, 
            (fecha_desde, fecha_hasta)  # pytds maneja datetime directamente
        )
        
        logger.info(f"[SYNC_PROPINAS_SR] {conn_info['unidad_nombre']}: {len(rows)} cheques con propina TPV")
        
        # Transformar a formato EDARSAHUB
        registros = []
        for row in rows:
            # Construir registro para propinas_tpv_control
            # Usar folio como IdOrigen (es el identificador único del cheque)
            registro = {
                # Identificación de unidad
                'UnidadNegocioID': conn_info['unidad_negocio_id'],
                'UnidadNegocioNombre': conn_info['unidad_nombre'],
                'ServerID': conn_info['server_id'],
                'server_name': conn_info['servidor_nombre'],
                
                # Identificación de origen
                'SistemaOrigen': 'SoftRestaurant',
                'BaseDatosOrigen': conn_info['database'],
                'TablaOrigen': 'cheques',
                'IdOrigen': str(row.get('folio', '')),  # folio es el ID único
                'FolioOrigen': str(row.get('numcheque', row.get('folio', ''))),  # numcheque como folio visible
                
                # Fechas - IMPORTANTE: folio_corte debe ser único por cheque
                # Usamos el folio del cheque como folio_corte (no el turno)
                'FechaOperacion': row.get('fecha'),
                'fecha_corte': row.get('fecha'),  # Usar fecha del cheque como fecha_corte
                'folio_corte': str(row.get('folio', '')),  # folio del cheque como folio_corte (único)
                
                # Montos
                'ImportePropinaTPV': Decimal(str(row.get('propinatarjeta', 0) or 0)),
                'propinas_totales_corte': Decimal(str(row.get('propina', 0) or 0)),
                'propinas_tpv': Decimal(str(row.get('propinatarjeta', 0) or 0)),
                'propinas_efectivo': Decimal(str(row.get('propina', 0) or 0)) - Decimal(str(row.get('propinatarjeta', 0) or 0)),
                'ventas_tarjeta': Decimal(str(row.get('tarjeta', 0) or 0)),
                'ventas_efectivo': Decimal(str(row.get('efectivo', 0) or 0)),
                'ventas_totales': Decimal(str(row.get('total', 0) or 0)),
                
                # Forma de pago (para uniformidad)
                'FormaPagoID': 'TARJETA',
                'FormaPagoNombre': 'Tarjeta',
                'EsTarjeta': 1,
                
                # Otros campos
                'sucursal_id': conn_info.get('unidad_codigo', conn_info['server_id']),
                'sucursal_nombre': conn_info['unidad_nombre'],
                'system_type': 'SoftRestaurant',
                'total_cheques': 1,
                'estacion_id': str(row.get('estacion', '')),
                'turno_id_origen': str(row.get('idturno', '')),
                
                # Flags
                'EsDemo': 0,
                'Activo': 1,
                
                # Datos adicionales
                'empresa_id': None,
                'corte_id_origen': str(row.get('idturno', '')),
                'tipo_dato': 'EXACTO',
                'metodo_calculo': 'cheques.propinatarjeta',
                'confianza': 1.0,
                'query_origen': 'cheques WHERE propinatarjeta > 0',
            }
            
            # Calcular HashOrigen
            registro['HashOrigen'] = calcular_hash_propina(registro)
            
            registros.append(registro)
        
        return registros
        
    finally:
        sr_conn.close()


# ============================================================================
# CARGA HACIA EDARSAHUB
# ============================================================================

def cargar_propinas_edarsahub(
    registros: List[Dict],
    conn_info: Dict
) -> Dict[str, Any]:
    """
    Carga propinas TPV en EDARSAHUB.propinas_tpv_control
    
    Usa MERGE/UPSERT basado en HashOrigen para idempotencia.
    """
    if not registros:
        return {
            'insertados': 0,
            'actualizados': 0,
            'omitidos': 0,
            'errores': 0,
            'total_propinas_tpv': Decimal('0')
        }
    
    conn = get_edarsahub_connection()
    cursor = conn.cursor()
    
    stats = {
        'insertados': 0,
        'actualizados': 0,
        'omitidos': 0,
        'errores': 0,
        'total_propinas_tpv': Decimal('0')
    }
    
    try:
        for registro in registros:
            try:
                # Verificar si existe por HashOrigen
                cursor.execute("""
                    SELECT id FROM propinas_tpv_control 
                    WHERE HashOrigen = %s
                """, (registro['HashOrigen'],))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Ya existe, omitir (idempotencia)
                    stats['omitidos'] += 1
                else:
                    # Insertar nuevo
                    cursor.execute("""
                        INSERT INTO propinas_tpv_control (
                            server_id, sucursal_id, folio_corte, fecha_corte,
                            server_name, system_type, sucursal_nombre, empresa_id,
                            estacion_id, propinas_totales_corte, propinas_efectivo,
                            propinas_tpv, ventas_tarjeta, ventas_totales, ventas_efectivo,
                            total_cheques, corte_id_origen, turno_id_origen,
                            tipo_dato, metodo_calculo, confianza, query_origen,
                            fecha_sincronizacion,
                            UnidadNegocioID, UnidadNegocioNombre, SistemaOrigen,
                            BaseDatosOrigen, TablaOrigen, IdOrigen, FolioOrigen,
                            HashOrigen, EsDemo, Activo, FormaPagoID, FormaPagoNombre, EsTarjeta
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, GETDATE(),
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        registro['ServerID'],
                        registro['sucursal_id'],
                        registro['folio_corte'],
                        registro['fecha_corte'],
                        registro['server_name'],
                        registro['system_type'],
                        registro['sucursal_nombre'],
                        registro['empresa_id'],
                        registro['estacion_id'],
                        float(registro['propinas_totales_corte']),
                        float(registro['propinas_efectivo']),
                        float(registro['propinas_tpv']),
                        float(registro['ventas_tarjeta']),
                        float(registro['ventas_totales']),
                        float(registro['ventas_efectivo']),
                        registro['total_cheques'],
                        registro['corte_id_origen'],
                        registro['turno_id_origen'],
                        registro['tipo_dato'],
                        registro['metodo_calculo'],
                        registro['confianza'],
                        registro['query_origen'],
                        registro['UnidadNegocioID'],
                        registro['UnidadNegocioNombre'],
                        registro['SistemaOrigen'],
                        registro['BaseDatosOrigen'],
                        registro['TablaOrigen'],
                        registro['IdOrigen'],
                        registro['FolioOrigen'],
                        registro['HashOrigen'],
                        registro['EsDemo'],
                        registro['Activo'],
                        registro['FormaPagoID'],
                        registro['FormaPagoNombre'],
                        registro['EsTarjeta'],
                    ))
                    
                    stats['insertados'] += 1
                    stats['total_propinas_tpv'] += registro['propinas_tpv']
                    
            except Exception as e:
                logger.error(f"[SYNC_PROPINAS_SR] Error insertando registro: {e}")
                stats['errores'] += 1
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"[SYNC_PROPINAS_SR] Error en carga: {e}")
        raise
    finally:
        conn.close()
    
    return stats


def registrar_synclog_propinas(
    conn_info: Dict,
    fecha_desde: datetime,
    fecha_hasta: datetime,
    stats: Dict,
    estatus: str,
    error_mensaje: str = None,
    tipo_ejecucion: str = 'MANUAL'
) -> int:
    """Registra en Finanzas_PropinasTPV_SyncLog"""
    
    conn = get_edarsahub_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Finanzas_PropinasTPV_SyncLog (
                FechaInicio, FechaFin, UnidadNegocioID, UnidadNegocioNombre,
                ServerID, SistemaOrigen, BaseDatosOrigen,
                FechaDesde, FechaHasta,
                RegistrosLeidos, RegistrosInsertados, RegistrosActualizados,
                RegistrosOmitidos, RegistrosConError,
                TotalPropinasTPV, Estatus, ErrorMensaje, TipoEjecucion
            ) VALUES (
                GETDATE(), GETDATE(), %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            SELECT SCOPE_IDENTITY()
        """, (
            conn_info['unidad_negocio_id'],
            conn_info['unidad_nombre'],
            conn_info['server_id'],
            'SoftRestaurant',
            conn_info['database'],
            fecha_desde.date(),
            fecha_hasta.date(),
            stats.get('insertados', 0) + stats.get('omitidos', 0),
            stats.get('insertados', 0),
            stats.get('actualizados', 0),
            stats.get('omitidos', 0),
            stats.get('errores', 0),
            float(stats.get('total_propinas_tpv', 0)),
            estatus,
            error_mensaje,
            tipo_ejecucion
        ))
        
        conn.commit()
        
        # Obtener ID del log
        cursor.execute("SELECT MAX(LogID) FROM Finanzas_PropinasTPV_SyncLog")
        log_id = cursor.fetchone()[0]
        
        logger.info(f"[SYNC_PROPINAS_SR] SyncLog registrado: ID={log_id}, Estatus={estatus}")
        
        return log_id
        
    finally:
        conn.close()


# ============================================================================
# FUNCIÓN PRINCIPAL DE SINCRONIZACIÓN
# ============================================================================

def sincronizar_propinas_softrestaurant(
    unidad_nombre: str,
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    dias_atras: int = 7
) -> Dict[str, Any]:
    """
    Sincroniza propinas TPV de una unidad SoftRestaurant hacia EDARSAHUB.
    
    Args:
        unidad_nombre: Nombre de la unidad (130° MERIDA, CIENFUEGOS, LA ESTELAR)
        fecha_desde: Fecha inicio (opcional)
        fecha_hasta: Fecha fin (opcional)
        dias_atras: Días hacia atrás si no se especifica rango (default: 7)
        
    Returns:
        Dict con resultados de la sincronización
    """
    logger.info(f"[SYNC_PROPINAS_SR] === Iniciando sync de propinas TPV: {unidad_nombre} ===")
    
    inicio = datetime.now()
    
    # Validar unidad autorizada
    if unidad_nombre not in UNIDADES_SR_AUTORIZADAS:
        return {
            'unidad': unidad_nombre,
            'estatus': 'ERROR',
            'error': f'Unidad no autorizada: {unidad_nombre}. Autorizadas: {UNIDADES_SR_AUTORIZADAS}'
        }
    
    # Calcular rango de fechas
    if fecha_hasta is None:
        fecha_hasta = datetime.now()
    if fecha_desde is None:
        fecha_desde = fecha_hasta - timedelta(days=dias_atras)
    
    # Obtener info de conexión
    conn_info = get_unidad_connection_info(unidad_nombre)
    if not conn_info:
        return {
            'unidad': unidad_nombre,
            'estatus': 'ERROR',
            'error': f'No se encontró información de conexión para {unidad_nombre}'
        }
    
    resultado = {
        'unidad': unidad_nombre,
        'unidad_negocio_id': conn_info['unidad_negocio_id'],
        'server_id': conn_info['server_id'],
        'base_datos_origen': conn_info['database'],
        'fecha_desde': fecha_desde.isoformat(),
        'fecha_hasta': fecha_hasta.isoformat(),
        'stats': {},
        'estatus': 'EN_PROGRESO'
    }
    
    try:
        # 1. Extraer propinas de SoftRestaurant
        registros = extraer_propinas_tpv_softrestaurant(conn_info, fecha_desde, fecha_hasta)
        resultado['registros_origen'] = len(registros)
        
        # Calcular suma de propinas origen
        suma_origen = sum(r['propinas_tpv'] for r in registros)
        resultado['suma_propinas_origen'] = float(suma_origen)
        
        # 2. Cargar en EDARSAHUB
        stats = cargar_propinas_edarsahub(registros, conn_info)
        resultado['stats'] = {
            'leidos': len(registros),
            'insertados': stats['insertados'],
            'actualizados': stats['actualizados'],
            'omitidos': stats['omitidos'],
            'errores': stats['errores']
        }
        
        # 3. Determinar estatus
        if stats['errores'] > 0:
            resultado['estatus'] = 'PARCIAL'
        elif stats['insertados'] > 0 or stats['omitidos'] > 0:
            resultado['estatus'] = 'COMPLETADO'
        else:
            resultado['estatus'] = 'SIN_DATOS'
        
        # 4. Registrar SyncLog
        log_id = registrar_synclog_propinas(
            conn_info, fecha_desde, fecha_hasta,
            resultado['stats'], resultado['estatus']
        )
        resultado['synclog_id'] = log_id
        
        # 5. Muestra de registros (primeros 5)
        if registros:
            resultado['muestra_origen'] = [
                {
                    'IdOrigen': r['IdOrigen'],
                    'FolioOrigen': r['FolioOrigen'],
                    'FechaOperacion': str(r['FechaOperacion']),
                    'PropinasTPV': float(r['propinas_tpv']),
                    'HashOrigen': r['HashOrigen'][:16] + '...'
                }
                for r in registros[:5]
            ]
        
    except Exception as e:
        resultado['estatus'] = 'ERROR'
        resultado['error'] = str(e)
        logger.error(f"[SYNC_PROPINAS_SR] Error en sync de {unidad_nombre}: {e}")
        
        # Registrar error en SyncLog
        try:
            registrar_synclog_propinas(
                conn_info, fecha_desde, fecha_hasta,
                {'insertados': 0, 'actualizados': 0, 'omitidos': 0, 'errores': 1},
                'ERROR', str(e)
            )
        except:
            pass
    
    # Calcular duración
    resultado['duracion_segundos'] = int((datetime.now() - inicio).total_seconds())
    
    logger.info(f"[SYNC_PROPINAS_SR] {unidad_nombre}: {resultado['estatus']}, "
                f"insertados={resultado.get('stats', {}).get('insertados', 0)}, "
                f"omitidos={resultado.get('stats', {}).get('omitidos', 0)}")
    
    return resultado


def sincronizar_todas_unidades_sr(
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    dias_atras: int = 7
) -> Dict[str, Any]:
    """
    Sincroniza propinas TPV de todas las unidades SoftRestaurant.
    """
    logger.info("=" * 70)
    logger.info("SYNC PROPINAS TPV — TODAS LAS UNIDADES SOFTRESTAURANT")
    logger.info("=" * 70)
    
    resultados = {
        'unidades_procesadas': 0,
        'unidades_exitosas': 0,
        'unidades_fallidas': 0,
        'total_insertados': 0,
        'total_omitidos': 0,
        'detalle': []
    }
    
    for unidad in UNIDADES_SR_AUTORIZADAS:
        resultado = sincronizar_propinas_softrestaurant(
            unidad, fecha_desde, fecha_hasta, dias_atras
        )
        
        resultados['unidades_procesadas'] += 1
        resultados['detalle'].append(resultado)
        
        if resultado['estatus'] in ('COMPLETADO', 'PARCIAL', 'SIN_DATOS'):
            resultados['unidades_exitosas'] += 1
            resultados['total_insertados'] += resultado.get('stats', {}).get('insertados', 0)
            resultados['total_omitidos'] += resultado.get('stats', {}).get('omitidos', 0)
        else:
            resultados['unidades_fallidas'] += 1
    
    resultados['estatus_general'] = (
        'COMPLETADO' if resultados['unidades_fallidas'] == 0
        else 'PARCIAL' if resultados['unidades_exitosas'] > 0
        else 'FALLIDO'
    )
    
    return resultados


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'sincronizar_propinas_softrestaurant',
    'sincronizar_todas_unidades_sr',
    'UNIDADES_SR_AUTORIZADAS'
]
