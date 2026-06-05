-- =====================================================
-- EDARSA HUB - DDL Triggers CRM
-- =====================================================
-- Tablas para el sistema de triggers avanzados del CRM
-- Ejecutar en EDARSAHUB SQL Server
-- =====================================================

-- Tabla principal de Triggers
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CRM_Triggers')
BEGIN
    CREATE TABLE CRM_Triggers (
        TriggerID NVARCHAR(50) PRIMARY KEY,
        EmpresaID NVARCHAR(50) NOT NULL,
        Nombre NVARCHAR(200) NOT NULL,
        Descripcion NVARCHAR(500),
        TipoEvento NVARCHAR(50) NOT NULL,  -- OPORTUNIDAD_CREADA, ETAPA_CAMBIADA, etc.
        CondicionesJSON NVARCHAR(MAX),      -- Condiciones en JSON
        AccionesJSON NVARCHAR(MAX) NOT NULL, -- Acciones en JSON
        Prioridad INT DEFAULT 100,
        Activo BIT DEFAULT 1,
        UsuarioCreacionID NVARCHAR(50),
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FechaModificacion DATETIME,
        
        CONSTRAINT FK_Trigger_Empresa FOREIGN KEY (EmpresaID) 
            REFERENCES Empresas(EmpresaID)
    );
    
    CREATE INDEX IX_CRM_Triggers_Empresa ON CRM_Triggers(EmpresaID);
    CREATE INDEX IX_CRM_Triggers_Evento ON CRM_Triggers(TipoEvento);
    CREATE INDEX IX_CRM_Triggers_Activo ON CRM_Triggers(Activo);
    
    PRINT 'Tabla CRM_Triggers creada';
END
GO

-- Tabla de Log de Ejecución de Triggers
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CRM_Trigger_Log')
BEGIN
    CREATE TABLE CRM_Trigger_Log (
        LogID NVARCHAR(50) PRIMARY KEY,
        TriggerID NVARCHAR(50) NOT NULL,
        EntidadID NVARCHAR(50),           -- ID de la oportunidad/lead afectado
        EmpresaID NVARCHAR(50) NOT NULL,
        Exitoso BIT DEFAULT 0,
        ResultadoJSON NVARCHAR(MAX),       -- Detalle del resultado
        FechaEjecucion DATETIME DEFAULT GETDATE(),
        
        CONSTRAINT FK_TriggerLog_Trigger FOREIGN KEY (TriggerID) 
            REFERENCES CRM_Triggers(TriggerID)
    );
    
    CREATE INDEX IX_CRM_TriggerLog_Fecha ON CRM_Trigger_Log(FechaEjecucion);
    CREATE INDEX IX_CRM_TriggerLog_Trigger ON CRM_Trigger_Log(TriggerID);
    
    PRINT 'Tabla CRM_Trigger_Log creada';
END
GO

-- Tabla de Tareas de Seguimiento
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'CRM_Tareas')
BEGIN
    CREATE TABLE CRM_Tareas (
        TareaID NVARCHAR(50) PRIMARY KEY,
        EmpresaID NVARCHAR(50) NOT NULL,
        OportunidadID NVARCHAR(50),
        ResponsableID NVARCHAR(50),
        Titulo NVARCHAR(200) NOT NULL,
        Descripcion NVARCHAR(1000),
        FechaVencimiento DATETIME,
        Prioridad NVARCHAR(20) DEFAULT 'MEDIA',  -- BAJA, MEDIA, ALTA, URGENTE
        EstatusID INT DEFAULT 1,                  -- 1=Pendiente, 2=Completada, 3=Cancelada
        AutoGenerada BIT DEFAULT 0,
        FechaCreacion DATETIME DEFAULT GETDATE(),
        FechaCompletada DATETIME,
        
        CONSTRAINT FK_Tarea_Empresa FOREIGN KEY (EmpresaID) 
            REFERENCES Empresas(EmpresaID),
        CONSTRAINT FK_Tarea_Oportunidad FOREIGN KEY (OportunidadID) 
            REFERENCES CRM_Oportunidades(OportunidadID)
    );
    
    CREATE INDEX IX_CRM_Tareas_Empresa ON CRM_Tareas(EmpresaID);
    CREATE INDEX IX_CRM_Tareas_Oportunidad ON CRM_Tareas(OportunidadID);
    CREATE INDEX IX_CRM_Tareas_Vencimiento ON CRM_Tareas(FechaVencimiento);
    CREATE INDEX IX_CRM_Tareas_Estatus ON CRM_Tareas(EstatusID);
    
    PRINT 'Tabla CRM_Tareas creada';
END
GO

