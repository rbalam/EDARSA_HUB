# AUDITORÍA DE DEPENDENCIAS MONGODB → EDARSAHUB SQL

**Fecha:** 14-Dic-2025  
**Autor:** Agente E1 (Ingeniero Senior / Arquitecto de Datos)  
**Estado:** DIAGNÓSTICO PASIVO COMPLETADO  
**Objetivo:** Mapear todas las dependencias de MongoDB para migración a EDARSAHUB SQL Server

---

## RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| Archivos con AsyncIOMotorClient | 18 |
| Referencias a MONGO_URL | 30+ |
| Referencias a `db.servers` activas | 5 (después de P1.4-B/C/E) |
| Referencias a `db.users` | 40+ |
| Referencias a `db.empresas` | 18 |
| Referencias a `db.sucursales_catalogo` | 12 |
| Referencias a `db.sucursal_servidor_map` | 8 |
| Referencias a `db.roles` / `rbac_*` | 28 |
| Colecciones MongoDB identificadas | 22+ |
| Operaciones `.find()` / `.to_list()` | 281 |
| Operaciones `.insert_one` / `.update_one` | 223 |

### Veredicto Global

```
⚠️ MONGODB ES AÚN FUENTE PRIMARIA PARA:
- Autenticación y usuarios (P0)
- RBAC y permisos (P0)
- Empresas y sucursales (P0)
- Mapeos sucursal↔servidor (P0)
- Configuración de UI de sucursales (P1)
- Alertas, queries, cache (P2-P3)

✅ EDARSAHUB SQL YA ES FUENTE PRIMARIA PARA:
- Conexiones de servidores (Servidores_Conexiones)
- Unidades de negocio (Unidades_Negocio)
- Catálogos operativos (EDARSAHUB_CONFIG)
```

---

## 1. MATRIZ DE COLECCIONES MONGODB

### 1.1 COLECCIONES P0 (CRÍTICAS — Bloquean operación)

| Colección | Uso | Archivos | Tabla SQL Existente | Tabla SQL Faltante | Riesgo |
|-----------|-----|----------|--------------------|--------------------|--------|
| `db.users` | AUTH, USUARIOS | 15+ archivos | ❌ Parcial (`Usuarios` básico) | `Usuarios` completo con permisos | **ALTO** |
| `db.roles` | RBAC | 1 archivo | ❌ No | `Roles`, `Permisos` | **ALTO** |
| `db.rbac_roles` | RBAC | 3 archivos | ❌ No | `RBAC_Roles` | **ALTO** |
| `db.rbac_usuarios_roles` | RBAC | 4 archivos | ❌ No | `RBAC_Usuarios_Roles` | **ALTO** |
| `db.servers` | CONEXIONES | 5 activas, 82 total | ✅ `Servidores_Conexiones` | N/A | **MEDIO** (en migración) |
| `db.empresas` | MULTI-EMPRESA | 18 archivos | ❌ Parcial | `Empresas` completo | **ALTO** |
| `db.sucursales_catalogo` | MULTI-SUCURSAL | 12 archivos | ❌ No | `Sucursales_Catalogo` | **ALTO** |
| `db.sucursal_servidor_map` | MAPEO SUC↔SRV | 8 archivos | ✅ Parcial (`Unidades_Negocio`) | Completar campos | **MEDIO** |

### 1.2 COLECCIONES P1 (CONFIGURACIÓN — Afectan funcionalidad)

| Colección | Uso | Archivos | Tabla SQL Existente | Tabla SQL Faltante | Riesgo |
|-----------|-----|----------|--------------------|--------------------|--------|
| `db.server_sucursales_config` | CONFIG UI | 8 referencias | ❌ No | `Servidores_Sucursales_Config` | **MEDIO** |
| `db.queries` | TEMPLATES SQL | 5 referencias | ❌ No | `Consultas_Templates` | **MEDIO** |
| `db.consultas_custom` | QUERIES CUSTOM | 2 referencias | ❌ No | `Consultas_Custom` | **BAJO** |
| `db.config_catalogos` | CONFIG CATÁLOGOS | 1 referencia | ❌ No | `Config_Catalogos` | **BAJO** |

### 1.3 COLECCIONES P2 (CACHE — Pueden ser temporales)

