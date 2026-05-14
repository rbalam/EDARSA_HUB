# FASE 3-A: Diagnóstico Pasivo de Empresas/Sucursales/Mapeos hacia EDARSAHUB SQL

**Fecha:** 2026-05-14  
**Fase:** FASE 3-A (Diagnóstico Pasivo)  
**Estado:** COMPLETADA  
**Autor:** Agente E1  
**Régimen:** Autorización Controlada

---

## 1. Resumen Ejecutivo

### Hallazgos Principales:
1. **4 colecciones MongoDB** son fuente productiva de empresas/sucursales:
   - `db.empresas` (19 referencias)
   - `db.sucursales_catalogo` (10 referencias)
   - `db.sucursal_servidor_map` (6 referencias)
   - `db.server_sucursales_config` (12 referencias)

2. **Tablas SQL equivalentes ya existen:**
   - `Sistema_Empresas` (5 empresas activas)
   - `Sistema_EmpresasMongoMap` (5 mapeos UUID→SQL)
   - `Unidades_Negocio` (5 unidades)
   - `Servidores_Conexiones` (con columna `EmpresaID`)

3. **Tablas SQL faltantes:**
   - Sucursales canónicas (equivalente a `db.sucursales_catalogo`)
   - Mapeo sucursal→servidor (equivalente a `db.sucursal_servidor_map`)
   - Configuración servidor→sucursales (equivalente a `db.server_sucursales_config`)

4. **Archivos críticos (P0):**
   - `/app/backend/core/context_resolver.py` - 42 referencias MongoDB
   - `/app/backend/core/user_access_context.py` - 42 referencias MongoDB
   - `/app/backend/modules/auth/context_service.py` - 46 referencias MongoDB
   - `/app/backend/core/security.py` - 50 referencias empresas/sucursales

---

## 2. Dependencias MongoDB Encontradas

### 2.1. db.empresas (19 referencias)

| # | Archivo | Función/Línea | Tipo de Uso | Módulo |
|---|---------|---------------|-------------|--------|
| 1 | `context_resolver.py:83` | `get_user_unidades_negocio()` | Lectura | Context |
| 2 | `context_resolver.py:269` | `resolve_unidad_context()` | Lectura | Context |
| 3 | `user_access_context.py:276` | `_resolver_acceso_global()` | Lectura | Context |
| 4 | `context_service.py:55,66,144,200` | Múltiples funciones | Lectura | Auth |
| 5 | `security.py:485,495` | `get_user_empresas_permitidas()` | Lectura | Auth |
| 6 | `tesoreria.py:39` | Listado de empresas | Lectura | Finanzas |
| 7 | `cuentas_por_pagar.py:69` | Listado de empresas | Lectura | Finanzas |
| 8 | `routes_edarsahub.py:77` | Propinas TPV | Lectura | Finanzas |
| 9 | `propinas_tpv/routes.py:141` | Propinas TPV | Lectura | Finanzas |
| 10 | `rh/routes.py:138` | Listado de empresas | Lectura | RH |
| 11 | `config_asignaciones_repository.py:127,238` | Configuración | Lectura | Config |
| 12 | `pedidos_detector_job.py:424` | Scheduler | Lectura | Scheduler |
| 13 | `carga_historica_fase23.py:149` | Script migración | Lectura | Scripts |

### 2.2. db.sucursales_catalogo (10 referencias)

| # | Archivo | Función/Línea | Tipo de Uso | Módulo |
|---|---------|---------------|-------------|--------|
| 1 | `context_resolver.py:90` | `get_user_unidades_negocio()` | Lectura | Context |
| 2 | `context_resolver.py:253` | Resolución de contexto | Lectura | Context |
| 3 | `user_access_context.py:293` | `_resolver_servers_desde_empresas()` | Lectura | Context |
| 4 | `context_service.py:102,170` | Contexto de UI | Lectura | Auth |
| 5 | `security.py:515` | Resolución de permisos | Lectura | Auth |
| 6 | `alcance_helper.py:68,87` | Helper de alcance | Lectura | Core |
| 7 | `config_asignaciones_repository.py:135` | Configuración | Lectura | Config |
| 8 | `pedidos_detector_job.py:434` | Scheduler | Lectura | Scheduler |

### 2.3. db.sucursal_servidor_map (6 referencias)

