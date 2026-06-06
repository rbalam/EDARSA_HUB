# FASE A-P0: COMERCIAL ROUTES LIVE → SQL

**Fecha:** 2026-05-26  
**Estado:** ✅ COMPLETADO  
**Alcance:** Endpoints LIVE legacy en `/app/backend/modules/comercial/routes.py`

---

## 1. RESUMEN EJECUTIVO

Se implementó un **GUARD RAIL** para bloquear endpoints que requieren conexión LIVE a servidores remotos (SoftRestaurant/MPRO) desde la UI.

**Resultado:**
- 7 endpoints LIVE legacy bloqueados con error controlado `LEGACY_LIVE_DISABLED`
- 2 endpoints ya migrados a SQL-First confirmados funcionales
- 0 regresiones en módulos V2

---

## 2. GREP - EVIDENCIA ANTES

### Endpoints con {server_id}
```
1816:@router.get("/comercial/sucursales/{server_id}")
1882:@router.get("/comercial/metas/{server_id}")
2155:@router.get("/comercial/ticket-perfecto/{server_id}")
2378:@router.get("/comercial/ventas-tiempo/{server_id}")
2602:@router.get("/comercial/mesas/{server_id}")
2875:@router.get("/comercial/detalle-movimientos/{server_id}")
3119:@router.get("/comercial/precios-constantes/{server_id}")
3703:@router.get("/comercial/reporte-pax/{server_id}")
4143:@router.get("/comercial/dashboard/{server_id}")
```

### Conexiones LIVE
```
2416:conn = pymssql.connect(...)  # En mesas
2524:conn_hoy = pymssql.connect(...)  # En mesas
```

### Helpers de Conexión
```
127: get_connection_for_role
```

---

## 3. CLASIFICACIÓN POR ENDPOINT

| # | Endpoint | Clasificación | Estado Post-Fix |
|---|----------|---------------|-----------------|
| 1 | `/comercial/dashboard/{server_id}` | SQL_FIRST_MIGRADO | ✅ Usa EDARSAHUB vía `get_dashboard_kpis_from_edarsahub` |
| 2 | `/comercial/ventas-tiempo/{server_id}` | SQL_FIRST_MIGRADO | ✅ Usa `Sync_Ventas_PorHora` desde EDARSAHUB |
| 3 | `/comercial/sucursales/{server_id}` | LEGACY_BLOQUEADO | ✅ GUARD RAIL activo - SR: sin LIVE, MPRO: bloqueado |
| 4 | `/comercial/metas/{server_id}` | LEGACY_BLOQUEADO | ✅ GUARD RAIL activo - Requiere `Sync_Metas_Comerciales` |
| 5 | `/comercial/ticket-perfecto/{server_id}` | LEGACY_BLOQUEADO | ✅ GUARD RAIL activo - Requiere `Sync_Ticket_Perfecto` |
| 6 | `/comercial/mesas/{server_id}` | LEGACY_BLOQUEADO | ✅ GUARD RAIL activo - Requiere `Sync_Mesas` |
| 7 | `/comercial/detalle-movimientos/{server_id}` | LEGACY_BLOQUEADO | ✅ GUARD RAIL activo - Requiere `Sync_Movimientos_Detalle` |
| 8 | `/comercial/precios-constantes/{server_id}` | LEGACY_BLOQUEADO | ✅ GUARD RAIL activo - Requiere `Sync_Precios_Historicos` |
| 9 | `/comercial/reporte-pax/{server_id}` | LEGACY_BLOQUEADO | ✅ GUARD RAIL activo - Requiere `Sync_PAX_Detalle` |

---

## 4. IMPLEMENTACIÓN DEL GUARD RAIL

### Configuración Global (líneas 133-218)
```python
# Flag para habilitar/deshabilitar el guard rail LIVE
ENABLE_LIVE_GUARD_RAIL = True

# Endpoints LIVE Legacy con sus tablas requeridas
ENDPOINTS_LIVE_LEGACY = {
    '/comercial/sucursales': {'tabla_requerida': 'Sistema_Sucursales', 'job_requerido': 'sync_sucursales'},
    '/comercial/metas': {'tabla_requerida': 'Sync_Metas_Comerciales', 'job_requerido': 'sync_metas'},
    '/comercial/ticket-perfecto': {'tabla_requerida': 'Sync_Ticket_Perfecto', 'job_requerido': 'sync_ticket_perfecto'},
    '/comercial/mesas': {'tabla_requerida': 'Sync_Mesas', 'job_requerido': 'sync_mesas'},
    '/comercial/detalle-movimientos': {'tabla_requerida': 'Sync_Movimientos_Detalle', 'job_requerido': 'sync_movimientos'},
    '/comercial/precios-constantes': {'tabla_requerida': 'Sync_Precios_Historicos', 'job_requerido': 'sync_precios_historicos'},
    '/comercial/reporte-pax': {'tabla_requerida': 'Sync_PAX_Detalle', 'job_requerido': 'sync_pax'},
}

def check_live_guard_rail(endpoint_base: str, server_id: str) -> dict | None:
    """Verifica si un endpoint LIVE legacy debe ser bloqueado."""
    if not ENABLE_LIVE_GUARD_RAIL:
        return None
    # ... verifica y retorna error controlado si está bloqueado
```

### Respuesta de Endpoint Bloqueado
```json
{
  "source_status": "LEGACY_LIVE_DISABLED",
  "source_message": "Este endpoint requiere conexión LIVE a servidor remoto. EDARSAHUB SQL es el cerebro del sistema. Para habilitar, crear tabla 'X' y job 'Y'.",
  "tabla_requerida": "Sync_X",
  "job_requerido": "sync_x"
}
```

