# FASE 2-A: DDL AUTH/RBAC — PROPUESTA DE MIGRACIÓN A EDARSAHUB SQL

**Fecha:** 14-Dic-2025  
**Estado:** DISEÑO COMPLETADO — PENDIENTE AUTORIZACIÓN  
**Autor:** Agente E1 (Arquitecto de Datos)

---

## 1. RESUMEN EJECUTIVO

### 1.1 Estado Actual

| Componente | MongoDB | SQL Server | Gap |
|------------|---------|------------|-----|
| Usuarios | 17 registros (`db.users`) | 9 registros (`Usuario_Catalogo`) | 8 usuarios faltan en SQL |
| Roles | 4 (`roles`) + 5 (`sec_roles`) + 6 (`rbac_roles`) | 5 (`Usuario_Roles`) | Normalizar en SQL |
| Asignación Usuario↔Rol | 72 (`rbac_usuarios_roles`) | 0 (`Usuario_RolesAsignacion`) | Poblar completamente |
| Asignación Usuario↔Empresa | En `users.empresas_permitidas` | 0 (`Usuario_EmpresasAsignacion`) | Poblar completamente |
| Password Hash | En `users.password` (bcrypt) | En `Usuario_Catalogo.PasswordHashTexto` | Ya migrado para 9 usuarios |
| Trazabilidad Mongo→SQL | N/A | 9 (`Usuario_MigracionMongoTrace`) | Completar migración |

### 1.2 Veredicto

```
✅ TABLAS SQL EXISTEN Y ESTÁN BIEN DISEÑADAS
⚠️ FALTA POBLAR: Usuario_RolesAsignacion, Usuario_EmpresasAsignacion
⚠️ FALTAN 8 USUARIOS EN SQL
✅ PASSWORD HASH COMPATIBLE (bcrypt texto plano en PasswordHashTexto)
```

---

## 2. TABLAS SQL EXISTENTES EN EDARSAHUB

### 2.1 Usuario_Catalogo (✅ EXISTE)

```sql
-- Estructura actual - NO REQUIERE ALTER
CREATE TABLE dbo.Usuario_Catalogo (
    UsuarioID INT NOT NULL PRIMARY KEY,
    CodigoUsuario VARCHAR(30) NOT NULL,
    Username VARCHAR(60) NOT NULL,
    Email VARCHAR(150) NOT NULL UNIQUE,
    PasswordHash VARBINARY(MAX) NULL,         -- Hash binario (opcional)
    PasswordHashTexto VARCHAR(255) NULL,       -- Hash bcrypt texto (USADO)
    Nombre VARCHAR(100) NOT NULL,
    Apellidos VARCHAR(150) NULL,
    NombreCompleto VARCHAR(251) NULL,
    Telefono VARCHAR(25) NULL,
    Celular VARCHAR(25) NULL,
    Puesto VARCHAR(100) NULL,
    Departamento VARCHAR(100) NULL,
    EsUsuarioPortal BIT NOT NULL DEFAULT 0,
    RequiereMFA BIT NOT NULL DEFAULT 0,
    PasswordTemporal BIT NOT NULL DEFAULT 0,
    DebeCambiarPassword BIT NOT NULL DEFAULT 0,
    IntentosFallidos INT NOT NULL DEFAULT 0,
    Bloqueado BIT NOT NULL DEFAULT 0,
    FechaBloqueo DATETIME2 NULL,
    MotivoBloqueo VARCHAR(250) NULL,
    UltimoAcceso DATETIME2 NULL,
    UltimoCambioPassword DATETIME2 NULL,
    FechaExpiracionPassword DATETIME2 NULL,
    ZonaHoraria VARCHAR(60) NULL,
    Idioma VARCHAR(20) NULL,
    Activo BIT NOT NULL DEFAULT 1,
    FechaAlta DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaModificacion DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL,
    ModifiedBy VARCHAR(100) NULL
);
```

**Mapeo MongoDB → SQL:**

