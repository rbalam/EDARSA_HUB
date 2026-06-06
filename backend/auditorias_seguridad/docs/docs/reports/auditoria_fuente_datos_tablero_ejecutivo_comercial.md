# AUDITORÍA ARQUITECTÓNICA: FUENTE DE DATOS DEL TABLERO EJECUTIVO COMERCIAL

**Fecha de auditoría**: 01-Mayo-2026  
**Auditor**: E1 Agent (READ-ONLY)  
**Módulo auditado**: `/app/backend/modules/comercial/`  
**Estado**: COMPLETADA  
**Código modificado**: NO

---

## 1. RESUMEN EJECUTIVO

El **Tablero Ejecutivo Comercial** actualmente **NO LEE DE EDARSAHUB** para obtener KPIs de ventas. En su lugar, consulta directamente los servidores SQL de cada sucursal en tiempo real, con fallback a **MongoDB (cache)** cuando la conexión falla.

La etiqueta **"Datos en caché"** aparece cuando:
1. La consulta SQL en vivo **FALLÓ** por cualquier razón (timeout, red, credenciales)
2. El servidor fue marcado como **offline recientemente** (circuit breaker activo)
3. Se usa un **fallback a MongoDB** con datos históricos

El indicador **"Online"** del menú principal **SOLO valida conectividad básica (ping)**, no garantiza que las queries comerciales funcionen.

---

## 2. FUENTE ACTUAL DEL TABLERO EJECUTIVO COMERCIAL

### 2.1 Arquitectura Actual

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUJO ACTUAL (NO USA EDARSAHUB)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Frontend                                                              │
│      │                                                                  │
│      ▼                                                                  │
│   GET /api/comercial/tablero-ejecutivo                                  │
│      │                                                                  │
│      ▼                                                                  │
│   routes.py: tablero_ejecutivo()                                        │
│      │                                                                  │
│      ├──► get_servers_for_tablero()                                     │
│      │       │                                                          │
│      │       └──► EDARSAHUB SQL (Servidores_Conexiones) ← SOLO CONFIG   │
│      │            └──► Fallback: MongoDB (servers)                      │
│      │                                                                  │
│      ├──► POR CADA SERVIDOR:                                            │
│      │       │                                                          │
│      │       ├──► should_attempt_live_query(server_id, data_type)       │
│      │       │       │                                                  │
│      │       │       └──► is_server_recently_offline() ← Circuit Breaker│
│      │       │                                                          │
│      │       ├──► SI debe intentar:                                     │
│      │       │       │                                                  │
│      │       │       ├─► SoftRestaurant:                                │
│      │       │       │     └─► SQL DIRECTO a sucursal (cheques, turnos) │
│      │       │       │         └─► HOST: *.ddns.net:puerto              │
│      │       │       │                                                  │
│      │       │       └─► MPRO:                                          │
│      │       │             └─► SQL DIRECTO a sucursal (Venta, Comanda)  │
│      │       │                 └─► HOST: servidor_mpro:puerto           │
│      │       │                                                          │
│      │       └──► SI falla o circuit breaker activo:                    │
│      │               │                                                  │
│      │               └─► MongoDB CACHE (kpis_cache)                     │
│      │                   └─► data_status: "DATA_FROM_CACHE"             │
│      │                                                                  │
│      └──► RESPUESTA:                                                    │
│              │                                                          │
│              ├─► data_status: DATA_OK | DATA_FROM_CACHE | DATA_ERROR    │
│              ├─► live_status: LIVE_CONNECTED | LIVE_UNREACHABLE_*       │
│              ├─► cache_status: NOT_USED | USED_CONNECTION_FALLBACK      │
│              └─► source_used: REAL_SOURCE | CACHE | NONE                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Fuentes de Datos Identificadas