| # | Archivo | Función/Línea | Tipo de Uso | Módulo |
|---|---------|---------------|-------------|--------|
| 1 | `context_resolver.py:98` | `get_user_unidades_negocio()` | Lectura | Context |
| 2 | `context_resolver.py:238` | `resolve_unidad_context()` | Lectura | Context |
| 3 | `user_access_context.py:304` | `_resolver_servers_desde_empresas()` | Lectura | Context |
| 4 | `security.py:523` | Resolución de mapeos | Lectura | Auth |
| 5 | `config_asignaciones_repository.py:144` | Configuración | Lectura | Config |
| 6 | `pedidos_detector_job.py:445` | Scheduler | Lectura | Scheduler |

### 2.4. db.server_sucursales_config (12 referencias)

| # | Archivo | Función/Línea | Tipo de Uso | Módulo |
|---|---------|---------------|-------------|--------|
| 1 | `server.py:2098,2359,2418` | Endpoints configuración | Lectura | Server |
| 2 | `server.py:2435,2461,2508` | Endpoints configuración | Escritura | Server |
| 3 | `server.py:2465,2542,2573` | Endpoints configuración | Lectura/Escritura | Server |
| 4 | `asignacion_repository.py:20` | Repository | Lectura | Fase2 |
| 5 | `server_registry.py:778` | Registry de servidores | Lectura | Core |

---

## 3. Endpoints Afectados

| Endpoint | Archivo | Colección MongoDB | Tipo | Prioridad |
|----------|---------|-------------------|------|-----------|
| `GET /api/context/unidades` | context_resolver.py | empresas, sucursales, mapeos | Lectura | P0 |
| `GET /api/auth/context` | context_service.py | empresas, sucursales | Lectura | P0 |
| `GET /api/finanzas/tesoreria/*` | tesoreria.py | empresas | Lectura | P1 |
| `GET /api/finanzas/cuentas-por-pagar` | cuentas_por_pagar.py | empresas | Lectura | P1 |
| `GET /api/servers/*` (configuración) | server.py | server_sucursales_config | R/W | P1 |
| `POST /api/servers/*/sucursales` | server.py | server_sucursales_config | Escritura | P1 |
| `GET /api/comercial/*` | comercial/routes.py | empresas via security | Lectura | P1 |
| `GET /api/rh/empresas` | rh/routes.py | empresas | Lectura | P2 |
| `GET /api/config/asignaciones/*` | config_asignaciones | empresas, sucursales | Lectura | P2 |

---

## 4. Archivos Afectados

### P0 - Críticos (Context/Auth)
| Archivo | Referencias MongoDB | Impacto |
|---------|---------------------|---------|
| `/app/backend/core/context_resolver.py` | 42 | Define qué unidades ve el usuario |
| `/app/backend/core/user_access_context.py` | 42 | Resuelve acceso efectivo |
| `/app/backend/modules/auth/context_service.py` | 46 | Contexto de navegación UI |
| `/app/backend/core/security.py` | 50 | Funciones de permisos empresas |

### P1 - Funcionales (Módulos principales)
| Archivo | Referencias MongoDB | Impacto |
|---------|---------------------|---------|
| `/app/backend/modules/finanzas/tesoreria.py` | 3 | Filtro de empresas |
| `/app/backend/modules/finanzas/cuentas_por_pagar.py` | 2 | Filtro de empresas |
| `/app/backend/server.py` | 12 | Configuración sucursales |
| `/app/backend/core/server_registry.py` | 1 | Registry de servidores |

### P2 - Configuración
| Archivo | Referencias MongoDB | Impacto |
|---------|---------------------|---------|
| `/app/backend/modules/configuracion/repositories/config_asignaciones_repository.py` | 4 | Configuración de asignaciones |
| `/app/backend/modules/rh/routes.py` | 1 | Listado empresas RH |
| `/app/backend/core/alcance_helper.py` | 2 | Helper de alcance |

### P3 - Scheduler/Scripts
| Archivo | Referencias MongoDB | Impacto |
|---------|---------------------|---------|
| `/app/backend/core/scheduler/jobs/pedidos_detector_job.py` | 3 | Job de pedidos |
| `/app/backend/scripts/carga_historica_fase23.py` | 1 | Script de carga |

---

## 5. Tablas SQL Existentes Útiles

### Sistema_Empresas ✅
```sql
EmpresaID | CodigoEmpresa | NombreEmpresa | Activo
1         | ORIGEN        | ORIGEN        | True
2         | 130QRO        | 130 QRO       | True
3         | CIENFUEGOS    | CIENFUEGOS    | True
4         | ESTELAR       | LA ESTELAR    | True
5         | 130MID        | 130 MID       | True
```
**Uso:** Reemplaza `db.empresas` para catálogo de empresas.

