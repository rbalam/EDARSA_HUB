# FASE 1: Ejecución DDL - Catálogo Consultas SQL
## Tablas ConsultasSQL_* en EDARSAHUB

**Fecha:** 2026-05-15  
**Ejecutado por:** E1 Agent  
**Estado:** COMPLETADO

---

## 1. ESTADO PREVIO

### Tablas Existentes Antes del DDL
```
ConsultasSQL_*: NINGUNA
```

### Tablas Relacionadas Verificadas
- `Sistema_Tipos` ✅ (FK disponible)
- `Servidores_Conexiones` ✅ (No afectada)
- `Usuario_Catalogo` ✅ (No afectada)
- `Usuario_Roles` ✅ (No afectada)

---

## 2. DDL EJECUTADO

### 2.1 ConsultasSQL_Catalogo
```sql
CREATE TABLE ConsultasSQL_Catalogo (
    ConsultaID          INT IDENTITY(1,1) PRIMARY KEY,
    PublicUUID          UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    CodigoConsulta      VARCHAR(50) NOT NULL,
    NombreConsulta      NVARCHAR(200) NOT NULL,
    Descripcion         NVARCHAR(500) NULL,
    Modulo              VARCHAR(50) NOT NULL,
    TipoConsulta        VARCHAR(30) NOT NULL DEFAULT 'CONSULTA',
    SistemaTipoID       INT NOT NULL,
    ConsultaSQL         NVARCHAR(MAX) NOT NULL,
    EsSistema           BIT NOT NULL DEFAULT 0,
    EsPersonalizada     BIT NOT NULL DEFAULT 0,
    EsSincronizable     BIT NOT NULL DEFAULT 0,
    PermiteEjecucionManual BIT NOT NULL DEFAULT 1,
    SoloLectura         BIT NOT NULL DEFAULT 1,
    RequiereAutorizacion BIT NOT NULL DEFAULT 0,
    Activo              BIT NOT NULL DEFAULT 1,
    Version             INT NOT NULL DEFAULT 1,
    ConfigOrigen        VARCHAR(50) NOT NULL DEFAULT 'LEGACY_PYTHON',
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
    UsuarioCreacionID   NVARCHAR(100) NULL,
    FechaModificacion   DATETIME2 NULL,
    UsuarioModificacionID NVARCHAR(100) NULL,
    CONSTRAINT UQ_ConsultasSQL_Codigo UNIQUE (CodigoConsulta),
    CONSTRAINT UQ_ConsultasSQL_UUID UNIQUE (PublicUUID),
    CONSTRAINT FK_ConsultasSQL_SistemaTipo FOREIGN KEY (SistemaTipoID) 
        REFERENCES Sistema_Tipos(SistemaTipoID)
);
```

### 2.2 ConsultasSQL_Parametros
```sql
CREATE TABLE ConsultasSQL_Parametros (
    ParametroID         INT IDENTITY(1,1) PRIMARY KEY,
    ConsultaID          INT NOT NULL,
    NombreParametro     VARCHAR(50) NOT NULL,
    NombreMostrar       NVARCHAR(100) NULL,
    TipoDato            VARCHAR(20) NOT NULL DEFAULT 'STRING',
    Requerido           BIT NOT NULL DEFAULT 1,
    ValorDefault        NVARCHAR(200) NULL,
    RegexValidacion     NVARCHAR(500) NULL,
    ValorMinimo         NVARCHAR(100) NULL,
    ValorMaximo         NVARCHAR(100) NULL,
    ListaValoresJSON    NVARCHAR(MAX) NULL,
    OrdenMostrar        INT NOT NULL DEFAULT 0,
    ComponenteUI        VARCHAR(30) NULL,
    Activo              BIT NOT NULL DEFAULT 1,
    CONSTRAINT FK_ConsultasSQL_Param_Consulta FOREIGN KEY (ConsultaID) 
        REFERENCES ConsultasSQL_Catalogo(ConsultaID) ON DELETE CASCADE,
    CONSTRAINT UQ_ConsultasSQL_Param_Nombre UNIQUE (ConsultaID, NombreParametro)
);
```

