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

## What's Been Implemented (as of April 3, 2026)

### ✅ Core Infrastructure
- Multi-server architecture with dynamic SQL Server connections
- MongoDB caching for network resilience
- JWT authentication with role-based access
- Sync status indicators for network state

### ✅ Módulo Comercial
- Dashboard de ventas con KPIs (Ventas, PAX, Ticket Promedio)
- Multiselección de años y meses con comparación histórica
- Datos de SoftRestaurant y MPRO

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

---

## Prioritized Backlog

### P0 (Critical)
- [ ] Drill-down Compras para SoftRestaurant (implementar queries para `compras` y `comprasdetalle`)

### P1 (High Priority)
- [ ] Dashboard Comercial estilo Power BI (gráficos de líneas, distribución por área, top 10 productos)
- [ ] Ventas sin inflación (valuación con precios año anterior)
- [ ] Módulo Seguridad y Monitoreo (log de logins, alertas de IPs)
- [ ] Rentabilidad con integración OpenTable

### P2 (Medium Priority)
- [ ] Infraestructura de Presupuestos (Budgets CRUD)
- [ ] Módulo CRM (Captación Leads, estado cuenta)
- [ ] Módulo Comisionistas, Bonificaciones
- [ ] Exportación PDF, Excel, WhatsApp, Email

### Bloqueados
- [ ] Toast POS integration (requiere API Key)
- [ ] QuickBooks Online integration (requiere OAuth credentials)
- [ ] MarginEdge integration (requiere API Key)
- [ ] Portal Proveedores (requiere código fuente)
- [ ] Bitácora Activos (requiere código fuente)

---

## Key Technical Concepts
- FastAPI con conexiones dinámicas a múltiples SQL Server usando `pytds`
- MongoDB collections: `servers`, `users`, `kpis_cache`, `script_logs`
- SoftRestaurant y MPRO tienen esquemas de BD diferentes
- Hot reload habilitado para desarrollo

## Areas Needing Refactor
- `/app/backend/server.py` tiene >10,000 líneas - dividir en routers

## Known Issues
- Bug en "Rendimiento" para códigos duplicados en Insumos/Presentaciones (postponed)
- Arquitectura Local-First (IndexedDB) en evaluación - no tocar sin permiso
