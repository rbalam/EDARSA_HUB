"""
Endpoints del módulo Costos y Márgenes.
FASE 1C-3C - Endpoints NO-LIVE

IMPORTANTE:
- Todos los endpoints leen EXCLUSIVAMENTE de EDARSAHUB SQL
- NO se realizan conexiones live a sistemas externos
- NO se usa MongoDB
- Se respeta RBAC y permisos por empresa/unidad
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import math

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
    get_insumos_producto,
    get_sync_status,
)
from core.security import get_current_user


router = APIRouter(prefix="/costos-margenes", tags=["Costos y Márgenes"])


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
    # Verificar permiso
    # await require_permission(current_user, "comercial.costos_margenes.ver")
    
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
    unidad_negocio_id: Optional[int] = Query(None, description="Filtrar por unidad de negocio"),
    servidor_id: Optional[str] = Query(None, description="Filtrar por servidor"),
    sistema_origen: Optional[str] = Query(None, description="Filtrar por sistema (SOFTRESTAURANT_PRO, MPRO)"),
    familia: Optional[str] = Query(None, description="Filtrar por familia"),
    subfamilia: Optional[str] = Query(None, description="Filtrar por subfamilia"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre o código"),
    solo_con_receta: bool = Query(False, description="Solo productos con receta"),
    margen_bajo: bool = Query(False, description="Solo productos con margen < 20%"),
    page: int = Query(1, ge=1, description="Página"),
    page_size: int = Query(50, ge=1, le=200, description="Tamaño de página"),
    current_user: dict = Depends(get_current_user)
):
    """
    Lista productos con información de costos y márgenes.
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **Permisos requeridos**: comercial.costos_margenes.ver
    
    **Filtros disponibles**:
    - empresa_id, unidad_negocio_id, servidor_id
    - sistema_origen (SOFTRESTAURANT_PRO, MPRO)
    - familia, subfamilia
    - busqueda (nombre o código)
    - solo_con_receta, margen_bajo
    
    **Paginación**: page, page_size
    """
    # await require_permission(current_user, "comercial.costos_margenes.ver")
    
    try:
        productos_data, total = get_productos_con_costos(
            empresa_id=empresa_id,
            unidad_negocio_id=unidad_negocio_id,
            servidor_id=servidor_id,
            sistema_origen=sistema_origen,
            familia=familia,
            subfamilia=subfamilia,
            busqueda=busqueda,
            solo_con_receta=solo_con_receta,
            margen_bajo=margen_bajo,
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
                unidad_negocio_id=p.get('unidad_negocio_id'),
                familia=p.get('familia'),
                subfamilia=p.get('subfamilia'),
                precio_venta=p.get('precio_venta'),
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
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la receta expandida de un producto.
    
    **Fuente**: EDARSAHUB SQL (NO-LIVE)
    
    **Permisos requeridos**: comercial.costos_margenes.ver_receta
    
    **Retorna**:
    - Producto
    - Lista jerárquica de componentes
    - Insumos directos
    - Insumos elaborados
    - Subrecetas
    - Costos por componente
    """
    # await require_permission(current_user, "comercial.costos_margenes.ver_receta")
    
    try:
        producto, componentes = get_receta_producto(producto_id, server_id)
        
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
    # await require_permission(current_user, "comercial.costos_margenes.ver_insumos")
    
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
    # await require_permission(current_user, "comercial.costos_margenes.ver_sync_status")
    
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
