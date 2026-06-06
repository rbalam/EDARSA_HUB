# AUDITORÍA COMPLETA: MENÚS, FUENTES DE DATOS Y CONEXIONES EDARSAHUB

**Fecha:** 2026-05-26  
**Versión:** 1.0  
**Estado:** AUDITORÍA INICIAL COMPLETA

---

## RESUMEN EJECUTIVO

### Hallazgos Críticos

| Categoría | Cantidad | Severidad |
|-----------|----------|-----------|
| Menús con conexiones LIVE | 12+ | 🔴 P0-P1 |
| Módulos con MongoDB activo | 5 | 🔴 P0-P1 |
| Endpoints con server_id remoto | 10+ | 🟡 P1 |
| Hardcodes detectados | 3 | 🟡 P2 |
| Módulos SQL-Only correctos | 8+ | ✅ OK |

### Arquitectura Objetivo vs Actual

```
OBJETIVO (SQL-First):
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │ ───► │   Backend API   │ ───► │  EDARSAHUB SQL  │
│   (React)       │      │   (FastAPI)     │      │   (Cerebro)     │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                          ▲
                                                          │
                                               ┌─────────────────┐
                                               │   Jobs/Syncs    │
                                               │  (Background)   │
                                               └─────────────────┘
                                                          │
                                               ┌─────────────────┐
                                               │ Servidores      │
                                               │ Remotos (SR/MP) │
                                               └─────────────────┘

ACTUAL (Mixto con violaciones):
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │ ───► │   Backend API   │ ───► │  EDARSAHUB SQL  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │                         ▲
                                ├──────────────────────────┤ ✅ OK
                                │                         │
                                │      ┌─────────────────┐│
                                ├─────►│  MongoDB        ││ 🔴 VIOLACIÓN
                                │      │  (Legacy)       ││
                                │      └─────────────────┘│
                                │                         │
                                │      ┌─────────────────┐│
                                └─────►│  Servidores     ││ 🔴 VIOLACIÓN LIVE
                                       │  Remotos LIVE   ││
                                       └─────────────────┘│
```

---

## INVENTARIO DE MENÚS FRONTEND

### A. Menús Principales y Rutas

| # | Menú | Ruta Frontend | Archivo Principal | Estado |
|---|------|---------------|-------------------|--------|
| 1 | Tablero Ejecutivo | `/tablero-ejecutivo` | `TableroEjecutivo.js` | ✅ SQL-Only |
| 2 | Comercial | `/comercial` | `Comercial.js` | 🔴 LIVE |
| 3 | Costos y Márgenes | `/comercial/costos-margenes` | `CostosMargenes.jsx` | ✅ SQL-Only |
| 4 | Pricing IA | `/comercial/pricing-ia` | `PricingIA.jsx` | ✅ SQL-Only |
| 5 | CRM Dashboard | `/crm/dashboard` | `CRMDashboard.jsx` | ⚠️ Verificar |
| 6 | CRM Leads | `/crm/leads` | `LeadsPage.jsx` | ⚠️ MongoDB? |
| 7 | CRM Oportunidades | `/crm/oportunidades` | `OportunidadesPage.jsx` | ⚠️ MongoDB? |
| 8 | CRM Pipeline | `/crm/pipeline` | `PipelinePage.jsx` | ⚠️ Verificar |
| 9 | CRM Cuentas | `/crm/cuentas` | `CuentasPage.jsx` | ⚠️ Verificar |
| 10 | CRM Cotizaciones | `/crm/cotizaciones` | `CotizacionesPage.jsx` | ⚠️ Verificar |
| 11 | CRM Pedidos | `/crm/pedidos` | `PedidosPage.jsx` | ⚠️ Verificar |
| 12 | CRM Remisiones | `/crm/remisiones` | `RemisionesPage.jsx` | ⚠️ Verificar |
| 13 | Reportes/Operaciones | `/reportes` | `Reportes.js` | 🟡 Mixto |
| 14 | Compras | `/compras` | `Compras.js` | ✅ SQL-Only |
| 15 | Proveedores | `/proveedores` | `Proveedores.js` | ⚠️ Verificar |
| 16 | Finanzas | `/finanzas` | `Finanzas.js` | 🔴 MongoDB |
| 17 | Producción | `/produccion` | `Produccion.js` | ⚠️ Verificar |
| 18 | Tablajería Dashboard | `/tablajeria` | `TablajeriaDashboard.jsx` | ⚠️ Verificar |
| 19 | Tablajería Órdenes | `/tablajeria/ordenes` | `OrdenesPage.jsx` | ⚠️ Verificar |
| 20 | Tablajería Plantillas | `/tablajeria/plantillas` | `PlantillasPage.jsx` | ⚠️ Verificar |
| 21 | Servidores | `/servidores` | `Servidores.js` | ✅ SQL-Only |
| 22 | Catálogo Consultas | `/catalogo-consultas` | `CatalogoConsultas.js` | ✅ SQL-Only |
| 23 | Explorador BD | `/explorador-bd` | `ExploradorBD.js` | 🔴 LIVE (Admin) |
| 24 | Usuarios | `/usuarios` | `Usuarios.js` | ✅ SQL-Only |
| 25 | Scheduler | `/scheduler` | `Scheduler.jsx` | ✅ SQL-Only |
| 26 | Centro Control | `/centro-control` | `CentroControl.jsx` | ⚠️ Verificar |
| 27 | RRHH | `/recursos-humanos` | `RecursosHumanos.js` | ⚠️ Verificar |
| 28 | Alertas | `/alertas` | `Alertas.jsx` | ✅ SQL-Only |
| 29 | Cava Socios | `/cava-socios` | `CavaSociosDashboard.jsx` | ⚠️ Verificar |

