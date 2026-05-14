# FASE 4B-RBAC — Propuesta Técnica de Migración

**Fecha:** 2026-05-14  
**Estado:** ✅ COMPLETADA  
**Régimen:** Autorización Controlada  
**Módulo Autorizado:** RBAC MongoDB → EDARSAHUB SQL

---

## RESUMEN DE EJECUCIÓN

### DDL Ejecutado:
1. ✅ Creada tabla `Usuario_LogRBACVerificacion` con índices
2. ✅ Insertados 11 módulos en `Usuario_Modulos`
3. ✅ Insertadas 6 acciones en `Usuario_Acciones`
4. ✅ Insertados 4 roles en `Usuario_Roles` (DIRECCION, GERENTE_OPS, OPERADOR, AUDITOR)
5. ✅ Poblados 95 registros en `Usuario_PermisosRolModulo`
6. ✅ Migrados 598 registros de `rbac_audit_log` a `Usuario_LogRBACVerificacion`

### Código Modificado:
1. ✅ `/app/backend/core/rbac/repository.py` - Proxy a repository_sql.py
2. ✅ `/app/backend/core/rbac/repository_sql.py` - Nuevo repositorio SQL
3. ✅ `/app/backend/core/rbac/service.py` - Actualizado LEGACY_ROLE_MAPPING
4. ✅ `/app/backend/core/rbac/__init__.py` - Documentación actualizada

### Conteos Finales:
| Tabla | Registros |
|-------|-----------|
| Usuario_Roles | 13 |
| Usuario_Modulos | 19 |
| Usuario_Acciones | 16 |
| Usuario_PermisosRolModulo | 95 |
| Usuario_RolesAsignacion | 13 (11 activos) |
| Usuario_LogRBACVerificacion | 599 |

### Validaciones Realizadas:
- ✅ Login admin@inventario.com funciona
- ✅ Permisos se cargan correctamente (28 permisos, nivel 100)
- ✅ Endpoint /api/v2/rbac/mis-permisos funciona
- ✅ Endpoint /api/v2/rbac/roles funciona (13 roles)
- ✅ Endpoint /api/users funciona (11 usuarios)
- ✅ Endpoint /api/servers funciona (8 servidores)
- ✅ Tablero Ejecutivo sin regresión

### Plan de Rollback:
Si se requiere volver a MongoDB:
1. Restaurar `/app/backend/core/rbac/repository.py` original
2. Las tablas SQL son aditivas, no afectan MongoDB
3. MongoDB sigue teniendo los datos originales

---

## 1. ESTADO ACTUAL DE RBAC EN MONGODB

### 1.1 Colecciones MongoDB Origen

| Colección | Documentos | Estado |
|-----------|------------|--------|
| `rbac_permisos` | 43 | ACTIVO (semilla del sistema) |
| `rbac_roles` | 6 | ACTIVO (roles del sistema) |
| `rbac_usuarios_roles` | 72 | ACTIVO (asignaciones usuario-rol) |
| `rbac_audit_log` | 598 | ACTIVO (log de verificaciones) |

### 1.2 Estructura rbac_permisos (MongoDB)
```json
{
  "id": "UUID",
  "codigo": "CARGOS_VER",
  "modulo": "cargos",          // string del enum ModuloSistema
  "accion": "ver",             // string del enum AccionPermiso
  "descripcion": "Ver cargos económicos",
  "es_sistema": true,
  "activo": true,
  "created_at": ISODate
}
```

