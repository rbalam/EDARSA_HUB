# DIAGNÓSTICO ARQUITECTÓNICO - FASE 1A
## Módulo: Comercial / Ventas

**Fecha:** 2026-05-24
**Arquitecto:** E1 (Agente Senior ERP)
**Estado:** DIAGNÓSTICO PASIVO COMPLETADO

---

## 1. DIAGNÓSTICO PASIVO

### 1.1 Módulos Frontend Existentes

| Ruta | Componente | Estado |
|------|------------|--------|
| `/comercial` | `Comercial.js` | **BLINDADO** - No modificar |
| `/crm/dashboard` | `CRMDashboard.jsx` | Activo |
| `/crm/cuentas` | `CuentasPage.jsx` | Activo |
| `/crm/solicitudes-alta` | `SolicitudesAltaPage.jsx` | Activo |
| `/crm/cotizaciones` | `CotizacionesPage.jsx` | Activo |
| `/crm/pedidos` | `PedidosPage.jsx` | Activo |
| `/crm/remisiones` | `RemisionesPage.jsx` | Activo |
| `/crm/leads` | `LeadsPage.jsx` | Activo |
| `/crm/oportunidades` | `OportunidadesPage.jsx` | Activo |
| `/crm/pipeline` | `PipelinePage.jsx` | Activo |

### 1.2 Endpoints Backend Existentes

**Módulo `/api/crm/` (CRM Comercial):**
- `GET /api/crm/cuentas` - Listar cuentas
- `POST /api/crm/cuentas` - Crear cuenta
- `GET /api/crm/cuentas/{id}` - Detalle cuenta
- `POST /api/crm/cuentas/{id}/ligar-cliente` - Ligar a cliente
- `GET /api/crm/clientes` - Listar clientes
- `GET /api/crm/clientes/solicitudes` - Solicitudes de alta
- `POST /api/crm/clientes/solicitudes` - Nueva solicitud
- `POST /api/crm/clientes/solicitudes/{id}/enviar` - Enviar solicitud
- `POST /api/crm/clientes/solicitudes/{id}/autorizar` - Autorizar
- `POST /api/crm/clientes/solicitudes/{id}/rechazar` - Rechazar
- `GET /api/crm/actividades` - Listar actividades
- `POST /api/crm/actividades` - Crear actividad
- `POST /api/crm/actividades/{id}/cerrar` - Cerrar actividad
- `GET /api/crm/cotizaciones` - Listar cotizaciones
- `GET /api/crm/cotizaciones/{id}` - Detalle cotización
- `POST /api/crm/cotizaciones` - Nueva cotización
- `POST /api/crm/cotizaciones/{id}/enviar` - Enviar
- `POST /api/crm/cotizaciones/{id}/aprobar` - Aprobar

**Módulo `/api/crm/automation/` (Automatización):**
- `GET /api/crm/automation/reglas` - Reglas
- `POST /api/crm/automation/reglas` - Crear regla
- `GET /api/crm/automation/sla/verificar` - Verificar SLA
- `GET /api/crm/automation/estadisticas` - Estadísticas
- `POST /api/crm/automation/ejecutar/cambio-etapa` - Trigger manual

**Módulo `/api/comercial/` (Dashboard Ventas):**
- `GET /api/comercial/dashboard/{server_id}` - Dashboard KPIs
- `GET /api/comercial/ticket-perfecto/{server_id}` - Ticket perfecto
- `GET /api/comercial/metas/{server_id}` - Metas de ventas
- `GET /api/comercial/ventas-tiempo/{server_id}` - Ventas por hora/día
- `GET /api/comercial/detalle-movimientos/{server_id}` - Drill-down

### 1.3 Tablas EDARSAHUB SQL Existentes

**Clientes y Ventas:**
- `Cliente_Catalogo` (2 registros)
- `Cliente_Contactos`
- `Cliente_Direcciones`
- `Cliente_Grupos`
- `Venta_Cotizaciones` (2 registros)
- `Venta_CotizacionesDetalle`
- `Venta_CotizacionesEstatus`
- `Venta_Pedidos` (2 registros)
- `Venta_PedidosDetalle`
- `Venta_PedidosEstatus`
- `Venta_Remisiones` (2 registros)
- `Venta_RemisionesDetalle`
- `Venta_RemisionesHistorial`
- `Venta_ListasPrecios` (1 registro)
- `Venta_ListasPreciosDetalle`
- `Venta_CondicionesPago`
- `Venta_FormaPago`
- `Venta_Estatus`

**CRM:**
- `CRM_Cuentas`
- `CRM_Leads`
- `CRM_Oportunidades`
- `CRM_Oportunidades_HistorialEtapas`
- `CRM_Oportunidad_Contactos`
- `CRM_Oportunidad_Documentos`
- `CRM_Actividades`
- `CRM_Tareas`
- `CRM_Contratos`
- `CRM_Propuestas`
- `CRM_ClientesSolicitudesAlta`
- `CRM_ClientesSolicitudesAltaHistorial`
- `CRM_Config_Pipelines`
- `CRM_Config_PipelineEtapas`
- `CRM_Automation_Reglas`
- `CRM_Automation_Log`
- `CRM_Triggers`
- `CRM_Trigger_Log`
- `CRM_Integracion_*` (Conectores, Mapeo, SyncLog)
- `CRM_Staging_*` (Cuentas, Leads, Oportunidades)
- `CRM_Cat_*` (18 catálogos)

