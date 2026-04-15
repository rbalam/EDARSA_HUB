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
from datetime import datetime

logger = logging.getLogger(__name__)

# Flag para habilitar/deshabilitar auditoría (para rollback fácil)
AUDITORIA_HABILITADA = True


async def registrar_auditoria_cxp(
    current_user: Dict,
    request: Any = None,
    accion: str = 'EDIT',  # VIEW, EDIT, CONFIRM, AUTHORIZE
    factura_id: str = None,
    factura_folio: str = None,
    empresa_id: str = None,
    sucursal_id: str = None,
    valor_anterior: Any = None,
    valor_nuevo: Any = None,
    motivo: str = None,
    resultado: str = 'OK'  # OK, ERROR, RECHAZADO
):
    """
    Registra auditoría para acciones de Cuentas por Pagar.
    
    Acciones típicas:
    - CXP_MARCAR_PAGAR (EDIT)
    - CXP_PAGO_MASIVO (EDIT) 
    - CXP_AUTORIZAR_PAGO (AUTHORIZE)
    """
    if not AUDITORIA_HABILITADA:
        return True
    
    try:
        from core.auditoria import (
            servicio_auditoria, 
            AccionAuditoria, 
            ModuloAuditoria, 
            NivelRiesgo,
            ResultadoAuditoria,
            OrigenSistema
        )
        
        # Mapear acción string a enum
        accion_enum = {
            'VIEW': AccionAuditoria.VIEW,
            'EDIT': AccionAuditoria.EDIT,
            'CONFIRM': AccionAuditoria.CONFIRM,
            'AUTHORIZE': AccionAuditoria.AUTHORIZE
        }.get(accion, AccionAuditoria.EDIT)
        
        # Determinar nivel de riesgo
        nivel = NivelRiesgo.MEDIO
        if accion == 'AUTHORIZE':
            nivel = NivelRiesgo.CRITICO
        elif accion == 'EDIT' and 'masivo' in (motivo or '').lower():
            nivel = NivelRiesgo.ALTO
        
        # Determinar origen del sistema
        origen = OrigenSistema.EDARSA_HUB
        if factura_id and factura_id.startswith('MPRO_'):
            origen = OrigenSistema.MPRO
        elif factura_id and factura_id.startswith('SOFT_'):
            origen = OrigenSistema.SOFT
        
        await servicio_auditoria.registrar(
            usuario=current_user,
            request=request,
            empresa_id=empresa_id,
            sucursal_id=sucursal_id,
            origen_sistema=origen,
            modulo=ModuloAuditoria.CXP,
            entidad='factura',
            entidad_origen='cuentas_por_pagar',
            accion=accion_enum,
            registro_id=str(factura_id) if factura_id else 'N/A',
            registro_folio=factura_folio,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            resultado=ResultadoAuditoria[resultado] if resultado in ['OK', 'ERROR', 'RECHAZADO'] else ResultadoAuditoria.OK,
            motivo=motivo,
            nivel_riesgo=nivel
        )
        
        logger.debug(f"[AUDIT] CxP {accion} - Factura {factura_id}")
        return True
        
    except Exception as e:
        # La auditoría NO debe bloquear operaciones
        logger.error(f"Error en auditoría CxP: {e}")
        return False


async def registrar_auditoria_tesoreria(
    current_user: Dict,
    request: Any = None,
    accion: str = 'EDIT',  # VIEW, EDIT, CONFIRM, AUTHORIZE
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
    """
    Registra auditoría para acciones de Tesorería / Cuadre Z.
    
    Acciones típicas:
    - TESORERIA_INICIAR_CUADRE (EDIT)
    - TESORERIA_GUARDAR_CUADRE (CONFIRM)
    - TESORERIA_AJUSTAR_CUADRE (EDIT)
    - TESORERIA_AUTORIZAR_DESCUADRE (AUTHORIZE)
    """
    if not AUDITORIA_HABILITADA:
        return True
    
    try:
        from core.auditoria import (
            servicio_auditoria, 
            AccionAuditoria, 
            ModuloAuditoria, 
            NivelRiesgo,
            ResultadoAuditoria,
            OrigenSistema
        )
        
        # Mapear acción string a enum
        accion_enum = {
            'VIEW': AccionAuditoria.VIEW,
            'EDIT': AccionAuditoria.EDIT,
            'CONFIRM': AccionAuditoria.CONFIRM,
            'AUTHORIZE': AccionAuditoria.AUTHORIZE
        }.get(accion, AccionAuditoria.EDIT)
        
        # Determinar nivel de riesgo
        nivel = NivelRiesgo.MEDIO
        if accion == 'AUTHORIZE':
            nivel = NivelRiesgo.CRITICO
        elif accion == 'CONFIRM':
            nivel = NivelRiesgo.ALTO if tiene_descuadre else NivelRiesgo.MEDIO
        
        await servicio_auditoria.registrar(
            usuario=current_user,
            request=request,
            empresa_id=empresa_id,
            sucursal_id=sucursal_id,
            origen_sistema=OrigenSistema.EDARSA_HUB,
            modulo=ModuloAuditoria.TESORERIA,
            entidad='cuadre_z',
            entidad_origen='cuadres_z',
            accion=accion_enum,
            registro_id=str(corte_id) if corte_id else 'N/A',
            registro_folio=folio_corte,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            resultado=ResultadoAuditoria[resultado] if resultado in ['OK', 'ERROR', 'RECHAZADO'] else ResultadoAuditoria.OK,
            motivo=motivo,
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
    entidad: str = 'config',  # config, cuadre, pago
    registro_id: str = None,
    empresa_id: str = None,
    sucursal_id: str = None,
    valor_anterior: Any = None,
    valor_nuevo: Any = None,
    motivo: str = None,
    resultado: str = 'OK'
):
    """
    Registra auditoría para acciones de Propinas TPV.
    
    Acciones típicas:
    - PROPINAS_CONFIG_EDITAR (EDIT)
    - PROPINAS_CUADRE_CONFIRMAR (CONFIRM)
    """
    if not AUDITORIA_HABILITADA:
        return True
    
    try:
        from core.auditoria import (
            servicio_auditoria, 
            AccionAuditoria, 
            ModuloAuditoria, 
            NivelRiesgo,
            ResultadoAuditoria,
            OrigenSistema
        )
        
        accion_enum = {
            'VIEW': AccionAuditoria.VIEW,
            'EDIT': AccionAuditoria.EDIT,
            'CONFIRM': AccionAuditoria.CONFIRM,
            'AUTHORIZE': AccionAuditoria.AUTHORIZE
        }.get(accion, AccionAuditoria.EDIT)
        
        # Config de propinas siempre es ALTO
        nivel = NivelRiesgo.ALTO if entidad == 'config' else NivelRiesgo.MEDIO
        
        await servicio_auditoria.registrar(
            usuario=current_user,
            request=request,
            empresa_id=empresa_id,
            sucursal_id=sucursal_id,
            origen_sistema=OrigenSistema.EDARSA_HUB,
            modulo=ModuloAuditoria.PROPINAS,
            entidad=entidad,
            entidad_origen=f'propinas_{entidad}',
            accion=accion_enum,
            registro_id=str(registro_id) if registro_id else 'N/A',
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
            resultado=ResultadoAuditoria[resultado] if resultado in ['OK', 'ERROR', 'RECHAZADO'] else ResultadoAuditoria.OK,
            motivo=motivo,
            nivel_riesgo=nivel
        )
        
        logger.debug(f"[AUDIT] Propinas {accion} - {entidad} {registro_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error en auditoría Propinas: {e}")
        return False
