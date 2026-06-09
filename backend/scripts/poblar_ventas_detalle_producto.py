"""
ETL NO-LIVE: Poblar Comercial_Inteligencia_VentasDetalleProducto
================================================================
Fuente 100% EDARSAHUB (NO toca POS): shred de dbo.Sync_Sales.items (JSON) +
enriquecimiento canónico con dbo.Sync_Productos (match CodigoFuente+ServerID) y
dbo.Comercial_Productos_Enriquecidos (casa, grado_alcohol, es_alcoholico).

- Idempotente: hash_origen = SHA2_256(unidad|ticket|fecha|indiceLinea|codigo).
  Re-ejecutar NO duplica (NOT EXISTS por hash).
- Procesa por unidad y por mes para mantener transacciones acotadas y resumibles.
- Sin hardcode: unidades y servers se leen de dbo.Unidades_Negocio.

Uso:
  cd /app/backend && set -a && source .env && set +a && \
  python -m scripts.poblar_ventas_detalle_producto [--unidad 130MID] [--desde 2026-01-01] [--hasta 2026-07-01]
"""
import argparse
import logging
import uuid
from datetime import date, datetime

import pymssql
from core.sql_first.db import get_sql_connection
from core.config.edarsahub_config import get_edarsahub_sql_config


def _etl_conn():
    """Conexión dedicada al ETL con timeout amplio (INSERTs mensuales pesados)."""
    c = get_edarsahub_sql_config()
    return pymssql.connect(
        server=c.host, port=int(c.port), user=c.user, password=c.password,
        database=c.database, login_timeout=15, timeout=0, as_dict=True,
    )


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("etl_ventas_detalle")

# Una fila por (unidad, ticket, fecha, código): se AGREGAN las líneas del mismo
# producto dentro del ticket (el índice único de la tabla exige 1 producto/ticket).
_INSERT_SQL = """
INSERT INTO dbo.Comercial_Inteligencia_VentasDetalleProducto
 (id, unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal_id, sucursal_nombre,
  sistema_origen, fecha_operacion, fecha_hora, numero_ticket, id_transaccion,
  producto_codigo_fuente, producto_id, producto_nombre, familia_id, familia_nombre,
  subfamilia_id, subfamilia_nombre, casa, porcentaje_alcohol, es_alcohol,
  cantidad, precio_unitario, importe_bruto, importe_neto, descuento, propina, pax,
  sync_run_id, hash_origen, fecha_sincronizacion, activo)
SELECT
  NEWID(),
  agg.unidad_codigo, agg.unidad_nombre, CONVERT(varchar(50), agg.server_id),
  CONVERT(varchar(50), agg.sucursal_origen_id), agg.unidad_nombre,
  agg.system_type, agg.fecha_op, agg.fecha_hora, agg.ticket, agg.id_trans,
  LEFT(agg.codigo, 100), p.ProductoID, LEFT(COALESCE(p.Nombre, agg.nombre_item), 300),
  p.FamiliaID, LEFT(p.FamiliaNombre, 200), NULL, LEFT(p.SubFamiliaNombre, 200),
  LEFT(e.casa_comercial, 100), e.grado_alcohol, ISNULL(e.es_alcoholico, 0),
  agg.cant, CASE WHEN agg.cant > 0 THEN agg.importe / agg.cant ELSE NULL END,
  agg.importe, agg.importe, 0, 0, agg.pax,
  %s, agg.hash_origen, SYSUTCDATETIME(), 1
FROM (
  SELECT
    u.codigo AS unidad_codigo, u.nombre AS unidad_nombre, u.server_id,
    u.sucursal_origen_id, u.system_type,
    CAST(s.FechaHora AS DATE) AS fecha_op, MIN(s.FechaHora) AS fecha_hora,
    s.NumeroTicket AS ticket, LEFT(MIN(ISNULL(s.IdTransaccion, s.id)), 64) AS id_trans,
    LTRIM(RTRIM(JSON_VALUE(j.value,'$.id'))) AS codigo,
    MAX(JSON_VALUE(j.value,'$.name')) AS nombre_item, MAX(s.Pax) AS pax,
    SUM(TRY_CONVERT(decimal(18,6), JSON_VALUE(j.value,'$.quantity'))) AS cant,
    SUM(TRY_CONVERT(decimal(18,6), JSON_VALUE(j.value,'$.total'))) AS importe,
    CONVERT(varchar(64), HASHBYTES('SHA2_256', CONCAT(
      u.codigo,'|',s.NumeroTicket,'|',CONVERT(varchar(10),CAST(s.FechaHora AS DATE),120),
      '|',LTRIM(RTRIM(JSON_VALUE(j.value,'$.id'))))), 2) AS hash_origen
  FROM dbo.Sync_Sales s
  JOIN dbo.Unidades_Negocio u ON u.codigo = s.UnidadNegocio
  CROSS APPLY OPENJSON(s.items) j
  WHERE s.UnidadNegocio = %s
    AND s.FechaHora >= %s AND s.FechaHora < %s
    AND s.items IS NOT NULL AND LEN(s.items) > 5
    AND JSON_VALUE(j.value,'$.id') IS NOT NULL
  GROUP BY u.codigo, u.nombre, u.server_id, u.sucursal_origen_id, u.system_type,
           CAST(s.FechaHora AS DATE), s.NumeroTicket, LTRIM(RTRIM(JSON_VALUE(j.value,'$.id')))
) agg
LEFT JOIN dbo.Sync_Productos p
       ON LTRIM(RTRIM(p.CodigoFuente)) = agg.codigo AND p.ServerID = agg.server_id
LEFT JOIN dbo.Comercial_Productos_Enriquecidos e ON e.producto_id = p.ProductoID
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.Comercial_Inteligencia_VentasDetalleProducto t
  WHERE t.id_transaccion = agg.id_trans AND t.numero_ticket = agg.ticket
    AND t.producto_codigo_fuente = agg.codigo AND t.fecha_operacion = agg.fecha_op
);
"""


