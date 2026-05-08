"""
SUBFASE 3.7 — Carga Histórica 24 meses Propinas TPV

Este script ejecuta la carga histórica de propinas TPV desde SoftRestaurant y MPRO
hacia EDARSAHUB, procesando mes por mes para evitar timeouts.

FUENTES AUTORIZADAS:
- SoftRestaurant: cheques.propinatarjeta
- MPRO: Comanda_Pago.Cp_Propina WHERE Forma_Pago.Fp_Tipo = '04'

DESTINO:
- EDARSAHUB.propinas_tpv_control
- EDARSAHUB.Finanzas_PropinasTPV_SyncLog

CARACTERÍSTICAS:
- Procesamiento por bloques mensuales
- Idempotente (HashOrigen)
- Tolerante a fallos por bloque
- SyncLog por bloque
- EsDemo=0 para datos reales
- NO usa MongoDB como fuente financiera

Autor: E1 Agent
Fecha: 1 Mayo 2026
Fase: Finanzas Fase 3 - Propinas TPV - Subfase 3.7
"""

import os
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Cargar variables de entorno
def _load_env():
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

# Unidades autorizadas
UNIDADES_SOFTRESTAURANT = ['130° MERIDA', 'CIENFUEGOS', 'LA ESTELAR']
UNIDADES_MPRO = ['130° QUERETARO', 'ORIGEN']


def generar_bloques_mensuales(meses_atras: int = 24) -> List[Dict]:
    """
    Genera lista de bloques mensuales para procesar.
    
    Args:
        meses_atras: Número de meses hacia atrás (default: 24)
        
    Returns:
        Lista de dicts con fecha_desde, fecha_hasta, año, mes
    """
    bloques = []
    ahora = datetime.now()
    
    for i in range(meses_atras, 0, -1):  # Del más antiguo al más reciente
        # Calcular inicio del mes
        fecha_ref = ahora - relativedelta(months=i)
        fecha_desde = datetime(fecha_ref.year, fecha_ref.month, 1)
        
        # Calcular fin del mes
        if fecha_ref.month == 12:
            fecha_hasta = datetime(fecha_ref.year + 1, 1, 1) - timedelta(seconds=1)
        else:
            fecha_hasta = datetime(fecha_ref.year, fecha_ref.month + 1, 1) - timedelta(seconds=1)
        
        bloques.append({
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'año': fecha_ref.year,
            'mes': fecha_ref.month,
            'periodo': f"{fecha_ref.year}-{fecha_ref.month:02d}"
        })
    
    return bloques


