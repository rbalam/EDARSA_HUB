# P1.4-A: DIAGNÓSTICO PASIVO — CONFIGURACIÓN/SERVIDORES

**Fecha:** 14-Dic-2025  
**Estado:** DIAGNÓSTICO COMPLETADO  
**Objetivo:** Mapear todas las dependencias de `db.servers` (MongoDB) y la sincronización SQL↔MongoDB antes de la migración EDARSAHUB-FIRST.

---

## 1. RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| Archivos con `db.servers` activo (producción) | **9** |
| Archivos con `db.servers` en scripts/tests | 14 |
| Archivos ya migrados a `server_registry` | 5 |
| Endpoints CRUD afectados | 4 (`/api/servers`) |
| Componentes frontend afectados | 3 |

### Dictamen Global

```
ESTADO: HÍBRIDO_CON_DEUDA_TÉCNICA

El CRUD de servidores en server.py ya usa server_registry para
CREATE/READ/UPDATE/DELETE principales, pero existen ENDPOINTS LEGACY
que aún consultan MongoDB directamente.

Módulo Configuración (config_asignaciones) y almacenes_sync_service
todavía dependen de MongoDB para resolver contexto de servidores.
```

---

## 2. MATRIZ DE ENDPOINTS (`/api/servers/*`)

| Endpoint | Archivo | Líneas | Usa `db.servers`? | Usa `server_registry`? | Dictamen |
|----------|---------|--------|-------------------|------------------------|----------|
| `POST /api/servers` (crear) | `server.py` | 1148-1203 | ❌ | ✅ `registry_create_server` | MIGRADO |
| `GET /api/servers` (listar) | `server.py` | 1205-1229 | ❌ | ✅ `registry_list_servers` | MIGRADO |
| `GET /api/servers/{id}` (detalle) | `server.py` | 1231-1256 | ❌ | ✅ `registry_get_server` | MIGRADO |
| `PUT /api/servers/{id}` (actualizar) | `server.py` | 1258-1314 | ❌ | ✅ `registry_update_server` | MIGRADO |
| `DELETE /api/servers/{id}` (eliminar) | `server.py` | 1316-1368 | ❌ | ✅ `registry_delete_server` | MIGRADO |
| `GET /api/servers/{id}/ping` | `server.py` | 1370-1459 | ❌ | ✅ `get_server_connection_info` | MIGRADO |
| `POST /api/servers/{id}/queries/validate` | `server.py` | 1587-1661 | ✅ L:1607 | ❌ | **DEUDA** |
| `POST /api/servers/{id}/queries/save` | `server.py` | 1693-1730 | ✅ L:1698,1712,1718,1725 | ❌ | **DEUDA** |
| `POST /api/servers/{id}/run-query` | `server.py` | 1740-1796 | ✅ L:1743 | ❌ | **DEUDA** |
| `POST /api/servers/{id}/analyze-inventory` | `server.py` | 3095-3138 | ✅ L:3101 | ❌ | **DEUDA** |
| `GET /api/servers/{id}/sucursales-config` | `server.py` | 3310-3400 | ✅ L:3318 | ❌ | **DEUDA** |
| `GET /api/servers/{id}/inventory-summary` | `server.py` | 4605-4662 | ✅ L:4613 | ❌ | **DEUDA** |
| `POST /api/servers/{id}/generate-report` | `server.py` | 4845-4933 | ✅ L:4853 | ❌ | **DEUDA** |
| `POST /api/auditorias` (crear informe) | `server.py` | 5405-5480 | ✅ L:5411 | ❌ | **DEUDA** |

### Resumen de Endpoints

| Categoría | Cantidad |
|-----------|----------|
| CRUD Principal (MIGRADO) | 6 |
| Endpoints Legacy (DEUDA) | 8 |

---

## 3. MATRIZ DE CAMPOS SENSIBLES