### 2.3 ConsultasSQL_Servidores
```sql
CREATE TABLE ConsultasSQL_Servidores (
    ConsultaServidorID  INT IDENTITY(1,1) PRIMARY KEY,
    ConsultaID          INT NOT NULL,
    ServidorID          UNIQUEIDENTIFIER NOT NULL,
    EmpresaID           INT NULL,
    SucursalID          NVARCHAR(50) NULL,
    Activo              BIT NOT NULL DEFAULT 1,
    Prioridad           INT NOT NULL DEFAULT 0,
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
    UsuarioCreacionID   NVARCHAR(100) NULL,
    CONSTRAINT FK_ConsultasSQL_Srv_Consulta FOREIGN KEY (ConsultaID) 
        REFERENCES ConsultasSQL_Catalogo(ConsultaID) ON DELETE CASCADE,
    CONSTRAINT UQ_ConsultasSQL_Srv_Unique UNIQUE (ConsultaID, ServidorID, EmpresaID, SucursalID)
);
```

### 2.4 ConsultasSQL_EjecucionesLog
```sql
CREATE TABLE ConsultasSQL_EjecucionesLog (
    EjecucionID         BIGINT IDENTITY(1,1) PRIMARY KEY,
    ConsultaID          INT NOT NULL,
    ServidorID          UNIQUEIDENTIFIER NULL,
    UsuarioID           NVARCHAR(100) NOT NULL,
    FechaEjecucion      DATETIME2 NOT NULL DEFAULT GETDATE(),
    ParametrosJSON      NVARCHAR(MAX) NULL,
    ConsultaSQLEjecutada NVARCHAR(MAX) NULL,
    Estado              VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
    DuracionMs          INT NULL,
    RegistrosDevueltos  INT NULL,
    ErrorMensaje        NVARCHAR(MAX) NULL,
    IpOrigen            VARCHAR(50) NULL,
    UserAgent           NVARCHAR(500) NULL
);
```

### 2.5 ConsultasSQL_Permisos
```sql
CREATE TABLE ConsultasSQL_Permisos (
    PermisoID           INT IDENTITY(1,1) PRIMARY KEY,
    ConsultaID          INT NOT NULL,
    RolID               NVARCHAR(100) NULL,
    UsuarioID           NVARCHAR(100) NULL,
    PuedeVer            BIT NOT NULL DEFAULT 1,
    PuedeEjecutar       BIT NOT NULL DEFAULT 0,
    PuedeEditar         BIT NOT NULL DEFAULT 0,
    PuedeAutorizar      BIT NOT NULL DEFAULT 0,
    Activo              BIT NOT NULL DEFAULT 1,
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
    UsuarioCreacionID   NVARCHAR(100) NULL,
    CONSTRAINT FK_ConsultasSQL_Perm_Consulta FOREIGN KEY (ConsultaID) 
        REFERENCES ConsultasSQL_Catalogo(ConsultaID) ON DELETE CASCADE
);
```

### 2.6 ConsultasSQL_Versiones
```sql
CREATE TABLE ConsultasSQL_Versiones (
    VersionID           INT IDENTITY(1,1) PRIMARY KEY,
    ConsultaID          INT NOT NULL,
    Version             INT NOT NULL,
    ConsultaSQL         NVARCHAR(MAX) NOT NULL,
    ParametrosJSON      NVARCHAR(MAX) NULL,
    MotivoCambio        NVARCHAR(500) NULL,
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
    UsuarioCreacionID   NVARCHAR(100) NULL,
    CONSTRAINT FK_ConsultasSQL_Ver_Consulta FOREIGN KEY (ConsultaID) 
        REFERENCES ConsultasSQL_Catalogo(ConsultaID) ON DELETE CASCADE,
    CONSTRAINT UQ_ConsultasSQL_Ver_Unico UNIQUE (ConsultaID, Version)
);
```

---

## 3. TABLAS CREADAS

