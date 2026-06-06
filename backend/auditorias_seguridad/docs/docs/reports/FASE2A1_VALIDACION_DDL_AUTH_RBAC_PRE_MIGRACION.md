# FASE 2-A.1: VALIDACIÓN DDL AUTH/RBAC PRE-MIGRACIÓN

**Fecha:** 14-Dic-2025  
**Estado:** DIAGNÓSTICO PASIVO COMPLETADO  
**Autor:** Agente E1 (Régimen de Autorización Controlada)  
**Sin modificaciones al código, DDL, ni datos**

---

## 1. TABLAS SQL EXISTENTES EN EDARSAHUB

### 1.1 Usuario_Catalogo (EXISTE - 31 columnas)

| Columna | Tipo | Nullable | Observación |
|---------|------|----------|-------------|
| UsuarioID | int | NO | PK, Autoincrement implícito |
| CodigoUsuario | varchar(30) | NO | Código corto |
| Username | varchar(60) | NO | |
| Email | varchar(150) | NO | Único |
| PasswordHash | varbinary(max) | YES | Hash binario (no usado) |
| **PasswordHashTexto** | varchar(255) | YES | **Hash bcrypt texto (ACTIVO)** |
| Nombre | varchar(100) | NO | |
| Apellidos | varchar(150) | YES | |
| NombreCompleto | varchar(251) | YES | Calculado |
| Telefono | varchar(25) | YES | |
| Celular | varchar(25) | YES | |
| Puesto | varchar(100) | YES | |
| Departamento | varchar(100) | YES | |
| EsUsuarioPortal | bit | NO | Default 0 |
| RequiereMFA | bit | NO | Default 0 |
| PasswordTemporal | bit | NO | Default 0 |
| DebeCambiarPassword | bit | NO | Default 0 |
| IntentosFallidos | int | NO | Default 0 |
| Bloqueado | bit | NO | Default 0 |
| FechaBloqueo | datetime2 | YES | |
| MotivoBloqueo | varchar(250) | YES | |
| UltimoAcceso | datetime2 | YES | |
| UltimoCambioPassword | datetime2 | YES | |
| FechaExpiracionPassword | datetime2 | YES | |
| ZonaHoraria | varchar(60) | YES | |
| Idioma | varchar(20) | YES | |
| Activo | bit | NO | Default 1 |
| FechaAlta | datetime2 | NO | Default GETUTCDATE() |
| FechaModificacion | datetime2 | YES | |
| CreatedBy | varchar(100) | YES | |
| ModifiedBy | varchar(100) | YES | |

**Datos actuales:** 9 registros migrados

| UsuarioID | Email | Hash | Activo |
|-----------|-------|------|--------|
| 1 | admin@edarsa.com | SI | True |
| 2 | admin@inventario.com | SI | True |
| 3 | carlosruz@edarsa.com.mx | SI | True |
| 4 | noxte@alpyc.com | SI | True |
| 5 | auditoria@edarsa.com.mx | SI | True |
| 6 | almacen@cienfuegos.mx | SI | True |
| 7 | administracion@cienfuegos.mx | SI | True |
| 8 | ricardo@edarsa.com.mx | SI | True |
| 9 | david.ricardez@cienfuegos.mx | SI | True |

---

### 1.2 Usuario_Roles (EXISTE - 9 columnas)

| Columna | Tipo |
|---------|------|
| RolID | int |
| CodigoRol | varchar |
| NombreRol | varchar |
| Descripcion | varchar |
| EsRolSistema | bit |
| Activo | bit |
| FechaAlta | datetime2 |
| FechaModificacion | datetime2 |
| NivelJerarquia | int |

**Roles existentes (5):**

| RolID | CodigoRol | NombreRol | Sistema | Activo |
|-------|-----------|-----------|---------|--------|
| 1 | ADMIN | Administrador | True | True |
| 2 | GERENCIA | Gerencia | True | True |
| 3 | COMPRAS | Compras | True | True |
| 4 | VENTAS | Ventas | True | True |
| 5 | TESORERIA | Tesoreria | True | True |

---

### 1.3 Usuario_RolesAsignacion (EXISTE - VACÍA)

