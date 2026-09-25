"""
EDARSA HUB - Cava de Socios Routes
===================================
Endpoints API para el módulo Cava de Socios.

Permisos RBAC: CAVA_SOCIOS_*
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from fastapi.responses import StreamingResponse
from uuid import UUID
import io
import logging

from .service import get_cava_socios_service
from .persona_link_service import get_cava_socios_persona_link_service
from .blind_audit_operational_service import get_cava_blind_audit_operational_service
from core.auth.sql_user_identity import enrich_current_user_with_sql_id
from core.rbac import require_explicit_permission
from modules.rbac_context_sql.context_service import RBACContextService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cava-socios", tags=["Cava de Socios"])
context_service = RBACContextService()


def _resolve_cava_scope(
    current_user: Dict,
    unidad_negocio_pk: Optional[str],
) -> Dict[str, Any]:
    """Resuelve el scope operativo de Cavas desde la unidad autorizada por RBAC SQL."""
    user_with_sql_id = enrich_current_user_with_sql_id(current_user)
    context = context_service.get_user_context(
        user_with_sql_id,
        unidad_negocio_id=unidad_negocio_pk,
    )

    if not context:
        raise HTTPException(status_code=403, detail="Contexto Cavas no autorizado")

    active_unit_raw = context.get("unidad_activa")
    try:
        active_unit = str(UUID(str(active_unit_raw).strip()))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=403, detail="Unidad de negocio no autorizada")

    allowed_units = context.get("unidades_permitidas") or []
    selected = None
    for unit in allowed_units:
        try:
            allowed_unit = str(
                UUID(str(unit.get("UnidadNegocioID") or "").strip())
            )
        except (ValueError, TypeError, AttributeError):
            continue
        if allowed_unit == active_unit:
            selected = unit
            break

    if not selected:
        raise HTTPException(status_code=403, detail="Unidad de negocio no autorizada")

    # CavaSocios_*.EmpresaID es UNIQUEIDENTIFIER y representa el
    # UnidadNegocioID autorizado. No mezclarlo con EmpresaID INT corporativo.
    return {"empresa_id": active_unit, "unidad_negocio_pk": active_unit}


def _resolve_cava_actor(current_user: Dict) -> Dict[str, Any]:
    """Resuelve IDs canónicos del actor sin mezclar UsuarioID int con PublicUUID."""
    enriched = enrich_current_user_with_sql_id(dict(current_user))
    sql_user_id = enriched.get("UsuarioID") or enriched.get("_sql_usuario_id")
    if sql_user_id is None:
        raise HTTPException(status_code=403, detail="Usuario SQL canónico no resuelto")

    public_uuid = (
        enriched.get("PublicUUID")
        or enriched.get("public_uuid")
        or enriched.get("uuid")
        or enriched.get("public_id")
        or enriched.get("user_uuid")
    )
    return {
        "usuario_sql_id": int(sql_user_id),
        "usuario_public_uuid": str(public_uuid) if public_uuid else None,
    }


# ==================== SCHEMAS ====================

class SocioCreate(BaseModel):
    """Schema para crear socio."""
    nombre_completo: str = Field(..., min_length=3, max_length=200)
    numero_socio: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    cliente_crm_id: Optional[str] = None
    tipo_membresia: str = "ESTANDAR"
    fecha_alta: Optional[str] = None
    fecha_vencimiento: Optional[str] = None
    maximo_botellas: int = 12
    observaciones: Optional[str] = None


class SocioUpdate(BaseModel):
    """Schema para actualizar socio."""
    nombre_completo: str = Field(..., min_length=3, max_length=200)
    numero_socio: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    cliente_crm_id: Optional[str] = None
    tipo_membresia: Optional[str] = None
    fecha_vencimiento: Optional[str] = None
    maximo_botellas: Optional[int] = None
    estatus: Optional[str] = None
    observaciones: Optional[str] = None


class PersonaExistingLinkRequest(BaseModel):
    """Vincula una Persona BOS existente; nunca hace matching implícito."""
    persona_id: int = Field(..., gt=0)
    cliente_id: Optional[int] = Field(default=None, gt=0)


class PersonaCreateLinkRequest(BaseModel):
    """Crea una Persona BOS de forma explícita y la vincula al socio."""
    nombre: str = Field(..., min_length=1, max_length=150)
    apellido_paterno: Optional[str] = Field(default=None, max_length=100)
    apellido_materno: Optional[str] = Field(default=None, max_length=100)
    rfc: Optional[str] = Field(default=None, max_length=13)
    curp: Optional[str] = Field(default=None, max_length=18)
    fecha_nacimiento: Optional[str] = None
    nacionalidad: Optional[str] = Field(default=None, max_length=80)
    cliente_id: Optional[int] = Field(default=None, gt=0)



class BotellaCreate(BaseModel):
    """Schema para registrar botella."""
    producto_nombre: str = Field(..., min_length=2)
    producto_codigo: Optional[str] = None
    marca: Optional[str] = None
    tipo_bebida: Optional[str] = None  # VINO_TINTO, WHISKY, etc
    añada: Optional[str] = None
    capacidad: float = 1.0  # 1.0 PZ (Puntaje de botella)
    nivel_actual: float = 100.0  # 100% = 1.0 PZ
    ubicacion: Optional[str] = None
    valor_declarado: float = 0
    foto_url: Optional[str] = None
    observaciones: Optional[str] = None


class ConsumoCreate(BaseModel):
    """Schema para registrar consumo en puntaje de botella (PZ)."""
    porcentaje_consumido: float = Field(100, ge=0, le=100)  # % de botella (100% = 1.0 PZ, 50% = 0.5 PZ)
    motivo: Optional[str] = None
    reservacion_id: Optional[str] = None
    mesero_id: Optional[str] = None
    generar_cargo_descorche: bool = True
    monto_descorche: float = 350
    foto_evidencia: Optional[str] = None
    observaciones: Optional[str] = None


class PromoverClienteCreate(BaseModel):
    """Schema para promover cliente del catálogo maestro a Socio de Cava."""
    cliente_id: Optional[str] = None
    cliente_crm_id: Optional[str] = None
    nombre_completo: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    tipo_membresia: str = "ESTANDAR"
    maximo_botellas: int = 12
    fecha_alta: Optional[str] = None
    fecha_vencimiento: Optional[str] = None
    observaciones: Optional[str] = None


class SincronizarClientesRequest(BaseModel):
    """Schema para sincronización de clientes canónicos."""
    cliente_ids: Optional[List[int]] = None


class InventarioInicialBotellaItem(BaseModel):
    """Detalle de botella para inventario inicial en PZ."""
    producto_nombre: str = Field(..., min_length=2)
    producto_codigo: Optional[str] = None
    marca: Optional[str] = None
    tipo_bebida: Optional[str] = None
    añada: Optional[str] = None
    ubicacion: Optional[str] = None
    valor_declarado: float = 0.0
    puntaje_inicial_pct: float = Field(100.0, ge=1, le=100)  # % de botella (100% = 1.0 PZ)
    cantidad_piezas: int = Field(1, ge=1, le=50)  # Piezas (PZ)
    foto_url: Optional[str] = None
    observaciones: Optional[str] = None


class InventarioInicialCreate(BaseModel):
    """Schema para registrar carga de inventario inicial."""
    socio_id: str
    botellas: List[InventarioInicialBotellaItem]


class InventarioFisicoItem(BaseModel):
    """Registro de conteo de botella física."""
    botella_id: str
    nivel_fisico_pct: float = Field(100.0, ge=0, le=100)
    encontrada: bool = True
    observaciones: Optional[str] = None


class InventarioFisicoAplicarRequest(BaseModel):
    """Schema para conciliar y aplicar ajustes de inventario físico al Kardex."""
    conteos: List[InventarioFisicoItem]
    observaciones_generales: Optional[str] = "Auditoría física de cava"


class BlindAuditObservationInput(BaseModel):
    """Captura ciega: no expone inventario esperado al operador."""
    observation_id: str = Field(..., min_length=1, max_length=120)
    observed_reference: str = Field(..., min_length=1, max_length=255)
    observed_quantity: int = Field(default=1, ge=0)
    observed_level_pct: Optional[float] = Field(default=None, ge=0, le=100)
    evidence_id: Optional[str] = Field(default=None, max_length=160)
    recognition_confidence: Optional[float] = Field(default=None, ge=0, le=1)


class BlindAuditReconcileRequest(BaseModel):
    """Reconciliacion sin escrituras ni ajustes automaticos."""
    socio_id: Optional[str] = None
    ubicacion: Optional[str] = Field(default=None, max_length=200)
    idempotency_key: str = Field(..., min_length=1, max_length=160)
    observations: List[BlindAuditObservationInput]
    observation_to_bottle: Dict[str, str]
    level_tolerance_pct: float = Field(default=5.0, ge=0, le=100)
    min_recognition_confidence: float = Field(default=0.90, ge=0, le=1)


@router.post("/auditorias-ciegas/reconciliar")
async def reconciliar_auditoria_ciega(
    data: BlindAuditReconcileRequest,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER")),
):
    """Compara captura ciega contra inventario canonico sin modificar existencias."""
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    cava_service = get_cava_socios_service()
    inventory = cava_service.obtener_inventario_global(
        empresa_id=scope["empresa_id"],
        ubicacion=data.ubicacion,
        estatus="EN_CAVA",
        socio_id=data.socio_id,
        skip=0,
        limit=1000,
    )
    rows = inventory.get("botellas") or []
    if not rows:
        raise HTTPException(status_code=404, detail="No hay inventario elegible para auditar")

    audit_service = get_cava_blind_audit_operational_service()
    try:
        result = audit_service.reconcile(
            inventory_rows=rows,
            observations=[item.model_dump() for item in data.observations],
            observation_to_bottle=data.observation_to_bottle,
            idempotency_key=data.idempotency_key,
            level_tolerance_pct=data.level_tolerance_pct,
            min_recognition_confidence=data.min_recognition_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return {
        **result,
        "empresa_id": scope["empresa_id"],
        "unidad_negocio_pk": scope["unidad_negocio_pk"],
        "socio_id": data.socio_id,
        "ubicacion": data.ubicacion,
    }


# ==================== ENDPOINTS SOCIOS ====================

@router.get("/dashboard")
async def get_dashboard(
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Obtiene dashboard del módulo Cava de Socios.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        return service.obtener_dashboard(scope["empresa_id"])
    except Exception as e:
        logger.error(f"[CavaSocios] Error en dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/socios")
async def listar_socios(
    unidad_negocio_pk: Optional[str] = Query(None),
    estatus: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Lista socios de cava con paginación.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        return service.listar_socios(scope["empresa_id"], estatus, skip, limit)
    except Exception as e:
        logger.error(f"[CavaSocios] Error listando socios: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/socios/{socio_id}")
async def obtener_socio(
    socio_id: str,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Obtiene detalle de un socio con sus botellas.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        socio = service.obtener_socio(socio_id, scope["empresa_id"])
        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")
        return socio
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error obteniendo socio: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/socios")
async def crear_socio(
    data: SocioCreate,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_CREAR"))
):
    """
    Crea un nuevo socio de cava.

    Permisos: CAVA_SOCIOS_CREAR
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        return service.crear_socio(scope["empresa_id"], data.model_dump(), usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[CavaSocios] Error creando socio: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/socios/{socio_id}")
async def actualizar_socio(
    socio_id: str,
    data: SocioUpdate,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_EDITAR"))
):
    """
    Actualiza datos de un socio existente.

    Permisos: CAVA_SOCIOS_EDITAR
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        return service.actualizar_socio(socio_id, scope["empresa_id"], data.model_dump(), usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[CavaSocios] Error actualizando socio: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/personas-canonicas")
async def listar_personas_canonicas(
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER")),
):
    """Búsqueda explícita de Personas BOS para selección humana."""
    _resolve_cava_actor(current_user)
    try:
        service = get_cava_socios_persona_link_service()
        return {"personas": service.buscar_personas(search=search, limit=limit)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[CavaSocios] Error buscando Personas BOS: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/socios/{socio_id}/persona-link")
async def obtener_persona_link(
    socio_id: str,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER")),
):
    """Consulta el vínculo explícito entre una membresía Cava y BOS Persona."""
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_persona_link_service()
        return service.obtener_link(socio_id, scope["empresa_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[CavaSocios] Error consultando Persona link: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/socios/{socio_id}/persona-link")
async def vincular_persona_existente(
    socio_id: str,
    data: PersonaExistingLinkRequest,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_EDITAR")),
):
    """Vincula una Persona existente; reemplazos requieren desvinculación explícita previa."""
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    actor = _resolve_cava_actor(current_user)
    try:
        service = get_cava_socios_persona_link_service()
        return service.vincular_persona_existente(
            socio_id=socio_id,
            empresa_id=scope["empresa_id"],
            persona_id=data.persona_id,
            cliente_id=data.cliente_id,
            usuario_sql_id=actor["usuario_sql_id"],
            usuario_public_uuid=actor["usuario_public_uuid"],
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"[CavaSocios] Error vinculando Persona existente: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/socios/{socio_id}/persona-link/crear-persona")
async def crear_persona_y_vincular(
    socio_id: str,
    data: PersonaCreateLinkRequest,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_EDITAR")),
):
    """Crea Persona y vínculo en una única transacción; sin matching automático."""
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    actor = _resolve_cava_actor(current_user)
    try:
        service = get_cava_socios_persona_link_service()
        payload = data.model_dump(exclude={"cliente_id"})
        return service.crear_persona_y_vincular(
            socio_id=socio_id,
            empresa_id=scope["empresa_id"],
            persona=payload,
            cliente_id=data.cliente_id,
            usuario_sql_id=actor["usuario_sql_id"],
            usuario_public_uuid=actor["usuario_public_uuid"],
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"[CavaSocios] Error creando/vinculando Persona: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/socios/{socio_id}/persona-link")
async def desvincular_persona(
    socio_id: str,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_EDITAR")),
):
    """Desvincula solo la membresía; nunca elimina Persona ni Gobierno_PersonaVinculo."""
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    actor = _resolve_cava_actor(current_user)
    try:
        service = get_cava_socios_persona_link_service()
        return service.desvincular_persona(
            socio_id=socio_id,
            empresa_id=scope["empresa_id"],
            usuario_public_uuid=actor["usuario_public_uuid"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[CavaSocios] Error desvinculando Persona: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/clientes-canonicos")
async def listar_clientes_canonicos(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Consulta catálogo maestro de clientes disponibles para promover a Cava de Socios.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        return service.listar_clientes_canonicos(scope["empresa_id"], search, skip, limit)
    except Exception as e:
        logger.error(f"[CavaSocios] Error buscando clientes canónicos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/socios/promover-cliente")
async def promover_cliente_canonico(
    data: PromoverClienteCreate,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_CREAR"))
):
    """
    Convierte/promueve un cliente del catálogo canónico a Socio de Cava.

    Permisos: CAVA_SOCIOS_CREAR
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        return service.promover_cliente_canonico(scope["empresa_id"], data.model_dump(), usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[CavaSocios] Error promoviendo cliente a socio: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/clientes-canonicos/sync")
async def sincronizar_clientes_canonicos(
    data: SincronizarClientesRequest,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_CREAR"))
):
    """
    Sincroniza masiva o individualmente clientes del catálogo canónico a Cava de Socios.

    Permisos: CAVA_SOCIOS_CREAR
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        return service.sincronizar_clientes_canonicos(scope["empresa_id"], data.cliente_ids, usuario_id)
    except Exception as e:
        logger.error(f"[CavaSocios] Error sincronizando clientes canónicos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/inventario-inicial")
async def registrar_inventario_inicial(
    data: InventarioInicialCreate,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_CREAR"))
):
    """
    Registra carga masiva o individual de inventario inicial de botellas en custodia (PZ / puntaje de botella).

    Permisos: CAVA_SOCIOS_CREAR
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        botellas_dict = [b.model_dump() for b in data.botellas]
        return service.registrar_inventario_inicial(
            empresa_id=scope["empresa_id"],
            socio_id=data.socio_id,
            botellas=botellas_dict,
            usuario_id=usuario_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[CavaSocios] Error registrando inventario inicial: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/kardex")
async def obtener_kardex(
    socio_id: Optional[str] = Query(None),
    botella_id: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    tipo_movimiento: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Consulta el Kardex general de Cavas con ecuación de balance en PZ.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        return service.obtener_kardex(
            empresa_id=scope["empresa_id"],
            socio_id=socio_id,
            botella_id=botella_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo_movimiento=tipo_movimiento,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"[CavaSocios] Error consultando Kardex: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/inventario-fisico/hoja")
async def obtener_hoja_inventario_fisico(
    ubicacion: Optional[str] = Query(None),
    socio_id: Optional[str] = Query(None),
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Genera hoja de conteo para auditoría física con stock teórico esperado.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        return service.obtener_hoja_inventario_fisico(
            empresa_id=scope["empresa_id"],
            ubicacion=ubicacion,
            socio_id=socio_id
        )
    except Exception as e:
        logger.error(f"[CavaSocios] Error generando hoja de inventario físico: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/inventario-fisico/aplicar")
async def aplicar_ajustes_inventario_fisico(
    data: InventarioFisicoAplicarRequest,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_EDITAR"))
):
    """
    Concilia auditoría física vs stock teórico y aplica ajustes automáticos al Kardex.

    Permisos: CAVA_SOCIOS_EDITAR
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        conteos_dict = [c.model_dump() for c in data.conteos]
        return service.aplicar_ajustes_inventario_fisico(
            empresa_id=scope["empresa_id"],
            conteos=conteos_dict,
            observaciones_generales=data.observaciones_generales or "Auditoría física de cava",
            usuario_id=usuario_id
        )
    except Exception as e:
        logger.error(f"[CavaSocios] Error aplicando ajustes de inventario físico: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/inventario")
async def obtener_inventario(
    ubicacion: Optional[str] = Query(None),
    tipo_bebida: Optional[str] = Query(None),
    estatus: Optional[str] = Query(None),
    socio_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Inventario global consolidado de botellas en custodia por casillero/cava.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        return service.obtener_inventario_global(
            empresa_id=scope["empresa_id"],
            ubicacion=ubicacion,
            tipo_bebida=tipo_bebida,
            estatus=estatus,
            socio_id=socio_id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"[CavaSocios] Error consultando inventario global: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/consumos")
async def obtener_consumos(
    socio_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Historial operativo global de consumos y movimientos de cava.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        return service.obtener_historial_consumos_global(
            empresa_id=scope["empresa_id"],
            socio_id=socio_id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"[CavaSocios] Error consultando consumos globales: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/botellas/{botella_id}/etiqueta")
async def obtener_etiqueta_botella(
    botella_id: str,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Datos para la ficha/etiqueta de resguardo físico de la botella.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        return service.obtener_etiqueta_botella(botella_id, scope["empresa_id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[CavaSocios] Error obteniendo etiqueta de botella: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")




# ==================== ENDPOINTS BOTELLAS ====================

@router.post("/socios/{socio_id}/botellas")
async def registrar_botella(
    socio_id: str,
    data: BotellaCreate,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_CREAR"))
):
    """
    Registra una botella nueva en la cava del socio.

    Permisos: CAVA_SOCIOS_CREAR
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        return service.registrar_botella(
            socio_id,
            scope["empresa_id"],
            data.model_dump(),
            usuario_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[CavaSocios] Error registrando botella: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/botellas/{botella_id}/consumo")
async def registrar_consumo(
    botella_id: str,
    data: ConsumoCreate,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_EDITAR"))
):
    """
    Registra un consumo parcial o total de una botella.

    Permisos: CAVA_SOCIOS_EDITAR
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        service = get_cava_socios_service()
        usuario_id = current_user.get('public_uuid') or current_user.get('id', '')
        return service.registrar_consumo(
            botella_id,
            scope["empresa_id"],
            data.model_dump(),
            usuario_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[CavaSocios] Error registrando consumo: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ==================== REPORTES PDF ====================

from .report_service import get_cava_report_service


@router.get("/reportes/socio/{socio_id}/ficha", summary="Descargar Ficha de Socio PDF")
async def descargar_ficha_socio(
    socio_id: str,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Genera y descarga la ficha completa del socio en PDF.

    Incluye:
    - Datos personales y membresía
    - Resumen de cava
    - Lista de botellas en resguardo

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        # Obtener datos del socio
        cava_service = get_cava_socios_service()
        socio = cava_service.obtener_socio(socio_id, scope["empresa_id"])

        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")

        # Generar PDF
        report_service = get_cava_report_service()
        pdf_bytes = report_service.generar_ficha_socio(socio)

        # Nombre del archivo
        filename = f"ficha_socio_{socio.get('numero_socio', socio_id)}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error generando ficha PDF: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reportes/socio/{socio_id}/consumos", summary="Descargar Historial de Consumos PDF")
async def descargar_historial_consumos(
    socio_id: str,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Genera y descarga el historial de consumos del socio en PDF.

    Incluye:
    - Datos resumidos del socio
    - Lista de todos los consumos
    - Total de cargos por descorche

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        cava_service = get_cava_socios_service()
        socio = cava_service.obtener_socio(socio_id, scope["empresa_id"])

        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")

        # Obtener movimientos del socio
        movimientos = cava_service.obtener_movimientos_socio(
            socio_id,
            scope["empresa_id"],
        )

        # Generar PDF
        report_service = get_cava_report_service()
        pdf_bytes = report_service.generar_historial_consumos(socio, movimientos)

        filename = f"consumos_socio_{socio.get('numero_socio', socio_id)}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error generando historial consumos PDF: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reportes/socio/{socio_id}/estado-cuenta", summary="Descargar Estado de Cuenta PDF")
async def descargar_estado_cuenta(
    socio_id: str,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Genera y descarga el estado de cuenta del socio en PDF.

    Incluye:
    - Resumen financiero
    - Detalle de cargos (pagados y pendientes)
    - Saldo total

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        cava_service = get_cava_socios_service()
        socio = cava_service.obtener_socio(socio_id, scope["empresa_id"])

        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")

        # Obtener cargos del socio
        cargos = cava_service.obtener_cargos_socio(
            socio_id,
            scope["empresa_id"],
        )

        # Generar PDF
        report_service = get_cava_report_service()
        pdf_bytes = report_service.generar_estado_cuenta(socio, cargos)

        filename = f"estado_cuenta_{socio.get('numero_socio', socio_id)}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error generando estado de cuenta PDF: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ==================== ENVÍO DE REPORTES (EMAIL / WHATSAPP) ====================

from .notification_service import get_notification_service


class EnvioReporteRequest(BaseModel):
    """Schema para solicitar envío de reporte."""
    tipo_reporte: str = Field(..., description="Tipo: ficha, consumos, estado_cuenta")
    canales: List[str] = Field(default=["email"], description="Canales: email, whatsapp")
    email_alternativo: Optional[str] = None
    telefono_alternativo: Optional[str] = None


@router.post("/socios/{socio_id}/enviar-reporte", summary="Enviar Reporte por Email/WhatsApp")
async def enviar_reporte_socio(
    socio_id: str,
    data: EnvioReporteRequest,
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Genera y envía un reporte PDF al socio por Email y/o WhatsApp.

    Tipos de reporte disponibles:
    - ficha: Ficha completa del socio
    - consumos: Historial de consumos
    - estado_cuenta: Estado de cuenta con cargos

    Canales disponibles:
    - email: Envía el PDF como adjunto
    - whatsapp: Envía mensaje con información del reporte

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        cava_service = get_cava_socios_service()
        socio = cava_service.obtener_socio(socio_id, scope["empresa_id"])

        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")

        # Sobrescribir email/teléfono si se proporcionan alternativos
        if data.email_alternativo:
            socio['email'] = data.email_alternativo
        if data.telefono_alternativo:
            socio['telefono'] = data.telefono_alternativo

        # Validar que tenga al menos un medio de contacto
        if 'email' in data.canales and not socio.get('email'):
            raise HTTPException(status_code=400, detail="El socio no tiene email registrado")
        if 'whatsapp' in data.canales and not socio.get('telefono'):
            raise HTTPException(status_code=400, detail="El socio no tiene teléfono registrado")

        # Generar PDF según tipo
        report_service = get_cava_report_service()

        if data.tipo_reporte == 'ficha':
            pdf_bytes = report_service.generar_ficha_socio(socio)
        elif data.tipo_reporte == 'consumos':
            movimientos = cava_service.obtener_movimientos_socio(
                socio_id,
                scope["empresa_id"],
            )
            pdf_bytes = report_service.generar_historial_consumos(socio, movimientos)
        elif data.tipo_reporte == 'estado_cuenta':
            cargos = cava_service.obtener_cargos_socio(
                socio_id,
                scope["empresa_id"],
            )
            pdf_bytes = report_service.generar_estado_cuenta(socio, cargos)
        else:
            raise HTTPException(status_code=400, detail=f"Tipo de reporte inválido: {data.tipo_reporte}")

        # Enviar por canales seleccionados
        notification_service = get_notification_service()
        resultado = notification_service.enviar_reporte_multicanal(
            socio=socio,
            tipo_reporte=data.tipo_reporte,
            pdf_bytes=pdf_bytes,
            canales=data.canales
        )

        logger.info(f"[CavaSocios] Reporte {data.tipo_reporte} enviado al socio {socio_id} via {data.canales}")

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error enviando reporte: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/socios/{socio_id}/enviar-todos-reportes", summary="Enviar Todos los Reportes")
async def enviar_todos_reportes_socio(
    socio_id: str,
    canales: List[str] = Query(default=["email"], description="Canales: email, whatsapp"),
    unidad_negocio_pk: Optional[str] = Query(None),
    current_user: Dict = Depends(require_explicit_permission("CAVA_SOCIOS_VER"))
):
    """
    Genera y envía los 3 reportes (Ficha, Consumos, Estado de Cuenta) al socio.

    Útil para envío mensual automático o solicitud completa del socio.

    Permisos: CAVA_SOCIOS_VER
    """
    scope = _resolve_cava_scope(current_user, unidad_negocio_pk)
    try:
        cava_service = get_cava_socios_service()
        socio = cava_service.obtener_socio(socio_id, scope["empresa_id"])

        if not socio:
            raise HTTPException(status_code=404, detail="Socio no encontrado")

        report_service = get_cava_report_service()
        notification_service = get_notification_service()

        resultados = {
            "socio_id": socio_id,
            "numero_socio": socio.get('numero_socio'),
            "reportes": {}
        }

        # 1. Ficha de Socio
        pdf_ficha = report_service.generar_ficha_socio(socio)
        resultados["reportes"]["ficha"] = notification_service.enviar_reporte_multicanal(
            socio=socio, tipo_reporte='ficha', pdf_bytes=pdf_ficha, canales=canales
        )

        # 2. Historial de Consumos
        movimientos = cava_service.obtener_movimientos_socio(
            socio_id,
            scope["empresa_id"],
        )
        pdf_consumos = report_service.generar_historial_consumos(socio, movimientos)
        resultados["reportes"]["consumos"] = notification_service.enviar_reporte_multicanal(
            socio=socio, tipo_reporte='consumos', pdf_bytes=pdf_consumos, canales=canales
        )

        # 3. Estado de Cuenta
        cargos = cava_service.obtener_cargos_socio(
            socio_id,
            scope["empresa_id"],
        )
        pdf_estado = report_service.generar_estado_cuenta(socio, cargos)
        resultados["reportes"]["estado_cuenta"] = notification_service.enviar_reporte_multicanal(
            socio=socio, tipo_reporte='estado_cuenta', pdf_bytes=pdf_estado, canales=canales
        )

        # Resumen
        exitos = sum(1 for r in resultados["reportes"].values() if r.get("success"))
        resultados["exitos"] = exitos
        resultados["total_reportes"] = 3

        logger.info(f"[CavaSocios] Todos los reportes enviados al socio {socio_id}: {exitos}/3 exitosos")

        return resultados

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CavaSocios] Error enviando todos los reportes: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
