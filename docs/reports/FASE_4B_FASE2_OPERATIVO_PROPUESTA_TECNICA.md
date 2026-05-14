# FASE 4B-FASE2_OPERATIVO — Propuesta Técnica de Migración

**Fecha:** 2026-05-14  
**Estado:** PROPUESTA (PENDIENTE AUTORIZACIÓN)  
**Régimen:** Autorización Controlada  
**Módulo:** fase2_operativo (Operaciones de Inventario)

---

## 1. RESUMEN EJECUTIVO

El módulo `fase2_operativo` gestiona:
- Workflows de inventarios físicos
- Tareas de inventario (asignaciones, seguimiento)
- Detalle de diferencias encontradas
- Alertas del sistema
- Configuración operativa

Este módulo tiene **36 referencias directas** a colecciones MongoDB distribuidas en 6 archivos de servicios.

### Complejidad: ALTA
- 18 archivos de servicios
- 14 archivos de repositorios
- 10 archivos de schemas
- Múltiples colecciones interconectadas

---

## 2. ESTADO ACTUAL EN MONGODB

### 2.1 Colecciones Usadas

| Colección MongoDB | Documentos | Descripción |
|-------------------|------------|-------------|
| `tareas_inventario` | 18 | Tareas de seguimiento de inventarios |
| `workflow_inventarios` | 18 | Flujos de trabajo de inventarios físicos |
| `detalle_diferencias` | 1,960 | Diferencias encontradas en conteos |
| `inventarios_sin_asignar` | 8 | Inventarios pendientes de asignación |
| `alertas_sistema` | 8 | Alertas operativas |
| `config_asignaciones` | 2 | Configuración de asignaciones |
| `configuracion_operativo` | 1 | Configuración general operativa |
| `inventarios_fisicos_procesados` | 1 | Inventarios ya procesados |
| `workflows_inventario` | 0 | (Alias o typo de workflow_inventarios) |
| `configuracion_operativa` | 0 | (Alias o typo de configuracion_operativo) |
| `users` | ~15 | (Tabla compartida - ya migrada a SQL) |

**Total documentos en colecciones específicas:** ~2,016

### 2.2 Archivos con Referencias MongoDB

| Archivo | Referencias | Colecciones |
|---------|-------------|-------------|
| `services/orquestador_service.py` | 17 | tareas_inventario, workflow_inventarios, users |
| `services/sla_service.py` | 11 | tareas_inventario, workflows_inventario, configuracion_operativo |
| `services/auditoria_programada_service.py` | 4 | workflow_inventarios, users, config_asignaciones, configuracion_operativa |
| `services/cargos_service.py` | 2 | users, workflow_inventarios |
| `services/automatizacion_compras_service.py` | 1 | inventarios_fisicos_procesados |
| `services/document_data_service.py` | 1 | workflow_inventarios |

---

## 3. ESTADO ACTUAL EN EDARSAHUB SQL

### 3.1 Tablas Relacionadas (Existentes)

| Tabla SQL | Registros | Compatible | Uso |
|-----------|-----------|------------|-----|
| `automatizacion_inventarios_*` | ~1 | PARCIAL | Para automatización |
| `Inventario_*` | 0-6 | NO | Catálogos de inventario físico |
| `Usuario_Catalogo` | ~15 | SÍ | Usuarios (ya migrada) |

### 3.2 Tablas Requeridas (No Existen)

| Tabla Propuesta | Equivale a MongoDB |
|-----------------|-------------------|
| `Operativo_Workflows` | workflow_inventarios |
| `Operativo_Tareas` | tareas_inventario |
| `Operativo_DetalleDiferencias` | detalle_diferencias |
| `Operativo_Alertas` | alertas_sistema |
| `Operativo_InventariosSinAsignar` | inventarios_sin_asignar |
| `Operativo_ConfigAsignaciones` | config_asignaciones |
| `Operativo_Configuracion` | configuracion_operativo |

---

## 4. ANÁLISIS DE ESTRUCTURA MONGODB

