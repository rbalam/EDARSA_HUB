"""
SUBFASE 3.3 - Sincronización de Propinas TPV desde MPRO hacia EDARSAHUB

Este módulo extrae propinas pagadas con tarjeta de MPRO (ManagementPro)
y las sincroniza hacia EDARSAHUB.propinas_tpv_control.

Unidades soportadas:
- 130° QUERETARO
- ORIGEN

Fuente:
- tabla `Comanda_Pago` campo `Cp_Propina`
- filtrado por `Forma_Pago.Fp_Tipo = '04'` (tarjetas)

Formas de pago tarjeta:
- 0004: T DE CREDITO
- 0005: T DE DEBITO
- 0006: T AMEX

Destino:
- EDARSAHUB.propinas_tpv_control
- EDARSAHUB.Finanzas_PropinasTPV_SyncLog

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

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

EDARSAHUB_CONFIG = {
    'server': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'user': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
}

# Unidades MPRO autorizadas
UNIDADES_MPRO_AUTORIZADAS = ['130° QUERETARO', 'ORIGEN']

# Formas de pago tarjeta en MPRO (Tipo '04')
FORMAS_PAGO_TARJETA = ['0004', '0005', '0006']  # Crédito, Débito, AMEX


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


def get_unidad_mpro_connection_info(unidad_nombre: str) -> Optional[Dict]:
    """
    Obtiene información de conexión para una unidad MPRO desde EDARSAHUB.
    
    MPRO usa CENTRAL2020 como base de datos compartida con filtro por empresa.
    """
    conn = get_edarsahub_connection()
    cursor = conn.cursor(as_dict=True)
    
    try:
        # Obtener unidad y servidor (sin JOIN a Empresas que no existe)
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
              AND s.system_type IN ('MPRO', 'ManagementPro')
        """, (unidad_nombre,))
        
        unidad = cursor.fetchone()
        
        if not unidad:
            logger.warning(f"[SYNC_PROPINAS_MPRO] Unidad MPRO no encontrada: {unidad_nombre}")
            return None
        
        # Mapeo de unidades MPRO a códigos de empresa en CENTRAL2020
        # Validado: Empresa.Em_Cve_Empresa
        # 0004 = 130° QUERETARO (Sucursal 0021)
        # 0006 = ORIGEN (Sucursal 0023)
        EMPRESA_MAPPING = {
            '130° QUERETARO': '0004',  # Código empresa en CENTRAL2020
            'ORIGEN': '0006',           # Código empresa en CENTRAL2020
        }
        
        empresa_codigo = EMPRESA_MAPPING.get(unidad_nombre)
        
        return {
            'unidad_negocio_id': str(unidad['unidad_negocio_id']),
            'unidad_nombre': unidad['unidad_nombre'],
            'unidad_codigo': unidad['unidad_codigo'],
            'server_id': str(unidad['server_id']),
            'servidor_nombre': unidad['servidor_nombre'],
            'empresa_id': None,
            'empresa_codigo': empresa_codigo,
            'empresa_nombre': unidad_nombre,
            'host': unidad['host'] or '54.39.104.176',
            'port': unidad['port'] or 1433,
            'database': unidad['database_name'] or 'CENTRAL2020',
            'user': unidad['username'] or 'HRLectura',
            'password': 'National09$',
            'system_type': 'MPRO'
        }
        
    finally:
        conn.close()


def get_mpro_connection(conn_info: Dict):
    """Obtiene conexión a MPRO (CENTRAL2020)"""
    return pymssql.connect(
        server=conn_info['host'],
        port=conn_info['port'],
        database=conn_info['database'],
        user=conn_info['user'],
        password=conn_info['password'],
        login_timeout=30,
        autocommit=False
    )


# ============================================================================
# FUNCIONES DE HASH
# ============================================================================

def calcular_hash_propina_mpro(registro: Dict) -> str:
    """
    Calcula SHA256 para idempotencia de propinas TPV MPRO.
    
    Componentes:
    - SistemaOrigen
    - ServerID
    - IdOrigen (Cp_ID o combinación única)
    - FolioOrigen (Co_Folio)
    - FormaPagoID
    - FechaOperacion
    - ImportePropinaTPV
    """
    componentes = [
        str(registro.get('SistemaOrigen', 'MPRO')),
        str(registro.get('ServerID', '')),
        str(registro.get('IdOrigen', '')),
        str(registro.get('FolioOrigen', '')),
        str(registro.get('FormaPagoID', '')),
        str(registro.get('FechaOperacion', '')),
        str(float(registro.get('ImportePropinaTPV', 0) or 0)),
    ]
    cadena = '|'.join(componentes)
    return hashlib.sha256(cadena.encode()).hexdigest()


