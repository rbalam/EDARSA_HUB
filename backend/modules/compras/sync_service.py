
# REGLA CRÍTICA SYNC ORIGEN → EDARSAHUB:
# ServerID, OrigenSistema, id_empresa e id_unidad_negocio NO existen ni deben leerse desde SoftRestaurant/MPRO.
# Esos campos se agregan desde el contexto EDARSAHUB del servidor/unidad antes de hacer MERGE al destino.


# NOTA SQL-FIRST:
# Los nombres de tablas origen SoftRestaurant/MPRO deben vivir en adapters.
# Destinos EDARSAHUB conservan nombres canónicos:
# Inventario_*, Compras_*.
# invfisico/invfisicomovtos NO deben mapearse a Inventario_Movimientos;
# se mantienen en Compras_Inventarios_Fisicos_Sync hasta migración canónica futura.

"""
COMPRAS SYNC SERVICE - Sincronización de Inventarios y Requisiciones a EDARSAHUB
================================================================================
POLÍTICA: Todo se lee de EDARSAHUB SQL. Los servidores físicos solo se consultan
durante la sincronización (job background).


from modules.compras.adapters import softrestaurant_pro_adapter
from modules.compras.adapters import mpro_adapter
Tablas EDARSAHUB:
- Compras_Inventarios_Fisicos_Sync: Inventarios físicos sincronizados
- Compras_Requisiciones_Sync: Requisiciones/pedidos sincronizados
- Compras_Sync_Log: Log de sincronizaciones
"""

import os
import pymssql
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.db import get_sql_connection
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)
SQL_SERVER_SAFE_PARAM_LIMIT = 2000

# P2-01: Configuración EDARSAHUB centralizada (sin fallbacks legacy)
EDARSAHUB_CONFIG = {
    'host': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'username': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}


def _sql_identifier(name: str) -> str:
    return f"[{str(name).replace(']', ']]')}]"


def _as_text(value: Any, max_length: Optional[int] = None) -> str:
    text = str(value or "").strip()
    if max_length is not None:
        return text[:max_length]
    return text


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _sql_literal(value: Any) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _folio_in_filter(column_expression: str, folios: Optional[List[Any]]) -> str:
    values = []
    seen = set()
    for folio in folios or []:
        text = _as_text(folio, 50)
        if not text or text in seen:
            continue
        seen.add(text)
        values.append(_sql_literal(text))
    if not values:
        return ""
    return f" AND CAST({column_expression} AS VARCHAR(50)) IN ({', '.join(values)})"


def _inventory_detail_batch_size() -> int:
    try:
        value = int(os.environ.get("SYNC_INVENTARIOS_FISICOS_DETAIL_BATCH_SIZE", "20"))
    except (TypeError, ValueError):
        value = 20
    return max(1, min(value, 100))


def _unique_folio_batches(rows: List[Dict[str, Any]], batch_size: int) -> List[List[str]]:
    folios = []
    seen = set()
    for row in rows:
        folio = _as_text(row.get("folio"), 50)
        if folio and folio not in seen:
            seen.add(folio)
            folios.append(folio)
    return [folios[i:i + batch_size] for i in range(0, len(folios), batch_size)]


def _inventory_header_detail_key(row: Dict[str, Any]) -> tuple[str, str]:
    return (_as_text(row.get("folio"), 50), _as_text(row.get("almacen_id"), 50))


def _inventory_detail_key(row: Dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        _as_text(row.get("server_id"), 100),
        _as_text(row.get("unidad_negocio_id"), 64),
        _as_text(row.get("folio"), 50),
        _as_text(row.get("codigo_producto"), 100),
        _as_text(row.get("almacen_id"), 50),
    )


def _filter_inventory_headers_with_detail(
    rows: List[Dict[str, Any]],
    detail_rows: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], int]:
    detail_counts: Dict[tuple[str, str], int] = {}
    for detail in detail_rows:
        key = _inventory_header_detail_key(detail)
        if key[0] and key[1]:
            detail_counts[key] = detail_counts.get(key, 0) + 1

    filtered_rows = []
    skipped = 0
    for row in rows:
        key = _inventory_header_detail_key(row)
        count = detail_counts.get(key, 0)
        if not count:
            skipped += 1
            continue
        row_copy = dict(row)
        if not _as_float(row_copy.get("total_productos")):
            row_copy["total_productos"] = count
        filtered_rows.append(row_copy)
    return filtered_rows, skipped


