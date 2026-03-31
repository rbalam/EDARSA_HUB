# Edarsa Hub - PRD (Product Requirements Document)

## Original Problem Statement
Aplicación web ERP modular para gestionar múltiples sucursales con bases de datos SQL Server externas (SoftRestaurant y ManagementPro/MPRO). Requiere tableros consolidados, módulos de Compras, Inventarios, Comercial, y herramientas de análisis con drill-down.

## Core Requirements
1. **Minimizar y controlar estrictamente el consumo de créditos** - NUNCA ejecutar tareas sin autorización explícita
2. **Separación estricta por sucursales** - Cada sucursal tiene su propia base de datos
3. **Drill-down profundo en KPIs** - Permitir análisis detallado de cualquier métrica
4. **Arquitectura preparada para clientes "Standalone"** - Preparar BD para clientes autónomos

## User Personas
- **Administrador**: Acceso completo a todos los módulos y configuraciones
- **Gerente de Sucursal**: Acceso a su sucursal específica, reportes y auditorías
- **Operador de Compras**: Módulo de compras, requisiciones, inventarios

## Tech Stack
- **Frontend**: React + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python
- **Database**: MongoDB (app data) + SQL Server externo (pytds) para SoftRestaurant/MPRO
- **Auth**: JWT-based authentication

## Architecture
```
/app/
├── backend/
│   └── server.py           # Monolito (>9000 líneas) - TODO: Dividir en rutas
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Compras.js  # Auditoría operativa, cálculos, modales
│       │   ├── Reportes.js # Análisis de inventarios
│       │   └── ...
└── memory/
    └── PRD.md
```

## Key Business Logic
- **Normalización de Unidades**: TODO se convierte a unidad mínima (Insumos) en el backend usando "rendimiento"
- **Inventarios**: Comparación entre inventarios físicos iniciales y finales
- **Días de Inventario**: Cálculo dinámico con objetivo editable por SKU
- **Captura Manual**: Permite inventario físico directo en la tabla

## Key API Endpoints
- `POST /api/compras/auditoria-operativa` - Procesa múltiples inventarios, normaliza a Insumos y calcula KPIs
- `POST /api/compras/detalle-movimientos/{server_id}` - Drill-down de compras
- `POST /api/compras/detalle-consumos/{server_id}` - Drill-down de salidas/ventas usando recetas

## DB Schema (SQL Server External)
- `movtosalmacen`, `movsinv` - Movimientos de almacén
- `insumosdetalle`, `insumospresentacionesdetalle` - Detalles de insumos/presentaciones con costos
- `cheqdet` - Productos vendidos
- `recetasalmacenes` - Recetas (qué insumos gasta cada venta)
- `invfisicomovtos` - Movimientos de inventario físico

---

# CHANGELOG

## 2025-03-31
- **FIXED**: Error de sintaxis en `Compras.js` - código JSX duplicado/corrupto eliminado (~260 líneas)
- **VERIFIED**: Layout compacto de formulario de Auditoría funcionando correctamente
- **ADDED**: Badges de folios de requisiciones seleccionadas (estilo igual a inventarios)
- **IDENTIFIED**: Bug de rendimiento incorrecto cuando código existe como INSUMO y PRESENTACIÓN (ej: B070033) - pendiente corregir

## Previous Session (before fork)
- ✅ Bug de validación por filtros cacheados en Auditoría de Compras
- ✅ Filtro dinámico para Inventarios Finales (solo fechas >= Iniciales)
- ✅ Corrección SQL "Invalid column name 'referencia'" para base LA ESTELAR
- ✅ Separación de columnas de unidades (Principal vs Alternativa/Paréntesis)
- ✅ Queries para costos exactos (`insumosdetalle.costo`, `insumospresentacionesdetalle.costo`)
- ✅ Query de Consumos con `cheqdet` y `recetasalmacenes`
- ✅ Normalización total de unidades (backend convierte todo a INSUMOS)
- ✅ Captura manual de Inventario Físico en tabla
- ✅ Días de inventario objetivo ("Días Obj") editable por SKU
- ✅ Columna "Ajuste" (recomendación de compra +/-)
- ✅ Reorganización compacta del formulario de filtros

---

# ROADMAP

## P0 - Critical
- [x] Fix error de sintaxis en Compras.js

## P1 - High Priority
- [ ] Tablero de Compras estilo Power BI (selector multi-mes, tabla proveedores, gráfico)
- [ ] Filtro "Gasto" vs "Venta" en Análisis de Inventario MPRO (BLOCKED - esperando confirmación del usuario)
- [ ] Módulo Comercial - "Ventas sin inflación" (Valuación con precios año anterior)
- [ ] Módulo Rentabilidad - Integración con OpenTable y conciliación PAX

## P2 - Medium Priority
- [ ] Infraestructura de Presupuestos (Budgets) - Las comparativas financieras muestran 0
- [ ] Standalone DB (Opción 2) - BLOCKED (Esperando scripts SQL del usuario)
- [ ] Módulo CRM (Captación Leads, estado cuenta)
- [ ] Módulo Comisionistas, Bonificaciones
- [ ] Botones de Exportación (PDF, Excel, WA, Email)

## P3 - Low Priority / Technical Debt
- [ ] Refactorización de `server.py` (dividir en rutas/módulos)
- [ ] Refactorización de `Compras.js` (dividir en componentes más pequeños)

---

## Known Issues
- **Timeout de red**: Conexiones inestables al servidor del cliente (`Adaptive Server is unavailable`) - NO INTENTAR ARREGLAR, es infraestructura del cliente
