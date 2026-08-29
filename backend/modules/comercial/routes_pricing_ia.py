from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
FASE 1C-3I-B: Endpoints de Pricing IA y Benchmark

Este módulo expone los endpoints CRUD para:
- Perfiles Digitales de Unidad de Negocio
- Competidores
- Menu Items de Competidores
- Benchmark de Productos
- Cálculo de Precios Sugeridos Base (SIN IA)

REGLAS:
- RBAC obligatorio en todos los endpoints
- NO ejecutar IA (IA en SUBFASE 1C-3I-C)
- DELETE es baja lógica
- Auditoría en todas las operaciones
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import logging
import math

from core.security import get_current_user
from core.rbac.middleware import require_permission

# Schemas
from modules.comercial.services.pricing_schemas import (
    # Perfil Digital
    PerfilDigitalCreate,
    PerfilDigitalUpdate,
    PerfilDigitalResponse,
    PerfilesDigitalesListResponse,
    # Competidores
    CompetidorCreate,
    CompetidorUpdate,
    CompetidorResponse,
    CompetidoresListResponse,
    # Menu Items
    CompetidorMenuItemCreate,
    CompetidorMenuItemUpdate,
    CompetidorMenuItemResponse,
    MenuItemsListResponse,
    # Benchmark
    PricingBenchmarkProductoCreate,
    PricingBenchmarkProductoUpdate,
    PricingBenchmarkProductoResponse,
    BenchmarksListResponse,
    BenchmarkResumenResponse,
    BenchmarkEstadoPreparacionResponse,
    # Precios Sugeridos
    PrecioSugeridoCalcularRequest,
    PrecioSugeridoCalcularResponse,
)

# Services
from modules.comercial.services.perfil_unidad_service import (
    listar_perfiles_digitales,
    obtener_perfil_por_unidad,
    obtener_perfil_por_id,
    crear_perfil_digital,
    actualizar_perfil_digital,
    inactivar_perfil_digital,
)

from modules.comercial.services.competidores_service import (
    listar_competidores,
    obtener_competidor_por_id,
    crear_competidor,
    actualizar_competidor,
    inactivar_competidor,
    listar_menu_items,
    obtener_menu_item_por_id,
    crear_menu_item,
    actualizar_menu_item,
    inactivar_menu_item,
)

from modules.comercial.services.benchmark_service import (
    listar_benchmarks,
    obtener_benchmark_por_id,
    crear_benchmark,
    actualizar_benchmark,
    validar_benchmark,
    inactivar_benchmark,
    obtener_resumen_benchmark,
    obtener_estado_preparacion_ia,
)

