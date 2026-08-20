SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_Sync',
        'U'
    ) IS NULL
    BEGIN
        THROW 51000,
            'Falta tabla canonica dbo.Compras_Inventarios_Fisicos_Sync',
            1;
    END;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_Detalle_Sync',
        'U'
    ) IS NULL
    BEGIN
        THROW 51001,
            'Falta tabla canonica dbo.Compras_Inventarios_Fisicos_Detalle_Sync',
            1;
    END;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_SyncRuns',
        'U'
    ) IS NULL
    BEGIN
        CREATE TABLE dbo.Compras_Inventarios_Fisicos_SyncRuns
        (
            run_id varchar(64) NOT NULL,
            server_id varchar(64) NOT NULL,
            unidad_negocio_id varchar(64) NOT NULL,
            unidad_codigo varchar(100) NULL,
            system_type varchar(80) NULL,
            status varchar(20) NOT NULL,
            expected_headers int NULL,
            expected_details bigint NULL,
            staged_headers int NOT NULL
                CONSTRAINT DF_CIFSR_StagedHeaders DEFAULT (0),
            staged_details bigint NOT NULL
                CONSTRAINT DF_CIFSR_StagedDetails DEFAULT (0),
            started_at datetime2(3) NOT NULL
                CONSTRAINT DF_CIFSR_StartedAt DEFAULT SYSUTCDATETIME(),
            completed_at datetime2(3) NULL,
            activated_at datetime2(3) NULL,
            last_error nvarchar(1000) NULL,

            CONSTRAINT PK_Compras_Inventarios_Fisicos_SyncRuns
                PRIMARY KEY CLUSTERED (run_id),

            CONSTRAINT CK_CIFSR_Status
                CHECK (
                    status IN (
                        'STAGING',
                        'VALIDATED',
                        'ACTIVATING',
                        'ACTIVE',
                        'FAILED',
                        'ABANDONED'
                    )
                )
        );

        CREATE INDEX IX_CIFSR_UnidadStatus
        ON dbo.Compras_Inventarios_Fisicos_SyncRuns
        (
            server_id,
            unidad_negocio_id,
            status,
            started_at
        );
    END;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_Stage',
        'U'
    ) IS NULL
    BEGIN
        CREATE TABLE dbo.Compras_Inventarios_Fisicos_Stage
        (
            run_id varchar(64) NOT NULL,
            server_id varchar(64) NOT NULL,
            unidad_negocio_id varchar(64) NOT NULL,
            unidad_negocio_codigo varchar(100) NULL,
            system_type varchar(80) NULL,
            folio varchar(100) NOT NULL,
            fecha datetime NULL,
            almacen varchar(255) NULL,
            almacen_id varchar(100) NULL,
            sucursal varchar(255) NULL,
            sucursal_id varchar(100) NULL,
            tipo varchar(50) NULL,
            estatus varchar(50) NULL,
            total_productos int NULL,
            comentario nvarchar(255) NULL,
            staged_at datetime2(3) NOT NULL
                CONSTRAINT DF_CIFS_StagedAt DEFAULT SYSUTCDATETIME(),

            CONSTRAINT PK_Compras_Inventarios_Fisicos_Stage
                PRIMARY KEY CLUSTERED
                (
                    run_id,
                    server_id,
                    unidad_negocio_id,
                    folio
                )
        );

        CREATE INDEX IX_CIFS_Run
        ON dbo.Compras_Inventarios_Fisicos_Stage
        (
            run_id,
            server_id,
            unidad_negocio_id
        );
    END;

    IF OBJECT_ID(
        'dbo.Compras_Inventarios_Fisicos_Detalle_Stage',
        'U'
    ) IS NULL
    BEGIN
        CREATE TABLE dbo.Compras_Inventarios_Fisicos_Detalle_Stage
        (
            run_id varchar(64) NOT NULL,
            server_id varchar(64) NOT NULL,
            unidad_negocio_id varchar(64) NOT NULL,
            unidad_negocio_codigo varchar(100) NULL,
            system_type varchar(80) NULL,
            folio varchar(100) NOT NULL,
            almacen varchar(255) NULL,
            almacen_id varchar(100) NOT NULL,
            codigo_producto varchar(100) NOT NULL,
            nombre_producto nvarchar(500) NULL,
            unidad nvarchar(50) NULL,
            existencia_fisica decimal(18,6) NULL,
            rendimiento decimal(18,6) NULL,
            costo_unitario decimal(18,6) NULL,
            staged_at datetime2(3) NOT NULL
                CONSTRAINT DF_CIFDS_StagedAt DEFAULT SYSUTCDATETIME(),

            CONSTRAINT PK_Compras_Inventarios_Fisicos_Detalle_Stage
                PRIMARY KEY CLUSTERED
                (
                    run_id,
                    server_id,
                    unidad_negocio_id,
                    folio,
                    almacen_id,
                    codigo_producto
                )
        );

        CREATE INDEX IX_CIFDS_RunFolio
        ON dbo.Compras_Inventarios_Fisicos_Detalle_Stage
        (
            run_id,
            server_id,
            unidad_negocio_id,
            folio
        );
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
