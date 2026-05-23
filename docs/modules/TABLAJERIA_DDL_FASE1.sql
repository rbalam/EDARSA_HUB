-- ============================================================================
-- EDARSAHUB - MÓDULO TABLAJERÍA
-- DDL Script - Fase 1
-- Fecha: 2026-05-23
-- Autor: Sistema EDARSAHUB
-- ============================================================================
-- MÁXIMAS RESPETADAS:
-- 1. EDARSAHUB SQL Server es el cerebro del sistema
-- 2. Timestamps técnicos en UTC, FechaOperacion en México
-- 3. Nomenclatura: Operaciones_Tablaje_*
-- 4. Sin dependencia de MongoDB
-- ============================================================================

-- ============================================================================
-- TABLA 1: Operaciones_Tablaje_Plantillas
-- Plantillas maestras de transformación/tablajería
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_Plantillas')
BEGIN
    CREATE TABLE Operaciones_Tablaje_Plantillas (
        PlantillaID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        SucursalID INT NULL,
        
        -- Almacenes
        AlmacenOrigenID INT NULL,
        AlmacenDestinoID INT NULL,
        
        -- Identificación
        CodigoPlantilla NVARCHAR(50) NOT NULL,
        NombrePlantilla NVARCHAR(200) NOT NULL,
        Descripcion NVARCHAR(500) NULL,
        TipoTransformacion NVARCHAR(50) NULL, -- TABLAJERIA, DESPIECE, PRODUCCION, ENSAMBLE
        
        -- Insumo Base
        InsumoBaseID INT NULL, -- FK a producto/insumo
        InsumoBaseCodigo NVARCHAR(50) NULL,
        InsumoBaseNombre NVARCHAR(200) NULL,
        UnidadBaseID INT NULL,
        UnidadBaseCodigo NVARCHAR(20) NULL,
        CantidadBaseEstandar DECIMAL(18,4) NOT NULL DEFAULT 1,
        
        -- Rendimientos esperados
        RendimientoEsperadoPorcentaje DECIMAL(5,2) NULL,
        MermaEsperadaPorcentaje DECIMAL(5,2) NULL,
        ToleranciaRendimiento DECIMAL(5,2) NULL DEFAULT 5.00, -- +/- % tolerancia
        
        -- Costeo
        ReglaCosteo NVARCHAR(50) NULL DEFAULT 'PROPORCIONAL', -- PROPORCIONAL, FIJO, RESIDUAL
        CostoBaseReferencia DECIMAL(18,4) NULL,
        MonedaID INT NULL DEFAULT 1,
        
        -- Origen de datos
        OrigenPlantilla NVARCHAR(50) NOT NULL DEFAULT 'CAPTURA_DIRECTA_EDARSAHUB',
        SistemaOrigen NVARCHAR(50) NULL,
        ServidorOrigenID NVARCHAR(100) NULL, -- ID del servidor en Servidores_Conexiones
        BaseDatosOrigen NVARCHAR(100) NULL,
        IDLegacyPlantilla NVARCHAR(100) NULL, -- ID en sistema origen
        HashOrigen NVARCHAR(64) NULL, -- SHA256 para detectar cambios
        
        -- Versionamiento
        VersionActual INT NOT NULL DEFAULT 1,
        PlantillaPadreID UNIQUEIDENTIFIER NULL, -- Para versiones
        
        -- Estados
        Estatus NVARCHAR(50) NOT NULL DEFAULT 'BORRADOR',
        RequiereAutorizacion BIT NOT NULL DEFAULT 0,
        AutorizadoPor UNIQUEIDENTIFIER NULL,
        FechaAutorizacion DATETIME2 NULL,
        
        -- Control
        Activo BIT NOT NULL DEFAULT 1,
        FechaAltaUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaModificacionUTC DATETIME2 NULL,
        FechaSincronizacionUTC DATETIME2 NULL,
        FechaOperacionMexico DATE NOT NULL,
        UsuarioAltaID UNIQUEIDENTIFIER NULL,
        UsuarioModificacionID UNIQUEIDENTIFIER NULL,
        
        -- Índices únicos
        CONSTRAINT UQ_Plantilla_Codigo_Empresa UNIQUE (EmpresaID, CodigoPlantilla, VersionActual)
    );
    
    -- Índices
    CREATE INDEX IX_Plantillas_Empresa ON Operaciones_Tablaje_Plantillas(EmpresaID);
    CREATE INDEX IX_Plantillas_UnidadNegocio ON Operaciones_Tablaje_Plantillas(UnidadNegocioID);
    CREATE INDEX IX_Plantillas_Estatus ON Operaciones_Tablaje_Plantillas(Estatus);
    CREATE INDEX IX_Plantillas_Origen ON Operaciones_Tablaje_Plantillas(OrigenPlantilla);
    CREATE INDEX IX_Plantillas_InsumoBase ON Operaciones_Tablaje_Plantillas(InsumoBaseID);
    CREATE INDEX IX_Plantillas_Legacy ON Operaciones_Tablaje_Plantillas(ServidorOrigenID, IDLegacyPlantilla);
    
    PRINT 'Tabla Operaciones_Tablaje_Plantillas creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 2: Operaciones_Tablaje_PlantillasDetalle
