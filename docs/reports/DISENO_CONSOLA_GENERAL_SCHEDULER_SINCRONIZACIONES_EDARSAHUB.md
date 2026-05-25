# DISEÑO TÉCNICO: Consola General de Scheduler y Sincronizaciones EDARSAHUB

**Fecha:** 2026-05-25  
**Versión:** 1.0  
**Estado:** DISEÑO TÉCNICO - NO IMPLEMENTAR SIN AUTORIZACIÓN  
**Autor:** E1 Agent (Ingeniero Senior Fullstack + SQL Server)

---

## 1. RESUMEN EJECUTIVO

Este documento describe el diseño técnico completo de la **Consola Administrativa General del Scheduler de EDARSAHUB**, un componente central que permitirá administrar todos los jobs oficiales del sistema bajo control, permisos y auditoría completa.

La consola permitirá gestionar sincronizaciones de todos los módulos (Comercial, Finanzas, Compras, Inventarios, Costos, etc.) desde una interfaz unificada, con la configuración viviendo en EDARSAHUB SQL como fuente de verdad.

---

## 2. PROBLEMA ACTUAL

### Situación
- Los jobs están definidos en código Python con configuración hardcodeada
- No existe forma de modificar frecuencias, horarios o parámetros sin redeploy
- No hay visibilidad del estado de los jobs para usuarios administrativos
- No existe mecanismo oficial de re-sincronización histórica
- No hay auditoría de cambios en configuración de jobs
- Cada módulo tiene su propia forma de manejar syncs

### Consecuencias
- P0-B CIENFUEGOS: No se pueden recuperar días faltantes sin scripts manuales
- Operaciones dependen de desarrolladores para cambios simples
- Sin trazabilidad de quién cambió qué configuración
- Riesgo de ejecuciones no controladas

---

## 3. JUSTIFICACIÓN ARQUITECTÓNICA

### Principio: EDARSAHUB SQL es el Cerebro

La configuración operativa de los jobs debe vivir en EDARSAHUB SQL porque:

1. **Centralización**: Una sola fuente de verdad
2. **Operabilidad**: Cambios sin redeploy
3. **Auditoría**: Trazabilidad completa
4. **Consistencia**: Misma arquitectura que el resto del sistema
5. **Respaldo**: Incluido en backups de BD

### NO usar MongoDB para configuración de jobs
MongoDB solo debe usarse para locks técnicos temporales, NO para configuración de negocio.

---

## 4. OBJETIVO DE LA CONSOLA

Proveer una interfaz administrativa unificada para:

1. **Ver** todos los jobs programados del sistema
2. **Monitorear** estado y resultados de ejecuciones
3. **Configurar** parámetros operativos sin redeploy
4. **Ejecutar** jobs manualmente con control
5. **Re-sincronizar** períodos históricos
6. **Auditar** todos los cambios y ejecuciones

---

## 5. ALCANCE GENERAL

### Jobs Soportados (por módulo)

| Módulo | Jobs |
|--------|------|
| **Comercial** | ventas_cerradas, ventas_abiertas, ventas_por_hora, ventas_historicas |
| **Finanzas** | cortes_z, cuadres_z, ingresos, bancos |
| **Compras** | pedidos, recepciones, tracking |
| **Inventarios** | existencias, movimientos, conteos |
| **Costos** | margenes, alertas, evaluacion |
| **Productos** | catalogo, precios, recetas |
| **Proveedores** | catalogo, pedidos |
| **Tablajería** | produccion, mermas |
| **Catálogos** | empresas, sucursales, unidades |
| **Sistema** | limpieza, respaldos, health_check |

### Funcionalidades por Rol

| Funcionalidad | SUPERADMIN | SYNC_ADMIN | DATA_ADMIN | VIEWER |
|--------------|------------|------------|------------|--------|
| Ver jobs | ✅ | ✅ | ✅ | ✅ |
| Ver ejecuciones | ✅ | ✅ | ✅ | ✅ |
| Ver logs | ✅ | ✅ | ✅ | ❌ |
| Editar config | ✅ | ✅ | ❌ | ❌ |
| Activar/Desactivar | ✅ | ✅ | ❌ | ❌ |
| Ejecutar manual | ✅ | ✅ | ✅* | ❌ |
| Re-sincronizar | ✅ | ✅ | ❌ | ❌ |
| Dry run | ✅ | ✅ | ✅ | ❌ |

*Solo jobs de nivel BAJO/MEDIO

---

## 6. ARQUITECTURA FRONTEND

### Ubicación
`/app/frontend/src/pages/admin/SchedulerConsole.jsx`

### Estructura de Navegación

```
Administración
└── Scheduler / Sincronizaciones
    ├── Jobs Programados
    ├── Ejecuciones
    ├── Re-sincronización
    ├── Logs
    └── Configuración
```

### Tabs de la Consola

