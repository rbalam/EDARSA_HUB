# COMPRAS - BLINDAJE POR system_type PARA MPRO/ManagementPro

## Fecha: Diciembre 2025
## Autor: EDARSA HUB - Arquitecto Senior

---

## 1. RESUMEN EJECUTIVO

Este documento describe el diagnóstico y corrección del módulo Compras para evitar que queries de SoftRestaurant se ejecuten contra bases ManagementPro y viceversa.

---

## 2. PROBLEMA ORIGINAL

El módulo Compras falla cuando consulta unidades MPRO/ManagementPro porque:
1. Algunos endpoints retornan `[]` vacío cuando `system_type` no es reconocido
2. Errores SQL se transforman silenciosamente en "sin datos"
3. No hay distinción clara entre NO_DATA real y errores técnicos
4. La normalización de `system_type` no es consistente

---

## 3. ARCHIVOS DIAGNOSTICADOS

### Backend (server.py) - Endpoints de Compras:
| Línea | Endpoint | Estado |
|-------|----------|--------|
| 5888 | GET /compras/inventarios-fisicos/{server_id} | Tiene separación MPRO/SR, retorna [] si no match |
| 5993 | GET /compras/pedidos-vigentes/{server_id} | Tiene separación MPRO/SR |
| 6062 | GET /compras/detalle-pedido-manual/{server_id} | Solo MPRO |
| 6117 | GET /compras/detalle-movimientos/{server_id} | Solo MPRO |
| 6154 | GET /compras/detalle-consumos/{server_id} | Solo MPRO |
| 6189 | GET /compras/detalle-pedido/{server_id}/{folio} | Solo MPRO |
| 6236 | POST /compras/calculo-pedido | Tiene separación MPRO/SR |
| 6666 | GET /compras/parametros/{server_id} | Sin SQL, MongoDB |
| 6687 | POST /compras/parametros | Sin SQL, MongoDB |
| 6731 | POST /compras/productos-para-captura | Tiene separación MPRO/SR |
| 6840 | POST /compras/auditoria-operativa | Tiene separación MPRO/SR |
| 7553 | POST /compras/detalle-movimientos | Tiene separación MPRO/SR |
| 7730 | POST /compras/detalle-consumos | Tiene separación MPRO/SR |
| 7837 | GET /compras/dashboard/{server_id} | Tiene separación MPRO/SR |
| 8073 | POST /compras/analisis | Tiene separación MPRO/SR |
| 8211 | GET /compras/facturas-proveedor/{server_id} | Solo MPRO |
| 8265 | GET /compras/detalle-factura/{server_id}/{folio} | Solo MPRO |

### Módulo Compras (/app/backend/modules/compras/):
| Archivo | Estado |
|---------|--------|
| service.py | Tiene separación MPRO/SR, retorna [] si no match |
| repository.py | Queries separadas, tiene ComprasQueryResult |
| routes.py | Endpoints comentados (pendientes de migración) |
| schemas.py | Schemas de request/response |

---

## 4. CAUSA RAÍZ

1. **Retornos silenciosos:** Cuando `system_type` no es MPRO ni SoftRestaurant, los endpoints retornan `[]` vacío sin informar que el sistema no está soportado.

2. **Errores capturados como vacíos:** En líneas como 5987-5989, los errores se capturan y retornan `[]`, ocultando el error real.

3. **Normalización inconsistente:** No hay normalización de `system_type` (MPRO vs MANAGEMENTPRO vs ManagementPro).

---

## 5. CORRECCIONES APLICADAS

### 5.1 Archivo creado: system_type_utils.py
`/app/backend/modules/compras/system_type_utils.py`
- Función `normalize_system_type()` para normalizar variantes (MPRO → MANAGEMENTPRO)
- Funciones helpers: `is_mpro_system()`, `is_softrestaurant_system()`, `is_api_system()`
- Clase `ComprasResponse` para envelope estándar de respuesta
- Funciones de logging: `log_compras_adapter_selected()`, `log_compras_query_result()`, `log_compras_error()`
- Constantes `SystemType` y `ComprasStatus`