-- Agregar columna NotificacionEnviada a CRM_Actividades si no existe
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('CRM_Actividades') AND name = 'NotificacionEnviada'
)
BEGIN
    ALTER TABLE CRM_Actividades ADD NotificacionEnviada BIT DEFAULT 0;
    ALTER TABLE CRM_Actividades ADD FechaNotificacion DATETIME;
    PRINT 'Columnas de notificación agregadas a CRM_Actividades';
END
GO

-- Agregar columna DiasSLAMaximo a CRM_Config_PipelineEtapas si no existe
IF NOT EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('CRM_Config_PipelineEtapas') AND name = 'DiasSLAMaximo'
)
BEGIN
    ALTER TABLE CRM_Config_PipelineEtapas ADD DiasSLAMaximo INT;
    PRINT 'Columna DiasSLAMaximo agregada a CRM_Config_PipelineEtapas';
    
    -- Valores por defecto de SLA por etapa
    UPDATE CRM_Config_PipelineEtapas SET DiasSLAMaximo = 3 WHERE Nombre LIKE '%Prospecci%';
    UPDATE CRM_Config_PipelineEtapas SET DiasSLAMaximo = 5 WHERE Nombre LIKE '%Calific%';
    UPDATE CRM_Config_PipelineEtapas SET DiasSLAMaximo = 7 WHERE Nombre LIKE '%Propuesta%';
    UPDATE CRM_Config_PipelineEtapas SET DiasSLAMaximo = 10 WHERE Nombre LIKE '%Negociaci%';
    UPDATE CRM_Config_PipelineEtapas SET DiasSLAMaximo = 5 WHERE Nombre LIKE '%Cierre%';
END
GO

-- =====================================================
-- TRIGGERS DE EJEMPLO (Semilla)
-- =====================================================

-- Trigger: Crear actividad de seguimiento al crear oportunidad
IF NOT EXISTS (SELECT 1 FROM CRM_Triggers WHERE Nombre = 'Seguimiento inicial nueva oportunidad')
BEGIN
    INSERT INTO CRM_Triggers (
        TriggerID, EmpresaID, Nombre, TipoEvento,
        CondicionesJSON, AccionesJSON, Prioridad, Activo, FechaCreacion
    ) VALUES (
        NEWID(), 
        'd290f1ee-6c54-4b01-90e6-d701748f0851',
        'Seguimiento inicial nueva oportunidad',
        'OPORTUNIDAD_CREADA',
        '{}',
        '[{"tipo":"CREAR_ACTIVIDAD","titulo":"Primer contacto con {nombre_oportunidad}","descripcion":"Realizar primer contacto con el prospecto","dias_programar":1}]',
        100, 1, GETDATE()
    );
    PRINT 'Trigger de ejemplo creado: Seguimiento inicial';
END
GO

-- Trigger: Notificar al ganar oportunidad
IF NOT EXISTS (SELECT 1 FROM CRM_Triggers WHERE Nombre = 'Notificación oportunidad ganada')
BEGIN
    INSERT INTO CRM_Triggers (
        TriggerID, EmpresaID, Nombre, TipoEvento,
        CondicionesJSON, AccionesJSON, Prioridad, Activo, FechaCreacion
    ) VALUES (
        NEWID(), 
        'd290f1ee-6c54-4b01-90e6-d701748f0851',
        'Notificación oportunidad ganada',
        'OPORTUNIDAD_GANADA',
        '{}',
        '[{"tipo":"CREAR_NOTIFICACION","titulo":"¡Oportunidad Ganada!","mensaje":"La oportunidad {nombre_oportunidad} ha sido cerrada como ganada por ${monto_estimado}"}]',
        50, 1, GETDATE()
    );
    PRINT 'Trigger de ejemplo creado: Notificación ganada';
END
GO

-- Trigger: Alerta SLA vencido
IF NOT EXISTS (SELECT 1 FROM CRM_Triggers WHERE Nombre = 'Alerta SLA vencido')
BEGIN
    INSERT INTO CRM_Triggers (
        TriggerID, EmpresaID, Nombre, TipoEvento,
        CondicionesJSON, AccionesJSON, Prioridad, Activo, FechaCreacion
    ) VALUES (
        NEWID(), 
        'd290f1ee-6c54-4b01-90e6-d701748f0851',
        'Alerta SLA vencido',
        'SLA_VENCIDO',
        '{}',
        '[{"tipo":"CREAR_NOTIFICACION","titulo":"⚠️ SLA Vencido","mensaje":"La oportunidad {nombre_oportunidad} lleva {dias_en_etapa} días en etapa {etapa_nombre}"},{"tipo":"CREAR_TAREA_SEGUIMIENTO","titulo":"Revisar oportunidad estancada: {nombre_oportunidad}","dias_programar":1,"prioridad":"ALTA"}]',
        10, 1, GETDATE()
    );
    PRINT 'Trigger de ejemplo creado: Alerta SLA';
END
GO

PRINT '========================================';
PRINT 'DDL CRM Triggers completado';
PRINT '========================================';
