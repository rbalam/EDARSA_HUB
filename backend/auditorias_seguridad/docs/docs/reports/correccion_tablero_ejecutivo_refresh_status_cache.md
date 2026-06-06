# P0 — CORRECCIÓN TABLERO EJECUTIVO: Refresco Automático + Status Correcto + Uso Estricto de Cache

**Fecha**: 2026-04-30
**Status**: IMPLEMENTADO

## 1. Causa Raíz

El frontend estaba reutilizando el campo `status` (online/offline) anterior al cambiar de pantalla, mientras los datos del período sí se actualizaban correctamente. Esto generaba inconsistencia visual:

- **Problema**: Una unidad podía mostrar `ventas = $4M` con badge visual "Offline"
- **Causa**: El campo `status` era un campo único que mezclaba el estado de datos (`data_status`) con el estado de conexión en vivo (`live_status`)

## 2. Archivos Revisados

- `/app/frontend/src/pages/TableroEjecutivo.js`
- `/app/backend/modules/comercial/routes.py`
- `/app/backend/modules/comercial/service.py`

## 3. Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `/app/backend/modules/comercial/service.py` | Agregadas clases `DataStatus`, `LiveStatus`, `CacheStatus`, `SourceUsed`, `SourceRealStatus` y función `build_unit_response()` |
| `/app/backend/modules/comercial/routes.py` | Refactorizado endpoint `/tablero-ejecutivo` para usar nueva estructura. Agregado `status_summary` en respuesta |
| `/app/frontend/src/pages/TableroEjecutivo.js` | Actualizado `UnidadCard` para usar nuevos estados. Agregado refresco automático con `visibilitychange` y TTL |

## 4. Lógica Anterior

```javascript
// Frontend
const isOnline = unidad.status === 'online';
const isOffline = unidad.status === 'offline';

// Backend
resultados.append({
    "status": "online" | "offline" | "error",
    // ... sin distinguir data vs live
})
```

## 5. Lógica Nueva

### Backend - Estructura de respuesta por unidad:
```json
{
  "unidad_key": "server_id:sucursal",
  "data_status": "DATA_OK|DATA_FROM_CACHE|NO_DATA_CONFIRMED|DATA_ERROR",
  "live_status": "LIVE_CONNECTED|LIVE_UNREACHABLE_PREVIEW_ENV|LIVE_UNREACHABLE_REAL|LIVE_API_UNREACHABLE",
  "cache_status": "NOT_USED|USED_CONNECTION_FALLBACK|AVAILABLE_NOT_USED|STALE|MISSING",
  "source_used": "REAL_SOURCE|CACHE|NONE",
  "source_real_attempted": true,
  "source_real_status": "SUCCESS|CONNECTION_ERROR|TIMEOUT|QUERY_ERROR",
  "cache_warning": null | "Mensaje de advertencia",
  "status": "online",  // Compatibilidad legacy
  // ... KPIs
}
```

### Frontend - Determinación de estado visual:
```javascript
const dataStatus = unidad.data_status || 'DATA_OK';
const liveStatus = unidad.live_status || 'LIVE_CONNECTED';
const sourceUsed = unidad.source_used || 'REAL_SOURCE';

// Caso A: DATA_OK + REAL_SOURCE + LIVE_CONNECTED = Verde
// Caso B: DATA_OK + REAL_SOURCE + LIVE_UNREACHABLE_PREVIEW = Verde/Gris
// Caso D: DATA_FROM_CACHE = Amarillo con advertencia
// Caso E: DATA_ERROR = Rojo con mensaje
```

## 6. Eventos que Disparan Refresh

1. **Montaje inicial** del componente (`useEffect` con `[]`)
2. **Cambio de filtros** (mes, año, tipo_comparacion)
3. **Clic en botón Actualizar** (refresh manual forzado)
4. **`visibilitychange`** cuando la página vuelve a ser visible y datos > TTL
5. **Vencimiento de TTL** (120 segundos) al regresar al tablero

## 7. Separación data_status / live_status / cache_status

