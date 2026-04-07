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
- **Selector de Tipo de Comparación** (Implementado April 7, 2026):
  - Botón toggle: "Días Equiv." vs "Mes Completo"
  - **Días Equivalentes**: Detecta automáticamente el último día con ventas en la BD y compara ese mismo número de días
  - **Mes Completo**: Compara vs el mes/año anterior completo
  - **Lógica inteligente de corte**: Si último día con venta = día 5 y estamos en día 6/7 → compara 1-5 vs 1-5
  - Se aplica a "vs Mes Ant" y "vs Año Ant"
  - Funciona con SoftRestaurant y MPRO
- **Análisis de Ventas a Precios Constantes** (Implementado April 7, 2026):
  - Compara ventas eliminando el efecto inflacionario
  - Modo Manual: selección libre de períodos actual y base
  - Modo Automático: año actual vs mismo mes año anterior
  - Granularidad: Por Categoría, Por Familia, Por Producto
  - KPIs: Ventas Actuales, Ventas Constantes, Efecto Precio, Productos Nuevos/Descontinuados
  - Productos In/Out: Nuevos usan precio actual, Descontinuados usan último precio
  - Tabla detallada con efecto precio por ítem
  - **Funciona con MPRO y SoftRestaurant** (queries corregidas para ambos sistemas)
  - **Cálculo de Ventas Unificado** (Completado April 7, 2026):
    - Ventas ahora coinciden exactamente con el Tablero Ejecutivo
    - SoftRestaurant: Usa `SUM(cheques.total)` como referencia
    - MPRO: Usa `SUM(Venta_Encabezado.Vn_Precio_Neto_Importe)` como referencia
    - Factor de ajuste aplicado a productos individuales para incluir propinas/impuestos
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
- **Detección automática de último día con ventas** (Implementado April 7, 2026):
  - Compara días equivalentes (1-5 vs 1-5 si último día con datos = día 5)
  - Aplica a todas las unidades automáticamente (SoftRestaurant + MPRO)
  - Corrige el cálculo de variaciones % vs Mes y vs Año

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

---

## Changelog

### April 7, 2026 - Reporte Comparativo de Auditoría
- **Nuevo**: Botón "Comparativo 4 Cortes" en Análisis de Inventarios
- **Backend**: Endpoint `/api/reports/export/comparativo-inventarios` para generar Excel con los últimos 4 cortes de inventario
- **Excel**: Muestra diferencias por SKU entre cortes consecutivos, total acumulado, y detección de patrones (FALTANTE/SOBRANTE CONSTANTE)
- **Frontend**: Botón verde esmeralda junto a "Generar Reporte"
- Cambio: Headers de tabla de inventarios ahora muestran "Qty" en lugar de "CANTIDAD"

### April 7, 2026 - Cache de Diferencias en MongoDB
- **Nuevo**: Colección `inventario_diferencias_detalle` en MongoDB para almacenar diferencias calculadas
- **Optimización**: Primera generación calcula y guarda en cache; siguientes generaciones usan cache (instantáneo)
- **Multi-almacén**: Soporta múltiples almacenes/comentarios en un solo reporte
- **MPRO**: Filtra por comentario (CAVA, BARRA, BODEGA) para comparar inventarios de misma naturaleza
- **Velocidad**: De ~5-10s (SQL Server) a ~0.3s (cache MongoDB)
- **Detección automática**: Si hay nuevos inventarios, recalcula y actualiza cache

### April 7, 2026 - Fix: Comparativo 4 Cortes Bug
- **Bug corregido**: El endpoint de exportación retornaba folios antiguos (2025) en lugar de recientes (2026)
- **Causa raíz**: La comparación de fechas en SQL Server (`Fi_Fecha <= 'YYYY-MM-DD'`) no funcionaba correctamente con formato string
- **Solución**: Usar `CONVERT(date, F.Fi_Fecha) <= CONVERT(date, '{fecha}')` en la query SQL
- **Frontend Fix**: Ahora envía `almacen_id` y `fecha` en `inventarios_finales_info` para guardar cache correctamente
- **Backend Fix**: Logging mejorado para depuración de cache
- **Aclaración Badge**: El número "1" en el botón representa almacenes seleccionados, no reportes cacheados (diseño intencionado)

