# PROPUESTA DDL AUTH/RBAC EDARSAHUB

**Documento:** Propuesta de Modelo de Datos para Migración Auth/RBAC  
**Fecha:** 8 de Mayo 2026  
**Estado:** PROPUESTA DOCUMENTAL — NO EJECUTAR  
**Versión:** 1.0

---

## 1. RESUMEN

Este documento presenta el análisis técnico para determinar si los campos faltantes en EDARSAHUB deben implementarse como:
- **OPCIÓN A:** Columnas directas en `Usuario_Catalogo`
- **OPCIÓN B:** Tablas relacionales normalizadas
- **OPCIÓN C:** Reutilización de tablas existentes
- **OPCIÓN D:** Mantener temporalmente en MongoDB

La recomendación final favorece **OPCIÓN B/C (Tablas Relacionales)** para `empresas_permitidas` y `sec_permisos`, y **OPCIÓN A (Columna)** para `nivel_jerarquia` en `Usuario_Roles`.

---

## 2. CAMPOS FALTANTES DETECTADOS

| Campo MongoDB | Colección | Tipo Actual | Uso |
|---------------|-----------|-------------|-----|
| `empresas_permitidas` | users | Array de UUIDs | Filtro RBAC por empresa/unidad |
| `sucursales` | users | Array de strings | Filtro RBAC por sucursal |
| `sec_permisos` | users | Array de strings | Códigos de permisos directos |
| `sec_rol` | users | String | ID del rol RBAC asignado |
| `nivel_jerarquia` | rbac_roles | Integer (20-100) | Nivel de acceso del rol |
| `permisos_catalogos` | users | Array | Catálogos SQL permitidos |
| `puede_autorizar` | users | Boolean | Flag de workflow |
| `puede_liberar` | users | Boolean | Flag de workflow |
| `puede_solicitar` | users | Boolean | Flag de workflow |
| `empresa_default_id` | users | UUID string | Empresa por defecto |

---

## 3. VALIDACIÓN CONTRA TABLAS EXISTENTES EDARSAHUB

### 3.1 Para `empresas_permitidas` / `sucursales`

**Tablas encontradas:**
| Tabla | Descripción | Registros | ¿Útil? |
|-------|-------------|-----------|--------|
| `Unidades_Negocio` | Catálogo de unidades de negocio | 5 | ✅ SÍ |
| `RH_Cat_Sucursales` | Catálogo de sucursales fiscales | 0 | ⚠️ Vacía |
| `Usuario_RolesAsignacion` | Asignación usuario-rol | 0 | ✅ Modelo existe |

**Conclusión:** NO existe tabla `Usuario_UnidadesPermitidas`. Se debe CREAR como relación N:M.

### 3.2 Para `sec_permisos`

**Tablas encontradas:**
| Tabla | Descripción | Registros | ¿Útil? |
|-------|-------------|-----------|--------|
| `Usuario_PermisosRolModulo` | Permisos por rol-módulo-acción | 0 | ✅ MODELO EXISTE |
| `Usuario_Modulos` | Catálogo de módulos | 8 | ✅ CON DATOS |
| `Usuario_Acciones` | Catálogo de acciones | 10 | ✅ CON DATOS |

**Conclusión:** El modelo normalizado YA ESTÁ DISEÑADO. Solo falta:
1. Poblar `Usuario_PermisosRolModulo` con los permisos
2. Crear tabla `Usuario_PermisosEspeciales` para permisos directos a usuario (bypass rol)

### 3.3 Para `nivel_jerarquia`

**Tablas encontradas:**
| Tabla | Descripción | ¿Tiene nivel? |
|-------|-------------|---------------|
| `Usuario_Roles` | Catálogo de roles | ❌ NO |
| `RH_Cat_Puestos` | Catálogo de puestos | ✅ `NivelOrganizacional` (varchar) |

**Conclusión:** 
- `RH_Cat_Puestos.NivelOrganizacional` es de RH, no de seguridad
- Se recomienda agregar columna `NivelJerarquia INT` a `Usuario_Roles`

---

## 4. DECISIÓN DE MODELADO RECOMENDADA

### 4.1 `empresas_permitidas` → CREAR TABLA RELACIONAL