# ============================================================================
# EXTRACCIÓN DESDE MPRO
# ============================================================================

def extraer_propinas_tpv_mpro(
    conn_info: Dict,
    fecha_desde: datetime,
    fecha_hasta: datetime
) -> List[Dict]:
    """
    Extrae propinas pagadas con tarjeta de MPRO.
    
    Fuente: Comanda_Pago.Cp_Propina donde Forma_Pago.Fp_Tipo = '04'
    
    Args:
        conn_info: Información de conexión
        fecha_desde: Fecha inicio
        fecha_hasta: Fecha fin
        
    Returns:
        Lista de registros transformados para EDARSAHUB
    """
    logger.info(f"[SYNC_PROPINAS_MPRO] Extrayendo propinas TPV de {conn_info['unidad_nombre']} "
                f"desde {fecha_desde.date()} hasta {fecha_hasta.date()}")
    
    try:
        mpro_conn = get_mpro_connection(conn_info)
    except Exception as e:
        logger.error(f"[SYNC_PROPINAS_MPRO] Error conectando a {conn_info['unidad_nombre']}: {e}")
        raise
    
    cursor = mpro_conn.cursor(as_dict=True)
    
    try:
        # Obtener el código de empresa para filtrar
        empresa_codigo = conn_info.get('empresa_codigo')
        
        # Query para extraer propinas TPV de MPRO
        # Solo formas de pago tipo '04' (tarjetas)
        # Relación: Comanda_Pago → Comanda (Co_Folio) → Sucursal (Sc_Cve_Sucursal) → Empresa (Em_Cve_Empresa)
        query = """
            SELECT 
                cp.Co_Folio,
                cp.Cp_ID,
                cp.Fp_Cve_Forma_Pago,
                cp.Cp_Importe,
                cp.Cp_Propina,
                cp.Cp_Referencia,
                c.Co_Fecha,
                c.Co_Propina as Propina_Total_Comanda,
                c.Sc_Cve_Sucursal,
                s.Sc_Descripcion as Sucursal_Nombre,
                s.Em_Cve_Empresa,
                e.Em_Descripcion as Empresa_Nombre,
                fp.Fp_Descripcion,
                fp.Fp_Tipo
            FROM Comanda_Pago cp
            JOIN Comanda c ON c.Co_Folio = cp.Co_Folio
            JOIN Sucursal s ON s.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
            JOIN Empresa e ON e.Em_Cve_Empresa = s.Em_Cve_Empresa
            JOIN Forma_Pago fp ON fp.Fp_Cve_Forma_Pago = cp.Fp_Cve_Forma_Pago
            WHERE c.Co_Fecha >= %s
              AND c.Co_Fecha < %s
              AND cp.Cp_Propina > 0
              AND fp.Fp_Tipo = '04'
        """
        
        params = [fecha_desde, fecha_hasta]
        
        # Filtrar por empresa usando la relación Sucursal.Em_Cve_Empresa
        if empresa_codigo:
            query += " AND s.Em_Cve_Empresa = %s"
            params.append(empresa_codigo)
        
        query += " ORDER BY c.Co_Fecha, cp.Co_Folio, cp.Fp_Cve_Forma_Pago"
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        logger.info(f"[SYNC_PROPINAS_MPRO] {conn_info['unidad_nombre']}: {len(rows)} pagos con propina TPV")
        
        # Transformar a formato EDARSAHUB
        registros = []
        for row in rows:
            # Crear ID único combinando folio + Cp_ID (identificador único del pago)
            id_origen = f"{row['Co_Folio']}_{row['Cp_ID']}"
            
            registro = {
                # Identificación de unidad
                'UnidadNegocioID': conn_info['unidad_negocio_id'],
                'UnidadNegocioNombre': conn_info['unidad_nombre'],
                'ServerID': conn_info['server_id'],
                'server_name': conn_info['servidor_nombre'],
                
                # Identificación de origen
                'SistemaOrigen': 'MPRO',
                'BaseDatosOrigen': conn_info['database'],
                'TablaOrigen': 'Comanda_Pago',
                'IdOrigen': id_origen,
                'FolioOrigen': str(row['Co_Folio']),
                
                # Fechas - Usar folio_comanda + Cp_ID para unicidad (UK_propinas_tpv_corte)
                'FechaOperacion': row['Co_Fecha'],
                'fecha_corte': row['Co_Fecha'],
                'folio_corte': f"{row['Co_Folio']}_{row['Cp_ID']}",  # Incluir Cp_ID para unicidad
                
                # Montos
                'ImportePropinaTPV': Decimal(str(row['Cp_Propina'] or 0)),
                'propinas_totales_corte': Decimal(str(row['Propina_Total_Comanda'] or 0)),
                'propinas_tpv': Decimal(str(row['Cp_Propina'] or 0)),
                'propinas_efectivo': Decimal('0'),  # No aplica, es pago con tarjeta
                'ventas_tarjeta': Decimal(str(row['Cp_Importe'] or 0)),
                'ventas_efectivo': Decimal('0'),
                'ventas_totales': Decimal(str(row['Cp_Importe'] or 0)),  # Importe del pago
                
                # Forma de pago (específica para MPRO)
                'FormaPagoID': str(row['Fp_Cve_Forma_Pago']),
                'FormaPagoNombre': row['Fp_Descripcion'],
                'EsTarjeta': 1,
                
                # Otros campos
                'sucursal_id': str(row['Sc_Cve_Sucursal']),
                'sucursal_nombre': row['Sucursal_Nombre'],
                'system_type': 'MPRO',
                'total_cheques': 1,
                'estacion_id': '',
                'turno_id_origen': '',
                
                # Flags
                'EsDemo': 0,
                'Activo': 1,
                
                # Datos adicionales
                'empresa_id': row['Em_Cve_Empresa'],
                'corte_id_origen': str(row['Co_Folio']),
                'tipo_dato': 'EXACTO',
                'metodo_calculo': 'Comanda_Pago.Cp_Propina WHERE Fp_Tipo=04',
                'confianza': 1.0,
                'query_origen': 'Comanda_Pago JOIN Sucursal JOIN Empresa WHERE Fp_Tipo=04',
            }
            
            # Calcular HashOrigen
            registro['HashOrigen'] = calcular_hash_propina_mpro(registro)
            
            registros.append(registro)
        
        return registros
        
    finally:
        mpro_conn.close()


