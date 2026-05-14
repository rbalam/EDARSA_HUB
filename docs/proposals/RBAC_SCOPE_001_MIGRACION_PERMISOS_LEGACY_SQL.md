# RBAC-SCOPE-001: Migración de Permisos Legacy de MongoDB a EDARSAHUB SQL

**Fecha:** 14 de Diciembre de 2025  
**Estado:** PROPUESTA - Pendiente Autorización  
**Autor:** Agente E1 - Arquitecto SQL Senior  
**Régimen:** Autorización Controlada

---

## 1. Resumen Ejecutivo

Este documento propone la migración definitiva de los permisos operativos legacy (`allowed_servers`, `allowed_sucursales`, `allowed_warehouses`) desde MongoDB hacia EDARSAHUB SQL Server.

**Objetivo:** Eliminar toda dependencia funcional de MongoDB del módulo Usuarios/Roles/Auth/RBAC, consolidando EDARSAHUB SQL como la **única fuente de verdad** para permisos de usuario.

**Estado actual:** Hotfix funcional con lectura híbrida (datos base SQL + permisos MongoDB).

**Estado objetivo:** Lectura y escritura 100% SQL para todos los permisos.

---

## 2. Causa Raíz de la Dependencia MongoDB

Después de la migración FASE 2 (Auth/RBAC SQL-first), los permisos granulares de acceso a recursos quedaron en MongoDB porque:

1. **Diseño original:** El sistema fue construido con MongoDB como almacén principal.
2. **Migración parcial:** FASE 2 migró usuarios, roles y empresas, pero NO permisos operativos.
3. **Hotfix BUG-RBAC-PERM-001:** Se implementó enriquecimiento de datos SQL con permisos MongoDB para mantener funcionalidad.

**Resultado:** Inconsistencia arquitectónica donde:
- `get_current_user()` → 100% SQL ✅
- `get_all_users()` → SQL + MongoDB (híbrido) ⚠️
- `update_user(permissions)` → 100% MongoDB ❌

---

## 3. Estado Actual del Hotfix

| Componente | Fuente Actual | Estado |
|------------|---------------|--------|
| Usuario base (id, email, name) | EDARSAHUB SQL | ✅ Definitivo |
| Rol del usuario | EDARSAHUB SQL | ✅ Definitivo |
| Empresas permitidas | EDARSAHUB SQL | ✅ Definitivo |
| `allowed_servers` | MongoDB | ⚠️ Hotfix |
| `allowed_sucursales` | MongoDB | ⚠️ Hotfix |
| `allowed_warehouses` | MongoDB | ⚠️ Hotfix |
| Lectura de permisos | SQL + MongoDB | ⚠️ Híbrido |
| Escritura de permisos | MongoDB | ❌ Inaceptable |

---

## 4. Dependencias MongoDB que Quedaron

### 4.1 Campos Legacy en MongoDB (colección `users`)

| Campo | Tipo | Descripción | Ejemplo Real |
|-------|------|-------------|--------------|
| `allowed_servers` | `List[str]` | UUIDs de servidores permitidos | `["6d053c22-523e-48c0-b72b-96081e2d781b"]` |
| `allowed_sucursales` | `Dict[str, List[str]]` | server_id → [sucursal_ids] | `{"1b230a06...": ["0023", "0021"]}` |
| `allowed_warehouses` | `Dict[str, List[str]]` | server_id → [warehouse_codes] | `{"6d053c22...": ["003", "004"]}` |

### 4.2 Valores Reales por Usuario (MongoDB)