| Atributo | Análisis |
|----------|----------|
| **Campo requerido** | `empresas_permitidas` (array de UUIDs) |
| **Origen MongoDB** | `users.empresas_permitidas` |
| **Uso actual en código** | Filtro RBAC en `user_access_context.py`, `resolve_user_access_context()` |
| **Endpoint/función** | Todos los endpoints protegidos, Dashboard, Comercial, Finanzas |
| **Riesgo si falta** | **P0_CRÍTICO** - Usuarios no pueden filtrar por unidad de negocio |
| **Tabla EDARSAHUB candidata** | `Unidades_Negocio` (existe) |
| **Recomendación** | ✅ **CREAR TABLA RELACIONAL** `Usuario_UnidadesPermitidas` |

**Justificación:**
- Una relación N:M usuario-unidad es el modelo correcto
- Evita JSON/arrays en columnas
- Permite queries eficientes con JOIN
- Permite auditoría y fechas de asignación

### 4.2 `sec_permisos` → USAR TABLA EXISTENTE + NUEVA

| Atributo | Análisis |
|----------|----------|
| **Campo requerido** | `sec_permisos` (array de códigos como "CARGOS_VER") |
| **Origen MongoDB** | `users.sec_permisos` |
| **Uso actual en código** | Validación de permisos en endpoints, `@require_permission()` |
| **Endpoint/función** | Múltiples: `/cargos`, `/catalogos`, `/usuarios`, etc. |
| **Riesgo si falta** | **P0_CRÍTICO** - Autorización falla |
| **Tabla EDARSAHUB candidata** | `Usuario_PermisosRolModulo` (existe, vacía) |
| **Recomendación** | ✅ **USAR EXISTENTE** + CREAR `Usuario_PermisosDirectos` |

**Justificación:**
- `Usuario_PermisosRolModulo` cubre permisos heredados del rol
- Se necesita tabla adicional para permisos específicos de usuario (override)
- El modelo actual de MongoDB mezcla ambos conceptos

### 4.3 `nivel_jerarquia` → AGREGAR COLUMNA A TABLA EXISTENTE

| Atributo | Análisis |
|----------|----------|
| **Campo requerido** | `nivel_jerarquia` (entero 20-100) |
| **Origen MongoDB** | `rbac_roles.nivel_jerarquia` |
| **Uso actual en código** | Comparación de niveles para autorización jerárquica |
| **Endpoint/función** | `/rbac/roles`, comparación en autorizaciones |
| **Riesgo si falta** | **P1_ALTO** - Jerarquía de autorización indefinida |
| **Tabla EDARSAHUB candidata** | `Usuario_Roles` (existe) |
| **Recomendación** | ✅ **AGREGAR COLUMNA** `NivelJerarquia INT` a `Usuario_Roles` |

**Justificación:**
- Es un atributo directo del rol, no una relación
- Una columna INT es más eficiente que una tabla
- `RH_Cat_Puestos.NivelOrganizacional` es de RH, no seguridad

### 4.4 Otros campos

| Campo | Recomendación | Justificación |
|-------|---------------|---------------|
| `sec_rol` | USAR `Usuario_RolesAsignacion` | Tabla ya existe |
| `permisos_catalogos` | CREAR columna JSON temporal | Específico del sistema |
| `puede_autorizar/liberar/solicitar` | DERIVAR de permisos | No columnas separadas |
| `empresa_default_id` | AGREGAR columna a `Usuario_Catalogo` | Es atributo directo |

---

## 5. DDL PROPUESTO (SIN EJECUTAR)

### OPCIÓN A: Agregar columnas directas (NO RECOMENDADO para relaciones N:M)

```sql
-- ⚠️ NO EJECUTAR - SOLO REFERENCIA
-- NO RECOMENDADO: Usar JSON para relaciones N:M es anti-patrón

ALTER TABLE Usuario_Catalogo ADD 
    EmpresasPermitidasJSON NVARCHAR(MAX) NULL,  -- NO RECOMENDADO
    SucursalesJSON NVARCHAR(MAX) NULL,          -- NO RECOMENDADO
    PermisosDirectosJSON NVARCHAR(MAX) NULL,    -- NO RECOMENDADO
    EmpresaDefaultID NVARCHAR(100) NULL;        -- ✅ Este sí es atributo directo

ALTER TABLE Usuario_Roles ADD
    NivelJerarquia INT NOT NULL DEFAULT 0;      -- ✅ RECOMENDADO
```

