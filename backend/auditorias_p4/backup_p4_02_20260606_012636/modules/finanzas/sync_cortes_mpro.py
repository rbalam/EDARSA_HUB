"""
SUBFASE 2.3 - Sincronización de Cortes de Caja desde MPRO/ManagementPro hacia EDARSAHUB

Este módulo extrae cortes de caja de MPRO (CENTRAL2020.Comanda_Corte) 
y los sincroniza hacia EDARSAHUB.Finanzas_CortesCaja.

Unidades soportadas:
- 130° QUERETARO (Sc_Cve_Sucursal = '0021')
- ORIGEN (Sc_Cve_Sucursal = '0023')

Fuentes:
- tabla `Comanda_Corte` (CENTRAL2020)

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
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


# Configuración de logging
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

EDARSAHUB_CONFIG = {
    'server': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'user': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}

# Unidades MPRO autorizadas con su mapeo de sucursal
UNIDADES_MPRO_AUTORIZADAS = {
    '130° QUERETARO': '0021',
    'ORIGEN': '0023'
}


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


def get_unidad_info_mpro(unidad_nombre: str) -> Optional[Dict]:
    """
    Obtiene información de conexión y mapeo para una unidad MPRO desde EDARSAHUB.
    """
    # Importar decrypt_secret aquí para evitar problemas de import circular
    try:
        from core.secret_manager import decrypt_secret
    except ImportError:
        decrypt_secret = lambda x: x
    
    conn = get_edarsahub_connection()
    cursor = conn.cursor(as_dict=True)
    
    try:
        cursor.execute("""
            SELECT 
                u.id as unidad_negocio_id,
                u.nombre as unidad_nombre,
                u.codigo as unidad_codigo,
                u.server_id,
                u.sucursal_origen_id,
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
              AND s.system_type = 'MPRO'
        """, (unidad_nombre,))
        
        unidad = cursor.fetchone()
        
        if not unidad:
            logger.warning(f"[SYNC_MPRO] Unidad no encontrada: {unidad_nombre}")
            return None
        
        # Parsear host
        host_raw = unidad['host'] or ''
        host = host_raw
        port = unidad['port'] or 1433
        
        if ':' in host_raw:
            parts = host_raw.split(':')
            host = parts[0]
            try:
                port = int(parts[1])
            except ValueError:
                port = 1433
        
        # Descifrar contraseña
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
            'sucursal_origen_id': unidad['sucursal_origen_id'],
            'servidor_nombre': unidad['servidor_nombre'],
            'host': host,
            'port': port,
            'database': unidad['database_name'],
            'user': unidad['username'],
            'password': password,
            'system_type': unidad['system_type']
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
        login_timeout=30
    )


# ============================================================================
# FUNCIONES DE HASH E IDEMPOTENCIA
# ============================================================================

def calcular_hash_origen_mpro(registro: Dict) -> str:
    """
    Calcula SHA256 para validar integridad y detectar cambios.
    """
    componentes = [
        str(registro.get('SistemaOrigen', '')),
        str(registro.get('ServerID', '')),
        str(registro.get('IdOrigen', '')),
        str(registro.get('FolioCorte', '')),
        str(registro.get('FechaCorte', '')),
        str(registro.get('CajaID', '')),
        str(registro.get('TurnoID', '')),
        str(float(registro.get('TotalVenta', 0) or 0)),
        str(float(registro.get('TotalPago', 0) or 0)),
        str(float(registro.get('TotalDeclarado', 0) or 0)),
    ]
    cadena = '|'.join(componentes)
    return hashlib.sha256(cadena.encode()).hexdigest()


# ============================================================================
# EXTRACCIÓN DESDE MPRO
# ============================================================================

def extraer_cortes_mpro(
    conn_info: Dict,
    fecha_desde: datetime,
    fecha_hasta: datetime
) -> List[Dict]:
    """
    Extrae cortes de caja de MPRO (Comanda_Corte) para un rango de fechas.
    
    Args:
        conn_info: Información de conexión de EDARSAHUB
        fecha_desde: Fecha inicio del rango
        fecha_hasta: Fecha fin del rango
        
    Returns:
        Lista de registros transformados listos para EDARSAHUB
    """
    sucursal_id = conn_info.get('sucursal_origen_id')
    if not sucursal_id:
        raise ValueError(f"No se encontró sucursal_origen_id para {conn_info['unidad_nombre']}")
    
    logger.info(f"[SYNC_MPRO] Extrayendo cortes de {conn_info['unidad_nombre']} "
                f"(sucursal {sucursal_id}) desde {fecha_desde.date()} hasta {fecha_hasta.date()}")
    
    try:
        mpro_conn = get_mpro_connection(conn_info)
        cursor = mpro_conn.cursor(as_dict=True)
        
        # Query de extracción - MPRO usa Comanda_Corte
        cursor.execute("""
            SELECT 
                Cc_Folio,
                Cc_Fecha,
                Sc_Cve_Sucursal,
                Cc_Turno,
                Cc_Caja,
                Cc_Cajero,
                Cc_Importe_Pago,
                Cc_Importe_Venta,
                Cc_Importe_Declarado,
                Cc_Importe_Retirado,
                Cc_Importe_Descuento,
                Cc_Venta_Contado,
                Cc_Venta_Credito,
                Cc_Anticipo,
                Cc_Anticipo_Aplicado,
                Cc_Devolucion,
                Es_Cve_Estado,
                Fecha_Alta
            FROM Comanda_Corte
            WHERE Sc_Cve_Sucursal = %s
              AND Cc_Fecha >= %s
              AND Cc_Fecha < %s
              AND (Es_Cve_Estado IS NULL OR Es_Cve_Estado != 'BAJA')
            ORDER BY Cc_Fecha ASC, Cc_Turno ASC
        """, (sucursal_id, fecha_desde, fecha_hasta))
        
        cortes_origen = cursor.fetchall()
        mpro_conn.close()
        
        logger.info(f"[SYNC_MPRO] {len(cortes_origen)} cortes encontrados en {conn_info['unidad_nombre']}")
        
        # Transformar a formato EDARSAHUB
        registros = []
        for c in cortes_origen:
            # Calcular totales
            total_venta = float(c.get('Cc_Importe_Venta') or 0)
            total_pago = float(c.get('Cc_Importe_Pago') or 0)
            total_declarado = float(c.get('Cc_Importe_Declarado') or 0)
            venta_contado = float(c.get('Cc_Venta_Contado') or 0)  # Efectivo aproximado
            venta_credito = float(c.get('Cc_Venta_Credito') or 0)  # Tarjeta/Crédito aproximado
            retiros = float(c.get('Cc_Importe_Retirado') or 0)
            descuentos = float(c.get('Cc_Importe_Descuento') or 0)
            
            registro = {
                # Trazabilidad
                'UnidadNegocioID': conn_info['unidad_negocio_id'],
                'UnidadNegocioNombre': conn_info['unidad_nombre'],
                'ServerID': conn_info['server_id'],
                'EmpresaID': None,  # MPRO no tiene este campo
                
                # Identificación de origen
                'SistemaOrigen': 'MPRO',
                'BaseDatosOrigen': conn_info['database'],
                'TablaOrigen': 'Comanda_Corte',
                
                # Identificadores únicos
                'IdOrigen': c['Cc_Folio'],  # PK en MPRO es el folio
                'FolioCorte': c['Cc_Folio'],
                'SucursalOrigenID': c['Sc_Cve_Sucursal'],
                
                # Fechas
                'FechaCorte': c['Cc_Fecha'].date() if c['Cc_Fecha'] else None,
                'FechaApertura': None,  # MPRO no tiene apertura explícita
                'FechaCierre': c['Cc_Fecha'],  # Usamos fecha del corte como cierre
                
                # Caja/Cajero
                'CajaID': c.get('Cc_Caja'),
                'CajaNombre': c.get('Cc_Caja'),
                'CajeroID': c.get('Cc_Cajero'),
                'CajeroNombre': c.get('Cc_Cajero'),  # MPRO solo tiene ID
                
                # Turno
                'TurnoID': c.get('Cc_Turno'),
                
                # Montos - MPRO estructura diferente a SR
                'TotalEfectivo': venta_contado,  # Venta_Contado ≈ efectivo
                'TotalTarjetaDebito': venta_credito / 2 if venta_credito > 0 else 0,  # Aproximación
                'TotalTarjetaCredito': venta_credito / 2 if venta_credito > 0 else 0,  # Aproximación
                'TotalVales': 0,  # MPRO no tiene vales explícitos
                'FondoInicial': 0,  # MPRO no tiene fondo explícito
                'TotalVenta': total_venta,
                'TotalPago': total_pago,
                'TotalDeclarado': total_declarado,
                
                # Otros campos
                'Propinas': 0,  # No disponible en Comanda_Corte
                'Retiros': abs(retiros),  # MPRO guarda negativo
                'TotalAmex': 0,
                'TotalInternacional': 0,
                'TotalOtros': 0,
                'TotalDescuento': descuentos,
                
                # Control
                'EsDemo': 0,
                'Activo': 1,
            }
            
            # Calcular hash
            registro['HashOrigen'] = calcular_hash_origen_mpro(registro)
            
            registros.append(registro)
        
        return registros
        
    except Exception as e:
        logger.error(f"[SYNC_MPRO] Error extrayendo de {conn_info['unidad_nombre']}: {e}")
        raise


# ============================================================================
# SINCRONIZACIÓN A EDARSAHUB
# ============================================================================

def sincronizar_a_edarsahub_mpro(
    registros: List[Dict],
    conn_info: Dict
) -> Dict[str, int]:
    """
    Sincroniza registros MPRO a EDARSAHUB usando MERGE (idempotente).
    """
    if not registros:
        return {'leidos': 0, 'insertados': 0, 'actualizados': 0, 'omitidos': 0, 'errores': 0}
    
    logger.info(f"[SYNC_MPRO] Sincronizando {len(registros)} registros a EDARSAHUB")
    
    stats = {'leidos': len(registros), 'insertados': 0, 'actualizados': 0, 'omitidos': 0, 'errores': 0}
    
    conn = get_edarsahub_connection()
    cursor = conn.cursor(as_dict=True)
    
    try:
        for reg in registros:
            try:
                # Para MPRO, IdOrigen es string (Cc_Folio), usamos FolioCorte para buscar
                cursor.execute("""
                    SELECT CorteCajaID, HashOrigen 
                    FROM Finanzas_CortesCaja
                    WHERE SistemaOrigen = %s AND ServerID = %s AND FolioCorte = %s
                """, (reg['SistemaOrigen'], reg['ServerID'], reg['FolioCorte']))
                
                existente = cursor.fetchone()
                
                if existente:
                    # Existe - verificar si cambió
                    if existente['HashOrigen'] == reg['HashOrigen']:
                        stats['omitidos'] += 1
                    else:
                        # Cambió - actualizar
                        cursor.execute("""
                            UPDATE Finanzas_CortesCaja SET
                                FechaCorte = %s,
                                FechaCierre = %s,
                                CajaID = %s,
                                CajaNombre = %s,
                                CajeroID = %s,
                                CajeroNombre = %s,
                                TurnoID = %s,
                                TotalEfectivo = %s,
                                TotalTarjetaDebito = %s,
                                TotalTarjetaCredito = %s,
                                TotalVenta = %s,
                                Retiros = %s,
                                HashOrigen = %s,
                                FechaUltimaActualizacion = GETDATE(),
                                FechaSincronizacion = GETDATE()
                            WHERE CorteCajaID = %s
                        """, (
                            reg['FechaCorte'], reg['FechaCierre'],
                            reg['CajaID'], reg['CajaNombre'], reg['CajeroID'], reg['CajeroNombre'],
                            reg['TurnoID'],
                            reg['TotalEfectivo'], reg['TotalTarjetaDebito'], reg['TotalTarjetaCredito'],
                            reg['TotalVenta'], reg['Retiros'],
                            reg['HashOrigen'], existente['CorteCajaID']
                        ))
                        stats['actualizados'] += 1
                else:
                    # No existe - insertar
                    # Para MPRO, IdOrigen se deja NULL porque es BIGINT y el folio es string
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
                            NULL, %s, %s,
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
                        reg['FolioCorte'], reg['SucursalOrigenID'],
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
                logger.error(f"[SYNC_MPRO] Error procesando registro FolioCorte={reg.get('FolioCorte')}: {e}")
                stats['errores'] += 1
        
        # Solo hacer commit si no hay errores críticos
        if stats['insertados'] > 0 or stats['actualizados'] > 0:
            conn.commit()
        logger.info(f"[SYNC_MPRO] Sincronización completada: {stats}")
        
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        logger.error(f"[SYNC_MPRO] Error en sincronización: {e}")
        raise
    finally:
        conn.close()
    
    return stats


def registrar_sync_log_mpro(
    unidad_id: str,
    server_id: str,
    fecha_desde: datetime,
    fecha_hasta: datetime,
    stats: Dict[str, int],
    estatus: str,
    error_mensaje: str = None,
    duracion_segundos: int = None,
    tipo_ejecucion: str = 'MANUAL'
) -> int:
    """Registra la ejecución de sincronización MPRO en bitácora"""
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
            unidad_id, server_id, 'MPRO',
            fecha_desde.date(), fecha_hasta.date(),
            stats.get('leidos', 0), stats.get('insertados', 0), stats.get('actualizados', 0),
            stats.get('omitidos', 0), stats.get('errores', 0),
            estatus, error_mensaje, duracion_segundos,
            tipo_ejecucion
        ))
        conn.commit()
        
        cursor.execute("SELECT @@IDENTITY")
        log_id = cursor.fetchone()[0]
        
        logger.info(f"[SYNC_MPRO] SyncLog registrado: ID={log_id}, Estatus={estatus}")
        return log_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"[SYNC_MPRO] Error registrando SyncLog: {e}")
        raise
    finally:
        conn.close()


# ============================================================================
# FUNCIÓN PRINCIPAL DE SINCRONIZACIÓN
# ============================================================================

def sincronizar_unidad_mpro(
    unidad_nombre: str,
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    dias_atras: int = 7
) -> Dict[str, Any]:
    """
    Sincroniza cortes de caja de una unidad MPRO específica.
    """
    # Validar unidad autorizada
    if unidad_nombre not in UNIDADES_MPRO_AUTORIZADAS:
        raise ValueError(f"Unidad no autorizada: {unidad_nombre}. "
                        f"Autorizadas: {list(UNIDADES_MPRO_AUTORIZADAS.keys())}")
    
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
        conn_info = get_unidad_info_mpro(unidad_nombre)
        if not conn_info:
            raise ValueError(f"No se encontró configuración para {unidad_nombre}")
        
        resultado['server_id'] = conn_info['server_id']
        resultado['unidad_negocio_id'] = conn_info['unidad_negocio_id']
        resultado['database'] = conn_info['database']
        resultado['sucursal_origen_id'] = conn_info['sucursal_origen_id']
        
        # Extraer de MPRO
        registros = extraer_cortes_mpro(conn_info, fecha_desde, fecha_hasta)
        
        # Sincronizar a EDARSAHUB
        stats = sincronizar_a_edarsahub_mpro(registros, conn_info)
        resultado['stats'] = stats
        
        # Determinar estatus
        if stats['errores'] > 0:
            resultado['estatus'] = 'PARCIAL'
        else:
            resultado['estatus'] = 'COMPLETADO'
        
        resultado['duracion_segundos'] = int((datetime.now() - inicio).total_seconds())
        
        # Registrar en bitácora
        registrar_sync_log_mpro(
            unidad_id=conn_info['unidad_negocio_id'],
            server_id=conn_info['server_id'],
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
        logger.error(f"[SYNC_MPRO] Error sincronizando {unidad_nombre}: {e}")
        
        # Intentar registrar error en bitácora
        try:
            if 'server_id' in resultado:
                registrar_sync_log_mpro(
                    unidad_id=resultado.get('unidad_negocio_id', ''),
                    server_id=resultado.get('server_id', ''),
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


def sincronizar_todas_unidades_mpro(
    fecha_desde: datetime = None,
    fecha_hasta: datetime = None,
    dias_atras: int = 7
) -> List[Dict[str, Any]]:
    """
    Sincroniza todas las unidades MPRO autorizadas.
    """
    resultados = []
    
    for unidad in UNIDADES_MPRO_AUTORIZADAS.keys():
        logger.info(f"[SYNC_MPRO] === Iniciando sincronización: {unidad} ===")
        try:
            resultado = sincronizar_unidad_mpro(
                unidad_nombre=unidad,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                dias_atras=dias_atras
            )
            resultados.append(resultado)
        except Exception as e:
            logger.error(f"[SYNC_MPRO] Error fatal en {unidad}: {e}")
            resultados.append({
                'unidad': unidad,
                'estatus': 'ERROR',
                'error': str(e),
                'stats': {}
            })
    
    return resultados


# ============================================================================
# EJECUCIÓN DIRECTA
# ============================================================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("SINCRONIZACIÓN MPRO - PRUEBA")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        unidad = sys.argv[1]
        resultado = sincronizar_unidad_mpro(unidad, dias_atras=7)
        print(f"\nResultado {unidad}:")
        print(f"  Estatus: {resultado['estatus']}")
        print(f"  Stats: {resultado['stats']}")
        if resultado['error']:
            print(f"  Error: {resultado['error']}")
    else:
        resultados = sincronizar_todas_unidades_mpro(dias_atras=7)
        for r in resultados:
            print(f"\n{r['unidad']}:")
            print(f"  Estatus: {r['estatus']}")
            print(f"  Stats: {r.get('stats', {})}")
            if r.get('error'):
                print(f"  Error: {r['error']}")