| Columna | Tipo |
|---------|------|
| UsuarioRolAsignacionID | bigint (PK, IDENTITY) |
| UsuarioID | int (FK) |
| RolID | int (FK) |
| EsPrincipal | bit |
| FechaInicio | datetime2 |
| FechaFin | datetime2 |
| Activo | bit |
| CreatedAt | datetime2 |
| CreatedBy | varchar |

**Registros:** 0 (VACÍA)

---

### 1.4 Usuario_EmpresasAsignacion (EXISTE - VACÍA)

| Columna | Tipo |
|---------|------|
| UsuarioEmpresaAsignacionID | bigint (PK, IDENTITY) |
| UsuarioID | int (FK) |
| EmpresaID | int (FK) |
| EsPrincipal | bit |
| FechaInicio | datetime2 |
| FechaFin | datetime2 |
| Activo | bit |
| CreatedAt | datetime2 |
| CreatedBy | varchar |
| UpdatedAt | datetime2 |
| UpdatedBy | varchar |

**Registros:** 0 (VACÍA)

---

### 1.5 Usuario_MigracionMongoTrace (EXISTE - 9 registros)

Tabla de trazabilidad de usuarios migrados:

| TraceID | MongoID | Email | UsuarioID_SQL | RolMongoDB | Activo | Clasificacion |
|---------|---------|-------|---------------|------------|--------|---------------|
| 1 | 69d88ca7... | admin@edarsa.com | 1 | Administrador | True | PRODUCTIVO |
| 2 | 69e4576b... | admin@inventario.com | 2 | SuperAdministrador | True | PRODUCTIVO |
| 3 | 69e4576b... | carlosruz@edarsa.com.mx | 3 | Administrador | True | PRODUCTIVO |
| 4 | 69e4576b... | noxte@alpyc.com | 4 | Supervisor | True | PRODUCTIVO |
| 5 | 69e4576b... | auditoria@edarsa.com.mx | 5 | Usuario | True | PRODUCTIVO |
| 6 | 69e4576b... | almacen@cienfuegos.mx | 6 | Usuario | True | PRODUCTIVO |
| 7 | 69e4576b... | administracion@cienfuegos.mx | 7 | Supervisor | True | PRODUCTIVO |
| 8 | 69e6f703... | ricardo@edarsa.com.mx | 8 | SuperAdministrador | True | PRODUCTIVO |
| 9 | 69e75b91... | david.ricardez@cienfuegos.mx | 9 | Usuario | True | PRODUCTIVO |

---

## 2. CAMPOS REALES EN MongoDB db.users

### 2.1 Campos encontrados (33 únicos)

```
_id                    (ObjectId MongoDB - interno)
id                     (UUID público - usado en JWT)
email                  (string - login)
password               (string - bcrypt hash)
name / nombre          (string - nombre display)
role                   (string - rol legacy)
active / activo        (boolean - estado)
empresas_permitidas    (array - UUIDs de empresas)
empresa_default_id     (string - UUID empresa principal)
allowed_servers        (array - IDs servidores legacy)
allowed_sucursales     (object - {server_id: [sucursal_ids]})
allowed_warehouses     (object - {server_id: [almacen_ids]})
sec_roles              (array - códigos de roles RBAC)
sec_rol                (string - rol RBAC único legacy)
sec_perfil             (string - perfil asignado)
sec_permisos           (array - permisos directos)
sec_roles_alcance      (object - alcance por rol)
permisos_catalogos     (array - permisos de catálogos)
puede_autorizar        (boolean)
puede_solicitar        (boolean)
puede_liberar          (boolean)
telefono               (string)
created_at             (datetime)
created_by             (string)
contexto_updated_at    (datetime)
migrated_at            (datetime)
migrated_from          (string)
disabled_at            (datetime)
disabled_reason        (string)
rol                    (string - legacy duplicado)
sucursales             (array - legacy)
```

---

### 2.2 Total usuarios en MongoDB: 17