-- Derivados/productos resultantes de cada plantilla
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_PlantillasDetalle')
BEGIN
    CREATE TABLE Operaciones_Tablaje_PlantillasDetalle (
        PlantillaDetalleID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        PlantillaID UNIQUEIDENTIFIER NOT NULL,
        
        -- Producto derivado
        ProductoDerivadoID INT NULL,
        ProductoDerivadoCodigo NVARCHAR(50) NULL,
        ProductoDerivadoNombre NVARCHAR(200) NOT NULL,
        
        -- Clasificación
        TipoDerivado NVARCHAR(50) NOT NULL DEFAULT 'PRINCIPAL', -- PRINCIPAL, SUBPRODUCTO, MERMA, DESPERDICIO
        
        -- Unidad y cantidad
        UnidadDerivadoID INT NULL,
        UnidadDerivadoCodigo NVARCHAR(20) NULL,
        CantidadEsperada DECIMAL(18,4) NOT NULL,
        PorcentajeRendimientoEsperado DECIMAL(5,2) NULL,
        
        -- Costeo
        PorcentajeCostoAsignado DECIMAL(5,2) NULL,
        CostoUnitarioFijo DECIMAL(18,4) NULL,
        
        -- Flags
        EsMerma BIT NOT NULL DEFAULT 0,
        EsSubproducto BIT NOT NULL DEFAULT 0,
        EsProductoVendible BIT NOT NULL DEFAULT 1,
        EsInventariable BIT NOT NULL DEFAULT 1,
        GeneraMovimientoInventario BIT NOT NULL DEFAULT 1,
        
        -- Presentación
        OrdenVisual INT NOT NULL DEFAULT 0,
        Observaciones NVARCHAR(500) NULL,
        
        -- Origen legacy
        IDLegacyDetalle NVARCHAR(100) NULL,
        
        -- Control
        Activo BIT NOT NULL DEFAULT 1,
        FechaAltaUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaModificacionUTC DATETIME2 NULL,
        
        CONSTRAINT FK_PlantillaDetalle_Plantilla FOREIGN KEY (PlantillaID) 
            REFERENCES Operaciones_Tablaje_Plantillas(PlantillaID)
    );
    
    CREATE INDEX IX_PlantillaDetalle_Plantilla ON Operaciones_Tablaje_PlantillasDetalle(PlantillaID);
    CREATE INDEX IX_PlantillaDetalle_Producto ON Operaciones_Tablaje_PlantillasDetalle(ProductoDerivadoID);
    CREATE INDEX IX_PlantillaDetalle_Tipo ON Operaciones_Tablaje_PlantillasDetalle(TipoDerivado);
    
    PRINT 'Tabla Operaciones_Tablaje_PlantillasDetalle creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 3: Operaciones_Tablaje_PlantillasVersiones
-- Historial de versiones de plantillas
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_PlantillasVersiones')
BEGIN
    CREATE TABLE Operaciones_Tablaje_PlantillasVersiones (
        VersionID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        PlantillaID UNIQUEIDENTIFIER NOT NULL,
        NumeroVersion INT NOT NULL,
        
        -- Snapshot de datos al momento de versionar
        DatosPlantillaJSON NVARCHAR(MAX) NULL,
        DatosDetalleJSON NVARCHAR(MAX) NULL,
        HashVersion NVARCHAR(64) NULL,
        
        -- Motivo del cambio
        MotivoVersion NVARCHAR(500) NULL,
        TipoCambio NVARCHAR(50) NULL, -- SINCRONIZACION, EDICION_MANUAL, AUTORIZACION
        
        -- Control
        EsVersionActiva BIT NOT NULL DEFAULT 0,
        FechaVersionUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        UsuarioVersionID UNIQUEIDENTIFIER NULL,
        
        CONSTRAINT FK_PlantillaVersion_Plantilla FOREIGN KEY (PlantillaID) 
            REFERENCES Operaciones_Tablaje_Plantillas(PlantillaID)
    );
    
    CREATE INDEX IX_PlantillaVersiones_Plantilla ON Operaciones_Tablaje_PlantillasVersiones(PlantillaID);
    CREATE UNIQUE INDEX IX_PlantillaVersiones_Unica ON Operaciones_Tablaje_PlantillasVersiones(PlantillaID, NumeroVersion);
    
    PRINT 'Tabla Operaciones_Tablaje_PlantillasVersiones creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 4: Operaciones_Tablaje_Ordenes
