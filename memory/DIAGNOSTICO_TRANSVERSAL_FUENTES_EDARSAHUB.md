# DIAGNÓSTICO TRANSVERSAL: FUENTES DE DATOS, MONGODB, CONEXIONES VIVAS Y LÓGICA DE UNIDADES DE NEGOCIO

**Fecha:** 2025-12-13
**Estado:** DIAGNÓSTICO PASIVO COMPLETADO
**Régimen:** SOLO LECTURA - NO SE MODIFICÓ NINGÚN ARCHIVO

---

## 1. RESUMEN EJECUTIVO

### Estadísticas Generales
| Métrica | Cantidad |
|---------|----------|
| Referencias a `db.servers` (MongoDB) | 23 |
| Referencias a `server_registry` | 70 |
| Referencias a `execute_sql_query` | 137 |
| Módulos analizados | 8 |
| Endpoints con conexión live | 40+ |

### Estado de Migración EDARSAHUB

| Módulo | Estado | MongoDB | server_registry | EDARSAHUB SQL |
|--------|--------|---------|-----------------|---------------|
| **Finanzas** | ✅ MIGRADO | ❌ Eliminado | ✅ Usa | ✅ Fuente principal |
| **Comercial (Tablero)** | ✅ MIGRADO (parcial) | ⚠️ Residual | ✅ Usa | ✅ Para unidades |
| **Comercial (V1 tabs)** | ⚠️ PARCIAL | ⚠️ Residual | ⚠️ Parcial | ⚠️ Mixto |
| **Compras** | ⚠️ MIXTO | ⚠️ Usa db.servers | ❌ No usa | ⚠️ Live principal |
| **Configuración** | ⚠️ MIXTO | ⚠️ Usa db.servers | ❌ No usa | ❌ No usa |
| **Catálogos** | ⚠️ MIXTO | ⚠️ Usa db.servers | ❌ No usa | ⚠️ Parcial |
| **Universal Query** | ❌ NO MIGRADO | ⚠️ Usa db.servers | ❌ No usa | ❌ No usa |
| **Fase2 Operativo** | ❌ NO APLICA | ✅ MongoDB OK | N/A | N/A |
| **RH** | ⚠️ MIXTO | ⚠️ Usa db.servers | ⚠️ Parcial | ⚠️ Parcial |

---

## 2. HALLAZGOS CRÍTICOS P0

| # | Módulo | Archivo | Problema | Impacto | Acción |
|---|--------|---------|----------|---------|--------|
| 1 | Comercial | `repository.py:228` | Usa `db.servers.find_one()` para obtener servidor | Depende de MongoDB para conexiones | REQUIERE_SERVER_REGISTRY |
| 2 | Comercial | `repository.py:247` | Usa `db.servers.find()` para listar servidores | Depende de MongoDB | REQUIERE_SERVER_REGISTRY |
| 3 | Comercial | `historical_kpis_repository.py:62` | Usa `db.servers.find_one()` | Depende de MongoDB | REQUIERE_SERVER_REGISTRY |
| 4 | Catálogos | `repository.py:31` | Usa `db.servers.find_one()` | Depende de MongoDB | REQUIERE_SERVER_REGISTRY |
| 5 | Universal Query | `routes.py:164,243` | Usa `db.servers.find_one()` | Depende de MongoDB | REQUIERE_SERVER_REGISTRY |

---

## 3. HALLAZGOS P1

| # | Módulo | Archivo | Problema | Impacto | Acción |
|---|--------|---------|----------|---------|--------|
| 1 | Configuración | `config_asignaciones_repository.py:249` | Usa `db.servers.find_one()` | Config depende de MongoDB | REQUIERE_SERVER_REGISTRY |
| 2 | Configuración | `almacenes_sync_service.py:138` | Usa `db.servers.find_one()` | Sync depende de MongoDB | REQUIERE_SERVER_REGISTRY |
| 3 | RH | `importador/repository.py:68` | Usa `db.servers.find_one()` | Importador depende de MongoDB | REQUIERE_SERVER_REGISTRY |
| 4 | Comercial | `routes.py` (40+ lugares) | Usa conexión live a servidores | Rendimiento/disponibilidad | REQUIERE_SNAPSHOT |
| 5 | Server.py | Líneas 1607-1802 | CRUD de servidores usa MongoDB | Configuración en MongoDB | EVALUAR_MIGRACION |

