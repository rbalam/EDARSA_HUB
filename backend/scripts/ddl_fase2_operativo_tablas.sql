-- =============================================================================
-- DDL FASE B-P0-B: Tablas SQL para fase2_operativo
-- EDARSAHUB SQL Server
-- Fecha: 25 Mayo 2026
-- IDEMPOTENTE: Puede ejecutarse múltiples veces sin error
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Operativo_Notificaciones_Log
-- Reemplaza: MongoDB notificaciones_log
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_Notificaciones_Log', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_Notificaciones_Log (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        NotificacionID VARCHAR(50) NOT NULL,
        TipoEvento VARCHAR(50) NOT NULL,
        WorkflowID VARCHAR(50) NULL,
        TareaID VARCHAR(50) NULL,
        Destinatario VARCHAR(200) NULL,
        DestinatarioEmail VARCHAR(200) NULL,
        Titulo VARCHAR(500) NULL,
        Mensaje NVARCHAR(MAX) NULL,
        Estado VARCHAR(50) DEFAULT 'PENDIENTE',
        Canal VARCHAR(50) DEFAULT 'EMAIL',
        FechaEnvio DATETIME2 DEFAULT GETUTCDATE(),
        FechaLeido DATETIME2 NULL,
        ErrorMensaje NVARCHAR(MAX) NULL,
        MetadatosJSON NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_OpNotif_NotificacionID UNIQUE (NotificacionID)
    );
    
    CREATE INDEX IX_OpNotif_TipoEvento ON Operativo_Notificaciones_Log(TipoEvento);
    CREATE INDEX IX_OpNotif_WorkflowID ON Operativo_Notificaciones_Log(WorkflowID);
    CREATE INDEX IX_OpNotif_TareaID ON Operativo_Notificaciones_Log(TareaID);
    CREATE INDEX IX_OpNotif_FechaEnvio ON Operativo_Notificaciones_Log(FechaEnvio DESC);
    CREATE INDEX IX_OpNotif_Estado ON Operativo_Notificaciones_Log(Estado);
    
    PRINT 'CREADA: Operativo_Notificaciones_Log';
END
ELSE
    PRINT 'EXISTE: Operativo_Notificaciones_Log';
GO

-- -----------------------------------------------------------------------------
-- 2. Workflow_Justificaciones
-- Reemplaza: MongoDB justificaciones_inventario
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Workflow_Justificaciones', 'U') IS NULL
BEGIN
    CREATE TABLE Workflow_Justificaciones (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        JustificacionID VARCHAR(50) NOT NULL,
        WorkflowID VARCHAR(50) NOT NULL,
        DetalleID VARCHAR(50) NULL,
        CodigoProducto VARCHAR(50) NULL,
        TipoJustificacion VARCHAR(50) NOT NULL,
        Descripcion NVARCHAR(MAX) NULL,
        CantidadJustificada DECIMAL(18,4) NULL,
        ValorJustificado DECIMAL(18,2) NULL,
        EvidenciaURL VARCHAR(500) NULL,
        UsuarioID VARCHAR(50) NOT NULL,
        UsuarioNombre VARCHAR(200) NULL,
        Estado VARCHAR(50) DEFAULT 'PENDIENTE',
        FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
        FechaRevision DATETIME2 NULL,
        RevisadoPorID VARCHAR(50) NULL,
        Comentarios NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_WfJust_JustificacionID UNIQUE (JustificacionID)
    );
    
    CREATE INDEX IX_WfJust_WorkflowID ON Workflow_Justificaciones(WorkflowID);
    CREATE INDEX IX_WfJust_DetalleID ON Workflow_Justificaciones(DetalleID);
    CREATE INDEX IX_WfJust_Estado ON Workflow_Justificaciones(Estado);
    
    PRINT 'CREADA: Workflow_Justificaciones';
END
ELSE
    PRINT 'EXISTE: Workflow_Justificaciones';
GO