#### Tab 1: Jobs Programados
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SCHEDULER / SINCRONIZACIONES                                    [Refrescar] │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Jobs Programados] [Ejecuciones] [Re-sincronización] [Logs] [Config]        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Filtros: [Módulo ▼] [Estado ▼] [Nivel Riesgo ▼]              [Buscar...  ] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌─ Job ──────────────────────────────────────────────────────────────────┐ │
│ │ ● comercial_ventas_cerradas                              [ACTIVO] 🟢   │ │
│ │   Módulo: Comercial | Frecuencia: cada 15 min | Riesgo: MEDIO          │ │
│ │   Última ejecución: 2026-05-25 20:15 ✅ SUCCESS | Próxima: 20:30       │ │
│ │   Unidades: 130MID, CIENFUEGOS, ESTELAR, 130QRO, ORIGEN               │ │
│ │   [Editar] [Ejecutar Ahora] [Ver Historial] [Desactivar]              │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌─ Job ──────────────────────────────────────────────────────────────────┐ │
│ │ ● finanzas_cortes_z                                      [ACTIVO] 🟢   │ │
│ │   Módulo: Finanzas | Frecuencia: cada 30 min | Riesgo: MEDIO           │ │
│ │   Última ejecución: 2026-05-25 20:00 ✅ SUCCESS | Próxima: 20:30       │ │
│ │   [Editar] [Ejecutar Ahora] [Ver Historial] [Desactivar]              │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Tab 2: Ejecuciones
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ EJECUCIONES RECIENTES                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Filtros: [Job ▼] [Estado ▼] [Fecha desde] [Fecha hasta]     [Buscar...  ]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Fecha/Hora      │ Job                    │ Estado │ Duración │ Registros   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2026-05-25 20:15│ comercial_ventas_cerr..│ ✅     │ 12.3s    │ +5 ins      │
│ 2026-05-25 20:00│ finanzas_cortes_z      │ ✅     │ 8.1s     │ +3 ins      │
│ 2026-05-25 19:45│ comercial_ventas_cerr..│ ❌     │ 45.2s    │ Error       │
│   └─ Error: Timeout conectando a 130MID                      [Reintentar]  │
│ 2026-05-25 19:30│ comercial_ventas_cerr..│ ✅     │ 11.8s    │ +4 ins      │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Tab 3: Re-sincronización
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ RE-SINCRONIZACIÓN                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Tipo de Sincronización: [Comercial - Ventas Cerradas ▼]                  │
│                                                                             │
│   Unidad de Negocio:      [CIENFUEGOS ▼]                                   │
│                                                                             │
│   Servidor/Conexión:      6d053c22-523e... (Auto)                          │
│                                                                             │
│   Fecha Inicio:           [2026-05-19]                                     │
│                                                                             │
│   Fecha Fin:              [2026-05-20]                                     │
│                                                                             │
│   ⚠️ Rango: 2 días (Máximo permitido: 30 días)                             │
│                                                                             │
│   Motivo (obligatorio):   [Reconciliación P0-B días faltantes___________]  │
│                                                                             │
│   ☑️ Ejecutar como Dry Run (solo simulación)                               │
│                                                                             │
│   ┌─ Validación Previa ─────────────────────────────────────────────────┐  │
│   │ ✅ Conexión al servidor: ONLINE                                      │  │
│   │ ⚠️ Días existentes en destino: 0 de 2                                │  │
│   │ ✅ Sin conflictos detectados                                         │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   [Validar]  [Ejecutar Dry Run]  [Ejecutar Re-sincronización]              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Tab 4: Logs
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ LOGS DEL SCHEDULER                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Filtros: [Job ▼] [Nivel ▼] [Ejecución ID]                   [Buscar...  ]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2026-05-25 20:15:03 INFO  [comercial_ventas_cerradas] Iniciando sync...    │
│ 2026-05-25 20:15:04 INFO  [comercial_ventas_cerradas] Conectando 130MID... │
│ 2026-05-25 20:15:05 INFO  [comercial_ventas_cerradas] Procesando 3 días... │
│ 2026-05-25 20:15:12 INFO  [comercial_ventas_cerradas] Insertados: 5        │
│ 2026-05-25 20:15:12 INFO  [comercial_ventas_cerradas] Completado: SUCCESS  │
│                                                                             │
│ 2026-05-25 19:45:01 INFO  [comercial_ventas_cerradas] Iniciando sync...    │
│ 2026-05-25 19:45:02 WARN  [comercial_ventas_cerradas] Retry 1/3: 130MID... │
│ 2026-05-25 19:45:32 WARN  [comercial_ventas_cerradas] Retry 2/3: 130MID... │
│ 2026-05-25 19:46:02 ERROR [comercial_ventas_cerradas] Timeout: 130MID      │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Tab 5: Configuración
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CONFIGURACIÓN DEL SCHEDULER                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─ Configuración Global ──────────────────────────────────────────────┐  │
│   │ Timezone por defecto:        [America/Mexico_City ▼]                 │  │
│   │ Timeout global (seg):        [300]                                   │  │
│   │ Max reintentos por defecto:  [3]                                     │  │
│   │ Delay entre reintentos (s):  [30]                                    │  │
│   │ Evitar solapamiento:         [✓] Activado                           │  │
│   │ Notificar errores a:         [admin@edarsa.com]                      │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ┌─ Límites de Seguridad ──────────────────────────────────────────────┐  │
│   │ Rango máximo re-sync (días): [30]                                    │  │
│   │ Ejecuciones manuales/hora:   [10]                                    │  │
│   │ Require dry_run para ALTO:   [✓] Activado                           │  │
│   │ Require motivo siempre:      [✓] Activado                           │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   [Guardar Configuración]                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Componentes React Sugeridos