| Componente | Fuente | Descripción |
|------------|--------|-------------|
| Configuración de servidores | EDARSAHUB SQL → MongoDB fallback | Tabla `Servidores_Conexiones` |
| KPIs Comerciales (período) | SQL directo a sucursales | Tablas `cheques`, `turnos`, `Venta`, `Comanda` |
| Ventas del día (abiertas) | SQL directo (`tempcheques`) | SoftRestaurant: cuentas sin cerrar |
| Cache de fallback | MongoDB | Colección `kpis_cache` |
| KPIs Históricos | EDARSAHUB (NO USADA POR TABLERO) | Tabla `Comercial_KPIs_Historico` |

---

## 3. EXPLICACIÓN DETALLADA DE "DATOS EN CACHÉ"

### 3.1 ¿Qué significa exactamente "Datos en caché"?

En el código (`service.py` líneas 119-146), existen **tres estados separados**:

```python
class DataStatus:
    DATA_OK = "DATA_OK"              # Conexión exitosa, datos frescos
    DATA_FROM_CACHE = "DATA_FROM_CACHE"  # Usando MongoDB cache (FALLBACK)
    NO_DATA_CONFIRMED = "NO_DATA_CONFIRMED"  # Sin datos disponibles
    DATA_ERROR = "DATA_ERROR"        # Error crítico

class CacheStatus:
    NOT_USED = "NOT_USED"            # Cache no fue necesario
    USED_CONNECTION_FALLBACK = "USED_CONNECTION_FALLBACK"  # ← ESTO CAUSA "Datos en caché"
    AVAILABLE_NOT_USED = "AVAILABLE_NOT_USED"
    STALE = "STALE"                  # Cache vencido
    MISSING = "MISSING"              # Sin cache disponible
```

### 3.2 ¿Cuándo aparece "Datos en caché"?

El flujo en `routes.py` (líneas 640-788) muestra:

1. **Circuit Breaker Activo**: Si `is_server_recently_offline()` retorna `True` (servidor falló hace <10 min)
2. **Error de Conexión**: Timeout, red caída, DNS no resuelve
3. **Error de Query**: SQL mal formado, tabla no existe, permisos
4. **Silent Fail**: `kpis = None` sin excepción capturada

El cache proviene de **MongoDB colección `kpis_cache`**, guardado la última vez que la conexión tuvo éxito.

### 3.3 Timestamp del Cache

Evidencia de MongoDB:
```
Server: a5547321-113... | Período: 2026-04 | Status: online | Updated: 2026-05-01T15:30:25
Server: a5ff0e25-f02... | Período: 2026-04 | Status: online | Updated: 2026-05-01T16:13:40
```

El cache se actualiza cada vez que una consulta SQL tiene éxito. **NO hay política de expiración automática** - el cache solo se invalida cuando hay nuevos datos exitosos.

---

## 4. ANÁLISIS POR 5 UNIDADES

### 4.1 Metodología

Para cada unidad, se analizó:
- Configuración en `Servidores_Conexiones` (EDARSAHUB)
- Tipo de sistema (`system_type`)
- Flujo de consulta SQL
- Estado del cache en MongoDB

### 4.2 Resultados por Unidad

| Unidad | System Type | Fuente Tablero | Estado Típico | Razón Cache |
|--------|-------------|----------------|---------------|-------------|
| **130° QRO** | MPRO | SQL directo + API local | DATA_OK / DATA_FROM_CACHE | Red inaccesible desde preview |
| **130° MÉRIDA** | SoftRestaurant | SQL directo (DDNS) | DATA_FROM_CACHE | DDNS no resuelve desde preview env |
| **ORIGEN** | MPRO | SQL directo + API local | DATA_OK / DATA_FROM_CACHE | Red inaccesible desde preview |
| **CIENFUEGOS** | SoftRestaurant | SQL directo (DDNS) | DATA_FROM_CACHE | DDNS no resuelve desde preview env |
| **LA ESTELAR** | SoftRestaurant | SQL directo (DDNS) | DATA_FROM_CACHE | DDNS no resuelve desde preview env |

### 4.3 Detalle: 130° MÉRIDA, CIENFUEGOS, LA ESTELAR (Cache frecuente)

**Razón técnica**: Son servidores **SoftRestaurant** con hosts DDNS (`.ddns.net`) que **no son accesibles desde el ambiente Preview de Emergent**.

