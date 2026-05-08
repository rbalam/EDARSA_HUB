#!/usr/bin/env python3
"""
Script de carga histórica con persistencia de progreso.
Ejecutar con: python carga_historica_runner.py
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Setup
sys.path.insert(0, '/app/backend')

# Cargar .env
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

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/carga_historica_progress.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROGRESS_FILE = '/tmp/carga_historica_progress.json'


def load_progress():
    """Carga el progreso guardado."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {
        'unidades_completadas': [],
        'unidad_actual': None,
        'mes_actual': None,
        'resultados': {},
        'inicio': datetime.now().isoformat(),
        'ultimo_update': None
    }


def save_progress(progress):
    """Guarda el progreso."""
    progress['ultimo_update'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2, default=str)


def generar_meses(meses_atras=24):
    """Genera lista de meses a procesar."""
    ahora = datetime.now()
    meses = []
    for i in range(meses_atras, 0, -1):
        fecha_ref = ahora - relativedelta(months=i)
        meses.append(f"{fecha_ref.year}-{fecha_ref.month:02d}")
    return meses


def procesar_mes_sr(unidad, periodo):
    """Procesa un mes para SoftRestaurant."""
    from modules.finanzas.sync_propinas_softrestaurant import sincronizar_propinas_softrestaurant
    
    year, month = map(int, periodo.split('-'))
    fecha_desde = datetime(year, month, 1)
    if month == 12:
        fecha_hasta = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        fecha_hasta = datetime(year, month + 1, 1) - timedelta(seconds=1)
    
    logger.info(f"Procesando {unidad} - {periodo}")
    
    try:
        resultado = sincronizar_propinas_softrestaurant(
            unidad_nombre=unidad,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )
        return {
            'periodo': periodo,
            'estatus': resultado.get('estatus'),
            'registros_origen': resultado.get('registros_origen', 0),
            'insertados': resultado.get('stats', {}).get('insertados', 0),
            'omitidos': resultado.get('stats', {}).get('omitidos', 0),
            'propinas': resultado.get('suma_propinas_origen', 0),
            'error': resultado.get('error')
        }
    except Exception as e:
        logger.error(f"Error en {unidad} - {periodo}: {e}")
        return {
            'periodo': periodo,
            'estatus': 'ERROR',
            'error': str(e)
        }


def procesar_mes_mpro(unidad, periodo):
    """Procesa un mes para MPRO."""
    from modules.finanzas.sync_propinas_mpro import sincronizar_propinas_mpro
    
    year, month = map(int, periodo.split('-'))
    fecha_desde = datetime(year, month, 1)
    if month == 12:
        fecha_hasta = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        fecha_hasta = datetime(year, month + 1, 1) - timedelta(seconds=1)
    
    logger.info(f"Procesando {unidad} - {periodo}")
    
    try:
        resultado = sincronizar_propinas_mpro(
            unidad_nombre=unidad,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )
        return {
            'periodo': periodo,
            'estatus': resultado.get('estatus'),
            'registros_origen': resultado.get('registros_origen', 0),
            'insertados': resultado.get('stats', {}).get('insertados', 0),
            'omitidos': resultado.get('stats', {}).get('omitidos', 0),
            'propinas': resultado.get('suma_propinas_origen', 0),
            'error': resultado.get('error')
        }
    except Exception as e:
        logger.error(f"Error en {unidad} - {periodo}: {e}")
        return {
            'periodo': periodo,
            'estatus': 'ERROR',
            'error': str(e)
        }


def main():
    logger.info("="*70)
    logger.info("CARGA HISTÓRICA 24 MESES - PROPINAS TPV")
    logger.info("="*70)
    
    progress = load_progress()
    
    # Unidades a procesar (las que necesitan carga histórica)
    unidades = [
        {'nombre': 'LA ESTELAR', 'sistema': 'SR', 'meses': 10},  # Jul 2025+
        {'nombre': '130° QUERETARO', 'sistema': 'MPRO', 'meses': 24},
        {'nombre': 'ORIGEN', 'sistema': 'MPRO', 'meses': 24}
    ]
    
    for unidad in unidades:
        nombre = unidad['nombre']
        
        if nombre in progress['unidades_completadas']:
            logger.info(f"SKIP {nombre} - ya completada")
            continue
        
        logger.info(f"\n{'='*70}")
        logger.info(f"PROCESANDO: {nombre} ({unidad['sistema']})")
        logger.info(f"{'='*70}")
        
        if nombre not in progress['resultados']:
            progress['resultados'][nombre] = {
                'sistema': unidad['sistema'],
                'meses_procesados': [],
                'total_insertados': 0,
                'total_omitidos': 0,
                'total_propinas': 0,
                'errores': []
            }
        
        meses = generar_meses(unidad['meses'])
        meses_procesados = progress['resultados'][nombre]['meses_procesados']
        
        for periodo in meses:
            if periodo in [m['periodo'] for m in meses_procesados]:
                logger.info(f"SKIP {periodo} - ya procesado")
                continue
            
            progress['unidad_actual'] = nombre
            progress['mes_actual'] = periodo
            save_progress(progress)
            
            if unidad['sistema'] == 'SR':
                resultado = procesar_mes_sr(nombre, periodo)
            else:
                resultado = procesar_mes_mpro(nombre, periodo)
            
            meses_procesados.append(resultado)
            
            if resultado.get('estatus') not in ['ERROR']:
                progress['resultados'][nombre]['total_insertados'] += resultado.get('insertados', 0)
                progress['resultados'][nombre]['total_omitidos'] += resultado.get('omitidos', 0)
                progress['resultados'][nombre]['total_propinas'] += resultado.get('propinas', 0)
            else:
                progress['resultados'][nombre]['errores'].append(resultado)
            
            save_progress(progress)
            logger.info(f"  -> {resultado.get('estatus')}: {resultado.get('insertados', 0)} insertados, {resultado.get('omitidos', 0)} omitidos")
            
            time.sleep(1)  # Pausa entre meses
        
        progress['unidades_completadas'].append(nombre)
        progress['unidad_actual'] = None
        progress['mes_actual'] = None
        save_progress(progress)
        
        logger.info(f"\n{nombre} COMPLETADA:")
        logger.info(f"  Insertados: {progress['resultados'][nombre]['total_insertados']}")
        logger.info(f"  Omitidos: {progress['resultados'][nombre]['total_omitidos']}")
        logger.info(f"  Propinas: ${progress['resultados'][nombre]['total_propinas']:,.2f}")
    
    progress['fin'] = datetime.now().isoformat()
    save_progress(progress)
    
    logger.info("\n" + "="*70)
    logger.info("CARGA HISTÓRICA FINALIZADA")
    logger.info("="*70)
    
    # Resumen
    total_insertados = sum(r['total_insertados'] for r in progress['resultados'].values())
    total_propinas = sum(r['total_propinas'] for r in progress['resultados'].values())
    
    logger.info(f"Total insertados: {total_insertados}")
    logger.info(f"Total propinas: ${total_propinas:,.2f}")


if __name__ == '__main__':
    main()