```
/app/frontend/src/pages/admin/
├── SchedulerConsole.jsx              # Página principal
├── components/
│   ├── JobsList.jsx                  # Lista de jobs
│   ├── JobCard.jsx                   # Card individual de job
│   ├── JobEditModal.jsx              # Modal de edición
│   ├── ExecutionsList.jsx            # Lista de ejecuciones
│   ├── ExecutionDetail.jsx           # Detalle de ejecución
│   ├── ResyncForm.jsx                # Formulario de re-sync
│   ├── LogsViewer.jsx                # Visor de logs
│   ├── SchedulerConfig.jsx           # Configuración global
│   └── AuditTrail.jsx                # Trail de auditoría
```

---

## 7. ARQUITECTURA BACKEND

### Estructura de Archivos

```
/app/backend/api/
├── admin_scheduler.py                # Router principal
├── admin_scheduler_jobs.py           # CRUD de jobs
├── admin_scheduler_executions.py     # Ejecuciones
├── admin_scheduler_resync.py         # Re-sincronización
└── admin_scheduler_audit.py          # Auditoría

/app/backend/core/scheduler/
├── registry.py                       # JobRegistry desde SQL
├── executor.py                       # Ejecutor de jobs
├── resync_manager.py                 # Manager de re-syncs
└── config_loader.py                  # Carga config desde SQL
```

### Endpoints API

#### Jobs
```
GET    /api/admin/scheduler/jobs                    # Listar jobs
GET    /api/admin/scheduler/jobs/{job_id}           # Detalle de job
PUT    /api/admin/scheduler/jobs/{job_id}           # Actualizar job
POST   /api/admin/scheduler/jobs/{job_id}/enable    # Activar job
POST   /api/admin/scheduler/jobs/{job_id}/disable   # Desactivar job
POST   /api/admin/scheduler/jobs/{job_id}/run-now   # Ejecutar ahora
```

#### Ejecuciones
```
GET    /api/admin/scheduler/executions              # Listar ejecuciones
GET    /api/admin/scheduler/executions/{id}         # Detalle ejecución
POST   /api/admin/scheduler/executions/{id}/retry   # Reintentar
POST   /api/admin/scheduler/executions/{id}/cancel  # Cancelar
```

#### Re-sincronización
```
POST   /api/admin/scheduler/resync/validate         # Validar re-sync
POST   /api/admin/scheduler/resync/execute          # Ejecutar re-sync
GET    /api/admin/scheduler/resync/history          # Historial de re-syncs
```

#### Logs y Auditoría
```
GET    /api/admin/scheduler/logs                    # Logs de ejecuciones
GET    /api/admin/scheduler/audit                   # Trail de auditoría
```

### Request/Response Schemas

```python
# POST /api/admin/scheduler/resync/execute
class ResyncRequest(BaseModel):
    tipo_sync: str                    # "comercial_ventas_cerradas"
    unidad_negocio_id: str            # "CIENFUEGOS"
    empresa_id: Optional[str] = None
    servidor_id: Optional[str] = None # Auto desde unidad si no se especifica
    fecha_inicio: date
    fecha_fin: date
    motivo: str                       # Obligatorio
    dry_run: bool = True              # Por defecto solo simula
    forzar: bool = False              # Para sobrescribir existentes

class ResyncResponse(BaseModel):
    success: bool
    ejecucion_id: str
    sync_run_id: str
    modo: str                         # "DRY_RUN" o "REAL"
    unidad_negocio_id: str
    fecha_inicio: str
    fecha_fin: str
    validacion_previa: dict
    resultado: Optional[dict] = None
    validacion_posterior: Optional[dict] = None
    error_message: Optional[str] = None
```

---

## 8. INTEGRACIÓN CON SCHEDULER EXISTENTE

### Comportamiento Actual
```python
# core/scheduler/jobs/sync_comercial_v2_job.py
SYNC_INCREMENTAL_DAYS = int(os.environ.get("SYNC_COMERCIAL_V2_DAYS", "3"))
```

### Comportamiento Nuevo
```python
# core/scheduler/config_loader.py
def get_job_config(job_codigo: str) -> JobConfig:
    """
    Obtiene configuración del job desde EDARSAHUB SQL.
    Falls back a valores por defecto si no existe.
    """
    query = f"""
    SELECT * FROM Sistema_Scheduler_Jobs
    WHERE Codigo = '{job_codigo}' AND Activo = 1
    """
    result = execute_edarsahub_query(query)
    if result:
        return JobConfig.from_db_row(result[0])
    return JobConfig.get_defaults(job_codigo)
```

### Flujo de Ejecución Actualizado

