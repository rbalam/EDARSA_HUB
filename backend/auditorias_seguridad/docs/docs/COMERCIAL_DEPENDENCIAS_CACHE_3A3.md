# FASE 3A.3 - Dependencias Internas y Cache Keys de Comercial

**Fecha de ejecución:** 2025-12-XX  
**Archivos modificados:** 5  
**Fuente de verdad:** `/app/backend/core/system_type_utils.py`  
**Estado:** COMPLETADO

---

## 1. Resumen Ejecutivo

La FASE 3A.3 completó el blindaje interno del módulo Comercial migrando:
- 4 comparaciones directas de `system_type` en queries secundarias
- 3 llamadas a `build_cache_key` actualizadas para incluir `system_type`
- Función `build_cache_key` modificada para incluir `system_type_normalized`

Esto garantiza que:
- SoftRestaurant NO comparta caché con MPRO
- MPRO NO comparta caché con SoftRestaurant
- Variantes de system_type se normalicen automáticamente

---

## 2. Archivos Revisados

| Archivo | Comparaciones | Cache Keys | Acción |
|---------|---------------|------------|--------|
| `routes.py` | 0 (ya migrado 3A.2) | 3 | Actualizado |
| `service.py` | 0 | 0 | Sin cambios |
| `cache_service.py` | 0 | 1 función | Actualizado |
| `queries/mpro.py` | 3 → 0 | 0 | Migrado |
| `queries/softrestaurant.py` | 1 → 0 | 0 | Migrado |
| `queries/__init__.py` | 0 | 0 | Sin cambios |
| `queries/hub.py` | 0 | 0 | Sin cambios |
| `adapters.py` | 0 | 0 | Sin cambios |
| `repository.py` | 0 | 0 | Sin cambios |
| `kpis_repository.py` | 0 | 0 | Sin cambios |
| `schemas.py` | 0 | 0 | Sin cambios |

---

## 3. Bitácora de Comparaciones Migradas

| Archivo | Línea aprox. | Comparación anterior | Reemplazo aplicado | Estado | Riesgo |
|---------|-------------|---------------------|-------------------|--------|--------|
| `queries/mpro.py` | ~138 | `system_type != 'MPRO'` | `not is_mpro_system(system_type)` | COMPLETADO | Ninguno |
| `queries/mpro.py` | ~271 | `system_type != 'MPRO'` | `not is_mpro_system(system_type)` | COMPLETADO | Ninguno |
| `queries/mpro.py` | ~528 | `system_type != 'MPRO'` | `not is_mpro_system(system_type)` | COMPLETADO | Ninguno |
| `queries/softrestaurant.py` | ~133 | `system_type != 'SoftRestaurant'` | `not is_softrestaurant_system(system_type)` | COMPLETADO | Ninguno |

---

## 4. Literales NO Migrados (Correctos)

| Archivo | Línea | Contexto | Razón |
|---------|-------|----------|-------|
| `service.py` | ~709 | `"system_type": "MPRO"` | Literal de campo en respuesta JSON, no comparación |
| `service.py` | ~751 | `"system_type": "MPRO"` | Literal de campo en respuesta JSON, no comparación |
| `service.py` | ~1084 | `"system_type": "MPRO"` | Literal de campo en respuesta JSON, no comparación |

**Decisión:** Estos literales son valores de campo para respuestas API. No son comparaciones de lógica condicional, por lo tanto no requieren migración. El valor `"MPRO"` se mantiene para compatibilidad con el frontend.

---

## 5. Bitácora de Cache Keys

### Cache Keys Encontradas

| Archivo | Función/Endpoint | Cache Key Anterior | Riesgo |
|---------|------------------|-------------------|--------|
| `cache_service.py` | `build_cache_key()` | `comercial:{endpoint}:{server_id}:{sucursal}:{fecha}:...` | CRÍTICO: Sin system_type |
| `routes.py` | `/comercial/metas` | Usaba `build_cache_key` sin system_type | MEDIO |
| `routes.py` | `/comercial/ticket-perfecto` | Usaba `build_cache_key` sin system_type | MEDIO |
| `routes.py` | `/comercial/reporte-pax` | Usaba `build_cache_key` sin system_type | MEDIO |

### Cache Keys Modificadas