| Colección | Uso | Archivos | Puede ser Cache? | Propuesta |
|-----------|-----|----------|------------------|-----------|
| `db.kpis_cache` | CACHE KPIs | 3 referencias | ✅ SÍ | Mantener como cache |
| `db.inventario_diferencias_cache` | CACHE INV | 3 referencias | ✅ SÍ | Mantener como cache |
| `db.inventario_diferencias_detalle` | CACHE DETALLE | 4 referencias | ✅ SÍ | Mantener como cache |
| `db.server_status` | STATUS CONEXIÓN | 4 referencias | ✅ SÍ | Mantener como cache |

### 1.4 COLECCIONES P3 (LOGS/AUDITORÍA — Pueden quedarse)

| Colección | Uso | Archivos | Propuesta |
|-----------|-----|----------|-----------|
| `db.alerts` | ALERTAS | 5 referencias | Migrar a SQL o mantener |
| `db.script_logs` | LOGS SCRIPTS | 1 referencia | Mantener en Mongo |
| `db.informes_auditoria` | AUDITORÍAS | 5 referencias | Migrar a SQL |

---

## 2. MATRIZ DE ENDPOINTS POR DEPENDENCIA

### 2.1 Endpoints que usan `db.users` (P0)

| Endpoint | Archivo | Función | Criticidad |
|----------|---------|---------|------------|
| `POST /auth/login` | `core/security.py` | Autenticación | **P0** |
| `GET /auth/me` | `core/security.py` | Contexto usuario | **P0** |
| `GET /admin/users` | `server.py:14241` | Listar usuarios | **P0** |
| `PUT /users/{id}/password` | `server.py:13452-13472` | Cambiar password | **P0** |
| `POST /admin/users/{id}/empresas` | `server.py:15212-15260` | Asignar empresas | **P0** |
| Varios endpoints RBAC | `server.py:15400+` | Asignación roles | **P0** |
| `modules/auth/context_service.py` | Varias funciones | Contexto usuario | **P0** |
| `modules/auth/password_reset.py` | Reset password | Recuperación | **P0** |
| `modules/fase2_operativo/*` | Automatización | Notificaciones | **P1** |
| `modules/configuracion/*` | Config asignaciones | CRUD | **P1** |

### 2.2 Endpoints que usan `db.empresas` (P0)

| Endpoint | Archivo | Función | Criticidad |
|----------|---------|---------|------------|
| `GET /empresas` | `modules/finanzas/tesoreria.py` | Listar empresas | **P0** |
| `GET /rh/empresas` | `modules/rh/routes.py` | RH empresas | **P1** |
| `modules/auth/context_service.py` | Contexto | Multi-empresa | **P0** |
| `core/security.py:363-373` | Filtros | Permisos | **P0** |
| `core/context_resolver.py` | Resolver | Alcance | **P0** |
| `core/user_access_context.py` | Acceso | RBAC | **P0** |

### 2.3 Endpoints que usan `db.sucursales_catalogo` (P0)

| Endpoint | Archivo | Función | Criticidad |
|----------|---------|---------|------------|
| `modules/auth/context_service.py` | Contexto | Multi-sucursal | **P0** |
| `core/security.py:393` | Filtros | Permisos | **P0** |
| `core/context_resolver.py` | Resolver | Alcance | **P0** |
| `core/alcance_helper.py` | Helper | RBAC | **P0** |
| `modules/comercial/repository.py` | Comercial | Dashboard | **P1** |
| `modules/configuracion/*` | Config | Asignaciones | **P1** |

### 2.4 Endpoints que usan `db.servers` (En migración)

| Endpoint | Estado | Fase |
|----------|--------|------|
| CRUD `/api/servers` | ✅ MIGRADO | P1.4-A |
| `/api/servers/{id}/queries/*` | ✅ MIGRADO | P1.4-B |
| `/api/reports/inventory*` | ✅ MIGRADO | P1.4-C |
| `/api/compras/auditoria-operativa` | ✅ MIGRADO | P1.4-E1 |
| `/api/dashboard/inventory-summary` | ✅ MIGRADO | P1.4-E2 |
| `/api/reports/export/comparativo-inventarios` | ✅ MIGRADO | P1.4-E3 |
| `/api/explorador/ejecutar-con-credenciales/{id}` | ⏸️ PENDIENTE | P1.4-E4 |
| `/api/catalogo/ejecutar-rich/{consulta_id}` | ⏸️ PENDIENTE | P1.4-E4 |
| `modules/configuracion/repositories/*` | ⏸️ PENDIENTE | P1.4-F |
| `modules/comercial/historical_kpis_repository.py` | ⚠️ ACTIVO | Legacy |
| Scripts de carga histórica | ⚠️ ACTIVO | Legacy |