```
1. Scheduler trigger (cron/intervalo)
   │
2. JobRegistry.get_job_config(job_codigo)
   │ └─ Lee de Sistema_Scheduler_Jobs en EDARSAHUB SQL
   │
3. Verificar si job está Activo
   │
4. Verificar horario permitido (HoraInicioPermitida, HoraFinPermitida)
   │
5. Verificar lock de concurrencia
   │
6. Crear registro en Sistema_Scheduler_Ejecuciones (Estado='INICIADO')
   │
7. Ejecutar handler del job con parámetros de config
   │
8. Actualizar Sistema_Scheduler_Ejecuciones con resultado
   │
9. Actualizar Sistema_Scheduler_Jobs (UltimaEjecucionFecha, etc.)
   │
10. Registrar logs en Sistema_Scheduler_EjecucionesLog
```

---

## 9. MODELO SQL PROPUESTO

### Verificación de Tablas Existentes

Antes de crear, verificar si existen equivalentes:
```sql
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE '%Scheduler%' OR TABLE_NAME LIKE '%Job%' OR TABLE_NAME LIKE '%Sync%Config%'
```

### Tabla: Sistema_Scheduler_Jobs

```sql
CREATE TABLE Sistema_Scheduler_Jobs (
    -- Identificación
    JobID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Codigo VARCHAR(100) NOT NULL UNIQUE,          -- 'comercial_ventas_cerradas'
    Nombre NVARCHAR(200) NOT NULL,                -- 'Sincronización Ventas Cerradas'
    Modulo VARCHAR(50) NOT NULL,                  -- 'Comercial'
    Descripcion NVARCHAR(500),
    
    -- Handler
    Handler VARCHAR(200) NOT NULL,                -- 'sync_comercial_v2_job.execute_sync_comercial_v2'
    TipoJob VARCHAR(20) NOT NULL DEFAULT 'SYNC',  -- 'SYNC', 'PROCESS', 'REPORT', 'CLEANUP'
    
    -- Estado
    Activo BIT NOT NULL DEFAULT 1,
    
    -- Frecuencia
    FrecuenciaTipo VARCHAR(20) NOT NULL,          -- 'INTERVALO', 'CRON', 'MANUAL'
    IntervaloMinutos INT,                         -- 15 (si FrecuenciaTipo='INTERVALO')
    CronExpression VARCHAR(100),                  -- '*/15 * * * *' (si FrecuenciaTipo='CRON')
    
    -- Horario permitido
    HoraInicioPermitida TIME,                     -- NULL = sin restricción
    HoraFinPermitida TIME,
    Timezone VARCHAR(50) DEFAULT 'America/Mexico_City',
    
    -- Permisos
    PermiteEjecucionManual BIT DEFAULT 1,
    PermiteResync BIT DEFAULT 1,
    PermiteDryRun BIT DEFAULT 1,
    
    -- Requerimientos
    RequiereUnidad BIT DEFAULT 0,
    RequiereEmpresa BIT DEFAULT 0,
    RequiereServidor BIT DEFAULT 0,
    RequiereRangoFechas BIT DEFAULT 1,
    RangoMaximoDias INT DEFAULT 30,
    
    -- Riesgo y permisos de administración
    NivelRiesgo VARCHAR(20) DEFAULT 'MEDIO',      -- 'BAJO', 'MEDIO', 'ALTO', 'CRITICO'
    PermisoAdministracion VARCHAR(50),            -- 'SYNC_ADMIN' o NULL para SUPERADMIN only
    PermisoEjecucionManual VARCHAR(50),           -- 'DATA_ADMIN'
    
    -- Configuración de ejecución
    TimeoutSegundos INT DEFAULT 300,
    MaxRetries INT DEFAULT 3,
    RetryDelaySegundos INT DEFAULT 30,
    ConcurrencyKey VARCHAR(100),                  -- Para evitar solapamiento
    EvitarSolapamiento BIT DEFAULT 1,
    
    -- Estado de ejecución
    UltimaEjecucionID UNIQUEIDENTIFIER,
    UltimaEjecucionFecha DATETIME2,
    UltimaEjecucionEstado VARCHAR(20),            -- 'SUCCESS', 'FAILED', 'RUNNING'
    ProximaEjecucionFecha DATETIME2,
    
    -- Parámetros adicionales (JSON)
    ParametrosDefault NVARCHAR(MAX),              -- JSON con parámetros por defecto
    
    -- Auditoría
    FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
    UsuarioCreacion VARCHAR(100),
    FechaModificacion DATETIME2,
    UsuarioModificacion VARCHAR(100),
    
    -- Índices
    INDEX IX_Jobs_Modulo (Modulo),
    INDEX IX_Jobs_Activo (Activo),
    INDEX IX_Jobs_ProximaEjecucion (ProximaEjecucionFecha)
);
```

### Tabla: Sistema_Scheduler_JobUnidades

```sql
CREATE TABLE Sistema_Scheduler_JobUnidades (
    ID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    JobID UNIQUEIDENTIFIER NOT NULL REFERENCES Sistema_Scheduler_Jobs(JobID),
    UnidadNegocioID VARCHAR(50) NOT NULL,
    Activo BIT DEFAULT 1,
    Orden INT DEFAULT 0,
    ParametrosEspecificos NVARCHAR(MAX),          -- JSON override por unidad
    
    UNIQUE (JobID, UnidadNegocioID)
);
```

