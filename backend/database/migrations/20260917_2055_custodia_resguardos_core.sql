/*
RRHH / CUSTODIA - GATE 3 MINIMAL DDL DESIGN R1
ARTEFACTO DE MIGRACION. ESTE JOB NO EJECUTA SQL.
Production=false.

Contratos certificados:
- dbo.RH_Colaboradores_Expediente(ColaboradorID int)
- dbo.RH_Cat_Puestos(PuestoID int)
- dbo.Producto_Catalogo(ProductoID int)
- dbo.ActivoFijo_Activos(ActivoID bigint)
- dbo.Sistema_Empresas(EmpresaID int)
- dbo.Unidades_Negocio(id uniqueidentifier)
- dbo.Sistema_Sucursales(SucursalID int)
- dbo.Usuario_Catalogo(UsuarioID int)
- dbo.Gobierno_Documento(DocumentoID bigint)
- dbo.RH_Nomina_Detalle(NominaDetalleID int)

Gate2C no certifico un modelo Producto<->talla/color reutilizable.
Este DDL NO crea RH_Uniforme_Tallas ni variantes paralelas.
*/

SET XACT_ABORT ON;

IF OBJECT_ID('dbo.RH_Colaboradores_Expediente','U') IS NULL THROW 51000,'Falta dbo.RH_Colaboradores_Expediente canonica.',1;
IF OBJECT_ID('dbo.RH_Cat_Puestos','U') IS NULL THROW 51000,'Falta dbo.RH_Cat_Puestos canonica.',1;
IF OBJECT_ID('dbo.Producto_Catalogo','U') IS NULL THROW 51000,'Falta dbo.Producto_Catalogo canonica.',1;
IF OBJECT_ID('dbo.ActivoFijo_Activos','U') IS NULL THROW 51000,'Falta dbo.ActivoFijo_Activos canonica.',1;
IF OBJECT_ID('dbo.Sistema_Empresas','U') IS NULL THROW 51000,'Falta dbo.Sistema_Empresas canonica.',1;
IF OBJECT_ID('dbo.Unidades_Negocio','U') IS NULL THROW 51000,'Falta dbo.Unidades_Negocio canonica.',1;
IF OBJECT_ID('dbo.Sistema_Sucursales','U') IS NULL THROW 51000,'Falta dbo.Sistema_Sucursales canonica.',1;
IF OBJECT_ID('dbo.Usuario_Catalogo','U') IS NULL THROW 51000,'Falta dbo.Usuario_Catalogo canonica.',1;
IF OBJECT_ID('dbo.Gobierno_Documento','U') IS NULL THROW 51000,'Falta dbo.Gobierno_Documento canonica.',1;
IF OBJECT_ID('dbo.RH_Nomina_Detalle','U') IS NULL THROW 51000,'Falta dbo.RH_Nomina_Detalle canonica.',1;

