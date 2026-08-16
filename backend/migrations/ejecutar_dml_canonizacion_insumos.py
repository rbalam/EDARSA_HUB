"""Canonización controlada de insumos hacia catálogo y puente canónicos.

Por defecto solo audita. La escritura exige --apply más el conteo y fingerprint
obtenidos en el dry-run previo.
"""

import argparse
import hashlib
import logging
import sys

sys.path.insert(0, "/app/backend")
logging.disable(logging.CRITICAL)

from core.sql_first.db import get_sql_connection


TARGETS_SQL = """
SELECT
    s.InsumoID,
    s.ServerID,
    UPPER(LTRIM(RTRIM(s.SystemType))) AS SystemType,
    LTRIM(RTRIM(s.CodigoFuente)) AS CodigoFuente,
    LTRIM(RTRIM(s.Nombre)) AS Nombre,
    LTRIM(RTRIM(s.UnidadMedida)) AS UnidadMedida
FROM dbo.Sync_Productos_Insumos s {sync_lock}
WHERE s.Activo = 1
  AND s.CodigoFuente IS NOT NULL
  AND LTRIM(RTRIM(s.CodigoFuente)) <> ''
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.Producto_MapeoOrigen m {mapping_lock}
      WHERE m.OrigenInsumoID = s.InsumoID
        AND m.Activo = 1
  )
ORDER BY s.InsumoID
"""


INSERT_CATALOGO = """
DECLARE @base INT = ISNULL((
    SELECT MAX(TRY_CONVERT(INT, SUBSTRING(CodigoProducto, 5, 7)))
    FROM dbo.Producto_Catalogo WITH (UPDLOCK, HOLDLOCK)
    WHERE CodigoProducto LIKE 'INS-%'
), 0);
INSERT INTO dbo.Producto_Catalogo
   (CodigoProducto, SKU, NombreProducto, NombreCorto, Descripcion, MonedaID, TipoProducto,
    EsInventariable, EsServicio, PermiteVenta, PermiteCompra, PermiteVentaSinExistencia,
    UnidadInventario, UnidadVenta, UnidadCompra, PrecioVentaBase, PrecioCostoBase, TasaImpuesto,
    StockActual, StockMinimo, Activo, FechaAlta)
SELECT
    'INS-' + RIGHT('0000000' + CAST(@base + ROW_NUMBER() OVER (ORDER BY s.InsumoID) AS varchar(7)),7),
    CONVERT(varchar(36), s.InsumoID),
    LEFT(ISNULL(NULLIF(LTRIM(RTRIM(s.Nombre)),''), s.CodigoFuente),150),
    LEFT(ISNULL(NULLIF(LTRIM(RTRIM(s.Nombre)),''), s.CodigoFuente),80),
    LEFT(s.Descripcion,1000),
    1, 'PRODUCTO', 1, 0, 0, 1, 0,
    LEFT(ISNULL(NULLIF(LTRIM(RTRIM(s.UnidadMedida)),''),'PZA'),30),
    LEFT(ISNULL(NULLIF(LTRIM(RTRIM(s.UnidadMedida)),''),'PZA'),30),
    LEFT(ISNULL(NULLIF(LTRIM(RTRIM(s.UnidadMedida)),''),'PZA'),30),
    0, CASE WHEN COALESCE(s.CostoPromedio, s.UltimoCosto, s.Costo, 0) < 0 THEN 0
            ELSE COALESCE(s.CostoPromedio, s.UltimoCosto, s.Costo, 0) END, 0, 0, 0,
    1, GETDATE()
FROM dbo.Sync_Productos_Insumos s WITH (UPDLOCK, HOLDLOCK)
WHERE s.Activo = 1
  AND s.CodigoFuente IS NOT NULL
  AND LTRIM(RTRIM(s.CodigoFuente)) <> ''
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.Producto_MapeoOrigen m WITH (UPDLOCK, HOLDLOCK)
      WHERE m.OrigenInsumoID = s.InsumoID
        AND m.Activo = 1
  )
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.Producto_Catalogo pc WITH (UPDLOCK, HOLDLOCK)
      WHERE pc.SKU = CONVERT(varchar(36), s.InsumoID)
  );
"""


INSERT_PUENTE = """
INSERT INTO dbo.Producto_MapeoOrigen
    (ServerID, SystemType, CodigoFuente, ProductoID, OrigenInsumoID)
SELECT
    s.ServerID,
    LEFT(s.SystemType, 40),
    LEFT(s.CodigoFuente, 100),
    pc.ProductoID,
    s.InsumoID
FROM dbo.Sync_Productos_Insumos s WITH (UPDLOCK, HOLDLOCK)
JOIN dbo.Producto_Catalogo pc WITH (UPDLOCK, HOLDLOCK)
  ON pc.SKU = CONVERT(varchar(36), s.InsumoID)
WHERE s.Activo = 1
  AND s.CodigoFuente IS NOT NULL
  AND LTRIM(RTRIM(s.CodigoFuente)) <> ''
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.Producto_MapeoOrigen m WITH (UPDLOCK, HOLDLOCK)
      WHERE m.OrigenInsumoID = s.InsumoID
        AND m.Activo = 1
  );
"""