### April 7, 2026 - Fix: Whiskys y Familias de COMPRA No Aparecían en Inventarios
- **Bug corregido**: Los Whiskys y otras familias (VODKAS, VINOS TINTOS) no aparecían en el reporte de análisis de inventarios
- **Causa raíz**: La query usaba `TOP 3000` con `ORDER BY Familia`, y familias que empiezan con W, V quedaban fuera del límite alfabético (3,856 productos pasaban el filtro)
- **Solución**: 
  - Eliminado `TOP 3000` y agregado filtro `EXISTS` que trae productos con:
    1. Inventario físico en folios seleccionados
    2. O movimientos en el período (entradas/salidas/traspasos)
    3. O ventas en el período (a través de recetas Producto_Kit)
  - Cambiado `NOT IN` a `NOT EXISTS` para mejor compatibilidad con SQL Server
  - Corregido error `strptime() argument 1 must be str, not None` con fallbacks de fecha
- **Resultado**: De 288 productos/0 Whiskys a 418 productos/21 Whiskys (ahora incluye productos con movimientos pero sin inventario capturado)

### April 7, 2026 - Fix: Color Azul Chillante en Modal de Auditoría
- **Problema**: El header del modal "Generar Informe de Auditoría" usaba un azul eléctrico (blue-600/700) que rompía con la paleta de colores del proyecto
- **Solución**: Cambio a tonos zinc (zinc-800/900) consistentes con el resto del proyecto
- **Cambios aplicados**:
  - Header del modal de auditoría: `from-blue-600 to-blue-700` → `from-zinc-800 to-zinc-900`
  - Tabla de Insumos Pendientes: `bg-blue-800` → `bg-zinc-800`, `bg-blue-700` → `bg-zinc-700`
  - Hover de filas: `hover:bg-blue-50` → `hover:bg-zinc-50`
- **Nota**: Los botones de acción (Guardar Informe, Generar Informe) permanecen en azul según preferencia del usuario

### April 7, 2026 - Tabla Insumos Pendientes en Dashboard de Inventarios
- **Problema**: La tabla de "Insumos Pendientes a Descargar" no aparecía en el Dashboard de Inventarios
- **Solución**: Integrada la tabla directamente en el componente `Dashboard.js`
- **Funcionalidad**:
  - Se carga automáticamente al seleccionar un servidor SoftRestaurant
  - KPIs: Total Insumos, Cantidad Total, Valor Total
  - Filtros por Almacén (Todos, 100, 200, etc.)
  - Tabla completa con: No, ALM, GRUPO, CODIGO, INSUMO, CANTIDAD, UM, COSTO, TOTAL, 80-20
  - Items con Pareto ≤80% resaltados en amarillo
  - Fila de totales sticky al final
- **Pendiente**: Implementar misma funcionalidad para MPRO (usuario proporcionará query SQL)

### April 7, 2026 - Fase 2 RRHH: UI Completa con Modales
- **Implementado**: Módulo completo de Recursos Humanos con CRUD funcional
- **Modal Nuevo/Editar Colaborador**:
  - Campos: Nombre Completo, CURP, RFC, CLABE Bancaria, Sucursal, Puesto, Estatus Laboral
  - Validación de campos requeridos
  - Creación y actualización via API
- **Modal Nueva Incidencia**:
  - Campos: Colaborador, Tipo de Incidencia, Fecha, Monto, Unidades
  - 10 tipos de incidencia: Falta, Retardo, Bono, Descuento, Horas Extra, Vacaciones, Incapacidad, Permiso, Comision, Otro
