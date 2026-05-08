# =============================================================================
# CAB-003 FASE 1B.1 - DETECTION SERVICE (Dry-Run)
# =============================================================================
# Servicio de detección de inventarios válidos en sistemas origen.
# 
# FASE 1B.1: Solo detección DRY-RUN
# - Lee configuración de EDARSAHUB
# - Consulta SOFT y MPRO (solo SELECT)
# - Construye clave CAB-003 de 8 campos
# - Compara contra ya procesados
# - Reporta qué detectaría
# - NO inserta nada
# - NO usa ultimo_folio_conocido
# =============================================================================

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class InventarioDetectado:
    """Estructura de salida para cada inventario detectado."""
    # Clave CAB-003 (8 campos)
    sistema_origen: str
    server_id: str
    sucursal_id: str
    almacen_id: str
    comentario: Optional[str]
    folio_inventario: str
    fecha_inventario: str  # ISO format string
    estado_inventario_origen: Optional[str]
    
    # Metadata de detección
    ya_procesado: bool
    accion_sugerida: str  # 'PROCESAR' o 'OMITIR'
    razon_omision: Optional[str]
    
    # Datos para análisis (si se aprueba procesar)
    folio_inicial_calculado: Optional[str]
    fecha_inicial_calculada: Optional[str]
    
    # Metadata adicional
    almacen_nombre: Optional[str] = None
    sucursal_nombre: Optional[str] = None


@dataclass
class ResultadoDryRun:
    """Estructura de salida del dry-run completo."""
    timestamp: str
    modo: str
    servidores_escaneados: int
    inventarios_detectados: List[Dict]
    resumen: Dict
    errores: List[str]


# =============================================================================
# FUNCIONES DE DETECCIÓN
# =============================================================================