---

## 4. MATRIZ POR MENÚ / TAB

### COMERCIAL

| Tab | Endpoint | Fuente Actual | Usa EDARSAHUB | Usa MongoDB | Usa Live | Riesgo | Dictamen |
|-----|----------|---------------|---------------|-------------|----------|--------|----------|
| Tablero Ejecutivo | `/api/comercial/tablero-ejecutivo` | EDARSAHUB + Live | ✅ | ❌ | ✅ MPRO | P1 | OK_LIVE_OPERATIVO |
| Dashboard V2 | `/api/v2/comercial/dashboard` | EDARSAHUB + Live | ✅ | ❌ | ✅ | P1 | OK_LIVE_OPERATIVO |
| Dashboard V1 | `/api/comercial/dashboard/{id}` | Live principal | ⚠️ | ⚠️ repo | ✅ | P1 | REQUIERE_MIGRACION_SQL |
| Mesas | `/api/comercial/mesas/{id}` | Live | ❌ | ⚠️ | ✅ | P2 | OK_LIVE_OPERATIVO |
| Detalle Venta | `/api/comercial/detalle-venta` | Live | ❌ | ⚠️ | ✅ | P2 | OK_LIVE_OPERATIVO |
| Precios | `/api/comercial/precios/{id}` | Live | ❌ | ⚠️ | ✅ | P2 | OK_LIVE_OPERATIVO |

### FINANZAS

| Tab | Endpoint | Fuente Actual | Usa EDARSAHUB | Usa MongoDB | Usa Live | Riesgo | Dictamen |
|-----|----------|---------------|---------------|-------------|----------|--------|----------|
| Tesorería | `/api/tesoreria/sucursales` | EDARSAHUB | ✅ | ❌ | ❌ | - | OK_EDARSAHUB |
| Cortes Z | `/api/finanzas/cortes-z` | EDARSAHUB + Live | ✅ | ❌ | ⚠️ | P2 | OK_EDARSAHUB |
| Propinas TPV | `/api/finanzas/propinas-tpv` | EDARSAHUB | ✅ | ❌ | ❌ | - | OK_EDARSAHUB |
| Cuentas Bancarias | `/api/finanzas/cuentas-bancarias` | EDARSAHUB | ✅ | ❌ | ❌ | - | OK_EDARSAHUB |

### COMPRAS

| Tab | Endpoint | Fuente Actual | Usa EDARSAHUB | Usa MongoDB | Usa Live | Riesgo | Dictamen |
|-----|----------|---------------|---------------|-------------|----------|--------|----------|
| Dashboard | `/api/compras/dashboard/{id}` | Live | ❌ | ⚠️ | ✅ | P1 | REQUIERE_SNAPSHOT |
| Inventarios | `/api/compras/inventarios-fisicos/{id}` | Live | ❌ | ⚠️ | ✅ | P1 | REQUIERE_SNAPSHOT |
| Pedidos | `/api/compras/pedidos-vigentes/{id}` | Live | ❌ | ⚠️ | ✅ | P1 | OK_LIVE_OPERATIVO |
| Auditoría Op. | `/api/compras/auditoria-operativa/{id}` | Live | ⚠️ | ⚠️ | ✅ | P2 | REQUIERE_MIGRACION_SQL |

### CONFIGURACIÓN