| Usuario | Email | Rol | Servidores | Sucursales | Almacenes |
|---------|-------|-----|------------|------------|-----------|
| Carlos Ruz | carlosruz@edarsa.com.mx | Administrador | 1 | 0 | 2 (CIENFUEGOS) |
| Nestor Oxte | noxte@alpyc.com | Supervisor | 1 | 2 (MPRO) | 5 (MPRO) |
| William Chuc | auditoria@edarsa.com.mx | Usuario | 3 | 2 (MPRO) | 20 (multi-server) |
| Cristina Chi | almacen@cienfuegos.mx | Usuario | 1 | 0 | 10 (CIENFUEGOS) |
| Daniel Pool | administracion@cienfuegos.mx | Supervisor | 1 | 1 | 9 (CIENFUEGOS) |
| David Ricardez | david.ricardez@cienfuegos.mx | Usuario | 4 | 0 | 6 (CIENFUEGOS) |

---

## 5. Endpoints Afectados

| Endpoint | Archivo | Operación | Fuente Actual | Fuente Objetivo |
|----------|---------|-----------|---------------|-----------------|
| `GET /api/users` | `routes.py:597` | Lectura | SQL + MongoDB | SQL |
| `PUT /api/users/{id}/permissions` | `routes.py:615` | Escritura | MongoDB | SQL |
| `GET /api/auth/me` | `security.py:240` | Lectura | SQL | SQL (sin cambio) |

---

## 6. Archivos Backend Afectados

| Archivo | Funciones | Cambio Requerido |
|---------|-----------|------------------|
| `/app/backend/modules/auth/repository.py` | `get_all_users()`, `update_user()` | Migrar a SQL |
| `/app/backend/modules/auth/service.py` | `update_user_permissions()` | Adaptar a nuevo repo |
| `/app/backend/modules/auth/context_service.py` | `get_user_context()` | Leer de SQL |
| `/app/backend/core/user_access_context.py` | `build_user_access_context()` | Leer de SQL |
| `/app/backend/modules/api_connections/universal_test_routes.py` | Validación `allowed_servers` | Sin cambio (usa objeto user) |

---

## 7. Archivos Frontend Afectados

| Archivo | Líneas | Uso | Cambio Requerido |
|---------|--------|-----|------------------|
| `/app/frontend/src/pages/Usuarios.js` | 102-104, 464-466 | Estado inicial permisos | Ninguno (JSON compatible) |
| `/app/frontend/src/pages/Usuarios.js` | 492-534 | Manipulación permisos | Ninguno |
| `/app/frontend/src/pages/Usuarios.js` | 1780-1837 | Renderizado modal | Ninguno |

**Nota:** El frontend no requiere cambios si el backend mantiene el mismo contrato JSON.

---

## 8. Campos Legacy Detectados

### 8.1 Detalle de `allowed_servers`

```json
// Estructura actual en MongoDB
"allowed_servers": [
  "6d053c22-523e-48c0-b72b-96081e2d781b",  // CIENFUEGOS
  "1b230a06-ffaf-4c70-bd27-b1be3579dea6"   // ManagmentPro
]

// Tipo: List[str] de UUIDs (PublicUUID de Servidores_Conexiones)
```

### 8.2 Detalle de `allowed_sucursales`

```json
// Estructura actual en MongoDB
"allowed_sucursales": {
  "1b230a06-ffaf-4c70-bd27-b1be3579dea6": ["0023", "0021"]
}

// Tipo: Dict[server_uuid, List[sucursal_code]]
// Las sucursales son códigos del sistema remoto (SoftRestaurant/MPRO)
```

### 8.3 Detalle de `allowed_warehouses`

```json
// Estructura actual en MongoDB
"allowed_warehouses": {
  "6d053c22-523e-48c0-b72b-96081e2d781b": ["003", "004", "100"]
}

// Tipo: Dict[server_uuid, List[warehouse_code]]
// Los warehouses/departamentos son códigos del sistema remoto
```

---

## 9. Valores Reales Detallados

### Carlos Ruz (carlosruz@edarsa.com.mx)
```json
{
  "allowed_servers": ["6d053c22-523e-48c0-b72b-96081e2d781b"],
  "allowed_sucursales": {},
  "allowed_warehouses": {
    "6d053c22-523e-48c0-b72b-96081e2d781b": ["003", "004"]
  }
}
```