-- Órdenes de producción/tablaje
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_Ordenes')
BEGIN
    CREATE TABLE Operaciones_Tablaje_Ordenes (
        OrdenID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        SucursalID INT NULL,
        
        -- Identificación
        FolioOrden NVARCHAR(50) NOT NULL,
        PlantillaID UNIQUEIDENTIFIER NOT NULL,
        PlantillaVersion INT NOT NULL DEFAULT 1,
        
        -- Almacenes
        AlmacenOrigenID INT NULL,
        AlmacenDestinoID INT NULL,
        
        -- Insumo consumido
        InsumoBaseID INT NULL,
        InsumoBaseCodigo NVARCHAR(50) NULL,
        InsumoBaseNombre NVARCHAR(200) NULL,
        LoteInsumo NVARCHAR(100) NULL,
        
        -- Cantidades planeadas
        CantidadBasePlaneada DECIMAL(18,4) NOT NULL,
        UnidadBaseID INT NULL,
        
        -- Cantidades reales (al ejecutar)
        CantidadBaseReal DECIMAL(18,4) NULL,
        PesoInicialKg DECIMAL(18,4) NULL,
        PesoFinalKg DECIMAL(18,4) NULL,
        
        -- Rendimientos
        RendimientoEsperadoPorcentaje DECIMAL(5,2) NULL,
        RendimientoRealPorcentaje DECIMAL(5,2) NULL,
        DesviacionRendimiento DECIMAL(5,2) NULL,
        
        -- Mermas
        MermaEsperadaPorcentaje DECIMAL(5,2) NULL,
        MermaRealPorcentaje DECIMAL(5,2) NULL,
        MermaRealKg DECIMAL(18,4) NULL,
        
        -- Costos
        CostoInsumoBase DECIMAL(18,4) NULL,
        CostoTotalOrden DECIMAL(18,4) NULL,
        MonedaID INT NULL DEFAULT 1,
        
        -- Estados
        EstatusOrden NVARCHAR(50) NOT NULL DEFAULT 'BORRADOR',
        -- BORRADOR, PLANEADA, EN_EJECUCION, PENDIENTE_AUTORIZACION, CERRADA, CANCELADA, REVERTIDA
        
        RequiereAutorizacion BIT NOT NULL DEFAULT 0,
        MotivoAutorizacion NVARCHAR(500) NULL,
        AutorizadoPor UNIQUEIDENTIFIER NULL,
        FechaAutorizacion DATETIME2 NULL,
        
        -- Fechas operativas
        FechaOperacionMexico DATE NOT NULL,
        FechaProgramada DATE NULL,
        FechaInicioEjecucion DATETIME2 NULL,
        FechaFinEjecucion DATETIME2 NULL,
        FechaCierre DATETIME2 NULL,
        
        -- Responsables
        ResponsableID UNIQUEIDENTIFIER NULL,
        EjecutorID UNIQUEIDENTIFIER NULL,
        SupervisorID UNIQUEIDENTIFIER NULL,
        
        -- Origen
        OrigenOrden NVARCHAR(50) NOT NULL DEFAULT 'CAPTURA_DIRECTA',
        IDLegacyOrden NVARCHAR(100) NULL,
        
        -- Inventario
        AfectaInventario BIT NOT NULL DEFAULT 1,
        MovimientoInventarioGenerado BIT NOT NULL DEFAULT 0,
        
        -- Observaciones
        Observaciones NVARCHAR(1000) NULL,
        
        -- Control
        Activo BIT NOT NULL DEFAULT 1,
        FechaAltaUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaModificacionUTC DATETIME2 NULL,
        UsuarioAltaID UNIQUEIDENTIFIER NULL,
        UsuarioModificacionID UNIQUEIDENTIFIER NULL,
        
        CONSTRAINT FK_Orden_Plantilla FOREIGN KEY (PlantillaID) 
            REFERENCES Operaciones_Tablaje_Plantillas(PlantillaID)
    );
    
    CREATE UNIQUE INDEX IX_Ordenes_Folio ON Operaciones_Tablaje_Ordenes(EmpresaID, FolioOrden);
    CREATE INDEX IX_Ordenes_Empresa ON Operaciones_Tablaje_Ordenes(EmpresaID);
    CREATE INDEX IX_Ordenes_UnidadNegocio ON Operaciones_Tablaje_Ordenes(UnidadNegocioID);
    CREATE INDEX IX_Ordenes_Plantilla ON Operaciones_Tablaje_Ordenes(PlantillaID);
    CREATE INDEX IX_Ordenes_Estatus ON Operaciones_Tablaje_Ordenes(EstatusOrden);
    CREATE INDEX IX_Ordenes_FechaOp ON Operaciones_Tablaje_Ordenes(FechaOperacionMexico);
    
    PRINT 'Tabla Operaciones_Tablaje_Ordenes creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 5: Operaciones_Tablaje_OrdenesDetalle