- **Modal Detalle Colaborador**:
  - Información completa del expediente
  - Últimas incidencias
  - Últimas asistencias
- **Modal Importar Excel** (NUEVO):
  - Instrucciones de formato (RFC/ID, Tipo, Fecha, Monto, Unidades)
  - Botón "Descargar Plantilla" genera Excel con formato y ejemplos
  - Selector de archivo con validación .xlsx/.xls
  - Procesamiento de filas con mapeo RFC → ColaboradorID
  - Reporte de importación con errores detallados
  - Endpoints: `/api/rrhh/incidencias/importar-excel`, `/api/rrhh/incidencias/plantilla-excel`
- **Acciones en tabla de colaboradores**:
  - Ver detalle (ojo azul)
  - Editar (lápiz amarillo)
  - Nueva incidencia (triángulo púrpura)
  - Dar de baja (trash rojo)
- **Estilos actualizados**: Headers de tabla en zinc-800 (consistente con el resto del proyecto)
- **Nota**: Las tablas SQL de RRHH están integradas pero vacías en la BD de producción

### April 7, 2026 - Fase 3 Finanzas: Módulo de Control Presupuestal
- **Implementado**: Módulo completo de Finanzas con Dashboard y CRUD de presupuestos
- **Backend** (`/app/backend/server.py`):
  - `GET /api/finanzas/dashboard`: KPIs financieros (Ingresos, Egresos, Utilidad, Margen) con comparativo vs mes anterior
  - `GET /api/finanzas/presupuestos`: Lista presupuestos con filtros (año, mes, sucursal, categoría)
  - `POST /api/finanzas/presupuestos`: Crear nuevo presupuesto
  - `PUT /api/finanzas/presupuestos/{id}`: Actualizar presupuesto
  - `DELETE /api/finanzas/presupuestos/{id}`: Eliminar presupuesto
  - `GET /api/finanzas/categorias`: Listar categorías únicas de presupuestos
  - `POST /api/finanzas/registrar-movimiento`: Registrar movimiento y actualizar ejecutado
  - `GET /api/finanzas/script-inicializacion`: Obtener script SQL para crear tablas
- **Frontend** (`/app/frontend/src/pages/Finanzas.js`):
  - **Dashboard**: KPIs con variación vs mes anterior, Comparativo por Sucursal
  - **Presupuestos**: Tabla CRUD con filtros, botón "Ver Script SQL"
  - **Modal Nuevo/Editar Presupuesto**: Sucursal, Tipo, Categoría, Subcategoría, Mes, Año, Monto, Notas
  - **Modal Script SQL**: Instrucciones paso a paso + Script completo con botón "Copiar"
- **Estructura SQL** (Tabla `Finanzas_Presupuestos`):
  - PresupuestoID, SucursalID, Categoria, SubCategoria, Tipo, Monto_Presupuestado, Monto_Ejecutado, Anio, Mes, Notas
- **Nota**: Las tablas deben crearse ejecutando el script SQL en EDARSA HUB via "Explorador BD"

### April 7, 2026 - Fase 4 Finanzas: Gráficos y Reportes Avanzados
- **Implementado**: Dashboard con gráficos interactivos y pestaña de Reportes
- **Gráficos agregados** (`/app/frontend/src/pages/Finanzas.js`):
  - Gráfico de Barras: "Presupuesto vs Ejecutado por Sucursal" (Recharts BarChart)
  - Gráfico de Pie: "Distribución de Egresos por Sucursal" (Recharts PieChart)
  - Alertas de Sobregiro: Notificación cuando egresos > presupuesto
- **Pestaña Reportes**:
  - Reporte Financiero con encabezado y botón "Imprimir"
  - Resumen Ejecutivo: Total Ingresos, Total Egresos, Utilidad Neta, Margen
  - Comparativo por Sucursal con gráfico de barras (Ingresos, Egresos, Utilidad)
  - Detalle por Sucursal: Tabla con variaciones porcentuales
  - Pie de página con fecha de generación

