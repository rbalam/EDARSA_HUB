# AUDITORÍA: Conexiones en Vivo vs EDARSAHUB SQL

**Fecha:** 2026-05-15  
**Tipo:** Diagnóstico Pasivo  
**Autor:** E1 Agent  
**Estado:** SOLO LECTURA - NO SE MODIFICÓ CÓDIGO NI BASE DE DATOS

---

## 1. RESUMEN EJECUTIVO

Se identificaron **múltiples conexiones en vivo** desde módulos funcionales del backend hacia servidores externos (SoftRestaurant, MPRO, APIs locales). Estas conexiones **VIOLAN** la regla arquitectónica de que EDARSAHUB SQL debe ser la única fuente de lectura para dashboards y endpoints funcionales.

### Hallazgos Críticos:

| Categoría | Cantidad | Riesgo |
|-----------|----------|--------|
| **PROHIBIDO** - Endpoints con consultas LIVE | 8+ | ALTO |
| **PROHIBIDO** - Funciones con execute_sql_query a host externo | 40+ líneas | ALTO |
| **PERMITIDO** - Jobs de sincronización | 8 | BAJO |
| **TOLERADO** - Adapters para APIs locales | 1 archivo | MEDIO |

---

## 2. REGLA ARQUITECTÓNICA FINAL

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    EDARSAHUB SQL ES LA ÚNICA FUENTE                        ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Frontend → Backend EDARSA HUB → EDARSAHUB SQL                            ║
║                                                                            ║
║  Las fuentes origen (SoftRestaurant, MPRO, APIs locales) SOLO pueden       ║
║  ser consultadas por:                                                      ║
║    - Jobs de sincronización programados                                    ║
║    - Agentes locales autorizados                                           ║
║    - Servicios de ingesta backend                                          ║
║                                                                            ║
║  PROHIBIDO:                                                                ║
║    - Dashboards consultando fuentes externas                               ║
║    - Endpoints funcionales con fallback LIVE                               ║
║    - Frontend invocando APIs locales                                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. MAPA DE FUENTES

### 3.1 FUENTES PERMITIDAS (Solo para Jobs de Sync)

| Fuente | Tipo | Uso Permitido |
|--------|------|---------------|
| SoftRestaurant SQL | SQL Server remoto | Job sync_comercial_v2, sync_nightly |
| MPRO SQL | SQL Server remoto | Job sync_comercial_v2 |
| API Local ORIGEN (8000) | HTTP API | Job sync_comercial_abiertas_v2 |
| API Local QRO (8001) | HTTP API | Job sync_comercial_abiertas_v2 |

### 3.2 FUENTES PROHIBIDAS (Para Dashboards)

| Fuente | Riesgo | Tabla EDARSAHUB que debe usarse |
|--------|--------|--------------------------------|
| SoftRestaurant LIVE | ALTO | Comercial_KPIs_Diarios_v2 |
| MPRO LIVE | ALTO | Comercial_KPIs_Diarios_v2 |
| API Local LIVE | ALTO | Comercial_Ventas_Dia_Abiertas_v2 |
| tempcheques LIVE | ALTO | Comercial_Ventas_Dia_Abiertas_v2 |

---

## 4. HALLAZGOS POR ARCHIVO Y LÍNEA

### 4.1 MÓDULO COMERCIAL - routes.py

| Línea | Función/Endpoint | Tipo Conexión | Clasificación | Riesgo |
|-------|------------------|---------------|---------------|--------|
| 3611 | Modal detalle (comparativos) | SQL a server['host'] SoftRestaurant | **PROHIBIDO** | ALTO |
| 3765 | Modal detalle (comparativos) | SQL a server['host'] MPRO | **PROHIBIDO** | ALTO |
| 1450 | /comercial/sucursales/{server_id} | SQL a server['host'] | **PROHIBIDO** | ALTO |
| 1545-1598 | Productos/Vendedores | SQL a server['host'] | **PROHIBIDO** | ALTO |
| 1651-1684 | Productos/Vendedores | SQL a server['host'] | **PROHIBIDO** | ALTO |
| 1838 | Rentabilidad | SQL a server['host'] | **PROHIBIDO** | ALTO |
| 1914 | Rentabilidad | SQL a server['host'] | **PROHIBIDO** | ALTO |
| 2027-2095 | Ventas por hora/día | SQL a server['host'] | **PROHIBIDO** | ALTO |
| 2158-2247 | Ventas por hora/día MPRO | SQL a server['host'] | **PROHIBIDO** | ALTO |
| 2352-2540 | Mesas/Movimientos | SQL a server['host'] | **PROHIBIDO** | ALTO |
| 2617-2663 | Detalle movimientos | SQL a server['host'] | **PROHIBIDO** | ALTO |

