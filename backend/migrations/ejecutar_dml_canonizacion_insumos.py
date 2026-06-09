"""
PASO 2 (Ruta B) - Canonización de insumos: Sync_Productos_Insumos -> Producto_Catalogo + puente.
Set-based, idempotente. SKU = GUID (InsumoID). CodigoProducto = 'INS-#######' secuencial.
Alcance: solo insumos con CodigoFuente válido. descartados = 0 (no resueltos no se fuerzan).
Valida y reporta. No imprime secretos.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection

INSERT_CATALOGO = """
DECLARE @base INT = ISNULL((SELECT MAX(CAST(SUBSTRING(CodigoProducto,5,7) AS INT))
                            FROM Producto_Catalogo WHERE CodigoProducto LIKE 'INS-%'),0);
INSERT INTO Producto_Catalogo
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
    ISNULL(s.Activo,1), GETDATE()
FROM Sync_Productos_Insumos s
WHERE s.CodigoFuente IS NOT NULL AND LTRIM(RTRIM(s.CodigoFuente)) <> ''
  AND NOT EXISTS (SELECT 1 FROM Producto_MapeoOrigen m WHERE m.OrigenInsumoID = s.InsumoID);
"""

INSERT_PUENTE = """
INSERT INTO Producto_MapeoOrigen (ServerID, SystemType, CodigoFuente, ProductoID, OrigenInsumoID)
SELECT s.ServerID, LEFT(s.SystemType,40), LEFT(s.CodigoFuente,100), pc.ProductoID, s.InsumoID
FROM Sync_Productos_Insumos s
JOIN Producto_Catalogo pc ON pc.SKU = CONVERT(varchar(36), s.InsumoID)
WHERE s.CodigoFuente IS NOT NULL AND LTRIM(RTRIM(s.CodigoFuente)) <> ''
  AND NOT EXISTS (SELECT 1 FROM Producto_MapeoOrigen m WHERE m.OrigenInsumoID = s.InsumoID);
"""


def scalar(cur, q, p=()):
    cur.execute(q, p); return cur.fetchone()[0]


def main():
    conn = get_sql_connection()
    cur = conn.cursor()

    elegibles = scalar(cur, "SELECT COUNT(*) FROM Sync_Productos_Insumos WHERE CodigoFuente IS NOT NULL AND LTRIM(RTRIM(CodigoFuente))<>''")
    cat_antes = scalar(cur, "SELECT COUNT(*) FROM Producto_Catalogo")
    puente_antes = scalar(cur, "SELECT COUNT(*) FROM Producto_MapeoOrigen")
    print(f"[PRE] insumos elegibles={elegibles} | Producto_Catalogo={cat_antes} | puente={puente_antes}")

    try:
        cur.execute(INSERT_CATALOGO)
        cur.execute(INSERT_PUENTE)
        conn.commit()
        print("[OK] DML ejecutado y commit.")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] rollback. {str(e)[:200]}")
        conn.close(); return

    # Validaciones
    cat_post = scalar(cur, "SELECT COUNT(*) FROM Producto_Catalogo")
    puente_post = scalar(cur, "SELECT COUNT(*) FROM Producto_MapeoOrigen")
    print(f"\n[POST] Producto_Catalogo={cat_post} (+{cat_post-cat_antes}) | puente={puente_post} (+{puente_post-puente_antes})")

    huerfanos = scalar(cur, "SELECT COUNT(*) FROM Producto_MapeoOrigen m WHERE NOT EXISTS (SELECT 1 FROM Producto_Catalogo pc WHERE pc.ProductoID=m.ProductoID)")
    print(f"[FK] puente->catalogo huérfanos: {huerfanos} (debe ser 0)")

    dup_cod = scalar(cur, "SELECT COUNT(*) FROM (SELECT CodigoProducto FROM Producto_Catalogo GROUP BY CodigoProducto HAVING COUNT(*)>1) t")
    dup_sku = scalar(cur, "SELECT COUNT(*) FROM (SELECT SKU FROM Producto_Catalogo GROUP BY SKU HAVING COUNT(*)>1) t")
    print(f"[UNIQUE] CodigoProducto dups={dup_cod} | SKU dups={dup_sku} (deben ser 0)")

    descartados = elegibles - (puente_post - puente_antes)
    print(f"[COBERTURA] elegibles={elegibles} mapeados={puente_post-puente_antes} descartados={descartados} (debe ser 0)")

    print("\n[POR SERVER] mapeos en puente:")
    cur2 = conn.cursor(as_dict=True)
    cur2.execute("SELECT ServerID, SystemType, COUNT(*) n FROM Producto_MapeoOrigen GROUP BY ServerID, SystemType ORDER BY n DESC")
    for r in cur2.fetchall():
        print(f"   {r['ServerID']} {r['SystemType']}: {r['n']}")

    conn.close()


if __name__ == "__main__":
    main()
