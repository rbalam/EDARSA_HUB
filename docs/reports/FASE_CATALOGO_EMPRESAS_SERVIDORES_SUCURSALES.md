# FASE: Catálogo Empresas / Servidores / Sucursales

**Fecha**: 2026-05-15  
**Estado**: DDL EJECUTADO, DML PENDIENTE AUTORIZACIÓN  
**Rol**: Arquitecto Senior EDARSAHUB / DBA SQL Server

---

## 1. Resumen Ejecutivo

Se completó la creación de la estructura canónica para administrar la relación entre empresas, servidores y sucursales en EDARSAHUB SQL.

### Acciones realizadas:
1. ✅ Diagnóstico de 38 tablas relacionadas
2. ✅ Validación de tablas existentes (Sistema_Empresas, Servidores_Conexiones, etc.)
3. ✅ Creación de `Sistema_Tipos` (catálogo de tipos de sistema)
4. ✅ Creación de `Sistema_EmpresasAlias` (aliases legacy → EmpresaID)
5. ✅ Creación de `Sistema_EmpresasServidores` (relación empresa-servidor-sucursal)
6. ❌ **NO** se ejecutó DML de carga inicial (pendiente autorización)

### Tablas creadas:
| Tabla | Estado | Registros |
|-------|--------|-----------|
| Sistema_Tipos | CREADA (vacía) | 0 |
| Sistema_EmpresasAlias | CREADA (vacía) | 0 |
| Sistema_EmpresasServidores | CREADA (vacía) | 0 |

---

## 2. Objetivo de la Fase

Crear la base canónica en EDARSAHUB SQL para:
- Eliminar dependencia de nombres variables/aliases
- Eliminar LIKE, contains, split o comparaciones textuales
- Resolver empresas, sucursales y servidores por ID
- Establecer EDARSAHUB SQL como fuente autoritativa

---

## 3. Tablas Existentes Detectadas

| Tabla | Propósito | Registros |
|-------|-----------|-----------|
| Sistema_Empresas | Catálogo maestro de empresas | 5 |
| Sistema_Sucursales | Sucursales por empresa | 5 |
| Servidores_Conexiones | Conexiones técnicas | 13 activas |
| Sistema_SucursalServidorMapeo | Mapeo sucursal-servidor | 5 |
| Sistema_ServidorSucursalesConfig | Config sucursales por servidor | 7 |
| Unidades_Negocio | Legacy unidades negocio | 5 |
| Sistema_EmpresasMongoMap | Mapeo MongoDB | 5 |
| Usuario_EmpresasAsignacion | Permisos usuario-empresa | - |

---

## 4. Diagnóstico de Sistema_Empresas

### Estructura:
```
EmpresaID           int           NOT NULL (PK)
CodigoEmpresa       varchar(20)   NOT NULL (UNIQUE)
NombreEmpresa       nvarchar(100) NOT NULL
NombreComercial     nvarchar(100) NULL
RFC                 varchar(13)   NULL
Activo              bit           NOT NULL
FechaAlta           datetime2     NOT NULL
FechaModificacion   datetime2     NULL
CreatedBy           varchar(100)  NULL
UpdatedBy           varchar(100)  NULL
```

### Registros actuales:
| EmpresaID | CodigoEmpresa | NombreEmpresa | Activo |
|-----------|---------------|---------------|--------|
| 1 | ORIGEN | ORIGEN | ✅ |
| 2 | 130QRO | 130 QRO | ✅ |
| 3 | CIENFUEGOS | CIENFUEGOS | ✅ |
| 4 | ESTELAR | LA ESTELAR | ✅ |
| 5 | 130MID | 130 MID | ✅ |

### Estado: ✅ CORRECTO
Las 5 unidades canónicas existen. No requiere modificación.

---

## 5. Diagnóstico de Servidores_Conexiones

### Estructura (columnas principales):
```
id                  uniqueidentifier NOT NULL (PK)
nombre              nvarchar(100)    NOT NULL
system_type         nvarchar(50)     NOT NULL
host                nvarchar(255)    NULL
port                int              NULL
database_name       nvarchar(100)    NULL
activo              bit              NULL
EmpresaID           int              NULL
```