-- -----------------------------------------------------------------------------
-- 3. Workflow_DecisionesAuditoria
-- Reemplaza: MongoDB decisiones_auditoria
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Workflow_DecisionesAuditoria', 'U') IS NULL
BEGIN
    CREATE TABLE Workflow_DecisionesAuditoria (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        DecisionID VARCHAR(50) NOT NULL,
        WorkflowID VARCHAR(50) NOT NULL,
        TipoDecision VARCHAR(50) NOT NULL,
        Decision VARCHAR(50) NOT NULL,
        Comentario NVARCHAR(MAX) NULL,
        UsuarioID VARCHAR(50) NOT NULL,
        UsuarioNombre VARCHAR(200) NULL,
        CicloAuditoria INT DEFAULT 1,
        AccionSiguiente VARCHAR(100) NULL,
        FechaDecision DATETIME2 DEFAULT GETUTCDATE(),
        MetadatosJSON NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_WfDec_DecisionID UNIQUE (DecisionID)
    );
    
    CREATE INDEX IX_WfDec_WorkflowID ON Workflow_DecisionesAuditoria(WorkflowID);
    CREATE INDEX IX_WfDec_FechaDecision ON Workflow_DecisionesAuditoria(FechaDecision DESC);
    
    PRINT 'CREADA: Workflow_DecisionesAuditoria';
END
ELSE
    PRINT 'EXISTE: Workflow_DecisionesAuditoria';
GO

-- -----------------------------------------------------------------------------
-- 4. Operativo_HistorialAsignaciones
-- Reemplaza: MongoDB historial_asignaciones
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_HistorialAsignaciones', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_HistorialAsignaciones (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        HistorialID VARCHAR(50) NOT NULL,
        TareaID VARCHAR(50) NOT NULL,
        WorkflowID VARCHAR(50) NULL,
        UsuarioAnteriorID VARCHAR(50) NULL,
        UsuarioAnteriorNombre VARCHAR(200) NULL,
        UsuarioNuevoID VARCHAR(50) NULL,
        UsuarioNuevoNombre VARCHAR(200) NULL,
        AsignadoPorID VARCHAR(50) NULL,
        AsignadoPorNombre VARCHAR(200) NULL,
        TipoAsignacion VARCHAR(50) DEFAULT 'MANUAL',
        Motivo NVARCHAR(MAX) NULL,
        FechaAsignacion DATETIME2 DEFAULT GETUTCDATE(),
        CONSTRAINT UQ_OpHist_HistorialID UNIQUE (HistorialID)
    );
    
    CREATE INDEX IX_OpHist_TareaID ON Operativo_HistorialAsignaciones(TareaID);
    CREATE INDEX IX_OpHist_WorkflowID ON Operativo_HistorialAsignaciones(WorkflowID);
    CREATE INDEX IX_OpHist_FechaAsignacion ON Operativo_HistorialAsignaciones(FechaAsignacion DESC);
    
    PRINT 'CREADA: Operativo_HistorialAsignaciones';
END
ELSE
    PRINT 'EXISTE: Operativo_HistorialAsignaciones';
GO

-- -----------------------------------------------------------------------------
-- 5. Operativo_ResponsabilidadEconomica
-- Reemplaza: MongoDB responsabilidades
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_ResponsabilidadEconomica', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_ResponsabilidadEconomica (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        ResponsabilidadID VARCHAR(50) NOT NULL,
        WorkflowID VARCHAR(50) NOT NULL,
        ServerID VARCHAR(50) NULL,
        SucursalID VARCHAR(100) NULL,
        SucursalNombre VARCHAR(100) NULL,
        ResponsableID VARCHAR(50) NULL,
        ResponsableNombre VARCHAR(200) NULL,
        MontoTotal DECIMAL(18,2) NOT NULL DEFAULT 0,
        MontoJustificado DECIMAL(18,2) DEFAULT 0,
        MontoNoJustificado DECIMAL(18,2) DEFAULT 0,
        Estado VARCHAR(50) DEFAULT 'PENDIENTE',
        ExcedeMinimo BIT DEFAULT 0,
        UmbralMinimo DECIMAL(18,2) DEFAULT 500,
        FechaCalculo DATETIME2 DEFAULT GETUTCDATE(),
        FechaUltimaActualizacion DATETIME2 NULL,
        FechaAprobacion DATETIME2 NULL,
        AprobadoPorID VARCHAR(50) NULL,
        Comentarios NVARCHAR(MAX) NULL,
        MetadatosJSON NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_OpResp_ResponsabilidadID UNIQUE (ResponsabilidadID)
    );
    
    CREATE INDEX IX_OpResp_WorkflowID ON Operativo_ResponsabilidadEconomica(WorkflowID);
    CREATE INDEX IX_OpResp_Estado ON Operativo_ResponsabilidadEconomica(Estado);
    CREATE INDEX IX_OpResp_SucursalID ON Operativo_ResponsabilidadEconomica(SucursalID);
    CREATE INDEX IX_OpResp_FechaCalculo ON Operativo_ResponsabilidadEconomica(FechaCalculo DESC);
    
    PRINT 'CREADA: Operativo_ResponsabilidadEconomica';
