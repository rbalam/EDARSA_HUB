# FIX: Circuit Breaker HUB - Tablero Ejecutivo V1

**Fecha:** 2026-05-17  
**Módulo:** Comercial - Tablero Ejecutivo  
**Prioridad:** P0 - CRÍTICO  
**Estado:** COMPLETADO ✅  

---

## 1. PROBLEMA DETECTADO

El endpoint `/api/comercial/tablero-ejecutivo` devolvía `DATA_FROM_CACHE` para 3 de 5 unidades (CIENFUEGOS, 130° MÉRIDA, LA ESTELAR), a pesar de que EDARSAHUB SQL tenía datos frescos actualizados.

### Síntomas Observados
```
ANTES DEL FIX:
  CIENFUEGOS:    data_status=DATA_FROM_CACHE, ventas=$2,543,511.00
  130° MERIDA:   data_status=DATA_FROM_CACHE, ventas=$1,827,730.00  (datos viejos)
  LA ESTELAR:    data_status=DATA_FROM_CACHE, ventas=$1,512,404.00  (datos viejos)
  130° QUERETARO: data_status=DATA_OK, ventas=$2,037,841.00
  ORIGEN:        data_status=DATA_OK, ventas=$1,322,475.18
```

---

## 2. CAUSA RAÍZ

### Flujo Incorrecto (Antes)
```
Request GET /api/comercial/tablero-ejecutivo
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
Retorna DATA_FROM_CACHE
```

### Problema Arquitectónico
- `get_kpis_softrestaurant()` **YA lee de EDARSAHUB SQL** (no del servidor local)
- El circuit breaker verificaba estado de conexión del **servidor local** en MongoDB
- Cuando el servidor local estaba "offline", bloqueaba una consulta a EDARSAHUB que **siempre funciona**
- Resultado: Se servían datos de caché MongoDB en lugar de datos frescos de EDARSAHUB SQL

---

## 3. DIFERENCIA ENTRE MODO HUB Y MODO LIVE

| Aspecto | Modo HUB | Modo LIVE-C |
|---------|----------|-------------|
| **Propósito** | Datos consolidados/históricos | Ventas del día (crítico) |
| **Fuente de datos** | EDARSAHUB SQL | Servidor local (SoftRestaurant/MPRO) |
| **Circuit breaker** | **NO aplica** | SÍ aplica |
| **Caché fallback** | Solo si EDARSAHUB falla | Si servidor local falla |
| **Ejemplo** | Tablero Ejecutivo mes/año | Ventas del Día |

---

## 4. ARCHIVO MODIFICADO

**Archivo:** `/app/backend/modules/comercial/routes.py`

### Cambio 1: Bypass Circuit Breaker para HUB (líneas ~767-782)
```python
# ANTES:
should_try = await should_attempt_live_query(server['id'], data_type)

# DESPUÉS:
if data_type == "HUB":
    # EDARSAHUB SQL siempre disponible - no aplicar circuit breaker
    should_try = True
    logging.info(f"[HUB-EDARSAHUB] {server['name']}: Modo HUB - lectura directa desde EDARSAHUB SQL")
else:
    # LIVE-C: Aplicar circuit breaker normal para conexiones reales
    should_try = await should_attempt_live_query(server['id'], data_type)
```

### Cambio 2: No guardar estado MongoDB para HUB (líneas ~798-811)
```python
# Solo guardar estado de conexión para modo LIVE-C (conexión real)
if data_type != "HUB":
    if kpis and not kpis.get('error'):
        await save_server_connection_status(server['id'], True)
    elif not solo_ventas_dia:
        await save_server_connection_status(server['id'], False)
```

### Cambio 3: Source indica EDARSAHUB_SQL (líneas ~818-833)
```python
# Indicar fuente correcta en la respuesta
source_period = "EDARSAHUB_SQL" if data_type == "HUB" else "SQL"
source_live = "EDARSAHUB_SQL" if data_type == "HUB" else "TEMPCHEQUES"
live_status = LiveStatus.LIVE_NOT_APPLICABLE if data_type == "HUB" else LiveStatus.LIVE_CONNECTED
```

---