**Endpoints Afectados:**
- `/comercial/sucursales/{server_id}`
- `/comercial/metas/{server_id}`
- `/comercial/ticket-perfecto/{server_id}`
- `/comercial/ventas-tiempo/{server_id}`
- `/comercial/mesas/{server_id}`
- `/comercial/detalle-movimientos/{server_id}`
- `/comercial/precios-constantes/{server_id}`
- `/comercial/reporte-pax/{server_id}`
- `/comercial/dashboard/{server_id}`

### 4.2 MÓDULO COMERCIAL - service.py

| Línea | Función | Tipo Conexión | Clasificación | Riesgo |
|-------|---------|---------------|---------------|--------|
| 1321 | sumar_ventas_api_local | API Local MPRO | **PROHIBIDO** para tablero | ALTO |
| 1437-1678 | get_kpis_mpro_por_sucursal (fallback SQL) | SQL a server['host'] MPRO | **PROHIBIDO** | ALTO |
| 1291-1400 | Modo Ventas del Día - API local | API Local MPRO | **PROHIBIDO** para tablero | ALTO |

**Flujo Problemático:**
```
Tablero Ejecutivo (solo_ventas_dia=True)
    → get_kpis_mpro_por_sucursal()
        → sumar_ventas_api_local_a_sucursal()  ← PROHIBIDO
        → fallback: execute_sql_query(server['host'])  ← PROHIBIDO
```

### 4.3 MÓDULO COMERCIAL - queries/

| Archivo | Línea | Función | Clasificación |
|---------|-------|---------|---------------|
| mpro.py | 181-182 | query_ventas_periodo_mpro | **PROHIBIDO** si usado por dashboard |
| mpro.py | 350-351 | query interno | **PROHIBIDO** si usado por dashboard |
| mpro.py | 571-572 | query interno | **PROHIBIDO** si usado por dashboard |
| softrestaurant.py | 160-182 | query_ventas_periodo_sr | **PROHIBIDO** si usado por dashboard |

### 4.4 MÓDULO COMERCIAL - adapters.py

| Función | Tipo | Clasificación |
|---------|------|---------------|
| query_api_mpro_local() | API Local | **TOLERADO** si usado solo por jobs |
| obtener_ventas_dia_api_local() | API Local | **PROHIBIDO** si usado por tablero |
| sumar_ventas_api_local_a_sucursal() | API Local | **PROHIBIDO** si usado por tablero |

**Estado Actual:** Usado por `get_kpis_mpro_por_sucursal()` que es llamado desde `tablero-ejecutivo` → **PROHIBIDO**

### 4.5 MÓDULO COMERCIAL - repository.py

| Línea | Función | Clasificación |
|-------|---------|---------------|
| 437-438 | query_rentabilidad_sr | **PROHIBIDO** si usado por dashboard |
| 466-467 | query_ventas_softrestaurant | **PROHIBIDO** si usado por dashboard |
| 501-502 | query interno | **PROHIBIDO** si usado por dashboard |

---

## 5. JOBS DE SINCRONIZACIÓN (PERMITIDOS)

| Job | Archivo | Fuentes Consultadas | Tabla Destino EDARSAHUB |
|-----|---------|---------------------|------------------------|
| sync_comercial_abiertas_v2 | sync_comercial_abiertas_v2_job.py | API Local MPRO, SoftRestaurant SQL | Comercial_Ventas_Dia_Abiertas_v2 |
| sync_comercial_v2 | sync_comercial_v2_job.py | MPRO SQL, SoftRestaurant SQL | Comercial_KPIs_Diarios_v2 |
| sync_nightly_comercial | sync_nightly_comercial_job.py | SoftRestaurant SQL | Comercial_KPIs_Diarios_v2 |
| sync_short_comercial | sync_short_comercial_job.py | SoftRestaurant SQL | Comercial_KPIs_Diarios_v2 |
| sync_ingresos | sync_ingresos_job.py | SoftRestaurant SQL | Comercial_Ingresos_* |
| sync_propinas_tpv | sync_propinas_tpv_job.py | SoftRestaurant SQL | Propinas_* |

**Clasificación:** PERMITIDO - Los jobs son el único mecanismo autorizado para traer datos de fuentes origen a EDARSAHUB.

---

## 6. ANÁLISIS DE IMPACTO

### 6.1 Tablero Ejecutivo - Modo Ventas del Día