| # | Email | role | active | UUID (id) | empresas_permitidas | sec_roles |
|---|-------|------|--------|-----------|---------------------|-----------|
| 1 | admin@edarsa.com | Administrador | True | f648dd3f-... | 5 empresas | [] |
| 2 | admin@inventario.com | SuperAdministrador | True | 0da77b7b-... | 5 empresas | [] |
| 3 | carlosruz@edarsa.com.mx | Administrador | True | a5e56ed0-... | 5 empresas | [] |
| 4 | noxte@alpyc.com | Supervisor | True | a72b325b-... | 5 empresas | [] |
| 5 | auditoria@edarsa.com.mx | Usuario | True | e200de9e-... | 5 empresas | [] |
| 6 | almacen@cienfuegos.mx | Usuario | True | 30702651-... | 1 empresa | ['VISOR_ESTRUCTURA', 'GESTOR_SISTEMA'] |
| 7 | administracion@cienfuegos.mx | Supervisor | True | 57dbb5ad-... | 1 empresa | [] |
| 8 | ricardo@edarsa.com.mx | SuperAdministrador | True | 1e18a085-... | 0 empresas | [] |
| 9 | david.ricardez@cienfuegos.mx | Usuario | True | f3ba4a2f-... | 0 empresas | ['VISOR_ESTRUCTURA', 'VISOR_SISTEMA'] |
| 10 | test_validacion@test.com | Usuario | **False** | 71018d7b-... | 0 empresas | [] |
| 11 | test_rbac_val@test.com | Usuario | **False** | 837fb84c-... | 0 empresas | [] |
| 12 | superadmin@test.com | SuperAdministrador | True | **SIN UUID** | 0 empresas | [] |
| 13 | superadmin2@test.com | SuperAdministrador | True | ec59635e-... | 0 empresas | [] |
| 14 | usuario_test_portal@test.com | Usuario | True | 20bb73a7-... | 0 empresas | [] |
| 15 | test_propinas@edarsa.com | **DESHABILITADO** | **False** | 33f29be3-... | 0 empresas | [] |
| 16 | carlos@alpuntoycoma.mx | Administrador | True | 9dd2a053-... | 0 empresas | [] |
| 17 | eduardo@alpuntoycoma.mx | Administrador | True | 12d4041c-... | 0 empresas | [] |

---

## 3. CAMPOS USADOS POR CÓDIGO AUTH/SECURITY/RBAC

### 3.1 core/security.py - get_current_user()

```python
# Línea 265: Consulta por email del JWT
user = await db.users.find_one({"email": payload['email']}, {"_id": 0})
```

**Campos leídos del JWT:**
- `payload['email']` - para buscar usuario

**Campos devueltos del usuario:**
- Todo el documento excepto `_id` y `password`

### 3.2 core/security.py - Funciones de permisos

| Función | Campos user.get() |
|---------|-------------------|
| `get_user_empresas_permitidas()` | `role`, `empresas_permitidas` |
| `user_has_server_access()` | `role`, `allowed_servers` |
| `filter_servers_by_permissions()` | `role`, `allowed_servers` |
| `filter_sucursales_by_permissions()` | `role`, `allowed_sucursales` |

### 3.3 core/user_access_context.py - resolve_user_access_context()

| Campo user.get() | Uso |
|------------------|-----|
| `id` | user_id del contexto |
| `email` | email del contexto |
| `name`, `nombre` | nombre display |
| `role` | verificar SuperAdmin/Admin |
| `empresas_permitidas` | empresas RBAC |
| `empresa_default_id` | empresa principal |
| `allowed_servers` | servidores legacy |
| `allowed_sucursales` | sucursales por servidor |
| `allowed_warehouses` | almacenes por servidor |
| `sec_roles` | roles RBAC |
| `sec_rol` | rol único legacy |
| `sec_permisos` | permisos directos |
| `sec_perfil` | perfil |
| `permisos_catalogos` | permisos catálogos |
| `puede_autorizar` | flag |
| `puede_solicitar` | flag |
| `puede_liberar` | flag |

### 3.4 modules/auth/service.py - login_user()

```python
# Línea 100: Crea JWT con estos campos
token = create_token(user['id'], user['email'], user['role'])
```