### Servidores activos relevantes:
| Nombre | Tipo | Database | Uso |
|--------|------|----------|-----|
| 130° MERIDA | SoftRestaurant | softrestaurant10 | 130MID |
| CIENFUEGOS | SoftRestaurant | softrestaurant95pro | CIENFUEGOS |
| LA ESTELAR | SoftRestaurant | softrestaurant12 | ESTELAR |
| ManagmentPro | MPRO | CENTRAL2020 | ORIGEN + 130QRO |
| ORIGEN LOCAL | MPRO | ORIGEN | API Local ORIGEN |
| 130° QRO LOCAL | MPRO | QUERETARO | API Local 130QRO |

### Estado: ✅ CORRECTO
Servidores definidos correctamente. NO se duplicará esta tabla.

---

## 6. Diagnóstico de Sistema_Tipos (Equivalente)

No existía tabla equivalente.

### Tabla creada: `Sistema_Tipos`

```sql
CREATE TABLE Sistema_Tipos (
    SistemaTipoID INT IDENTITY(1,1) PRIMARY KEY,
    CodigoSistema VARCHAR(50) NOT NULL UNIQUE,
    NombreSistema NVARCHAR(100) NOT NULL,
    Descripcion NVARCHAR(500) NULL,
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME2 NOT NULL DEFAULT GETDATE(),
    FechaActualizacion DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL,
    UpdatedBy VARCHAR(100) NULL
);
```

### Valores propuestos (DML pendiente):
| CodigoSistema | NombreSistema |
|---------------|---------------|
| SOFTRESTAURANT | SoftRestaurant |
| MPRO | ManagementPro |
| API_LOCAL | API Local |
| EDARSAHUB_SQL | EDARSAHUB SQL Server |
| OTRO | Otro sistema |

---

## 7. Diagnóstico de Roles de Conexión

No existía tabla de roles. Se implementó mediante **CHECK CONSTRAINT** en `Sistema_EmpresasServidores`.

### Roles de conexión permitidos:
| Código | Descripción |
|--------|-------------|
| PRINCIPAL_SQL | Conexión SQL principal |
| VENTAS_DIA_API_LOCAL | API local para ventas del día |
| SINCRONIZACION_ANALITICA | Sincronización analítica |
| SINCRONIZACION_OPERATIVA | Sincronización operativa |
| HISTORICO | Consulta histórica |
| RESPALDO | Servidor de respaldo |
| CONSULTA_MANUAL | Consulta manual ad-hoc |

---

## 8. Tablas Creadas

### 8.1 Sistema_Tipos
```sql
-- Catálogo de tipos de sistema origen
CREATE TABLE Sistema_Tipos (
    SistemaTipoID INT IDENTITY(1,1) PRIMARY KEY,
    CodigoSistema VARCHAR(50) NOT NULL,
    NombreSistema NVARCHAR(100) NOT NULL,
    Descripcion NVARCHAR(500) NULL,
    Activo BIT NOT NULL DEFAULT 1,
    ...
    CONSTRAINT UQ_Sistema_Tipos_Codigo UNIQUE (CodigoSistema)
);
```

### 8.2 Sistema_EmpresasAlias
```sql
-- Aliases legacy para resolver nombres hacia EmpresaID
CREATE TABLE Sistema_EmpresasAlias (
    EmpresaAliasID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL,
    Alias NVARCHAR(200) NOT NULL,
    AliasNormalizado NVARCHAR(200) NOT NULL,
    OrigenAlias VARCHAR(50) NULL,
    Activo BIT NOT NULL DEFAULT 1,
    ...
    CONSTRAINT FK_EmpresasAlias_Empresa FOREIGN KEY (EmpresaID) 
        REFERENCES Sistema_Empresas(EmpresaID)
);

-- Índice único filtrado para evitar aliases duplicados activos
CREATE UNIQUE INDEX IX_EmpresasAlias_Normalizado_Activo 
    ON Sistema_EmpresasAlias(AliasNormalizado) WHERE Activo = 1;
```