**Estado Actual (PROBLEMÁTICO):**
```
GET /api/comercial/tablero-ejecutivo?anios=-1
    │
    ├── SoftRestaurant: Lee de Comercial_Ventas_Dia_Abiertas_v2 (EDARSAHUB) ✅
    │   └── Funciona correctamente
    │
    └── MPRO (130QRO, ORIGEN): Intenta API local EN VIVO ❌
        └── Si falla: Fallback a SQL server['host'] EN VIVO ❌
            └── Si falla: Muestra $0
```

**Estado Correcto (PROPUESTO):**
```
GET /api/comercial/tablero-ejecutivo?anios=-1
    │
    ├── SoftRestaurant: Lee de Comercial_Ventas_Dia_Abiertas_v2 (EDARSAHUB) ✅
    │
    └── MPRO (130QRO, ORIGEN): Lee de Comercial_Ventas_Dia_Abiertas_v2 (EDARSAHUB) ✅
        └── Si no hay datos: Mostrar "SYNC_STALE" o "NO_SYNC_DATA"
```

### 6.2 Modal de Detalle de Unidad

**Estado Actual (PROBLEMÁTICO):**
- Comparativos (Día anterior, Mes anterior, Año anterior): SQL LIVE a server['host']
- Ventas por hora: SQL LIVE
- Ventas por día semana: SQL LIVE

**Estado Correcto (PROPUESTO):**
- Leer de Comercial_KPIs_Diarios_v2 (histórico)
- Crear tabla de granularidad por hora si se requiere

---

## 7. RECOMENDACIONES

### P0 - CRÍTICO (Ventas del Día MPRO)

| Acción | Archivo | Descripción |
|--------|---------|-------------|
| **ELIMINAR** conexión API local para tablero | service.py | `get_kpis_mpro_por_sucursal()` no debe llamar a APIs locales |
| **LEER** de EDARSAHUB | service.py | Usar `_get_ventas_abiertas_edarsahub()` para MPRO |
| **VERIFICAR** job de sync | sync_comercial_abiertas_v2_job.py | Asegurar que guarde datos MPRO correctos |

### P1 - ALTO (Modal de Detalle)

| Acción | Endpoint | Tabla EDARSAHUB Requerida |
|--------|----------|--------------------------|
| Migrar comparativos | Modal detalle | Comercial_KPIs_Diarios_v2 |
| Migrar ventas por hora | /ventas-tiempo | **NUEVA TABLA REQUERIDA** |
| Migrar ventas por día | /ventas-tiempo | **NUEVA TABLA REQUERIDA** |

### P2 - MEDIO (Endpoints de Detalle)

| Endpoint | Acción | Prioridad |
|----------|--------|-----------|
| /comercial/sucursales/{server_id} | Migrar a EDARSAHUB | P2 |
| /comercial/metas/{server_id} | Evaluar si necesita LIVE | P2 |
| /comercial/ticket-perfecto/{server_id} | Migrar a EDARSAHUB | P2 |
| /comercial/mesas/{server_id} | Evaluar necesidad | P2 |

---

## 8. TABLAS EDARSAHUB EXISTENTES

| Tabla | Contiene | Sync Job |
|-------|----------|----------|
| Comercial_Ventas_Dia_Abiertas_v2 | Ventas del día (snapshot) | sync_comercial_abiertas_v2 |
| Comercial_KPIs_Diarios_v2 | Histórico cerrado por día | sync_comercial_v2, sync_nightly |

---

## 9. TABLAS EDARSAHUB REQUERIDAS (Propuestas)

| Tabla Propuesta | Contenido | Job Requerido |
|-----------------|-----------|---------------|
| Comercial_Ventas_Por_Hora_v2 | Desglose por hora del día | sync_comercial_hora_job (NUEVO) |
| Comercial_Ventas_Por_DiaSemana_v2 | Desglose por día de semana | sync_comercial_diasemana_job (NUEVO) |

---

## 10. CONFIRMACIONES

- [x] NO se modificó código
- [x] NO se modificó base de datos
- [x] Solo se realizó diagnóstico de lectura
- [x] Se identificaron conexiones PROHIBIDAS
- [x] Se identificaron conexiones PERMITIDAS
- [x] Se generó plan de migración

---

## 11. PRÓXIMOS PASOS

1. **AUTORIZACIÓN REQUERIDA:** Aprobar eliminación de conexiones LIVE en `service.py`
2. **VERIFICAR:** Que job `sync_comercial_abiertas_v2` esté guardando datos MPRO
3. **REFACTORIZAR:** `get_kpis_mpro_por_sucursal()` para leer solo de EDARSAHUB
4. **CREAR:** Jobs de sincronización para granularidad por hora (si se requiere modal)
5. **MIGRAR:** Endpoints de detalle gradualmente

---

**FIN DEL REPORTE DE AUDITORÍA**
