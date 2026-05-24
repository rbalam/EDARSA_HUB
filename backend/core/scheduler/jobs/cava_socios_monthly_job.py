"""
EDARSA HUB - Cava de Socios Monthly Job
========================================
Job para envío automático mensual de estados de cuenta a socios activos.

Ejecución: Primer día de cada mes a las 9:00 AM
Acción: Envía estado de cuenta por email a todos los socios activos con email registrado.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


async def execute_cava_socios_monthly(db) -> Dict[str, Any]:
    """
    Ejecuta el envío mensual de estados de cuenta a socios activos.
    
    Args:
        db: Conexión (StubDatabase - no usado, conexión es SQL Server)
    
    Returns:
        Dict con resultados del envío masivo
    """
    from modules.cava_socios.service import get_cava_socios_service
    from modules.cava_socios.report_service import get_cava_report_service
    from modules.cava_socios.notification_service import get_notification_service
    
    inicio = datetime.now()
    
    cava_service = get_cava_socios_service()
    report_service = get_cava_report_service()
    notification_service = get_notification_service()
    
    # Obtener todas las empresas con módulo Cava activo
    # Por ahora usamos empresa hardcodeada (se puede expandir)
    empresas = ['d290f1ee-6c54-4b01-90e6-d701748f0851']
    
    total_enviados = 0
    total_fallidos = 0
    total_sin_email = 0
    detalles = []
    
    for empresa_id in empresas:
        try:
            # Listar socios activos
            result = cava_service.listar_socios(
                empresa_id=empresa_id, 
                estatus='ACTIVO',
                skip=0,
                limit=1000  # Max socios por empresa
            )
            
            socios = result.get('socios', [])
            logger.info(f"[CAVA_MONTHLY] Empresa {empresa_id}: {len(socios)} socios activos")
            
            for socio_resumen in socios:
                socio_id = socio_resumen.get('socio_id')
                email = socio_resumen.get('email')
                
                if not email:
                    total_sin_email += 1
                    continue
                
                try:
                    # Obtener datos completos del socio
                    socio = cava_service.obtener_socio(socio_id)
                    if not socio:
                        continue
                    
                    # Obtener cargos para el estado de cuenta
                    cargos = cava_service.obtener_cargos_socio(socio_id)
                    
                    # Generar PDF de estado de cuenta
                    pdf_bytes = report_service.generar_estado_cuenta(socio, cargos)
                    
                    # Enviar por email
                    resultado = notification_service.enviar_reporte_email(
                        socio=socio,
                        tipo_reporte='estado_cuenta',
                        pdf_bytes=pdf_bytes
                    )
                    
                    if resultado.get('success'):
                        total_enviados += 1
                        logger.debug(f"[CAVA_MONTHLY] Enviado a {email}")
                    else:
                        total_fallidos += 1
                        detalles.append({
                            'socio_id': socio_id,
                            'email': email,
                            'error': resultado.get('error')
                        })
                        
                except Exception as e:
                    total_fallidos += 1
                    logger.warning(f"[CAVA_MONTHLY] Error con socio {socio_id}: {e}")
                    detalles.append({
                        'socio_id': socio_id,
                        'error': str(e)
                    })
                    
        except Exception as e:
            logger.error(f"[CAVA_MONTHLY] Error empresa {empresa_id}: {e}")
    
    duracion_ms = int((datetime.now() - inicio).total_seconds() * 1000)
    
    resultado = {
        "estatus_general": "OK" if total_fallidos == 0 else "PARCIAL",
        "total_enviados": total_enviados,
        "total_fallidos": total_fallidos,
        "total_sin_email": total_sin_email,
        "duracion_ms": duracion_ms,
        "fecha_ejecucion": inicio.isoformat(),
        "errores": detalles[:10]  # Máximo 10 errores en log
    }
    
    logger.info(
        f"[CAVA_MONTHLY] Completado: {total_enviados} enviados, "
        f"{total_fallidos} fallidos, {total_sin_email} sin email, {duracion_ms}ms"
    )
    
    return resultado
