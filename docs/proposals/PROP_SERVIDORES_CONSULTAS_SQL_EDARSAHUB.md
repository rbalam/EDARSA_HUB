# PROPUESTA: Modelo SQL para Consultas Configurables
## Migración de Catálogo Hardcodeado a EDARSAHUB SQL

**Fecha:** 2026-05-15  
**Autor:** E1 Agent  
**Estado:** PROPUESTA - SIN EJECUTAR

---

## 1. RESUMEN

Esta propuesta define el DDL para migrar el catálogo de consultas SQL desde código Python hardcodeado hacia tablas estructuradas en EDARSAHUB SQL Server.

### Objetivos:
1. Eliminar dependencia de código Python para definir consultas
2. Permitir versionado y auditoría de cambios
3. Implementar control de permisos granular
4. Registrar todas las ejecuciones para auditoría

---

## 2. TABLAS YA EXISTENTES (NO MODIFICAR)

### `Sistema_Tipos`
```sql
-- YA EXISTE - NO CREAR
-- Contiene: SOFTRESTAURANT, MPRO, API_LOCAL, EDARSAHUB_SQL, OTRO
```

### `Servidores_Conexiones`
```sql
-- YA EXISTE - NO CREAR
-- Ya soporta queries por servidor via campos JSON:
--   query_ventas, query_inventario, query_movimientos
```

---

## 3. DDL PROPUESTO (SIN EJECUTAR)

### 3.1 Tabla: `ConsultasSQL_Catalogo`
```sql
-- ============================================================================
-- PROPUESTA DDL - NO EJECUTAR SIN AUTORIZACIÓN
-- ============================================================================

CREATE TABLE ConsultasSQL_Catalogo (
    -- Identificadores
    ConsultaID          INT IDENTITY(1,1) PRIMARY KEY,
    PublicUUID          UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    CodigoConsulta      VARCHAR(50) NOT NULL,        -- Ej: SR_VENTAS_DIA, MPRO_COMPRAS_PERIODO
    
    -- Metadata
    NombreConsulta      NVARCHAR(200) NOT NULL,      -- Ej: "Ventas del Día"
    Descripcion         NVARCHAR(500) NULL,
    
    -- Clasificación
    Modulo              VARCHAR(50) NOT NULL,        -- Ventas, Compras, Inventario, Pagos, Reportes
    TipoConsulta        VARCHAR(30) NOT NULL,        -- CONSULTA, REPORTE, SINCRONIZACION, DIAGNOSTICO
    SistemaTipoID       INT NOT NULL,                -- FK a Sistema_Tipos
    
    -- SQL Query
    ConsultaSQL         NVARCHAR(MAX) NOT NULL,      -- El SQL con placeholders {param}
    
    -- Flags de comportamiento
    EsSistema           BIT NOT NULL DEFAULT 0,      -- 1=Predefinida del sistema, no editable
    EsPersonalizada     BIT NOT NULL DEFAULT 0,      -- 1=Creada por usuario
    EsSincronizable     BIT NOT NULL DEFAULT 0,      -- 1=Usada por scheduler
    PermiteEjecucionManual BIT NOT NULL DEFAULT 1,   -- 1=Puede ejecutarse desde UI
    SoloLectura         BIT NOT NULL DEFAULT 1,      -- 1=Solo SELECT permitido
    RequiereAutorizacion BIT NOT NULL DEFAULT 0,     -- 1=Necesita aprobación para ejecutar
    
    -- Control de estado
    Activo              BIT NOT NULL DEFAULT 1,
    Version             INT NOT NULL DEFAULT 1,
    
    -- Origen de configuración
    ConfigOrigen        VARCHAR(50) NOT NULL DEFAULT 'EDARSAHUB_SQL',
    
    -- Auditoría
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
    UsuarioCreacionID   NVARCHAR(100) NULL,
    FechaModificacion   DATETIME2 NULL,
    UsuarioModificacionID NVARCHAR(100) NULL,
    
    -- Constraints
    CONSTRAINT UQ_ConsultasSQL_Codigo UNIQUE (CodigoConsulta),
    CONSTRAINT UQ_ConsultasSQL_UUID UNIQUE (PublicUUID),
    CONSTRAINT FK_ConsultasSQL_SistemaTipo FOREIGN KEY (SistemaTipoID) 
        REFERENCES Sistema_Tipos(SistemaTipoID),
    CONSTRAINT CK_ConsultasSQL_TipoConsulta CHECK (
        TipoConsulta IN ('CONSULTA', 'REPORTE', 'SINCRONIZACION', 'DIAGNOSTICO')
    )
);

-- Índices
CREATE INDEX IX_ConsultasSQL_Modulo ON ConsultasSQL_Catalogo(Modulo);
CREATE INDEX IX_ConsultasSQL_Sistema ON ConsultasSQL_Catalogo(SistemaTipoID);
CREATE INDEX IX_ConsultasSQL_Activo ON ConsultasSQL_Catalogo(Activo);
CREATE INDEX IX_ConsultasSQL_EsSistema ON ConsultasSQL_Catalogo(EsSistema);
```

