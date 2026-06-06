"""
Backfill Sync_Precios_Historicos desde Sync_Productos
Versión optimizada con INSERT directo (sin loop de verificación)
"""
import os
import argparse
import pymssql
from datetime import date

def conn_edarsa():
    return pymssql.connect(
        server=os.getenv('EDARSAHUB_SQL_HOST'),
        port=int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
        database=os.getenv('EDARSAHUB_SQL_DATABASE'),
        user=os.getenv('EDARSAHUB_SQL_USER'),
        password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
        login_timeout=30,
        autocommit=False
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--fecha-vigencia", default=date.today().isoformat())
    args = ap.parse_args()

    cn = conn_edarsa()
    cur = cn.cursor()

    print(f"Fecha vigencia: {args.fecha_vigencia}")

    # Contar registros fuente
    cur.execute("SELECT COUNT(*) FROM Sync_Productos WHERE ISNULL(PrecioVenta,0) > 0")
    total_fuente = cur.fetchone()[0]
    print(f"Total productos con precio en fuente: {total_fuente}")

    # Contar existentes en destino para esta fecha
    cur.execute("SELECT COUNT(*) FROM Sync_Precios_Historicos WHERE FechaVigencia = %s", (args.fecha_vigencia,))
    existentes = cur.fetchone()[0]
    print(f"Existentes en destino para {args.fecha_vigencia}: {existentes}")

    # INSERT directo excluyendo duplicados
    insert_sql = f"""
    INSERT INTO Sync_Precios_Historicos (
        PrecioHistoricoID,
        ServerID,
        SucursalID,
        ProductoID,
        ProductoCodigo,
        ProductoNombre,
        FechaVigencia,
        FechaFinVigencia,
        PrecioBase,
        PrecioFinal,
        ImpuestoIncluido,
        TasaImpuesto,
        PrecioAnterior,
        VariacionPorcentaje,
        MotivosCambio,
        UsuarioModificacion,
        FechaSync
    )
    SELECT
        CAST(NEWID() AS NVARCHAR(100)),
        CAST(sp.ServerID AS NVARCHAR(100)),
        'DEFAULT',
        CAST(sp.ProductoID AS NVARCHAR(100)),
        ISNULL(sp.CodigoFuente, ''),
        ISNULL(sp.Nombre, ''),
        '{args.fecha_vigencia}',
        NULL,
        ISNULL(sp.PrecioSinImpuestos, sp.PrecioVenta),
        sp.PrecioVenta,
        1,
        ISNULL(sp.TasaImpuesto, 16.00),
        NULL,
        NULL,
        'BACKFILL_INICIAL_DESDE_SYNC_PRODUCTOS',
        'SYSTEM_BACKFILL',
        SYSDATETIME()
    FROM Sync_Productos sp
    WHERE ISNULL(sp.PrecioVenta, 0) > 0
      AND NOT EXISTS (
          SELECT 1 FROM Sync_Precios_Historicos h
          WHERE h.ServerID = CAST(sp.ServerID AS NVARCHAR(100))
            AND h.ProductoID = CAST(sp.ProductoID AS NVARCHAR(100))
            AND h.FechaVigencia = '{args.fecha_vigencia}'
      )
    """

    if args.commit:
        print("\nEjecutando INSERT...")
        cur.execute(insert_sql)
        rows_inserted = cur.rowcount
        cn.commit()
        print(f"COMMIT OK - Registros insertados: {rows_inserted}")
    else:
        # Dry-run: contar cuántos se insertarían
        count_sql = f"""
        SELECT COUNT(*)
        FROM Sync_Productos sp
        WHERE ISNULL(sp.PrecioVenta, 0) > 0
          AND NOT EXISTS (
              SELECT 1 FROM Sync_Precios_Historicos h
              WHERE h.ServerID = CAST(sp.ServerID AS NVARCHAR(100))
                AND h.ProductoID = CAST(sp.ProductoID AS NVARCHAR(100))
                AND h.FechaVigencia = '{args.fecha_vigencia}'
          )
        """
        cur.execute(count_sql)
        insertables = cur.fetchone()[0]
        print(f"\nDRY-RUN - Registros que se insertarían: {insertables}")

    # Total final
    cur.execute("SELECT COUNT(*) FROM Sync_Precios_Historicos")
    total_destino = cur.fetchone()[0]
    print(f"Total en destino: {total_destino}")

    cn.close()

if __name__ == "__main__":
    main()