**Campos críticos para JWT:**
- `user['id']` → se convierte en `payload['user_id']`
- `user['email']` → se convierte en `payload['email']`
- `user['role']` → se convierte en `payload['role']`

### 3.5 modules/auth/repository.py - find_user_by_email()

```python
# Línea 50: Busca en MongoDB
return await get_db().users.find_one({"email": email}, projection)
```

**Fuente:** 100% MongoDB (`db.users`)

---

## 4. COMPARACIÓN CAMPO MongoDB → COLUMNA SQL

| Campo MongoDB | Columna SQL Existente | Transformación | Estado |
|---------------|----------------------|----------------|--------|
| `_id` (ObjectId) | - | Trazabilidad en `Usuario_MigracionMongoTrace.MongoID` | MIGRADO |
| `id` (UUID) | **NO EXISTE** | **REQUIERE:** `PublicUUID` en `Usuario_Catalogo` | **PENDIENTE DDL** |
| `email` | `Email` | Directo | OK |
| `password` | `PasswordHashTexto` | Directo (bcrypt texto) | OK |
| `name`/`nombre` | `Nombre` | Coalesce | OK |
| `active`/`activo` | `Activo` | Boolean→Bit | OK |
| `role` | Via `Usuario_RolesAsignacion.RolID` | Normalizado | PENDIENTE POBLAR |
| `empresas_permitidas` | Via `Usuario_EmpresasAsignacion.EmpresaID` | Array→Rows | PENDIENTE POBLAR |
| `empresa_default_id` | Via `Usuario_EmpresasAsignacion.EsPrincipal=1` | Flag | PENDIENTE POBLAR |
| `allowed_servers` | - | Legacy, no migrar | DEPRECAR |
| `allowed_sucursales` | - | Legacy, no migrar | DEPRECAR |
| `allowed_warehouses` | - | Legacy, no migrar | DEPRECAR |
| `sec_roles` | Via nueva tabla o JSON | Pendiente diseño | FUTURO |
| `sec_permisos` | Via nueva tabla o JSON | Pendiente diseño | FUTURO |
| `permisos_catalogos` | - | Pendiente diseño | FUTURO |

---

## 5. CONFIRMACIÓN: PASSWORD HASH SE PRESERVA SIN RESET

### 5.1 Verificación del formato de hash

**MongoDB (db.users.password):**
```
$2b$12$... (bcrypt, 60 caracteres)
```

**SQL (Usuario_Catalogo.PasswordHashTexto):**
```
$2b$12$... (mismo formato bcrypt, 60 caracteres)
```

### 5.2 Verificación de usuarios con hash en SQL

| Email | Hash en MongoDB | Hash en SQL | Coincide |
|-------|-----------------|-------------|----------|
| admin@edarsa.com | SI | SI | Pendiente verificar |
| admin@inventario.com | SI | SI | Pendiente verificar |
| carlosruz@edarsa.com.mx | SI | SI | Pendiente verificar |
| noxte@alpyc.com | SI | SI | Pendiente verificar |
| auditoria@edarsa.com.mx | SI | SI | Pendiente verificar |
| almacen@cienfuegos.mx | SI | SI | Pendiente verificar |
| administracion@cienfuegos.mx | SI | SI | Pendiente verificar |
| ricardo@edarsa.com.mx | SI | SI | Pendiente verificar |
| david.ricardez@cienfuegos.mx | SI | SI | Pendiente verificar |

### 5.3 Verificación de compatibilidad bcrypt

