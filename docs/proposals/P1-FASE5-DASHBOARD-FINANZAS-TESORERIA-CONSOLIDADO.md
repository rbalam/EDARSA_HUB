# P1-FASE5 — Dashboard Finanzas/Tesorería Consolidado

## PROPUESTA FORMAL

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-05 |
| **Versión** | 1.0 |
| **Estado** | PROPUESTA - PENDIENTE AUTORIZACIÓN |
| **Prioridad** | P1 |
| **Tipo** | Nueva funcionalidad |

---

## 1. OBJETIVO FUNCIONAL

Crear un **Dashboard Financiero Consolidado** que permita a la dirección general y al área de finanzas visualizar en tiempo real:

- Posición de efectivo y liquidez
- Ingresos y egresos consolidados por unidad de negocio
- Flujo de caja proyectado con alertas de vencimientos
- Calendario de pagos y obligaciones
- Cuentas por pagar con análisis de deuda
- Indicadores gerenciales financieros

**Meta**: Tomar decisiones informadas sobre el flujo de efectivo y cumplimiento de obligaciones.

---

## 2. ALCANCE DE LA FASE

### 2.1 Incluido en P1-FASE5

| Componente | Descripción |
|------------|-------------|
| Posición de efectivo | Saldos por banco/cuenta, efectivo disponible |
| Ingresos | Ventas cobradas, depósitos, cobros por unidad |
| Egresos | Cuentas por pagar, pagos programados, obligaciones |
| Flujo proyectado | Efectivo actual vs compromisos próximos |
| Calendario de pagos | Vencimientos, fechas límite, alertas |
| CxP Dashboard | Deuda por proveedor, análisis de antigüedad |
| KPIs gerenciales | Liquidez, deuda vencida, compromisos críticos |

### 2.2 Subfases propuestas

| Subfase | Contenido | Dependencia |
|---------|-----------|-------------|
| 5A | Estructura base + Posición de efectivo | Ninguna |
| 5B | Ingresos consolidados | 5A |
| 5C | Egresos y CxP Dashboard | 5A |
| 5D | Flujo proyectado | 5B, 5C |
| 5E | Calendario de pagos | 5C |
| 5F | Indicadores gerenciales | 5B, 5C, 5D |

---

## 3. FUERA DE ALCANCE

| Elemento | Razón |
|----------|-------|
| Cuadre de Cortes Z | Ya estabilizado en P1-FASE4A |
| Propinas TPV | Módulo independiente |
| Conciliación bancaria avanzada | Fase posterior |
| Estado de resultados completo | Fase posterior |
| Integración bancaria automática | Requiere APIs bancarias |
| Facturación electrónica | Módulo separado |
| Tablero Ejecutivo | Módulo blindado |
| Comercial V1/V2 | Módulos blindados |
| Compras | Módulo blindado |
| Auth/RBAC | Módulo blindado |

---

## 4. MÓDULOS EXISTENTES RELACIONADOS

| Módulo | Archivo | Relación |
|--------|---------|----------|
| Cuentas por Pagar | `cuentas_por_pagar.py` | Fuente de egresos/deuda |
| Control de Ingresos | `ingresos.py` | Fuente de ingresos/depósitos |
| Tesorería (Cuadre Z) | `tesoreria.py` | Referencia de cortes |
| Health Check | `health.py` | Monitoreo de conexiones |
| Repository EDARSAHUB | `repository_edarsahub.py` | Acceso a datos consolidados |

**Dependencia crítica**: Los datos deben venir de EDARSAHUB, no de consultas vivas a SoftRestaurant/MPRO.

---

## 5. TABLAS ACTUALES DE EDARSAHUB QUE YA PUEDEN USARSE

### 5.1 Tablas con datos operativos

| Tabla | Registros | Uso |
|-------|-----------|-----|
| `Finanzas_CortesCaja` | 3,992 | Ingresos por corte/caja |
| `Finanzas_CuentasPorPagar` | 25 | Deuda por proveedor |
| `Global_Cat_Bancos` | 5 | Catálogo de bancos |
| `Proveedor_Catalogo` | ~N | Catálogo de proveedores |
| `Comercial_KPIs_Diarios_v2` | ~N | Ventas por unidad |
| `Servidores_Conexiones` | 17 | Unidades de negocio |
| `Unidades_Negocio` | ~N | Catálogo unidades |

### 5.2 Tablas vacías pero con estructura lista