-- Detalle de derivados producidos en cada orden
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_OrdenesDetalle')
BEGIN
    CREATE TABLE Operaciones_Tablaje_OrdenesDetalle (
        OrdenDetalleID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        OrdenID UNIQUEIDENTIFIER NOT NULL,
        PlantillaDetalleID UNIQUEIDENTIFIER NULL,
        
        -- Producto
        ProductoDerivadoID INT NULL,
        ProductoDerivadoCodigo NVARCHAR(50) NULL,
        ProductoDerivadoNombre NVARCHAR(200) NOT NULL,
        TipoDerivado NVARCHAR(50) NOT NULL,
        
        -- Cantidades esperadas (de la plantilla)
        CantidadEsperada DECIMAL(18,4) NULL,
        PorcentajeEsperado DECIMAL(5,2) NULL,
        
        -- Cantidades reales (capturadas)
        CantidadReal DECIMAL(18,4) NULL,
        PesoRealKg DECIMAL(18,4) NULL,
        PorcentajeReal DECIMAL(5,2) NULL,
        
        -- Desviación
        DesviacionCantidad DECIMAL(18,4) NULL,
        DesviacionPorcentaje DECIMAL(5,2) NULL,
        
        -- Costeo
        CostoUnitario DECIMAL(18,4) NULL,
        CostoTotal DECIMAL(18,4) NULL,
        PorcentajeCostoAsignado DECIMAL(5,2) NULL,
        
        -- Unidad
        UnidadID INT NULL,
        UnidadCodigo NVARCHAR(20) NULL,
        
        -- Inventario
        GeneraMovimiento BIT NOT NULL DEFAULT 1,
        MovimientoGenerado BIT NOT NULL DEFAULT 0,
        AlmacenDestinoID INT NULL,
        LoteGenerado NVARCHAR(100) NULL,
        
        -- Control
        Observaciones NVARCHAR(500) NULL,
        FechaCaptura DATETIME2 NULL,
        UsuarioCapturaID UNIQUEIDENTIFIER NULL,
        
        CONSTRAINT FK_OrdenDetalle_Orden FOREIGN KEY (OrdenID) 
            REFERENCES Operaciones_Tablaje_Ordenes(OrdenID)
    );
    
    CREATE INDEX IX_OrdenDetalle_Orden ON Operaciones_Tablaje_OrdenesDetalle(OrdenID);
    CREATE INDEX IX_OrdenDetalle_Producto ON Operaciones_Tablaje_OrdenesDetalle(ProductoDerivadoID);
    
    PRINT 'Tabla Operaciones_Tablaje_OrdenesDetalle creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 6: Operaciones_Tablaje_Rendimientos
-- Registro histórico de rendimientos por orden
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_Rendimientos')
BEGIN
    CREATE TABLE Operaciones_Tablaje_Rendimientos (
        RendimientoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        OrdenID UNIQUEIDENTIFIER NOT NULL,
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        
        -- Fecha operativa
        FechaOperacionMexico DATE NOT NULL,
        
        -- Plantilla referencia
        PlantillaID UNIQUEIDENTIFIER NULL,
        NombrePlantilla NVARCHAR(200) NULL,
        
        -- Insumo
        InsumoBaseID INT NULL,
        InsumoBaseNombre NVARCHAR(200) NULL,
        CantidadInsumoConsumido DECIMAL(18,4) NOT NULL,
        
        -- Rendimiento
        RendimientoEsperadoPorcentaje DECIMAL(5,2) NULL,
        RendimientoRealPorcentaje DECIMAL(5,2) NOT NULL,
        DesviacionPorcentaje DECIMAL(5,2) NULL,
        
        -- Clasificación
        ClasificacionRendimiento NVARCHAR(50) NULL, -- EXCELENTE, NORMAL, BAJO, CRITICO
        DentroTolerancia BIT NOT NULL DEFAULT 1,
        
        -- Costos
        CostoInsumo DECIMAL(18,4) NULL,
        CostoDerivados DECIMAL(18,4) NULL,
        CostoPerdido DECIMAL(18,4) NULL,
        
        -- Control
        FechaRegistroUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        
        CONSTRAINT FK_Rendimiento_Orden FOREIGN KEY (OrdenID) 
            REFERENCES Operaciones_Tablaje_Ordenes(OrdenID)
    );
    
    CREATE INDEX IX_Rendimientos_Orden ON Operaciones_Tablaje_Rendimientos(OrdenID);
    CREATE INDEX IX_Rendimientos_Empresa ON Operaciones_Tablaje_Rendimientos(EmpresaID);
    CREATE INDEX IX_Rendimientos_FechaOp ON Operaciones_Tablaje_Rendimientos(FechaOperacionMexico);
    CREATE INDEX IX_Rendimientos_Plantilla ON Operaciones_Tablaje_Rendimientos(PlantillaID);
    
    PRINT 'Tabla Operaciones_Tablaje_Rendimientos creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 7: Operaciones_Tablaje_Mermas