**Comercial KPIs (Sincronización):**
- `Comercial_KPIs_Diarios_v2`
- `Comercial_KPIs_Mensuales_v2`
- `Comercial_KPIs_Historico`
- `Comercial_SyncLog_v2`
- `Comercial_Ventas_Dia_Abiertas_v2`

### 1.4 Permisos RBAC Existentes

**Módulos registrados en `Usuario_Modulos`:**
- `crm` - CRM
- `crm.dashboard` - Dashboard CRM
- `crm.cuentas` - Cuentas
- `crm.clientes` - Clientes
- `crm.contactos` - Contactos
- `crm.leads` - Leads
- `crm.oportunidades` - Oportunidades
- `crm.pipeline` - Pipeline
- `crm.cotizaciones` - Cotizaciones
- `crm.pedidos` - Pedidos
- `crm.remisiones` - Remisiones
- `crm.solicitudes` - Solicitudes Alta
- `crm.actividades` - Actividades
- `crm.integraciones` - Integraciones
- `crm.kpis` - KPIs
- `crm.config` - Configuración
- `VENTA_COT` - Cotizaciones de venta
- `VENTA_PED` - Pedidos de venta
- `VENTA_LISTAS` - Listas de precios

### 1.5 Menús SQL Registrados (Sistema_Modulos)

**COMERCIAL (Principal):**
| Menú | Ruta |
|------|------|
| Dashboard Comercial | `/comercial` |
| Clientes | `/comercial/clientes` |
| Cotizaciones | `/crm/cotizaciones` |
| Pedidos | `/crm/pedidos` |
| Remisiones | `/crm/remisiones` |
| Costos y Márgenes | `/comercial/costos-margenes` |

**CRM (Principal):**
| Menú | Ruta |
|------|------|
| Dashboard CRM | `/crm/dashboard` |
| Cuentas | `/crm/cuentas` |
| Solicitudes Alta | `/crm/solicitudes-alta` |
| Leads | `/crm/leads` |
| Oportunidades | `/crm/oportunidades` |
| Pipeline | `/crm/pipeline` |

### 1.6 Dependencias MongoDB

**RESULTADO:** NINGUNA ENCONTRADA

El módulo Comercial usa comentarios explícitos:
```python
# NO consulta servidores locales ni MongoDB para KPIs.
# NO usar MongoDB como fuente funcional para unidades.
```

### 1.7 Conexiones Remotas Vivas

**ATENCIÓN:** El módulo `Comercial.js` hace conexiones en vivo a:
- Servidores SoftRestaurant (para KPIs de ventas)
- Servidores MPRO (Management Pro)

Estas conexiones son **ACEPTABLES** porque:
1. Son fuentes operativas sincronizadas
2. Los KPIs se cachean en `Comercial_KPIs_*` de EDARSAHUB SQL
3. El dashboard maneja estados `DEGRADED_CACHE` y `SOURCE_UNREACHABLE`

### 1.8 Módulos Blindados

| Archivo | Estado | Razón |
|---------|--------|-------|
| `/app/frontend/src/pages/Comercial.js` | **BLINDADO** | Dashboard de Ventas estabilizado (Abril 2026) |

---

## 2. CLASIFICACIÓN DEL PROCESO

| Aspecto | Clasificación |
|---------|--------------|
| Tipo de Proceso | **Módulo Principal Analítico/Comercial** |
| Categoría | Comercial / Ventas |
| Satélite | NO (POS y Comandero son satélites separados) |
| Portal | NO |

---

## 3. UBICACIÓN CORRECTA EN EL ERP

### Jerarquía Confirmada:

```
COMERCIAL / VENTAS
├── Dashboard Comercial (Blindado)
├── Clientes
│   ├── Catálogo de Clientes
│   ├── Grupos de Clientes
│   └── Solicitudes de Alta
├── Cotizaciones
│   ├── Lista de Cotizaciones
│   ├── Detalle Cotización
│   └── Flujo de Aprobación
├── Pedidos
│   ├── Lista de Pedidos
│   ├── Detalle Pedido
│   └── Conversión Cot→Ped
├── Remisiones
│   ├── Lista de Remisiones
│   ├── Detalle Remisión
│   └── Historial Remisiones
├── Listas de Precios
└── Costos y Márgenes (PENDIENTE)
```

**NOTA:** CRM es módulo separado pero relacionado.

---

## 4. TABLAS EXISTENTES A REUTILIZAR

