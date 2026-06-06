# DIAGNÓSTICO: Portal Inteligencia Comercial IA
## EDARSA HUB - Junio 2026

---

## 1. RESUMEN EJECUTIVO

| Componente | Estado | Ubicación | Notas |
|------------|--------|-----------|-------|
| Backend API | ✅ Implementado | `/app/backend/modules/inteligencia_comercial/routes.py` | Conexión directa a EDARSAHUB SQL Server |
| Frontend Portal | ✅ Implementado | `/app/frontend/src/portal-inteligencia/` | Standalone con routing desacoplado |
| Host Router | ✅ Implementado | `/app/frontend/src/HostRouter.jsx` | Subdominios → Portal |
| RBAC Permisos | ❌ FALTANTE | N/A | No existen permisos `INTELIGENCIA_COMERCIAL_*` |
| Scheduler Job | ❌ FALTANTE | N/A | No registrado `inteligencia_comercial_sync` |
| Tablas SQL | ⚠️ PARCIAL | EDARSAHUB | Algunas vistas creadas, esquema por validar |

---

## 2. ANÁLISIS DE COMPONENTES

### 2.1 Backend (`/app/backend/modules/inteligencia_comercial/routes.py`)

**Endpoints existentes:**

| Endpoint | Método | Descripción | Estado |
|----------|--------|-------------|--------|
| `/api/inteligencia/dashboard` | GET | Dashboard con fallback dinámico | ✅ |
| `/api/inteligencia/dashboard/sp` | GET | Versión con Stored Procedure | ✅ |
| `/api/inteligencia/comercial/units` | GET | Lista de unidades/sucursales | ✅ |
| `/api/inteligencia/scheduler/jobs` | GET | Lista de jobs SQL | ✅ |
| `/api/inteligencia/scheduler/force/{id}` | POST | Trigger manual de job | ✅ |

**Conexión SQL:**
- Host: `54.39.104.176` (EDARSAHUB)
- Puerto: `1433`
- Base de datos: `EDARSAHUB`
- Usuario: Variables de entorno `EDARSAHUB_USERNAME`, `EDARSAHUB_PASSWORD`
- Driver: `pymssql`

**FALLBACK Implementado:**
```python
UNIDAD_MULTIPLIERS = {
    'todas': 1.0,
    'cienfuegos': 0.32,
    'merida': 0.25,
    'queretaro': 0.18,
    'estelar': 0.15,
    'origen': 0.10,
}
```

### 2.2 Frontend Portal (`/app/frontend/src/portal-inteligencia/`)

**Estructura de archivos:**
```
portal-inteligencia/
├── App.jsx                    # Root del portal standalone
├── components/                # Componentes compartidos
└── pages/
    ├── DashboardIA.jsx        # Dashboard principal (KPIs)
    ├── VentasProductoPage.jsx # Análisis por producto
    ├── VentasCasaPage.jsx     # Análisis por casa/distribuidor
    ├── VentasFamiliaPage.jsx  # Análisis por familia
    ├── VentasHorarioPage.jsx  # Análisis por horario
    └── AnalisisPAXPage.jsx    # Análisis de PAX y propinas
```

**Integración con selector de unidades:**
- Todos los componentes reciben `unidadSeleccionada` como prop
- `useEffect` con dependencia en `unidadSeleccionada` para re-fetch

**Rutas de acceso:**
- Interno CRM: `/inteligencia-comercial/*`
- Subdominio: `inteligencia.edarsa.com.mx` → Portal standalone

### 2.3 Host Router (`/app/frontend/src/HostRouter.jsx`)

**Mapeo de subdominios:**
```javascript
const SUBDOMAIN_CONFIG = {
  'inteligencia.edarsa.com.mx': 'inteligencia',
  'proveedores.edarsa.com.mx': 'proveedores',
  'ia.edarsa.com.mx': 'inteligencia',
  'suppliers.edarsa.com.mx': 'proveedores',
};
```

### 2.4 Menú Principal (`/app/frontend/src/pages/Layout.js`)

**Estado actual:**
- Módulo Comercial tiene submenu "Dashboard Comercial"
- ❌ NO existe entrada para "Portal Inteligencia Comercial" en el sidebar principal
- El portal se accede vía:
  - URL directa `/inteligencia-comercial`
  - Pestaña dentro de `/comercial` (ComercialDashboard)

