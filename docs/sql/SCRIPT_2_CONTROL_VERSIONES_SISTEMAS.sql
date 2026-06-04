/* ============================================================
   SCRIPT 2 - CONTROL DE VERSIONES DE SISTEMAS EDARSAHUB
   Objetivo:
   - Agregar catálogo editable de versiones por sistema.
   - Permitir mapear tablas y columnas por versión.
   - Relacionar servidores con una versión específica.
   - No romper estructuras actuales.
   - No borrar datos.
   ============================================================ */

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    PRINT '============================================================';
    PRINT 'SCRIPT 2 - CONTROL DE VERSIONES DE SISTEMAS EDARSAHUB';
    PRINT '============================================================';

    /* ============================================================
       1. Tabla: Sistema_VersionesSistemas
       ============================================================ */

    IF OBJECT_ID('dbo.Sistema_VersionesSistemas', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sistema_VersionesSistemas (
            sistema_version_id UNIQUEIDENTIFIER NOT NULL
                CONSTRAINT DF_Sistema_VersionesSistemas_id DEFAULT NEWID(),

            tipo_sistema NVARCHAR(80) NOT NULL,
            nombre_sistema NVARCHAR(150) NOT NULL,
            version_sistema NVARCHAR(100) NOT NULL,
            descripcion NVARCHAR(500) NULL,

            proveedor NVARCHAR(150) NULL,
            motor_base_datos NVARCHAR(80) NULL,
            version_base_datos NVARCHAR(100) NULL,

            es_version_default BIT NOT NULL
                CONSTRAINT DF_Sistema_VersionesSistemas_default DEFAULT 0,

            activo BIT NOT NULL
                CONSTRAINT DF_Sistema_VersionesSistemas_activo DEFAULT 1,

            observaciones NVARCHAR(MAX) NULL,

            created_at DATETIME2(0) NOT NULL
                CONSTRAINT DF_Sistema_VersionesSistemas_created DEFAULT SYSUTCDATETIME(),

            updated_at DATETIME2(0) NULL,

            created_by NVARCHAR(150) NULL,
            updated_by NVARCHAR(150) NULL,

            CONSTRAINT PK_Sistema_VersionesSistemas
                PRIMARY KEY CLUSTERED (sistema_version_id),

            CONSTRAINT UQ_Sistema_VersionesSistemas_tipo_version
                UNIQUE (tipo_sistema, version_sistema)
        );

        PRINT 'Tabla creada: dbo.Sistema_VersionesSistemas';
    END
    ELSE
    BEGIN
        PRINT 'Tabla ya existe: dbo.Sistema_VersionesSistemas';
    END;


    /* ============================================================
       2. Tabla: Sistema_MapeoTablasVersion
       ============================================================ */

    IF OBJECT_ID('dbo.Sistema_MapeoTablasVersion', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sistema_MapeoTablasVersion (
            sistema_mapeo_tabla_id UNIQUEIDENTIFIER NOT NULL
                CONSTRAINT DF_Sistema_MapeoTablasVersion_id DEFAULT NEWID(),

            sistema_version_id UNIQUEIDENTIFIER NOT NULL,

            modulo_edarsahub NVARCHAR(120) NOT NULL,
            entidad_canonica NVARCHAR(120) NOT NULL,

            tabla_origen_schema NVARCHAR(120) NULL,
            tabla_origen_nombre NVARCHAR(180) NOT NULL,

            tabla_destino_schema NVARCHAR(120) NULL,
            tabla_destino_nombre NVARCHAR(180) NULL,

            tipo_operacion NVARCHAR(80) NULL,
            descripcion NVARCHAR(500) NULL,

            requiere_sync BIT NOT NULL
                CONSTRAINT DF_Sistema_MapeoTablasVersion_requiere_sync DEFAULT 1,

            permite_lectura_live BIT NOT NULL
                CONSTRAINT DF_Sistema_MapeoTablasVersion_permite_live DEFAULT 0,

            activo BIT NOT NULL
                CONSTRAINT DF_Sistema_MapeoTablasVersion_activo DEFAULT 1,

            observaciones NVARCHAR(MAX) NULL,

            created_at DATETIME2(0) NOT NULL
                CONSTRAINT DF_Sistema_MapeoTablasVersion_created DEFAULT SYSUTCDATETIME(),

            updated_at DATETIME2(0) NULL,

            created_by NVARCHAR(150) NULL,
            updated_by NVARCHAR(150) NULL,

            CONSTRAINT PK_Sistema_MapeoTablasVersion
                PRIMARY KEY CLUSTERED (sistema_mapeo_tabla_id),

            CONSTRAINT FK_Sistema_MapeoTablasVersion_Version
                FOREIGN KEY (sistema_version_id)
                REFERENCES dbo.Sistema_VersionesSistemas (sistema_version_id),

            CONSTRAINT UQ_Sistema_MapeoTablasVersion_unico
                UNIQUE (
                    sistema_version_id,
                    modulo_edarsahub,
                    entidad_canonica,
                    tabla_origen_nombre
                )
        );

        PRINT 'Tabla creada: dbo.Sistema_MapeoTablasVersion';
    END
    ELSE
    BEGIN
        PRINT 'Tabla ya existe: dbo.Sistema_MapeoTablasVersion';
    END;


    /* ============================================================
       3. Tabla: Sistema_MapeoColumnasVersion
       ============================================================ */

    IF OBJECT_ID('dbo.Sistema_MapeoColumnasVersion', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.Sistema_MapeoColumnasVersion (
            sistema_mapeo_columna_id UNIQUEIDENTIFIER NOT NULL
                CONSTRAINT DF_Sistema_MapeoColumnasVersion_id DEFAULT NEWID(),

            sistema_mapeo_tabla_id UNIQUEIDENTIFIER NOT NULL,

            campo_canonico NVARCHAR(180) NOT NULL,
            columna_origen NVARCHAR(180) NOT NULL,
            columna_destino NVARCHAR(180) NULL,

            tipo_dato_origen NVARCHAR(80) NULL,
            tipo_dato_destino NVARCHAR(80) NULL,

            transformacion_sql NVARCHAR(MAX) NULL,
            valor_default NVARCHAR(500) NULL,

            es_pk_origen BIT NOT NULL
                CONSTRAINT DF_Sistema_MapeoColumnasVersion_pk DEFAULT 0,

            es_obligatorio BIT NOT NULL
                CONSTRAINT DF_Sistema_MapeoColumnasVersion_obligatorio DEFAULT 0,

            permite_null BIT NOT NULL
                CONSTRAINT DF_Sistema_MapeoColumnasVersion_null DEFAULT 1,

            activo BIT NOT NULL
                CONSTRAINT DF_Sistema_MapeoColumnasVersion_activo DEFAULT 1,

            observaciones NVARCHAR(MAX) NULL,

            created_at DATETIME2(0) NOT NULL
                CONSTRAINT DF_Sistema_MapeoColumnasVersion_created DEFAULT SYSUTCDATETIME(),

            updated_at DATETIME2(0) NULL,

            created_by NVARCHAR(150) NULL,
            updated_by NVARCHAR(150) NULL,

            CONSTRAINT PK_Sistema_MapeoColumnasVersion
                PRIMARY KEY CLUSTERED (sistema_mapeo_columna_id),

            CONSTRAINT FK_Sistema_MapeoColumnasVersion_Tabla
                FOREIGN KEY (sistema_mapeo_tabla_id)
                REFERENCES dbo.Sistema_MapeoTablasVersion (sistema_mapeo_tabla_id),

            CONSTRAINT UQ_Sistema_MapeoColumnasVersion_unico
                UNIQUE (
                    sistema_mapeo_tabla_id,
                    campo_canonico,
                    columna_origen
                )
        );

        PRINT 'Tabla creada: dbo.Sistema_MapeoColumnasVersion';
    END
    ELSE
    BEGIN
        PRINT 'Tabla ya existe: dbo.Sistema_MapeoColumnasVersion';
    END;


    /* ============================================================
       4. Agregar columna sistema_version_id a Servidores_Conexiones
       ============================================================ */

    IF COL_LENGTH('dbo.Servidores_Conexiones', 'sistema_version_id') IS NULL
    BEGIN
        ALTER TABLE dbo.Servidores_Conexiones
        ADD sistema_version_id UNIQUEIDENTIFIER NULL;

        PRINT 'Columna agregada: Servidores_Conexiones.sistema_version_id';
    END
    ELSE
    BEGIN
        PRINT 'Columna ya existe: Servidores_Conexiones.sistema_version_id';
    END;


    /* ============================================================
       5. Agregar FK si no existe
       ============================================================ */

    IF NOT EXISTS (
        SELECT 1
        FROM sys.foreign_keys
        WHERE name = 'FK_Servidores_Conexiones_SistemaVersion'
    )
    BEGIN
        ALTER TABLE dbo.Servidores_Conexiones
        ADD CONSTRAINT FK_Servidores_Conexiones_SistemaVersion
        FOREIGN KEY (sistema_version_id)
        REFERENCES dbo.Sistema_VersionesSistemas (sistema_version_id);

        PRINT 'FK creada: FK_Servidores_Conexiones_SistemaVersion';
    END
    ELSE
    BEGIN
        PRINT 'FK ya existe: FK_Servidores_Conexiones_SistemaVersion';
    END;


    /* ============================================================
       6. Índices
       ============================================================ */

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_Sistema_VersionesSistemas_tipo_activo'
          AND object_id = OBJECT_ID('dbo.Sistema_VersionesSistemas')
    )
    BEGIN
        CREATE INDEX IX_Sistema_VersionesSistemas_tipo_activo
        ON dbo.Sistema_VersionesSistemas (tipo_sistema, activo, es_version_default);

        PRINT 'Índice creado: IX_Sistema_VersionesSistemas_tipo_activo';
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_Sistema_MapeoTablasVersion_version_modulo'
          AND object_id = OBJECT_ID('dbo.Sistema_MapeoTablasVersion')
    )
    BEGIN
        CREATE INDEX IX_Sistema_MapeoTablasVersion_version_modulo
        ON dbo.Sistema_MapeoTablasVersion (
            sistema_version_id,
            modulo_edarsahub,
            entidad_canonica,
            activo
        );

        PRINT 'Índice creado: IX_Sistema_MapeoTablasVersion_version_modulo';
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_Sistema_MapeoColumnasVersion_tabla'
          AND object_id = OBJECT_ID('dbo.Sistema_MapeoColumnasVersion')
    )
    BEGIN
        CREATE INDEX IX_Sistema_MapeoColumnasVersion_tabla
        ON dbo.Sistema_MapeoColumnasVersion (
            sistema_mapeo_tabla_id,
            campo_canonico,
            activo
        );

        PRINT 'Índice creado: IX_Sistema_MapeoColumnasVersion_tabla';
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE name = 'IX_Servidores_Conexiones_sistema_version'
          AND object_id = OBJECT_ID('dbo.Servidores_Conexiones')
    )
    BEGIN
        CREATE INDEX IX_Servidores_Conexiones_sistema_version
        ON dbo.Servidores_Conexiones (sistema_version_id);

        PRINT 'Índice creado: IX_Servidores_Conexiones_sistema_version';
    END;


    /* ============================================================
       7. Insertar versiones base por tipo_sistema existente
       ============================================================ */

    ;WITH Tipos AS (
        SELECT DISTINCT
            tipo_sistema
        FROM dbo.Servidores_Conexiones
        WHERE tipo_sistema IS NOT NULL
          AND LTRIM(RTRIM(tipo_sistema)) <> ''
    )
    INSERT INTO dbo.Sistema_VersionesSistemas (
        tipo_sistema,
        nombre_sistema,
        version_sistema,
        descripcion,
        proveedor,
        motor_base_datos,
        es_version_default,
        activo,
        observaciones,
        created_by
    )
    SELECT
        t.tipo_sistema,
        t.tipo_sistema AS nombre_sistema,
        'SIN_VERSION_DEFINIDA' AS version_sistema,
        'Versión temporal creada automáticamente para control de versiones y mapeo de esquemas.' AS descripcion,
        NULL AS proveedor,
        'SQL Server' AS motor_base_datos,
        1 AS es_version_default,
        1 AS activo,
        'Registro inicial. Debe editarse manualmente conforme se confirme la versión real del sistema.' AS observaciones,
        'SCRIPT_2_CONTROL_VERSIONES' AS created_by
    FROM Tipos t
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_VersionesSistemas v
        WHERE v.tipo_sistema = t.tipo_sistema
          AND v.version_sistema = 'SIN_VERSION_DEFINIDA'
    );

    PRINT 'Versiones base insertadas para tipos de sistema existentes.';


    /* ============================================================
       8. Asignar versión default a servidores sin versión
       ============================================================ */

    UPDATE sc
    SET sc.sistema_version_id = v.sistema_version_id
    FROM dbo.Servidores_Conexiones sc
    INNER JOIN dbo.Sistema_VersionesSistemas v
        ON v.tipo_sistema = sc.tipo_sistema
       AND v.version_sistema = 'SIN_VERSION_DEFINIDA'
       AND v.activo = 1
    WHERE sc.sistema_version_id IS NULL;

    PRINT 'Servidores sin versión asignados a versión default temporal.';


    /* ============================================================
       9. Crear vista de consulta
       ============================================================ */

    IF OBJECT_ID('dbo.vw_Servidores_Conexiones_Versiones', 'V') IS NOT NULL
    BEGIN
        DROP VIEW dbo.vw_Servidores_Conexiones_Versiones;
        PRINT 'Vista anterior eliminada: vw_Servidores_Conexiones_Versiones';
    END;

    EXEC('
        CREATE VIEW dbo.vw_Servidores_Conexiones_Versiones AS
        SELECT
            sc.servidor_conexion_id,
            sc.nombre,
            sc.tipo_sistema,
            sc.host,
            sc.database_name,
            sc.activo,
            sc.visible_en_operaciones,
            sc.es_core,
            sc.sistema_version_id,
            v.nombre_sistema,
            v.version_sistema,
            v.descripcion AS descripcion_version,
            v.proveedor,
            v.motor_base_datos,
            v.version_base_datos,
            v.es_version_default,
            v.activo AS version_activa
        FROM dbo.Servidores_Conexiones sc
        LEFT JOIN dbo.Sistema_VersionesSistemas v
            ON v.sistema_version_id = sc.sistema_version_id;
    ');

    PRINT 'Vista creada: dbo.vw_Servidores_Conexiones_Versiones';


    /* ============================================================
       10. Resultado
       ============================================================ */

    PRINT '============================================================';
    PRINT 'RESULTADO VERSIONES POR SERVIDOR';
    PRINT '============================================================';

    SELECT
        servidor_conexion_id,
        nombre,
        tipo_sistema,
        sistema_version_id,
        nombre_sistema,
        version_sistema,
        es_version_default,
        version_activa
    FROM dbo.vw_Servidores_Conexiones_Versiones
    ORDER BY tipo_sistema, nombre;

    COMMIT TRANSACTION;

    PRINT '============================================================';
    PRINT 'SCRIPT 2 COMPLETADO CORRECTAMENTE';
    PRINT '============================================================';

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    PRINT '============================================================';
    PRINT 'ERROR EN SCRIPT 2 - ROLLBACK APLICADO';
    PRINT '============================================================';

    SELECT
        ERROR_NUMBER() AS ErrorNumber,
        ERROR_SEVERITY() AS ErrorSeverity,
        ERROR_STATE() AS ErrorState,
        ERROR_LINE() AS ErrorLine,
        ERROR_MESSAGE() AS ErrorMessage;

    THROW;
END CATCH;