El código en `core/security.py` usa:
```python
bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

**Esto funciona con cualquier hash bcrypt en formato texto ($2a$, $2b$).**

**CONCLUSIÓN:** Los hashes bcrypt son portables entre MongoDB y SQL sin conversión.

---

## 6. CONFIRMACIÓN: USER_ID/JWT NO SE ROMPE

### 6.1 Estructura actual del JWT

```python
# core/security.py línea 131-136
payload = {
    'user_id': user_id,      # ← user['id'] de MongoDB (UUID string)
    'email': email,          # ← user['email']
    'role': role,            # ← user['role']
    'exp': datetime...
}
```

### 6.2 Cómo get_current_user() valida

```python
# core/security.py línea 262-270
payload = verify_token(token)          # Extrae email del JWT
user = await db.users.find_one({"email": payload['email']}, {"_id": 0})
```

**PROBLEMA IDENTIFICADO:**
- El JWT contiene `user_id` (UUID de MongoDB)
- Pero `get_current_user()` busca por `email`, no por `user_id`
- Esto significa que el JWT actual NO depende del `user_id` para la búsqueda

### 6.3 Riesgo de migración

| Escenario | Riesgo |
|-----------|--------|
| Login después de migración | BAJO - se genera nuevo token con datos de SQL |
| Token existente post-migración | BAJO - busca por email, no por user_id |
| Cambio de user_id (int vs UUID) | MEDIO - código que use `user['id']` podría fallar |

### 6.4 RECOMENDACIÓN

Agregar columna `PublicUUID` a `Usuario_Catalogo` para mantener el UUID original de MongoDB:

```sql
ALTER TABLE Usuario_Catalogo ADD PublicUUID UNIQUEIDENTIFIER NULL;
```

Y usarla como `user['id']` en el JSON de respuesta al autenticar.

---

## 7. CONFIRMACIÓN: SUPERADMINISTRADOR PRESERVADO

### 7.1 SuperAdministradores en MongoDB (4)

| Email | Estado | En SQL |
|-------|--------|--------|
| admin@inventario.com | Activo | SI (UsuarioID=2) |
| ricardo@edarsa.com.mx | Activo | SI (UsuarioID=8) |
| superadmin@test.com | Activo | **NO** |
| superadmin2@test.com | Activo | **NO** |

### 7.2 Roles en SQL vs MongoDB

| Rol MongoDB | Rol SQL Existente | RolID |
|-------------|-------------------|-------|
| SuperAdministrador | **NO EXISTE** | - |
| Administrador | ADMIN | 1 |
| Supervisor | **NO EXISTE** | - |
| Usuario | **NO EXISTE** | - |

### 7.3 ACCIÓN REQUERIDA

Antes de poblar `Usuario_RolesAsignacion`, ejecutar:

```sql
INSERT INTO Usuario_Roles (RolID, CodigoRol, NombreRol, Descripcion, EsRolSistema, NivelJerarquia)
VALUES 
    (10, 'SUPERADMIN', 'SuperAdministrador', 'Acceso total al sistema', 1, 100),
    (11, 'SUPERVISOR', 'Supervisor', 'Supervisión de operaciones', 0, 50),
    (12, 'USUARIO', 'Usuario', 'Usuario estándar', 0, 10);
```

---

## 8. CONFIRMACIÓN: EMAILS DUPLICADOS O AUSENTES

### 8.1 Emails duplicados en MongoDB
```
NINGUNO
```

### 8.2 Emails duplicados en SQL
```
NINGUNO (restricción UNIQUE en columna Email)
```

### 8.3 Usuarios en MongoDB que faltan en SQL (8)

| Email | role | active | Acción sugerida |
|-------|------|--------|-----------------|
| test_validacion@test.com | Usuario | False | OMITIR (test inactivo) |
| test_rbac_val@test.com | Usuario | False | OMITIR (test inactivo) |
| superadmin@test.com | SuperAdministrador | True | **MIGRAR** |
| superadmin2@test.com | SuperAdministrador | True | **MIGRAR** |
| usuario_test_portal@test.com | Usuario | True | Evaluar (test activo) |
| test_propinas@edarsa.com | DESHABILITADO | False | OMITIR (deshabilitado) |
| carlos@alpuntoycoma.mx | Administrador | True | **MIGRAR** |
| eduardo@alpuntoycoma.mx | Administrador | True | **MIGRAR** |

---

## 9. CONFIRMACIÓN: USUARIOS ACTIVOS/INACTIVOS

### 9.1 Resumen MongoDB

| Estado | Cantidad |
|--------|----------|
| Activos | 14 |
| Inactivos | 3 |
| **Total** | **17** |

### 9.2 Usuarios inactivos (no migrar)

| Email | role | Razón |
|-------|------|-------|
| test_validacion@test.com | Usuario | Test inactivo |
| test_rbac_val@test.com | Usuario | Test inactivo |
| test_propinas@edarsa.com | DESHABILITADO | Deshabilitado explícito |

### 9.3 Resumen SQL actual

| Estado | Cantidad |
|--------|----------|
| Activos | 9 |
| Inactivos | 0 |
| **Total** | **9** |

---

## 10. RIESGOS ANTES DE POBLAR

### 10.1 Riesgos ALTOS

| Riesgo | Descripción | Mitigación |
|--------|-------------|------------|
| **R1** | SuperAdministrador pierde acceso global | Crear rol SUPERADMIN antes de poblar |
| **R2** | Usuario sin UUID en MongoDB (`superadmin@test.com`) | Generar UUID durante migración |

### 10.2 Riesgos MEDIOS

| Riesgo | Descripción | Mitigación |
|--------|-------------|------------|
| **R3** | Código que use `user['id']` espera UUID, no int | Agregar `PublicUUID` a SQL y usarlo |
| **R4** | Empresas UUID en MongoDB vs int en SQL | Crear tabla de mapeo `Empresas_MigracionMongoMap` |

### 10.3 Riesgos BAJOS

| Riesgo | Descripción | Mitigación |
|--------|-------------|------------|
| **R5** | Usuarios test activos migrados | Evaluar si migrar o excluir |

---

## 11. SCRIPT DDL FINAL REVISADO

```sql
-- =====================================================================
-- FASE 2-B: DDL AUTORIZADO (SOLO EJECUTAR CON AUTORIZACIÓN EXPLÍCITA)
-- =====================================================================

