# FASE B-P0-A: Diagnóstico Migración fase2_operativo MongoDB → SQL

**Fecha:** 25 Mayo 2026  
**Módulo:** `/app/backend/modules/fase2_operativo/`  
**Prefijo API:** `/api/v2/`  
**Arquitectura Destino:** EDARSAHUB SQL Server (CERO MongoDB)

---

## 1. RESUMEN EJECUTIVO

El módulo `fase2_operativo` constituye el **núcleo de la Gestión Operativa de Inventarios (Fase 2A)** del CRM EDARSA HUB. Actualmente opera con una arquitectura **híbrida no deseada**:

| Componente | Estado Actual | Estado Deseado |
|------------|--------------|----------------|
| `sql_repository.py` | Funciones SQL para Workflows/Tareas | ✅ Mantener |
| `db_utils.py` | Conexión MongoDB activa | ❌ Eliminar |
| Repositories (`/repositories/*.py`) | 100% MongoDB | ❌ Migrar a SQL |
| Services | 80% MongoDB, 20% SQL | ❌ Migrar a SQL |
| Routes | Llamadas directas a MongoDB | ❌ Migrar a SQL |

**Impacto crítico:** 13 tablas SQL faltan para reemplazar completamente MongoDB.

---

## 2. COLECCIONES MONGODB USADAS

### 2.1 Colecciones Detectadas (18 total)

| Colección MongoDB | Usos Detectados | Tabla SQL Equivalente | Estado SQL |
|-------------------|-----------------|----------------------|------------|
| `workflow_inventarios` | 6 | `Workflow_Inventarios` | ✅ EXISTE |
| `tareas_inventario` | 7 | `Tareas_Inventario` | ✅ EXISTE |
| `detalle_diferencias` | 1 | `Workflow_DetalleDiferencias` | ✅ EXISTE |
| `configuracion_operativa` | 3 | `Configuracion_Operativa` | ✅ EXISTE |
| `notificaciones_log` | 8 | `Notificaciones_Log` | ❌ FALTA |
| `users` | 8 | `Usuarios` (ya existe) | ✅ EXISTE |
| `tareas_operativas_compras` | 6 | `Tareas_Operativas_Compras` | ❌ FALTA |
| `documentos_generados` | 4 | `Documentos_Generados` | ❌ FALTA |
| `justificaciones_inventario` | 2 | `Justificaciones_Inventario` | ❌ FALTA |
| `inventarios_fisicos_procesados` | 2 | `Compras_Inventarios_Fisicos_Sync` | ✅ EXISTE |
| `decisiones_auditoria` | 1 | `Decisiones_Auditoria` | ❌ FALTA |
| `historial_asignaciones` | 1 | `Historial_Asignaciones` | ❌ FALTA |
| `scheduler_job_logs` | 1 | `Scheduler_Job_Logs` | ❌ FALTA |
| `pedidos_procesados_automatizacion` | 1 | `Pedidos_Procesados_Automatizacion` | ❌ FALTA |
| `auditoria_compras_bitacora` | 1 | `Auditoria_Compras_Bitacora` | ❌ FALTA |
| `server_sucursales_config` | 1 | `Sistema_ServidorSucursalesConfig` | ✅ EXISTE |
| `cargos_responsabilidad` | Inferred | `Cargos_Responsabilidad` | ❌ FALTA |
| `historial_cargos` | Inferred | `Historial_Cargos` | ❌ FALTA |

### 2.2 Tablas SQL Existentes vs Faltantes

**EXISTENTES (6):**
1. `Workflow_Inventarios`
2. `Tareas_Inventario`
3. `Workflow_DetalleDiferencias`
4. `Configuracion_Operativa`
5. `Config_Asignaciones`
6. `Inventarios_SinAsignar`

**FALTANTES (13):**
1. `Notificaciones_Log`
2. `Justificaciones_Inventario`
3. `Decisiones_Auditoria`
4. `Historial_Asignaciones`
5. `Responsabilidad_Economica`
6. `Cargos_Responsabilidad`
7. `Historial_Cargos`
8. `Scheduler_Job_Logs`
9. `Tareas_Operativas_Compras`
10. `Auditoria_Compras_Bitacora`
11. `Pedidos_Procesados_Automatizacion`
12. `Auditorias_Programadas`
13. `Documentos_Generados`

