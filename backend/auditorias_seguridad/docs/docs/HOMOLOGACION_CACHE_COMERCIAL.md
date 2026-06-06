# HOMOLOGACIÓN SourceQueryResult + Cache en Módulo Comercial

**Fecha:** 2026-04-20  
**Versión:** 3.4.2  
**Autor:** Arquitectura Senior

---

## 1. OBJETIVO

Implementar cache controlado en los endpoints individuales de Comercial con respuesta homologada (SourceQueryResult), mejorando la resiliencia cuando las fuentes SQL/API no respondan.

## 2. SERVICIO CENTRAL DE CACHE

### Archivo: `/app/backend/modules/comercial/cache_service.py`

```python
# TTLs configurables
CACHE_TTL = {
    "dashboard": 180,       # 3 minutos
    "reporte_pax": 180,     # 3 minutos
    "ticket_perfecto": 300, # 5 minutos
    "metas": 900,           # 15 minutos
}

# Estados de respuesta
SourceStatus.SUCCESS          # Query exitosa con datos
SourceStatus.NO_DATA          # Query exitosa sin datos
SourceStatus.DEGRADED_CACHE   # Usando cache como fallback
SourceStatus.SOURCE_UNREACHABLE # Sin datos ni cache
SourceStatus.ERROR            # Error interno
```

### Funciones Principales

| Función | Descripción |
|---------|-------------|
| `build_cache_key()` | Genera clave única por módulo+endpoint+servidor+fecha+filtros |
| `get_cached_response()` | Obtiene datos de cache si no expiró |
| `save_to_cache()` | Guarda respuesta exitosa en cache |
| `build_envelope_response()` | Construye envelope de respuesta homologado |

## 3. ENVELOPE DE RESPUESTA ESTÁNDAR

Todos los endpoints homologados devuelven:

```json
{
  "source_status": "SUCCESS|NO_DATA|DEGRADED_CACHE|SOURCE_UNREACHABLE|ERROR",
  "source_message": "Descripción del estado",
  "fuentes_consultadas": ["servidor"],
  "cache_used": false,
  "last_successful_sync": null,
  "server_name": "CIENFUEGOS",
  "server_type": "SoftRestaurant",
  "data": { ... },
  "timestamp": "2026-04-20T16:00:00Z"
}
```

## 4. ENDPOINTS HOMOLOGADOS

| Endpoint | TTL | Estado |
|----------|-----|--------|
| `/comercial/metas/{server_id}` | 15 min | ✅ Homologado |
| `/comercial/ticket-perfecto/{server_id}` | 5 min | ✅ Homologado |
| `/comercial/reporte-pax/{server_id}` | 3 min | ✅ Homologado |
| `/comercial/dashboard/{server_id}` | - | Ya tenía source_status |
| `/comercial/tablero-ejecutivo` | - | No tocado (tiene su propio cache) |

## 5. COMPORTAMIENTO DE CACHE

### Caso 1: SQL/API Responde
```
source_status = SUCCESS (o NO_DATA si vacío)
cache_used = false
→ Se guarda en cache para futuras fallas
```

### Caso 2: SQL/API Falla + Cache Existe
```
source_status = DEGRADED_CACHE
cache_used = true
last_successful_sync = timestamp del cache
→ Se muestra advertencia de datos no actuales
```

### Caso 3: SQL/API Falla + Sin Cache
```
source_status = SOURCE_UNREACHABLE
cache_used = false
data = estructura vacía controlada
→ Frontend muestra mensaje apropiado
```

## 6. COLECCIÓN MONGODB

```
Collection: comercial_cache
Índices:
  - cache_key (unique)
  - cached_at (para TTL queries)

Documento:
{
  cache_key: "comercial:metas:server123:all:2026-04-20",
  data: { ... },
  cached_at: "2026-04-20T16:00:00Z",
  ttl: 900,
  endpoint: "metas",
  server_name: "CIENFUEGOS",
  server_type: "SoftRestaurant"
}
```

## 7. VALIDACIONES REALIZADAS

| Endpoint | Resultado |
|----------|-----------|
| Metas | ✅ source_status: NO_DATA, cache_used: false |
| Ticket Perfecto | ✅ source_status: NO_DATA, cache_used: false |
| Reporte PAX | ✅ source_status: NO_DATA, cache_used: false |
| Dashboard MPRO | ✅ source_status: SUCCESS (sin regresión) |
| Tablero Ejecutivo | ✅ 5 unidades, $10.2M (sin regresión) |

## 8. REGLAS DE IMPLEMENTACIÓN

1. **Cache NO es fuente de verdad** - Siempre intenta SQL primero
2. **Sin datos inventados** - Si falla todo, devuelve estructura vacía
3. **Fórmulas intactas** - No se modificaron cálculos de Ventas, PAX, Ticket
4. **Tablero Ejecutivo no tocado** - Mantiene su propio sistema de cache
5. **Granularidad de cache** - Por servidor + fecha + filtros

## 9. PRÓXIMOS PASOS

- [x] Agregar indicador visual en frontend cuando cache_used=true (2026-04-20)
- [ ] Homologar endpoints restantes (ventas-tiempo, mesas)
- [ ] Implementar purga automática de cache expirado

## 10. INDICADORES VISUALES EN FRONTEND

### Componentes Actualizados (2026-04-20)

| Componente | Archivo | Estado |
|------------|---------|--------|
| Dashboard (tab principal) | Comercial.js | ✅ Homologado |
| MetasVentas | Comercial.js | ✅ Homologado |
| TicketPerfecto | Comercial.js | ✅ Homologado |
| ReportePax | Comercial.js | ✅ Homologado |

### Indicadores Visuales Implementados

1. **DEGRADED_CACHE** (fondo amber):
   - Icono: Clock
   - Mensaje descriptivo con timestamp de última sincronización
   - Texto: "La fuente de datos no está disponible. Mostrando datos guardados previamente."

2. **NO_DATA** (fondo blue):
   - Icono: Info
   - Mensaje: Conexión exitosa pero sin datos en el período

3. **SOURCE_UNREACHABLE** (fondo orange):
   - Icono: AlertTriangle
   - Mensaje: No se pudo conectar a la fuente

4. **Indicador sutil de cache** (pill amber):
   - Cuando cache_used=true pero status=SUCCESS
   - Muestra "Datos de cache" con timestamp

---

**Documento de referencia para implementación de cache en otros módulos**