| Tabla | Estado | Notas |
|-------|--------|-------|
| `Finanzas_Cat_CuentasBancarias` | 0 registros | Requiere carga inicial |
| `Finanzas_Depositos` | 0 registros | Requiere carga inicial |
| `Finanzas_Pagos` | 0 registros | Requiere carga inicial |
| `Finanzas_Presupuestos` | 0 registros | Requiere carga inicial |
| `RH_Nomina` | 0 registros | Pendiente integración RH |
| `RH_Periodos_Nomina` | 0 registros | Pendiente integración RH |

---

## 6. TABLAS FALTANTES QUE HABRÍA QUE CREAR

| Tabla propuesta | Propósito | Prioridad |
|-----------------|-----------|-----------|
| `Finanzas_ObligacionesRecurrentes` | Nómina, IMSS, CFE, rentas, etc. | ALTA |
| `Finanzas_CalendarioPagos` | Fechas de vencimiento programadas | ALTA |
| `Finanzas_FlujoProyectado` | Forecast de efectivo | MEDIA |
| `Finanzas_SaldosBancarios` | Saldos por cuenta/fecha | ALTA |
| `Finanzas_ConciliacionBancaria` | Movimientos vs banco | BAJA (fase posterior) |
| `Finanzas_KPIs_Dashboard` | KPIs calculados consolidados | MEDIA |

**Nota**: La creación de tablas requiere autorización separada y debe hacerse en EDARSAHUB.

---

## 7. ENDPOINTS PROPUESTOS

### 7.1 Endpoint principal del Dashboard

```
GET /api/v2/finanzas/dashboard
```

**Parámetros**:
- `unidad_negocio_id` (opcional)
- `fecha_inicio` (opcional)
- `fecha_fin` (opcional)

**Respuesta**:
```json
{
  "posicion_efectivo": {...},
  "ingresos": {...},
  "egresos": {...},
  "flujo_proyectado": {...},
  "cuentas_por_pagar": {...},
  "indicadores": {...}
}
```

### 7.2 Endpoints específicos

| Endpoint | Método | Propósito |
|----------|--------|-----------|
| `/api/v2/finanzas/dashboard` | GET | Dashboard consolidado |
| `/api/v2/finanzas/posicion-efectivo` | GET | Saldos bancarios y caja |
| `/api/v2/finanzas/ingresos/resumen` | GET | Ingresos consolidados |
| `/api/v2/finanzas/egresos/resumen` | GET | Egresos consolidados |
| `/api/v2/finanzas/flujo-proyectado` | GET | Forecast de caja |
| `/api/v2/finanzas/calendario-pagos` | GET | Vencimientos próximos |
| `/api/v2/finanzas/cxp/dashboard` | GET | Dashboard de CxP |
| `/api/v2/finanzas/indicadores` | GET | KPIs gerenciales |
| `/api/v2/finanzas/obligaciones-recurrentes` | GET/POST | CRUD obligaciones |

---

## 8. COMPONENTES FRONTEND PROPUESTOS

### 8.1 Estructura de páginas

```
/app/frontend/src/
├── pages/
│   └── FinanzasDashboard.js          # Página principal (nuevo)
├── components/
│   └── finanzas-dashboard/
│       ├── index.js
│       ├── PosicionEfectivo.jsx      # Widget saldos
│       ├── IngresosResumen.jsx       # Widget ingresos
│       ├── EgresosResumen.jsx        # Widget egresos
│       ├── FlujoProyectado.jsx       # Widget forecast
│       ├── CalendarioPagos.jsx       # Calendario/timeline
│       ├── CxPDashboard.jsx          # Análisis CxP
│       ├── IndicadoresGerenciales.jsx # KPIs
│       └── hooks/
│           └── useFinanzasDashboard.js
```

### 8.2 Integración con Finanzas existente

**Opción A**: Nuevo tab en `/pages/Finanzas.js`
```javascript
{ id: 'dashboard-consolidado', label: 'Dashboard Consolidado', icon: BarChart3 }
```

**Opción B**: Nueva página independiente en menú principal
```
/finanzas-dashboard
```

**Recomendación**: Opción A para mantener cohesión del módulo.

---

## 9. KPIs DEL DASHBOARD