### 3.2 Tabla: `ConsultasSQL_Parametros`
```sql
CREATE TABLE ConsultasSQL_Parametros (
    ParametroID         INT IDENTITY(1,1) PRIMARY KEY,
    ConsultaID          INT NOT NULL,
    
    -- Definición del parámetro
    NombreParametro     VARCHAR(50) NOT NULL,        -- Ej: fecha_ini, fecha_fin, sucursal_id
    NombreMostrar       NVARCHAR(100) NULL,          -- Ej: "Fecha Inicio"
    TipoDato            VARCHAR(20) NOT NULL,        -- STRING, DATE, INT, DECIMAL, BOOLEAN
    
    -- Validación
    Requerido           BIT NOT NULL DEFAULT 1,
    ValorDefault        NVARCHAR(200) NULL,
    RegexValidacion     NVARCHAR(500) NULL,          -- Ej: ^\d{4}-\d{2}-\d{2}$
    ValorMinimo         NVARCHAR(100) NULL,
    ValorMaximo         NVARCHAR(100) NULL,
    ListaValoresPermitidosJSON NVARCHAR(MAX) NULL,   -- ["opcion1", "opcion2"]
    
    -- UI
    OrdenMostrar        INT NOT NULL DEFAULT 0,
    ComponenteUI        VARCHAR(30) NULL,            -- DATE_PICKER, SELECT, INPUT, CHECKBOX
    
    -- Estado
    Activo              BIT NOT NULL DEFAULT 1,
    
    CONSTRAINT FK_ConsultasSQL_Param_Consulta FOREIGN KEY (ConsultaID) 
        REFERENCES ConsultasSQL_Catalogo(ConsultaID) ON DELETE CASCADE,
    CONSTRAINT UQ_ConsultasSQL_Param_Nombre UNIQUE (ConsultaID, NombreParametro),
    CONSTRAINT CK_ConsultasSQL_Param_Tipo CHECK (
        TipoDato IN ('STRING', 'DATE', 'DATETIME', 'INT', 'DECIMAL', 'BOOLEAN')
    )
);

CREATE INDEX IX_ConsultasSQL_Param_Consulta ON ConsultasSQL_Parametros(ConsultaID);
```

### 3.3 Tabla: `ConsultasSQL_Servidores`
```sql
-- Relación N:M entre Consultas y Servidores donde pueden ejecutarse
CREATE TABLE ConsultasSQL_Servidores (
    ConsultaServidorID  INT IDENTITY(1,1) PRIMARY KEY,
    ConsultaID          INT NOT NULL,
    ServidorID          UNIQUEIDENTIFIER NOT NULL,   -- FK a Servidores_Conexiones.id
    
    -- Contexto empresarial
    EmpresaID           INT NULL,                    -- FK a Sistema_Empresas (opcional)
    SucursalID          NVARCHAR(50) NULL,           -- Sucursal específica (opcional)
    
    -- Control
    Activo              BIT NOT NULL DEFAULT 1,
    Prioridad           INT NOT NULL DEFAULT 0,      -- Para ordenar si hay múltiples servidores
    
    -- Auditoría
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
    UsuarioCreacionID   NVARCHAR(100) NULL,
    
    CONSTRAINT FK_ConsultasSQL_Srv_Consulta FOREIGN KEY (ConsultaID) 
        REFERENCES ConsultasSQL_Catalogo(ConsultaID) ON DELETE CASCADE,
    CONSTRAINT UQ_ConsultasSQL_Srv_Unique UNIQUE (ConsultaID, ServidorID, EmpresaID, SucursalID)
);

CREATE INDEX IX_ConsultasSQL_Srv_Consulta ON ConsultasSQL_Servidores(ConsultaID);
CREATE INDEX IX_ConsultasSQL_Srv_Servidor ON ConsultasSQL_Servidores(ServidorID);
```

