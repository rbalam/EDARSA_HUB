"""
Analisis canonico de inventario para ManagementPro (NO-LIVE).

Fuentes exclusivas EDARSAHUB:
- Compras_Inventarios_Fisicos_Sync / Detalle_Sync
- Inventario_Movimientos / Inventario_MovimientosDetalle / Inventario_TipoMovimiento
- Producto_MapeoOrigen
- Comercial_Inteligencia_VentasDetalleProducto
- Sync_Productos / Sync_Productos_Compuestos / Sync_Productos_Recetas

Nunca conecta al POS.
"""
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from core.inventarios.resolver_canonico import resolver_empresa_id, resolver_sucursal_id
from core.sql_first.connection_factory import get_edarsahub_pymssql_connection


@dataclass
class MproInventoryAnalysisSourceError(Exception):
    code: str
    message: str
    status_code: int = 503

    def __str__(self) -> str:
        return self.message


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _unique(values: Iterable[Any]) -> List[str]:
    return list(dict.fromkeys(_text(v) for v in values if _text(v)))


def _filter_candidates(selected_almacenes: Sequence[Any]) -> List[str]:
    values: List[str] = []
    for item in selected_almacenes or []:
        if isinstance(item, dict):
            for key in ("almacen_id", "id", "nombre", "almacen", "label", "value"):
                value = _text(item.get(key))
                if value and value not in values:
                    values.append(value)
        else:
            value = _text(item)
            if value and value not in values:
                values.append(value)
    return values


