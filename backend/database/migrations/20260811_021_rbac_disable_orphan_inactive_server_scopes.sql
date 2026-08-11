/*
EDARSAHUB V1.0
Remediacion RBAC:
desactivar scopes activos que apuntan a servidores inactivos.

Evidencia previa:
- Usuario_ServidoresAsignacion: 243, 250
- Usuario_SucursalesAsignacion: 245, 249
- UsuarioID afectado: 3
- Servidores:
  b5175237-5e57-41f3-ab6d-b5ae2f5e780b
  d8425038-5e57-42d9-8f3a-62e287888874

Reglas:
- No DELETE.
- No crear nuevos scopes.
- No modificar servidores.
- ModificadoPor permanece NULL porque no existe actor
  administrativo canonico demostrado para migraciones.
- Preservar historial en Observaciones.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    ------------------------------------------------------------
    -- Guardrail: servidores objetivo deben seguir inactivos.
    ------------------------------------------------------------

    IF (
        SELECT COUNT(*)
        FROM dbo.Servidores_Conexiones
        WHERE id IN (
            'b5175237-5e57-41f3-ab6d-b5ae2f5e780b',
            'd8425038-5e57-42d9-8f3a-62e287888874'
        )
          AND activo = 0
    ) <> 2
    BEGIN
        THROW 51000,
            'RBAC orphan remediation abort: target server state changed.',
            1;
    END;

    ------------------------------------------------------------
    -- Guardrail: preimagen exacta servidor.
    ------------------------------------------------------------

    IF (
        SELECT COUNT(*)
        FROM dbo.Usuario_ServidoresAsignacion
        WHERE
            (
                AsignacionID = 243
                AND UsuarioID = 3
                AND ServidorID =
                    'd8425038-5e57-42d9-8f3a-62e287888874'
                AND Activo = 1
                AND FechaModificacion IS NULL
                AND ModificadoPor IS NULL
                AND Observaciones =
                    N'RBAC-SCOPE-E-HARDENED: Escritura SQL productiva'
            )
            OR
            (
                AsignacionID = 250
                AND UsuarioID = 3
                AND ServidorID =
                    'b5175237-5e57-41f3-ab6d-b5ae2f5e780b'
                AND Activo = 1
                AND FechaModificacion IS NULL
                AND ModificadoPor IS NULL
                AND Observaciones =
                    N'RBAC-SCOPE-E-HARDENED: Escritura SQL productiva'
            )
    ) <> 2
    BEGIN
        THROW 51001,
            'RBAC orphan remediation abort: server scope preimage changed.',
            1;
    END;

    ------------------------------------------------------------
    -- Guardrail: preimagen exacta sucursal.
    ------------------------------------------------------------

    IF (
        SELECT COUNT(*)
        FROM dbo.Usuario_SucursalesAsignacion
        WHERE
            (
                AsignacionID = 245
                AND UsuarioID = 3
                AND ServidorID =
                    'b5175237-5e57-41f3-ab6d-b5ae2f5e780b'
                AND SucursalCodigo = 'default'
                AND Activo = 1
                AND FechaModificacion IS NULL
                AND ModificadoPor IS NULL
                AND Observaciones =
                    N'RBAC-SCOPE-E-HARDENED: Escritura SQL productiva'
            )
            OR
            (
                AsignacionID = 249
                AND UsuarioID = 3
                AND ServidorID =
                    'd8425038-5e57-42d9-8f3a-62e287888874'
                AND SucursalCodigo = 'default'
                AND Activo = 1
                AND FechaModificacion IS NULL
                AND ModificadoPor IS NULL
                AND Observaciones =
                    N'RBAC-SCOPE-E-HARDENED: Escritura SQL productiva'
            )
    ) <> 2
    BEGIN
        THROW 51002,
            'RBAC orphan remediation abort: branch scope preimage changed.',
            1;
    END;

    ------------------------------------------------------------
    -- Desactivar scopes de servidor.
    ------------------------------------------------------------

    UPDATE dbo.Usuario_ServidoresAsignacion
    SET
        Activo = 0,
        FechaModificacion = SYSUTCDATETIME(),
        ModificadoPor = NULL,
        Observaciones =
            CONCAT(
                Observaciones,
                N' | RBAC-ORPHAN-REMEDIATION-20260811: ',
                N'scope desactivado porque ServidorID esta inactivo.'
            )
    WHERE AsignacionID IN (243, 250)
      AND UsuarioID = 3
      AND Activo = 1;

    IF @@ROWCOUNT <> 2
    BEGIN
        THROW 51003,
            'RBAC orphan remediation abort: unexpected server scope rowcount.',
            1;
    END;

    ------------------------------------------------------------
    -- Desactivar scopes de sucursal.
    ------------------------------------------------------------

    UPDATE dbo.Usuario_SucursalesAsignacion
    SET
        Activo = 0,
        FechaModificacion = SYSUTCDATETIME(),
        ModificadoPor = NULL,
        Observaciones =
            CONCAT(
                Observaciones,
                N' | RBAC-ORPHAN-REMEDIATION-20260811: ',
                N'scope desactivado porque ServidorID esta inactivo.'
            )
    WHERE AsignacionID IN (245, 249)
      AND UsuarioID = 3
      AND SucursalCodigo = 'default'
      AND Activo = 1;

    IF @@ROWCOUNT <> 2
    BEGIN
        THROW 51004,
            'RBAC orphan remediation abort: unexpected branch scope rowcount.',
            1;
    END;

    ------------------------------------------------------------
    -- Postcondicion.
    ------------------------------------------------------------

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_ServidoresAsignacion usa
        LEFT JOIN dbo.Servidores_Conexiones sc
            ON sc.id = usa.ServidorID
        WHERE usa.Activo = 1
          AND (
                sc.id IS NULL
                OR ISNULL(sc.activo, 0) = 0
          )
    )
    BEGIN
        THROW 51005,
            'RBAC orphan remediation abort: active orphan server scopes remain.',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_SucursalesAsignacion usa
        LEFT JOIN dbo.Servidores_Conexiones sc
            ON sc.id = usa.ServidorID
        WHERE usa.Activo = 1
          AND (
                sc.id IS NULL
                OR ISNULL(sc.activo, 0) = 0
          )
    )
    BEGIN
        THROW 51006,
            'RBAC orphan remediation abort: active orphan branch scopes remain.',
            1;
    END;

    COMMIT TRANSACTION;

    SELECT
        CAST(1 AS bit) AS Success,
        2 AS ServerScopesDisabled,
        2 AS BranchScopesDisabled,
        'PASS' AS Resultado;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