---

## 3. ARCHIVOS AFECTADOS

### 3.1 Archivos con Dependencia MongoDB DIRECTA

| Archivo | Líneas MongoDB | Prioridad Migración |
|---------|---------------|---------------------|
| `/modules/fase2_operativo/db_utils.py` | L8-32 (MongoClient) | 🔴 CRÍTICO |
| `/modules/fase2_operativo/repositories/base_repository.py` | L34-163 (self.collection) | 🔴 CRÍTICO |
| `/modules/fase2_operativo/repositories/workflow_repository.py` | L28-137 | 🔴 CRÍTICO |
| `/modules/fase2_operativo/repositories/tarea_repository.py` | L29-202 | 🔴 CRÍTICO |
| `/modules/fase2_operativo/repositories/responsabilidad_repository.py` | L28-221 | 🔴 CRÍTICO |
| `/modules/fase2_operativo/repositories/cargos_repository.py` | L31-331 | 🔴 CRÍTICO |
| `/modules/fase2_operativo/services/notification_service.py` | L36 (db.notificaciones_log) | 🟠 ALTO |
| `/modules/fase2_operativo/services/cargos_service.py` | L795-808 | 🟠 ALTO |
| `/modules/fase2_operativo/services/document_data_service.py` | L85 | 🟠 ALTO |
| `/modules/fase2_operativo/services/auditoria_programada_service.py` | L262 | 🟠 ALTO |
| `/modules/fase2_operativo/services/automatizacion_compras_service.py` | L77-1107 (Masivo) | 🔴 CRÍTICO |
| `/modules/fase2_operativo/routes/automatizacion_compras_routes.py` | L138-603 | 🔴 CRÍTICO |
| `/modules/fase2_operativo/routes/notificaciones_routes.py` | L65-152 | 🟠 ALTO |
| `/modules/fase2_operativo/routes/sla_routes.py` | L246 | 🟡 MEDIO |
| `/modules/fase2_operativo/scripts/init_collections_fase2a.py` | TODO | 🟢 ELIMINAR |
| `/modules/fase2_operativo/scripts/init_notificaciones.py` | TODO | 🟢 ELIMINAR |

### 3.2 Repositorios que Heredan de BaseRepository (MongoDB)

```
/repositories/
├── base_repository.py          # Clase base MongoDB → SQL
├── asignacion_repository.py    # db.server_sucursales_config
├── auditoria_repository.py     # db.decisiones_auditoria
├── auditoria_programada_repository.py
├── cargos_repository.py        # Masivo
├── configuracion_repository.py
├── detalle_diferencias_repository.py
├── historial_repository.py
├── historial_responsabilidad_repository.py
├── justificacion_repository.py
├── responsabilidad_repository.py
├── tarea_repository.py
└── workflow_repository.py
```

---

## 4. ENDPOINTS AFECTADOS

### 4.1 Endpoints con Dependencia MongoDB

| Endpoint | Archivo | Colecciones MongoDB |
|----------|---------|---------------------|
| `GET /api/v2/dashboard/resumen` | dashboard_routes.py | workflows, tareas |
| `GET /api/v2/dashboard/alertas` | dashboard_routes.py | alertas |
| `GET /api/v2/dashboard/kpis` | dashboard_routes.py | workflows, tareas |
| `GET /api/v2/workflows` | workflow_routes.py | workflow_inventarios |
| `GET /api/v2/tareas` | tarea_routes.py | tareas_inventario |
| `GET /api/v2/notificaciones/log` | notificaciones_routes.py | notificaciones_log |
| `POST /api/v2/notificaciones/verificar-vencidas` | notificaciones_routes.py | tareas, users |
| `GET /api/v2/responsabilidad/*` | responsabilidad_routes.py | responsabilidades |
| `GET /api/v2/cargos/*` | cargos_routes.py | cargos_responsabilidad |
| `GET /api/v2/automatizacion/tareas` | automatizacion_compras_routes.py | tareas_operativas_compras |
| `GET /api/v2/automatizacion/bitacora` | automatizacion_compras_routes.py | auditoria_compras_bitacora |
| `GET /api/v2/automatizacion/pedidos` | automatizacion_compras_routes.py | pedidos_procesados |
| `POST /api/v2/automatizacion/aprobar-gerencia` | automatizacion_compras_routes.py | users, collection |
| `POST /api/v2/automatizacion/aprobar-tesoreria` | automatizacion_compras_routes.py | users, collection |