-- PASO 1: Agregar columnas faltantes a Usuario_Catalogo
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Usuario_Catalogo' AND COLUMN_NAME = 'MongoLegacyID')
BEGIN
    ALTER TABLE dbo.Usuario_Catalogo ADD MongoLegacyID VARCHAR(50) NULL;
END

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Usuario_Catalogo' AND COLUMN_NAME = 'PublicUUID')
BEGIN
    ALTER TABLE dbo.Usuario_Catalogo ADD PublicUUID UNIQUEIDENTIFIER NULL;
END

-- PASO 2: Crear índices únicos
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Usuario_PublicUUID')
BEGIN
    CREATE UNIQUE INDEX IX_Usuario_PublicUUID 
    ON dbo.Usuario_Catalogo(PublicUUID) WHERE PublicUUID IS NOT NULL;
END

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Usuario_MongoLegacyID')
BEGIN
    CREATE UNIQUE INDEX IX_Usuario_MongoLegacyID 
    ON dbo.Usuario_Catalogo(MongoLegacyID) WHERE MongoLegacyID IS NOT NULL;
END

-- PASO 3: Insertar roles faltantes
IF NOT EXISTS (SELECT 1 FROM Usuario_Roles WHERE CodigoRol = 'SUPERADMIN')
    INSERT INTO Usuario_Roles (RolID, CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, NivelJerarquia)
    VALUES (10, 'SUPERADMIN', 'SuperAdministrador', 'Acceso total al sistema', 1, 1, 100);

IF NOT EXISTS (SELECT 1 FROM Usuario_Roles WHERE CodigoRol = 'SUPERVISOR')
    INSERT INTO Usuario_Roles (RolID, CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, NivelJerarquia)
    VALUES (11, 'SUPERVISOR', 'Supervisor', 'Supervisión de operaciones', 0, 1, 50);

IF NOT EXISTS (SELECT 1 FROM Usuario_Roles WHERE CodigoRol = 'USUARIO')
    INSERT INTO Usuario_Roles (RolID, CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, NivelJerarquia)
    VALUES (12, 'USUARIO', 'Usuario estándar', 'Usuario estándar', 0, 1, 10);

-- PASO 4: Crear tabla de mapeo de empresas (si no existe)
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Empresas_MigracionMongoMap')
BEGIN
    CREATE TABLE dbo.Empresas_MigracionMongoMap (
        MapID INT IDENTITY(1,1) PRIMARY KEY,
        MongoEmpresaID VARCHAR(50) NOT NULL UNIQUE,
        EmpresaID_SQL INT NULL,
        NombreEmpresa VARCHAR(200) NULL,
        Clasificacion VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
    );
