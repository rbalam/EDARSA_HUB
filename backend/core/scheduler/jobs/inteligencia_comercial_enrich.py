"""
EDARSA HUB - Enriquecimiento Inteligencia Comercial (por TICKET)
================================================================
Extrae del POS origen (SOLO LECTURA) y puebla en EDARSAHUB, por ticket:
  (a) Tipo de servicio  -> dbo.Sync_Sales.TipoServicioID / .TipoServicio
  (b) Formas de pago     -> dbo.Finanzas_CortesCaja_DetallePagos (1 fila por pago)

Fuentes (descubiertas y verificadas, sin hardcode de credenciales):
  SoftRestaurant:
    - tipo servicio: cheques.tipodeservicio (catálogo dbo.tiposervicio: Idtiposervicio/Desc_tiposervicio)
    - pagos: chequespagos (folio, idformadepago, importe, propina, referencia) + formasdepago.descripcion
  MPRO (CENTRAL2020, filtrado por sucursal canónica):
    - tipo servicio: Comanda.Co_Tipo (join Comanda.Co_Folio = Venta_Encabezado.Vn_Folio)
    - pagos: Comanda_Pago (Co_Folio, Fp_Cve_Forma_Pago, Cp_Importe, Cp_Propina, Cp_Referencia) + Forma_Pago.Fp_Descripcion

Idempotente por (UnidadNegocio, periodo): re-escribe DetallePagos del rango y
actualiza TipoServicio sobre tickets existentes en Sync_Sales.
NO toca KPIs canónicos. NO imprime secretos. NO usa MongoDB.
"""
import json
import time
import hashlib
import logging
from datetime import datetime