### 3.4 Tabla: `ConsultasSQL_EjecucionesLog`
```sql
CREATE TABLE ConsultasSQL_EjecucionesLog (
    EjecucionID         BIGINT IDENTITY(1,1) PRIMARY KEY,
    
    -- Referencias
    ConsultaID          INT NOT NULL,
    ServidorID          UNIQUEIDENTIFIER NOT NULL,
    UsuarioID           NVARCHAR(100) NOT NULL,
    
    -- Contexto de ejecución
    FechaEjecucion      DATETIME2 NOT NULL DEFAULT GETDATE(),
    ParametrosJSON      NVARCHAR(MAX) NULL,          -- {"fecha_ini": "2026-01-01", ...}
    ConsultaSQLEjecutada NVARCHAR(MAX) NULL,         -- SQL con parámetros reemplazados
    
    -- Resultado
    Estado              VARCHAR(20) NOT NULL,        -- SUCCESS, ERROR, TIMEOUT, CANCELLED
    DuracionMs          INT NULL,
    RegistrosDevueltos  INT NULL,
    ErrorMensaje        NVARCHAR(MAX) NULL,
    
    -- Metadata técnica
    IpOrigen            VARCHAR(50) NULL,
    UserAgent           NVARCHAR(500) NULL,
    
    -- NO FK para evitar bloqueos en alta concurrencia
    CONSTRAINT CK_ConsultasSQL_Log_Estado CHECK (
        Estado IN ('SUCCESS', 'ERROR', 'TIMEOUT', 'CANCELLED', 'DENIED')
    )
);

-- Índices para queries de auditoría
CREATE INDEX IX_ConsultasSQL_Log_Fecha ON ConsultasSQL_EjecucionesLog(FechaEjecucion DESC);
CREATE INDEX IX_ConsultasSQL_Log_Consulta ON ConsultasSQL_EjecucionesLog(ConsultaID);
CREATE INDEX IX_ConsultasSQL_Log_Usuario ON ConsultasSQL_EjecucionesLog(UsuarioID);
CREATE INDEX IX_ConsultasSQL_Log_Estado ON ConsultasSQL_EjecucionesLog(Estado);

-- Particionamiento sugerido para tabla de log (comentado para evaluación)
-- ALTER TABLE ConsultasSQL_EjecucionesLog 
-- ADD CONSTRAINT PK_Log_Partitioned PRIMARY KEY CLUSTERED (EjecucionID, FechaEjecucion);
```

### 3.5 Tabla: `ConsultasSQL_Permisos`
```sql
CREATE TABLE ConsultasSQL_Permisos (
    PermisoID           INT IDENTITY(1,1) PRIMARY KEY,
    ConsultaID          INT NOT NULL,
    
    -- Asignación (uno de los dos)
    RolID               NVARCHAR(100) NULL,          -- Rol del sistema (Administrador, Operador, etc.)
    UsuarioID           NVARCHAR(100) NULL,          -- Usuario específico (opcional)
    
    -- Permisos granulares
    PuedeVer            BIT NOT NULL DEFAULT 1,      -- Ver en catálogo
    PuedeEjecutar       BIT NOT NULL DEFAULT 0,      -- Ejecutar consulta
    PuedeEditar         BIT NOT NULL DEFAULT 0,      -- Modificar SQL (solo si no es sistema)
    PuedeAutorizar      BIT NOT NULL DEFAULT 0,      -- Aprobar ejecución de consultas restringidas
    
    -- Estado
    Activo              BIT NOT NULL DEFAULT 1,
    
    -- Auditoría
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
    UsuarioCreacionID   NVARCHAR(100) NULL,
    
    CONSTRAINT FK_ConsultasSQL_Perm_Consulta FOREIGN KEY (ConsultaID) 
        REFERENCES ConsultasSQL_Catalogo(ConsultaID) ON DELETE CASCADE,
    CONSTRAINT CK_ConsultasSQL_Perm_RolOUsuario CHECK (
        (RolID IS NOT NULL AND UsuarioID IS NULL) OR 
        (RolID IS NULL AND UsuarioID IS NOT NULL)
    )
);

CREATE INDEX IX_ConsultasSQL_Perm_Consulta ON ConsultasSQL_Permisos(ConsultaID);
CREATE INDEX IX_ConsultasSQL_Perm_Rol ON ConsultasSQL_Permisos(RolID);
CREATE INDEX IX_ConsultasSQL_Perm_Usuario ON ConsultasSQL_Permisos(UsuarioID);
```

