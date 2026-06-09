"""
Migración: Clasificación Comercial Canónica de Producto.
=========================================================
La clasificación comercial (ALIMENTOS/BEBIDAS/OTROS/PENDIENTE_CLASIFICACION) deja
de ser un CASE en los endpoints y pasa a ser DATO CANÓNICO del producto, alimentado
desde un catálogo controlado.

- dbo.Comercial_ClasificacionesProducto: catálogo controlado de clasificaciones.
- dbo.Sync_Productos += ClasificacionProductoID (FK) + ClasificacionOrigen + ClasificacionFecha
  (trazabilidad). Columnas NULLABLES → seguras; el MERGE del sync las preserva.

Backfill (idempotente, NO pisa clasificación 'MANUAL'):
- SOFTRESTAURANT_PRO → SOLO por prefijo de familia 'A '/'B ' (regla NO global). Resto → PENDIENTE.
- MPRO → SOLO por CategoriaNombre (ALIMENTOS/BEBIDAS; otra categoría → OTROS; vacía → PENDIENTE).
- Cualquier otro sistema → PENDIENTE (jamás se aplica A/B fuera de SoftRestaurant).

Re-ejecutable post-sync: reclasifica solo filas con ClasificacionProductoID NULL.

Uso: cd /app/backend && set -a && source .env && set +a && \
     python -m migrations.comercial_clasificacion_producto_20260609
"""
import logging
from core.sql_first.db import get_sql_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mig_clasificacion_producto")

DDL_CATALOGO = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Comercial_ClasificacionesProducto')
BEGIN
  CREATE TABLE dbo.Comercial_ClasificacionesProducto (
    ClasificacionProductoID INT IDENTITY(1,1) NOT NULL,
    Codigo                  VARCHAR(40)   NOT NULL,
    Nombre                  NVARCHAR(120) NOT NULL,
    Descripcion             NVARCHAR(400) NULL,
    Activo                  BIT           NOT NULL CONSTRAINT DF_CCP_Activo DEFAULT(1),
    Orden                   INT           NOT NULL CONSTRAINT DF_CCP_Orden  DEFAULT(0),
    FechaCreacion           DATETIME2     NOT NULL CONSTRAINT DF_CCP_FCrea  DEFAULT(SYSDATETIME()),
    FechaActualizacion      DATETIME2     NULL,
    CreadoPor               NVARCHAR(120) NULL,
    ActualizadoPor          NVARCHAR(120) NULL,
    CONSTRAINT PK_Comercial_ClasificacionesProducto PRIMARY KEY (ClasificacionProductoID),
    CONSTRAINT UX_CCP_Codigo UNIQUE (Codigo)
  );
END;
"""

SEED = """
IF NOT EXISTS (SELECT 1 FROM dbo.Comercial_ClasificacionesProducto WHERE Codigo=%s)
INSERT INTO dbo.Comercial_ClasificacionesProducto (Codigo, Nombre, Descripcion, Orden, CreadoPor)
VALUES (%s, %s, %s, %s, N'migracion_clasificacion');
"""
CLASIFICACIONES = [
    ("ALIMENTOS", "Alimentos", "Productos de cocina/alimentos", 1),
    ("BEBIDAS", "Bebidas", "Bebidas (con o sin alcohol)", 2),
    ("OTROS", "Otros", "No-alimentos/no-bebidas (gastos, cavas, etc.)", 3),
    ("PENDIENTE_CLASIFICACION", "Pendiente de clasificación",
     "Sin clasificación confiable; requiere revisión", 99),
]

DDL_COLUMNAS = """
IF COL_LENGTH('dbo.Sync_Productos','ClasificacionProductoID') IS NULL
  ALTER TABLE dbo.Sync_Productos ADD ClasificacionProductoID INT NULL;
IF COL_LENGTH('dbo.Sync_Productos','ClasificacionOrigen') IS NULL
  ALTER TABLE dbo.Sync_Productos ADD ClasificacionOrigen VARCHAR(40) NULL;
IF COL_LENGTH('dbo.Sync_Productos','ClasificacionFecha') IS NULL
  ALTER TABLE dbo.Sync_Productos ADD ClasificacionFecha DATETIME2 NULL;
"""

DDL_FK_IX = """
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name='FK_SyncProductos_Clasificacion')
  ALTER TABLE dbo.Sync_Productos WITH NOCHECK
    ADD CONSTRAINT FK_SyncProductos_Clasificacion
    FOREIGN KEY (ClasificacionProductoID)
    REFERENCES dbo.Comercial_ClasificacionesProducto (ClasificacionProductoID);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_SyncProductos_Clasificacion')
  CREATE INDEX IX_SyncProductos_Clasificacion ON dbo.Sync_Productos (ClasificacionProductoID);