END
```

---

## 12. ROLLBACK PROPUESTO

En caso de fallo durante la migración:

```sql
-- =====================================================================
-- ROLLBACK FASE 2-B (NO EJECUTAR SIN NECESIDAD)
-- =====================================================================

-- Paso 1: Eliminar asignaciones creadas por migración
DELETE FROM Usuario_RolesAsignacion WHERE CreatedBy = 'MIGRATION_FASE2B';
DELETE FROM Usuario_EmpresasAsignacion WHERE CreatedBy = 'MIGRATION_FASE2B';

-- Paso 2: Eliminar usuarios nuevos (si los hubiera)
-- NOTA: No eliminar los 9 usuarios preexistentes
DELETE FROM Usuario_Catalogo 
WHERE UsuarioID > 9 
  AND CreatedBy = 'MIGRATION_FASE2B';

-- Paso 3: Limpiar columnas agregadas (opcional)
-- UPDATE Usuario_Catalogo SET MongoLegacyID = NULL, PublicUUID = NULL;

-- Paso 4: Revertir código a MongoDB-only
-- Restaurar modules/auth/repository.py desde git
-- Restaurar core/security.py desde git

-- Paso 5: NO eliminar roles nuevos (pueden estar referenciados)
```

---

## 13. CRITERIO EXACTO PARA AUTORIZAR FASE 2-B

El usuario debe confirmar que:

### 13.1 Pre-requisitos verificados

- [ ] La estructura de `Usuario_Catalogo` es correcta
- [ ] Los 9 usuarios existentes en SQL tienen hash válido
- [ ] Los roles faltantes (SUPERADMIN, SUPERVISOR, USUARIO) serán creados
- [ ] Se agregará `PublicUUID` para mantener compatibilidad con JWT actual
- [ ] Se entiende que `Usuario_RolesAsignacion` y `Usuario_EmpresasAsignacion` están vacías

### 13.2 Decisiones de migración

- [ ] **Usuarios a migrar:** Todos los activos (14) o solo los 5 faltantes productivos
- [ ] **Usuarios a excluir:** Los 3 inactivos (test_validacion, test_rbac_val, test_propinas)
- [ ] **Usuario superadmin@test.com:** Migrar (generar UUID) o excluir

### 13.3 Estrategia de ejecución

- [ ] Ejecutar DDL primero (ALTER TABLE, CREATE INDEX, INSERT roles)
- [ ] Poblar `PublicUUID` para los 9 usuarios existentes desde MongoDB
- [ ] Insertar usuarios faltantes (5 productivos)
- [ ] Poblar `Usuario_RolesAsignacion` para los 14 usuarios
- [ ] Poblar `Usuario_EmpresasAsignacion` para usuarios con empresas

### 13.4 Confirmación final

```
[ ] SÍ AUTORIZO ejecutar FASE 2-B con el DDL revisado
[ ] Excluir usuarios de prueba (3 inactivos)
[ ] Generar UUID para superadmin@test.com si se incluye
```

---

## 14. RESUMEN EJECUTIVO

| Aspecto | Estado | Acción |
|---------|--------|--------|
| Tablas SQL | EXISTEN | Sin cambios estructurales mayores |
| Columnas faltantes | `PublicUUID`, `MongoLegacyID` | DDL pendiente |
| Roles faltantes | SUPERADMIN, SUPERVISOR, USUARIO | INSERT pendiente |
| Usuarios SQL | 9 de 14 productivos | Faltan 5 productivos |
| Password hash | Compatible bcrypt | Sin conversión |
| JWT/user_id | Busca por email | Sin impacto directo |
| SuperAdministrador | 4 en Mongo, 2 en SQL | Preservar rol |
| Emails duplicados | 0 | OK |
| Usuarios inactivos | 3 | Excluir de migración |

**ESTADO:** DIAGNÓSTICO COMPLETADO — ESPERANDO AUTORIZACIÓN PARA FASE 2-B

---

*Documento generado bajo régimen de Autorización Controlada.*  
*No se ejecutó ningún DDL, INSERT, UPDATE ni modificación de código.*