| Campo MongoDB | Campo SQL | Transformación |
|---------------|-----------|----------------|
| `email` | `Email` | Directo |
| `password` | `PasswordHashTexto` | Directo (bcrypt) |
| `nombre` / `name` | `Nombre` | Directo |
| `active` / `activo` | `Activo` | Directo |
| `id` (UUID) | **FALTA** | Ver ALTER propuesto |
| `role` | Via `Usuario_RolesAsignacion` | Normalizado |
| `empresas_permitidas` | Via `Usuario_EmpresasAsignacion` | Normalizado |

---

### 2.2 Usuario_Roles (✅ EXISTE)

```sql
-- Estructura actual - NO REQUIERE ALTER
CREATE TABLE dbo.Usuario_Roles (
    RolID INT NOT NULL PRIMARY KEY,
    CodigoRol VARCHAR(30) NOT NULL UNIQUE,
    NombreRol VARCHAR(100) NOT NULL,
    Descripcion VARCHAR(250) NULL,
    EsRolSistema BIT NOT NULL DEFAULT 0,
    Activo BIT NOT NULL DEFAULT 1,
    FechaAlta DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaModificacion DATETIME2 NULL,
    NivelJerarquia INT NOT NULL DEFAULT 0
);
```

**Roles existentes:**
| RolID | CodigoRol | NombreRol |
|-------|-----------|-----------|
| 1 | ADMIN | Administrador |
| 2 | GERENCIA | Gerencia |
| 3 | COMPRAS | Compras |
| 4 | VENTAS | Ventas |
| 5 | TESORERIA | Tesoreria |

**Roles faltantes (de MongoDB):**
- SuperAdministrador
- Supervisor
- Usuario

---

### 2.3 Usuario_RolesAsignacion (✅ EXISTE - VACÍA)

```sql
-- Estructura actual - NO REQUIERE ALTER
CREATE TABLE dbo.Usuario_RolesAsignacion (
    UsuarioRolAsignacionID BIGINT NOT NULL PRIMARY KEY IDENTITY(1,1),
    UsuarioID INT NOT NULL,           -- FK a Usuario_Catalogo
    RolID INT NOT NULL,               -- FK a Usuario_Roles
    EsPrincipal BIT NOT NULL DEFAULT 1,
    FechaInicio DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaFin DATETIME2 NULL,
    Activo BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy VARCHAR(100) NULL
);
```

---

### 2.4 Usuario_EmpresasAsignacion (✅ EXISTE - VACÍA)

```sql
-- Estructura actual - NO REQUIERE ALTER
CREATE TABLE dbo.Usuario_EmpresasAsignacion (
    UsuarioEmpresaAsignacionID BIGINT NOT NULL PRIMARY KEY IDENTITY(1,1),
    UsuarioID INT NOT NULL,           -- FK a Usuario_Catalogo
    EmpresaID INT NOT NULL,           -- FK a Empresas
    EsPrincipal BIT NOT NULL DEFAULT 0,
    FechaInicio DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaFin DATETIME2 NULL,
    Activo BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy VARCHAR(100) NULL,
    UpdatedAt DATETIME2 NULL,
    UpdatedBy VARCHAR(100) NULL
);
```

---

### 2.5 Usuario_MigracionMongoTrace (✅ EXISTE)

```sql
-- Tabla de trazabilidad para migración
CREATE TABLE dbo.Usuario_MigracionMongoTrace (
    TraceID INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    MongoID VARCHAR(24) NOT NULL,         -- ObjectId MongoDB
    Email VARCHAR(150) NOT NULL,
    UsuarioID_SQL INT NULL,               -- FK a Usuario_Catalogo
    RolMongoDB VARCHAR(50) NOT NULL,
    ActivoMongoDB BIT NOT NULL,
    Clasificacion VARCHAR(20) NOT NULL,   -- MIGRADO, PENDIENTE, OMITIR
    FechaMigracion DATETIME2 NULL,
    CreatedBy VARCHAR(100) NULL
);
```