### 4.1 workflow_inventarios
```json
{
  "id": "UUID",
  "folio": "INV-2026-001",
  "server_id": "UUID del servidor",
  "sucursal_id": "UUID de sucursal",
  "tipo_inventario": "FISICO|CICLICO",
  "estado": "PENDIENTE|EN_PROCESO|COMPLETADO|CERRADO",
  "fecha_inicio": ISODate,
  "fecha_cierre": ISODate,
  "responsable_id": "UUID",
  "diferencias_count": 150,
  "diferencias_valor": 25000.50,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### 4.2 tareas_inventario
```json
{
  "id": "UUID",
  "workflow_id": "UUID del workflow",
  "tipo_tarea": "CONTEO|RECONTEO|JUSTIFICACION|APLICACION",
  "estado": "PENDIENTE|EN_PROCESO|COMPLETADA|VENCIDA",
  "asignado_a": "UUID del usuario",
  "fecha_limite": ISODate,
  "fecha_completada": ISODate,
  "prioridad": "ALTA|MEDIA|BAJA",
  "notas": "texto",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### 4.3 detalle_diferencias
```json
{
  "id": "UUID",
  "workflow_id": "UUID del workflow",
  "producto_id": "código producto",
  "descripcion": "nombre producto",
  "existencia_sistema": 100,
  "existencia_fisica": 95,
  "diferencia": -5,
  "costo_unitario": 150.00,
  "costo_diferencia": -750.00,
  "justificacion": "texto",
  "estado": "PENDIENTE|JUSTIFICADO|APLICADO",
  "created_at": ISODate
}
```

### 4.4 alertas_sistema
```json
{
  "id": "UUID",
  "tipo": "SLA_VENCIDO|INVENTARIO_CRITICO|DIFERENCIA_ALTA",
  "mensaje": "texto",
  "entidad_tipo": "WORKFLOW|TAREA",
  "entidad_id": "UUID",
  "usuario_destino": "UUID",
  "leida": false,
  "created_at": ISODate
}
```

---

## 5. DDL PROPUESTO

### 5.1 Operativo_Workflows
```sql
CREATE TABLE Operativo_Workflows (
    WorkflowID BIGINT IDENTITY(1,1) PRIMARY KEY,
    PublicUUID VARCHAR(36) NOT NULL UNIQUE,
    Folio VARCHAR(30) NOT NULL,
    ServerID INT NULL,                      -- FK Sistema_Servidores
    SucursalID INT NULL,                    -- FK Sistema_Sucursales
    TipoInventario VARCHAR(20) NOT NULL,    -- FISICO, CICLICO
    Estado VARCHAR(20) NOT NULL,            -- PENDIENTE, EN_PROCESO, COMPLETADO, CERRADO
    FechaInicio DATETIME2 NOT NULL,
    FechaCierre DATETIME2 NULL,
    ResponsableID INT NULL,                 -- FK Usuario_Catalogo
    DiferenciasCount INT NOT NULL DEFAULT 0,
    DiferenciasValor DECIMAL(18,2) NOT NULL DEFAULT 0,
    Activo BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE(),
    UpdatedAt DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL,
    
    INDEX IX_Workflow_Estado (Estado),
    INDEX IX_Workflow_Server (ServerID),
    INDEX IX_Workflow_Fecha (FechaInicio DESC)
);
```

### 5.2 Operativo_Tareas
```sql
CREATE TABLE Operativo_Tareas (
    TareaID BIGINT IDENTITY(1,1) PRIMARY KEY,
    PublicUUID VARCHAR(36) NOT NULL UNIQUE,
    WorkflowID BIGINT NOT NULL,             -- FK Operativo_Workflows
    TipoTarea VARCHAR(30) NOT NULL,         -- CONTEO, RECONTEO, JUSTIFICACION, APLICACION
    Estado VARCHAR(20) NOT NULL,            -- PENDIENTE, EN_PROCESO, COMPLETADA, VENCIDA
    AsignadoA INT NULL,                     -- FK Usuario_Catalogo
    FechaLimite DATETIME2 NULL,
    FechaCompletada DATETIME2 NULL,
    Prioridad VARCHAR(10) NOT NULL DEFAULT 'MEDIA',
    Notas NVARCHAR(500) NULL,
    Activo BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE(),
    UpdatedAt DATETIME2 NULL,
    
    FOREIGN KEY (WorkflowID) REFERENCES Operativo_Workflows(WorkflowID),
    INDEX IX_Tarea_Estado (Estado),
    INDEX IX_Tarea_Workflow (WorkflowID),
    INDEX IX_Tarea_Asignado (AsignadoA)
);
```

### 5.3 Operativo_DetalleDiferencias
```sql
CREATE TABLE Operativo_DetalleDiferencias (
    DetalleID BIGINT IDENTITY(1,1) PRIMARY KEY,
    PublicUUID VARCHAR(36) NOT NULL UNIQUE,
    WorkflowID BIGINT NOT NULL,             -- FK Operativo_Workflows
    ProductoID VARCHAR(50) NOT NULL,
    Descripcion NVARCHAR(200) NULL,
    ExistenciaSistema DECIMAL(18,4) NOT NULL,
    ExistenciaFisica DECIMAL(18,4) NOT NULL,
    Diferencia DECIMAL(18,4) NOT NULL,
    CostoUnitario DECIMAL(18,4) NOT NULL DEFAULT 0,
    CostoDiferencia DECIMAL(18,4) NOT NULL DEFAULT 0,
    Justificacion NVARCHAR(500) NULL,
    Estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    Activo BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    FOREIGN KEY (WorkflowID) REFERENCES Operativo_Workflows(WorkflowID),
    INDEX IX_Detalle_Workflow (WorkflowID),
    INDEX IX_Detalle_Estado (Estado)
);
```

### 5.4 Operativo_Alertas
```sql
CREATE TABLE Operativo_Alertas (
    AlertaID BIGINT IDENTITY(1,1) PRIMARY KEY,
    PublicUUID VARCHAR(36) NOT NULL UNIQUE,
    Tipo VARCHAR(30) NOT NULL,              -- SLA_VENCIDO, INVENTARIO_CRITICO, DIFERENCIA_ALTA
    Mensaje NVARCHAR(500) NOT NULL,
    EntidadTipo VARCHAR(30) NULL,           -- WORKFLOW, TAREA
    EntidadID VARCHAR(36) NULL,
    UsuarioDestinoID INT NULL,              -- FK Usuario_Catalogo
    Leida BIT NOT NULL DEFAULT 0,
    Activo BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    INDEX IX_Alerta_Usuario (UsuarioDestinoID),
    INDEX IX_Alerta_Tipo (Tipo)
);
```

### 5.5 Operativo_InventariosSinAsignar
```sql
CREATE TABLE Operativo_InventariosSinAsignar (
    RegistroID BIGINT IDENTITY(1,1) PRIMARY KEY,
    PublicUUID VARCHAR(36) NOT NULL UNIQUE,
    ServerID INT NULL,
    SucursalID INT NULL,
    Folio VARCHAR(30) NOT NULL,
    FechaInventario DATETIME2 NOT NULL,
    DiferenciasCount INT NOT NULL DEFAULT 0,
    DiferenciasValor DECIMAL(18,2) NOT NULL DEFAULT 0,
    Estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    Activo BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    INDEX IX_SinAsignar_Estado (Estado),
    INDEX IX_SinAsignar_Server (ServerID)
);
```

### 5.6 Operativo_Configuracion
```sql
CREATE TABLE Operativo_Configuracion (
    ConfigID INT IDENTITY(1,1) PRIMARY KEY,
    Clave VARCHAR(50) NOT NULL UNIQUE,
    Valor NVARCHAR(500) NOT NULL,
    Descripcion NVARCHAR(200) NULL,
    TipoDato VARCHAR(20) NOT NULL DEFAULT 'STRING',
    Activo BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE(),
    UpdatedAt DATETIME2 NULL
);
```

### 5.7 Operativo_ConfigAsignaciones
```sql
CREATE TABLE Operativo_ConfigAsignaciones (
    ConfigAsignacionID INT IDENTITY(1,1) PRIMARY KEY,
    PublicUUID VARCHAR(36) NOT NULL UNIQUE,
    TipoAsignacion VARCHAR(30) NOT NULL,
    UsuarioID INT NULL,                     -- FK Usuario_Catalogo
    ServerID INT NULL,
    SucursalID INT NULL,
    EsDefault BIT NOT NULL DEFAULT 0,
    Activo BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    INDEX IX_ConfigAsig_Tipo (TipoAsignacion)
);
```

---

## 6. ESTRATEGIA DE MIGRACIÓN

### 6.1 Fases de Migración

```
FASE A: Crear tablas SQL (DDL)
FASE B: Migrar datos de MongoDB a SQL
FASE C: Crear repositorios SQL (*_repository_sql.py)
FASE D: Modificar servicios para SQL-first
FASE E: Validación y pruebas
```

### 6.2 Orden de Migración de Datos

```
1. Operativo_Configuracion ← configuracion_operativo
2. Operativo_ConfigAsignaciones ← config_asignaciones
3. Operativo_Workflows ← workflow_inventarios
4. Operativo_Tareas ← tareas_inventario
5. Operativo_DetalleDiferencias ← detalle_diferencias
6. Operativo_InventariosSinAsignar ← inventarios_sin_asignar
7. Operativo_Alertas ← alertas_sistema
```

### 6.3 Estimación de Migración de Datos

| Colección | Documentos | Estimación |
|-----------|------------|------------|
| configuracion_operativo | 1 | < 1 min |
| config_asignaciones | 2 | < 1 min |
| workflow_inventarios | 18 | < 1 min |
| tareas_inventario | 18 | < 1 min |
| detalle_diferencias | 1,960 | ~ 2 min |
| inventarios_sin_asignar | 8 | < 1 min |
| alertas_sistema | 8 | < 1 min |
| **TOTAL** | **2,016** | **~5 min** |

---

## 7. ARCHIVOS A MODIFICAR

### 7.1 Servicios (6 archivos)

| Archivo | Cambio |
|---------|--------|
| `services/orquestador_service.py` | Migrar a SQL |
| `services/sla_service.py` | Migrar a SQL |
| `services/auditoria_programada_service.py` | Migrar a SQL |
| `services/cargos_service.py` | Usar usuarios de SQL |
| `services/automatizacion_compras_service.py` | Migrar a SQL |
| `services/document_data_service.py` | Migrar a SQL |

### 7.2 Repositorios Nuevos (a crear)

| Archivo | Propósito |
|---------|-----------|
| `repositories/workflow_repository_sql.py` | CRUD workflows |
| `repositories/tarea_repository_sql.py` | CRUD tareas |
| `repositories/diferencias_repository_sql.py` | CRUD diferencias |
| `repositories/alertas_repository_sql.py` | CRUD alertas |
| `repositories/config_repository_sql.py` | CRUD configuración |

---

## 8. ENDPOINTS AFECTADOS

| Endpoint | Impacto |
|----------|---------|
| `GET /api/operativo/workflows` | ALTO |
| `POST /api/operativo/workflows` | ALTO |
| `GET /api/operativo/tareas` | ALTO |
| `POST /api/operativo/tareas/{id}/completar` | ALTO |
| `GET /api/operativo/diferencias` | ALTO |
| `POST /api/operativo/diferencias/{id}/justificar` | ALTO |
| `GET /api/operativo/alertas` | MEDIO |
| `GET /api/operativo/configuracion` | BAJO |

---

## 9. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Pérdida de datos en migración | BAJA | ALTO | Backup previo, validar conteos |
| Incompatibilidad de tipos de datos | MEDIA | MEDIO | Mapeo cuidadoso de tipos |
| Regresión en operaciones diarias | MEDIA | ALTO | Pruebas extensivas |
| Rendimiento en detalle_diferencias | MEDIA | MEDIO | Índices adecuados |

---

## 10. VALIDACIONES POST-MIGRACIÓN

### 10.1 Conteos
```sql
-- Verificar migración completa
SELECT 'Workflows' as Tabla, COUNT(*) as Registros FROM Operativo_Workflows
UNION ALL
SELECT 'Tareas', COUNT(*) FROM Operativo_Tareas
UNION ALL
SELECT 'Diferencias', COUNT(*) FROM Operativo_DetalleDiferencias
UNION ALL
SELECT 'Alertas', COUNT(*) FROM Operativo_Alertas
```

### 10.2 Funcionalidad
- [ ] Listar workflows funciona
- [ ] Crear workflow funciona
- [ ] Listar tareas funciona
- [ ] Completar tarea funciona
- [ ] Ver diferencias funciona
- [ ] Justificar diferencias funciona
- [ ] Alertas se generan correctamente

---

## 11. PLAN DE ROLLBACK

### Rollback por DDL:
- Las tablas son nuevas (no modifican existentes)
- `DROP TABLE` revierte el DDL

### Rollback por Código:
- Git revert de archivos modificados
- MongoDB sigue teniendo los datos originales

---

## 12. CONFIRMACIONES REQUERIDAS

### Fuera de Alcance (NO se modificará):
- ❌ RBAC (ya migrado)
- ❌ Comercial V2 / Tablero Ejecutivo
- ❌ Compras
- ❌ Finanzas
- ❌ Autenticación
- ❌ Usuarios (ya migrados)

### En Alcance:
- ✅ módulo `fase2_operativo` únicamente

---

## 13. SOLICITUD DE AUTORIZACIÓN

### Para proceder con FASE 4B-FASE2_OPERATIVO se requiere:

1. **¿Autoriza crear las 7 tablas SQL propuestas?**
   - Operativo_Workflows
   - Operativo_Tareas
   - Operativo_DetalleDiferencias
   - Operativo_Alertas
   - Operativo_InventariosSinAsignar
   - Operativo_Configuracion
   - Operativo_ConfigAsignaciones

2. **¿Autoriza migrar los ~2,016 documentos de MongoDB a SQL?**

3. **¿Autoriza modificar los 6 archivos de servicios?**

4. **¿Confirma que MongoDB queda como histórico temporal (sin eliminar colecciones)?**

---

**Propuesta generada:** 2026-05-14  
**Estado:** PENDIENTE AUTORIZACIÓN  
**Sin modificaciones de código realizadas**