-- Registro detallado de mermas
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_Mermas')
BEGIN
    CREATE TABLE Operaciones_Tablaje_Mermas (
        MermaID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        OrdenID UNIQUEIDENTIFIER NOT NULL,
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        
        FechaOperacionMexico DATE NOT NULL,
        
        -- Tipo de merma
        TipoMerma NVARCHAR(50) NOT NULL, -- HUESO, GRASA, DESPERDICIO, EVAPORACION, OTRO
        Descripcion NVARCHAR(200) NULL,
        
        -- Cantidades
        CantidadKg DECIMAL(18,4) NOT NULL,
        PorcentajeSobreInsumo DECIMAL(5,2) NULL,
        
        -- Comparación
        MermaEsperadaKg DECIMAL(18,4) NULL,
        MermaEsperadaPorcentaje DECIMAL(5,2) NULL,
        DesviacionKg DECIMAL(18,4) NULL,
        DentroTolerancia BIT NOT NULL DEFAULT 1,
        
        -- Costeo
        CostoMerma DECIMAL(18,4) NULL,
        EsRecuperable BIT NOT NULL DEFAULT 0,
        
        -- Autorización (si excede tolerancia)
        RequiereAutorizacion BIT NOT NULL DEFAULT 0,
        AutorizadoPor UNIQUEIDENTIFIER NULL,
        FechaAutorizacion DATETIME2 NULL,
        
        -- Control
        Observaciones NVARCHAR(500) NULL,
        FechaRegistroUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        UsuarioRegistroID UNIQUEIDENTIFIER NULL,
        
        CONSTRAINT FK_Merma_Orden FOREIGN KEY (OrdenID) 
            REFERENCES Operaciones_Tablaje_Ordenes(OrdenID)
    );
    
    CREATE INDEX IX_Mermas_Orden ON Operaciones_Tablaje_Mermas(OrdenID);
    CREATE INDEX IX_Mermas_Empresa ON Operaciones_Tablaje_Mermas(EmpresaID);
    CREATE INDEX IX_Mermas_FechaOp ON Operaciones_Tablaje_Mermas(FechaOperacionMexico);
    CREATE INDEX IX_Mermas_Tipo ON Operaciones_Tablaje_Mermas(TipoMerma);
    
    PRINT 'Tabla Operaciones_Tablaje_Mermas creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 8: Operaciones_Tablaje_Costos
-- Costeo de derivados por orden
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_Costos')
BEGIN
    CREATE TABLE Operaciones_Tablaje_Costos (
        CostoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        OrdenID UNIQUEIDENTIFIER NOT NULL,
        OrdenDetalleID UNIQUEIDENTIFIER NULL,
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        
        FechaOperacionMexico DATE NOT NULL,
        
        -- Producto
        ProductoID INT NULL,
        ProductoCodigo NVARCHAR(50) NULL,
        ProductoNombre NVARCHAR(200) NULL,
        
        -- Costeo
        ReglaCosteo NVARCHAR(50) NOT NULL, -- PROPORCIONAL, FIJO, RESIDUAL
        CostoInsumoBase DECIMAL(18,4) NULL,
        PorcentajeAsignado DECIMAL(5,2) NULL,
        CostoAsignado DECIMAL(18,4) NOT NULL,
        CantidadProducida DECIMAL(18,4) NULL,
        CostoUnitario DECIMAL(18,4) NULL,
        
        -- Moneda
        MonedaID INT NOT NULL DEFAULT 1,
        TipoCambio DECIMAL(18,6) NULL DEFAULT 1,
        
        -- Control
        EsCostoFinal BIT NOT NULL DEFAULT 0,
        FechaCalculoUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        UsuarioCalculoID UNIQUEIDENTIFIER NULL,
        
        CONSTRAINT FK_Costo_Orden FOREIGN KEY (OrdenID) 
            REFERENCES Operaciones_Tablaje_Ordenes(OrdenID)
    );
    
    CREATE INDEX IX_Costos_Orden ON Operaciones_Tablaje_Costos(OrdenID);
    CREATE INDEX IX_Costos_Empresa ON Operaciones_Tablaje_Costos(EmpresaID);
    CREATE INDEX IX_Costos_FechaOp ON Operaciones_Tablaje_Costos(FechaOperacionMexico);
    CREATE INDEX IX_Costos_Producto ON Operaciones_Tablaje_Costos(ProductoID);
    
    PRINT 'Tabla Operaciones_Tablaje_Costos creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 9: Operaciones_Tablaje_SyncLog