---

## INVENTARIO DE ENDPOINTS BACKEND

### Endpoints SQL-Only (CORRECTOS ✅)

| Endpoint | Archivo | Tabla EDARSAHUB | Descripción |
|----------|---------|-----------------|-------------|
| `GET /api/v2/comercial/dashboard` | `comercial_v2/routes.py` | `Comercial_KPIs_Diarios_v2` | Dashboard ejecutivo |
| `GET /api/v2/comercial/kpis-diarios` | `comercial_v2/routes.py` | `Comercial_KPIs_Diarios_v2` | KPIs por día |
| `GET /api/v2/comercial/ventas-dia` | `comercial_v2/routes.py` | `Comercial_Ventas_Dia_Abiertas_v2` | Ventas del día |
| `GET /api/servers` | `server.py` | `Servidores_Conexiones` | Lista de servidores |
| `GET /api/unidades-negocio` | `server.py` | `Unidades_Negocio` | Unidades de negocio |
| `GET /api/sistema/menus/usuario` | `sistema/routes.py` | `Sistema_Menus` | Menús dinámicos |
| `GET /api/auth/me` | `auth/routes.py` | `Usuario_Catalogo` | Usuario actual |
| `GET /api/roles` | `auth/routes.py` | `Usuario_Roles` | Roles RBAC |
| `POST /api/admin/scheduler/resync/*` | `admin_scheduler_resync.py` | `Sistema_Scheduler_*` | Resync administrativo |
| `GET /api/admin/data-quality/*` | `admin_data_quality.py` | `Comercial_KPIs_*` | Auditoría de datos |

### Endpoints con Conexiones LIVE (VIOLACIÓN 🔴)

