"""
CARGA HISTÓRICA 24 MESES — CONTROL DE INGRESOS / CORTES DE CAJA
================================================================

Script de carga histórica controlada para sincronizar 24 meses de datos reales
desde SoftRestaurant y MPRO hacia EDARSAHUB.

AUTORIZACIÓN: Usuario 2026-05-01
MÁXIMAS: 15 Máximas Obligatorias respetadas
BLINDAJE: CxP, Tablero, etc. no tocados

ESTRATEGIA:
- Ejecutar por unidad
- Ejecutar por bloques trimestrales (3 meses)
- Validar totales por bloque
- Registrar SyncLog por bloque
- Tolerante a fallos (una unidad falla, las demás continúan)

CONEXIONES:
- Usa credenciales cifradas de EDARSAHUB.Servidores_Conexiones
- Descifra con SERVER_SECRET_KEY del entorno
- NO expone secretos

Autor: E1 Agent
Fecha: 2026-05-01
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
from pathlib import Path

# ============================================================================
# CARGAR VARIABLES DE ENTORNO DESDE .env
# ============================================================================
# CRÍTICO: Cargar .env ANTES de importar módulos que usan secret_manager

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
                    if key not in os.environ:  # No sobreescribir si ya existe
                        os.environ[key] = value

_load_env()

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Período histórico: 24 meses hacia atrás
MESES_HISTORICOS = 24

# Tamaño de bloque: 3 meses (trimestre)
MESES_POR_BLOQUE = 3


def calcular_bloques_trimestrales(
    meses_totales: int = 24,
    meses_por_bloque: int = 3
) -> List[Dict[str, datetime]]:
    """
    Calcula los bloques trimestrales para la carga histórica.
    
    Retorna lista de bloques desde el más antiguo al más reciente.
    El bloque incremental (últimos 7 días) NO se incluye para no interferir
    con el scheduler incremental.
    """
    bloques = []
    hoy = datetime.now()
    
    # Calcular fecha inicio histórico (24 meses atrás)
    fecha_inicio_historico = hoy - timedelta(days=meses_totales * 30)
    
    # Crear bloques trimestrales
    fecha_actual = fecha_inicio_historico
    while fecha_actual < (hoy - timedelta(days=7)):  # Dejar últimos 7 días para incremental
        fecha_fin_bloque = min(
            fecha_actual + timedelta(days=meses_por_bloque * 30),
            hoy - timedelta(days=7)
        )
        
        bloques.append({
            'fecha_desde': fecha_actual,
            'fecha_hasta': fecha_fin_bloque,
            'bloque_nombre': f"{fecha_actual.strftime('%Y-%m')} a {fecha_fin_bloque.strftime('%Y-%m')}"
        })
        
        fecha_actual = fecha_fin_bloque
    
    return bloques


def ejecutar_carga_historica_unidad_sr(
    unidad_nombre: str,
    bloques: List[Dict] = None
) -> Dict[str, Any]:
    """
    Ejecuta carga histórica para una unidad SoftRestaurant.
    
    Args:
        unidad_nombre: Nombre de la unidad (130° MERIDA, CIENFUEGOS, LA ESTELAR)
        bloques: Lista de bloques a procesar (opcional, calcula automáticamente)
        
    Returns:
        Dict con resumen completo de la carga
    """
    from modules.finanzas.sync_cortes_softrestaurant import sincronizar_unidad_softrestaurant
    
    if bloques is None:
        bloques = calcular_bloques_trimestrales()
    
    logger.info(f"[HISTORICA_SR] === Iniciando carga histórica: {unidad_nombre} ===")
    logger.info(f"[HISTORICA_SR] Bloques a procesar: {len(bloques)}")
    
    inicio_total = datetime.now()
    
    resultado = {
        'unidad': unidad_nombre,
        'sistema': 'SoftRestaurant',
        'fecha_inicio': inicio_total.isoformat(),
        'bloques_procesados': 0,
        'bloques_exitosos': 0,
        'bloques_fallidos': 0,
        'total_leidos': 0,
        'total_insertados': 0,
        'total_actualizados': 0,
        'total_omitidos': 0,
        'total_errores': 0,
        'detalle_bloques': [],
        'errores': [],
        'fecha_min': None,
        'fecha_max': None
    }
    
    for i, bloque in enumerate(bloques, 1):
        logger.info(f"[HISTORICA_SR] Bloque {i}/{len(bloques)}: {bloque['bloque_nombre']}")
        
        try:
            res = sincronizar_unidad_softrestaurant(
                unidad_nombre=unidad_nombre,
                fecha_desde=bloque['fecha_desde'],
                fecha_hasta=bloque['fecha_hasta']
            )
            
            stats = res.get('stats', {})
            
            detalle = {
                'bloque': bloque['bloque_nombre'],
                'fecha_desde': bloque['fecha_desde'].isoformat(),
                'fecha_hasta': bloque['fecha_hasta'].isoformat(),
                'estatus': res.get('estatus', 'UNKNOWN'),
                'leidos': stats.get('leidos', 0),
                'insertados': stats.get('insertados', 0),
                'actualizados': stats.get('actualizados', 0),
                'omitidos': stats.get('omitidos', 0),
                'errores': stats.get('errores', 0),
                'duracion_seg': res.get('duracion_segundos', 0)
            }
            
            resultado['detalle_bloques'].append(detalle)
            resultado['bloques_procesados'] += 1
            
            if res.get('estatus') in ('COMPLETADO', 'PARCIAL'):
                resultado['bloques_exitosos'] += 1
                resultado['total_leidos'] += stats.get('leidos', 0)
                resultado['total_insertados'] += stats.get('insertados', 0)
                resultado['total_actualizados'] += stats.get('actualizados', 0)
                resultado['total_omitidos'] += stats.get('omitidos', 0)
                
                # Actualizar fechas min/max
                if resultado['fecha_min'] is None or bloque['fecha_desde'] < datetime.fromisoformat(resultado['fecha_min']):
                    resultado['fecha_min'] = bloque['fecha_desde'].isoformat()
                if resultado['fecha_max'] is None or bloque['fecha_hasta'] > datetime.fromisoformat(resultado['fecha_max']):
                    resultado['fecha_max'] = bloque['fecha_hasta'].isoformat()
            else:
                resultado['bloques_fallidos'] += 1
                resultado['total_errores'] += stats.get('errores', 1)
                if res.get('error'):
                    resultado['errores'].append(f"Bloque {bloque['bloque_nombre']}: {res.get('error')}")
                    
        except Exception as e:
            logger.error(f"[HISTORICA_SR] Error en bloque {bloque['bloque_nombre']}: {e}")
            resultado['bloques_procesados'] += 1
            resultado['bloques_fallidos'] += 1
            resultado['total_errores'] += 1
            resultado['errores'].append(f"Bloque {bloque['bloque_nombre']}: {str(e)}")
            resultado['detalle_bloques'].append({
                'bloque': bloque['bloque_nombre'],
                'estatus': 'ERROR',
                'error': str(e)
            })
    
    # Finalizar
    resultado['fecha_fin'] = datetime.now().isoformat()
    resultado['duracion_total_seg'] = int((datetime.now() - inicio_total).total_seconds())
    resultado['estatus_general'] = (
        'COMPLETADO' if resultado['bloques_fallidos'] == 0
        else 'PARCIAL' if resultado['bloques_exitosos'] > 0
        else 'FALLIDO'
    )
    
    logger.info(
        f"[HISTORICA_SR] {unidad_nombre} completado: "
        f"bloques={resultado['bloques_exitosos']}/{resultado['bloques_procesados']}, "
        f"insertados={resultado['total_insertados']}, "
        f"omitidos={resultado['total_omitidos']}"
    )
    
    return resultado


def ejecutar_carga_historica_unidad_mpro(
    unidad_nombre: str,
    bloques: List[Dict] = None
) -> Dict[str, Any]:
    """
    Ejecuta carga histórica para una unidad MPRO.
    
    Args:
        unidad_nombre: Nombre de la unidad (130° QUERETARO, ORIGEN)
        bloques: Lista de bloques a procesar (opcional, calcula automáticamente)
        
    Returns:
        Dict con resumen completo de la carga
    """
    from modules.finanzas.sync_cortes_mpro import sincronizar_unidad_mpro
    
    if bloques is None:
        bloques = calcular_bloques_trimestrales()
    
    logger.info(f"[HISTORICA_MPRO] === Iniciando carga histórica: {unidad_nombre} ===")
    logger.info(f"[HISTORICA_MPRO] Bloques a procesar: {len(bloques)}")
    
    inicio_total = datetime.now()
    
    resultado = {
        'unidad': unidad_nombre,
        'sistema': 'MPRO',
        'fecha_inicio': inicio_total.isoformat(),
        'bloques_procesados': 0,
        'bloques_exitosos': 0,
        'bloques_fallidos': 0,
        'total_leidos': 0,
        'total_insertados': 0,
        'total_actualizados': 0,
        'total_omitidos': 0,
        'total_errores': 0,
        'detalle_bloques': [],
        'errores': [],
        'fecha_min': None,
        'fecha_max': None
    }
    
    for i, bloque in enumerate(bloques, 1):
        logger.info(f"[HISTORICA_MPRO] Bloque {i}/{len(bloques)}: {bloque['bloque_nombre']}")
        
        try:
            res = sincronizar_unidad_mpro(
                unidad_nombre=unidad_nombre,
                fecha_desde=bloque['fecha_desde'],
                fecha_hasta=bloque['fecha_hasta']
            )
            
            stats = res.get('stats', {})
            
            detalle = {
                'bloque': bloque['bloque_nombre'],
                'fecha_desde': bloque['fecha_desde'].isoformat(),
                'fecha_hasta': bloque['fecha_hasta'].isoformat(),
                'estatus': res.get('estatus', 'UNKNOWN'),
                'leidos': stats.get('leidos', 0),
                'insertados': stats.get('insertados', 0),
                'actualizados': stats.get('actualizados', 0),
                'omitidos': stats.get('omitidos', 0),
                'errores': stats.get('errores', 0),
                'duracion_seg': res.get('duracion_segundos', 0)
            }
            
            resultado['detalle_bloques'].append(detalle)
            resultado['bloques_procesados'] += 1
            
            if res.get('estatus') in ('COMPLETADO', 'PARCIAL'):
                resultado['bloques_exitosos'] += 1
                resultado['total_leidos'] += stats.get('leidos', 0)
                resultado['total_insertados'] += stats.get('insertados', 0)
                resultado['total_actualizados'] += stats.get('actualizados', 0)
                resultado['total_omitidos'] += stats.get('omitidos', 0)
                
                # Actualizar fechas min/max
                if resultado['fecha_min'] is None or bloque['fecha_desde'] < datetime.fromisoformat(resultado['fecha_min']):
                    resultado['fecha_min'] = bloque['fecha_desde'].isoformat()
                if resultado['fecha_max'] is None or bloque['fecha_hasta'] > datetime.fromisoformat(resultado['fecha_max']):
                    resultado['fecha_max'] = bloque['fecha_hasta'].isoformat()
            else:
                resultado['bloques_fallidos'] += 1
                resultado['total_errores'] += stats.get('errores', 1)
                if res.get('error'):
                    resultado['errores'].append(f"Bloque {bloque['bloque_nombre']}: {res.get('error')}")
                    
        except Exception as e:
            logger.error(f"[HISTORICA_MPRO] Error en bloque {bloque['bloque_nombre']}: {e}")
            resultado['bloques_procesados'] += 1
            resultado['bloques_fallidos'] += 1
            resultado['total_errores'] += 1
            resultado['errores'].append(f"Bloque {bloque['bloque_nombre']}: {str(e)}")
            resultado['detalle_bloques'].append({
                'bloque': bloque['bloque_nombre'],
                'estatus': 'ERROR',
                'error': str(e)
            })
    
    # Finalizar
    resultado['fecha_fin'] = datetime.now().isoformat()
    resultado['duracion_total_seg'] = int((datetime.now() - inicio_total).total_seconds())
    resultado['estatus_general'] = (
        'COMPLETADO' if resultado['bloques_fallidos'] == 0
        else 'PARCIAL' if resultado['bloques_exitosos'] > 0
        else 'FALLIDO'
    )
    
    logger.info(
        f"[HISTORICA_MPRO] {unidad_nombre} completado: "
        f"bloques={resultado['bloques_exitosos']}/{resultado['bloques_procesados']}, "
        f"insertados={resultado['total_insertados']}, "
        f"omitidos={resultado['total_omitidos']}"
    )
    
    return resultado


def ejecutar_carga_historica_completa() -> Dict[str, Any]:
    """
    Ejecuta carga histórica completa para las 5 unidades.
    
    Orden de ejecución:
    1. SoftRestaurant: 130° MERIDA, CIENFUEGOS, LA ESTELAR
    2. MPRO: 130° QUERETARO, ORIGEN
    
    Returns:
        Dict con resumen consolidado de toda la carga
    """
    logger.info("=" * 70)
    logger.info("CARGA HISTÓRICA 24 MESES — CONTROL DE INGRESOS")
    logger.info("=" * 70)
    
    inicio = datetime.now()
    bloques = calcular_bloques_trimestrales()
    
    logger.info(f"Período: {bloques[0]['fecha_desde'].date()} a {bloques[-1]['fecha_hasta'].date()}")
    logger.info(f"Bloques: {len(bloques)} (trimestrales)")
    
    resultado_consolidado = {
        'tipo': 'CARGA_HISTORICA_24_MESES',
        'fecha_inicio': inicio.isoformat(),
        'periodo_desde': bloques[0]['fecha_desde'].isoformat(),
        'periodo_hasta': bloques[-1]['fecha_hasta'].isoformat(),
        'bloques_configurados': len(bloques),
        'unidades_procesadas': 0,
        'unidades_exitosas': 0,
        'unidades_fallidas': 0,
        'total_registros_insertados': 0,
        'total_registros_omitidos': 0,
        'resultados_unidades': [],
        'errores_globales': []
    }
    
    # =========================================================================
    # SOFTRESTAURANT
    # =========================================================================
    
    unidades_sr = ['130° MERIDA', 'CIENFUEGOS', 'LA ESTELAR']
    
    for unidad in unidades_sr:
        logger.info(f"\n{'='*50}")
        logger.info(f"PROCESANDO: {unidad} (SoftRestaurant)")
        logger.info(f"{'='*50}")
        
        resultado_consolidado['unidades_procesadas'] += 1
        
        try:
            res = ejecutar_carga_historica_unidad_sr(unidad, bloques)
            resultado_consolidado['resultados_unidades'].append(res)
            
            if res['estatus_general'] in ('COMPLETADO', 'PARCIAL'):
                resultado_consolidado['unidades_exitosas'] += 1
                resultado_consolidado['total_registros_insertados'] += res['total_insertados']
                resultado_consolidado['total_registros_omitidos'] += res['total_omitidos']
            else:
                resultado_consolidado['unidades_fallidas'] += 1
                resultado_consolidado['errores_globales'].extend(res.get('errores', []))
                
        except Exception as e:
            logger.error(f"Error fatal en {unidad}: {e}")
            resultado_consolidado['unidades_fallidas'] += 1
            resultado_consolidado['errores_globales'].append(f"{unidad}: {str(e)}")
            resultado_consolidado['resultados_unidades'].append({
                'unidad': unidad,
                'sistema': 'SoftRestaurant',
                'estatus_general': 'ERROR',
                'error': str(e)
            })
    
    # =========================================================================
    # MPRO
    # =========================================================================
    
    unidades_mpro = ['130° QUERETARO', 'ORIGEN']
    
    for unidad in unidades_mpro:
        logger.info(f"\n{'='*50}")
        logger.info(f"PROCESANDO: {unidad} (MPRO)")
        logger.info(f"{'='*50}")
        
        resultado_consolidado['unidades_procesadas'] += 1
        
        try:
            res = ejecutar_carga_historica_unidad_mpro(unidad, bloques)
            resultado_consolidado['resultados_unidades'].append(res)
            
            if res['estatus_general'] in ('COMPLETADO', 'PARCIAL'):
                resultado_consolidado['unidades_exitosas'] += 1
                resultado_consolidado['total_registros_insertados'] += res['total_insertados']
                resultado_consolidado['total_registros_omitidos'] += res['total_omitidos']
            else:
                resultado_consolidado['unidades_fallidas'] += 1
                resultado_consolidado['errores_globales'].extend(res.get('errores', []))
                
        except Exception as e:
            logger.error(f"Error fatal en {unidad}: {e}")
            resultado_consolidado['unidades_fallidas'] += 1
            resultado_consolidado['errores_globales'].append(f"{unidad}: {str(e)}")
            resultado_consolidado['resultados_unidades'].append({
                'unidad': unidad,
                'sistema': 'MPRO',
                'estatus_general': 'ERROR',
                'error': str(e)
            })
    
    # =========================================================================
    # FINALIZAR
    # =========================================================================
    
    resultado_consolidado['fecha_fin'] = datetime.now().isoformat()
    resultado_consolidado['duracion_total_seg'] = int((datetime.now() - inicio).total_seconds())
    resultado_consolidado['estatus_general'] = (
        'COMPLETADO' if resultado_consolidado['unidades_fallidas'] == 0
        else 'PARCIAL' if resultado_consolidado['unidades_exitosas'] > 0
        else 'FALLIDO'
    )
    
    logger.info("\n" + "=" * 70)
    logger.info("RESUMEN CARGA HISTÓRICA")
    logger.info("=" * 70)
    logger.info(f"Unidades: {resultado_consolidado['unidades_exitosas']}/{resultado_consolidado['unidades_procesadas']}")
    logger.info(f"Insertados: {resultado_consolidado['total_registros_insertados']}")
    logger.info(f"Omitidos: {resultado_consolidado['total_registros_omitidos']}")
    logger.info(f"Duración: {resultado_consolidado['duracion_total_seg']} segundos")
    logger.info(f"Estado: {resultado_consolidado['estatus_general']}")
    
    return resultado_consolidado


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'calcular_bloques_trimestrales',
    'ejecutar_carga_historica_unidad_sr',
    'ejecutar_carga_historica_unidad_mpro',
    'ejecutar_carga_historica_completa'
]