### 8.3 Sistema_EmpresasServidores
```sql
-- Relación empresa-servidor con rol de conexión
CREATE TABLE Sistema_EmpresasServidores (
    EmpresaServidorID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    SistemaTipoID INT NULL,
    RolConexion VARCHAR(50) NOT NULL,
    NumeroSucursalSistema INT NULL,
    CodigoSucursalSistema VARCHAR(20) NULL,
    NombreSucursalSistema NVARCHAR(100) NULL,
    Prioridad INT NOT NULL DEFAULT 1,
    EsPrincipal BIT NOT NULL DEFAULT 0,
    Activo BIT NOT NULL DEFAULT 1,
    ...
    CONSTRAINT FK_EmpresasServidores_Empresa FOREIGN KEY (EmpresaID) 
        REFERENCES Sistema_Empresas(EmpresaID),
    CONSTRAINT FK_EmpresasServidores_Servidor FOREIGN KEY (ServidorID) 
        REFERENCES Servidores_Conexiones(id)
);
```

---

## 9. DDL Ejecutado

✅ Sistema_Tipos creada  
✅ Sistema_EmpresasAlias creada  
✅ Sistema_EmpresasServidores creada  
✅ Foreign Keys creadas  
✅ Índices creados  

---

## 10. Índices y Constraints Creados

### Sistema_Tipos:
- PK: SistemaTipoID
- UQ: CodigoSistema
- IX: Activo

### Sistema_EmpresasAlias:
- PK: EmpresaAliasID
- FK: EmpresaID → Sistema_Empresas
- IX UNIQUE FILTERED: AliasNormalizado (WHERE Activo = 1)
- IX: EmpresaID, Activo

### Sistema_EmpresasServidores:
- PK: EmpresaServidorID
- FK: EmpresaID → Sistema_Empresas
- FK: ServidorID → Servidores_Conexiones
- IX: EmpresaID, Activo
- IX: ServidorID, Activo

---

## 11. Script DML Propuesto (NO EJECUTADO)

### 11.1 Carga Sistema_Tipos
```sql
-- DML PROPUESTO - NO EJECUTAR SIN AUTORIZACIÓN
INSERT INTO Sistema_Tipos (CodigoSistema, NombreSistema, Descripcion, CreatedBy)
VALUES 
    ('SOFTRESTAURANT', 'SoftRestaurant', 'Sistema POS SoftRestaurant', 'FASE_CATALOGO'),
    ('MPRO', 'ManagementPro', 'Sistema ManagementPro', 'FASE_CATALOGO'),
    ('API_LOCAL', 'API Local', 'API local para sincronización en tiempo real', 'FASE_CATALOGO'),
    ('EDARSAHUB_SQL', 'EDARSAHUB SQL Server', 'Base de datos centralizada EDARSAHUB', 'FASE_CATALOGO'),
    ('OTRO', 'Otro', 'Otros sistemas no clasificados', 'FASE_CATALOGO');
```

