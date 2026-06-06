# FASE 3A.2 - Normalización system_type en Módulo COMERCIAL

**Fecha de ejecución:** 2025-12-XX  
**Archivo principal:** `/app/backend/modules/comercial/routes.py`  
**Fuente de verdad:** `/app/backend/core/system_type_utils.py`  
**Estado:** COMPLETADO

---

## Objetivo

Migrar todas las comparaciones directas de `system_type` en el módulo Comercial hacia las funciones centralizadas de normalización, eliminando fragilidad por variantes de strings (`MPRO`, `ManagmentPro`, `ManagementPro`, `SoftRestaurant`, `SR`, etc.).

---

## Funciones Utilizadas

| Función | Propósito |
|---------|-----------|
| `is_softrestaurant_system(system_type)` | Detecta SoftRestaurant y variantes (SR, SOFT, etc.) |
| `is_mpro_system(system_type)` | Detecta ManagementPro/MPRO y variantes |
| `is_api_system(system_type)` | Detecta API local |
| `normalize_system_type(system_type)` | Normaliza a valor canónico |

---

## Bitácora de Reemplazos

| Archivo | Línea aprox. | Comparación anterior | Reemplazo aplicado | Estado | Riesgo residual |
|---------|-------------|---------------------|-------------------|--------|-----------------|
| `routes.py` | ~474 | `server['system_type'] == 'SoftRestaurant'` | `is_softrestaurant_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~561 | `server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~719 | `server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~745 | `server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~822 | `server['system_type'] == 'SoftRestaurant'` | `is_softrestaurant_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~898 | `server['system_type'] in ['MPRO', 'ManagmentPro']` | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~1093 | `server['system_type'] == 'SoftRestaurant'` | `is_softrestaurant_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~1279 | `server['system_type'] == 'SoftRestaurant'` | `is_softrestaurant_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~1401 | `server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~1601 | `server['system_type'] == 'SoftRestaurant'` | `is_softrestaurant_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~1708 | `server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~1884 | `server['system_type'] == 'SoftRestaurant'` | `is_softrestaurant_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~1982 | `server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO' or server['system_type'] == 'MPRO'` (redundante) | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno - Corregida redundancia |
| `routes.py` | ~2146 | `server['system_type'] == 'SoftRestaurant'` | `is_softrestaurant_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~2424 | `server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~2742 | `server['system_type'] == 'SoftRestaurant'` | `is_softrestaurant_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~2896 | `server['system_type'] == 'ManagmentPro' or server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~3290 | `server['system_type'] == 'SoftRestaurant'` | `is_softrestaurant_system(server.get('system_type'))` | COMPLETADO | Ninguno |
| `routes.py` | ~3580 | `server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` | COMPLETADO | Ninguno |

---

## Comparaciones NO migradas (Correctas)

| Archivo | Línea | Contexto | Razón |
|---------|-------|----------|-------|
| `routes.py` | ~2200 | `'SoftRestaurant' as categoria` | Literal de string para campo de categoría en query SQL, no es comparación |
| `routes.py` | Múltiples | `server['system_type']` en asignaciones/retornos | Solo lectura para devolver al frontend, no comparación |

---

## Cambios Adicionales

1. **Acceso seguro:** Todos los accesos cambiados de `server['system_type']` a `server.get('system_type')` para evitar `KeyError`.

2. **Eliminación de redundancia:** Línea ~1982 contenía comparación redundante `or server['system_type'] == 'MPRO' or server['system_type'] == 'MPRO'` - corregida.

3. **Comentarios de trazabilidad:** Cada bloque migrado incluye comentario `# FASE 3A.2: Migrado a helper centralizado`.

---

## Endpoints Afectados

| Endpoint | Función |
|----------|---------|
| `/comercial/dashboard/{server_id}` | Dashboard principal comercial |
| `/comercial/metas/{server_id}` | Metas por producto/vendedor |
| `/comercial/ticket-perfecto/{server_id}` | Análisis de ticket perfecto |
| `/comercial/ventas-tiempo/{server_id}` | Ventas por hora/día |
| `/comercial/mesas/{server_id}` | Rotación de mesas |
| `/comercial/cheques/{server_id}` | Detalle de cheques |
| `/comercial/precios-constantes/{server_id}` | Análisis de precios constantes |
| `/comercial/reporte-pax/{server_id}` | Reporte PAX |
| `/comercial/sucursales/{server_id}` | Listado de sucursales |

---

## Validación Realizada

- [x] `python -m py_compile routes.py` - Sintaxis OK
- [x] `python -m compileall /app/backend` - Compilación completa OK
- [x] Backend arrancando correctamente (supervisor status: RUNNING)
- [x] No quedan comparaciones directas `system_type ==` en el archivo
- [x] No se tocó migración de tabla `servers` (FASE 3B)
- [x] No se modificó frontend

---

## Archivos NO modificados (Fuera de alcance FASE 3A.2)

- `/app/backend/modules/comercial/service.py` - Pendiente FASE 3A.3
- `/app/backend/modules/comercial/queries/mpro.py` - Pendiente FASE 3A.3
- `/app/backend/modules/comercial/queries/__init__.py` - Pendiente FASE 3A.3
- `/app/backend/server.py` - Pendiente FASE 3B

---

## Próximos Pasos

1. **FASE 3A.3:** Migrar dependencias secundarias de Comercial (`service.py`, `queries/`)
2. **FASE 3B:** Migración de tabla `servers` a EDARSAHUB SQL
3. **Actualización de cache keys** para incluir `system_type_normalized`

---

## Responsable

Agente E1 - Emergent Labs  
Fase: 3A.2

---

## Cierre 3A.3 — Dependencias internas y cache keys

**Fecha:** 2025-12-XX  
**Estado:** COMPLETADO

### Archivos migrados en FASE 3A.3

| Archivo | Comparaciones migradas | Cache keys actualizadas |
|---------|------------------------|------------------------|
| `queries/mpro.py` | 3 | 0 |
| `queries/softrestaurant.py` | 1 | 0 |
| `cache_service.py` | 0 | 1 (función `build_cache_key`) |
| `routes.py` | 0 | 3 llamadas actualizadas |

### Cambio principal en cache_service.py

La función `build_cache_key()` ahora incluye `system_type_normalized` como parte de la clave de caché:

**Formato anterior:**
```
comercial:{endpoint}:{server_id}:{sucursal}:{fecha}:...
```

**Formato nuevo:**
```
comercial:{endpoint}:{server_id}:{sucursal}:{system_type_normalized}:{fecha}:...
```

### Impacto

- La caché existente será invalidada automáticamente (las keys antiguas no coinciden)
- SoftRestaurant y MPRO NUNCA compartirán caché
- Variantes de system_type (MPRO, ManagmentPro, etc.) se normalizan automáticamente

### Documento detallado

Ver: `/app/docs/COMERCIAL_DEPENDENCIAS_CACHE_3A3.md`