| Campo | Fuente SQL (`Servidores_Conexiones`) | Fuente MongoDB (`servers`) | Tratamiento |
|-------|--------------------------------------|---------------------------|-------------|
| `id` | ✅ `id` (INT autonumérico) | ✅ `id` (UUID string) | SQL normaliza a string |
| `name` | ✅ `nombre` | ✅ `name` | SQL→`nombre`, Mongo→`name` |
| `host` | ✅ `host` | ✅ `host` | Idéntico |
| `port` | ✅ `port` | ✅ `port` | Idéntico |
| `database` | ✅ `database_name` | ✅ `database` | SQL→`database_name` |
| `username` | ✅ `username` | ✅ `username` | Idéntico |
| `password` | ✅ `password_encrypted` (CIFRADO) | ⚠️ `password` (algunos plaintext) | **CRÍTICO** |
| `api_key` | ✅ `api_key_encrypted` (CIFRADO) | ⚠️ `api_key` (algunos plaintext) | **CRÍTICO** |
| `system_type` | ✅ `system_type` | ✅ `system_type` | Idéntico |
| `tipos_movimiento` | ✅ `tipos_movimiento` (JSON) | ✅ `tipos_movimiento` (array) | Parseado en registry |
| `categorias` | ✅ `categorias` (JSON) | ✅ `categorias` (array) | Parseado en registry |
| `departamentos` | ✅ `departamentos` (JSON) | ✅ `departamentos` (array) | Parseado en registry |
| `visible_en_operaciones` | ✅ `visible_en_operaciones` | ✅ `visible_en_operaciones` | Idéntico |
| `active` | ✅ `activo` (BIT) | ✅ `active` (bool) | SQL→`activo` |
| `tipo_conexion` | ✅ `tipo_conexion` | ✅ `tipo_conexion` | Idéntico |
| `query_inventario` | ✅ `query_inventario` (JSON) | ✅ `query_inventario` (object) | Parseado |
| `query_ventas` | ✅ `query_ventas` (JSON) | ✅ `query_ventas` (object) | Parseado |
| `query_movimientos` | ✅ `query_movimientos` (JSON) | ✅ `query_movimientos` (object) | Parseado |

### Campos Exclusivos MongoDB (no migrados a SQL)

| Campo | Descripción | Acción Recomendada |
|-------|-------------|---------------------|
| `sucursales` | Array de IDs de sucursales | Migrar a `sucursales` (JSON) en SQL |
| `queries_configured` | Bool flag | Migrar a `queries_configured` (BIT) en SQL |
| `date_calculation_method` | String ("inventory_dates") | Migrar a SQL |

---

## 4. MATRIZ DE COMPONENTES FRONTEND

| Componente | Archivo | Consume `/api/servers`? | Usa `server_id`? | Dictamen |
|------------|---------|-------------------------|------------------|----------|
| Servidores (Admin) | `pages/Servidores.js` | ✅ CRUD completo | ✅ | UI Principal |
| Propinas TPV | `components/PropinasTPV.jsx` | ✅ L:107, 138 | ✅ | Filtro servidores |
| Tesorería Corte Z | `useTesoreriaCorteZData.js` | ✅ L:38 | ✅ | Listado servidores |
| Comercial | `pages/Comercial.js` | ⚠️ Comentado L:2807 | ❌ | No usa servers |
| serversService | `services/serversService.js` | ✅ Centralizado | ✅ | Wrapper `/api/servers` |

### Flujo Frontend Actual

```
Servidores.js  →  fetch('/api/servers')  →  server.py (CRUD migrado a server_registry)
                                                    ↓
                                        ┌──────────────────────────────────────┐
                                        │  server_registry.list_servers()     │
                                        │  - Consulta EDARSAHUB SQL primero   │
                                        │  - Fallback MongoDB si SQL vacío    │
                                        │  - Enmascara secretos               │
                                        └──────────────────────────────────────┘
```

---

## 5. MATRIZ DE SINCRONIZACIÓN SQL↔MONGODB

### Flujo Actual (CRUD MIGRADO)