---

## 3. TABLAS SQL EXISTENTES EN EDARSAHUB

| Tabla | Propósito | Campos Clave | Estado |
|-------|-----------|--------------|--------|
| `Servidores_Conexiones` | Conexiones a servidores | id, host, port, database_name, username, password_encrypted, system_type, tipos_movimiento, etc. | ✅ EN USO |
| `Unidades_Negocio` | Mapeo unidad↔servidor | codigo, nombre, server_id, sucursal_origen_id, empresa, visible_en_operaciones | ✅ EN USO |
| `tipos_movimiento` (EDARSAHUB_CONFIG) | Catálogo movimientos | codigo, descripcion, tipo_modificador | ✅ EN USO |
| `categorias` (EDARSAHUB_CONFIG) | Catálogo categorías | codigo, descripcion | ✅ EN USO |
| `departamentos` (EDARSAHUB_CONFIG) | Catálogo departamentos | codigo, descripcion | ✅ EN USO |
| `Usuarios` (parcial) | Usuarios básicos | (verificar campos) | ⚠️ PARCIAL |
| `Empresas` (parcial) | Empresas | (verificar campos) | ⚠️ PARCIAL |

---

## 4. TABLAS SQL FALTANTES (PROPUESTA DDL)

### 4.1 `Usuarios` (Completar)

```sql
-- Ya existe parcialmente, completar con:
ALTER TABLE dbo.Usuarios ADD
    empresas_permitidas NVARCHAR(MAX),  -- JSON array
    sucursales_permitidas NVARCHAR(MAX), -- JSON array
    rol_principal VARCHAR(50),
    permisos_especiales NVARCHAR(MAX),  -- JSON
    ultimo_login DATETIME2,
    activo BIT DEFAULT 1;
```

### 4.2 `RBAC_Roles` (Nueva)

```sql
CREATE TABLE dbo.RBAC_Roles (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    nombre NVARCHAR(100) NOT NULL UNIQUE,
    descripcion NVARCHAR(500),
    permisos NVARCHAR(MAX),  -- JSON array de permisos
    activo BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2
);
```

### 4.3 `RBAC_Usuarios_Roles` (Nueva)

```sql
CREATE TABLE dbo.RBAC_Usuarios_Roles (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    rol_id UNIQUEIDENTIFIER NOT NULL,
    empresa_id VARCHAR(50),
    sucursal_id VARCHAR(50),
    activo BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT UQ_RBAC_User_Rol_Suc UNIQUE(user_id, rol_id, sucursal_id)
);
```

### 4.4 `Sucursales_Catalogo` (Nueva)

```sql
CREATE TABLE dbo.Sucursales_Catalogo (
    id VARCHAR(50) PRIMARY KEY,
    nombre NVARCHAR(200) NOT NULL,
    empresa_id VARCHAR(50),
    direccion NVARCHAR(500),
    telefono VARCHAR(50),
    activa BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE()
);
```

### 4.5 `Servidores_Sucursales_Config` (Nueva)

```sql
CREATE TABLE dbo.Servidores_Sucursales_Config (
    id INT IDENTITY(1,1) PRIMARY KEY,
    server_id VARCHAR(50) NOT NULL,
    sucursal_origen_id VARCHAR(50) NOT NULL,
    sucursal_nombre_origen NVARCHAR(200),
    nombre_visible NVARCHAR(200),
    visible_en_operaciones BIT DEFAULT 1,
    activa BIT DEFAULT 1,
    orden INT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    CONSTRAINT UQ_Server_Sucursal UNIQUE(server_id, sucursal_origen_id)
);
```

---

## 5. ANÁLISIS DE RIESGO

### 5.1 Si se apaga MongoDB HOY:

| Sistema | Impacto | Motivo |
|---------|---------|--------|
| **Login/Auth** | 🔴 FATAL | `db.users` es fuente primaria |
| **RBAC/Permisos** | 🔴 FATAL | `db.rbac_*` sin equivalente SQL |
| **Multi-empresa** | 🔴 FATAL | `db.empresas` sin equivalente SQL |
| **Multi-sucursal** | 🔴 FATAL | `db.sucursales_catalogo` sin equivalente SQL |
| **Servidores** | 🟡 PARCIAL | `server_registry` usa SQL pero algunos endpoints legacy fallarían |
| **Comercial** | 🟡 PARCIAL | Tablero funciona, algunos legacy fallarían |
| **Finanzas** | 🟡 PARCIAL | Tesorería funciona, propinas dependen de empresas |
| **Inventarios** | 🟢 OK | Migrado a server_registry |
| **Cache/KPIs** | 🟢 OK | Cache no crítico |

### 5.2 Dependencias que pueden eliminarse de inmediato:

1. ❌ **Ninguna P0 puede eliminarse sin migración**
2. ⚠️ Scripts de carga histórica (solo batch)
3. ⚠️ Scripts de reconciliación (solo mantenimiento)

### 5.3 Dependencias que requieren doble lectura temporal:

1. `db.users` → Leer SQL primero, fallback Mongo
2. `db.empresas` → Leer SQL primero, fallback Mongo
3. `db.sucursales_catalogo` → Leer SQL primero, fallback Mongo
4. `db.rbac_*` → Leer SQL primero, fallback Mongo

### 5.4 Dependencias que pueden quedarse como cache:

1. `db.kpis_cache` — Cache analítico
2. `db.inventario_diferencias_*` — Cache de reportes
3. `db.server_status` — Status temporal
4. `db.script_logs` — Logs de scripts

---

## 6. PROPUESTA DE FASES DE MIGRACIÓN

### FASE 1: Completar migración de `db.servers` (EN CURSO)

| Subfase | Descripción | Estado |
|---------|-------------|--------|
| P1.4-B | Endpoints de Queries | ✅ CERRADO |
| P1.4-C | Endpoints de Inventario/Reportes | ✅ CERRADO |
| P1.4-D1 | Sucursales-config (diagnóstico) | ✅ CERRADO |
| P1.4-E1 | Auditoría Operativa | ✅ CERRADO |
| P1.4-E2 | Dashboard Inventory | ✅ CERRADO |
| P1.4-E3 | Comparativo Inventarios | ✅ CERRADO |
| P1.4-E4 | Explorador/Catálogo | ⏸️ PENDIENTE |
| P1.4-F | Módulo Configuración | ⏸️ PENDIENTE |

**Resultado:** `db.servers` eliminado como fuente funcional en server.py

---

### FASE 2: Migrar Auth/Users/Roles a EDARSAHUB SQL

| Paso | Acción | Riesgo |
|------|--------|--------|
| 2.1 | Crear/completar tabla `Usuarios` en EDARSAHUB | BAJO |
| 2.2 | Crear tablas `RBAC_Roles`, `RBAC_Usuarios_Roles` | BAJO |
| 2.3 | Migrar datos existentes de MongoDB a SQL | MEDIO |
| 2.4 | Crear `user_repository.py` centralizado | BAJO |
| 2.5 | Implementar dual-read (SQL primero, Mongo fallback) | MEDIO |
| 2.6 | Migrar `core/security.py` a user_repository | ALTO |
| 2.7 | Migrar `modules/auth/context_service.py` | ALTO |
| 2.8 | Validar login, /me, permisos | CRÍTICO |
| 2.9 | Desactivar fallback MongoDB | MEDIO |

**Duración estimada:** 3-5 fases con autorización

---

### FASE 3: Migrar Empresas/Sucursales a EDARSAHUB SQL

| Paso | Acción | Riesgo |
|------|--------|--------|
| 3.1 | Crear/completar tabla `Empresas` en EDARSAHUB | BAJO |
| 3.2 | Crear tabla `Sucursales_Catalogo` | BAJO |
| 3.3 | Verificar/completar `Unidades_Negocio` como mapeo | BAJO |
| 3.4 | Migrar datos existentes | MEDIO |
| 3.5 | Crear `empresa_repository.py`, `sucursal_repository.py` | BAJO |
| 3.6 | Implementar dual-read | MEDIO |
| 3.7 | Migrar `core/context_resolver.py` | ALTO |
| 3.8 | Migrar `core/user_access_context.py` | ALTO |
| 3.9 | Migrar `core/alcance_helper.py` | ALTO |
| 3.10 | Validar multi-empresa, multi-sucursal | CRÍTICO |

