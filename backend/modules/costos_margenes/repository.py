"""
Repository para el módulo Costos y Márgenes.
FASE 1C-3C - Acceso EXCLUSIVO a EDARSAHUB SQL (NO-LIVE)
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG


def _get_edarsahub_connection() -> Tuple[str, int, str, str, str]:
    """Retorna parámetros de conexión a EDARSAHUB."""
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )


def _safe_decimal(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Convierte Decimal a float de forma segura."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ==================== RESUMEN ====================

def get_resumen_costos_margenes() -> Dict[str, Any]:
    """
    Obtiene resumen general de costos y márgenes.
    Fuente: EDARSAHUB SQL (NO-LIVE)
    """
    conn = _get_edarsahub_connection()
    
    # Query principal de productos
    productos_query = """
    SELECT 
        COUNT(*) as total_productos,
        SUM(CASE WHEN TieneReceta = 1 THEN 1 ELSE 0 END) as productos_con_receta,
        SUM(CASE WHEN TieneReceta = 0 OR TieneReceta IS NULL THEN 1 ELSE 0 END) as productos_sin_receta,
        AVG(CASE WHEN CostoReceta > 0 THEN CostoReceta END) as costo_promedio,
        AVG(CASE WHEN MargenBrutoPorcentaje IS NOT NULL AND PrecioVenta > 0 THEN MargenBrutoPorcentaje END) as margen_promedio,
        SUM(CASE WHEN MargenBrutoPorcentaje < 20 AND MargenBrutoPorcentaje IS NOT NULL THEN 1 ELSE 0 END) as margen_bajo,
        SUM(CASE WHEN CostoReceta IS NULL OR CostoReceta = 0 THEN 1 ELSE 0 END) as sin_costo,
        SUM(CASE WHEN PrecioVenta IS NULL OR PrecioVenta = 0 THEN 1 ELSE 0 END) as sin_precio,
        MAX(SyncedAtMexico) as ultima_sync,
        MAX(SyncRunID) as sync_run_id
    FROM Sync_Productos
    WHERE Activo = 1 OR Activo IS NULL
    """
    productos_result = execute_sql_query(*conn, productos_query)
    
    # Conteo de insumos
    insumos_query = "SELECT COUNT(*) as total FROM Sync_Productos_Insumos"
    insumos_result = execute_sql_query(*conn, insumos_query)
    
    # Conteo de recetas
    recetas_query = "SELECT COUNT(*) as total FROM Sync_Productos_Recetas"
    recetas_result = execute_sql_query(*conn, recetas_query)
    
    # Conteo de elaborados (subrecetas)
    elaborados_query = "SELECT COUNT(*) as total FROM Sync_Productos_Elaborados"
    elaborados_result = execute_sql_query(*conn, elaborados_query)
    
    p = productos_result[0] if productos_result else {}
    
    return {
        'total_productos': p.get('total_productos', 0) or 0,
        'productos_con_receta': p.get('productos_con_receta', 0) or 0,
        'productos_sin_receta': p.get('productos_sin_receta', 0) or 0,
        'total_insumos': insumos_result[0].get('total', 0) if insumos_result else 0,
        'total_recetas': recetas_result[0].get('total', 0) if recetas_result else 0,
        'total_subrecetas': elaborados_result[0].get('total', 0) if elaborados_result else 0,
        'costo_promedio_general': _safe_decimal(p.get('costo_promedio')),
        'margen_promedio_porcentaje': _safe_decimal(p.get('margen_promedio')),
        'productos_margen_bajo': p.get('margen_bajo', 0) or 0,
        'productos_sin_costo': p.get('sin_costo', 0) or 0,
        'productos_sin_precio': p.get('sin_precio', 0) or 0,
        'ultima_sincronizacion': p.get('ultima_sync'),
        'sync_run_id': p.get('sync_run_id'),
    }


# ==================== PRODUCTOS ====================

def get_productos_con_costos(
    empresa_id: Optional[int] = None,
    unidad_negocio_id: Optional[int] = None,
    servidor_id: Optional[str] = None,
    sistema_origen: Optional[str] = None,
    familia: Optional[str] = None,
    subfamilia: Optional[str] = None,
    busqueda: Optional[str] = None,
    solo_con_receta: bool = False,
    margen_bajo: bool = False,
    page: int = 1,
    page_size: int = 50
) -> Tuple[List[Dict], int]:
    """
    Obtiene lista de productos con costos y márgenes.
    Fuente: EDARSAHUB SQL (NO-LIVE)
    """
    conn = _get_edarsahub_connection()
    
    # Construir WHERE dinámico
    where_clauses = ["1=1"]
    
    if empresa_id:
        where_clauses.append(f"p.EmpresaID = {empresa_id}")
    if unidad_negocio_id:
        where_clauses.append(f"p.UnidadNegocioID = {unidad_negocio_id}")
    if servidor_id:
        where_clauses.append(f"p.ServerID = '{servidor_id}'")
    if sistema_origen:
        where_clauses.append(f"p.SystemType = '{sistema_origen}'")
    if familia:
        where_clauses.append(f"p.FamiliaNombre LIKE '%{familia}%'")
    if subfamilia:
        where_clauses.append(f"p.SubFamiliaNombre LIKE '%{subfamilia}%'")
    if busqueda:
        where_clauses.append(f"(p.Nombre LIKE '%{busqueda}%' OR p.CodigoFuente LIKE '%{busqueda}%')")
    if solo_con_receta:
        where_clauses.append("p.TieneReceta = 1")
    if margen_bajo:
        where_clauses.append("p.MargenBrutoPorcentaje < 20 AND p.MargenBrutoPorcentaje IS NOT NULL")
    
    where_sql = " AND ".join(where_clauses)
    
    # Query de conteo total
    count_query = f"""
    SELECT COUNT(*) as total
    FROM Sync_Productos p
    WHERE {where_sql}
    """
    count_result = execute_sql_query(*conn, count_query)
    total = count_result[0].get('total', 0) if count_result else 0
    
    # Query de datos con paginación
    offset = (page - 1) * page_size
    data_query = f"""
    SELECT 
        CAST(p.ProductoID AS NVARCHAR(36)) as producto_id,
        p.CodigoFuente as id_producto_origen,
        p.Nombre as nombre,
        p.NombreCorto as nombre_corto,
        p.SystemType as sistema_origen,
        CAST(p.ServerID AS NVARCHAR(36)) as server_id,
        p.EmpresaID as empresa_id,
        p.UnidadNegocioID as unidad_negocio_id,
        COALESCE(p.FamiliaNombre, 'Sin clasificar') as familia,
        p.SubFamiliaNombre as subfamilia,
        p.PrecioVenta as precio_venta,
        p.CostoReceta as costo_receta,
        p.CostoPromedio as costo_promedio,
        p.MargenBrutoPesos as margen_pesos,
        p.MargenBrutoPorcentaje as margen_porcentaje,
        p.MargenObjetivo as margen_objetivo,
        CAST(p.TieneReceta AS BIT) as tiene_receta,
        CAST(p.TieneSubRecetas AS BIT) as tiene_subrecetas,
        COALESCE(p.CantidadComponentesReceta, 0) as numero_insumos,
        p.SyncedAtMexico as ultima_sincronizacion
    FROM Sync_Productos p
    WHERE {where_sql}
    ORDER BY p.Nombre
    OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
    """
    
    data_result = execute_sql_query(*conn, data_query) or []
    
    # Procesar resultados
    productos = []
    for row in data_result:
        productos.append({
            'producto_id': row.get('producto_id', ''),
            'id_producto_origen': row.get('id_producto_origen', ''),
            'nombre': row.get('nombre', ''),
            'nombre_corto': row.get('nombre_corto'),
            'sistema_origen': row.get('sistema_origen', ''),
            'server_id': row.get('server_id', ''),
            'empresa_id': row.get('empresa_id'),
            'unidad_negocio_id': row.get('unidad_negocio_id'),
            'familia': row.get('familia'),
            'subfamilia': row.get('subfamilia'),
            'precio_venta': _safe_decimal(row.get('precio_venta')),
            'costo_receta': _safe_decimal(row.get('costo_receta')),
            'costo_promedio': _safe_decimal(row.get('costo_promedio')),
            'margen_pesos': _safe_decimal(row.get('margen_pesos')),
            'margen_porcentaje': _safe_decimal(row.get('margen_porcentaje')),
            'margen_objetivo': _safe_decimal(row.get('margen_objetivo')),
            'tiene_receta': bool(row.get('tiene_receta')),
            'tiene_subrecetas': bool(row.get('tiene_subrecetas')),
            'numero_insumos': row.get('numero_insumos', 0) or 0,
            'ultima_sincronizacion': row.get('ultima_sincronizacion'),
        })
    
    return productos, total


# ==================== RECETA EXPANDIDA ====================

def get_producto_by_id(producto_id: str) -> Optional[Dict]:
    """Obtiene un producto por su ID."""
    conn = _get_edarsahub_connection()
    
    query = f"""
    SELECT 
        CAST(ProductoID AS NVARCHAR(36)) as producto_id,
        CodigoFuente,
        Nombre,
        SystemType,
        CAST(ServerID AS NVARCHAR(36)) as server_id,
        CostoReceta,
        SyncRunID,
        SyncedAtMexico
    FROM Sync_Productos
    WHERE ProductoID = '{producto_id}'
    OR CodigoFuente = '{producto_id}'
    """
    result = execute_sql_query(*conn, query)
    return result[0] if result else None


def get_receta_producto(producto_id: str, server_id: Optional[str] = None) -> Tuple[Dict, List[Dict]]:
    """
    Obtiene la receta completa de un producto.
    Fuente: EDARSAHUB SQL (NO-LIVE)
    """
    conn = _get_edarsahub_connection()
    
    # Primero obtener el producto
    producto = get_producto_by_id(producto_id)
    if not producto:
        # Intentar buscar por CodigoFuente con ServerID
        if server_id:
            query = f"""
            SELECT 
                CAST(ProductoID AS NVARCHAR(36)) as producto_id,
                CodigoFuente,
                Nombre,
                SystemType,
                CAST(ServerID AS NVARCHAR(36)) as server_id,
                CostoReceta,
                SyncRunID,
                SyncedAtMexico
            FROM Sync_Productos
            WHERE CodigoFuente = '{producto_id}'
            AND ServerID = '{server_id}'
            """
            result = execute_sql_query(*conn, query)
            producto = result[0] if result else None
    
    if not producto:
        return None, []
    
    # Obtener componentes de la receta
    srv_id = producto.get('server_id')
    codigo_fuente = producto.get('CodigoFuente')
    
    receta_query = f"""
    SELECT 
        CAST(r.RecetaDetalleID AS NVARCHAR(36)) as componente_id,
        r.ComponenteCodigoFuente as codigo_fuente,
        r.ComponenteNombre as nombre,
        COALESCE(r.TipoComponente, 'INSUMO_DIRECTO') as tipo_componente,
        r.Cantidad as cantidad,
        COALESCE(r.UnidadMedida, 'PZA') as unidad_medida,
        r.CostoUnitario as costo_unitario,
        r.CostoTotal as costo_total,
        r.PorcentajeCostoTotal as porcentaje_costo_total,
        COALESCE(r.NivelExplosion, 1) as nivel_jerarquico,
        CAST(r.EsElaborado AS BIT) as es_elaborado,
        r.RendimientoElaborado as rendimiento_elaborado
    FROM Sync_Productos_Recetas r
    WHERE r.ProductoCodigoFuente = '{codigo_fuente}'
    AND r.ServerID = '{srv_id}'
    ORDER BY r.OrdenVisual, r.ComponenteNombre
    """
    
    receta_result = execute_sql_query(*conn, receta_query) or []
    
    componentes = []
    for row in receta_result:
        componentes.append({
            'componente_id': row.get('componente_id', ''),
            'codigo_fuente': row.get('codigo_fuente', ''),
            'nombre': row.get('nombre', ''),
            'tipo_componente': row.get('tipo_componente', 'INSUMO_DIRECTO'),
            'cantidad': _safe_decimal(row.get('cantidad'), 0),
            'unidad_medida': row.get('unidad_medida', 'PZA'),
            'costo_unitario': _safe_decimal(row.get('costo_unitario')),
            'costo_total': _safe_decimal(row.get('costo_total')),
            'porcentaje_costo_total': _safe_decimal(row.get('porcentaje_costo_total')),
            'nivel_jerarquico': row.get('nivel_jerarquico', 1),
            'es_elaborado': bool(row.get('es_elaborado')),
            'rendimiento_elaborado': _safe_decimal(row.get('rendimiento_elaborado')),
        })
    
    return producto, componentes


# ==================== INSUMOS CONSOLIDADOS ====================

def get_insumos_producto(producto_id: str, server_id: Optional[str] = None) -> Tuple[Dict, List[Dict]]:
    """
    Obtiene lista consolidada de insumos de un producto.
    Fuente: EDARSAHUB SQL (NO-LIVE)
    """
    producto, componentes = get_receta_producto(producto_id, server_id)
    
    if not producto:
        return None, []
    
    # Consolidar insumos por código fuente
    insumos_consolidados = {}
    
    for comp in componentes:
        codigo = comp['codigo_fuente']
        if codigo not in insumos_consolidados:
            insumos_consolidados[codigo] = {
                'insumo_id': comp['componente_id'],
                'codigo_fuente': codigo,
                'nombre': comp['nombre'],
                'cantidad_total': 0,
                'unidad_medida': comp['unidad_medida'],
                'costo_unitario': comp['costo_unitario'],
                'costo_total': 0,
                'porcentaje_costo_total': 0,
                'origen': comp['tipo_componente'],
                'nivel_origen': comp['nivel_jerarquico'],
                'es_elaborado': comp['es_elaborado'],
            }
        
        insumos_consolidados[codigo]['cantidad_total'] += comp['cantidad'] or 0
        insumos_consolidados[codigo]['costo_total'] += comp['costo_total'] or 0
    
    # Calcular porcentajes
    costo_total_general = sum(i['costo_total'] for i in insumos_consolidados.values())
    for ins in insumos_consolidados.values():
        if costo_total_general > 0:
            ins['porcentaje_costo_total'] = round((ins['costo_total'] / costo_total_general) * 100, 2)
    
    return producto, list(insumos_consolidados.values())


# ==================== SYNC STATUS ====================

def get_sync_status() -> Dict[str, Any]:
    """
    Obtiene estado de sincronización.
    Fuente: EDARSAHUB SQL
    """
    conn = _get_edarsahub_connection()
    
    # Último sync
    sync_query = """
    SELECT TOP 1 SyncRunID, SyncedAtMexico
    FROM Sync_Productos
    ORDER BY SyncedAtMexico DESC
    """
    sync_result = execute_sql_query(*conn, sync_query)
    
    # Conteos por tabla
    tablas = [
        'Sync_Productos',
        'Sync_Productos_Familias',
        'Sync_Productos_SubFamilias',
        'Sync_Productos_Insumos',
        'Sync_Productos_Recetas',
        'Sync_Productos_Elaborados'
    ]
    
    conteos_tabla = []
    total_registros = 0
    for tabla in tablas:
        count_query = f"SELECT COUNT(*) as cnt FROM {tabla}"
        result = execute_sql_query(*conn, count_query)
        cnt = result[0].get('cnt', 0) if result else 0
        total_registros += cnt
        conteos_tabla.append({'tabla': tabla, 'registros': cnt})
    
    # Conteos por sistema
    sistema_query = """
    SELECT SystemType as sistema, COUNT(*) as cnt
    FROM Sync_Productos
    GROUP BY SystemType
    """
    sistema_result = execute_sql_query(*conn, sistema_query) or []
    conteos_sistema = [{'sistema': r['sistema'], 'registros': r['cnt']} for r in sistema_result]
    
    # Conteos por servidor
    servidor_query = """
    SELECT 
        CAST(p.ServerID AS NVARCHAR(36)) as servidor_id,
        p.SystemType as sistema,
        COUNT(*) as cnt
    FROM Sync_Productos p
    GROUP BY p.ServerID, p.SystemType
    """
    servidor_result = execute_sql_query(*conn, servidor_query) or []
    conteos_servidor = [
        {
            'servidor_id': r['servidor_id'],
            'servidor_nombre': None,  # Podría obtenerse de tabla Servidores
            'sistema': r['sistema'],
            'registros': r['cnt']
        } 
        for r in servidor_result
    ]
    
    sync_info = sync_result[0] if sync_result else {}
    
    # Determinar estado
    estado = 'EDARSAHUB_SQL'
    if total_registros == 0:
        estado = 'SIN_DATOS_EDARSAHUB'
    elif sync_info.get('SyncedAtMexico'):
        # Si la última sync fue hace más de 24 horas, marcar como STALE
        from datetime import timezone, timedelta
        ultima = sync_info.get('SyncedAtMexico')
        if ultima:
            try:
                if isinstance(ultima, datetime):
                    if (datetime.now() - ultima).days > 1:
                        estado = 'STALE_EDARSAHUB_SQL'
            except:
                pass
    
    return {
        'ultimo_sync_run_id': sync_info.get('SyncRunID'),
        'fecha_ultima_sincronizacion': sync_info.get('SyncedAtMexico'),
        'registros_por_tabla': conteos_tabla,
        'registros_por_sistema': conteos_sistema,
        'registros_por_servidor': conteos_servidor,
        'total_registros': total_registros,
        'errores': [],
        'warnings': [],
        'estado': estado,
    }