| # | KPI | Descripción |
|---|-----|-------------|
| 1 | Efectivo disponible | Saldo total en bancos + caja |
| 2 | Ingresos del período | Ventas cobradas en rango |
| 3 | Egresos del período | Pagos realizados en rango |
| 4 | Flujo neto | Ingresos - Egresos |
| 5 | Deuda total CxP | Suma de facturas pendientes |
| 6 | Deuda vencida | Facturas pasadas de fecha |
| 7 | Deuda por vencer (7 días) | Próximos vencimientos |
| 8 | Ratio de liquidez | Efectivo / Compromisos próximos |
| 9 | Días promedio de pago | DPP real vs crédito |
| 10 | Cobertura de obligaciones | Efectivo / Obligaciones mes |
| 11 | Concentración de deuda | % top 5 proveedores |
| 12 | Forecast 30 días | Proyección de caja |

---

## 10. FUENTES DE DATOS POR KPI

| KPI | Fuente principal | Tabla EDARSAHUB |
|-----|------------------|-----------------|
| Efectivo disponible | EDARSAHUB | `Finanzas_SaldosBancarios` (nueva) / `Finanzas_Cat_CuentasBancarias` |
| Ingresos del período | EDARSAHUB | `Finanzas_CortesCaja` |
| Egresos del período | EDARSAHUB | `Finanzas_Pagos` |
| Deuda total CxP | EDARSAHUB | `Finanzas_CuentasPorPagar` |
| Deuda vencida | EDARSAHUB | `Finanzas_CuentasPorPagar` (WHERE FechaVencimiento < GETDATE()) |
| Días promedio de pago | EDARSAHUB | `Finanzas_Pagos` + `Finanzas_CuentasPorPagar` |
| Ventas por unidad | EDARSAHUB | `Comercial_KPIs_Diarios_v2` |
| Obligaciones recurrentes | EDARSAHUB | `Finanzas_ObligacionesRecurrentes` (nueva) |

---

## 11. REGLAS DE CÁLCULO

### 11.1 Flujo Neto
```
flujo_neto = ingresos_periodo - egresos_periodo
```

### 11.2 Ratio de Liquidez
```
ratio_liquidez = efectivo_disponible / compromisos_proximos_30_dias
```

### 11.3 Días Promedio de Pago
```
DPP = AVG(fecha_pago_real - fecha_documento)
```

### 11.4 Forecast de Caja
```
forecast_dia_n = saldo_actual + ingresos_proyectados - egresos_programados
```

### 11.5 Deuda Vencida
```
deuda_vencida = SUM(MontoOriginal - MontoPagado) 
                WHERE FechaVencimiento < GETDATE() AND EstatusPagoID != 'PAGADO'
```

---

## 12. FILTROS REQUERIDOS

| Filtro | Tipo | Valores |
|--------|------|---------|
| Unidad de negocio | Select múltiple | CIENFUEGOS, LA ESTELAR, 130° MÉRIDA, etc. |
| Rango de fechas | Date picker | fecha_inicio, fecha_fin |
| Proveedor | Select con búsqueda | Catálogo proveedores |
| Banco/Cuenta | Select | Cuentas bancarias activas |
| Tipo de obligación | Select | Nómina, IMSS, CFE, Renta, etc. |
| Estatus de pago | Select | Pendiente, Parcial, Pagado, Vencido |
| Período | Quick select | Hoy, Semana, Mes, Trimestre, Año |

---

## 13. MODELO DE PERMISOS/RBAC REQUERIDO

### 13.1 Roles sugeridos

| Rol | Permisos |
|-----|----------|
| SuperAdministrador | Acceso total a todas las unidades |
| Director Finanzas | Dashboard completo, todas las unidades |
| Contador | Dashboard lectura, unidades asignadas |
| Tesorero | Posición efectivo, CxP, calendario pagos |
| Gerente Unidad | Solo su unidad de negocio |

### 13.2 Permisos por módulo

| Permiso | Descripción |
|---------|-------------|
| `finanzas.dashboard.view` | Ver dashboard consolidado |
| `finanzas.posicion.view` | Ver posición de efectivo |
| `finanzas.cxp.view` | Ver cuentas por pagar |
| `finanzas.flujo.view` | Ver flujo proyectado |
| `finanzas.calendario.view` | Ver calendario de pagos |
| `finanzas.obligaciones.manage` | Gestionar obligaciones recurrentes |

**Nota**: No se modifica RBAC existente en esta fase. Se documenta para fase posterior.

---

## 14. RIESGOS TÉCNICOS

| # | Riesgo | Impacto | Mitigación |
|---|--------|---------|------------|
| 1 | Tablas sin datos | ALTO | Definir carga inicial de catálogos |
| 2 | Cálculos incorrectos | ALTO | Validar fórmulas con Finanzas |
| 3 | Performance en consultas | MEDIO | Usar tablas consolidadas, no queries vivos |
| 4 | Inconsistencia de datos | MEDIO | Validar integridad referencial |
| 5 | Complejidad de integración | MEDIO | Implementar por subfases |
| 6 | Dependencia de RH/Nómina | MEDIO | Marcar como opcional hasta integración |