---

## 3. DDL PROPUESTO

### 3.1 ALTER TABLE: Agregar campos faltantes a Usuario_Catalogo

```sql
-- =====================================================================
-- FASE 2-A: ALTER TABLE Usuario_Catalogo
-- Agregar campos para compatibilidad con MongoDB
-- =====================================================================

-- Campo para UUID de MongoDB (trazabilidad)
ALTER TABLE dbo.Usuario_Catalogo 
ADD MongoLegacyID VARCHAR(50) NULL;

-- Campo para UUID público (usado en JWT actual)
ALTER TABLE dbo.Usuario_Catalogo 
ADD PublicUUID UNIQUEIDENTIFIER NULL DEFAULT NEWID();

-- Índice único para búsqueda por UUID
CREATE UNIQUE INDEX IX_Usuario_PublicUUID 
ON dbo.Usuario_Catalogo(PublicUUID) WHERE PublicUUID IS NOT NULL;

-- Índice único para búsqueda por MongoID
CREATE UNIQUE INDEX IX_Usuario_MongoLegacyID 
ON dbo.Usuario_Catalogo(MongoLegacyID) WHERE MongoLegacyID IS NOT NULL;

-- Comentario de migración
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'UUID público usado en JWT y APIs. Compatible con MongoDB user.id', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE', @level1name = 'Usuario_Catalogo',
    @level2type = N'COLUMN', @level2name = 'PublicUUID';
```

---

### 3.2 INSERT: Agregar roles faltantes

```sql
-- =====================================================================
-- FASE 2-A: INSERT Roles faltantes
-- =====================================================================

-- Verificar y agregar roles que existen en MongoDB pero no en SQL
INSERT INTO dbo.Usuario_Roles (RolID, CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, NivelJerarquia)
SELECT RolID, CodigoRol, NombreRol, Descripcion, EsRolSistema, 1, NivelJerarquia
FROM (VALUES
    (10, 'SUPERADMIN', 'SuperAdministrador', 'Acceso total al sistema', 1, 100),
    (11, 'SUPERVISOR', 'Supervisor', 'Supervisión de operaciones', 0, 50),
    (12, 'USUARIO', 'Usuario', 'Usuario estándar', 0, 10),
    (13, 'VISOR', 'Visor', 'Solo lectura', 0, 5)
) AS Roles(RolID, CodigoRol, NombreRol, Descripcion, EsRolSistema, NivelJerarquia)
WHERE NOT EXISTS (SELECT 1 FROM dbo.Usuario_Roles WHERE CodigoRol = Roles.CodigoRol);
```

---

### 3.3 Tabla de mapeo Empresa MongoDB → SQL

```sql
-- =====================================================================
-- FASE 2-A: Tabla auxiliar para mapeo de empresas
-- =====================================================================

CREATE TABLE dbo.Empresas_MigracionMongoMap (
    MapID INT IDENTITY(1,1) PRIMARY KEY,
    MongoEmpresaID VARCHAR(50) NOT NULL UNIQUE,   -- UUID de MongoDB
    EmpresaID_SQL INT NULL,                        -- FK a Empresas (si existe)
    NombreEmpresa VARCHAR(200) NULL,
    Clasificacion VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);
```

---

## 4. ESTRATEGIA DE MIGRACIÓN DE DATOS

### 4.1 Fase 2-B: Poblar tablas SQL desde MongoDB