| Tab | Endpoint | Fuente Actual | Usa EDARSAHUB | Usa MongoDB | Usa Live | Riesgo | Dictamen |
|-----|----------|---------------|---------------|-------------|----------|--------|----------|
| Servidores | `/api/servers` | MongoDB | ❌ | ✅ | ❌ | P1 | EVALUAR_MIGRACION |
| Almacenes | `/api/servers/{id}/almacenes` | Live | ❌ | ✅ | ✅ | P2 | OK_LIVE_OPERATIVO |

---

## 5. MATRIZ DE ENDPOINTS QUE USAN CONEXIÓN LIVE

| Endpoint | Archivo | Sistema | Motivo Live | ¿Debe ser Live? | Alternativa |
|----------|---------|---------|-------------|-----------------|-------------|
| `/api/comercial/dashboard/{id}` | routes.py | SR/MPRO | KPIs tiempo real | ⚠️ Parcial | Snapshot EDARSAHUB |
| `/api/comercial/mesas/{id}` | routes.py | SR | Estado actual mesas | ✅ Sí | N/A |
| `/api/comercial/detalle-venta/{id}` | routes.py | SR/MPRO | Tickets específicos | ✅ Sí | N/A |
| `/api/compras/inventarios-fisicos/{id}` | routes.py | SR/MPRO | Stock actual | ⚠️ Parcial | Snapshot diario |
| `/api/compras/pedidos-vigentes/{id}` | routes.py | SR/MPRO | Pedidos abiertos | ✅ Sí | N/A |
| `/api/comercial/tablero-ejecutivo` | routes.py | MPRO | Ventas día | ⚠️ Parcial | Snapshot horario |

---

## 6. MATRIZ DE ARCHIVOS QUE USAN MONGODB

| Archivo | Función | Colección | Motivo | Alternativa EDARSAHUB | Riesgo |
|---------|---------|-----------|--------|----------------------|--------|
| `comercial/repository.py:228` | `get_server_by_id()` | servers | Conexión servidor | `server_registry.get_server_by_id()` | P0 |
| `comercial/repository.py:247` | `get_servers()` | servers | Listar servidores | `server_registry.list_servers()` | P0 |
| `comercial/historical_kpis_repository.py:62` | lookup | servers | Config EDARSAHUB | `EDARSAHUB_CONFIG` | P0 |
| `catalogos/repository.py:31` | lookup | servers | Config conexión | `server_registry` | P0 |
| `universal_query/routes.py:164,243` | lookup | servers | Ejecutar query | `server_registry` | P0 |
| `configuracion/config_asignaciones_repository.py:249` | lookup | servers | Asignaciones | `server_registry` | P1 |
| `configuracion/almacenes_sync_service.py:138` | lookup | servers | Sync almacenes | `server_registry` | P1 |
| `rh/importador/repository.py:68` | lookup | servers | Importar datos | `server_registry` | P1 |
| `server.py:1607-1802` | CRUD | servers | Admin servidores | Evaluar migración | P1 |

---

## 7. MATRIZ DE LÓGICA DE UNIDADES NO CANÓNICA

| Archivo | Línea | Patrón | Problema | Corrección |
|---------|-------|--------|----------|------------|
| `comercial/service.py` | 214-219 | Fallback hardcode | `0021: 130QRO` hardcodeado | Eliminar si `resolve_unidad` funciona |
| `comercial/queries/mpro.py` | 300-301 | `.lower()` matching | Usa lowercase para empatar | Usar códigos canónicos |
| `comercial/routes.py` | 1995-1996 | `.lower()` matching | Compara por nombre.lower() | Usar `unidad_negocio_codigo` |
| `comercial/routes.py` | 2303-2304 | `.lower()` matching | Compara por nombre.lower() | Usar `unidad_negocio_codigo` |
| `comercial/routes.py` | 4609-4610 | `.lower()` matching | Busca unidad por nombre | Usar `unidad_negocio_codigo` |

---

## 8. MÓDULOS OK (CUMPLEN EDARSAHUB)

