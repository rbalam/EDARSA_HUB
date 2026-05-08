# PROPUESTA DDL AUTH/RBAC EDARSAHUB — NOMENCLATURA CORREGIDA

**Documento:** Propuesta de Modelo de Datos con Nomenclatura Validada  
**Fecha:** 8 de Mayo 2026  
**Estado:** PROPUESTA DOCUMENTAL — NO EJECUTAR  
**Versión:** 2.0 (Nomenclatura corregida)

---

## 1. RESUMEN

Este documento corrige la propuesta DDL anterior, aplicando el **patrón de nomenclatura real** detectado en EDARSAHUB para el módulo Usuario/Auth.

### Cambios respecto a v1.0

| Propuesta v1.0 (INCORRECTA) | Propuesta v2.0 (CORREGIDA) |
|-----------------------------|-----------------------------|
| `Usuario_UnidadesPermitidas` | `Usuario_UnidadesAsignacion` |
| `Usuario_SucursalesPermitidas` | `Usuario_SucursalesAsignacion` |
| `Usuario_PermisosDirectos` | `Usuario_PermisosUsuario` |

---

## 2. PATRÓN DE NOMENCLATURA DETECTADO EN EDARSAHUB

### 2.1 Tablas Existentes del Módulo Usuario_* (14 tablas)

```
Usuario_Acciones              (Catálogo de acciones)
Usuario_Autorizaciones        (Proceso de autorización)
Usuario_AutorizacionesDetalle (Detalle de autorización)
Usuario_Catalogo              (Tabla maestra de usuarios)
Usuario_LogAccesos            (Bitácora de accesos)
Usuario_LogActividades        (Bitácora de actividades)
Usuario_MatrizAutorizacion    (Matriz de autorización)
Usuario_Modulos               (Catálogo de módulos)
Usuario_PermisosRolModulo     (Relación Rol-Módulo-Acción)
Usuario_PortalConfiguracion   (Configuración de portal)
Usuario_Roles                 (Catálogo de roles)
Usuario_RolesAsignacion       (Relación N:M Usuario-Rol)
Usuario_Sesiones              (Registro de sesiones)
Usuario_TiposAutorizacion     (Catálogo de tipos)
```

### 2.2 Reglas de Nomenclatura Identificadas

| Tipo | Patrón | Ejemplo Real |
|------|--------|--------------|
| **Prefijo de módulo** | `Usuario_` | `Usuario_Catalogo` |
| **Tabla maestra** | `Usuario_[Entidad]` | `Usuario_Roles` |
| **Relación N:M** | `Usuario_[Entidad]Asignacion` | `Usuario_RolesAsignacion` |
| **Permisos** | `Usuario_Permisos[Entidad][Contexto]` | `Usuario_PermisosRolModulo` |
| **Bitácora** | `Usuario_Log[Entidad]` | `Usuario_LogAccesos` |
| **Detalle** | `Usuario_[Entidad]Detalle` | `Usuario_AutorizacionesDetalle` |
| **Configuración** | `Usuario_[Entidad]Configuracion` | `Usuario_PortalConfiguracion` |

### 2.3 Reglas de Columnas

| Tipo | Patrón | Ejemplo Real |
|------|--------|--------------|
| **PK** | `[NombreSinPrefijo]ID` | `UsuarioRolAsignacionID` |
| **FK a Usuario** | `UsuarioID` | `UsuarioID INT NOT NULL` |
| **FK a Rol** | `RolID` | `RolID INT NOT NULL` |
| **FK a Unidad** | `UnidadNegocioID` | `UnidadNegocioID UNIQUEIDENTIFIER` |
| **Fecha inicio** | `FechaInicio` | `FechaInicio DATETIME2 NOT NULL` |
| **Fecha fin** | `FechaFin` | `FechaFin DATETIME2 NULL` |
| **Fecha alta** | `FechaAlta` | `FechaAlta DATETIME2 NOT NULL` |
| **Activo** | `Activo` | `Activo BIT NOT NULL` |
| **Auditoría creación** | `CreatedAt`, `CreatedBy` | `CreatedAt DATETIME2`, `CreatedBy VARCHAR(100)` |
| **Auditoría modificación** | `FechaModificacion`, `ModifiedBy` | `FechaModificacion DATETIME2`, `ModifiedBy VARCHAR(100)` |

---

## 3. VALIDACIÓN DE CAMPOS FALTANTES

### 3.1 `empresas_permitidas` → Mapea a Unidades de Negocio

| Aspecto | Análisis |
|---------|----------|
| **Origen MongoDB** | `users.empresas_permitidas` (array de UUIDs) |
| **Uso** | Filtro RBAC para limitar acceso por empresa/unidad |
| **Tabla EDARSAHUB relacionada** | `Unidades_Negocio` (existe, 5 registros) |
| **Tabla de relación existente** | NO EXISTE |
| **Nombre propuesto** | `Usuario_UnidadesAsignacion` |
| **Justificación** | Sigue patrón de `Usuario_RolesAsignacion` |