### 2.5 Scheduler Existente

**Jobs registrados en `scheduler_manager.py`:**
1. `sla_processor` - Procesa SLAs
2. `notifications_dispatcher` - Envía notificaciones
3. `auditorias_scheduler` - Auditorías programadas
4. `pedidos_detector` - Detecta pedidos en MPRO/Soft
5. `inventarios_detector` - Detecta inventarios
6. `sync_short_comercial` - SYNC-S KPIs (cada 15 min)
7. `sync_nightly_comercial` - SYNC-N nocturno
8. `sync_ingresos_incremental` - Control de ingresos
9. `sync_propinas_tpv_incremental` - Propinas TPV
10. `sync_comercial_v2` - KPIs Comerciales V2
11. `sync_comercial_abiertas_v2` - Ventas abiertas
12. `cava_socios_monthly` - Estados de cuenta Cava
13. `crm_sync` - Sincronización CRM
14. `crm_sla_check` - Verificación SLA CRM
15. `crm_actividades_vencidas` - Actividades CRM
16. `vtiger_sync` - Sincronización Vtiger

**❌ FALTANTE: `inteligencia_comercial_sync`**

### 2.6 RBAC Actual (`/app/backend/core/rbac/schemas.py`)

**Módulos existentes:**
```python
class ModuloSistema(str, Enum):
    OPERATIVO = "operativo"
    SLA = "sla"
    CARGOS = "cargos"
    RESPONSABILIDAD = "responsabilidad"
    NOTIFICACIONES = "notificaciones"
    SCHEDULER = "scheduler"
    WORKFLOW = "workflow"
    AUTH = "auth"
    REPORTES = "reportes"
    CONFIGURACION = "configuracion"
```

**❌ FALTANTE: `INTELIGENCIA_COMERCIAL`**

**Permisos existentes (patrón):**
```python
{"codigo": "CARGOS_VER", "modulo": "cargos", "accion": "ver", ...},
{"codigo": "CARGOS_CREAR", "modulo": "cargos", "accion": "crear", ...},
{"codigo": "CARGOS_APLICAR", "modulo": "cargos", "accion": "aplicar", ...},
```

---

## 3. BRECHAS IDENTIFICADAS

### 3.1 RBAC - Permisos Faltantes

**Requerido crear en `PERMISOS_SISTEMA`:**

| Código | Módulo | Acción | Descripción |
|--------|--------|--------|-------------|
| `INTELIGENCIA_COMERCIAL_VER` | `inteligencia_comercial` | `ver` | Ver dashboards y KPIs |
| `INTELIGENCIA_COMERCIAL_EXPORTAR` | `inteligencia_comercial` | `crear` | Exportar reportes |
| `INTELIGENCIA_COMERCIAL_CONFIGURAR` | `inteligencia_comercial` | `configurar` | Configurar umbrales/alertas |
| `INTELIGENCIA_COMERCIAL_SYNC` | `inteligencia_comercial` | `gestionar` | Ejecutar sincronización manual |
| `INTELIGENCIA_COMERCIAL_ADMIN` | `inteligencia_comercial` | `admin` | Administración completa |

### 3.2 Scheduler - Job Faltante

**Requerido crear en `config.py`:**
```python
"inteligencia_comercial_sync": JobConfig(
    job_id="inteligencia_comercial_sync",
    job_name="Inteligencia Comercial - Sincronización",
    description="Sincroniza datos analíticos desde sistemas origen hacia EDARSAHUB",
    enabled=True,
    interval_seconds=900,  # 15 minutos
    batch_size=100,
    timeout_seconds=600
),
```

### 3.3 Integración con Módulo Comercial Existente

**Queries existentes en `/app/backend/modules/comercial/`:**

**SoftRestaurant:**
```sql
SELECT totalprecuenta, nopersonas 
FROM cheques 
WHERE ...
```

**MPRO:**
```sql
SELECT co_personas FROM Comanda
SELECT Vn_Folio, Vn_Precio_Neto_Importe FROM Venta_Encabezado
```

