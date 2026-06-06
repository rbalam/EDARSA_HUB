# FASE 3A.1 - CIERRE TÉCNICO DEL BLINDAJE system_type

## Fecha: Diciembre 2025
## EDARSA HUB - Arquitecto Senior

---

## 1. RESUMEN EJECUTIVO

Esta fase cierra técnicamente el blindaje de `system_type` implementado en la FASE 3A, centralizando las utilidades de normalización en `/app/backend/core/system_type_utils.py` como fuente de verdad única para todo el sistema.

---

## 2. POR QUÉ SE EJECUTÓ ESTA FASE

1. Las utilidades de normalización estaban duplicadas en `modules/compras/system_type_utils.py`
2. Existían 258 comparaciones directas de `system_type` que podrían causar inconsistencias
3. Se necesitaba una fuente de verdad centralizada para normalización
4. El módulo Compras ya estaba migrado pero otros módulos podrían necesitar las mismas utilidades

---

## 3. ARCHIVOS CREADOS

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/core/system_type_utils.py` | Fuente de verdad centralizada para normalización de system_type |
| `/app/docs/SYSTEM_TYPE_NORMALIZATION_CIERRE_3A1.md` | Este documento |

---

## 4. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/compras/system_type_utils.py` | Re-exporta desde core, mantiene funciones específicas de Compras |
| `/app/backend/server.py` | Importa desde core.system_type_utils |

---

## 5. COMPARACIONES system_type ENCONTRADAS

### Estadísticas:
- **Total encontradas:** 258 ocurrencias
- **Módulo Compras (service.py, routes.py):** 0 (ya migrado en FASE 3A)
- **server.py:** 56
- **modules/comercial/routes.py:** 18
- **modules/configuracion:** 4
- **modules/automatizacion:** 4
- **modules/finanzas:** 2
- **scripts/:** 2
- **tests/:** Varias (assertions de test, aceptable)

### Tabla de comparaciones por archivo:

| Archivo | Líneas aproximadas | Comparación actual | Riesgo | Estado |
|---------|-------------------|-------------------|--------|--------|
| modules/compras/service.py | - | Usa is_mpro_system() | BAJO | ✅ MIGRADO |
| modules/compras/routes.py | - | Sin comparaciones | BAJO | ✅ OK |
| server.py (endpoints compras) | 5997, 8223, 8265, 8285 | Usa is_mpro_system() | MEDIO | ✅ MIGRADO |
| server.py (otros endpoints) | 1525-2409 | == "MPRO" / == "SoftRestaurant" | MEDIO | ⏸️ PENDIENTE |
| modules/comercial/routes.py | 465-3571 | == "SoftRestaurant" / == "MPRO" | MEDIO | ⏸️ PENDIENTE |
| modules/comercial/queries/mpro.py | 138, 271, 528 | != "MPRO" | BAJO | ⏸️ PENDIENTE |
| modules/comercial/queries/softrestaurant.py | 133 | != "SoftRestaurant" | BAJO | ⏸️ PENDIENTE |
| modules/configuracion/ | 148, 150, 204 | == "SoftRestaurant" / == "MPRO" | BAJO | ⏸️ PENDIENTE |
| modules/automatizacion/ | 516-527 | == "SoftRestaurant" / == "MPRO" | BAJO | ⏸️ PENDIENTE |
| modules/finanzas/ | 226, 412 | != "SoftRestaurant" | BAJO | ⏸️ PENDIENTE |
| tests/* | Varias | Assertions | MUY BAJO | ⏸️ ACEPTABLE |

---

## 6. COMPARACIONES MIGRADAS

| Archivo | Función/Endpoint | Antes | Después |
|---------|-----------------|-------|---------|
| server.py | /compras/inventarios-fisicos | `server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` |
| server.py | /compras/analisis | `server['system_type'] == 'MPRO'` | `is_mpro_system(server.get('system_type'))` |
| server.py | /compras/facturas-proveedor | `server['system_type'] == 'MPRO'` | `is_mpro_system(system_type)` |
| server.py | /compras/detalle-factura | (retorno [] silencioso) | NOT_AVAILABLE_FOR_SYSTEM |
| modules/compras/service.py | obtener_inventarios_fisicos | `server['system_type'] == 'MPRO'` | `is_mpro_system(system_type)` |
| modules/compras/service.py | obtener_pedidos_vigentes | `server['system_type'] == 'MPRO'` | `is_mpro_system(system_type)` |
| modules/compras/service.py | obtener_detalle_factura | `server['system_type'] == 'MPRO'` | `is_mpro_system(system_type)` |
| modules/compras/service.py | obtener_facturas_proveedor | `server['system_type'] == 'MPRO'` | `is_mpro_system(system_type)` |

---

## 7. COMPARACIONES NO MIGRADAS Y JUSTIFICACIÓN

| Módulo | Razón de no migrar |
|--------|-------------------|
| server.py (endpoints no-compras) | Fuera del alcance de FASE 3A/3A.1 |
| modules/comercial/routes.py | Módulo Comercial no es objetivo de esta fase |
| modules/comercial/queries/*.py | Guardias de seguridad de queries, bajo riesgo |
| modules/configuracion/ | Fuera del alcance |
| modules/automatizacion/ | Fuera del alcance |
| modules/finanzas/ | Fuera del alcance |
| tests/* | Son assertions de test, no lógica de producción |

**Nota:** Se recomienda migrar gradualmente estos módulos en fases posteriores (P2/P3).

---

## 8. REGLAS DE NORMALIZACIÓN IMPLEMENTADAS

```
Entrada                → Salida
--------------------- → --------------------
"MPRO"                → "MANAGEMENTPRO"
"MANAGEMENT_PRO"      → "MANAGEMENTPRO"
"MANAGEMENTPRO"       → "MANAGEMENTPRO"
"MANAGEMENT PRO"      → "MANAGEMENTPRO"
"MANAGMENTPRO"        → "MANAGEMENTPRO"  (typo)
"MANAGMENT_PRO"       → "MANAGEMENTPRO"  (typo)

"SOFTRESTAURANT"      → "SOFTRESTAURANT"
"SR"                  → "SOFTRESTAURANT"
"SOFT"                → "SOFTRESTAURANT"
"SOFT_RESTAURANT"     → "SOFTRESTAURANT"
"SOFT RESTAURANT"     → "SOFTRESTAURANT"

"API"                 → "API"
"LOCAL_API"           → "API"
"API_LOCAL"           → "API"

None / "" / unknown   → "UNKNOWN"
```

**IMPORTANTE:** NUNCA se asume SoftRestaurant por default. Si el valor es desconocido, se retorna UNKNOWN.

---

## 9. CAMBIOS EN CACHE_KEY

Se agregó la función `build_cache_key_with_system_type()` en `core/system_type_utils.py`:

```python
cache_key = build_cache_key_with_system_type(
    prefix="compras",
    endpoint="inventarios",
    server_id="server-123",
    system_type="MPRO",  # Se normaliza automáticamente
    sucursal_id="0021",
    fecha_inicio="2025-01-01"
)
# Resultado: "compras:inventarios:server-123:MANAGEMENTPRO:fecha_inicio=2025-01-01:sucursal_id=0021"
```

**Nota:** El módulo Compras actualmente NO usa caché extensivo. La función está disponible para uso futuro.

---

## 10. CAMBIOS FRONTEND

No se requirieron cambios en frontend en esta fase. Los endpoints de Compras que retornan estados estructurados (`UNSUPPORTED_SYSTEM_TYPE`, `NOT_AVAILABLE_FOR_SYSTEM`) ya fueron implementados en FASE 3A.

---

## 11. VALIDACIÓN DE NO REGRESIÓN

### Pruebas ejecutadas:

| Test | Resultado |
|------|-----------|
| python -c "import server" | ✅ PASS |
| core.system_type_utils import | ✅ PASS |
| modules.compras import | ✅ PASS |
| SoftRestaurant /compras/inventarios-fisicos | ✅ PASS (2415 items) |
| MPRO /compras/facturas-proveedor | ✅ PASS (1 item) |
| yarn build | ✅ PASS |
| Login | ✅ PASS |
| /api/servers | ✅ PASS (8 servers) |
| /api/users | ✅ PASS |
| /api/roles | ✅ PASS |

---

## 12. RIESGOS RESIDUALES

1. **MEDIO:** 200+ comparaciones directas de `system_type` en módulos fuera de Compras
2. **BAJO:** El módulo Comercial usa comparaciones directas pero funciona correctamente
3. **BAJO:** Tests tienen assertions directas (aceptable para tests)

---

## 13. RECOMENDACIÓN PARA FASES POSTERIORES

### P2 - Migración gradual de módulos:
1. `modules/comercial/routes.py` - 18 comparaciones
2. `server.py` (endpoints no-compras) - ~40 comparaciones
3. `modules/configuracion/` - 4 comparaciones

### P3 - FASE 3B:
1. Migrar tabla `servers` a EDARSAHUB SQL
2. Actualizar resolución de system_type desde SQL en lugar de MongoDB

---

## 14. CRITERIO DE ACEPTACIÓN - CUMPLIMIENTO

| Criterio | Estado |
|----------|--------|
| Utilidades centralizadas en core | ✅ |
| MPRO/MANAGEMENTPRO se normaliza consistentemente | ✅ |
| SoftRestaurant/SR/SOFT se normaliza consistentemente | ✅ |
| Valores desconocidos NO caen en SoftRestaurant | ✅ |
| SoftRestaurant sigue funcionando | ✅ |
| MPRO sigue funcionando | ✅ |
| Backend compila | ✅ |
| Frontend build pasa | ✅ |
| No se migró servers | ✅ |
| No se hizo refactor masivo | ✅ |

---

## ARCHIVOS DE REFERENCIA

- `/app/backend/core/system_type_utils.py` - Fuente de verdad
- `/app/backend/modules/compras/system_type_utils.py` - Re-exports para Compras
- `/app/docs/COMPRAS_BLINDAJE_SYSTEM_TYPE_MPRO.md` - Documentación FASE 3A