### 11.2 Carga Sistema_EmpresasAlias
```sql
-- DML PROPUESTO - NO EJECUTAR SIN AUTORIZACIÓN
-- ORIGEN (EmpresaID=1)
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, CreatedBy)
VALUES 
    (1, 'ORIGEN', 'ORIGEN', 'CANONICO', 'FASE_CATALOGO'),
    (1, 'Origen', 'ORIGEN', 'LEGACY', 'FASE_CATALOGO'),
    (1, 'origen', 'ORIGEN', 'LEGACY', 'FASE_CATALOGO');

-- 130QRO (EmpresaID=2)
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, CreatedBy)
VALUES 
    (2, '130QRO', '130QRO', 'CANONICO', 'FASE_CATALOGO'),
    (2, '130 QRO', '130 QRO', 'LEGACY', 'FASE_CATALOGO'),
    (2, '130-QRO', '130 QRO', 'LEGACY', 'FASE_CATALOGO'),
    (2, '130° QRO', '130 QRO', 'LEGACY', 'FASE_CATALOGO'),
    (2, '130 QUERETARO', '130 QUERETARO', 'LEGACY', 'FASE_CATALOGO'),
    (2, '130° QUERETARO', '130 QUERETARO', 'LEGACY', 'FASE_CATALOGO'),
    (2, '130 Grados Querétaro', '130 GRADOS QUERETARO', 'LEGACY', 'FASE_CATALOGO'),
    (2, 'QUERETARO', 'QUERETARO', 'LEGACY', 'FASE_CATALOGO'),
    (2, 'QRO', 'QRO', 'LEGACY', 'FASE_CATALOGO');

-- CIENFUEGOS (EmpresaID=3)
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, CreatedBy)
VALUES 
    (3, 'CIENFUEGOS', 'CIENFUEGOS', 'CANONICO', 'FASE_CATALOGO'),
    (3, 'Cienfuegos', 'CIENFUEGOS', 'LEGACY', 'FASE_CATALOGO'),
    (3, 'CF', 'CF', 'LEGACY', 'FASE_CATALOGO');

-- ESTELAR (EmpresaID=4)
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, CreatedBy)
VALUES 
    (4, 'ESTELAR', 'ESTELAR', 'CANONICO', 'FASE_CATALOGO'),
    (4, 'LA ESTELAR', 'LA ESTELAR', 'LEGACY', 'FASE_CATALOGO'),
    (4, 'LA-ESTELAR', 'LA ESTELAR', 'LEGACY', 'FASE_CATALOGO'),
    (4, 'La Estelar', 'LA ESTELAR', 'LEGACY', 'FASE_CATALOGO');

-- 130MID (EmpresaID=5)
INSERT INTO Sistema_EmpresasAlias (EmpresaID, Alias, AliasNormalizado, OrigenAlias, CreatedBy)
VALUES 
    (5, '130MID', '130MID', 'CANONICO', 'FASE_CATALOGO'),
    (5, '130 MID', '130 MID', 'LEGACY', 'FASE_CATALOGO'),
    (5, '130-MER', '130 MER', 'LEGACY', 'FASE_CATALOGO'),
    (5, '130 MER', '130 MER', 'LEGACY', 'FASE_CATALOGO'),
    (5, '130 MERIDA', '130 MERIDA', 'LEGACY', 'FASE_CATALOGO'),
    (5, '130 MÉRIDA', '130 MERIDA', 'LEGACY', 'FASE_CATALOGO'),
    (5, '130° MERIDA', '130 MERIDA', 'LEGACY', 'FASE_CATALOGO'),
    (5, '130° MÉRIDA', '130 MERIDA', 'LEGACY', 'FASE_CATALOGO'),
    (5, '130 Grados Mérida', '130 GRADOS MERIDA', 'LEGACY', 'FASE_CATALOGO');
```

### 11.3 Carga Sistema_EmpresasServidores
```sql
-- DML PROPUESTO - NO EJECUTAR SIN AUTORIZACIÓN
-- Requiere identificar ServidorID correctos de Servidores_Conexiones

-- ORIGEN: MPRO Principal (sucursal 23)
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, EsPrincipal, CreatedBy)
VALUES 
    (1, '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'PRINCIPAL_SQL', 23, '0023', 
     'ORIGEN', 1, 'FASE_CATALOGO');

-- ORIGEN: API Local para ventas del día
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, EsPrincipal, CreatedBy)
VALUES 
    (1, '(ID_SERVIDOR_ORIGEN_LOCAL)', 'VENTAS_DIA_API_LOCAL', 23, '0023', 
     'ORIGEN', 0, 'FASE_CATALOGO');

-- 130QRO: MPRO Principal (sucursal 21)
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, CodigoSucursalSistema, 
     NombreSucursalSistema, EsPrincipal, CreatedBy)
VALUES 
    (2, '1b230a06-ffaf-4c70-bd27-b1be3579dea6', 'PRINCIPAL_SQL', 21, '0021', 
     '130 QUERETARO', 1, 'FASE_CATALOGO');

-- CIENFUEGOS: SoftRestaurant Principal
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, 
     NombreSucursalSistema, EsPrincipal, CreatedBy)
VALUES 
    (3, '6d053c22-523e-48c0-b72b-96081e2d781b', 'PRINCIPAL_SQL', NULL, 
     'CIENFUEGOS', 1, 'FASE_CATALOGO');

-- ESTELAR: SoftRestaurant Principal
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, 
     NombreSucursalSistema, EsPrincipal, CreatedBy)
VALUES 
    (4, 'a5ff0e25-f029-43db-b634-d4ac814c904f', 'PRINCIPAL_SQL', NULL, 
     'LA ESTELAR', 1, 'FASE_CATALOGO');

-- 130MID: SoftRestaurant Principal
INSERT INTO Sistema_EmpresasServidores 
    (EmpresaID, ServidorID, RolConexion, NumeroSucursalSistema, 
     NombreSucursalSistema, EsPrincipal, CreatedBy)
VALUES 
    (5, 'a5547321-1139-4d2b-9d53-182ca737b6b6', 'PRINCIPAL_SQL', NULL, 
     '130 MERIDA', 1, 'FASE_CATALOGO');
```

---