---

## 5. TABLAS SQL USADAS

### Tablas Existentes
| Tabla | Usado Por | Estado |
|-------|-----------|--------|
| `Comercial_KPIs_Diarios_v2` | Dashboard V2, Tablero Ejecutivo | ✅ Activa |
| `Comercial_Ventas_Dia_Abiertas_v2` | Ventas del Día | ✅ Activa |
| `Sync_Ventas_PorHora` | `/ventas-tiempo/{server_id}` | ✅ Activa |
| `Sync_Ventas_PorDiaSemana` | Dashboard | ✅ Activa |

### Tablas Faltantes (Requeridas para desbloquear endpoints)
| Tabla Requerida | Endpoint | Job Requerido |
|-----------------|----------|---------------|
| `Sistema_Sucursales` | `/sucursales/{server_id}` | `sync_sucursales` |
| `Sync_Metas_Comerciales` | `/metas/{server_id}` | `sync_metas` |
| `Sync_Ticket_Perfecto` | `/ticket-perfecto/{server_id}` | `sync_ticket_perfecto` |
| `Sync_Mesas` | `/mesas/{server_id}` | `sync_mesas` |
| `Sync_Movimientos_Detalle` | `/detalle-movimientos/{server_id}` | `sync_movimientos` |
| `Sync_Precios_Historicos` | `/precios-constantes/{server_id}` | `sync_precios_historicos` |
| `Sync_PAX_Detalle` | `/reporte-pax/{server_id}` | `sync_pax` |

---

## 6. VALIDACIONES DE NO REGRESIÓN

### ✅ Comercial V2 - Dashboard
```bash
GET /api/v2/comercial/dashboard?fecha_inicio=2026-05-20&fecha_fin=2026-05-25
# Resultado: 5 registros, sin errores
```

### ✅ Comercial V2 - KPIs Diarios
```bash
GET /api/v2/comercial/kpis/diarios?fecha_inicio=2026-05-20&fecha_fin=2026-05-25
# Resultado: Funcional
```

### ✅ Auth/RBAC
```bash
POST /api/auth/login
# Resultado: Token obtenido correctamente
```

### ✅ Servidores
```bash
GET /api/servers
# Resultado: 9 servidores desde EDARSAHUB SQL
```

### ✅ Endpoint LIVE Bloqueado (MPRO)
```bash
GET /api/comercial/sucursales/72f6e9a7-...
# Resultado: {"source_status": "LEGACY_LIVE_DISABLED", ...}
```

### ✅ Endpoint SoftRestaurant (Sin LIVE)
```bash
GET /api/comercial/sucursales/a5547321-...
# Resultado: {"source_status": "SUCCESS", "source_type": "NO_LIVE_REQUIRED"}
```

---

## 7. RIESGOS RESIDUALES

| Riesgo | Mitigación |
|--------|------------|
| Frontend que use endpoints bloqueados mostrará error | El error es controlado con mensaje claro |
| Código LIVE legacy sigue existiendo | Solo se ejecuta si `ENABLE_LIVE_GUARD_RAIL = False` |
| Conexiones `pymssql.connect` directas | Solo dentro de código condicional post-guard |

---

## 8. PROPUESTA FASE A-P1

### Objetivos
1. **Crear tablas sync faltantes** (7 tablas)
2. **Crear jobs de sincronización** (7 jobs)
3. **Migrar endpoints a SQL-First** (eliminar código LIVE)
4. **Eliminar flag `ENABLE_LIVE_GUARD_RAIL`** (ya no será necesario)

### Prioridad Sugerida
| Tabla | Prioridad | Justificación |
|-------|-----------|---------------|
| `Sistema_Sucursales` | P1 | Usado en filtros de varios módulos |
| `Sync_Metas_Comerciales` | P2 | Funcionalidad de metas poco usada |
| `Sync_Ticket_Perfecto` | P2 | Análisis avanzado |
| `Sync_Mesas` | P3 | Funcionalidad específica SR |
| `Sync_Movimientos_Detalle` | P3 | Drill-down detallado |
| `Sync_Precios_Historicos` | P3 | Análisis inflacionario |
| `Sync_PAX_Detalle` | P3 | Reporte específico |

---

## 9. CRITERIOS DE ACEPTACIÓN - CUMPLIMIENTO

| Criterio | Estado |
|----------|--------|
| ✅ Se identifican todos los endpoints LIVE en comercial/routes.py | 9 endpoints identificados |
| ✅ Ningún endpoint productivo de UI consulta LIVE sin justificación | Guard rail activo |
| ✅ Los endpoints migrables leen EDARSAHUB SQL | Dashboard y ventas-tiempo migrados |
| ✅ Los endpoints no migrables quedan bloqueados o documentados | 7 endpoints bloqueados |
| ✅ No se usa MongoDB | Confirmado |
| ✅ No se rompe Comercial V2 ni Tablero Ejecutivo | Validado |
| ✅ Se genera el reporte | Este documento |

---

## 10. CONCLUSIÓN

**FASE A-P0 COMPLETADA.**

El sistema ahora tiene un guard rail que impide conexiones LIVE desde endpoints de UI hacia servidores remotos. Los endpoints que ya están migrados a SQL-First siguen funcionando. Los endpoints legacy devuelven un error controlado que indica qué tabla y job se requieren para habilitarlos.

**Próximo paso:** FASE A-P1 para crear las tablas y jobs de sincronización faltantes.