### Tabla: Sistema_Scheduler_Ejecuciones

```sql
CREATE TABLE Sistema_Scheduler_Ejecuciones (
    -- Identificación
    EjecucionID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    JobID UNIQUEIDENTIFIER NOT NULL REFERENCES Sistema_Scheduler_Jobs(JobID),
    SyncRunID VARCHAR(100) NOT NULL,              -- 'INCR-20260525-201500-xxxx' o 'BACKFILL-...'
    
    -- Estado
    Estado VARCHAR(20) NOT NULL,                  -- 'PENDIENTE', 'INICIADO', 'SUCCESS', 'FAILED', 'CANCELADO'
    
    -- Modo
    ModoEjecucion VARCHAR(20) NOT NULL,           -- 'AUTOMATICO', 'MANUAL', 'RESYNC', 'RETRY'
    DryRun BIT DEFAULT 0,
    
    -- Fechas
    FechaSolicitud DATETIME2 DEFAULT GETUTCDATE(),
    FechaInicio DATETIME2,
    FechaFin DATETIME2,
    FechaFinEjecucion DATETIME2,
    
    -- Solicitante
    SolicitadoPorUsuarioID VARCHAR(100),
    SolicitadoPorUsuarioEmail VARCHAR(200),
    Motivo NVARCHAR(500),
    
    -- Alcance
    UnidadNegocioID VARCHAR(50),                  -- NULL = todas
    EmpresaID VARCHAR(50),
    ServidorConexionID UNIQUEIDENTIFIER,
    FechaInicioRango DATE,
    FechaFinRango DATE,
    
    -- Parámetros
    ParametrosJSON NVARCHAR(MAX),
    
    -- Resultados
    RegistrosDetectados INT DEFAULT 0,
    RegistrosInsertados INT DEFAULT 0,
    RegistrosActualizados INT DEFAULT 0,
    RegistrosOmitidos INT DEFAULT 0,
    RegistrosError INT DEFAULT 0,
    
    -- Resultado detallado
    ResultadoJSON NVARCHAR(MAX),
    
    -- Errores
    ErrorCodigo VARCHAR(50),
    ErrorMensaje NVARCHAR(500),
    ErrorDetalle NVARCHAR(MAX),
    
    -- Métricas
    DuracionMS INT,
    
    -- Índices
    INDEX IX_Ejecuciones_JobID (JobID),
    INDEX IX_Ejecuciones_Estado (Estado),
    INDEX IX_Ejecuciones_Fecha (FechaSolicitud DESC),
    INDEX IX_Ejecuciones_SyncRunID (SyncRunID)
);
```

### Tabla: Sistema_Scheduler_EjecucionesLog

```sql
CREATE TABLE Sistema_Scheduler_EjecucionesLog (
    LogID BIGINT IDENTITY(1,1) PRIMARY KEY,
    EjecucionID UNIQUEIDENTIFIER NOT NULL REFERENCES Sistema_Scheduler_Ejecuciones(EjecucionID),
    Timestamp DATETIME2 DEFAULT GETUTCDATE(),
    Nivel VARCHAR(10) NOT NULL,                   -- 'DEBUG', 'INFO', 'WARN', 'ERROR'
    Mensaje NVARCHAR(MAX),
    Contexto NVARCHAR(MAX),                       -- JSON con datos adicionales
    
    INDEX IX_Log_Ejecucion (EjecucionID),
    INDEX IX_Log_Timestamp (Timestamp DESC)
);
```

### Tabla: Sistema_Scheduler_CambiosAuditoria

```sql
CREATE TABLE Sistema_Scheduler_CambiosAuditoria (
    AuditoriaID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    JobID UNIQUEIDENTIFIER REFERENCES Sistema_Scheduler_Jobs(JobID),
    EjecucionID UNIQUEIDENTIFIER REFERENCES Sistema_Scheduler_Ejecuciones(EjecucionID),
    
    -- Usuario
    UsuarioID VARCHAR(100) NOT NULL,
    UsuarioEmail VARCHAR(200),
    
    -- Cambio
    TipoAccion VARCHAR(50) NOT NULL,              -- 'CONFIG_UPDATE', 'ENABLE', 'DISABLE', 'MANUAL_RUN', 'RESYNC'
    FechaCambio DATETIME2 DEFAULT GETUTCDATE(),
    
    -- Detalle del cambio
    CampoModificado VARCHAR(100),
    ValorAnterior NVARCHAR(MAX),
    ValorNuevo NVARCHAR(MAX),
    Motivo NVARCHAR(500),
    
    -- Contexto
    IPOrigen VARCHAR(50),
    UserAgent NVARCHAR(500),
    
    INDEX IX_Auditoria_JobID (JobID),
    INDEX IX_Auditoria_Fecha (FechaCambio DESC),
    INDEX IX_Auditoria_Usuario (UsuarioID)
);
```

