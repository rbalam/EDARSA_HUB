# -*- coding: utf-8 -*-
"""
Feature Flags - Automatización de Análisis de Inventarios
CAB-003 - Fase 0

REGLA: Todos los flags están APAGADOS por defecto.
No se activa ninguna funcionalidad hasta aprobación explícita.
"""

# =============================================================================
# FEATURE FLAGS - FASE 0: TODO APAGADO
# =============================================================================

FEATURE_FLAGS = {
    # Master switch - Control principal del módulo
    "AUTOMATIZACION_INVENTARIOS_ENABLED": False,
    
    # Scheduler - Detección automática de nuevos folios
    "SCHEDULER_ACTIVO": False,
    
    # Procesamiento - Generación de análisis
    "PROCESAMIENTO_ACTIVO": False,
    
    # Envíos - Email y WhatsApp
    "ENVIO_EMAIL_ACTIVO": False,
    "ENVIO_WHATSAPP_ACTIVO": False,
    
    # Conexiones a sistemas origen
    "CONEXION_SOFTRESTAURANT_ACTIVA": False,
    "CONEXION_MPRO_ACTIVA": False,
    
    # Tareas y justificaciones (Fase 1.5)
    "TAREAS_ACTIVAS": False,
    "JUSTIFICACIONES_ACTIVAS": False,
}


def is_enabled(flag_name: str) -> bool:
    """
    Verifica si un feature flag está habilitado.
    
    Args:
        flag_name: Nombre del flag a verificar
        
    Returns:
        bool: True si está habilitado, False en caso contrario
        
    Nota:
        En Fase 0, SIEMPRE retorna False para cualquier flag.
    """
    return FEATURE_FLAGS.get(flag_name, False)


def get_all_flags() -> dict:
    """
    Retorna el estado de todos los feature flags.
    
    Returns:
        dict: Copia del diccionario de flags
    """
    return FEATURE_FLAGS.copy()


def is_module_active() -> bool:
    """
    Verifica si el módulo principal está activo.
    
    Returns:
        bool: True si AUTOMATIZACION_INVENTARIOS_ENABLED está en True
        
    Nota:
        En Fase 0, SIEMPRE retorna False.
    """
    return FEATURE_FLAGS.get("AUTOMATIZACION_INVENTARIOS_ENABLED", False)
