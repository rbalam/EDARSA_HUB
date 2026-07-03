/*
EDARSAHUB Finanzas / Presupuestos
Migración canónica por Unidad de Negocio.

Reglas:
- No MongoDB.
- No conexiones live.
- No datos demo.
- No RH_Cat_Sucursales como FK primaria.
- FK canónica: dbo.Unidades_Negocio(id).

Si existe dbo.Finanzas_Presupuestos legacy sin UnidadNegocioID:
- se renombra a dbo.Finanzas_Presupuestos_Legacy_Backup
- se crea una nueva dbo.Finanzas_Presupuestos canónica vacía
*/

SET XACT_ABORT ON;

BEGIN TRAN;

IF OBJECT_ID('dbo.Unidades_Negocio', 'U') IS NULL
BEGIN
    THROW 51000, 'Falta tabla canonica dbo.Unidades_Negocio. No se puede crear Finanzas_Presupuestos.', 1;
END;

IF OBJECT_ID('dbo.Finanzas_Presupuestos', 'U') IS NOT NULL
   AND COL_LENGTH('dbo.Finanzas_Presupuestos', 'UnidadNegocioID') IS NULL
BEGIN
    IF OBJECT_ID('dbo.Finanzas_Presupuestos_Legacy_Backup', 'U') IS NULL
    BEGIN
        EXEC sp_rename 'dbo.Finanzas_Presupuestos', 'Finanzas_Presupuestos_Legacy_Backup';
    END
    ELSE
    BEGIN
        THROW 51001, 'Ya existe dbo.Finanzas_Presupuestos_Legacy_Backup. Revisar antes de sobrescribir respaldo legacy.', 1;
    END;
END;

IF OBJECT_ID('dbo.Finanzas_Presupuestos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Finanzas_Presupuestos (
        PresupuestoID INT IDENTITY(1,1) NOT NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NOT NULL,
        Categoria NVARCHAR(100) NOT NULL,
        SubCategoria NVARCHAR(100) NULL,
        Tipo NVARCHAR(20) NOT NULL,
        Monto_Presupuestado DECIMAL(18,2) NOT NULL
            CONSTRAINT DF_Finanzas_Presupuestos_MontoPresupuestado DEFAULT (0),
        Monto_Ejecutado DECIMAL(18,2) NOT NULL
            CONSTRAINT DF_Finanzas_Presupuestos_MontoEjecutado DEFAULT (0),
        Anio INT NOT NULL,
        Mes INT NOT NULL,
        Notas NVARCHAR(500) NULL,
        Activo BIT NOT NULL
            CONSTRAINT DF_Finanzas_Presupuestos_Activo DEFAULT (1),
        Fecha_Creacion DATETIME2(0) NOT NULL
            CONSTRAINT DF_Finanzas_Presupuestos_FechaCreacion DEFAULT (SYSUTCDATETIME()),
        Fecha_Modificacion DATETIME2(0) NULL,
        Creado_Por NVARCHAR(100) NULL,
        Modificado_Por NVARCHAR(100) NULL,

        CONSTRAINT PK_Finanzas_Presupuestos
            PRIMARY KEY CLUSTERED (PresupuestoID),

        CONSTRAINT CK_Finanzas_Presupuestos_Tipo
            CHECK (Tipo IN ('Ingreso', 'Egreso')),

        CONSTRAINT CK_Finanzas_Presupuestos_Mes
            CHECK (Mes BETWEEN 1 AND 12),

        CONSTRAINT FK_Finanzas_Presupuestos_UnidadNegocio
            FOREIGN KEY (UnidadNegocioID)
            REFERENCES dbo.Unidades_Negocio(id)
    );
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_Finanzas_Presupuestos_Periodo'
      AND object_id = OBJECT_ID('dbo.Finanzas_Presupuestos')
)
BEGIN
    CREATE INDEX IX_Finanzas_Presupuestos_Periodo
    ON dbo.Finanzas_Presupuestos(Anio, Mes, Activo);
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_Finanzas_Presupuestos_Unidad'
      AND object_id = OBJECT_ID('dbo.Finanzas_Presupuestos')
)
BEGIN
    CREATE INDEX IX_Finanzas_Presupuestos_Unidad
    ON dbo.Finanzas_Presupuestos(UnidadNegocioID, Anio, Mes, Activo);
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_Finanzas_Presupuestos_Categoria'
      AND object_id = OBJECT_ID('dbo.Finanzas_Presupuestos')
)
BEGIN
    CREATE INDEX IX_Finanzas_Presupuestos_Categoria
    ON dbo.Finanzas_Presupuestos(Categoria, Tipo, Activo);
END;

COMMIT;

SELECT
    'OK' AS Estatus,
    OBJECT_ID('dbo.Finanzas_Presupuestos') AS FinanzasPresupuestosObjectID,
    OBJECT_ID('dbo.Finanzas_Presupuestos_Legacy_Backup') AS LegacyBackupObjectID;
