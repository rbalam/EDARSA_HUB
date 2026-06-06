# AUDITORÍA TABLEROS KPIs FILTROS - INVENTARIO
## AUDITORIA-TABLEROS-KPIS-FILTROS-01

**Fecha inicio:** 2025-04-27  
**Estado:** EN PROGRESO - FASE 1 INVENTARIO  
**Auditor:** Agente E1

---

## HALLAZGO CRÍTICO INICIAL

### Problema identificado: Archivos usando `axios` directo en lugar de `api` centralizado

Los siguientes archivos usan `import axios from 'axios'` en lugar del cliente API centralizado (`@/lib/api`) que incluye el interceptor con `memoryToken` para autenticación:

| Archivo | Estado | Impacto |
|---------|--------|---------|
| `/app/frontend/src/pages/TableroEjecutivo.js` | ⚠️ AXIOS DIRECTO | KPIs muestran $0 porque no envía token |
| `/app/frontend/src/pages/Comercial.js` | ⚠️ AXIOS DIRECTO | Posible falla de auth |
| `/app/frontend/src/pages/AutorizacionCompras.js` | ⚠️ AXIOS DIRECTO | Posible falla de auth |
| `/app/frontend/src/pages/ExploradorBD.js` | ⚠️ AXIOS DIRECTO | Posible falla de auth |
| `/app/frontend/src/pages/CatalogoConsultas.js` | ⚠️ AXIOS DIRECTO | Posible falla de auth |

**Evidencia:** El Tablero Ejecutivo muestra "No hay datos disponibles" y todos los KPIs en $0, pero el endpoint `/api/comercial/tablero-ejecutivo` devuelve datos correctamente cuando se usa el token en Authorization header.

---

## INVENTARIO DE TABLEROS Y DASHBOARDS

### 1. TABLERO EJECUTIVO

| Campo | Valor |
|-------|-------|
| **Menú** | Tablero Ejecutivo |
| **Archivo Frontend** | `/app/frontend/src/pages/TableroEjecutivo.js` (929 líneas) |
| **Endpoint Backend** | `GET /api/comercial/tablero-ejecutivo` |
| **Archivo Backend** | `/app/backend/modules/comercial/routes.py` (línea 235) |
| **Fuente de Datos** | SoftRestaurant / ManagementPro vía SQL Server |
| **KPIs Visibles** | Ventas Consolidadas, PAX Total, Cheques, Proyección Mes, Unidades Conectadas |
| **Filtros** | Mes(es), Año(s), Tipo comparación |
| **Parámetros enviados** | `meses`, `anios`, `tipo_comparacion` |
| **Estado** | ⚠️ FALLA AUTH - Usa axios directo sin token |

#### KPIs del Tablero Ejecutivo

| KPI | Ubicación | Formato | Estado |
|-----|-----------|---------|--------|
| Ventas Consolidadas | Totales | Moneda ($) | FALLA - Muestra $0 |
| vs Mes | Totales | Porcentaje | FALLA - Muestra 0% |
| vs Año | Totales | Porcentaje | FALLA - Muestra 0% |
| PAX Total | Totales | Número | FALLA - Muestra 0 |
| Ticket Promedio | Totales | Moneda | FALLA - Muestra $0 |
| Cheques | Totales | Número | FALLA - Muestra 0 |
| Proyección Mes | Totales | Moneda | FALLA - Muestra $0 |
| Unidades Conectadas | Totales | Número | FALLA - Muestra 0 |

---

### 2. DASHBOARD (Inventarios)

| Campo | Valor |
|-------|-------|
| **Menú** | Inicio / Dashboard |
| **Archivo Frontend** | `/app/frontend/src/pages/Dashboard.js` (750 líneas) |
| **Endpoint Backend** | Múltiples: `/api/dashboard/*`, `/api/inventarios/*` |
| **Fuente de Datos** | SoftRestaurant / ManagementPro vía SQL Server + MongoDB cache |
| **KPIs Visibles** | Inventario, Insumos Pendientes, Costos |
| **Filtros** | Unidad de Negocio |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 3. COMERCIAL

| Campo | Valor |
|-------|-------|
| **Menú** | Comercial |
| **Archivo Frontend** | `/app/frontend/src/pages/Comercial.js` |
| **Endpoints Backend** | `/api/comercial/dashboard/{server_id}`, `/api/comercial/ventas-tiempo/{server_id}`, `/api/comercial/mesas/{server_id}`, `/api/comercial/ticket-perfecto/{server_id}`, `/api/comercial/metas/{server_id}`, `/api/comercial/reporte-pax/{server_id}`, `/api/comercial/precios-constantes/{server_id}` |
| **Fuente de Datos** | SoftRestaurant / ManagementPro vía SQL Server |
| **Estado** | ⚠️ POSIBLE FALLA AUTH - Usa axios directo |

#### Sub-tabs Comercial