### 3.2 `sucursales` → Sucursales por usuario

| Aspecto | Análisis |
|---------|----------|
| **Origen MongoDB** | `users.sucursales` (array de strings) |
| **Uso** | Filtro RBAC para limitar acceso por sucursal |
| **Tabla EDARSAHUB relacionada** | `RH_Cat_Sucursales` (existe, 0 registros) |
| **Tabla de relación existente** | NO EXISTE |
| **Nombre propuesto** | `Usuario_SucursalesAsignacion` |
| **Justificación** | Sigue patrón de `Usuario_RolesAsignacion` |

### 3.3 `sec_permisos` → Permisos directos por usuario

| Aspecto | Análisis |
|---------|----------|
| **Origen MongoDB** | `users.sec_permisos` (array de códigos) |
| **Uso** | Permisos específicos asignados al usuario (bypass rol) |
| **Tabla EDARSAHUB relacionada** | `Usuario_PermisosRolModulo` (permisos por rol, no usuario) |
| **Tabla de relación existente** | NO EXISTE para permisos directos |
| **Nombre propuesto** | `Usuario_PermisosUsuario` |
| **Justificación** | Análogo a `Usuario_PermisosRolModulo` pero a nivel usuario |

### 3.4 `nivel_jerarquia` → Atributo de Usuario_Roles

| Aspecto | Análisis |
|---------|----------|
| **Origen MongoDB** | `rbac_roles.nivel_jerarquia` (INT 20-100) |
| **Uso** | Comparación jerárquica entre roles |
| **Tabla EDARSAHUB** | `Usuario_Roles` (existe, 5 registros, SIN nivel) |
| **Propuesta** | Agregar columna `NivelJerarquia INT` a `Usuario_Roles` |
| **Justificación** | Es atributo directo del rol, no relación |

---

## 4. DDL PROPUESTO CON NOMENCLATURA CORREGIDA (SIN EJECUTAR)

### 4.1 Tabla: `Usuario_UnidadesAsignacion`

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA PARA REVISIÓN

-- ============================================================
-- TABLA: Usuario_UnidadesAsignacion
-- Relación N:M entre usuarios y unidades de negocio
-- Sigue el patrón de Usuario_RolesAsignacion
-- ============================================================
CREATE TABLE Usuario_UnidadesAsignacion (
    -- PK siguiendo patrón [NombreSinPrefijo]ID
    UsuarioUnidadAsignacionID   BIGINT IDENTITY(1,1) NOT NULL,
    
    -- FKs
    UsuarioID                   INT NOT NULL,
    UnidadNegocioID             UNIQUEIDENTIFIER NOT NULL,
    
    -- Atributos de la relación (igual que Usuario_RolesAsignacion)
    EsPrincipal                 BIT NOT NULL DEFAULT 0,
    FechaInicio                 DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaFin                    DATETIME2 NULL,
    Activo                      BIT NOT NULL DEFAULT 1,
    
    -- Auditoría (patrón EDARSAHUB)
    CreatedAt                   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy                   VARCHAR(100) NULL,
    
    -- Constraints
    CONSTRAINT PK_Usuario_UnidadesAsignacion 
        PRIMARY KEY (UsuarioUnidadAsignacionID),
    CONSTRAINT FK_UsuarioUnidades_Usuario 
        FOREIGN KEY (UsuarioID) REFERENCES Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_UsuarioUnidades_Unidad 
        FOREIGN KEY (UnidadNegocioID) REFERENCES Unidades_Negocio(id),
    CONSTRAINT UQ_UsuarioUnidades_Unico 
        UNIQUE (UsuarioID, UnidadNegocioID)
);

-- Índices
CREATE INDEX IX_UsuarioUnidadesAsignacion_Usuario 
    ON Usuario_UnidadesAsignacion(UsuarioID);
CREATE INDEX IX_UsuarioUnidadesAsignacion_Unidad 
    ON Usuario_UnidadesAsignacion(UnidadNegocioID);
CREATE INDEX IX_UsuarioUnidadesAsignacion_Activo 
    ON Usuario_UnidadesAsignacion(Activo) WHERE Activo = 1;