| Endpoint | Archivo | Servidor Remoto | Severidad | Migración |
|----------|---------|-----------------|-----------|-----------|
| `GET /comercial/dashboard/{server_id}` | `comercial/routes.py:4143` | SoftRestaurant/MPRO LIVE | 🔴 P0 | Usar snapshot SQL |
| `GET /comercial/sucursales/{server_id}` | `comercial/routes.py:1816` | SoftRestaurant LIVE | 🔴 P0 | Crear tabla sync |
| `GET /comercial/metas/{server_id}` | `comercial/routes.py:1882` | MPRO LIVE | 🔴 P1 | Crear tabla sync |
| `GET /comercial/ticket-perfecto/{server_id}` | `comercial/routes.py:2155` | SoftRestaurant LIVE | 🔴 P1 | Crear tabla sync |
| `GET /comercial/ventas-tiempo/{server_id}` | `comercial/routes.py:2378` | SoftRestaurant LIVE | 🔴 P1 | Crear tabla sync |
| `GET /comercial/mesas/{server_id}` | `comercial/routes.py:2602` | SoftRestaurant LIVE | 🟡 P2 | Crear tabla sync |
| `GET /comercial/detalle-movimientos/{server_id}` | `comercial/routes.py:2875` | SoftRestaurant LIVE | 🟡 P2 | Crear tabla sync |
| `GET /comercial/precios-constantes/{server_id}` | `comercial/routes.py:3119` | SoftRestaurant LIVE | 🟡 P2 | Crear tabla sync |
| `GET /comercial/reporte-pax/{server_id}` | `comercial/routes.py:3703` | SoftRestaurant LIVE | 🟡 P2 | Crear tabla sync |
| `POST /api/universal-query/execute` | `universal_query/routes.py` | Cualquiera (Admin) | 🟡 P2-Admin | OK si es admin |

### Endpoints con MongoDB (VIOLACIÓN 🔴)

| Endpoint | Archivo | Colección | Severidad | Migración |
|----------|---------|-----------|-----------|-----------|
| Fase2 Operativo (todos) | `fase2_operativo/db_utils.py` | `tareas, workflows, etc` | 🔴 P0 | Migrar a SQL |
| Finanzas - Cuadres Z | `finanzas/repository_cuadres_z.py` | `cuadres_z` | 🔴 P1 | Migrar a SQL |
| Config Asignaciones | `configuracion/routes/config_asignaciones_routes.py` | `asignaciones` | 🟡 P2 | Migrar a SQL |

---

## MAPA DE SINCRONIZACIONES

### Jobs Existentes

| Job | Archivo | Origen | Destino SQL | Frecuencia | Estado |
|-----|---------|--------|-------------|------------|--------|
| `sync_comercial_v2` | `sync_comercial_v2_job.py` | SR/MPRO | `Comercial_KPIs_Diarios_v2` | 5 min | ✅ Activo |
| `sync_comercial_abiertas_v2` | `sync_comercial_abiertas_v2_job.py` | SR/MPRO | `Comercial_Ventas_Dia_Abiertas_v2` | 2 min | ✅ Activo |
| `pedidos_detector` | `pedidos_detector_job.py` | MPRO | `Scheduler_PedidosProcesados` | 1 min | ✅ Activo |
| Resync Manual | `admin_scheduler_resync.py` | SR/MPRO | `Comercial_KPIs_*` | Manual | ✅ Disponible |

### Jobs Faltantes (Recomendados)

| Job Propuesto | Origen | Destino SQL Propuesto | Prioridad |
|---------------|--------|----------------------|-----------|
| `sync_sucursales` | SR/MPRO | `Sync_Sucursales` | P1 |
| `sync_metas` | MPRO | `Sync_Metas_Comerciales` | P1 |
| `sync_ticket_perfecto` | SR | `Sync_Ticket_Perfecto` | P2 |
| `sync_ventas_hora` | SR/MPRO | `Sync_Ventas_PorHora` | P2 |
| `sync_mesas` | SR | `Sync_Mesas_Uso` | P3 |
| `sync_finanzas_cuadres` | SR | `Finanzas_Cuadres_Z` | P1 |

---

## TABLAS EDARSAHUB SQL

### Tablas Existentes y Usadas