| Tab | KPIs/Tablas | Filtros | Estado |
|-----|-------------|---------|--------|
| Dashboard | Ventas, PAX, Ticket Promedio, Cheques | Fecha, Servidor | PENDIENTE |
| Ticket Perfecto | Cumplimiento %, Top productos | Servidor | PENDIENTE |
| Metas | Metas vs Real | Servidor, Período | PENDIENTE |
| Ventas en Tiempo | Gráfica temporal | Servidor, Rango fechas | PENDIENTE |
| Mesas | Ocupación, Rotación | Servidor | PENDIENTE |
| Reporte PAX | Desglose por área | Servidor, Fecha | PENDIENTE |
| Precios Constantes | Comparativo precios | Servidor, Período | PENDIENTE |

---

### 4. FINANZAS

| Campo | Valor |
|-------|-------|
| **Menú** | Finanzas |
| **Archivo Frontend** | `/app/frontend/src/pages/Finanzas.js` + `/app/frontend/src/components/finanzas/*` |
| **Componentes** | FinanzasDashboard.jsx, FinanzasCuentasPorPagar.jsx, FinanzasPresupuestos.jsx, FinanzasControlIngresos.jsx |
| **Endpoints Backend** | `/api/finanzas/*` |
| **Fuente de Datos** | EDARSAHUB SQL Server |
| **Estado** | PENDIENTE VERIFICACIÓN |

#### Sub-tabs Finanzas

| Tab | Archivo | Estado |
|-----|---------|--------|
| Dashboard | FinanzasDashboard.jsx | PENDIENTE |
| Cuentas por Pagar | FinanzasCuentasPorPagar.jsx | PENDIENTE |
| Presupuestos | FinanzasPresupuestos.jsx | PENDIENTE |
| Control Ingresos | FinanzasControlIngresos.jsx | PENDIENTE |

---

### 5. COMPRAS