def ejecutar_carga_historica_unidad_sr(
    unidad_nombre: str,
    meses_atras: int = 24,
    continuar_desde_mes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta carga histórica para una unidad SoftRestaurant.
    
    Args:
        unidad_nombre: Nombre de la unidad
        meses_atras: Meses hacia atrás
        continuar_desde_mes: Formato 'YYYY-MM' para continuar desde un mes específico
        
    Returns:
        Dict con resultados consolidados
    """
    from modules.finanzas.sync_propinas_softrestaurant import sincronizar_propinas_softrestaurant
    
    logger.info(f"[CARGA_HISTORICA] Iniciando carga histórica SR: {unidad_nombre}")
    
    bloques = generar_bloques_mensuales(meses_atras)
    
    # Filtrar si se especifica continuar desde un mes
    if continuar_desde_mes:
        bloques = [b for b in bloques if b['periodo'] >= continuar_desde_mes]
    
    resultado = {
        'unidad': unidad_nombre,
        'sistema': 'SoftRestaurant',
        'meses_atras': meses_atras,
        'bloques_total': len(bloques),
        'bloques_exitosos': 0,
        'bloques_fallidos': 0,
        'bloques_sin_datos': 0,
        'total_registros_origen': 0,
        'total_insertados': 0,
        'total_actualizados': 0,
        'total_omitidos': 0,
        'total_errores': 0,
        'total_propinas_origen': 0.0,
        'fecha_min': None,
        'fecha_max': None,
        'detalle_bloques': [],
        'bloques_fallidos_lista': [],
        'inicio': datetime.now().isoformat(),
        'fin': None
    }
    
    for bloque in bloques:
        logger.info(f"[CARGA_HISTORICA] {unidad_nombre} - Procesando {bloque['periodo']}...")
        
        try:
            res = sincronizar_propinas_softrestaurant(
                unidad_nombre=unidad_nombre,
                fecha_desde=bloque['fecha_desde'],
                fecha_hasta=bloque['fecha_hasta']
            )
            
            stats = res.get('stats', {})
            
            detalle = {
                'periodo': bloque['periodo'],
                'fecha_desde': bloque['fecha_desde'].isoformat(),
                'fecha_hasta': bloque['fecha_hasta'].isoformat(),
                'estatus': res.get('estatus'),
                'registros_origen': res.get('registros_origen', 0),
                'suma_propinas_origen': res.get('suma_propinas_origen', 0),
                'insertados': stats.get('insertados', 0),
                'actualizados': stats.get('actualizados', 0),
                'omitidos': stats.get('omitidos', 0),
                'errores': stats.get('errores', 0),
                'error': res.get('error')
            }
            resultado['detalle_bloques'].append(detalle)
            
            if res.get('estatus') == 'SIN_DATOS':
                resultado['bloques_sin_datos'] += 1
            elif res.get('estatus') in ['COMPLETADO', 'PARCIAL']:
                resultado['bloques_exitosos'] += 1
                resultado['total_registros_origen'] += res.get('registros_origen', 0)
                resultado['total_insertados'] += stats.get('insertados', 0)
                resultado['total_actualizados'] += stats.get('actualizados', 0)
                resultado['total_omitidos'] += stats.get('omitidos', 0)
                resultado['total_propinas_origen'] += res.get('suma_propinas_origen', 0)
                
                # Actualizar fechas min/max
                if res.get('registros_origen', 0) > 0:
                    if resultado['fecha_min'] is None:
                        resultado['fecha_min'] = bloque['fecha_desde'].strftime('%Y-%m-%d')
                    resultado['fecha_max'] = bloque['fecha_hasta'].strftime('%Y-%m-%d')
            else:
                resultado['bloques_fallidos'] += 1
                resultado['bloques_fallidos_lista'].append({
                    'periodo': bloque['periodo'],
                    'error': res.get('error')
                })
                resultado['total_errores'] += stats.get('errores', 0)
                
        except Exception as e:
            logger.error(f"[CARGA_HISTORICA] Error en bloque {bloque['periodo']}: {e}")
            resultado['bloques_fallidos'] += 1
            resultado['bloques_fallidos_lista'].append({
                'periodo': bloque['periodo'],
                'error': str(e)
            })
            resultado['detalle_bloques'].append({
                'periodo': bloque['periodo'],
                'estatus': 'ERROR',
                'error': str(e)
            })
    
    resultado['fin'] = datetime.now().isoformat()
    
    # Determinar estatus general
    if resultado['bloques_fallidos'] == 0:
        resultado['estatus_general'] = 'COMPLETADO'
    elif resultado['bloques_exitosos'] > 0:
        resultado['estatus_general'] = 'PARCIAL'
    else:
        resultado['estatus_general'] = 'FALLIDO'
    
    logger.info(
        f"[CARGA_HISTORICA] {unidad_nombre} completado: "
        f"exitosos={resultado['bloques_exitosos']}/{resultado['bloques_total']}, "
        f"insertados={resultado['total_insertados']}, "
        f"propinas=${resultado['total_propinas_origen']:,.2f}"
    )
    
    return resultado


def ejecutar_carga_historica_unidad_mpro(
    unidad_nombre: str,
    meses_atras: int = 24,
    continuar_desde_mes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta carga histórica para una unidad MPRO.
    
    Args:
        unidad_nombre: Nombre de la unidad
        meses_atras: Meses hacia atrás
        continuar_desde_mes: Formato 'YYYY-MM' para continuar desde un mes específico
        
    Returns:
        Dict con resultados consolidados
    """
    from modules.finanzas.sync_propinas_mpro import sincronizar_propinas_mpro
    
    logger.info(f"[CARGA_HISTORICA] Iniciando carga histórica MPRO: {unidad_nombre}")
    
    bloques = generar_bloques_mensuales(meses_atras)
    
    if continuar_desde_mes:
        bloques = [b for b in bloques if b['periodo'] >= continuar_desde_mes]
    
    resultado = {
        'unidad': unidad_nombre,
        'sistema': 'MPRO',
        'meses_atras': meses_atras,
        'bloques_total': len(bloques),
        'bloques_exitosos': 0,
        'bloques_fallidos': 0,
        'bloques_sin_datos': 0,
        'total_registros_origen': 0,
        'total_insertados': 0,
        'total_actualizados': 0,
        'total_omitidos': 0,
        'total_errores': 0,
        'total_propinas_origen': 0.0,
        'fecha_min': None,
        'fecha_max': None,
        'detalle_bloques': [],
        'bloques_fallidos_lista': [],
        'formas_pago_acumuladas': {},
        'inicio': datetime.now().isoformat(),
        'fin': None
    }
    
    for bloque in bloques:
        logger.info(f"[CARGA_HISTORICA] {unidad_nombre} - Procesando {bloque['periodo']}...")
        
        try:
            res = sincronizar_propinas_mpro(
                unidad_nombre=unidad_nombre,
                fecha_desde=bloque['fecha_desde'],
                fecha_hasta=bloque['fecha_hasta']
            )
            
            stats = res.get('stats', {})
            
            detalle = {
                'periodo': bloque['periodo'],
                'fecha_desde': bloque['fecha_desde'].isoformat(),
                'fecha_hasta': bloque['fecha_hasta'].isoformat(),
                'estatus': res.get('estatus'),
                'registros_origen': res.get('registros_origen', 0),
                'suma_propinas_origen': res.get('suma_propinas_origen', 0),
                'insertados': stats.get('insertados', 0),
                'actualizados': stats.get('actualizados', 0),
                'omitidos': stats.get('omitidos', 0),
                'errores': stats.get('errores', 0),
                'formas_pago': res.get('formas_pago_detectadas', {}),
                'error': res.get('error')
            }
            resultado['detalle_bloques'].append(detalle)
            
            # Acumular formas de pago
            for fp, data in res.get('formas_pago_detectadas', {}).items():
                if fp not in resultado['formas_pago_acumuladas']:
                    resultado['formas_pago_acumuladas'][fp] = {'count': 0, 'total': 0.0}
                resultado['formas_pago_acumuladas'][fp]['count'] += data.get('count', 0)
                resultado['formas_pago_acumuladas'][fp]['total'] += data.get('total', 0)
            
            if res.get('estatus') == 'SIN_DATOS':
                resultado['bloques_sin_datos'] += 1
            elif res.get('estatus') in ['COMPLETADO', 'PARCIAL']:
                resultado['bloques_exitosos'] += 1
                resultado['total_registros_origen'] += res.get('registros_origen', 0)
                resultado['total_insertados'] += stats.get('insertados', 0)
                resultado['total_actualizados'] += stats.get('actualizados', 0)
                resultado['total_omitidos'] += stats.get('omitidos', 0)
                resultado['total_propinas_origen'] += res.get('suma_propinas_origen', 0)
                
                if res.get('registros_origen', 0) > 0:
                    if resultado['fecha_min'] is None:
                        resultado['fecha_min'] = bloque['fecha_desde'].strftime('%Y-%m-%d')
                    resultado['fecha_max'] = bloque['fecha_hasta'].strftime('%Y-%m-%d')
            else:
                resultado['bloques_fallidos'] += 1
                resultado['bloques_fallidos_lista'].append({
                    'periodo': bloque['periodo'],
                    'error': res.get('error')
                })
                resultado['total_errores'] += stats.get('errores', 0)
                
        except Exception as e:
            logger.error(f"[CARGA_HISTORICA] Error en bloque {bloque['periodo']}: {e}")
            resultado['bloques_fallidos'] += 1
            resultado['bloques_fallidos_lista'].append({
                'periodo': bloque['periodo'],
                'error': str(e)
            })
            resultado['detalle_bloques'].append({
                'periodo': bloque['periodo'],
                'estatus': 'ERROR',
                'error': str(e)
            })
    
    resultado['fin'] = datetime.now().isoformat()
    
    if resultado['bloques_fallidos'] == 0:
        resultado['estatus_general'] = 'COMPLETADO'
    elif resultado['bloques_exitosos'] > 0:
        resultado['estatus_general'] = 'PARCIAL'
    else:
        resultado['estatus_general'] = 'FALLIDO'
    
    logger.info(
        f"[CARGA_HISTORICA] {unidad_nombre} completado: "
        f"exitosos={resultado['bloques_exitosos']}/{resultado['bloques_total']}, "
        f"insertados={resultado['total_insertados']}, "
        f"propinas=${resultado['total_propinas_origen']:,.2f}"
    )
    
    return resultado


def ejecutar_carga_historica_completa(meses_atras: int = 24) -> Dict[str, Any]:
    """
    Ejecuta carga histórica completa para todas las unidades.
    
    Args:
        meses_atras: Meses hacia atrás (default: 24)
        
    Returns:
        Dict con resultados consolidados de todas las unidades
    """
    logger.info(f"[CARGA_HISTORICA] === INICIANDO CARGA HISTÓRICA {meses_atras} MESES ===")
    
    inicio_global = datetime.now()
    
    resultado = {
        'tipo': 'CARGA_HISTORICA_24M',
        'meses_atras': meses_atras,
        'inicio': inicio_global.isoformat(),
        'fin': None,
        'unidades_procesadas': 0,
        'unidades_exitosas': 0,
        'unidades_parciales': 0,
        'unidades_fallidas': 0,
        'total_registros_origen': 0,
        'total_insertados': 0,
        'total_actualizados': 0,
        'total_omitidos': 0,
        'total_errores': 0,
        'total_propinas_origen': 0.0,
        'por_sistema': {
            'SoftRestaurant': {
                'unidades': 0,
                'registros': 0,
                'insertados': 0,
                'propinas': 0.0
            },
            'MPRO': {
                'unidades': 0,
                'registros': 0,
                'insertados': 0,
                'propinas': 0.0
            }
        },
        'por_unidad': [],
        'errores': []
    }
    
    # Procesar SoftRestaurant
    for unidad in UNIDADES_SOFTRESTAURANT:
        try:
            res = ejecutar_carga_historica_unidad_sr(unidad, meses_atras)
            resultado['unidades_procesadas'] += 1
            resultado['por_unidad'].append(res)
            
            if res.get('estatus_general') == 'COMPLETADO':
                resultado['unidades_exitosas'] += 1
            elif res.get('estatus_general') == 'PARCIAL':
                resultado['unidades_parciales'] += 1
            else:
                resultado['unidades_fallidas'] += 1
            
            resultado['total_registros_origen'] += res.get('total_registros_origen', 0)
            resultado['total_insertados'] += res.get('total_insertados', 0)
            resultado['total_actualizados'] += res.get('total_actualizados', 0)
            resultado['total_omitidos'] += res.get('total_omitidos', 0)
            resultado['total_errores'] += res.get('total_errores', 0)
            resultado['total_propinas_origen'] += res.get('total_propinas_origen', 0)
            
            resultado['por_sistema']['SoftRestaurant']['unidades'] += 1
            resultado['por_sistema']['SoftRestaurant']['registros'] += res.get('total_registros_origen', 0)
            resultado['por_sistema']['SoftRestaurant']['insertados'] += res.get('total_insertados', 0)
            resultado['por_sistema']['SoftRestaurant']['propinas'] += res.get('total_propinas_origen', 0)
            
        except Exception as e:
            logger.error(f"[CARGA_HISTORICA] Error procesando {unidad}: {e}")
            resultado['unidades_fallidas'] += 1
            resultado['errores'].append(f"{unidad}: {str(e)}")
    
    # Procesar MPRO
    for unidad in UNIDADES_MPRO:
        try:
            res = ejecutar_carga_historica_unidad_mpro(unidad, meses_atras)
            resultado['unidades_procesadas'] += 1
            resultado['por_unidad'].append(res)
            
            if res.get('estatus_general') == 'COMPLETADO':
                resultado['unidades_exitosas'] += 1
            elif res.get('estatus_general') == 'PARCIAL':
                resultado['unidades_parciales'] += 1
            else:
                resultado['unidades_fallidas'] += 1
            
            resultado['total_registros_origen'] += res.get('total_registros_origen', 0)
            resultado['total_insertados'] += res.get('total_insertados', 0)
            resultado['total_actualizados'] += res.get('total_actualizados', 0)
            resultado['total_omitidos'] += res.get('total_omitidos', 0)
            resultado['total_errores'] += res.get('total_errores', 0)
            resultado['total_propinas_origen'] += res.get('total_propinas_origen', 0)
            
            resultado['por_sistema']['MPRO']['unidades'] += 1
            resultado['por_sistema']['MPRO']['registros'] += res.get('total_registros_origen', 0)
            resultado['por_sistema']['MPRO']['insertados'] += res.get('total_insertados', 0)
            resultado['por_sistema']['MPRO']['propinas'] += res.get('total_propinas_origen', 0)
            
        except Exception as e:
            logger.error(f"[CARGA_HISTORICA] Error procesando {unidad}: {e}")
            resultado['unidades_fallidas'] += 1
            resultado['errores'].append(f"{unidad}: {str(e)}")
    
    resultado['fin'] = datetime.now().isoformat()
    duracion = (datetime.now() - inicio_global).total_seconds()
    resultado['duracion_segundos'] = duracion
    
    # Determinar estatus general
    if resultado['unidades_fallidas'] == 0 and resultado['unidades_parciales'] == 0:
        resultado['estatus_general'] = 'COMPLETADO'
    elif resultado['unidades_exitosas'] > 0 or resultado['unidades_parciales'] > 0:
        resultado['estatus_general'] = 'PARCIAL'
    else:
        resultado['estatus_general'] = 'FALLIDO'
    
    logger.info(
        f"[CARGA_HISTORICA] === CARGA HISTÓRICA FINALIZADA ===\n"
        f"  Unidades: {resultado['unidades_exitosas']}/{resultado['unidades_procesadas']} exitosas\n"
        f"  Registros: {resultado['total_registros_origen']} origen, {resultado['total_insertados']} insertados\n"
        f"  Propinas: ${resultado['total_propinas_origen']:,.2f}\n"
        f"  Duración: {duracion:.0f} segundos"
    )
    
    return resultado


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'generar_bloques_mensuales',
    'ejecutar_carga_historica_unidad_sr',
    'ejecutar_carga_historica_unidad_mpro',
    'ejecutar_carga_historica_completa'
]