### 3.6 Tabla: `ConsultasSQL_Versiones`
```sql
-- Historial de versiones de cada consulta
CREATE TABLE ConsultasSQL_Versiones (
    VersionID           INT IDENTITY(1,1) PRIMARY KEY,
    ConsultaID          INT NOT NULL,
    
    -- Snapshot de la versión
    Version             INT NOT NULL,
    ConsultaSQL         NVARCHAR(MAX) NOT NULL,
    ParametrosJSON      NVARCHAR(MAX) NULL,          -- Snapshot de parámetros
    
    -- Metadata del cambio
    MotivoCambio        NVARCHAR(500) NULL,
    
    -- Auditoría
    FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
    UsuarioCreacionID   NVARCHAR(100) NULL,
    
    CONSTRAINT FK_ConsultasSQL_Ver_Consulta FOREIGN KEY (ConsultaID) 
        REFERENCES ConsultasSQL_Catalogo(ConsultaID) ON DELETE CASCADE,
    CONSTRAINT UQ_ConsultasSQL_Ver_Unico UNIQUE (ConsultaID, Version)
);

CREATE INDEX IX_ConsultasSQL_Ver_Consulta ON ConsultasSQL_Versiones(ConsultaID);
```

---

## 4. TABLAS OPCIONALES (EVALUACIÓN POSTERIOR)

### 4.1 `API_ConexionesLocales` (Opcional)
```sql
-- NOTA: Esta funcionalidad YA EXISTE en Servidores_Conexiones con tipo_conexion='API_LOCAL'
-- Solo crear si se requiere separación explícita

-- CREATE TABLE API_ConexionesLocales (
--     APIConexionID       INT IDENTITY(1,1) PRIMARY KEY,
--     PublicUUID          UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
--     ServidorID          UNIQUEIDENTIFIER NOT NULL,   -- FK a Servidores_Conexiones (padre SQL Server)
--     EmpresaID           INT NULL,
--     SucursalID          NVARCHAR(50) NULL,
--     Nombre              NVARCHAR(100) NOT NULL,
--     BaseUrl             NVARCHAR(500) NOT NULL,
--     EndpointQuery       NVARCHAR(200) NOT NULL DEFAULT '/query',
--     ApiKeyEncrypted     NVARCHAR(500) NULL,
--     RolConexion         VARCHAR(50) NULL,            -- VENTAS_DIA_API_LOCAL, REPLICA_DIARIA, etc.
--     Activo              BIT NOT NULL DEFAULT 1,
--     FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
--     UsuarioCreacionID   NVARCHAR(100) NULL
-- );
```

---

## 5. DATOS INICIALES SUGERIDOS (DML)