"""

# Backfill idempotente: cada UPDATE solo toca filas NULL y NUNCA pisa Origen='MANUAL'.
BACKFILL = """
DECLARE @ALI INT = (SELECT ClasificacionProductoID FROM dbo.Comercial_ClasificacionesProducto WHERE Codigo='ALIMENTOS');
DECLARE @BEB INT = (SELECT ClasificacionProductoID FROM dbo.Comercial_ClasificacionesProducto WHERE Codigo='BEBIDAS');
DECLARE @OTR INT = (SELECT ClasificacionProductoID FROM dbo.Comercial_ClasificacionesProducto WHERE Codigo='OTROS');
DECLARE @PEN INT = (SELECT ClasificacionProductoID FROM dbo.Comercial_ClasificacionesProducto WHERE Codigo='PENDIENTE_CLASIFICACION');

-- (1) SOFTRESTAURANT_PRO → SOLO prefijo de familia
UPDATE sp SET ClasificacionProductoID=@ALI, ClasificacionOrigen='PREFIJO_FAMILIA_AB', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='SOFTRESTAURANT_PRO' AND LEFT(LTRIM(sp.FamiliaNombre),2)='A ' AND sp.ClasificacionProductoID IS NULL;

UPDATE sp SET ClasificacionProductoID=@BEB, ClasificacionOrigen='PREFIJO_FAMILIA_AB', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='SOFTRESTAURANT_PRO' AND LEFT(LTRIM(sp.FamiliaNombre),2)='B ' AND sp.ClasificacionProductoID IS NULL;

UPDATE sp SET ClasificacionProductoID=@PEN, ClasificacionOrigen='PREFIJO_FAMILIA_AB', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='SOFTRESTAURANT_PRO' AND LEFT(LTRIM(sp.FamiliaNombre),2) NOT IN ('A ','B ')
  AND sp.ClasificacionProductoID IS NULL;

-- (2) MPRO → SOLO CategoriaNombre
UPDATE sp SET ClasificacionProductoID=@ALI, ClasificacionOrigen='MPRO_CATEGORIA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='MPRO' AND UPPER(LTRIM(RTRIM(ISNULL(sp.CategoriaNombre,''))))='ALIMENTOS'
  AND sp.ClasificacionProductoID IS NULL;

UPDATE sp SET ClasificacionProductoID=@BEB, ClasificacionOrigen='MPRO_CATEGORIA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='MPRO' AND UPPER(LTRIM(RTRIM(ISNULL(sp.CategoriaNombre,''))))='BEBIDAS'
  AND sp.ClasificacionProductoID IS NULL;

UPDATE sp SET ClasificacionProductoID=@OTR, ClasificacionOrigen='MPRO_CATEGORIA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='MPRO' AND LTRIM(RTRIM(ISNULL(sp.CategoriaNombre,'')))<>''
  AND UPPER(LTRIM(RTRIM(sp.CategoriaNombre))) NOT IN ('ALIMENTOS','BEBIDAS')
  AND sp.ClasificacionProductoID IS NULL;

UPDATE sp SET ClasificacionProductoID=@PEN, ClasificacionOrigen='MPRO_CATEGORIA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.SystemType='MPRO' AND LTRIM(RTRIM(ISNULL(sp.CategoriaNombre,'')))=''
  AND sp.ClasificacionProductoID IS NULL;

-- (3) Resto → PENDIENTE (jamás A/B global)
UPDATE sp SET ClasificacionProductoID=@PEN, ClasificacionOrigen='NO_REGLA', ClasificacionFecha=SYSDATETIME()
FROM dbo.Sync_Productos sp
WHERE sp.ClasificacionProductoID IS NULL;
"""


def run():
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)

    logger.info("1) Catálogo de clasificaciones (idempotente)…")
    cur.execute(DDL_CATALOGO)
    conn.commit()
    for codigo, nombre, desc, orden in CLASIFICACIONES:
        cur.execute(SEED, (codigo, codigo, nombre, desc, orden))
    conn.commit()

    logger.info("2) Columnas + FK + índice en Sync_Productos (idempotente)…")
    cur.execute(DDL_COLUMNAS)
    conn.commit()
    cur.execute(DDL_FK_IX)
    conn.commit()

    logger.info("3) Backfill idempotente…")
    cur.execute(BACKFILL)
    conn.commit()

    # Validación
    cur.execute("""
        SELECT cc.Codigo, COUNT(*) n FROM dbo.Sync_Productos sp
        JOIN dbo.Comercial_ClasificacionesProducto cc ON cc.ClasificacionProductoID=sp.ClasificacionProductoID
        GROUP BY cc.Codigo ORDER BY n DESC
    """)
    for r in cur.fetchall():
        logger.info("   %-26s %s", r["Codigo"], r["n"])
    cur.execute("SELECT COUNT(*) n FROM dbo.Sync_Productos WHERE ClasificacionProductoID IS NULL")
    sin = cur.fetchone()["n"]
    logger.info("   SIN CLASIFICAR (NULL): %s (esperado 0)", sin)
    logger.info("==== OK ====")
    conn.close()


if __name__ == "__main__":
    run()