def _fetch_table_columns(cursor, table_name: str) -> Dict[str, str]:
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
          AND TABLE_NAME = %s
    """, (table_name,))
    return {
        str(row[0]).strip().lower(): str(row[0]).strip()
        for row in cursor.fetchall()
        if row and row[0]
    }


INVENTORY_SYNC_MODE_ROLLING_6M = "ROLLING_6M"
INVENTORY_SYNC_MODE_FULL = "FULL"


def _inventory_history_filter(
    column_expression: str,
    sync_mode: str,
) -> str:
    """
    Ventana temporal canonica de inventarios fisicos.

    FULL:
        carga inicial, backfill o reconstruccion de todo el historico.

    ROLLING_6M:
        mantenimiento operativo normal de los ultimos 6 meses.
    """
    mode = str(sync_mode or "").strip().upper()

    if mode == INVENTORY_SYNC_MODE_FULL:
        return f"{column_expression} IS NOT NULL"

    if mode == INVENTORY_SYNC_MODE_ROLLING_6M:
        return (
            f"{column_expression} IS NOT NULL "
            f"AND {column_expression} >= DATEADD(MONTH, -6, GETDATE())"
        )

    raise ValueError(
        f"Modo de sincronizacion de inventarios no soportado: {sync_mode!r}"
    )


def _inventarios_fisicos_detalle_query(
    system_type: str,
    folios: Optional[List[Any]] = None,
    sucursal_origen_id: Optional[str] = None,
    sync_mode: str = INVENTORY_SYNC_MODE_ROLLING_6M,
) -> Optional[str]:
    from core.system_type_utils import is_mpro_system, is_softrestaurant_system

    inventory_filter_mpro = _inventory_history_filter(
        "F.Fi_Fecha",
        sync_mode,
    )
    inventory_filter_softrestaurant = _inventory_history_filter(
        "FISICO.fecha",
        sync_mode,
    )

    if is_mpro_system(system_type):
        folio_filter = _folio_in_filter("F.Fi_Folio", folios)

        if not sucursal_origen_id:
            raise ValueError(
                "MPRO requiere sucursal_origen_id canónica "
                "para consultar detalle de inventarios"
            )

        safe_sucursal_origen = (
            str(sucursal_origen_id)
            .strip()
            .replace("'", "''")
        )

        sucursal_filter = (
            f"AND F.Sc_Cve_Sucursal = "
            f"'{safe_sucursal_origen}'"
        )

        return f"""
            SELECT
                CAST(F.Fi_Folio AS VARCHAR(50)) as folio,
                RTRIM(LTRIM(CAST(F.Pr_Cve_Producto AS VARCHAR(50)))) as codigo_producto,
                COALESCE(P.Pr_Descripcion, CAST(F.Pr_Cve_Producto AS VARCHAR(100))) as nombre_producto,
                COALESCE(P.Pr_Unidad_Control_1, '') as unidad,
                ISNULL(F.Fi_Cantidad_Control_1, 0) as existencia_fisica,
                1 as rendimiento,
                ISNULL(F.Fi_Costo, ISNULL(P.Pr_ultimo_costo, 0)) as costo_unitario,
                COALESCE(A.Al_Descripcion, CAST(F.Al_Cve_Almacen AS VARCHAR(50))) as almacen,
                CAST(F.Al_Cve_Almacen AS VARCHAR(50)) as almacen_id
            FROM Fisico F
            INNER JOIN Almacen A
                ON A.Al_Cve_Almacen = F.Al_Cve_Almacen
               AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
            LEFT JOIN Producto P ON P.Pr_Cve_Producto = F.Pr_Cve_Producto
            WHERE {inventory_filter_mpro}
              AND ISNULL(F.Es_Cve_Estado, '') <> 'CA'
              {sucursal_filter}
              {folio_filter}
            ORDER BY F.Fi_Fecha DESC, F.Fi_Folio, F.Pr_Cve_Producto
        """

    if is_softrestaurant_system(system_type):
        folio_filter = _folio_in_filter("FISICO.folio", folios)
        return f"""
            SELECT
                CAST(FMOV.folio AS VARCHAR(50)) as folio,
                CASE
                    WHEN NULLIF(RTRIM(LTRIM(CAST(ISNULL(FMOV.idinsumo, '') AS VARCHAR(50)))), '') IS NULL
                    THEN RTRIM(LTRIM(CAST(FMOV.idpresentacion AS VARCHAR(50))))
                    ELSE RTRIM(LTRIM(CAST(FMOV.idinsumo AS VARCHAR(50))))
                END as codigo_producto,
                CASE
                    WHEN NULLIF(RTRIM(LTRIM(CAST(ISNULL(FMOV.idinsumo, '') AS VARCHAR(50)))), '') IS NULL
                    THEN COALESCE(IP.descripcion, CAST(FMOV.idpresentacion AS VARCHAR(100)))
                    ELSE COALESCE(I_INS.descripcion, CAST(FMOV.idinsumo AS VARCHAR(100)))
                END as nombre_producto,
                CASE
                    WHEN NULLIF(RTRIM(LTRIM(CAST(ISNULL(FMOV.idinsumo, '') AS VARCHAR(50)))), '') IS NULL
                    THEN COALESCE(I_PRES.unidad, '')
                    ELSE COALESCE(I_INS.unidad, '')
                END as unidad,
                ISNULL(FMOV.fisicoalmacen1, 0) as existencia_fisica,
                CASE
                    WHEN NULLIF(RTRIM(LTRIM(CAST(ISNULL(FMOV.idinsumo, '') AS VARCHAR(50)))), '') IS NULL
                    THEN ISNULL(IP.rendimiento, 1)
                    ELSE 1
                END as rendimiento,
                ISNULL(FMOV.costo, 0) as costo_unitario,
                COALESCE(AL.nombre, CAST(FISICO.idalmacen1 AS VARCHAR(50))) as almacen,
                CAST(FISICO.idalmacen1 AS VARCHAR(50)) as almacen_id
            FROM invfisicomovtos FMOV
            INNER JOIN invfisico FISICO ON FISICO.folio = FMOV.folio
            LEFT JOIN almacen AL ON AL.idalmacen = FISICO.idalmacen1
            LEFT JOIN insumospresentaciones IP ON IP.idinsumospresentaciones = FMOV.idpresentacion
            LEFT JOIN insumos I_PRES ON I_PRES.idinsumo = IP.idinsumo
            LEFT JOIN insumos I_INS ON I_INS.idinsumo = FMOV.idinsumo
            WHERE {inventory_filter_softrestaurant}
              AND ISNULL(FISICO.cancelado, 0) = 0
              {folio_filter}
            ORDER BY FISICO.fecha DESC, FMOV.folio, codigo_producto
        """

    return None


def _detail_values(row: Dict[str, Any], server_id: str, system_type: str, unidad_id: str, unidad_codigo: str) -> Dict[str, Any]:
    return {
        "unidad_negocio_id": unidad_id,
        "unidad_negocio_codigo": unidad_codigo,
        "server_id": server_id,
        "system_type": system_type,
        "folio": _as_text(row.get("folio"), 50),
        "codigo_producto": _as_text(row.get("codigo_producto"), 100),
        "nombre_producto": _as_text(row.get("nombre_producto"), 255),
        "unidad": _as_text(row.get("unidad"), 50),
        "existencia_fisica": _as_float(row.get("existencia_fisica")),
        "rendimiento": _as_float(row.get("rendimiento"), 1.0),
        "costo_unitario": _as_float(row.get("costo_unitario")),
        "almacen": _as_text(row.get("almacen"), 100),
        "almacen_id": _as_text(row.get("almacen_id"), 50),
        "sync_source": "SYNC",
        "sync_status": "ACTIVE",
    }


def _insert_detail_row(cursor, columns: Dict[str, str], values: Dict[str, Any]) -> None:
    insert_sql, param_names = _detail_insert_statement(columns)
    cursor.execute(insert_sql, tuple(values.get(name) for name in param_names))


def _detail_insert_parts(columns: Dict[str, str]) -> tuple[List[str], List[str], List[str]]:
    ordered = [
        "unidad_negocio_id",
        "unidad_negocio_codigo",
        "server_id",
        "system_type",
        "folio",
        "codigo_producto",
        "nombre_producto",
        "unidad",
        "existencia_fisica",
        "rendimiento",
        "costo_unitario",
        "almacen",
        "almacen_id",
        "sync_source",
        "sync_timestamp",
        "sync_status",
    ]

    insert_columns = []
    placeholders = []
    params = []
    for logical_name in ordered:
        column_name = columns.get(logical_name)
        if not column_name:
            continue
        insert_columns.append(_sql_identifier(column_name))
        if logical_name == "sync_timestamp":
            placeholders.append("GETDATE()")
        else:
            placeholders.append("%s")
            params.append(logical_name)

    return insert_columns, placeholders, params


def _detail_insert_statement(columns: Dict[str, str]) -> tuple[str, List[str]]:
    insert_columns, placeholders, params = _detail_insert_parts(columns)
    return (
        f"""
            INSERT INTO dbo.Compras_Inventarios_Fisicos_Detalle_Sync
            ({', '.join(insert_columns)})
            VALUES ({', '.join(placeholders)})
        """,
        params,
    )


def _detail_update_statement(columns: Dict[str, str]) -> tuple[Optional[str], List[str]]:
    key_names = [
        "server_id",
        "unidad_negocio_id",
        "folio",
        "codigo_producto",
        "almacen_id",
    ]
    if any(not columns.get(key) for key in key_names):
        return None, []

    update_names = [
        "unidad_negocio_codigo",
        "system_type",
        "nombre_producto",
        "unidad",
        "existencia_fisica",
        "rendimiento",
        "costo_unitario",
        "almacen",
        "sync_source",
        "sync_timestamp",
        "sync_status",
    ]
    assignments = []
    params = []
    for logical_name in update_names:
        column_name = columns.get(logical_name)
        if not column_name:
            continue
        if logical_name == "sync_timestamp":
            assignments.append(f"{_sql_identifier(column_name)} = GETDATE()")
        else:
            assignments.append(f"{_sql_identifier(column_name)} = %s")
            params.append(logical_name)

    where_clause = " AND ".join(
        f"{_sql_identifier(columns[key])} = %s"
        for key in key_names
    )
    params.extend(key_names)
    return (
        f"""
            UPDATE dbo.Compras_Inventarios_Fisicos_Detalle_Sync
            SET {', '.join(assignments)}
            WHERE {where_clause}
        """,
        params,
    )


def _bulk_insert_detail_values(
    cursor,
    columns: Dict[str, str],
    values_list: List[Dict[str, Any]],
) -> int:
    if not values_list:
        return 0

    insert_columns, placeholders, param_names = _detail_insert_parts(columns)
    params_per_row = max(1, len(param_names))
    chunk_size = max(1, min(250, SQL_SERVER_SAFE_PARAM_LIMIT // params_per_row))
    total = 0
    for start in range(0, len(values_list), chunk_size):
        chunk = values_list[start:start + chunk_size]
        values_sql = ", ".join(f"({', '.join(placeholders)})" for _ in chunk)
        params = []
        for values in chunk:
            params.extend(values.get(name) for name in param_names)
        cursor.execute(
            f"""
                INSERT INTO dbo.Compras_Inventarios_Fisicos_Detalle_Sync
                ({', '.join(insert_columns)})
                VALUES {values_sql}
            """,
            tuple(params),
        )
        total += len(chunk)
        logger.warning(
            "[SYNC] Bulk detalle inventarios insertado: %s/%s",
            total,
            len(values_list),
        )
    return total


def _bulk_update_detail_values(
    cursor,
    columns: Dict[str, str],
    values_list: List[Dict[str, Any]],
) -> int:
    if not values_list:
        return 0

    key_names = [
        "server_id",
        "unidad_negocio_id",
        "folio",
        "codigo_producto",
        "almacen_id",
    ]
    if any(not columns.get(key) for key in key_names):
        return 0

    update_names = [
        "unidad_negocio_codigo",
        "system_type",
        "nombre_producto",
        "unidad",
        "existencia_fisica",
        "rendimiento",
        "costo_unitario",
        "almacen",
        "sync_source",
        "sync_status",
    ]
    update_names = [name for name in update_names if columns.get(name)]
    source_names = key_names + update_names
    params_per_row = max(1, len(source_names))
    chunk_size = max(1, min(120, SQL_SERVER_SAFE_PARAM_LIMIT // params_per_row))

    source_columns = ", ".join(_sql_identifier(name) for name in source_names)
    set_clauses = [
        f"target.{_sql_identifier(columns[name])} = source.{_sql_identifier(name)}"
        for name in update_names
    ]
    if columns.get("sync_timestamp"):
        set_clauses.append(f"target.{_sql_identifier(columns['sync_timestamp'])} = GETDATE()")
    join_clause = " AND ".join(
        f"target.{_sql_identifier(columns[name])} = source.{_sql_identifier(name)}"
        for name in key_names
    )

    total = 0
    for start in range(0, len(values_list), chunk_size):
        chunk = values_list[start:start + chunk_size]
        row_placeholders = ", ".join(
            f"({', '.join(['%s'] * len(source_names))})"
            for _ in chunk
        )
        params = []
        for values in chunk:
            params.extend(values.get(name) for name in source_names)
        cursor.execute(
            f"""
                UPDATE target
                SET {', '.join(set_clauses)}
                FROM dbo.Compras_Inventarios_Fisicos_Detalle_Sync AS target
                INNER JOIN (VALUES {row_placeholders}) AS source ({source_columns})
                    ON {join_clause}
            """,
            tuple(params),
        )
        total += len(chunk)
        logger.warning(
            "[SYNC] Bulk detalle inventarios actualizado: %s/%s",
            total,
            len(values_list),
        )
    return total


def _update_detail_row(cursor, columns: Dict[str, str], values: Dict[str, Any]) -> int:
    update_sql, param_names = _detail_update_statement(columns)
    if not update_sql:
        return 0

    cursor.execute(update_sql, tuple(values.get(name) for name in param_names))
    return int(cursor.rowcount or 0)


def _fetch_existing_detail_keys(
    cursor,
    columns: Dict[str, str],
    values_list: List[Dict[str, Any]],
) -> set[tuple[str, str, str, str]]:
    if not values_list:
        return set()

    key_names = [
        "server_id",
        "unidad_negocio_id",
        "folio",
        "codigo_producto",
        "almacen_id",
    ]
    if any(not columns.get(key) for key in key_names):
        return set()

    server_id = _as_text(values_list[0].get("server_id"), 100)
    unidad_negocio_id = _as_text(
        values_list[0].get("unidad_negocio_id"),
        64,
    )
    folios = []
    seen_folios = set()
    for values in values_list:
        folio = _as_text(values.get("folio"), 50)
        if folio and folio not in seen_folios:
            seen_folios.add(folio)
            folios.append(folio)
    if not server_id or not unidad_negocio_id or not folios:
        return set()

    existing = set()
    server_column = _sql_identifier(columns["server_id"])
    unidad_column = _sql_identifier(columns["unidad_negocio_id"])
    folio_column = _sql_identifier(columns["folio"])
    select_columns = ", ".join(_sql_identifier(columns[key]) for key in key_names)
    batch_size = 500
    for start in range(0, len(folios), batch_size):
        batch = folios[start:start + batch_size]
        placeholders = ", ".join(["%s"] * len(batch))
        cursor.execute(
            f"""
                SELECT {select_columns}
                FROM dbo.Compras_Inventarios_Fisicos_Detalle_Sync
                WHERE {server_column} = %s
                  AND {unidad_column} = %s
                  AND CAST({folio_column} AS VARCHAR(50)) IN ({placeholders})
            """,
            tuple([server_id, unidad_negocio_id] + batch),
        )
        for row in cursor.fetchall():
            if isinstance(row, dict):
                key = tuple(_as_text(row.get(columns[name]) or row.get(name), 100) for name in key_names)
            else:
                key = tuple(_as_text(row[index], 100) for index in range(5))
            existing.add(key)
    return existing


def _collapse_detail_values_by_key(values_list: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], int]:
    ordered_keys = []
    by_key: Dict[tuple[str, str, str, str, str], Dict[str, Any]] = {}
    duplicates = 0
    for values in values_list:
        key = _inventory_detail_key(values)
        if key in by_key:
            duplicates += 1
        else:
            ordered_keys.append(key)
        by_key[key] = values
    return [by_key[key] for key in ordered_keys], duplicates


def _bulk_upsert_detail_values(
    cursor,
    columns: Dict[str, str],
    values_list: List[Dict[str, Any]],
) -> tuple[int, int]:
    values_list, duplicates = _collapse_detail_values_by_key(values_list)
    if duplicates:
        logger.warning(
            "[SYNC] Detalle inventarios colapsado por llaves duplicadas: %s",
            duplicates,
        )

    existing_keys = _fetch_existing_detail_keys(cursor, columns, values_list)
    values_to_update = []
    values_to_insert = []
    for values in values_list:
        if _inventory_detail_key(values) in existing_keys:
            values_to_update.append(values)
        else:
            values_to_insert.append(values)

    details_updated = _bulk_update_detail_values(cursor, columns, values_to_update)
    details_synced = _bulk_insert_detail_values(cursor, columns, values_to_insert)
    return details_synced, details_updated


def _sync_inventarios_fisicos_detalle(
    cursor,
    detail_rows: List[Dict[str, Any]],
    server_id: str,
    system_type: str,
    unidad_id: str,
    unidad_codigo: str,
) -> Dict[str, Any]:
    table_name = "Compras_Inventarios_Fisicos_Detalle_Sync"
    columns = _fetch_table_columns(cursor, table_name)
    required_columns = [
        "server_id",
        "folio",
        "codigo_producto",
        "nombre_producto",
        "unidad",
        "existencia_fisica",
        "costo_unitario",
        "almacen",
        "almacen_id",
        "sync_status",
    ]
    missing_columns = [column for column in required_columns if not columns.get(column)]
    if missing_columns:
        return {
            "status": "ERROR",
            "details_synced": 0,
            "details_updated": 0,
            "detail_errors": len(missing_columns),
            "error": f"Tabla {table_name} incompleta o inexistente. Faltan columnas: {', '.join(missing_columns)}",
        }

    cursor.execute("""
        UPDATE dbo.Compras_Inventarios_Fisicos_Detalle_Sync
        SET sync_status = 'REPLACED'
        WHERE server_id = %s
          AND unidad_negocio_id = %s
          AND sync_status = 'ACTIVE'
    """, (server_id, unidad_id))

    values_list = []
    detail_errors = 0
    for row in detail_rows:
        values = _detail_values(row, server_id, system_type, unidad_id, unidad_codigo)
        if not values["folio"] or not values["codigo_producto"] or not values["almacen_id"]:
            detail_errors += 1
            logger.warning("[SYNC] Detalle inventario omitido por llave incompleta: %s", values)
            continue
        values_list.append(values)

    details_synced = 0
    details_updated = 0
    try:
        details_synced, details_updated = _bulk_upsert_detail_values(cursor, columns, values_list)
    except Exception as bulk_error:
        logger.warning(
            "[SYNC] Bulk upsert detalle inventarios no disponible/falló; fallback fila por fila: %s",
            str(bulk_error)[:180],
        )
        details_synced = 0
        details_updated = 0
        for values in values_list:
            try:
                _insert_detail_row(cursor, columns, values)
                details_synced += 1
            except Exception as insert_error:
                try:
                    updated = _update_detail_row(cursor, columns, values)
                    if updated:
                        details_updated += updated
                        continue
                except Exception as update_error:
                    logger.warning(
                        "[SYNC] Error actualizando detalle inventario folio=%s producto=%s: %s",
                        values["folio"],
                        values["codigo_producto"],
                        update_error,
                    )
                detail_errors += 1
                logger.warning(
                    "[SYNC] Error insertando detalle inventario folio=%s producto=%s: %s",
                    values["folio"],
                    values["codigo_producto"],
                    insert_error,
                )

    status = "OK" if detail_errors == 0 else "PARTIAL"
    return {
        "status": status,
        "details_synced": details_synced,
        "details_updated": details_updated,
        "detail_errors": detail_errors,
        "error": None if detail_errors == 0 else f"{detail_errors} detalles de inventario no sincronizados",
    }




TIPO_MOVIMIENTO_SR_TO_EDARSAHUB = {
    # Compras
    "EPC": 1,  # ENTRADA_COMPRA
    "SPC": 2,  # SALIDA_DEV_PROV

    # Traspasos
    "ETA": 5,  # TRASPASO_ENTRADA
    "STA": 6,  # TRASPASO_SALIDA

    # Inventario físico / ajustes
    "ECI": 3,  # AJUSTE_ENTRADA
    "SCI": 4,  # AJUSTE_SALIDA

    # Otras entradas
    "EPA": 3,
    "EPL": 3,
    "EPB": 3,

    # Otras salidas
    "SPA": 4,
    "SPM": 4,
    "SPD": 4,
}




def registrar_concepto_movimiento_no_mapeado(acumulador, concepto, cantidad=None, fecha=None):
    concepto = str(concepto or "NULL").strip().upper()
    if concepto not in acumulador:
        acumulador[concepto] = {
            "idconcepto": concepto,
            "registros": 0,
            "cantidad_total": 0,
            "ejemplo_fecha": str(fecha) if fecha else None,
        }
    acumulador[concepto]["registros"] += 1
    try:
        acumulador[concepto]["cantidad_total"] += float(cantidad or 0)
    except Exception:
        pass
    if not acumulador[concepto].get("ejemplo_fecha") and fecha:
        acumulador[concepto]["ejemplo_fecha"] = str(fecha)


def resolver_proveedor_edarsahub(cursor, empresa_id, proveedor_origen_id=None, proveedor_nombre=None, proveedor_rfc=None):
    """
    Resuelve ProveedorID canónico EDARSAHUB.
    Prohibido usar ProveedorID=1 como default.

    Si no existe, crea placeholder trazable por código origen.
    """
    proveedor_origen_id = str(proveedor_origen_id or "").strip()
    proveedor_nombre = str(proveedor_nombre or proveedor_origen_id or "PROVEEDOR ORIGEN SIN NOMBRE").strip()
    proveedor_rfc = str(proveedor_rfc or "").strip()

    if proveedor_rfc:
        cursor.execute("""
            SELECT TOP 1 ProveedorID
            FROM dbo.Proveedor_Catalogo
            WHERE EmpresaID = %s AND RFC = %s
            ORDER BY ProveedorID
        """, (empresa_id, proveedor_rfc))
        row = cursor.fetchone()
        if row:
            return row[0]

    if proveedor_origen_id:
        cursor.execute("""
            SELECT TOP 1 ProveedorID
            FROM dbo.Proveedor_Catalogo
            WHERE EmpresaID = %s
              AND (
                    CodigoProveedor = %s
                 OR CodigoOrigen = %s
                 OR CAST(ProveedorID AS NVARCHAR(50)) = %s
              )
            ORDER BY ProveedorID
        """, (empresa_id, proveedor_origen_id, proveedor_origen_id, proveedor_origen_id))
        row = cursor.fetchone()
        if row:
            return row[0]

    codigo = proveedor_origen_id or f"ORIGEN_SIN_CODIGO_{proveedor_nombre[:20]}"

    cursor.execute("""
        INSERT INTO dbo.Proveedor_Catalogo
        (
            EmpresaID,
            CodigoProveedor,
            CodigoOrigen,
            RazonSocial,
            NombreComercial,
            RFC,
            Activo,
            FechaCreacion
        )
        OUTPUT INSERTED.ProveedorID
        VALUES (%s, %s, %s, %s, %s, NULLIF(%s, ''), 1, GETDATE())
    """, (
        empresa_id,
        codigo,
        codigo,
        proveedor_nombre,
        proveedor_nombre,
        proveedor_rfc
    ))

    return cursor.fetchone()[0]


def map_tipo_movimiento_softrestaurant(idconcepto, cantidad=None):
    """
    Mapea idconcepto de SoftRestaurant a Inventario_TipoMovimiento.TipoMovimientoID.

    Si no hay mapeo, devuelve None para evitar insertar movimientos ambiguos.
    """
    concepto = str(idconcepto or "").strip().upper()
    if concepto in TIPO_MOVIMIENTO_SR_TO_EDARSAHUB:
        return TIPO_MOVIMIENTO_SR_TO_EDARSAHUB[concepto]

    return None


def get_compras_adapter(system_type: str):
    """
    Retorna adapter por sistema origen.
    Los nombres de tablas origen viven solo en adapters.
    EDARSAHUB conserva modelo canónico.
    """
    st = (system_type or "").upper()

    if "SOFT" in st:
        return softrestaurant_pro_adapter

    if "MPRO" in st or "MANAGEMENT" in st or "MANAGMENT" in st:
        return mpro_adapter

    return None


def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB usando configuración de variables de entorno"""
    return get_sql_connection()