```sql
-- SCRIPT DE MIGRACIÓN (NO EJECUTAR SIN AUTORIZACIÓN)

-- Paso 1: Insertar usuarios faltantes en Usuario_Catalogo
INSERT INTO dbo.Usuario_Catalogo (
    CodigoUsuario, Username, Email, PasswordHashTexto, Nombre,
    Activo, FechaAlta, MongoLegacyID, PublicUUID
)
SELECT 
    SUBSTRING(u.email, 1, 30) AS CodigoUsuario,
    u.email AS Username,
    u.email AS Email,
    u.password AS PasswordHashTexto,
    COALESCE(u.nombre, u.name, u.email) AS Nombre,
    CASE WHEN u.active = true OR u.activo = true THEN 1 ELSE 0 END AS Activo,
    GETUTCDATE() AS FechaAlta,
    u._id AS MongoLegacyID,
    CAST(u.id AS UNIQUEIDENTIFIER) AS PublicUUID
FROM MongoDB.db.users u
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.Usuario_Catalogo uc WHERE uc.Email = u.email
);

-- Paso 2: Actualizar MongoLegacyID y PublicUUID para usuarios existentes
UPDATE uc SET 
    uc.MongoLegacyID = u._id,
    uc.PublicUUID = CAST(u.id AS UNIQUEIDENTIFIER)
FROM dbo.Usuario_Catalogo uc
INNER JOIN MongoDB.db.users u ON uc.Email = u.email
WHERE uc.MongoLegacyID IS NULL;

-- Paso 3: Poblar Usuario_RolesAsignacion
INSERT INTO dbo.Usuario_RolesAsignacion (UsuarioID, RolID, EsPrincipal, Activo, CreatedBy)
SELECT 
    uc.UsuarioID,
    CASE u.role
        WHEN 'SuperAdministrador' THEN 10
        WHEN 'Administrador' THEN 1
        WHEN 'Supervisor' THEN 11
        WHEN 'Usuario' THEN 12
        ELSE 12
    END AS RolID,
    1 AS EsPrincipal,
    1 AS Activo,
    'MIGRATION_FASE2B' AS CreatedBy
FROM MongoDB.db.users u
INNER JOIN dbo.Usuario_Catalogo uc ON uc.Email = u.email
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.Usuario_RolesAsignacion ura WHERE ura.UsuarioID = uc.UsuarioID
);

-- Paso 4: Poblar Usuario_EmpresasAsignacion
INSERT INTO dbo.Usuario_EmpresasAsignacion (UsuarioID, EmpresaID, EsPrincipal, Activo, CreatedBy)
SELECT 
    uc.UsuarioID,
    em.EmpresaID_SQL,
    CASE WHEN u.empresa_default_id = emp.MongoEmpresaID THEN 1 ELSE 0 END AS EsPrincipal,
    1 AS Activo,
    'MIGRATION_FASE2B' AS CreatedBy
FROM MongoDB.db.users u
CROSS APPLY STRING_SPLIT(u.empresas_permitidas, ',') AS emp
INNER JOIN dbo.Usuario_Catalogo uc ON uc.Email = u.email
INNER JOIN dbo.Empresas_MigracionMongoMap em ON em.MongoEmpresaID = emp.value
WHERE em.EmpresaID_SQL IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM dbo.Usuario_EmpresasAsignacion uea 
      WHERE uea.UsuarioID = uc.UsuarioID AND uea.EmpresaID = em.EmpresaID_SQL
  );
```

---

### 4.2 Fase 2-C: Queries de validación

