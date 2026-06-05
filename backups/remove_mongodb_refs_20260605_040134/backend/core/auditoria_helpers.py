"""
EDARSA HUB - Helpers de Auditoría para Módulos Financieros
==========================================================
Funciones helper para integrar auditoría de forma no invasiva.

USO:
    from core.auditoria_helpers import registrar_auditoria_cxp, registrar_auditoria_tesoreria

    # En endpoint
    await registrar_auditoria_cxp(
        current_user=current_user,
        request=request,
        accion='EDIT',
        factura_id=factura_id,
        valor_anterior={'decision_pago': False},
        valor_nuevo={'decision_pago': True}
    )
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Flag para habilitar/deshabilitar auditoría (para rollback fácil)
AUDITORIA_HABILITADA = True


# =============================================================================
# HELPERS INTERNOS
# =============================================================================

def _get_auditoria_imports():
    """Lazy import del módulo de auditoría."""
    from core.auditoria import (
        servicio_auditoria, 
        AccionAuditoria, 
        ModuloAuditoria, 
        NivelRiesgo,
        ResultadoAuditoria,
        OrigenSistema
    )
    return {
        'servicio': servicio_auditoria,
        'AccionAuditoria': AccionAuditoria,
        'ModuloAuditoria': ModuloAuditoria,
        'NivelRiesgo': NivelRiesgo,
        'ResultadoAuditoria': ResultadoAuditoria,
        'OrigenSistema': OrigenSistema
    }


def _map_accion(accion_str: str, audit_module):
    """Mapea string de acción a enum."""
    mapping = {
        'VIEW': audit_module['AccionAuditoria'].VIEW,
        'EDIT': audit_module['AccionAuditoria'].EDIT,
        'CONFIRM': audit_module['AccionAuditoria'].CONFIRM,
        'AUTHORIZE': audit_module['AccionAuditoria'].AUTHORIZE
    }
    return mapping.get(accion_str, audit_module['AccionAuditoria'].EDIT)


def _map_resultado(resultado_str: str, audit_module):
    """Mapea string de resultado a enum."""
    if resultado_str in ['OK', 'ERROR', 'RECHAZADO']:
        return audit_module['ResultadoAuditoria'][resultado_str]
    return audit_module['ResultadoAuditoria'].OK


def _determinar_origen_factura(factura_id: str, audit_module):
    """Determina el origen del sistema basado en el ID de factura."""
    if factura_id:
        if factura_id.startswith('MPRO_'):
            return audit_module['OrigenSistema'].MPRO
        if factura_id.startswith('SOFT_'):
            return audit_module['OrigenSistema'].SOFT
    return audit_module['OrigenSistema'].EDARSA_HUB


async def _registrar_auditoria_base(
    audit_module,
    current_user: Dict,
    request: Any,
    modulo,
    entidad: str,
    entidad_origen: str,
    accion_str: str,
    registro_id: str,
    registro_folio: str = None,
    empresa_id: str = None,
    sucursal_id: str = None,
    origen_sistema = None,
    valor_anterior: Any = None,
    valor_nuevo: Any = None,
    motivo: str = None,
    resultado_str: str = 'OK',
    nivel_riesgo = None
) -> bool:
    """Función base para registrar auditoría."""
    await audit_module['servicio'].registrar(
        usuario=current_user,
        request=request,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        origen_sistema=origen_sistema or audit_module['OrigenSistema'].EDARSA_HUB,
        modulo=modulo,
        entidad=entidad,
        entidad_origen=entidad_origen,
        accion=_map_accion(accion_str, audit_module),
        registro_id=str(registro_id) if registro_id else 'N/A',
        registro_folio=registro_folio,
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
        resultado=_map_resultado(resultado_str, audit_module),
        motivo=motivo,
        nivel_riesgo=nivel_riesgo or audit_module['NivelRiesgo'].MEDIO
    )
    return True


# =============================================================================
# FUNCIONES PÚBLICAS
# =============================================================================

async def registrar_auditoria_cxp(
    current_user: Dict,
    request: Any = None,
    accion: str = 'EDIT',
    factura_id: str = None,
    factura_folio: str = None,
    empresa_id: str = None,
    sucursal_id: str = None,
    valor_anterior: Any = None,
    valor_nuevo: Any = None,
    motivo: str = None,
    resultado: str = 'OK'
):
    """Registra auditoría para acciones de Cuentas por Pagar."""
    if not AUDITORIA_HABILITADA:
        return True
    
    try:
        audit = _get_auditoria_imports()
        
        # Determinar nivel de riesgo
        nivel = audit['NivelRiesgo'].MEDIO
        if accion == 'AUTHORIZE':
            nivel = audit['NivelRiesgo'].CRITICO
        elif accion == 'EDIT' and 'masivo' in (motivo or '').lower():
            nivel = audit['NivelRiesgo'].ALTO
        
        await _registrar_auditoria_base(
            audit_module=audit,
            current_user=current_user,
            request=request,
            modulo=audit['ModuloAuditoria'].CXP,
            entidad='factura',
            entidad_origen='cuentas_por_pagar',
            accion_str=accion,
            registro_id=factura_id,
            registro_folio=factura_folio,
            empresa_id=empresa_id,
            sucursal_id=sucursal_id,
            origen_sistema=_determinar_origen_factura(factura_id, audit),
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            motivo=motivo,
            resultado_str=resultado,
            nivel_riesgo=nivel
        )
        
        logger.debug(f"[AUDIT] CxP {accion} - Factura {factura_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error en auditoría CxP: {e}")
        return False


async def registrar_auditoria_tesoreria(
    current_user: Dict,
    request: Any = None,
    accion: str = 'EDIT',
    corte_id: str = None,
    folio_corte: str = None,
    empresa_id: str = None,
    sucursal_id: str = None,
    valor_anterior: Any = None,
    valor_nuevo: Any = None,
    motivo: str = None,
    resultado: str = 'OK',
    tiene_descuadre: bool = False
):
    """Registra auditoría para acciones de Tesorería / Cuadre Z."""
    if not AUDITORIA_HABILITADA:
        return True
    
    try:
        audit = _get_auditoria_imports()
        
        # Determinar nivel de riesgo
        nivel = audit['NivelRiesgo'].MEDIO
        if accion == 'AUTHORIZE':
            nivel = audit['NivelRiesgo'].CRITICO
        elif accion == 'CONFIRM' and tiene_descuadre:
            nivel = audit['NivelRiesgo'].ALTO
        
        await _registrar_auditoria_base(
            audit_module=audit,
            current_user=current_user,
            request=request,
            modulo=audit['ModuloAuditoria'].TESORERIA,
            entidad='cuadre_z',
            entidad_origen='cuadres_z',
            accion_str=accion,
            registro_id=corte_id,
            registro_folio=folio_corte,
            empresa_id=empresa_id,
            sucursal_id=sucursal_id,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            motivo=motivo,
            resultado_str=resultado,
            nivel_riesgo=nivel
        )
        
        logger.debug(f"[AUDIT] Tesorería {accion} - Corte {corte_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error en auditoría Tesorería: {e}")
        return False


async def registrar_auditoria_propinas(
    current_user: Dict,
    request: Any = None,
    accion: str = 'EDIT',
    entidad: str = 'config',
    registro_id: str = None,
    empresa_id: str = None,
    sucursal_id: str = None,
    valor_anterior: Any = None,
    valor_nuevo: Any = None,
    motivo: str = None,
    resultado: str = 'OK'
):
    """Registra auditoría para acciones de Propinas TPV."""
    if not AUDITORIA_HABILITADA:
        return True
    
    try:
        audit = _get_auditoria_imports()
        
        # Config de propinas siempre es ALTO
        nivel = audit['NivelRiesgo'].ALTO if entidad == 'config' else audit['NivelRiesgo'].MEDIO
        
        await _registrar_auditoria_base(
            audit_module=audit,
            current_user=current_user,
            request=request,
            modulo=audit['ModuloAuditoria'].PROPINAS,
            entidad=entidad,
            entidad_origen=f'propinas_{entidad}',
            accion_str=accion,
            registro_id=registro_id,
            empresa_id=empresa_id,
            sucursal_id=sucursal_id,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            motivo=motivo,
            resultado_str=resultado,
            nivel_riesgo=nivel
        )
        
        logger.debug(f"[AUDIT] Propinas {accion} - {entidad} {registro_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error en auditoría Propinas: {e}")
        return False
