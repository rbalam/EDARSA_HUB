#!/usr/bin/env python3
"""
Poblar detalle canónico de ventas/productos para Inteligencia Comercial.

Guardrails:
- Dry-run por defecto.
- --commit requerido para escribir.
- No usa Sync_Sales.
- No recalcula KPIs.
- No toca frontend, modal ni endpoints.
- Solo escribe días que cuadran contra vw_Comercial_KPIs_Diarios_v2_Runtime.
- Bloquea días con ventas abiertas/runtime overlay cuando --excluir-abiertas está activo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import pymssql
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Optional, Tuple

from core.sql_first.db import get_sql_connection
from core.secret_manager import decrypt_secret, is_encrypted_secret
from core.system_type_utils import SystemType, normalize_system_type


DESTINO = "dbo.Comercial_Inteligencia_VentasDetalleProducto"
RUNTIME = "dbo.vw_Comercial_KPIs_Diarios_v2_Runtime"

TOLERANCIA_VENTAS = Decimal("0.05")


def _query_edarsahub_dicts(sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
    """Consulta EDARSAHUB SQL y devuelve dicts sin depender del scheduler."""
    conn = get_sql_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        cols = [c[0] for c in (cur.description or [])]
        rows = cur.fetchall() or []
        result = []
        for row in rows:
            if isinstance(row, dict):
                result.append(row)
            else:
                result.append({cols[i]: row[i] for i in range(len(cols))})
        cur.close()
        return result
    finally:
        conn.close()


def get_unidades_negocio_pos(
    unidades: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Obtiene el contexto POS mediante la relación canónica:

        dbo.Unidades_Negocio.server_id
            -> dbo.Servidores_Conexiones.id

    No infiere sistema, servidor, sucursal o conexión por nombre.
    No utiliza fallback operativo.
    """
    rows = _query_edarsahub_dicts(
        """
        SELECT
            CONVERT(varchar(36), u.id) AS unidad_pk,
            CONVERT(varchar(50), u.codigo) AS unidad_codigo,
            CONVERT(varchar(200), u.nombre) AS unidad_nombre,

            CONVERT(varchar(36), u.server_id) AS server_id,
            CONVERT(varchar(100), u.system_type)
                AS unidad_system_type,
            CONVERT(varchar(100), u.sucursal_origen_id)
                AS sucursal_origen_id,

            CONVERT(varchar(200), s.nombre)
                AS servidor_nombre,
            CONVERT(varchar(100), s.system_type)
                AS servidor_system_type,
            CONVERT(varchar(50), s.tipo_conexion)
                AS tipo_conexion,

            s.host,
            s.port,
            s.database_name,
            s.username,
            s.password_encrypted

        FROM dbo.Unidades_Negocio AS u

        INNER JOIN dbo.Servidores_Conexiones AS s
            ON s.id = u.server_id

        WHERE ISNULL(u.activo, 1) = 1
          AND ISNULL(s.activo, 1) = 1

        ORDER BY u.codigo
        """
    )

    wanted = {
        str(value).strip().upper()
        for value in (unidades or [])
        if str(value).strip()
    }

    result: List[Dict[str, Any]] = []
    seen_unit_ids = set()
    seen_unit_codes = set()

    for row in rows:
        unit_pk = _s(row.get("unidad_pk"))
        unit_code = _s(row.get("unidad_codigo"))
        unit_name = _s(row.get("unidad_nombre"))
        server_id = _s(row.get("server_id"))

        if not unit_pk:
            raise RuntimeError(
                "Unidad canónica sin UUID"
            )

        if not unit_code:
            raise RuntimeError(
                f"Unidad canónica sin código: unidad_pk={unit_pk}"
            )

        if not unit_name:
            raise RuntimeError(
                f"Unidad canónica sin nombre: unidad={unit_code}"
            )

        if not server_id:
            raise RuntimeError(
                f"Unidad sin server_id canónico: unidad={unit_code}"
            )

        unit_pk_key = unit_pk.lower()
        unit_code_key = unit_code.upper()

        if unit_pk_key in seen_unit_ids:
            raise RuntimeError(
                f"UUID de unidad duplicado: {unit_pk}"
            )

        if unit_code_key in seen_unit_codes:
            raise RuntimeError(
                f"Código de unidad duplicado: {unit_code}"
            )

        seen_unit_ids.add(unit_pk_key)
        seen_unit_codes.add(unit_code_key)

        identities = {
            unit_pk.upper(),
            unit_code.upper(),
            unit_name.upper(),
        }

        if wanted and not (wanted & identities):
            continue

        result.append(dict(row))

    if wanted and not result:
        raise RuntimeError(
            "Ninguna unidad configurada coincide con: "
            + ", ".join(sorted(wanted))
        )

    if not result:
        raise RuntimeError(
            "No existen unidades POS activas con servidor canónico"
        )

    return result


def _secret_value(value: Any) -> str:
    """
    Devuelve secreto usable en memoria.
    No imprime ni persiste valores descifrados.
    """
    raw = _s(value)
    if not raw:
        return ""

    try:
        if is_encrypted_secret(raw):
            return decrypt_secret(raw)
    except Exception as exc:
        raise RuntimeError(f"No se pudo descifrar secreto POS: {type(exc).__name__}")

    return raw


