"""
Fuentes canónicas NO-LIVE para Análisis de Inventarios SoftRestaurant.

- Movimientos: Inventario_Movimientos + Detalle + TipoMovimiento.
- Ventas/consumos: Comercial_Inteligencia_VentasDetalleProducto + recetas.
- Identidad: unidad canónica -> Empresa/Sucursal mediante resolver central.
"""
from collections import defaultdict
from typing import Any, Dict, List, Sequence, Tuple

from core.inventarios.resolver_canonico import resolver_empresa_id, resolver_sucursal_id
from core.recetas_service import RecetasService


def _text(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _float(v: Any) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _unique(values: Sequence[Any]) -> List[str]:
    return list(dict.fromkeys(_text(v) for v in values if _text(v)))


def _fetch_table_columns(cursor, table_name: str) -> set:
    cursor.execute(
        """
        SELECT LOWER(COLUMN_NAME) AS column_name
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=%s
        """,
        (table_name,),
    )
    return {_text(r.get("column_name")).lower() for r in (cursor.fetchall() or [])}


def _fetch_soft_ledger_net(
    cursor,
    *,
    server_id: str,
    unidad_codigo: str,
    sucursal_origen_id: str,
    fecha_ini,
    fecha_fin,
    warehouses: Sequence[str],
    visible_product_codes: Sequence[str] = (),
) -> Dict[str, float]:
    empresa = resolver_empresa_id(unidad_codigo)
    sucursal = resolver_sucursal_id(server_id, sucursal_origen_id or None)
    if not empresa.resuelto or not sucursal.resuelto:
        return {}

    visible_product_codes = _unique(visible_product_codes)
    preferred_order = ""
    preferred_params: List[Any] = []
    if visible_product_codes:
        preferred_ph = ",".join(["%s"] * len(visible_product_codes))
        preferred_order = (
            f"CASE WHEN pmo.CodigoFuente IN ({preferred_ph}) THEN 0 ELSE 1 END,"
        )
        preferred_params.extend(visible_product_codes)

    params: List[Any] = [
        server_id,
        *preferred_params,
        int(empresa.canonical_id),
        int(sucursal.canonical_id),
        fecha_ini,
        fecha_fin,
    ]
    warehouse_filter = ""
    warehouses = _unique(warehouses)
    if warehouses:
        ph = ",".join(["%s"] * len(warehouses))
        # El scope puede llegar como AlmacenID canónico (int serializado), código
        # de origen o nombre visible. Priorizar/aceptar los tres evita que un
        # inventario físico válido deje movimientos en cero por discrepancia de
        # identificador entre snapshots y el ledger canónico.
        warehouse_filter = (
            f" AND (CONVERT(varchar(50), a.AlmacenID) IN ({ph}) "
            f"OR a.CodigoAlmacen IN ({ph}) OR a.NombreAlmacen IN ({ph}))"
        )
        params.extend(warehouses)
        params.extend(warehouses)
        params.extend(warehouses)

    cursor.execute(
        f"""
        SELECT
            alias.codigo_producto,
            SUM(
                CASE
                    WHEN UPPER(LTRIM(RTRIM(ISNULL(tm.Naturaleza,''))))
                         IN ('E','EN','ENTRADA')
                    THEN ISNULL(d.Cantidad,0)
                    ELSE -ISNULL(d.Cantidad,0)
                END
            ) AS cantidad
        FROM dbo.Inventario_MovimientosDetalle d
        INNER JOIN dbo.Inventario_Movimientos m
            ON m.MovimientoID=d.MovimientoID
        INNER JOIN dbo.Inventario_TipoMovimiento tm
            ON tm.TipoMovimientoID=m.TipoMovimientoID
        LEFT JOIN dbo.Inventario_Almacenes a
            ON a.AlmacenID=m.AlmacenID
        OUTER APPLY (
            SELECT TOP 1
                pmo.CodigoFuente AS codigo_producto
            FROM dbo.Producto_MapeoOrigen pmo
            WHERE pmo.ProductoID=d.ProductoID
              AND LOWER(CONVERT(varchar(36),pmo.ServerID))=LOWER(%s)
              AND UPPER(pmo.SystemType) IN ('SOFTRESTAURANT','SOFTRESTAURANT_PRO')
              AND pmo.Activo=1
            ORDER BY
                {preferred_order}
                pmo.CodigoFuente
        ) alias
        WHERE m.EmpresaID=%s
          AND m.SucursalID=%s
          AND m.FechaMovimiento >= %s
          AND m.FechaMovimiento <= %s
          AND ISNULL(m.Activo,1)=1
          AND alias.codigo_producto IS NOT NULL
          {warehouse_filter}
        GROUP BY alias.codigo_producto
        """,
        tuple(params),
    )
    return {
        _text(row.get("codigo_producto")): _float(row.get("cantidad"))
        for row in (cursor.fetchall() or [])
        if _text(row.get("codigo_producto"))
    }


def _fetch_soft_sales_rows(
    cursor,
    *,
    unidad_codigo: str,
    server_id: str,
    fecha_ini,
    fecha_fin,
    group_by_date: bool = False,
) -> List[Dict[str, Any]]:
    columns = _fetch_table_columns(cursor, "Comercial_Inteligencia_VentasDetalleProducto")
    required = {"unidad_negocio_id", "fecha_operacion", "producto_codigo_fuente", "cantidad"}
    if not required.issubset(columns):
        return []

    extra = []
    params: List[Any] = [unidad_codigo, fecha_ini, fecha_fin]
    if "activo" in columns:
        extra.append("ISNULL(activo,1)=1")
    if "cancelado_origen" in columns:
        extra.append("ISNULL(cancelado_origen,0)=0")
    if "es_kpi_valido" in columns:
        extra.append("ISNULL(es_kpi_valido,1)=1")
    if "server_id" in columns:
        extra.append("LOWER(ISNULL(server_id,''))=LOWER(%s)")
        params.append(server_id)

    date_select = "CAST(fecha_operacion AS date) AS fecha_operacion, " if group_by_date else ""
    date_group = "CAST(fecha_operacion AS date), " if group_by_date else ""
    cursor.execute(
        f"""
        SELECT {date_select}producto_codigo_fuente,
               SUM(ISNULL(cantidad,0)) AS cantidad
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        WHERE unidad_negocio_id=%s
          AND fecha_operacion >= CAST(%s AS date)
          AND fecha_operacion <= CAST(%s AS date)
          AND NULLIF(LTRIM(RTRIM(producto_codigo_fuente)),'') IS NOT NULL
          {" AND " + " AND ".join(extra) if extra else ""}
        GROUP BY {date_group}producto_codigo_fuente
        """,
        tuple(params),
    )
    return list(cursor.fetchall() or [])


def _explode_sales_to_consumption(
    server_id: str,
    sales_rows: Sequence[Dict[str, Any]],
) -> Dict[str, float]:
    sold = {
        _text(r.get("producto_codigo_fuente")): _float(r.get("cantidad"))
        for r in sales_rows or []
        if _text(r.get("producto_codigo_fuente"))
    }
    if not sold:
        return {}

    components = RecetasService.get_componentes_bulk(server_id, list(sold))
    consumption: Dict[str, float] = defaultdict(float)
    for row in components or []:
        prod = _text(row.get("producto_codigo_fuente"))
        comp = _text(row.get("componente_codigo_fuente"))
        if not prod or not comp or prod not in sold:
            continue
        consumption[comp] += sold[prod] * _float(row.get("cantidad"))
    return dict(consumption)


def fetch_soft_activity_canonical(
    cursor,
    *,
    server_id: str,
    unidad_codigo: str,
    sucursal_origen_id: str,
    movement_start,
    movement_end,
    sales_start,
    sales_end,
    warehouses: Sequence[str],
    visible_product_codes: Sequence[str] = (),
    include_sales: bool = True,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    movimientos = _fetch_soft_ledger_net(
        cursor,
        server_id=server_id,
        unidad_codigo=unidad_codigo,
        sucursal_origen_id=sucursal_origen_id,
        fecha_ini=movement_start,
        fecha_fin=movement_end,
        warehouses=warehouses,
        visible_product_codes=visible_product_codes,
    )
    if not include_sales:
        return movimientos, {}

    sales_rows = _fetch_soft_sales_rows(
        cursor,
        unidad_codigo=unidad_codigo,
        server_id=server_id,
        fecha_ini=sales_start,
        fecha_fin=sales_end,
    )
    ventas = _explode_sales_to_consumption(server_id, sales_rows)
    return movimientos, ventas


def get_soft_sales_consumption_detail(
    cursor,
    *,
    unidad_codigo: str,
    server_id: str,
    componente_codigo: str,
    fecha_ini,
    fecha_fin,
) -> Dict[str, Any]:
    """Desglosa VENTAS con la misma consulta y receta del análisis SoftRestaurant.

    Se agrupan las mismas filas de venta por fecha y producto para conservar
    el día de operación; la explosión utiliza RecetasService exactamente como
    _explode_sales_to_consumption, sin consultar al POS en vivo.
    """
    # Reportes puede agrupar insumos de igual nombre/unidad y remitir varios
    # códigos de origen separados por coma. Se conserva la misma suma del padre.
    componentes_seleccionados = {
        _text(value) for value in _text(componente_codigo).split(",") if _text(value)
    }
    if not componentes_seleccionados:
        return {"rows": [], "total": 0.0}

    sales_rows = _fetch_soft_sales_rows(
        cursor,
        unidad_codigo=unidad_codigo,
        server_id=server_id,
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
        group_by_date=True,
    )
    if not sales_rows:
        return {"rows": [], "total": 0.0}

    product_codes = _unique([row.get("producto_codigo_fuente") for row in sales_rows])
    components = RecetasService.get_componentes_bulk(server_id, product_codes)
    factor_by_product: Dict[str, float] = defaultdict(float)
    for row in components or []:
        prod = _text(row.get("producto_codigo_fuente"))
        comp = _text(row.get("componente_codigo_fuente"))
        if comp in componentes_seleccionados and prod:
            factor_by_product[prod] += _float(row.get("cantidad"))

    rows = []
    total = 0.0
    for sale in sales_rows:
        prod = _text(sale.get("producto_codigo_fuente"))
        factor = factor_by_product.get(prod, 0.0)
        consumo = _float(sale.get("cantidad")) * factor
        if not consumo:
            continue
        total += consumo
        rows.append({
            "fecha": sale.get("fecha_operacion"),
            "producto_venta": prod,
            "cantidad_venta": _float(sale.get("cantidad")),
            "factor_consumo": factor,
            "cantidad_consumo": consumo,
        })
    return {"rows": rows, "total": total}


def get_soft_movement_detail(
    cursor,
    *,
    server_id: str,
    unidad_codigo: str,
    sucursal_origen_id: str,
    componente_codigo: str,
    fecha_ini,
    fecha_fin,
    warehouses: Sequence[str] = (),
) -> Dict[str, Any]:
    """Desglosa MOVIMIENTOS del mismo ledger y ventana exacta del reporte SR.

    Los códigos de producto se verifican mediante el puente canónico de
    origen, sin duplicar registros si hay más de un mapeo activo.
    """
    codigos = _unique(_text(componente_codigo).split(","))
    if not codigos:
        return {"rows": [], "totales": {"entradas": 0.0, "salidas": 0.0, "neto": 0.0}}

    empresa = resolver_empresa_id(unidad_codigo)
    sucursal = resolver_sucursal_id(server_id, sucursal_origen_id or None)
    if not empresa.resuelto or not sucursal.resuelto:
        raise ValueError("No se pudo resolver Empresa/Sucursal canónica para detalle SoftRestaurant")

    params: List[Any] = [
        int(empresa.canonical_id),
        int(sucursal.canonical_id),
        fecha_ini,
        fecha_fin,
        server_id,
        *codigos,
    ]
    warehouses = _unique(warehouses)
    warehouse_filter = ""
    if warehouses:
        ph = ",".join(["%s"] * len(warehouses))
        warehouse_filter = (
            f" AND (CONVERT(varchar(50), a.AlmacenID) IN ({ph}) "
            f"OR a.CodigoAlmacen IN ({ph}) OR a.NombreAlmacen IN ({ph}))"
        )
        params.extend(warehouses)
        params.extend(warehouses)
        params.extend(warehouses)

    cursor.execute(
        f"""
        SELECT m.FechaMovimiento AS fecha,
               tm.Codigo AS concepto,
               tm.Descripcion AS descripcion,
               tm.Naturaleza AS naturaleza,
               ISNULL(d.Cantidad,0) AS cantidad,
               a.NombreAlmacen AS almacen,
               m.FolioReferencia AS referencia,
               m.ReferenciaTipo AS referencia_tipo
        FROM dbo.Inventario_MovimientosDetalle d
        INNER JOIN dbo.Inventario_Movimientos m
            ON m.MovimientoID=d.MovimientoID
        INNER JOIN dbo.Inventario_TipoMovimiento tm
            ON tm.TipoMovimientoID=m.TipoMovimientoID
        LEFT JOIN dbo.Inventario_Almacenes a
            ON a.AlmacenID=m.AlmacenID
        WHERE m.EmpresaID=%s
          AND m.SucursalID=%s
          AND m.FechaMovimiento >= %s
          AND m.FechaMovimiento <= %s
          AND ISNULL(m.Activo,1)=1
          AND EXISTS (
              SELECT 1 FROM dbo.Producto_MapeoOrigen pmo
              WHERE pmo.ProductoID=d.ProductoID
                AND LOWER(CONVERT(varchar(36),pmo.ServerID))=LOWER(%s)
                AND UPPER(pmo.SystemType) IN ('SOFTRESTAURANT','SOFTRESTAURANT_PRO')
                AND pmo.Activo=1
                AND pmo.CodigoFuente IN ({",".join(["%s"] * len(codigos))})
          )
          {warehouse_filter}
        ORDER BY m.FechaMovimiento DESC, m.MovimientoID DESC
        """,
        tuple(params),
    )

    movimientos = []
    entradas = 0.0
    salidas = 0.0
    for row in cursor.fetchall() or []:
        cantidad = _float(row.get("cantidad"))
        naturaleza = _text(row.get("naturaleza")).upper()
        es_entrada = naturaleza in ("E", "EN", "ENTRADA")
        signed = cantidad if es_entrada else -cantidad
        if es_entrada:
            entradas += cantidad
        else:
            salidas += cantidad

        referencia_tipo = _text(row.get("referencia_tipo"))
        concepto = _text(row.get("concepto"))
        if referencia_tipo.upper().startswith("MOVIMIENTO_POS|"):
            concepto = referencia_tipo.split("|", 1)[1].strip() or concepto

        fecha = row.get("fecha")
        movimientos.append({
            "fecha": fecha.isoformat() if hasattr(fecha, "isoformat") else _text(fecha),
            "concepto": concepto,
            "descripcion": _text(row.get("descripcion")),
            "cantidad": signed,
            "almacen": _text(row.get("almacen")),
            "referencia": _text(row.get("referencia")),
            "tipo": "E" if es_entrada else "S",
        })

    return {
        "rows": movimientos,
        "totales": {
            "entradas": round(entradas, 4),
            "salidas": round(salidas, 4),
            "neto": round(entradas - salidas, 4),
        },
    }
