"""
EDARSA HUB - Sync Históricos: Sync de Ventas
=============================================
FASE SYNC-1: Funciones específicas para sincronización de ventas.

Este módulo contiene helpers y funciones utilitarias para el proceso
de sincronización de ventas históricas.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal

from core.utils.operational_window import (
    get_mexico_now,
    get_sync_operational_window,
    DEFAULT_VENTANA_INICIO_HORA,
    DEFAULT_VENTANA_FIN_HORA,
)

from .models import SyncRunConfig, SyncRunResult
from .service import SyncHistoricosService

logger = logging.getLogger(__name__)


def ejecutar_sync_ventas_dry_run(
    server_ids: Optional[List[str]] = None,
    dias_atras: int = 7,
    ventana_inicio_hora: int = DEFAULT_VENTANA_INICIO_HORA,
    ventana_fin_hora: int = DEFAULT_VENTANA_FIN_HORA,
) -> SyncRunResult:
    """
    Ejecuta sincronización de ventas en modo DRY-RUN.
    
    FASE SYNC-1: Modo obligatorio antes de escritura real.
    
    Args:
        server_ids: Lista de IDs de servidores (None = todos)
        dias_atras: Días a procesar desde hoy
        ventana_inicio_hora: Hora inicio de jornada (default 13)
        ventana_fin_hora: Hora fin de jornada (default 11)
    
    Returns:
        SyncRunResult con detalle del dry-run
    """
    logger.info(
        f"[SYNC-VENTAS] Iniciando DRY-RUN. "
        f"Servidores: {server_ids or 'TODOS'}, "
        f"Días: {dias_atras}, "
        f"Ventana: {ventana_inicio_hora}:00-{ventana_fin_hora}:00"
    )
    
    config = SyncRunConfig(
        server_ids=server_ids,
        dias_atras=dias_atras,
        ventana_inicio_hora=ventana_inicio_hora,
        ventana_fin_hora=ventana_fin_hora,
        dry_run=True  # OBLIGATORIO DRY-RUN
    )
    
    service = SyncHistoricosService()
    return service.sync_ventas_historicas(config)


def ejecutar_sync_ventas_real(
    server_ids: List[str],  # OBLIGATORIO especificar servidores
    dias_atras: int = 7,
    ventana_inicio_hora: int = DEFAULT_VENTANA_INICIO_HORA,
    ventana_fin_hora: int = DEFAULT_VENTANA_FIN_HORA,
) -> SyncRunResult:
    """
    Ejecuta sincronización de ventas con escritura real.
    
    FASE SYNC-1: Solo para servidores específicos después de dry-run exitoso.
    
    Args:
        server_ids: Lista de IDs de servidores (OBLIGATORIO)
        dias_atras: Días a procesar desde hoy
        ventana_inicio_hora: Hora inicio de jornada (default 13)
        ventana_fin_hora: Hora fin de jornada (default 11)
    
    Returns:
        SyncRunResult con detalle de la ejecución
    """
    if not server_ids:
        raise ValueError("Debe especificar server_ids para escritura real")
    
    logger.info(
        f"[SYNC-VENTAS] Iniciando ESCRITURA REAL. "
        f"Servidores: {server_ids}, "
        f"Días: {dias_atras}, "
        f"Ventana: {ventana_inicio_hora}:00-{ventana_fin_hora}:00"
    )
    
    config = SyncRunConfig(
        server_ids=server_ids,
        dias_atras=dias_atras,
        ventana_inicio_hora=ventana_inicio_hora,
        ventana_fin_hora=ventana_fin_hora,
        dry_run=False  # Escritura real
    )
    
    service = SyncHistoricosService()
    return service.sync_ventas_historicas(config)


def inicializar_tablas_sync() -> Dict[str, bool]:
    """
    Crea las tablas Sync_* en EDARSAHUB si no existen.
    
    Returns:
        Dict con resultado por tabla
    """
    service = SyncHistoricosService()
    return service.inicializar_infraestructura()


def verificar_estado_sync() -> Dict:
    """
    Verifica el estado de la infraestructura de sincronización.
    
    Returns:
        Dict con información de estado
    """
    from core.db import execute_sql_query
    from core.server_registry import EDARSAHUB_CONFIG
    
    estado = {
        'tablas_existentes': [],
        'tablas_faltantes': [],
        'ultimo_sync': None,
        'registros_sync_ventas': 0,
    }
    
    tablas_esperadas = [
        'Sync_Ventas_Historicas',
        'Sync_Ventas_PorHora',
        'Sync_Ventas_PorDiaSemana',
        'Sync_Control_Ejecuciones'
    ]
    
    try:
        for tabla in tablas_esperadas:
            query = f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{tabla}'"
            result = execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                query
            )
            if result:
                estado['tablas_existentes'].append(tabla)
            else:
                estado['tablas_faltantes'].append(tabla)
        
        # Contar registros si existe la tabla
        if 'Sync_Ventas_Historicas' in estado['tablas_existentes']:
            count = execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                "SELECT COUNT(*) as total FROM Sync_Ventas_Historicas"
            )
            estado['registros_sync_ventas'] = count[0]['total'] if count else 0
        
    except Exception as e:
        estado['error'] = str(e)
    
    return estado
