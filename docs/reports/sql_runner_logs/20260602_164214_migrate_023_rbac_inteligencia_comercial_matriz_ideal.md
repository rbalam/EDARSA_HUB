# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:42:14.941676
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: Cannot commit transaction: (51000, b'Existen roles ideales faltantes en Usuario_Roles. Crear roles antes de asignar permisos.DB-Lib error message 20018, severity 16:\nGeneral SQL Server error: Check messages from the SQL Server\n')
```

## SQL ejecutado / revisado
```sql
/* ============================================================
   EDARSAHUB - RBAC INTELIGENCIA COMERCIAL
   Validación + Implementación de matriz ideal de permisos
   Fecha: 2026-06-02

   OBJETIVO:
   1. Validar módulo INTELIGENCIA_COMERCIAL.
   2. Validar roles ideales.
   3. Validar acciones requeridas.
   4. Retirar permisos de roles no aprobados:
      CRM_ADMIN, CRM_EJEC, CRM_AUDIT, ADMIN, GERENCIA,
      GERENTE_OPS, AUDITOR, VENTAS, COMPRAS, TESORERIA,
      OPERADOR, USUARIO, SUPERVISOR.
   5. Asignar permisos solo a:
      SUPERADMIN
      ADMIN_COMERCIAL
      DIRECCION
      GERENTE_UNIDAD
      ANALISTA_COMERCIAL
      VISOR_COMERCIAL
      CONFIGURADOR_COMERCIAL

   REGLAS:
   - No crea usuarios.
   - No migra usuarios.
   - No toca MongoDB.
   - No usa Sistema_RBAC_* como modelo final.
   - Usa Usuario_* como RBAC canónico.
   ============================================================ */

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    /* ============================================================
       0. Validaciones estructurales
       ============================================================ */

    IF OBJECT_ID('dbo.Usuario_Modulos', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Modulos.', 1;

    IF OBJECT_ID('dbo.Usuario_Roles', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Roles.', 1;

    IF OBJECT_ID('dbo.Usuario_Acciones', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Acciones.', 1;

    IF OBJECT_ID('dbo.Usuario_PermisosRolModulo', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_PermisosRolModulo.', 1;

    IF COL_LENGTH('dbo.Usuario_Modulos', 'ModuloID') IS NULL
        THROW 51000, 'Usuario_Modulos no tiene columna ModuloID.', 1;

    IF COL_LENGTH('dbo.Usuario_Modulos', 'CodigoModulo') IS NULL
        THROW 51000, 'Usuario_Modulos no tiene columna CodigoModulo.', 1;

    IF COL_LENGTH('dbo.Usuario_Roles', 'RolID') IS NULL
        THROW 51000, 'Usuario_Roles no tiene columna RolID.', 1;

    IF COL_LENGTH('dbo.Usuario_Roles', 'CodigoRol') IS NULL
        THROW 51000, 'Usuario_Roles no tiene columna CodigoRol.', 1;

    IF COL_LENGTH('dbo.Usuario_Acciones', 'AccionID') IS NULL
        THROW 51000, 'Usuario_Acciones no tiene columna AccionID.', 1;

    IF COL_LENGTH('dbo.Usuario_Acciones', 'CodigoAccion') IS NULL
        THROW 51000, 'Usuario_Acciones no tiene columna CodigoAccion.', 1;

    IF COL_LENGTH('dbo.Usuario_PermisosRolModulo', 'RolID') IS NULL
        THROW 51000, 'Usuario_PermisosRolModulo no tiene columna RolID.', 1;

    IF COL_LENGTH('dbo.Usuario_PermisosRolModulo', 'ModuloID') IS NULL
        THROW 51000, 'Usuario_PermisosRolModulo no tiene columna ModuloID.', 1;

    IF COL_LENGTH('dbo.Usuario_PermisosRolModulo', 'AccionID') IS NULL
        THROW 51000, 'Usuario_PermisosRolModulo no tiene columna AccionID.', 1;

    IF COL_LENGTH('dbo.Usuario_PermisosRolModulo', 'Activo') IS NULL
        THROW 51000, 'Usuario_PermisosRolModulo no tiene columna Activo.', 1;


    /* ============================================================
       1. Obtener módulo INTELIGENCIA_COMERCIAL
       ============================================================ */

    DECLARE @ModuloID INT;

    SELECT @ModuloID = ModuloID
    FROM dbo.Usuario_Modulos
    WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';

    IF @ModuloID IS NULL
        THROW 51000, 'No existe el módulo INTELIGENCIA_COMERCIAL en Usuario_Modulos.', 1;


    /* ============================================================
       2. Crear tabla temporal de matriz ideal
       ============================================================ */

    -- Crear tabla temporal de matriz ideal
    CREATE TABLE #MatrizIdealIC (
        CodigoRol NVARCHAR(100) NOT NULL,
        CodigoAccion NVARCHAR(100) NOT NULL
    );

    /* SUPERADMIN: acceso total */
    INSERT INTO #MatrizIdealIC (CodigoRol, CodigoAccion)
    VALUES
        ('SUPERADMIN', 'VER'),
        ('SUPERADMIN', 'EXPORTAR'),
        ('SUPERADMIN', 'GESTIONAR'),
        ('SUPERADMIN', 'CONFIGURAR');

    /* ADMIN_COMERCIAL: administración completa del módulo comercial */
    INSERT INTO #MatrizIdealIC (CodigoRol, CodigoAccion)
    VALUES
        ('ADMIN_COMERCIAL', 'VER'),
        ('ADMIN_COMERCIAL', 'EXPORTAR'),
        ('ADMIN_COMERCIAL', 'GESTIONAR'),
        ('ADMIN_COMERCIAL', 'CONFIGURAR');

    /* DIRECCION: consulta y exportación ejecutiva */
    INSERT INTO #MatrizIdealIC (CodigoRol, CodigoAccion)
    VALUES
        ('DIRECCION', 'VER'),
        ('DIRECCION', 'EXPORTAR');

    /* GERENTE_UNIDAD: consulta/exportación de su unidad autorizada */
    INSERT INTO #MatrizIdealIC (CodigoRol, CodigoAccion)
    VALUES
        ('GERENTE_UNIDAD', 'VER'),
        ('GERENTE_UNIDAD', 'EXPORTAR');

    /* ANALISTA_COMERCIAL: análisis y exportación */
    INSERT INTO #MatrizIdealIC (CodigoRol, CodigoAccion)
    VALUES
        ('ANALISTA_COMERCIAL', 'VER'),
        ('ANALISTA_COMERCIAL', 'EXPORTAR');

    /* VISOR_COMERCIAL: solo lectura */
    INSERT INTO #MatrizIdealIC (CodigoRol, CodigoAccion)
    VALUES
        ('VISOR_COMERCIAL', 'VER');

    /* CONFIGURADOR_COMERCIAL: configuración y gestión operativa del portal */
    INSERT INTO #MatrizIdealIC (CodigoRol, CodigoAccion)
    VALUES
        ('CONFIGURADOR_COMERCIAL', 'VER'),
        ('CONFIGURADOR_COMERCIAL', 'GESTIONAR'),
        ('CONFIGURADOR_COMERCIAL', 'CONFIGURAR');


    /* ============================================================
       3. Validar roles requeridos
       ============================================================ */

    IF EXISTS (
        SELECT 1
        FROM #MatrizIdealIC m
        LEFT JOIN dbo.Usuario_Roles r
            ON r.CodigoRol = m.CodigoRol
        WHERE r.RolID IS NULL
    )
    BEGIN
        SELECT DISTINCT
            m.CodigoRol AS RolFaltante
        FROM #MatrizIdealIC m
        LEFT JOIN dbo.Usuario_Roles r
            ON r.CodigoRol = m.CodigoRol
        WHERE r.RolID IS NULL
        ORDER BY m.CodigoRol;

        THROW 51000, 'Existen roles ideales faltantes en Usuario_Roles. Crear roles antes de asignar permisos.', 1;
    END;


    /* ============================================================
       4. Validar acciones requeridas
       ============================================================ */

    IF EXISTS (
        SELECT 1
        FROM #MatrizIdealIC m
        LEFT JOIN dbo.Usuario_Acciones a
            ON a.CodigoAccion = m.CodigoAccion
        WHERE a.AccionID IS NULL
    )
    BEGIN
        SELECT DISTINCT
            m.CodigoAccion AS AccionFaltante
        FROM #MatrizIdealIC m
        LEFT JOIN dbo.Usuario_Acciones a
            ON a.CodigoAccion = m.CodigoAccion
        WHERE a.AccionID IS NULL
        ORDER BY m.CodigoAccion;

        THROW 51000, 'Existen acciones faltantes en Usuario_Acciones. Crear acciones antes de asignar permisos.', 1;
    END;


    /* ============================================================
       5. Desactivar permisos actuales de INTELIGENCIA_COMERCIAL
          que NO estén en la matriz ideal
       ============================================================ */

    UPDATE prm
    SET
        prm.Activo = 0
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
    WHERE
        prm.ModuloID = @ModuloID
        AND prm.Activo = 1
        AND NOT EXISTS (
            SELECT 1
            FROM #MatrizIdealIC m
            WHERE m.CodigoRol = r.CodigoRol
              AND m.CodigoAccion = a.CodigoAccion
        );


    /* ============================================================
       6. Reforzar retiro explícito de roles CRM y otros no aprobados
       ============================================================ */

    UPDATE prm
    SET prm.Activo = 0
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    WHERE
        prm.ModuloID = @ModuloID
        AND r.CodigoRol IN (
            'CRM_ADMIN',
            'CRM_EJEC',
            'CRM_AUDIT',
            'ADMIN',
            'GERENCIA',
            'GERENTE_OPS',
            'AUDITOR',
            'VENTAS',
            'COMPRAS',
            'TESORERIA',
            'OPERADOR',
            'USUARIO',
            'SUPERVISOR'
        );


    /* ============================================================
       7. Insertar permisos faltantes de la matriz ideal
       ============================================================ */

    INSERT INTO dbo.Usuario_PermisosRolModulo (
        RolID,
        ModuloID,
        AccionID,
        Activo
    )
    SELECT
        r.RolID,
        @ModuloID,
        a.AccionID,
        1
    FROM #MatrizIdealIC m
    INNER JOIN dbo.Usuario_Roles r
        ON r.CodigoRol = m.CodigoRol
    INNER JOIN dbo.Usuario_Acciones a
        ON a.CodigoAccion = m.CodigoAccion
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        WHERE prm.RolID = r.RolID
          AND prm.ModuloID = @ModuloID
          AND prm.AccionID = a.AccionID
    );


    /* ============================================================
       8. Reactivar permisos existentes que sí están en la matriz ideal
       ============================================================ */

    UPDATE prm
    SET prm.Activo = 1
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
    INNER JOIN #MatrizIdealIC m
        ON m.CodigoRol = r.CodigoRol
       AND m.CodigoAccion = a.CodigoAccion
    WHERE prm.ModuloID = @ModuloID;


    /* ============================================================
       9. Registrar decisión en Sistema_Gobierno_Tablas si existe
       ============================================================ */

    IF OBJECT_ID('dbo.Sistema_Gobierno_Tablas', 'U') IS NOT NULL
    BEGIN
        UPDATE dbo.Sistema_Gobierno_Tablas
        SET
            observaciones = CONCAT(
                ISNULL(observaciones, ''),
                CASE WHEN observaciones IS NULL OR observaciones = '' THEN '' ELSE CHAR(13) + CHAR(10) END,
                'RBAC INTELIGENCIA_COMERCIAL: matriz canónica aplicada. Roles CRM excluidos. Fecha: ',
                CONVERT(NVARCHAR(30), SYSDATETIME(), 126)
            ),
            fecha_ultima_actualizacion = SYSDATETIME()
        WHERE nombre_tabla IN (
            'Usuario_Modulos',
            'Usuario_Roles',
            'Usuario_PermisosRolModulo',
            'Usuario_Acciones'
        );
    END;


    COMMIT TRANSACTION;

    PRINT 'RBAC INTELIGENCIA_COMERCIAL aplicado correctamente.';

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    DECLARE @Err NVARCHAR(4000) = ERROR_MESSAGE();
    DECLARE @ErrLine INT = ERROR_LINE();

    PRINT 'ERROR aplicando RBAC INTELIGENCIA_COMERCIAL';
    PRINT CONCAT('Linea: ', @ErrLine);
    PRINT @Err;

    THROW;
END CATCH;

```