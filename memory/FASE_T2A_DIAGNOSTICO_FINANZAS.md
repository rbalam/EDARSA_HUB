# FASE T2-A: DIAGNÓSTICO PASIVO DE FINANZAS
**Fecha:** 2026-05-13
**Estado:** DIAGNÓSTICO COMPLETADO — Pendiente Autorización para Implementación

---

## 1. RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| **Archivos revisados** | 42 |
| **Referencias a db.servers** | 12 |
| **Endpoints afectados** | 8 |
| **Funciones afectadas** | 15+ |
| **Riesgo general** | MEDIO |

---

## 2. ARCHIVOS FINANZAS CON REFERENCIAS A MONGODB

### 2.1 Referencias Directas a `db.servers`

| # | Archivo | Línea | Tipo de Consulta |
|---|---------|-------|------------------|
| 1 | `tesoreria.py` | 636 | `db.servers.find()` |
| 2 | `repository_real.py` | 47 | `db.servers.find_one()` |
| 3 | `historical_kpis_repository.py` | 31 | `db.servers.find_one()` |
| 4 | `propinas_tpv/service.py` | 79 | `db['servers'].find()` |
| 5 | `propinas_tpv/routes_sql.py` | 408 | `db.servers.find_one()` |
| 6 | `propinas_tpv/routes_sql.py` | 440 | `db.servers.find()` |
| 7 | `propinas_tpv/routes_sql.py` | 516 | `db.servers.find()` |
| 8 | `propinas_tpv/sql_repository.py` | 70 | `mongo_db.servers.find_one()` |
| 9 | `propinas_tpv/service_sql.py` | 160 | `db['servers'].find()` |
| 10 | `propinas_tpv/routes.py` | 222 | `db.servers.find_one()` |
| 11 | `propinas_tpv/routes.py` | 262 | `db.servers.find()` |
| 12 | `propinas_tpv/routes.py` | 358 | `db.servers.find()` |

---

## 3. ANÁLISIS DETALLADO POR MÓDULO

### 3.1 TESORERÍA (`tesoreria.py`)

| Campo | Valor |
|-------|-------|
| **Línea** | 636 |
| **Función** | `_get_servidores_operativos_mongo_fallback()` |
| **Query MongoDB** | `db.servers.find({active: True, system_type: {$in: [...]}, ...})` |
| **Datos obtenidos** | id, name, system_type, visible_en_operaciones, active |
| **Endpoint** | `GET /api/finanzas/tesoreria/sucursales` |
| **Propósito** | Listar servidores visibles para operaciones de tesorería |
| **Riesgo** | **BAJO** — Es fallback, ya hay lógica EDARSAHUB primero |

**Función de reemplazo:** `get_visible_servers_for_operaciones()`

---

### 3.2 REPOSITORY REAL (`repository_real.py`)

| Campo | Valor |
|-------|-------|
| **Línea** | 47 |
| **Función** | `_get_server()` |
| **Query MongoDB** | `db.servers.find_one({id: EDARSA_HUB_SERVER_ID})` |
| **Datos obtenidos** | host, port, database, username, password |
| **Propósito** | Obtener conexión a EDARSAHUB para CxP |
| **Riesgo** | **ALTO** — Único punto de entrada para conexión EDARSAHUB |

**Función de reemplazo:** `get_connection_config(EDARSA_HUB_SERVER_ID)` o usar `EDARSAHUB_CONFIG` directamente

---

### 3.3 HISTORICAL KPIS (`historical_kpis_repository.py`)

| Campo | Valor |
|-------|-------|
| **Línea** | 31 |
| **Función** | `get_edarsahub_server()` |
| **Query MongoDB** | `db.servers.find_one({name: 'EDARSA HUB'})` |
| **Datos obtenidos** | host, port, database, username, password |
| **Propósito** | Conexión para carga histórica de KPIs |
| **Riesgo** | **MEDIO** — Función standalone, usada en scripts de carga |

**Función de reemplazo:** Usar `EDARSAHUB_CONFIG` desde `server_registry.py`

---

### 3.4 PROPINAS TPV — SERVICE (`propinas_tpv/service.py`)

| Campo | Valor |
|-------|-------|
| **Línea** | 79 |
| **Función** | `sincronizar()` |
| **Query MongoDB** | `db['servers'].find({system_type: 'SoftRestaurant'})` |
| **Datos obtenidos** | id, name, host, port, database, username, password |
| **Propósito** | Listar servidores SR para sincronizar propinas |
| **Riesgo** | **CRÍTICO** — Punto central de sincronización |