### 1.3 Estructura rbac_roles (MongoDB)
```json
{
  "id": "UUID",
  "nombre": "ADMIN",
  "descripcion": "Administrador del sistema",
  "nivel_jerarquia": 100,
  "es_sistema": true,
  "activo": true,
  "permisos": ["CARGOS_VER", "CARGOS_CREAR", ...],  // Array de códigos
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### 1.4 Estructura rbac_usuarios_roles (MongoDB)
```json
{
  "id": "UUID",
  "user_id": "PublicUUID del usuario",
  "rol_id": "UUID del rol",
  "rol_nombre": "ADMIN",
  "sucursal_id": null,         // o UUID de sucursal
  "activo": true,
  "asignado_por": "UUID del admin",
  "fecha_asignacion": ISODate
}
```

### 1.5 Roles MongoDB Actuales
| Nombre | Nivel | Permisos | Sistema |
|--------|-------|----------|---------|
| ADMIN | 100 | 43 (todos) | Sí |
| DIRECCION | 80 | 30 | Sí |
| GERENTE_OPS | 60 | 24 | Sí |
| SUPERVISOR | 40 | 17 | Sí |
| AUDITOR | 30 | 12 | Sí |
| OPERADOR | 20 | 8 | Sí |

---

## 2. ESTADO ACTUAL DE TABLAS SQL RELACIONADAS

### 2.1 Tablas Existentes en EDARSAHUB

| Tabla | Registros | Propósito | Compatible RBAC |
|-------|-----------|-----------|-----------------|
| `Usuario_Roles` | 9 | Catálogo de roles | ✅ PARCIAL |
| `Usuario_RolesAsignacion` | 11 activas | Asignación user-rol | ✅ PARCIAL |
| `Usuario_Modulos` | 8 | Catálogo de módulos | ✅ REUTILIZABLE |
| `Usuario_Acciones` | 10 | Catálogo de acciones | ✅ REUTILIZABLE |
| `Usuario_PermisosRolModulo` | 0 | Permisos granulares | ✅ VACÍA (usar) |
| `Usuario_Catalogo` | ~15 | Usuarios | ✅ YA MIGRADO |

### 2.2 Estructura Usuario_Roles (SQL) - YA EXISTE
```sql
CREATE TABLE Usuario_Roles (
    RolID INT PRIMARY KEY,
    CodigoRol VARCHAR(30) NOT NULL,      -- Equivale a "nombre" en MongoDB
    NombreRol VARCHAR(100) NOT NULL,     -- Equivale a "descripcion"
    Descripcion VARCHAR(250),
    EsRolSistema BIT NOT NULL,           -- Equivale a "es_sistema"
    Activo BIT NOT NULL,
    FechaAlta DATETIME2 NOT NULL,
    FechaModificacion DATETIME2,
    NivelJerarquia INT NOT NULL          -- YA EXISTE ✅
)
```

### 2.3 Roles SQL Actuales
| RolID | Código | Nombre | Nivel | Sistema |
|-------|--------|--------|-------|---------|
| 6 | SUPERADMIN | SuperAdministrador | 100 | Sí |
| 7 | SUPERVISOR | Supervisor | 50 | No |
| 8 | USUARIO | Usuario | 10 | No |
| 9 | VISOR | Visor | 5 | No |
| 1 | ADMIN | Administrador | 0 | Sí |
| 2 | GERENCIA | Gerencia | 0 | Sí |
| 3 | COMPRAS | Compras | 0 | Sí |
| 4 | VENTAS | Ventas | 0 | Sí |
| 5 | TESORERIA | Tesoreria | 0 | Sí |

### 2.4 Estructura Usuario_Acciones (SQL) - YA EXISTE
```sql
CREATE TABLE Usuario_Acciones (
    AccionID SMALLINT PRIMARY KEY,
    CodigoAccion VARCHAR(30) NOT NULL,   -- VER, CREAR, EDITAR, ELIMINAR, etc.
    NombreAccion VARCHAR(100) NOT NULL,
    Descripcion VARCHAR(250),
    EsAutorizable BIT NOT NULL,
    Activo BIT NOT NULL
)
```

### 2.5 Estructura Usuario_Modulos (SQL) - YA EXISTE
```sql
CREATE TABLE Usuario_Modulos (
    ModuloID INT PRIMARY KEY,
    ModuloPadreID INT,
    CodigoModulo VARCHAR(30) NOT NULL,
    NombreModulo VARCHAR(100) NOT NULL,
    Descripcion VARCHAR(250),
    TipoModulo VARCHAR(20) NOT NULL,
    Ruta VARCHAR(200),
    Icono VARCHAR(100),
    OrdenMenu INT NOT NULL,
    EsVisibleMenu BIT NOT NULL,
    RequiereAutorizacion BIT NOT NULL,
    Activo BIT NOT NULL,
    FechaAlta DATETIME2 NOT NULL,
    FechaModificacion DATETIME2
)
```

### 2.6 Estructura Usuario_PermisosRolModulo (SQL) - YA EXISTE (VACÍA)
```sql
CREATE TABLE Usuario_PermisosRolModulo (
    PermisoRolModuloID BIGINT PRIMARY KEY,
    RolID INT NOT NULL,                   -- FK Usuario_Roles
    ModuloID INT NOT NULL,                -- FK Usuario_Modulos
    AccionID SMALLINT NOT NULL,           -- FK Usuario_Acciones
    Permitido BIT NOT NULL,               -- Si el permiso está activo
    RestriccionPropietario BIT NOT NULL,  -- Solo su propio registro
    RestriccionSucursal BIT NOT NULL,     -- Solo su sucursal
    RequiereAutorizacion BIT NOT NULL,    -- Requiere aprobación
    NivelAutorizacionRequerido SMALLINT,  -- Nivel mínimo para autorizar
    Activo BIT NOT NULL,
    FechaAlta DATETIME2 NOT NULL,
    FechaModificacion DATETIME2,
    CreatedBy VARCHAR(100),
    ModifiedBy VARCHAR(100)
)
```

---

## 3. MAPEO MONGODB → EDARSAHUB SQL

### 3.1 Mapeo de Colecciones

| MongoDB | SQL Destino | Acción |
|---------|-------------|--------|
| `rbac_permisos` | `Usuario_Modulos` + `Usuario_Acciones` | REUTILIZAR tablas existentes + insertar módulos faltantes |
| `rbac_roles` | `Usuario_Roles` | REUTILIZAR (ya tiene estructura similar) |
| `rbac_usuarios_roles` | `Usuario_RolesAsignacion` | REUTILIZAR (ya existe) |
| `rbac_audit_log` | **NUEVA TABLA** `Usuario_LogRBACVerificacion` | CREAR |

### 3.2 Mapeo de Permisos MongoDB → SQL

El sistema MongoDB usa códigos compuestos (`MODULO_ACCION`), mientras que SQL usa una matriz `RolID × ModuloID × AccionID`.

**Ejemplo de transformación:**
```
MongoDB:  permiso.codigo = "CARGOS_VER"
SQL:      RolID + ModuloID (CARGOS) + AccionID (VER) → Usuario_PermisosRolModulo
```

### 3.3 Módulos MongoDB vs SQL (Análisis de Gaps)

| Módulo MongoDB | ModuloID SQL | Estado |
|----------------|--------------|--------|
| `cargos` | - | **FALTA** |
| `responsabilidad` | - | **FALTA** |
| `sla` | - | **FALTA** |
| `workflow` | - | **FALTA** |
| `operativo` | - | **FALTA** |
| `notificaciones` | - | **FALTA** |
| `scheduler` | - | **FALTA** |
| `auditorias` | - | **FALTA** |
| `reportes` | - | **FALTA** |
| `configuracion` | - | **FALTA** |
| `auth` | 1 (SEGURIDAD) | ✅ SIMILAR |
| `compras` | 2,3,4 | ✅ EXISTE |
| `tesoreria` | 5 | ✅ EXISTE |
| `ventas` | 6,7,8 | ✅ EXISTE |

### 3.4 Acciones MongoDB vs SQL

| Acción MongoDB | AccionID SQL | Estado |
|----------------|--------------|--------|
| `ver` | 1 (VER) | ✅ EXISTE |
| `crear` | 2 (CREAR) | ✅ EXISTE |
| `editar` | 3 (EDITAR) | ✅ EXISTE |
| `eliminar` | 4 (ELIMINAR) | ✅ EXISTE |
| `autorizar` | 7 (AUTORIZAR) | ✅ EXISTE |
| `aplicar` | - | **FALTA** (usar EJECUTAR?) |
| `revertir` | - | **FALTA** |
| `configurar` | - | **FALTA** |
| `enviar` | - | **FALTA** |
| `gestionar` | - | **FALTA** |
| `admin` | - | **FALTA** |

---

## 4. DDL PROPUESTO (SOLO SI FALTAN TABLAS)

### 4.1 TABLA NUEVA: Usuario_LogRBACVerificacion
```sql
-- Equivalente a rbac_audit_log de MongoDB
CREATE TABLE Usuario_LogRBACVerificacion (
    LogID BIGINT IDENTITY(1,1) PRIMARY KEY,
    UsuarioID INT NULL,                    -- FK Usuario_Catalogo (puede ser NULL si usuario no existe)
    PublicUUID VARCHAR(36) NULL,           -- UUID del usuario para cross-reference
    Email VARCHAR(150) NULL,
    PermisoRequerido VARCHAR(50) NOT NULL, -- Código del permiso (ej: CARGOS_VER)
    Resultado VARCHAR(20) NOT NULL,        -- 'PERMITIDO' | 'DENEGADO'
    Endpoint VARCHAR(200) NULL,
    MetodoHTTP VARCHAR(10) NULL,
    IPAddress VARCHAR(45) NULL,
    DetallesJSON NVARCHAR(MAX) NULL,       -- JSON con detalles adicionales
    FechaVerificacion DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    INDEX IX_LogRBAC_Usuario (UsuarioID),
    INDEX IX_LogRBAC_Fecha (FechaVerificacion DESC),
    INDEX IX_LogRBAC_Resultado (Resultado, FechaVerificacion DESC)
);
```

### 4.2 INSERTS NECESARIOS EN Usuario_Modulos
```sql
-- Insertar módulos faltantes de EDARSA HUB
INSERT INTO Usuario_Modulos (ModuloID, CodigoModulo, NombreModulo, TipoModulo, OrdenMenu, EsVisibleMenu, RequiereAutorizacion, Activo, FechaAlta)
VALUES 
    (100, 'CARGOS', 'Cargos Económicos', 'OPERATIVO', 100, 1, 1, 1, GETDATE()),
    (101, 'RESPONSABILIDAD', 'Responsabilidad Económica', 'OPERATIVO', 101, 1, 1, 1, GETDATE()),
    (102, 'SLA', 'SLA y Métricas', 'MONITOREO', 102, 1, 0, 1, GETDATE()),
    (103, 'WORKFLOW', 'Workflows', 'OPERATIVO', 103, 1, 0, 1, GETDATE()),
    (104, 'TAREAS', 'Tareas Operativas', 'OPERATIVO', 104, 1, 0, 1, GETDATE()),
    (105, 'NOTIFICACIONES', 'Notificaciones', 'SISTEMA', 105, 1, 0, 1, GETDATE()),
    (106, 'SCHEDULER', 'Programador de Tareas', 'SISTEMA', 106, 0, 1, 1, GETDATE()),
    (107, 'AUDITORIAS', 'Auditorías Programadas', 'OPERATIVO', 107, 1, 0, 1, GETDATE()),
    (108, 'REPORTES', 'Reportes', 'REPORTES', 108, 1, 0, 1, GETDATE()),
    (109, 'CONFIG', 'Configuración Sistema', 'SISTEMA', 109, 0, 1, 1, GETDATE()),
    (110, 'RBAC', 'Gestión RBAC', 'SISTEMA', 110, 0, 1, 1, GETDATE());