END
ELSE
    PRINT 'EXISTE: Operativo_ResponsabilidadEconomica';
GO

-- -----------------------------------------------------------------------------
-- 6. Operativo_CargosResponsabilidad
-- Reemplaza: MongoDB cargos_responsabilidad
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_CargosResponsabilidad', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_CargosResponsabilidad (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        CargoID VARCHAR(50) NOT NULL,
        ResponsabilidadID VARCHAR(50) NOT NULL,
        WorkflowID VARCHAR(50) NOT NULL,
        SucursalID VARCHAR(100) NULL,
        ResponsableID VARCHAR(50) NULL,
        ResponsableNombre VARCHAR(200) NULL,
        MontoPropuesto DECIMAL(18,2) NOT NULL,
        MontoFinal DECIMAL(18,2) NULL,
        EstatusCargo VARCHAR(50) DEFAULT 'PROPUESTO',
        FechaPropuesta DATETIME2 DEFAULT GETUTCDATE(),
        FechaAprobacion DATETIME2 NULL,
        AprobadoPorID VARCHAR(50) NULL,
        FechaRechazo DATETIME2 NULL,
        RechazadoPorID VARCHAR(50) NULL,
        MotivoRechazo NVARCHAR(MAX) NULL,
        FechaDisputa DATETIME2 NULL,
        DisputadoPorID VARCHAR(50) NULL,
        MotivoDisputa NVARCHAR(MAX) NULL,
        FechaResolucion DATETIME2 NULL,
        ResueltoPorID VARCHAR(50) NULL,
        Comentarios NVARCHAR(MAX) NULL,
        MetadatosJSON NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_OpCargo_CargoID UNIQUE (CargoID)
    );
    
    CREATE INDEX IX_OpCargo_ResponsabilidadID ON Operativo_CargosResponsabilidad(ResponsabilidadID);
    CREATE INDEX IX_OpCargo_WorkflowID ON Operativo_CargosResponsabilidad(WorkflowID);
    CREATE INDEX IX_OpCargo_EstatusCargo ON Operativo_CargosResponsabilidad(EstatusCargo);
    CREATE INDEX IX_OpCargo_FechaPropuesta ON Operativo_CargosResponsabilidad(FechaPropuesta DESC);
    
    PRINT 'CREADA: Operativo_CargosResponsabilidad';
END
ELSE
    PRINT 'EXISTE: Operativo_CargosResponsabilidad';
GO

-- -----------------------------------------------------------------------------
-- 7. Operativo_HistorialCargos
-- Reemplaza: MongoDB historial de cargos
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_HistorialCargos', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_HistorialCargos (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        HistorialID VARCHAR(50) NOT NULL,
        CargoID VARCHAR(50) NOT NULL,
        Accion VARCHAR(50) NOT NULL,
        UsuarioID VARCHAR(50) NOT NULL,
        UsuarioNombre VARCHAR(200) NULL,
        Detalle NVARCHAR(MAX) NULL,
        EstadoAnterior VARCHAR(50) NULL,
        EstadoNuevo VARCHAR(50) NULL,
        Fecha DATETIME2 DEFAULT GETUTCDATE(),
        CONSTRAINT UQ_OpHistCargo_HistorialID UNIQUE (HistorialID)
    );
    
    CREATE INDEX IX_OpHistCargo_CargoID ON Operativo_HistorialCargos(CargoID);
    CREATE INDEX IX_OpHistCargo_Fecha ON Operativo_HistorialCargos(Fecha DESC);
    
    PRINT 'CREADA: Operativo_HistorialCargos';
