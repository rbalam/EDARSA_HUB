/* ============================================================
   EDARSAHUB
   Reactivar permiso canónico:
     SUPERADMIN / INTELIGENCIA_COMERCIAL / GESTIONAR

   Alcance:
   - Una sola fila existente.
   - Permitido = 1.
   - Activo = 1.
   - No crea roles, módulos, acciones ni permisos.
   - No modifica otros roles.
   ============================================================ */

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @RolID INT;
    DECLARE @ModuloID INT;
    DECLARE @AccionID INT;

    DECLARE @RolCount INT;
    DECLARE @ModuloCount INT;
    DECLARE @AccionCount INT;
    DECLARE @TargetCount INT;
    DECLARE @UpdatedCount INT;

    SELECT
        @RolID = MIN(RolID),
        @RolCount = COUNT(*)
    FROM dbo.Usuario_Roles WITH (UPDLOCK, HOLDLOCK)
    WHERE CodigoRol = 'SUPERADMIN'
      AND Activo = 1;

    IF @RolCount <> 1
        THROW 51000,
            'SUPERADMIN activo inexistente o duplicado.',
            1;

    SELECT
        @ModuloID = MIN(ModuloID),
        @ModuloCount = COUNT(*)
    FROM dbo.Usuario_Modulos WITH (UPDLOCK, HOLDLOCK)
    WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL'
      AND Activo = 1;

    IF @ModuloCount <> 1
        THROW 51000,
            'INTELIGENCIA_COMERCIAL activo inexistente o duplicado.',
            1;

    SELECT
        @AccionID = MIN(AccionID),
        @AccionCount = COUNT(*)
    FROM dbo.Usuario_Acciones WITH (UPDLOCK, HOLDLOCK)
    WHERE CodigoAccion = 'GESTIONAR'
      AND Activo = 1;

    IF @AccionCount <> 1
        THROW 51000,
            'GESTIONAR activo inexistente o duplicado.',
            1;

    SELECT
        prm.RolID,
        prm.ModuloID,
        prm.AccionID,
        prm.Permitido,
        prm.Activo
    INTO #AntesGestionar
    FROM dbo.Usuario_PermisosRolModulo prm
        WITH (UPDLOCK, HOLDLOCK)
    WHERE prm.ModuloID = @ModuloID
      AND prm.AccionID = @AccionID;

    SELECT
        @TargetCount = COUNT(*)
    FROM #AntesGestionar
    WHERE RolID = @RolID;

    IF @TargetCount <> 1
        THROW 51000,
            'La fila objetivo SUPERADMIN/GESTIONAR no existe o está duplicada.',
            1;

    UPDATE dbo.Usuario_PermisosRolModulo
    SET
        Permitido = 1,
        Activo = 1
    WHERE RolID = @RolID
      AND ModuloID = @ModuloID
      AND AccionID = @AccionID;

    SET @UpdatedCount = @@ROWCOUNT;

    IF @UpdatedCount <> 1
        THROW 51000,
            'El UPDATE no afectó exactamente una fila.',
            1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo
        WHERE RolID = @RolID
          AND ModuloID = @ModuloID
          AND AccionID = @AccionID
          AND Permitido = 1
          AND Activo = 1
    )
        THROW 51000,
            'La fila objetivo no quedó activa y permitida.',
            1;

    IF EXISTS (
        SELECT
            RolID,
            ModuloID,
            AccionID,
            Permitido,
            Activo
        FROM #AntesGestionar
        WHERE RolID <> @RolID

        EXCEPT

        SELECT
            RolID,
            ModuloID,
            AccionID,
            Permitido,
            Activo
        FROM dbo.Usuario_PermisosRolModulo
        WHERE ModuloID = @ModuloID
          AND AccionID = @AccionID
          AND RolID <> @RolID
    )
        THROW 51000,
            'Se detectó modificación colateral en otros roles.',
            1;

    IF EXISTS (
        SELECT
            RolID,
            ModuloID,
            AccionID,
            Permitido,
            Activo
        FROM dbo.Usuario_PermisosRolModulo
        WHERE ModuloID = @ModuloID
          AND AccionID = @AccionID
          AND RolID <> @RolID

        EXCEPT

        SELECT
            RolID,
            ModuloID,
            AccionID,
            Permitido,
            Activo
        FROM #AntesGestionar
        WHERE RolID <> @RolID
    )
        THROW 51000,
            'Se detectó modificación colateral en otros roles.',
            1;

    COMMIT TRANSACTION;

    SELECT
        'SUPERADMIN_GESTIONAR_REACTIVATED' AS Resultado,
        r.CodigoRol,
        m.CodigoModulo,
        a.CodigoAccion,
        prm.Permitido,
        prm.Activo
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    INNER JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
    WHERE r.CodigoRol = 'SUPERADMIN'
      AND m.CodigoModulo = 'INTELIGENCIA_COMERCIAL'
      AND a.CodigoAccion = 'GESTIONAR';

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
