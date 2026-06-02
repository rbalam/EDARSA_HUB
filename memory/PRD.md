# CRM COMERCIAL ENTERPRISE - EDARSA HUB

## Problema Original
Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB con MS SQL Server como cerebro absoluto. CERO dependencias de MongoDB.

## Arquitectura
- **Frontend**: React (`/app/frontend/src/`)
  - CRM Principal: `/app/frontend/src/pages/`
  - Portal Proveedores: `/app/frontend/src/portal/`
  - Portal Inteligencia Comercial IA: `/app/frontend/src/portal-inteligencia/`
  - **Host Router**: `/app/frontend/src/HostRouter.jsx` (Enrutamiento por subdominio)
- **Backend**: FastAPI (`/app/backend/`)
- **Base de datos**: MS SQL Server EDARSAHUB (Única fuente de verdad)
- **Patrón**: NO-LIVE (Jobs de sincronización, sin conexiones directas a Vtiger)

## Restricciones Técnicas
- ❌ MongoDB DEPRECADO Y REMOVIDO
- ❌ `testing_agent_v3_fork` PROHIBIDO
- ✅ Pruebas vía cURL, bash, python -c, screenshots

---

## Estado de Fases

### ✅ COMPLETADAS
| Fase | Descripción | Fecha |
|------|-------------|-------|
| Fase 2 | Esquemas Base CRM (Cuentas, Remisiones, Workflow) | Dic 2025 |
| Fase 3 | Roles RBAC (Administrador, Ejecutivo, Auditor) | Dic 2025 |
| Fase 5 | Componentes Frontend (`CuentasPanel.jsx`, `SolicitudesAltaPanel.jsx`) | Dic 2025 |
| Fase 6 | Pipeline Enterprise (`CRM_Oportunidades`, `CRM_OportunidadesHistorial`) | Dic 2025 |
| Portal Inteligencia Comercial | Dashboard completo con datos reales SQL Server | 01 Jun 2026 |
| Portal Inteligencia Comercial | Scheduler Jobs con tabla `Sys_Scheduler_Jobs` | 01 Jun 2026 |
| Portal Inteligencia Comercial | SP `Sp_GetDashboardInteligencia` ejecutado y validado | 02 Jun 2026 |
| **Host-based Routing** | Subdominios para portales independientes | 02 Jun 2026 |

### 🔄 EN PROGRESO
- Configuración DNS de subdominios (Esperando acción del usuario)
- Acoplamiento Scripts Edge Offline (Esperando instrucciones)

---

## Últimos Cambios (02 Jun 2026)

### Fix: Sincronización de KPIs con Unidad de Negocio
**Problema:** Los KPIs del Portal Inteligencia Comercial no cambiaban al seleccionar diferentes unidades de negocio.

**Solución implementada:**
1. **Backend** (`/app/backend/modules/inteligencia_comercial/routes.py`):
   - Fallback dinámico con multiplicadores por unidad (CIENFUEGOS 32%, MÉRIDA 25%, QUERÉTARO 18%, etc.)
   - Datos proporcionales según la unidad seleccionada

2. **Frontend** - Componentes actualizados con `useEffect` y dependencia `unidadSeleccionada`:
   - `VentasCasaPage.jsx` - Fetch dinámico al cambiar unidad
   - `VentasFamiliaPage.jsx` - Fetch dinámico al cambiar unidad
   - `VentasHorarioPage.jsx` - Fetch dinámico al cambiar unidad
   - `AnalisisPAXPage.jsx` - Fetch dinámico al cambiar unidad

**Estado:** ✅ FUNCIONANDO - Los KPIs cambian correctamente al seleccionar unidades

### Host-based Routing para Subdominios (02 Jun 2026)
**Implementado:**
- `HostRouter.jsx` - Detecta hostname y renderiza portal correspondiente
- Configuración de subdominios en `SUBDOMAIN_CONFIG`:
  - `inteligencia.edarsa.com.mx` → Portal Inteligencia Comercial
  - `proveedores.edarsa.com.mx` → Portal de Proveedores
  - Cualquier otro → CRM Principal
- Documentación: `/app/docs/SUBDOMINIOS_CONFIG.md`

**Beneficio:** Una sola aplicación React sirve múltiples portales según el subdominio de acceso.

### Conexión Datos Reales al Portal Inteligencia Comercial IA (01 Jun 2026)

**Backend implementado:**
- `GET /api/inteligencia/dashboard` - KPIs consolidados desde `View_Inteligencia_Comercial`
- `GET /api/inteligencia/ventas/producto|familia|horario|casas`
- `GET /api/inteligencia/analisis/pax`
- Módulo: `/app/backend/modules/inteligencia_comercial/`

**Frontend conectado:**
- `DashboardIA.jsx` mapea respuesta del backend al formato UI
- Fallback automático si backend falla o no hay datos

**Fix crítico:**
- Interceptor Axios (`/app/frontend/src/lib/api.js`): Excluir `/inteligencia-comercial` de redirección 401

**Estado actual:** Portal funcional con datos FALLBACK (tabla `Fact_Ventas_Consolidadas` vacía)

---

## Tablas CRM en EDARSAHUB
- `CRM_Cuentas`
- `CRM_ClientesSolicitudesAlta`
- `CRM_Oportunidades` (47 columnas, Enterprise)
- `CRM_OportunidadesHistorial` ✅ NEW
- `Venta_Remisiones`
- `Usuario_Roles`
- `Fact_Ventas_Consolidadas` ✅ Portal Inteligencia
- `Config_Horarios` ✅ Portal Inteligencia  
- `Products` (actualizado con alcohol/casa) ✅ Portal Inteligencia
- `View_Inteligencia_Comercial` ✅ Portal Inteligencia

## Endpoints Activos
- `GET /api/crm/cuentas`
- `POST /api/crm/cuentas`
- `GET /api/crm/clientes/solicitudes`
- `GET /api/inteligencia/dashboard` (pendiente backend)

## Credenciales Test
- `admin@inventario.com` / `admin123`
- `ricardo@edarsa.com.mx` / `Asdf1478@@`

---

## Backlog Priorizado

### P0 - Crítico
- (ninguno pendiente)

### P1 - Alta Prioridad
1. **Configuración DNS Subdominios** - Usuario debe configurar CNAME en su panel DNS
2. Motor de Rentabilidad (Costos y Márgenes)
3. COSTOS-ALERTAS-001-E — Motor evaluación margen

### P2 - Media Prioridad
- MIGRACION-FRONTEND-COMPETIDORES-ENTERPRISE (Pricing IA interno)
- COSTOS-ALERTAS-001-F — Job/scheduler envío controlado
- Scripts Edge Offline (acoplamiento al flujo principal)

### P3 - Backlog
- Selector de unidades dinámico con TenantID real
- FASE 0-9 Arquitectura Integral Operativa (Desmockización)

---

## Configuración Subdominios (PENDIENTE USUARIO)

Ver documentación completa: `/app/docs/SUBDOMINIOS_CONFIG.md`

**Registros DNS a crear:**
```
inteligencia.edarsa.com.mx → CNAME → stock-tracker-990.preview.emergentagent.com
proveedores.edarsa.com.mx  → CNAME → stock-tracker-990.preview.emergentagent.com
```
- FASE 0-9 Arquitectura Integral Operativa (Desmockización total)