### Tabla: Sistema_Sync_Tipos

```sql
CREATE TABLE Sistema_Sync_Tipos (
    TipoSyncID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Codigo VARCHAR(100) NOT NULL UNIQUE,          -- 'comercial_ventas_cerradas'
    Nombre NVARCHAR(200) NOT NULL,
    Modulo VARCHAR(50) NOT NULL,
    Descripcion NVARCHAR(500),
    
    -- Handler de sync
    SyncHandler VARCHAR(200) NOT NULL,            -- 'sync_comercial_edarsahub.sync_softrestaurant_ventas_cerradas'
    
    -- Tablas destino
    TablaDestinoPrincipal VARCHAR(100),           -- 'Comercial_KPIs_Diarios_v2'
    TablasDestinoSecundarias NVARCHAR(MAX),       -- JSON array
    TablaLog VARCHAR(100),                        -- 'Comercial_SyncLog_v2'
    
    -- Sistemas origen soportados
    SistemasOrigen NVARCHAR(200),                 -- 'SOFTRESTAURANT,MPRO'
    
    -- Configuración
    PermiteResync BIT DEFAULT 1,
    RequiereUnidad BIT DEFAULT 1,
    RequiereRangoFechas BIT DEFAULT 1,
    RangoMaximoDias INT DEFAULT 30,
    
    -- Validaciones
    ValidarNoDuplicados BIT DEFAULT 1,
    UsaUpsert BIT DEFAULT 1,
    
    -- KPIs
    SeparaPropinas BIT DEFAULT 1,                 -- Para tipos de venta
    CampoVentaSinPropina VARCHAR(100),            -- 'ventas_sin_propina'
    
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT GETUTCDATE()
);
```

---

## 10. PERMISOS Y ROLES

### Matriz de Permisos

| Acción | Permiso Requerido |
|--------|-------------------|
| Ver jobs | `SCHEDULER_VIEW` |
| Ver ejecuciones | `SCHEDULER_VIEW` |
| Ver logs | `SCHEDULER_LOGS` |
| Editar configuración | `SCHEDULER_CONFIG` |
| Activar/Desactivar jobs | `SCHEDULER_CONFIG` |
| Ejecutar manual (BAJO/MEDIO) | `SCHEDULER_EXECUTE` |
| Ejecutar manual (ALTO/CRITICO) | `SCHEDULER_EXECUTE_HIGH` |
| Re-sincronizar | `SCHEDULER_RESYNC` |
| Configuración global | `SCHEDULER_ADMIN` |

### Roles Predefinidos

```sql
-- SUPERADMIN: Todos los permisos
-- SYNC_ADMIN: SCHEDULER_VIEW, SCHEDULER_LOGS, SCHEDULER_CONFIG, SCHEDULER_EXECUTE, SCHEDULER_EXECUTE_HIGH, SCHEDULER_RESYNC
-- DATA_ADMIN: SCHEDULER_VIEW, SCHEDULER_LOGS, SCHEDULER_EXECUTE
-- VIEWER: SCHEDULER_VIEW
```

---

## 11. AUDITORÍA

### Eventos Auditados

| Evento | Datos Registrados |
|--------|-------------------|
| Cambio de configuración | Campo, valor anterior, valor nuevo, motivo |
| Activar/Desactivar job | Estado anterior, estado nuevo, motivo |
| Ejecución manual | Parámetros, usuario, motivo |
| Re-sincronización | Tipo, unidad, rango, motivo, resultado |
| Cambio de permisos | Permiso, valor anterior, valor nuevo |

### Retención

- Ejecuciones: 90 días detalle, resumen indefinido
- Logs: 30 días
- Auditoría de cambios: Indefinido

---

## 12. EDICIÓN DE JOBS

### Campos Editables

| Campo | Editable | Restricciones |
|-------|----------|---------------|
| Activo | ✅ | Requiere motivo |
| FrecuenciaTipo | ✅ | Admin solo |
| IntervaloMinutos | ✅ | Mínimo 5 |
| CronExpression | ✅ | Validar formato |
| HoraInicioPermitida | ✅ | - |
| HoraFinPermitida | ✅ | - |
| TimeoutSegundos | ✅ | 30-3600 |
| MaxRetries | ✅ | 0-10 |
| RangoMaximoDias | ✅ | 1-365 |
| ParametrosDefault | ✅ | JSON válido |

### Campos NO Editables

| Campo | Motivo |
|-------|--------|
| Codigo | Identificador único |
| Handler | Requiere deploy |
| TipoJob | Definido en código |
| NivelRiesgo | Definido por arquitectura |

---

## 13. RE-SINCRONIZACIÓN

### Flujo de Re-sincronización