# =============================================================================
# LECTURA DE DATOS SINCRONIZADOS (Endpoints usan estas funciones)
# =============================================================================


def _get_edarsahub_context(server_info: Dict, unidad_info: Dict) -> Dict:
    """
    Resuelve identidad canónica EDARSAHUB para sincronizaciones de Compras.

    Contrato:
    - unidad_negocio_pk proviene directamente de dbo.Unidades_Negocio.id.
    - EmpresaID y SucursalID se resuelven con el resolver canónico existente.
    - No existen defaults ni IDs inventados.
    - Si alguna dimensión no puede resolverse, falla cerrado.
    """
    from core.inventarios.resolver_canonico import (
        resolver_empresa_id,
        resolver_sucursal_id,
    )

    unidad_info = unidad_info or {}
    server_info = server_info or {}

    unidad_negocio_pk = str(unidad_info.get('id') or '').strip()
    unidad_codigo = str(unidad_info.get('codigo') or '').strip()
    server_id = str(
        server_info.get('id') or server_info.get('server_id') or ''
    ).strip()
    sucursal_origen_id = unidad_info.get('sucursal_origen_id')

    if not unidad_negocio_pk:
        raise ValueError(
            "UNIDAD_NEGOCIO_PK_NO_RESUELTA: "
            "unidad_info.id canónico es obligatorio"
        )

    if not unidad_codigo:
        raise ValueError(
            "UNIDAD_CODIGO_NO_RESUELTO: "
            "unidad_info.codigo canónico es obligatorio"
        )

    if not server_id:
        raise ValueError(
            "SERVER_ID_NO_RESUELTO: requerido para resolver sucursal canónica"
        )

    emp = resolver_empresa_id(unidad_codigo)
    suc = resolver_sucursal_id(server_id, sucursal_origen_id)

    if not emp.resuelto:
        raise ValueError(
            f"EMPRESA_CANONICA_NO_RESUELTA:{emp.motivo}"
        )

    if not suc.resuelto:
        raise ValueError(
            f"SUCURSAL_CANONICA_NO_RESUELTA:{suc.motivo}"
        )

    return {
        'empresa_id': int(emp.canonical_id),
        'sucursal_id': int(suc.canonical_id),
        'unidad_negocio_pk': unidad_negocio_pk,
        'system_type': server_info.get('system_type', 'UNKNOWN'),
        'server_name': (
            server_info.get('nombre')
            or server_info.get('name')
            or 'UNKNOWN'
        ),
        'unidad_codigo': unidad_codigo,
    }