### OPCIÓN B: Crear tablas relacionales (RECOMENDADO)

```sql
-- ⚠️ NO EJECUTAR - SOLO PROPUESTA PARA REVISIÓN

-- ============================================================
-- TABLA: Usuario_UnidadesPermitidas
-- Relación N:M entre usuarios y unidades de negocio permitidas
-- ============================================================
CREATE TABLE Usuario_UnidadesPermitidas (
    UsuarioUnidadID         BIGINT IDENTITY(1,1) NOT NULL,
    UsuarioID               INT NOT NULL,
    UnidadNegocioID         UNIQUEIDENTIFIER NOT NULL,
    EsDefault               BIT NOT NULL DEFAULT 0,
    Activo                  BIT NOT NULL DEFAULT 1,
    FechaAsignacion         DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaRevocacion         DATETIME2 NULL,
    AsignadoPor             VARCHAR(100) NULL,
    
    CONSTRAINT PK_Usuario_UnidadesPermitidas PRIMARY KEY (UsuarioUnidadID),
    CONSTRAINT FK_UsuarioUnidades_Usuario FOREIGN KEY (UsuarioID) 
        REFERENCES Usuario_Catalogo(UsuarioID),
    CONSTRAINT FK_UsuarioUnidades_Unidad FOREIGN KEY (UnidadNegocioID) 
        REFERENCES Unidades_Negocio(id),
    CONSTRAINT UQ_UsuarioUnidades UNIQUE (UsuarioID, UnidadNegocioID)
);

CREATE INDEX IX_UsuarioUnidades_Usuario ON Usuario_UnidadesPermitidas(UsuarioID);
CREATE INDEX IX_UsuarioUnidades_Unidad ON Usuario_UnidadesPermitidas(UnidadNegocioID);

-- ============================================================
-- TABLA: Usuario_SucursalesPermitidas
-- Relación N:M entre usuarios y sucursales permitidas
-- ============================================================
CREATE TABLE Usuario_SucursalesPermitidas (
    UsuarioSucursalID       BIGINT IDENTITY(1,1) NOT NULL,
    UsuarioID               INT NOT NULL,
    SucursalID              VARCHAR(50) NOT NULL,  -- ID de sucursal del sistema origen
    ServerID                UNIQUEIDENTIFIER NULL, -- Referencia al servidor
    Activo                  BIT NOT NULL DEFAULT 1,
    FechaAsignacion         DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    
    CONSTRAINT PK_Usuario_SucursalesPermitidas PRIMARY KEY (UsuarioSucursalID),
    CONSTRAINT FK_UsuarioSucursales_Usuario FOREIGN KEY (UsuarioID) 
        REFERENCES Usuario_Catalogo(UsuarioID),
    CONSTRAINT UQ_UsuarioSucursales UNIQUE (UsuarioID, SucursalID, ServerID)
);

-- ============================================================
-- TABLA: Usuario_PermisosDirectos
-- Permisos específicos asignados directamente al usuario (bypass rol)
-- ============================================================
CREATE TABLE Usuario_PermisosDirectos (
    PermisoDirectoID        BIGINT IDENTITY(1,1) NOT NULL,
    UsuarioID               INT NOT NULL,
    CodigoPermiso           VARCHAR(50) NOT NULL,  -- Ej: "CARGOS_VER", "CATALOGOS_SQL_EDITAR"
    ModuloID                INT NULL,              -- FK opcional a Usuario_Modulos
    AccionID                SMALLINT NULL,         -- FK opcional a Usuario_Acciones
    Otorgado                BIT NOT NULL DEFAULT 1, -- TRUE=permite, FALSE=deniega
    Activo                  BIT NOT NULL DEFAULT 1,
    FechaOtorgamiento       DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    FechaExpiracion         DATETIME2 NULL,
    OtorgadoPor             VARCHAR(100) NULL,
    Motivo                  VARCHAR(500) NULL,
    
    CONSTRAINT PK_Usuario_PermisosDirectos PRIMARY KEY (PermisoDirectoID),
    CONSTRAINT FK_PermisosDirectos_Usuario FOREIGN KEY (UsuarioID) 
        REFERENCES Usuario_Catalogo(UsuarioID),
    CONSTRAINT UQ_PermisosDirectos UNIQUE (UsuarioID, CodigoPermiso)
);

CREATE INDEX IX_PermisosDirectos_Usuario ON Usuario_PermisosDirectos(UsuarioID);
CREATE INDEX IX_PermisosDirectos_Codigo ON Usuario_PermisosDirectos(CodigoPermiso);

-- ============================================================
-- MODIFICACIÓN: Usuario_Roles - Agregar NivelJerarquia
-- ============================================================
ALTER TABLE Usuario_Roles ADD
    NivelJerarquia INT NOT NULL DEFAULT 0 
        CONSTRAINT DF_Roles_NivelJerarquia DEFAULT 0;

-- Comentario: Niveles sugeridos según MongoDB actual:
-- ADMIN = 100, DIRECCION = 80, GERENTE_OPS = 60, 
-- SUPERVISOR = 40, AUDITOR = 30, OPERADOR = 20

-- ============================================================
-- MODIFICACIÓN: Usuario_Catalogo - Agregar EmpresaDefaultID
-- ============================================================
ALTER TABLE Usuario_Catalogo ADD
    EmpresaDefaultID UNIQUEIDENTIFIER NULL;

-- FK opcional (si Unidades_Negocio se usa como "empresas")
-- ALTER TABLE Usuario_Catalogo ADD
--     CONSTRAINT FK_Usuario_EmpresaDefault FOREIGN KEY (EmpresaDefaultID) 
--         REFERENCES Unidades_Negocio(id);
```