## 5. VALIDACIÓN cURL ANTES/DESPUÉS

### ANTES del FIX
```bash
$ curl -s "$API_URL/api/comercial/tablero-ejecutivo" -H "Authorization: Bearer $TOKEN" | jq '.status_summary'

{
  "total_unidades": 5,
  "unidades_data_ok": 2,
  "unidades_data_cache": 3,    # ❌ PROBLEMA
  "unidades_data_error": 0
}
```

### DESPUÉS del FIX
```bash
$ curl -s "$API_URL/api/comercial/tablero-ejecutivo" -H "Authorization: Bearer $TOKEN" | jq '.status_summary'

{
  "total_unidades": 5,
  "unidades_data_ok": 5,       # ✅ TODAS OK
  "unidades_data_cache": 0,    # ✅ SIN CACHÉ
  "unidades_data_error": 0
}
```

---

## 6. DATA_STATUS ANTES/DESPUÉS

| Unidad | ANTES | DESPUÉS |
|--------|-------|---------|
| CIENFUEGOS | `DATA_FROM_CACHE` | `DATA_OK` ✅ |
| 130° MÉRIDA | `DATA_FROM_CACHE` | `DATA_OK` ✅ |
| LA ESTELAR | `DATA_FROM_CACHE` | `DATA_OK` ✅ |
| 130° QUERÉTARO | `DATA_OK` | `DATA_OK` ✅ |
| ORIGEN | `DATA_OK` | `DATA_OK` ✅ |

---

## 7. VALIDACIÓN DE NO REGRESIÓN

### Circuit Breaker LIVE sigue intacto
```python
# El circuit breaker sigue aplicando para modo LIVE-C:
if data_type == "HUB":
    should_try = True  # HUB: Siempre EDARSAHUB
else:
    # LIVE-C: Aplicar circuit breaker normal
    should_try = await should_attempt_live_query(server['id'], data_type)
```

### Verificación de módulos no afectados
- [x] Comercial V2: No modificado
- [x] Auth/RBAC: No modificado
- [x] Compras: No modificado
- [x] Finanzas: No modificado
- [x] Inventarios: No modificado

---

## 8. CONFIRMACIONES

### EDARSAHUB SQL es fuente primaria del Tablero Ejecutivo
```
Flujo correcto implementado:
Request ─► data_type="HUB" ─► should_try=True ─► get_kpis_softrestaurant() ─► EDARSAHUB SQL ─► DATA_OK
```

### Circuit Breaker LIVE sigue funcionando
```
Para modo LIVE-C (Ventas del Día):
Request ─► data_type="LIVE-C" ─► should_attempt_live_query() ─► circuit breaker aplicado
```

### MongoDB NO es fuente primaria
- El circuit breaker de MongoDB (`server_status`) ya no bloquea lecturas HUB
- La caché MongoDB (`kpis_cache`) solo se usa si EDARSAHUB SQL falla

---

## 9. RESULTADO FINAL

```
=== VALIDACIÓN POST-FIX: TABLERO EJECUTIVO V1 ===
Periodo: 5/2026
Dias transcurridos: 17

=== STATUS SUMMARY ===
  Total unidades: 5
  DATA_OK: 5           ✅
  DATA_FROM_CACHE: 0   ✅
  DATA_ERROR: 0        ✅

=== DETALLE POR UNIDAD ===
  CIENFUEGOS:
    data_status: DATA_OK
    source_period: EDARSAHUB_SQL
    ventas: $2,543,511.00

  130° MERIDA:
    data_status: DATA_OK
    source_period: EDARSAHUB_SQL
    ventas: $2,094,097.00

  130° QUERETARO:
    data_status: DATA_OK
    source_period: SQL
    ventas: $2,037,841.00

  LA ESTELAR:
    data_status: DATA_OK
    source_period: EDARSAHUB_SQL
    ventas: $1,744,171.00

  ORIGEN:
    data_status: DATA_OK
    source_period: SQL
    ventas: $1,322,475.18
```

---

**Autor:** Sistema E1  
**Validado:** 2026-05-17 17:15 UTC  
**Estado:** COMPLETADO ✅
