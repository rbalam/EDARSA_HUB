from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Endpoints para Configuración de Asignaciones de Responsables
============================================================

MODELO FUNCIONAL:
UNIDAD DE NEGOCIO + ALMACÉN → USUARIO RESPONSABLE

PRINCIPIOS:
1. Solo conceptos de negocio en la API (NO server_id, NO sucursal_id)
2. Almacenes desde catálogo local (NO consulta SQL en tiempo real)
3. RBAC: Usuario solo opera en su alcance
4. Validaciones estrictas de usuario responsable

Fecha: Abril 2026
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import logging
import os

# Motor para conexión a MongoDB

from core.security import get_current_user
from core.alcance_helper import resolver_alcance_usuarios
from core.rbac_helper_sql import es_superadmin
from core.auditoria import servicio_auditoria, AccionAuditoria, ModuloAuditoria
from ..repositories.config_asignaciones_repository import get_config_asignaciones_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config-asignaciones", tags=["Config Asignaciones"])

# Conexión a MongoDB
_db = None

def get_db():
    """DEPRECADO: MongoDB ya no se usa. Retorna None (NO-MONGO / P5-1 sunset)."""
    logging.debug("[CONFIG_ASIGNACIONES] get_db() - MongoDB deprecado, retornando None")
    return None


# Alias para uso en el módulo
db = property(lambda self: get_db())


# =============================================================================
# MODELOS PYDANTIC
# =============================================================================

class CrearAsignacionRequest(BaseModel):
    """Request para crear nueva asignación."""
    unidad_negocio_pk: str = Field(..., description="ID de la unidad de negocio")
    almacen_id: str = Field("", description="ID del almacén (vacío = todos)")
    usuario_responsable_id: str = Field(..., description="ID del usuario responsable")


class ActualizarAsignacionRequest(BaseModel):
    """Request para actualizar asignación."""
    unidad_negocio_pk: Optional[str] = Field(None, description="Nueva unidad de negocio")
    almacen_id: Optional[str] = Field(None, description="Nuevo almacén (vacío = todos)")
    usuario_responsable_id: Optional[str] = Field(None, description="Nuevo usuario responsable")
    activa: Optional[bool] = Field(None, description="Estado activo/inactivo")


class ResolverRequest(BaseModel):
    """Request para resolver responsable (testing)."""
    unidad_negocio_pk: str
    almacen_id: str = ""


# =============================================================================
# HELPERS
# =============================================================================

async def obtener_empresas_permitidas(current_user: dict) -> list:
    """
    Obtiene la lista de unidades (EmpresaMongoUUID) a las que el usuario tiene acceso.
    SQL-First: usa el mismo espacio de IDs que el endpoint /unidades-negocio.
    """
    alcance = await resolver_alcance_usuarios(current_user, None)
    
    if alcance.get("tiene_acceso_global"):
        from core.context_resolver import get_user_unidades_negocio
        unidades = await get_user_unidades_negocio(current_user)
        return [u["id"] for u in unidades]
    
    return alcance.get("empresas_ids", [])


async def obtener_unidad_accesible(current_user: dict, unidad_negocio_pk: str) -> Optional[dict]:
    """
    Devuelve la unidad de negocio (dict con id, nombre, server_id) si el usuario
    tiene acceso a ella. Usa get_user_unidades_negocio (mismo espacio de IDs que
    el frontend). Retorna None si no existe o el usuario no tiene alcance.
    """
    from core.context_resolver import get_user_unidades_negocio
    unidades = await get_user_unidades_negocio(current_user)
    return next((u for u in unidades if str(u.get("id")) == str(unidad_negocio_pk)), None)


async def validar_alcance_usuario(current_user: dict, unidad_negocio_pk: str):
    """Valida que el usuario tenga alcance sobre la unidad de negocio."""
    # SuperAdministrador tiene acceso total
    if es_superadmin(current_user):
        return True
    
    empresas_permitidas = await obtener_empresas_permitidas(current_user)
    
    if unidad_negocio_pk not in empresas_permitidas:
        raise HTTPException(
            status_code=403,
            detail="No tiene alcance sobre esta unidad de negocio"
        )
    
    return True