**Tablas existentes referenciadas:**
- `cheques` (SoftRestaurant)
- `turnos` (SoftRestaurant)
- `meseros` (SoftRestaurant)
- `Comanda` (MPRO)
- `Venta_Encabezado` (MPRO)
- `Venta_Detalle` (MPRO)
- `Products` (EDARSAHUB)
- `Servidores_Conexiones` (EDARSAHUB)

### 3.4 Catálogos SQL en EDARSAHUB

**Vistas creadas (verificar existencia):**
- `View_Inteligencia_Comercial`
- `Cat_Productos` (alias de Products)
- `Cat_Familias`

**Stored Procedure creado:**
- `Sp_GetDashboardInteligencia`

---

## 4. DEPENDENCIAS CRÍTICAS

### 4.1 Variables de Entorno Requeridas

```bash
# Backend .env
EDARSAHUB_HOST=54.39.104.176
EDARSAHUB_PORT=1433
EDARSAHUB_DATABASE=EDARSAHUB
EDARSAHUB_USERNAME=HRLectura
EDARSAHUB_PASSWORD=***
```

### 4.2 Tablas SQL Requeridas en EDARSAHUB

**Para validar con `INFORMATION_SCHEMA`:**
```sql
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
AND TABLE_NAME IN (
    'Products',
    'Fact_Ventas_Consolidadas',
    'Sync_Sales',
    'Sync_Payments',
    'Config_Horarios',
    'Sys_Scheduler_Jobs'
)
```

### 4.3 Conexiones a Sistemas Origen

| Sistema | Tipo | Sucursales |
|---------|------|------------|
| SoftRestaurant | POS | 130° MÉRIDA, CIENFUEGOS, LA ESTELAR |
| MPRO | POS | 130° QRO, ORIGEN |

---

## 5. PLAN DE ACCIÓN RECOMENDADO

### Fase 1: Validación de Esquema SQL
1. Solicitar archivo `EDARSAHUB_SCHEMA_ONLY.sql` o ejecutar `INFORMATION_SCHEMA`
2. Verificar existencia de tablas/vistas requeridas
3. Documentar estructura real de columnas

### Fase 2: RBAC
1. Agregar módulo `INTELIGENCIA_COMERCIAL` al enum `ModuloSistema`
2. Agregar permisos `INTELIGENCIA_COMERCIAL_*` a `PERMISOS_SISTEMA`
3. Asignar permisos a roles existentes (ADMIN, DIRECCION, GERENTE_OPS)

### Fase 3: Scheduler
1. Crear `inteligencia_comercial_sync_job.py` en `/app/backend/core/scheduler/jobs/`
2. Registrar en `config.py` y `scheduler_manager.py`
3. Implementar lógica de sincronización desde sistemas origen

### Fase 4: Integración de Datos Reales
1. Crear queries para extraer de SoftRestaurant/MPRO
2. Implementar ETL interno (NO externo) hacia `Fact_Ventas_Consolidadas`
3. Conectar dashboard con datos sincronizados

---

## 6. ARCHIVOS DE REFERENCIA

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/modules/inteligencia_comercial/routes.py` | API endpoints |
| `/app/backend/core/scheduler/config.py` | Configuración de jobs |
| `/app/backend/core/scheduler/scheduler_manager.py` | Registro de jobs |
| `/app/backend/core/rbac/schemas.py` | Permisos y roles |
| `/app/frontend/src/portal-inteligencia/App.jsx` | Root del portal |
| `/app/frontend/src/pages/Layout.js` | Menú principal |
| `/app/frontend/src/HostRouter.jsx` | Router por subdominio |
| `/app/backend/modules/comercial/routes.py` | Queries existentes MPRO/Soft |
| `/app/backend/modules/comercial/repository.py` | Repositorio comercial |

---

## 7. NOTAS IMPORTANTES

1. **NO crear tablas SQL tipo `Roles`, `Companies`, `TenantID`** - Usar el esquema existente de EDARSAHUB
2. **NO usar MongoDB** para datos comerciales - Todo en EDARSAHUB SQL Server
3. **NO crear ETL externo** - La sincronización debe ser un job interno del scheduler
4. **NO usar conexiones LIVE** para dashboards - Usar datos sincronizados/cacheados
5. **Seguir el patrón de permisos existente** - `MODULO_ACCION`

---

*Documento generado: Junio 2026*
*Autor: Agente E1 - EDARSA HUB*
