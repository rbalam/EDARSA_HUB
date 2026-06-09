from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
from core.rbac_helper_sql import es_admin, tiene_acceso_lectura_comercial
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
from typing import Optional, List
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
from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG
from core.corporate_filters.request_resolver import resolve_unidad_scope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/costos-margenes", tags=["Costos y Márgenes"])


# ==================== RBAC HELPERS ====================

def _get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB SQL."""
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )


def _get_user_allowed_servers(user: dict) -> tuple[List[str], bool]:
    """
    FASE P2 - RBAC por Unidad de Negocio
    
    Obtiene los server_id permitidos para el usuario desde Usuario_ServidoresAsignacion.
    
    Returns:
        (lista_server_ids, es_corporativo)
        - es_corporativo=True si tiene acceso global (rol admin, superadmin, o 0 asignaciones)
    """
    role = user.get('role', '')
    user_id = user.get('id', '')
    email = user.get('email', '')
    
    # SuperAdministrador y Administrador tienen acceso global (RBAC canónico)
    if es_admin(user):
        logger.info(f"[RBAC] Usuario {email} tiene acceso global por rol {role}")
        return [], True
    
    # Buscar UsuarioID y sus servidores asignados
    conn = _get_edarsahub_connection()
    
    try:
        # Buscar el UsuarioID por email o PublicUUID
        user_query = f"""
        SELECT UsuarioID 
        FROM Usuario_Catalogo 
        WHERE (Email = '{Email}' OR LOWER(CAST(PublicUUID AS VARCHAR(36))) = '{user_id.lower()}')
        AND Activo = 1
        """
        user_result = execute_sql_query(*conn, user_query)
        
        if not user_result:
            logger.warning(f"[RBAC] Usuario {email} no encontrado en Usuario_Catalogo")
            return [], False  # Sin acceso si no está en catálogo
        
        usuario_id_sql = user_result[0].get('UsuarioID')
        
        # Obtener servidores asignados
        servers_query = f"""
        SELECT CAST(sa.ServidorID AS NVARCHAR(36)) as server_id
        FROM Usuario_ServidoresAsignacion sa
        WHERE sa.UsuarioID = {usuario_id_sql}
        AND sa.Activo = 1
        """
        servers_result = execute_sql_query(*conn, servers_query) or []
        
        server_ids = [r.get('server_id') for r in servers_result if r.get('server_id')]
        
        # Si tiene 0 asignaciones, es corporativo (ve todo)
        if len(server_ids) == 0:
            logger.info(f"[RBAC] Usuario {email} tiene 0 asignaciones → acceso corporativo")
            return [], True
        
        logger.info(f"[RBAC] Usuario {email} tiene acceso a {len(server_ids)} servidores: {server_ids[:3]}...")
        return server_ids, False
        
    except Exception as e:
        logger.error(f"[RBAC] Error obteniendo servidores para {email}: {e}")
        return [], False


def _check_admin_or_comercial(user: dict) -> bool:
    """
    FASE 1C-3E: Verifica si el usuario tiene acceso al módulo Costos y Márgenes.
    
    Roles permitidos:
    - SuperAdministrador: Acceso total
    - Administrador: Acceso total
    - Supervisor: Acceso de lectura
    - Usuario con rol comercial: Acceso de lectura
    
    NOTA: En futuras fases se puede integrar con require_permission() de core.rbac
    """
    # Acceso de lectura: cualquier rol canónico del staff (RBAC canónico,
    # reemplaza la lista legacy ['Supervisor','Comercial','Gerente','Usuario']).
    return tiene_acceso_lectura_comercial(user)


def _verify_costos_margenes_access(user: dict) -> None:
    """
    FASE 1C-3E: Verifica acceso al módulo y lanza 403 si no tiene permiso.
    """
    if not _check_admin_or_comercial(user):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "PERMISO_DENEGADO",
                "mensaje": "No tiene acceso al módulo de Costos y Márgenes",
                "permiso_requerido": "comercial.costos_margenes.ver"
            }
        )


async def _resolve_servidor_filtro(current_user: dict, unidad: Optional[str], servidor_id: Optional[str]):
    """
    Resolución CANÓNICA de la unidad de negocio para Costos y Márgenes.

    - Si llega 'unidad' (codigo o id) → puerta única ``resolve_unidad_scope``
      (resuelve server_id + valida RBAC reutilizando el sistema existente). Es el
      contrato canónico, igual que el resto de tableros del ERP.
    - 'servidor_id' queda SOLO como compatibilidad DEPRECATED.
    - Sin filtro → fallback RBAC por servidores permitidos del usuario.

    Returns: (servidor_id_filtro, servidores_ids_filtro, access_denied)
    """
    if unidad:
        scope = await resolve_unidad_scope(current_user, unidad=unidad)
        if scope.access_denied:
            return None, None, True
        return scope.server_id, None, False

    allowed_servers, es_corporativo = _get_user_allowed_servers(current_user)
    if servidor_id and not es_corporativo and servidor_id not in allowed_servers:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "ACCESO_DENEGADO_UNIDAD",
                "mensaje": "No tiene acceso a esta unidad de negocio"
            }
        )
    servidores_ids_filtro = allowed_servers if (not es_corporativo and not servidor_id) else None
    return servidor_id, servidores_ids_filtro, False


# ==================== RESUMEN ====================

@router.get("/resumen", response_model=CostosMargenesResumen)
async def obtener_resumen(
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
    # FASE 1C-3E: Verificar permisos
    _verify_costos_margenes_access(current_user)
    
    try:
        data = get_resumen_costos_margenes()
        
        return CostosMargenesResumen(
            total_productos=data.get('total_productos', 0),
            productos_con_receta=data.get('productos_con_receta', 0),
            productos_sin_receta=data.get('productos_sin_receta', 0),
            total_insumos=data.get('total_insumos', 0),
            total_recetas=data.get('total_recetas', 0),
            total_subrecetas=data.get('total_subrecetas', 0),
            costo_promedio_general=data.get('costo_promedio_general'),
            margen_promedio_porcentaje=data.get('margen_promedio_porcentaje'),
            productos_margen_bajo=data.get('productos_margen_bajo', 0),
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
    unidad_negocio_pk: Optional[int] = Query(None, description="Filtrar por unidad de negocio"),
    unidad: Optional[str] = Query(None, description="CANÓNICO: unidad de negocio (codigo o id)"),
    servidor_id: Optional[str] = Query(None, description="DEPRECATED: usar 'unidad'"),
    sistema_origen: Optional[str] = Query(None, description="Filtrar por sistema (SOFTRESTAURANT_PRO, MPRO)"),
    familia: Optional[str] = Query(None, description="Filtrar por familia"),
    subfamilia: Optional[str] = Query(None, description="Filtrar por subfamilia"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre o código"),
    solo_con_receta: bool = Query(False, description="Solo productos con receta"),
    margen_bajo: bool = Query(False, description="Solo productos con margen bajo"),
    umbral_margen: int = Query(20, ge=0, le=100, description="Umbral de margen bajo (%)"),
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
    # FASE 1C-3E: Verificar permisos
    _verify_costos_margenes_access(current_user)
    
    # CANÓNICO: 'unidad' (codigo/id) → server_id vía puerta única (RBAC incluido).
    # 'servidor_id' queda DEPRECATED (compat).
    servidor_id_filtro, servidores_ids_filtro, _acc_denied = await _resolve_servidor_filtro(
        current_user, unidad, servidor_id
    )
    if _acc_denied:
        return ProductosListResponse(
            productos=[], total=0, page=page, page_size=page_size,
            total_pages=1, source_type=SourceType.EDARSAHUB_SQL
        )
    
    try:
        productos_data, total = get_productos_con_costos(
            empresa_id=empresa_id,
            unidad_negocio_pk=unidad_negocio_pk,
            servidor_id=servidor_id_filtro,
            servidores_ids=servidores_ids_filtro,  # Nuevo parámetro para RBAC
            sistema_origen=sistema_origen,
            familia=familia,
            subfamilia=subfamilia,
            busqueda=busqueda,
            solo_con_receta=solo_con_receta,
            margen_bajo=margen_bajo,
            umbral_margen=umbral_margen,  # Umbral editable
            incluir_inactivos=incluir_inactivos,  # BUG-COSTOS-001
            page=page,
            page_size=page_size
        )
        
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
                margen_objetivo=p.get('margen_objetivo'),
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
            source_type=SourceType.EDARSAHUB_SQL
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos: {str(e)}")


# ==================== RECETA ====================

@router.get("/productos/{producto_id}/receta", response_model=RecetaExpandida)
async def obtener_receta_producto(
    producto_id: str,
    server_id: Optional[str] = Query(None, description="ServerID para búsqueda por código fuente"),
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
    # FASE 1C-3E: Verificar permisos
    _verify_costos_margenes_access(current_user)
    
    try:
        # Primero intentar como producto normal
        producto, componentes = get_receta_producto(producto_id, server_id)
        
        # Si no encuentra y es_elaborado=True, buscar en tabla de elaborados
        if not producto and es_elaborado:
            producto, componentes = get_receta_elaborado(producto_id, server_id)
        
        # Si aún no encuentra, intentar automáticamente como elaborado
        if not producto:
            producto, componentes = get_receta_elaborado(producto_id, server_id)
        
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
    server_id: Optional[str] = Query(None, description="ServerID para búsqueda por código fuente"),
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
    # FASE 1C-3E: Verificar permisos
    _verify_costos_margenes_access(current_user)
    
    try:
        producto, insumos = get_insumos_producto(producto_id, server_id)
        
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
    _verify_costos_margenes_access(current_user)
    
    # FASE P2: RBAC por Unidad de Negocio
    allowed_servers, es_corporativo = _get_user_allowed_servers(current_user)
    
    try:
        unidades = get_unidades_negocio()
        
        # Filtrar por servidores permitidos si no es corporativo
        if not es_corporativo and allowed_servers:
            unidades = [u for u in unidades if u.get('server_id') in allowed_servers]
        
        return {
            "unidades": unidades,
            "total": len(unidades),
            "source_type": "EDARSAHUB_SQL",
            "es_corporativo": es_corporativo  # Indicador para el frontend
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
    _verify_costos_margenes_access(current_user)
    
    # CANÓNICO: resolver 'unidad' → server_id (RBAC incluido). 'servidor_id' DEPRECATED.
    servidor_id_filtro, servidores_ids_filtro, _acc = await _resolve_servidor_filtro(
        current_user, unidad, servidor_id
    )
    if _acc:
        return {"familias": [], "total": 0, "source_type": "EDARSAHUB_SQL"}
    
    try:
        familias = get_familias_productos(servidor_id_filtro, servidores_ids_filtro)
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
    _verify_costos_margenes_access(current_user)
    
    servidor_id_filtro, _sids, _acc = await _resolve_servidor_filtro(current_user, unidad, servidor_id)
    if _acc:
        return {"subfamilias": [], "total": 0, "source_type": "EDARSAHUB_SQL"}
    
    try:
        subfamilias = get_subfamilias_productos(familia, servidor_id_filtro)
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
    _verify_costos_margenes_access(current_user)
    
    try:
        # Obtener datos (máximo 10,000 para evitar sobrecarga)
        productos, total = get_productos_con_costos(
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
            f"registros={len(productos)}, filtros={{familia={familia}, sistema={sistema}}}"
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