### Nestor Oxte (noxte@alpyc.com)
```json
{
  "allowed_servers": ["1b230a06-ffaf-4c70-bd27-b1be3579dea6"],
  "allowed_sucursales": {
    "1b230a06-ffaf-4c70-bd27-b1be3579dea6": ["0023", "0021"]
  },
  "allowed_warehouses": {
    "1b230a06-ffaf-4c70-bd27-b1be3579dea6": ["0003", "0006", "0004", "0007", "0002"]
  }
}
```

### William Chuc (auditoria@edarsa.com.mx)
```json
{
  "allowed_servers": [
    "1b230a06-ffaf-4c70-bd27-b1be3579dea6",
    "6d053c22-523e-48c0-b72b-96081e2d781b",
    "a5ff0e25-f029-43db-b634-d4ac814c904f"
  ],
  "allowed_sucursales": {
    "1b230a06-ffaf-4c70-bd27-b1be3579dea6": ["0021", "0023"]
  },
  "allowed_warehouses": {
    "1b230a06-ffaf-4c70-bd27-b1be3579dea6": ["0003", "0006", "0001", "0004", "0007", "0002"],
    "6d053c22-523e-48c0-b72b-96081e2d781b": ["004", "002", "003", "100", "200", "400", "300"],
    "a5ff0e25-f029-43db-b634-d4ac814c904f": ["001", "100", "002", "200", "003", "300", "900"]
  }
}
```

---

## 10. Matriz Campo MongoDB → Tabla SQL

| Campo MongoDB | Archivo Uso | Endpoint | Tipo | Tabla SQL Destino | Columna SQL | Tipo SQL | Mapeo | Riesgo | Acción |
|---------------|-------------|----------|------|-------------------|-------------|----------|-------|--------|--------|
| `allowed_servers[]` | repository.py | GET/PUT users | Lectura/Escritura | `Usuario_ServidoresAsignacion` | `ServidorID` | INT FK | UUID→ServidorID via Servidores_Conexiones | Bajo | Crear tabla |
| `allowed_sucursales{}` | repository.py | GET/PUT users | Lectura/Escritura | `Usuario_SucursalesAsignacion` | `SucursalCodigo` | VARCHAR(20) | Código remoto directo | Medio | Crear tabla |
| `allowed_warehouses{}` | repository.py | GET/PUT users | Lectura/Escritura | `Usuario_AlmacenesAsignacion` | `AlmacenCodigo` | VARCHAR(20) | Código remoto directo | Medio | Crear tabla |

---

## 11. Tablas SQL Existentes Reutilizables

| Tabla | Propósito | Reutilizable |
|-------|-----------|--------------|
| `Usuario_Catalogo` | Datos base de usuario | ✅ Ya en uso |
| `Usuario_RolesAsignacion` | Asignación usuario-rol | ✅ Ya en uso |
| `Usuario_EmpresasAsignacion` | Asignación usuario-empresa | ✅ Ya en uso |
| `Usuario_Roles` | Catálogo de roles | ✅ Ya en uso |
| `Sistema_Empresas` | Catálogo de empresas | ✅ Ya en uso |
| `Servidores_Conexiones` | Catálogo de servidores | ✅ Reutilizar para FK |
| `Usuario_ServidoresAsignacion` | Asignación usuario-servidor | ❌ **No existe - CREAR** |
| `Usuario_SucursalesAsignacion` | Asignación usuario-sucursal | ❌ **No existe - CREAR** |
| `Usuario_AlmacenesAsignacion` | Asignación usuario-almacén | ❌ **No existe - CREAR** |

---

## 12. DDL Propuesto para Tablas Faltantes

### 12.1 Usuario_ServidoresAsignacion