| Módulo | Componente | Evidencia |
|--------|------------|-----------|
| Finanzas | Tesorería | `from core.server_registry import EDARSAHUB_CONFIG` |
| Finanzas | Propinas TPV | `FASE T2.3: Reemplaza db.servers` |
| Finanzas | Cortes Z | `from core.server_registry import` |
| Finanzas | KPIs Históricos | `[T2.1] Conexión EDARSAHUB desde server_registry.py` |
| Comercial | Tablero Ejecutivo (unidades) | `resolve_unidad_by_server_sucursal()` |
| Comercial | Modal Filtros | EDARSAHUB-first para catálogos |

---

## 9. FASE 2 OPERATIVO (EXCEPCIÓN DOCUMENTADA)

El módulo `/app/backend/modules/fase2_operativo/` usa MongoDB **intencionalmente** para:
- SLA
- Tareas operativas
- Workflows
- Auditoría
- Justificaciones
- Responsabilidades
- Cargos

**Dictamen:** NO_APLICA - Es un módulo independiente que no usa `db.servers` ni datos de servidores operativos.

---

## 10. RECOMENDACIÓN DE FASES DE CORRECCIÓN

### FASE P0 - INMEDIATA
1. ✅ **COMPLETADO:** Fix EDARSA/Unidad Desconocida en Tablero Ejecutivo
2. **PENDIENTE:** Migrar `comercial/repository.py` a `server_registry`
3. **PENDIENTE:** Migrar `catalogos/repository.py` a `server_registry`
4. **PENDIENTE:** Migrar `universal_query/routes.py` a `server_registry`

### FASE P1 - CORTO PLAZO
1. Migrar `configuracion/` a `server_registry`
2. Migrar `rh/importador/` a `server_registry`
3. Implementar deduplicación en Tablero Ejecutivo (LA ESTELAR)
4. Evaluar snapshots para Comercial V1 tabs
5. Evaluar snapshots para Compras dashboard

### FASE P2 - MEDIANO PLAZO
1. Eliminar `.lower()` matching en favor de códigos canónicos
2. Configurar visibilidad de sucursales multi-unidad
3. Migrar Comercial V1 tabs legacy a V2
4. Evaluar migración de `server.py` CRUD a EDARSAHUB

### FASE P3 - LARGO PLAZO
1. Deprecación formal de `db.servers`
2. Scheduler de sincronización de catálogos
3. UI de administración de visibilidad

---

## 11. QUÉ NO TOCAR TODAVÍA

| Componente | Razón |
|------------|-------|
| `server.py` CRUD de servidores | Funciona, requiere análisis de impacto |
| Fase2 Operativo (MongoDB) | Es independiente, no usa servidores |
| Comercial Mesas/Detalle | Son operativos que requieren live |
| Auth/RBAC | Blindado, funciona correctamente |
| Scripts de migración | Solo para uso controlado |

---

## 12. ARCHIVOS REVISADOS

```
/app/backend/modules/comercial/*.py (13 archivos)
/app/backend/modules/finanzas/*.py (40+ archivos)
/app/backend/modules/configuracion/**/*.py
/app/backend/modules/catalogos/*.py
/app/backend/modules/universal_query/*.py
/app/backend/modules/rh/**/*.py
/app/backend/modules/fase2_operativo/**/*.py
/app/backend/server.py
/app/backend/core/server_registry.py
/app/frontend/src/pages/Compras.js
```

---

## 13. CONFIRMACIÓN

✅ **NO SE MODIFICÓ NINGÚN ARCHIVO**
✅ **DIAGNÓSTICO PASIVO COMPLETADO**
✅ **TODAS LAS REFERENCIAS DOCUMENTADAS**

---

## 14. PRÓXIMOS PASOS RECOMENDADOS

1. **Autorizar P1 LA ESTELAR duplicada** (documento separado)
2. **Autorizar migración de `comercial/repository.py`** a `server_registry`
3. **Definir prioridad de migración** para módulos restantes
4. **Continuar con P1-C** (Sincronización programada de catálogos)
