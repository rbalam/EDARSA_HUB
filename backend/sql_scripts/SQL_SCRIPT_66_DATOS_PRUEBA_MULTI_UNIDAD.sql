-- =====================================================
-- SQL SCRIPT 66 - Datos de Prueba Multi-Unidad
-- SOLO PARA ENTORNO DE PRUEBA
-- Ajustar @UsuarioID según necesidad
-- =====================================================
SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @UsuarioID INT = 1; -- AJUSTAR AL USUARIO DESEADO
    DECLARE @Rol1 INT = (SELECT TOP 1 RolID FROM Usuario_Roles ORDER BY RolID);
    DECLARE @Rol2 INT = (SELECT TOP 1 RolID FROM Usuario_Roles WHERE RolID <> @Rol1 ORDER BY RolID);

    DECLARE @Unidad1 UNIQUEIDENTIFIER = (SELECT TOP 1 id FROM Unidades_Negocio ORDER BY nombre);
    DECLARE @Unidad2 UNIQUEIDENTIFIER = (
        SELECT TOP 1 id
        FROM Unidades_Negocio
        WHERE id <> @Unidad1
        ORDER BY nombre
    );

    IF @UsuarioID IS NOT NULL AND @Rol1 IS NOT NULL AND @Unidad1 IS NOT NULL
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM Usuario_RolesContexto
            WHERE UsuarioID = @UsuarioID
              AND RolID = @Rol1
              AND UnidadNegocioID = @Unidad1
              AND Activo = 1
        )
        BEGIN
            INSERT INTO Usuario_RolesContexto (
                UsuarioID, RolID, UnidadNegocioID, EsRolPrimario, Activo, FechaAlta, Observaciones, CreatedBy
            )
            VALUES (
                @UsuarioID, @Rol1, @Unidad1, 1, 1, GETDATE(),
                'PRUEBA_MULTI_UNIDAD_1', 'SCRIPT_SQL_66'
            );
        END
    END

    IF @UsuarioID IS NOT NULL AND @Rol2 IS NOT NULL AND @Unidad2 IS NOT NULL
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM Usuario_RolesContexto
            WHERE UsuarioID = @UsuarioID
              AND RolID = @Rol2
              AND UnidadNegocioID = @Unidad2
              AND Activo = 1
        )
        BEGIN
            INSERT INTO Usuario_RolesContexto (
                UsuarioID, RolID, UnidadNegocioID, EsRolPrimario, Activo, FechaAlta, Observaciones, CreatedBy
            )
            VALUES (
                @UsuarioID, @Rol2, @Unidad2, 0, 1, GETDATE(),
                'PRUEBA_MULTI_UNIDAD_2', 'SCRIPT_SQL_66'
            );
        END
    END

    COMMIT TRANSACTION;
    PRINT 'OK - SCRIPT SQL 66 aplicado.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