### OPCIÓN C: Reutilizar tablas existentes (PARCIALMENTE APLICABLE)

```sql
-- ⚠️ NO EJECUTAR - SOLO REFERENCIA

-- Usuario_PermisosRolModulo YA EXISTE y es el modelo correcto
-- Solo necesita ser poblada con datos

-- Ejemplo de INSERT (NO EJECUTAR):
-- INSERT INTO Usuario_PermisosRolModulo (RolID, ModuloID, AccionID, Permitido, Activo)
-- VALUES (1, 1, 1, 1, 1);  -- Rol ADMIN puede VER módulo SEGURIDAD

-- Usuario_RolesAsignacion YA EXISTE
-- Solo necesita ser poblada cuando se migre sec_rol

-- Ejemplo de INSERT (NO EJECUTAR):
-- INSERT INTO Usuario_RolesAsignacion (UsuarioID, RolID, EsPrincipal, FechaInicio, Activo)
-- VALUES (1, 1, 1, GETUTCDATE(), 1);  -- Usuario 1 tiene rol ADMIN
```

### OPCIÓN D: Mantener fallback temporal en MongoDB

```python
# En código Python, mantener lectura dual:

async def get_user_permissions(user_id: int) -> List[str]:
    # Intentar EDARSAHUB primero
    try:
        permisos_sql = await get_permisos_from_edarsahub(user_id)
        if permisos_sql:
            return permisos_sql
    except Exception as e:
        logger.warning(f"EDARSAHUB permisos failed: {e}")
    
    # Fallback a MongoDB
    user = await db.users.find_one({"id": user_id_str})
    return user.get("sec_permisos", [])
```

---

## 6. IMPACTO

### 6.1 Archivos que requieren modificación (cuando se autorice)

| Archivo | Cambio Requerido |
|---------|------------------|
| `core/security.py` | Leer usuario de EDARSAHUB |
| `core/user_access_context.py` | Resolver permisos desde SQL |
| `modules/auth/repository.py` | Queries a nuevas tablas |
| `modules/auth/service.py` | Lógica de permisos |
| `server.py` (endpoints usuarios) | Adaptación CRUD |

### 6.2 Endpoints afectados

| Endpoint | Impacto |
|----------|---------|
| `POST /auth/login` | Leer de Usuario_Catalogo |
| `GET /auth/me` | JOIN con UnidadesPermitidas |
| `GET /auth/me/menu-permissions` | JOIN con PermisosRolModulo |
| `PUT /users/{id}/permissions` | INSERT/UPDATE nuevas tablas |
| Todos los protegidos | Validación de permisos |

### 6.3 Módulos blindados (NO TOCAR)

| Módulo | Razón |
|--------|-------|
| Tablero Ejecutivo | Alta visibilidad, ya funciona |
| Comercial | KPIs en producción |
| Compras | Operación diaria |
| Finanzas | Ya migrado a EDARSAHUB |

