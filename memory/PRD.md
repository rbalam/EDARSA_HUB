# Edarsa Hub - PRD (Product Requirements Document)

## Original Problem Statement
ERP modular para gestionar múltiples sucursales con bases de datos SQL Server externas (SoftRestaurant y ManagmentPro/MPRO). Requiere tableros consolidados, módulos de Compras, Inventarios, Comercial, y herramientas de análisis con drill-down estilo Power BI.

## Core Requirements
1. Minimizar y controlar estrictamente el consumo de créditos
2. Separación estricta por sucursales
3. Drill-down profundo en KPIs (estilo Power BI)
4. Preparar la arquitectura visual y de BD para clientes "Standalone"

## Tech Stack
- **Frontend**: React + Shadcn UI + Tailwind CSS
- **Backend**: FastAPI + pytds (SQL Server connections)
- **Databases**: MongoDB (cache, config) + SQL Server externos (SoftRestaurant, MPRO)

---

## What's Been Implemented (as of April 6, 2026)

### ✅ Core Infrastructure
- Multi-server architecture with dynamic SQL Server connections
- MongoDB caching for network resilience
- JWT authentication with role-based access
- Sync status indicators for network state

### ✅ Módulo Comercial
- Dashboard de ventas con KPIs (Ventas, PAX, Ticket Promedio)
- Multiselección de años y meses con comparación histórica
- Datos de SoftRestaurant y MPRO
- **Análisis de Ventas a Precios Constantes** (Implementado April 7, 2026):
  - Compara ventas eliminando el efecto inflacionario
  - Modo Manual: selección libre de períodos actual y base
  - Modo Automático: año actual vs mismo mes año anterior
  - Granularidad: Por Categoría, Por Familia, Por Producto
  - KPIs: Ventas Actuales, Ventas Constantes, Efecto Precio, Productos Nuevos/Descontinuados
  - Productos In/Out: Nuevos usan precio actual, Descontinuados usan último precio
  - Tabla detallada con efecto precio por ítem
  - **Funciona con MPRO y SoftRestaurant** (queries corregidas para ambos sistemas)
  - **Crecimiento Real vs Año Anterior** (Completado April 7, 2026):
    - KPIs: Crecimiento Nominal, Crecimiento Real, Ventas Año Anterior, Diferencia Real
    - Compara automáticamente con el mismo periodo del año pasado
  - **Gráfico Histórico de 5 Años** (Completado April 7, 2026):
    - Gráfico de barras comparativo: Ventas Actuales vs Precios Constantes
    - Años: T-4 hasta T (últimos 5 años)
    - Tooltip con valores exactos
    - Leyenda de interpretación con efecto inflación % por año

### ✅ Módulo Compras
- Dashboard de compras por servidor/sucursal
- **MultiAnálisis** con drill-down:
  - Nivel 1: Proveedores con totales por mes
  - Nivel 2: Facturas del proveedor (solo MPRO)
  - Nivel 3: Productos de cada factura (solo MPRO)
- KPIs: Total Compras, Proveedores, Promedio
- Auto-actualización al cambiar filtros

### ✅ Módulo Inventarios
- Análisis de inventarios (inicial, movimientos, ventas, final, diferencias)
- Inventarios físicos multi-selección
- Filtros por Categoría, Familia, Subfamilia
- **Insumos Pendientes de Descargar** (SoftRestaurant):
  - Tabla `inventariopendiente` con JOIN a `insumos` y `gruposi`
  - KPIs: Total items, Cantidad, Valor
  - Filtros por Almacén (100, 200, 400)
  - Cálculo Pareto 80-20

### ✅ Explorador BD
- Consulta de tablas SQL Server
- Scripts SQL en "stand-by" para ejecución posterior por DBA
- CRUD de scripts guardados en MongoDB

### ✅ Tablero Ejecutivo
- KPIs consolidados de todas las sucursales
- Gráficos de tendencias