### April 7, 2026 - Fase 5 RRHH: Módulo de Reclutamiento (Vacantes y Candidatos)
- **Backend** (`/app/backend/server.py`):
  - `GET/POST/PUT/DELETE /api/rrhh/vacantes`: CRUD de vacantes
  - `GET/POST/PUT/DELETE /api/rrhh/candidatos`: CRUD de candidatos
  - `GET /api/rrhh/reclutamiento/dashboard`: Métricas de reclutamiento
  - `GET /api/rrhh/reclutamiento/script-inicializacion`: Script SQL para crear tablas
- **Frontend** (`/app/frontend/src/pages/RecursosHumanos.js`):
  - Nueva pestaña **"Reclutamiento"**
  - KPIs: Vacantes Abiertas, Total Candidatos, Pendientes Revisión, Contratados
  - Lista de Vacantes con indicador de candidatos
  - Tabla de Candidatos con cambio de estatus en línea (dropdown)
  - **Modal Nueva Vacante**: Título, Sucursal, Puesto, Descripción, Requisitos, Salarios, Tipo Contrato
  - **Modal Nuevo Candidato**: Vacante, Nombre, Email, Teléfono, URL del CV
  - **Modal Script SQL**: Con instrucciones y botón copiar
- **Estructura SQL** (Tablas `RH_Vacantes` y `RH_Candidatos`):
  - RH_Vacantes: VacanteID, SucursalID, PuestoID, Titulo, Descripcion, Requisitos, Salario_Min, Salario_Max, Tipo_Contrato, Estatus, Fechas
  - RH_Candidatos: CandidatoID, VacanteID, Nombre_Completo, Email, Telefono, CV_URL, Estatus, Puntuacion, Notas, Fecha_Entrevista
- **Estatus de Candidato**: Recibido, En Revision, Entrevista Programada, Entrevistado, Seleccionado, Rechazado, Contratado

### April 7, 2026 - Insumos Pendientes MPRO (Dashboard Inventarios)
- **Implementado**: Soporte de "Insumos Pendientes a Descargar" para ManagmentPro
- **Backend** (`/app/backend/server.py`):
  - Endpoint `/api/inventarios/pendientes/{server_id}` ahora soporta ambos sistemas
  - SoftRestaurant: Usa tabla `inventariopendiente`
  - MPRO: Calcula diferencia entre ventas/consumos y existencias teóricas
- **Query MPRO**: Guardada en MongoDB (`catalogos_sql.mpro_insumos_pendientes`)
  - Compara `venta * producto_kit` vs `movimiento`
  - Filtra por categorías (0001,0002,0004) y departamentos (0003,0004,0007,0002)
  - Solo muestra items con diferencia > 0 (consumido > existencia)
  - Usa periodo operativo abierto (Pr_Compras = 'NO')
- **Columnas retornadas**:
  - almacen, codigo, categoria, grupo, insumo, unidad
  - cantidad_vendida, existencia, diferencia (pendiente)
  - costo, total, pareto (80-20)

### April 7, 2026 - Incidencias Clasificadas (Ingresos/Descuentos)
- **Implementado**: Clasificación de incidencias por tipo (suma o resta al salario)
- **INGRESOS (+)**: Bono, Horas Extra, Comisión, Incentivo, Gratificación
- **DESCUENTOS (-)**: Falta, Retardo, Descuento, Vacaciones, Incapacidad, Permiso, Préstamo, Otro Descuento
- **UI Mejorada**:
  - Dropdown con optgroups separados (verde para +, rojo para -)
  - Indicador visual al seleccionar: "Este tipo SUMA/RESTA al salario"
  - Campo Monto con borde verde/rojo según tipo
  - Tabla de incidencias con badge +/- coloreado y monto con signo
