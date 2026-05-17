# FASE 1: Circuit Breaker HUB - EDARSAHUB SQL (No MongoDB)

**Fecha:** 2026-05-17  
**Módulo:** Comercial - Tablero Ejecutivo V1  
**Estado:** ✅ COMPLETADO  
**Archivo modificado:** `/app/backend/modules/comercial/routes.py`  

---

## 1. CAUSA RAÍZ

El endpoint `/api/comercial/tablero-ejecutivo` consultaba MongoDB (`server_status`) para determinar si un servidor estaba "offline" mediante `should_attempt_live_query()`. Si el servidor estaba marcado como offline, el sistema usaba `kpis_cache` de MongoDB como fallback.

**PROBLEMA:** La función `get_kpis_softrestaurant()` ya lee de **EDARSAHUB SQL** (no del servidor SoftRestaurant local), por lo que:
1. El circuit breaker de servidor local era **irrelevante**
2. Se bloqueaban consultas SQL que siempre funcionan
3. Se servían datos de MongoDB en lugar de EDARSAHUB SQL

---

## 2. FUNCIONES MODIFICADAS

### Archivo: `/app/backend/modules/comercial/routes.py`

| Línea | Función | Cambio |
|-------|---------|--------|
| 776-782 | `tablero_ejecutivo()` | Si `data_type == "HUB"`: `should_try = True` siempre |
| 798-811 | `tablero_ejecutivo()` | Si `data_type != "HUB"`: guardar estado MongoDB (solo LIVE-C) |
| 820-833 | `tablero_ejecutivo()` | `source_period = "EDARSAHUB_SQL"` para modo HUB |
| 967-1032 | `tablero_ejecutivo()` | Si error y HUB: reportar `EDARSAHUB_SQL_ERROR`, NO caché MongoDB |

---

## 3. FLUJO ANTERIOR (INCORRECTO)

```
Request GET /api/comercial/tablero-ejecutivo (modo HUB)
    │
    ▼
should_attempt_live_query(server_id, "HUB")
    │
    ▼
is_server_recently_offline() ──► MongoDB: server_status
    │                                 │
    │ (servidor marcado offline)      │
    ▼                                 │
should_try = False ◄─────────────────┘
    │
    ▼
get_cached_kpis() ──► MongoDB: kpis_cache (datos viejos)
    │
    ▼
Retorna DATA_FROM_CACHE ❌
```

---

## 4. FLUJO NUEVO (CORRECTO)

```
Request GET /api/comercial/tablero-ejecutivo (modo HUB)
    │
    ▼
data_type = "HUB"
    │
    ▼
should_try = True (FORZADO - circuit breaker ignorado)
    │
    ▼
get_kpis_softrestaurant() ──► EDARSAHUB SQL
    │
    ├── SUCCESS ──► DATA_OK, source=EDARSAHUB_SQL ✅
    │
    └── ERROR ──► EDARSAHUB_SQL_ERROR (NO MongoDB fallback) ✅
```

---

## 5. CONFIRMACIÓN: MODO HUB NO USA MONGODB

### Para Circuit Breaker:
- ✅ `should_try = True` forzado para `data_type == "HUB"`
- ✅ NO se consulta `is_server_recently_offline()`
- ✅ NO se consulta MongoDB `server_status`

### Para Fallback de Datos:
- ✅ Si EDARSAHUB SQL tiene éxito → `DATA_OK`
- ✅ Si EDARSAHUB SQL falla → `EDARSAHUB_SQL_ERROR` (NO `kpis_cache` MongoDB)
- ✅ NO se usa `get_cached_kpis()` para modo HUB
- ✅ NO se usa `dashboard_cache` para modo HUB

### Para Guardar Estado:
- ✅ NO se ejecuta `save_server_connection_status()` para modo HUB

---

## 6. VALIDACIÓN DE LAS 5 UNIDADES

| Unidad | data_status | source_period | live_status | ventas |
|--------|-------------|---------------|-------------|--------|
| CIENFUEGOS | `DATA_OK` ✅ | `EDARSAHUB_SQL` 🟢 | `LIVE_NOT_APPLICABLE` | $2,543,511.00 |
| 130° MÉRIDA | `DATA_OK` ✅ | `EDARSAHUB_SQL` 🟢 | `LIVE_NOT_APPLICABLE` | $2,094,097.00 |
| 130° QUERÉTARO | `DATA_OK` ✅ | `SQL` 🟢 | `LIVE_CONNECTED` | $2,037,841.00 |
| LA ESTELAR | `DATA_OK` ✅ | `EDARSAHUB_SQL` 🟢 | `LIVE_NOT_APPLICABLE` | $1,744,171.00 |
| ORIGEN | `DATA_OK` ✅ | `SQL` 🟢 | `LIVE_CONNECTED` | $1,322,475.18 |

**Status Summary:**
- Total unidades: 5
- DATA_OK: **5** ✅
- DATA_FROM_CACHE: **0** ✅
- DATA_ERROR: 0

---

## 7. EVIDENCIA cURL

### Comando Ejecutado:
```bash
curl -s "$API_URL/api/comercial/tablero-ejecutivo" -H "Authorization: Bearer $TOKEN"
```