### Sistema_EmpresasMongoMap ✅
```sql
MapID | EmpresaMongoUUID | EmpresaID_SQL | CodigoEmpresa
1     | 31784356-...     | 1             | ORIGEN
2     | 1118f83c-...     | 2             | 130QRO
3     | 1d91f076-...     | 3             | CIENFUEGOS
4     | e302e16f-...     | 4             | ESTELAR
5     | a4d8b5e7-...     | 5             | 130MID
```
**Uso:** Traduce UUIDs de MongoDB a IDs de SQL.

### Usuario_EmpresasAsignacion ✅
**Ya en uso** por RBAC-SCOPE-G para asignación de empresas a usuarios.

### Servidores_Conexiones ✅
```sql
Columnas relevantes:
- id (uniqueidentifier)
- nombre
- system_type
- EmpresaID (FK a Sistema_Empresas)
- visible_en_operaciones
- activo
```
**Uso:** Ya tiene `EmpresaID` que vincula servidor con empresa.

### Unidades_Negocio ✅
```sql
nombre | codigo | server_id | system_type | activo
ORIGEN | ORIGEN | ...       | MPRO        | True
```
**Uso:** Alternativa a context_resolver para unidades de negocio.

---

## 6. Tablas SQL Faltantes

### 6.1. Sistema_Sucursales (NUEVA)
**Propósito:** Reemplazar `db.sucursales_catalogo`

```sql
CREATE TABLE Sistema_Sucursales (
    SucursalID INT IDENTITY(1,1) PRIMARY KEY,
    CodigoSucursal VARCHAR(50) NOT NULL,
    NombreSucursal NVARCHAR(200) NOT NULL,
    EmpresaID INT NOT NULL FOREIGN KEY REFERENCES Sistema_Empresas(EmpresaID),
    MongoUUID VARCHAR(36) NULL,  -- Para migración
    Activa BIT NOT NULL DEFAULT 1,
    FechaAlta DATETIME2 NOT NULL DEFAULT GETDATE(),
    CreatedBy VARCHAR(100)
);
```

### 6.2. Sistema_SucursalServidorMap (NUEVA)
**Propósito:** Reemplazar `db.sucursal_servidor_map`

```sql
CREATE TABLE Sistema_SucursalServidorMap (
    MapeoID INT IDENTITY(1,1) PRIMARY KEY,
    SucursalID INT NOT NULL FOREIGN KEY REFERENCES Sistema_Sucursales(SucursalID),
    ServidorID UNIQUEIDENTIFIER NOT NULL,  -- FK a Servidores_Conexiones
    SucursalOrigenID VARCHAR(50) NULL,  -- ID en sistema externo (MPRO)
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME2 NOT NULL DEFAULT GETDATE(),
    CreatedBy VARCHAR(100)
);
```

### 6.3. Sistema_ServidorSucursalesConfig (NUEVA)
**Propósito:** Reemplazar `db.server_sucursales_config`

```sql
CREATE TABLE Sistema_ServidorSucursalesConfig (
    ConfigID INT IDENTITY(1,1) PRIMARY KEY,
    ServidorID UNIQUEIDENTIFIER NOT NULL,
    SucursalNombre NVARCHAR(200) NOT NULL,
    SucursalCodigo VARCHAR(50) NULL,
    VisibleEnOperaciones BIT NOT NULL DEFAULT 0,
    VisibleEnComercial BIT NOT NULL DEFAULT 0,
    Activo BIT NOT NULL DEFAULT 1,
    FechaCreacion DATETIME2 NOT NULL DEFAULT GETDATE(),
    FechaModificacion DATETIME2 NULL,
    CreatedBy VARCHAR(100)
);
```

---

## 7. Matriz MongoDB → SQL

| Colección MongoDB | Tabla SQL Existente | Tabla SQL Faltante | Estado |
|-------------------|--------------------|--------------------|--------|
| `db.empresas` | `Sistema_Empresas` + `Sistema_EmpresasMongoMap` | - | ✅ Listo |
| `db.sucursales_catalogo` | - | `Sistema_Sucursales` | ❌ Crear |
| `db.sucursal_servidor_map` | - | `Sistema_SucursalServidorMap` | ❌ Crear |
| `db.server_sucursales_config` | - | `Sistema_ServidorSucursalesConfig` | ❌ Crear |

---

## 8. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| `context_resolver.py` rompe múltiples módulos | Alta | Crítico | Migrar gradualmente con feature flag |
| `user_access_context.py` afecta permisos globales | Alta | Crítico | Validar con usuarios SUPERADMIN primero |
| Escritura en `server_sucursales_config` | Media | Alto | Migrar lectura antes que escritura |
| Jobs del scheduler fallan | Baja | Medio | Son procesos batch, pueden esperar |

