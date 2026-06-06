# FASE A1.7 — DDL BASE ORGANIZACIONAL AUTH/RBAC

**Documento:** Registro de Ejecución DDL  
**Fecha:** 8 de Mayo 2026, 19:57 UTC  
**Estado:** ✅ EJECUTADO EXITOSAMENTE  
**Versión:** 1.0

---

## 1. RESUMEN

Se ejecutó exitosamente el DDL para crear la estructura base organizacional de Auth/RBAC en EDARSAHUB:

| Objeto | Tipo | Estado | Registros |
|--------|------|--------|-----------|
| `Sistema_Empresas` | Tabla | ✅ CREADA | 0 |
| `Usuario_EmpresasAsignacion` | Tabla | ✅ CREADA | 0 |
| `Usuario_Roles.NivelJerarquia` | Columna | ✅ AGREGADA | 5 roles con valor 0 |

**⚠️ NO SE INSERTARON DATOS** — Las tablas están vacías según lo autorizado.

---

## 2. CONFIRMACIÓN DE AUTORIZACIÓN

| Autorización | Estado |
|--------------|--------|
| Crear `Sistema_Empresas` | ✅ AUTORIZADO Y EJECUTADO |
| Crear `Usuario_EmpresasAsignacion` | ✅ AUTORIZADO Y EJECUTADO |
| Agregar `NivelJerarquia` a `Usuario_Roles` | ✅ AUTORIZADO Y EJECUTADO |
| Insertar datos de empresas | ❌ NO AUTORIZADO |
| Insertar asignaciones de usuarios | ❌ NO AUTORIZADO |
| Modificar código backend | ❌ NO AUTORIZADO |
| Modificar login/JWT | ❌ NO AUTORIZADO |

---

## 3. VALIDACIÓN PRE-DDL

Antes de ejecutar el DDL, se confirmó:

| Validación | Resultado |
|------------|-----------|
| ¿Existe tabla equivalente a Empresas? | ❌ NO - OK para crear |
| ¿Existe `Usuario_EmpresasAsignacion`? | ❌ NO - OK para crear |
| ¿Existe columna `NivelJerarquia`? | ❌ NO - OK para agregar |
| Patrón de `Usuario_RolesAsignacion` | ✅ Identificado y seguido |
| Patrón de `Global_Cat_Bancos` | ✅ Identificado y seguido |
| FK a `Usuario_Catalogo.UsuarioID` | ✅ Verificada (INT) |

---

## 4. SCRIPT DDL EJECUTADO

### 4.1 Sistema_Empresas

```sql
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sistema_Empresas')
BEGIN
    CREATE TABLE Sistema_Empresas (
        EmpresaID           INT IDENTITY(1,1) NOT NULL,
        CodigoEmpresa       VARCHAR(20) NOT NULL,
        NombreEmpresa       NVARCHAR(100) NOT NULL,
        NombreComercial     NVARCHAR(100) NULL,
        RFC                 VARCHAR(13) NULL,
        Activo              BIT NOT NULL DEFAULT 1,
        FechaAlta           DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        FechaModificacion   DATETIME2 NULL,
        CreatedBy           VARCHAR(100) NULL,
        UpdatedBy           VARCHAR(100) NULL,
        
        CONSTRAINT PK_Sistema_Empresas PRIMARY KEY (EmpresaID),
        CONSTRAINT UQ_Sistema_Empresas_Codigo UNIQUE (CodigoEmpresa)
    );
    
    CREATE INDEX IX_Sistema_Empresas_Codigo ON Sistema_Empresas(CodigoEmpresa);
    CREATE INDEX IX_Sistema_Empresas_Activo ON Sistema_Empresas(Activo);
END
```

### 4.2 Usuario_EmpresasAsignacion