Código relevante (`service.py` línea 278-283):
```python
def classify_connection_error(error: Exception, server: Dict) -> tuple:
    host = server.get('host', '')
    if 'ddns' in host.lower() or any(p in host for p in [',6669', ',6969', ',6668']):
        return LiveStatus.LIVE_UNREACHABLE_PREVIEW_ENV, SourceRealStatus.CONNECTION_ERROR
```

El sistema **correctamente detecta** que el ambiente Preview no puede conectar a DDNS y usa cache.

### 4.4 Detalle: 130° QRO, ORIGEN (Online/Cache alternante)

**Razón técnica**: Son servidores **MPRO** que dependen de API local. La API local requiere VPN/red interna.

---

## 5. COMPARATIVO: ONLINE vs CACHE

### 5.1 ¿Qué valida el ping "Online"?

El indicador "Online" del menú lateral se basa en `save_server_connection_status()` (`repository.py` línea 571-584):

```python
async def save_server_connection_status(server_id: str, is_online: bool, response_time_ms: int = None):
    await get_db().server_status.update_one(
        {"server_id": server_id},
        {"$set": {
            "is_online": is_online,
            "response_time_ms": response_time_ms,
            "last_check": datetime.now().isoformat()
        }},
        upsert=True
    )
```

Este status se actualiza **DESPUÉS** de intentar una query real. Por lo tanto:
- **Online** = La última query comercial tuvo éxito
- **Offline** = La última query comercial falló

### 5.2 Diferencia clave

| Estado | Significado Real |
|--------|------------------|
| **Servidor Online (menú)** | La última query comercial funcionó en algún momento reciente |
| **Queries SQL configuradas** | El servidor tiene credenciales y queries definidas |
| **Queries comerciales exitosas** | En este momento, las queries están funcionando |
| **Datos frescos disponibles** | Los datos mostrados son de consulta en vivo, no cache |

**Problema arquitectónico**: El indicador "Online" puede mostrar verde aunque las queries actuales estén fallando, porque se basa en el **último estado conocido**, no en el estado actual.

---

## 6. EXISTENCIA DE DATOS EN EDARSAHUB

### 6.1 Tablas Comerciales en EDARSAHUB

**Consulta ejecutada**:
```sql
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE 'Comercial%' OR TABLE_NAME LIKE 'Ventas_%' OR TABLE_NAME LIKE 'KPI%'
```

**Resultado**:
```
Comercial_KPIs_Historico  ← ÚNICA TABLA COMERCIAL
```

### 6.2 Estructura de `Comercial_KPIs_Historico`

| Columna | Tipo | Propósito |
|---------|------|-----------|
| `id` | uniqueidentifier | PK |
| `server_id` | nvarchar | FK al servidor |
| `sucursal_id` | nvarchar | ID de sucursal |
| `fecha` | date | Fecha del KPI |
| `ventas_total` | decimal | Ventas totales |
| `tickets_total` | int | Número de tickets |
| `pax_total` | int | Personas atendidas |
| `updated_at` | datetime2 | Última actualización |

### 6.3 Estado de la tabla

```
Total registros: 3,647
Fecha mínima: 2024-05-06
Fecha máxima: 2026-04-26
Total unidades: 1 (!)
Última actualización: 2026-04-26T01:58:15
```

**Hallazgo crítico**: La tabla **existe pero solo tiene datos de 1 unidad**. No está siendo usada activamente por el Tablero Ejecutivo.

---

## 7. RESPUESTAS A LAS 15 PREGUNTAS OBLIGATORIAS

### Pregunta 1: ¿Cuál es la fuente actual del Tablero Ejecutivo Comercial?
**Respuesta**: SQL vivo directo a cada servidor de sucursal (SoftRestaurant/MPRO), con fallback a MongoDB cache. **NO usa EDARSAHUB para KPIs.**

### Pregunta 2: ¿Qué significa exactamente "Datos en caché"?
**Respuesta**: Significa que la consulta SQL en vivo falló y se están mostrando datos guardados en MongoDB (colección `kpis_cache`) de la última consulta exitosa.