def obtener_inventarios_fisicos_sync(
    unidad_negocio_id: str = None,
    server_id: str = None,
    sucursal: str = None,
    almacen_id: str = None,
    almacen: str = None,
    limit: int = 500
) -> List[Dict]:
    """
    Obtiene inventarios físicos DESDE EDARSAHUB (sincronizados).
    NO se conecta a servidores en vivo.
    """
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        # NO-LIVE / EDARSAHUB única fuente: se leen TODOS los inventarios capturados
        # (ACTIVE y REPLACED) deduplicando por inventario físico real
        # (server_id+sucursal_id+almacen_id+folio) y prefiriendo ACTIVE. Esto corrige
        # el caso en que un sync marcó los registros como REPLACED pero el insert de la
        # nueva tanda ACTIVE falló (POS inaccesible), dejando data válida oculta (MPRO).
        inner_where = "WHERE sync_status IN ('ACTIVE', 'REPLACED')"
        params = []
        
        if unidad_negocio_id:
            inner_where += " AND unidad_negocio_id = %s"
            params.append(unidad_negocio_id)
        
        if server_id:
            inner_where += " AND LOWER(server_id) = LOWER(%s)"
            params.append(server_id)
        
        if sucursal:
            inner_where += " AND (sucursal LIKE %s OR sucursal_id = %s)"
            params.extend([f'%{sucursal}%', sucursal])
        
        if almacen_id and almacen_id != 'TODOS' and almacen and almacen != 'TODOS':
            # Algunas pantallas tienen un id canónico de almacén que no coincide 1:1
            # con el almacen_id sincronizado del origen; conservamos el filtro por id,
            # pero dejamos el nombre como recuperación para no ocultar inventarios.
            inner_where += " AND (almacen_id = %s OR almacen LIKE %s)"
            params.extend([almacen_id, f'%{almacen}%'])
        elif almacen_id and almacen_id != 'TODOS':
            inner_where += " AND almacen_id = %s"
            params.append(almacen_id)
        elif almacen and almacen != 'TODOS':
            inner_where += " AND almacen LIKE %s"
            params.append(f'%{almacen}%')
        
        query = f"""
            SELECT 
                folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
                tipo, estatus, total_productos, comentario, unidad_negocio_id, 
                unidad_negocio_codigo, server_id, system_type,
                sync_timestamp, sync_status
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY server_id, sucursal_id, almacen_id, folio
                        ORDER BY CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END, sync_timestamp DESC
                    ) AS _rn
                FROM Compras_Inventarios_Fisicos_Sync
                {inner_where}
            ) t
            WHERE t._rn = 1
            ORDER BY fecha DESC OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir datetime a string
        for row in rows:
            if row.get('fecha'):
                row['fecha'] = row['fecha'].isoformat() if hasattr(row['fecha'], 'isoformat') else str(row['fecha'])
            if row.get('sync_timestamp'):
                row['sync_timestamp'] = str(row['sync_timestamp'])
        
        logger.warning(
            "[SYNC-READ] Inventarios físicos filtros server_id=%s sucursal=%s almacen_id=%s almacen=%s rows=%s",
            server_id,
            sucursal,
            almacen_id,
            almacen,
            len(rows),
        )
        return rows
        
    except Exception as e:
        logger.error(f"[SYNC-READ] Error obteniendo inventarios: {e}")
        return []


def obtener_requisiciones_sync(
    unidad_negocio_id: str = None,
    server_id: str = None,
    sucursal: str = None,
    limit: int = 500
) -> List[Dict]:
    """
    Obtiene requisiciones/pedidos DESDE EDARSAHUB (sincronizados).
    NO se conecta a servidores en vivo.
    """
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        # Compras_Requisiciones_Sync es versionada.
        # Algunas sincronizaciones dejan la versión más reciente como REPLACED
        # cuando no existe una fila ACTIVE vigente. No debemos perder el documento
        # ni devolver todas sus versiones históricas.
        #
        # Contrato de lectura:
        # - una sola fila efectiva por unidad + servidor + tipo + folio;
        # - ACTIVE tiene prioridad cuando existe;
        # - en ausencia de ACTIVE se usa la versión sincronizada más reciente.
        query = """
            SELECT
                tipo, folio, fecha, fecha_entrega, proveedor, proveedor_id,
                sucursal, sucursal_id, total_productos, importe, estatus,
                unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
                sync_timestamp, sync_status
            FROM (
                SELECT
                    id,
                    tipo, folio, fecha, fecha_entrega, proveedor, proveedor_id,
                    sucursal, sucursal_id, total_productos, importe, estatus,
                    unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
                    sync_timestamp, sync_status,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            unidad_negocio_id,
                            server_id,
                            tipo,
                            folio
                        ORDER BY
                            CASE WHEN sync_status = 'ACTIVE' THEN 0 ELSE 1 END,
                            sync_timestamp DESC,
                            id DESC
                    ) AS _rn
                FROM Compras_Requisiciones_Sync
            ) AS requisiciones_efectivas
            WHERE _rn = 1
        """
        params = []
        
        if unidad_negocio_id:
            query += " AND unidad_negocio_id = %s"
            params.append(unidad_negocio_id)
        
        if server_id:
            query += " AND server_id = %s"
            params.append(server_id)
        
        if sucursal:
            # SoftRestaurant es 1:1 servidor-sucursal y guarda sucursal=''. Como el query
            # ya filtra por server_id, las filas sin sucursal (SR) deben pasar siempre;
            # el filtro de sucursal solo desambigua servidores multisucursal (MPRO).
            query += " AND (sucursal LIKE %s OR sucursal_id = %s OR ISNULL(sucursal,'') = '')"
            params.extend([f'%{sucursal}%', sucursal])
        
        query += f" ORDER BY fecha DESC OFFSET 0 ROWS FETCH NEXT {limit} ROWS ONLY"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir datetime a string
        for row in rows:
            for date_field in ['fecha', 'fecha_entrega', 'sync_timestamp']:
                if row.get(date_field):
                    row[date_field] = row[date_field].isoformat() if hasattr(row[date_field], 'isoformat') else str(row[date_field])
        
        logger.info(f"[SYNC-READ] Requisiciones: {len(rows)} registros desde EDARSAHUB")
        return rows
        
    except Exception as e:
        logger.error(f"[SYNC-READ] Error obteniendo requisiciones: {e}")
        return []


# =============================================================================
# SINCRONIZACIÓN (Job Background - se conecta a servidores físicos)
# =============================================================================

def sync_inventarios_fisicos_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_query_func,
    sync_mode: str = INVENTORY_SYNC_MODE_ROLLING_6M,
) -> Dict:
    """
    Sincroniza inventarios físicos desde un servidor físico a EDARSAHUB.
    Esta función se llama desde el job de sincronización.
    
    Args:
        server_info: Diccionario con host, port, database, username, password, system_type
        unidad_info: Diccionario con id, codigo, nombre
        execute_sql_query_func: Función para ejecutar queries en el servidor origen
    
    Returns:
        Dict con status, records_synced, error
    """
    from core.system_type_utils import is_mpro_system, is_softrestaurant_system
    
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '')

    sync_mode = str(sync_mode or "").strip().upper()

    if sync_mode not in {
        INVENTORY_SYNC_MODE_ROLLING_6M,
        INVENTORY_SYNC_MODE_FULL,
    }:
        raise ValueError(
            f"Modo de sincronizacion de inventarios no soportado: {sync_mode!r}"
        )

    unidad_id = unidad_info.get('id')
    unidad_codigo = unidad_info.get('codigo')
    sucursal_origen_id = (
        (unidad_info or {}).get('sucursal_origen_id')
    )

    if is_mpro_system(system_type):
        sucursal_origen_id = str(
            sucursal_origen_id or ""
        ).strip()

        if not sucursal_origen_id:
            return {
                "status": "ERROR",
                "records_synced": 0,
                "details_synced": 0,
                "details_updated": 0,
                "detail_errors": 0,
                "error": (
                    "MPRO requiere sucursal_origen_id canónica "
                    "para sincronizar inventarios sin mezclar unidades"
                ),
            }
    
    logger.info(f"[SYNC] Iniciando sync inventarios: {unidad_codigo} ({system_type})")
    
    try:
        # Query según tipo de sistema
        if is_mpro_system(system_type):
            # MPRO es multisucursal. La unidad se delimita mediante
            # sucursal_origen_id canónica de Unidades_Negocio.
            safe_sucursal_origen = (
                str(sucursal_origen_id)
                .strip()
                .replace("'", "''")
            )

            query = f"""
                SELECT 
                    F.Fi_Folio as folio,
                    F.Fi_Fecha as fecha,
                    A.Al_Descripcion as almacen,
                    A.Al_Cve_Almacen as almacen_id,
                    S.Sc_Descripcion as sucursal,
                    A.Sc_Cve_Sucursal as sucursal_id,
                    'FISICO' as tipo,
                    'CERRADO' as estatus,
                    COUNT(F.Pr_Cve_Producto) as total_productos,
                    MAX(F.Fi_Comentario) as comentario
                FROM Fisico F
                INNER JOIN Almacen A ON A.Al_Cve_Almacen = F.Al_Cve_Almacen AND A.Sc_Cve_Sucursal = F.Sc_Cve_Sucursal
                LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = A.Sc_Cve_Sucursal
                WHERE {_inventory_history_filter("F.Fi_Fecha", sync_mode)}
                  AND ISNULL(F.Es_Cve_Estado, '') <> 'CA'
                  AND F.Sc_Cve_Sucursal = '{safe_sucursal_origen}'
                GROUP BY F.Fi_Folio, F.Fi_Fecha, A.Al_Descripcion, A.Al_Cve_Almacen, S.Sc_Descripcion, A.Sc_Cve_Sucursal
                ORDER BY F.Fi_Fecha DESC
            """
        elif is_softrestaurant_system(system_type):
            # SoftRestaurant usa tabla "invfisico". El almacen_id debe venir
            # del encabezado del inventario; no depende del LEFT JOIN al catalogo.
            query = f"""
                SELECT 
                    CAST(INV.folio AS VARCHAR) as folio,
                    INV.fecha as fecha,
                    COALESCE(A.nombre, CAST(INV.idalmacen1 AS VARCHAR(50))) as almacen,
                    CAST(INV.idalmacen1 AS VARCHAR(50)) as almacen_id,
                    '' as sucursal,
                    '' as sucursal_id,
                    'FISICO' as tipo,
                    'CERRADO' as estatus,
                    0 as total_productos,
                    '' as comentario
                FROM invfisico INV
                LEFT JOIN almacen A ON A.idalmacen = INV.idalmacen1
                WHERE {_inventory_history_filter("INV.fecha", sync_mode)}
                  AND ISNULL(INV.cancelado, 0) = 0
                ORDER BY INV.fecha DESC
            """
        else:
            return {"status": "ERROR", "records_synced": 0, "error": f"Sistema no soportado: {system_type}"}
        
        # Ejecutar encabezados en servidor origen
        rows = execute_sql_query_func(
            server_info['host'],
            server_info['port'],
            server_info['database'],
            server_info['username'],
            server_info['password'],
            query
        )
        
        if rows is None:
            return {
                "status": "ERROR",
                "records_synced": 0,
                "error": "No se pudo consultar el servidor origen",
            }

        if not rows:
            return {"status": "OK", "records_synced": 0, "error": None}

        source_header_count = len(rows)
        # Ejecutar detalle físico en servidor origen. El endpoint de análisis
        # consume esta tabla canónica y no debe conectarse live al POS.
        detail_query = _inventarios_fisicos_detalle_query(
            system_type,
            [],
            sucursal_origen_id,
            sync_mode=sync_mode,
        )
        detail_rows = []
        if detail_query:
            batch_size = _inventory_detail_batch_size()
            folio_batches = _unique_folio_batches(rows, batch_size)
            logger.warning(
                "[SYNC] Consultando detalle inventarios por lotes: headers=%s folios=%s batch_size=%s",
                len(rows),
                sum(len(batch) for batch in folio_batches),
                batch_size,
            )
            for batch_index, folios_batch in enumerate(folio_batches, 1):
                batch_query = _inventarios_fisicos_detalle_query(
                    system_type,
                    folios_batch,
                    sucursal_origen_id,
                    sync_mode=sync_mode,
                )
                batch_rows = execute_sql_query_func(
                    server_info['host'],
                    server_info['port'],
                    server_info['database'],
                    server_info['username'],
                    server_info['password'],
                    batch_query
                )
                if batch_rows is None:
                    return {
                        "status": "ERROR",
                        "records_synced": 0,
                        "details_synced": 0,
                        "details_updated": 0,
                        "detail_errors": 0,
                        "error": (
                            "No se pudo consultar el detalle físico en el servidor origen "
                            f"(lote {batch_index}/{len(folio_batches)})"
                        ),
                    }
                detail_rows.extend(batch_rows)
                logger.warning(
                    "[SYNC] Detalle inventarios lote %s/%s: folios=%s rows=%s acumulado=%s",
                    batch_index,
                    len(folio_batches),
                    len(folios_batch),
                    len(batch_rows),
                    len(detail_rows),
                )
            if not detail_rows:
                return {
                    "status": "ERROR",
                    "records_synced": 0,
                    "details_synced": 0,
                    "details_updated": 0,
                    "detail_errors": len(rows),
                    "error": (
                        "Inventarios físicos con encabezado pero sin detalle origen. "
                        "No se actualiza el canónico para evitar folios sin detalle."
                    ),
                }
            rows, headers_without_detail = _filter_inventory_headers_with_detail(rows, detail_rows)
            if not rows:
                return {
                    "status": "ERROR",
                    "records_synced": 0,
                    "details_synced": 0,
                    "details_updated": 0,
                    "detail_errors": headers_without_detail,
                    "error": (
                        "Inventarios físicos sin detalle coincidente por folio/almacén. "
                        "No se actualiza el canónico para evitar folios sin detalle."
                    ),
                }
            if headers_without_detail:
                logger.error(
                    "[SYNC] Snapshot rechazado: %s inventarios físicos sin detalle coincidente",
                    headers_without_detail,
                )
                return {
                    "status": "ERROR",
                    "records_synced": 0,
                    "details_synced": 0,
                    "details_updated": 0,
                    "detail_errors": headers_without_detail,
                    "error": (
                        f"{headers_without_detail} inventarios físicos sin detalle coincidente. "
                        "Snapshot anterior preservado; no se actualiza EDARSAHUB."
                    ),
                }
        else:
            headers_without_detail = 0
        
        # Guardar en EDARSAHUB
        conn = get_edarsahub_connection()
        cursor = conn.cursor()

        detail_result = {
            "status": "OK",
            "details_synced": 0,
            "details_updated": 0,
            "detail_errors": 0,
            "error": None,
        }
        if detail_query:
            detail_result = _sync_inventarios_fisicos_detalle(
                cursor,
                detail_rows,
                str(server_id or ""),
                system_type,
                str(unidad_id or ""),
                str(unidad_codigo or ""),
            )
            if detail_result.get("status") != "OK":
                conn.rollback()
                conn.close()
                return {
                    "status": "ERROR",
                    "records_synced": 0,
                    "details_synced": 0,
                    "details_updated": 0,
                    "detail_errors": detail_result.get("detail_errors", 0),
                    "error": (
                        detail_result.get("error")
                        or "Detalle de inventario incompleto; snapshot anterior preservado"
                    ),
                }
        
        # Marcar registros anteriores como inactivos
        cursor.execute("""
            UPDATE Compras_Inventarios_Fisicos_Sync
            SET sync_status = 'REPLACED'
            WHERE server_id = %s
              AND unidad_negocio_id = %s
              AND sync_status = 'ACTIVE'
        """, (server_id, unidad_id))

        # Insertar nuevos registros.
        # La fotografia solo puede confirmarse si TODAS las cabeceras validas
        # quedan persistidas. Cualquier fallo provoca rollback completo.
        records_synced = 0
        header_errors = 0
        for row in rows:
            try:
                cursor.execute("""
                    INSERT INTO Compras_Inventarios_Fisicos_Sync
                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
                     folio, fecha, almacen, almacen_id, sucursal, sucursal_id,
                     tipo, estatus, total_productos, comentario, sync_source, sync_timestamp, sync_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'SYNC', GETDATE(), 'ACTIVE')
                """, (
                    unidad_id, unidad_codigo, server_id, system_type,
                    str(row.get('folio', '')),
                    row.get('fecha'),
                    row.get('almacen', ''),
                    str(row.get('almacen_id', '')),
                    row.get('sucursal', ''),
                    str(row.get('sucursal_id', '')),
                    row.get('tipo', 'FISICO'),
                    row.get('estatus', ''),
                    row.get('total_productos', 0),
                    (row.get('comentario') or '')[:50]
                ))
                records_synced += 1
            except Exception as insert_error:
                try:
                    cursor.execute("""
                        UPDATE Compras_Inventarios_Fisicos_Sync
                        SET unidad_negocio_id = %s,
                            unidad_negocio_codigo = %s,
                            system_type = %s,
                            fecha = %s,
                            almacen = %s,
                            almacen_id = %s,
                            sucursal = %s,
                            sucursal_id = %s,
                            tipo = %s,
                            estatus = %s,
                            total_productos = %s,
                            comentario = %s,
                            sync_source = 'SYNC',
                            sync_timestamp = GETDATE(),
                            sync_status = 'ACTIVE'
                        WHERE server_id = %s
                          AND unidad_negocio_id = %s
                          AND folio = %s
                    """, (
                        unidad_id,
                        unidad_codigo,
                        system_type,
                        row.get('fecha'),
                        row.get('almacen', ''),
                        str(row.get('almacen_id', '')),
                        row.get('sucursal', ''),
                        str(row.get('sucursal_id', '')),
                        row.get('tipo', 'FISICO'),
                        row.get('estatus', ''),
                        row.get('total_productos', 0),
                        (row.get('comentario') or '')[:50],
                        str(server_id or ''),
                        str(unidad_id or ''),
                        str(row.get('folio', '')),
                    ))
                    if cursor.rowcount:
                        records_synced += int(cursor.rowcount)
                        continue
                except Exception as update_error:
                    logger.warning(
                        "[SYNC] Error actualizando inventario %s: %s",
                        row.get('folio'),
                        update_error,
                    )
                header_errors += 1
                logger.warning(
                    "[SYNC] Error persistiendo inventario folio=%s insert_error=%s",
                    row.get("folio"),
                    insert_error,
                )

        if header_errors or records_synced != len(rows):
            expected_headers = len(rows)
            persisted_headers = records_synced
            conn.rollback()
            conn.close()
            return {
                "status": "ERROR",
                "records_synced": 0,
                "details_synced": 0,
                "details_updated": 0,
                "detail_errors": int(detail_result.get("detail_errors") or 0),
                "error": (
                    "Snapshot de inventarios incompleto; rollback aplicado. "
                    f"cabeceras_esperadas={expected_headers} "
                    f"cabeceras_persistidas={persisted_headers} "
                    f"errores_cabecera={header_errors}"
                ),
            }

        conn.commit()
        conn.close()
        
        details_synced = int(detail_result.get("details_synced") or 0)
        details_updated = int(detail_result.get("details_updated") or 0)
        detail_errors = int(detail_result.get("detail_errors") or 0) + int(headers_without_detail or 0)
        status = "OK" if detail_result.get("status") == "OK" and not headers_without_detail else "PARTIAL"
        error_message = detail_result.get("error")
        if headers_without_detail:
            skipped_message = f"{headers_without_detail} inventarios físicos omitidos por falta de detalle coincidente"
            error_message = f"{error_message}; {skipped_message}" if error_message else skipped_message
        logger.info(
            "[SYNC] Inventarios sincronizados: headers=%s/%s detalles_insertados=%s detalles_actualizados=%s errores_detalle=%s",
            records_synced,
            source_header_count,
            details_synced,
            details_updated,
            detail_errors,
        )
        return {
            "status": status,
            "records_synced": records_synced,
            "details_synced": details_synced,
            "details_updated": details_updated,
            "detail_errors": detail_errors,
            "error": error_message,
        }
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync inventarios {unidad_codigo}: {e}")
        return {
            "status": "ERROR",
            "records_synced": 0,
            "details_synced": 0,
            "details_updated": 0,
            "detail_errors": 0,
            "error": str(e),
        }


def sync_requisiciones_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_query_func
) -> Dict:
    """
    Sincroniza requisiciones/pedidos desde un servidor físico a EDARSAHUB.
    """
    from core.system_type_utils import is_mpro_system, is_softrestaurant_system
    
    server_id = server_info.get('id')
    system_type = server_info.get('system_type', '')
    unidad_id = unidad_info.get('id')
    unidad_codigo = unidad_info.get('codigo')
    
    logger.info(f"[SYNC] Iniciando sync requisiciones: {unidad_codigo} ({system_type})")
    
    try:
        # Query según tipo de sistema
        if is_mpro_system(system_type):
            # Esquema real ManagementPro (verificado): Orden_Compra es a nivel renglón
            # (1 fila por producto). Se agrupa por folio. Columnas reales:
            # Es_Cve_Estado (no Oc_Status), Pv_Descripcion (no Pv_Nombre),
            # importe = SUM(Oc_Precio_Neto_Importe) (no existe Oc_Total).
            query = """
                SELECT 
                    'OC' as tipo,
                    OC.Oc_Folio as folio,
                    MIN(OC.Oc_Fecha) as fecha,
                    MIN(OC.Oc_Fecha_Entrega) as fecha_entrega,
                    MAX(P.Pv_Descripcion) as proveedor,
                    MAX(OC.Pv_Cve_Proveedor) as proveedor_id,
                    MAX(S.Sc_Descripcion) as sucursal,
                    MAX(OC.Sc_Cve_Sucursal) as sucursal_id,
                    COUNT(OC.Pr_Cve_Producto) as total_productos,
                    SUM(ISNULL(OC.Oc_Precio_Neto_Importe, 0)) as importe,
                    MAX(OC.Es_Cve_Estado) as estatus
                FROM Orden_Compra OC
                LEFT JOIN Proveedor P ON P.Pv_Cve_Proveedor = OC.Pv_Cve_Proveedor
                LEFT JOIN Sucursal S ON S.Sc_Cve_Sucursal = OC.Sc_Cve_Sucursal
                WHERE OC.Es_Cve_Estado IN ('PXA', 'AC', 'RCT')
                  AND OC.Oc_Fecha >= DATEADD(MONTH, -3, GETDATE())
                GROUP BY OC.Oc_Folio
                ORDER BY MIN(OC.Oc_Fecha) DESC
            """
        elif is_softrestaurant_system(system_type):
            # Esquema real SoftRestaurant (verificado): ordenescompra usa fechacaptura/
            # fecharecepcion, aplicada/cancelado (no 'estatus'); JOIN ordenescompramov por
            # idordencompra. Mirror de la query LIVE legacy que ya funcionaba.
            query = """
                SELECT 
                    'ORDEN' as tipo,
                    CAST(OC.folio AS VARCHAR(50)) as folio,
                    OC.fechacaptura as fecha,
                    OC.fecharecepcion as fecha_entrega,
                    MAX(PR.nombre) as proveedor,
                    CAST(MAX(OC.idproveedor) AS VARCHAR(50)) as proveedor_id,
                    '' as sucursal,
                    '' as sucursal_id,
                    COUNT(OCM.idinsumo) as total_productos,
                    ISNULL(OC.total, 0) as importe,
                    CASE WHEN OC.aplicada = 0 THEN 'PXA' ELSE 'AUT' END as estatus
                FROM ordenescompra OC
                LEFT JOIN proveedores PR ON PR.idproveedor = OC.idproveedor
                LEFT JOIN ordenescompramov OCM ON OCM.idordencompra = OC.idordencompra
                WHERE OC.aplicada = 0 AND OC.cancelado = 0
                  AND OC.fechacaptura >= DATEADD(MONTH, -3, GETDATE())
                GROUP BY OC.folio, OC.fechacaptura, OC.fecharecepcion, OC.aplicada, OC.total
                ORDER BY OC.fechacaptura DESC
            """
        else:
            return {"status": "ERROR", "records_synced": 0, "error": f"Sistema no soportado: {system_type}"}
        
        # Ejecutar query en servidor origen
        rows = execute_sql_query_func(
            server_info['host'],
            server_info['port'],
            server_info['database'],
            server_info['username'],
            server_info['password'],
            query
        )
        
        if rows is None:
            return {
                "status": "ERROR",
                "records_synced": 0,
                "error": "No se pudo consultar el servidor origen",
            }

        if not rows:
            return {"status": "OK", "records_synced": 0, "error": None}
        
        # Guardar en EDARSAHUB
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        # Marcar registros anteriores como inactivos
        cursor.execute("""
            UPDATE Compras_Requisiciones_Sync 
            SET sync_status = 'REPLACED' 
            WHERE server_id = %s AND sync_status = 'ACTIVE'
        """, (server_id,))
        
        # Insertar nuevos registros
        records_synced = 0
        records_errors = 0
        for row in rows:
            tipo = row.get('tipo', 'OC')
            folio = str(row.get('folio', ''))
            try:
                cursor.execute("""
                    INSERT INTO Compras_Requisiciones_Sync
                    (unidad_negocio_id, unidad_negocio_codigo, server_id, system_type,
                     tipo, folio, fecha, fecha_entrega, proveedor, proveedor_id,
                     sucursal, sucursal_id, total_productos, importe, estatus,
                     sync_source, sync_timestamp, sync_status)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'SYNC', GETDATE(), 'ACTIVE')
                """, (
                    unidad_id,
                    unidad_codigo,
                    server_id,
                    system_type,
                    tipo,
                    folio,
                    row.get('fecha'),
                    row.get('fecha_entrega'),
                    row.get('proveedor', ''),
                    str(row.get('proveedor_id', '')),
                    row.get('sucursal', ''),
                    str(row.get('sucursal_id', '')),
                    row.get('total_productos', 0),
                    row.get('importe', 0),
                    row.get('estatus', '')
                ))
                records_synced += 1
            except Exception as insert_error:
                try:
                    cursor.execute("""
                        UPDATE Compras_Requisiciones_Sync
                        SET unidad_negocio_id = %s,
                            unidad_negocio_codigo = %s,
                            system_type = %s,
                            fecha = %s,
                            fecha_entrega = %s,
                            proveedor = %s,
                            proveedor_id = %s,
                            sucursal = %s,
                            sucursal_id = %s,
                            total_productos = %s,
                            importe = %s,
                            estatus = %s,
                            sync_source = 'SYNC',
                            sync_timestamp = GETDATE(),
                            sync_status = 'ACTIVE'
                        WHERE server_id = %s
                          AND folio = %s
                          AND tipo = %s
                    """, (
                        unidad_id,
                        unidad_codigo,
                        system_type,
                        row.get('fecha'),
                        row.get('fecha_entrega'),
                        row.get('proveedor', ''),
                        str(row.get('proveedor_id', '')),
                        row.get('sucursal', ''),
                        str(row.get('sucursal_id', '')),
                        row.get('total_productos', 0),
                        row.get('importe', 0),
                        row.get('estatus', ''),
                        str(server_id or ''),
                        folio,
                        tipo,
                    ))
                    if cursor.rowcount:
                        records_synced += int(cursor.rowcount)
                        continue
                except Exception as update_error:
                    logger.warning(
                        "[SYNC] Error actualizando requisición %s: %s",
                        folio,
                        update_error,
                    )
                records_errors += 1
                logger.warning(
                    "[SYNC] Error insertando requisición %s: %s",
                    folio,
                    insert_error,
                )
        
        conn.commit()
        conn.close()
        
        status = "OK" if records_errors == 0 else "PARTIAL"
        error = None if records_errors == 0 else f"{records_errors} requisiciones no sincronizadas"
        logger.info(
            "[SYNC] Requisiciones sincronizadas: %s de %s errores=%s",
            records_synced,
            len(rows),
            records_errors,
        )
        return {"status": status, "records_synced": records_synced, "error": error}
        
    except Exception as e:
        logger.error(f"[SYNC] Error sync requisiciones {unidad_codigo}: {e}")
        return {"status": "ERROR", "records_synced": 0, "error": str(e)}


def log_sync_operation(
    unidad_negocio_id: str,
    server_id: str,
    sync_type: str,
    sync_start: datetime,
    sync_end: datetime,
    records_synced: int,
    status: str,
    error_message: str = None
):
    """Registra la operación de sincronización en el log"""
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Compras_Sync_Log
            (unidad_negocio_id, server_id, sync_type, sync_start, sync_end, 
             records_synced, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            unidad_negocio_id, server_id, sync_type,
            sync_start, sync_end, records_synced, status, error_message
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[SYNC-LOG] Error registrando log: {e}")


def get_last_sync_info(server_id: str, sync_type: str) -> Optional[Dict]:
    """Obtiene información de la última sincronización"""
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute("""
            SELECT TOP 1 * FROM Compras_Sync_Log
            WHERE server_id = %s AND sync_type = %s
            ORDER BY created_at DESC
        """, (server_id, sync_type))
        row = cursor.fetchone()
        conn.close()
        return row
    except Exception as e:
        logger.error(f"[SYNC-LOG] Error obteniendo último sync: {e}")
        return None


# ============================================================================
# FUNCIONES DE SINCRONIZACIÓN ADICIONALES - SQL-FIRST
# ============================================================================

def sync_almacenes_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable
) -> Dict[str, Any]:
    """
    Sincroniza catálogo de almacenes desde servidor físico a EDARSAHUB.
    Destino: Inventario_Almacenes
    
    Llave MERGE: EmpresaID + SucursalID + CodigoAlmacen
    """
    # Resolución canónica de empresa/sucursal (Sistema_Empresas / Sistema_Sucursales).
    # No usa el contexto legacy (empresa=1/sucursal=1) que causaba mis-atribución.
    from core.inventarios.resolver_canonico import resolver_empresa_id, resolver_sucursal_id
    unidad_codigo = (unidad_info or {}).get('codigo', '')
    server_id = server_info.get('id') or server_info.get('server_id')
    system_type = server_info.get('system_type', '')

    emp = resolver_empresa_id(unidad_codigo)
    suc = resolver_sucursal_id(str(server_id), (unidad_info or {}).get('sucursal_origen_id'))
    if not emp.resuelto or not suc.resuelto:
        return {"status": "PENDIENTE", "records_synced": 0,
                "motivo": {"empresa": emp.motivo if not emp.resuelto else "OK",
                           "sucursal": suc.motivo if not suc.resuelto else "OK"}}
    empresa_id = emp.canonical_id
    sucursal_id = suc.canonical_id
    sucursal_origen = (unidad_info or {}).get('sucursal_origen_id')

    logger.info(f"[SYNC] Iniciando sync almacenes: Empresa={empresa_id}, Sucursal={sucursal_id}")
    
    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            # Esquema real ManagementPro (verificado): la tabla Almacen no tiene 'Al_Estatus';
            # el estado activo es Es_Cve_Estado='AC'. No expone tipo canónico -> 'GENERAL'.
            # MPRO es multisucursal: el código de almacén (p.ej. '0001') se repite por sucursal,
            # por lo que se DEBE filtrar por Sc_Cve_Sucursal = sucursal de origen de la unidad.
            filtro_suc_alm = ""
            if sucursal_origen:
                _so = str(sucursal_origen).replace("'", "''")
                filtro_suc_alm = f" AND Sc_Cve_Sucursal = '{_so}' "
            query_origen = f"""
                SELECT 
                    CAST(Al_Cve_Almacen AS VARCHAR(50)) AS codigo_almacen,
                    Al_Descripcion AS nombre_almacen,
                    'GENERAL' AS tipo_almacen,
                    CASE WHEN Es_Cve_Estado = 'AC' THEN 1 ELSE 0 END AS activo
                FROM Almacen
                WHERE 1=1 {filtro_suc_alm}
            """
        else:
            # SoftRestaurant Pro - usar nombres de tabla correctos.
            # NOTA: el campo 'tipo' en SoftRestaurant es un código numérico interno, NO un
            # tipo de almacén canónico. El destino Inventario_Almacenes tiene CHECK constraint
            # (GENERAL/BODEGA/CONSUMO/TRANSITO/DEVOLUCIONES/DAÑADOS). Se mapea a 'GENERAL'
            # (default canónico) ya que el origen no expone esa clasificación canónica.
            query_origen = """
                SELECT 
                    CAST(idalmacen AS VARCHAR(50)) AS codigo_almacen,
                    nombre AS nombre_almacen,
                    'GENERAL' AS tipo_almacen,
                    1 AS activo
                FROM almacen
            """
        
        result_origen = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_origen
        )
        
        if result_origen is None:
            return {"status": "ERROR", "error": "Timeout o error de conexión", "records_synced": 0}
        
        if not result_origen:
            return {"status": "OK", "records_synced": 0, "message": "Sin datos en origen"}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        for row in result_origen:
            try:
                codigo = str(row.get('codigo_almacen', ''))[:50]
                nombre = str(row.get('nombre_almacen', ''))[:100]
                tipo = str(row.get('tipo_almacen', 'GENERAL'))[:50]
                activo = 1 if row.get('activo') in (1, '1', 'A', True) else 0
                
                cursor.execute("""
                    MERGE INTO Inventario_Almacenes AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS CodigoAlmacen) AS source 
                    ON target.EmpresaID = source.EmpresaID 
                       AND target.SucursalID = source.SucursalID 
                       AND target.CodigoAlmacen = source.CodigoAlmacen
                    WHEN MATCHED THEN 
                        UPDATE SET NombreAlmacen = %s, TipoAlmacen = %s, Activo = %s, FechaModificacion = GETDATE()
                    WHEN NOT MATCHED THEN 
                        INSERT (EmpresaID, SucursalID, CodigoAlmacen, NombreAlmacen, TipoAlmacen, PermiteCompras, PermiteVentas, Activo, FechaAlta)
                        VALUES (%s, %s, %s, %s, %s, 1, 1, %s, GETDATE());
                """, (
                    empresa_id, sucursal_id, codigo,
                    nombre, tipo, activo,
                    empresa_id, sucursal_id, codigo, nombre, tipo, activo
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando almacen {row.get('codigo_almacen')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"status": "OK", "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error en sync_almacenes: {e}")
        return {"status": "ERROR", "error": str(e), "records_synced": 0}



def sync_existencias_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable
) -> Dict[str, Any]:
    """
    Sincroniza existencias de inventario desde servidor físico a EDARSAHUB.
    Destino: Inventario_Existencias
    
    OPCIÓN B: Usa EmpresaID + SucursalID + AlmacenID + ProductoID como llave.
    NO usa ServerID ni OrigenSistema.
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    system_type = ctx['system_type']
    
    logger.info(f"[SYNC] Iniciando sync existencias: Empresa={empresa_id}, Sucursal={sucursal_id}")
    
    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_origen = """
                SELECT TOP 5000
                    CAST(Ar_Cve_Articulo AS INT) AS producto_id,
                    CAST(Al_Cve_Almacen AS INT) AS almacen_id,
                    ISNULL(Ex_Existencia, 0) AS existencia,
                    ISNULL(Ex_Costo_Promedio, 0) AS costo_promedio
                FROM Existencia E
                WHERE E.Ex_Existencia <> 0
            """
        else:
            # SoftRestaurant Pro - NO tiene tabla "existencias"
            # Las existencias se calculan de movtosalmacen
            # Por ahora retornamos vacío hasta tener el cálculo correcto
            query_origen = """
                SELECT TOP 0 
                    0 AS producto_id,
                    0 AS almacen_id,
                    0 AS existencia,
                    0 AS costo_promedio
            """
            logger.warning(f"[SYNC] SoftRestaurant no tiene tabla 'existencias' directa - se requiere calcular de movtosalmacen")
        
        result_origen = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_origen
        )
        
        if result_origen is None:
            return {"status": "ERROR", "error": "Timeout o error de conexión", "records_synced": 0}
        
        if not result_origen:
            return {"status": "OK", "records_synced": 0, "message": "Sin datos en origen"}
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        records_synced = 0
        for row in result_origen:
            try:
                almacen_id = row.get('almacen_id') or 1
                producto_id = row.get('producto_id') or 0
                existencia = float(row.get('existencia') or 0)
                costo = float(row.get('costo_promedio') or 0)
                
                # MERGE usando llave: EmpresaID + SucursalID + AlmacenID + ProductoID
                cursor.execute("""
                    MERGE INTO Inventario_Existencias AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS AlmacenID, %s AS ProductoID) AS source 
                    ON target.EmpresaID = source.EmpresaID 
                       AND target.SucursalID = source.SucursalID 
                       AND target.AlmacenID = source.AlmacenID 
                       AND target.ProductoID = source.ProductoID
                    WHEN MATCHED THEN 
                        UPDATE SET ExistenciaActual = %s, CostoPromedio = %s, FechaModificacion = GETDATE()
                    WHEN NOT MATCHED THEN 
                        INSERT (EmpresaID, SucursalID, AlmacenID, ProductoID, ExistenciaActual, CostoPromedio, FechaAlta)
                        VALUES (%s, %s, %s, %s, %s, %s, GETDATE());
                """, (
                    empresa_id, sucursal_id, almacen_id, producto_id,
                    existencia, costo,
                    empresa_id, sucursal_id, almacen_id, producto_id, existencia, costo
                ))
                records_synced += 1
            except Exception as e:
                logger.warning(f"[SYNC] Error insertando existencia {row.get('producto_id')}: {e}")
        
        conn.commit()
        conn.close()
        
        return {"status": "OK", "records_synced": records_synced}
        
    except Exception as e:
        logger.error(f"[SYNC] Error en sync_existencias: {e}")
        return {"status": "ERROR", "error": str(e), "records_synced": 0}