```sql
-- =============================================================================
-- TABLA: Usuario_ServidoresAsignacion
-- PROPÓSITO: Almacenar qué servidores puede acceder cada usuario
-- MIGRACIÓN: Reemplaza MongoDB allowed_servers
-- =============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Usuario_ServidoresAsignacion')
BEGIN
    CREATE TABLE Usuario_ServidoresAsignacion (
        AsignacionID        INT IDENTITY(1,1) PRIMARY KEY,
        UsuarioID           INT NOT NULL,
        ServidorID          INT NOT NULL,
        
        -- Campos de auditoría y trazabilidad
        LegacyMongoValue    VARCHAR(100) NULL,      -- UUID original de MongoDB para trazabilidad
        Activo              BIT NOT NULL DEFAULT 1,
        FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
        FechaModificacion   DATETIME2 NULL,
        CreadoPor           INT NULL,               -- UsuarioID que creó
        ModificadoPor       INT NULL,               -- UsuarioID que modificó
        Observaciones       NVARCHAR(500) NULL,
        
        -- Foreign Keys
        CONSTRAINT FK_UsuarioServidores_Usuario 
            FOREIGN KEY (UsuarioID) REFERENCES Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_UsuarioServidores_Servidor 
            FOREIGN KEY (ServidorID) REFERENCES Servidores_Conexiones(id),
        
        -- Constraint única: un usuario no puede tener el mismo servidor asignado más de una vez (activo)
        CONSTRAINT UQ_UsuarioServidores_Activo 
            UNIQUE (UsuarioID, ServidorID, Activo)
    );
    
    -- Índices
    CREATE NONCLUSTERED INDEX IX_UsuarioServidores_Usuario 
        ON Usuario_ServidoresAsignacion(UsuarioID) WHERE Activo = 1;
    CREATE NONCLUSTERED INDEX IX_UsuarioServidores_Servidor 
        ON Usuario_ServidoresAsignacion(ServidorID) WHERE Activo = 1;
    
    PRINT 'Tabla Usuario_ServidoresAsignacion creada exitosamente.';
END
GO
```

### 12.2 Usuario_SucursalesAsignacion

```sql
-- =============================================================================
-- TABLA: Usuario_SucursalesAsignacion
-- PROPÓSITO: Almacenar qué sucursales puede acceder cada usuario por servidor
-- MIGRACIÓN: Reemplaza MongoDB allowed_sucursales
-- NOTA: SucursalCodigo es código del sistema remoto, no hay catálogo local
-- =============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Usuario_SucursalesAsignacion')
BEGIN
    CREATE TABLE Usuario_SucursalesAsignacion (
        AsignacionID        INT IDENTITY(1,1) PRIMARY KEY,
        UsuarioID           INT NOT NULL,
        ServidorID          INT NOT NULL,
        SucursalCodigo      VARCHAR(20) NOT NULL,   -- Código de sucursal del sistema remoto
        
        -- Campos de auditoría y trazabilidad
        LegacyMongoValue    VARCHAR(100) NULL,      -- Valor original de MongoDB
        Activo              BIT NOT NULL DEFAULT 1,
        FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
        FechaModificacion   DATETIME2 NULL,
        CreadoPor           INT NULL,
        ModificadoPor       INT NULL,
        Observaciones       NVARCHAR(500) NULL,
        
        -- Foreign Keys
        CONSTRAINT FK_UsuarioSucursales_Usuario 
            FOREIGN KEY (UsuarioID) REFERENCES Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_UsuarioSucursales_Servidor 
            FOREIGN KEY (ServidorID) REFERENCES Servidores_Conexiones(id),
        
        -- Constraint única
        CONSTRAINT UQ_UsuarioSucursales_Activo 
            UNIQUE (UsuarioID, ServidorID, SucursalCodigo, Activo)
    );
    
    -- Índices
    CREATE NONCLUSTERED INDEX IX_UsuarioSucursales_Usuario 
        ON Usuario_SucursalesAsignacion(UsuarioID) WHERE Activo = 1;
    CREATE NONCLUSTERED INDEX IX_UsuarioSucursales_Servidor 
        ON Usuario_SucursalesAsignacion(ServidorID) WHERE Activo = 1;
    
    PRINT 'Tabla Usuario_SucursalesAsignacion creada exitosamente.';
END
GO
```