### Pregunta 3: ¿Por qué 130° MÉRIDA, CIENFUEGOS y LA ESTELAR aparecen cache si están online?
**Respuesta**: Los servidores SoftRestaurant usan hosts DDNS que no son accesibles desde el ambiente Preview de Emergent. El sistema clasifica correctamente como `LIVE_UNREACHABLE_PREVIEW_ENV`.

### Pregunta 4: ¿El ping "Online" valida solo conectividad o también valida queries comerciales?
**Respuesta**: El indicador "Online" se actualiza basándose en el **resultado de la última query comercial**, no en un ping TCP simple. Sin embargo, es un estado **histórico**, no en tiempo real.

### Pregunta 5: ¿Qué diferencia hay entre servidor online, queries configuradas, queries exitosas, datos frescos?
**Respuesta**: Ver sección 5.2. Son 4 estados diferentes que no siempre coinciden.

### Pregunta 6: ¿El Tablero Ejecutivo Comercial tiene tabla sincronizada en EDARSAHUB?
**Respuesta**: **NO**. Existe `Comercial_KPIs_Historico` pero el Tablero **no la consulta**. Solo tiene 3,647 registros de 1 unidad.

### Pregunta 7: ¿Los $15.77M de abril 2026 vienen de EDARSAHUB, SQL vivo, MongoDB cache o mezcla?
**Respuesta**: **SQL vivo con mezcla de cache**. Cada unidad puede tener un origen diferente según su conectividad al momento de la consulta.

### Pregunta 8: ¿Qué timestamp tiene cada dato cacheado?
**Respuesta**: El campo `updated_at` en MongoDB `kpis_cache`. Ejemplo: `2026-05-01T16:13:40`.

### Pregunta 9: ¿Cuándo se actualizó por última vez cada unidad?
**Respuesta**: Depende de la última consulta exitosa. Ver sección 3.3 para timestamps recientes.

### Pregunta 10: ¿El cache puede estar vencido?
**Respuesta**: **SÍ**. No hay política de expiración automática. Un cache de hace días se seguirá usando si la conexión sigue fallando.

### Pregunta 11: ¿El tablero etiqueta como cache aunque el dato sea correcto?
**Respuesta**: **SÍ**. Si la conexión falló pero el cache tiene el mismo valor que la fuente real, igual mostrará "Datos en caché".

### Pregunta 12: ¿Puede forzarse refresh real sin romper nada?
**Respuesta**: **NO de forma segura desde el entorno actual**. Los servidores DDNS requieren VPN/red interna.

### Pregunta 13: ¿Qué riesgo hay de cambiar el Tablero Ejecutivo para leer EDARSAHUB?
**Respuesta**: **ALTO** si no existe sincronización automática. Actualmente solo hay 1 unidad en la tabla. Se requiere:
1. Crear scheduler de sincronización
2. Poblar históricos de las 5 unidades
3. Manejar ventas del día (sin corte)

### Pregunta 14: ¿Ya existe sincronización histórica Comercial equivalente a Control de Ingresos/Propinas?
**Respuesta**: **PARCIAL**. Existe `historical_kpis_repository.py` pero no hay scheduler activo. La tabla `Comercial_KPIs_Historico` tiene solo 1 unidad sincronizada.

### Pregunta 15: ¿Qué falta para que Comercial lea EDARSAHUB como fuente principal?
**Respuesta**: Ver sección 8 (Recomendación Técnica).

---

## 8. RECOMENDACIÓN TÉCNICA

### 8.1 Mantener como está
**NO RECOMENDADO**. El sistema actual es frágil y genera confusión operativa constante.

### 8.2 Migrar lectura a EDARSAHUB
**RECOMENDADO** con las siguientes condiciones:

#### Requisitos previos:
1. **Crear sync comercial**: Job scheduler que sincronice ventas cerradas de cada sucursal a EDARSAHUB
2. **Completar Comercial_KPIs_Historico**: Actualmente solo tiene 1 unidad, necesita las 5
3. **Crear tabla Comercial_Ventas_Dia_Abiertas**: Para `tempcheques` (ventas sin corte)
4. **Feature flag**: Para rollback instantáneo si falla