| Operación | SQL First | Sync a MongoDB | Comportamiento |
|-----------|-----------|----------------|----------------|
| CREATE | ✅ INSERT en `Servidores_Conexiones` | ✅ `insert_one` en `servers` | SQL es fuente, Mongo espejo |
| READ | ✅ SELECT de SQL | ⚠️ Fallback Mongo si SQL vacío | Híbrido |
| UPDATE | ✅ UPDATE en SQL | ✅ `update_one` en `servers` | SQL es fuente, Mongo espejo |
| DELETE | ✅ UPDATE `activo=0` (soft) | ✅ `update_one` `active=false` | Soft delete en ambos |

### Funciones de Sincronización en `server_registry.py`

| Función | Propósito | Líneas |
|---------|-----------|--------|
| `create_server()` | SQL-first, sync a Mongo | 1016-1161 |
| `update_server()` | SQL-first, sync a Mongo | 1164-1344 |
| `delete_server()` | SQL-first (soft delete), sync a Mongo | 1347-1445 |
| `sync_server_to_mongo()` | Reconciliación manual SQL→Mongo | 1448-1522 |
| `reconcile_sql_mongo_servers()` | Auditoría de diferencias | 1649+ |

### Problema de Doble Fuente

```
ESCENARIO ACTUAL:
┌─────────────────────────────────────────────────────────────────────┐
│  Endpoints MIGRADOS (CRUD)                                          │
│  → Usan server_registry → SQL primario, Mongo espejo                │
└─────────────────────────────────────────────────────────────────────┘
                                ↕ INCONSISTENCIA
┌─────────────────────────────────────────────────────────────────────┐
│  Endpoints LEGACY (queries, inventario, auditoría)                  │
│  → Usan db.servers.find_one() directo → MongoDB es fuente           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. MATRIZ DE DEUDA TÉCNICA

### Por Archivo (Solo Código Productivo)

| Archivo | Líneas con `db.servers` | Impacto | Prioridad |
|---------|-------------------------|---------|-----------|
| `server.py` | 1607, 1698, 1712, 1718, 1725, 1743, 1797, 1802, 3101, 3318, 4613, 4853, 5411 | **ALTO** - Múltiples endpoints | P0 |
| `config_asignaciones_repository.py` | 249 | MEDIO - Solo en actualizar() | P1 |
| `almacenes_sync_service.py` | 138 | MEDIO - Solo en sincronizar | P1 |
| `historical_kpis_repository.py` (comercial) | 62 | BAJO - Constante EDARSAHUB | P2 |

### Por Funcionalidad

| Funcionalidad | Archivos | ¿Bloquea deprecación MongoDB? |
|---------------|----------|-------------------------------|
| Validación de queries SQL | `server.py` | ✅ SÍ |
| Guardar queries configuradas | `server.py` | ✅ SÍ |
| Run query manual | `server.py` | ✅ SÍ |
| Análisis de inventario | `server.py` | ✅ SÍ |
| Configuración de sucursales | `server.py` | ✅ SÍ |
| Resumen de inventario | `server.py` | ✅ SÍ |
| Generación de reportes | `server.py` | ✅ SÍ |
| Creación de auditorías | `server.py` | ✅ SÍ |
| Asignación de responsables | `config_asignaciones_repository.py` | ✅ SÍ |
| Sincronización almacenes | `almacenes_sync_service.py` | ✅ SÍ |

---

## 7. PROPUESTA DE SUBFASES (P1.4-B a P1.4-F)

### Fase P1.4-B: Migrar Endpoints de Queries

**Objetivo:** Eliminar `db.servers.find_one()` en validación/guardado de queries.

| Endpoint | Acción |
|----------|--------|
| `POST /api/servers/{id}/queries/validate` | Usar `server_registry.get_server_connection_info()` |
| `POST /api/servers/{id}/queries/save` | Usar `server_registry.update_server()` |
| `POST /api/servers/{id}/run-query` | Usar `server_registry.get_server_connection_info()` |

**Archivos a modificar:** `server.py`  
**Líneas afectadas:** ~1607, 1698, 1712, 1718, 1725, 1743, 1797, 1802  
**Riesgo:** BAJO (funcionalidad similar ya existe en CRUD)

---

### Fase P1.4-C: Migrar Endpoints de Inventario

**Objetivo:** Eliminar `db.servers.find_one()` en análisis y reportes de inventario.

| Endpoint | Acción |
|----------|--------|
| `POST /api/servers/{id}/analyze-inventory` | Usar `server_registry.get_server_connection_info()` |
| `GET /api/servers/{id}/inventory-summary` | Usar `server_registry.get_server_connection_info()` |
| `POST /api/servers/{id}/generate-report` | Usar `server_registry.get_server_connection_info()` |

**Archivos a modificar:** `server.py`  
**Líneas afectadas:** ~3101, 4613, 4853  
**Riesgo:** MEDIO (flujos más complejos)

---

### Fase P1.4-D: Migrar Configuración de Sucursales

**Objetivo:** Eliminar `db.servers.find_one()` en configuración de sucursales.

| Endpoint | Acción |
|----------|--------|
| `GET /api/servers/{id}/sucursales-config` | Usar `server_registry.get_server_sucursales()` |
| Relacionados (PUT bulk update) | Evaluar si migrar o deprecar |

**Archivos a modificar:** `server.py`  
**Líneas afectadas:** ~3318  
**Riesgo:** MEDIO (verificar impacto en frontend Servidores.js)

---

### Fase P1.4-E: Migrar Auditorías

**Objetivo:** Eliminar `db.servers.find_one()` en creación de informes de auditoría.

| Endpoint | Acción |
|----------|--------|
| `POST /api/auditorias` | Usar `server_registry.get_server_connection_info()` |

**Archivos a modificar:** `server.py`  
**Líneas afectadas:** ~5411  
**Riesgo:** BAJO (uso puntual)

---

### Fase P1.4-F: Migrar Módulo Configuración

**Objetivo:** Eliminar dependencia de `db.servers` en módulo de asignaciones y sincronización.

| Componente | Archivo | Acción |
|------------|---------|--------|
| `actualizar()` | `config_asignaciones_repository.py` | Usar `server_registry` en vez de `db.servers.find_one()` L:249 |
| `sincronizar_almacenes_desde_origen()` | `almacenes_sync_service.py` | Usar `server_registry.get_server_connection_info()` L:138 |

**Archivos a modificar:** 2  
**Riesgo:** MEDIO (verificar que catálogos locales funcionen)

---

## 8. CHECKLIST DE VALIDACIÓN PRE-IMPLEMENTACIÓN

Antes de autorizar cada subfase, verificar:

- [ ] ¿El endpoint tiene tests existentes?
- [ ] ¿El frontend depende del formato de respuesta actual?
- [ ] ¿Hay campos que solo existen en MongoDB y no en SQL?
- [ ] ¿La función `server_registry` equivalente ya existe?
- [ ] ¿Qué pasa si SQL está vacío? (fallback a Mongo)
- [ ] ¿Se deben preservar passwords/api_keys sin enmascarar internamente?

---

## 9. RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Queries configuradas no guardadas en SQL | ALTA | ALTO | Verificar columnas `query_*` en `Servidores_Conexiones` |
| Frontend espera campos MongoDB-only | MEDIA | MEDIO | Mapeo en `server_registry._sql_row_to_server_dict()` |
| Scripts de carga histórica fallan | BAJA | BAJO | Son operaciones batch, no afectan producción |
| Sincronización SQL↔Mongo desincronizada | MEDIA | ALTO | Ejecutar `reconcile_sql_mongo_servers()` después de cada fase |

---

## 10. PRÓXIMOS PASOS

| # | Acción | Requiere Autorización |
|---|--------|----------------------|
| 1 | Usuario revisa este documento | — |
| 2 | Usuario autoriza Fase P1.4-B (Queries) | ✅ SÍ |
| 3 | Implementar P1.4-B | Post-autorización |
| 4 | Validar con testing subagent | Post-implementación |
| 5 | Usuario autoriza siguiente fase | ✅ SÍ |

---

**ESTADO:** DIAGNÓSTICO P1.4-A COMPLETADO — PENDIENTE AUTORIZACIÓN USUARIO PARA FASES B-F

---

*Documento generado bajo régimen de Autorización Controlada. No se realizaron cambios de código.*
