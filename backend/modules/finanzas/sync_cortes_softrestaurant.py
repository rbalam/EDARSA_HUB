"""
SUBFASE 2.2 - Sincronización de Cortes de Caja desde SoftRestaurant hacia EDARSAHUB

Este módulo extrae cortes de caja (turnos cerrados) de SoftRestaurant 
y los sincroniza hacia EDARSAHUB.Finanzas_CortesCaja.

Unidades soportadas:
- 130° MERIDA
- CIENFUEGOS
- LA ESTELAR

Fuentes:
- tabla `turnos` (SoftRestaurant)

Destino:
- EDARSAHUB.Finanzas_CortesCaja
- EDARSAHUB.Finanzas_CortesCaja_SyncLog

Autor: E1 Agent
Fecha: 1 Mayo 2026
Fase: Finanzas Fase 2 - Control de Ingresos
"""

import os
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

import pymssql

from core.system_type_utils import build_system_type_sql_filter
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


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

# Unidades SoftRestaurant autorizadas
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
    
    CORRECCIÓN 2026-05-01:
    - Usa core.db.parse_sql_server_host() para parsear correctamente instancias nombradas
    - Preserva la instancia (ej: \nationalsoft) que antes se descartaba
    - Compatible con formatos: host,port\instance, host\instance, host,port, host
    
    Args:
        unidad_nombre: Nombre de la unidad (ej: '130° MERIDA')
        
    Returns:
        Dict con datos de conexión o None si no se encuentra
    """
    # Importar decrypt_secret y parse_sql_server_host
    try:
        from core.secret_manager import decrypt_secret
    except ImportError:
        decrypt_secret = lambda x: x  # Fallback: usar valor directo
    
    try:
        from core.db import parse_sql_server_host
    except ImportError:
        # Fallback local si no está disponible
        def parse_sql_server_host(host, default_port):
            return (host, default_port, None)
    
    conn = get_edarsahub_connection()
    cursor = conn.cursor(as_dict=True)
    
    try:
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
            logger.warning(f"[SYNC_SR] Unidad no encontrada: {unidad_nombre}")
            return None
        
        # CORRECCIÓN: Usar parse_sql_server_host() igual que endpoint /ping
        # Esto preserva la instancia nombrada (ej: \nationalsoft)
        host_raw = unidad['host'] or ''
        default_port = unidad['port'] or 1433
        
        hostname, parsed_port, instance = parse_sql_server_host(host_raw, default_port)
        
        logger.info(f"[SYNC_SR] Conexión parseada para {unidad_nombre}: "
                    f"host={hostname}, port={parsed_port}, instance={instance}")
        
        # Descifrar contraseña
        password_enc = unidad['password_encrypted'] or ''
        try:
            password = decrypt_secret(password_enc)
        except Exception:
            # Si falla descifrado, usar valor directo (legacy)
            password = password_enc
        
        return {
            'unidad_negocio_id': str(unidad['unidad_negocio_id']),
            'unidad_nombre': unidad['unidad_nombre'],
            'unidad_codigo': unidad['unidad_codigo'],
            'server_id': str(unidad['server_id']),
            'servidor_nombre': unidad['servidor_nombre'],
            'host': hostname,           # Hostname parseado
            'host_raw': host_raw,       # Host original (para logging)
            'port': parsed_port,        # Puerto parseado
            'instance': instance,       # Instancia nombrada (CORRECCIÓN)
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
    
    CORRECCIÓN 2026-05-01:
    - Usa pytds como driver principal (igual que endpoint /ping)
    - Soporta instancias nombradas correctamente
    - Fallback a pymssql si pytds falla
    - Retorna tupla (conexión, driver_name) para manejo correcto de cursor
    """
    import pytds
    
    host = conn_info['host']
    port = conn_info['port']
    instance = conn_info.get('instance')  # Nueva: instancia nombrada
    database = conn_info['database']
    user = conn_info['user']
    password = conn_info['password']
    
    # pytds maneja mejor las instancias nombradas (igual que endpoint /ping)
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
        logger.info(f"[SYNC_SR] Conexión pytds exitosa a {host}:{port}/{database}")
        # Añadir atributo para identificar el driver
        conn._driver_name = 'pytds'
        return conn
    except Exception as pytds_error:
        logger.warning(f"[SYNC_SR] pytds falló: {pytds_error}, intentando pymssql...")
        
        # Fallback a pymssql con instancia
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
    """
    Ejecuta query en conexión SoftRestaurant y retorna resultados como lista de dicts.
    
    Maneja la diferencia entre pytds y pymssql:
    - pymssql: soporta cursor(as_dict=True)
    - pytds: requiere conversión manual
    """
    driver = getattr(conn, '_driver_name', 'unknown')
    
    if driver == 'pymssql':
        cursor = conn.cursor(as_dict=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return list(cursor.fetchall())
    else:
        # pytds - conversión manual a dict
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

def calcular_hash_origen(registro: Dict) -> str:
    """
    Calcula SHA256 para validar integridad y detectar cambios.
    
    El hash se basa en campos clave que definen el corte.
    Si alguno cambia, el hash cambia y se actualiza el registro.
    """
    componentes = [
        str(registro.get('SistemaOrigen', '')),
        str(registro.get('ServerID', '')),
        str(registro.get('IdOrigen', '')),
        str(registro.get('FolioCorte', '')),
        str(registro.get('FechaCorte', '')),
        str(registro.get('CajaID', '')),
        str(registro.get('CajeroID', '')),
        str(float(registro.get('TotalEfectivo', 0) or 0)),
        str(float(registro.get('TotalTarjetaDebito', 0) or 0)),
        str(float(registro.get('TotalTarjetaCredito', 0) or 0)),
        str(float(registro.get('TotalVales', 0) or 0)),
    ]
    cadena = '|'.join(componentes)
    return hashlib.sha256(cadena.encode()).hexdigest()


# ============================================================================
# EXTRACCIÓN DESDE SOFTRESTAURANT
# ============================================================================

def extraer_turnos_softrestaurant(
    conn_info: Dict,
    fecha_desde: datetime,
    fecha_hasta: datetime
) -> List[Dict]:
    """
    Extrae turnos cerrados de SoftRestaurant para un rango de fechas.
    
    Args:
        conn_info: Información de conexión de EDARSAHUB
        fecha_desde: Fecha inicio del rango
        fecha_hasta: Fecha fin del rango
        
    Returns:
        Lista de registros transformados listos para EDARSAHUB
    """
    logger.info(f"[SYNC_SR] Extrayendo turnos de {conn_info['unidad_nombre']} "
                f"desde {fecha_desde.date()} hasta {fecha_hasta.date()}")
    
    try:
        sr_conn = get_softrestaurant_connection(conn_info)
        
        # Query de extracción
        query = """
            SELECT 
                idturnointerno,
                idturno,
                apertura,
                cierre,
                idestacion,
                cajero,
                efectivo,
                tarjeta,
                vales,
                credito,
                fondo,
                idempresa
            FROM turnos
            WHERE cierre IS NOT NULL
              AND cierre >= %s
              AND cierre < %s
            ORDER BY cierre ASC
        """
        
        turnos_origen = execute_sr_query(sr_conn, query, (fecha_desde, fecha_hasta))
        sr_conn.close()
        
        logger.info(f"[SYNC_SR] {len(turnos_origen)} turnos encontrados en {conn_info['unidad_nombre']}")
        
        # Transformar a formato EDARSAHUB
        registros = []
        for t in turnos_origen:
            registro = {
                # Trazabilidad
                'UnidadNegocioID': conn_info['unidad_negocio_id'],
                'UnidadNegocioNombre': conn_info['unidad_nombre'],
                'ServerID': conn_info['server_id'],
                'EmpresaID': t.get('idempresa'),
                
                # Identificación de origen
                'SistemaOrigen': 'SoftRestaurant',
                'BaseDatosOrigen': conn_info['database'],
                'TablaOrigen': 'turnos',
                
                # Identificadores únicos
                'IdOrigen': t['idturnointerno'],
                'FolioCorte': str(t['idturno']),
                
                # Fechas
                'FechaCorte': t['cierre'].date() if t['cierre'] else None,
                'FechaApertura': t['apertura'],
                'FechaCierre': t['cierre'],
                
                # Caja/Cajero
                'CajaID': t.get('idestacion'),
                'CajaNombre': t.get('idestacion'),
                'CajeroID': t.get('cajero'),
                'CajeroNombre': t.get('cajero'),
                
                # Turno
                'TurnoID': None,  # SoftRestaurant no tiene turno explícito
                
                # Montos
                'TotalEfectivo': float(t.get('efectivo') or 0),
                'TotalTarjetaDebito': float(t.get('tarjeta') or 0),  # SR no distingue deb/cred en turnos
                'TotalTarjetaCredito': float(t.get('credito') or 0),
                'TotalVales': float(t.get('vales') or 0),
                'FondoInicial': float(t.get('fondo') or 0),
                'TotalVenta': float(t.get('efectivo') or 0) + float(t.get('tarjeta') or 0) + 
                              float(t.get('credito') or 0) + float(t.get('vales') or 0),
                
                # Otros campos (NULL por ahora)
                'Propinas': 0,
                'Retiros': 0,
                'TotalAmex': 0,
                'TotalInternacional': 0,
                'TotalOtros': 0,
                
                # Control
                'EsDemo': 0,
                'Activo': 1,
            }
            
            # Calcular hash
            registro['HashOrigen'] = calcular_hash_origen(registro)
            
            registros.append(registro)
        
        return registros
        
    except Exception as e:
        logger.error(f"[SYNC_SR] Error extrayendo de {conn_info['unidad_nombre']}: {e}")
        raise


# ============================================================================
# SINCRONIZACIÓN A EDARSAHUB
# ============================================================================

def sincronizar_a_edarsahub(
    registros: List[Dict],
    conn_info: Dict
) -> Dict[str, int]:
    """
    Sincroniza registros a EDARSAHUB usando MERGE (idempotente).
    
    Args:
        registros: Lista de registros a sincronizar
        conn_info: Información de la unidad origen
        
    Returns:
        Dict con estadísticas: insertados, actualizados, omitidos, errores
    """
    if not registros:
        return {'leidos': 0, 'insertados': 0, 'actualizados': 0, 'omitidos': 0, 'errores': 0}
    
    logger.info(f"[SYNC_SR] Sincronizando {len(registros)} registros a EDARSAHUB")
    
    stats = {'leidos': len(registros), 'insertados': 0, 'actualizados': 0, 'omitidos': 0, 'errores': 0}
    
    conn = get_edarsahub_connection()
    cursor = conn.cursor(as_dict=True)
    
    try:
        for reg in registros:
            try:
                # Verificar si existe por llave única
                cursor.execute("""
                    SELECT CorteCajaID, HashOrigen 
                    FROM Finanzas_CortesCaja
                    WHERE SistemaOrigen = %s AND ServerID = %s AND IdOrigen = %s
                """, (reg['SistemaOrigen'], reg['ServerID'], reg['IdOrigen']))
                
                existente = cursor.fetchone()
                
                if existente:
                    # Existe - verificar si cambió
                    if existente['HashOrigen'] == reg['HashOrigen']:
                        # Sin cambios - omitir
                        stats['omitidos'] += 1
                    else:
                        # Cambió - actualizar
                        cursor.execute("""
                            UPDATE Finanzas_CortesCaja SET
                                FechaCorte = %s,
                                FechaApertura = %s,
                                FechaCierre = %s,
                                CajaID = %s,
                                CajaNombre = %s,
                                CajeroID = %s,
                                CajeroNombre = %s,
                                TotalEfectivo = %s,
                                TotalTarjetaDebito = %s,
                                TotalTarjetaCredito = %s,
                                TotalVales = %s,
                                TotalVenta = %s,
                                FondoInicial = %s,
                                HashOrigen = %s,
                                FechaUltimaActualizacion = GETDATE(),
                                FechaSincronizacion = GETDATE()
                            WHERE CorteCajaID = %s
                        """, (
                            reg['FechaCorte'], reg['FechaApertura'], reg['FechaCierre'],
                            reg['CajaID'], reg['CajaNombre'], reg['CajeroID'], reg['CajeroNombre'],
                            reg['TotalEfectivo'], reg['TotalTarjetaDebito'], reg['TotalTarjetaCredito'],
                            reg['TotalVales'], reg['TotalVenta'], reg['FondoInicial'],
                            reg['HashOrigen'], existente['CorteCajaID']
                        ))
                        stats['actualizados'] += 1
                else:
                    # No existe - insertar
                    cursor.execute("""
                        INSERT INTO Finanzas_CortesCaja (
                            UnidadNegocioID, UnidadNegocioNombre, EmpresaID, ServerID,
                            SistemaOrigen, BaseDatosOrigen, TablaOrigen,
                            IdOrigen, FolioCorte, SucursalOrigenID,
                            FechaCorte, FechaApertura, FechaCierre,
                            CajaID, CajaNombre, CajeroID, CajeroNombre, TurnoID,
                            TotalEfectivo, TotalTarjetaDebito, TotalTarjetaCredito,
                            TotalVales, TotalVenta, FondoInicial,
                            TotalAmex, TotalInternacional, TotalOtros,
                            Propinas, Retiros,
                            HashOrigen, FechaSincronizacion, EsDemo, Activo, FechaAlta,
                            SucursalID
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, GETDATE(), %s, %s, GETDATE(),
                            0
                        )
                    """, (
                        reg['UnidadNegocioID'], reg['UnidadNegocioNombre'], reg['EmpresaID'], reg['ServerID'],
                        reg['SistemaOrigen'], reg['BaseDatosOrigen'], reg['TablaOrigen'],
                        reg['IdOrigen'], reg['FolioCorte'], None,
                        reg['FechaCorte'], reg['FechaApertura'], reg['FechaCierre'],
                        reg['CajaID'], reg['CajaNombre'], reg['CajeroID'], reg['CajeroNombre'], reg['TurnoID'],
                        reg['TotalEfectivo'], reg['TotalTarjetaDebito'], reg['TotalTarjetaCredito'],
                        reg['TotalVales'], reg['TotalVenta'], reg['FondoInicial'],
                        reg['TotalAmex'], reg['TotalInternacional'], reg['TotalOtros'],
                        reg['Propinas'], reg['Retiros'],
                        reg['HashOrigen'], reg['EsDemo'], reg['Activo']
                    ))
                    stats['insertados'] += 1
                    
            except Exception as e:
                logger.error(f"[SYNC_SR] Error procesando registro IdOrigen={reg.get('IdOrigen')}: {e}")
                stats['errores'] += 1
        
        conn.commit()
        logger.info(f"[SYNC_SR] Sincronización completada: {stats}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"[SYNC_SR] Error en sincronización: {e}")
        raise
    finally:
        conn.close()
    
    return stats


def registrar_sync_log(
    unidad_id: str,
    server_id: str,
    sistema_origen: str,
    fecha_desde: datetime,
    fecha_hasta: datetime,
    stats: Dict[str, int],
    estatus: str,
    error_mensaje: str = None,
    duracion_segundos: int = None,
    tipo_ejecucion: str = 'MANUAL'
) -> int:
    """Registra la ejecución de sincronización en bitácora"""
    conn = get_edarsahub_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO Finanzas_CortesCaja_SyncLog (
                FechaInicio, FechaFin,
                UnidadNegocioID, ServerID, SistemaOrigen,
                FechaDesde, FechaHasta,
                RegistrosLeidos, RegistrosInsertados, RegistrosActualizados,
                RegistrosOmitidos, RegistrosError,
                Estatus, ErrorMensaje, DuracionSegundos,
                TipoEjecucion
            ) VALUES (
                GETDATE(), GETDATE(),
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s
            )
        """, (
            unidad_id, server_id, sistema_origen,
            fecha_desde.date(), fecha_hasta.date(),
            stats.get('leidos', 0), stats.get('insertados', 0), stats.get('actualizados', 0),
            stats.get('omitidos', 0), stats.get('errores', 0),
            estatus, error_mensaje, duracion_segundos,
            tipo_ejecucion
        ))
        conn.commit()
        
        # Obtener ID insertado
        cursor.execute("SELECT @@IDENTITY")
        log_id = cursor.fetchone()[0]
        
        logger.info(f"[SYNC_SR] SyncLog registrado: ID={log_id}, Estatus={estatus}")
        return log_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"[SYNC_SR] Error registrando SyncLog: {e}")
        raise
    finally:
        conn.close()


# ============================================================================
# FUNCIÓN PRINCIPAL DE SINCRONIZACIÓN
# ============================================================================

def sincronizar_unidad_softrestaurant(
    unidad_nombre: str,
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    dias_atras: int = 7
) -> Dict[str, Any]:
    """
    Sincroniza cortes de caja de una unidad SoftRestaurant específica.
    
    Args:
        unidad_nombre: Nombre de la unidad (debe estar en UNIDADES_SR_AUTORIZADAS)
        fecha_desde: Fecha inicio (opcional, default: dias_atras antes de hoy)
        fecha_hasta: Fecha fin (opcional, default: hoy)
        dias_atras: Días hacia atrás si no se especifica fecha_desde
        
    Returns:
        Dict con resultado de sincronización
    """
    # Validar unidad autorizada
    if unidad_nombre not in UNIDADES_SR_AUTORIZADAS:
        raise ValueError(f"Unidad no autorizada: {unidad_nombre}. "
                        f"Autorizadas: {UNIDADES_SR_AUTORIZADAS}")
    
    # Establecer fechas
    if fecha_hasta is None:
        fecha_hasta = datetime.now()
    if fecha_desde is None:
        fecha_desde = fecha_hasta - timedelta(days=dias_atras)
    
    inicio = datetime.now()
    resultado = {
        'unidad': unidad_nombre,
        'fecha_desde': fecha_desde.isoformat(),
        'fecha_hasta': fecha_hasta.isoformat(),
        'stats': {},
        'estatus': 'ERROR',
        'error': None,
        'duracion_segundos': 0
    }
    
    try:
        # Obtener conexión desde EDARSAHUB
        conn_info = get_unidad_connection_info(unidad_nombre)
        if not conn_info:
            raise ValueError(f"No se encontró configuración para {unidad_nombre}")
        
        resultado['server_id'] = conn_info['server_id']
        resultado['unidad_negocio_id'] = conn_info['unidad_negocio_id']
        resultado['database'] = conn_info['database']
        
        # Extraer de SoftRestaurant
        registros = extraer_turnos_softrestaurant(conn_info, fecha_desde, fecha_hasta)
        
        # Sincronizar a EDARSAHUB
        stats = sincronizar_a_edarsahub(registros, conn_info)
        resultado['stats'] = stats
        
        # Determinar estatus
        if stats['errores'] > 0:
            resultado['estatus'] = 'PARCIAL'
        else:
            resultado['estatus'] = 'COMPLETADO'
        
        resultado['duracion_segundos'] = int((datetime.now() - inicio).total_seconds())
        
        # Registrar en bitácora
        registrar_sync_log(
            unidad_id=conn_info['unidad_negocio_id'],
            server_id=conn_info['server_id'],
            sistema_origen='SoftRestaurant',
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            stats=stats,
            estatus=resultado['estatus'],
            duracion_segundos=resultado['duracion_segundos'],
            tipo_ejecucion='MANUAL'
        )
        
    except Exception as e:
        resultado['error'] = str(e)
        resultado['estatus'] = 'ERROR'
        resultado['duracion_segundos'] = int((datetime.now() - inicio).total_seconds())
        logger.error(f"[SYNC_SR] Error sincronizando {unidad_nombre}: {e}")
        
        # Intentar registrar error en bitácora
        try:
            if 'server_id' in resultado:
                registrar_sync_log(
                    unidad_id=resultado.get('unidad_negocio_id', ''),
                    server_id=resultado.get('server_id', ''),
                    sistema_origen='SoftRestaurant',
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    stats={'leidos': 0, 'insertados': 0, 'actualizados': 0, 'omitidos': 0, 'errores': 1},
                    estatus='ERROR',
                    error_mensaje=str(e),
                    duracion_segundos=resultado['duracion_segundos'],
                    tipo_ejecucion='MANUAL'
                )
        except:
            pass
    
    return resultado


def sincronizar_todas_unidades_softrestaurant(
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    dias_atras: int = 7
) -> List[Dict[str, Any]]:
    """
    Sincroniza todas las unidades SoftRestaurant autorizadas.
    
    Si una unidad falla, continúa con las demás (tolerancia a fallos).
    
    Returns:
        Lista de resultados por unidad
    """
    resultados = []
    
    for unidad in UNIDADES_SR_AUTORIZADAS:
        logger.info(f"[SYNC_SR] === Iniciando sincronización: {unidad} ===")
        try:
            resultado = sincronizar_unidad_softrestaurant(
                unidad_nombre=unidad,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                dias_atras=dias_atras
            )
            resultados.append(resultado)
        except Exception as e:
            logger.error(f"[SYNC_SR] Error fatal en {unidad}: {e}")
            resultados.append({
                'unidad': unidad,
                'estatus': 'ERROR',
                'error': str(e),
                'stats': {}
            })
    
    return resultados


# ============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar sincronización de prueba (últimos 7 días)
    print("=" * 80)
    print("SINCRONIZACIÓN SOFTRESTAURANT - PRUEBA")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        # Unidad específica
        unidad = sys.argv[1]
        resultado = sincronizar_unidad_softrestaurant(unidad, dias_atras=7)
        print(f"\nResultado {unidad}:")
        print(f"  Estatus: {resultado['estatus']}")
        print(f"  Stats: {resultado['stats']}")
        if resultado['error']:
            print(f"  Error: {resultado['error']}")
    else:
        # Todas las unidades
        resultados = sincronizar_todas_unidades_softrestaurant(dias_atras=7)
        for r in resultados:
            print(f"\n{r['unidad']}:")
            print(f"  Estatus: {r['estatus']}")
            print(f"  Stats: {r.get('stats', {})}")
            if r.get('error'):
                print(f"  Error: {r['error']}")
