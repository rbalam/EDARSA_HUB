"""
P1-FASE5A.1 - Router de Cuentas Bancarias
==========================================
Endpoints CRUD para gestión de cuentas bancarias.

IMPORTANTE:
- SIEMPRE enmascarar número de cuenta y CLABE
- NO usar MongoDB
- Fuente única: EDARSAHUB
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging

from modules.finanzas.models_bancarios import (
    CuentaBancariaCreate,
    CuentaBancariaUpdate,
    CuentaBancariaDesactivar,
    ListaCuentasResponse,
    CuentaBancariaResponse,
)
from modules.finanzas.repository_bancarios import (
    get_bancos_activos,
    get_banco_by_id,
    get_cuentas_bancarias,
    get_cuenta_by_id,
    get_empresa_id_for_unidad,
    existe_numero_cuenta,
    existe_alias,
    crear_cuenta_bancaria,
    actualizar_cuenta_bancaria,
    desactivar_cuenta_bancaria,
    cuenta_tiene_saldos_vigentes,
    get_ultimo_saldo_vigente,
)
from modules.finanzas.utils_bancarios import (
    serialize_cuenta_bancaria,
    serialize_banco,
    validar_numero_cuenta,
    validar_clabe,
    validar_alias,
)
from core.security import get_current_user
from modules.finanzas.access import (
    FINANZAS_ADMINISTRAR,
    FINANZAS_EDITAR,
    FINANZAS_VER,
    require_any_finanzas_permission,
    require_finanzas_permission,
    resolve_finanzas_unit_filter,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/finanzas", tags=["Finanzas - Cuentas Bancarias"])


# =============================================================================
# HELPERS DE PERMISOS
# =============================================================================

def require_view_scope(current_user: dict, unidad_ref: Optional[str] = None):
    return resolve_finanzas_unit_filter(current_user, unidad_ref, FINANZAS_VER)


def require_write_scope(current_user: dict, unidad_ref: Optional[str] = None):
    permission = require_any_finanzas_permission(
        current_user,
        (FINANZAS_ADMINISTRAR, FINANZAS_EDITAR),
    )
    return resolve_finanzas_unit_filter(
        current_user,
        unidad_ref,
        permission["permission_code"],
    )


def require_cuenta_scope(
    current_user: dict,
    cuenta: dict,
    permission_code: str = FINANZAS_VER,
):
    unidad_ref = (
        cuenta.get("unidad_negocio_pk")
        or cuenta.get("unidad_negocio_codigo")
        or cuenta.get("empresa_codigo")
    )
    if unidad_ref:
        resolve_finanzas_unit_filter(current_user, unidad_ref, permission_code)
        return

    _, allowed_units = resolve_finanzas_unit_filter(
        current_user,
        None,
        permission_code,
    )
    if allowed_units is not None:
        raise HTTPException(
            status_code=403,
            detail="La cuenta bancaria no tiene unidad de negocio canónica para validar alcance.",
        )


def get_user_id(user: dict) -> int:
    """Obtiene el UsuarioID SQL canónico; 0 se persiste como NULL en repositorio."""
    for key in ("_sql_usuario_id", "UsuarioID", "usuario_id", "user_id", "id"):
        value = user.get(key)
        if value in (None, "") or isinstance(value, bool):
            continue
        try:
            usuario_id = int(value)
        except (TypeError, ValueError):
            continue
        if usuario_id > 0:
            return usuario_id
    return 0


# =============================================================================
# ENDPOINT: CATÁLOGO DE BANCOS
# =============================================================================

@router.get("/bancos")
async def listar_bancos(current_user: dict = Depends(get_current_user)):
    """
    Lista el catálogo de bancos activos.
    
    Permiso: finanzas.cuentas_bancarias.view
    Tabla: Global_Cat_Bancos
    """
    try:
        require_finanzas_permission(current_user, FINANZAS_VER)

        bancos = get_bancos_activos()
        
        return {
            "bancos": [serialize_banco(b) for b in bancos],
            "total": len(bancos),
            "_fuente": "EDARSAHUB"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando bancos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener catálogo de bancos")


# =============================================================================
# ENDPOINTS: CUENTAS BANCARIAS
# =============================================================================

@router.get("/cuentas-bancarias")
async def listar_cuentas_bancarias(
    banco_id: Optional[int] = Query(None, description="Filtrar por banco"),
    activo: Optional[bool] = Query(True, description="Filtrar por estado"),
    include_inactive: bool = Query(False, description="Incluir inactivas"),
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por unidad de negocio canónica"),
    empresa_codigo: Optional[str] = Query(None, description="Deprecated: usar unidad_negocio_pk"),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista cuentas bancarias con datos ENMASCARADOS.
    
    Permiso: finanzas.cuentas_bancarias.view
    Tabla: Finanzas_Cat_CuentasBancarias
    
    IMPORTANTE: Número de cuenta y CLABE siempre enmascarados.
    """
    try:
        unidad_pk, unidades_permitidas = require_view_scope(
            current_user,
            unidad_negocio_pk or empresa_codigo,
        )

        cuentas = get_cuentas_bancarias(
            banco_id=banco_id,
            activo=activo,
            include_inactive=include_inactive,
            unidad_negocio_pk=unidad_pk,
            unidades_permitidas=unidades_permitidas,
        )
        
        # Serializar con enmascaramiento y agregar último saldo
        cuentas_response = []
        for cuenta in cuentas:
            cuenta_serializada = serialize_cuenta_bancaria(cuenta)
            
            # Agregar último saldo si existe
            ultimo = get_ultimo_saldo_vigente(cuenta['CuentaBancariaID'])
            if ultimo:
                cuenta_serializada['ultimo_saldo'] = {
                    "fecha": str(ultimo['FechaSaldo']),
                    "saldo_final": float(ultimo['SaldoFinal']),
                    "dias_desde_actualizacion": ultimo.get('DiasDesdeActualizacion', 0)
                }
            else:
                cuenta_serializada['ultimo_saldo'] = None
            
            cuentas_response.append(cuenta_serializada)
        
        # Respuesta con manejo de estado vacío
        response = {
            "cuentas": cuentas_response,
            "total": len(cuentas_response),
            "_fuente": "EDARSAHUB"
        }
        
        if len(cuentas_response) == 0:
            response["mensaje"] = "No hay cuentas bancarias configuradas"
            response["accion_sugerida"] = "Configure al menos una cuenta bancaria para comenzar"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando cuentas bancarias: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener cuentas bancarias")