END
ELSE
    PRINT 'EXISTE: Operativo_HistorialCargos';
GO

-- -----------------------------------------------------------------------------
-- 8. Scheduler_BitacoraJobs - REUTILIZAR EXISTENTE
-- NO SE CREA - Ya existe con 909 registros
-- -----------------------------------------------------------------------------
PRINT 'REUTILIZADA: Scheduler_BitacoraJobs (existente)';
GO

-- -----------------------------------------------------------------------------
-- 9. Operativo_TareasCompras
-- Reemplaza: MongoDB tareas_operativas_compras
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_TareasCompras', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_TareasCompras (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        TareaID VARCHAR(50) NOT NULL,
        AutomatizacionID VARCHAR(50) NULL,
        TipoTarea VARCHAR(50) NOT NULL,
        Titulo VARCHAR(500) NULL,
        Descripcion NVARCHAR(MAX) NULL,
        ServerID VARCHAR(50) NULL,
        SucursalID VARCHAR(100) NULL,
        SucursalNombre VARCHAR(100) NULL,
        UsuarioAsignadoID VARCHAR(50) NULL,
        UsuarioAsignadoNombre VARCHAR(200) NULL,
        Estado VARCHAR(50) DEFAULT 'PENDIENTE',
        Prioridad VARCHAR(20) DEFAULT 'NORMAL',
        FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
        FechaLimite DATETIME2 NULL,
        FechaCompletada DATETIME2 NULL,
        Resultado NVARCHAR(MAX) NULL,
        MetadatosJSON NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_OpTareaComp_TareaID UNIQUE (TareaID)
    );
    
    CREATE INDEX IX_OpTareaComp_Estado ON Operativo_TareasCompras(Estado);
    CREATE INDEX IX_OpTareaComp_AutomatizacionID ON Operativo_TareasCompras(AutomatizacionID);
    CREATE INDEX IX_OpTareaComp_FechaCreacion ON Operativo_TareasCompras(FechaCreacion DESC);
    
    PRINT 'CREADA: Operativo_TareasCompras';
END
ELSE
    PRINT 'EXISTE: Operativo_TareasCompras';
GO

-- -----------------------------------------------------------------------------
-- 10. Operativo_BitacoraCompras
-- Reemplaza: MongoDB auditoria_compras_bitacora
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_BitacoraCompras', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_BitacoraCompras (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        BitacoraID VARCHAR(50) NOT NULL,
        AutomatizacionID VARCHAR(50) NULL,
        Accion VARCHAR(50) NOT NULL,
        UsuarioID VARCHAR(50) NULL,
        UsuarioNombre VARCHAR(200) NULL,
        Detalle NVARCHAR(MAX) NULL,
        EstadoAnterior VARCHAR(50) NULL,
        EstadoNuevo VARCHAR(50) NULL,
        Fecha DATETIME2 DEFAULT GETUTCDATE(),
        MetadatosJSON NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_OpBitComp_BitacoraID UNIQUE (BitacoraID)
    );
    
    CREATE INDEX IX_OpBitComp_AutomatizacionID ON Operativo_BitacoraCompras(AutomatizacionID);
    CREATE INDEX IX_OpBitComp_Fecha ON Operativo_BitacoraCompras(Fecha DESC);
    
    PRINT 'CREADA: Operativo_BitacoraCompras';
END
ELSE
    PRINT 'EXISTE: Operativo_BitacoraCompras';
GO

-- -----------------------------------------------------------------------------
-- 11. Operativo_PedidosProcesados
-- Reemplaza: MongoDB pedidos_procesados_automatizacion
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_PedidosProcesados', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_PedidosProcesados (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        PedidoID VARCHAR(50) NOT NULL,
        AutomatizacionID VARCHAR(50) NOT NULL,
        ServerID VARCHAR(50) NULL,
        SucursalID VARCHAR(100) NULL,
        FolioInventario VARCHAR(100) NULL,
        Estado VARCHAR(50) DEFAULT 'PROCESADO',
        CantidadItems INT DEFAULT 0,
        MontoTotal DECIMAL(18,2) DEFAULT 0,
        FechaProcesamiento DATETIME2 DEFAULT GETUTCDATE(),
        DetalleJSON NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_OpPedProc_PedidoID UNIQUE (PedidoID)
    );
    
    CREATE INDEX IX_OpPedProc_AutomatizacionID ON Operativo_PedidosProcesados(AutomatizacionID);
    CREATE INDEX IX_OpPedProc_FechaProcesamiento ON Operativo_PedidosProcesados(FechaProcesamiento DESC);
    
    PRINT 'CREADA: Operativo_PedidosProcesados';