from modules.comercial.services.pricing_sugerido_service import (
    calcular_precio_sugerido_base,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comercial", tags=["Comercial - Pricing IA"])


# =============================================================================
# PERFIL DIGITAL DE UNIDAD DE NEGOCIO
# =============================================================================

@router.get(
    "/perfil-unidad",
    response_model=PerfilesDigitalesListResponse,
    summary="Listar perfiles digitales"
)
async def listar_perfiles(
    empresa_id: Optional[int] = Query(None, description="Filtrar por empresa"),
    unidad_negocio_pk: Optional[int] = Query(None, description="Filtrar por unidad"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.perfil_unidad.ver"))
):
    """Lista perfiles digitales de unidades de negocio."""
    perfiles, total = listar_perfiles_digitales(
        empresa_id=empresa_id,
        unidad_negocio_pk=unidad_negocio_pk,
        page=page,
        page_size=page_size
    )
    
    return PerfilesDigitalesListResponse(
        perfiles=perfiles,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get(
    "/perfil-unidad/{unidad_negocio_pk}",
    response_model=PerfilDigitalResponse,
    summary="Obtener perfil digital por unidad"
)
async def obtener_perfil(
    unidad_negocio_pk: int,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.perfil_unidad.ver"))
):
    """Obtiene el perfil digital de una unidad de negocio."""
    perfil = obtener_perfil_por_unidad(unidad_negocio_pk)
    
    if not perfil:
        raise HTTPException(
            status_code=404,
            detail=f"No existe perfil digital para la unidad {unidad_negocio_pk}"
        )
    
    return perfil


@router.post(
    "/perfil-unidad",
    response_model=PerfilDigitalResponse,
    summary="Crear perfil digital"
)
async def crear_perfil(
    data: PerfilDigitalCreate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.perfil_unidad.editar"))
):
    """Crea un nuevo perfil digital de unidad de negocio."""
    try:
        perfil = crear_perfil_digital(data, current_user.get('email', 'sistema'))
        logger.info(f"[API] Perfil digital creado para unidad {data.unidad_negocio_pk}")
        return perfil
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except Exception as e:
        logger.error(f"[API] Error creando perfil: {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear perfil")


@router.put(
    "/perfil-unidad/{perfil_id}",
    response_model=PerfilDigitalResponse,
    summary="Actualizar perfil digital"
)
async def actualizar_perfil(
    perfil_id: str,
    data: PerfilDigitalUpdate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.perfil_unidad.editar"))
):
    """Actualiza un perfil digital existente."""
    perfil = actualizar_perfil_digital(perfil_id, data, current_user.get('email', 'sistema'))
    
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    
    return perfil


# =============================================================================
# COMPETIDORES
# =============================================================================

@router.get(
    "/competidores",
    response_model=CompetidoresListResponse,
    summary="Listar competidores"
)
async def listar_todos_competidores(
    empresa_id: Optional[int] = Query(None),
    unidad_negocio_pk: Optional[int] = Query(None),
    solo_directos: Optional[bool] = Query(None, description="Solo competencia directa"),
    solo_aspiracionales: Optional[bool] = Query(None, description="Solo benchmark aspiracional"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver"))
):
    """Lista competidores con filtros opcionales."""
    competidores, total = listar_competidores(
        empresa_id=empresa_id,
        unidad_negocio_pk=unidad_negocio_pk,
        solo_directos=solo_directos,
        solo_aspiracionales=solo_aspiracionales,
        page=page,
        page_size=page_size
    )
    
    return CompetidoresListResponse(
        competidores=competidores,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get(
    "/competidores/{competidor_id}",
    response_model=CompetidorResponse,
    summary="Obtener competidor"
)
async def obtener_competidor(
    competidor_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver"))
):
    """Obtiene un competidor por su ID."""
    competidor = obtener_competidor_por_id(competidor_id)
    
    if not competidor:
        raise HTTPException(status_code=404, detail="Competidor no encontrado")
    
    return competidor


@router.post(
    "/competidores",
    response_model=CompetidorResponse,
    summary="Crear competidor"
)
async def crear_nuevo_competidor(
    data: CompetidorCreate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.crear"))
):
    """Crea un nuevo competidor."""
    try:
        competidor = crear_competidor(data, current_user.get('email', 'sistema'))
        logger.info(f"[API] Competidor creado: {data.nombre_competidor}")
        return competidor
    except Exception as e:
        logger.error(f"[API] Error creando competidor: {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear competidor")


@router.put(
    "/competidores/{competidor_id}",
    response_model=CompetidorResponse,
    summary="Actualizar competidor"
)
async def actualizar_competidor_existente(
    competidor_id: str,
    data: CompetidorUpdate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.editar"))
):
    """Actualiza un competidor existente."""
    competidor = actualizar_competidor(competidor_id, data, current_user.get('email', 'sistema'))
    
    if not competidor:
        raise HTTPException(status_code=404, detail="Competidor no encontrado")
    
    return competidor


@router.delete(
    "/competidores/{competidor_id}",
    summary="Inactivar competidor"
)
async def eliminar_competidor(
    competidor_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.inactivar"))
):
    """Inactiva un competidor (baja lógica)."""
    inactivar_competidor(competidor_id, current_user.get('email', 'sistema'))
    logger.info(f"[API] Competidor inactivado: {competidor_id}")
    return {"mensaje": "Competidor inactivado correctamente"}


# =============================================================================
# MENU ITEMS DE COMPETIDORES
# =============================================================================

@router.get(
    "/competidores/{competidor_id}/menu-items",
    response_model=MenuItemsListResponse,
    summary="Listar items de menú de competidor"
)
async def listar_items_competidor(
    competidor_id: str,
    categoria: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver"))
):
    """Lista items de menú de un competidor."""
    items, total = listar_menu_items(
        competidor_id=competidor_id,
        categoria=categoria,
        page=page,
        page_size=page_size
    )
    
    return MenuItemsListResponse(
        menu_items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.post(
    "/competidores/{competidor_id}/menu-items",
    response_model=CompetidorMenuItemResponse,
    summary="Crear item de menú"
)
async def crear_item_menu(
    competidor_id: str,
    data: CompetidorMenuItemCreate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.crear"))
):
    """Crea un nuevo item de menú para un competidor."""
    # Asegurar que el competidor_id del path coincide con el del body
    if data.competidor_id != competidor_id:
        data.competidor_id = competidor_id
    
    try:
        item = crear_menu_item(data, current_user.get('email', 'sistema'))
        logger.info(f"[API] Menu item creado: {data.nombre_producto_competidor}")
        return item
    except Exception as e:
        logger.error(f"[API] Error creando menu item: {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear item")


@router.put(
    "/competidores/menu-items/{menu_item_id}",
    response_model=CompetidorMenuItemResponse,
    summary="Actualizar item de menú"
)
async def actualizar_item_menu(
    menu_item_id: str,
    data: CompetidorMenuItemUpdate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.editar"))
):
    """Actualiza un item de menú existente."""
    item = actualizar_menu_item(menu_item_id, data, current_user.get('email', 'sistema'))
    
    if not item:
        raise HTTPException(status_code=404, detail="Item de menú no encontrado")
    
    return item


@router.delete(
    "/competidores/menu-items/{menu_item_id}",
    summary="Inactivar item de menú"
)
async def eliminar_item_menu(
    menu_item_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.inactivar"))
):
    """Inactiva un item de menú (baja lógica)."""
    inactivar_menu_item(menu_item_id, current_user.get('email', 'sistema'))
    logger.info(f"[API] Menu item inactivado: {menu_item_id}")
    return {"mensaje": "Item de menú inactivado correctamente"}


# =============================================================================
# BENCHMARK DE PRODUCTOS
# =============================================================================

@router.get(
    "/benchmark/productos",
    response_model=BenchmarksListResponse,
    summary="Listar benchmarks de productos"
)
async def listar_benchmarks_productos(
    empresa_id: Optional[int] = Query(None),
    unidad_negocio_pk: Optional[int] = Query(None),
    codigo_producto: Optional[str] = Query(None),
    competidor_id: Optional[str] = Query(None),
    solo_validados: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver"))
):
    """Lista mapeos de benchmark producto vs competencia."""
    benchmarks, total = listar_benchmarks(
        empresa_id=empresa_id,
        unidad_negocio_pk=unidad_negocio_pk,
        codigo_producto=codigo_producto,
        competidor_id=competidor_id,
        solo_validados=solo_validados,
        page=page,
        page_size=page_size
    )
    
    return BenchmarksListResponse(
        benchmarks=benchmarks,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0
    )


@router.get(
    "/benchmark/productos/{producto_id}",
    response_model=PricingBenchmarkProductoResponse,
    summary="Obtener benchmark de producto"
)
async def obtener_benchmark_producto(
    producto_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver"))
):
    """Obtiene un benchmark por su ID."""
    benchmark = obtener_benchmark_por_id(producto_id)
    
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado")
    
    return benchmark


@router.post(
    "/benchmark/productos",
    response_model=PricingBenchmarkProductoResponse,
    summary="Crear benchmark de producto"
)
async def crear_benchmark_producto(
    data: PricingBenchmarkProductoCreate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver"))
):
    """Crea un nuevo mapeo de benchmark."""
    try:
        benchmark = crear_benchmark(data, current_user.get('email', 'sistema'))
        logger.info(f"[API] Benchmark creado para producto {data.codigo_producto}")
        return benchmark
    except Exception as e:
        logger.error(f"[API] Error creando benchmark: {e}")
        raise HTTPException(status_code=500, detail="Error interno al crear benchmark")


@router.put(
    "/benchmark/productos/{benchmark_id}",
    response_model=PricingBenchmarkProductoResponse,
    summary="Actualizar benchmark"
)
async def actualizar_benchmark_producto(
    benchmark_id: str,
    data: PricingBenchmarkProductoUpdate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver"))
):
    """Actualiza un benchmark existente."""
    benchmark = actualizar_benchmark(benchmark_id, data, current_user.get('email', 'sistema'))
    
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado")
    
    return benchmark


@router.post(
    "/benchmark/productos/{benchmark_id}/validar",
    response_model=PricingBenchmarkProductoResponse,
    summary="Validar benchmark"
)
async def validar_benchmark_producto(
    benchmark_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.validar"))
):
    """Marca un benchmark como validado por el usuario."""
    benchmark = validar_benchmark(benchmark_id, current_user.get('email', 'sistema'))
    
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado")
    
    logger.info(f"[API] Benchmark validado: {benchmark_id}")
    return benchmark


@router.delete(
    "/benchmark/productos/{benchmark_id}",
    summary="Inactivar benchmark"
)
async def eliminar_benchmark_producto(
    benchmark_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver"))
):
    """Inactiva un benchmark (baja lógica)."""
    inactivar_benchmark(benchmark_id, current_user.get('email', 'sistema'))
    logger.info(f"[API] Benchmark inactivado: {benchmark_id}")
    return {"mensaje": "Benchmark inactivado correctamente"}


# =============================================================================
# RESUMEN DE BENCHMARK
# =============================================================================

@router.get(
    "/benchmark/resumen/{unidad_negocio_pk}",
    response_model=BenchmarkResumenResponse,
    summary="Resumen de benchmark por unidad"
)
async def obtener_resumen(
    unidad_negocio_pk: int,
    empresa_id: int = Query(..., description="ID de la empresa"),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver"))
):
    """
    Obtiene resumen de benchmark para una unidad de negocio.
    
    Incluye:
    - Competidores configurados
    - Items de competencia capturados
    - Productos mapeados
    - Cobertura de benchmark
    - Estado general
    
    NO ejecuta IA.
    """
    resumen = obtener_resumen_benchmark(unidad_negocio_pk, empresa_id)
    return resumen


@router.get(
    "/benchmark/estado-preparacion/{unidad_negocio_pk}",
    response_model=BenchmarkEstadoPreparacionResponse,
    summary="Estado de preparación para IA"
)
async def obtener_estado_preparacion(
    unidad_negocio_pk: int,
    empresa_id: int = Query(..., description="ID de la empresa"),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver"))
):
    """
    Verifica si la unidad está lista para análisis IA.
    
    Evalúa:
    - Perfil digital completo
    - Competidores mínimos (3)
    - Items de competencia mínimos (10)
    - Mapeos validados
    
    NO ejecuta IA. Solo verifica requisitos.
    """
    estado = obtener_estado_preparacion_ia(unidad_negocio_pk, empresa_id)
    return estado


# =============================================================================
# CÁLCULO DE PRECIOS SUGERIDOS
# =============================================================================

@router.post(
    "/precios-sugeridos/calcular-base",
    response_model=PrecioSugeridoCalcularResponse,
    summary="Calcular precio sugerido base"
)
async def calcular_precio_base(
    request: PrecioSugeridoCalcularRequest,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.precios_sugeridos.generar"))
):
    """
    Calcula el precio sugerido base para un producto (SIN IA).
    
    Tipos de motor disponibles:
    - VINOS_RANGOS: Usa regla de rangos existente (para vinos)
    - COSTO_MARGEN: Fórmula precio = costo / (1 - margen)
    - BENCHMARK_COMPETENCIA: Basado en promedio de competidores
    - MIXTO_COSTO_COMPETENCIA: Combina costo+margen con benchmark
    
    IMPORTANTE:
    - NO ejecuta IA (IA será en SUBFASE 1C-3I-C)
    - Usa resolver_tasa_impuesto() para impuestos
    - NO hardcodea 16%
    - NO modifica precios oficiales
    
    Para vinos, use tipo_motor=VINOS_RANGOS.
    Para otros productos, use COSTO_MARGEN o MIXTO_COSTO_COMPETENCIA.
    """
    resultado = calcular_precio_sugerido_base(request)
    
    logger.info(
        f"[API] Precio sugerido calculado: {request.codigo_producto} "
        f"motor={request.tipo_motor.value} estado={resultado.estado.value}"
    )
    
    return resultado


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get(
    "/pricing-ia/health",
    summary="Health check del módulo Pricing IA"
)
async def health_check():
    """Verifica que el módulo de Pricing IA está operativo."""
    return {
        "modulo": "comercial-pricing-ia",
        "fase": "1C-3I-B",
        "estado": "operativo",
        "ia_ejecutada": False,
        "endpoints": {
            "perfil_unidad": "activo",
            "competidores": "activo",
            "menu_items": "activo",
            "benchmark": "activo",
            "precios_sugeridos": "activo"
        }
    }