---

## 5. PANTALLAS/TABS AFECTADOS

### 5.1 Frontend - Componentes

| Componente | Archivo | Endpoints Consumidos |
|------------|---------|---------------------|
| `OperativoDashboard` | `/components/fase2_operativo/OperativoDashboard.jsx` | dashboard/*, workflows, tareas |
| `KPICards` | `/components/fase2_operativo/KPICards.jsx` | dashboard/kpis |
| `AlertasBanner` | `/components/fase2_operativo/AlertasBanner.jsx` | dashboard/alertas |
| `WorkflowList` | `/components/fase2_operativo/WorkflowList.jsx` | workflows |
| `TareaList` | `/components/fase2_operativo/TareaList.jsx` | tareas |
| `ResponsabilidadCard` | `/components/fase2_operativo/ResponsabilidadCard.jsx` | responsabilidad/* |
| `ResponsabilidadPendientesPanel` | `/components/fase2_operativo/ResponsabilidadPendientesPanel.jsx` | responsabilidad/* |
| `ResponsabilidadAccionesModal` | `/components/fase2_operativo/ResponsabilidadAccionesModal.jsx` | responsabilidad/* |
| `SLACard` | `/components/fase2_operativo/SLACard.jsx` | sla/* |

### 5.2 Rutas de Acceso

| Ruta URL | Página | Tab |
|----------|--------|-----|
| `/reportes?tab=operativo` | `Reportes.js` | Dashboard Operativo |
| `/operativo` | Redirect → `/reportes?tab=operativo` | - |

### 5.3 API Service Frontend

- **Archivo:** `/frontend/src/services/operativoApi.js`
- **Base URL:** `${API_BASE}/api/v2`
- **Funciones:** 40+ funciones de API

---

## 6. DDL PROPUESTO PARA TABLAS FALTANTES

### 6.1 Notificaciones_Log

```sql
CREATE TABLE Notificaciones_Log (
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
    FechaEnvio DATETIME2 DEFAULT GETUTCDATE(),
    FechaLeido DATETIME2 NULL,
    Canal VARCHAR(50) DEFAULT 'EMAIL',
    ErrorMensaje NVARCHAR(MAX) NULL,
    MetadatosJSON NVARCHAR(MAX) NULL,
    CONSTRAINT UQ_Notificaciones_NotificacionID UNIQUE (NotificacionID)
);

CREATE INDEX IX_Notificaciones_TipoEvento ON Notificaciones_Log(TipoEvento);
CREATE INDEX IX_Notificaciones_WorkflowID ON Notificaciones_Log(WorkflowID);
CREATE INDEX IX_Notificaciones_TareaID ON Notificaciones_Log(TareaID);
CREATE INDEX IX_Notificaciones_FechaEnvio ON Notificaciones_Log(FechaEnvio DESC);
```

### 6.2 Justificaciones_Inventario

```sql
CREATE TABLE Justificaciones_Inventario (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    JustificacionID VARCHAR(50) NOT NULL,
    WorkflowID VARCHAR(50) NOT NULL,
    DiferenciaID VARCHAR(50) NULL,
    CodigoProducto VARCHAR(50) NULL,
    TipoJustificacion VARCHAR(50) NOT NULL,
    Descripcion NVARCHAR(MAX) NULL,
    CantidadJustificada DECIMAL(18,4) NULL,
    ValorJustificado DECIMAL(18,2) NULL,
    EvidenciaURL VARCHAR(500) NULL,
    UsuarioID VARCHAR(50) NOT NULL,
    UsuarioNombre VARCHAR(200) NULL,
    FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
    Estado VARCHAR(50) DEFAULT 'PENDIENTE',
    FechaRevision DATETIME2 NULL,
    RevisadoPorID VARCHAR(50) NULL,
    Comentarios NVARCHAR(MAX) NULL,
    CONSTRAINT UQ_Justificaciones_JustificacionID UNIQUE (JustificacionID),
    CONSTRAINT FK_Justificaciones_Workflow FOREIGN KEY (WorkflowID) REFERENCES Workflow_Inventarios(WorkflowID)
);

CREATE INDEX IX_Justificaciones_WorkflowID ON Justificaciones_Inventario(WorkflowID);
CREATE INDEX IX_Justificaciones_DiferenciaID ON Justificaciones_Inventario(DiferenciaID);
```

### 6.3 Decisiones_Auditoria

```sql
CREATE TABLE Decisiones_Auditoria (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    DecisionID VARCHAR(50) NOT NULL,
    WorkflowID VARCHAR(50) NOT NULL,
    TipoDecision VARCHAR(50) NOT NULL,
    Decision VARCHAR(50) NOT NULL,
    Comentario NVARCHAR(MAX) NULL,
    UsuarioID VARCHAR(50) NOT NULL,
    UsuarioNombre VARCHAR(200) NULL,
    FechaDecision DATETIME2 DEFAULT GETUTCDATE(),
    CicloAuditoria INT DEFAULT 1,
    AccionSiguiente VARCHAR(100) NULL,
    MetadatosJSON NVARCHAR(MAX) NULL,
    CONSTRAINT UQ_Decisiones_DecisionID UNIQUE (DecisionID)
);

CREATE INDEX IX_Decisiones_WorkflowID ON Decisiones_Auditoria(WorkflowID);
```

### 6.4 Responsabilidad_Economica

```sql
CREATE TABLE Responsabilidad_Economica (
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
    CONSTRAINT UQ_Responsabilidad_ResponsabilidadID UNIQUE (ResponsabilidadID)
);

CREATE INDEX IX_Responsabilidad_WorkflowID ON Responsabilidad_Economica(WorkflowID);
CREATE INDEX IX_Responsabilidad_Estado ON Responsabilidad_Economica(Estado);
CREATE INDEX IX_Responsabilidad_SucursalID ON Responsabilidad_Economica(SucursalID);
```

### 6.5 Cargos_Responsabilidad

```sql
CREATE TABLE Cargos_Responsabilidad (
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
    CONSTRAINT UQ_Cargos_CargoID UNIQUE (CargoID)
);

CREATE INDEX IX_Cargos_ResponsabilidadID ON Cargos_Responsabilidad(ResponsabilidadID);
CREATE INDEX IX_Cargos_WorkflowID ON Cargos_Responsabilidad(WorkflowID);
CREATE INDEX IX_Cargos_EstatusCargo ON Cargos_Responsabilidad(EstatusCargo);
CREATE INDEX IX_Cargos_FechaPropuesta ON Cargos_Responsabilidad(FechaPropuesta DESC);
```

### 6.6 Historial_Cargos

```sql
CREATE TABLE Historial_Cargos (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    HistorialID VARCHAR(50) NOT NULL,
    CargoID VARCHAR(50) NOT NULL,
    Accion VARCHAR(50) NOT NULL,
    UsuarioID VARCHAR(50) NOT NULL,
    UsuarioNombre VARCHAR(200) NULL,
    Fecha DATETIME2 DEFAULT GETUTCDATE(),
    Detalle NVARCHAR(MAX) NULL,
    EstadoAnterior VARCHAR(50) NULL,
    EstadoNuevo VARCHAR(50) NULL,
    CONSTRAINT UQ_HistorialCargos_HistorialID UNIQUE (HistorialID)
);

CREATE INDEX IX_HistorialCargos_CargoID ON Historial_Cargos(CargoID);
CREATE INDEX IX_HistorialCargos_Fecha ON Historial_Cargos(Fecha DESC);
```

### 6.7 Scheduler_Job_Logs

```sql
CREATE TABLE Scheduler_Job_Logs (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    LogID VARCHAR(50) NOT NULL,
    JobName VARCHAR(100) NOT NULL,
    JobType VARCHAR(50) NULL,
    EstadoEjecucion VARCHAR(50) DEFAULT 'INICIADO',
    FechaInicio DATETIME2 DEFAULT GETUTCDATE(),
    FechaFin DATETIME2 NULL,
    DuracionSegundos INT NULL,
    RegistrosProcesados INT DEFAULT 0,
    RegistrosExitosos INT DEFAULT 0,
    RegistrosFallidos INT DEFAULT 0,
    ErrorMensaje NVARCHAR(MAX) NULL,
    DetalleJSON NVARCHAR(MAX) NULL,
    CONSTRAINT UQ_SchedulerLogs_LogID UNIQUE (LogID)
);

CREATE INDEX IX_SchedulerLogs_JobName ON Scheduler_Job_Logs(JobName);
CREATE INDEX IX_SchedulerLogs_FechaInicio ON Scheduler_Job_Logs(FechaInicio DESC);
```

### 6.8 Tareas_Operativas_Compras

```sql
CREATE TABLE Tareas_Operativas_Compras (
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
    CONSTRAINT UQ_TareasCompras_TareaID UNIQUE (TareaID)
);

CREATE INDEX IX_TareasCompras_Estado ON Tareas_Operativas_Compras(Estado);
CREATE INDEX IX_TareasCompras_AutomatizacionID ON Tareas_Operativas_Compras(AutomatizacionID);
```

### 6.9 Auditoria_Compras_Bitacora

```sql
CREATE TABLE Auditoria_Compras_Bitacora (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    BitacoraID VARCHAR(50) NOT NULL,
    AutomatizacionID VARCHAR(50) NULL,
    Accion VARCHAR(50) NOT NULL,
    UsuarioID VARCHAR(50) NULL,
    UsuarioNombre VARCHAR(200) NULL,
    Fecha DATETIME2 DEFAULT GETUTCDATE(),
    Detalle NVARCHAR(MAX) NULL,
    EstadoAnterior VARCHAR(50) NULL,
    EstadoNuevo VARCHAR(50) NULL,
    MetadatosJSON NVARCHAR(MAX) NULL,
    CONSTRAINT UQ_BitacoraCompras_BitacoraID UNIQUE (BitacoraID)
);

CREATE INDEX IX_BitacoraCompras_AutomatizacionID ON Auditoria_Compras_Bitacora(AutomatizacionID);
CREATE INDEX IX_BitacoraCompras_Fecha ON Auditoria_Compras_Bitacora(Fecha DESC);
```

### 6.10 Pedidos_Procesados_Automatizacion

```sql
CREATE TABLE Pedidos_Procesados_Automatizacion (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    PedidoID VARCHAR(50) NOT NULL,
    AutomatizacionID VARCHAR(50) NOT NULL,
    ServerID VARCHAR(50) NULL,
    SucursalID VARCHAR(100) NULL,
    FolioInventario VARCHAR(100) NULL,
    FechaProcesamiento DATETIME2 DEFAULT GETUTCDATE(),
    Estado VARCHAR(50) DEFAULT 'PROCESADO',
    CantidadItems INT DEFAULT 0,
    MontoTotal DECIMAL(18,2) DEFAULT 0,
    DetalleJSON NVARCHAR(MAX) NULL,
    CONSTRAINT UQ_PedidosProc_PedidoID UNIQUE (PedidoID)
);

CREATE INDEX IX_PedidosProc_AutomatizacionID ON Pedidos_Procesados_Automatizacion(AutomatizacionID);
CREATE INDEX IX_PedidosProc_FechaProcesamiento ON Pedidos_Procesados_Automatizacion(FechaProcesamiento DESC);
```

### 6.11 Auditorias_Programadas

```sql
CREATE TABLE Auditorias_Programadas (
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
    CONSTRAINT UQ_AuditoriasProg_AuditoriaID UNIQUE (AuditoriaID)
);

CREATE INDEX IX_AuditoriasProg_ProximaEjecucion ON Auditorias_Programadas(ProximaEjecucion);
CREATE INDEX IX_AuditoriasProg_Estado ON Auditorias_Programadas(Estado);
```

### 6.12 Documentos_Generados

```sql
CREATE TABLE Documentos_Generados (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    DocumentoID VARCHAR(50) NOT NULL,
    WorkflowID VARCHAR(50) NULL,
    TipoDocumento VARCHAR(50) NOT NULL,
    NombreArchivo VARCHAR(500) NULL,
    URLDescarga VARCHAR(1000) NULL,
    Formato VARCHAR(20) DEFAULT 'PDF',
    TamanioBytes BIGINT NULL,
    UsuarioGeneradorID VARCHAR(50) NULL,
    FechaGeneracion DATETIME2 DEFAULT GETUTCDATE(),
    FechaExpiracion DATETIME2 NULL,
    Estado VARCHAR(50) DEFAULT 'GENERADO',
    MetadatosJSON NVARCHAR(MAX) NULL,
    CONSTRAINT UQ_Documentos_DocumentoID UNIQUE (DocumentoID)
);

CREATE INDEX IX_Documentos_WorkflowID ON Documentos_Generados(WorkflowID);
CREATE INDEX IX_Documentos_TipoDocumento ON Documentos_Generados(TipoDocumento);
CREATE INDEX IX_Documentos_FechaGeneracion ON Documentos_Generados(FechaGeneracion DESC);
```

### 6.13 Historial_Asignaciones

```sql
CREATE TABLE Historial_Asignaciones (
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
    FechaAsignacion DATETIME2 DEFAULT GETUTCDATE(),
    Motivo NVARCHAR(MAX) NULL,
    TipoAsignacion VARCHAR(50) DEFAULT 'MANUAL',
    CONSTRAINT UQ_HistorialAsig_HistorialID UNIQUE (HistorialID)
);

CREATE INDEX IX_HistorialAsig_TareaID ON Historial_Asignaciones(TareaID);
CREATE INDEX IX_HistorialAsig_FechaAsignacion ON Historial_Asignaciones(FechaAsignacion DESC);
```

---

## 7. PLAN DE MIGRACIÓN DE DATOS

### 7.1 Fases de Migración

| Fase | Tablas | Prioridad | Complejidad |
|------|--------|-----------|-------------|
| B-P0-B | DDL Creación 13 tablas | 🔴 P0 | Media |
| B-P0-C | Migrar `base_repository.py` a SQL | 🔴 P0 | Alta |
| B-P1-A | Migrar `workflow_repository.py` | 🔴 P0 | Alta |
| B-P1-B | Migrar `tarea_repository.py` | 🔴 P0 | Alta |
| B-P2-A | Migrar `notification_service.py` | 🟠 P1 | Media |
| B-P2-B | Migrar `automatizacion_compras_service.py` | 🟠 P1 | MUY Alta |
| B-P2-C | Migrar `cargos_service.py` | 🟠 P1 | Alta |
| B-P3-A | Migrar Routes (automatizacion_compras_routes.py) | 🟡 P2 | Media |
| B-P3-B | Migrar Routes (notificaciones_routes.py) | 🟡 P2 | Baja |
| B-P4 | Eliminar `db_utils.py` y scripts MongoDB | 🟢 P3 | Baja |
| B-P5 | Pruebas integrales + Cleanup | 🟢 P3 | Media |

### 7.2 Script de Migración de Datos (Conceptual)

```python
# Script para migrar datos de MongoDB a SQL (ejecutar en producción)
# NOTA: Solo referencia - NO ejecutar sin autorización

from pymongo import MongoClient
import pymssql

def migrar_coleccion(coleccion_mongo, tabla_sql, mapeo_campos):
    """
    Migra datos de una colección MongoDB a una tabla SQL.
    
    Args:
        coleccion_mongo: Nombre de la colección MongoDB
        tabla_sql: Nombre de la tabla SQL destino
        mapeo_campos: Dict {campo_mongo: campo_sql}
    """
    # 1. Leer todos los documentos de MongoDB
    # 2. Transformar según mapeo
    # 3. Insertar en SQL Server
    # 4. Validar conteos
    pass
```

---

## 8. PLAN DE CAMBIO DE CÓDIGO

### 8.1 Estrategia General

1. **No romper funcionalidad existente** durante migración
2. **Patrón Toggle**: Crear funciones SQL paralelas, switchear gradualmente
3. **sql_repository.py ya existe**: Extender con nuevas funciones
4. **Eliminar db_utils.py** solo al final, cuando 100% SQL

### 8.2 Orden de Cambios

```
1. Crear tablas SQL faltantes (DDL)
2. Extender sql_repository.py con funciones para todas las tablas
3. Crear sql_base_repository.py (clase base SQL equivalente)
4. Migrar repositories uno a uno
5. Migrar services (actualizar imports)
6. Migrar routes (actualizar get_database → sql)
7. Eliminar db_utils.py
8. Eliminar scripts init_collections_*.py
```

---

## 9. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Pérdida de datos durante migración | Media | 🔴 Crítico | Backup completo antes de migrar |
| Downtime en producción | Alta | 🟠 Alto | Migración gradual con toggles |
| Inconsistencia de datos | Media | 🟠 Alto | Scripts de validación post-migración |
| Regresiones en endpoints | Alta | 🟠 Alto | Pruebas exhaustivas por endpoint |
| Performance degradada en SQL | Baja | 🟡 Medio | Índices adecuados, monitoreo |
| Timeouts en migración masiva | Media | 🟡 Medio | Migración en lotes |

---

## 10. PRIORIDADES DE EJECUCIÓN

| # | Tarea | Prioridad | Dependencia |
|---|-------|-----------|-------------|
| 1 | Ejecutar DDL 13 tablas faltantes | 🔴 P0 | Ninguna |
| 2 | Migrar `base_repository.py` a SQL | 🔴 P0 | #1 |
| 3 | Migrar `workflow_repository.py` | 🔴 P0 | #2 |
| 4 | Migrar `tarea_repository.py` | 🔴 P0 | #2 |
| 5 | Migrar `responsabilidad_repository.py` | 🟠 P1 | #2 |
| 6 | Migrar `cargos_repository.py` | 🟠 P1 | #2 |
| 7 | Migrar `automatizacion_compras_service.py` | 🟠 P1 | #1, #2 |
| 8 | Migrar `notification_service.py` | 🟠 P1 | #1 |
| 9 | Migrar `automatizacion_compras_routes.py` | 🟡 P2 | #7 |
| 10 | Eliminar archivos MongoDB obsoletos | 🟢 P3 | Todos |

---

## 11. CONFIRMACIÓN DE NO MODIFICACIÓN DE CÓDIGO

✅ **CONFIRMADO:** Este reporte es diagnóstico pasivo.

- ❌ No se modificó código productivo
- ❌ No se ejecutó DDL
- ❌ No se migraron datos
- ❌ No se cambió frontend
- ❌ No se cambió backend
- ❌ No se usaron conexiones LIVE como reemplazo
- ❌ No se amplió MongoDB
- ❌ No se borraron colecciones
- ❌ No se hizo refactor transversal

---

## 12. CRITERIOS DE ACEPTACIÓN

| Criterio | Estado |
|----------|--------|
| Se identificó toda dependencia MongoDB de fase2_operativo | ✅ Completado |
| Se identificó qué pantallas/endpoints afecta | ✅ Completado |
| Se definió reemplazo SQL (DDL propuesto) | ✅ Completado |
| Se propuso plan de migración | ✅ Completado |
| No se usó conexión LIVE como parche | ✅ Confirmado |
| Se generó el reporte | ✅ Este documento |

---

## 13. PRÓXIMOS PASOS RECOMENDADOS

1. **Autorización del usuario** para proceder con FASE B-P0-B (Creación de DDL)
2. Ejecutar script DDL en EDARSAHUB (requiere credenciales de escritura)
3. Verificar creación de tablas
4. Continuar con FASE B-P0-C (Migración de base_repository.py)

---

**Documento generado automáticamente - FASE B-P0-A COMPLETADA**