### 12.3 Usuario_AlmacenesAsignacion

```sql
-- =============================================================================
-- TABLA: Usuario_AlmacenesAsignacion
-- PROPÓSITO: Almacenar qué almacenes/departamentos puede acceder cada usuario por servidor
-- MIGRACIÓN: Reemplaza MongoDB allowed_warehouses
-- NOTA: AlmacenCodigo es código del sistema remoto (departamento en SoftRestaurant)
-- =============================================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Usuario_AlmacenesAsignacion')
BEGIN
    CREATE TABLE Usuario_AlmacenesAsignacion (
        AsignacionID        INT IDENTITY(1,1) PRIMARY KEY,
        UsuarioID           INT NOT NULL,
        ServidorID          INT NOT NULL,
        AlmacenCodigo       VARCHAR(20) NOT NULL,   -- Código de almacén/departamento del sistema remoto
        
        -- Campos de auditoría y trazabilidad
        LegacyMongoValue    VARCHAR(100) NULL,      -- Valor original de MongoDB
        Activo              BIT NOT NULL DEFAULT 1,
        FechaCreacion       DATETIME2 NOT NULL DEFAULT GETDATE(),
        FechaModificacion   DATETIME2 NULL,
        CreadoPor           INT NULL,
        ModificadoPor       INT NULL,
        Observaciones       NVARCHAR(500) NULL,
        
        -- Foreign Keys
        CONSTRAINT FK_UsuarioAlmacenes_Usuario 
            FOREIGN KEY (UsuarioID) REFERENCES Usuario_Catalogo(UsuarioID),
        CONSTRAINT FK_UsuarioAlmacenes_Servidor 
            FOREIGN KEY (ServidorID) REFERENCES Servidores_Conexiones(id),
        
        -- Constraint única
        CONSTRAINT UQ_UsuarioAlmacenes_Activo 
            UNIQUE (UsuarioID, ServidorID, AlmacenCodigo, Activo)
    );
    
    -- Índices
    CREATE NONCLUSTERED INDEX IX_UsuarioAlmacenes_Usuario 
        ON Usuario_AlmacenesAsignacion(UsuarioID) WHERE Activo = 1;
    CREATE NONCLUSTERED INDEX IX_UsuarioAlmacenes_Servidor 
        ON Usuario_AlmacenesAsignacion(ServidorID) WHERE Activo = 1;
    
    PRINT 'Tabla Usuario_AlmacenesAsignacion creada exitosamente.';
END
GO
```

---

## 13. Índices y Constraints

| Tabla | Índice/Constraint | Propósito |
|-------|-------------------|-----------|
| `Usuario_ServidoresAsignacion` | `UQ_UsuarioServidores_Activo` | Evitar duplicados activos |
| `Usuario_ServidoresAsignacion` | `IX_UsuarioServidores_Usuario` | Búsqueda rápida por usuario |
| `Usuario_SucursalesAsignacion` | `UQ_UsuarioSucursales_Activo` | Evitar duplicados activos |
| `Usuario_AlmacenesAsignacion` | `UQ_UsuarioAlmacenes_Activo` | Evitar duplicados activos |

---

## 14. Mapeos Requeridos

### 14.1 Servidores: MongoDB UUID → SQL ServidorID

```sql
-- Mapeo vía Servidores_Conexiones.uuid_mongo
SELECT id AS ServidorID, uuid_mongo AS MongoUUID, nombre
FROM Servidores_Conexiones
WHERE uuid_mongo IS NOT NULL;
```