def _inventory_map(rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for row in rows or []:
        code = _text(row.get("codigo_producto"))
        if not code:
            continue
        item = result.setdefault(
            code,
            {
                "cantidad": 0.0,
                "costo": 0.0,
                "nombre": _text(row.get("nombre_producto")),
                "unidad": _text(row.get("unidad")) or "PZA",
            },
        )
        item["cantidad"] += _float(row.get("existencia_fisica"))
        cost = _float(row.get("costo_unitario"))
        if cost:
            item["costo"] = cost
        if not item["nombre"]:
            item["nombre"] = _text(row.get("nombre_producto"))
    return result


def _movement_display_and_theoretical(
    initial_qty: float,
    ledger_net: float,
    sales_qty: float,
) -> Dict[str, float]:
    """
    El ledger MPRO ya contiene la salida por venta.
    Para mostrar Ventas separadas sin duplicarla:
      movimientos_mostrados = ledger_net + ventas
      teorico = inicial + movimientos_mostrados - ventas
              = inicial + ledger_net
    """
    movements_display = ledger_net + sales_qty
    theoretical = initial_qty + movements_display - sales_qty
    return {
        "movimientos": movements_display,
        "teorico": theoretical,
    }


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


def _fetch_inventory_headers(
    cursor,
    *,
    server_id: str,
    unidad_pk: str,
    folios: Sequence[str],
    warehouses: Sequence[str],
) -> List[Dict[str, Any]]:
    if not folios:
        return []
    folio_ph = ",".join(["%s"] * len(folios))
    params: List[Any] = [server_id, unidad_pk, *folios]
    filters = [
        "LOWER(server_id)=LOWER(%s)",
        "unidad_negocio_id=%s",
        f"folio IN ({folio_ph})",
        "sync_status IN ('ACTIVE','REPLACED')",
    ]
    if warehouses:
        alm_ph = ",".join(["%s"] * len(warehouses))
        filters.append(f"(almacen_id IN ({alm_ph}) OR almacen IN ({alm_ph}))")
        params.extend(warehouses)
        params.extend(warehouses)

    cursor.execute(
        f"""
        SELECT folio, fecha, almacen, almacen_id, sucursal, sucursal_id, sync_status
        FROM (
            SELECT folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
                   sync_status, sync_timestamp,
                   ROW_NUMBER() OVER (
                       PARTITION BY server_id, unidad_negocio_id, sucursal_id, almacen_id, folio
                       ORDER BY CASE WHEN sync_status='ACTIVE' THEN 0 ELSE 1 END,
                                sync_timestamp DESC
                   ) rn
            FROM dbo.Compras_Inventarios_Fisicos_Sync
            WHERE {' AND '.join(filters)}
        ) x
        WHERE rn=1
        ORDER BY fecha, folio
        """,
        tuple(params),
    )
    return list(cursor.fetchall() or [])


def _fetch_inventory_details(
    cursor,
    *,
    server_id: str,
    unidad_pk: str,
    folios: Sequence[str],
    warehouses: Sequence[str],
) -> List[Dict[str, Any]]:
    if not folios:
        return []
    columns = _fetch_table_columns(cursor, "Compras_Inventarios_Fisicos_Detalle_Sync")
    if not columns:
        raise MproInventoryAnalysisSourceError(
            "INVENTORY_DETAIL_SOURCE_MISSING",
            "No existe el detalle canónico de inventarios físicos en EDARSAHUB.",
        )
    folio_ph = ",".join(["%s"] * len(folios))
    params: List[Any] = [server_id, unidad_pk, *folios]
    filters = [
        "LOWER(server_id)=LOWER(%s)",
        "unidad_negocio_id=%s",
        f"folio IN ({folio_ph})",
        "sync_status IN ('ACTIVE','REPLACED')",
    ]
    if warehouses:
        alm_ph = ",".join(["%s"] * len(warehouses))
        filters.append(f"(almacen_id IN ({alm_ph}) OR almacen IN ({alm_ph}))")
        params.extend(warehouses)
        params.extend(warehouses)

    rendimiento = "ISNULL(rendimiento,1)" if "rendimiento" in columns else "1"
    cursor.execute(
        f"""
        SELECT folio, codigo_producto, nombre_producto, unidad,
               existencia_fisica, costo_unitario, almacen, almacen_id,
               {rendimiento} AS rendimiento
        FROM (
            SELECT folio, codigo_producto, nombre_producto, unidad,
                   existencia_fisica, costo_unitario, almacen, almacen_id,
                   {rendimiento} AS rendimiento,
                   sync_status, sync_timestamp,
                   ROW_NUMBER() OVER (
                       PARTITION BY server_id, unidad_negocio_id, almacen_id, folio, codigo_producto
                       ORDER BY CASE WHEN sync_status='ACTIVE' THEN 0 ELSE 1 END,
                                sync_timestamp DESC
                   ) rn
            FROM dbo.Compras_Inventarios_Fisicos_Detalle_Sync
            WHERE {' AND '.join(filters)}
        ) x
        WHERE rn=1
        """,
        tuple(params),
    )
    return list(cursor.fetchall() or [])


def _resolve_product_ids(
    cursor,
    server_id: str,
    codes: Sequence[str],
) -> Dict[str, Any]:
    if not codes:
        return {}
    result: Dict[str, Any] = {}
    for offset in range(0, len(codes), 500):
        chunk = list(codes[offset:offset + 500])
        ph = ",".join(["%s"] * len(chunk))
        cursor.execute(
            f"""
            SELECT CodigoFuente, ProductoID
            FROM dbo.Producto_MapeoOrigen
            WHERE LOWER(CONVERT(varchar(36),ServerID))=LOWER(%s)
              AND UPPER(SystemType)='MPRO'
              AND CodigoFuente IN ({ph})
              AND Activo=1
            """,
            tuple([server_id, *chunk]),
        )
        for row in cursor.fetchall() or []:
            code = _text(row.get("CodigoFuente"))
            pid = row.get("ProductoID")
            if code and pid is not None:
                if code in result and str(result[code]) != str(pid):
                    raise MproInventoryAnalysisSourceError(
                        "MPRO_PRODUCT_MAPPING_AMBIGUOUS",
                        f"El producto {code} tiene más de un mapeo canónico activo.",
                    )
                result[code] = pid
    return result


def _fetch_ledger_net(
    cursor,
    *,
    empresa_id: int,
    sucursal_id: int,
    product_ids_by_code: Dict[str, Any],
    fecha_ini: str,
    fecha_fin: str,
    warehouses: Sequence[str],
) -> Dict[str, float]:
    if not product_ids_by_code:
        return {}

    reverse: Dict[str, str] = {}
    for code, pid in product_ids_by_code.items():
        key = str(pid).lower()
        if key in reverse and reverse[key] != code:
            raise MproInventoryAnalysisSourceError(
                "MPRO_PRODUCT_MAPPING_COLLISION",
                "Dos códigos de inventario resuelven al mismo ProductoID canónico; no se mezclan movimientos.",
            )
        reverse[key] = code

    pids = list(product_ids_by_code.values())
    totals: Dict[str, float] = defaultdict(float)
    for offset in range(0, len(pids), 400):
        chunk = pids[offset:offset + 400]
        ph = ",".join(["%s"] * len(chunk))
        params: List[Any] = [empresa_id, sucursal_id, fecha_ini, fecha_fin, *chunk]
        warehouse_filter = ""
        if warehouses:
            wh_ph = ",".join(["%s"] * len(warehouses))
            warehouse_filter = (
                f" AND (a.CodigoAlmacen IN ({wh_ph}) OR a.NombreAlmacen IN ({wh_ph}))"
            )
            params.extend(warehouses)
            params.extend(warehouses)

        cursor.execute(
            f"""
            SELECT d.ProductoID,
                   SUM(
                       CASE
                         WHEN UPPER(LTRIM(RTRIM(ISNULL(tm.Naturaleza,'')))) IN ('E','EN','ENTRADA')
                           THEN ISNULL(d.Cantidad,0)
                         ELSE -ISNULL(d.Cantidad,0)
                       END
                   ) AS neto
            FROM dbo.Inventario_MovimientosDetalle d
            INNER JOIN dbo.Inventario_Movimientos m
                ON m.MovimientoID=d.MovimientoID
            INNER JOIN dbo.Inventario_TipoMovimiento tm
                ON tm.TipoMovimientoID=m.TipoMovimientoID
            LEFT JOIN dbo.Inventario_Almacenes a
                ON a.AlmacenID=m.AlmacenID
            WHERE m.EmpresaID=%s
              AND m.SucursalID=%s
              AND m.FechaMovimiento >= CAST(%s AS date)
              AND m.FechaMovimiento < DATEADD(day,1,CAST(%s AS date))
              AND ISNULL(m.Activo,1)=1
              AND d.ProductoID IN ({ph})
              {warehouse_filter}
            GROUP BY d.ProductoID
            """,
            tuple(params),
        )
        for row in cursor.fetchall() or []:
            code = reverse.get(str(row.get("ProductoID")).lower())
            if code:
                totals[code] += _float(row.get("neto"))
    return dict(totals)


def _fetch_sales_rows(
    cursor,
    *,
    unidad_codigo: str,
    server_id: str,
    fecha_ini: str,
    fecha_fin: str,
) -> List[Dict[str, Any]]:
    columns = _fetch_table_columns(cursor, "Comercial_Inteligencia_VentasDetalleProducto")
    required = {"unidad_negocio_id", "fecha_operacion", "producto_codigo_fuente", "cantidad"}
    if not required.issubset(columns):
        raise MproInventoryAnalysisSourceError(
            "MPRO_SALES_DETAIL_SOURCE_MISSING",
            "La fuente canónica de detalle de ventas no tiene el contrato requerido.",
        )

    extra = []
    if "activo" in columns:
        extra.append("ISNULL(activo,1)=1")
    if "cancelado_origen" in columns:
        extra.append("ISNULL(cancelado_origen,0)=0")
    if "es_kpi_valido" in columns:
        extra.append("ISNULL(es_kpi_valido,1)=1")
    if "server_id" in columns:
        extra.append("LOWER(ISNULL(server_id,''))=LOWER(%s)")
        extra_params: List[Any] = [server_id]
    else:
        extra_params = []

    where_extra = (" AND " + " AND ".join(extra)) if extra else ""
    cursor.execute(
        f"""
        SELECT producto_codigo_fuente,
               SUM(ISNULL(cantidad,0)) AS cantidad
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
        WHERE unidad_negocio_id=%s
          AND fecha_operacion >= CAST(%s AS date)
          AND fecha_operacion <= CAST(%s AS date)
          AND NULLIF(LTRIM(RTRIM(producto_codigo_fuente)),'') IS NOT NULL
          {where_extra}
        GROUP BY producto_codigo_fuente
        """,
        tuple([unidad_codigo, fecha_ini, fecha_fin, *extra_params]),
    )
    return list(cursor.fetchall() or [])


def _fetch_mpro_sales_components(
    cursor,
    server_id: str,
    product_codes: Sequence[str],
) -> List[Dict[str, Any]]:
    """
    Fuente canónica de componentes para ventas MPRO.

    Prioridad por producto:
      1) Sync_Productos_Compuestos/FuenteDetalle=PRODUCTO_KIT
         (equivale al histórico Producto_Kit.Pk_Cantidad).
      2) Sync_Productos_Recetas para fórmulas de producción cuando el
         producto no tiene kit activo.

    No mezcla ambas fuentes para el mismo producto.
    """
    codes = _unique(product_codes)
    if not codes:
        return []

    rows: List[Dict[str, Any]] = []
    for offset in range(0, len(codes), 400):
        chunk = codes[offset:offset + 400]
        ph = ",".join(["%s"] * len(chunk))
        params = tuple([server_id, *chunk, server_id, *chunk])
        cursor.execute(
            f"""
            WITH kits AS (
                SELECT
                    ProductoCodigoFuente AS producto_codigo_fuente,
                    ComponenteCodigoFuente AS componente_codigo_fuente,
                    Cantidad AS cantidad,
                    UnidadMedida AS unidad_medida,
                    'PRODUCTO_KIT' AS fuente
                FROM dbo.Sync_Productos_Compuestos
                WHERE LOWER(CONVERT(varchar(36),ServerID))=LOWER(%s)
                  AND ProductoCodigoFuente IN ({ph})
                  AND ISNULL(Activo,1)=1
                  AND UPPER(ISNULL(FuenteDetalle,''))='PRODUCTO_KIT'
            ),
            recetas AS (
                SELECT
                    r.ProductoCodigoFuente AS producto_codigo_fuente,
                    r.ComponenteCodigoFuente AS componente_codigo_fuente,
                    r.Cantidad AS cantidad,
                    r.UnidadMedida AS unidad_medida,
                    'RECETA' AS fuente
                FROM dbo.Sync_Productos_Recetas r
                WHERE LOWER(CONVERT(varchar(36),r.ServerID))=LOWER(%s)
                  AND r.ProductoCodigoFuente IN ({ph})
                  AND ISNULL(r.Activo,1)=1
                  AND NOT EXISTS (
                      SELECT 1
                      FROM dbo.Sync_Productos_Compuestos k
                      WHERE k.ServerID=r.ServerID
                        AND k.ProductoCodigoFuente=r.ProductoCodigoFuente
                        AND ISNULL(k.Activo,1)=1
                        AND UPPER(ISNULL(k.FuenteDetalle,''))='PRODUCTO_KIT'
                  )
            )
            SELECT * FROM kits
            UNION ALL
            SELECT * FROM recetas
            """,
            params,
        )
        rows.extend(cursor.fetchall() or [])
    return rows


def _sales_consumption(
    cursor,
    server_id: str,
    sales_rows: Sequence[Dict[str, Any]],
) -> Dict[str, float]:
    sold = {
        _text(row.get("producto_codigo_fuente")): _float(row.get("cantidad"))
        for row in sales_rows or []
        if _text(row.get("producto_codigo_fuente"))
    }
    if not sold:
        return {}

    components = _fetch_mpro_sales_components(cursor, server_id, list(sold))
    if not components:
        raise MproInventoryAnalysisSourceError(
            "MPRO_COMPONENTS_SOURCE_INCOMPLETE",
            (
                "No se encontraron componentes canónicos MPRO para las ventas "
                "del periodo (Producto_Kit/recetas)."
            ),
        )

    consumption: Dict[str, float] = defaultdict(float)
    for row in components:
        product_code = _text(row.get("producto_codigo_fuente"))
        component_code = _text(row.get("componente_codigo_fuente"))
        if not product_code or not component_code or product_code not in sold:
            continue
        consumption[component_code] += (
            sold[product_code] * _float(row.get("cantidad"))
        )

    return dict(consumption)


def _fetch_product_metadata(
    cursor,
    server_id: str,
    codes: Sequence[str],
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for offset in range(0, len(codes), 500):
        chunk = list(codes[offset:offset + 500])
        if not chunk:
            continue
        ph = ",".join(["%s"] * len(chunk))
        cursor.execute(
            f"""
            SELECT CodigoFuente, Nombre,
                   CategoriaCodigoFuente, CategoriaNombre,
                   FamiliaCodigoFuente, FamiliaNombre,
                   SubFamiliaCodigoFuente, SubFamiliaNombre
            FROM dbo.Sync_Productos
            WHERE LOWER(CONVERT(varchar(36),ServerID))=LOWER(%s)
              AND CodigoFuente IN ({ph})
              AND ISNULL(Activo,1)=1
            """,
            tuple([server_id, *chunk]),
        )
        for row in cursor.fetchall() or []:
            result[_text(row.get("CodigoFuente"))] = dict(row)
    return result


def generate_mpro_inventory_analysis_canonical(
    *,
    server_id: str,
    unidad_pk: str,
    unidad_codigo: str,
    sucursal_origen_id: str,
    folios_iniciales: Sequence[str],
    folios_finales: Sequence[str],
    fecha_ini: str,
    fecha_fin: str,
    almacenes: Sequence[Any],
    categorias: Sequence[Any] = (),
    familias: Sequence[Any] = (),
    subfamilias: Sequence[Any] = (),
) -> Dict[str, Any]:
    server_id = _text(server_id)
    unidad_pk = _text(unidad_pk)
    unidad_codigo = _text(unidad_codigo)
    sucursal_origen_id = _text(sucursal_origen_id)
    folios_ini = _unique(folios_iniciales)
    folios_fin = _unique(folios_finales)
    warehouses = _filter_candidates(almacenes)

    if not all((server_id, unidad_pk, unidad_codigo, sucursal_origen_id)):
        raise MproInventoryAnalysisSourceError(
            "MPRO_CANONICAL_SCOPE_INCOMPLETE",
            "No se pudo resolver la unidad/sucursal canónica para ManagementPro.",
            400,
        )
    if not folios_ini or not folios_fin:
        raise MproInventoryAnalysisSourceError(
            "MPRO_INVENTORY_FOLIOS_REQUIRED",
            "Debe seleccionar inventario inicial y final.",
            400,
        )
    if not fecha_ini or not fecha_fin:
        raise MproInventoryAnalysisSourceError(
            "MPRO_ANALYSIS_DATES_REQUIRED",
            "El rango de movimientos es obligatorio.",
            400,
        )

    empresa = resolver_empresa_id(unidad_codigo)
    sucursal = resolver_sucursal_id(server_id, sucursal_origen_id)
    if not empresa.resuelto or not sucursal.resuelto:
        raise MproInventoryAnalysisSourceError(
            "MPRO_CANONICAL_IDENTITY_UNRESOLVED",
            "No se pudo resolver Empresa/Sucursal canónica para el análisis MPRO.",
        )

    conn = get_edarsahub_pymssql_connection(
        profile="default",
        timeout=60,
        login_timeout=10,
        autocommit=True,
    )
    try:
        cursor = conn.cursor(as_dict=True)
        all_folios = _unique([*folios_ini, *folios_fin])
        headers = _fetch_inventory_headers(
            cursor,
            server_id=server_id,
            unidad_pk=unidad_pk,
            folios=all_folios,
            warehouses=warehouses,
        )
        found = {_text(row.get("folio")) for row in headers}
        missing = [folio for folio in all_folios if folio not in found]
        if missing:
            raise MproInventoryAnalysisSourceError(
                "MPRO_INVENTORY_HEADERS_INCOMPLETE",
                "Faltan inventarios físicos canónicos: " + ", ".join(missing),
            )

        # Regla contractual ManagementPro:
        # solamente el almacén fuente 0001 (Almacén general) descarga ventas.
        # Los demás almacenes muestran únicamente entradas/salidas.
        selected_header_warehouse_ids = {
            _text(row.get("almacen_id")).zfill(4)
            for row in headers
            if _text(row.get("almacen_id"))
        }
        sales_enabled = (
            not warehouses
            or "0001" in selected_header_warehouse_ids
        )

        details = _fetch_inventory_details(
            cursor,
            server_id=server_id,
            unidad_pk=unidad_pk,
            folios=all_folios,
            warehouses=warehouses,
        )
        ini = _inventory_map([r for r in details if _text(r.get("folio")) in folios_ini])
        fin = _inventory_map([r for r in details if _text(r.get("folio")) in folios_fin])
        all_codes = sorted(set(ini) | set(fin))
        if not all_codes:
            raise MproInventoryAnalysisSourceError(
                "MPRO_INVENTORY_DETAIL_EMPTY",
                "Los inventarios seleccionados no tienen detalle canónico.",
            )

        product_ids = _resolve_product_ids(cursor, server_id, all_codes)
        ledger_net = _fetch_ledger_net(
            cursor,
            empresa_id=int(empresa.canonical_id),
            sucursal_id=int(sucursal.canonical_id),
            product_ids_by_code=product_ids,
            fecha_ini=fecha_ini,
            fecha_fin=fecha_fin,
            warehouses=warehouses,
        )

        if sales_enabled:
            sales_rows = _fetch_sales_rows(
                cursor,
                unidad_codigo=unidad_codigo,
                server_id=server_id,
                fecha_ini=fecha_ini,
                fecha_fin=fecha_fin,
            )
            if not sales_rows:
                raise MproInventoryAnalysisSourceError(
                    "MPRO_SALES_DETAIL_INCOMPLETE",
                    "No hay detalle canónico de ventas para el periodo seleccionado.",
                )
            sales_consumption = _sales_consumption(cursor, server_id, sales_rows)
        else:
            sales_rows = []
            sales_consumption = {}

        metadata = _fetch_product_metadata(cursor, server_id, all_codes)

        selected_categories = set(_unique(
            item.get("id") if isinstance(item, dict) else item for item in categorias
        ))
        selected_families = set(_unique(
            item.get("id") if isinstance(item, dict) else item for item in familias
        ))
        selected_subfamilies = set(_unique(
            item.get("id") if isinstance(item, dict) else item for item in subfamilias
        ))

        results: List[Dict[str, Any]] = []
        for code in all_codes:
            meta = metadata.get(code, {})
            if selected_categories and _text(meta.get("CategoriaCodigoFuente")) not in selected_categories:
                continue
            if selected_families and _text(meta.get("FamiliaCodigoFuente")) not in selected_families:
                continue
            if selected_subfamilies and _text(meta.get("SubFamiliaCodigoFuente")) not in selected_subfamilies:
                continue

            initial = _float(ini.get(code, {}).get("cantidad"))
            final = _float(fin.get(code, {}).get("cantidad"))
            sales = _float(sales_consumption.get(code))
            ledger = _float(ledger_net.get(code))
            calc = _movement_display_and_theoretical(initial, ledger, sales)
            movements = calc["movimientos"]
            theoretical = calc["teorico"]
            difference = final - theoretical

            initial_cost = _float(ini.get(code, {}).get("costo"))
            final_cost = _float(fin.get(code, {}).get("costo"))
            cost = final_cost or initial_cost
            name = (
                _text(meta.get("Nombre"))
                or _text(fin.get(code, {}).get("nombre"))
                or _text(ini.get(code, {}).get("nombre"))
                or f"Producto {code}"
            )
            unit = (
                _text(fin.get(code, {}).get("unidad"))
                or _text(ini.get(code, {}).get("unidad"))
                or "PZA"
            )
            difference_cost = difference * cost
            difference_pct = (difference / theoretical * 100.0) if theoretical else 0.0
            real_value = (initial + movements - final) * cost

            results.append({
                "ID_Inv_Ini": ", ".join(folios_ini),
                "Comentario_Ini": ", ".join(warehouses),
                "ID_Inv_Fin": ", ".join(folios_fin),
                "Comentario_Fin": ", ".join(warehouses),
                "Categoria": _text(meta.get("CategoriaNombre")) or "SIN CATEGORIA",
                "Familia": _text(meta.get("FamiliaNombre")) or "SIN FAMILIA",
                "SubFamilia": _text(meta.get("SubFamiliaNombre")) or "SIN SUBFAMILIA",
                "Codigo": code,
                "Producto": name,
                "Unidad": unit,
                "Rendimiento": 1,
                "tipo_almacen": 1,
                "Costo_Unitario": round(cost, 4),
                "Inv_Inicial_Cantidad": round(initial, 4),
                "Inv_Inicial_Costo": round(initial * cost, 2),
                "Movimientos": round(movements, 4),
                "Movimientos_Costo": round(movements * cost, 2),
                "Ventas": round(sales, 4),
                "Ventas_Costo": round(sales * cost, 2),
                "Inv_Teorico_Cantidad": round(theoretical, 4),
                "Inv_Teorico_Costo": round(theoretical * cost, 2),
                "Inv_Final_Cantidad": round(final, 4),
                "Inv_Final_Costo": round(final * cost, 2),
                "Diferencia_Cantidad": round(difference, 4),
                "Diferencia_Costo": round(difference_cost, 2),
                "Diferencia_Porcentaje": round(difference_pct, 2),
                "Valor_Real": round(real_value, 2),
                "Teorico": 0.0,
                "source": "EDARSAHUB_SQL_CANONICAL",
            })

        return {
            "data": results,
            "count": len(results),
            "source": "EDARSAHUB_SQL_CANONICAL",
            "meta": {
                "system_type": "MPRO",
                "unidad": unidad_codigo,
                "server_id": server_id,
                "sucursal_origen_id": sucursal_origen_id,
                "ventas_productos": len(sales_rows),
                "movimientos_productos": len(ledger_net),
                "ventas_aplicadas": sales_enabled,
                "almacenes_seleccionados": sorted(selected_header_warehouse_ids),
            },
        }
    finally:
        conn.close()