IF OBJECT_ID('dbo.Custodia_Recurso','U') IS NULL
BEGIN
    CREATE TABLE dbo.Custodia_Recurso (
        RecursoCustodiaID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Custodia_Recurso PRIMARY KEY,
        EmpresaID int NOT NULL,
        UnidadNegocioID uniqueidentifier NULL,
        SucursalID int NULL,
        ProductoID int NULL,
        ActivoID bigint NULL,
        ReferenciaExterna varchar(120) NULL,
        CantidadBase decimal(18,4) NOT NULL CONSTRAINT DF_Custodia_Recurso_CantidadBase DEFAULT (1),
        Activo bit NOT NULL CONSTRAINT DF_Custodia_Recurso_Activo DEFAULT (1),
        FechaCreacionUTC datetime2(3) NOT NULL CONSTRAINT DF_Custodia_Recurso_Fecha DEFAULT (SYSUTCDATETIME()),
        UsuarioCreacionID int NULL,
        CONSTRAINT FK_Custodia_Recurso_Empresa FOREIGN KEY (EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
        CONSTRAINT FK_Custodia_Recurso_Unidad FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
        CONSTRAINT FK_Custodia_Recurso_Sucursal FOREIGN KEY (SucursalID) REFERENCES dbo.Sistema_Sucursales(SucursalID),
        CONSTRAINT FK_Custodia_Recurso_Producto FOREIGN KEY (ProductoID) REFERENCES dbo.Producto_Catalogo(ProductoID),
        CONSTRAINT FK_Custodia_Recurso_ActivoFijo FOREIGN KEY (ActivoID) REFERENCES dbo.ActivoFijo_Activos(ActivoID),
        CONSTRAINT FK_Custodia_Recurso_Usuario FOREIGN KEY (UsuarioCreacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT CK_Custodia_Recurso_Origen CHECK (
            (CASE WHEN ProductoID IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN ActivoID IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN ReferenciaExterna IS NOT NULL THEN 1 ELSE 0 END) = 1
        ),
        CONSTRAINT CK_Custodia_Recurso_Cantidad CHECK (CantidadBase > 0)
    );
    CREATE UNIQUE INDEX UX_Custodia_Recurso_ActivoID ON dbo.Custodia_Recurso(ActivoID) WHERE ActivoID IS NOT NULL;
    CREATE INDEX IX_Custodia_Recurso_ProductoID ON dbo.Custodia_Recurso(ProductoID) WHERE ProductoID IS NOT NULL;
    CREATE INDEX IX_Custodia_Recurso_Contexto ON dbo.Custodia_Recurso(EmpresaID,UnidadNegocioID,SucursalID);
END;

IF OBJECT_ID('dbo.Custodia_Resguardo','U') IS NULL
BEGIN
    CREATE TABLE dbo.Custodia_Resguardo (
        ResguardoID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Custodia_Resguardo PRIMARY KEY,
        RecursoCustodiaID bigint NOT NULL,
        ColaboradorID int NOT NULL,
        EmpresaID int NOT NULL,
        UnidadNegocioID uniqueidentifier NULL,
        SucursalID int NULL,
        TipoResguardoCodigo varchar(40) NOT NULL,
        EstadoCodigo varchar(40) NOT NULL,
        Cantidad decimal(18,4) NOT NULL CONSTRAINT DF_Custodia_Resguardo_Cantidad DEFAULT (1),
        EsVigente bit NOT NULL CONSTRAINT DF_Custodia_Resguardo_Vigente DEFAULT (1),
        FechaOperacion date NOT NULL,
        FechaInicioUTC datetime2(3) NOT NULL,
        FechaFinUTC datetime2(3) NULL,
        ResponsableEntregaID int NOT NULL,
        ResponsableRecepcionID int NULL,
        DocumentoResponsivaID bigint NULL,
        IdempotencyKey uniqueidentifier NOT NULL,
        FechaCreacionUTC datetime2(3) NOT NULL CONSTRAINT DF_Custodia_Resguardo_Fecha DEFAULT (SYSUTCDATETIME()),
        FechaModificacionUTC datetime2(3) NULL,
        CONSTRAINT FK_Custodia_Resguardo_Recurso FOREIGN KEY (RecursoCustodiaID) REFERENCES dbo.Custodia_Recurso(RecursoCustodiaID),
        CONSTRAINT FK_Custodia_Resguardo_Colaborador FOREIGN KEY (ColaboradorID) REFERENCES dbo.RH_Colaboradores_Expediente(ColaboradorID),
        CONSTRAINT FK_Custodia_Resguardo_Empresa FOREIGN KEY (EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
        CONSTRAINT FK_Custodia_Resguardo_Unidad FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
        CONSTRAINT FK_Custodia_Resguardo_Sucursal FOREIGN KEY (SucursalID) REFERENCES dbo.Sistema_Sucursales(SucursalID),
        CONSTRAINT FK_Custodia_Resguardo_Entrega FOREIGN KEY (ResponsableEntregaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_Custodia_Resguardo_Recepcion FOREIGN KEY (ResponsableRecepcionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_Custodia_Resguardo_Responsiva FOREIGN KEY (DocumentoResponsivaID) REFERENCES dbo.Gobierno_Documento(DocumentoID),
        CONSTRAINT UQ_Custodia_Resguardo_Idempotency UNIQUE (IdempotencyKey),
        CONSTRAINT CK_Custodia_Resguardo_Cantidad CHECK (Cantidad > 0),
        CONSTRAINT CK_Custodia_Resguardo_Fechas CHECK (FechaFinUTC IS NULL OR FechaFinUTC >= FechaInicioUTC)
    );
    CREATE UNIQUE INDEX UX_Custodia_Resguardo_RecursoVigente ON dbo.Custodia_Resguardo(RecursoCustodiaID) WHERE EsVigente=1;
    CREATE INDEX IX_Custodia_Resguardo_ColaboradorEstado ON dbo.Custodia_Resguardo(ColaboradorID,EstadoCodigo);
    CREATE INDEX IX_Custodia_Resguardo_Contexto ON dbo.Custodia_Resguardo(EmpresaID,UnidadNegocioID,SucursalID,EstadoCodigo);
    CREATE INDEX IX_Custodia_Resguardo_FechaOperacion ON dbo.Custodia_Resguardo(FechaOperacion);
END;

IF OBJECT_ID('dbo.Custodia_Movimiento','U') IS NULL
BEGIN
    CREATE TABLE dbo.Custodia_Movimiento (
        MovimientoID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Custodia_Movimiento PRIMARY KEY,
        ResguardoID bigint NOT NULL,
        TipoMovimientoCodigo varchar(40) NOT NULL,
        EstadoAnteriorCodigo varchar(40) NULL,
        EstadoNuevoCodigo varchar(40) NOT NULL,
        FechaOperacion date NOT NULL,
        OcurridoAtUTC datetime2(3) NOT NULL CONSTRAINT DF_Custodia_Movimiento_Ocurrido DEFAULT (SYSUTCDATETIME()),
        UsuarioID int NOT NULL,
        MotivoCodigo varchar(60) NULL,
        Observaciones nvarchar(1000) NULL,
        DocumentoID bigint NULL,
        IdempotencyKey uniqueidentifier NOT NULL,
        HashContexto varchar(64) NULL,
        CONSTRAINT FK_Custodia_Movimiento_Resguardo FOREIGN KEY (ResguardoID) REFERENCES dbo.Custodia_Resguardo(ResguardoID),
        CONSTRAINT FK_Custodia_Movimiento_Usuario FOREIGN KEY (UsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_Custodia_Movimiento_Documento FOREIGN KEY (DocumentoID) REFERENCES dbo.Gobierno_Documento(DocumentoID),
        CONSTRAINT UQ_Custodia_Movimiento_Idempotency UNIQUE (IdempotencyKey)
    );
    CREATE INDEX IX_Custodia_Movimiento_ResguardoFecha ON dbo.Custodia_Movimiento(ResguardoID,OcurridoAtUTC);
END;

IF OBJECT_ID('dbo.Custodia_Devolucion','U') IS NULL
BEGIN
    CREATE TABLE dbo.Custodia_Devolucion (
        DevolucionID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Custodia_Devolucion PRIMARY KEY,
        ResguardoID bigint NOT NULL,
        FechaOperacion date NOT NULL,
        OcurridoAtUTC datetime2(3) NOT NULL CONSTRAINT DF_Custodia_Devolucion_Ocurrido DEFAULT (SYSUTCDATETIME()),
        CondicionDevolucionCodigo varchar(40) NOT NULL,
        Completo bit NOT NULL,
        CantidadDevuelta decimal(18,4) NOT NULL,
        Observaciones nvarchar(1000) NULL,
        UsuarioRecibeID int NOT NULL,
        DocumentoEvidenciaID bigint NULL,
        IdempotencyKey uniqueidentifier NOT NULL,
        CONSTRAINT FK_Custodia_Devolucion_Resguardo FOREIGN KEY (ResguardoID) REFERENCES dbo.Custodia_Resguardo(ResguardoID),
        CONSTRAINT FK_Custodia_Devolucion_Usuario FOREIGN KEY (UsuarioRecibeID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_Custodia_Devolucion_Documento FOREIGN KEY (DocumentoEvidenciaID) REFERENCES dbo.Gobierno_Documento(DocumentoID),
        CONSTRAINT UQ_Custodia_Devolucion_Idempotency UNIQUE (IdempotencyKey),
        CONSTRAINT CK_Custodia_Devolucion_Cantidad CHECK (CantidadDevuelta > 0)
    );
    CREATE INDEX IX_Custodia_Devolucion_ResguardoFecha ON dbo.Custodia_Devolucion(ResguardoID,OcurridoAtUTC);
END;

IF OBJECT_ID('dbo.Custodia_Incidencia','U') IS NULL
BEGIN
    CREATE TABLE dbo.Custodia_Incidencia (
        IncidenciaID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Custodia_Incidencia PRIMARY KEY,
        ResguardoID bigint NOT NULL,
        TipoIncidenciaCodigo varchar(40) NOT NULL,
        ResponsabilidadEstadoCodigo varchar(40) NOT NULL,
        FechaOperacion date NOT NULL,
        OcurridoAtUTC datetime2(3) NOT NULL CONSTRAINT DF_Custodia_Incidencia_Ocurrido DEFAULT (SYSUTCDATETIME()),
        Descripcion nvarchar(1500) NOT NULL,
        MontoReferencia decimal(19,4) NULL,
        MonedaCodigo char(3) NULL,
        UsuarioReportaID int NOT NULL,
        DocumentoEvidenciaID bigint NULL,
        FechaResolucionUTC datetime2(3) NULL,
        IdempotencyKey uniqueidentifier NOT NULL,
        CONSTRAINT FK_Custodia_Incidencia_Resguardo FOREIGN KEY (ResguardoID) REFERENCES dbo.Custodia_Resguardo(ResguardoID),
        CONSTRAINT FK_Custodia_Incidencia_Usuario FOREIGN KEY (UsuarioReportaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_Custodia_Incidencia_Documento FOREIGN KEY (DocumentoEvidenciaID) REFERENCES dbo.Gobierno_Documento(DocumentoID),
        CONSTRAINT UQ_Custodia_Incidencia_Idempotency UNIQUE (IdempotencyKey),
        CONSTRAINT CK_Custodia_Incidencia_Monto CHECK (MontoReferencia IS NULL OR MontoReferencia >= 0)
    );
    CREATE INDEX IX_Custodia_Incidencia_ResguardoEstado ON dbo.Custodia_Incidencia(ResguardoID,ResponsabilidadEstadoCodigo);
END;

IF OBJECT_ID('dbo.Custodia_CargoPropuesto','U') IS NULL
BEGIN
    CREATE TABLE dbo.Custodia_CargoPropuesto (
        CargoPropuestoID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_Custodia_CargoPropuesto PRIMARY KEY,
        IncidenciaID bigint NOT NULL,
        MontoPropuesto decimal(19,4) NOT NULL,
        MonedaCodigo char(3) NOT NULL,
        EstadoCodigo varchar(40) NOT NULL,
        Motivo nvarchar(1000) NOT NULL,
        UsuarioProponeID int NOT NULL,
        UsuarioAutorizaID int NULL,
        FechaPropuestaUTC datetime2(3) NOT NULL CONSTRAINT DF_Custodia_Cargo_Fecha DEFAULT (SYSUTCDATETIME()),
        FechaAutorizacionUTC datetime2(3) NULL,
        NominaDetalleID int NULL,
        IdempotencyKey uniqueidentifier NOT NULL,
        CONSTRAINT FK_Custodia_Cargo_Incidencia FOREIGN KEY (IncidenciaID) REFERENCES dbo.Custodia_Incidencia(IncidenciaID),
        CONSTRAINT FK_Custodia_Cargo_Propone FOREIGN KEY (UsuarioProponeID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_Custodia_Cargo_Autoriza FOREIGN KEY (UsuarioAutorizaID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_Custodia_Cargo_NominaDetalle FOREIGN KEY (NominaDetalleID) REFERENCES dbo.RH_Nomina_Detalle(NominaDetalleID),
        CONSTRAINT UQ_Custodia_Cargo_Idempotency UNIQUE (IdempotencyKey),
        CONSTRAINT CK_Custodia_Cargo_Monto CHECK (MontoPropuesto >= 0)
    );
    CREATE INDEX IX_Custodia_Cargo_IncidenciaEstado ON dbo.Custodia_CargoPropuesto(IncidenciaID,EstadoCodigo);
END;

IF OBJECT_ID('dbo.RH_UniformePolitica','U') IS NULL
BEGIN
    CREATE TABLE dbo.RH_UniformePolitica (
        UniformePoliticaID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_RH_UniformePolitica PRIMARY KEY,
        EmpresaID int NOT NULL,
        UnidadNegocioID uniqueidentifier NULL,
        PuestoID int NOT NULL,
        Version int NOT NULL,
        VigenciaDesde date NOT NULL,
        VigenciaHasta date NULL,
        Activo bit NOT NULL CONSTRAINT DF_RH_UniformePolitica_Activo DEFAULT (1),
        UsuarioCreacionID int NULL,
        FechaCreacionUTC datetime2(3) NOT NULL CONSTRAINT DF_RH_UniformePolitica_Fecha DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_RH_UniformePolitica_Empresa FOREIGN KEY (EmpresaID) REFERENCES dbo.Sistema_Empresas(EmpresaID),
        CONSTRAINT FK_RH_UniformePolitica_Unidad FOREIGN KEY (UnidadNegocioID) REFERENCES dbo.Unidades_Negocio(id),
        CONSTRAINT FK_RH_UniformePolitica_Puesto FOREIGN KEY (PuestoID) REFERENCES dbo.RH_Cat_Puestos(PuestoID),
        CONSTRAINT FK_RH_UniformePolitica_Usuario FOREIGN KEY (UsuarioCreacionID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT UQ_RH_UniformePolitica_ContextoVersion UNIQUE (EmpresaID,UnidadNegocioID,PuestoID,Version),
        CONSTRAINT CK_RH_UniformePolitica_Version CHECK (Version > 0),
        CONSTRAINT CK_RH_UniformePolitica_Vigencia CHECK (VigenciaHasta IS NULL OR VigenciaHasta >= VigenciaDesde)
    );
END;

IF OBJECT_ID('dbo.RH_UniformePoliticaDetalle','U') IS NULL
BEGIN
    CREATE TABLE dbo.RH_UniformePoliticaDetalle (
        UniformePoliticaDetalleID bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_RH_UniformePoliticaDetalle PRIMARY KEY,
        UniformePoliticaID bigint NOT NULL,
        ProductoID int NOT NULL,
        Cantidad decimal(18,4) NOT NULL,
        PeriodicidadDias int NULL,
        VidaUtilDias int NULL,
        RequiereDevolucion bit NOT NULL CONSTRAINT DF_RH_UniformeDetalle_Devolucion DEFAULT (0),
        ReposicionDesgastePermitida bit NOT NULL CONSTRAINT DF_RH_UniformeDetalle_Desgaste DEFAULT (1),
        ReposicionPerdidaPermitida bit NOT NULL CONSTRAINT DF_RH_UniformeDetalle_Perdida DEFAULT (0),
        Orden int NOT NULL CONSTRAINT DF_RH_UniformeDetalle_Orden DEFAULT (0),
        CONSTRAINT FK_RH_UniformeDetalle_Politica FOREIGN KEY (UniformePoliticaID) REFERENCES dbo.RH_UniformePolitica(UniformePoliticaID),
        CONSTRAINT FK_RH_UniformeDetalle_Producto FOREIGN KEY (ProductoID) REFERENCES dbo.Producto_Catalogo(ProductoID),
        CONSTRAINT UQ_RH_UniformeDetalle_PoliticaProducto UNIQUE (UniformePoliticaID,ProductoID),
        CONSTRAINT CK_RH_UniformeDetalle_Cantidad CHECK (Cantidad > 0),
        CONSTRAINT CK_RH_UniformeDetalle_Periodicidad CHECK (PeriodicidadDias IS NULL OR PeriodicidadDias > 0),
        CONSTRAINT CK_RH_UniformeDetalle_VidaUtil CHECK (VidaUtilDias IS NULL OR VidaUtilDias > 0)
    );
END;

/*
NO se crean tablas de stock de uniformes.
NO se crea almacenamiento documental paralelo.
NO se crea maestro paralelo de colaboradores, activos, productos, RBAC o nomina.
NO se crea catalogo de tallas/colores hasta resolver el contrato canonico de variantes de Producto.
NO se ejecutan deducciones. Custodia_CargoPropuesto solo enlaza a RH_Nomina_Detalle cuando Nomina las aplique.
*/