```

### 4.2 Tabla: `Usuario_SucursalesAsignacion`

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA PARA REVISIÓN

-- ============================================================
-- TABLA: Usuario_SucursalesAsignacion
-- Relación N:M entre usuarios y sucursales
-- ============================================================
CREATE TABLE Usuario_SucursalesAsignacion (
    UsuarioSucursalAsignacionID BIGINT IDENTITY(1,1) NOT NULL,
    UsuarioID                   INT NOT NULL,
    SucursalID                  VARCHAR(50) NOT NULL,
    ServerID                    UNIQUEIDENTIFIER NULL,
    EsPrincipal                 BIT NOT NULL DEFAULT 0,
    FechaInicio                 DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaFin                    DATETIME2 NULL,
    Activo                      BIT NOT NULL DEFAULT 1,
    CreatedAt                   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy                   VARCHAR(100) NULL,
    
    CONSTRAINT PK_Usuario_SucursalesAsignacion 
        PRIMARY KEY (UsuarioSucursalAsignacionID),
    CONSTRAINT FK_UsuarioSucursales_Usuario 
        FOREIGN KEY (UsuarioID) REFERENCES Usuario_Catalogo(UsuarioID),
    CONSTRAINT UQ_UsuarioSucursales_Unico 
        UNIQUE (UsuarioID, SucursalID, ServerID)
);

CREATE INDEX IX_UsuarioSucursalesAsignacion_Usuario 
    ON Usuario_SucursalesAsignacion(UsuarioID);
```

### 4.3 Tabla: `Usuario_PermisosUsuario`

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA PARA REVISIÓN

-- ============================================================
-- TABLA: Usuario_PermisosUsuario
-- Permisos específicos asignados directamente al usuario
-- Análogo a Usuario_PermisosRolModulo pero a nivel usuario
-- ============================================================
CREATE TABLE Usuario_PermisosUsuario (
    PermisoUsuarioID            BIGINT IDENTITY(1,1) NOT NULL,
    UsuarioID                   INT NOT NULL,
    ModuloID                    INT NULL,
    AccionID                    SMALLINT NULL,
    CodigoPermiso               VARCHAR(50) NOT NULL,
    Permitido                   BIT NOT NULL DEFAULT 1,
    RestriccionPropietario      BIT NOT NULL DEFAULT 0,
    RestriccionSucursal         BIT NOT NULL DEFAULT 0,
    RequiereAutorizacion        BIT NOT NULL DEFAULT 0,
    NivelAutorizacionRequerido  SMALLINT NULL,
    Activo                      BIT NOT NULL DEFAULT 1,
    FechaAlta                   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaModificacion           DATETIME2 NULL,
    FechaExpiracion             DATETIME2 NULL,
    CreatedBy                   VARCHAR(100) NULL,
    ModifiedBy                  VARCHAR(100) NULL,
    Motivo                      VARCHAR(500) NULL,
    
    CONSTRAINT PK_Usuario_PermisosUsuario 
        PRIMARY KEY (PermisoUsuarioID),
    CONSTRAINT FK_PermisosUsuario_Usuario 
        FOREIGN KEY (UsuarioID) REFERENCES Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_PermisosUsuario_Modulo 
        FOREIGN KEY (ModuloID) REFERENCES Usuario_Modulos(ModuloID),
    CONSTRAINT FK_PermisosUsuario_Accion 
        FOREIGN KEY (AccionID) REFERENCES Usuario_Acciones(AccionID),
    CONSTRAINT UQ_PermisosUsuario_Unico 
        UNIQUE (UsuarioID, CodigoPermiso)
);

CREATE INDEX IX_PermisosUsuario_Usuario 
    ON Usuario_PermisosUsuario(UsuarioID);
CREATE INDEX IX_PermisosUsuario_Codigo 
    ON Usuario_PermisosUsuario(CodigoPermiso);
```

### 4.4 Modificación: Agregar `NivelJerarquia` a `Usuario_Roles`

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA PARA REVISIÓN

-- ============================================================
-- MODIFICACIÓN: Usuario_Roles - Agregar NivelJerarquia
-- ============================================================
ALTER TABLE Usuario_Roles ADD
    NivelJerarquia INT NOT NULL 
        CONSTRAINT DF_Usuario_Roles_NivelJerarquia DEFAULT 0;

-- Comentario: Actualizar valores según MongoDB actual:
-- UPDATE Usuario_Roles SET NivelJerarquia = 100 WHERE CodigoRol = 'ADMIN';
-- UPDATE Usuario_Roles SET NivelJerarquia = 80 WHERE CodigoRol = 'GERENCIA';
-- etc.
```

### 4.5 Modificación: Agregar `UnidadNegocioDefaultID` a `Usuario_Catalogo`

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA PARA REVISIÓN

-- ============================================================
-- MODIFICACIÓN: Usuario_Catalogo - Agregar UnidadNegocioDefaultID
-- ============================================================
ALTER TABLE Usuario_Catalogo ADD
    UnidadNegocioDefaultID UNIQUEIDENTIFIER NULL;