### 5.1 Carga de Consultas Predefinidas
```sql
-- ============================================================================
-- PROPUESTA DML - NO EJECUTAR SIN AUTORIZACIÓN
-- ============================================================================

-- EJEMPLO: Migrar SR_VENTAS_DIA desde Python
INSERT INTO ConsultasSQL_Catalogo (
    CodigoConsulta, NombreConsulta, Descripcion, Modulo, TipoConsulta,
    SistemaTipoID, ConsultaSQL, EsSistema, PermiteEjecucionManual,
    SoloLectura, Activo, UsuarioCreacionID
)
VALUES (
    'SR_VENTAS_DIA',
    'Ventas del Día',
    'Total de ventas, cheques y comensales del día seleccionado',
    'Ventas',
    'CONSULTA',
    1,  -- SistemaTipoID = SOFTRESTAURANT
    'SELECT 
    COUNT(DISTINCT cheques.folio) as Cheques,
    ISNULL(SUM(cheques.total), 0) as Venta_Total,
    ISNULL(SUM(cheques.nopersonas), 0) as PAX,
    ISNULL(AVG(cheques.total), 0) as Cheque_Promedio,
    ISNULL(AVG(CAST(cheques.nopersonas as float)), 0) as PAX_Promedio
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE CONVERT(date, turnos.apertura) = ''{fecha}''
  AND cheques.cancelado = 0',
    1,  -- EsSistema = true
    1,  -- PermiteEjecucionManual = true
    1,  -- SoloLectura = true
    1,  -- Activo = true
    'SISTEMA'
);

-- Registrar parámetro
INSERT INTO ConsultasSQL_Parametros (
    ConsultaID, NombreParametro, NombreMostrar, TipoDato,
    Requerido, OrdenMostrar, ComponenteUI
)
SELECT 
    ConsultaID, 'fecha', 'Fecha', 'DATE', 1, 1, 'DATE_PICKER'
FROM ConsultasSQL_Catalogo
WHERE CodigoConsulta = 'SR_VENTAS_DIA';

-- Registrar versión inicial
INSERT INTO ConsultasSQL_Versiones (
    ConsultaID, Version, ConsultaSQL, MotivoCambio, UsuarioCreacionID
)
SELECT 
    ConsultaID, 1, ConsultaSQL, 'Versión inicial migrada desde Python', 'SISTEMA'
FROM ConsultasSQL_Catalogo
WHERE CodigoConsulta = 'SR_VENTAS_DIA';

-- Asignar permiso por defecto a Administrador
INSERT INTO ConsultasSQL_Permisos (
    ConsultaID, RolID, PuedeVer, PuedeEjecutar, PuedeEditar, UsuarioCreacionID
)
SELECT 
    ConsultaID, 'Administrador', 1, 1, 0, 'SISTEMA'
FROM ConsultasSQL_Catalogo
WHERE CodigoConsulta = 'SR_VENTAS_DIA';
```

---

## 6. PROPUESTA DE ENDPOINTS

### 6.1 Nuevos Endpoints (Fuente: EDARSAHUB SQL)

```python
# /app/backend/modules/consultas_sql/routes.py

# LECTURA
GET    /api/consultas-sql                           # Lista consultas con filtros
GET    /api/consultas-sql/{id}                      # Detalle de consulta
GET    /api/consultas-sql/{id}/parametros           # Parámetros de la consulta
GET    /api/consultas-sql/{id}/servidores           # Servidores compatibles
GET    /api/consultas-sql/{id}/versiones            # Historial de versiones
GET    /api/consultas-sql/{id}/ejecuciones          # Log de ejecuciones

# ESCRITURA
POST   /api/consultas-sql                           # Crear consulta personalizada
PUT    /api/consultas-sql/{id}                      # Actualizar consulta
PATCH  /api/consultas-sql/{id}/estatus              # Activar/Desactivar

# EJECUCIÓN
POST   /api/consultas-sql/{id}/validar              # Validar sintaxis SQL
POST   /api/consultas-sql/{id}/ejecutar             # Ejecutar con parámetros

# PERMISOS (Solo SuperAdmin/Admin)
GET    /api/consultas-sql/{id}/permisos             # Ver permisos
POST   /api/consultas-sql/{id}/permisos             # Asignar permiso
DELETE /api/consultas-sql/{id}/permisos/{permiso_id} # Revocar permiso
```

### 6.2 Compatibilidad Temporal (Wrapper Legacy)

```python
# Mantener endpoints actuales pero redirigir a SQL

GET    /api/catalogo/consultas-rich                 # Lee SQL + fallback Python
POST   /api/catalogo/ejecutar-rich/{consulta_id}    # Ejecuta desde SQL primero
PUT    /api/catalogo/consultas/{consulta_id}        # Escribe a SQL
POST   /api/catalogo/consultas-custom               # Crea en SQL (no MongoDB)
DELETE /api/catalogo/consultas-custom/{consulta_id} # Elimina de SQL
```

---

## 7. PROPUESTA DE UI

### 7.1 Catálogo de Consultas (Modificar existente)