### Respuesta (extracto):
```json
{
  "periodo": {"mes": 5, "anio": 2026, "dias_transcurridos": 17, "dias_mes": 31},
  "status_summary": {
    "total_unidades": 5,
    "unidades_data_ok": 5,
    "unidades_data_cache": 0,
    "unidades_data_error": 0
  },
  "unidades": [
    {"nombre": "CIENFUEGOS", "data_status": "DATA_OK", "source_period": "EDARSAHUB_SQL"},
    {"nombre": "130° MERIDA", "data_status": "DATA_OK", "source_period": "EDARSAHUB_SQL"},
    {"nombre": "130° QUERETARO", "data_status": "DATA_OK", "source_period": "SQL"},
    {"nombre": "LA ESTELAR", "data_status": "DATA_OK", "source_period": "EDARSAHUB_SQL"},
    {"nombre": "ORIGEN", "data_status": "DATA_OK", "source_period": "SQL"}
  ]
}
```

---

## 8. EVIDENCIA GREP

### 8.1 `server_status` (MongoDB circuit breaker)
```
/app/backend/modules/comercial/repository.py:573: await get_db().server_status.update_one(
/app/backend/modules/comercial/repository.py:589: return await get_db().server_status.find_one(...)
/app/backend/modules/comercial/routes.py:4282: server_status_doc = await get_server_connection_status(...)  # ← NO afecta HUB
/app/backend/modules/comercial/routes.py:4541: server_status_doc_mpro = await get_server_connection_status(...)  # ← NO afecta HUB
```
**Estado:** Referencias en líneas 4282 y 4541 son para flujos LIVE (dashboard individual), NO para Tablero Ejecutivo HUB.

### 8.2 `kpis_cache` (MongoDB fallback)
```
/app/backend/modules/comercial/repository.py:538: cache = await get_db().kpis_cache.find_one(...)
/app/backend/modules/comercial/routes.py:842: await save_kpis_cache(...)  # ← Solo se ejecuta si consulta exitosa (no fallback)
/app/backend/modules/comercial/routes.py:968-1008: cached = await get_cached_kpis(...)  # ← BLOQUEADO para HUB (nuevo if)
```
**Estado:** El bloque de fallback a `kpis_cache` (líneas 968-1008) ahora está condicionado: Solo se ejecuta para `LIVE-C`, NO para `HUB`.

### 8.3 `should_attempt_live_query` (decisión de consulta)
```
/app/backend/modules/comercial/routes.py:782: should_try = await should_attempt_live_query(...)
```
**Estado:** Esta línea solo se ejecuta para `data_type != "HUB"`. Para HUB, `should_try = True` directamente (línea 778).

---

## 9. RIESGOS RESIDUALES

| Riesgo | Mitigación | Estado |
|--------|------------|--------|
| Circuit breaker LIVE real | Preservado para `data_type != "HUB"` | ✅ Mitigado |
| MongoDB fallback para LIVE | Preservado solo para LIVE-C | ✅ Aceptable (fuera de alcance Fase 1) |
| Dashboard individual (línea 4282) | Usa circuit breaker | ⚠️ Fase 2 |
| MPRO dashboard (línea 4541) | Usa circuit breaker | ⚠️ Fase 2 |

**Referencias MongoDB residuales fuera de alcance Fase 1:**
- Dashboard individual SoftRestaurant (línea 4282-4474)
- Dashboard MPRO (línea 4541-4874)
- Estas referencias aplican para consultas LIVE reales, no para modo HUB

---

## 10. RECOMENDACIÓN PARA FASE 2

### Alcance propuesto:
1. **Dashboard individual SoftRestaurant** (`/api/comercial/dashboard/{server_id}`):
   - Migrar de MongoDB `dashboard_cache` a EDARSAHUB SQL
   - Evaluar si requiere circuit breaker o si puede leer siempre de SQL

2. **Dashboard MPRO** (`/api/comercial/mpro/{server_id}`):
   - Similar migración
   - Evaluar arquitectura: ¿necesita conexión LIVE o puede usar EDARSAHUB?

3. **Tabla SQL de estado de conexión** (opcional):
   - Si jobs de sincronización necesitan circuit breaker, crear tabla SQL
   - Propuesta: `Servidores_EstadoConexion` (ver diagnóstico previo)

### Criterio para Fase 2:
- Solo implementar cuando se requiera consulta LIVE real
- Para tableros que leen EDARSAHUB SQL, NO necesitan circuit breaker

---

## 11. VALIDACIONES ADICIONALES

| Validación | Resultado |
|------------|-----------|
| Login funciona | ✅ PASS |
| `/api/users` retorna 11 | ✅ PASS |
| `/api/servers` retorna 8 | ✅ PASS |
| Comercial V2 carga | ✅ PASS (con parámetros) |
| Tablero Ejecutivo carga | ✅ PASS |
| Sin error 500 | ✅ PASS |
| Sin regresión | ✅ PASS |

---

## 12. CRITERIOS DE ACEPTACIÓN - VERIFICACIÓN

| Criterio | Estado |
|----------|--------|
| Modo HUB no consulta MongoDB para circuit breaker | ✅ CUMPLIDO |
| Modo HUB no usa `kpis_cache`/`dashboard_cache` MongoDB | ✅ CUMPLIDO |
| Tablero Ejecutivo lee EDARSAHUB SQL | ✅ CUMPLIDO |
| Unidades no se bloquean por estado offline servidor externo | ✅ CUMPLIDO |
| No se rompe Comercial V2 ni Tablero Ejecutivo | ✅ CUMPLIDO |
| Se genera reporte | ✅ CUMPLIDO (este documento) |

---

**FASE 1 CERRADA ✅**

**Autor:** Sistema E1  
**Validado:** 2026-05-17 17:45 UTC