**Ejemplo:**
| ServidorID | MongoUUID | Nombre |
|------------|-----------|--------|
| 2 | 6d053c22-523e-48c0-b72b-96081e2d781b | CIENFUEGOS |
| 6 | 1b230a06-ffaf-4c70-bd27-b1be3579dea6 | ManagmentPro |

### 14.2 Sucursales: Código Remoto (Sin Catálogo Local)

Los códigos de sucursal (`0021`, `0023`, `default`) son identificadores del sistema remoto (SoftRestaurant/MPRO). No existe catálogo local, se almacenan como strings.

### 14.3 Almacenes/Departamentos: Código Remoto (Sin Catálogo Local)

Los códigos de almacén (`002`, `003`, `100`) son identificadores del sistema remoto. No existe catálogo local, se almacenan como strings.

---

## 15. Riesgos

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Pérdida de permisos durante migración | **Alta** | Script idempotente con validación previa y backup |
| UUID case-sensitivity | **Media** | Normalizar a lowercase antes de comparar |
| Códigos de sucursal/almacén sin catálogo | **Media** | Almacenar como VARCHAR, validar contra sistema remoto en runtime |
| Duplicados en MongoDB | **Baja** | Limpiar con script previo a migración |
| Frontend rompe contrato | **Baja** | Backend mantiene misma estructura JSON |

---

## 16. Plan de Migración por Fases

### FASE RBAC-SCOPE-A (ACTUAL)
**Estado:** ✅ Completada  
**Acciones:**
- Diagnóstico completo
- DDL propuesto
- Matriz de equivalencias
- Documento de propuesta

### FASE RBAC-SCOPE-B
**Estado:** Pendiente autorización  
**Acciones:**
- Ejecutar DDL para crear 3 tablas
- Validar estructura con `sp_help`
- No modificar código backend

### FASE RBAC-SCOPE-C
**Estado:** Pendiente autorización  
**Acciones:**
- Script de migración idempotente
- Leer permisos de MongoDB
- Insertar en tablas SQL
- Preservar `LegacyMongoValue` para trazabilidad
- Validar conteo: MongoDB vs SQL

### FASE RBAC-SCOPE-D
**Estado:** Pendiente autorización  
**Acciones:**
- Modificar `get_all_users()` para leer permisos de SQL
- Eliminar lectura de MongoDB para permisos
- Mantener estructura JSON compatible
- Validar que frontend renderiza correctamente

### FASE RBAC-SCOPE-E
**Estado:** Pendiente autorización  
**Acciones:**
- Modificar `update_user_permissions()` para escribir en SQL
- Eliminar escritura en MongoDB para permisos
- Validar guardado y persistencia

### FASE RBAC-SCOPE-F
**Estado:** Pendiente autorización  
**Acciones:**
- Pruebas end-to-end del modal de permisos
- Validar: ver departamentos, guardar, recargar, persistir
- Validar no regresión en otros módulos

### FASE RBAC-SCOPE-G
**Estado:** Pendiente autorización  
**Acciones:**
- Eliminar código de lectura MongoDB en `get_all_users()`
- Eliminar código de escritura MongoDB en `update_user()`
- Documentar eliminación
- Cerrar deuda técnica

---

## 17. Rollback

### En caso de fallo en FASE B (DDL):
```sql
DROP TABLE IF EXISTS Usuario_AlmacenesAsignacion;
DROP TABLE IF EXISTS Usuario_SucursalesAsignacion;
DROP TABLE IF EXISTS Usuario_ServidoresAsignacion;
```

### En caso de fallo en FASE C-G (Código):
- Revertir cambios en `repository.py` y `service.py`
- Restaurar lectura/escritura MongoDB
- Los datos en tablas SQL no afectan funcionamiento si código no las usa

---

## 18. Criterios de Aceptación