# ============================================================================
# CARGA HACIA EDARSAHUB
# ============================================================================

def cargar_propinas_mpro_edarsahub(
    registros: List[Dict],
    conn_info: Dict
) -> Dict[str, Any]:
    """
    Carga propinas TPV de MPRO en EDARSAHUB.propinas_tpv_control
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
                    stats['omitidos'] += 1
                else:
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
                logger.error(f"[SYNC_PROPINAS_MPRO] Error insertando registro: {e}")
                stats['errores'] += 1
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"[SYNC_PROPINAS_MPRO] Error en carga: {e}")
        raise
    finally:
        conn.close()
    
    return stats


def registrar_synclog_propinas_mpro(
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
        """, (
            conn_info['unidad_negocio_id'],
            conn_info['unidad_nombre'],
            conn_info['server_id'],
            'MPRO',
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
        
        cursor.execute("SELECT MAX(LogID) FROM Finanzas_PropinasTPV_SyncLog")
        log_id = cursor.fetchone()[0]
        
        logger.info(f"[SYNC_PROPINAS_MPRO] SyncLog registrado: ID={log_id}, Estatus={estatus}")
        
        return log_id
        
    finally:
        conn.close()


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def sincronizar_propinas_mpro(
    unidad_nombre: str,
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    dias_atras: int = 7
) -> Dict[str, Any]:
    """
    Sincroniza propinas TPV de una unidad MPRO hacia EDARSAHUB.
    
    Args:
        unidad_nombre: Nombre de la unidad (130° QUERETARO, ORIGEN)
        fecha_desde: Fecha inicio
        fecha_hasta: Fecha fin
        dias_atras: Días hacia atrás si no se especifica rango
        
    Returns:
        Dict con resultados
    """
    logger.info(f"[SYNC_PROPINAS_MPRO] === Iniciando sync de propinas TPV: {unidad_nombre} ===")
    
    inicio = datetime.now()
    
    if unidad_nombre not in UNIDADES_MPRO_AUTORIZADAS:
        return {
            'unidad': unidad_nombre,
            'estatus': 'ERROR',
            'error': f'Unidad no autorizada: {unidad_nombre}. Autorizadas: {UNIDADES_MPRO_AUTORIZADAS}'
        }
    
    if fecha_hasta is None:
        fecha_hasta = datetime.now()
    if fecha_desde is None:
        fecha_desde = fecha_hasta - timedelta(days=dias_atras)
    
    conn_info = get_unidad_mpro_connection_info(unidad_nombre)
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
        'empresa_codigo': conn_info.get('empresa_codigo'),
        'base_datos_origen': conn_info['database'],
        'fecha_desde': fecha_desde.isoformat(),
        'fecha_hasta': fecha_hasta.isoformat(),
        'stats': {},
        'estatus': 'EN_PROGRESO'
    }
    
    try:
        # 1. Extraer propinas de MPRO
        registros = extraer_propinas_tpv_mpro(conn_info, fecha_desde, fecha_hasta)
        resultado['registros_origen'] = len(registros)
        
        # Calcular suma y agrupar por forma de pago
        suma_origen = sum(r['propinas_tpv'] for r in registros)
        resultado['suma_propinas_origen'] = float(suma_origen)
        
        # Agrupar por forma de pago
        formas_pago = {}
        for r in registros:
            fp = r['FormaPagoNombre']
            if fp not in formas_pago:
                formas_pago[fp] = {'count': 0, 'total': Decimal('0')}
            formas_pago[fp]['count'] += 1
            formas_pago[fp]['total'] += r['propinas_tpv']
        
        resultado['formas_pago_detectadas'] = {
            k: {'count': v['count'], 'total': float(v['total'])}
            for k, v in formas_pago.items()
        }
        
        # 2. Cargar en EDARSAHUB
        stats = cargar_propinas_mpro_edarsahub(registros, conn_info)
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
        log_id = registrar_synclog_propinas_mpro(
            conn_info, fecha_desde, fecha_hasta,
            resultado['stats'], resultado['estatus']
        )
        resultado['synclog_id'] = log_id
        
        # 5. Muestra de registros
        if registros:
            resultado['muestra_origen'] = [
                {
                    'IdOrigen': r['IdOrigen'],
                    'FolioOrigen': r['FolioOrigen'],
                    'FechaOperacion': str(r['FechaOperacion']),
                    'PropinasTPV': float(r['propinas_tpv']),
                    'FormaPago': r['FormaPagoNombre'],
                    'HashOrigen': r['HashOrigen'][:16] + '...'
                }
                for r in registros[:5]
            ]
        
    except Exception as e:
        resultado['estatus'] = 'ERROR'
        resultado['error'] = str(e)
        logger.error(f"[SYNC_PROPINAS_MPRO] Error en sync de {unidad_nombre}: {e}")
        
        try:
            registrar_synclog_propinas_mpro(
                conn_info, fecha_desde, fecha_hasta,
                {'insertados': 0, 'actualizados': 0, 'omitidos': 0, 'errores': 1},
                'ERROR', str(e)
            )
        except:
            pass
    
    resultado['duracion_segundos'] = int((datetime.now() - inicio).total_seconds())
    
    logger.info(f"[SYNC_PROPINAS_MPRO] {unidad_nombre}: {resultado['estatus']}, "
                f"insertados={resultado.get('stats', {}).get('insertados', 0)}, "
                f"omitidos={resultado.get('stats', {}).get('omitidos', 0)}")
    
    return resultado


def sincronizar_todas_unidades_mpro(
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    dias_atras: int = 7
) -> Dict[str, Any]:
    """
    Sincroniza propinas TPV de todas las unidades MPRO.
    """
    logger.info("=" * 70)
    logger.info("SYNC PROPINAS TPV — TODAS LAS UNIDADES MPRO")
    logger.info("=" * 70)
    
    resultados = {
        'unidades_procesadas': 0,
        'unidades_exitosas': 0,
        'unidades_fallidas': 0,
        'total_insertados': 0,
        'total_omitidos': 0,
        'detalle': []
    }
    
    for unidad in UNIDADES_MPRO_AUTORIZADAS:
        resultado = sincronizar_propinas_mpro(
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
    'sincronizar_propinas_mpro',
    'sincronizar_todas_unidades_mpro',
    'UNIDADES_MPRO_AUTORIZADAS'
]