```sql
-- =====================================================================
-- QUERIES DE VALIDACIÓN
-- =====================================================================

-- 1. Conteo usuarios MongoDB vs SQL
-- MongoDB: SELECT COUNT(*) FROM db.users
-- SQL:
SELECT COUNT(*) AS total_sql FROM dbo.Usuario_Catalogo;

-- 2. Usuarios activos
SELECT COUNT(*) AS activos_sql FROM dbo.Usuario_Catalogo WHERE Activo = 1;

-- 3. Usuarios sin rol asignado
SELECT uc.Email, uc.Activo
FROM dbo.Usuario_Catalogo uc
LEFT JOIN dbo.Usuario_RolesAsignacion ura ON uc.UsuarioID = ura.UsuarioID
WHERE ura.UsuarioRolAsignacionID IS NULL;

-- 4. Usuarios sin empresa asignada
SELECT uc.Email, uc.Activo
FROM dbo.Usuario_Catalogo uc
LEFT JOIN dbo.Usuario_EmpresasAsignacion uea ON uc.UsuarioID = uea.UsuarioID
WHERE uea.UsuarioEmpresaAsignacionID IS NULL;

-- 5. Usuarios SuperAdministrador
SELECT uc.Email, ur.NombreRol
FROM dbo.Usuario_Catalogo uc
INNER JOIN dbo.Usuario_RolesAsignacion ura ON uc.UsuarioID = ura.UsuarioID
INNER JOIN dbo.Usuario_Roles ur ON ura.RolID = ur.RolID
WHERE ur.CodigoRol = 'SUPERADMIN';

-- 6. Hashes nulos (usuarios sin password)
SELECT Email FROM dbo.Usuario_Catalogo 
WHERE PasswordHashTexto IS NULL OR PasswordHashTexto = '';

-- 7. Emails duplicados
SELECT Email, COUNT(*) AS cnt
FROM dbo.Usuario_Catalogo
GROUP BY Email
HAVING COUNT(*) > 1;

-- 8. Diferencias MongoDB vs SQL
SELECT 
    mt.Email,
    mt.RolMongoDB,
    mt.ActivoMongoDB,
    mt.Clasificacion,
    CASE WHEN uc.UsuarioID IS NOT NULL THEN 'EN SQL' ELSE 'FALTA EN SQL' END AS EstadoSQL
FROM dbo.Usuario_MigracionMongoTrace mt
LEFT JOIN dbo.Usuario_Catalogo uc ON mt.Email = uc.Email;
```

---

## 5. ESTRATEGIA DUAL-READ

### 5.1 Fases de implementación

| Fase | Descripción | Riesgo |
|------|-------------|--------|
| **2-B** | Poblar tablas SQL desde MongoDB | BAJO |
| **2-C** | Validar conteos y hashes | BAJO |
| **2-D** | Crear `user_repository_sql.py` | BAJO |
| **2-E** | Modificar `get_current_user()` a SQL-first con Mongo fallback | MEDIO |
| **2-F** | Período de observación (1-2 semanas) | BAJO |
| **2-G** | Apagar fallback MongoDB | ALTO |
| **2-H** | Eliminar dependencias `db.users` | MEDIO |

### 5.2 Diseño dual-read

```python
# Pseudocódigo para user_repository_sql.py

async def get_user_by_email_sql_first(email: str, db_mongo=None) -> Optional[Dict]:
    """
    Intenta obtener usuario de SQL primero.
    Si falla o no existe, fallback a MongoDB.
    """
    # 1. Intentar SQL
    user_sql = await get_user_from_sql(email)
    if user_sql:
        return transform_sql_to_user_dict(user_sql)
    
    # 2. Fallback MongoDB (temporal)
    if db_mongo:
        logging.warning(f"[AUTH-FALLBACK] Usuario {email} no encontrado en SQL, usando MongoDB")
        user_mongo = await db_mongo.users.find_one({"email": email}, {"_id": 0})
        return user_mongo
    
    return None
```

---

## 6. MATRIZ DE EQUIVALENCIA COMPLETA

| Campo MongoDB | Tabla SQL | Columna SQL | Transformación | Obligatorio |
|---------------|-----------|-------------|----------------|-------------|
| `_id` (ObjectId) | `Usuario_Catalogo` | `MongoLegacyID` | String | Sí (trazabilidad) |
| `id` (UUID) | `Usuario_Catalogo` | `PublicUUID` | UNIQUEIDENTIFIER | Sí (JWT) |
| `email` | `Usuario_Catalogo` | `Email` | Directo | Sí |
| `password` | `Usuario_Catalogo` | `PasswordHashTexto` | Directo | Sí |
| `nombre` / `name` | `Usuario_Catalogo` | `Nombre` | Coalesce | Sí |
| `active` / `activo` | `Usuario_Catalogo` | `Activo` | Boolean→Bit | Sí |
| `role` | `Usuario_RolesAsignacion` | `RolID` | Via mapeo | Sí |
| `empresas_permitidas` | `Usuario_EmpresasAsignacion` | `EmpresaID` | Array→Rows | No |
| `sec_permisos` | `Usuario_PermisosRolModulo` | (existente) | Normalizado | No |
| `sec_rol` | `Usuario_RolesAsignacion` | `RolID` | Via mapeo | No |
| `empresa_default_id` | `Usuario_EmpresasAsignacion` | `EsPrincipal=1` | Flag | No |

