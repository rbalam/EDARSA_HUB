# FASE B-P0-B: Validación y Creación DDL para fase2_operativo

**Fecha:** 25 Mayo 2026  
**Fase:** B-P0-B  
**Módulo:** fase2_operativo  
**Objetivo:** Crear tablas SQL faltantes respetando patrones EDARSAHUB

---

## 1. TABLA COMPARATIVA DE DECISIONES

| # | Nombre Propuesto Original | Nombre Final Validado | Patrón/Módulo | Equivalente Existente | Decisión | Motivo |
|---|---------------------------|----------------------|---------------|----------------------|----------|--------|
| 1 | Notificaciones_Log | **Operativo_Notificaciones_Log** | Operativo_* | Ninguna | ✅ CREAR | No existe equivalente funcional |
| 2 | Justificaciones_Inventario | **Workflow_Justificaciones** | Workflow_* | Ninguna | ✅ CREAR | Extiende módulo Workflow existente |
| 3 | Decisiones_Auditoria | **Workflow_DecisionesAuditoria** | Workflow_* | Ninguna | ✅ CREAR | Asociada a Workflow_Inventarios |
| 4 | Historial_Asignaciones | **Operativo_HistorialAsignaciones** | Operativo_* | ActivoFijo_HistorialAsignaciones (vacía, otro módulo) | ✅ CREAR | Diferente estructura y propósito |
| 5 | Responsabilidad_Economica | **Operativo_ResponsabilidadEconomica** | Operativo_* | Ninguna | ✅ CREAR | Funcionalidad nueva |
| 6 | Cargos_Responsabilidad | **Operativo_CargosResponsabilidad** | Operativo_* | CavaSocios_Cargos (otro módulo) | ✅ CREAR | Diferente estructura y propósito |
| 7 | Historial_Cargos | **Operativo_HistorialCargos** | Operativo_* | Ninguna | ✅ CREAR | Funcionalidad nueva |
| 8 | Scheduler_Job_Logs | **Scheduler_BitacoraJobs** | Scheduler_* | ✅ Scheduler_BitacoraJobs (909 regs) | 🔄 REUTILIZAR | Ya existe y está en uso activo |
| 9 | Tareas_Operativas_Compras | **Operativo_TareasCompras** | Operativo_* | Ninguna (CRM_Tareas es otro módulo) | ✅ CREAR | Funcionalidad específica de fase2 |
| 10 | Auditoria_Compras_Bitacora | **Operativo_BitacoraCompras** | Operativo_* | Ninguna | ✅ CREAR | Log específico de automatización |
| 11 | Pedidos_Procesados_Automatizacion | **Operativo_PedidosProcesados** | Operativo_* | Scheduler_PedidosProcesados (otro uso) | ✅ CREAR | Diferente estructura y propósito |
| 12 | Auditorias_Programadas | **Operativo_AuditoriasProgramadas** | Operativo_* | Ninguna | ✅ CREAR | Funcionalidad nueva |
| 13 | Documentos_Generados | **Operativo_DocumentosGenerados** | Operativo_* | Ninguna | ✅ CREAR | Funcionalidad específica de reportes |

---

## 2. RESUMEN DE DECISIONES

| Decisión | Cantidad | Tablas |
|----------|----------|--------|
| ✅ CREAR | 12 | Todas excepto Scheduler_Job_Logs |
| 🔄 REUTILIZAR | 1 | Scheduler_BitacoraJobs |
| ❌ DESCARTAR | 0 | - |
| 🔧 ALTER TABLE | 0 | - |

---

## 3. PATRÓN DE NOMENCLATURA ADOPTADO

Se adopta el prefijo `Operativo_` para las nuevas tablas del módulo fase2_operativo, alineándose con:
- `Operaciones_Tablaje_*` (14 tablas existentes)
- Patrón de módulos: `Comercial_*`, `Compras_*`, `Finanzas_*`

Excepción: Tablas que extienden `Workflow_Inventarios` usan prefijo `Workflow_`.

---

## 4. DDL EJECUTADO

### 4.1 Operativo_Notificaciones_Log

```sql
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
END;
```

### 4.2 Workflow_Justificaciones

```sql
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
END;
```

### 4.3 Workflow_DecisionesAuditoria

```sql
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
END;
```

### 4.4 Operativo_HistorialAsignaciones

```sql
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
END;
```

### 4.5 Operativo_ResponsabilidadEconomica

```sql
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
END;
```

### 4.6 Operativo_CargosResponsabilidad

```sql
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
END;
```

### 4.7 Operativo_HistorialCargos

```sql
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
END;
```

### 4.8 Scheduler_BitacoraJobs - REUTILIZAR EXISTENTE

```sql
-- NO SE CREA - SE REUTILIZA Scheduler_BitacoraJobs existente (909 registros)
-- Estructura compatible:
--   ID, JobName, RunID, Accion, FechaAccion, ServerID, DetallesJSON, Exito, MensajeError
```

### 4.9 Operativo_TareasCompras

```sql
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
END;
```

### 4.10 Operativo_BitacoraCompras

```sql
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
END;
```

### 4.11 Operativo_PedidosProcesados

```sql
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
END;
```

### 4.12 Operativo_AuditoriasProgramadas

```sql
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
END;
```

### 4.13 Operativo_DocumentosGenerados

```sql
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
END;
```