def get_pos_config_for_unidad(
    unidad_row: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Construye el contexto exclusivamente con datos provenientes del JOIN
    canónico de Unidades_Negocio y Servidores_Conexiones.

    No realiza búsquedas secundarias ni inferencias silenciosas.
    """
    unit_pk = _s(unidad_row.get("unidad_pk"))
    unit_code = _s(unidad_row.get("unidad_codigo"))
    unit_name = _s(unidad_row.get("unidad_nombre"))
    server_id = _s(unidad_row.get("server_id"))

    unit_system_raw = _s(
        unidad_row.get("unidad_system_type")
    )
    server_system_raw = _s(
        unidad_row.get("servidor_system_type")
    )

    unit_system = normalize_system_type(
        unit_system_raw
    )
    server_system = normalize_system_type(
        server_system_raw
    )

    if unit_system == SystemType.UNKNOWN.value:
        raise RuntimeError(
            "Unidades_Negocio.system_type ausente o no soportado: "
            f"unidad={unit_code!r} valor={unit_system_raw!r}"
        )

    if server_system == SystemType.UNKNOWN.value:
        raise RuntimeError(
            "Servidores_Conexiones.system_type ausente o no soportado: "
            f"unidad={unit_code!r} "
            f"server_id={server_id!r} "
            f"valor={server_system_raw!r}"
        )

    if unit_system != server_system:
        raise RuntimeError(
            "Inconsistencia de system_type entre unidad y servidor: "
            f"unidad={unit_code!r} "
            f"unidad_system_type={unit_system!r} "
            f"servidor_system_type={server_system!r}"
        )

    connection_type = _s(
        unidad_row.get("tipo_conexion")
    ).upper()

    if not connection_type:
        raise RuntimeError(
            "Servidor sin tipo_conexion: "
            f"unidad={unit_code!r} server_id={server_id!r}"
        )

    if connection_type in {"CORE", "API_LOCAL"}:
        raise RuntimeError(
            "La unidad apunta a una conexión no POS: "
            f"unidad={unit_code!r} "
            f"server_id={server_id!r} "
            f"tipo_conexion={connection_type!r}"
        )

    branch_id = _s(
        unidad_row.get("sucursal_origen_id")
    )

    if (
        unit_system == SystemType.MANAGEMENTPRO.value
        and not branch_id
    ):
        raise RuntimeError(
            "ManagementPro requiere "
            "Unidades_Negocio.sucursal_origen_id: "
            f"unidad={unit_code!r}"
        )

    password = _secret_value(
        unidad_row.get("password_encrypted")
    )

    cfg = {
        "unidad_pk": unit_pk,
        "unidad_codigo": unit_code,
        "unidad_nombre": unit_name,

        "server_id": server_id,
        "servidor_nombre": _s(
            unidad_row.get("servidor_nombre")
        ),
        "sucursal_origen_id": branch_id,

        "system_type": unit_system,
        "tipo_conexion": connection_type,

        "host": unidad_row.get("host"),
        "port": unidad_row.get("port"),
        "database": unidad_row.get("database_name"),
        "username": unidad_row.get("username"),
        "password": password,

        "source": (
            "dbo.Unidades_Negocio.server_id"
            "->dbo.Servidores_Conexiones.id"
        ),
    }

    missing = [
        key
        for key in (
            "unidad_pk",
            "unidad_codigo",
            "unidad_nombre",
            "server_id",
            "system_type",
            "host",
            "port",
            "database",
            "username",
            "password",
        )
        if cfg.get(key) in (None, "")
    ]

    if missing:
        raise RuntimeError(
            "Configuración POS canónica incompleta: "
            f"unidad={unit_code!r} "
            f"server_id={server_id!r} "
            f"faltan={missing}"
        )

    return cfg


def _parse_sql_server_host_port(raw_host: Any, raw_port: Any = None) -> Tuple[str, int, Optional[str]]:
    """
    Normaliza el host canónico guardado en dbo.Servidores_Conexiones.

    Soporta formatos usados por SQL Server / UI:
    - server
    - server,1433
    - server,6669\\instance
    - server\\instance
    - server:1433

    La fuente canónica no se reescribe aquí; el consumidor parsea antes de conectar.
    """
    host = _s(raw_host).strip()
    port = int(raw_port or 1433)
    instance = None

    if "," in host:
        left, right = host.split(",", 1)
        host = left.strip()
        right = right.strip()

        if "\\" in right:
            port_part, instance_part = right.split("\\", 1)
            instance = instance_part.strip() or None
        else:
            port_part = right

        if str(port_part).strip().isdigit():
            port = int(str(port_part).strip())

    if "\\" in host:
        left, instance_part = host.split("\\", 1)
        host = left.strip()
        instance = instance_part.strip() or instance

    if ":" in host and host.count(":") == 1:
        left, port_part = host.split(":", 1)
        if port_part.strip().isdigit():
            host = left.strip()
            port = int(port_part.strip())

    if not host:
        raise RuntimeError("host POS vacío después de parsear configuración canónica")

    return host, port, instance


def get_pos_connection(config: Dict[str, Any]):
    host, port, _instance = _parse_sql_server_host_port(
        config.get("host"),
        config.get("port") or 1433,
    )

    return pymssql.connect(
        server=host,
        port=int(port),
        user=config["username"],
        password=config["password"],
        database=config["database"],
        login_timeout=15,
        timeout=180,
        tds_version="7.0",
        as_dict=True,
    )


def _d(v: Any) -> Decimal:
    if v is None:
        return Decimal("0")
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _as_date(v: Any) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()


def _daterange(inicio: date, fin_exclusivo: date) -> Iterable[date]:
    d = inicio
    while d < fin_exclusivo:
        yield d
        d += timedelta(days=1)


def _money_eq(a: Any, b: Any) -> bool:
    return abs(_d(a) - _d(b)) <= TOLERANCIA_VENTAS


def _int_eq(a: Any, b: Any) -> bool:
    return int(_d(a)) == int(_d(b))


def _first(row: Dict[str, Any], names: List[str], default: Any = None) -> Any:
    lower = {k.lower(): k for k in row.keys()}
    for name in names:
        k = lower.get(name.lower())
        if k is not None:
            return row.get(k)
    return default


def _hash_row(row: Dict[str, Any]) -> str:
    payload = json.dumps(
        {
            k: str(row.get(k))
            for k in sorted(row.keys())
            if k not in {"id", "fecha_sincronizacion", "sync_run_id", "hash_origen"}
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_print(obj: Any) -> None:
    print(json.dumps(obj, default=str, ensure_ascii=False, sort_keys=True))


def _object_columns(conn, object_name: str) -> List[str]:
    cur = conn.cursor(as_dict=True)
    cur.execute(
        """
        SELECT c.name
        FROM sys.columns c
        WHERE c.object_id = OBJECT_ID(%s)
        ORDER BY c.column_id
        """,
        (object_name,),
    )
    return [r["name"] for r in cur.fetchall()]


def _table_has_col(pos_conn, table: str, col: str) -> bool:
    cur = pos_conn.cursor(as_dict=True)
    cur.execute(
        """
        SELECT 1 AS ok
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table, col),
    )
    return bool(cur.fetchone())


def _load_runtime_rows(
    fecha_inicio: date,
    fecha_fin: date,
    unidad: Optional[str],
) -> List[Dict[str, Any]]:
    conn = get_sql_connection()
    try:
        cols = _object_columns(conn, RUNTIME)
        if "fecha_operacion" not in [c.lower() for c in cols]:
            raise RuntimeError(f"{RUNTIME} no expone fecha_operacion")

        unit_candidates = [
            "unidad_negocio_id",
            "unidad_negocio_pk",
            "unidad_negocio_nombre",
            "unidad_id",
            "unidad_codigo",
        ]
        existing_unit_cols = [c for c in cols if c.lower() in unit_candidates]

        where = ["fecha_operacion >= %s", "fecha_operacion < %s"]
        params: List[Any] = [fecha_inicio.isoformat(), fecha_fin.isoformat()]

        if unidad and existing_unit_cols:
            ors = []
            for c in existing_unit_cols:
                ors.append(f"CONVERT(varchar(100), [{c}]) = %s")
                params.append(unidad)
            where.append("(" + " OR ".join(ors) + ")")

        sql = f"""
        SELECT *
        FROM {RUNTIME}
        WHERE {" AND ".join(where)}
        ORDER BY fecha_operacion
        """
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, tuple(params))
        return cur.fetchall() or []
    finally:
        conn.close()


