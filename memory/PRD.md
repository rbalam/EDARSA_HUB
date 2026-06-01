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

### Corrección de Enrutamiento Portal Inteligencia Comercial
**Problema**: La ruta `/inteligencia-comercial` redirigía incorrectamente a `/login`

**Causa raíz**: El catch-all `path="*"` dentro del `<Route path="/">` en React Router 6 interfería con rutas de portales externos definidas antes.

**Solución aplicada**:
1. Movido catch-all FUERA del Layout a nivel global de `<Routes>`
2. Creado componente `ProtectedRoute` para manejar auth de forma independiente
3. Eliminada verificación de auth redundante en `Layout.js`
4. Añadido timeout de 3s en `checkSession()` del portal para evitar bloqueos

**Archivos modificados**:
- `/app/frontend/src/App.js` - Reestructuración de rutas
- `/app/frontend/src/pages/Layout.js` - Removida verificación auth
- `/app/frontend/src/portal-inteligencia/App.jsx` - Timeout en checkSession
- `/app/frontend/src/components/ProtectedRoute.jsx` - Nuevo componente

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