| Tabla | Columnas | PK | FK | Índices |
|-------|----------|----|----|---------|
| ConsultasSQL_Catalogo | 22 | ✅ | ✅ Sistema_Tipos | 4 |
| ConsultasSQL_Parametros | 14 | ✅ | ✅ Catalogo | 1 |
| ConsultasSQL_Servidores | 9 | ✅ | ✅ Catalogo | 2 |
| ConsultasSQL_EjecucionesLog | 13 | ✅ | ❌ (performance) | 3 |
| ConsultasSQL_Permisos | 11 | ✅ | ✅ Catalogo | 2 |
| ConsultasSQL_Versiones | 8 | ✅ | ✅ Catalogo | 1 |

---

## 4. ÍNDICES CREADOS

### ConsultasSQL_Catalogo
- `IX_ConsultasSQL_Modulo` (Modulo)
- `IX_ConsultasSQL_Sistema` (SistemaTipoID)
- `IX_ConsultasSQL_Activo` (Activo)
- `IX_ConsultasSQL_EsSistema` (EsSistema)

### ConsultasSQL_EjecucionesLog
- `IX_ConsultasSQL_Log_Fecha` (FechaEjecucion DESC)
- `IX_ConsultasSQL_Log_Consulta` (ConsultaID)
- `IX_ConsultasSQL_Log_Usuario` (UsuarioID)

### ConsultasSQL_Permisos
- `IX_ConsultasSQL_Perm_Consulta` (ConsultaID)
- `IX_ConsultasSQL_Perm_Rol` (RolID)

### ConsultasSQL_Versiones
- `IX_ConsultasSQL_Ver_Consulta` (ConsultaID)

---

## 5. FOREIGN KEYS CREADAS

| FK | Tabla Origen | Columna | Tabla Destino | ON DELETE |
|----|--------------|---------|---------------|-----------|
| FK_ConsultasSQL_SistemaTipo | Catalogo | SistemaTipoID | Sistema_Tipos | NO ACTION |
| FK_ConsultasSQL_Param_Consulta | Parametros | ConsultaID | Catalogo | CASCADE |
| FK_ConsultasSQL_Srv_Consulta | Servidores | ConsultaID | Catalogo | CASCADE |
| FK_ConsultasSQL_Perm_Consulta | Permisos | ConsultaID | Catalogo | CASCADE |
| FK_ConsultasSQL_Ver_Consulta | Versiones | ConsultaID | Catalogo | CASCADE |

---

## 6. VALIDACIONES REALIZADAS

| # | Validación | Estado |
|---|------------|--------|
| 1 | Tablas ConsultasSQL_* existen | ✅ |
| 2 | Columnas principales creadas | ✅ |
| 3 | Índices creados | ✅ |
| 4 | Servidores_Conexiones no afectada | ✅ |
| 5 | server_registry.py no modificado | ✅ |
| 6 | Frontend no modificado | ✅ |
| 7 | Endpoints no modificados | ✅ |
| 8 | Catálogo SQL legacy funciona | ✅ |
| 9 | Backend arranca | ✅ |
| 10 | Login funciona | ✅ |

---

## 7. ROLLBACK SQL

```sql
-- ROLLBACK: Eliminar tablas en orden inverso (por FK)
DROP TABLE IF EXISTS ConsultasSQL_Versiones;
DROP TABLE IF EXISTS ConsultasSQL_Permisos;
DROP TABLE IF EXISTS ConsultasSQL_EjecucionesLog;
DROP TABLE IF EXISTS ConsultasSQL_Servidores;
DROP TABLE IF EXISTS ConsultasSQL_Parametros;
DROP TABLE IF EXISTS ConsultasSQL_Catalogo;
```

---

## 8. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Duplicación de datos al migrar | BAJA | MEDIO | Script idempotente con MERGE |
| FK falla al insertar | BAJA | BAJO | Verificar SistemaTipoID existe |
| Rendimiento en Log | MEDIA | BAJO | Índices + particionamiento futuro |

---

## 9. RESULTADO FINAL

**FASE 1 COMPLETADA EXITOSAMENTE**

- 6 tablas creadas
- 13 índices creados
- 5 foreign keys configuradas
- Backend operativo
- Sin regresiones detectadas
- Catálogo SQL legacy sigue funcionando

**Próximo paso:** FASE 2 - Cargar consultas desde `catalogo_consultas.py`

---

*Documento generado automáticamente por E1 Agent*  
*Fecha: 2026-05-15*
