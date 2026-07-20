from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Repository para el módulo Costos y Márgenes.
FASE 1C-3C - Acceso EXCLUSIVO a EDARSAHUB SQL (NO-LIVE)
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal

from core.db import execute_sql_query, execute_sql_query_params
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

def get_resumen_costos_margenes(
    unidad_negocio_pk: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Obtiene resumen general de costos y márgenes.
    Fuente: EDARSAHUB SQL (NO-LIVE)
    """
    conn = _get_edarsahub_connection()
    params: List[Any] = []
    unidad_where = ""
    if unidad_negocio_pk:
        unidad_where = "AND CONVERT(varchar(36), p.UnidadNegocioID) = %s"
        params.append(str(unidad_negocio_pk))
    
    # Query principal de productos
    productos_query = f"""
    SELECT 
        COUNT(*) as total_productos,
        SUM(CASE WHEN p.TieneReceta = 1 THEN 1 ELSE 0 END) as productos_con_receta,
        SUM(CASE WHEN p.TieneReceta = 0 OR p.TieneReceta IS NULL THEN 1 ELSE 0 END) as productos_sin_receta,
        AVG(CASE WHEN p.CostoReceta > 0 THEN p.CostoReceta END) as costo_promedio,
        AVG(CASE WHEN p.MargenBrutoPorcentaje IS NOT NULL AND p.PrecioVenta > 0 THEN p.MargenBrutoPorcentaje END) as margen_promedio,
        SUM(CASE WHEN p.MargenBrutoPorcentaje < 20 AND p.MargenBrutoPorcentaje IS NOT NULL THEN 1 ELSE 0 END) as margen_bajo,
        SUM(CASE WHEN p.CostoReceta IS NULL OR p.CostoReceta = 0 THEN 1 ELSE 0 END) as sin_costo,
        SUM(CASE WHEN p.PrecioVenta IS NULL OR p.PrecioVenta = 0 THEN 1 ELSE 0 END) as sin_precio,
        MAX(p.SyncedAtMexico) as ultima_sync,
        MAX(p.SyncRunID) as sync_run_id
    FROM Sync_Productos p
    WHERE (p.Activo = 1 OR p.Activo IS NULL)
      {unidad_where}
    """
    productos_result = execute_sql_query_params(*conn, productos_query, tuple(params))
    
    if unidad_negocio_pk:
        insumos_query = """
        SELECT COUNT(DISTINCT i.InsumoID) as total
        FROM Sync_Productos_Insumos i
        WHERE EXISTS (
            SELECT 1
            FROM Sync_Productos p
            WHERE p.ServerID = i.ServerID
              AND CONVERT(varchar(36), p.UnidadNegocioID) = %s
              AND (p.Activo = 1 OR p.Activo IS NULL)
        )
        """
        recetas_query = """
        SELECT COUNT(DISTINCT r.RecetaDetalleID) as total
        FROM Sync_Productos_Recetas r
        WHERE EXISTS (
            SELECT 1
            FROM Sync_Productos p
            WHERE p.ServerID = r.ServerID
              AND p.CodigoFuente = r.ProductoCodigoFuente
              AND CONVERT(varchar(36), p.UnidadNegocioID) = %s
              AND (p.Activo = 1 OR p.Activo IS NULL)
        )
        """
        elaborados_query = """
        SELECT COUNT(DISTINCT e.ElaboradoDetalleID) as total
        FROM Sync_Productos_Elaborados e
        WHERE EXISTS (
            SELECT 1
            FROM Sync_Productos p
            WHERE p.ServerID = e.ServerID
              AND CONVERT(varchar(36), p.UnidadNegocioID) = %s
              AND (p.Activo = 1 OR p.Activo IS NULL)
        )
        """
        insumos_result = execute_sql_query_params(*conn, insumos_query, (str(unidad_negocio_pk),))
        recetas_result = execute_sql_query_params(*conn, recetas_query, (str(unidad_negocio_pk),))
        elaborados_result = execute_sql_query_params(*conn, elaborados_query, (str(unidad_negocio_pk),))
    else:
        insumos_result = execute_sql_query(*conn, "SELECT COUNT(*) as total FROM Sync_Productos_Insumos")
        recetas_result = execute_sql_query(*conn, "SELECT COUNT(*) as total FROM Sync_Productos_Recetas")
        elaborados_result = execute_sql_query(*conn, "SELECT COUNT(*) as total FROM Sync_Productos_Elaborados")
    
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



def _mpro_comercial_where(alias: str = "p") -> str:
    """
    Filtro comercial para MPRO dentro de Costos y Márgenes.

    MPRO mezcla catálogo comercial POS con insumos/elaborados de producción.
    Para esta pantalla comercial se conserva el menú vendible/no inventariable
    y se excluyen elaborados de producción.
    """
    prefix = f"{alias}." if alias else ""
    return f"""(
        UPPER(ISNULL({prefix}SystemType, '')) <> 'MPRO'
        OR (
            ISNULL({prefix}EsVendible, 0) = 1
            AND ISNULL({prefix}EsInventariable, 0) = 0
            AND ISNULL({prefix}FamiliaCodigoFuente, '') <> '0019'
            AND ISNULL({prefix}SubFamiliaNombre, '') <> 'PRODUCCION'
        )
    )"""


def _mpro_menu_pos_where(alias: str = "p") -> str:
    """Conserva productos MPRO que existen en el menú POS sincronizado."""
    prefix = f"{alias}." if alias else ""

    return f"""(
        UPPER(ISNULL({prefix}SystemType, '')) <> 'MPRO'
        OR EXISTS (
            SELECT 1
            FROM dbo.Comercial_MPRO_MenuPOS_Sync mpos
            WHERE mpos.ServerID = {prefix}ServerID
              AND mpos.Activo = 1
              AND mpos.ProductoCodigoFuentePadded = {prefix}CodigoFuente
        )
    )"""


# ==================== PRODUCTOS ====================

def get_productos_con_costos(
    empresa_id: Optional[int] = None,
    unidad_negocio_pk: Optional[str] = None,
    servidor_id: Optional[str] = None,
    servidores_ids: Optional[List[str]] = None,  # FASE P2: RBAC por Unidad
    sistema_origen: Optional[str] = None,
    familia: Optional[str] = None,
    subfamilia: Optional[str] = None,
    busqueda: Optional[str] = None,
    solo_con_receta: bool = False,
    margen_bajo: bool = False,
    umbral_margen: int = 20,  # Umbral editable para margen bajo
    incluir_inactivos: bool = False,  # BUG-COSTOS-001: Por defecto excluir inactivos
    page: int = 1,
    page_size: int = 50,
) -> Tuple[List[Dict], int]:
    """
    Obtiene lista de productos con costos y márgenes.
    Fuente: EDARSAHUB SQL (NO-LIVE)
    
    FASE P2: Nuevo parámetro servidores_ids para RBAC por Unidad de Negocio.
    Si se proporciona, filtra productos que pertenezcan a cualquiera de esos servidores.
    
    BUG-COSTOS-001: Por defecto solo muestra productos activos.
    Usar incluir_inactivos=True para ver también productos inactivos/dados de baja.
    
    BUG-COSTOS-001-R2: El filtro correcto es SOLO Activo = 1.
    NO usar PrecioVenta > 0 como criterio de activo.
    Productos con precio $0 pueden ser activos.
    """
    conn = _get_edarsahub_connection()
    
    # BUG-COSTOS-001-R2: Solo usar Activo = 1, NO PrecioVenta > 0
    if not incluir_inactivos:
        where_clauses = ["p.Activo = 1"]
    else:
        where_clauses = ["1=1"]
    query_params: List[Any] = []
    
    if empresa_id:
        where_clauses.append("p.EmpresaID = %s")
        query_params.append(empresa_id)
    if unidad_negocio_pk:
        where_clauses.append("CONVERT(varchar(36), p.UnidadNegocioID) = %s")
        query_params.append(str(unidad_negocio_pk))
    if servidor_id:
        where_clauses.append("CAST(p.ServerID AS NVARCHAR(36)) = %s")
        query_params.append(str(servidor_id))
    
    # FASE P2: RBAC - Filtrar por múltiples servidores permitidos
    if servidores_ids and len(servidores_ids) > 0:
        servers = [str(s) for s in servidores_ids if str(s).strip()]
        if servers:
            placeholders = ",".join(["%s"] * len(servers))
            where_clauses.append(
                f"CAST(p.ServerID AS NVARCHAR(36)) IN ({placeholders})"
            )
            query_params.extend(servers)
        else:
            where_clauses.append("1=0")
    
    receta_real_sql = """EXISTS (
        SELECT 1
        FROM Sync_Productos_Recetas r_chk
        WHERE r_chk.ProductoCodigoFuente = p.CodigoFuente
          AND r_chk.ServerID = p.ServerID
    )"""

    receta_comercial_sql = f"""(
        (
            UPPER(ISNULL(p.SystemType, '')) = 'MPRO'
            AND (
                ISNULL(p.EsCompuesto, 0) = 1
                OR ISNULL(p.CantidadComponentesReceta, 0) > 0
                OR {receta_real_sql}
            )
        )
        OR (
            UPPER(ISNULL(p.SystemType, '')) <> 'MPRO'
            AND {receta_real_sql}
        )
    )"""

    where_clauses.append(_mpro_comercial_where("p"))
    where_clauses.append(_mpro_menu_pos_where("p"))

    if sistema_origen:
        where_clauses.append("p.SystemType = %s")
        query_params.append(str(sistema_origen))
    if familia:
        familia_value = familia.strip()
        familia_like = f"%{familia_value}%"
        where_clauses.append("""(
            p.FamiliaNombre LIKE %s
            OR p.FamiliaCodigoFuente = %s
            OR EXISTS (
                SELECT 1
                FROM Sync_Productos pfam
                WHERE pfam.ServerID = p.ServerID
                  AND pfam.SystemType = p.SystemType
                  AND ISNULL(pfam.Activo, 1) = 1
                  AND pfam.FamiliaCodigoFuente IS NOT NULL
                  AND pfam.FamiliaCodigoFuente <> ''
                  AND (
                      pfam.FamiliaNombre LIKE %s
                      OR pfam.FamiliaCodigoFuente = %s
                  )
                  AND (
                      p.FamiliaCodigoFuente = pfam.FamiliaCodigoFuente
                      OR (
                          UPPER(ISNULL(p.SystemType, '')) LIKE '%SOFT%'
                          AND p.CodigoFuente LIKE pfam.FamiliaCodigoFuente + '%'
                      )
                  )
            )
        )""")
        query_params.extend([familia_like, familia_value, familia_like, familia_value])
    if subfamilia:
        where_clauses.append("p.SubFamiliaNombre LIKE %s")
        query_params.append(f"%{subfamilia.strip()}%")
    if busqueda:
        busqueda_like = f"%{busqueda.strip()}%"
        where_clauses.append("(p.Nombre LIKE %s OR p.CodigoFuente LIKE %s)")
        query_params.extend([busqueda_like, busqueda_like])
    if solo_con_receta:
        where_clauses.append(receta_comercial_sql)
    
    # MARGEN BAJO: Filtrar productos con margen < umbral configurado
    # El costo real viene de Sync_Productos_Recetas (no de p.CostoReceta)
    # Requiere: receta, precio > 0, costo calculado > 0, margen < umbral
    if margen_bajo:
        where_clauses.append(f"""(
            {receta_real_sql}
            AND p.PrecioVenta > 0 
            AND COALESCE(
                (SELECT SUM(r.CostoTotal) FROM Sync_Productos_Recetas r 
                 WHERE r.ProductoCodigoFuente = p.CodigoFuente AND r.ServerID = p.ServerID),
                p.CostoReceta, 0
            ) > 0
            AND (
                (p.PrecioVenta - COALESCE(
                    (SELECT SUM(r.CostoTotal) FROM Sync_Productos_Recetas r 
                     WHERE r.ProductoCodigoFuente = p.CodigoFuente AND r.ServerID = p.ServerID),
                    p.CostoReceta, 0
                )) / p.PrecioVenta * 100
            ) < %s
        )""")
        query_params.append(umbral_margen)
    
    where_sql = " AND ".join(where_clauses)
    
    # Query de conteo total
    count_query = f"""
    SELECT COUNT(*) as total
    FROM Sync_Productos p
    WHERE {where_sql}
    """
    count_result = execute_sql_query_params(*conn, count_query, tuple(query_params))
    total = count_result[0].get('total', 0) if count_result else 0
    
    # Query de datos con paginación
    # NOTA: CostoReceta en Sync_Productos puede estar en 0, así que calculamos
    # el costo real sumando CostoTotal de Sync_Productos_Recetas
    offset = (page - 1) * page_size
    # FASE 1C-3G-B: Incluir TasaImpuesto para validación de pricing
    data_query = f"""
    SELECT 
        CAST(p.ProductoID AS NVARCHAR(36)) as producto_id,
        p.CodigoFuente as id_producto_origen,
        p.Nombre as nombre,
        p.NombreCorto as nombre_corto,
        p.SystemType as sistema_origen,
        CAST(p.ServerID AS NVARCHAR(36)) as server_id,
        p.EmpresaID as empresa_id,
        p.UnidadNegocioID as unidad_negocio_pk,
        COALESCE(p.FamiliaNombre, 'Sin clasificar') as familia,
        p.SubFamiliaNombre as subfamilia,
        p.PrecioVenta as precio_venta,
        p.PrecioSinImpuestos as precio_sin_impuestos,
        p.TasaImpuesto as tasa_impuesto,
        COALESCE(
            (SELECT SUM(r.CostoTotal) 
             FROM Sync_Productos_Recetas r 
             WHERE r.ProductoCodigoFuente = p.CodigoFuente 
             AND r.ServerID = p.ServerID),
            p.CostoReceta,
            0
        ) as costo_receta,
        p.CostoPromedio as costo_promedio,
        p.MargenBrutoPesos as margen_pesos,
        p.MargenBrutoPorcentaje as margen_porcentaje,
        p.MargenObjetivo as margen_objetivo,
        CAST(CASE WHEN (
            (
                UPPER(ISNULL(p.SystemType, '')) = 'MPRO'
                AND (
                    ISNULL(p.EsCompuesto, 0) = 1
                    OR ISNULL(p.CantidadComponentesReceta, 0) > 0
                    OR EXISTS (
                        SELECT 1
                        FROM Sync_Productos_Recetas r_chk
                        WHERE r_chk.ProductoCodigoFuente = p.CodigoFuente
                          AND r_chk.ServerID = p.ServerID
                    )
                )
            )
            OR (
                UPPER(ISNULL(p.SystemType, '')) <> 'MPRO'
                AND EXISTS (
                    SELECT 1
                    FROM Sync_Productos_Recetas r_chk
                    WHERE r_chk.ProductoCodigoFuente = p.CodigoFuente
                      AND r_chk.ServerID = p.ServerID
                )
            )
        ) THEN 1 ELSE 0 END AS BIT) as tiene_receta,
        CAST(p.TieneSubRecetas AS BIT) as tiene_subrecetas,
        COALESCE(
            NULLIF(p.CantidadComponentesReceta, 0),
            (SELECT COUNT(1)
             FROM Sync_Productos_Recetas r_cnt
             WHERE r_cnt.ProductoCodigoFuente = p.CodigoFuente
               AND r_cnt.ServerID = p.ServerID),
            0
        ) as numero_insumos,
        p.SyncedAtMexico as ultima_sincronizacion,
        p.Activo as activo
    FROM Sync_Productos p
    WHERE {where_sql}
    ORDER BY p.Nombre
    OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
    """
    
    data_result = execute_sql_query_params(*conn, data_query, tuple(query_params)) or []
    
    # Procesar resultados y calcular márgenes dinámicamente
    productos = []
    for row in data_result:
        precio_venta = _safe_decimal(row.get('precio_venta'), 0) or 0
        costo_receta = _safe_decimal(row.get('costo_receta'), 0) or 0
        
        # Calcular margen dinámicamente si no está en la BD
        margen_pesos_bd = _safe_decimal(row.get('margen_pesos'))
        margen_porcentaje_bd = _safe_decimal(row.get('margen_porcentaje'))
        
        # Si los márgenes de BD son 0 o None, calcularlos
        if (margen_pesos_bd is None or margen_pesos_bd == 0) and precio_venta > 0 and costo_receta > 0:
            margen_pesos = round(precio_venta - costo_receta, 2)
            margen_porcentaje = round((margen_pesos / precio_venta) * 100, 2) if precio_venta > 0 else 0
        else:
            margen_pesos = margen_pesos_bd
            margen_porcentaje = margen_porcentaje_bd
        
        # FASE 1C-3G-B: Obtener tasa de impuesto
        tasa_impuesto_raw = _safe_decimal(row.get('tasa_impuesto'))
        
        # Determinar estado de impuesto:
        # -1 = IMPUESTO_NO_CONFIGURADO (no permite cálculo de precio)
        # 0 = Tasa cero válida (alimentos)
        # >0 = IVA/IEPS normal
        estado_impuesto = 'OK'
        if tasa_impuesto_raw == -1:
            estado_impuesto = 'IMPUESTO_NO_CONFIGURADO'
            tasa_impuesto = None  # No mostrar -1 en UI
        else:
            tasa_impuesto = tasa_impuesto_raw
        
        productos.append({
            'producto_id': row.get('producto_id', ''),
            'id_producto_origen': row.get('id_producto_origen', ''),
            'nombre': row.get('nombre', ''),
            'nombre_corto': row.get('nombre_corto'),
            'sistema_origen': row.get('sistema_origen', ''),
            'system_type': row.get('sistema_origen', ''),  # Alias para compatibilidad
            'server_id': row.get('server_id', ''),
            'empresa_id': row.get('empresa_id'),
            'unidad_negocio_pk': row.get('unidad_negocio_pk'),
            'familia': row.get('familia'),
            'subfamilia': row.get('subfamilia'),
            'precio_venta': precio_venta if precio_venta > 0 else _safe_decimal(row.get('precio_venta')),
            'precio_sin_impuestos': _safe_decimal(row.get('precio_sin_impuestos')),
            'tasa_impuesto': tasa_impuesto,
            'estado_impuesto': estado_impuesto,
            'costo_receta': costo_receta if costo_receta > 0 else _safe_decimal(row.get('costo_receta')),
            'costo_promedio': _safe_decimal(row.get('costo_promedio')),
            'margen_pesos': margen_pesos,
            'margen_porcentaje': margen_porcentaje,
            'margen_objetivo': _safe_decimal(row.get('margen_objetivo')),
            'tiene_receta': bool(row.get('tiene_receta')),
            'tiene_subrecetas': bool(row.get('tiene_subrecetas')),
            'numero_insumos': row.get('numero_insumos', 0) or 0,
            'ultima_sincronizacion': row.get('ultima_sincronizacion'),
            # BUG-COSTOS-001-R2: Campo activo para badges en UI
            'activo': bool(row.get('activo', 1)),
        })
    
    return productos, total


# ==================== RECETA EXPANDIDA ====================

def get_producto_by_id(producto_id: str) -> Optional[Dict]:
    """Obtiene un producto por su ID."""
    conn = _get_edarsahub_connection()
    
    query = f"""
    SELECT 
        CAST(ProductoID AS NVARCHAR(36)) as ProductoID,
        CodigoFuente,
        Nombre,
        SystemType,
        CAST(ServerID AS NVARCHAR(36)) as ServerID,
        CostoReceta,
        SyncRunID,
        SyncedAtMexico
    FROM Sync_Productos
    WHERE (
        TRY_CONVERT(UNIQUEIDENTIFIER, '{producto_id}') IS NOT NULL
        AND ProductoID = TRY_CONVERT(UNIQUEIDENTIFIER, '{producto_id}')
    )
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
                CAST(ProductoID AS NVARCHAR(36)) as ProductoID,
                CodigoFuente,
                Nombre,
                SystemType,
                CAST(ServerID AS NVARCHAR(36)) as ServerID,
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
    srv_id = producto.get('ServerID') or producto.get('server_id') or server_id
    codigo_fuente = producto.get('CodigoFuente')
    
    receta_query = f"""
    SELECT 
        CAST(r.RecetaDetalleID AS NVARCHAR(36)) as componente_id,
        r.ComponenteCodigoFuente as codigo_fuente,
        r.ComponenteNombre as nombre,
        COALESCE(r.TipoComponente, 'INSUMO_DIRECTO') as tipo_componente,
        r.Cantidad as Cantidad,
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
    
    # Primero calcular el costo total de todos los componentes para el %
    costo_total_receta = sum(_safe_decimal(row.get('costo_total'), 0) for row in receta_result)
    
    componentes = []
    for row in receta_result:
        costo_comp = _safe_decimal(row.get('costo_total'), 0)
        # Calcular porcentaje dinámicamente
        porcentaje = round((costo_comp / costo_total_receta * 100), 2) if costo_total_receta > 0 else 0
        
        componentes.append({
            'componente_id': row.get('componente_id', ''),
            'codigo_fuente': row.get('codigo_fuente', ''),
            'nombre': row.get('nombre', ''),
            'tipo_componente': row.get('tipo_componente', 'INSUMO_DIRECTO'),
            'cantidad': _safe_decimal(row.get('cantidad'), 0),
            'unidad_medida': row.get('unidad_medida', 'PZA'),
            'costo_unitario': _safe_decimal(row.get('costo_unitario')),
            'costo_total': costo_comp,
            'porcentaje_costo_total': porcentaje,
            'nivel_jerarquico': row.get('nivel_jerarquico', 1),
            'es_elaborado': bool(row.get('es_elaborado')),
            'rendimiento_elaborado': _safe_decimal(row.get('rendimiento_elaborado')),
        })
    
    return producto, componentes


# ==================== RECETA DE ELABORADO (SUB-RECETA) ====================

def get_receta_elaborado(codigo_elaborado: str, server_id: Optional[str] = None) -> Tuple[Optional[Dict], List[Dict]]:
    """
    Obtiene la receta de un insumo elaborado desde Sync_Productos_Elaborados.
    
    Los elaborados NO existen en Sync_Productos, sus recetas están en 
    Sync_Productos_Elaborados donde InsumoElaboradoCodigoFuente es el código del elaborado.
    
    Args:
        codigo_elaborado: Código fuente del insumo elaborado
        server_id: ServerID para filtrar
    
    Returns:
        Tuple[producto_info, componentes]
    """
    conn = _get_edarsahub_connection()
    
    # Primero buscar info del elaborado en Sync_Productos_Insumos
    where_srv = f"AND CAST(ServerID AS NVARCHAR(36)) = '{server_id}'" if server_id else ""
    
    insumo_query = f"""
    SELECT TOP 1
        CAST(InsumoID AS NVARCHAR(36)) as insumo_id,
        CodigoFuente,
        Nombre,
        SystemType,
        CAST(ServerID AS NVARCHAR(36)) as ServerID,
        Costo,
        EsElaborado,
        RendimientoElaborado,
        SyncRunID,
        SyncedAtMexico
    FROM Sync_Productos_Insumos
    WHERE LTRIM(RTRIM(CodigoFuente)) = LTRIM(RTRIM('{codigo_elaborado}'))
    {where_srv}
    """
    insumo_result = execute_sql_query(*conn, insumo_query)
    
    if not insumo_result:
        # Intentar buscar en Sync_Productos (algunos elaborados pueden estar ahí)
        producto_query = f"""
        SELECT TOP 1
            CAST(ProductoID AS NVARCHAR(36)) as ProductoID,
            CodigoFuente,
            Nombre,
            SystemType,
            CAST(ServerID AS NVARCHAR(36)) as ServerID,
            CostoReceta as Costo,
            1 as EsElaborado,
            SyncRunID,
            SyncedAtMexico
        FROM Sync_Productos
        WHERE LTRIM(RTRIM(CodigoFuente)) = LTRIM(RTRIM('{codigo_elaborado}'))
        {where_srv}
        """
        insumo_result = execute_sql_query(*conn, producto_query)
        
        if insumo_result:
            # Si lo encontramos como producto, usar get_receta_producto
            return get_receta_producto(codigo_elaborado, server_id)
    
    if not insumo_result:
        return None, []
    
    insumo_info = insumo_result[0]
    srv_id = insumo_info.get('server_id') or server_id
    
    # Buscar los componentes del elaborado en Sync_Productos_Elaborados
    # También verificar si cada componente es a su vez un elaborado
    elaborado_query = f"""
    SELECT 
        CAST(e.ElaboradoDetalleID AS NVARCHAR(36)) as componente_id,
        LTRIM(RTRIM(e.ComponenteCodigoFuente)) as codigo_fuente,
        e.ComponenteNombre as nombre,
        'INSUMO' as tipo_componente,
        e.Cantidad as cantidad,
        COALESCE(e.UnidadMedida, 'PZA') as unidad_medida,
        e.CostoUnitario as costo_unitario,
        e.CostoTotal as costo_total,
        1 as nivel_jerarquico,
        COALESCE(i.EsElaborado, 0) as es_elaborado,
        i.RendimientoElaborado as rendimiento_elaborado
    FROM Sync_Productos_Elaborados e
    LEFT JOIN Sync_Productos_Insumos i 
        ON LTRIM(RTRIM(i.CodigoFuente)) = LTRIM(RTRIM(e.ComponenteCodigoFuente))
        AND i.ServerID = e.ServerID
    WHERE LTRIM(RTRIM(e.InsumoElaboradoCodigoFuente)) = LTRIM(RTRIM('{codigo_elaborado}'))
    AND CAST(e.ServerID AS NVARCHAR(36)) = '{srv_id}'
    ORDER BY e.ComponenteNombre
    """
    
    elaborado_result = execute_sql_query(*conn, elaborado_query) or []
    
    # Calcular costo total y porcentajes
    costo_total = sum(_safe_decimal(row.get('costo_total'), 0) for row in elaborado_result)
    
    componentes = []
    for row in elaborado_result:
        costo_comp = _safe_decimal(row.get('costo_total'), 0)
        porcentaje = round((costo_comp / costo_total * 100), 2) if costo_total > 0 else 0
        
        componentes.append({
            'componente_id': row.get('componente_id', ''),
            'codigo_fuente': row.get('codigo_fuente', ''),
            'nombre': row.get('nombre', ''),
            'tipo_componente': row.get('tipo_componente', 'INSUMO'),
            'cantidad': _safe_decimal(row.get('cantidad'), 0),
            'unidad_medida': row.get('unidad_medida', 'PZA'),
            'costo_unitario': _safe_decimal(row.get('costo_unitario')),
            'costo_total': costo_comp,
            'porcentaje_costo_total': porcentaje,
            'nivel_jerarquico': 1,
            'es_elaborado': bool(row.get('es_elaborado')),
            'rendimiento_elaborado': _safe_decimal(row.get('rendimiento_elaborado')),
        })
    
    # Construir info del "producto" (elaborado)
    elaborado_info = {
        'producto_id': insumo_info.get('insumo_id', ''),
        'CodigoFuente': insumo_info.get('CodigoFuente', ''),
        'Nombre': insumo_info.get('Nombre', ''),
        'SystemType': insumo_info.get('SystemType', ''),
        'server_id': srv_id,
        'CostoReceta': costo_total,
        'SyncRunID': insumo_info.get('SyncRunID'),
        'SyncedAtMexico': insumo_info.get('SyncedAtMexico'),
    }
    
    return elaborado_info, componentes



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
            except (TypeError, AttributeError):
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



# ==================== UNIDADES DE NEGOCIO ====================

def get_unidades_negocio() -> List[Dict[str, Any]]:
    """
    Obtiene lista de unidades de negocio activas desde EDARSAHUB.
    
    Fuente: Tabla Unidades_Negocio en EDARSAHUB SQL
    NO-LIVE: No consulta sistemas externos.
    """
    conn = _get_edarsahub_connection()
    
    query = """
    SELECT 
        id,
        codigo,
        nombre,
        CAST(server_id AS NVARCHAR(36)) as server_id,
        sucursal_origen_id,
        system_type,
        activo,
        orden
    FROM Unidades_Negocio
    WHERE activo = 1
    ORDER BY orden, nombre
    """
    
    result = execute_sql_query(*conn, query)
    
    unidades = []
    for row in result or []:
        unidades.append({
            'id': row.get('id'),
            'codigo': row.get('codigo', ''),
            'nombre': row.get('nombre', ''),
            'server_id': row.get('server_id', ''),
            'sucursal_origen_id': row.get('sucursal_origen_id'),
            'system_type': row.get('system_type', ''),
            'orden': row.get('orden', 0)
        })
    
    return unidades


# ==================== FAMILIAS Y SUBFAMILIAS ====================

def get_familias_productos(
    servidor_id: Optional[str] = None,
    servidores_ids: Optional[List[str]] = None,
    unidad_negocio_pk: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Obtiene lista de familias únicas de productos desde EDARSAHUB.
    
    Args:
        servidor_id: Filtrar por unidad de negocio específica (ServerID)
        servidores_ids: FASE P2 RBAC - Lista de servidores permitidos
    
    Fuente: Tabla Sync_Productos en EDARSAHUB SQL
    NO-LIVE: No consulta sistemas externos.
    """
    conn = _get_edarsahub_connection()
    
    where_clause = (
        "WHERE p.FamiliaNombre IS NOT NULL "
        "AND p.FamiliaNombre != '' "
        f"AND {_mpro_comercial_where('p')} "
        f"AND {_mpro_menu_pos_where('p')}"
    )
    params: List[Any] = []
    if unidad_negocio_pk:
        where_clause += " AND CONVERT(varchar(36), p.UnidadNegocioID) = %s"
        params.append(str(unidad_negocio_pk))
    elif servidor_id:
        where_clause += " AND CAST(p.ServerID AS NVARCHAR(36)) = %s"
        params.append(str(servidor_id))
    
    # FASE P2: RBAC - Filtrar por múltiples servidores permitidos
    if servidores_ids and len(servidores_ids) > 0 and not servidor_id and not unidad_negocio_pk:
        servers = [str(s) for s in servidores_ids if str(s).strip()]
        if servers:
            placeholders = ",".join(["%s"] * len(servers))
            where_clause += f" AND CAST(p.ServerID AS NVARCHAR(36)) IN ({placeholders})"
            params.extend(servers)
        else:
            where_clause += " AND 1=0"
    
    query = f"""
    SELECT 
        FamiliaNombre as familia,
        COUNT(*) as total_productos
    FROM Sync_Productos p
    {where_clause}
    GROUP BY FamiliaNombre
    ORDER BY FamiliaNombre
    """
    
    result = execute_sql_query_params(*conn, query, tuple(params))
    
    familias = []
    for row in result or []:
        familias.append({
            'familia': row.get('familia', ''),
            'codigo': '',
            'total_productos': row.get('total_productos', 0)
        })
    
    return familias


def get_subfamilias_productos(
    familia: Optional[str] = None,
    servidor_id: Optional[str] = None,
    unidad_negocio_pk: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Obtiene lista de subfamilias de productos desde EDARSAHUB.
    
    Args:
        familia: Filtrar por familia
        servidor_id: Filtrar por unidad de negocio (ServerID)
    
    Fuente: Tabla Sync_Productos en EDARSAHUB SQL
    NO-LIVE: No consulta sistemas externos.
    """
    conn = _get_edarsahub_connection()
    
    where_clause = (
        "WHERE p.SubFamiliaNombre IS NOT NULL "
        "AND p.SubFamiliaNombre != '' "
        f"AND {_mpro_comercial_where('p')} "
        f"AND {_mpro_menu_pos_where('p')}"
    )
    params: List[Any] = []
    if familia:
        where_clause += " AND p.FamiliaNombre = %s"
        params.append(str(familia))
    if unidad_negocio_pk:
        where_clause += " AND CONVERT(varchar(36), p.UnidadNegocioID) = %s"
        params.append(str(unidad_negocio_pk))
    elif servidor_id:
        where_clause += " AND CAST(p.ServerID AS NVARCHAR(36)) = %s"
        params.append(str(servidor_id))
    
    query = f"""
    SELECT 
        FamiliaNombre as familia,
        SubFamiliaNombre as subfamilia,
        COUNT(*) as total_productos
    FROM Sync_Productos p
    {where_clause}
    GROUP BY FamiliaNombre, SubFamiliaNombre
    ORDER BY FamiliaNombre, SubFamiliaNombre
    """
    
    result = execute_sql_query_params(*conn, query, tuple(params))
    
    subfamilias = []
    for row in result or []:
        subfamilias.append({
            'familia': row.get('familia', ''),
            'subfamilia': row.get('subfamilia', ''),
            'codigo': '',
            'total_productos': row.get('total_productos', 0)
        })
    
    return subfamilias