-- FK opcional:
-- ALTER TABLE Usuario_Catalogo ADD
--     CONSTRAINT FK_Usuario_UnidadDefault 
--         FOREIGN KEY (UnidadNegocioDefaultID) REFERENCES Unidades_Negocio(id);
```

---

## 5. COMPARACIÓN DE ESTRUCTURA: MODELO EXISTENTE vs PROPUESTA

### 5.1 Usuario_RolesAsignacion (EXISTENTE - Modelo a seguir)

```sql
UsuarioRolAsignacionID  BIGINT IDENTITY    -- PK
UsuarioID               INT NOT NULL       -- FK Usuario
RolID                   INT NOT NULL       -- FK Rol
EsPrincipal             BIT NOT NULL       -- Es rol principal
FechaInicio             DATETIME2 NOT NULL -- Inicio vigencia
FechaFin                DATETIME2 NULL     -- Fin vigencia
Activo                  BIT NOT NULL       -- Estado
CreatedAt               DATETIME2 NOT NULL -- Auditoría
CreatedBy               VARCHAR(100) NULL  -- Auditoría
```

### 5.2 Usuario_UnidadesAsignacion (PROPUESTA)

```sql
UsuarioUnidadAsignacionID  BIGINT IDENTITY    -- PK (mismo patrón)
UsuarioID                  INT NOT NULL       -- FK Usuario
UnidadNegocioID            UNIQUEIDENTIFIER   -- FK Unidad (tipo correcto)
EsPrincipal                BIT NOT NULL       -- Es unidad principal
FechaInicio                DATETIME2 NOT NULL -- Inicio vigencia
FechaFin                   DATETIME2 NULL     -- Fin vigencia
Activo                     BIT NOT NULL       -- Estado
CreatedAt                  DATETIME2 NOT NULL -- Auditoría
CreatedBy                  VARCHAR(100) NULL  -- Auditoría
```

**Conclusión:** La propuesta sigue exactamente el patrón de Usuario_RolesAsignacion.

---

## 6. RESUMEN DE NOMENCLATURA VALIDADA

| Campo MongoDB | Tabla EDARSAHUB Propuesta | Estado |
|---------------|---------------------------|--------|
| `empresas_permitidas` | `Usuario_UnidadesAsignacion` | ✅ Sigue patrón |
| `sucursales` | `Usuario_SucursalesAsignacion` | ✅ Sigue patrón |
| `sec_permisos` | `Usuario_PermisosUsuario` | ✅ Sigue patrón |
| `nivel_jerarquia` | Columna en `Usuario_Roles` | ✅ Atributo directo |
| `empresa_default_id` | Columna en `Usuario_Catalogo` | ✅ Atributo directo |

---

## 7. RIESGOS Y MITIGACIÓN

| Riesgo | Mitigación |
|--------|------------|
| Tipo de ID diferente (UsuarioID es INT, UnidadNegocioID es UNIQUEIDENTIFIER) | Usar tipo correcto en cada FK |
| Unicidad de relación | Constraint UNIQUE en combinación de FKs |
| Histórico de asignaciones | FechaInicio/FechaFin permiten tracking |
| Rollback | Scripts DROP TABLE preparados |

---

## 8. AUTORIZACIÓN REQUERIDA

### Checklist de Autorización

| Paso | Estado |
|------|--------|
| ✅ Backup MongoDB completado | LISTO |
| ✅ Análisis de nomenclatura EDARSAHUB | LISTO |
| ✅ Propuesta DDL v2.0 con nombres corregidos | LISTO |
| ⬜ Revisión y aprobación de nomenclatura por usuario | PENDIENTE |
| ⬜ Autorización para ejecutar DDL | NO AUTORIZADO |
| ⬜ Crear tablas en EDARSAHUB | NO AUTORIZADO |
| ⬜ Poblar tablas con datos | NO AUTORIZADO |
| ⬜ Modificar código backend | NO AUTORIZADO |

---

## 9. PREGUNTAS PENDIENTES PARA EL USUARIO

Antes de autorizar el DDL, se requiere decisión sobre:

1. **¿`Usuario_UnidadesAsignacion` o `Usuario_EmpresasAsignacion`?**
   - El sistema actual usa "empresas_permitidas" en MongoDB
   - EDARSAHUB tiene "Unidades_Negocio" (no "Empresas")
   - ¿Son sinónimos en el contexto del negocio?

2. **¿Se debe crear tabla `Sistema_Empresas` o usar `Unidades_Negocio` como equivalente?**
   - MongoDB tiene colección `empresas` (5 documentos)
   - ¿Son las "empresas" equivalentes a "unidades de negocio"?

3. **¿`Usuario_PermisosUsuario` o mantener solo `Usuario_PermisosRolModulo`?**
   - La tabla de permisos por rol ya existe
   - ¿Realmente hay permisos directos al usuario que no pasan por rol?

---

**FIN DEL DOCUMENTO DE PROPUESTA DDL v2.0**

*Este documento es de solo lectura. Ningún DDL ha sido ejecutado.*
*Toda implementación requiere autorización expresa del usuario.*
