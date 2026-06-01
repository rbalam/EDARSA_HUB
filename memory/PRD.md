# CRM COMERCIAL ENTERPRISE - EDARSA HUB

## Problema Original
Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB con MS SQL Server como cerebro absoluto. CERO dependencias de MongoDB.

## Arquitectura
- **Frontend**: React (`/app/frontend/src/`)
  - CRM Principal: `/app/frontend/src/pages/`
  - Portal Proveedores: `/app/frontend/src/portal/`
  - Portal Inteligencia Comercial IA: `/app/frontend/src/portal-inteligencia/`
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
| Portal Inteligencia Comercial | Estructura base, tablas DB, enrutamiento corregido | 01 Jun 2026 |

### 🔄 EN PROGRESO
- Portal Inteligencia Comercial IA - Desarrollo de páginas internas (VentasProducto, VentasFamilia, etc.)
- Integración de componentes Frontend a rutas principales React

---

## Últimos Cambios (01 Jun 2026)

### Conexión Datos Reales al Portal Inteligencia Comercial IA

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
1. **Portal Inteligencia Comercial** - Crear endpoint backend `/api/inteligencia/dashboard`
2. **Portal Inteligencia Comercial** - Conectar dashboard con `View_Inteligencia_Comercial`
3. Motor de Rentabilidad (Costos y Márgenes)
4. COSTOS-ALERTAS-001-E — Motor evaluación margen

### P2 - Media Prioridad
- MIGRACION-FRONTEND-COMPETIDORES-ENTERPRISE
- COSTOS-ALERTAS-001-F — Job/scheduler envío controlado

### P3 - Backlog
- Scripts Edge Offline (acoplamiento al flujo principal)
- FASE 0-9 Arquitectura Integral Operativa (Desmockización total)