-- Historial de sincronizaciones con sistemas externos
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_SyncLog')
BEGIN
    CREATE TABLE Operaciones_Tablaje_SyncLog (
        SyncLogID BIGINT IDENTITY(1,1) PRIMARY KEY,
        EmpresaID UNIQUEIDENTIFIER NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        
        -- Servidor origen
        ServidorID NVARCHAR(100) NOT NULL,
        ServidorNombre NVARCHAR(200) NULL,
        SistemaOrigen NVARCHAR(50) NULL,
        BaseDatosOrigen NVARCHAR(100) NULL,
        
        -- Tipo de sync
        TipoEntidad NVARCHAR(50) NOT NULL, -- PLANTILLAS, ORDENES, PRODUCTOS, UNIDADES
        Operacion NVARCHAR(50) NOT NULL, -- SYNC_COMPLETO, SYNC_INCREMENTAL, VALIDACION
        
        -- Timing
        FechaInicioUTC DATETIME2 NOT NULL,
        FechaFinUTC DATETIME2 NULL,
        DuracionSegundos INT NULL,
        
        -- Resultados
        RegistrosLeidos INT NOT NULL DEFAULT 0,
        RegistrosCreados INT NOT NULL DEFAULT 0,
        RegistrosActualizados INT NOT NULL DEFAULT 0,
        RegistrosSinCambios INT NOT NULL DEFAULT 0,
        RegistrosError INT NOT NULL DEFAULT 0,
        
        -- Estado
        Estado NVARCHAR(50) NOT NULL DEFAULT 'EN_PROCESO', -- EN_PROCESO, COMPLETADO, ERROR, CANCELADO
        MensajeError NVARCHAR(MAX) NULL,
        DetallesJSON NVARCHAR(MAX) NULL,
        
        -- Usuario
        EjecutadoPor UNIQUEIDENTIFIER NULL
    );
    
    CREATE INDEX IX_SyncLog_Servidor ON Operaciones_Tablaje_SyncLog(ServidorID);
    CREATE INDEX IX_SyncLog_Fecha ON Operaciones_Tablaje_SyncLog(FechaInicioUTC);
    CREATE INDEX IX_SyncLog_Estado ON Operaciones_Tablaje_SyncLog(Estado);
    
    PRINT 'Tabla Operaciones_Tablaje_SyncLog creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 10: Operaciones_Tablaje_SyncErrores
-- Errores detallados de sincronización
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_SyncErrores')
BEGIN
    CREATE TABLE Operaciones_Tablaje_SyncErrores (
        ErrorID BIGINT IDENTITY(1,1) PRIMARY KEY,
        SyncLogID BIGINT NOT NULL,
        
        -- Registro con error
        TipoEntidad NVARCHAR(50) NOT NULL,
        IDLegacy NVARCHAR(100) NULL,
        DatosRegistroJSON NVARCHAR(MAX) NULL,
        
        -- Error
        TipoError NVARCHAR(100) NOT NULL,
        MensajeError NVARCHAR(MAX) NOT NULL,
        StackTrace NVARCHAR(MAX) NULL,
        
        -- Resolución
        Resuelto BIT NOT NULL DEFAULT 0,
        FechaResolucion DATETIME2 NULL,
        ResolucionNotas NVARCHAR(500) NULL,
        
        -- Control
        FechaErrorUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        
        CONSTRAINT FK_SyncError_SyncLog FOREIGN KEY (SyncLogID) 
            REFERENCES Operaciones_Tablaje_SyncLog(SyncLogID)
    );
    
    CREATE INDEX IX_SyncErrores_Log ON Operaciones_Tablaje_SyncErrores(SyncLogID);
    CREATE INDEX IX_SyncErrores_Resuelto ON Operaciones_Tablaje_SyncErrores(Resuelto);
    
    PRINT 'Tabla Operaciones_Tablaje_SyncErrores creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 11: Operaciones_Tablaje_Autorizaciones