---

## 15. RIESGOS DE NEGOCIO

| # | Riesgo | Impacto | Mitigación |
|---|--------|---------|------------|
| 1 | Datos financieros sensibles expuestos | CRÍTICO | Implementar RBAC estricto |
| 2 | Decisiones basadas en datos incompletos | ALTO | Indicar claramente fuentes y cobertura |
| 3 | Expectativas no alineadas | MEDIO | Validar alcance con usuarios clave |
| 4 | Resistencia al cambio | BAJO | Capacitación y documentación |

---

## 16. PLAN DE IMPLEMENTACIÓN POR SUBFASES

### Subfase 5A: Estructura base + Posición de efectivo
**Duración estimada**: 1 sprint

| Tarea | Descripción |
|-------|-------------|
| 5A.1 | Crear endpoint `/api/v2/finanzas/dashboard` (estructura) |
| 5A.2 | Crear componente `FinanzasDashboard.jsx` |
| 5A.3 | Implementar widget `PosicionEfectivo.jsx` |
| 5A.4 | Verificar/poblar `Finanzas_Cat_CuentasBancarias` |
| 5A.5 | Crear tabla `Finanzas_SaldosBancarios` si se autoriza |

### Subfase 5B: Ingresos consolidados
**Duración estimada**: 1 sprint

| Tarea | Descripción |
|-------|-------------|
| 5B.1 | Endpoint `/api/v2/finanzas/ingresos/resumen` |
| 5B.2 | Widget `IngresosResumen.jsx` |
| 5B.3 | Integrar con `Finanzas_CortesCaja` |
| 5B.4 | Calcular ingresos por unidad de negocio |

### Subfase 5C: Egresos y CxP Dashboard
**Duración estimada**: 1-2 sprints

| Tarea | Descripción |
|-------|-------------|
| 5C.1 | Endpoint `/api/v2/finanzas/egresos/resumen` |
| 5C.2 | Endpoint `/api/v2/finanzas/cxp/dashboard` |
| 5C.3 | Widget `EgresosResumen.jsx` |
| 5C.4 | Widget `CxPDashboard.jsx` |
| 5C.5 | Análisis de antigüedad de deuda |

### Subfase 5D: Flujo proyectado
**Duración estimada**: 1 sprint

| Tarea | Descripción |
|-------|-------------|
| 5D.1 | Endpoint `/api/v2/finanzas/flujo-proyectado` |
| 5D.2 | Widget `FlujoProyectado.jsx` |
| 5D.3 | Algoritmo de forecast |
| 5D.4 | Crear tabla `Finanzas_FlujoProyectado` si se autoriza |

### Subfase 5E: Calendario de pagos
**Duración estimada**: 1 sprint

| Tarea | Descripción |
|-------|-------------|
| 5E.1 | Endpoint `/api/v2/finanzas/calendario-pagos` |
| 5E.2 | Endpoint `/api/v2/finanzas/obligaciones-recurrentes` |
| 5E.3 | Widget `CalendarioPagos.jsx` |
| 5E.4 | Crear tabla `Finanzas_ObligacionesRecurrentes` si se autoriza |
| 5E.5 | Sistema de alertas por vencimiento |

### Subfase 5F: Indicadores gerenciales
**Duración estimada**: 1 sprint

| Tarea | Descripción |
|-------|-------------|
| 5F.1 | Endpoint `/api/v2/finanzas/indicadores` |
| 5F.2 | Widget `IndicadoresGerenciales.jsx` |
| 5F.3 | Cálculo de 12 KPIs definidos |
| 5F.4 | Visualizaciones y gráficos |

---

## 17. PRUEBAS OBLIGATORIAS

| # | Prueba | Criterio |
|---|--------|----------|
| 1 | Dashboard carga sin errores | HTTP 200, datos visibles |
| 2 | Filtro por unidad funciona | Datos filtrados correctamente |
| 3 | KPIs calculan correctamente | Validar contra Excel/manual |
| 4 | No regresión Comercial V2 | 5 unidades, ventas correctas |
| 5 | No regresión Tablero Ejecutivo | Sin cambios |
| 6 | No regresión Compras | Sin cambios |
| 7 | No regresión Cuadre Cortes Z | 4 sucursales operativas |
| 8 | RBAC respetado | Usuarios ven solo lo permitido |
| 9 | Performance aceptable | < 3 segundos carga dashboard |
| 10 | Sin datos demo | Solo datos reales |