```

### 4.3 INSERTS NECESARIOS EN Usuario_Acciones
```sql
-- Insertar acciones faltantes
INSERT INTO Usuario_Acciones (AccionID, CodigoAccion, NombreAccion, Descripcion, EsAutorizable, Activo)
VALUES 
    (11, 'APLICAR', 'Aplicar', 'Aplicar cambio autorizado', 1, 1),
    (12, 'REVERTIR', 'Revertir', 'Revertir cambio aplicado', 1, 1),
    (13, 'CONFIGURAR', 'Configurar', 'Modificar configuración', 0, 1),
    (14, 'ENVIAR', 'Enviar', 'Enviar notificación o documento', 0, 1),
    (15, 'GESTIONAR', 'Gestionar', 'Gestión completa del módulo', 0, 1),
    (16, 'ADMIN', 'Administrar', 'Administración total', 0, 1);
```

### 4.4 INSERTS EN Usuario_Roles (Roles Faltantes)
```sql
-- Insertar roles RBAC que no existen en SQL
INSERT INTO Usuario_Roles (RolID, CodigoRol, NombreRol, Descripcion, EsRolSistema, Activo, FechaAlta, NivelJerarquia)
VALUES 
    (10, 'DIRECCION', 'Dirección', 'Nivel dirección - autoriza montos altos', 1, 1, GETDATE(), 80),
    (11, 'GERENTE_OPS', 'Gerente Operaciones', 'Gerente de operaciones - autoriza y aplica', 1, 1, GETDATE(), 60),
    (12, 'OPERADOR', 'Operador', 'Operador - ejecuta tareas y registra', 1, 1, GETDATE(), 20),
    (13, 'AUDITOR', 'Auditor', 'Auditor - solo lectura para fiscalización', 1, 1, GETDATE(), 30);