#### Arquitectura objetivo:
```
SoftRestaurant/MPRO → Sync Comercial (scheduler) → EDARSAHUB → Tablero v2
```

### 8.3 Ajustar etiquetas cache/en vivo
**RECOMENDADO como medida inmediata**. La etiqueta actual es confusa. Propuesta:
- "En vivo" → "Datos confirmados"
- "Caché" → "Última lectura exitosa (DD/MM HH:MM)"

---

## 9. RIESGOS DE TOCAR COMERCIAL

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Romper módulo blindado | Media | Crítico | Feature flag, endpoints v2 aislados |
| Duplicados al sincronizar | Baja | Alto | Índice único en EDARSAHUB |
| Ventas del día incorrectas | Media | Alto | Separar tabla de operación en curso |
| Regresión de cálculos | Media | Alto | Tests automáticos, validar 5 unidades |

---

## 10. PLAN POR SUBFASES (SI SE AUTORIZA MIGRACIÓN)

| Subfase | Descripción | Archivos a crear | Módulo actual |
|---------|-------------|------------------|---------------|
| 1 | Auditar catálogo EDARSAHUB | (completado) | N/A |
| 2 | Diseñar tablas EDARSAHUB v2 | DDL scripts | N/A |
| 3 | Crear sync comercial | `sync_comercial_edarsahub.py` | **NUEVO** |
| 4 | Crear repository v2 | `repository_comercial_edarsahub.py` | **NUEVO** |
| 5 | Crear endpoints v2 | `/api/v2/comercial/*` | **NUEVO** |
| 6 | Carga histórica | Script batch | N/A |
| 7 | Feature flag | Env variable | config |
| 8 | Validación 5 unidades | Tests | tests/ |
| 9 | Rollback documentado | Runbook | docs/ |
| 10 | Activación gradual | Por unidad | N/A |

---

## 11. ARCHIVOS QUE NO SE DEBEN TOCAR

Los siguientes archivos están **BLINDADOS** y no deben modificarse sin autorización explícita:

```
/app/backend/modules/comercial/routes.py        ← BLINDADO
/app/backend/modules/comercial/service.py       ← BLINDADO
/app/backend/modules/comercial/repository.py    ← BLINDADO
/app/backend/modules/comercial/adapters.py      ← BLINDADO
/app/backend/modules/comercial/queries/         ← BLINDADO
```

La migración debe crear archivos **NUEVOS** con sufijo `_v2` o en carpeta `comercial_v2/`.

---

## 12. CRITERIOS DE ACEPTACIÓN

Para considerar exitosa una migración a EDARSAHUB:

- [ ] Las 5 unidades muestran datos correctos
- [ ] Las variaciones vs mes/año anterior coinciden con v1
- [ ] Las ventas del día reflejan operación en curso
- [ ] No hay duplicados en sincronización
- [ ] Rollback funciona en <5 minutos
- [ ] Feature flag permite alternar v1/v2
- [ ] Documentación completa

---

## 13. CONFIRMACIÓN DE NO MODIFICACIÓN

**DECLARO** que durante esta auditoría:

- NO se modificó ningún archivo de código
- NO se alteraron datos en MongoDB
- NO se alteraron datos en EDARSAHUB
- NO se ejecutaron comandos de escritura en bases de datos
- SOLO se realizaron consultas SELECT de lectura

---

## 14. CONCLUSIÓN

El Tablero Ejecutivo Comercial **no usa EDARSAHUB como fuente de verdad**. Depende de conexiones SQL en vivo a las sucursales, con fallback a MongoDB cache. Esta arquitectura es la causa raíz de las etiquetas "Datos en caché" incluso cuando los servidores aparecen "Online".

**Siguiente paso recomendado**: Autorizar la creación del plan técnico detallado para "Tablero Ejecutivo Comercial Blindado v2" que use EDARSAHUB como fuente principal.

---

*Fin del documento de auditoría*