@router.get("/cuentas-bancarias/{cuenta_id}")
async def obtener_cuenta_bancaria(
    cuenta_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene una cuenta bancaria por ID con datos ENMASCARADOS.
    
    Permiso: finanzas.cuentas_bancarias.view
    
    IMPORTANTE: Número de cuenta y CLABE siempre enmascarados.
    """
    try:
        require_finanzas_permission(current_user, FINANZAS_VER)

        cuenta = get_cuenta_by_id(cuenta_id)
        
        if not cuenta:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada")
        require_cuenta_scope(current_user, cuenta, FINANZAS_VER)
        
        cuenta_serializada = serialize_cuenta_bancaria(cuenta)
        
        # Agregar último saldo
        ultimo = get_ultimo_saldo_vigente(cuenta_id)
        if ultimo:
            cuenta_serializada['ultimo_saldo'] = {
                "fecha": str(ultimo['FechaSaldo']),
                "saldo_final": float(ultimo['SaldoFinal']),
                "dias_desde_actualizacion": ultimo.get('DiasDesdeActualizacion', 0)
            }
        
        return cuenta_serializada
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo cuenta {cuenta_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener cuenta bancaria")


@router.post("/cuentas-bancarias", status_code=201)
async def crear_cuenta(
    data: CuentaBancariaCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una nueva cuenta bancaria.
    
    Permiso: finanzas.cuentas_bancarias.manage
    
    Validaciones:
    - BancoID debe existir en Global_Cat_Bancos
    - NumeroCuenta único
    - Alias único
    - CLABE formato válido (18 dígitos) si se proporciona
    
    Response: Datos enmascarados
    """
    try:
        if not data.unidad_negocio_pk:
            raise HTTPException(status_code=400, detail="unidad_negocio_pk es requerida")
        unidad_pk, _ = require_write_scope(current_user, data.unidad_negocio_pk)
        empresa_id = get_empresa_id_for_unidad(unidad_pk)
        if empresa_id is None:
            raise HTTPException(
                status_code=400,
                detail="La unidad de negocio no tiene EmpresaID canónico para cuentas bancarias",
            )
        
        # Validar banco existe
        banco = get_banco_by_id(data.banco_id)
        if not banco:
            raise HTTPException(status_code=400, detail="Banco no encontrado")
        if not banco.get('Activo'):
            raise HTTPException(status_code=400, detail="El banco no está activo")
        
        # Validar número de cuenta único
        if existe_numero_cuenta(data.numero_cuenta):
            raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese número")
        
        # Validar alias único
        if existe_alias(data.alias):
            raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese alias")
        
        # Validar CLABE si se proporciona
        if data.clabe:
            valido, error = validar_clabe(data.clabe)
            if not valido:
                raise HTTPException(status_code=400, detail=error)
        
        # Crear cuenta
        usuario_id = get_user_id(current_user)
        cuenta_id = crear_cuenta_bancaria(
            banco_id=data.banco_id,
            numero_cuenta=data.numero_cuenta,
            alias=data.alias,
            moneda=data.moneda,
            usuario_creacion_id=usuario_id,
            clabe=data.clabe,
            es_cuenta_principal=data.es_cuenta_principal,
            empresa_id=empresa_id
        )
        
        # Obtener cuenta creada para respuesta (para logging interno)
        _ = get_cuenta_by_id(cuenta_id)
        
        logger.info(f"Cuenta bancaria creada: ID={cuenta_id}, Alias={data.alias}, Usuario={usuario_id}")
        
        return {
            "message": "Cuenta bancaria creada exitosamente",
            "cuenta": {
                "cuenta_bancaria_id": cuenta_id,
                "alias": data.alias,
                "numero_cuenta": f"****{data.numero_cuenta[-4:]}"  # Enmascarado
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando cuenta bancaria: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al crear cuenta bancaria")


@router.put("/cuentas-bancarias/{cuenta_id}")
async def actualizar_cuenta(
    cuenta_id: int,
    data: CuentaBancariaUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza campos editables de una cuenta bancaria.
    
    Permiso: finanzas.cuentas_bancarias.manage
    
    Campos editables:
    - alias
    - es_cuenta_principal
    - empresa_id
    
    Campos INMUTABLES (no se pueden cambiar):
    - numero_cuenta
    - clabe
    - banco_id
    - moneda
    """
    try:
        permission = require_any_finanzas_permission(
            current_user,
            (FINANZAS_ADMINISTRAR, FINANZAS_EDITAR),
        )

        # Verificar cuenta existe
        cuenta = get_cuenta_by_id(cuenta_id)
        if not cuenta:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada")
        require_cuenta_scope(current_user, cuenta, permission["permission_code"])
        if data.empresa_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Cambiar EmpresaID directamente no es un flujo canónico; use unidad_negocio_pk.",
            )
        
        # Validar alias único si se actualiza
        if data.alias and data.alias != cuenta.get('Alias'):
            if existe_alias(data.alias, excluir_id=cuenta_id):
                raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese alias")
        
        # Actualizar
        usuario_id = get_user_id(current_user)
        actualizar_cuenta_bancaria(
            cuenta_id=cuenta_id,
            usuario_modificacion_id=usuario_id,
            alias=data.alias,
            es_cuenta_principal=data.es_cuenta_principal,
            empresa_id=None
        )
        
        # Obtener cuenta actualizada
        cuenta_actualizada = get_cuenta_by_id(cuenta_id)
        
        logger.info(f"Cuenta bancaria actualizada: ID={cuenta_id}, Usuario={usuario_id}")
        
        return {
            "message": "Cuenta bancaria actualizada",
            "cuenta": serialize_cuenta_bancaria(cuenta_actualizada)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando cuenta {cuenta_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al actualizar cuenta bancaria")


@router.post("/cuentas-bancarias/{cuenta_id}/desactivar")
async def desactivar_cuenta(
    cuenta_id: int,
    data: CuentaBancariaDesactivar,
    current_user: dict = Depends(get_current_user)
):
    """
    Desactiva una cuenta bancaria (baja lógica).
    
    Permiso: finanzas.cuentas_bancarias.manage
    
    Validaciones:
    - Motivo obligatorio (mínimo 10 caracteres)
    - No se puede desactivar si tiene saldos vigentes
    
    NOTA: No se elimina físicamente, solo se marca Activo = 0
    """
    try:
        permission = require_any_finanzas_permission(
            current_user,
            (FINANZAS_ADMINISTRAR, FINANZAS_EDITAR),
        )

        # Verificar cuenta existe
        cuenta = get_cuenta_by_id(cuenta_id)
        if not cuenta:
            raise HTTPException(status_code=404, detail="Cuenta bancaria no encontrada")
        require_cuenta_scope(current_user, cuenta, permission["permission_code"])
        
        if not cuenta.get('Activo'):
            raise HTTPException(status_code=400, detail="La cuenta ya está desactivada")
        
        # Verificar si tiene saldos vigentes
        if cuenta_tiene_saldos_vigentes(cuenta_id):
            raise HTTPException(
                status_code=400, 
                detail="No se puede desactivar: la cuenta tiene saldos vigentes. Cancele los saldos primero."
            )
        
        # Desactivar
        usuario_id = get_user_id(current_user)
        desactivar_cuenta_bancaria(cuenta_id, usuario_id)
        
        logger.info(f"Cuenta bancaria desactivada: ID={cuenta_id}, Motivo={data.motivo}, Usuario={usuario_id}")
        
        return {
            "message": "Cuenta bancaria desactivada",
            "cuenta_bancaria_id": cuenta_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error desactivando cuenta {cuenta_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al desactivar cuenta bancaria")
