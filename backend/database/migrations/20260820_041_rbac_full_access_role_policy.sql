SET NOCOUNT ON;
SET XACT_ABORT ON;

/*
EDARSAHUB RBAC - politica canonica de acceso total.

Objetivo:
- SUPERADMIN no es un bypass runtime.
- Un rol de acceso total recibe permisos por la misma matriz canonica
  dbo.Usuario_PermisosRolModulo que cualquier otro rol.
- Los permisos actuales se convergen de forma idempotente.
- Los permisos funcionales futuros se materializan automaticamente cuando
  una combinacion ModuloID + AccionID es concedida de forma activa a algun rol.

La semantica de acceso total queda parametrizada en dbo.Usuario_Roles mediante
EsAccesoTotal; el runtime no depende de CodigoRol, email, JWT ni jerarquia.
*/

BEGIN TRY
    BEGIN TRANSACTION;

    IF COL_LENGTH('dbo.Usuario_Roles', 'EsAccesoTotal') IS NULL
    BEGIN
        ALTER TABLE dbo.Usuario_Roles
        ADD EsAccesoTotal BIT NOT NULL
            CONSTRAINT DF_Usuario_Roles_EsAccesoTotal DEFAULT (0);
    END;

    /*
      Seed de configuracion existente: SUPERADMIN es el rol de sistema
      historicamente definido como "Acceso total al sistema".
      Esta referencia existe solo en migracion/configuracion; no en runtime.
    */
    UPDATE dbo.Usuario_Roles
    SET EsAccesoTotal = 1
    WHERE CodigoRol = 'SUPERADMIN'
      AND ISNULL(EsRolSistema, 0) = 1
      AND ISNULL(Activo, 1) = 1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Roles
        WHERE ISNULL(EsAccesoTotal, 0) = 1
          AND ISNULL(Activo, 1) = 1
    )
    BEGIN
        THROW 51041, 'No existe un rol activo configurado con EsAccesoTotal=1.', 1;
    END;

    DECLARE @PermisosCanonicos TABLE (
        ModuloID INT NOT NULL,
        AccionID INT NOT NULL,
        PRIMARY KEY (ModuloID, AccionID)
    );

    /*
      Universo real, no CROSS JOIN artificial: solo combinaciones que ya son
      permisos funcionales activos y permitidos en la matriz canonica.
    */
    INSERT INTO @PermisosCanonicos (ModuloID, AccionID)
    SELECT DISTINCT
        prm.ModuloID,
        prm.AccionID
    FROM dbo.Usuario_PermisosRolModulo AS prm
    INNER JOIN dbo.Usuario_Modulos AS m
        ON m.ModuloID = prm.ModuloID
    INNER JOIN dbo.Usuario_Acciones AS a
        ON a.AccionID = prm.AccionID
    WHERE ISNULL(prm.Activo, 1) = 1
      AND ISNULL(prm.Permitido, 0) = 1
      AND ISNULL(m.Activo, 1) = 1
      AND ISNULL(a.Activo, 1) = 1;

    /* Converger filas existentes de roles de acceso total. */
    UPDATE prm
    SET
        prm.Permitido = 1,
        prm.RestriccionPropietario = 0,
        prm.RestriccionSucursal = 0,
        prm.RequiereAutorizacion = 0,
        prm.Activo = 1
    FROM dbo.Usuario_PermisosRolModulo AS prm
    INNER JOIN dbo.Usuario_Roles AS r
        ON r.RolID = prm.RolID
    INNER JOIN @PermisosCanonicos AS pc
        ON pc.ModuloID = prm.ModuloID
       AND pc.AccionID = prm.AccionID
    WHERE ISNULL(r.EsAccesoTotal, 0) = 1
      AND ISNULL(r.Activo, 1) = 1;

    /* Materializar gaps actuales en la misma fuente canonica. */
    INSERT INTO dbo.Usuario_PermisosRolModulo (
        RolID,
        ModuloID,
        AccionID,
        Permitido,
        RestriccionPropietario,
        RestriccionSucursal,
        RequiereAutorizacion,
        Activo,
        FechaAlta,
        CreatedBy
    )
    SELECT
        r.RolID,
        pc.ModuloID,
        pc.AccionID,
        1,
        0,
        0,
        0,
        1,
        GETDATE(),
        'RBAC_FULL_ACCESS_POLICY_041'
    FROM dbo.Usuario_Roles AS r
    CROSS JOIN @PermisosCanonicos AS pc
    WHERE ISNULL(r.EsAccesoTotal, 0) = 1
      AND ISNULL(r.Activo, 1) = 1
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_PermisosRolModulo AS prm
          WHERE prm.RolID = r.RolID
            AND prm.ModuloID = pc.ModuloID
            AND prm.AccionID = pc.AccionID
      );

    /*
      Futuro: cada permiso funcional que entre activo/permitido a la matriz
      se replica automaticamente a todos los roles configurados como acceso
      total. No hay bypass; se materializa en Usuario_PermisosRolModulo.
    */
    EXEC(N'
CREATE OR ALTER TRIGGER dbo.TR_Usuario_PermisosRolModulo_AutoGrantAccesoTotal
ON dbo.Usuario_PermisosRolModulo
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    IF TRIGGER_NESTLEVEL() > 1
        RETURN;

    DECLARE @NuevosPermisos TABLE (
        ModuloID INT NOT NULL,
        AccionID INT NOT NULL,
        PRIMARY KEY (ModuloID, AccionID)
    );

    INSERT INTO @NuevosPermisos (ModuloID, AccionID)
    SELECT DISTINCT
        i.ModuloID,
        i.AccionID
    FROM inserted AS i
    INNER JOIN dbo.Usuario_Modulos AS m
        ON m.ModuloID = i.ModuloID
    INNER JOIN dbo.Usuario_Acciones AS a
        ON a.AccionID = i.AccionID
    WHERE ISNULL(i.Activo, 1) = 1
      AND ISNULL(i.Permitido, 0) = 1
      AND ISNULL(m.Activo, 1) = 1
      AND ISNULL(a.Activo, 1) = 1;

    IF NOT EXISTS (SELECT 1 FROM @NuevosPermisos)
        RETURN;

    UPDATE prm
    SET
        prm.Permitido = 1,
        prm.RestriccionPropietario = 0,
        prm.RestriccionSucursal = 0,
        prm.RequiereAutorizacion = 0,
        prm.Activo = 1
    FROM dbo.Usuario_PermisosRolModulo AS prm
    INNER JOIN dbo.Usuario_Roles AS r
        ON r.RolID = prm.RolID
    INNER JOIN @NuevosPermisos AS np
        ON np.ModuloID = prm.ModuloID
       AND np.AccionID = prm.AccionID
    WHERE ISNULL(r.EsAccesoTotal, 0) = 1
      AND ISNULL(r.Activo, 1) = 1;

    INSERT INTO dbo.Usuario_PermisosRolModulo (
        RolID,
        ModuloID,
        AccionID,
        Permitido,
        RestriccionPropietario,
        RestriccionSucursal,
        RequiereAutorizacion,
        Activo,
        FechaAlta,
        CreatedBy
    )
    SELECT
        r.RolID,
        np.ModuloID,
        np.AccionID,
        1,
        0,
        0,
        0,
        1,
        GETDATE(),
        ''RBAC_FULL_ACCESS_AUTO_GRANT''
    FROM dbo.Usuario_Roles AS r
    CROSS JOIN @NuevosPermisos AS np
    WHERE ISNULL(r.EsAccesoTotal, 0) = 1
      AND ISNULL(r.Activo, 1) = 1
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_PermisosRolModulo AS prm
          WHERE prm.RolID = r.RolID
            AND prm.ModuloID = np.ModuloID
            AND prm.AccionID = np.AccionID
      );
END;
');

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
