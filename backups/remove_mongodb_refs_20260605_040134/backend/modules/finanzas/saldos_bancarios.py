"""
P1-FASE5A.1 - Router de Saldos Bancarios
=========================================
Endpoints para gestión de saldos bancarios.

IMPORTANTE:
- NO editar registros históricos directamente
- Corrección = marcar anterior como CORREGIDO + crear nuevo VIGENTE
- Cancelación = motivo obligatorio
- Fuente única: EDARSAHUB
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import date
from decimal import Decimal
import logging

from modules.finanzas.models_bancarios import (
    SaldoBancarioCreate,
    SaldoBancarioCorregir,
    SaldoBancarioCancelar,
)
from modules.finanzas.repository_bancarios import (
    get_cuenta_by_id,
    get_saldos_cuenta,
    get_ultimo_saldo_vigente,
    existe_saldo_vigente,
    get_saldo_by_id,
    crear_saldo_bancario,
    marcar_saldo_corregido,
    marcar_saldo_cancelado,
    get_saldo_bancario_total,
    get_historial_saldo,
)
from modules.finanzas.utils_bancarios import (
    serialize_saldo_bancario,
    validar_saldo,
    validar_motivo,
    mask_numero_cuenta,
)
from core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/finanzas", tags=["Finanzas - Saldos Bancarios"])


# =============================================================================
# HELPERS DE PERMISOS
# =============================================================================

def check_permission(user: dict, permission: str) -> bool:
    """
    Verifica si el usuario tiene el permiso requerido.
    """
    if not user:
        return False
    
    user_role = user.get('role', user.get('rol', ''))
    
    # Roles con acceso total
    roles_admin = ['superadmin', 'SuperAdministrador', 'admin', 'Director Finanzas']
    if user_role in roles_admin:
        return True
    
    # Roles con acceso a saldos
    roles_finanzas = ['Contador', 'Tesorero', 'contador', 'tesorero']
    if user_role in roles_finanzas:
        if permission in ['finanzas.saldos.view', 'finanzas.saldos.manage']:
            return True
    
    # Permisos explícitos
    user_permissions = user.get('permissions', [])
    return permission in user_permissions


def get_user_id(user: dict) -> int:
    """
    Obtiene el ID del usuario para auditoría.
    """
    user_id = user.get('user_id') or user.get('id') or user.get('_id')
    if user_id:
        try:
            return int(str(user_id).split('ObjectId')[-1].replace("('", "").replace("')", "")[:24])
        except (ValueError, TypeError, AttributeError):
            pass
    return 1  # Default para pruebas


# =============================================================================
# ENDPOINTS: SALDOS DE UNA CUENTA
# =============================================================================

@router.get("/cuentas-bancarias/{cuenta_id}/saldos")
async def listar_saldos_cuenta(
    cuenta_id: int,
    fecha_inicio: Optional[date] = Query(None, description="Filtrar desde fecha"),
    fecha_fin: Optional[date] = Query(None, description="Filtrar hasta fecha"),
    solo_vigentes: bool = Query(False, description="Solo mostrar VIGENTES"),
    limit: int = Query(100, ge=1, le=500, description="Máximo registros"),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista saldos de una cuenta bancaria.
    
    Permiso: finanzas.saldos.view
    Tabla: Finanzas_SaldosBancarios
    """
    try:
        if not check_permission(current_user, 'finanzas.saldos.view'):
            raise HTTPException(status_code=403, detail="No tiene permiso para ver saldos")
        
        # Verificar cuenta existe
        cuenta = get_cuenta_by_id(cuenta_id)
        if not cuenta:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada")
        
        saldos = get_saldos_cuenta(
            cuenta_id=cuenta_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            solo_vigentes=solo_vigentes,
            limit=limit
        )
        
        return {
            "cuenta_bancaria_id": cuenta_id,
            "alias": cuenta.get('Alias'),
            "saldos": [serialize_saldo_bancario(s) for s in saldos],
            "total": len(saldos)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando saldos de cuenta {cuenta_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener saldos")


@router.get("/cuentas-bancarias/{cuenta_id}/saldo-actual")
async def obtener_saldo_actual(
    cuenta_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el último saldo vigente de una cuenta.
    
    Permiso: finanzas.saldos.view
    
    Incluye alerta si el saldo tiene más de 3 días sin actualizar.
    """
    try:
        if not check_permission(current_user, 'finanzas.saldos.view'):
            raise HTTPException(status_code=403, detail="No tiene permiso para ver saldos")
        
        # Verificar cuenta existe
        cuenta = get_cuenta_by_id(cuenta_id)
        if not cuenta:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada")
        
        ultimo = get_ultimo_saldo_vigente(cuenta_id)
        
        if ultimo:
            dias_desde = ultimo.get('DiasDesdeActualizacion', 0)
            return {
                "cuenta_bancaria_id": cuenta_id,
                "alias": cuenta.get('Alias'),
                "ultimo_saldo": {
                    "saldo_bancario_id": ultimo['SaldoBancarioID'],
                    "fecha_saldo": str(ultimo['FechaSaldo']),
                    "saldo_final": float(ultimo['SaldoFinal']),
                    "moneda": ultimo.get('Moneda', 'MXN'),
                    "dias_desde_actualizacion": dias_desde
                },
                "alerta_desactualizado": dias_desde > 3
            }
        else:
            return {
                "cuenta_bancaria_id": cuenta_id,
                "alias": cuenta.get('Alias'),
                "ultimo_saldo": None,
                "mensaje": "Esta cuenta no tiene saldos registrados",
                "accion_sugerida": "Capture el saldo actual para ver la posición de efectivo"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo saldo actual de cuenta {cuenta_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener saldo actual")


# =============================================================================
# ENDPOINTS: GESTIÓN DE SALDOS
# =============================================================================

@router.post("/saldos-bancarios", status_code=201)
async def capturar_saldo(
    data: SaldoBancarioCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Captura un nuevo saldo bancario.
    
    Permiso: finanzas.saldos.manage
    
    Validaciones:
    - Cuenta debe existir y estar activa
    - Fecha no puede ser futura
    - No debe existir saldo vigente para cuenta+fecha
    
    Si ya existe saldo vigente, usar endpoint de corrección.
    """
    try:
        if not check_permission(current_user, 'finanzas.saldos.manage'):
            raise HTTPException(status_code=403, detail="No tiene permiso para capturar saldos")
        
        # Verificar cuenta existe y está activa
        cuenta = get_cuenta_by_id(data.cuenta_bancaria_id)
        if not cuenta:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada")
        if not cuenta.get('Activo'):
            raise HTTPException(status_code=400, detail="La cuenta bancaria no está activa")
        
        # Validar que no existe saldo vigente para esa fecha
        if existe_saldo_vigente(data.cuenta_bancaria_id, data.fecha_saldo):
            raise HTTPException(
                status_code=400,
                detail="Ya existe un saldo vigente para esta cuenta y fecha. Use el endpoint de corrección."
            )
        
        # Validar saldo
        valido, error, saldo_decimal = validar_saldo(data.saldo_final)
        if not valido:
            raise HTTPException(status_code=400, detail=error)
        
        # Crear saldo
        usuario_id = get_user_id(current_user)
        saldo_id = crear_saldo_bancario(
            cuenta_id=data.cuenta_bancaria_id,
            fecha_saldo=data.fecha_saldo,
            saldo_final=saldo_decimal,
            moneda=cuenta.get('Moneda', 'MXN'),
            usuario_creacion_id=usuario_id,
            observaciones=data.observaciones
        )
        
        logger.info(f"Saldo capturado: ID={saldo_id}, Cuenta={data.cuenta_bancaria_id}, Fecha={data.fecha_saldo}, Usuario={usuario_id}")
        
        return {
            "message": "Saldo capturado exitosamente",
            "saldo": {
                "saldo_bancario_id": saldo_id,
                "cuenta_bancaria_id": data.cuenta_bancaria_id,
                "fecha_saldo": str(data.fecha_saldo),
                "saldo_final": float(saldo_decimal),
                "estatus": "VIGENTE"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error capturando saldo: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al capturar saldo")


@router.post("/saldos-bancarios/{saldo_id}/corregir")
async def corregir_saldo(
    saldo_id: int,
    data: SaldoBancarioCorregir,
    current_user: dict = Depends(get_current_user)
):
    """
    Corrige un saldo bancario existente.
    
    Permiso: finanzas.saldos.manage
    
    Proceso:
    1. Verifica que el saldo existe y es VIGENTE
    2. Marca el saldo anterior como CORREGIDO (EsVigente=0, Activo=0)
    3. Crea nuevo saldo con el valor corregido (VIGENTE)
    
    IMPORTANTE: No se edita el registro original, se crea historial.
    """
    try:
        if not check_permission(current_user, 'finanzas.saldos.manage'):
            raise HTTPException(status_code=403, detail="No tiene permiso para corregir saldos")
        
        # Verificar saldo existe
        saldo = get_saldo_by_id(saldo_id)
        if not saldo:
            raise HTTPException(status_code=404, detail="Saldo bancario no encontrado")
        
        # Verificar que es VIGENTE
        if saldo.get('Estatus') != 'VIGENTE' or not saldo.get('EsVigente'):
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden corregir saldos VIGENTES"
            )
        
        # Validar motivo
        valido, error = validar_motivo(data.motivo_correccion)
        if not valido:
            raise HTTPException(status_code=400, detail=error)
        
        # Validar saldo correcto
        valido, error, saldo_correcto = validar_saldo(data.saldo_final_correcto)
        if not valido:
            raise HTTPException(status_code=400, detail=error)
        
        usuario_id = get_user_id(current_user)
        
        # Marcar anterior como CORREGIDO
        marcar_saldo_corregido(saldo_id, usuario_id, data.motivo_correccion)
        
        # Crear nuevo saldo VIGENTE
        nuevo_saldo_id = crear_saldo_bancario(
            cuenta_id=saldo['CuentaBancariaID'],
            fecha_saldo=saldo['FechaSaldo'],
            saldo_final=saldo_correcto,
            moneda=saldo.get('Moneda', 'MXN'),
            usuario_creacion_id=usuario_id,
            observaciones=f"Corrección de saldo anterior (ID: {saldo_id})"
        )
        
        logger.info(f"Saldo corregido: Anterior={saldo_id}, Nuevo={nuevo_saldo_id}, Usuario={usuario_id}")
        
        return {
            "message": "Saldo corregido exitosamente",
            "saldo_anterior": {
                "saldo_bancario_id": saldo_id,
                "saldo_final": float(saldo['SaldoFinal']),
                "estatus": "CORREGIDO"
            },
            "saldo_nuevo": {
                "saldo_bancario_id": nuevo_saldo_id,
                "saldo_final": float(saldo_correcto),
                "estatus": "VIGENTE"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error corrigiendo saldo {saldo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al corregir saldo")


@router.post("/saldos-bancarios/{saldo_id}/cancelar")
async def cancelar_saldo(
    saldo_id: int,
    data: SaldoBancarioCancelar,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancela un saldo bancario.
    
    Permiso: finanzas.saldos.manage
    
    Proceso:
    1. Verifica que el saldo existe y es VIGENTE
    2. Marca el saldo como CANCELADO (EsVigente=0, Activo=0)
    3. Registra motivo, usuario y fecha de cancelación
    
    IMPORTANTE: Motivo de cancelación es OBLIGATORIO.
    """
    try:
        if not check_permission(current_user, 'finanzas.saldos.manage'):
            raise HTTPException(status_code=403, detail="No tiene permiso para cancelar saldos")
        
        # Verificar saldo existe
        saldo = get_saldo_by_id(saldo_id)
        if not saldo:
            raise HTTPException(status_code=404, detail="Saldo bancario no encontrado")
        
        # Verificar que es VIGENTE
        if saldo.get('Estatus') != 'VIGENTE' or not saldo.get('EsVigente'):
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden cancelar saldos VIGENTES"
            )
        
        # Validar motivo
        valido, error = validar_motivo(data.motivo_cancelacion)
        if not valido:
            raise HTTPException(status_code=400, detail=error)
        
        usuario_id = get_user_id(current_user)
        
        # Marcar como CANCELADO
        marcar_saldo_cancelado(saldo_id, usuario_id, data.motivo_cancelacion)
        
        # Obtener saldo actualizado
        saldo_actualizado = get_saldo_by_id(saldo_id)
        
        logger.info(f"Saldo cancelado: ID={saldo_id}, Motivo={data.motivo_cancelacion}, Usuario={usuario_id}")
        
        return {
            "message": "Saldo cancelado exitosamente",
            "saldo": {
                "saldo_bancario_id": saldo_id,
                "estatus": "CANCELADO",
                "fecha_cancelacion": str(saldo_actualizado.get('FechaCancelacion')) if saldo_actualizado else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelando saldo {saldo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al cancelar saldo")


@router.get("/saldos-bancarios/{saldo_id}/historial")
async def obtener_historial_saldo(
    saldo_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el historial de auditoría de un saldo.
    
    Permiso: finanzas.saldos.view
    
    Muestra todas las versiones del saldo (original, correcciones, cancelaciones).
    """
    try:
        if not check_permission(current_user, 'finanzas.saldos.view'):
            raise HTTPException(status_code=403, detail="No tiene permiso para ver historial")
        
        # Verificar saldo existe
        saldo = get_saldo_by_id(saldo_id)
        if not saldo:
            raise HTTPException(status_code=404, detail="Saldo bancario no encontrado")
        
        # Obtener historial
        historial_raw = get_historial_saldo(saldo_id)
        
        # Transformar a formato de acciones
        historial = []
        for i, h in enumerate(historial_raw):
            if h['Estatus'] == 'VIGENTE':
                if i == 0:
                    accion = "CREACION"
                else:
                    accion = "CORRECCION_NUEVA"
            elif h['Estatus'] == 'CORREGIDO':
                accion = "CORRECCION"
            elif h['Estatus'] == 'CANCELADO':
                accion = "CANCELACION"
            else:
                accion = h['Estatus']
            
            item = {
                "accion": accion,
                "fecha": h['FechaCreacion'] if accion in ['CREACION', 'CORRECCION_NUEVA'] else h.get('FechaCancelacion'),
                "usuario": h.get('UsuarioCreacion') if accion in ['CREACION', 'CORRECCION_NUEVA'] else h.get('UsuarioCancelacion'),
                "saldo_final": float(h['SaldoFinal']),
                "motivo": h.get('MotivoCancelacion')
            }
            historial.append(item)
        
        return {
            "saldo_bancario_id": saldo_id,
            "cuenta_bancaria_id": saldo['CuentaBancariaID'],
            "fecha_saldo": str(saldo['FechaSaldo']),
            "historial": historial
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo historial de saldo {saldo_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener historial")


# =============================================================================
# ENDPOINT: SALDO TOTAL
# =============================================================================

@router.get("/saldos-bancarios/total")
async def obtener_saldo_total(
    fecha: Optional[date] = Query(None, description="Fecha de consulta (default: hoy)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Calcula el saldo bancario total de todas las cuentas activas.
    
    Permiso: finanzas.saldos.view
    
    Usa el último saldo vigente de cada cuenta hasta la fecha indicada.
    """
    try:
        if not check_permission(current_user, 'finanzas.saldos.view'):
            raise HTTPException(status_code=403, detail="No tiene permiso para ver saldos")
        
        fecha_consulta = fecha or date.today()
        
        resultado = get_saldo_bancario_total(fecha_consulta)
        
        response = {
            "fecha_consulta": str(fecha_consulta),
            "saldo_bancario_total": resultado['saldo_total'],
            "moneda": "MXN",
            "cuentas_con_saldo": resultado['cuentas_con_saldo'],
            "cuentas_sin_saldo": resultado['cuentas_sin_saldo'],
            "cuentas_desactualizadas": resultado['cuentas_desactualizadas'],
            "detalle_por_banco": resultado['detalle_por_banco'],
            "_fuente": "EDARSAHUB"
        }
        
        # Manejo de estado vacío
        if resultado['cuentas_con_saldo'] == 0:
            if resultado['cuentas_sin_saldo'] > 0:
                response["mensaje"] = "No hay saldos registrados para ninguna cuenta"
                response["accion_sugerida"] = "Capture los saldos actuales de las cuentas bancarias"
            else:
                response["mensaje"] = "No hay cuentas bancarias configuradas"
                response["accion_sugerida"] = "Configure al menos una cuenta bancaria para comenzar"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo saldo total: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al calcular saldo total")
