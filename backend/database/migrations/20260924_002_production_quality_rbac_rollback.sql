/*
EDARSAHUB
Production Quality / Foto Finish
Gate5D2 RBAC rollback.

Removes only artifacts attributable to Gate5D2.
Does not delete canonical roles or actions.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DELETE prm
    FROM dbo.Usuario_PermisosRolModulo prm
    JOIN dbo.Usuario_Modulos m
      ON m.ModuloID = prm.ModuloID
    WHERE LOWER(m.CodigoModulo) LIKE 'production_quality%'
      AND prm.CreatedBy = 'PQ_RBAC_GATE5D2';

    DECLARE @RootID INT;

    SELECT @RootID = ModuloID
    FROM dbo.Usuario_Modulos
    WHERE LOWER(CodigoModulo) = 'production_quality';

    DELETE FROM dbo.Usuario_Modulos
    WHERE ModuloPadreID = @RootID
      AND Descripcion LIKE N'PQ_RBAC_GATE5D2:%'
      AND LOWER(CodigoModulo) IN (
          'production_quality.execution',
          'production_quality.standards',
          'production_quality.evidence',
          'production_quality.decisions',
          'production_quality.rework',
          'production_quality.override',
          'production_quality.devices'
      )
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_PermisosRolModulo prm
          WHERE prm.ModuloID = dbo.Usuario_Modulos.ModuloID
      );

    DELETE FROM dbo.Usuario_Modulos
    WHERE LOWER(CodigoModulo) = 'production_quality'
      AND Descripcion =
          N'PQ_RBAC_GATE5D2: raiz RBAC canonica Production Quality.'
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_Modulos child
          WHERE child.ModuloPadreID =
                dbo.Usuario_Modulos.ModuloID
      )
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_PermisosRolModulo prm
          WHERE prm.ModuloID =
                dbo.Usuario_Modulos.ModuloID
      );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
