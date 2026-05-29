# CRM COMERCIAL ENTERPRISE - EDARSA HUB

## Problema Original
Construir el CRM COMERCIAL ENTERPRISE y módulos satélite integrados al ecosistema EDARSA HUB con MS SQL Server como cerebro absoluto. CERO dependencias de MongoDB.

## Arquitectura
- **Frontend**: React (`/app/frontend/src/`)
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

### 🔄 EN PROGRESO
- Integración de componentes Frontend a rutas principales React

---

## Backlog Priorizado

### P0 - Crítico
- (ninguno pendiente)

### P1 - Alta Prioridad
1. Integrar paneles CRM a rutas React
2. Motor de Rentabilidad (Costos y Márgenes)
3. COSTOS-ALERTAS-001-E — Motor evaluación margen
4. COSTOS-ALERTAS-001-F — Job/scheduler envío controlado

### P2 - Media Prioridad
- MIGRACION-FRONTEND-COMPETIDORES-ENTERPRISE

### P3 - Backlog
- FASE 0-9 Arquitectura Integral Operativa (Desmockización total)

---

## Tablas CRM en EDARSAHUB
- `CRM_Cuentas`
- `CRM_ClientesSolicitudesAlta`
- `CRM_Oportunidades` (47 columnas, Enterprise)
- `CRM_OportunidadesHistorial` ✅ NEW
- `Venta_Remisiones`
- `Usuario_Roles`

## Endpoints Activos
- `GET /api/crm/cuentas`
- `POST /api/crm/cuentas`
- `GET /api/crm/clientes/solicitudes`

## Credenciales Test
- `admin@inventario.com` / `admin123`
- `ricardo@edarsa.com.mx` / `Asdf1478@@`