| Tabla | Uso | Estado |
|-------|-----|--------|
| `Cliente_Catalogo` | Maestro de clientes | 2 registros |
| `Venta_Cotizaciones` | Cabecera cotizaciones | 2 registros |
| `Venta_CotizacionesDetalle` | Detalle cotizaciones | Existente |
| `Venta_Pedidos` | Cabecera pedidos | 2 registros |
| `Venta_PedidosDetalle` | Detalle pedidos | Existente |
| `Venta_Remisiones` | Cabecera remisiones | 2 registros |
| `Venta_RemisionesDetalle` | Detalle remisiones | Existente |
| `Venta_ListasPrecios` | Listas de precios | 1 registro |

---

## 5. TABLAS NUEVAS JUSTIFICADAS

**NINGUNA REQUERIDA PARA FASE 1A**

Las tablas existentes cubren completamente el alcance de Comercial/Ventas.

---

## 6. ENDPOINTS PROPUESTOS

**NINGUNO NUEVO PARA FASE 1A**

Los endpoints existentes cubren el alcance:
- Dashboard: `/api/comercial/dashboard/{server_id}`
- Cotizaciones: `/api/crm/cotizaciones`
- Pedidos: `/api/crm/pedidos` (necesita implementación)
- Remisiones: `/api/crm/remisiones` (necesita implementación)
- Clientes: `/api/crm/clientes`

---

## 7. FRONTEND PROPUESTO

**NINGUNA PÁGINA NUEVA PARA FASE 1A**

### Verificar funcionamiento de páginas existentes:
- `/comercial` - Dashboard (BLINDADO, no tocar)
- `/comercial/clientes` - **VERIFICAR SI EXISTE**
- `/crm/cotizaciones` - Cotizaciones
- `/crm/pedidos` - Pedidos
- `/crm/remisiones` - Remisiones
- `/comercial/costos-margenes` - **VERIFICAR SI EXISTE**

---

## 8. PERMISOS RBAC

**EXISTENTES Y SUFICIENTES**

No se requieren permisos nuevos para FASE 1A.

---

## 9. RIESGOS IDENTIFICADOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Romper `Comercial.js` blindado | ALTA si se modifica | CRÍTICO | **NO MODIFICAR** |
| Rutas `/comercial/clientes` y `/comercial/costos-margenes` no existen | MEDIA | BAJO | Verificar y crear si necesario |
| Endpoint `/api/crm/pedidos` y `/api/crm/remisiones` incompletos | MEDIA | MEDIO | Verificar implementación |

---

## 10. FASES DE IMPLEMENTACIÓN

### FASE 1A.1: Verificación de Integridad (ACTUAL)
- [x] Diagnóstico pasivo completado
- [ ] Verificar rutas faltantes
- [ ] Verificar endpoints faltantes
- [ ] Validar no regresión

### FASE 1A.2: Completar Rutas Faltantes
- [ ] `/comercial/clientes` (si no existe)
- [ ] `/comercial/costos-margenes` (si no existe)

### FASE 1A.3: Validación Final
- [ ] Login funciona
- [ ] Menús SQL cargan
- [ ] Comercial accesible desde menú
- [ ] Rutas no 404
- [ ] No errores 500

---

## 11. PRUEBAS DE NO REGRESIÓN

### Checklist obligatorio antes de cerrar FASE 1A:

| # | Prueba | Método |
|---|--------|--------|
| 1 | Login funciona | cURL |
| 2 | Auth SQL-first | cURL |
| 3 | Token persiste | Screenshot |
| 4 | `/api/sistema/menus/usuario` responde | cURL |
| 5 | Menú principal carga desde SQL | Screenshot |
| 6 | SuperAdministrador ve módulos | Screenshot |
| 7 | `/comercial` renderiza (blindado) | Screenshot |
| 8 | `/crm/cotizaciones` accesible | Screenshot |
| 9 | `/crm/pedidos` accesible | Screenshot |
| 10 | `/crm/remisiones` accesible | Screenshot |
| 11 | No errores 500 | cURL |
| 12 | No errores críticos frontend | Console logs |
| 13 | No dependencia MongoDB nueva | grep |
| 14 | No exposición de secretos | grep |

---

## 12. CRITERIO DE PARO

**DETENERSE Y REPORTAR SI:**
- Se requiere modificar `Comercial.js`
- Se necesita crear tablas nuevas
- Se detecta dependencia MongoDB
- Se rompe autenticación o RBAC
- Hay errores 500 en endpoints existentes

---

## 13. CONCLUSIÓN

### Estado: LISTO PARA IMPLEMENTACIÓN

**Alcance confirmado para FASE 1A:**
1. Verificar rutas frontend faltantes (`/comercial/clientes`, `/comercial/costos-margenes`)
2. Verificar endpoints backend faltantes
3. Asegurar que módulo Comercial/Ventas es accesible desde menú SQL
4. Ejecutar pruebas de no regresión
5. Generar reporte de cierre

**NO AUTORIZADO:**
- Modificar `Comercial.js` (BLINDADO)
- Crear tablas nuevas
- Modificar satélites (POS, Comandero)
- Agregar dependencias MongoDB

---

*Documento generado: 2026-05-24*
*Próximo paso: Verificar rutas faltantes y estado de endpoints*