```sql
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Usuario_EmpresasAsignacion')
BEGIN
    CREATE TABLE Usuario_EmpresasAsignacion (
        UsuarioEmpresaAsignacionID  BIGINT IDENTITY(1,1) NOT NULL,
        UsuarioID                   INT NOT NULL,
        EmpresaID                   INT NOT NULL,
        EsPrincipal                 BIT NOT NULL DEFAULT 0,
        FechaInicio                 DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        FechaFin                    DATETIME2 NULL,
        Activo                      BIT NOT NULL DEFAULT 1,
        CreatedAt                   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        CreatedBy                   VARCHAR(100) NULL,
        UpdatedAt                   DATETIME2 NULL,
        UpdatedBy                   VARCHAR(100) NULL,
        
        CONSTRAINT PK_Usuario_EmpresasAsignacion PRIMARY KEY (UsuarioEmpresaAsignacionID),
        CONSTRAINT FK_UsuarioEmpresas_Usuario FOREIGN KEY (UsuarioID) REFERENCES Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_UsuarioEmpresas_Empresa FOREIGN KEY (EmpresaID) REFERENCES Sistema_Empresas(EmpresaID),
        CONSTRAINT UQ_UsuarioEmpresas_Activo UNIQUE (UsuarioID, EmpresaID, Activo)
    );
    
    CREATE INDEX IX_UsuarioEmpresasAsignacion_Usuario ON Usuario_EmpresasAsignacion(UsuarioID);
    CREATE INDEX IX_UsuarioEmpresasAsignacion_Empresa ON Usuario_EmpresasAsignacion(EmpresaID);
    CREATE INDEX IX_UsuarioEmpresasAsignacion_Activo ON Usuario_EmpresasAsignacion(Activo) WHERE Activo = 1;
END
```

### 4.3 NivelJerarquia en Usuario_Roles

```sql
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'Usuario_Roles' AND COLUMN_NAME = 'NivelJerarquia')
BEGIN
    ALTER TABLE Usuario_Roles ADD 
        NivelJerarquia INT NOT NULL DEFAULT 0;
END
```

---

## 5. SCRIPT ROLLBACK GENERADO

⚠️ **EJECUTAR SOLO EN CASO DE EMERGENCIA**

```sql
-- ROLLBACK FASE A1.7
-- Ejecutar en orden inverso

-- 1. Eliminar Usuario_EmpresasAsignacion (elimina FK primero)
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Usuario_EmpresasAsignacion')
BEGIN
    DROP TABLE Usuario_EmpresasAsignacion;
    PRINT 'Usuario_EmpresasAsignacion eliminada';
END

-- 2. Eliminar Sistema_Empresas
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sistema_Empresas')
BEGIN
    DROP TABLE Sistema_Empresas;
    PRINT 'Sistema_Empresas eliminada';
END

-- 3. Eliminar NivelJerarquia de Usuario_Roles
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
           WHERE TABLE_NAME = 'Usuario_Roles' AND COLUMN_NAME = 'NivelJerarquia')
BEGIN
    ALTER TABLE Usuario_Roles DROP COLUMN NivelJerarquia;
    PRINT 'NivelJerarquia eliminado de Usuario_Roles';
END
```

---

## 6. RESULTADO DE EJECUCIÓN

| Hora (UTC) | Acción | Resultado |
|------------|--------|-----------|
| 19:57:18 | CREATE TABLE Sistema_Empresas | ✅ Éxito |
| 19:57:18 | CREATE TABLE Usuario_EmpresasAsignacion | ✅ Éxito |
| 19:57:18 | ALTER TABLE Usuario_Roles ADD NivelJerarquia | ✅ Éxito |

---

## 7. VALIDACIÓN POST-DDL

### 7.1 Sistema_Empresas

| Aspecto | Estado |
|---------|--------|
| Tabla existe | ✅ |
| Columnas correctas | ✅ 10 columnas |
| PK `EmpresaID` | ✅ INT IDENTITY |
| UQ `CodigoEmpresa` | ✅ |
| Índices | ✅ 4 índices |
| Registros | 0 (correcto - no se insertaron) |

### 7.2 Usuario_EmpresasAsignacion

| Aspecto | Estado |
|---------|--------|
| Tabla existe | ✅ |
| Columnas correctas | ✅ 11 columnas |
| PK `UsuarioEmpresaAsignacionID` | ✅ BIGINT IDENTITY |
| FK a Usuario_Catalogo | ✅ |
| FK a Sistema_Empresas | ✅ |
| UQ `UsuarioID + EmpresaID + Activo` | ✅ |
| Índices | ✅ 5 índices |
| Registros | 0 (correcto - no se insertaron) |