**Archivo:** `/app/frontend/src/pages/CatalogoConsultas.js`

**Cambios propuestos:**
1. Agregar columna "Origen" con badge:
   - `SISTEMA` (verde) - Consulta predefinida
   - `PERSONALIZADA` (azul) - Creada por usuario
   - `LEGACY_PYTHON` (amarillo) - Aún no migrada

2. Agregar filtro por origen

3. Agregar botón "Ver Historial" para consultas con versiones

4. Agregar indicador de permisos del usuario actual

### 7.2 Modal de Ejecución (Sin cambios visuales)

Mantener flujo actual pero backend valida:
- Permiso `PuedeEjecutar` del usuario
- Si `RequiereAutorizacion`, solicitar aprobación

---

## 8. PLAN DE MIGRACIÓN DETALLADO

| Fase | Descripción | Archivos a Crear/Modificar | Riesgo |
|------|-------------|---------------------------|--------|
| 1 | Ejecutar DDL (tablas nuevas) | SQL directo en EDARSAHUB | 🟢 BAJO |
| 2 | Crear repository SQL | `/backend/modules/consultas_sql/repository.py` | 🟢 BAJO |
| 3 | Crear routes nuevos | `/backend/modules/consultas_sql/routes.py` | 🟢 BAJO |
| 4 | Cargar consultas sistema | DML desde `catalogo_consultas.py` | 🟡 MEDIO |
| 5 | Wrapper dual-read | Modificar `/backend/server.py` líneas 12308+ | 🟡 MEDIO |
| 6 | Actualizar frontend | `/frontend/src/pages/CatalogoConsultas.js` | 🟢 BAJO |
| 7 | Deprecar fallback | Eliminar lecturas de MongoDB | 🟢 BAJO |

---

## 9. PRUEBAS DE ACEPTACIÓN

```gherkin
# Escenario 1: Listar consultas
Given un usuario autenticado con rol Administrador
When accede a GET /api/consultas-sql
Then recibe lista de consultas desde EDARSAHUB SQL
And cada consulta tiene campo "source": "EDARSAHUB_SQL"

# Escenario 2: Ejecutar consulta predefinida
Given una consulta SR_VENTAS_DIA migrada a SQL
When el usuario ejecuta POST /api/consultas-sql/{id}/ejecutar con { "fecha": "2026-05-15" }
Then se validan permisos del usuario
And se registra en ConsultasSQL_EjecucionesLog
And se retorna el resultado de la query

# Escenario 3: Crear consulta personalizada
Given un usuario con permiso de creación
When envía POST /api/consultas-sql con nuevo SQL
Then se guarda en ConsultasSQL_Catalogo con EsPersonalizada=1
And se crea versión inicial en ConsultasSQL_Versiones
And NO se guarda en MongoDB

# Escenario 4: Módulos protegidos sin cambio
Given el Tablero Ejecutivo funcionando
When se migran las consultas del catálogo
Then el Tablero Ejecutivo sigue funcionando sin cambios
And Comercial sigue funcionando
And Compras sigue funcionando
And Finanzas sigue funcionando
```

---

## 10. RIESGOS Y MITIGACIONES

| Riesgo | Mitigación |
|--------|------------|
| SQL Injection en parámetros | Usar parámetros tipados y whitelist de nombres |
| Consultas costosas bloquean BD | Implementar timeout y limit obligatorio |
| Permisos mal configurados | Default = solo ver, ejecución explícita |
| Pérdida de consultas al migrar | Backup de `catalogo_consultas.py` antes de deprecar |

---

## 11. RESUMEN

**Tablas Nuevas (6):**
1. `ConsultasSQL_Catalogo`
2. `ConsultasSQL_Parametros`
3. `ConsultasSQL_Servidores`
4. `ConsultasSQL_EjecucionesLog`
5. `ConsultasSQL_Permisos`
6. `ConsultasSQL_Versiones`

**Tablas Existentes (NO tocar):**
- `Sistema_Tipos`
- `Servidores_Conexiones`

**Endpoints Nuevos: 12**
**Endpoints Legacy a Mantener: 5** (con wrapper SQL-first)

---

*Este documento es una PROPUESTA. NO ejecutar DDL ni DML sin autorización explícita.*