**Función de reemplazo:** `list_operational_servers()` filtrado por system_type

---

### 3.5 PROPINAS TPV — ROUTES SQL (`propinas_tpv/routes_sql.py`)

| Línea | Endpoint | Query | Riesgo |
|-------|----------|-------|--------|
| 408 | `GET /detectar-esquema/{server_id}` | `find_one({id: server_id})` | MEDIO |
| 440 | `GET /detectar-esquema-todos` | `find({system_type: 'SoftRestaurant'})` | MEDIO |
| 516 | `GET /propinas/validar-periodo` | `find({system_type: 'SoftRestaurant'})` | MEDIO |

**Función de reemplazo:** `get_server_by_id()` para find_one, `list_operational_servers()` para find

---

### 3.6 PROPINAS TPV — SQL REPOSITORY (`propinas_tpv/sql_repository.py`)

| Campo | Valor |
|-------|-------|
| **Línea** | 70 |
| **Función** | `get_edarsa_hub_server()` |
| **Query MongoDB** | `mongo_db.servers.find_one({id: EDARSA_HUB_SERVER_ID})` |
| **Datos obtenidos** | host, port, database, username, password |
| **Propósito** | Conexión a EDARSAHUB para guardar propinas |
| **Riesgo** | **ALTO** — Punto de escritura a EDARSAHUB |

**Función de reemplazo:** `get_connection_config(EDARSA_HUB_SERVER_ID)` o `EDARSAHUB_CONFIG`

---

### 3.7 PROPINAS TPV — ROUTES (`propinas_tpv/routes.py`)

| Línea | Endpoint | Query | Riesgo |
|-------|----------|-------|--------|
| 222 | `GET /detectar-esquema/{server_id}` | `find_one({id: server_id})` | MEDIO |
| 262 | `GET /detectar-esquema-todos` | `find({system_type: 'SoftRestaurant'})` | MEDIO |
| 358 | `GET /propinas/validar-periodo` | `find({system_type: 'SoftRestaurant'})` | MEDIO |

**Función de reemplazo:** Igual que routes_sql.py

---

## 4. MAPEO: MONGODB → SERVER_REGISTRY

| Dato Actual (MongoDB) | Función Server Registry |
|-----------------------|------------------------|
| `db.servers.find_one({id: server_id})` | `get_server_by_id(server_id)` |
| `db.servers.find({system_type: 'SoftRestaurant'})` | `list_operational_servers()` filtrado |
| `db.servers.find({active: True, visible_en_operaciones: True})` | `get_visible_servers_for_operaciones()` |
| `server['host'], server['port'], ...` | `get_connection_config(server_id)` |
| EDARSA_HUB_SERVER_ID lookup | Usar `EDARSAHUB_CONFIG` directamente |

---

## 5. CLASIFICACIÓN DE RIESGO POR ENDPOINT

| Prioridad | Endpoint | Módulo | Riesgo | Razón |
|-----------|----------|--------|--------|-------|
| 1 | Conexión EDARSAHUB | repository_real.py, sql_repository.py | **CRÍTICO** | Punto único de escritura/lectura |
| 2 | Sincronizar propinas | propinas_tpv/service.py | **ALTO** | Afecta jobs de sincronización |
| 3 | Listar sucursales tesorería | tesoreria.py | **BAJO** | Ya tiene fallback, lógica SQL primero |
| 4 | Detectar esquema (todos) | routes.py, routes_sql.py | **MEDIO** | Solo lectura, no afecta datos |
| 5 | Validar periodo propinas | routes.py, routes_sql.py | **MEDIO** | Solo lectura |
| 6 | Historical KPIs | historical_kpis_repository.py | **MEDIO** | Scripts de carga, no runtime |

---

## 6. PROPUESTA DE MIGRACIÓN POR SUBFASES

### FASE T2.1 — Conexión EDARSAHUB Centralizada (RECOMENDADA PRIMERO)
**Archivos:** `repository_real.py`, `sql_repository.py`, `historical_kpis_repository.py`
**Cambio:** Reemplazar lookup de EDARSA_HUB_SERVER_ID por `EDARSAHUB_CONFIG`
**Riesgo:** ALTO pero controlado — Único punto de cambio
**Beneficio:** Elimina 3 referencias de golpe

### FASE T2.2 — Tesorería Sucursales
**Archivo:** `tesoreria.py`
**Cambio:** Reemplazar `_get_servidores_operativos_mongo_fallback()` por `get_visible_servers_for_operaciones()`
**Riesgo:** BAJO — Ya es fallback