def scalar(cur, query, params=()):
    cur.execute(query, params)
    return cur.fetchone()[0]


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Canoniza insumos con dry-run obligatorio por defecto."
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--expected-fingerprint")
    return parser.parse_args()


def _fetch_targets(conn, lock=False):
    lock_hint = "WITH (UPDLOCK, HOLDLOCK)" if lock else ""
    cur = conn.cursor(as_dict=True)
    cur.execute(
        TARGETS_SQL.format(sync_lock=lock_hint, mapping_lock=lock_hint)
    )
    return list(cur.fetchall())


def _target_fingerprint(rows):
    payload = "\n".join(
        "|".join(
            (
                str(row["InsumoID"]).upper(),
                str(row["ServerID"]).upper(),
                str(row["SystemType"] or "").upper(),
                str(row["CodigoFuente"] or "").strip(),
            )
        )
        for row in rows
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _print_dry_run(conn, rows, fingerprint):
    cur = conn.cursor()
    base = scalar(
        cur,
        """SELECT ISNULL(MAX(TRY_CONVERT(INT, SUBSTRING(CodigoProducto, 5, 7))), 0)
           FROM dbo.Producto_Catalogo
           WHERE CodigoProducto LIKE 'INS-%'""",
    )
    print(f"[DRY-RUN] objetivos={len(rows)} fingerprint={fingerprint}")
    for position, row in enumerate(rows, start=1):
        code = f"INS-{base + position:07d}"
        print(
            f"  {code} | {str(row['InsumoID']).upper()} | "
            f"{row['SystemType']} | {row['CodigoFuente']} | {row['Nombre']}"
        )


def _validate_apply_args(args, rows, fingerprint):
    if args.expected_count is None or not args.expected_fingerprint:
        raise RuntimeError(
            "--apply requiere --expected-count y --expected-fingerprint del dry-run"
        )
    if len(rows) != args.expected_count:
        raise RuntimeError(
            f"Alcance cambió: esperado={args.expected_count}, actual={len(rows)}"
        )
    if fingerprint.lower() != args.expected_fingerprint.lower():
        raise RuntimeError("Alcance cambió: fingerprint no coincide")


def main():
    args = _parse_args()
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        if not args.apply:
            rows = _fetch_targets(conn)
            fingerprint = _target_fingerprint(rows)
            _print_dry_run(conn, rows, fingerprint)
            conn.rollback()
            return 0

        cur.execute(
            "SET XACT_ABORT ON; "
            "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;"
        )
        rows = _fetch_targets(conn, lock=True)
        fingerprint = _target_fingerprint(rows)
        _validate_apply_args(args, rows, fingerprint)

        target_skus = [str(row["InsumoID"]) for row in rows]
        if target_skus:
            placeholders = ", ".join(["%s"] * len(target_skus))
            existing_catalog = scalar(
                cur,
                f"""SELECT COUNT(*)
                    FROM dbo.Producto_Catalogo WITH (UPDLOCK, HOLDLOCK)
                    WHERE SKU IN ({placeholders})""",
                tuple(target_skus),
            )
            if existing_catalog:
                raise RuntimeError(
                    f"Existen {existing_catalog} SKU objetivo sin puente; requiere auditoría"
                )

        cat_antes = scalar(cur, "SELECT COUNT(*) FROM dbo.Producto_Catalogo")
        puente_antes = scalar(cur, "SELECT COUNT(*) FROM dbo.Producto_MapeoOrigen")
        cur.execute(INSERT_CATALOGO)
        cur.execute(INSERT_PUENTE)

        cat_post = scalar(cur, "SELECT COUNT(*) FROM dbo.Producto_Catalogo")
        puente_post = scalar(cur, "SELECT COUNT(*) FROM dbo.Producto_MapeoOrigen")
        catalogo_insertado = cat_post - cat_antes
        puente_insertado = puente_post - puente_antes
        huerfanos = scalar(
            cur,
            """SELECT COUNT(*)
               FROM dbo.Producto_MapeoOrigen m
               WHERE NOT EXISTS (
                   SELECT 1
                   FROM dbo.Producto_Catalogo pc
                   WHERE pc.ProductoID = m.ProductoID
               )""",
        )
        if (
            catalogo_insertado != args.expected_count
            or puente_insertado != args.expected_count
            or huerfanos != 0
        ):
            raise RuntimeError(
                "Postcondición inválida; se revierte la transacción completa"
            )

        conn.commit()
        print(
            f"[OK] catalogo={catalogo_insertado} puente={puente_insertado} "
            f"fingerprint={fingerprint}"
        )
        return 0
    except Exception as exc:
        conn.rollback()
        print(f"[ERROR] rollback. {str(exc)[:200]}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