# ADVERTENCIA: sync_movimientos_from_server debe usar map_tipo_movimiento_softrestaurant() antes de MERGE.

# sync_movimientos_from_server debe:
# - usar map_tipo_movimiento_softrestaurant(idconcepto)
# - saltar registros con TipoMovimientoID None
# - devolver conceptos_no_mapeados en el resultado
def sync_movimientos_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza movimientos de inventario POS -> Inventario_Movimientos + Detalle.

    REFACTOR Ruta B (int estricta): delega en la capa común
    `core.inventarios.sync_movimientos_canonico`, que usa el RESOLVER CENTRALIZADO
    (producto/almacén/sucursal/tipo) y escribe en el ESQUEMA REAL.
    - Corrige el bug previo (MERGE con columnas inexistentes -> 0 filas).
    - No inventa IDs: lo no resoluble queda en pendientes; descartados=0.
    - Sin hardcode de clasificación (tipo de movimiento vía catálogo DB-driven).
    """
    # Import perezoso para evitar import circular con esta misma capa.
    import os as _os
    from core.inventarios.sync_movimientos_canonico import sync_movimientos_canonico
    # Ventana histórica configurable (backfill). Default 30 días para el job recurrente.
    dias_atras = int(_os.environ.get("SYNC_COMPRAS_MOV_DIAS_ATRAS", "30"))
    return sync_movimientos_canonico(server_info, unidad_info, execute_sql_fn, dias_atras=dias_atras)



def sync_pedidos_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza pedidos de compra desde servidor físico a EDARSAHUB.
    Destino: Compras_Pedidos + Compras_PedidosDetalle

    Llave MERGE Encabezado: EmpresaID + SucursalID + FolioPedido
    Llave MERGE Detalle: PedidoCompraID + ProductoID (o renglon)
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    unidad_negocio_pk = ctx['unidad_negocio_pk']
    system_type = ctx['system_type']

    logger.info(f"[SYNC] Iniciando sync pedidos: Empresa={empresa_id}, Sucursal={sucursal_id}")

    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_encabezado = f"""
                SELECT TOP 500
                    Pc_Folio AS folio_pedido,
                    Pc_Fecha AS fecha_pedido,
                    Pc_Fecha_Requerida AS fecha_requerida,
                    Pc_Total AS total,
                    Pc_Estatus AS estatus,
                    Pc_Observaciones AS observaciones
                FROM Pedido_Compra
                WHERE Pc_Fecha >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
            query_detalle = f"""
                SELECT
                    Pc_Folio AS folio_pedido,
                    Ar_Cve_Articulo AS producto_id,
                    Pcd_Cantidad AS cantidad,
                    Pcd_Precio AS precio_unitario
                FROM Pedido_Compra_Detalle PCD
                INNER JOIN Pedido_Compra PC ON PC.Pc_Cve_Pedido = PCD.Pc_Cve_Pedido
                WHERE PC.Pc_Fecha >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
        else:
            query_encabezado = f"""
                SELECT TOP 500
                    CAST(p.folio AS VARCHAR(50)) AS folio_pedido,
                    p.fechacaptura AS fecha_pedido,
                    p.fecharecepcion AS fecha_requerida,
                    0 AS total,
                    'ACTIVO' AS estatus,
                    '' AS observaciones
                FROM pedidos p
                WHERE p.fechacaptura >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
            query_detalle = f"""
                SELECT
                    CAST(p.folio AS VARCHAR(50)) AS folio_pedido,
                    CAST(d.idinsumo AS INT) AS producto_id,
                    ISNULL(d.cantidad, 0) AS cantidad,
                    ISNULL(d.costo, 0) AS precio_unitario
                FROM pedidos p
                INNER JOIN pedidosdetalle d ON d.idpedido = p.idpedido
                WHERE p.fechacaptura >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """

        # Obtener encabezados
        result_enc = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_encabezado
        )

        if result_enc is None:
            return {"status": "ERROR", "error": "Timeout conexión encabezados", "encabezados_synced": 0, "detalles_synced": 0}

        if not result_enc:
            return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0, "message": "Sin pedidos en origen"}

        # Obtener detalles
        result_det = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_detalle
        ) or []

        conn = get_edarsahub_connection()
        cursor = conn.cursor()

        enc_synced = 0
        det_synced = 0

        for enc in result_enc:
            try:
                folio = str(enc.get('folio_pedido', ''))[:50]
                fecha = enc.get('fecha_pedido')
                total = float(enc.get('total') or 0)

                # MERGE encabezado
                cursor.execute("""
                    MERGE INTO Compras_Pedidos AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS FolioPedido) AS source
                    ON target.EmpresaID = source.EmpresaID
                       AND target.SucursalID = source.SucursalID
                       AND target.FolioPedido = source.FolioPedido
                    WHEN MATCHED THEN
                        UPDATE SET Total = %s, unidad_negocio_pk = %s, ModifiedAt = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (FolioPedido, EmpresaID, SucursalID, unidad_negocio_pk, FechaPedido, SolicitanteUsuarioID,
                                Prioridad, MotivoCompra, EstatusPedidoCompraID, Total, Activo, CreatedAt, TipoCambio, Subtotal, DescuentoTotal, ImpuestoTotal)
                        VALUES (%s, %s, %s, %s, %s, 1, 'MEDIA', 'SYNC', 1, %s, 1, GETDATE(), 1, %s, 0, 0);
                """, (
                    empresa_id, sucursal_id, folio,
                    total, unidad_negocio_pk,
                    folio, empresa_id, sucursal_id, unidad_negocio_pk, fecha, total, total
                ))
                enc_synced += 1

            except Exception as e:
                logger.warning(f"[SYNC] Error insertando pedido {enc.get('folio_pedido')}: {e}")

        # P3-01E FIX: insertar detalles Compras_PedidosDetalle
        if result_det:
            for det in result_det:
                try:
                    folio_det = str(det.get('folio_pedido') or det.get('folio') or '').strip()
                    if not folio_det:
                        continue

                    producto_id = det.get('producto_id') or det.get('ProductoID') or 0
                    cantidad = float(det.get('cantidad') or det.get('Cantidad') or 0)
                    precio = float(det.get('precio_unitario') or det.get('precio') or det.get('costo') or 0)

                    # Buscar PedidoCompraID por folio
                    cursor.execute("""
                        SELECT TOP 1 PedidoCompraID
                        FROM Compras_Pedidos
                        WHERE FolioPedido = %s AND EmpresaID = %s AND SucursalID = %s
                    """, (folio_det, empresa_id, sucursal_id))

                    row = cursor.fetchone()
                    if not row:
                        continue

                    pedido_compra_id = row[0]

                    # Verificar si ya existe el detalle
                    cursor.execute("""
                        SELECT COUNT(*) FROM Compras_PedidosDetalle
                        WHERE PedidoCompraID = %s AND ProductoID = %s
                    """, (pedido_compra_id, producto_id))

                    if cursor.fetchone()[0] > 0:
                        continue

                    # Calcular totales línea
                    subtotal = cantidad * precio
                    tasa_impuesto = 16.0
                    impuesto = subtotal * tasa_impuesto / 100
                    total_linea = subtotal + impuesto

                    # Insertar detalle
                    cursor.execute("""
                        INSERT INTO Compras_PedidosDetalle (
                            PedidoCompraID, Renglon, ProductoID, Cantidad,
                            CantidadAtendida, CantidadCancelada, PrecioEstimado,
                            DescuentoPorcentaje, TasaImpuesto, SubtotalLinea,
                            ImpuestoImporte, TotalLinea, Activo, CreatedAt
                        ) VALUES (
                            %s, %s, %s, %s,
                            0, 0, %s,
                            0, %s, %s,
                            %s, %s, 1, GETDATE()
                        )
                    """, (
                        pedido_compra_id, det_synced + 1, producto_id, cantidad,
                        precio, tasa_impuesto, subtotal,
                        impuesto, total_linea
                    ))
                    det_synced += 1

                except Exception as det_err:
                    logger.warning(f"[SYNC] Error detalle pedido: {det_err}")

            # Actualizar totales de encabezados
            cursor.execute("""
                UPDATE p SET
                    p.Subtotal = ISNULL(d.Subtotal, 0),
                    p.ImpuestoTotal = ISNULL(d.Impuesto, 0),
                    p.Total = ISNULL(d.Total, 0),
                    p.ModifiedAt = GETDATE()
                FROM Compras_Pedidos p
                INNER JOIN (
                    SELECT PedidoCompraID,
                           SUM(ISNULL(SubtotalLinea,0)) AS Subtotal,
                           SUM(ISNULL(ImpuestoImporte,0)) AS Impuesto,
                           SUM(ISNULL(TotalLinea,0)) AS Total
                    FROM Compras_PedidosDetalle
                    GROUP BY PedidoCompraID
                ) d ON d.PedidoCompraID = p.PedidoCompraID
                WHERE p.EmpresaID = %s AND p.SucursalID = %s
                  AND (p.Total = 0 OR p.Total IS NULL)
            """, (empresa_id, sucursal_id))

        conn.commit()
        conn.close()

        return {"status": "OK", "encabezados_synced": enc_synced, "detalles_synced": det_synced}

    except Exception as e:
        logger.error(f"[SYNC] Error en sync_pedidos: {e}")
        return {"status": "ERROR", "error": str(e), "encabezados_synced": 0, "detalles_synced": 0}