---

## 18. CRITERIOS DE ACEPTACIÓN

### Por subfase

| Subfase | Criterio de aceptación |
|---------|------------------------|
| 5A | Dashboard muestra posición de efectivo correcta |
| 5B | Ingresos consolidados por unidad visibles |
| 5C | CxP Dashboard con análisis de deuda funcional |
| 5D | Flujo proyectado a 30 días calculado |
| 5E | Calendario de pagos con alertas funcionando |
| 5F | 12 KPIs visibles y correctos |

### General

- EDARSAHUB es fuente primaria para todos los datos
- MongoDB solo como fallback documentado
- Sin datos demo ni inventados
- Sin regresión en módulos existentes
- Documentación técnica completa

---

## 19. ROLLBACK

### Por subfase

```bash
# Revertir componentes frontend
git checkout -- /app/frontend/src/components/finanzas-dashboard/

# Revertir endpoints backend
git checkout -- /app/backend/modules/finanzas/dashboard_v2.py

# Reiniciar servicios
sudo supervisorctl restart backend frontend
```

### Rollback de tablas (si se crean)

```sql
-- Solo si se autoriza la creación de tablas
-- DROP TABLE Finanzas_SaldosBancarios;
-- DROP TABLE Finanzas_ObligacionesRecurrentes;
-- etc.
```

**Tiempo estimado**: < 5 minutos por subfase

---

## 20. REGLAS DE NO REGRESIÓN

| Módulo | Verificación |
|--------|--------------|
| Tablero Ejecutivo | No se toca, verificar que funciona |
| Comercial V1 | No se toca, verificar que funciona |
| Comercial V2 | No se toca, verificar 5 unidades |
| Compras | No se toca, verificar que funciona |
| Propinas TPV | No se toca |
| Auth/RBAC | No se toca |
| Cuadre Cortes Z | No se toca, verificar 4 sucursales |
| Cuentas por Pagar existente | No se modifica, se consume |
| Control de Ingresos existente | No se modifica, se consume |

---

## RESUMEN EJECUTIVO

### Lo que se propone

Crear un **Dashboard Financiero Consolidado** en 6 subfases:

1. **5A**: Posición de efectivo
2. **5B**: Ingresos consolidados
3. **5C**: Egresos y CxP Dashboard
4. **5D**: Flujo proyectado
5. **5E**: Calendario de pagos
6. **5F**: Indicadores gerenciales

### Fuente de datos

**EDARSAHUB** como fuente primaria. MongoDB solo fallback legacy documentado.

### Tablas existentes que se usarán

- `Finanzas_CortesCaja` (3,992 registros)
- `Finanzas_CuentasPorPagar` (25 registros)
- `Global_Cat_Bancos` (5 registros)
- `Comercial_KPIs_Diarios_v2`

### Tablas que requieren carga inicial

- `Finanzas_Cat_CuentasBancarias` (vacía)
- `Finanzas_Depositos` (vacía)
- `Finanzas_Pagos` (vacía)

### Tablas nuevas propuestas

- `Finanzas_SaldosBancarios`
- `Finanzas_ObligacionesRecurrentes`
- `Finanzas_CalendarioPagos`

---

## AUTORIZACIÓN SOLICITADA

### Para iniciar Subfase 5A:

1. ✅ Crear endpoint `/api/v2/finanzas/dashboard` (estructura base)
2. ✅ Crear componente `FinanzasDashboard.jsx`
3. ✅ Implementar widget `PosicionEfectivo.jsx`
4. ⚠️ Verificar estado de `Finanzas_Cat_CuentasBancarias`
5. ❓ ¿Autorizar creación de tabla `Finanzas_SaldosBancarios` en EDARSAHUB?

### NO se solicita autorización para:

- ❌ Modificar módulos existentes (Comercial, Compras, etc.)
- ❌ Modificar Cuadre de Cortes Z
- ❌ Implementar subfases 5B-5F sin autorización separada
- ❌ Crear tablas sin autorización explícita

---

**ESTADO**: ⏳ PROPUESTA FORMAL - PENDIENTE AUTORIZACIÓN PARA SUBFASE 5A

*Documento: P1-FASE5-DASHBOARD-FINANZAS-TESORERIA-CONSOLIDADO.md*  
*Fecha: 2026-05-05 v1.0*