```
1. Usuario selecciona tipo de sync, unidad, rango
   │
2. POST /api/admin/scheduler/resync/validate
   │ ├─ Validar permisos
   │ ├─ Validar rango no excede máximo
   │ ├─ Validar conectividad al servidor origen
   │ ├─ Contar registros existentes en destino
   │ └─ Retornar resumen de validación
   │
3. Usuario confirma (con motivo obligatorio)
   │
4. POST /api/admin/scheduler/resync/execute
   │ ├─ Crear registro en Sistema_Scheduler_Ejecuciones
   │ ├─ Si dry_run=true: simular sin modificar
   │ ├─ Si dry_run=false: ejecutar sync real
   │ ├─ Actualizar registro con resultado
   │ ├─ Registrar auditoría
   │ └─ Retornar resultado con validación posterior
```

### Tipos de Re-sync Soportados

| Tipo | Handler | Tabla Destino |
|------|---------|---------------|
| comercial_ventas_cerradas | sync_softrestaurant_ventas_cerradas | Comercial_KPIs_Diarios_v2 |
| comercial_ventas_abiertas | sync_softrestaurant_ventas_abiertas | Comercial_Ventas_Dia_Abiertas_v2 |
| finanzas_cortes_z | sync_cortes_z | Finanzas_CortesCaja |
| finanzas_cuadres_z | sync_cuadres_z | Finanzas_CuadresZ |

---

## 14. DRY RUN

### Comportamiento

Cuando `dry_run=true`:
1. Se ejecuta toda la lógica de validación
2. Se conecta al servidor origen
3. Se extraen los datos
4. Se calculan los registros que se insertarían/actualizarían
5. **NO se ejecuta INSERT/UPDATE en destino**
6. Se retorna resumen de lo que se habría hecho

### Response de Dry Run

```json
{
  "success": true,
  "modo": "DRY_RUN",
  "registros_que_se_insertarian": 2,
  "registros_que_se_actualizarian": 0,
  "detalle": [
    {
      "fecha": "2026-05-19",
      "accion": "INSERT",
      "ventas_total": 125430.50,
      "ventas_sin_propina": 118750.00,
      "propinas": 6680.50,
      "tickets": 42
    },
    {
      "fecha": "2026-05-20",
      "accion": "INSERT",
      "ventas_total": 98320.00,
      "ventas_sin_propina": 92100.00,
      "propinas": 6220.00,
      "tickets": 38
    }
  ]
}
```

---

## 15. EJECUCIÓN MANUAL

### Restricciones por Nivel de Riesgo

| Nivel | Requiere Motivo | Requiere Dry Run | Requiere Confirmación |
|-------|-----------------|------------------|----------------------|
| BAJO | ❌ | ❌ | ❌ |
| MEDIO | ✅ | ❌ | ❌ |
| ALTO | ✅ | ✅ | ✅ |
| CRITICO | ✅ | ✅ | ✅ + Doble auth* |

*Doble autorización: pendiente definición

---

## 16. CONTROL DE CONCURRENCIA

### Mecanismo

```python
def acquire_job_lock(job_codigo: str, execution_id: str) -> bool:
    """
    Intenta adquirir lock para el job.
    Usa ConcurrencyKey de la configuración del job.
    """
    query = f"""
    UPDATE Sistema_Scheduler_Jobs
    SET UltimaEjecucionID = '{execution_id}',
        UltimaEjecucionEstado = 'RUNNING'
    WHERE Codigo = '{job_codigo}'
      AND (UltimaEjecucionEstado IS NULL 
           OR UltimaEjecucionEstado NOT IN ('RUNNING', 'PENDIENTE')
           OR DATEDIFF(MINUTE, UltimaEjecucionFecha, GETUTCDATE()) > TimeoutSegundos/60)
    """
    # Si rows_affected = 1, se obtuvo el lock
```

### Evitar Solapamiento

Si `EvitarSolapamiento = 1`:
- No se permite iniciar nueva ejecución si hay una en curso
- Se puede forzar si la ejecución anterior excedió timeout

---

## 17. MANEJO DE ERRORES

### Códigos de Error

| Código | Descripción |
|--------|-------------|
| CONN_TIMEOUT | Timeout conectando al servidor origen |
| CONN_AUTH | Error de autenticación |
| CONN_NETWORK | Error de red |
| QUERY_EMPTY | Query retornó vacío |
| QUERY_ERROR | Error ejecutando query |
| DEST_ERROR | Error escribiendo en destino |
| LOCK_FAILED | No se pudo obtener lock |
| VALIDATION_FAILED | Validación previa falló |
| TIMEOUT | Ejecución excedió timeout |
| CANCELLED | Cancelado por usuario |

### Reintentos Automáticos

Para errores `CONN_*`:
1. Esperar `RetryDelaySegundos`
2. Reintentar hasta `MaxRetries` veces
3. Si todos fallan, marcar como FAILED

---

## 18. CASO INMEDIATO: CIENFUEGOS 2026-05-19 y 2026-05-20

### Configuración en Sistema_Scheduler_Jobs

```sql
INSERT INTO Sistema_Scheduler_Jobs (
    Codigo, Nombre, Modulo, Handler, TipoJob,
    Activo, FrecuenciaTipo, IntervaloMinutos,
    PermiteEjecucionManual, PermiteResync, PermiteDryRun,
    RequiereUnidad, RequiereRangoFechas, RangoMaximoDias,
    NivelRiesgo, TimeoutSegundos, MaxRetries
) VALUES (
    'comercial_ventas_cerradas',
    'Sincronización Ventas Cerradas',
    'Comercial',
    'modules.comercial_v2.sync_comercial_edarsahub.sync_softrestaurant_ventas_cerradas',
    'SYNC',
    1, 'INTERVALO', 15,
    1, 1, 1,
    1, 1, 30,
    'MEDIO', 300, 3
);
```