---

## 7. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Password no compatible | BAJA | ALTO | Ya validado: bcrypt en texto plano funciona |
| Pérdida de SuperAdministrador | BAJA | ALTO | Insertar rol SUPERADMIN antes de migrar |
| JWT inválido post-migración | MEDIA | ALTO | Usar PublicUUID compatible con `user.id` |
| Usuarios sin empresa | MEDIA | MEDIO | SuperAdmin tiene acceso total automático |
| Empresas UUID no mapeadas | MEDIA | MEDIO | Crear tabla de mapeo antes de migrar |
| Fallback MongoDB falla | BAJA | BAJO | Período de observación antes de apagar |

---

## 8. CRITERIOS DE ACEPTACIÓN

### Pre-migración (Fase 2-B)

- [ ] DDL ejecutado sin errores
- [ ] Roles faltantes insertados
- [ ] Usuarios migrados sin pérdida de passwords
- [ ] PublicUUID asignado a cada usuario

### Post-migración (Fase 2-C)

- [ ] Conteo SQL = Conteo MongoDB activos
- [ ] 0 usuarios sin rol
- [ ] 0 hashes nulos en usuarios activos
- [ ] 0 emails duplicados
- [ ] SuperAdministrador preservado

### Dual-read (Fase 2-E)

- [ ] Login funciona con SQL
- [ ] `get_current_user()` devuelve datos desde SQL
- [ ] Fallback MongoDB activo pero sin uso
- [ ] Logs de fallback vacíos después de 24h

---

## 9. ROLLBACK

En caso de fallo crítico:

```sql
-- ROLLBACK: Deshacer migración (NO EJECUTAR SIN AUTORIZACIÓN)

-- 1. Eliminar asignaciones
DELETE FROM dbo.Usuario_RolesAsignacion WHERE CreatedBy = 'MIGRATION_FASE2B';
DELETE FROM dbo.Usuario_EmpresasAsignacion WHERE CreatedBy = 'MIGRATION_FASE2B';

-- 2. Revertir código a MongoDB-only
-- (Revertir user_repository_sql.py y get_current_user())

-- 3. No eliminar Usuario_Catalogo (datos preexistentes)
```

---

## 10. CONCLUSIÓN

### 10.1 Resumen de cambios

| Tipo | Cantidad | Detalle |
|------|----------|---------|
| ALTER TABLE | 1 | Usuario_Catalogo (2 columnas + 2 índices) |
| CREATE TABLE | 1 | Empresas_MigracionMongoMap |
| INSERT | ~4 | Roles faltantes |
| Archivos nuevos | 1 | `user_repository_sql.py` |
| Archivos modificados | 1 | `core/security.py` (Fase 2-E) |

### 10.2 No se modificó

- ✅ Login (se modificará en Fase 2-E)
- ✅ JWT (compatible con PublicUUID)
- ✅ Frontend
- ✅ Tablero Ejecutivo
- ✅ Comercial V2
- ✅ Otros módulos

### 10.3 Siguiente paso

Solicitar autorización para:
1. Ejecutar DDL (ALTER TABLE, CREATE TABLE, INSERT)
2. Ejecutar migración de datos (Fase 2-B)
3. Validar (Fase 2-C)

---

**ESTADO:** DISEÑO COMPLETADO — PENDIENTE AUTORIZACIÓN PARA EJECUCIÓN

*Documento generado bajo régimen de Autorización Controlada. No se ejecutó ningún DDL.*