### 5.2 Archivo modificado: server.py
Endpoints corregidos para no retornar lista vacía silenciosa:
- `GET /compras/inventarios-fisicos/{server_id}` - Línea ~5997: Ahora lanza HTTPException con detalle
- `POST /compras/analisis` - Línea ~8223: Retorna objeto con status UNSUPPORTED_SYSTEM_TYPE
- `GET /compras/facturas-proveedor/{server_id}` - Usa `is_mpro_system()` y retorna NOT_AVAILABLE_FOR_SYSTEM
- `GET /compras/detalle-factura/{server_id}/{folio}` - Retorna NOT_AVAILABLE_FOR_SYSTEM para no-MPRO

### 5.3 Archivo modificado: service.py
- `obtener_inventarios_fisicos()`: Usa `is_mpro_system()` y `is_softrestaurant_system()`, logs de adapter
- `obtener_pedidos_vigentes()`: Normalización de system_type, logs diagnósticos
- `obtener_detalle_factura()`: Valida solo MPRO disponible
- `obtener_facturas_proveedor()`: Valida solo MPRO disponible

### 5.4 Archivo modificado: __init__.py
- Exporta nuevas utilidades de system_type

---

## 6. PRUEBAS EJECUTADAS

| Caso | Sistema | Endpoint | Resultado esperado | Resultado obtenido | Estado | Evidencia |
|------|---------|----------|--------------------|--------------------|--------|-----------|
| 1 | SoftRestaurant | /compras/inventarios-fisicos | SUCCESS (lista) | 2415 items | ✅ PASS | curl test |
| 2 | MPRO | /compras/facturas-proveedor | SUCCESS (lista) | 1 item | ✅ PASS | curl test |
| 3 | SoftRestaurant | /compras/facturas-proveedor | NOT_AVAILABLE | {"status":"NOT_AVAILABLE..."} | ✅ PASS | curl test |
| 4 | Backend | python -c import | Sin errores | OK | ✅ PASS | import test |
| 5 | Frontend | yarn build | Build exitoso | Done in 23.57s | ✅ PASS | build test |

---

## 7. RIESGOS RESIDUALES

1. Aún hay ~250 comparaciones directas de `system_type` en otros módulos (fuera de Compras)
2. La migración completa a helpers de normalización es recomendada gradualmente
3. El frontend puede mostrar mensajes de error diferentes para endpoints que ahora retornan status estructurado

---

## 8. PENDIENTES RECOMENDADOS

1. **P2**: Migrar comparaciones en `modules/comercial/routes.py` (18)
2. **P2**: Migrar comparaciones en `server.py` endpoints no-compras (~40)
3. **P3**: Migrar tabla `servers` a EDARSAHUB SQL (FASE 3B)
4. **P3**: Ajustar frontend para manejar estados estructurados de error

---

## 9. FASE 3A.1 - CIERRE TÉCNICO (Diciembre 2025)

### Implementado:
1. **Centralización en core:** `/app/backend/core/system_type_utils.py` es ahora la fuente de verdad
2. **Re-exports:** `modules/compras/system_type_utils.py` re-exporta de core para compatibilidad
3. **Nuevas funciones agregadas:**
   - `is_supported_system_type()`
   - `is_unknown_system()`
   - `get_system_type_label()`
   - `build_cache_key_with_system_type()`
   - `log_system_type_normalized()`

### Estadísticas de comparaciones:
- **Total encontradas:** 258
- **Migradas en Compras:** 8 (100% del módulo)
- **Pendientes en otros módulos:** 250 (fuera del alcance de esta fase)

### Documento técnico:
`/app/docs/SYSTEM_TYPE_NORMALIZATION_CIERRE_3A1.md`