| Tabla | Módulo | Job que la llena | Estado |
|-------|--------|------------------|--------|
| `Comercial_KPIs_Diarios_v2` | Comercial | `sync_comercial_v2` | ✅ OK |
| `Comercial_Ventas_Dia_Abiertas_v2` | Comercial | `sync_comercial_abiertas_v2` | ✅ OK |
| `Servidores_Conexiones` | Core | Manual/Admin | ✅ OK |
| `Unidades_Negocio` | Core | Manual/Admin | ✅ OK |
| `Sistema_Empresas` | Core | Manual/Admin | ✅ OK |
| `Usuario_Catalogo` | Auth | Manual/Admin | ✅ OK |
| `Usuario_Roles` | Auth/RBAC | Manual/Admin | ✅ OK |
| `Usuario_EmpresasAsignacion` | Auth/RBAC | Manual/Admin | ✅ OK |
| `Sistema_Menus` | Sistema | Manual/Admin | ✅ OK |
| `Scheduler_PedidosProcesados` | Compras | `pedidos_detector` | ✅ OK |

### Tablas Pendientes de Crear

| Tabla Propuesta | Módulo | Propósito |
|-----------------|--------|-----------|
| `Sync_Sucursales` | Comercial | Snapshot de sucursales |
| `Sync_Metas_Comerciales` | Comercial | Metas por unidad |
| `Sync_Ticket_Perfecto` | Comercial | Métricas de ticket |
| `Sync_Ventas_PorHora` | Comercial | Ventas horarias |
| `Finanzas_Cuadres_Z` | Finanzas | Cuadres de caja |
| `Sistema_Scheduler_Jobs` | Scheduler | Definición de jobs |
| `Sistema_Scheduler_Ejecuciones` | Scheduler | Historial de ejecuciones |

---

## CONEXIONES LIVE DETECTADAS (Detalle)

### 1. Módulo Comercial Legacy (`/app/backend/modules/comercial/`)

**Archivos afectados:**
- `routes.py` - 10+ endpoints con `{server_id}` que abren conexión LIVE
- `service.py` - `pymssql.connect()` directo a servidores remotos
- `adapters.py` - `get_connection_for_role()` conecta a servidores

**Funciones con conexión LIVE:**
```python
# routes.py:2416
conn = pymssql.connect(
    server=server_config['ip'],
    port=server_config['port'],
    ...
)

# routes.py:2524
conn_hoy = pymssql.connect(...)
```

**Clasificación:** 🔴 VIOLACIÓN P0

**Corrección recomendada:**
- Migrar todos los endpoints `{server_id}` a leer de tablas snapshot en EDARSAHUB
- Crear jobs de sincronización para poblar esas tablas

### 2. Módulo Fase2 Operativo (`/app/backend/modules/fase2_operativo/`)

**Archivos afectados:**
- `db_utils.py` - `MongoClient` directo
- `repositories/*.py` - Todos usan MongoDB

**Código violatorio:**
```python
# db_utils.py:26-29
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
_client = MongoClient(mongo_url)
```

**Clasificación:** 🔴 VIOLACIÓN P0-P1

**Corrección recomendada:**
- Crear tablas SQL equivalentes para tareas, workflows, auditorías
- Migrar repositorios a usar EDARSAHUB SQL

### 3. Módulo Universal Query (`/app/backend/modules/universal_query/`)

**Archivos afectados:**
- `routes.py` - `execute_sql_on_server()` conecta a cualquier servidor

**Clasificación:** 🟡 P2-Admin (Permitido si es solo para administradores)

**Nota:** Este módulo es una herramienta administrativa de diagnóstico. 
Se permite conexión LIVE bajo estas condiciones:
- Solo usuarios con rol `SUPERADMIN`
- Solo para diagnóstico, no para dashboards
- No debe alimentar ningún menú operativo

---

## HARDCODES DETECTADOS

### 1. Fallback de Unidades en Jobs
**Archivo:** `/app/backend/core/scheduler/jobs/sync_comercial_v2_job.py`
**Línea:** ~118
**Hardcode:** Lista de unidades con nombres fijos
**Severidad:** 🟡 P2 (es fallback de última línea)
**Estado:** Corregido parcialmente - nombres sin acentos

