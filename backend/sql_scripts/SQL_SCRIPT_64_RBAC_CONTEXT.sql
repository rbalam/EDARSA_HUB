-- =====================================================
-- SQL SCRIPT 64 - RBAC Context (Tabla + Migración + Vista)
-- Ejecutar en SQL Server
-- =====================================================
SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /* =========================================================
       1) TABLA CONTEXTUAL
       ========================================================= */
    IF OBJECT_ID('dbo.Usuario_RolesContexto', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Usuario_RolesContexto (
            UsuarioRolContextoID BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            UsuarioID INT NOT NULL,
            RolID INT NOT NULL,

            EmpresaID INT NULL,
            UnidadNegocioID UNIQUEIDENTIFIER NULL,
            SucursalID INT NULL,

            EsRolPrimario BIT NOT NULL CONSTRAINT DF_Usuario_RolesContexto_EsRolPrimario DEFAULT(0),
            Activo BIT NOT NULL CONSTRAINT DF_Usuario_RolesContexto_Activo DEFAULT(1),

            FechaAlta DATETIME2 NOT NULL CONSTRAINT DF_Usuario_RolesContexto_FechaAlta DEFAULT(SYSDATETIME()),
            FechaBaja DATETIME2 NULL,

            Observaciones NVARCHAR(500) NULL,

            CreatedAt DATETIME2 NOT NULL CONSTRAINT DF_Usuario_RolesContexto_CreatedAt DEFAULT(SYSDATETIME()),
            CreatedBy NVARCHAR(100) NULL,
            UpdatedAt DATETIME2 NULL,
            UpdatedBy NVARCHAR(100) NULL
        );
    END

    /* =========================================================
       2) FOREIGN KEYS
       ========================================================= */
    IF NOT EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE name = 'FK_Usuario_RolesContexto_Usuario'
    )
    BEGIN
        ALTER TABLE dbo.Usuario_RolesContexto
            ADD CONSTRAINT FK_Usuario_RolesContexto_Usuario
            FOREIGN KEY (UsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID);
    END

    IF NOT EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE name = 'FK_Usuario_RolesContexto_Rol'
    )
    BEGIN
        ALTER TABLE dbo.Usuario_RolesContexto
            ADD CONSTRAINT FK_Usuario_RolesContexto_Rol
            FOREIGN KEY (RolID) REFERENCES dbo.Usuario_Roles(RolID);
    END

    /* =========================================================
       3) INDICES
       ========================================================= */
    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'IX_Usuario_RolesContexto_Usuario'
          AND object_id = OBJECT_ID('dbo.Usuario_RolesContexto')
    )
    BEGIN
        CREATE INDEX IX_Usuario_RolesContexto_Usuario
            ON dbo.Usuario_RolesContexto(UsuarioID, Activo, UnidadNegocioID, EmpresaID, SucursalID);
    END

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'IX_Usuario_RolesContexto_Contexto'
          AND object_id = OBJECT_ID('dbo.Usuario_RolesContexto')
    )
    BEGIN
        CREATE INDEX IX_Usuario_RolesContexto_Contexto
            ON dbo.Usuario_RolesContexto(UnidadNegocioID, EmpresaID, SucursalID, Activo);
    END

    IF NOT EXISTS (
        SELECT 1 FROM sys.indexes
        WHERE name = 'UX_Usuario_RolesContexto_UniqueActivo'
          AND object_id = OBJECT_ID('dbo.Usuario_RolesContexto')
    )
    BEGIN
        CREATE UNIQUE INDEX UX_Usuario_RolesContexto_UniqueActivo
            ON dbo.Usuario_RolesContexto(UsuarioID, RolID, EmpresaID, UnidadNegocioID, SucursalID, Activo)
            WHERE Activo = 1;
    END

    /* =========================================================
       4) MIGRACION DESDE LEGACY
       ========================================================= */
    IF OBJECT_ID('dbo.Usuario_RolesAsignacion', 'U') IS NOT NULL
    BEGIN
        INSERT INTO dbo.Usuario_RolesContexto (
            UsuarioID,
            RolID,
            EmpresaID,
            UnidadNegocioID,
            SucursalID,
            EsRolPrimario,
            Activo,
            FechaAlta,
            Observaciones,
            CreatedAt,
            CreatedBy
        )
        SELECT
            ura.UsuarioID,
            ura.RolID,
            NULL AS EmpresaID,
            NULL AS UnidadNegocioID,
            NULL AS SucursalID,
            1 AS EsRolPrimario,
            CASE WHEN ISNULL(ura.Activo, 1) = 1 THEN 1 ELSE 0 END,
            ISNULL(ura.FechaAlta, SYSDATETIME()) AS FechaAlta,
            'MIGRADO_DESDE_Usuario_RolesAsignacion' AS Observaciones,
            ISNULL(ura.CreatedAt, SYSDATETIME()) AS CreatedAt,
            ISNULL(ura.CreatedBy, 'SCRIPT_SQL_64') AS CreatedBy
        FROM dbo.Usuario_RolesAsignacion ura
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.Usuario_RolesContexto x
            WHERE x.UsuarioID = ura.UsuarioID
              AND x.RolID = ura.RolID
              AND x.Activo = CASE WHEN ISNULL(ura.Activo, 1) = 1 THEN 1 ELSE 0 END
              AND x.EmpresaID IS NULL
              AND x.UnidadNegocioID IS NULL
              AND x.SucursalID IS NULL
        );
    END

    /* =========================================================
       5) VISTA CANONICA
       ========================================================= */
    IF OBJECT_ID('dbo.vw_Usuario_RolesContexto', 'V') IS NOT NULL
        DROP VIEW dbo.vw_Usuario_RolesContexto;
    EXEC('
        CREATE VIEW dbo.vw_Usuario_RolesContexto
        AS
        SELECT
            urc.UsuarioRolContextoID,
            urc.UsuarioID,
            u.Email,
            u.NombreCompleto,
            urc.RolID,
            r.NombreRol,
            urc.EmpresaID,
            e.NombreEmpresa,
            urc.UnidadNegocioID,
            un.nombre AS UnidadNegocioNombre,
            urc.SucursalID,
            s.NombreSucursal,
            urc.EsRolPrimario,
            urc.Activo,
            urc.FechaAlta,
            urc.FechaBaja,
            urc.Observaciones,
            urc.CreatedAt,
            urc.CreatedBy,
            urc.UpdatedAt,
            urc.UpdatedBy
        FROM dbo.Usuario_RolesContexto urc
        INNER JOIN dbo.Usuario_Catalogo u
            ON urc.UsuarioID = u.UsuarioID
        INNER JOIN dbo.Usuario_Roles r
            ON urc.RolID = r.RolID
        LEFT JOIN dbo.Sistema_Empresas e
            ON urc.EmpresaID = e.EmpresaID
        LEFT JOIN dbo.Unidades_Negocio un
            ON urc.UnidadNegocioID = un.id
        LEFT JOIN dbo.Sistema_Sucursales s
            ON urc.SucursalID = s.SucursalID;
    ');

    COMMIT TRANSACTION;
    PRINT 'OK - SCRIPT SQL 64 aplicado.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