---

## 9. Propuesta de Fases

### FASE 3-B: DDL y Migración de Datos (P0)
1. Crear tablas SQL faltantes
2. Migrar datos de MongoDB a SQL:
   - `db.sucursales_catalogo` → `Sistema_Sucursales`
   - `db.sucursal_servidor_map` → `Sistema_SucursalServidorMap`
   - `db.server_sucursales_config` → `Sistema_ServidorSucursalesConfig`
3. Validar integridad de datos

### FASE 3-C: Migración de Lectura (P0)
1. Crear funciones SQL equivalentes en `user_repository_sql.py`
2. Migrar `context_resolver.py` a SQL
3. Migrar `user_access_context.py` a SQL
4. Migrar funciones empresas/sucursales de `security.py` a SQL

### FASE 3-D: Migración de Context Service (P0)
1. Migrar `context_service.py` a SQL
2. Validar navegación UI funciona

### FASE 3-E: Migración de Escritura (P1)
1. Migrar endpoints de configuración en `server.py` a SQL
2. Migrar `config_asignaciones_repository.py` a SQL

### FASE 3-F: Migración de Módulos (P1)
1. Migrar Finanzas (tesoreria, cuentas_por_pagar)
2. Migrar Comercial
3. Migrar RH

### FASE 3-G: Validación y Cierre (P2)
1. Validar todos los módulos
2. Documentar referencias MongoDB residuales
3. Cerrar FASE 3

---

## 10. Reglas de Nomenclatura SQL Aplicables

Según el patrón existente en EDARSAHUB:

| Grupo | Prefijo | Ejemplos Existentes |
|-------|---------|---------------------|
| Sistema/Config | `Sistema_` | `Sistema_Empresas`, `Sistema_EmpresasMongoMap` |
| Usuarios | `Usuario_` | `Usuario_Catalogo`, `Usuario_EmpresasAsignacion` |
| Servidores | `Servidores_` | `Servidores_Conexiones`, `Servidores_Conexiones_Log` |
| RH | `RH_` | `RH_Cat_Sucursales` |
| Finanzas | `Finanzas_` | `Finanzas_ConfiguracionTPV_Sucursal` |

**Nuevas tablas deben seguir:**
- `Sistema_Sucursales` (no `Sucursales_Catalogo`)
- `Sistema_SucursalServidorMap` (no `Sucursal_Servidor_Map`)
- `Sistema_ServidorSucursalesConfig` (no `Server_Sucursales_Config`)

---

## 11. Criterios de Aceptación para FASE 3-B

FASE 3-B puede autorizarse si:

1. ✅ Se identificaron las 4 colecciones MongoDB afectadas
2. ✅ Se definieron las 3 tablas SQL faltantes con DDL propuesto
3. ✅ Se mapearon las 5 empresas existentes SQL ↔ MongoDB
4. ✅ Se identificaron los 4 archivos críticos P0
5. ✅ Se propuso orden de fases sin tocar producción
6. ✅ Se generó este reporte

---

## 12. Recomendación de Orden de Implementación

### Orden recomendado:
```
1. FASE 3-B: DDL y Migración de Datos
   └── Crear tablas, migrar datos, validar

2. FASE 3-C: Migración de Context Resolver
   └── Punto más crítico - define qué ve cada usuario

3. FASE 3-D: Migración de Context Service
   └── Navegación UI

4. FASE 3-E: Migración de Escritura (server.py)
   └── Configuración de sucursales

5. FASE 3-F: Migración de Módulos
   └── Finanzas, Comercial, RH (pueden ser en paralelo)

6. FASE 3-G: Validación y Cierre
```

### Dependencias:
- FASE 3-C requiere FASE 3-B completada
- FASE 3-D requiere FASE 3-C completada
- FASE 3-E y 3-F pueden ejecutarse en paralelo después de 3-D

---

## Resumen Ejecutivo

| Aspecto | Estado |
|---------|--------|
| Colecciones MongoDB identificadas | 4 |
| Referencias totales | 47 |
| Archivos P0 (críticos) | 4 |
| Tablas SQL existentes útiles | 5 |
| Tablas SQL faltantes | 3 |
| DDL propuesto | ✅ |
| Ruta de migración definida | ✅ |

**FASE 3-A: COMPLETADA (Diagnóstico Pasivo)**

**Próximo paso:** Solicitar autorización para FASE 3-B (DDL y Migración de Datos).