def detectar_inventarios_soft(
    execute_sql_func,
    server: Dict,
    folios_procesados: List[Dict]
) -> List[InventarioDetectado]:
    """
    Detecta inventarios válidos en un servidor SoftRestaurant.
    
    Args:
        execute_sql_func: Función para ejecutar SQL
        server: Configuración del servidor (host, port, database, etc.)
        folios_procesados: Lista de folios ya procesados para comparar
    
    Returns:
        Lista de InventarioDetectado
    """
    from . import repository
    
    detectados = []
    
    try:
        # Query simplificada para obtener inventarios válidos recientes
        query = """
            WITH inventarios_validos AS (
                SELECT
                    i.folio,
                    i.fecha,
                    i.idalmacen1 AS almacen_id,
                    a.nombre AS almacen_nombre,
                    ROW_NUMBER() OVER (
                        PARTITION BY i.idalmacen1, CONVERT(date, i.fecha)
                        ORDER BY i.folio DESC, i.fecha DESC
                    ) AS rn_dia
                FROM invfisico i
                LEFT JOIN almacen a ON a.idalmacen = i.idalmacen1
                WHERE i.cancelado = 0
                  AND i.fecha >= DATEADD(MONTH, -2, GETDATE())
            )
            SELECT folio, fecha, almacen_id, almacen_nombre
            FROM inventarios_validos
            WHERE rn_dia = 1
            ORDER BY fecha DESC
        """
        
        result = execute_sql_func(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        
        if not result:
            logger.info(f"SOFT {server['name']}: Sin inventarios recientes")
            return detectados
        
        for inv in result:
            folio = str(inv['folio'])
            fecha_inv = inv['fecha']
            almacen_id = str(inv['almacen_id']) if inv['almacen_id'] else ''
            
            # Convertir fecha a string ISO
            if isinstance(fecha_inv, datetime):
                fecha_str = fecha_inv.strftime('%Y-%m-%d')
                fecha_date = fecha_inv.date()
            elif isinstance(fecha_inv, date):
                fecha_str = fecha_inv.strftime('%Y-%m-%d')
                fecha_date = fecha_inv
            else:
                fecha_str = str(fecha_inv)[:10]
                fecha_date = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            # Verificar si ya procesado
            ya_procesado, registro = repository.verificar_ya_procesado(
                folios_procesados,
                sistema_origen='SOFTRESTAURANT',
                server_id=server['id'],
                sucursal_id='',
                almacen_id=almacen_id,
                comentario=None,
                folio_inventario=folio,
                fecha_inventario=fecha_date,
                estado_inventario_origen=None
            )
            
            # Calcular folio inicial (primer inventario del mes)
            folio_inicial, fecha_inicial = _calcular_inicial_soft(
                execute_sql_func, server, almacen_id, fecha_date
            )
            
            # Determinar acción sugerida
            if ya_procesado:
                accion = 'OMITIR'
                razon = 'Ya procesado anteriormente'
            elif not folio_inicial:
                accion = 'OMITIR'
                razon = 'No se encontró inventario inicial del mes'
            else:
                accion = 'PROCESAR'
                razon = None
            
            detectados.append(InventarioDetectado(
                sistema_origen='SOFTRESTAURANT',
                server_id=server['id'],
                sucursal_id='',
                almacen_id=almacen_id,
                comentario=None,
                folio_inventario=folio,
                fecha_inventario=fecha_str,
                estado_inventario_origen=None,
                ya_procesado=ya_procesado,
                accion_sugerida=accion,
                razon_omision=razon,
                folio_inicial_calculado=folio_inicial,
                fecha_inicial_calculada=fecha_inicial,
                almacen_nombre=inv.get('almacen_nombre')
            ))
        
        logger.info(f"SOFT {server['name']}: {len(detectados)} inventarios detectados")
        return detectados
        
    except Exception as e:
        logger.error(f"Error detectando en SOFT {server['name']}: {e}")
        return detectados


def _calcular_inicial_soft(
    execute_sql_func,
    server: Dict,
    almacen_id: str,
    fecha_final: date
) -> tuple:
    """
    Calcula el inventario inicial para SOFT (primer inv del mes).
    
    Returns:
        (folio_inicial, fecha_inicial) o (None, None) si no encuentra
    """
    try:
        inicio_mes = fecha_final.replace(day=1)
        inicio_mes_sig = (inicio_mes + relativedelta(months=1))
        
        query = f"""
            WITH inventarios_validos AS (
                SELECT
                    i.folio,
                    i.fecha,
                    ROW_NUMBER() OVER (
                        PARTITION BY CONVERT(date, i.fecha)
                        ORDER BY i.folio DESC, i.fecha DESC
                    ) AS rn_dia
                FROM invfisico i
                WHERE i.idalmacen1 = '{almacen_id}'
                  AND i.cancelado = 0
                  AND CONVERT(date, i.fecha) >= CONVERT(date, '{inicio_mes.strftime('%Y-%m-%d')}')
                  AND CONVERT(date, i.fecha) < CONVERT(date, '{inicio_mes_sig.strftime('%Y-%m-%d')}')
            )
            SELECT TOP 1 folio, fecha
            FROM inventarios_validos
            WHERE rn_dia = 1
            ORDER BY fecha ASC, folio ASC
        """
        
        result = execute_sql_func(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        
        if result and len(result) > 0:
            fecha_ini = result[0]['fecha']
            if isinstance(fecha_ini, datetime):
                fecha_ini_str = fecha_ini.strftime('%Y-%m-%d')
            elif isinstance(fecha_ini, date):
                fecha_ini_str = fecha_ini.strftime('%Y-%m-%d')
            else:
                fecha_ini_str = str(fecha_ini)[:10]
            
            return str(result[0]['folio']), fecha_ini_str
        
        return None, None
        
    except Exception as e:
        logger.error(f"Error calculando inicial SOFT: {e}")
        return None, None


def detectar_inventarios_mpro(
    execute_sql_func,
    server: Dict,
    folios_procesados: List[Dict]
) -> List[InventarioDetectado]:
    """
    Detecta inventarios válidos en un servidor MPRO.
    
    Args:
        execute_sql_func: Función para ejecutar SQL
        server: Configuración del servidor (host, port, database, etc.)
        folios_procesados: Lista de folios ya procesados para comparar
    
    Returns:
        Lista de InventarioDetectado
    """
    from . import repository
    
    detectados = []
    
    try:
        # Query para obtener inventarios automatizables (AC, AP)
        query = """
            SELECT DISTINCT
                F.Fi_Folio AS folio,
                F.Fi_Fecha AS fecha,
                F.Al_Cve_Almacen AS almacen_id,
                A.Al_Descripcion AS almacen_nombre,
                F.Sc_Cve_Sucursal AS sucursal_id,
                S.Sc_Descripcion AS sucursal_nombre,
                F.Fi_Comentario AS comentario,
                F.Es_Cve_Estado AS estado
            FROM Fisico F
            INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
            INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
            WHERE F.Es_Cve_Estado IN ('AC', 'AP')
              AND F.Fecha_Baja IS NULL
              AND F.Fi_Fecha >= DATEADD(MONTH, -2, GETDATE())
            GROUP BY 
                F.Fi_Folio, F.Fi_Fecha, 
                F.Al_Cve_Almacen, A.Al_Descripcion,
                F.Sc_Cve_Sucursal, S.Sc_Descripcion,
                F.Fi_Comentario, F.Es_Cve_Estado
            ORDER BY F.Fi_Fecha DESC
        """
        
        result = execute_sql_func(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        
        if not result:
            logger.info(f"MPRO {server['name']}: Sin inventarios recientes")
            return detectados
        
        for inv in result:
            folio = str(inv['folio'])
            fecha_inv = inv['fecha']
            almacen_id = str(inv['almacen_id']) if inv['almacen_id'] else ''
            sucursal_id = str(inv['sucursal_id']) if inv['sucursal_id'] else ''
            comentario = inv.get('comentario') or None
            estado = inv.get('estado') or None
            
            # Convertir fecha a string ISO
            if isinstance(fecha_inv, datetime):
                fecha_str = fecha_inv.strftime('%Y-%m-%d')
                fecha_date = fecha_inv.date()
            elif isinstance(fecha_inv, date):
                fecha_str = fecha_inv.strftime('%Y-%m-%d')
                fecha_date = fecha_inv
            else:
                fecha_str = str(fecha_inv)[:10]
                fecha_date = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            # Verificar si ya procesado
            ya_procesado, registro = repository.verificar_ya_procesado(
                folios_procesados,
                sistema_origen='MPRO',
                server_id=server['id'],
                sucursal_id=sucursal_id,
                almacen_id=almacen_id,
                comentario=comentario,
                folio_inventario=folio,
                fecha_inventario=fecha_date,
                estado_inventario_origen=estado
            )
            
            # Calcular folio inicial (último inventario del mes anterior)
            folio_inicial, fecha_inicial = _calcular_inicial_mpro(
                execute_sql_func, server, almacen_id, sucursal_id, comentario, fecha_date
            )
            
            # Determinar acción sugerida
            if ya_procesado:
                accion = 'OMITIR'
                razon = f'Ya procesado en estado {estado}'
            elif not folio_inicial:
                accion = 'OMITIR'
                razon = 'No se encontró inventario inicial del mes anterior'
            else:
                accion = 'PROCESAR'
                razon = None
            
            detectados.append(InventarioDetectado(
                sistema_origen='MPRO',
                server_id=server['id'],
                sucursal_id=sucursal_id,
                almacen_id=almacen_id,
                comentario=comentario,
                folio_inventario=folio,
                fecha_inventario=fecha_str,
                estado_inventario_origen=estado,
                ya_procesado=ya_procesado,
                accion_sugerida=accion,
                razon_omision=razon,
                folio_inicial_calculado=folio_inicial,
                fecha_inicial_calculada=fecha_inicial,
                almacen_nombre=inv.get('almacen_nombre'),
                sucursal_nombre=inv.get('sucursal_nombre')
            ))
        
        logger.info(f"MPRO {server['name']}: {len(detectados)} inventarios detectados")
        return detectados
        
    except Exception as e:
        logger.error(f"Error detectando en MPRO {server['name']}: {e}")
        return detectados


def _calcular_inicial_mpro(
    execute_sql_func,
    server: Dict,
    almacen_id: str,
    sucursal_id: str,
    comentario: Optional[str],
    fecha_final: date
) -> tuple:
    """
    Calcula el inventario inicial para MPRO (último inv del mes anterior).
    
    Returns:
        (folio_inicial, fecha_inicial) o (None, None) si no encuentra
    """
    try:
        inicio_mes_actual = fecha_final.replace(day=1)
        inicio_mes_anterior = inicio_mes_actual - relativedelta(months=1)
        
        comentario_sql = comentario.replace("'", "''") if comentario else ""
        
        query = f"""
            WITH inventarios_validos AS (
                SELECT
                    F.Fi_Folio AS folio,
                    F.Fi_Fecha AS fecha,
                    ROW_NUMBER() OVER (
                        PARTITION BY CONVERT(date, F.Fi_Fecha)
                        ORDER BY 
                            CASE F.Es_Cve_Estado WHEN 'AP' THEN 1 WHEN 'AC' THEN 2 ELSE 3 END,
                            F.Fi_Folio DESC, 
                            F.Fi_Fecha DESC
                    ) AS rn_dia
                FROM Fisico F
                WHERE F.Al_Cve_Almacen = '{almacen_id}'
                  AND F.Sc_Cve_Sucursal = '{sucursal_id}'
                  AND ISNULL(F.Fi_Comentario, '') = '{comentario_sql}'
                  AND F.Es_Cve_Estado IN ('AC', 'AP')
                  AND F.Fecha_Baja IS NULL
                  AND CONVERT(date, F.Fi_Fecha) >= CONVERT(date, '{inicio_mes_anterior.strftime('%Y-%m-%d')}')
                  AND CONVERT(date, F.Fi_Fecha) < CONVERT(date, '{inicio_mes_actual.strftime('%Y-%m-%d')}')
            )
            SELECT TOP 1 folio, fecha
            FROM inventarios_validos
            WHERE rn_dia = 1
            ORDER BY fecha DESC, folio DESC
        """
        
        result = execute_sql_func(
            server['host'],
            server['port'],
            server['database'],
            server['username'],
            server['password'],
            query
        )
        
        if result and len(result) > 0:
            fecha_ini = result[0]['fecha']
            if isinstance(fecha_ini, datetime):
                fecha_ini_str = fecha_ini.strftime('%Y-%m-%d')
            elif isinstance(fecha_ini, date):
                fecha_ini_str = fecha_ini.strftime('%Y-%m-%d')
            else:
                fecha_ini_str = str(fecha_ini)[:10]
            
            return str(result[0]['folio']), fecha_ini_str
        
        return None, None
        
    except Exception as e:
        logger.error(f"Error calculando inicial MPRO: {e}")
        return None, None


# =============================================================================
# FUNCIÓN PRINCIPAL DRY-RUN
# =============================================================================

def ejecutar_dry_run(
    execute_sql_func,
    get_servers_func,
    edarsahub_config: Dict
) -> ResultadoDryRun:
    """
    Ejecuta detección completa en modo dry-run.
    
    Args:
        execute_sql_func: Función para ejecutar SQL
        get_servers_func: Función async para obtener servidores de MongoDB
        edarsahub_config: Configuración de conexión a EDARSAHUB
    
    Returns:
        ResultadoDryRun con todos los inventarios detectados
    """
    from . import repository
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    errores = []
    todos_detectados = []
    servidores_escaneados = 0
    
    try:
        # Obtener servidores activos
        servers = get_servers_func()
        
        for server in servers:
            if not server.get('active'):
                continue
            
            servidores_escaneados += 1
            system_type = server.get('system_type', '')
            
            # Obtener folios ya procesados para este servidor
            folios_procesados = repository.get_folios_ya_procesados(
                execute_sql_func,
                edarsahub_config['host'],
                edarsahub_config['port'],
                edarsahub_config['database'],
                edarsahub_config['username'],
                edarsahub_config['password'],
                sistema_origen='SOFTRESTAURANT' if system_type == 'SoftRestaurant' else 'MPRO',
                server_id=server['id']
            )
            
            # Detectar según tipo de sistema
            if system_type == 'SoftRestaurant':
                detectados = detectar_inventarios_soft(
                    execute_sql_func, server, folios_procesados
                )
                todos_detectados.extend([asdict(d) for d in detectados])
                
            elif system_type == 'MPRO':
                detectados = detectar_inventarios_mpro(
                    execute_sql_func, server, folios_procesados
                )
                todos_detectados.extend([asdict(d) for d in detectados])
    
    except Exception as e:
        errores.append(f"Error general: {str(e)}")
        logger.error(f"Error en dry-run: {e}")
    
    # Calcular resumen
    total = len(todos_detectados)
    a_procesar = len([d for d in todos_detectados if d['accion_sugerida'] == 'PROCESAR'])
    a_omitir = len([d for d in todos_detectados if d['accion_sugerida'] == 'OMITIR'])
    ya_procesados = len([d for d in todos_detectados if d['ya_procesado']])
    
    return ResultadoDryRun(
        timestamp=timestamp,
        modo='DRY_RUN',
        servidores_escaneados=servidores_escaneados,
        inventarios_detectados=todos_detectados,
        resumen={
            'total_detectados': total,
            'a_procesar': a_procesar,
            'a_omitir': a_omitir,
            'ya_procesados': ya_procesados
        },
        errores=errores
    )