### 7.3 Usuario_Roles.NivelJerarquia

| Aspecto | Estado |
|---------|--------|
| Columna existe | ✅ |
| Tipo | INT NOT NULL |
| Default | 0 |
| Valores actuales | Todos los roles tienen 0 |

---

## 8. TABLAS CREADAS

| # | Tabla | Descripción | Sigue Patrón |
|---|-------|-------------|--------------|
| 1 | `Sistema_Empresas` | Catálogo de empresas del sistema | ✅ Sigue `Global_Cat_Bancos` |
| 2 | `Usuario_EmpresasAsignacion` | Relación N:M usuario-empresa | ✅ Sigue `Usuario_RolesAsignacion` |

---

## 9. COLUMNAS CREADAS

### Sistema_Empresas (10 columnas)

| Columna | Tipo | Nullable | Default |
|---------|------|----------|---------|
| `EmpresaID` | INT IDENTITY | NOT NULL | - |
| `CodigoEmpresa` | VARCHAR(20) | NOT NULL | - |
| `NombreEmpresa` | NVARCHAR(100) | NOT NULL | - |
| `NombreComercial` | NVARCHAR(100) | NULL | - |
| `RFC` | VARCHAR(13) | NULL | - |
| `Activo` | BIT | NOT NULL | 1 |
| `FechaAlta` | DATETIME2 | NOT NULL | GETUTCDATE() |
| `FechaModificacion` | DATETIME2 | NULL | - |
| `CreatedBy` | VARCHAR(100) | NULL | - |
| `UpdatedBy` | VARCHAR(100) | NULL | - |

### Usuario_EmpresasAsignacion (11 columnas)

| Columna | Tipo | Nullable | Default |
|---------|------|----------|---------|
| `UsuarioEmpresaAsignacionID` | BIGINT IDENTITY | NOT NULL | - |
| `UsuarioID` | INT | NOT NULL | - |
| `EmpresaID` | INT | NOT NULL | - |
| `EsPrincipal` | BIT | NOT NULL | 0 |
| `FechaInicio` | DATETIME2 | NOT NULL | GETUTCDATE() |
| `FechaFin` | DATETIME2 | NULL | - |
| `Activo` | BIT | NOT NULL | 1 |
| `CreatedAt` | DATETIME2 | NOT NULL | GETUTCDATE() |
| `CreatedBy` | VARCHAR(100) | NULL | - |
| `UpdatedAt` | DATETIME2 | NULL | - |
| `UpdatedBy` | VARCHAR(100) | NULL | - |

### Usuario_Roles (1 columna agregada)

| Columna | Tipo | Nullable | Default |
|---------|------|----------|---------|
| `NivelJerarquia` | INT | NOT NULL | 0 |

---

## 10. CONSTRAINTS / PK / FK / ÍNDICES

### Sistema_Empresas

| Tipo | Nombre | Descripción |
|------|--------|-------------|
| PK | `PK_Sistema_Empresas` | `EmpresaID` |
| UQ | `UQ_Sistema_Empresas_Codigo` | `CodigoEmpresa` |
| IX | `IX_Sistema_Empresas_Codigo` | Índice en `CodigoEmpresa` |
| IX | `IX_Sistema_Empresas_Activo` | Índice en `Activo` |

### Usuario_EmpresasAsignacion

| Tipo | Nombre | Descripción |
|------|--------|-------------|
| PK | `PK_Usuario_EmpresasAsignacion` | `UsuarioEmpresaAsignacionID` |
| FK | `FK_UsuarioEmpresas_Usuario` | → `Usuario_Catalogo(UsuarioID)` |
| FK | `FK_UsuarioEmpresas_Empresa` | → `Sistema_Empresas(EmpresaID)` |
| UQ | `UQ_UsuarioEmpresas_Activo` | `UsuarioID + EmpresaID + Activo` |
| IX | `IX_UsuarioEmpresasAsignacion_Usuario` | Índice en `UsuarioID` |
| IX | `IX_UsuarioEmpresasAsignacion_Empresa` | Índice en `EmpresaID` |
| IX | `IX_UsuarioEmpresasAsignacion_Activo` | Índice filtrado `WHERE Activo = 1` |