-- Workflow de autorizaciones
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_Autorizaciones')
BEGIN
    CREATE TABLE Operaciones_Tablaje_Autorizaciones (
        AutorizacionID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        
        -- Tipo de autorización
        TipoAutorizacion NVARCHAR(100) NOT NULL,
        -- PUBLICAR_PLANTILLA, MODIFICAR_PLANTILLA_PUBLICADA, MERMA_FUERA_TOLERANCIA,
        -- RENDIMIENTO_BAJO, CANCELAR_ORDEN, REPROCESAR_SYNC, CAMBIAR_COSTEO
        
        -- Entidad relacionada
        EntidadTipo NVARCHAR(50) NOT NULL, -- PLANTILLA, ORDEN, MERMA
        EntidadID UNIQUEIDENTIFIER NOT NULL,
        EntidadFolio NVARCHAR(100) NULL,
        
        -- Solicitante
        SolicitanteID UNIQUEIDENTIFIER NOT NULL,
        FechaSolicitudUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        MotivoSolicitud NVARCHAR(1000) NOT NULL,
        DatosSolicitudJSON NVARCHAR(MAX) NULL,
        
        -- Estado
        Estatus NVARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',
        -- PENDIENTE, APROBADA, RECHAZADA, CANCELADA, EXPIRADA
        
        -- Autorizador
        AutorizadorID UNIQUEIDENTIFIER NULL,
        FechaResolucionUTC DATETIME2 NULL,
        Comentarios NVARCHAR(1000) NULL,
        
        -- Escalamiento
        NivelEscalamiento INT NOT NULL DEFAULT 1,
        FechaExpiracion DATETIME2 NULL,
        
        -- Control
        FechaOperacionMexico DATE NOT NULL
    );
    
    CREATE INDEX IX_Autorizaciones_Empresa ON Operaciones_Tablaje_Autorizaciones(EmpresaID);
    CREATE INDEX IX_Autorizaciones_Estatus ON Operaciones_Tablaje_Autorizaciones(Estatus);
    CREATE INDEX IX_Autorizaciones_Tipo ON Operaciones_Tablaje_Autorizaciones(TipoAutorizacion);
    CREATE INDEX IX_Autorizaciones_Entidad ON Operaciones_Tablaje_Autorizaciones(EntidadTipo, EntidadID);
    
    PRINT 'Tabla Operaciones_Tablaje_Autorizaciones creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 12: Operaciones_Tablaje_Auditoria