def _row_unit_values(row: Dict[str, Any]) -> set:
    values = set()
    for k in [
        "unidad_negocio_id",
        "unidad_negocio_pk",
        "unidad_negocio_nombre",
        "unidad_id",
        "unidad_codigo",
    ]:
        v = _first(row, [k])
        if v is not None:
            values.add(_s(v).upper())
    return values


def _cfg_values(cfg: Dict[str, Any]) -> set:
    values = set()
    for k in ["unidad", "unidad_codigo", "unidad_nombre", "unidad_pk", "sucursal_origen_id"]:
        v = cfg.get(k)
        if v is not None:
            values.add(_s(v).upper())
    return values


def _runtime_for(runtime_rows: List[Dict[str, Any]], cfg: Dict[str, Any], dia: date) -> Optional[Dict[str, Any]]:
    cfgv = _cfg_values(cfg)
    for row in runtime_rows:
        try:
            if _as_date(_first(row, ["fecha_operacion"])) != dia:
                continue
        except Exception:
            continue
        if _row_unit_values(row) & cfgv:
            return row
    return None


def _runtime_metrics(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lee exclusivamente el contrato canónico de Runtime V2.

    Campos obligatorios:
    - ventas_total
    - tickets_total
    - pax_total

    No acepta campos legacy ni aliases monetarios alternativos.
    """
    required_fields = (
        "ventas_total",
        "tickets_total",
        "pax_total",
    )

    missing = [
        field
        for field in required_fields
        if field not in row or row.get(field) is None
    ]

    if missing:
        raise RuntimeError(
            "Runtime V2 no expone el contrato canónico requerido: "
            f"faltan={missing}"
        )

    ventas_abiertas = _first(
        row,
        [
            "ventas_abiertas",
            "ventas_dia_abiertas",
            "ventas_abiertas_total",
            "ventas_abiertas_runtime",
        ],
        0,
    )

    es_venta_abierta_raw = _first(
        row,
        ["es_venta_abierta"],
        None,
    )
    es_corte_cerrado_raw = _first(
        row,
        ["es_corte_cerrado"],
        None,
    )

    if es_venta_abierta_raw is not None:
        es_abierta = _s(es_venta_abierta_raw).upper() in {
            "1", "TRUE", "SI", "YES"
        }
    elif es_corte_cerrado_raw is not None:
        es_corte_cerrado = _s(es_corte_cerrado_raw).upper() in {
            "1", "TRUE", "SI", "YES"
        }
        es_abierta = not es_corte_cerrado
    else:
        es_abierta = _d(ventas_abiertas) > 0

    return {
        "ventas": _d(row["ventas_total"]),
        "tickets": int(_d(row["tickets_total"])),
        "pax": int(_d(row["pax_total"])),
        "ventas_abiertas": _d(ventas_abiertas),
        "es_abierta": es_abierta,
    }


def _sistema(cfg: Dict[str, Any]) -> str:
    raw_system_type = _s(cfg.get("system_type"))
    normalized = normalize_system_type(raw_system_type)

    if normalized == SystemType.SOFTRESTAURANT.value:
        return SystemType.SOFTRESTAURANT.value

    if normalized == SystemType.MANAGEMENTPRO.value:
        return SystemType.MANAGEMENTPRO.value

    raise RuntimeError(
        "system_type no reconocido o no soportado: "
        f"original={raw_system_type!r} "
        f"normalizado={normalized!r}"
    )


def _unidad_operativa_id_for_window(cfg: Dict[str, Any]) -> str:
    """
    Identificador canónico para Sistema_TurnosOperativosUnidad.
    """
    for key in (
        "unidad_codigo",
        "unidad_negocio_id",
        "unidad_id",
        "codigo",
        "unidad_negocio_pk",
    ):
        value = cfg.get(key)
        if value not in (None, ""):
            value = str(value).strip()
            if value:
                return value

    safe_context = {
        "unidad_pk": cfg.get("unidad_pk"),
        "unidad_codigo": cfg.get("unidad_codigo"),
        "unidad_nombre": cfg.get("unidad_nombre"),
        "server_id": cfg.get("server_id"),
        "system_type": cfg.get("system_type"),
        "sucursal_origen_id": cfg.get("sucursal_origen_id"),
        "source": cfg.get("source"),
    }
    raise RuntimeError(
        f"No se pudo resolver unidad operativa para ventana POS: {safe_context}"
    )


def _soft_operational_datetime_range(cfg: Dict[str, Any], dia: date) -> Tuple[str, str]:
    """Rango diario equivalente al filtro por fecha de turnos.apertura.

    Para un dia, Reporte Ejecutivo equivale a [00:00:00, siguiente 00:00:00).
    """
    inicio = datetime.combine(dia, datetime.min.time())
    if str(cfg.get('unidad_codigo') or '').strip().upper() == 'ESTELAR':
        inicio += timedelta(hours=9)
    fin = inicio + timedelta(days=1)
    return (
        inicio.strftime("%Y-%m-%d %H:%M:%S"),
        fin.strftime("%Y-%m-%d %H:%M:%S"),
    )


def _extract_soft(cfg: Dict[str, Any], dia: date) -> List[Dict[str, Any]]:
    conn = get_pos_connection(cfg)
    if not conn:
        raise RuntimeError(f"sin conexión POS para {cfg.get('unidad_codigo')}")

    try:
        prop_col = "propina" if _table_has_col(conn, "cheques", "propina") else None
        desc_col = None
        for candidate in ["totaldescuentoycortesia", "descuento"]:
            if _table_has_col(conn, "cheques", candidate):
                desc_col = candidate
                break

        prop_expr = f"ISNULL(ch.{prop_col}, 0)" if prop_col else "CAST(0 AS decimal(18,4))"
        desc_expr = f"ISNULL(ch.{desc_col}, 0)" if desc_col else "CAST(0 AS decimal(18,4))"

        fi, ff = _soft_operational_datetime_range(cfg, dia)

        sql = f"""
        WITH h AS (
            SELECT
                ch.folio,
                ch.fecha,
                  ISNULL(ch.cancelado, 0) AS cancelado_origen,
                ISNULL(ch.nopersonas, 0) AS pax_ticket,
                ISNULL(ch.total, 0) AS importe_neto_ticket,
                {prop_expr} AS propina_ticket,
                {desc_expr} AS descuento_ticket
            FROM cheques ch WITH (NOLOCK)
            INNER JOIN turnos tr WITH (NOLOCK)
                ON tr.idturno = ch.idturno
            WHERE tr.apertura >= %s
              AND tr.apertura < %s
              AND ISNULL(ch.cancelado, 0) = 0
        ),
        l AS (
            SELECT
                h.folio,
                h.fecha,
                  h.cancelado_origen,
                h.pax_ticket,
                h.importe_neto_ticket,
                h.propina_ticket,
                h.descuento_ticket,
                CASE
                    WHEN MAX(dc.foliodet) IS NULL THEN 'HEADER_SIN_DETALLE'
                    ELSE COALESCE(NULLIF(CONVERT(varchar(100), dc.idproducto), ''), 'SIN_CODIGO')
                END AS producto_codigo_fuente,
                COALESCE(MAX(CONVERT(varchar(300), p.descripcion)), 'HEADER SIN DETALLE') AS producto_nombre,
                SUM(CAST(ISNULL(dc.cantidad, 0) AS decimal(18,4))) AS cantidad,
                CASE
                    WHEN SUM(CAST(ISNULL(dc.cantidad, 0) AS decimal(18,4))) <> 0
                    THEN SUM(CAST(ISNULL(dc.cantidad, 0) * ISNULL(dc.precio, 0) AS decimal(18,4)))
                         / SUM(CAST(ISNULL(dc.cantidad, 0) AS decimal(18,4)))
                    ELSE MAX(CAST(ISNULL(dc.precio, 0) AS decimal(18,4)))
                END AS precio_unitario,
                SUM(CAST(ISNULL(dc.cantidad, 0) * ISNULL(dc.precio, 0) AS decimal(18,4))) AS importe_bruto
            FROM h
            LEFT JOIN cheqdet dc WITH (NOLOCK)
                ON dc.foliodet = h.folio
            LEFT JOIN productos p WITH (NOLOCK)
                ON p.idproducto = dc.idproducto
            GROUP BY
                h.folio,
                h.fecha,
                  h.cancelado_origen,
                h.pax_ticket,
                h.importe_neto_ticket,
                h.propina_ticket,
                h.descuento_ticket,
                COALESCE(NULLIF(CONVERT(varchar(100), dc.idproducto), ''), 'SIN_CODIGO')
        ),
        t AS (
            SELECT folio, SUM(importe_bruto) AS bruto_ticket
            FROM l
            GROUP BY folio
        )
        SELECT
            CONVERT(varchar(64), l.folio) AS numero_ticket,
            CONCAT('SOFT:', CONVERT(varchar(64), l.folio)) AS id_transaccion,
            l.fecha AS fecha_hora,
              l.cancelado_origen,
              CASE
                  WHEN ISNULL(l.cancelado_origen, 0) = 0 THEN 'ACTIVO'
                  ELSE 'CANCELADO'
              END AS estado_origen,
              CASE
                  WHEN ISNULL(l.cancelado_origen, 0) = 0 THEN 1
                  ELSE 0
              END AS es_kpi_valido,
              CONVERT(varchar(64), l.folio) AS folio_origen,
              CONVERT(varchar(64), l.folio) AS documento_origen,
            l.pax_ticket,
            l.importe_neto_ticket,
            l.propina_ticket,
            l.descuento_ticket,
            l.producto_codigo_fuente,
            l.producto_nombre,
            l.cantidad,
            l.precio_unitario,
            l.importe_bruto,
            CAST(l.importe_bruto AS decimal(18,4)) AS importe_neto
        FROM l
        INNER JOIN t ON t.folio = l.folio
        ORDER BY l.folio, l.producto_codigo_fuente
        """
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, (fi, ff))
        rows = cur.fetchall() or []
        for r in rows:
            r["sistema_origen"] = "SOFTRESTAURANT"
        return _soft_add_ticket_adjustments(rows)
    finally:
        conn.close()


SOFT_AJUSTE_CHEQUE = "__ISCAM_AJUSTE_CHEQUE__"
SOFT_AJUSTE_FRANQUICIA_CERO = "__ISCAM_AJUSTE_FRANQUICIA_CERO__"
SOFT_AJUSTE_ENCABEZADO = "__ISCAM_AJUSTE_ENCABEZADO__"


def _soft_add_ticket_adjustments(src_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Conserva productos reales y hace que el detalle dependa del folio header.

    La poblacion valida nace exclusivamente de ``h`` (cheques validos) y cada linea
    de ``cheqdet`` se une por ``dc.foliodet = h.folio``. No se prorratea ni se crea
    una poblacion de tickets independiente. El total monetario autoritativo es el
    encabezado del mismo folio; cualquier diferencia residual se conserva como una
    linea tecnica de conciliacion ligada al ticket para que el detalle sume
    exactamente al encabezado sin alterar los productos reales.
    """
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for raw in src_rows:
        row = dict(raw)
        key = _s(row.get("id_transaccion"))
        if not key:
            raise RuntimeError("SoftRestaurant: fila sin id_transaccion")
        grouped[key].append(row)

    out: List[Dict[str, Any]] = []
    for ticket_key, items in grouped.items():
        header_values = {_d(row.get("importe_neto_ticket")) for row in items}
        discount_values = {_d(row.get("descuento_ticket")) for row in items}
        if len(header_values) != 1 or len(discount_values) != 1:
            raise RuntimeError(f"SoftRestaurant: encabezado inconsistente en ticket {ticket_key}")

        header_total = next(iter(header_values))
        discount_indicator = next(iter(discount_values))
        product_total = sum((_d(row.get("importe_neto")) for row in items), Decimal("0"))
        delta = header_total - product_total

        out.extend(items)
        if abs(delta) <= TOLERANCIA_VENTAS:
            if delta == Decimal("0"):
                continue
            adjustment = dict(items[0])
            adjustment["producto_codigo_fuente"] = SOFT_AJUSTE_ENCABEZADO
            adjustment["producto_nombre"] = (
                "AJUSTE DE CONCILIACION CONTRA ENCABEZADO DEL TICKET"
            )
            adjustment["cantidad"] = Decimal("0")
            adjustment["precio_unitario"] = Decimal("0")
            adjustment["importe_bruto"] = Decimal("0")
            adjustment["importe_neto"] = delta
            out.append(adjustment)
            continue

        if delta < 0 and discount_indicator > 0:
            adjustment = dict(items[0])
            adjustment["producto_codigo_fuente"] = SOFT_AJUSTE_CHEQUE
            adjustment["producto_nombre"] = "AJUSTE DEL CHEQUE (DESCUENTO / CORTESIA NO ASIGNADO A PRODUCTO)"
            adjustment["cantidad"] = Decimal("0")
            adjustment["precio_unitario"] = Decimal("0")
            adjustment["importe_bruto"] = Decimal("0")
            adjustment["importe_neto"] = delta
            out.append(adjustment)
            continue

        negative_franchise = any(
            _d(row.get("importe_neto")) < 0
            and "FRANQUICIA" in _s(row.get("producto_nombre")).upper()
            for row in items
        )
        if (
            header_total == Decimal("0")
            and product_total < Decimal("0")
            and delta > Decimal("0")
            and negative_franchise
        ):
            adjustment = dict(items[0])
            adjustment["producto_codigo_fuente"] = SOFT_AJUSTE_FRANQUICIA_CERO
            adjustment["producto_nombre"] = "AJUSTE DE CIERRE A CERO (FRANQUICIA)"
            adjustment["cantidad"] = Decimal("0")
            adjustment["precio_unitario"] = Decimal("0")
            adjustment["importe_bruto"] = Decimal("0")
            adjustment["importe_neto"] = delta
            out.append(adjustment)
            continue

        # Un encabezado en cero con detalle monetario no explicado sigue siendo
        # un caso anomalo y se bloquea. La unica excepcion es la franquicia
        # negativa ya resuelta arriba. Esto conserva el guard historico R80C.
        if header_total == Decimal("0"):
            raise RuntimeError(
                f"SoftRestaurant: diferencia no explicada en ticket {ticket_key}; "
                f"productos={product_total}; encabezado={header_total}; delta={delta}; "
                f"indicador_descuento_cortesia={discount_indicator}"
            )

        # El folio del encabezado es el padre y la cifra autoritativa.
        # Conservamos las lineas reales tal como vienen del POS y agregamos una
        # linea tecnica por la diferencia residual del MISMO folio. De esta forma
        # nunca se fabrica una poblacion de detalle independiente del header.
        adjustment = dict(items[0])
        adjustment["producto_codigo_fuente"] = SOFT_AJUSTE_ENCABEZADO
        adjustment["producto_nombre"] = (
            "AJUSTE DE CONCILIACION CONTRA ENCABEZADO DEL TICKET"
        )
        adjustment["cantidad"] = Decimal("0")
        adjustment["precio_unitario"] = Decimal("0")
        adjustment["importe_bruto"] = Decimal("0")
        adjustment["importe_neto"] = delta
        out.append(adjustment)

    return out


def _mpro_operational_datetime_range(
    cfg: Dict[str, Any],
    dia: date,
) -> Tuple[str, str]:
    """
    Resuelve el rango fuente aplicable a ManagementPro.

    Vn_Fecha es datetime, pero MPRO almacena la fecha comercial con
    hora 00:00:00. Por ello no puede aplicarse una ventana horaria:
    hacerlo desplaza la extracción al día calendario siguiente.

    fecha_operacion sigue siendo la atribución canónica en EDARSAHUB.
    """
    del cfg

    inicio = datetime.combine(
        dia,
        datetime.min.time(),
    )

    fin = inicio + timedelta(days=1)

    return (
        inicio.strftime("%Y-%m-%d %H:%M:%S"),
        fin.strftime("%Y-%m-%d %H:%M:%S"),
    )

def _extract_mpro(cfg: Dict[str, Any], dia: date) -> List[Dict[str, Any]]:
    suc = cfg.get("sucursal_origen_id")
    if not suc:
        raise RuntimeError("MPRO requiere sucursal_origen_id")

    conn = get_pos_connection(cfg)
    if not conn:
        raise RuntimeError(f"sin conexión POS para {cfg.get('unidad_codigo')}")

    try:
        fi, ff = _mpro_operational_datetime_range(cfg, dia)

        sql = """
        WITH h AS (
            SELECT
                v.Vn_Folio,
                v.Vn_Documento,
                v.Vn_Fecha,
                v.Sc_Cve_Sucursal,
                  ISNULL(v.Es_Cve_Estado, '') AS estado_origen,
                ISNULL(c.Co_Personas, 0) AS pax_ticket,
                ISNULL(v.Vn_Precio_Neto_Importe, 0) AS importe_neto_ticket,
                ISNULL(c.Co_Propina, 0) AS propina_ticket,
                CAST(0 AS decimal(18,4)) AS descuento_comanda,
                CAST(0 AS decimal(18,4)) AS descuento_ticket
            FROM Venta_Encabezado v WITH (NOLOCK)
            LEFT JOIN Comanda c WITH (NOLOCK)
                ON c.Co_Folio = v.Vn_Documento
               AND c.Sc_Cve_Sucursal = v.Sc_Cve_Sucursal
            WHERE CONVERT(date, v.Vn_Fecha) >= CONVERT(date, %s)
              AND CONVERT(date, v.Vn_Fecha) < CONVERT(date, %s)
              AND v.Sc_Cve_Sucursal = %s
              AND ISNULL(v.Vn_Tabla, '') = 'Comanda'
              AND ISNULL(v.Es_Cve_Estado, '') IN ('AC', 'FA', 'CA')
        ),
        l AS (
            SELECT
                h.Vn_Folio,
                h.Vn_Documento,
                h.Vn_Fecha,
                  h.estado_origen,
                h.pax_ticket,
                h.importe_neto_ticket,
                h.propina_ticket,
                h.descuento_comanda,
                h.descuento_ticket,
                CASE
                    WHEN MAX(d.Co_Folio) IS NULL THEN 'HEADER_SIN_DETALLE'
                    ELSE COALESCE(NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''), 'SIN_CODIGO')
                END AS producto_codigo_fuente,
                COALESCE(MAX(CONVERT(varchar(300), d.Cd_Concepto)), 'HEADER SIN DETALLE') AS producto_nombre,
                SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) AS cantidad,
                CASE
                    WHEN SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) <> 0
                    THEN SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4)))
                         / SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4)))
                    ELSE MAX(CAST(ISNULL(d.Cd_Precio, 0) AS decimal(18,4)))
                END AS precio_unitario,
                SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto
            FROM h
            LEFT JOIN Comanda_Detalle d WITH (NOLOCK)
                ON d.Co_Folio = h.Vn_Documento
               AND ISNULL(d.Es_Cve_Estado, '') IN ('AC', 'FA')
            GROUP BY
                h.Vn_Folio,
                h.Vn_Documento,
                h.Vn_Fecha,
                  h.estado_origen,
                h.pax_ticket,
                h.importe_neto_ticket,
                h.propina_ticket,
                h.descuento_comanda,
                h.descuento_ticket,
                COALESCE(NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''), 'SIN_CODIGO')
        ),
        t AS (
            SELECT Vn_Folio, SUM(importe_bruto) AS bruto_ticket
            FROM l
            GROUP BY Vn_Folio
        )
        SELECT
            CONVERT(varchar(64), l.Vn_Folio) AS numero_ticket,
            CONCAT('MPRO:', %s, ':', CONVERT(varchar(64), l.Vn_Folio)) AS id_transaccion,
            l.Vn_Fecha AS fecha_hora,
              CASE
                  WHEN ISNULL(l.estado_origen, '') = 'CA' THEN 1
                  ELSE 0
              END AS cancelado_origen,
              l.estado_origen,
              CASE
                  WHEN ISNULL(l.estado_origen, '') IN ('AC', 'FA') THEN 1
                  ELSE 0
              END AS es_kpi_valido,
              CONVERT(varchar(64), l.Vn_Folio) AS folio_origen,
              CONVERT(varchar(64), l.Vn_Documento) AS documento_origen,
            l.pax_ticket,
            l.importe_neto_ticket,
            l.propina_ticket,
            l.descuento_comanda,
            l.descuento_ticket,
            l.producto_codigo_fuente,
            l.producto_nombre,
            l.cantidad,
            l.precio_unitario,
            l.importe_bruto,
            CASE
                WHEN ISNULL(t.bruto_ticket, 0) <> 0
                THEN CAST(l.importe_bruto * l.importe_neto_ticket / t.bruto_ticket AS decimal(18,4))
                ELSE CAST(0 AS decimal(18,4))
            END AS importe_neto
        FROM l
        INNER JOIN t ON t.Vn_Folio = l.Vn_Folio
        ORDER BY l.Vn_Folio, l.producto_codigo_fuente
        """
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, (fi, ff, str(suc), str(suc)))
        rows = cur.fetchall() or []
        for r in rows:
            r["sistema_origen"] = "MPRO"
        return _prorratear_mpro_por_ticket(rows)
    finally:
        conn.close()