```

---

## 5. ESTRATEGIA DE MIGRACIÓN DE DATOS

### 5.1 Secuencia de Migración
```
1. Crear tabla Usuario_LogRBACVerificacion (si se autoriza)
2. Insertar módulos faltantes en Usuario_Modulos
3. Insertar acciones faltantes en Usuario_Acciones
4. Insertar roles faltantes en Usuario_Roles
5. Poblar Usuario_PermisosRolModulo con la matriz de permisos
6. Migrar rbac_audit_log a Usuario_LogRBACVerificacion (opcional, histórico)
7. Actualizar código repository.py para leer de SQL
```

### 5.2 Mapeo de Permisos MongoDB → SQL (Script)
```python
# Ejemplo de transformación
MONGO_PERMISO = "CARGOS_APLICAR"

# Descomponer
modulo = "CARGOS"       # → ModuloID = 100
accion = "APLICAR"      # → AccionID = 11

# Insertar en Usuario_PermisosRolModulo para cada rol que tiene este permiso
INSERT INTO Usuario_PermisosRolModulo (RolID, ModuloID, AccionID, Permitido, ...)
VALUES (6, 100, 11, 1, ...)  -- SUPERADMIN tiene CARGOS_APLICAR
```

---

## 6. ESTRATEGIA DE LECTURA SQL-FIRST

### 6.1 Patrón de Migración Gradual
```
FASE A: Lectura paralela (SQL primero, MongoDB fallback)
FASE B: Lectura SQL exclusiva (MongoDB solo audit/log temporal)
FASE C: Eliminación de código MongoDB
```

### 6.2 Cambios en repository.py
```python
# ANTES (MongoDB):
def get_all_roles(self, activos_only: bool = True) -> List[Dict]:
    filtro = {"activo": True} if activos_only else {}
    return list(self.db.rbac_roles.find(filtro, {"_id": 0}))