| # | Criterio | Validación |
|---|----------|------------|
| 1 | Carlos Ruz conserva 1 servidor (CIENFUEGOS) | Query SQL + API |
| 2 | Nestor Oxte conserva 1 servidor (ManagmentPro) | Query SQL + API |
| 3 | William Chuc conserva 3 servidores | Query SQL + API |
| 4 | Cristina Chi conserva 1 servidor (CIENFUEGOS) | Query SQL + API |
| 5 | Departamentos se ven con nombre | Screenshot modal |
| 6 | Guardar permisos persiste en SQL | Query + API |
| 7 | Recargar modal muestra lo guardado desde SQL | Screenshot |
| 8 | `update_user()` no escribe en MongoDB | Log + inspección código |
| 9 | `get_all_users()` no depende de MongoDB | Log + inspección código |
| 10 | Login sigue funcionando | Curl test |
| 11 | JWT no cambia | Inspección token |
| 12 | Auth SQL-first sigue funcionando | `get_current_user()` test |
| 13 | SUPERADMIN conserva acceso global | API test |
| 14 | `/api/servers` devuelve 8 servidores | Curl test |
| 15 | Tablero Ejecutivo carga | Screenshot |
| 16 | Comercial V2 carga | Navegación |
| 17 | Finanzas carga | Navegación |
| 18 | Inventarios/Catálogos cargan | Navegación |
| 19 | No hay secretos expuestos | Inspección respuestas API |
| 20 | No hay regresión en Usuarios/Roles | Testing completo |

---

## 19. Pruebas de No Regresión

### Backend
```bash
# Login funciona
curl -X POST $API_URL/api/auth/login -d '{"email":"admin@inventario.com","password":"admin123"}'

# Usuarios cargan (11 usuarios)
curl $API_URL/api/users -H "Authorization: Bearer $TOKEN"

# Servidores cargan (8 servidores)
curl $API_URL/api/servers -H "Authorization: Bearer $TOKEN"

# Permisos se guardan
curl -X PUT $API_URL/api/users/{id}/permissions -d '{...}'

# Permisos persisten
curl $API_URL/api/users -H "Authorization: Bearer $TOKEN" | jq '.[] | select(.email=="carlosruz@edarsa.com.mx")'
```

### Frontend
- Navegar a Usuarios y Roles
- Verificar 11 usuarios
- Abrir modal Permisos de Carlos Ruz
- Verificar departamentos visibles
- Guardar permisos
- Recargar página
- Verificar permisos persistidos

---

## 20. Confirmación EDARSAHUB SQL como Única Fuente

**DECLARO:**

Tras la implementación completa de las fases RBAC-SCOPE-A a RBAC-SCOPE-G:

1. **EDARSAHUB SQL Server** será la **ÚNICA fuente productiva** para:
   - Datos de usuario (Usuario_Catalogo)
   - Roles (Usuario_Roles, Usuario_RolesAsignacion)
   - Empresas (Sistema_Empresas, Usuario_EmpresasAsignacion)
   - **Servidores permitidos** (Usuario_ServidoresAsignacion) ← NUEVO
   - **Sucursales permitidas** (Usuario_SucursalesAsignacion) ← NUEVO
   - **Almacenes permitidos** (Usuario_AlmacenesAsignacion) ← NUEVO

2. **MongoDB** quedará como:
   - Respaldo histórico (sin sincronización activa)
   - Fuente para otros módulos no migrados (fuera de Auth/RBAC)
   - No será consultado ni actualizado para permisos de usuario

3. **El código backend** no contendrá:
   - Lectura de permisos desde MongoDB
   - Escritura de permisos hacia MongoDB
   - Fallbacks hacia MongoDB para Auth/RBAC

---

**Documento preparado por:** Agente E1  
**Fecha:** 14 de Diciembre de 2025  
**Próximo paso:** Esperar autorización del usuario para FASE RBAC-SCOPE-B
