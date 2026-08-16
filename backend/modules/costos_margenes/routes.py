"""
Endpoints del módulo Costos y Márgenes.
FASE 1C-3C - Endpoints NO-LIVE
FASE 1C-3E - RBAC, Seguridad y Exportación
FASE P2 - RBAC por Unidad de Negocio

IMPORTANTE:
- Todos los endpoints leen EXCLUSIVAMENTE de EDARSAHUB SQL
- NO se realizan conexiones live a sistemas externos
- NO se usa MongoDB
- Se respeta RBAC y permisos por empresa/unidad
- Los usuarios solo ven datos de sus unidades de negocio asignadas
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional
import math
import io
import csv
from datetime import datetime
import logging

from modules.costos_margenes.schemas import (
    CostosMargenesResumen,
    ProductoCostoMargen,
    ProductosListResponse,
    RecetaExpandida,
    ComponenteReceta,
    InsumosProductoResponse,
    InsumoConsolidado,
    SyncStatusResponse,
    ConteoTabla,
    ConteoPorSistema,
    ConteoPorServidor,
    SourceType,
    ConfiguracionCostosMargenesUsuarioPatch,
)
from modules.costos_margenes.repository import (
    get_resumen_costos_margenes,
    get_productos_con_costos,
    get_receta_producto,
    get_receta_elaborado,
    get_insumos_producto,
    get_sync_status,
    get_unidades_negocio,
    get_familias_productos,
    get_subfamilias_productos,
)
from core.security import get_current_user
from modules.costos_margenes.configuracion_repository import (
    resolver_configuracion_efectiva,
    guardar_configuracion_usuario,
)
from core.rbac_sql.service import RBACSQLService
from core.rbac_helper_sql import tiene_acceso_lectura_comercial
from core.corporate_filters.request_resolver import (
    resolve_authorized_unidad_scope,
    resolve_unidad_scope,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/costos-margenes", tags=["Costos y Márgenes"])


# ==================== RBAC HELPERS ====================

COSTOS_MARGENES_VER = "comercial.costos_margenes_VER"
COSTOS_MARGENES_CONFIGURAR = "comercial.costos_margenes_CONFIGURAR"


def _check_admin_or_comercial(user: dict) -> bool:
    """Helper legacy de lectura; los endpoints usan RBAC SQL canónico."""
    return tiene_acceso_lectura_comercial(user)


def _get_sql_usuario_id(user: dict) -> Optional[int]:
    value = (
        (user or {}).get("_sql_usuario_id")
        or (user or {}).get("UsuarioID")
        or (user or {}).get("usuario_id")
    )
    if isinstance(value, bool):
        return None
    try:
        usuario_id = int(value)
    except (TypeError, ValueError):
        return None
    return usuario_id if usuario_id > 0 else None


def _verify_costos_margenes_access(
    user: dict,
    permission_code: str = COSTOS_MARGENES_VER,
) -> dict:
    """Exige permiso funcional desde RBAC SQL canónico."""
    usuario_id = _get_sql_usuario_id(user)
    normalized = str(permission_code or "").strip().upper()
    if usuario_id is None or not normalized:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "PERMISO_DENEGADO",
                "mensaje": "No existe identidad SQL canónica para Costos y Márgenes",
                "permiso_requerido": normalized or COSTOS_MARGENES_VER,
            },
        )

    try:
        permission = RBACSQLService.get_permission_scope_by_code(
            usuario_id,
            normalized,
        )
    except Exception as exc:
        logger.error("[COSTOS_MARGENES_RBAC] Error resolviendo permiso: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "error": "RBAC_NO_DISPONIBLE",
                "mensaje": "No fue posible resolver permisos de Costos y Márgenes",
                "permiso_requerido": normalized,
            },
        ) from exc

    if not permission:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "PERMISO_DENEGADO",
                "mensaje": "No tiene acceso al módulo de Costos y Márgenes",
                "permiso_requerido": normalized,
            },
        )

    return permission


def _resolve_configuracion_efectiva(
    current_user: dict,
    unidad_pk: Optional[str],
) -> Optional[dict]:
    """
    Resuelve configuración efectiva únicamente cuando existe
    una unidad canónica autorizada.

    Precedencia:
        usuario > unidad > empresa

    La ausencia de unidad o configuración no inventa defaults.
    """
    if not unidad_pk:
        return None

    usuario_id = _get_sql_usuario_id(current_user)

    if usuario_id is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "SQL_USUARIO_NO_RESUELTO",
                "mensaje": (
                    "No existe identidad SQL canónica para "
                    "resolver configuración de Costos y Márgenes"
                ),
            },
        )

    try:
        return resolver_configuracion_efectiva(
            str(unidad_pk),
            usuario_id=usuario_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "CONFIGURACION_EFECTIVA_NO_RESUELTA",
                "mensaje": str(exc),
            },
        ) from exc


async def _resolve_servidor_filtro(
    current_user: dict,
    unidad: Optional[str],
    servidor_id: Optional[str],
    permission: Optional[dict] = None,
):
    """
    Resolución canónica de unidad para Costos y Márgenes.

    El contrato preferido es ``unidad`` (codigo o unidad_negocio_pk). ``servidor_id``
    queda solo para compatibilidad y no se usa para saltar alcance RBAC.

    Returns: (servidor_id_filtro, servidores_ids_filtro, access_denied, unidad_pk)
    """
    permission = permission or _verify_costos_margenes_access(current_user)

    if unidad:
        scope = await resolve_authorized_unidad_scope(
            current_user,
            COSTOS_MARGENES_VER,
            unidad,
        )
        if scope.access_denied:
            return None, None, True, None
        return scope.server_id, None, False, scope.unidad_pk

    if servidor_id:
        if permission.get("restriccion_sucursal"):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "UNIDAD_CANONICA_REQUERIDA",
                    "mensaje": "Use unidad o unidad_negocio_pk para validar alcance RBAC",
                },
            )
        scope = await resolve_unidad_scope(current_user, server_id_legacy=servidor_id)
        if scope.access_denied:
            return None, None, True, None
        return scope.server_id or servidor_id, None, False, scope.unidad_pk

    if permission.get("restriccion_sucursal"):
        return None, None, True, None

    return None, None, False, None


async def _resolve_receta_servidor_filtro(
    current_user: dict,
    unidad: Optional[str],
    unidad_negocio_pk: Optional[str],
    server_id: Optional[str],
    permission: Optional[dict] = None,
) -> Optional[str]:
    """Resuelve server_id para receta/insumos desde la unidad canónica."""
    servidor_id_filtro, _, access_denied, _ = await _resolve_servidor_filtro(
        current_user,
        unidad or unidad_negocio_pk,
        server_id,
        permission,
    )
    if access_denied:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "ALCANCE_DENEGADO",
                "mensaje": "No tiene acceso a la unidad solicitada",
                "permiso_requerido": COSTOS_MARGENES_VER,
            },
        )
    return servidor_id_filtro




def _resolver_margen_efectivo_productos(
    productos,
    *,
    empresa_id,
    servidor_id,
    unidad_pk,
    usuario_id,
):
    """
    Enriquece productos con el unico margen efectivo canonico.

    No implementa una segunda cascada. Delega toda precedencia
    al resolver batch del dominio.
    """
    items = list(productos or [])

    if not items:
        return items

    if not unidad_pk:
        for item in items:
            item["margen_efectivo"] = None
            item["fuente_margen_efectivo"] = None
            item["margen_objetivo"] = None
        return items

    entradas_margen = [
        {
            "producto_id":
                item.get("producto_id_canonico"),
            "producto_clave":
                item.get("id_producto_origen"),
            "subfamilia_codigo":
                item.get("subfamilia_codigo"),
            "familia_codigo":
                item.get("familia_codigo"),
            "grupo_codigo":
                item.get("grupo_codigo"),
        }
        for item in items
    ]

    from modules.costos_margenes.reglas_margen_service import (
        resolver_margenes_esperados_batch,
    )

    resultados = resolver_margenes_esperados_batch(
        entradas_margen,
        empresa_id=empresa_id,
        sucursal_id=None,
        server_id=servidor_id,
        unidad_negocio_pk=unidad_pk,
        usuario_id=usuario_id,
    )

    if len(resultados) != len(items):
        raise HTTPException(
            status_code=500,
            detail="CARDINALIDAD_MARGEN_INCONSISTENTE",
        )

    for item, resultado in zip(
        items,
        resultados,
    ):
        item["margen_efectivo"] = (
            resultado.get("margen_efectivo")
        )
        item["fuente_margen_efectivo"] = (
            resultado.get(
                "fuente_margen_efectivo"
            )
        )
        item["margen_objetivo"] = (
            item["margen_efectivo"]
        )

    return items


def _contar_productos_margen_bajo_canonico(
    *,
    empresa_id,
    unidad_pk,
    servidor_id,
    servidores_ids,
    usuario_id,
    page_size=200,
):
    """
    Cuenta productos cuyo margen neto actual es menor que
    su margen efectivo canonico.

    Lee por paginas acotadas. No usa umbrales fijos.
    """
    if not unidad_pk:
        return 0

    page = 1
    total_revisados = 0
    total_margen_bajo = 0

    while True:
        productos, total = get_productos_con_costos(
            empresa_id=empresa_id,
            unidad_negocio_pk=unidad_pk,
            servidor_id=servidor_id,
            servidores_ids=servidores_ids,
            margen_bajo=False,
            incluir_inactivos=False,
            page=page,
            page_size=page_size,
        )

        if not productos:
            break

        _resolver_margen_efectivo_productos(
            productos,
            empresa_id=empresa_id,
            servidor_id=servidor_id,
            unidad_pk=unidad_pk,
            usuario_id=usuario_id,
        )

        for item in productos:
            margen_real = item.get(
                "margen_porcentaje"
            )
            margen_efectivo = item.get(
                "margen_efectivo"
            )

            if (
                margen_real is not None
                and margen_efectivo is not None
                and float(margen_real)
                < float(margen_efectivo)
            ):
                total_margen_bajo += 1

        total_revisados += len(productos)

        if total_revisados >= total:
            break

        page += 1

    return total_margen_bajo



# ==================== CONFIGURACION PERSONAL ====================

@router.patch("/configuracion/usuario")
async def actualizar_configuracion_personal(
    payload: ConfiguracionCostosMargenesUsuarioPatch,
    unidad: str = Query(
        ...,
        description="Unidad de negocio canónica para resolver configuración efectiva",
    ),
    current_user: dict = Depends(get_current_user),
):
    """
    Guarda únicamente overrides personales del usuario autenticado.

    Requiere comercial.costos_margenes_CONFIGURAR.
    """
    permission = _verify_costos_margenes_access(
        current_user,
        COSTOS_MARGENES_CONFIGURAR,
    )

    scope = await resolve_authorized_unidad_scope(
        current_user,
        COSTOS_MARGENES_CONFIGURAR,
        unidad,
    )

    if scope.access_denied or not scope.unidad_pk:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "ALCANCE_DENEGADO",
                "mensaje": "No tiene acceso a la unidad solicitada",
                "permiso_requerido": COSTOS_MARGENES_CONFIGURAR,
            },
        )

    usuario_id = _get_sql_usuario_id(current_user)

    if usuario_id is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "SQL_USUARIO_NO_RESUELTO",
                "mensaje": (
                    "No existe identidad SQL canónica para "
                    "guardar configuración personal"
                ),
            },
        )

    campos = {
        "margen_minimo_porcentaje":
            "MargenMinimoPorcentaje",
        "multiplo_redondeo":
            "MultiploRedondeo",
        "metodo_redondeo":
            "MetodoRedondeo",
    }

    fields_set = getattr(
        payload,
        "model_fields_set",
        getattr(payload, "__fields_set__", set()),
    )

    cambios = {
        sql_name: getattr(payload, api_name)
        for api_name, sql_name in campos.items()
        if api_name in fields_set
    }

    if not cambios:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "SIN_CAMBIOS_CONFIGURACION",
                "mensaje": (
                    "Debe proporcionar al menos un campo "
                    "de configuración personal"
                ),
            },
        )

    try:
        guardar_configuracion_usuario(
            usuario_id,
            cambios,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "CONFIGURACION_PERSONAL_INVALIDA",
                "mensaje": str(exc),
            },
        ) from exc
    except Exception as exc:
        logger.error(
            "[COSTOS_MARGENES_CONFIG_USUARIO] Error guardando configuración: %s",
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CONFIGURACION_PERSONAL_NO_GUARDADA",
                "mensaje": (
                    "No fue posible guardar la configuración personal"
                ),
            },
        ) from exc

    efectiva = resolver_configuracion_efectiva(
        str(scope.unidad_pk),
        usuario_id=usuario_id,
    )

    return {
        "ok": True,
        "configuracion_efectiva": efectiva,
    }


# ==================== RESUMEN ====================

@router.get("/resumen", response_model=CostosMargenesResumen)
async def obtener_resumen(
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    unidad_negocio_pk: Optional[str] = Query(None, description="DEPRECATED: usar unidad"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene resumen general de costos y márgenes.
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **Permisos requeridos**: comercial.costos_margenes.ver
    
    **Retorna**:
    - Total productos sincronizados
    - Productos con/sin receta
    - Promedios de costo y margen
    - Alertas de margen bajo
    - Metadata de sincronización
    """
    permission = _verify_costos_margenes_access(current_user)
    servidor_id_filtro, _, access_denied, unidad_pk = await _resolve_servidor_filtro(
        current_user,
        unidad or unidad_negocio_pk,
        None,
        permission,
    )
    if access_denied:
        return CostosMargenesResumen(
            total_productos=0,
            productos_con_receta=0,
            productos_sin_receta=0,
            total_insumos=0,
            total_recetas=0,
            total_subrecetas=0,
            costo_promedio_general=None,
            margen_promedio_porcentaje=None,
            productos_margen_bajo=0,
            productos_sin_costo=0,
            productos_sin_precio=0,
            ultima_sincronizacion=None,
            sync_run_id=None,
            source_type=SourceType.EDARSAHUB_SQL,
        )
    
    try:
        data = get_resumen_costos_margenes(
            servidor_id=servidor_id_filtro
        )

        productos_margen_bajo = 0

        if unidad_pk:
            usuario_id = _get_sql_usuario_id(
                current_user
            )

            if usuario_id is None:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error":
                            "SQL_USUARIO_NO_RESUELTO",
                        "mensaje": (
                            "No existe identidad SQL "
                            "canonica para resolver margen"
                        ),
                    },
                )

            config_efectiva = (
                _resolve_configuracion_efectiva(
                    current_user,
                    unidad_pk,
                )
            )

            empresa_id_margen = (
                config_efectiva.get("empresa_id")
                if config_efectiva
                else None
            )

            productos_margen_bajo = (
                _contar_productos_margen_bajo_canonico(
                    empresa_id=empresa_id_margen,
                    unidad_pk=unidad_pk,
                    servidor_id=servidor_id_filtro,
                    servidores_ids=None,
                    usuario_id=usuario_id,
                )
            )
        
        return CostosMargenesResumen(
            total_productos=data.get('total_productos', 0),
            productos_con_receta=data.get('productos_con_receta', 0),
            productos_sin_receta=data.get('productos_sin_receta', 0),
            total_insumos=data.get('total_insumos', 0),
            total_recetas=data.get('total_recetas', 0),
            total_subrecetas=data.get('total_subrecetas', 0),
            costo_promedio_general=data.get('costo_promedio_general'),
            margen_promedio_porcentaje=data.get('margen_promedio_porcentaje'),
            productos_margen_bajo=productos_margen_bajo,
            productos_sin_costo=data.get('productos_sin_costo', 0),
            productos_sin_precio=data.get('productos_sin_precio', 0),
            ultima_sincronizacion=data.get('ultima_sincronizacion'),
            sync_run_id=data.get('sync_run_id'),
            source_type=SourceType.EDARSAHUB_SQL
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {str(e)}")


# ==================== PRODUCTOS ====================

@router.get("/productos", response_model=ProductosListResponse)
async def listar_productos(
    empresa_id: Optional[int] = Query(None, description="Filtrar por empresa"),
    unidad_negocio_pk: Optional[str] = Query(None, description="Filtrar por unidad de negocio"),
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    servidor_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'"),
    sistema_origen: Optional[str] = Query(None, description="Filtrar por sistema (SOFTRESTAURANT_PRO, MPRO)"),
    familia: Optional[str] = Query(None, description="Filtrar por familia"),
    subfamilia: Optional[str] = Query(None, description="Filtrar por subfamilia"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre o código"),
    solo_con_receta: bool = Query(False, description="Solo productos con receta"),
    margen_bajo: bool = Query(False, description="Solo productos con margen bajo"),
    incluir_inactivos: bool = Query(False, description="Incluir productos inactivos/dados de baja"),
    page: int = Query(1, ge=1, description="Página"),
    page_size: int = Query(50, ge=1, le=200, description="Tamaño de página"),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista productos con información de costos y márgenes.
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **BUG-COSTOS-001**: Por defecto solo muestra productos activos.
    Usar incluir_inactivos=true para ver también productos inactivos/dados de baja.
    
    **RBAC**: Filtra automáticamente por las unidades de negocio del usuario.
    - Usuarios corporativos (ADMIN, SUPERADMIN, o sin asignaciones): ven todo
    - Usuarios con asignaciones: solo ven sus unidades
    
    **Permisos requeridos**: comercial.costos_margenes.ver
    
    **Filtros disponibles**:
    - empresa_id, unidad_negocio_pk, servidor_id
    - sistema_origen (SOFTRESTAURANT_PRO, MPRO)
    - familia, subfamilia
    - busqueda (nombre o código)
    - solo_con_receta, margen_bajo, incluir_inactivos
    
    **Paginación**: page, page_size
    """
    permission = _verify_costos_margenes_access(current_user)
    unidad_selector = unidad or unidad_negocio_pk
    servidor_id_filtro, servidores_ids_filtro, _acc_denied, unidad_pk_filtro = await _resolve_servidor_filtro(
        current_user,
        unidad_selector,
        servidor_id,
        permission,
    )

    config_efectiva = _resolve_configuracion_efectiva(
        current_user,
        unidad_pk_filtro,
    )

    if _acc_denied:
        return ProductosListResponse(
            productos=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=1,
            configuracion_efectiva=None,
            source_type=SourceType.EDARSAHUB_SQL,
        )
    
    try:
        usuario_id_margen = _get_sql_usuario_id(
            current_user
        )

        if unidad_pk_filtro and usuario_id_margen is None:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "SQL_USUARIO_NO_RESUELTO",
                    "mensaje": (
                        "No existe identidad SQL canonica "
                        "para resolver margen efectivo"
                    ),
                },
            )

        def _fetch_productos(
            fetch_page: int,
            fetch_page_size: int,
        ):
            return get_productos_con_costos(
                empresa_id=empresa_id,
                unidad_negocio_pk=unidad_pk_filtro,
                servidor_id=servidor_id_filtro,
                servidores_ids=servidores_ids_filtro,
                sistema_origen=sistema_origen,
                familia=familia,
                subfamilia=subfamilia,
                busqueda=busqueda,
                solo_con_receta=solo_con_receta,
                margen_bajo=False,
                incluir_inactivos=incluir_inactivos,
                page=fetch_page,
                page_size=fetch_page_size,
            )

        if margen_bajo and not unidad_pk_filtro:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "UNIDAD_CANONICA_REQUERIDA",
                    "mensaje": (
                        "El filtro margen_bajo requiere "
                        "Unidad de Negocio canonica"
                    ),
                },
            )

        if margen_bajo:
            _, candidatos_total = _fetch_productos(
                1,
                1,
            )

            productos_data = []

            if candidatos_total > 0:
                productos_data, _ = _fetch_productos(
                    1,
                    candidatos_total,
                )

            total = candidatos_total

        else:
            productos_data, total = _fetch_productos(
                page,
                page_size,
            )

        empresa_id_margen = (
            empresa_id
            or (
                config_efectiva.get("empresa_id")
                if config_efectiva
                else None
            )
        )

        _resolver_margen_efectivo_productos(
            productos_data,
            empresa_id=empresa_id_margen,
            servidor_id=servidor_id_filtro,
            unidad_pk=unidad_pk_filtro,
            usuario_id=usuario_id_margen,
        )

        if margen_bajo:
            filtrados = []

            for item in productos_data:
                margen_real = item.get(
                    "margen_porcentaje"
                )

                margen_efectivo = item.get(
                    "margen_efectivo"
                )

                if (
                    margen_real is not None
                    and margen_efectivo is not None
                    and float(margen_real)
                        < float(margen_efectivo)
                ):
                    filtrados.append(item)

            total = len(filtrados)

            inicio = (
                page - 1
            ) * page_size

            productos_data = filtrados[
                inicio:
                inicio + page_size
            ]
        
        productos = [
            ProductoCostoMargen(
                producto_id=p['producto_id'],
                id_producto_origen=p['id_producto_origen'],
                nombre=p['nombre'],
                nombre_corto=p.get('nombre_corto'),
                sistema_origen=p['sistema_origen'],
                server_id=p['server_id'],
                empresa_id=p.get('empresa_id'),
                unidad_negocio_pk=p.get('unidad_negocio_pk'),
                familia=p.get('familia'),
                subfamilia=p.get('subfamilia'),
                precio_venta=p.get('precio_venta'),
                precio_sin_impuestos=p.get('precio_sin_impuestos'),
                tasa_impuesto=p.get('tasa_impuesto'),
                estado_impuesto=p.get('estado_impuesto'),
                costo_receta=p.get('costo_receta'),
                costo_promedio=p.get('costo_promedio'),
                margen_pesos=p.get('margen_pesos'),
                margen_porcentaje=p.get('margen_porcentaje'),
                margen_objetivo=p.get('margen_efectivo'),
                margen_efectivo=p.get('margen_efectivo'),
                fuente_margen_efectivo=p.get('fuente_margen_efectivo'),
                tiene_receta=p.get('tiene_receta', False),
                tiene_subrecetas=p.get('tiene_subrecetas', False),
                numero_insumos=p.get('numero_insumos', 0),
                ultima_sincronizacion=p.get('ultima_sincronizacion'),
                source_type=SourceType.EDARSAHUB_SQL
            )
            for p in productos_data
        ]
        
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        
        return ProductosListResponse(
            productos=productos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            configuracion_efectiva=config_efectiva,
            source_type=SourceType.EDARSAHUB_SQL,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos: {str(e)}")


# ==================== RECETA ====================

@router.get("/productos/{producto_id}/receta", response_model=RecetaExpandida)
async def obtener_receta_producto(
    producto_id: str,
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    unidad_negocio_pk: Optional[str] = Query(None, description="DEPRECATED: usar unidad"),
    server_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'"),
    es_elaborado: bool = Query(False, description="Si es true, busca en tabla de elaborados"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la receta expandida de un producto o elaborado.
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **Permisos requeridos**: comercial.costos_margenes.ver_receta
    
    **Parámetros**:
    - producto_id: ID o código fuente del producto/elaborado
    - server_id: ServerID para filtrar (opcional pero recomendado para elaborados)
    - es_elaborado: Si true, busca la receta del elaborado en Sync_Productos_Elaborados
    
    **Retorna**:
    - Producto
    - Lista jerárquica de componentes
    - Insumos directos
    - Insumos elaborados
    - Subrecetas
    - Costos por componente
    """
    permission = _verify_costos_margenes_access(current_user)
    server_id_filtro = await _resolve_receta_servidor_filtro(
        current_user,
        unidad,
        unidad_negocio_pk,
        server_id,
        permission,
    )
    
    try:
        # Primero intentar como producto normal
        producto, componentes = get_receta_producto(producto_id, server_id_filtro)
        
        # Si no encuentra y es_elaborado=True, buscar en tabla de elaborados
        if not producto and es_elaborado:
            producto, componentes = get_receta_elaborado(producto_id, server_id_filtro)
        
        # Si aún no encuentra, intentar automáticamente como elaborado
        if not producto:
            producto, componentes = get_receta_elaborado(producto_id, server_id_filtro)
        
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto {producto_id} no encontrado")
        
        # Calcular totales
        costo_total = sum(c.get('costo_total', 0) or 0 for c in componentes)
        total_directos = sum(1 for c in componentes if c.get('tipo_componente') == 'INSUMO_DIRECTO')
        total_elaborados = sum(1 for c in componentes if c.get('es_elaborado'))
        total_subrecetas = sum(1 for c in componentes if c.get('tipo_componente') == 'SUBRECETA')
        
        componentes_schema = [
            ComponenteReceta(
                componente_id=c['componente_id'],
                codigo_fuente=c['codigo_fuente'],
                nombre=c['nombre'],
                tipo_componente=c['tipo_componente'],
                cantidad=c['cantidad'],
                unidad_medida=c['unidad_medida'],
                costo_unitario=c.get('costo_unitario'),
                costo_total=c.get('costo_total'),
                porcentaje_costo_total=c.get('porcentaje_costo_total'),
                nivel_jerarquico=c.get('nivel_jerarquico', 1),
                es_elaborado=c.get('es_elaborado', False),
                rendimiento_elaborado=c.get('rendimiento_elaborado'),
            )
            for c in componentes
        ]
        
        return RecetaExpandida(
            producto_id=producto.get('producto_id', ''),
            producto_nombre=producto.get('Nombre', ''),
            producto_codigo=producto.get('CodigoFuente', ''),
            sistema_origen=producto.get('SystemType', ''),
            server_id=producto.get('server_id', ''),
            costo_total_receta=costo_total if costo_total > 0 else None,
            total_componentes=len(componentes),
            total_insumos_directos=total_directos,
            total_elaborados=total_elaborados,
            total_subrecetas=total_subrecetas,
            componentes=componentes_schema,
            sync_run_id=producto.get('SyncRunID'),
            ultima_sincronizacion=producto.get('SyncedAtMexico'),
            source_type=SourceType.EDARSAHUB_SQL
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo receta: {str(e)}")


# ==================== INSUMOS ====================

@router.get("/productos/{producto_id}/insumos", response_model=InsumosProductoResponse)
async def obtener_insumos_producto(
    producto_id: str,
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    unidad_negocio_pk: Optional[str] = Query(None, description="DEPRECATED: usar unidad"),
    server_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene lista plana consolidada de insumos de un producto.
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **Permisos requeridos**: comercial.costos_margenes.ver_insumos
    
    **Retorna**:
    - Lista de insumos consolidados
    - Cantidad total por insumo
    - Costo por insumo
    - Porcentaje del costo total
    - Origen (directo/subreceta/elaborado)
    """
    permission = _verify_costos_margenes_access(current_user)
    server_id_filtro = await _resolve_receta_servidor_filtro(
        current_user,
        unidad,
        unidad_negocio_pk,
        server_id,
        permission,
    )
    
    try:
        producto, insumos = get_insumos_producto(producto_id, server_id_filtro)
        
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto {producto_id} no encontrado")
        
        costo_total = sum(i.get('costo_total', 0) or 0 for i in insumos)
        
        insumos_schema = [
            InsumoConsolidado(
                insumo_id=i['insumo_id'],
                codigo_fuente=i['codigo_fuente'],
                nombre=i['nombre'],
                cantidad_total=i['cantidad_total'],
                unidad_medida=i['unidad_medida'],
                costo_unitario=i.get('costo_unitario'),
                costo_total=i.get('costo_total'),
                porcentaje_costo_total=i.get('porcentaje_costo_total'),
                origen=i.get('origen', 'DIRECTO'),
                nivel_origen=i.get('nivel_origen', 1),
                es_elaborado=i.get('es_elaborado', False),
            )
            for i in insumos
        ]
        
        return InsumosProductoResponse(
            producto_id=producto.get('producto_id', ''),
            producto_nombre=producto.get('Nombre', ''),
            total_insumos=len(insumos),
            costo_total_insumos=costo_total if costo_total > 0 else None,
            insumos=insumos_schema,
            source_type=SourceType.EDARSAHUB_SQL
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo insumos: {str(e)}")


# ==================== SYNC STATUS ====================

@router.get("/sync-status", response_model=SyncStatusResponse)
async def obtener_sync_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene estado de sincronización del módulo.
    
    **Fuente**: EDARSAHUB SQL
    
    **Permisos requeridos**: comercial.costos_margenes.ver_sync_status
    
    **Retorna**:
    - Último sync_run_id
    - Fecha última sincronización
    - Conteos por tabla, sistema y servidor
    - Estado general (EDARSAHUB_SQL, STALE, SIN_DATOS)
    """
    # FASE 1C-3E: Verificar permisos
    _verify_costos_margenes_access(current_user)
    
    try:
        data = get_sync_status()
        
        return SyncStatusResponse(
            ultimo_sync_run_id=data.get('ultimo_sync_run_id'),
            fecha_ultima_sincronizacion=data.get('fecha_ultima_sincronizacion'),
            registros_por_tabla=[
                ConteoTabla(tabla=t['tabla'], registros=t['registros'])
                for t in data.get('registros_por_tabla', [])
            ],
            registros_por_sistema=[
                ConteoPorSistema(sistema=s['sistema'], registros=s['registros'])
                for s in data.get('registros_por_sistema', [])
            ],
            registros_por_servidor=[
                ConteoPorServidor(
                    servidor_id=s['servidor_id'],
                    servidor_nombre=s.get('servidor_nombre'),
                    sistema=s['sistema'],
                    registros=s['registros']
                )
                for s in data.get('registros_por_servidor', [])
            ],
            total_registros=data.get('total_registros', 0),
            errores=data.get('errores', []),
            warnings=data.get('warnings', []),
            estado=SourceType(data.get('estado', 'EDARSAHUB_SQL'))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo sync status: {str(e)}")


# ==================== UNIDADES DE NEGOCIO ====================

# DESACTIVADO 2026-06-04: endpoint duplicado. Usar /api/unidades-negocio en server.py
# @router.get("/unidades-negocio")
async def listar_unidades_negocio(
    current_user: dict = Depends(get_current_user)
):
    """
    Lista las unidades de negocio activas.
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **RBAC**: Filtra según asignaciones del usuario.
    - Usuarios corporativos: ven todas
    - Usuarios con asignaciones: solo ven sus unidades
    
    **Retorna**: Lista de unidades con código, nombre, server_id
    """
    permission = _verify_costos_margenes_access(current_user)
    
    try:
        unidades = get_unidades_negocio()
        if permission.get("restriccion_sucursal"):
            unidades = []
        
        return {
            "unidades": unidades,
            "total": len(unidades),
            "source_type": "EDARSAHUB_SQL",
            "es_corporativo": not permission.get("restriccion_sucursal")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo unidades de negocio: {str(e)}")


# ==================== FAMILIAS Y SUBFAMILIAS ====================

@router.get("/familias")
async def listar_familias(
    current_user: dict = Depends(get_current_user),
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    servidor_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'")
):
    """
    Lista las familias de productos disponibles.
    
    **Parámetros**:
    - unidad: Filtrar familias por unidad de negocio (canónico)
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **RBAC**: Filtra según asignaciones del usuario.
    
    **Retorna**: Lista de familias con total de productos por familia
    """
    permission = _verify_costos_margenes_access(current_user)
    servidor_id_filtro, servidores_ids_filtro, _acc, unidad_pk = await _resolve_servidor_filtro(
        current_user,
        unidad,
        servidor_id,
        permission,
    )
    if _acc:
        return {"familias": [], "total": 0, "source_type": "EDARSAHUB_SQL"}
    
    try:
        familias = get_familias_productos(
            servidor_id_filtro,
            servidores_ids_filtro,
            unidad_negocio_pk=unidad_pk,
        )
        return {
            "familias": familias,
            "total": len(familias),
            "source_type": "EDARSAHUB_SQL"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo familias: {str(e)}")


@router.get("/subfamilias")
async def listar_subfamilias(
    current_user: dict = Depends(get_current_user),
    familia: Optional[str] = Query(None, description="Filtrar por familia"),
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    servidor_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'")
):
    """
    Lista las subfamilias de productos.
    
    **Parámetros**:
    - familia: Filtrar subfamilias por familia padre
    - unidad: Filtrar por unidad de negocio (canónico)
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **Retorna**: Lista de subfamilias con total de productos
    """
    permission = _verify_costos_margenes_access(current_user)
    servidor_id_filtro, _sids, _acc, unidad_pk = await _resolve_servidor_filtro(
        current_user,
        unidad,
        servidor_id,
        permission,
    )
    if _acc:
        return {"subfamilias": [], "total": 0, "source_type": "EDARSAHUB_SQL"}
    
    try:
        subfamilias = get_subfamilias_productos(
            familia,
            servidor_id_filtro,
            unidad_negocio_pk=unidad_pk,
        )
        return {
            "subfamilias": subfamilias,
            "total": len(subfamilias),
            "source_type": "EDARSAHUB_SQL"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo subfamilias: {str(e)}")


# ==================== EXPORTACIÓN ====================

@router.get("/exportar")
async def exportar_productos_csv(
    current_user: dict = Depends(get_current_user),
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    unidad_negocio_pk: Optional[str] = Query(None, description="DEPRECATED: usar unidad"),
    servidor_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'"),
    familia: Optional[str] = Query(None, description="Filtrar por familia"),
    sistema: Optional[str] = Query(None, description="Filtrar por sistema (SOFTRESTAURANT_PRO, MPRO)"),
    solo_con_receta: bool = Query(False, description="Solo productos con receta"),
):
    """
    Exporta productos con costos y márgenes a CSV.
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **Permisos requeridos**: comercial.costos_margenes.exportar
    
    **FASE 1C-3E**: 
    - Exportación de solo lectura
    - No modifica datos
    - Respeta filtros del usuario
    - Límite de 10,000 registros por exportación
    
    **Formato CSV**:
    - Codificación UTF-8 con BOM
    - Separador: coma
    - Incluye encabezados
    """
    # FASE 1C-3E: Verificar permisos
    permission = _verify_costos_margenes_access(current_user)
    servidor_id_filtro, servidores_ids_filtro, access_denied, unidad_pk_filtro = await _resolve_servidor_filtro(
        current_user,
        unidad or unidad_negocio_pk,
        servidor_id,
        permission,
    )
    if access_denied:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "UNIDAD_CANONICA_REQUERIDA",
                "mensaje": "Use unidad o unidad_negocio_pk para validar alcance RBAC",
            },
        )
    
    try:
        # Obtener datos (máximo 10,000 para evitar sobrecarga)
        productos, total = get_productos_con_costos(
            unidad_negocio_pk=unidad_pk_filtro,
            servidor_id=servidor_id_filtro,
            servidores_ids=servidores_ids_filtro,
            page=1,
            page_size=10000,
            familia=familia,
            sistema_origen=sistema,
            solo_con_receta=solo_con_receta
        )
        
        if not productos:
            raise HTTPException(
                status_code=404, 
                detail="No se encontraron productos con los filtros especificados"
            )
        
        # Crear archivo CSV en memoria
        output = io.StringIO()
        
        # Agregar BOM para Excel (UTF-8)
        output.write('\ufeff')
        
        # Encabezados
        fieldnames = [
            'Código', 'Nombre', 'Familia', 'SubFamilia', 'Sistema', 
            'Precio Venta', 'Costo Receta', 'Margen Bruto $', 'Margen %',
            'Tiene Receta', 'Componentes Receta', 'Insumos Directos'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Escribir productos
        for p in productos:
            writer.writerow({
                'Código': p.get('codigo', ''),
                'Nombre': p.get('nombre', ''),
                'Familia': p.get('familia', ''),
                'SubFamilia': p.get('subfamilia', ''),
                'Sistema': p.get('sistema', ''),
                'Precio Venta': p.get('precio_venta', 0),
                'Costo Receta': p.get('costo_receta', 0),
                'Margen Bruto $': p.get('margen_bruto_pesos', 0),
                'Margen %': p.get('margen_porcentaje', 0),
                'Tiene Receta': 'Sí' if p.get('tiene_receta') else 'No',
                'Componentes Receta': p.get('total_componentes_receta', 0),
                'Insumos Directos': p.get('total_insumos_directos', 0),
            })
        
        # Preparar respuesta
        output.seek(0)
        
        # Nombre del archivo con fecha
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"costos_margenes_{timestamp}.csv"
        
        # Log de auditoría (sin datos sensibles)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"EXPORTACIÓN CSV: usuario={current_user.get('email')}, "
            f"registros={len(productos)}, filtros={{unidad={unidad or unidad_negocio_pk}, familia={familia}, sistema={sistema}}}"
        )
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "text/csv; charset=utf-8",
                "X-Total-Records": str(len(productos)),
                "X-Source-Type": "EDARSAHUB_SQL"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando exportación: {str(e)}")