---

## 7. ROLLBACK

### 7.1 DDL Rollback (si se ejecutara y fallara)

```sql
-- ⚠️ SOLO EN CASO DE EMERGENCIA POST-IMPLEMENTACIÓN

-- Eliminar tablas nuevas
DROP TABLE IF EXISTS Usuario_PermisosDirectos;
DROP TABLE IF EXISTS Usuario_SucursalesPermitidas;
DROP TABLE IF EXISTS Usuario_UnidadesPermitidas;

-- Revertir columnas
ALTER TABLE Usuario_Roles DROP COLUMN IF EXISTS NivelJerarquia;
ALTER TABLE Usuario_Catalogo DROP COLUMN IF EXISTS EmpresaDefaultID;
```

### 7.2 Rollback de código

```python
# Variable de entorno para rollback instantáneo
USE_EDARSAHUB_AUTH = os.environ.get('USE_EDARSAHUB_AUTH', 'false').lower() == 'true'

# Cambiar a 'false' restaura lectura MongoDB
```

---

## 8. PRUEBAS REQUERIDAS ANTES DE EJECUTAR DDL

| # | Prueba | Criterio |
|---|--------|----------|
| 1 | Crear tablas en ambiente de desarrollo | DDL sin errores |
| 2 | Insertar datos de prueba | INSERTs exitosos |
| 3 | Ejecutar queries de lectura | JOINs funcionan |
| 4 | Validar FK constraints | No violan integridad |
| 5 | Probar rollback DDL | DROP exitoso |
| 6 | Medir performance queries | < 100ms |

---

## 9. AUTORIZACIÓN REQUERIDA PARA EJECUTAR

### Checklist de Autorización

| Paso | Acción | Estado |
|------|--------|--------|
| 1 | ✅ Backup MongoDB completado | LISTO |
| 2 | ✅ Propuesta DDL documentada | LISTO |
| 3 | ⬜ Revisión de propuesta por usuario | PENDIENTE |
| 4 | ⬜ Autorización para ejecutar DDL | NO AUTORIZADO |
| 5 | ⬜ Crear tablas en EDARSAHUB | NO AUTORIZADO |
| 6 | ⬜ Poblar tablas con datos | NO AUTORIZADO |
| 7 | ⬜ Modificar código backend | NO AUTORIZADO |
| 8 | ⬜ Activar piloto SuperAdministrador | NO AUTORIZADO |

### Firmas Requeridas

| Rol | Firma | Fecha |
|-----|-------|-------|
| Usuario/Propietario | _________________ | __________ |
| Arquitectura | Propuesta entregada | 2026-05-08 |

---

## 10. RESUMEN DE RECOMENDACIONES

| Campo | Recomendación | Razón |
|-------|---------------|-------|
| `empresas_permitidas` | **CREAR TABLA** `Usuario_UnidadesPermitidas` | Relación N:M normalizada |
| `sucursales` | **CREAR TABLA** `Usuario_SucursalesPermitidas` | Relación N:M normalizada |
| `sec_permisos` | **USAR EXISTENTE** `Usuario_PermisosRolModulo` + **CREAR** `Usuario_PermisosDirectos` | Modelo ya diseñado + bypass |
| `sec_rol` | **USAR EXISTENTE** `Usuario_RolesAsignacion` | Tabla ya existe |
| `nivel_jerarquia` | **AGREGAR COLUMNA** a `Usuario_Roles` | Atributo directo del rol |
| `empresa_default_id` | **AGREGAR COLUMNA** a `Usuario_Catalogo` | Atributo directo del usuario |

### Conclusión Final

**NO SE RECOMIENDA** agregar `empresas_permitidas` ni `sec_permisos` como columnas JSON a `Usuario_Catalogo` porque:

1. Violaría normalización de base de datos
2. Haría queries ineficientes
3. Dificultaría auditoría
4. El modelo relacional ya está parcialmente diseñado en EDARSAHUB

**SE RECOMIENDA** crear las 3 tablas relacionales propuestas y agregar 2 columnas simples a tablas existentes.

---

**FIN DEL DOCUMENTO DE PROPUESTA DDL**

*Este documento es de solo lectura. Ningún DDL ha sido ejecutado.*
*Toda implementación requiere autorización expresa del usuario.*
