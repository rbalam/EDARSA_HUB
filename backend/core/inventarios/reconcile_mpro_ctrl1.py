"""Reconciliacion puntual MPRO CTRL_1 desde GitHub Actions.

Solo modifica Inventario_MovimientosDetalle.Cantidad cuando coincide la identidad
canonica completa, el origen MPRO y los valores auditados. No cambia el sync
recurrente, no lee POS desde dashboards y no necesita un endpoint LIVE.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation

UNIT = "130QRO"
ORIGIN_BRANCH = "0021"
ORIGIN_PRODUCT = "0000000061"
WAREHOUSE = "0001"
CONCEPT = "112"
EMPRESA_ID = 2
SUCURSAL_ID = 2
PRODUCTO_ID = 2014
REF_TYPE = "MOVIMIENTO_POS|112"
EXPECTED = {
    53898: ("2026-10-08", Decimal("5.000000"), Decimal("5000.000000")),
    53899: ("2026-10-13", Decimal("4.500000"), Decimal("4500.000000")),
    53903: ("2026-10-23", Decimal("6.200000"), Decimal("6200.000000")),
}


def _decimal(value):
    try:
        result = Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation) as exc:
        raise ValueError("CANTIDAD_INVALIDA") from exc
    if not result.is_finite():
        raise ValueError("CANTIDAD_NO_FINITA")
    return result


def _folio(value):
    return str(value or "").strip()[:30]


def build_reconciliation_plan(source_rows, hub_rows):
    """Fail-closed: origen y destino completos, univocos y en unidades CTRL_1."""
    by_date = {}
    expected_dates = {v[0] for v in EXPECTED.values()}
    for row in source_rows:
        day = str(row.get("fecha") or "")[:10]
        if day not in expected_dates:
            raise ValueError("ORIGEN_FECHA_INESPERADA")
        if str(row.get("unidad") or "").strip().upper() != "GR":
            raise ValueError("ORIGEN_UNIDAD_NO_GR")
        quantity = _decimal(row.get("cantidad"))
        if quantity <= 0:
            raise ValueError("ORIGEN_CANTIDAD_NO_POSITIVA")
        folio = _folio(row.get("folio"))
        if day not in by_date:
            by_date[day] = {"folio": folio, "cantidad": Decimal("0")}
        if by_date[day]["folio"] != folio:
            raise ValueError("ORIGEN_MULTIPLES_FOLIOS_MISMO_DIA")
        by_date[day]["cantidad"] += quantity

    if set(by_date) != expected_dates:
        raise ValueError("ORIGEN_INCOMPLETO_O_EXTRA")

    if len(hub_rows) != len(EXPECTED):
        raise ValueError("HUB_NUMERO_FILAS_DIFERENTE")

    by_id = {}
    for row in hub_rows:
        movement_id = int(row.get("MovimientoID") or 0)
        if movement_id not in EXPECTED or movement_id in by_id:
            raise ValueError("HUB_ID_DUPLICADO_O_AJENO")
        by_id[movement_id] = row

    if set(by_id) != set(EXPECTED):
        raise ValueError("HUB_MOVIMIENTOS_INCOMPLETOS")

    plan = []
    for movement_id, (day, old, certified_new) in EXPECTED.items():
        source = by_date[day]
        current = by_id[movement_id]
        if source["cantidad"] != certified_new:
            raise ValueError("ORIGEN_CTRL1_NO_COINCIDE_AUDITORIA")
        if (
            int(current.get("EmpresaID") or 0) != EMPRESA_ID
            or int(current.get("SucursalID") or 0) != SUCURSAL_ID
            or int(current.get("ProductoID") or 0) != PRODUCTO_ID
            or str(current.get("CodigoAlmacen") or "").strip() != WAREHOUSE
            or str(current.get("ReferenciaTipo") or "").strip() != REF_TYPE
            or str(current.get("Naturaleza") or "").strip().upper() != "E"
            or int(current.get("Activo") or 0) != 1
            or str(current.get("fecha") or "")[:10] != day
            or _folio(current.get("FolioReferencia")) != source["folio"]
        ):
            raise ValueError("HUB_IDENTIDAD_NO_COINCIDE_ORIGEN")
        quantity = _decimal(current.get("Cantidad"))
        if quantity not in (old, certified_new):
            raise ValueError("HUB_CANTIDAD_CAMBIO_INESPERADO")
        plan.append({
            "movement_id": movement_id,
            "fecha": day,
            "folio": source["folio"],
            "previous": quantity,
            "source_ctrl1": source["cantidad"],
            "needs_update": quantity != source["cantidad"],
        })
    if sum((p["source_ctrl1"] for p in plan), Decimal("0")) != Decimal("15700"):
        raise ValueError("TOTAL_CTRL1_INCONSISTENTE")
    return plan


def _connect(cfg, pymssql, *, readonly=False):
    conn = pymssql.connect(
        server=cfg.host,
        port=cfg.port,
        database=cfg.database,
        user=cfg.user,
        password=cfg.password,
        login_timeout=15,
        timeout=60,
        as_dict=True,
        autocommit=readonly,
    )
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "SELECT DB_NAME() AS db, SUSER_SNAME() AS login, USER_NAME() AS usuario"
    )
    identity = cur.fetchone() or {}
    if str(identity.get("db") or "").upper() != "EDARSAHUB":
        conn.close()
        raise ValueError("BASE_SQL_NO_EDARSAHUB")
    if readonly:
        if identity.get("login") != "HRLectura" or identity.get("usuario") != "HRLectura":
            conn.close()
            raise ValueError("LECTOR_DEBE_SER_HRLECTURA")
    elif str(identity.get("login") or "").upper() == "HRLECTURA" or str(identity.get("usuario") or "").upper() == "HRLECTURA":
        conn.close()
        raise ValueError("WRITER_NO_PUEDE_SER_HRLECTURA")
    return conn


def _one(cur, sql, params=()):
    cur.execute(sql, params)
    rows = cur.fetchall() or []
    if len(rows) != 1:
        raise ValueError("RESOLUCION_CANONICA_AUSENTE_O_AMBIGUA")
    return rows[0]


def _resolve_config(reader):
    cur = reader.cursor(as_dict=True)
    server = _one(cur, """
        SELECT s.id, s.host, ISNULL(s.port,1433) AS port,
               s.database_name, s.username, s.password_encrypted,
               s.system_type, u.sucursal_origen_id
        FROM dbo.Unidades_Negocio u
        JOIN dbo.Servidores_Conexiones s
          ON LOWER(CONVERT(VARCHAR(36),u.server_id))
           = LOWER(CONVERT(VARCHAR(36),s.id))
        WHERE UPPER(LTRIM(RTRIM(u.codigo)))=%s
          AND ISNULL(u.activo,0)=1 AND ISNULL(s.activo,0)=1
    """, (UNIT,))
    system = str(server.get("system_type") or "").upper()
    if not any(x in system for x in ("MPRO", "MANAGEMENT", "MANAGMENT")):
        raise ValueError("SISTEMA_NO_ES_MPRO")
    if str(server.get("sucursal_origen_id") or "").strip() != ORIGIN_BRANCH:
        raise ValueError("SUCURSAL_ORIGEN_NO_COINCIDE")

    empresa = _one(cur, """
        SELECT EmpresaID FROM dbo.Sistema_Empresas
        WHERE UPPER(LTRIM(RTRIM(CodigoEmpresa)))=%s AND Activo=1
    """, (UNIT,))
    if int(empresa["EmpresaID"]) != EMPRESA_ID:
        raise ValueError("EMPRESA_CANONICA_CAMBIO")

    sucursal = _one(cur, """
        SELECT SucursalID FROM dbo.Sistema_Sucursales
        WHERE EmpresaID=%s AND Activo=1
    """, (EMPRESA_ID,))
    if int(sucursal["SucursalID"]) != SUCURSAL_ID:
        raise ValueError("SUCURSAL_CANONICA_CAMBIO")

    producto = _one(cur, """
        SELECT ProductoID FROM dbo.Producto_MapeoOrigen
        WHERE LOWER(CONVERT(VARCHAR(36),ServerID))
              = LOWER(CONVERT(VARCHAR(36),%s))
          AND UPPER(SystemType)='MPRO'
          AND LTRIM(RTRIM(CONVERT(VARCHAR(50),CodigoFuente)))
              IN ('0000000061','000000061','61')
          AND Activo=1
    """, (str(server["id"]),))
    if int(producto["ProductoID"]) != PRODUCTO_ID:
        raise ValueError("PRODUCTO_CANONICO_CAMBIO")

    cur.close()
    return server


def _read_source(server, pymssql):
    from cryptography.fernet import Fernet

    encrypted = str(server.get("password_encrypted") or "")
    if encrypted.startswith("enc:v1:"):
        secret = os.environ.get("SERVER_SECRET_KEY") or ""
        if not secret:
            raise ValueError("SERVER_SECRET_KEY_NO_CONFIGURADA")
        password = Fernet(secret.encode()).decrypt(
            encrypted[len("enc:v1:"):].encode()
        ).decode()
    elif encrypted:
        password = encrypted
    else:
        raise ValueError("CREDENCIAL_ORIGEN_NO_DISPONIBLE")

    raw_host = str(server.get("host") or "").strip()
    port = int(server.get("port") or 1433)
    host = raw_host.split("\\", 1)[0].strip()
    if "," in host:
        name, sep, candidate = host.rpartition(",")
        if sep and candidate.strip().isdigit():
            host, port = name.strip(), int(candidate.strip())

    pos = pymssql.connect(
        server=host, port=port,
        database=str(server.get("database_name") or ""),
        user=str(server.get("username") or ""),
        password=password, login_timeout=15, timeout=90,
        as_dict=True, autocommit=True,
    )
    try:
        cur = pos.cursor(as_dict=True)
        cur.execute("""
            SELECT CONVERT(VARCHAR(10),m.Mv_Fecha,120) AS fecha,
                   CAST(m.Mv_Documento AS VARCHAR(50)) AS folio,
                   CAST(m.Mv_Cantidad_Control_1 AS DECIMAL(18,6)) AS cantidad,
                   CAST(p.Pr_Unidad_Control_1 AS VARCHAR(50)) AS unidad
            FROM dbo.Movimiento m
            INNER JOIN dbo.Producto p
                ON p.Pr_Cve_Producto=m.Pr_Cve_Producto
            WHERE m.Sc_Cve_Sucursal=%s
              AND LTRIM(RTRIM(CONVERT(VARCHAR(50),m.Pr_Cve_Producto))) IN ('0000000061','000000061','61')
              AND CONVERT(VARCHAR(50),m.Al_Cve_Almacen)=%s
              AND CONVERT(VARCHAR(50),m.Tm_Cve_Tipo_Movimiento)=%s
              AND m.Mv_Fecha >= '20261001'
              AND m.Mv_Fecha < '20261026'
              AND ISNULL(m.Es_Cve_Estado,'') <> 'CA'
        """, (ORIGIN_BRANCH, WAREHOUSE, CONCEPT))
        return cur.fetchall() or []
    finally:
        pos.close()


def _read_hub(conn, *, lock=False):
    cur = conn.cursor(as_dict=True)
    hint = "WITH (UPDLOCK,HOLDLOCK)" if lock else ""
    sql = """
        SELECT m.MovimientoID, CONVERT(VARCHAR(10),m.FechaMovimiento,120) AS fecha,
               m.EmpresaID, m.SucursalID, m.ReferenciaTipo,
               m.FolioReferencia, m.Activo,
               a.CodigoAlmacen, tm.Naturaleza,
               d.ProductoID, d.Cantidad
        FROM dbo.Inventario_Movimientos m {hint}
        LEFT JOIN dbo.Inventario_MovimientosDetalle d {hint}
          ON d.MovimientoID=m.MovimientoID AND d.ProductoID=%s
        LEFT JOIN dbo.Inventario_Almacenes a ON a.AlmacenID=m.AlmacenID
        LEFT JOIN dbo.Inventario_TipoMovimiento tm
          ON tm.TipoMovimientoID=m.TipoMovimientoID
        WHERE m.MovimientoID IN (53898,53899,53903)
    """.format(hint=hint)
    cur.execute(sql, (PRODUCTO_ID,))
    return cur.fetchall() or []


def _check_writer(conn):
    cur = conn.cursor(as_dict=True)
    cur.execute("""
        SELECT COALESCE(
            HAS_PERMS_BY_NAME(
                'dbo.Inventario_MovimientosDetalle','OBJECT','UPDATE'
            ),0
        ) AS permiso
    """)
    if int((cur.fetchone() or {}).get("permiso") or 0) != 1:
        raise ValueError("WRITER_SIN_PERMISO_UPDATE")


def _apply(reader_plan, source_rows, pymssql):
    from core.config.edarsahub_config import get_edarsahub_sql_config

    writer = _connect(get_edarsahub_sql_config("writer"), pymssql)
    try:
        _check_writer(writer)
        cur = writer.cursor(as_dict=True)
        cur.execute("SET XACT_ABORT ON")
        cur.execute("SET LOCK_TIMEOUT 15000")
        # Las lecturas con UPDLOCK/HOLDLOCK y los UPDATE viven en una transaccion.
        locked_plan = build_reconciliation_plan(source_rows, _read_hub(writer, lock=True))
        if locked_plan != reader_plan:
            raise ValueError("HUB_CAMBIO_ENTRE_AUDITORIA_Y_TRANSACCION")
        modifications = [p for p in locked_plan if p["needs_update"]]
        for p in modifications:
            cur.execute("""
                UPDATE d SET d.Cantidad=%s
                OUTPUT INSERTED.MovimientoID, INSERTED.ProductoID,
                       DELETED.Cantidad AS anterior, INSERTED.Cantidad AS nueva
                FROM dbo.Inventario_MovimientosDetalle d
                INNER JOIN dbo.Inventario_Movimientos m
                    ON m.MovimientoID=d.MovimientoID
                INNER JOIN dbo.Inventario_Almacenes a
                    ON a.AlmacenID=m.AlmacenID
                INNER JOIN dbo.Inventario_TipoMovimiento tm
                    ON tm.TipoMovimientoID=m.TipoMovimientoID
                WHERE d.MovimientoID=%s AND d.ProductoID=%s
                  AND d.Cantidad=%s
                  AND m.EmpresaID=%s AND m.SucursalID=%s
                  AND a.CodigoAlmacen=%s
                  AND m.ReferenciaTipo=%s AND tm.Naturaleza='E'
                  AND ISNULL(m.Activo,1)=1
                  AND CONVERT(VARCHAR(10),m.FechaMovimiento,120)=%s
                  AND ISNULL(m.FolioReferencia,'')=%s
            """, (
                p["source_ctrl1"], p["movement_id"], PRODUCTO_ID,
                p["previous"], EMPRESA_ID, SUCURSAL_ID, WAREHOUSE, REF_TYPE,
                p["fecha"], p["folio"],
            ))
            changed = cur.fetchall() or []
            if (
                len(changed) != 1
                or int(changed[0]["MovimientoID"]) != p["movement_id"]
                or _decimal(changed[0]["anterior"]) != p["previous"]
                or _decimal(changed[0]["nueva"]) != p["source_ctrl1"]
            ):
                raise ValueError("UPDATE_NO_ATOMICO_O_NO_COINCIDENTE")
        final = build_reconciliation_plan(source_rows, _read_hub(writer, lock=True))
        if any(p["needs_update"] for p in final):
            raise ValueError("VERIFICACION_POST_UPDATE_FALLIDA")
        writer.commit()
        return {"status": "APPLIED" if modifications else "ALREADY_CORRECT",
                "changed": len(modifications), "final_total_ctrl1": "15700.000000"}
    except Exception:
        writer.rollback()
        raise
    finally:
        writer.close()


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("audit", "apply"):
        raise SystemExit("USO: python -m core.inventarios.reconcile_mpro_ctrl1 audit|apply")
    mode = sys.argv[1]
    if os.environ.get("GITHUB_REF") != "refs/heads/Edarsahub_Desarrollo":
        raise ValueError("RAMA_GITHUB_NO_AUTORIZADA")
    if mode == "apply" and os.environ.get("BACKUP_VERIFIED") != "true":
        raise ValueError("RESPALDO_NO_CONFIRMADO")

    import pymssql
    from core.config.edarsahub_config import get_edarsahub_sql_config

    reader = _connect(get_edarsahub_sql_config("default"), pymssql, readonly=True)
    try:
        server = _resolve_config(reader)
        source_rows = _read_source(server, pymssql)
        plan = build_reconciliation_plan(source_rows, _read_hub(reader))
    finally:
        reader.close()

    summary = [{
        "MovimientoID": p["movement_id"],
        "fecha": p["fecha"],
        "hub_actual": str(p["previous"]),
        "origen_ctrl1": str(p["source_ctrl1"]),
        "diferente": p["needs_update"],
    } for p in plan]
    print("AUDITORIA_MP30QRO=" + json.dumps(
        {"status": "VALIDATED", "mode": mode, "rows": summary},
        ensure_ascii=False,
    ), flush=True)
    if mode == "audit":
        print("RESULTADO=" + json.dumps({
            "status": "AUDIT_ONLY",
            "would_update": sum(p["needs_update"] for p in plan),
            "production_data_modified": False,
        }), flush=True)
    else:
        outcome = _apply(plan, source_rows, pymssql)
        print("RESULTADO=" + json.dumps({
            **outcome,
            "production_data_modified": outcome["changed"] > 0,
        }), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR_RECONCILIACION=" + type(exc).__name__
              + ":" + str(exc), file=sys.stderr, flush=True)
        raise SystemExit(1)