def sync_ordenes_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza órdenes de compra desde servidor físico a EDARSAHUB.
    Destino: Compras_Ordenes + Compras_OrdenesDetalle

    Llave MERGE: EmpresaID + SucursalID + FolioOrden
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    unidad_negocio_pk = ctx['unidad_negocio_pk']
    system_type = ctx['system_type']

    logger.info(f"[SYNC] Iniciando sync ordenes: Empresa={empresa_id}, Sucursal={sucursal_id}")

    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_encabezado = f"""
                SELECT TOP 500
                    Oc_Folio AS folio_orden,
                    Oc_Fecha AS fecha_orden,
                    Pv_Cve_Proveedor AS proveedor_id,
                    Oc_Total AS total,
                    Oc_Estatus AS estatus
                FROM Orden_Compra
                WHERE Oc_Fecha >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
        else:
            query_encabezado = f"""
                SELECT TOP 500
                    CAST(o.folio AS VARCHAR(50)) AS folio_orden,
                    o.fechacaptura AS fecha_orden,
                    CAST(o.idproveedor AS INT) AS proveedor_id,
                    0 AS total,
                    'ACTIVO' AS estatus
                FROM ordenescompra o
                WHERE o.fechacaptura >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """

        result_enc = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_encabezado
        )

        if result_enc is None:
            return {"status": "ERROR", "error": "Timeout conexión", "encabezados_synced": 0, "detalles_synced": 0}

        if not result_enc:
            return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0, "message": "Sin ordenes en origen"}

        conn = get_edarsahub_connection()
        cursor = conn.cursor()

        enc_synced = 0

        for enc in result_enc:
            try:
                folio = str(enc.get('folio_orden', ''))[:50]
                fecha = enc.get('fecha_orden')
                proveedor_id = enc.get('proveedor_id') or 1
                total = float(enc.get('total') or 0)

                cursor.execute("""
                    MERGE INTO Compras_Ordenes AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS FolioOrden) AS source
                    ON target.EmpresaID = source.EmpresaID
                       AND target.SucursalID = source.SucursalID
                       AND target.FolioOrden = source.FolioOrden
                    WHEN MATCHED THEN
                        UPDATE SET Total = %s, unidad_negocio_pk = %s, ModifiedAt = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (FolioOrden, EmpresaID, SucursalID, unidad_negocio_pk, FechaOrden, ProveedorID, CompradorUsuarioID,
                                MonedaID, TipoCambio, EstatusOrdenCompraID, Total, Activo, CreatedAt, Subtotal, DescuentoTotal, ImpuestoTotal)
                        VALUES (%s, %s, %s, %s, %s, %s, 1, 1, 1, 1, %s, 1, GETDATE(), %s, 0, 0);
                """, (
                    empresa_id, sucursal_id, folio,
                    total, unidad_negocio_pk,
                    folio, empresa_id, sucursal_id, unidad_negocio_pk, fecha, proveedor_id, total, total
                ))
                enc_synced += 1

            except Exception as e:
                logger.warning(f"[SYNC] Error insertando orden {enc.get('folio_orden')}: {e}")

        conn.commit()
        conn.close()

        return {"status": "OK", "encabezados_synced": enc_synced, "detalles_synced": 0}

    except Exception as e:
        logger.error(f"[SYNC] Error en sync_ordenes: {e}")
        return {"status": "ERROR", "error": str(e), "encabezados_synced": 0, "detalles_synced": 0}



def sync_recepciones_from_server(
    server_info: Dict,
    unidad_info: Dict,
    execute_sql_fn: Callable,
    dias_atras: int = 30,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza recepciones de compra desde servidor físico a EDARSAHUB.
    Origen SR: tabla 'compras' (recepciones de mercancía)
    Destino: Compras_Recepciones + Compras_RecepcionesDetalle

    Llave MERGE: EmpresaID + SucursalID + FolioRecepcion
    """
    ctx = _get_edarsahub_context(server_info, unidad_info)
    empresa_id = ctx['empresa_id']
    sucursal_id = ctx['sucursal_id']
    unidad_negocio_pk = ctx['unidad_negocio_pk']
    system_type = ctx['system_type']

    logger.info(f"[SYNC] Iniciando sync recepciones: Empresa={empresa_id}, Sucursal={sucursal_id}")

    try:
        if 'MPRO' in system_type.upper() or 'MANAGEMENT' in system_type.upper():
            query_encabezado = f"""
                SELECT TOP 500
                    Re_Folio AS folio_recepcion,
                    Re_Fecha AS fecha_recepcion,
                    Pv_Cve_Proveedor AS proveedor_id,
                    Re_Total AS total
                FROM Recepcion
                WHERE Re_Fecha >= DATEADD(DAY, -{dias_atras}, GETDATE())
            """
        else:
            # SoftRestaurant - tabla 'compras' (recepciones de mercancía)
            # NOTA: 'compras' no tiene idalmacen directamente, se debe obtener del movimiento
            query_encabezado = f"""
                SELECT TOP 500
                    CAST(c.idcompra AS VARCHAR(50)) AS folio_recepcion,
                    c.fechaaplicacion AS fecha_recepcion,
                    CAST(c.idproveedor AS INT) AS proveedor_id,
                    ISNULL(c.total, 0) AS total,
                    1 AS almacen_id
                FROM compras c
                WHERE c.fechaaplicacion >= DATEADD(DAY, -{dias_atras}, GETDATE())
                  AND ISNULL(c.cancelado, 0) = 0
            """

        result_enc = execute_sql_fn(
            server_info['host'], server_info['port'], server_info['database'],
            server_info['username'], server_info['password'], query_encabezado
        )

        if result_enc is None:
            return {"status": "ERROR", "error": "Timeout conexión", "encabezados_synced": 0, "detalles_synced": 0}

        if not result_enc:
            return {"status": "OK", "encabezados_synced": 0, "detalles_synced": 0, "message": "Sin recepciones en origen"}

        conn = get_edarsahub_connection()
        cursor = conn.cursor()

        enc_synced = 0

        for enc in result_enc:
            try:
                folio = str(enc.get('folio_recepcion', ''))[:50]
                fecha = enc.get('fecha_recepcion')
                proveedor_id = enc.get('proveedor_id') or 1
                almacen_id = enc.get('almacen_id') or 1
                total = float(enc.get('total') or 0)

                cursor.execute("""
                    MERGE INTO Compras_Recepciones AS target
                    USING (SELECT %s AS EmpresaID, %s AS SucursalID, %s AS FolioRecepcion) AS source
                    ON target.EmpresaID = source.EmpresaID
                       AND target.SucursalID = source.SucursalID
                       AND target.FolioRecepcion = source.FolioRecepcion
                    WHEN MATCHED THEN
                        UPDATE SET Total = %s, unidad_negocio_pk = %s, ModifiedAt = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (FolioRecepcion, EmpresaID, SucursalID, unidad_negocio_pk, AlmacenID, ProveedorID, FechaRecepcion,
                                EstatusRecepcionID, Total, Activo, CreatedAt, Subtotal, ImpuestoTotal, TieneIncidencias)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, 1, GETDATE(), %s, 0, 0);
                """, (
                    empresa_id, sucursal_id, folio,
                    total, unidad_negocio_pk,
                    folio, empresa_id, sucursal_id, unidad_negocio_pk, almacen_id, proveedor_id, fecha, total, total
                ))
                enc_synced += 1

            except Exception as e:
                logger.warning(f"[SYNC] Error insertando recepcion {enc.get('folio_recepcion')}: {e}")

        conn.commit()
        conn.close()

        return {"status": "OK", "encabezados_synced": enc_synced, "detalles_synced": 0}

    except Exception as e:
        logger.error(f"[SYNC] Error en sync_recepciones: {e}")
        return {"status": "ERROR", "error": str(e), "encabezados_synced": 0, "detalles_synced": 0}