### FASE T2.3 — Propinas TPV Routes
**Archivos:** `routes.py`, `routes_sql.py`
**Cambio:** Reemplazar `db.servers.find_one()` y `find()` por funciones de server_registry
**Riesgo:** MEDIO — Múltiples endpoints

### FASE T2.4 — Propinas TPV Service
**Archivo:** `propinas_tpv/service.py`
**Cambio:** Reemplazar listado de servidores por `list_operational_servers()`
**Riesgo:** ALTO — Afecta sincronización

### FASE T2.5 — Limpieza Final
**Acción:** Eliminar imports de pymongo donde ya no se usen
**Riesgo:** BAJO

---

## 7. PRIMER ENDPOINT RECOMENDADO PARA MIGRAR

### Recomendación: FASE T2.1 — Conexión EDARSAHUB

**Archivos a modificar:**
1. `/app/backend/modules/finanzas/repository_real.py` (línea 47)
2. `/app/backend/modules/finanzas/propinas_tpv/sql_repository.py` (línea 70)
3. `/app/backend/modules/finanzas/historical_kpis_repository.py` (línea 31)

**Razón:**
- Es el cambio más **aislado** — Solo afecta cómo se obtiene la configuración de EDARSAHUB
- `EDARSAHUB_CONFIG` ya existe en `server_registry.py`
- No cambia lógica de negocio
- No afecta endpoints de usuario
- Elimina 3 referencias a MongoDB de una vez
- Prueba simple: Si las queries a EDARSAHUB funcionan, el cambio es exitoso

**Patrón de cambio:**
```python
# ANTES (MongoDB)
server = await self.db.servers.find_one({"id": EDARSA_HUB_SERVER_ID})
host = server['host']
...

# DESPUÉS (server_registry)
from core.server_registry import EDARSAHUB_CONFIG
host = EDARSAHUB_CONFIG['host']
port = EDARSAHUB_CONFIG['port']
database = EDARSAHUB_CONFIG['database']
username = EDARSAHUB_CONFIG['username']
password = EDARSAHUB_CONFIG['password']  # Ya descifrado si aplica
```

---

## 8. PRUEBAS DE NO REGRESIÓN REQUERIDAS

### Después de FASE T2.1:
1. ✅ `GET /api/finanzas/cuentas-por-pagar` responde correctamente
2. ✅ `POST /api/finanzas/propinas-tpv/sincronizar` ejecuta sin errores
3. ✅ Scripts de carga histórica funcionan
4. ✅ Tablero Ejecutivo Comercial sin regresión

### Después de FASE T2.2:
1. ✅ `GET /api/finanzas/tesoreria/sucursales` devuelve servidores correctos

### Después de FASE T2.3-T2.4:
1. ✅ `GET /api/finanzas/propinas-tpv/detectar-esquema/{server_id}` funciona
2. ✅ `GET /api/finanzas/propinas-tpv/detectar-esquema-todos` funciona
3. ✅ Sincronización de propinas manual funciona

---

## 9. ROLLBACK PROPUESTO

Para cada subfase, si hay error:

1. **Revertir el archivo modificado** usando git checkout o backup
2. **Reiniciar backend** con `sudo supervisorctl restart backend`
3. **Verificar endpoints** con curl
4. **Reportar** el error específico

No se eliminarán imports de MongoDB hasta que todas las subfases estén validadas.

---

## 10. CONFIRMACIONES

| Confirmación | Estado |
|--------------|--------|
| No se modificó ningún archivo | ✅ CONFIRMADO |
| No se ejecutó ningún script SQL | ✅ CONFIRMADO |
| No se tocó MongoDB | ✅ CONFIRMADO |
| No se tocó Comercial | ✅ CONFIRMADO |
| No se tocó Tablero Ejecutivo | ✅ CONFIRMADO |
| Solo se realizó lectura de código | ✅ CONFIRMADO |

---

## 11. SIGUIENTE PASO

**AUTORIZACIÓN REQUERIDA PARA:**

> **FASE T2.1** — Migrar conexión EDARSAHUB en:
> - `repository_real.py`
> - `propinas_tpv/sql_repository.py`
> - `historical_kpis_repository.py`

Este cambio eliminará 3 referencias a `db.servers.find_one()` reemplazándolas por `EDARSAHUB_CONFIG`.

---

**Generado:** 2026-05-13
**Tipo:** Diagnóstico Pasivo (Solo Lectura)