---

## 5. TABLAS CREADAS

| # | Tabla | Estado |
|---|-------|--------|
| 1 | Operativo_Notificaciones_Log | ✅ CREADA |
| 2 | Workflow_Justificaciones | ✅ CREADA |
| 3 | Workflow_DecisionesAuditoria | ✅ CREADA |
| 4 | Operativo_HistorialAsignaciones | ✅ CREADA |
| 5 | Operativo_ResponsabilidadEconomica | ✅ CREADA |
| 6 | Operativo_CargosResponsabilidad | ✅ CREADA |
| 7 | Operativo_HistorialCargos | ✅ CREADA |
| 8 | Operativo_TareasCompras | ✅ CREADA |
| 9 | Operativo_BitacoraCompras | ✅ CREADA |
| 10 | Operativo_PedidosProcesados | ✅ CREADA |
| 11 | Operativo_AuditoriasProgramadas | ✅ CREADA |
| 12 | Operativo_DocumentosGenerados | ✅ CREADA |

---

## 6. TABLAS REUTILIZADAS

| Tabla Original | Tabla Reutilizada | Motivo |
|----------------|-------------------|--------|
| Scheduler_Job_Logs | Scheduler_BitacoraJobs | Estructura compatible, 909 registros existentes |

---

## 7. TABLAS DESCARTADAS

Ninguna.

---

## 8. ÍNDICES Y CONSTRAINTS CREADOS

| Tabla | Índices | Constraint UNIQUE |
|-------|---------|-------------------|
| Operativo_Notificaciones_Log | 5 | NotificacionID |
| Workflow_Justificaciones | 3 | JustificacionID |
| Workflow_DecisionesAuditoria | 2 | DecisionID |
| Operativo_HistorialAsignaciones | 3 | HistorialID |
| Operativo_ResponsabilidadEconomica | 4 | ResponsabilidadID |
| Operativo_CargosResponsabilidad | 4 | CargoID |
| Operativo_HistorialCargos | 2 | HistorialID |
| Operativo_TareasCompras | 3 | TareaID |
| Operativo_BitacoraCompras | 2 | BitacoraID |
| Operativo_PedidosProcesados | 2 | PedidoID |
| Operativo_AuditoriasProgramadas | 3 | AuditoriaID |
| Operativo_DocumentosGenerados | 3 | DocumentoID |

**Total:** 36 índices + 12 constraints UNIQUE

---

## 9. CONFIRMACIONES

| Validación | Estado |
|------------|--------|
| DDL es idempotente (IF OBJECT_ID...IS NULL) | ✅ Confirmado y verificado |
| No se crean tablas duplicadas | ✅ Confirmado |
| No se insertan datos productivos | ✅ Confirmado (0 registros en todas) |
| No se modifica código productivo | ✅ Confirmado |
| CERO MongoDB | ✅ Confirmado |
| CERO conexiones LIVE | ✅ Confirmado |
| Login funciona | ✅ Verificado (admin@inventario.com) |
| Script reejecutado sin error | ✅ Verificado (idempotente) |
| Health check /api/v2/health | ✅ Verificado (status: ok) |

---

## 10. MAPEO COLECCIÓN MONGODB → TABLA SQL FINAL

| Colección MongoDB | Tabla SQL EDARSAHUB |
|-------------------|---------------------|
| notificaciones_log | Operativo_Notificaciones_Log |
| justificaciones_inventario | Workflow_Justificaciones |
| decisiones_auditoria | Workflow_DecisionesAuditoria |
| historial_asignaciones | Operativo_HistorialAsignaciones |
| responsabilidades (inferido) | Operativo_ResponsabilidadEconomica |
| cargos_responsabilidad | Operativo_CargosResponsabilidad |
| historial_cargos (inferido) | Operativo_HistorialCargos |
| scheduler_job_logs | Scheduler_BitacoraJobs (EXISTENTE) |
| tareas_operativas_compras | Operativo_TareasCompras |
| auditoria_compras_bitacora | Operativo_BitacoraCompras |
| pedidos_procesados_automatizacion | Operativo_PedidosProcesados |
| auditorias_programadas (inferido) | Operativo_AuditoriasProgramadas |
| documentos_generados | Operativo_DocumentosGenerados |

---

## 11. RIESGOS RESIDUALES

| Riesgo | Mitigación |
|--------|------------|
| FK no creadas hacia Workflow_Inventarios | Decisión consciente: se mantendrán como soft-references para flexibilidad en migración gradual |
| Campos JSON sin validación de schema | Standard en EDARSAHUB; validación en capa de aplicación |
| Nombres de tablas nuevos vs código existente | FASE B-P0-C ajustará el mapeo en repositories |

---

## 12. RECOMENDACIÓN PARA FASE B-P0-C

1. Crear archivo `sql_tables_mapping.py` con mapeo MongoDB → SQL
2. Refactorizar `base_repository.py` para soportar dual-mode (MongoDB/SQL)
3. Migrar repositories uno a uno con toggle de feature flag
4. Mantener MongoDB activo hasta validación completa en SQL

---

## 13. SCRIPT CONSOLIDADO PARA EJECUCIÓN

El script DDL completo se encuentra en:
`/app/backend/scripts/ddl_fase2_operativo_tablas.sql`

---

**Documento generado automáticamente - FASE B-P0-B**