| Campo | Valor |
|-------|-------|
| **Menú** | Compras |
| **Archivo Frontend** | `/app/frontend/src/pages/Compras.js` + componentes |
| **Endpoints Backend** | `/api/compras/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 6. AUTORIZACIÓN COMPRAS

| Campo | Valor |
|-------|-------|
| **Menú** | Compras > Autorización |
| **Archivo Frontend** | `/app/frontend/src/pages/AutorizacionCompras.js` |
| **Endpoints Backend** | `/api/compras/detalle-pedido-manual/*`, `/api/compras/calculo-pedido` |
| **Estado** | ⚠️ POSIBLE FALLA AUTH - Usa axios directo |

---

### 7. RECURSOS HUMANOS

| Campo | Valor |
|-------|-------|
| **Menú** | Recursos Humanos |
| **Archivo Frontend** | `/app/frontend/src/pages/RecursosHumanos.js` + `/app/frontend/src/components/recursos-humanos/*` |
| **Componentes** | RhDashboard.jsx, RhColaboradores.jsx, RhNominas.jsx, RhAsistencia.jsx, RhReclutamiento.jsx, RhIncidencias.jsx, RhCatalogos.jsx |
| **Endpoints Backend** | `/api/rh/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 8. NÓMINAS

| Campo | Valor |
|-------|-------|
| **Menú** | Nóminas |
| **Archivo Frontend** | `/app/frontend/src/pages/Nominas.js` |
| **Endpoints Backend** | `/api/nominas/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 9. MIS TAREAS

| Campo | Valor |
|-------|-------|
| **Menú** | Mis Tareas |
| **Archivo Frontend** | `/app/frontend/src/pages/MisTareas.js` |
| **Endpoints Backend** | `/api/sistema/mis-tareas`, `/api/sistema/solicitudes` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 10. CENTRO DE CONTROL

| Campo | Valor |
|-------|-------|
| **Menú** | Centro de Control |
| **Archivo Frontend** | `/app/frontend/src/pages/CentroControl.jsx` + componentes |
| **Endpoints Backend** | `/api/centro-control/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 11. SCHEDULER

| Campo | Valor |
|-------|-------|
| **Menú** | Programación |
| **Archivo Frontend** | `/app/frontend/src/pages/Scheduler.jsx` |
| **Endpoints Backend** | `/api/scheduler/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 12. AUDITORÍAS PROGRAMADAS

| Campo | Valor |
|-------|-------|
| **Menú** | Auditorías |
| **Archivo Frontend** | `/app/frontend/src/pages/AuditoriasProgramadas.jsx` |
| **Endpoints Backend** | `/api/auditorias/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 13. EXPLORADOR BD

| Campo | Valor |
|-------|-------|
| **Menú** | Explorador BD |
| **Archivo Frontend** | `/app/frontend/src/pages/ExploradorBD.js` |
| **Endpoints Backend** | `/api/explorador/*` |
| **Estado** | ⚠️ POSIBLE FALLA AUTH - Usa axios directo |

---

### 14. CATÁLOGO CONSULTAS

| Campo | Valor |
|-------|-------|
| **Menú** | Catálogo SQL |
| **Archivo Frontend** | `/app/frontend/src/pages/CatalogoConsultas.js` |
| **Endpoints Backend** | `/api/catalogo-consultas/*` |
| **Estado** | ⚠️ POSIBLE FALLA AUTH - Usa axios directo |

---

### 15. USUARIOS

| Campo | Valor |
|-------|-------|
| **Menú** | Usuarios |
| **Archivo Frontend** | `/app/frontend/src/pages/Usuarios.js` |
| **Endpoints Backend** | `/api/users`, `/api/roles` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 16. CATÁLOGOS

| Campo | Valor |
|-------|-------|
| **Menú** | Catálogos |
| **Archivo Frontend** | `/app/frontend/src/pages/Catalogos.js` |
| **Endpoints Backend** | `/api/catalogos/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 17. SERVIDORES

| Campo | Valor |
|-------|-------|
| **Menú** | Servidores |
| **Archivo Frontend** | `/app/frontend/src/pages/Servidores.js` |
| **Endpoints Backend** | `/api/servers` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 18. ALERTAS

| Campo | Valor |
|-------|-------|
| **Menú** | Alertas |
| **Archivo Frontend** | `/app/frontend/src/pages/Alertas.js` |
| **Endpoints Backend** | `/api/alertas/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 19. REPORTES BI

| Campo | Valor |
|-------|-------|
| **Menú** | Reportes BI |
| **Archivo Frontend** | `/app/frontend/src/pages/ReportesBI.js` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 20. PROVEEDORES

| Campo | Valor |
|-------|-------|
| **Menú** | Proveedores |
| **Archivo Frontend** | `/app/frontend/src/pages/Proveedores.js` |
| **Endpoints Backend** | `/api/proveedores/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 21. PORTAL PROVEEDORES

| Campo | Valor |
|-------|-------|
| **Menú** | Portal Proveedores (externo) |
| **Archivo Frontend** | `/app/frontend/src/pages/PortalProveedores/*` (si existe) |
| **Archivo Backend** | `/app/backend/routes/portal_proveedores.py` |
| **Endpoints Backend** | `/api/portal/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 22. PROPINAS TPV

| Campo | Valor |
|-------|-------|
| **Menú** | Finanzas > Propinas |
| **Archivo Frontend** | `/app/frontend/src/components/PropinasTPV.jsx` |
| **Endpoints Backend** | `/api/finanzas/propinas/*` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 23. TESORERÍA CORTE Z

| Campo | Valor |
|-------|-------|
| **Menú** | Finanzas > Corte Z |
| **Archivo Frontend** | `/app/frontend/src/components/TesoreriaCorteZ.jsx` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 24. CONFIGURACIÓN ASIGNACIONES

| Campo | Valor |
|-------|-------|
| **Menú** | Asignaciones |
| **Archivo Frontend** | `/app/frontend/src/pages/ConfigAsignaciones.jsx` |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

### 25. OPERATIVO DASHBOARD

| Campo | Valor |
|-------|-------|
| **Menú** | Operaciones |
| **Archivo Frontend** | `/app/frontend/src/pages/OperativoDashboardPage.jsx` + componentes fase2_operativo |
| **Componentes** | OperativoDashboard.jsx, KPICards.jsx, TareaList.jsx, WorkflowList.jsx |
| **Estado** | PENDIENTE VERIFICACIÓN |

---

## RESUMEN DE ESTADO INICIAL

| Estado | Cantidad |
|--------|----------|
| ✅ REPARADO Y VERIFICADO | 2 |
| ✅ MIGRADO (pendiente verificación) | 3 |
| PENDIENTE VERIFICACIÓN | 20 |
| **TOTAL** | 25 |

---

## REPARACIÓN URGENTE COMPLETADA (2026-04-27)

Los 5 archivos que usaban `axios` directo han sido migrados a `api` centralizado:

| Archivo | Estado | Evidencia |
|---------|--------|-----------|
| TableroEjecutivo.js | ✅ VERIFICADO | KPIs cargan: $9.29M ventas, 9453 PAX |
| Comercial.js | ✅ VERIFICADO | Página carga correctamente |
| AutorizacionCompras.js | ✅ MIGRADO | Pendiente verificación completa |
| ExploradorBD.js | ✅ MIGRADO | Pendiente verificación completa |
| CatalogoConsultas.js | ✅ MIGRADO | Pendiente verificación completa |

---

## PRÓXIMOS PASOS

1. **URGENTE:** Migrar archivos de `axios` directo a `api` centralizado:
   - TableroEjecutivo.js
   - Comercial.js
   - AutorizacionCompras.js
   - ExploradorBD.js
   - CatalogoConsultas.js

2. Verificar cada tablero con usuario admin y usuario limitado

3. Validar filtros aplicados en backend

4. Documentar KPIs con formato incorrecto

---

**Última actualización:** 2025-04-27 05:10 UTC