END
ELSE
    PRINT 'EXISTE: Operativo_PedidosProcesados';
GO

-- -----------------------------------------------------------------------------
-- 12. Operativo_AuditoriasProgramadas
-- Reemplaza: MongoDB auditorias programadas
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_AuditoriasProgramadas', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_AuditoriasProgramadas (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        AuditoriaID VARCHAR(50) NOT NULL,
        Nombre VARCHAR(200) NOT NULL,
        Descripcion NVARCHAR(MAX) NULL,
        ServerID VARCHAR(50) NULL,
        SucursalID VARCHAR(100) NULL,
        AlmacenID VARCHAR(50) NULL,
        Frecuencia VARCHAR(50) NOT NULL,
        DiaSemana INT NULL,
        DiaMes INT NULL,
        HoraEjecucion VARCHAR(10) NULL,
        Timezone VARCHAR(50) DEFAULT 'America/Mexico_City',
        ProximaEjecucion DATETIME2 NULL,
        UltimaEjecucion DATETIME2 NULL,
        Estado VARCHAR(50) DEFAULT 'ACTIVA',
        UsuarioCreadorID VARCHAR(50) NULL,
        FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
        FechaActualizacion DATETIME2 NULL,
        ConfiguracionJSON NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_OpAudProg_AuditoriaID UNIQUE (AuditoriaID)
    );
    
    CREATE INDEX IX_OpAudProg_ProximaEjecucion ON Operativo_AuditoriasProgramadas(ProximaEjecucion);
    CREATE INDEX IX_OpAudProg_Estado ON Operativo_AuditoriasProgramadas(Estado);
    CREATE INDEX IX_OpAudProg_ServerID ON Operativo_AuditoriasProgramadas(ServerID);
    
    PRINT 'CREADA: Operativo_AuditoriasProgramadas';
END
ELSE
    PRINT 'EXISTE: Operativo_AuditoriasProgramadas';
GO

-- -----------------------------------------------------------------------------
-- 13. Operativo_DocumentosGenerados
-- Reemplaza: MongoDB documentos_generados
-- -----------------------------------------------------------------------------
IF OBJECT_ID('Operativo_DocumentosGenerados', 'U') IS NULL
BEGIN
    CREATE TABLE Operativo_DocumentosGenerados (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        DocumentoID VARCHAR(50) NOT NULL,
        WorkflowID VARCHAR(50) NULL,
        TipoDocumento VARCHAR(50) NOT NULL,
        NombreArchivo VARCHAR(500) NULL,
        URLDescarga VARCHAR(1000) NULL,
        Formato VARCHAR(20) DEFAULT 'PDF',
        TamanioBytes BIGINT NULL,
        UsuarioGeneradorID VARCHAR(50) NULL,
        Estado VARCHAR(50) DEFAULT 'GENERADO',
        FechaGeneracion DATETIME2 DEFAULT GETUTCDATE(),
        FechaExpiracion DATETIME2 NULL,
        MetadatosJSON NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_OpDocGen_DocumentoID UNIQUE (DocumentoID)
    );
    
    CREATE INDEX IX_OpDocGen_WorkflowID ON Operativo_DocumentosGenerados(WorkflowID);
    CREATE INDEX IX_OpDocGen_TipoDocumento ON Operativo_DocumentosGenerados(TipoDocumento);
    CREATE INDEX IX_OpDocGen_FechaGeneracion ON Operativo_DocumentosGenerados(FechaGeneracion DESC);
    
    PRINT 'CREADA: Operativo_DocumentosGenerados';
END
ELSE
    PRINT 'EXISTE: Operativo_DocumentosGenerados';
GO

-- =============================================================================
-- FIN DDL FASE B-P0-B
-- =============================================================================
PRINT '=== DDL FASE B-P0-B COMPLETADO ===';
GO
