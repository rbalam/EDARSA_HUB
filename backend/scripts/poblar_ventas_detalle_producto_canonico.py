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
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple

from core.sql_first.db import get_sql_connection


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


def get_unidades_negocio_pos(unidades: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Resuelve unidades POS desde dbo.Unidades_Negocio.
    No usa scheduler. No imprime secretos.
    """
    rows = _query_edarsahub_dicts("SELECT * FROM dbo.Unidades_Negocio WITH (NOLOCK)")

    wanted = {str(u).strip().upper() for u in (unidades or []) if str(u).strip()}
    out: List[Dict[str, Any]] = []

    for r in rows:
        codigo = _s(_first(r, ["codigo", "unidad_codigo", "Codigo", "UnidadCodigo", "id", "unidad_negocio_id"]))
        nombre = _s(_first(r, ["nombre", "unidad_nombre", "Nombre", "UnidadNegocio", "unidad_negocio_nombre"], codigo))
        unidad_id = _first(r, ["id", "unidad_id", "unidad_negocio_id", "UnidadNegocioID"], codigo)
        server_id = _s(_first(r, ["server_id", "ServerID", "servidor_id", "ServidorID"]))
        sucursal = _s(_first(r, ["sucursal_origen_id", "SucursalOrigenID", "sucursal_id", "SucursalID"]))
        activo = _first(r, ["activo", "Activo", "is_active"], 1)

        try:
            activo_bool = bool(int(activo))
        except Exception:
            activo_bool = bool(activo)

        if not activo_bool:
            continue

        if not server_id:
            continue

        keys = {codigo.upper(), nombre.upper(), str(unidad_id).strip().upper()}
        if wanted and not (keys & wanted):
            continue

        system_type = _s(_first(r, ["system_type", "sistema_origen", "SistemaOrigen", "tipo_sistema", "TipoSistema"]))
        if not system_type:
            system_type = "MPRO" if codigo.upper() in {"130QRO", "ORIGEN"} else "SOFTRESTAURANT"

        out.append({
            "unidad_id": unidad_id,
            "unidad_codigo": codigo,
            "unidad_nombre": nombre,
            "server_id": server_id,
            "sucursal_origen_id": sucursal,
            "system_type": system_type.upper(),
            "raw": r,
        })

    return out


def get_pos_config_for_unidad(unidad_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resuelve conexión POS desde dbo.Servidores_Conexiones.
    No usa scheduler. No imprime secretos.
    """
    server_id = _s(unidad_row.get("server_id"))
    if not server_id:
        raise RuntimeError(f"Unidad sin server_id: {unidad_row}")

    rows = _query_edarsahub_dicts("SELECT * FROM dbo.Servidores_Conexiones WITH (NOLOCK)")

    selected = None
    for r in rows:
        rid = _s(_first(r, ["id", "server_id", "ServerID", "servidor_id", "ServidorID"]))
        if rid == server_id:
            selected = r
            break

    if not selected:
        raise RuntimeError(f"Servidor no encontrado en Servidores_Conexiones: {server_id}")

    cfg = {
        "server_id": server_id,
        "host": _first(selected, ["host", "Host", "servidor", "Servidor", "server", "Server", "ip", "IP"]),
        "port": _first(selected, ["port", "Port", "puerto", "Puerto"], 1433),
        "database": _first(selected, ["database", "Database", "base_datos", "BaseDatos", "database_name", "db_name", "nombre_bd"]),
        "username": _first(selected, ["username", "Username", "usuario", "Usuario", "user", "User", "db_user"]),
        "password": _first(selected, [
            "password", "Password",
            "contrasena", "Contrasena",
            "contraseña", "Contraseña",
            "clave", "Clave",
            "pwd", "PWD",
            "db_password", "DB_PASSWORD",
            "password_db", "PasswordDB",
            "sql_password", "SQL_PASSWORD",
            "pass", "Pass",
            "password_conexion", "PasswordConexion",
            "clave_conexion", "ClaveConexion",
            "conexion_password", "ConexionPassword",
        ]),
        "system_type": _s(unidad_row.get("system_type") or _first(selected, ["system_type", "tipo_sistema", "sistema", "Sistema"])).upper(),
        "sucursal_origen_id": unidad_row.get("sucursal_origen_id"),
        "unidad_codigo": unidad_row.get("unidad_codigo"),
        "unidad_nombre": unidad_row.get("unidad_nombre"),
        "source": "dbo.Servidores_Conexiones",
    }

    missing = [k for k in ["host", "database", "username", "password"] if not cfg.get(k)]
    if missing:
        raise RuntimeError(f"Config POS incompleta server_id={server_id}; faltan={missing}")

    if not cfg["system_type"]:
        cfg["system_type"] = "MPRO" if str(unidad_row.get("unidad_codigo")).upper() in {"130QRO", "ORIGEN"} else "SOFTRESTAURANT"

    return cfg


def get_pos_connection(config: Dict[str, Any]):
    """Conexión real read-only al POS origen."""
    return pymssql.connect(
        server=config["host"],
        port=int(config.get("port") or 1433),
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
    ventas = _first(
        row,
        [
            "ventas_total",
            "ventas_con_iva",
            "venta_total",
            "ventas",
            "ventas_sin_propina",
            "venta",
        ],
        0,
    )
    tickets = _first(row, ["tickets_total", "cheques_total", "tickets", "cheques"], 0)
    pax = _first(row, ["pax_total", "pax"], 0)
    abiertas = _first(
        row,
        [
            "ventas_abiertas",
            "ventas_dia_abiertas",
            "ventas_abiertas_total",
            "ventas_abiertas_runtime",
        ],
        0,
    )
    fuente = " ".join(str(v) for v in row.values() if v is not None)
    es_abierta = "Comercial_Ventas_Dia_Abiertas_v2" in fuente
    return {
        "ventas": _d(ventas),
        "tickets": int(_d(tickets)),
        "pax": int(_d(pax)),
        "ventas_abiertas": _d(abiertas),
        "es_abierta": es_abierta,
    }


def _sistema(cfg: Dict[str, Any]) -> str:
    st = _s(cfg.get("system_type")).upper()
    if "SOFT" in st:
        return "SOFTRESTAURANT"
    if "MPRO" in st or "MANAG" in st:
        return "MPRO"
    raise RuntimeError(f"system_type no reconocido: {st}")


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

        fi = dia.isoformat()
        ff = (dia + timedelta(days=1)).isoformat()

        sql = f"""
        WITH h AS (
            SELECT
                ch.folio,
                ch.fecha,
                ISNULL(ch.nopersonas, 0) AS pax_ticket,
                ISNULL(ch.total, 0) AS importe_neto_ticket,
                {prop_expr} AS propina_ticket,
                {desc_expr} AS descuento_ticket
            FROM cheques ch WITH (NOLOCK)
            WHERE ch.fecha >= %s
              AND ch.fecha < %s
              AND ISNULL(ch.cancelado, 0) = 0
        ),
        l AS (
            SELECT
                h.folio,
                h.fecha,
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
            l.pax_ticket,
            l.importe_neto_ticket,
            l.propina_ticket,
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
        INNER JOIN t ON t.folio = l.folio
        ORDER BY l.folio, l.producto_codigo_fuente
        """
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, (fi, ff))
        rows = cur.fetchall() or []
        for r in rows:
            r["sistema_origen"] = "SOFTRESTAURANT"
        return rows
    finally:
        conn.close()


def _extract_mpro(cfg: Dict[str, Any], dia: date) -> List[Dict[str, Any]]:
    suc = cfg.get("sucursal_origen_id")
    if not suc:
        raise RuntimeError("MPRO requiere sucursal_origen_id")

    conn = get_pos_connection(cfg)
    if not conn:
        raise RuntimeError(f"sin conexión POS para {cfg.get('unidad_codigo')}")

    try:
        fi = dia.isoformat()
        ff = (dia + timedelta(days=1)).isoformat()

        sql = """
        WITH h AS (
            SELECT
                v.Vn_Folio,
                v.Vn_Documento,
                v.Vn_Fecha,
                v.Sc_Cve_Sucursal,
                ISNULL(c.Co_Personas, 0) AS pax_ticket,
                ISNULL(v.Vn_Precio_Neto_Importe, 0) AS importe_neto_ticket,
                ISNULL(c.Co_Propina, 0) AS propina_ticket,
                ISNULL(v.Vn_Descuento_Global_Importe, 0)
                  + ISNULL(v.Vn_Descuento_Importe, 0) AS descuento_ticket
            FROM Venta_Encabezado v WITH (NOLOCK)
            LEFT JOIN Comanda c WITH (NOLOCK)
                ON c.Co_Folio = v.Vn_Documento
               AND c.Sc_Cve_Sucursal = v.Sc_Cve_Sucursal
            WHERE v.Vn_Fecha >= %s
              AND v.Vn_Fecha < %s
              AND v.Sc_Cve_Sucursal = %s
              AND ISNULL(v.Vn_Tabla, '') = 'Comanda'
              AND ISNULL(v.Es_Cve_Estado, '') <> 'CA'
        ),
        l AS (
            SELECT
                h.Vn_Folio,
                h.Vn_Documento,
                h.Vn_Fecha,
                h.pax_ticket,
                h.importe_neto_ticket,
                h.propina_ticket,
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
               AND ISNULL(d.Es_Cve_Estado, '') <> 'CA'
            GROUP BY
                h.Vn_Folio,
                h.Vn_Documento,
                h.Vn_Fecha,
                h.pax_ticket,
                h.importe_neto_ticket,
                h.propina_ticket,
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
            l.pax_ticket,
            l.importe_neto_ticket,
            l.propina_ticket,
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
        return rows
    finally:
        conn.close()


def _materialize_rows(cfg: Dict[str, Any], dia: date, src_rows: List[Dict[str, Any]], run_id: str) -> List[Dict[str, Any]]:
    seen_ticket = set()
    out: List[Dict[str, Any]] = []

    for r in src_rows:
        ticket_key = _s(r.get("id_transaccion"))
        first_for_ticket = ticket_key not in seen_ticket
        seen_ticket.add(ticket_key)

        importe_bruto = _d(r.get("importe_bruto"))
        importe_neto = _d(r.get("importe_neto"))

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
            "cantidad": _d(r.get("cantidad")),
            "precio_unitario": _d(r.get("precio_unitario")),
            "importe_bruto": importe_bruto,
            "importe_neto": importe_neto,
            "descuento": importe_bruto - importe_neto,
            "propina": _d(r.get("propina_ticket")) if first_for_ticket else Decimal("0"),
            "pax": int(_d(r.get("pax_ticket"))) if first_for_ticket else None,
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
    for r in src_rows:
        k = _s(r.get("id_transaccion"))
        if k not in tickets:
            tickets[k] = {
                "venta": _d(r.get("importe_neto_ticket")),
                "pax": int(_d(r.get("pax_ticket"))),
            }

    ventas_por_ticket = sum((v["venta"] for v in tickets.values()), Decimal("0"))
    pax = sum(v["pax"] for v in tickets.values())
    tickets_total = len(tickets)

    ventas_runtime = runtime["ventas"]
    tickets_runtime = runtime["tickets"]
    pax_runtime = runtime["pax"]

    ok = (
        _money_eq(ventas_por_ticket, ventas_runtime)
        and _int_eq(tickets_total, tickets_runtime)
        and _int_eq(pax, pax_runtime)
    )

    return {
        "ok": ok,
        "ventas_runtime": ventas_runtime,
        "ventas_por_ticket": ventas_por_ticket,
        "delta_ventas": ventas_por_ticket - ventas_runtime,
        "tickets_runtime": tickets_runtime,
        "tickets_por_ticket": tickets_total,
        "delta_tickets": tickets_total - tickets_runtime,
        "pax_runtime": pax_runtime,
        "pax_por_ticket": pax,
        "delta_pax": pax - pax_runtime,
        "lineas_producto": len(src_rows),
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
            %s,%s,%s,%s,%s,%s,%s,%s
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unidad", default=None)
    ap.add_argument("--fecha-inicio", required=True)
    ap.add_argument("--fecha-fin", required=True, help="Fecha fin exclusiva YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true", default=False)
    ap.add_argument("--commit", action="store_true", default=False)
    ap.add_argument("--solo-ok-runtime", action="store_true", default=True)
    ap.add_argument("--excluir-abiertas", action="store_true", default=True)
    ap.add_argument("--offset-pos-dias", type=int, default=0, help="Dias a sumar a fecha_operacion para consultar POS. MPRO historico usa +1.")
    args = ap.parse_args()

    offset_pos_dias = int(args.offset_pos_dias or 0)
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

            rm = _runtime_metrics(rt)

            if args.excluir_abiertas and (rm["ventas_abiertas"] > 0 or rm["es_abierta"]):
                item = {
                    "status": "NO_PROBAR_ABIERTO_REAL",
                    "unidad": cfg.get("unidad_codigo"),
                    "fecha_operacion": dia,
                    "ventas_runtime": rm["ventas"],
                    "ventas_abiertas_runtime": rm["ventas_abiertas"],
                    "tickets_runtime": rm["tickets"],
                    "pax_runtime": rm["pax"],
                }
                resumen.append(item)
                _safe_print(item)
                total_blocked += 1
                continue

            try:
                pos_dia = dia + timedelta(days=offset_pos_dias)

                if sistema == "SOFTRESTAURANT":
                    src_rows = _extract_soft(cfg, pos_dia)
                else:
                    src_rows = _extract_mpro(cfg, pos_dia)

                validation = _validate(src_rows, rm)
                status = "OK_HEADER_CANONICO" if validation["ok"] else "NO_CUADRA_REVISAR"

                item = {
                    "status": status,
                    "unidad": cfg.get("unidad_codigo"),
                    "unidad_nombre": cfg.get("unidad_nombre"),
                    "sistema": sistema,
                    "fecha_operacion": dia,
                    **validation,
                }

                if status != "OK_HEADER_CANONICO":
                    resumen.append(item)
                    _safe_print(item)
                    total_blocked += 1
                    continue

                rows = _materialize_rows(cfg, dia, src_rows, run_id)
                item["filas_destino_preparadas"] = len(rows)

                if args.commit:
                    inserted = _insert_rows(rows)
                    item["filas_insertadas"] = inserted
                    total_insertadas += inserted
                else:
                    item["filas_insertadas"] = 0

                resumen.append(item)
                _safe_print(item)
                total_ok += 1

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

    return 0


if __name__ == "__main__":
    sys.exit(main())
