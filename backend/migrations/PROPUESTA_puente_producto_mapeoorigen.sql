-- =====================================================================
-- PROPUESTA DDL (NO EJECUTADA) - Puente canónico POS -> ProductoID(int)
-- =====================================================================
-- Ruta B (int estricta). Pendiente de APROBACIÓN explícita del usuario.
-- Prueba de inexistencia de equivalente: scripts/diag_prueba_no_puente_safe.py
--   -> "NO existe ninguna tabla puente equivalente POS->ProductoID(int)".
--
-- OBJETIVO: resolver sin colisión (ServerID + SystemType + CodigoFuente) -> ProductoID
-- porque `Producto_Catalogo` NO tiene dimensión de origen y los CodigoFuente
-- colisionan entre unidades.
--
-- ALCANCE INICIAL: solo insumos inventariables usados por movimientos.
-- NO crea columnas en tablas existentes. NO altera FKs existentes.
-- =====================================================================

-- ---------- FORWARD (crear puente) ----------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Producto_MapeoOrigen')
BEGIN
    CREATE TABLE dbo.Producto_MapeoOrigen (
        MapeoOrigenID   INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ServerID        UNIQUEIDENTIFIER  NOT NULL,
        SystemType      VARCHAR(40)       NOT NULL,
        CodigoFuente    VARCHAR(100)      NOT NULL,
        ProductoID      INT               NOT NULL,   -- FK -> Producto_Catalogo.ProductoID
        OrigenInsumoID  UNIQUEIDENTIFIER  NULL,        -- traza GUID Sync_Productos_Insumos.InsumoID
        Activo          BIT               NOT NULL CONSTRAINT DF_PMO_Activo DEFAULT (1),
        FechaCreacion   DATETIME2         NOT NULL CONSTRAINT DF_PMO_Fecha DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_PMO_Producto FOREIGN KEY (ProductoID)
            REFERENCES dbo.Producto_Catalogo (ProductoID),
        CONSTRAINT UQ_PMO_Origen UNIQUE (ServerID, SystemType, CodigoFuente)
    );

    CREATE INDEX IX_PMO_Producto ON dbo.Producto_MapeoOrigen (ProductoID);
END
GO

-- ---------- ROLLBACK (revertir puente) ----------
-- Seguro e idempotente. No afecta Producto_Catalogo ni otras tablas.
-- IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Producto_MapeoOrigen')
--     DROP TABLE dbo.Producto_MapeoOrigen;
-- GO

-- =====================================================================
-- NOTA DE CANONIZACIÓN (DML, fase posterior, también pendiente de aprobación):
--   1) INSERT en Producto_Catalogo desde Sync_Productos_Insumos (solo inventariables),
--      asignando ProductoID(int) por IDENTITY.
--   2) INSERT en Producto_MapeoOrigen (ServerID, SystemType, CodigoFuente, ProductoID, OrigenInsumoID).
--   3) Idempotente vía UQ_PMO_Origen (re-ejecutar no duplica).
--   4) No resueltos -> staging/pendientes. descartados = 0.
-- =====================================================================