# DESPUÉS (SQL-first con fallback):
def get_all_roles(self, activos_only: bool = True) -> List[Dict]:
    try:
        return self._get_roles_sql(activos_only)
    except Exception as e:
        logger.warning(f"[RBAC] Fallback MongoDB: {e}")
        # FALLBACK TEMPORAL (marcar como LEGACY)
        return self._get_roles_mongo_legacy(activos_only)
```

---

## 7. ESTRATEGIA DE FALLBACK TEMPORAL

### 7.1 Durante Transición
- MongoDB permanece como fuente secundaria
- Cada operación intenta SQL primero
- Si SQL falla, usa MongoDB y registra warning
- Log de fallbacks para monitoreo

### 7.2 Condiciones de Eliminación de Fallback
- 7 días sin fallbacks MongoDB
- Todas las funciones SQL validadas
- Autorización explícita para eliminar

---

## 8. ARCHIVOS QUE SE MODIFICARÁN

| Archivo | Cambio | Impacto |
|---------|--------|---------|
| `/app/backend/core/rbac/repository.py` | Agregar métodos SQL, mantener MongoDB como fallback | ALTO |
| `/app/backend/core/rbac/service.py` | Actualizar inicialización para SQL | MEDIO |
| `/app/backend/core/rbac/middleware.py` | Sin cambios (usa service) | NINGUNO |
| `/app/backend/core/rbac/routes.py` | Sin cambios (usa service) | NINGUNO |
| `/app/backend/core/rbac/schemas.py` | Sin cambios | NINGUNO |

---

## 9. ENDPOINTS AFECTADOS

| Endpoint | Impacto | Validación Requerida |
|----------|---------|----------------------|
| `GET /api/v2/rbac/roles` | Leerá de SQL | ✅ |
| `POST /api/v2/rbac/roles` | Escribirá en SQL | ✅ |
| `GET /api/v2/rbac/permisos` | Leerá de SQL | ✅ |
| `POST /api/v2/rbac/asignar` | Escribirá en SQL | ✅ |
| `GET /api/v2/rbac/mis-permisos` | Leerá de SQL | ✅ |
| **Login `/api/auth/login`** | Sin cambio (JWT ya usa SQL) | ✅ SEGURO |

---

## 10. RIESGOS DE REGRESIÓN

| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| Login falla | BAJA | SuperAdministrador bypass se mantiene |
| Permisos incorrectos | MEDIA | Validar matriz SQL vs MongoDB |
| Menús no visibles | MEDIA | Verificar Usuario_Modulos poblado |
| Errores de conexión SQL | BAJA | Fallback MongoDB temporal |

---

## 11. VALIDACIONES OBLIGATORIAS POST-MIGRACIÓN

### 11.1 Pruebas de Regresión
```bash
# 1. Login con admin@inventario.com
curl -X POST /api/auth/login -d '{"email":"admin@inventario.com","password":"admin123"}'