## 12. Unidades Canónicas Propuestas

| # | CodigoEmpresa | NombreComercial | Sistema |
|---|---------------|-----------------|---------|
| 1 | ORIGEN | Origen | MPRO |
| 2 | 130QRO | 130 Grados Querétaro | MPRO |
| 3 | CIENFUEGOS | Cienfuegos | SoftRestaurant |
| 4 | ESTELAR | La Estelar | SoftRestaurant |
| 5 | 130MID | 130 Grados Mérida | SoftRestaurant |

---

## 13. Aliases Propuestos por Unidad

### ORIGEN (EmpresaID=1)
- ORIGEN (canónico)
- Origen
- origen

### 130QRO (EmpresaID=2)
- 130QRO (canónico)
- 130 QRO, 130-QRO, 130° QRO
- 130 QUERETARO, 130° QUERETARO
- 130 Grados Querétaro
- QUERETARO, QRO

### CIENFUEGOS (EmpresaID=3)
- CIENFUEGOS (canónico)
- Cienfuegos
- CF

### ESTELAR (EmpresaID=4)
- ESTELAR (canónico)
- LA ESTELAR, LA-ESTELAR
- La Estelar

### 130MID (EmpresaID=5)
- 130MID (canónico)
- 130 MID, 130-MER, 130 MER
- 130 MERIDA, 130 MÉRIDA, 130° MERIDA, 130° MÉRIDA
- 130 Grados Mérida

---

## 14. Relaciones Empresa-Servidor Propuestas

| Empresa | Servidor | Rol | SucursalSistema |
|---------|----------|-----|-----------------|
| ORIGEN | ManagmentPro | PRINCIPAL_SQL | 23 |
| ORIGEN | ORIGEN LOCAL | VENTAS_DIA_API_LOCAL | 23 |
| 130QRO | ManagmentPro | PRINCIPAL_SQL | 21 |
| 130QRO | 130° QRO LOCAL | VENTAS_DIA_API_LOCAL | 21 |
| CIENFUEGOS | CIENFUEGOS | PRINCIPAL_SQL | NULL |
| ESTELAR | LA ESTELAR | PRINCIPAL_SQL | NULL |
| 130MID | 130° MERIDA | PRINCIPAL_SQL | NULL |

---

## 15. Mapeo Especial MPRO

### Servidor compartido:
`ManagmentPro` (ID: 1b230a06-ffaf-4c70-bd27-b1be3579dea6)
- Database: CENTRAL2020
- Host: 54.39.104.176

### Diferenciación por NumeroSucursalSistema:
| Empresa | NumeroSucursalSistema | CodigoSucursalSistema |
|---------|----------------------|----------------------|
| ORIGEN | 23 | 0023 |
| 130QRO | 21 | 0021 |

### APIs Locales:
| Empresa | Servidor API | Host | Port |
|---------|--------------|------|------|
| ORIGEN | ORIGEN LOCAL | 54.39.104.176 | 8000 |
| 130QRO | 130° QRO LOCAL | 54.39.104.176 | 8001 |

---

## 16. Mapeo Especial SoftRestaurant

### Servidor dedicado por unidad:
| Empresa | Servidor | NumeroSucursalSistema |
|---------|----------|----------------------|
| CIENFUEGOS | CIENFUEGOS | NULL |
| ESTELAR | LA ESTELAR | NULL |
| 130MID | 130° MERIDA | NULL |

### Nota:
SoftRestaurant normalmente tiene un servidor por unidad de negocio, sin necesidad de NumeroSucursalSistema para diferenciar.

---

## 17. Reglas de Normalización

### Función conceptual: `NormalizarAlias(texto)`

```
1. Convertir a MAYÚSCULAS
2. Quitar acentos: Á→A, É→E, Í→I, Ó→O, Ú→U, Ñ→N
3. Quitar símbolo °
4. Reemplazar - y _ por espacio
5. Quitar puntos y comas
6. Normalizar espacios múltiples
7. TRIM
```

### Ejemplos:
| Entrada | Salida |
|---------|--------|
| 130 Grados Mérida | 130 GRADOS MERIDA |
| 130° MÉRIDA | 130 MERIDA |
| 130_mid | 130 MID |
| 130-MER | 130 MER |
| LA-ESTELAR | LA ESTELAR |
| Querétaro | QUERETARO |

---

## 18. Diseño Futuro de EmpresaResolver