### 2. Roles SuperAdmin (CORREGIDO)
**Archivo:** `/app/backend/modules/comercial_v2/routes.py`
**Función:** `get_unidades_permitidas_v2`
**Estado:** ✅ CORREGIDO - Ahora usa `rbac_helper_sql.py`

### 3. Códigos de Unidades Canónicas
**Archivo:** Múltiples
**Hardcode:** `['130MID', '130QRO', 'CIENFUEGOS', 'ESTELAR', 'ORIGEN']`
**Severidad:** 🟢 Aceptable (son códigos canónicos oficiales)

---

## CACHÉ DETECTADA

### Frontend
| Tipo | Ubicación | Qué guarda | Limpieza |
|------|-----------|------------|----------|
| localStorage | `AuthContext.jsx` | Token, usuario | Login/Logout |
| sessionStorage | Varios | Filtros temporales | Sesión |
| React Query | Hooks | Respuestas API | TTL automático |

### Backend
| Tipo | Archivo | Qué guarda | TTL |
|------|---------|------------|-----|
| LRU Cache | `rbac_helper_sql.py` | Roles | 5 min |
| In-memory | `server_registry.py` | Servidores | 5 min |
| In-memory | `dashboard_cache` | KPIs | Variable |

### Limpieza Preview
- ✅ Implementado en `previewCacheUtils.js`
- ✅ Se ejecuta en cada login en modo preview
- ✅ Endpoint `/api/admin/cache/clear-preview` disponible

---

## PLAN DE CORRECCIÓN

### FASE A: Eliminar conexiones LIVE en dashboards (P0)
1. Identificar todos los endpoints `{server_id}` en `comercial/routes.py`
2. Crear versiones SQL-Only que lean de tablas existentes o crear tablas nuevas
3. Deprecar endpoints LIVE progresivamente

### FASE B: Eliminar MongoDB en módulos críticos (P0-P1)
1. Migrar `fase2_operativo` de MongoDB a SQL
2. Migrar `finanzas/cuadres_z` a SQL
3. Eliminar fallbacks MongoDB

### FASE C: Crear jobs de sincronización faltantes (P1)
1. `sync_sucursales` - Para `/comercial/sucursales/{server_id}`
2. `sync_metas` - Para `/comercial/metas/{server_id}`
3. `sync_finanzas_cuadres` - Para cuadres Z

### FASE D: Normalizar filtros (P2)
1. Asegurar que `selectedServer` sea solo filtro lógico
2. Eliminar uso de `selectedServer` para abrir conexiones

### FASE E: Crear tablas scheduler SQL (P1)
1. `Sistema_Scheduler_Jobs`
2. `Sistema_Scheduler_Ejecuciones`
3. `Sistema_Scheduler_Logs`

### FASE F: Implementar guard rails (P2)
1. Middleware que detecte conexiones LIVE desde endpoints de UI
2. Logging de violaciones
3. Circuit breaker para proteger servidores remotos

---

## CRITERIOS DE ÉXITO

| Criterio | Estado Actual | Objetivo |
|----------|---------------|----------|
| Menús con conexiones LIVE | 12+ | 0 |
| MongoDB en módulos operativos | 5 | 0 |
| Endpoints con server_id remoto | 10+ | 0 (solo admin) |
| Jobs de sync documentados | 4 | 10+ |
| Tablas SQL para cada menú | Parcial | Completo |
| Hardcodes de roles | Eliminado ✅ | Eliminado |
| Cache preview limpia | Implementado ✅ | Implementado |

---

## CONCLUSIÓN

El sistema tiene una base sólida SQL-First en los módulos nuevos (`comercial_v2`, `scheduler`, `rbac`), pero conserva código legacy con conexiones LIVE y MongoDB en módulos antiguos.

**Prioridad inmediata:**
1. 🔴 Migrar módulo `fase2_operativo` de MongoDB a SQL
2. 🔴 Eliminar conexiones LIVE en `comercial/routes.py`
3. 🟡 Crear jobs de sync faltantes

**El Tablero Ejecutivo y los módulos V2 ya cumplen con la arquitectura SQL-First.**