### ✅ Portal de Proveedores (NEW - April 6, 2026)
- **Subproyecto separado** en `/portal-proveedores`
- **Dashboard** conectado a datos reales de SQL Server:
  - KPIs: Total Facturado, Total Pagado, Saldo Pendiente, Facturas Pendientes
  - Filtros por Sistema y Sucursal
  - Resumen por Sistema con status de conexión
  - Saldo por Sucursal con desglose MPRO/SoftRestaurant
  - Facturas Pendientes con drill-down por sucursal
- **Autenticación**: Login/Registro por RFC con JWT
- **Mis Facturas**: Listado de facturas subidas
- **Subir Factura**: Carga de XML CFDI con validación
- **Carga Masiva**: Placeholder para carga múltiple
- **Mis Pagos**: Historial de pagos (placeholder)
- **Endpoints Backend**:
  - `/api/portal/auth/*` - Autenticación
  - `/api/portal/saldos` - Saldos reales desde SQL Server
  - `/api/portal/invoices` - CRUD de facturas
  - `/api/portal/admin/*` - Administración

### ✅ Administración de Proveedores en EDARSA HUB (NEW - April 6, 2026)
- Nueva sección: **Sistema → Portal Proveedores**
- Tabla de proveedores con filtros (Todos/Pendientes/Aprobados/Rechazados)
- Búsqueda por RFC, razón social, email
- Modal de aprobación con asignación de sucursales
- Botón directo al portal externo

---

## Prioritized Backlog

### P0 (Critical)
- [x] ~~Portal de Proveedores - Dashboard con datos reales~~ ✅
- [x] ~~Administración de Proveedores en EDARSA HUB~~ ✅
- [x] ~~Gráfico histórico 5 años + Crecimiento Real en Precios Constantes~~ ✅
- [ ] Drill-down Compras para SoftRestaurant (implementar queries)

### P1 (High Priority)
- [ ] Dashboard Comercial estilo Power BI (gráficos de líneas, distribución por área, top 10 productos)
- [ ] Módulo Seguridad y Monitoreo (log de logins, alertas de IPs)
- [ ] Rentabilidad con integración OpenTable
- [ ] Diseño visual del Portal coincida exactamente con capturas del usuario

### P2 (Medium Priority)
- [ ] Infraestructura de Presupuestos (Budgets CRUD)
- [ ] Módulo CRM (Captación Leads, estado cuenta)
- [ ] Módulo Comisionistas, Bonificaciones
- [ ] Exportación PDF, Excel, WhatsApp, Email

### Bloqueados
- [ ] Toast POS integration (requiere API Key)
- [ ] QuickBooks Online integration (requiere OAuth credentials)
- [ ] MarginEdge integration (requiere API Key)

---

## Architecture

```
/app/
├── backend/
│   ├── server.py                   # Monolito principal (~10,000 líneas)
│   ├── models/
│   │   └── portal_models.py        # Modelos Pydantic del Portal
│   └── routes/
│       └── portal_proveedores.py   # Endpoints API del portal
├── frontend/
│   └── src/
│       ├── App.js                  # Enrutador principal
│       ├── pages/
│       │   ├── Proveedores.js      # Administración de proveedores (NEW)
│       │   └── ...
│       └── portal/                 # Subproyecto Portal Proveedores
│           ├── App.jsx
│           └── pages/
│               ├── DashboardPage.jsx  # Dashboard con saldos reales
│               ├── LoginPage.jsx
│               ├── InvoicesPage.jsx
│               ├── UploadInvoicePage.jsx
│               ├── BatchUploadPage.jsx
│               └── PaymentsPage.jsx
└── memory/
    └── PRD.md
```

## Key Technical Concepts
- FastAPI con conexiones dinámicas a múltiples SQL Server usando `pytds`
- MongoDB collections: `servers`, `users`, `kpis_cache`, `portal_suppliers`, `portal_invoices`
- SoftRestaurant y MPRO tienen esquemas de BD diferentes
- Hot reload habilitado para desarrollo
- Portal Proveedores usa JWT separado con type="portal_supplier"

## Areas Needing Refactor
- `/app/backend/server.py` tiene >10,000 líneas - dividir en routers

## Known Issues
- Bug en "Rendimiento" para códigos duplicados en Insumos/Presentaciones (postponed)
- Arquitectura Local-First (IndexedDB) en evaluación - no tocar sin permiso