-- Bitácora de auditoría
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_Auditoria')
BEGIN
    CREATE TABLE Operaciones_Tablaje_Auditoria (
        AuditoriaID BIGINT IDENTITY(1,1) PRIMARY KEY,
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        
        -- Entidad afectada
        EntidadTipo NVARCHAR(50) NOT NULL,
        EntidadID UNIQUEIDENTIFIER NOT NULL,
        EntidadFolio NVARCHAR(100) NULL,
        
        -- Acción
        Accion NVARCHAR(100) NOT NULL,
        -- CREAR, EDITAR, ELIMINAR, PUBLICAR, AUTORIZAR, RECHAZAR, CERRAR, CANCELAR, SINCRONIZAR
        
        -- Usuario
        UsuarioID UNIQUEIDENTIFIER NOT NULL,
        UsuarioNombre NVARCHAR(200) NULL,
        DireccionIP NVARCHAR(50) NULL,
        
        -- Datos
        ValoresAnterioresJSON NVARCHAR(MAX) NULL,
        ValoresNuevosJSON NVARCHAR(MAX) NULL,
        CamposModificados NVARCHAR(MAX) NULL,
        
        -- Contexto
        Descripcion NVARCHAR(500) NULL,
        Modulo NVARCHAR(50) NULL DEFAULT 'TABLAJERIA',
        
        -- Control
        FechaOperacionMexico DATE NOT NULL,
        FechaHoraUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    
    CREATE INDEX IX_Auditoria_Empresa ON Operaciones_Tablaje_Auditoria(EmpresaID);
    CREATE INDEX IX_Auditoria_Entidad ON Operaciones_Tablaje_Auditoria(EntidadTipo, EntidadID);
    CREATE INDEX IX_Auditoria_Usuario ON Operaciones_Tablaje_Auditoria(UsuarioID);
    CREATE INDEX IX_Auditoria_Fecha ON Operaciones_Tablaje_Auditoria(FechaHoraUTC);
    CREATE INDEX IX_Auditoria_FechaOp ON Operaciones_Tablaje_Auditoria(FechaOperacionMexico);
    
    PRINT 'Tabla Operaciones_Tablaje_Auditoria creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 13: Operaciones_Tablaje_Documentos
-- Documentos y evidencias
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_Documentos')
BEGIN
    CREATE TABLE Operaciones_Tablaje_Documentos (
        DocumentoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        
        -- Entidad relacionada
        EntidadTipo NVARCHAR(50) NOT NULL, -- PLANTILLA, ORDEN, MERMA, AUTORIZACION
        EntidadID UNIQUEIDENTIFIER NOT NULL,
        
        -- Documento
        TipoDocumento NVARCHAR(50) NOT NULL, -- FOTO, PDF, EXCEL, TICKET, OTRO
        NombreArchivo NVARCHAR(255) NOT NULL,
        Extension NVARCHAR(10) NULL,
        TamanoBytes BIGINT NULL,
        
        -- Almacenamiento
        RutaAlmacenamiento NVARCHAR(500) NULL,
        URLPublica NVARCHAR(500) NULL,
        ContenidoBase64 NVARCHAR(MAX) NULL, -- Solo para archivos pequeños
        
        -- Metadatos
        Descripcion NVARCHAR(500) NULL,
        EsEvidencia BIT NOT NULL DEFAULT 0,
        
        -- Control
        FechaSubidaUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        UsuarioSubidaID UNIQUEIDENTIFIER NULL,
        Activo BIT NOT NULL DEFAULT 1
    );
    
    CREATE INDEX IX_Documentos_Entidad ON Operaciones_Tablaje_Documentos(EntidadTipo, EntidadID);
    CREATE INDEX IX_Documentos_Empresa ON Operaciones_Tablaje_Documentos(EmpresaID);
    
    PRINT 'Tabla Operaciones_Tablaje_Documentos creada exitosamente';
END
GO

-- ============================================================================
-- TABLA 14: Operaciones_Tablaje_EventosContables
-- Eventos para integración con contabilidad
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Operaciones_Tablaje_EventosContables')
BEGIN
    CREATE TABLE Operaciones_Tablaje_EventosContables (
        EventoContableID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        EmpresaID UNIQUEIDENTIFIER NOT NULL,
        UnidadNegocioID UNIQUEIDENTIFIER NULL,
        
        -- Fecha operativa
        FechaOperacionMexico DATE NOT NULL,
        
        -- Origen
        OrdenID UNIQUEIDENTIFIER NOT NULL,
        OrdenFolio NVARCHAR(50) NULL,
        
        -- Tipo de evento
        TipoEvento NVARCHAR(100) NOT NULL,
        -- TABLAJE_CONSUMO_INSUMO_BASE, TABLAJE_ALTA_DERIVADOS, TABLAJE_REGISTRO_MERMA,
        -- TABLAJE_AJUSTE_COSTO, TABLAJE_VARIACION_RENDIMIENTO, TABLAJE_CANCELACION, TABLAJE_REVERSION
        
        -- Producto
        ProductoID INT NULL,
        ProductoCodigo NVARCHAR(50) NULL,
        ProductoNombre NVARCHAR(200) NULL,
        Cantidad DECIMAL(18,4) NULL,
        UnidadID INT NULL,
        
        -- Importes
        Importe DECIMAL(18,4) NOT NULL,
        MonedaID INT NOT NULL DEFAULT 1,
        TipoCambio DECIMAL(18,6) NULL DEFAULT 1,
        ImporteMXN DECIMAL(18,4) NULL,
        
        -- Cuentas contables sugeridas
        CuentaCargoSugerida NVARCHAR(50) NULL,
        CuentaAbonoSugerida NVARCHAR(50) NULL,
        CentroCostoID INT NULL,
        CentroCostoCodigo NVARCHAR(50) NULL,
        
        -- Estado contable
        EstatusContable NVARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',
        -- PENDIENTE, PROCESADO, CONTABILIZADO, ERROR, IGNORADO
        
        -- Póliza generada (si aplica)
        PolizaID NVARCHAR(100) NULL,
        NumeroPoliza NVARCHAR(50) NULL,
        FechaContabilizacion DATE NULL,
        
        -- Control
        Descripcion NVARCHAR(500) NULL,
        FechaCreacionUTC DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaProcesoUTC DATETIME2 NULL,
        UsuarioProcesoID UNIQUEIDENTIFIER NULL,
        MensajeError NVARCHAR(500) NULL,
        
        CONSTRAINT FK_EventoContable_Orden FOREIGN KEY (OrdenID) 
            REFERENCES Operaciones_Tablaje_Ordenes(OrdenID)
    );
    
    CREATE INDEX IX_EventosContables_Empresa ON Operaciones_Tablaje_EventosContables(EmpresaID);
    CREATE INDEX IX_EventosContables_FechaOp ON Operaciones_Tablaje_EventosContables(FechaOperacionMexico);
    CREATE INDEX IX_EventosContables_Orden ON Operaciones_Tablaje_EventosContables(OrdenID);
    CREATE INDEX IX_EventosContables_Tipo ON Operaciones_Tablaje_EventosContables(TipoEvento);
    CREATE INDEX IX_EventosContables_Estatus ON Operaciones_Tablaje_EventosContables(EstatusContable);
    
    PRINT 'Tabla Operaciones_Tablaje_EventosContables creada exitosamente';
END
GO

-- ============================================================================
-- FIN DEL SCRIPT DDL
-- ============================================================================
PRINT '============================================';
PRINT 'DDL TABLAJERÍA COMPLETADO';
PRINT '14 tablas creadas/verificadas';
PRINT '============================================';
GO