| Campo | Propósito | Valores |
|-------|-----------|---------|
| `data_status` | ¿Se obtuvieron datos? | DATA_OK, DATA_FROM_CACHE, DATA_ERROR, NO_DATA_CONFIRMED |
| `live_status` | ¿Conexión en vivo disponible? | LIVE_CONNECTED, LIVE_UNREACHABLE_PREVIEW_ENV, LIVE_UNREACHABLE_REAL, LIVE_API_UNREACHABLE |
| `cache_status` | ¿Se usó caché? | NOT_USED, USED_CONNECTION_FALLBACK, MISSING |
| `source_used` | ¿Qué fuente se usó? | REAL_SOURCE, CACHE, NONE |

## 8. Regla Estricta de Cache

El cache solo se usa cuando:
1. La fuente real fue intentada primero (`source_real_attempted: true`)
2. La fuente real falló por conectividad (`source_real_status: CONNECTION_ERROR|TIMEOUT`)
3. Existe cache válido para la misma unidad/período
4. El frontend muestra advertencia visible (`cache_warning`)

El cache NO se usa cuando:
- Hay error de query/mapeo/permisos (mostrar error controlado)
- La fuente real está disponible (usar dato real)
- Es modo "Ventas del Día" (LIVE-C crítico, no tolera cache)

## 9. Manejo de Status Stale

```javascript
const STATUS_TTL_SECONDS = 120;

// Al regresar a la página:
if (secondsSinceRefresh > STATUS_TTL_SECONDS) {
  // Datos stale, refrescar automáticamente
  cargarDatos(0, true);
}
```

## 10. Control de request_id

```javascript
const [requestId, setRequestId] = useState(0);

const cargarDatos = async (retry, forceRefresh) => {
  const currentRequestId = requestId + 1;
  setRequestId(currentRequestId);
  
  // ... fetch data ...
  
  // Solo actualizar si es el request actual
  if (currentRequestId === requestId + 1 || forceRefresh) {
    setData(response.data);
  }
};
```

## 11. Matriz de Pruebas

| Unidad | Fuente real intentada | Source usado | Datos período | Status antes | Status después | Cache usado | Advertencia visible | Resultado |
|--------|----------------------|--------------|---------------|--------------|----------------|-------------|---------------------|-----------|
| 130° MÉRIDA | ✅ | REAL_SOURCE | ✅ $4.06M | N/A | 🟢 DATA_OK | NO | NO | PASS REAL_SOURCE |
| CIENFUEGOS | ✅ | REAL_SOURCE | ✅ $3.71M | N/A | 🟢 DATA_OK | NO | NO | PASS REAL_SOURCE |
| LA ESTELAR | ✅ | REAL_SOURCE | ✅ $2.39M | N/A | 🟢 DATA_OK | NO | NO | PASS REAL_SOURCE |
| 130° QUERÉTARO | ✅ | REAL_SOURCE | ✅ $3.19M | N/A | 🟢 DATA_OK | NO | NO | PASS REAL_SOURCE |
| ORIGEN | ✅ | REAL_SOURCE | ✅ $1.77M | N/A | 🟢 DATA_OK | NO | NO | PASS REAL_SOURCE |

## 12. Consolidado Superior (status_summary)

```json
{
  "status_summary": {
    "total_unidades": 5,
    "unidades_data_ok": 5,
    "unidades_data_cache": 0,
    "unidades_data_error": 0,
    "unidades_no_data": 0,
    "unidades_live_connected": 5,
    "unidades_live_unreachable": 0,
    "unidades_source_real": 5,
    "unidades_source_cache": 0
  }
}
```

## Criterio de Aceptación

- [x] Al abrir Tablero Ejecutivo se actualizan status y datos automáticamente
- [x] Al regresar desde otra pantalla no quedan Offline obsoletos (TTL + visibilitychange)
- [x] Unidades con DATA_OK no muestran Offline genérico
- [x] SoftRestaurant no queda marcado Offline si tiene datos válidos
- [x] El botón Actualizar intenta fuente real (forceRefresh=true)
- [x] Cache solo se usa si la fuente real falló por conectividad
- [x] El usuario ve advertencia clara cuando se usa cache
- [x] El consolidado superior muestra desglose de estados
- [x] No hay $0 silencioso (DATA_ERROR no incluye KPIs)
- [x] EDARSAHUB SQL sigue siendo fuente maestra