PRORRATEO_Q4 = Decimal("0.0001")


def _q4(value: Any) -> Decimal:
    return _d(value).quantize(
        PRORRATEO_Q4,
        rounding=ROUND_HALF_UP,
    )


def _mpro_row_es_kpi_valido(row: Dict[str, Any]) -> bool:
    raw = _s(_first(row, ["es_kpi_valido"], 1)).upper()
    return raw not in {"0", "FALSE", "NO", "NONE", ""}


def _prorratear_mpro_por_ticket(
    src_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Distribuye la venta final MPRO entre productos usando el header canónico.

    Venta_Encabezado.Vn_Precio_Neto_Importe es la cifra final autoritativa.
    Comanda_Detalle solo aporta la estructura/proporción de productos; su importe
    bruto y Co_Descuento_Importe no pueden bloquear el detalle cuando existen
    ajustes finales que no están representados como descuento de la comanda.
    """
    rows = [dict(row) for row in src_rows]
    grouped: Dict[str, List[Tuple[int, Dict[str, Any]]]] = defaultdict(list)

    for position, row in enumerate(rows):
        if not _mpro_row_es_kpi_valido(row):
            continue

        ticket_key = _s(row.get("id_transaccion"))
        if not ticket_key:
            raise RuntimeError("MPRO: fila valida sin id_transaccion")

        grouped[ticket_key].append((position, row))

    for ticket_key, items in grouped.items():
        net_values = {_q4(row.get("importe_neto_ticket")) for _, row in items}
        if len(net_values) != 1:
            raise RuntimeError(
                f"MPRO: venta neta inconsistente en ticket {ticket_key}"
            )

        target_net = next(iter(net_values))
        if target_net < 0:
            raise RuntimeError(f"MPRO: venta neta negativa en ticket {ticket_key}")

        gross_values = [_q4(row.get("importe_bruto")) for _, row in items]
        if any(value < 0 for value in gross_values):
            raise RuntimeError(f"MPRO: importe bruto negativo en ticket {ticket_key}")

        gross_total = _q4(sum(gross_values, Decimal("0")))
        if gross_total <= 0:
            # Un ticket final de importe cero no requiere una base monetaria de
            # prorrateo. Conservamos sus líneas reales con importe neto cero para
            # mantener ticket/PAX y estructura de producto sin inventar venta.
            # Para cualquier encabezado positivo sin base monetaria se conserva
            # el bloqueo fail-closed de abajo.
            if target_net == Decimal("0.0000"):
                for _, row in items:
                    row["importe_neto"] = Decimal("0.0000")
                    row["descuento_prorrateado"] = Decimal("0.0000")
                continue

            header_only = all(
                _s(row.get("producto_codigo_fuente")).upper() == "HEADER_SIN_DETALLE"
                for _, row in items
            )
            if not header_only:
                raise RuntimeError(
                    f"MPRO: ticket sin detalle monetario distribuible: {ticket_key}"
                )

            # El encabezado final existe pero el POS no expone líneas de producto.
            # No se inventa producto: se conserva el ticket como ajuste técnico,
            # excluido de vistas de productos por el prefijo __ISCAM_AJUSTE_.
            for index, (_, row) in enumerate(items):
                line_net = target_net if index == 0 else Decimal("0")
                row["producto_codigo_fuente"] = SOFT_AJUSTE_ENCABEZADO
                row["producto_nombre"] = "AJUSTE MPRO: HEADER SIN DETALLE DE PRODUCTO"
                row["cantidad"] = Decimal("0")
                row["precio_unitario"] = Decimal("0")
                row["importe_bruto"] = line_net
                row["importe_neto"] = line_net
                row["descuento_prorrateado"] = Decimal("0")
            continue

        allocations: List[Decimal] = []
        remainders: List[Decimal] = []

        for gross in gross_values:
            raw = target_net * gross / gross_total
            base = raw.quantize(PRORRATEO_Q4, rounding=ROUND_DOWN)
            allocations.append(base)
            remainders.append(raw - base)

        residual = _q4(target_net - sum(allocations, Decimal("0")))
        residual_units = int(
            (residual / PRORRATEO_Q4).to_integral_value(
                rounding=ROUND_HALF_UP
            )
        )

        if residual_units < 0 or residual_units > len(items):
            raise RuntimeError(
                f"MPRO: residuo de prorrateo invalido en ticket {ticket_key}"
            )

        ordered_indexes = sorted(
            range(len(items)),
            key=lambda index: (
                -remainders[index],
                _s(items[index][1].get("producto_codigo_fuente")),
                _s(items[index][1].get("producto_nombre")),
                items[index][0],
            ),
        )

        for index in ordered_indexes[:residual_units]:
            allocations[index] += PRORRATEO_Q4

        allocated_total = _q4(sum(allocations, Decimal("0")))
        if allocated_total != target_net:
            raise RuntimeError(
                f"MPRO: venta neta distribuida no concilia en ticket {ticket_key}"
            )

        for index, (_, row) in enumerate(items):
            line_net = _q4(allocations[index])
            row["descuento_prorrateado"] = _q4(gross_values[index] - line_net)
            row["importe_neto"] = line_net

    return rows

def _materialize_rows(cfg: Dict[str, Any], dia: date, src_rows: List[Dict[str, Any]], run_id: str) -> List[Dict[str, Any]]:
    seen_ticket = set()
    out: List[Dict[str, Any]] = []

    for r in src_rows:
        ticket_key = _s(r.get("id_transaccion"))
        first_for_ticket = ticket_key not in seen_ticket
        seen_ticket.add(ticket_key)

        cancelado_raw = _first(r, ["cancelado_origen"], None)
        cancelado_origen = None
        if cancelado_raw is not None:
            cancelado_origen = _s(cancelado_raw).upper() in {"1", "TRUE", "SI", "YES"}

        es_kpi_raw = _s(_first(r, ["es_kpi_valido"], 1)).upper()
        es_kpi_valido = es_kpi_raw not in {"0", "FALSE", "NO", "NONE", ""}

        cantidad = _d(r.get("cantidad"))
        precio_unitario = _d(r.get("precio_unitario"))
        importe_bruto = _d(r.get("importe_bruto"))
        importe_neto = _d(r.get("importe_neto"))

        if not es_kpi_valido:
            cantidad = Decimal("0")
            precio_unitario = Decimal("0")
            importe_bruto = Decimal("0")
            importe_neto = Decimal("0")

        row = {
            "id": str(uuid.uuid4()),
            "unidad_negocio_id": _s(cfg.get("unidad_codigo") or cfg.get("unidad") or cfg.get("unidad_pk")),
            "unidad_negocio_nombre": _s(cfg.get("unidad_nombre") or cfg.get("unidad_codigo")),
            "server_id": _s(cfg.get("server_id")),
            "sucursal_id": _s(cfg.get("sucursal_origen_id")),
            "sucursal_nombre": _s(cfg.get("unidad_nombre") or cfg.get("unidad_codigo")),
            "sistema_origen": _s(r.get("sistema_origen")),
            "fecha_operacion": dia,
            "fecha_hora": r.get("fecha_hora"),
            "numero_ticket": _s(r.get("numero_ticket")),
            "id_transaccion": _s(r.get("id_transaccion")),
            "estado_origen": _s(r.get("estado_origen")),
            "cancelado_origen": cancelado_origen,
            "es_kpi_valido": es_kpi_valido,
            "folio_origen": _s(r.get("folio_origen") or r.get("numero_ticket")),
            "documento_origen": _s(r.get("documento_origen") or r.get("numero_ticket")),
            "fuente_original": _s(r.get("sistema_origen")),
            "producto_codigo_fuente": _s(r.get("producto_codigo_fuente")) or "SIN_CODIGO",
            "producto_id": None,
            "producto_nombre": _s(r.get("producto_nombre"))[:300],
            "familia_id": None,
            "familia_nombre": None,
            "subfamilia_id": None,
            "subfamilia_nombre": None,
            "casa": None,
            "porcentaje_alcohol": None,
            "es_alcohol": None,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "importe_bruto": importe_bruto,
            "importe_neto": importe_neto,
            "descuento": importe_bruto - importe_neto,
            "propina": _d(r.get("propina_ticket")) if first_for_ticket and es_kpi_valido else Decimal("0"),
            "pax": int(_d(r.get("pax_ticket"))) if first_for_ticket and es_kpi_valido else None,
            "sync_run_id": run_id,
            "hash_origen": None,
            "fecha_sincronizacion": datetime.utcnow(),
            "activo": True,
        }
        row["hash_origen"] = _hash_row(row)
        out.append(row)

    return out


def _validate(src_rows: List[Dict[str, Any]], runtime: Dict[str, Any]) -> Dict[str, Any]:
    tickets: Dict[str, Dict[str, Any]] = {}
    detalle_por_ticket: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for r in src_rows:
        es_kpi_raw = _s(_first(r, ["es_kpi_valido"], 1)).upper()
        if es_kpi_raw in {"0", "FALSE", "NO", "NONE", ""}:
            continue

        k = _s(r.get("id_transaccion"))
        if k not in tickets:
            tickets[k] = {
                "venta": _d(r.get("importe_neto_ticket")),
                "pax": int(_d(r.get("pax_ticket"))),
            }
        detalle_por_ticket[k] += _d(r.get("importe_neto"))

    ventas_por_ticket = sum((v["venta"] for v in tickets.values()), Decimal("0"))
    ventas_detalle = sum(detalle_por_ticket.values(), Decimal("0"))
    pax = sum(v["pax"] for v in tickets.values())
    tickets_total = len(tickets)
    diferencias = []
    for key, ticket in tickets.items():
        detalle = detalle_por_ticket.get(key, Decimal("0"))
        if not _money_eq(detalle, ticket["venta"]):
            diferencias.append({
                "id_transaccion": key,
                "encabezado": ticket["venta"],
                "detalle": detalle,
                "delta": detalle - ticket["venta"],
            })

    ventas_runtime = runtime["ventas"]
    tickets_runtime = runtime["tickets"]
    pax_runtime = runtime["pax"]

    ok = (
        _money_eq(ventas_por_ticket, ventas_runtime)
        and _money_eq(ventas_detalle, ventas_runtime)
        and not diferencias
        and _int_eq(tickets_total, tickets_runtime)
        and _int_eq(pax, pax_runtime)
    )

    return {
        "ok": ok,
        "ventas_runtime": ventas_runtime,
        "ventas_por_ticket": ventas_por_ticket,
        "ventas_detalle": ventas_detalle,
        "delta_ventas": ventas_por_ticket - ventas_runtime,
        "delta_detalle": ventas_detalle - ventas_runtime,
        "tickets_runtime": tickets_runtime,
        "tickets_por_ticket": tickets_total,
        "delta_tickets": tickets_total - tickets_runtime,
        "pax_runtime": pax_runtime,
        "pax_por_ticket": pax,
        "delta_pax": pax - pax_runtime,
        "tickets_no_conciliados": diferencias[:20],
        "lineas_producto_y_ajustes": len(src_rows),
    }


def _insert_rows(rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0

    conn = get_sql_connection()
    try:
        conn.autocommit(False)
        cur = conn.cursor()

        unidad = rows[0]["unidad_negocio_id"]
        fecha = rows[0]["fecha_operacion"]
        sistema = rows[0]["sistema_origen"]

        cur.execute(
            f"""
            DELETE FROM {DESTINO}
            WHERE unidad_negocio_id = %s
              AND fecha_operacion = %s
              AND sistema_origen = %s
            """,
            (unidad, fecha.isoformat(), sistema),
        )

        insert_sql = f"""
        INSERT INTO {DESTINO} (
            id,
            unidad_negocio_id,
            unidad_negocio_nombre,
            server_id,
            sucursal_id,
            sucursal_nombre,
            sistema_origen,
            fecha_operacion,
            fecha_hora,
            numero_ticket,
            id_transaccion,
            estado_origen,
            cancelado_origen,
            es_kpi_valido,
            folio_origen,
            documento_origen,
            fuente_original,
            producto_codigo_fuente,
            producto_id,
            producto_nombre,
            familia_id,
            familia_nombre,
            subfamilia_id,
            subfamilia_nombre,
            casa,
            porcentaje_alcohol,
            es_alcohol,
            cantidad,
            precio_unitario,
            importe_bruto,
            importe_neto,
            descuento,
            propina,
            pax,
            sync_run_id,
            hash_origen,
            fecha_sincronizacion,
            activo
        ) VALUES (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s
        )
        """

        for r in rows:
            cur.execute(
                insert_sql,
                (
                    r["id"],
                    r["unidad_negocio_id"],
                    r["unidad_negocio_nombre"],
                    r["server_id"],
                    r["sucursal_id"],
                    r["sucursal_nombre"],
                    r["sistema_origen"],
                    r["fecha_operacion"].isoformat(),
                    r["fecha_hora"],
                    r["numero_ticket"],
                    r["id_transaccion"],
                    r["estado_origen"],
                    None if r["cancelado_origen"] is None else (1 if r["cancelado_origen"] else 0),
                    1 if r["es_kpi_valido"] else 0,
                    r["folio_origen"],
                    r["documento_origen"],
                    r["fuente_original"],
                    r["producto_codigo_fuente"],
                    r["producto_id"],
                    r["producto_nombre"],
                    r["familia_id"],
                    r["familia_nombre"],
                    r["subfamilia_id"],
                    r["subfamilia_nombre"],
                    r["casa"],
                    r["porcentaje_alcohol"],
                    r["es_alcohol"],
                    r["cantidad"],
                    r["precio_unitario"],
                    r["importe_bruto"],
                    r["importe_neto"],
                    r["descuento"],
                    r["propina"],
                    r["pax"],
                    r["sync_run_id"],
                    r["hash_origen"],
                    r["fecha_sincronizacion"],
                    1 if r["activo"] else 0,
                ),
            )

        conn.commit()
        return len(rows)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def sync_detalle_producto_canonico_dia(
    cfg: Dict[str, Any],
    dia: date,
    runtime_row: Dict[str, Any],
    run_id: str,
    commit: bool = False,
    excluir_abiertas: bool = True,
) -> Dict[str, Any]:
    """
    Sincroniza el detalle canónico de producto para una unidad y un día
    operativo completos.

    Reutiliza exactamente los contratos existentes de extracción POS,
    validación contra Runtime V2, materialización e inserción.

    No descubre unidades.
    No calcula rangos.
    No infiere configuración.
    No acepta días sin Runtime canónico.
    """

    sistema = _sistema(cfg)
    rm = _runtime_metrics(runtime_row)

    if excluir_abiertas and (
        rm["ventas_abiertas"] > 0
        or rm["es_abierta"]
    ):
        return {
            "status": "NO_PROBAR_ABIERTO_REAL",
            "unidad": cfg.get("unidad_codigo"),
            "fecha_operacion": dia,
            "ventas_runtime": rm["ventas"],
            "ventas_abiertas_runtime": rm["ventas_abiertas"],
            "tickets_runtime": rm["tickets"],
            "pax_runtime": rm["pax"],
            "filas_insertadas": 0,
        }

    if sistema == SystemType.SOFTRESTAURANT.value:
        src_rows = _extract_soft(cfg, dia)
    elif sistema == SystemType.MANAGEMENTPRO.value:
        src_rows = _extract_mpro(cfg, dia)
    else:
        raise RuntimeError(
            "Sistema POS no soportado para extracción: "
            f"{sistema!r}"
        )

    validation = _validate(src_rows, rm)

    status = (
        "OK_HEADER_CANONICO"
        if validation["ok"]
        else "NO_CUADRA_REVISAR"
    )

    item = {
        "status": status,
        "unidad": cfg.get("unidad_codigo"),
        "unidad_nombre": cfg.get("unidad_nombre"),
        "sistema": sistema,
        "fecha_operacion": dia,
        **validation,
    }

    if status != "OK_HEADER_CANONICO":
        item["filas_insertadas"] = 0
        return item

    rows = _materialize_rows(
        cfg,
        dia,
        src_rows,
        run_id,
    )

    item["filas_destino_preparadas"] = len(rows)

    if commit:
        item["filas_insertadas"] = _insert_rows(rows)
    else:
        item["filas_insertadas"] = 0

    return item


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unidad", default=None)
    ap.add_argument("--fecha-inicio", required=True)
    ap.add_argument("--fecha-fin", required=True, help="Fecha fin exclusiva YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true", default=False)
    ap.add_argument("--commit", action="store_true", default=False)
    ap.add_argument("--solo-ok-runtime", action="store_true", default=True)
    ap.add_argument("--excluir-abiertas", action="store_true", default=True)
    args = ap.parse_args()

    fecha_inicio = _as_date(args.fecha_inicio)
    fecha_fin = _as_date(args.fecha_fin)
    if fecha_fin <= fecha_inicio:
        raise SystemExit("ERROR: --fecha-fin debe ser mayor que --fecha-inicio")

    run_id = f"canonico_detalle_{datetime.utcnow():%Y%m%d_%H%M%S}"
    modo = "COMMIT" if args.commit else "DRY_RUN"

    print("===== POBLAR DETALLE PRODUCTO CANONICO =====")
    _safe_print(
        {
            "modo": modo,
            "run_id": run_id,
            "unidad": args.unidad,
            "fecha_inicio": fecha_inicio,
            "fecha_fin_exclusivo": fecha_fin,
            "destino": DESTINO,
            "runtime": RUNTIME,
        }
    )

    runtime_rows = _load_runtime_rows(fecha_inicio, fecha_fin, args.unidad)
    unidades_raw = get_unidades_negocio_pos([args.unidad] if args.unidad else None)

    total_ok = 0
    total_blocked = 0
    total_insertadas = 0
    resumen: List[Dict[str, Any]] = []

    for unidad_row in unidades_raw:
        cfg = get_pos_config_for_unidad(unidad_row)
        if not cfg:
            _safe_print({"status": "SIN_CONFIG_POS", "unidad": unidad_row})
            total_blocked += 1
            continue

        sistema = _sistema(cfg)

        for dia in _daterange(fecha_inicio, fecha_fin):
            rt = _runtime_for(runtime_rows, cfg, dia)
            if not rt:
                item = {
                    "status": "SIN_RUNTIME",
                    "unidad": cfg.get("unidad_codigo"),
                    "fecha_operacion": dia,
                }
                resumen.append(item)
                _safe_print(item)
                total_blocked += 1
                continue

            try:
                item = sync_detalle_producto_canonico_dia(
                    cfg=cfg,
                    dia=dia,
                    runtime_row=rt,
                    run_id=run_id,
                    commit=args.commit,
                    excluir_abiertas=args.excluir_abiertas,
                )

                resumen.append(item)
                _safe_print(item)

                if item["status"] == "OK_HEADER_CANONICO":
                    total_ok += 1
                    total_insertadas += int(
                        item.get("filas_insertadas") or 0
                    )
                else:
                    total_blocked += 1

            except Exception as exc:
                item = {
                    "status": "ERROR",
                    "unidad": cfg.get("unidad_codigo"),
                    "fecha_operacion": dia,
                    "error": str(exc),
                }
                resumen.append(item)
                _safe_print(item)
                total_blocked += 1

    print("===== RESUMEN =====")
    _safe_print(
        {
            "modo": modo,
            "ok_header_canonico": total_ok,
            "bloqueados_o_error": total_blocked,
            "filas_insertadas": total_insertadas,
            "run_id": run_id,
        }
    )

    if args.commit and total_blocked > 0:
        print("ADVERTENCIA: hubo días bloqueados; solo se escribieron días OK_HEADER_CANONICO.")

    return 1 if total_blocked > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
