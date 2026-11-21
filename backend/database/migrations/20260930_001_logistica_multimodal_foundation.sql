SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 51000, 'ABORT_WRONG_DATABASE', 1;

IF SUSER_SNAME() = 'HRLectura'
    THROW 51001, 'ABORT_READONLY_LOGIN_NOT_WRITER', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Logistica_Cat_ModosTransporte','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Logistica_Cat_ModosTransporte(
            ModoTransporteCodigo varchar(30) NOT NULL
                CONSTRAINT PK_Logistica_Cat_ModosTransporte PRIMARY KEY,
            Nombre nvarchar(100) NOT NULL,
            Activo bit NOT NULL CONSTRAINT DF_Logistica_Modos_Activo DEFAULT(1),
            FechaAltaUTC datetime2(0) NOT NULL
                CONSTRAINT DF_Logistica_Modos_FechaAltaUTC DEFAULT(SYSUTCDATETIME())
        );

        INSERT INTO dbo.Logistica_Cat_ModosTransporte(ModoTransporteCodigo, Nombre)
        VALUES
            ('ROAD', N'Carretero'),
            ('RAIL', N'Ferroviario'),
            ('AIR', N'Aereo'),
            ('MARITIME', N'Maritimo'),
            ('INLAND_WATERWAY', N'Fluvial / vias navegables interiores');
    END;

    IF OBJECT_ID('dbo.Logistica_Cat_PropositosServicio','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Logistica_Cat_PropositosServicio(
            PropositoServicioCodigo varchar(30) NOT NULL
                CONSTRAINT PK_Logistica_Cat_PropositosServicio PRIMARY KEY,
            Nombre nvarchar(100) NOT NULL,
            Activo bit NOT NULL CONSTRAINT DF_Logistica_Propositos_Activo DEFAULT(1),
            FechaAltaUTC datetime2(0) NOT NULL
                CONSTRAINT DF_Logistica_Propositos_FechaAltaUTC DEFAULT(SYSUTCDATETIME())
        );

        INSERT INTO dbo.Logistica_Cat_PropositosServicio(PropositoServicioCodigo, Nombre)
        VALUES
            ('CARGO', N'Carga'),
            ('PASSENGER', N'Pasajeros'),
            ('MIXED', N'Mixto'),
            ('SPECIALIZED', N'Especializado');
    END;

    IF OBJECT_ID('dbo.Logistica_Ordenes','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Logistica_Ordenes(
            OrdenLogisticaID bigint IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_Logistica_Ordenes PRIMARY KEY,
            PublicUUID uniqueidentifier NOT NULL
                CONSTRAINT DF_Logistica_Ordenes_PublicUUID DEFAULT(NEWSEQUENTIALID()),
            EmpresaID int NOT NULL,
            UnidadNegocioID uniqueidentifier NOT NULL,
            SucursalID int NULL,
            ClienteID int NULL,
            ProveedorID int NULL,
            TipoOrden varchar(40) NOT NULL,
            ModoServicio varchar(40) NOT NULL,
            VentanaInicioUTC datetime2(0) NULL,
            VentanaFinUTC datetime2(0) NULL,
            FechaOperacion date NOT NULL,
            Estado varchar(30) NOT NULL,
            IdempotencyKey varchar(160) NOT NULL,
            CorrelationID uniqueidentifier NULL,
            UsuarioAltaID int NOT NULL,
            FechaAltaUTC datetime2(0) NOT NULL
                CONSTRAINT DF_Logistica_Ordenes_FechaAltaUTC DEFAULT(SYSUTCDATETIME()),
            FechaModificacionUTC datetime2(0) NULL,

            CONSTRAINT UQ_Logistica_Ordenes_PublicUUID UNIQUE(PublicUUID),
            CONSTRAINT UQ_Logistica_Ordenes_Empresa_Idempotency UNIQUE(EmpresaID, IdempotencyKey),

            CONSTRAINT FK_Logistica_Ordenes_Empresa
                FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
            CONSTRAINT FK_Logistica_Ordenes_Unidad
                FOREIGN KEY(UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
            CONSTRAINT FK_Logistica_Ordenes_Sucursal
                FOREIGN KEY(SucursalID) REFERENCES dbo.Sistema_Sucursales(SucursalID),
            CONSTRAINT FK_Logistica_Ordenes_Cliente
                FOREIGN KEY(ClienteID) REFERENCES dbo.Cliente_Catalogo(ClienteID),
            CONSTRAINT FK_Logistica_Ordenes_Proveedor
                FOREIGN KEY(ProveedorID) REFERENCES dbo.Proveedor_Catalogo(ProveedorID),
            CONSTRAINT FK_Logistica_Ordenes_UsuarioAlta
                FOREIGN KEY(UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT CK_Logistica_Ordenes_Ventana
                CHECK (VentanaInicioUTC IS NULL OR VentanaFinUTC IS NULL OR VentanaFinUTC >= VentanaInicioUTC)
        );

        CREATE INDEX IX_Logistica_Ordenes_Empresa_FechaOperacion
            ON dbo.Logistica_Ordenes(EmpresaID, FechaOperacion);

        CREATE INDEX IX_Logistica_Ordenes_Empresa_Estado_FechaOperacion
            ON dbo.Logistica_Ordenes(EmpresaID, Estado, FechaOperacion);
    END;

    IF OBJECT_ID('dbo.Logistica_MediosTransportePerfilOperativo','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Logistica_MediosTransportePerfilOperativo(
            MedioTransportePerfilOperativoID bigint IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_Logistica_MediosTransportePerfilOperativo PRIMARY KEY,
            PublicUUID uniqueidentifier NOT NULL
                CONSTRAINT DF_Logistica_Medios_PublicUUID DEFAULT(NEWSEQUENTIALID()),
            ActivoID bigint NOT NULL,
            EmpresaID int NOT NULL,
            ModoTransporteCodigo varchar(30) NOT NULL,
            PropositoServicioCodigo varchar(30) NOT NULL,
            CapacidadDescripcion nvarchar(250) NULL,
            EstadoOperativo varchar(30) NOT NULL,
            TelemetriaHabilitada bit NOT NULL
                CONSTRAINT DF_Logistica_Medios_Telemetria DEFAULT(0),
            Activo bit NOT NULL
                CONSTRAINT DF_Logistica_Medios_Activo DEFAULT(1),
            UsuarioAltaID int NOT NULL,
            FechaAltaUTC datetime2(0) NOT NULL
                CONSTRAINT DF_Logistica_Medios_FechaAltaUTC DEFAULT(SYSUTCDATETIME()),
            FechaModificacionUTC datetime2(0) NULL,

            CONSTRAINT UQ_Logistica_Medios_PublicUUID UNIQUE(PublicUUID),
            CONSTRAINT UQ_Logistica_Medios_Activo UNIQUE(ActivoID),

            CONSTRAINT FK_Logistica_Medios_ActivoFijo
                FOREIGN KEY(ActivoID) REFERENCES dbo.ActivoFijo_Activos(ActivoID),
            CONSTRAINT FK_Logistica_Medios_Empresa
                FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
            CONSTRAINT FK_Logistica_Medios_Modo
                FOREIGN KEY(ModoTransporteCodigo)
                REFERENCES dbo.Logistica_Cat_ModosTransporte(ModoTransporteCodigo),
            CONSTRAINT FK_Logistica_Medios_Proposito
                FOREIGN KEY(PropositoServicioCodigo)
                REFERENCES dbo.Logistica_Cat_PropositosServicio(PropositoServicioCodigo),
            CONSTRAINT FK_Logistica_Medios_UsuarioAlta
                FOREIGN KEY(UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID)
        );

        CREATE INDEX IX_Logistica_Medios_Empresa_Modo_Activo
            ON dbo.Logistica_MediosTransportePerfilOperativo(EmpresaID, ModoTransporteCodigo, Activo);
    END;

    IF OBJECT_ID('dbo.Logistica_Viajes','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Logistica_Viajes(
            ViajeID bigint IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_Logistica_Viajes PRIMARY KEY,
            PublicUUID uniqueidentifier NOT NULL
                CONSTRAINT DF_Logistica_Viajes_PublicUUID DEFAULT(NEWSEQUENTIALID()),
            EmpresaID int NOT NULL,
            UnidadNegocioID uniqueidentifier NOT NULL,
            OrdenLogisticaID bigint NULL,
            FechaOperacion date NOT NULL,
            InicioPlaneadoUTC datetime2(0) NULL,
            InicioRealUTC datetime2(0) NULL,
            FinRealUTC datetime2(0) NULL,
            Estado varchar(30) NOT NULL,
            IdempotencyKey varchar(160) NOT NULL,
            CorrelationID uniqueidentifier NULL,
            UsuarioAltaID int NOT NULL,
            FechaAltaUTC datetime2(0) NOT NULL
                CONSTRAINT DF_Logistica_Viajes_FechaAltaUTC DEFAULT(SYSUTCDATETIME()),
            FechaModificacionUTC datetime2(0) NULL,

            CONSTRAINT UQ_Logistica_Viajes_PublicUUID UNIQUE(PublicUUID),
            CONSTRAINT UQ_Logistica_Viajes_Empresa_Idempotency UNIQUE(EmpresaID, IdempotencyKey),

            CONSTRAINT FK_Logistica_Viajes_Empresa
                FOREIGN KEY(EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
            CONSTRAINT FK_Logistica_Viajes_Unidad
                FOREIGN KEY(UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
            CONSTRAINT FK_Logistica_Viajes_Orden
                FOREIGN KEY(OrdenLogisticaID) REFERENCES dbo.Logistica_Ordenes(OrdenLogisticaID),
            CONSTRAINT FK_Logistica_Viajes_UsuarioAlta
                FOREIGN KEY(UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT CK_Logistica_Viajes_Fechas
                CHECK (InicioRealUTC IS NULL OR FinRealUTC IS NULL OR FinRealUTC >= InicioRealUTC)
        );

        CREATE INDEX IX_Logistica_Viajes_Empresa_FechaOperacion
            ON dbo.Logistica_Viajes(EmpresaID, FechaOperacion);

        CREATE INDEX IX_Logistica_Viajes_Orden
            ON dbo.Logistica_Viajes(OrdenLogisticaID)
            WHERE OrdenLogisticaID IS NOT NULL;
    END;

    IF OBJECT_ID('dbo.Logistica_ViajeLegs','U') IS NULL
    BEGIN
        CREATE TABLE dbo.Logistica_ViajeLegs(
            ViajeLegID bigint IDENTITY(1,1) NOT NULL
                CONSTRAINT PK_Logistica_ViajeLegs PRIMARY KEY,
            ViajeID bigint NOT NULL,
            Secuencia int NOT NULL,
            ModoTransporteCodigo varchar(30) NOT NULL,
            PropositoServicioCodigo varchar(30) NOT NULL,
            MedioTransportePerfilOperativoID bigint NULL,
            OriginNodeRef varchar(200) NULL,
            DestinationNodeRef varchar(200) NULL,
            ScheduledDepartureUTC datetime2(0) NULL,
            ScheduledArrivalUTC datetime2(0) NULL,
            ActualDepartureUTC datetime2(0) NULL,
            ActualArrivalUTC datetime2(0) NULL,
            Estado varchar(30) NOT NULL,
            IdempotencyKey varchar(160) NOT NULL,
            UsuarioAltaID int NOT NULL,
            FechaAltaUTC datetime2(0) NOT NULL
                CONSTRAINT DF_Logistica_ViajeLegs_FechaAltaUTC DEFAULT(SYSUTCDATETIME()),
            FechaModificacionUTC datetime2(0) NULL,

            CONSTRAINT UQ_Logistica_ViajeLegs_Viaje_Secuencia UNIQUE(ViajeID, Secuencia),
            CONSTRAINT UQ_Logistica_ViajeLegs_Viaje_Idempotency UNIQUE(ViajeID, IdempotencyKey),

            CONSTRAINT FK_Logistica_ViajeLegs_Viaje
                FOREIGN KEY(ViajeID) REFERENCES dbo.Logistica_Viajes(ViajeID),
            CONSTRAINT FK_Logistica_ViajeLegs_Modo
                FOREIGN KEY(ModoTransporteCodigo)
                REFERENCES dbo.Logistica_Cat_ModosTransporte(ModoTransporteCodigo),
            CONSTRAINT FK_Logistica_ViajeLegs_Proposito
                FOREIGN KEY(PropositoServicioCodigo)
                REFERENCES dbo.Logistica_Cat_PropositosServicio(PropositoServicioCodigo),
            CONSTRAINT FK_Logistica_ViajeLegs_Medio
                FOREIGN KEY(MedioTransportePerfilOperativoID)
                REFERENCES dbo.Logistica_MediosTransportePerfilOperativo(MedioTransportePerfilOperativoID),
            CONSTRAINT FK_Logistica_ViajeLegs_UsuarioAlta
                FOREIGN KEY(UsuarioAltaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),

            CONSTRAINT CK_Logistica_ViajeLegs_Secuencia CHECK (Secuencia > 0),
            CONSTRAINT CK_Logistica_ViajeLegs_Scheduled
                CHECK (ScheduledDepartureUTC IS NULL OR ScheduledArrivalUTC IS NULL OR ScheduledArrivalUTC >= ScheduledDepartureUTC),
            CONSTRAINT CK_Logistica_ViajeLegs_Actual
                CHECK (ActualDepartureUTC IS NULL OR ActualArrivalUTC IS NULL OR ActualArrivalUTC >= ActualDepartureUTC)
        );

        CREATE INDEX IX_Logistica_ViajeLegs_Medio_Fechas
            ON dbo.Logistica_ViajeLegs(MedioTransportePerfilOperativoID, ScheduledDepartureUTC, ScheduledArrivalUTC)
            WHERE MedioTransportePerfilOperativoID IS NOT NULL;
    END;

    COMMIT;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK;
    THROW;
END CATCH;