def _meses(desde: date, hasta: date):
    y, m = desde.year, desde.month
    while date(y, m, 1) < hasta:
        ini = date(y, m, 1)
        if m == 12:
            y2, m2 = y + 1, 1
        else:
            y2, m2 = y, m + 1
        yield ini, date(y2, m2, 1)
        y, m = y2, m2


def poblar(unidad_filtro=None, desde=None, hasta=None):
    run_id = f"PIC-DET-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4]}"
    conn = _etl_conn()
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT codigo, CONVERT(varchar(36),server_id) sid FROM dbo.Unidades_Negocio "
                "WHERE activo=1 AND server_id IS NOT NULL ORDER BY codigo")
    unidades = [r["codigo"] for r in cur.fetchall()]
    if unidad_filtro:
        unidades = [u for u in unidades if u == unidad_filtro]

    total = 0
    for unidad in unidades:
        cur.execute("SELECT MIN(CAST(FechaHora AS DATE)) mn, MAX(CAST(FechaHora AS DATE)) mx "
                    "FROM dbo.Sync_Sales WHERE UnidadNegocio=%s AND items IS NOT NULL", (unidad,))
        rg = cur.fetchone()
        if not rg or not rg["mn"]:
            logger.info(f"[{unidad}] sin ventas; omitido")
            continue

        def _as_date(v):
            return datetime.strptime(v, "%Y-%m-%d").date() if isinstance(v, str) else v

        mn, mx = _as_date(rg["mn"]), _as_date(rg["mx"])
        u_desde = _as_date(desde) if desde else mn
        # fin exclusivo = primer día del mes siguiente al último con ventas
        u_hasta = _as_date(hasta) if hasta else date(
            mx.year + (mx.month // 12), (mx.month % 12) + 1, 1)
        u_sub = 0
        for ini, fin in _meses(u_desde, u_hasta):
            cur2 = conn.cursor()
            cur2.execute(_INSERT_SQL, (run_id, unidad, ini.isoformat(), fin.isoformat()))
            n = cur2.rowcount
            conn.commit()
            u_sub += max(n, 0)
            logger.info(f"[{unidad}] {ini:%Y-%m}: +{n} líneas")
        logger.info(f"[{unidad}] TOTAL +{u_sub}")
        total += u_sub
    conn.close()
    logger.info(f"==== FIN run={run_id} total_lineas={total} ====")
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--unidad", default=None)
    ap.add_argument("--desde", default=None)
    ap.add_argument("--hasta", default=None)
    a = ap.parse_args()
    poblar(a.unidad, a.desde, a.hasta)