### Funciones propuestas (NO IMPLEMENTADAS):

```python
# Normalización
def normalize_alias(texto: str) -> str
    """Normaliza un alias para búsqueda"""

# Resolución
def resolve_empresa_by_alias(alias: str) -> int
    """Resuelve alias → EmpresaID usando Sistema_EmpresasAlias"""

def resolve_empresa_by_id(empresa_id: int) -> dict
    """Obtiene datos de empresa por EmpresaID"""

# Conexiones
def get_empresa_connections(empresa_id: int) -> list
    """Obtiene todas las conexiones de una empresa"""

def get_connection_for_role(empresa_id: int, rol: str) -> dict
    """Obtiene conexión específica por rol"""

# Contexto
def get_system_branch_context(empresa_id: int, rol: str) -> dict
    """Obtiene contexto completo: servidor, sucursal, sistema"""

# Validación
def validate_no_ambiguous_alias(alias: str) -> bool
    """Valida que un alias no sea ambiguo"""
```

### Flujo de resolución:
```
Entrada: "130° MÉRIDA"
    ↓
normalize_alias() → "130 MERIDA"
    ↓
SELECT EmpresaID FROM Sistema_EmpresasAlias 
WHERE AliasNormalizado = '130 MERIDA' AND Activo = 1
    ↓
EmpresaID = 5 (130MID)
    ↓
get_connection_for_role(5, 'PRINCIPAL_SQL')
    ↓
ServidorID, NumeroSucursalSistema, etc.
```

---

## 19. Validaciones Ejecutadas

| Validación | Resultado |
|------------|-----------|
| Sistema_Tipos creada | ✅ |
| Sistema_EmpresasAlias creada | ✅ |
| Sistema_EmpresasServidores creada | ✅ |
| FK a Sistema_Empresas | ✅ |
| FK a Servidores_Conexiones | ✅ |
| Índices creados | ✅ |
| Sistema_Empresas no modificada | ✅ |
| Servidores_Conexiones no duplicada | ✅ |
| DML no ejecutado | ✅ |

---

## 20. Riesgos Pendientes

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Aliases duplicados en normalización | Medio | Índice único filtrado |
| ServidorID de APIs locales no confirmado | Bajo | Verificar antes de DML |
| Inconsistencia legacy en tablas operativas | Medio | Migración gradual |
| Dependencia de jobs en aliases textuales | Alto | Implementar EmpresaResolver |

---

## 21. Siguiente Fase Recomendada

1. **AUTORIZAR** DML de carga inicial
2. **CARGAR** Sistema_Tipos
3. **CARGAR** Sistema_EmpresasAlias
4. **CARGAR** Sistema_EmpresasServidores
5. **IMPLEMENTAR** EmpresaResolver en backend
6. **MIGRAR** gradualmente jobs y adapters

---

## 22. Confirmaciones Finales

| Confirmación | Estado |
|-------------|--------|
| No se modificó frontend | ✅ |
| No se modificó Tablero Ejecutivo | ✅ |
| No se modificó Comercial | ✅ |
| No se modificaron jobs | ✅ |
| No se ejecutó DML | ✅ |
| No se reactivó LIVE | ✅ |
| No se usaron datos mock | ✅ |
| EDARSAHUB SQL queda como base canónica | ✅ |
| Sistema_Empresas no modificada | ✅ |
| Servidores_Conexiones no duplicada | ✅ |

---

## Apéndice: IDs de Servidores Identificados

```sql
-- Servidores para mapeo empresa-servidor
SELECT id, nombre, system_type FROM Servidores_Conexiones WHERE activo = 1;

-- Resultado:
-- a5547321-1139-4d2b-9d53-182ca737b6b6 | 130° MERIDA | SoftRestaurant
-- 6d053c22-523e-48c0-b72b-96081e2d781b | CIENFUEGOS | SoftRestaurant
-- a5ff0e25-f029-43db-b634-d4ac814c904f | LA ESTELAR | SoftRestaurant
-- 1b230a06-ffaf-4c70-bd27-b1be3579dea6 | ManagmentPro | MPRO
-- (pendiente) | ORIGEN LOCAL | MPRO/API
-- (pendiente) | 130° QRO LOCAL | MPRO/API
```

---

**FIN DEL REPORTE**

Esperando autorización para ejecutar DML de carga inicial.