from core.sql_first.connection_factory import (
    get_external_sql_connection,
)
from core.connections.pos_runtime_resolver import resolve_pos_runtime_context
from core.sql_first.db import get_sql_connection
from core.scheduler.jobs.inteligencia_comercial_sync_job import (
    get_unidades_negocio_pos,
    get_pos_config_for_unidad,
    registrar_syncpos_bitacora,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def _connect_pos(cfg):
    connection_config = dict(cfg)
    connection_config.setdefault("login_timeout", 10)
    connection_config.setdefault("timeout", 240)
    connection_config.setdefault("tds_version", "7.0")
    connection_config.setdefault("as_dict", True)

    return get_external_sql_connection(
        connection_config
    )


def _cursor_as_dict(conn):
    """Cursor compatible con pymssql y fallback pyodbc."""
    try:
        return conn.cursor(as_dict=True)
    except TypeError:
        return conn.cursor()


def _fetchall_dicts(cur):
    """Normaliza filas del driver SQL a diccionarios."""
    rows = cur.fetchall() or []
    if not rows:
        return []
    if isinstance(rows[0], dict):
        return rows
    columns = [item[0] for item in (cur.description or [])]
    return [
        {columns[index]: row[index] for index in range(len(columns))}
        for row in rows
    ]


def _hash_pago(sistema, unidad, ticket, codigo, importe, propina, referencia):
    cadena = "|".join([
        str(sistema or ""), str(unidad or ""), str(ticket or ""), str(codigo or ""),
        str(float(importe or 0)), str(float(propina or 0)), str(referencia or ""),
    ])
    return hashlib.sha256(cadena.encode()).hexdigest()


def _bulk_insert(cur, prefix, ncols, rows, max_params=2000):
    """INSERT multi-fila parametrizado en chunks (respeta el límite de params)."""
    if not rows:
        return 0
    chunk = max(1, max_params // ncols)
    ph = "(" + ",".join(["%s"] * ncols) + ")"
    total = 0
    for i in range(0, len(rows), chunk):
        batch = rows[i:i + chunk]
        sql = prefix + " VALUES " + ",".join([ph] * len(batch))
        flat = [v for r in batch for v in r]
        cur.execute(sql, tuple(flat))
        total += len(batch)
    return total


# ============================================================================
# EXTRACCIÓN SOFTRESTAURANT
# ============================================================================
def _extract_softrestaurant(cfg, fi, ff):
    conn = _connect_pos(cfg)
    try:
        cur = _cursor_as_dict(conn)
        cur.execute(f"""
            SELECT CONVERT(VARCHAR(64), ch.folio) AS folio,
                   ch.tipodeservicio AS tsid, ts.Desc_tiposervicio AS tsdesc
            FROM cheques ch
            INNER JOIN turnos t ON t.idturno = ch.idturno
            LEFT JOIN tiposervicio ts ON ts.Idtiposervicio = ch.tipodeservicio
            WHERE t.apertura >= '{fi}' AND t.apertura < '{ff}'
              AND t.cierre IS NOT NULL
              AND ch.cancelado = 0 AND ch.total > 0
        """)
        tipos = _fetchall_dicts(cur)
        cur.execute(f"""
            SELECT CONVERT(VARCHAR(64), cp.folio) AS folio,
                   CONVERT(VARCHAR(40), cp.idformadepago) AS codigo,
                   fp.descripcion AS forma,
                   CAST(
                       ISNULL(cp.importe, 0)
                       * COALESCE(NULLIF(cp.tipodecambio, 0), NULLIF(fp.tipodecambio, 0), 1)
                       AS decimal(18,4)
                   ) AS importe,
                   CAST(
                       ISNULL(cp.propina, 0)
                       * COALESCE(NULLIF(cp.tipodecambio, 0), NULLIF(fp.tipodecambio, 0), 1)
                       AS decimal(18,4)
                   ) AS propina,
                   cp.referencia AS referencia, t.apertura AS fecha
            FROM chequespagos cp
            INNER JOIN cheques ch ON ch.folio = cp.folio
            INNER JOIN turnos t ON t.idturno = ch.idturno
            LEFT JOIN formasdepago fp ON fp.idformadepago = cp.idformadepago
            WHERE t.apertura >= '{fi}' AND t.apertura < '{ff}'
              AND t.cierre IS NOT NULL
              AND ch.cancelado = 0 AND ch.total > 0
        """)
        pagos = _fetchall_dicts(cur)
        cur.close()
    finally:
        conn.close()
    return tipos, pagos


# ============================================================================
# EXTRACCIÓN MPRO
# ============================================================================
def _extract_mpro(cfg, fi, ff):
    suc = cfg.get("sucursal_origen_id")
    if not suc:
        raise ValueError("MPRO requiere sucursal_origen_id canónico (Sc_Cve_Sucursal)")
    suc = str(suc).replace("'", "''")
    last_err = None
    for intento in range(3):
        conn = _connect_pos(cfg)
        try:
            cur = _cursor_as_dict(conn)
            cur.execute(f"""
                SELECT CONVERT(VARCHAR(64), v.Vn_Folio) AS folio,
                       CONVERT(VARCHAR(20), c.Co_Tipo) AS tsid, CAST(NULL AS NVARCHAR(120)) AS tsdesc
                FROM Venta_Encabezado v WITH (NOLOCK)
                INNER JOIN Comanda c WITH (NOLOCK)
                    ON c.Co_Folio = v.Vn_Folio AND c.Sc_Cve_Sucursal = v.Sc_Cve_Sucursal
                WHERE CONVERT(date, v.Vn_Fecha) >= CONVERT(date, '{fi}') AND CONVERT(date, v.Vn_Fecha) < CONVERT(date, '{ff}')
                  AND v.Sc_Cve_Sucursal = '{suc}'
                  AND ISNULL(v.Es_Cve_Estado, '') <> 'CA'
                  AND v.Vn_Precio_Neto_Importe > 0
            """)
            tipos = _fetchall_dicts(cur)
            cur.execute(f"""
                SELECT CONVERT(VARCHAR(64), v.Vn_Folio) AS folio,
                       CONVERT(VARCHAR(40), cp.Fp_Cve_Forma_Pago) AS codigo,
                       fp.Fp_Descripcion AS forma,
                       cp.Cp_Importe AS importe, cp.Cp_Propina AS propina,
                       cp.Cp_Referencia AS referencia, v.Vn_Fecha AS fecha
                FROM Venta_Encabezado v WITH (NOLOCK)
                INNER JOIN Comanda_Pago cp WITH (NOLOCK) ON cp.Co_Folio = v.Vn_Documento
                LEFT JOIN Forma_Pago fp WITH (NOLOCK) ON fp.Fp_Cve_Forma_Pago = cp.Fp_Cve_Forma_Pago
                WHERE CONVERT(date, v.Vn_Fecha) >= CONVERT(date, '{fi}') AND CONVERT(date, v.Vn_Fecha) < CONVERT(date, '{ff}')
                  AND v.Sc_Cve_Sucursal = '{suc}'
                  AND ISNULL(v.Es_Cve_Estado, '') <> 'CA'
                  AND cp.Cp_Importe > 0
            """)
            pagos = _fetchall_dicts(cur)
            cur.close()
            return tipos, pagos
        except Exception as e:
            last_err = e
            if "deadlock" in str(e).lower() or "1205" in str(e):
                time.sleep(2 + intento * 2)
                continue
            raise
        finally:
            conn.close()
    raise last_err


# ============================================================================
# ESCRITURA EN EDARSAHUB
# ============================================================================
def _write_enrichment(unidad_codigo, sistema, tipos, pagos, fi, ff):
    """Actualiza Sync_Sales.TipoServicio y re-escribe DetallePagos del rango."""
    metrics = {"tickets_tiposervicio": 0, "pagos_extraidos": len(pagos),
               "pagos_insertados": 0, "tickets_actualizados": 0}
    conn = get_sql_connection()
    try:
        cur = conn.cursor()

        # 1) Tipo de servicio -> Sync_Sales (UPDATE masivo vía tabla temporal)
        ts_rows = []
        seen = set()
        for r in tipos:
            folio = str(r.get("folio"))
            if folio in seen:
                continue
            seen.add(folio)
            tsid = r.get("tsid")
            tsid = None if tsid is None else str(tsid).strip()
            ts_rows.append((folio, tsid, r.get("tsdesc")))
        metrics["tickets_tiposervicio"] = len(ts_rows)
        if ts_rows:
            cur.execute("CREATE TABLE #ts (NumeroTicket NVARCHAR(64), tsid NVARCHAR(20), tsdesc NVARCHAR(120))")
            _bulk_insert(cur, "INSERT INTO #ts (NumeroTicket, tsid, tsdesc)", 3, ts_rows)
            cur.execute(
                "UPDATE s SET s.TipoServicioID=t.tsid, s.TipoServicio=t.tsdesc "
                "FROM dbo.Sync_Sales s INNER JOIN #ts t ON s.NumeroTicket=t.NumeroTicket "
                "WHERE s.UnidadNegocio=%s AND s.FechaHora >= %s AND s.FechaHora < %s",
                (unidad_codigo, fi, ff),
            )
            metrics["tickets_actualizados"] = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
            cur.execute("DROP TABLE #ts")

        # 2) Formas de pago -> DetallePagos (DELETE rango + INSERT, idempotente)
        cur.execute(
            "DELETE FROM dbo.Finanzas_CortesCaja_DetallePagos "
            "WHERE UnidadNegocio=%s AND FechaHora >= %s AND FechaHora < %s",
            (unidad_codigo, fi, ff),
        )
        now = datetime.now()
        rows = []
        for p in pagos:
            folio = str(p.get("folio"))
            codigo = (p.get("codigo") or "").strip()
            forma = (p.get("forma") or codigo or "SIN_FORMA").strip()
            importe = float(p.get("importe") or 0)
            propina = float(p.get("propina") or 0)
            referencia = (p.get("referencia") or "").strip() or None
            fecha = p.get("fecha")
            h = _hash_pago(sistema, unidad_codigo, folio, codigo, importe, propina, referencia)
            rows.append((None, forma, codigo or None, importe, referencia, sistema,
                         h, 1, unidad_codigo, folio, fecha, propina, now))
        if rows:
            prefix = (
                "INSERT INTO dbo.Finanzas_CortesCaja_DetallePagos "
                "(CorteCajaID, FormaPago, FormaPagoCodigo, Importe, Referencia, SistemaOrigen, "
                " HashOrigen, Activo, UnidadNegocio, NumeroTicket, FechaHora, Propina, FechaAlta)"
            )
            metrics["pagos_insertados"] = _bulk_insert(cur, prefix, 13, rows)
        cur.close()
        conn.commit()
        return metrics
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        metrics["error"] = f"{type(e).__name__}: {e}"
        return metrics
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ============================================================================
# ORQUESTADOR POR UNIDAD
# ============================================================================
def enrich_unidad(unidad_codigo, fecha_inicio, fecha_fin, dry_run=False):
    """Enriquece una unidad para un rango [fi, ff) (ff exclusivo). Devuelve métricas."""
    t0 = time.time()
    unidades = get_unidades_negocio_pos([unidad_codigo])
    if not unidades:
        return {"unidad": unidad_codigo, "error": "unidad no encontrada en canónico"}
    unidad_row = unidades[0]
    cfg = get_pos_config_for_unidad(unidad_row)
    if not cfg or not cfg.get("host"):
        return {"unidad": unidad_codigo, "error": "config POS no resuelta"}

    system = (cfg.get("system_type") or "").upper()
    codigo = unidad_row.get("unidad_codigo")
    sistema_origen = "MPRO" if "MPRO" in system else "SoftRestaurant"

    try:
        if "MPRO" in system:
            tipos, pagos = _extract_mpro(cfg, fecha_inicio, fecha_fin)
        else:
            tipos, pagos = _extract_softrestaurant(cfg, fecha_inicio, fecha_fin)
    except Exception as e:
        return {"unidad": codigo, "sistema": sistema_origen, "error": f"extracción: {type(e).__name__}: {e}"}

    extract_s = round(time.time() - t0, 1)
    base = {
        "unidad": codigo, "unidad_nombre": unidad_row.get("unidad_nombre"),
        "sistema": sistema_origen, "periodo": f"{fecha_inicio}..{fecha_fin}",
        "tickets_con_tiposervicio": len({str(r.get('folio')) for r in tipos}),
        "pagos_extraidos": len(pagos), "tiempo_extraccion_s": extract_s, "dry_run": dry_run,
    }
    if dry_run:
        base["mensaje"] = "DRY RUN: extracción OK, NO se escribió en EDARSAHUB."
        return base

    metrics = _write_enrichment(codigo, sistema_origen, tipos, pagos, fecha_inicio, fecha_fin)
    base.update(metrics)
    base["tiempo_total_s"] = round(time.time() - t0, 1)
    return base


def _write_payments_only(unidad_codigo, sistema, pagos, fi, ff):
    """Re-escribe SOLO Finanzas_CortesCaja_DetallePagos del rango.

    No toca Sync_Sales ni ninguna tabla de Cuentas/Comandas/Cortes.
    """
    metrics = {"pagos_extraidos": len(pagos), "pagos_insertados": 0}
    conn = get_sql_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM dbo.Finanzas_CortesCaja_DetallePagos "
            "WHERE UnidadNegocio=%s AND FechaHora >= %s AND FechaHora < %s",
            (unidad_codigo, fi, ff),
        )
        metrics["pagos_eliminados"] = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        now = datetime.now()
        rows = []
        for p in pagos:
            folio = str(p.get("folio"))
            codigo = (p.get("codigo") or "").strip()
            forma = (p.get("forma") or codigo or "SIN_FORMA").strip()
            importe = float(p.get("importe") or 0)
            propina = float(p.get("propina") or 0)
            referencia = (p.get("referencia") or "").strip() or None
            fecha = p.get("fecha")
            h = _hash_pago(sistema, unidad_codigo, folio, codigo, importe, propina, referencia)
            rows.append((None, forma, codigo or None, importe, referencia, sistema,
                         h, 1, unidad_codigo, folio, fecha, propina, now))
        if rows:
            prefix = (
                "INSERT INTO dbo.Finanzas_CortesCaja_DetallePagos "
                "(CorteCajaID, FormaPago, FormaPagoCodigo, Importe, Referencia, SistemaOrigen, "
                " HashOrigen, Activo, UnidadNegocio, NumeroTicket, FechaHora, Propina, FechaAlta)"
            )
            metrics["pagos_insertados"] = _bulk_insert(cur, prefix, 13, rows)
        cur.close()
        conn.commit()
        return metrics
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        metrics["error"] = f"{type(e).__name__}: {e}"
        return metrics
    finally:
        try:
            conn.close()
        except Exception:
            pass


def resync_pagos_unidad(unidad_codigo, fecha_inicio, fecha_fin, dry_run=False):
    """Resincroniza SOLO pagos por ticket para SoftRestaurant o ManagementPro en [fi, ff)."""
    try:
        context = resolve_pos_runtime_context(
            unidad_codigo,
            expected_system_types=("SOFTRESTAURANT", "MANAGEMENTPRO"),
        )
    except Exception as e:
        return {
            "unidad": unidad_codigo,
            "error": f"config POS no resuelta: {type(e).__name__}",
        }

    cfg = context.external_connection_config(as_dict=True)
    cfg.update({
        "unidad": context.unidad_codigo,
        "unidad_codigo": context.unidad_codigo,
        "unidad_pk": context.unidad_negocio_pk,
        "sucursal_origen_id": context.sucursal_origen_id,
        "server_id": context.server_id,
        "system_type": context.system_type,
    })

    system = (context.system_type or "").upper()
    is_mpro = "MPRO" in system or "MANAG" in system
    sistema_origen = "MPRO" if is_mpro else "SoftRestaurant"
    codigo = context.unidad_codigo

    try:
        if is_mpro:
            _tipos, pagos = _extract_mpro(cfg, fecha_inicio, fecha_fin)
        else:
            _tipos, pagos = _extract_softrestaurant(cfg, fecha_inicio, fecha_fin)
    except Exception as e:
        return {
            "unidad": codigo,
            "sistema": sistema_origen,
            "error": f"extraccion: {type(e).__name__}: {e}",
        }

    result = {
        "unidad": codigo,
        "sistema": sistema_origen,
        "periodo": f"{fecha_inicio}..{fecha_fin}",
        "pagos_extraidos": len(pagos),
        "dry_run": dry_run,
    }
    if dry_run:
        result["mensaje"] = "DRY RUN: pagos extraidos; no se escribio en EDARSAHUB."
        return result

    result.update(
        _write_payments_only(
            codigo,
            sistema_origen,
            pagos,
            fecha_inicio,
            fecha_fin,
        )
    )
    return result