---

## 11. RIESGOS REMANENTES

| Riesgo | Severidad | Estado |
|--------|-----------|--------|
| Tablas vacías - no hay datos para usar | P1 | Pendiente poblar |
| `NivelJerarquia` = 0 para todos los roles | P2 | Pendiente actualizar valores |
| MongoDB sigue siendo fuente principal | P1 | Correcto por ahora |
| FK a Usuario_Catalogo vacía (0 usuarios) | P1 | Pendiente migrar usuarios primero |

---

## 12. SIGUIENTE FASE PROPUESTA

### FASE A2 — POBLAR DATOS DE EMPRESAS

**Objetivo:** Insertar en `Sistema_Empresas` los datos de MongoDB `empresas`.

**Script propuesto (NO EJECUTAR SIN AUTORIZACIÓN):**

```sql
-- Insertar empresas desde MongoDB
INSERT INTO Sistema_Empresas (CodigoEmpresa, NombreEmpresa, Activo, CreatedBy)
VALUES 
    ('ORIGEN', 'ORIGEN', 1, 'MIGRACION'),
    ('130QRO', '130 QRO', 1, 'MIGRACION'),
    ('CIENFUEGOS', 'CIENFUEGOS', 1, 'MIGRACION'),
    ('ESTELAR', 'LA ESTELAR', 1, 'MIGRACION'),
    ('130MID', '130 MID', 1, 'MIGRACION');
```

### FASE A3 — ACTUALIZAR NivelJerarquia

**Objetivo:** Asignar valores de nivel a los roles según MongoDB `rbac_roles`.

**Script propuesto (NO EJECUTAR SIN AUTORIZACIÓN):**

```sql
-- Actualizar NivelJerarquia según rbac_roles de MongoDB
UPDATE Usuario_Roles SET NivelJerarquia = 100 WHERE CodigoRol = 'ADMIN';
UPDATE Usuario_Roles SET NivelJerarquia = 80 WHERE CodigoRol = 'GERENCIA';
-- etc.
```

---

## 13. AUTORIZACIÓN REQUERIDA PARA POBLAR DATOS

### Checklist de Siguiente Fase

| Paso | Descripción | Estado |
|------|-------------|--------|
| 1 | ✅ DDL Base ejecutado | COMPLETADO |
| 2 | ⬜ Poblar `Sistema_Empresas` con 5 empresas | **PENDIENTE AUTORIZACIÓN** |
| 3 | ⬜ Crear tabla de equivalencias UUID | **PENDIENTE AUTORIZACIÓN** |
| 4 | ⬜ Actualizar `NivelJerarquia` en roles | **PENDIENTE AUTORIZACIÓN** |
| 5 | ⬜ Poblar `Usuario_EmpresasAsignacion` | **PENDIENTE AUTORIZACIÓN** |
| 6 | ⬜ Modificar código para leer EDARSAHUB | **NO AUTORIZADO** |

---

## CONFIRMACIONES EXPLÍCITAS

| Confirmación | Estado |
|--------------|--------|
| ✅ `Sistema_Empresas` fue creada correctamente | CONFIRMADO |
| ✅ `Usuario_EmpresasAsignacion` fue creada correctamente | CONFIRMADO |
| ✅ `NivelJerarquia` fue agregado a `Usuario_Roles` | CONFIRMADO |
| ✅ NO se migraron datos | CONFIRMADO (0 registros) |
| ✅ NO se modificó código | CONFIRMADO |
| ✅ NO se modificó login/JWT/permisos | CONFIRMADO |
| ✅ MongoDB sigue siendo fuente principal | CONFIRMADO |

---

**FIN DEL DOCUMENTO FASE A1.7**

*DDL ejecutado exitosamente. Siguiente fase requiere autorización expresa.*