async def validar_usuario_responsable(usuario_id: str, unidad_negocio_pk: str):
    """
    Valida el usuario responsable contra la fuente canónica SQL (Usuario_Catalogo):
    1. Existe
    2. Está activo

    SQL-First: las validaciones legacy de alcance/roles MongoDB fueron removidas.
    El repositorio SQL es la única fuente de verdad.
    """
    repo = get_config_asignaciones_repository(None)
    usuario = await repo.obtener_usuario(usuario_id)
    
    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario responsable no encontrado")
    
    if not usuario.get("activo", True):
        raise HTTPException(status_code=400, detail="El usuario responsable está inactivo")
    
    return usuario


# =============================================================================
# ENDPOINTS - CONFIGURACIONES
# =============================================================================

@router.get("")
async def listar_asignaciones(
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por unidad"),
    activa: Optional[bool] = Query(None, description="Filtrar por estado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista configuraciones de asignación.
    
    Filtrado automático por RBAC: solo ve configuraciones de sus unidades.
    """
    repo = get_config_asignaciones_repository(get_db())
    
    # Si no es SuperAdmin, filtrar por empresas permitidas
    if not es_superadmin(current_user):
        empresas_permitidas = await obtener_empresas_permitidas(current_user)
        
        if unidad_negocio_pk:
            # Validar que puede ver esa unidad
            if unidad_negocio_pk not in empresas_permitidas:
                return {"success": True, "data": [], "total": 0}
        else:
            # Si no especifica, filtrar por todas las que puede ver
            # Para esto necesitamos ajustar el repositorio o hacer múltiples consultas
            # Por ahora, si tiene pocas empresas, iteramos
            resultado_total = {"data": [], "total": 0}
            for emp_id in empresas_permitidas:
                parcial = await repo.listar(
                    unidad_negocio_pk=emp_id,
                    activa=activa,
                    skip=0,
                    limit=100
                )
                resultado_total["data"].extend(parcial["data"])
                resultado_total["total"] += parcial["total"]
            
            # Aplicar paginación manual
            resultado_total["data"] = resultado_total["data"][skip:skip+limit]
            return {"success": True, **resultado_total}
    
    resultado = await repo.listar(
        unidad_negocio_pk=unidad_negocio_pk,
        activa=activa,
        skip=skip,
        limit=limit
    )
    
    return {"success": True, **resultado}


@router.get("/unidades-negocio")
async def listar_unidades_negocio(
    current_user: dict = Depends(get_current_user)
):
    """
    Lista unidades de negocio disponibles para configurar.
    
    Filtrado por RBAC del usuario.
    """
    from core.context_resolver import get_user_unidades_negocio
    
    unidades = await get_user_unidades_negocio(current_user)
    
    # Simplificar respuesta (solo id y nombre)
    return {
        "success": True,
        "data": [
            {"id": u["id"], "nombre": u["nombre"]}
            for u in unidades
        ]
    }


@router.get("/almacenes/{unidad_negocio_pk}")
async def listar_almacenes(
    unidad_negocio_pk: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Lista almacenes de una unidad de negocio.
    
    FUENTE: Catálogo local (NO consulta SQL externo).
    
    Incluye opción "(Todos los almacenes)" como primera opción.
    """
    # Validar alcance
    await validar_alcance_usuario(current_user, unidad_negocio_pk)
    
    repo = get_config_asignaciones_repository(get_db())
    almacenes = await repo.listar_almacenes(unidad_negocio_pk)
    
    return {"success": True, "data": almacenes}


@router.get("/almacenes/{unidad_negocio_pk}/sync-info")
async def info_sincronizacion_almacenes(
    unidad_negocio_pk: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene información de la última sincronización de almacenes.
    
    Returns:
        - ultima_sincronizacion: timestamp ISO
        - total_almacenes: cantidad en catálogo
        - usuario_sync: quién ejecutó la última sync
    """
    # Validar alcance
    await validar_alcance_usuario(current_user, unidad_negocio_pk)
    
    # Catálogo SQL-First: contar almacenes disponibles (excluye opción "(Todos)")
    repo = get_config_asignaciones_repository(None)
    almacenes = await repo.listar_almacenes(unidad_negocio_pk)
    total = len([a for a in almacenes if a.get("id")])
    
    return {
        "success": True,
        "data": {
            "ultima_sincronizacion": None,
            "usuario_sync": None,
            "total_almacenes": total
        }
    }


@router.get("/{config_id}")
async def obtener_asignacion(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtiene una configuración por ID."""
    repo = get_config_asignaciones_repository(get_db())
    config = await repo.obtener_por_id(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    # Validar alcance
    await validar_alcance_usuario(current_user, config["unidad_negocio_pk"])
    
    return {"success": True, "data": config}


@router.post("", status_code=201)
async def crear_asignacion(
    request: CrearAsignacionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Crea nueva configuración de asignación.
    
    Validaciones:
    - Usuario autenticado tiene alcance sobre la unidad
    - Unidad de negocio existe y está activa
    - Usuario responsable existe, está activo, tiene alcance y rol
    - No existe duplicado (unidad + almacén)
    """
    # 1. Validar alcance del usuario autenticado
    await validar_alcance_usuario(current_user, request.unidad_negocio_pk)
    
    # 2. Validar unidad de negocio (mismo espacio de IDs que /unidades-negocio)
    unidad = await obtener_unidad_accesible(current_user, request.unidad_negocio_pk)
    if not unidad:
        raise HTTPException(status_code=400, detail="Unidad de negocio no encontrada o inactiva")
    
    # 3. Validar usuario responsable (completo)
    await validar_usuario_responsable(request.usuario_responsable_id, request.unidad_negocio_pk)
    
    # 4. Validar almacén si se especifica
    if request.almacen_id:
        repo = get_config_asignaciones_repository(get_db())
        almacenes = await repo.listar_almacenes(request.unidad_negocio_pk)
        almacen_ids = [a["id"] for a in almacenes if a["id"]]  # Excluir opción "todos"
        
        if request.almacen_id not in almacen_ids:
            raise HTTPException(
                status_code=400,
                detail="El almacén no corresponde a la unidad de negocio seleccionada"
            )
    
    # 5. Crear configuración
    repo = get_config_asignaciones_repository(get_db())
    
    try:
        config = await repo.crear(
            unidad_negocio_pk=request.unidad_negocio_pk,
            almacen_id=request.almacen_id,
            usuario_responsable_id=request.usuario_responsable_id,
            usuario_creacion=current_user.get("email", ""),
            unidad_negocio_nombre=unidad.get("nombre", ""),
            server_id=unidad.get("server_id", "")
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    
    # 6. Auditoría
    await servicio_auditoria.registrar(
        usuario=current_user,
        modulo=ModuloAuditoria.CONFIG,
        entidad="config_asignaciones",
        accion=AccionAuditoria.EDIT,
        registro_id=config["id"],
        valor_nuevo={
            "unidad_negocio": config["unidad_negocio_nombre"],
            "almacen": config.get("almacen_nombre") or "(todos)",
            "responsable": config["usuario_responsable_nombre"]
        }
    )
    
    logger.info(
        f"Asignación creada: {config['unidad_negocio_nombre']}/{config.get('almacen_nombre') or '(todos)'} "
        f"→ {config['usuario_responsable_nombre']} por {current_user.get('email')}"
    )
    
    return {
        "success": True,
        "data": config,
        "message": "Configuración creada exitosamente"
    }


@router.put("/{config_id}")
async def actualizar_asignacion(
    config_id: str,
    request: ActualizarAsignacionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza una configuración existente.
    
    Permite cambiar:
    - unidad_negocio_pk
    - almacen_id
    - usuario_responsable_id
    - activa
    
    Valida duplicados si cambia unidad/almacén.
    """
    repo = get_config_asignaciones_repository(get_db())
    
    # Verificar que existe
    config_actual = await repo.obtener_por_id(config_id)
    if not config_actual:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    # Validar alcance sobre la unidad actual
    await validar_alcance_usuario(current_user, config_actual["unidad_negocio_pk"])
    
    # Determinar valores finales
    nueva_unidad = request.unidad_negocio_pk or config_actual["unidad_negocio_pk"]
    nuevo_almacen = request.almacen_id if request.almacen_id is not None else config_actual.get("almacen_id", "")
    nuevo_responsable = request.usuario_responsable_id or config_actual["usuario_responsable_id"]
    
    # Si cambia la unidad, validar alcance sobre la nueva
    if request.unidad_negocio_pk and request.unidad_negocio_pk != config_actual["unidad_negocio_pk"]:
        await validar_alcance_usuario(current_user, request.unidad_negocio_pk)
        
        # Validar que la nueva unidad existe (mismo espacio de IDs que /unidades-negocio)
        if not await obtener_unidad_accesible(current_user, request.unidad_negocio_pk):
            raise HTTPException(status_code=400, detail="Unidad de negocio no encontrada o inactiva")
    
    # Validar almacén si se especifica uno diferente
    if nuevo_almacen:
        almacenes = await repo.listar_almacenes(nueva_unidad)
        almacen_ids = [a["id"] for a in almacenes if a.get("id")]
        if nuevo_almacen not in almacen_ids:
            raise HTTPException(
                status_code=400,
                detail="El almacén no corresponde a la unidad de negocio seleccionada"
            )
    
    # Validar usuario responsable
    if request.usuario_responsable_id:
        await validar_usuario_responsable(request.usuario_responsable_id, nueva_unidad)
    
    # Verificar duplicados si cambia unidad, almacén o responsable
    cambio_clave = (
        (request.unidad_negocio_pk and request.unidad_negocio_pk != config_actual["unidad_negocio_pk"]) or
        (request.almacen_id is not None and request.almacen_id != config_actual.get("almacen_id", "")) or
        (request.usuario_responsable_id and request.usuario_responsable_id != config_actual["usuario_responsable_id"])
    )
    
    if cambio_clave:
        # Verificar que no exista otra configuración con la misma combinación (SQL)
        if await repo.existe_duplicado(
            unidad_negocio_pk=nueva_unidad,
            almacen_id=nuevo_almacen,
            usuario_responsable_id=nuevo_responsable,
            excluir_config_id=config_id
        ):
            raise HTTPException(
                status_code=409,
                detail="Ya existe una asignación con esta combinación de Unidad/Almacén/Usuario"
            )
    
    # Actualizar
    try:
        config = await repo.actualizar(
            config_id=config_id,
            unidad_negocio_pk=request.unidad_negocio_pk,
            almacen_id=request.almacen_id,
            usuario_responsable_id=request.usuario_responsable_id,
            activa=request.activa,
            usuario_modificacion=current_user.get("email", "")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Auditoría
    cambios = {}
    if request.unidad_negocio_pk:
        cambios["nueva_unidad"] = request.unidad_negocio_pk
    if request.almacen_id is not None:
        cambios["nuevo_almacen"] = request.almacen_id or "(todos)"
    if request.usuario_responsable_id:
        cambios["nuevo_responsable"] = request.usuario_responsable_id
    if request.activa is not None:
        cambios["activa"] = request.activa
    
    await servicio_auditoria.registrar(
        usuario=current_user,
        modulo=ModuloAuditoria.CONFIG,
        entidad="config_asignaciones",
        accion=AccionAuditoria.EDIT,
        registro_id=config_id,
        valor_nuevo=cambios
    )
    
    return {
        "success": True,
        "data": config,
        "message": "Configuración actualizada exitosamente"
    }


@router.delete("/{config_id}")
async def eliminar_asignacion(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina una configuración.
    
    Advertencia: Los inventarios futuros de esta combinación
    no tendrán responsable asignado automáticamente.
    """
    repo = get_config_asignaciones_repository(get_db())
    
    # Verificar que existe
    config_actual = await repo.obtener_por_id(config_id)
    if not config_actual:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    # Validar alcance
    await validar_alcance_usuario(current_user, config_actual["unidad_negocio_pk"])
    
    # Eliminar
    eliminado = await repo.eliminar(config_id)
    
    if not eliminado:
        raise HTTPException(status_code=500, detail="Error al eliminar configuración")
    
    # Auditoría
    await servicio_auditoria.registrar(
        usuario=current_user,
        modulo=ModuloAuditoria.CONFIG,
        entidad="config_asignaciones",
        accion=AccionAuditoria.AUTHORIZE,  # DELETE es acción de autorización
        registro_id=config_id,
        valor_anterior={
            "unidad_negocio": config_actual["unidad_negocio_nombre"],
            "almacen": config_actual.get("almacen_nombre") or "(todos)",
            "responsable": config_actual["usuario_responsable_nombre"]
        }
    )
    
    return {
        "success": True,
        "message": "Configuración eliminada exitosamente"
    }


@router.get("/resolver/test")
async def resolver_responsable_test(
    unidad_negocio_pk: str = Query(...),
    almacen_id: str = Query(""),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint de prueba: consulta qué responsable se asignaría.
    
    Útil para verificar la configuración antes de que un inventario real
    dispare la lógica del orquestador.
    """
    # Validar alcance
    await validar_alcance_usuario(current_user, unidad_negocio_pk)
    
    # Obtener server_id de la unidad
    from core.context_resolver import resolve_unidad_context
    try:
        context = await resolve_unidad_context(current_user, unidad_negocio_pk)
    except HTTPException:
        return {
            "success": True,
            "data": {
                "responsable_encontrado": False,
                "mensaje": "No se pudo resolver el contexto de la unidad"
            }
        }
    
    server_id = context.get("server_id")
    if not server_id:
        return {
            "success": True,
            "data": {
                "responsable_encontrado": False,
                "mensaje": "Unidad de negocio sin servidor configurado"
            }
        }
    
    # Resolver responsable
    repo = get_config_asignaciones_repository(get_db())
    responsable = await repo.resolver_responsable(server_id, almacen_id)
    
    if responsable:
        return {
            "success": True,
            "data": {
                "responsable_encontrado": True,
                "usuario_responsable_id": responsable["id"],
                "usuario_responsable_nombre": responsable["nombre"],
                "config_id": responsable["config_id"],
                "regla_aplicada": "específica" if almacen_id else "general"
            }
        }
    else:
        return {
            "success": True,
            "data": {
                "responsable_encontrado": False,
                "mensaje": "No hay configuración de responsable para esta combinación"
            }
        }


# =============================================================================
# ENDPOINT DE SINCRONIZACIÓN DE ALMACENES (Admin only)
# =============================================================================

@router.post("/almacenes/sincronizar/{unidad_negocio_pk}")
async def sincronizar_almacenes(
    unidad_negocio_pk: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Sincroniza almacenes desde el servidor SQL al catálogo local.
    
    SOLO SUPERADMINISTRADOR.
    Este proceso consulta el SQL externo y actualiza el catálogo local.
    Se ejecuta bajo demanda, NO en cada carga de la UI.
    
    ARQUITECTURA:
    - El endpoint solo valida permisos y delega al service
    - El service resuelve internamente el contexto técnico
    - Reutiliza queries probadas de automatizacion/queries_*.py
    - Retorna metadatos completos de la operación
    """
    # Solo SuperAdministrador puede sincronizar
    if not es_superadmin(current_user):
        raise HTTPException(status_code=403, detail="Solo SuperAdministrador puede sincronizar almacenes")
    
    # Validar que la unidad existe (mismo espacio de IDs que /unidades-negocio)
    if not await obtener_unidad_accesible(current_user, unidad_negocio_pk):
        raise HTTPException(status_code=404, detail="Unidad de negocio no encontrada")
    
    # Delegar al service (resuelve contexto internamente)
    from ..services.almacenes_sync_service import sincronizar_almacenes_desde_origen
    
    result = await sincronizar_almacenes_desde_origen(
        db=get_db(),
        user=current_user,
        unidad_negocio_pk=unidad_negocio_pk,
        usuario_sync=current_user.get("email", "SISTEMA")
    )
    
    # Si hubo error, lanzar excepción con detalle
    if not result.success:
        raise HTTPException(
            status_code=500 if result.status.value == "ERROR" else 400,
            detail=result.error_message or "Error desconocido en sincronización"
        )
    
    # Auditoría
    await servicio_auditoria.registrar(
        usuario=current_user,
        modulo=ModuloAuditoria.CONFIG,
        entidad="almacenes_catalogo",
        accion=AccionAuditoria.EDIT,
        registro_id=unidad_negocio_pk,
        valor_nuevo={
            "unidad_negocio_nombre": result.unidad_negocio_nombre,
            "leidos_origen": result.leidos_origen,
            "insertados": result.insertados,
            "actualizados": result.actualizados,
            "desactivados": result.desactivados
        }
    )
    
    # Retornar resultado completo
    return result.to_dict()