**Duración estimada:** 3-5 fases con autorización

---

### FASE 4: Migrar configuraciones vivas a EDARSAHUB SQL

| Paso | Acción | Riesgo |
|------|--------|--------|
| 4.1 | Crear tabla `Servidores_Sucursales_Config` | BAJO |
| 4.2 | Migrar `db.server_sucursales_config` | MEDIO |
| 4.3 | Crear tabla `Consultas_Templates` | BAJO |
| 4.4 | Migrar `db.queries` | BAJO |
| 4.5 | Crear tabla `Alertas` (opcional) | BAJO |
| 4.6 | Migrar `db.alerts` | BAJO |

**Duración estimada:** 2-3 fases con autorización

---

### FASE 5: Eliminación controlada de fallback MongoDB

| Paso | Acción | Riesgo |
|------|--------|--------|
| 5.1 | Auditar que todas las lecturas usen SQL | BAJO |
| 5.2 | Agregar logging de cualquier acceso MongoDB | BAJO |
| 5.3 | Período de observación (1-2 semanas) | BAJO |
| 5.4 | Desactivar fallback en auth | ALTO |
| 5.5 | Desactivar fallback en empresas/sucursales | ALTO |
| 5.6 | Desactivar fallback en servers (completar) | MEDIO |
| 5.7 | Mantener MongoDB solo para cache P2-P3 | BAJO |

---

### FASE 6: Pruebas de no regresión

| Prueba | Componente |
|--------|------------|
| 6.1 | Login y autenticación |
| 6.2 | Permisos RBAC por sucursal |
| 6.3 | Multi-empresa |
| 6.4 | Tablero Ejecutivo Comercial |
| 6.5 | Finanzas: Tesorería, Propinas |
| 6.6 | Inventarios: Auditoría, Comparativo |
| 6.7 | Compras: Automatización |
| 6.8 | Configuración: Servidores, Sucursales |
| 6.9 | Universal Query |
| 6.10 | Catálogos |

---

## 7. CONCLUSIONES

### 7.1 Estado Actual

- **MongoDB sigue siendo crítico** para auth, RBAC, empresas y sucursales
- **EDARSAHUB SQL ya es fuente primaria** para servidores y conexiones (parcial)
- **La migración de `db.servers`** está en 70% completada

### 7.2 Recomendaciones

1. **Completar P1.4** (Fase 1) antes de iniciar Fase 2
2. **No ejecutar DDL** sin autorización explícita
3. **Implementar dual-read** antes de eliminar MongoDB
4. **Mantener cache en MongoDB** para KPIs y diferencias
5. **Período de observación** obligatorio antes de desactivar fallback

### 7.3 Orden Exacto para Eliminar MongoDB Sin Romper el Sistema

```
1. ✅ Completar migración db.servers (Fase 1)
2. ⏸️ Crear tablas SQL faltantes (DDL autorizado)
3. ⏸️ Migrar datos de MongoDB a SQL
4. ⏸️ Implementar repositorios SQL centrales
5. ⏸️ Implementar dual-read en todos los módulos
6. ⏸️ Validar funcionamiento con SQL primario
7. ⏸️ Período de observación (logs de MongoDB access)
8. ⏸️ Desactivar fallback MongoDB por módulo
9. ⏸️ Mantener MongoDB solo para cache
10. ⏸️ Deprecar cache MongoDB (opcional, futuro)
```

---

## 8. PRÓXIMOS PASOS INMEDIATOS

| # | Acción | Requiere Autorización |
|---|--------|----------------------|
| 1 | Completar P1.4-E4 (Explorador/Catálogo) | ✅ SÍ |
| 2 | Completar P1.4-F (Módulo Configuración) | ✅ SÍ |
| 3 | Presentar propuesta DDL Fase 2 | ✅ SÍ |
| 4 | Iniciar migración de `db.users` | ✅ SÍ |

---

**ESTADO:** DIAGNÓSTICO COMPLETO — PENDIENTE AUTORIZACIÓN PARA FASES POSTERIORES

*Documento generado bajo régimen de Autorización Controlada. No se realizaron cambios de código.*