# 2. Verificar mis-permisos
curl -X GET /api/v2/rbac/mis-permisos -H "Authorization: Bearer $TOKEN"

# 3. Listar roles
curl -X GET /api/v2/rbac/roles -H "Authorization: Bearer $TOKEN"

# 4. Verificar Tablero Ejecutivo funciona
curl -X GET /api/v2/comercial/ventas-dia -H "Authorization: Bearer $TOKEN"

# 5. Verificar Comercial V2 funciona
curl -X GET /api/v2/comercial/kpis -H "Authorization: Bearer $TOKEN"
```

### 11.2 Checklist de Validación
- [ ] Login SuperAdministrador funciona
- [ ] Login admin@inventario.com funciona
- [ ] Permisos se cargan correctamente
- [ ] Menú de usuarios visible
- [ ] Roles visibles en admin RBAC
- [ ] Tablero Ejecutivo sin regresión
- [ ] Comercial V2 sin regresión
- [ ] Compras sin regresión
- [ ] Finanzas sin regresión

---

## 12. PLAN DE ROLLBACK

### 12.1 Rollback Inmediato
```python
# En repository.py: Cambiar flag
USE_SQL_RBAC = False  # Cambiar a False restaura MongoDB como fuente primaria
```

### 12.2 Rollback por DDL
- Las tablas nuevas son aditivas (no destruyen datos existentes)
- Usuario_PermisosRolModulo puede vaciarse sin impacto (MongoDB sigue teniendo los datos)

---

## 13. CONFIRMACIÓN: FASE2 OPERATIVO FUERA DE ALCANCE

| Módulo | En Alcance FASE 4B-RBAC |
|--------|-------------------------|
| core/rbac | ✅ SÍ |
| modules/auth | ❌ NO (ya migrado) |
| **modules/fase2_operativo** | ❌ **NO - EXCLUIDO** |
| modules/comercial | ❌ NO |
| modules/comercial_v2 | ❌ NO |
| modules/compras | ❌ NO |
| modules/finanzas | ❌ NO |

---

## 14. RESUMEN DE ACCIONES PROPUESTAS

### Requieren Autorización:
1. ⚠️ **Crear tabla** `Usuario_LogRBACVerificacion`
2. ⚠️ **Insertar módulos** faltantes en `Usuario_Modulos`
3. ⚠️ **Insertar acciones** faltantes en `Usuario_Acciones`
4. ⚠️ **Insertar roles** faltantes en `Usuario_Roles`
5. ⚠️ **Poblar** `Usuario_PermisosRolModulo` con matriz de permisos
6. ⚠️ **Modificar** `/app/backend/core/rbac/repository.py` para SQL-first

### No Requieren Autorización:
- Actualizar tests (si existen)
- Documentación

---

## 15. DECISIONES PENDIENTES DEL USUARIO

1. **¿Crear nueva tabla `Usuario_LogRBACVerificacion`?**  
   - Opción A: Sí, para auditoría SQL completa
   - Opción B: No, mantener audit en MongoDB temporalmente

2. **¿Migrar datos históricos de `rbac_audit_log`?**  
   - Opción A: Sí, migrar ~600 registros
   - Opción B: No, empezar desde cero en SQL

3. **¿Usar IDs autoincrementales o UUIDs en SQL?**  
   - Recomendación: IDs autoincrementales (consistente con estructura existente)

4. **¿Cuándo iniciar la implementación?**  
   - Tras autorización explícita

---

**Propuesta generada:** 2026-05-14  
**Estado:** PENDIENTE AUTORIZACIÓN  
**Sin modificaciones de código realizadas**