### Request de Re-sincronización

```json
POST /api/admin/scheduler/resync/execute
{
    "tipo_sync": "comercial_ventas_cerradas",
    "unidad_negocio_id": "CIENFUEGOS",
    "fecha_inicio": "2026-05-19",
    "fecha_fin": "2026-05-20",
    "motivo": "Reconciliación P0-B días faltantes Tablero Ejecutivo Mayo 2026",
    "dry_run": true
}
```

### Validaciones Esperadas

1. ✅ Conexión a servercienfuegos.ddns.net:6669 desde EDARSAHUB
2. ✅ Credenciales desde Servidores_Conexiones (CFLectura)
3. ✅ Días 19 y 20 no existen en Comercial_KPIs_Diarios_v2
4. ✅ UPSERT idempotente
5. ✅ Venta KPI sin propinas (campo ventas_sin_propina)
6. ✅ sync_run_id = 'RESYNC-CIENFUEGOS-20260519-20260520-xxxx'
7. ✅ Log en Sistema_Scheduler_Ejecuciones
8. ✅ Log en Comercial_SyncLog_v2
9. ✅ Auditoría en Sistema_Scheduler_CambiosAuditoria

### Resultado Esperado Post-Ejecución

```sql
-- CIENFUEGOS debería tener 24 días en mayo
SELECT COUNT(*) as dias_mayo
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = 'CIENFUEGOS'
  AND fecha_operacion BETWEEN '2026-05-01' AND '2026-05-25'
  AND activo = 1;
-- Antes: 22, Después: 24
```

---

## 19. PLAN DE IMPLEMENTACIÓN POR FASES

### Fase 1: Modelo de Datos (1-2 días)
- [ ] Crear tablas Sistema_Scheduler_* en EDARSAHUB
- [ ] Insertar datos iniciales de jobs existentes
- [ ] Migrar configuración de variables de entorno a SQL

### Fase 2: Backend - API Base (2-3 días)
- [ ] Crear endpoints de lectura (GET jobs, executions, logs)
- [ ] Integrar JobRegistry con SQL
- [ ] Crear endpoint de validación de re-sync

### Fase 3: Backend - Ejecución (2-3 días)
- [ ] Crear endpoint de ejecución manual
- [ ] Crear endpoint de re-sincronización
- [ ] Implementar dry_run
- [ ] Implementar auditoría

### Fase 4: Frontend - Consola (3-4 días)
- [ ] Crear página SchedulerConsole
- [ ] Implementar tabs de Jobs y Ejecuciones
- [ ] Implementar formulario de Re-sincronización
- [ ] Implementar visor de logs

### Fase 5: Integración y Testing (2-3 días)
- [ ] Integrar scheduler existente con nueva config SQL
- [ ] Testing de re-sync CIENFUEGOS
- [ ] Testing de edición de configuración
- [ ] Testing de auditoría

### Fase 6: Documentación y Deploy (1-2 días)
- [ ] Documentar APIs
- [ ] Documentar uso de consola
- [ ] Deploy a producción

**Total estimado: 11-17 días**

---

## 20. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Scheduler no lee config SQL | Media | Alto | Fallback a config hardcodeada |
| Ejecución masiva no controlada | Baja | Alto | Límites de rango, rate limiting |
| Pérdida de auditoría | Baja | Medio | Transacciones atómicas |
| Conflicto de locks | Media | Medio | Timeout y cleanup automático |
| Error en dry_run diferente a real | Baja | Medio | Testing exhaustivo |

---

## 21. CRITERIOS DE ACEPTACIÓN

| # | Criterio |
|---|----------|
| 1 | Jobs se pueden ver desde consola web |
| 2 | Configuración se edita desde consola sin redeploy |
| 3 | Re-sincronización funciona para CIENFUEGOS 19-20 mayo |
| 4 | Dry run muestra preview sin modificar datos |
| 5 | Auditoría registra todos los cambios |
| 6 | Permisos restringen acceso por rol |
| 7 | Propinas separadas en ventas |
| 8 | Tablero Ejecutivo lee de EDARSAHUB SQL (no live) |
| 9 | UPSERT evita duplicados |
| 10 | Logs accesibles desde consola |

---

## 22. SIGUIENTE PASO

**¿Autoriza proceder con la implementación por fases?**

Si autoriza, comenzaré con **Fase 1: Modelo de Datos** - crear las tablas en EDARSAHUB SQL.

---

**Firmado:** E1 Agent  
**Rol:** Ingeniero Senior Fullstack + SQL Server Especialista EDARSAHUB  
**Estado:** DISEÑO TÉCNICO COMPLETO - PENDIENTE AUTORIZACIÓN PARA IMPLEMENTAR