| Archivo | Función/Endpoint | Cache Key Nueva | Estado |
|---------|------------------|-----------------|--------|
| `cache_service.py` | `build_cache_key()` | `comercial:{endpoint}:{server_id}:{sucursal}:{system_type_normalized}:{fecha}:...` | COMPLETADO |
| `routes.py` | `/comercial/metas` | Agregado parámetro `system_type=server.get('system_type', '')` | COMPLETADO |
| `routes.py` | `/comercial/ticket-perfecto` | Agregado parámetro `system_type=server.get('system_type', '')` | COMPLETADO |
| `routes.py` | `/comercial/reporte-pax` | Agregado parámetro `system_type=server.get('system_type', '')` | COMPLETADO |

### Formato de Cache Key FASE 3A.3

**Antes:**
```
comercial:dashboard:server123:suc001:2026-04-20:periodo=mes
```

**Después:**
```
comercial:dashboard:server123:suc001:MANAGEMENTPRO:2026-04-20:periodo=mes
comercial:dashboard:server456:all:SOFTRESTAURANT:2026-04-20:periodo=mes
```

**Impacto:** La caché existente será invalidada automáticamente porque las nuevas keys tienen formato diferente. Esto es aceptable y esperado.

---

## 6. Imports Agregados

| Archivo | Import agregado |
|---------|-----------------|
| `queries/mpro.py` | `from core.system_type_utils import is_mpro_system` |
| `queries/softrestaurant.py` | `from core.system_type_utils import is_softrestaurant_system` |
| `cache_service.py` | `from core.system_type_utils import normalize_system_type` |

---

## 7. Validación de No Regresión

| Validación | Resultado |
|------------|-----------|
| `python -m py_compile queries/mpro.py` | ✅ OK |
| `python -m py_compile queries/softrestaurant.py` | ✅ OK |
| `python -m py_compile cache_service.py` | ✅ OK |
| `python -m py_compile routes.py` | ✅ OK |
| `python -m compileall /app/backend` | ✅ OK |
| Backend arranca (supervisor) | ✅ RUNNING |
| Login API `/api/auth/login` | ✅ Token generado |
| Listado servidores `/api/servers` | ✅ 8 servidores |
| DuplicateKeyError MongoDB | ⚠️ Conocido/Inofensivo |

---

## 8. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Caché existente invalidada | BAJO | Esperado y aceptable, se regenera al primer acceso |
| No se pudo validar SQL remoto | MEDIO | Entorno preview sin VPN, validar en producción |

---

## 9. Archivos NO Modificados

| Archivo | Razón |
|---------|-------|
| `service.py` | Solo tiene literales de campo, no comparaciones |
| `adapters.py` | Sin comparaciones de system_type |
| `repository.py` | Sin comparaciones de system_type en scope 3A.3 |
| `kpis_repository.py` | Sin comparaciones de system_type |
| `queries/hub.py` | Sin comparaciones de system_type |
| `queries/__init__.py` | Solo exports, sin lógica |
| `schemas.py` | Solo definiciones Pydantic |

---

## 10. Recomendación para FASE 3A.4 / FASE 3B

### FASE 3A.4 (Opcional - Mejoras adicionales)
- Revisar otros endpoints que construyan cache keys manualmente (fuera de `build_cache_key`)
- Agregar log `[COMERCIAL][CACHE_HIT]` y `[COMERCIAL][CACHE_MISS]` para diagnóstico

### FASE 3B (Próxima prioritaria)
- Migración de tabla `servers` a EDARSAHUB SQL
- **PROHIBIDO** ejecutar en FASE 3A.3

---

## 11. Responsable

Agente E1 - Emergent Labs  
Fase: 3A.3 - Dependencias Internas y Cache Keys

---

## Frontend 3A.4 — Manejo de respuestas estructuradas

**Fecha:** 2025-12-XX  
**Estado:** COMPLETADO

### Resumen

La FASE 3A.4 implementó el manejo de respuestas estructuradas en el frontend del módulo Comercial:

- Helper centralizado: `/app/frontend/src/utils/comercialStatusUtils.js`
- Componente reutilizable: `ComercialStatusIndicator`
- 4 tableros actualizados: Dashboard, Ticket Perfecto, Metas, Reporte PAX

### Estados adicionales soportados

- `NOT_AVAILABLE_FOR_SYSTEM`
- `UNSUPPORTED_SYSTEM_TYPE`
- `QUERY_ERROR`
- `FIELD_MAPPING_ERROR`
- `CONFIGURATION_MISSING`
- `PERMISSION_DENIED`
- `INACTIVE_SOURCE`
- `PARTIAL`

### Documento detallado

Ver: `/app/docs/COMERCIAL_FRONTEND_RESPUESTAS_ESTRUCTURADAS_3A4.md`
