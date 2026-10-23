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

    cursor.execute(
        f"""
        SELECT producto_codigo_fuente,
               SUM(ISNULL(cantidad,0)) AS cantidad
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        WHERE unidad_negocio_id=%s
          AND fecha_operacion >= CAST(%s AS date)
          AND fecha_operacion <= CAST(%s AS date)
          AND NULLIF(LTRIM(RTRIM(producto_codigo_fuente)),'') IS NOT NULL
          {" AND " + " AND ".join(extra) if extra else ""}
        GROUP BY producto_codigo_fuente
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
    sales_rows = _fetch_soft_sales_rows(
        cursor,
        unidad_codigo=unidad_codigo,
        server_id=server_id,
        fecha_ini=sales_start,
        fecha_fin=sales_end,
    )
    ventas = _explode_sales_to_consumption(server_id, sales_rows)
    return movimientos, ventas
