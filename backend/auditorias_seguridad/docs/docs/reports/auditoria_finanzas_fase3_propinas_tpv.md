# AUDITORÍA TÉCNICA — FINANZAS FASE 3: PROPINAS TPV

**Fecha de Auditoría:** 2026-05-01  
**Estado:** AUDITORÍA COMPLETADA  
**Versión:** 1.0

---

## 1. RESUMEN EJECUTIVO

La auditoría técnica de Propinas TPV revela que:

1. **Existen tablas en EDARSAHUB** pero están **vacías** (0 registros de control).
2. **El módulo actual usa MongoDB** como destino de datos (no EDARSAHUB).
3. **Solo soporta SoftRestaurant** (MPRO no implementado).
4. **MPRO tiene datos de propinas** perfectamente identificables en `Comanda_Pago`.
5. **Se requiere migración** similar a Control de Ingresos (Fase 2).

### Estado por Unidad

| Unidad | Sistema | Fuente Propinas TPV | Estado Actual |
|--------|---------|---------------------|---------------|
| 130° MÉRIDA | SoftRestaurant | `cheques.propinatarjeta` | ✅ Identificada |
| CIENFUEGOS | SoftRestaurant | `cheques.propinatarjeta` | ✅ Identificada |
| LA ESTELAR | SoftRestaurant | `cheques.propinatarjeta` | ✅ Identificada |
| 130° QUERETARO | MPRO | `Comanda_Pago.Cp_Propina` | ⚠️ NO IMPLEMENTADO |
| ORIGEN | MPRO | `Comanda_Pago.Cp_Propina` | ⚠️ NO IMPLEMENTADO |

---

## 2. ESTADO ACTUAL DEL TAB PROPINAS TPV

| Aspecto | Valor |
|---------|-------|
| Ubicación Frontend | `/app/frontend/src/components/PropinasTPV.jsx` |
| Tabs disponibles | Cuadre, Configuración |
| Filtro por Unidad | ✅ Implementado (usa `server_id`) |
| Filtro por Fechas | ✅ Implementado |
| Estado de cuadre | ✅ Implementado |

### Funcionalidades Actuales

1. **Cuadre de Propinas:** Listado de propinas por corte con estado de pago.
2. **Configuración:** Gestión de % de comisión (descuento).
3. **KPIs:** Tarjetas con totales de propinas, comisión, pendientes.

---

## 3. TABLAS EDARSAHUB EXISTENTES

| Tabla | Registros | Propósito |
|-------|-----------|-----------|
| `propinas_tpv_config` | 0 | Configuración de comisiones |
| `propinas_tpv_control` | 0 | Registro de propinas por corte |
| `propinas_tpv_historial` | 0 | Historial de cambios/pagos |
| `Finanzas_ConfiguracionTPV_Sucursal` | 8 | Config de terminales TPV |

### Estructura de `propinas_tpv_control`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | uniqueidentifier | PK |
| `server_id` | varchar | ID del servidor |
| `sucursal_id` | varchar | ID de sucursal |
| `folio_corte` | varchar | Folio del corte |
| `fecha_corte` | date | Fecha del corte |
| `propinas_totales_corte` | decimal | Total propinas |
| `propinas_efectivo` | decimal | Propinas en efectivo |
| `propinas_tpv` | decimal | **Propinas pagadas con tarjeta** |
| `ventas_tarjeta` | decimal | Total ventas con tarjeta |
| `porcentaje_comision` | decimal | % de comisión aplicada |
| `comision_calculada` | decimal | Monto de comisión |
| `monto_a_pagar_meseros` | decimal | Neto a pagar |
| `pago_registrado` | bit | Si ya se pagó |
| `cuadre_estado` | varchar | PENDIENTE/CUADRADO/DESCUADRE |

---

## 4. DATOS ACTUALES: REALES/DEMO/VACÍOS

| Tabla | Estado |
|-------|--------|
| `propinas_tpv_control` | **VACÍA** (0 registros) |
| `propinas_tpv_config` | **VACÍA** (0 registros) |
| `propinas_tpv_historial` | **VACÍA** (0 registros) |

### MongoDB (colecciones actuales)

| Colección | Registros | Estado |
|-----------|-----------|--------|
| `propinas_control` | 0 | Vacía |
| `propinas_config` | 1 | Configuración activa |
| `propinas_cache_listado` | 9 | Cache de consultas |
| `propinas_cache_resumen` | 5 | Cache de resúmenes |

---

## 5. ENDPOINTS ACTUALES

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/finanzas/propinas/health` | GET | Health check |
| `/api/finanzas/propinas` | GET | Listado de propinas |
| `/api/finanzas/propinas/resumen` | GET | Resumen/KPIs |
| `/api/finanzas/propinas/sincronizar` | POST | Sincronizar desde origen |
| `/api/finanzas/propinas/config` | GET/POST | Configuración |
| `/api/finanzas/propinas/config/all` | GET | Todas las configs |
| `/api/finanzas/propinas/{id}` | GET | Detalle de propina |
| `/api/finanzas/propinas/{id}/pago` | PUT | Registrar pago |

### Archivos de Backend

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/modules/finanzas/propinas_tpv/routes.py` | Endpoints REST |
| `/app/backend/modules/finanzas/propinas_tpv/service.py` | Lógica de negocio |
| `/app/backend/modules/finanzas/propinas_tpv/repository.py` | Acceso a datos |
| `/app/backend/modules/finanzas/propinas_tpv/models.py` | Modelos Pydantic |
| `/app/backend/modules/finanzas/propinas_tpv/sql_repository.py` | Queries SQL |

---

## 6. FRONTEND ACTUAL

| Archivo | Propósito |
|---------|-----------|
| `/app/frontend/src/components/PropinasTPV.jsx` | Componente principal |
| `/app/frontend/src/components/finanzas/propinas/PropinasKPICards.jsx` | KPIs |
| `/app/frontend/src/components/finanzas/propinas/PropinasTable.jsx` | Tabla de datos |
| `/app/frontend/src/components/finanzas/propinas/PropinasConfigForm.jsx` | Form config |
| `/app/frontend/src/components/finanzas/propinas/PropinasConfigList.jsx` | Lista configs |

---

## 7. FUENTE ACTUAL DE DATOS

| Fuente | Uso |
|--------|-----|
| **SoftRestaurant (SQL Server)** | ✅ Lectura de propinas en tiempo real |
| **MongoDB** | ✅ Almacenamiento de propinas_control |
| **EDARSAHUB** | ❌ NO SE USA (tablas vacías) |

### Flujo Actual

```
SoftRestaurant → Service → MongoDB (propinas_control)
                        ↓
                    Frontend
```

---

## 8. CONFIRMACIÓN DE USO O NO USO DE MONGODB

| Verificación | Estado |
|--------------|--------|
| MongoDB como destino de sincronización | ✅ SÍ |
| MongoDB como fuente para listados | ✅ SÍ |
| MongoDB como fuente para KPIs | ✅ SÍ |

**Problema:** Esto viola la Máxima #3: "MongoDB NO es fuente de verdad financiera".

---

## 9. CONFIRMACIÓN DE USO O NO USO DE EDARSAHUB

| Verificación | Estado |
|--------------|--------|
| EDARSAHUB como destino de sincronización | ❌ NO |
| EDARSAHUB como fuente para listados | ❌ NO |
| Tablas EDARSAHUB creadas | ✅ SÍ (pero vacías) |

---

## 10. ANÁLISIS POR LAS 5 UNIDADES

### 130° MÉRIDA (SoftRestaurant)

| Métrica | Valor |
|---------|-------|
| Fuente | `cheques.propinatarjeta` |
| Datos Abril 2026 | 41 cheques, $19,335.15 propinas TPV |
| Columnas disponibles | `propina`, `propinatarjeta`, `tarjeta`, `efectivo` |
| Estado | ✅ IMPLEMENTADO |

### CIENFUEGOS (SoftRestaurant)

| Métrica | Valor |
|---------|-------|
| Fuente | `cheques.propinatarjeta` |
| Columnas disponibles | `propina`, `propinatarjeta`, `tarjeta`, `efectivo` |
| Estado | ✅ IMPLEMENTADO |

### LA ESTELAR (SoftRestaurant)

| Métrica | Valor |
|---------|-------|
| Fuente | `cheques.propinatarjeta` |
| Columnas disponibles | `propina`, `propinatarjeta`, `tarjeta`, `efectivo` |
| Estado | ✅ IMPLEMENTADO |

### 130° QUERETARO (MPRO)

| Métrica | Valor |
|---------|-------|
| Fuente | `Comanda_Pago.Cp_Propina` donde `Forma_Pago.Fp_Tipo = '04'` |
| Datos Abril 2026 | 542 pagos crédito, 321 débito, 132 AMEX |
| Propinas TPV Abril | ~$496,537.78 |
| Formas de pago tarjeta | 0004 (Crédito), 0005 (Débito), 0006 (AMEX) |
| Estado | ⚠️ **NO IMPLEMENTADO** |

### ORIGEN (MPRO)

| Métrica | Valor |
|---------|-------|
| Fuente | `Comanda_Pago.Cp_Propina` donde `Forma_Pago.Fp_Tipo = '04'` |
| Formas de pago tarjeta | Igual que 130° QRO (compartidas en CENTRAL2020) |
| Estado | ⚠️ **NO IMPLEMENTADO** |

---

## 11. FUENTE SOFTRESTAURANT CONFIRMADA

| Campo | Tabla | Descripción |
|-------|-------|-------------|
| `propinatarjeta` | `cheques` | **Propina pagada con tarjeta** (FUENTE PRINCIPAL) |
| `propina` | `cheques` | Propina total del cheque |
| `tarjeta` | `cheques` | Monto total pagado con tarjeta |
| `efectivo` | `cheques` | Monto pagado en efectivo |

### Query Validada

```sql
SELECT 
    folio, fecha, total,
    propina,           -- Propina total
    propinatarjeta,    -- Propina TPV (FUENTE)
    tarjeta,           -- Pago con tarjeta
    efectivo           -- Pago efectivo
FROM cheques
WHERE propinatarjeta > 0
```

---

## 12. FUENTE MPRO INVESTIGADA

### Tablas Relevantes

| Tabla | Campo | Descripción |
|-------|-------|-------------|
| `Comanda` | `Co_Propina` | Propina total de la comanda |
| `Comanda` | `Co_Comision_Propina` | Comisión de propina |
| `Comanda_Pago` | `Cp_Propina` | **Propina por forma de pago** |
| `Forma_Pago` | `Fp_Tipo` | Tipo de forma de pago |

### Formas de Pago Tarjeta en MPRO

| Clave | Descripción | Tipo |
|-------|-------------|------|
| 0004 | T DE CREDITO | 04 (Tarjeta) |
| 0005 | T DE DEBITO | 04 (Tarjeta) |
| 0006 | T AMEX | 04 (Tarjeta) |

### Query Propuesta para MPRO

```sql
SELECT 
    c.Co_Folio,
    c.Co_Fecha,
    c.Co_Propina as propina_total,
    SUM(CASE WHEN fp.Fp_Tipo = '04' THEN cp.Cp_Propina ELSE 0 END) as propina_tpv,
    SUM(CASE WHEN fp.Fp_Tipo <> '04' THEN cp.Cp_Propina ELSE 0 END) as propina_efectivo
FROM Comanda c
JOIN Comanda_Pago cp ON cp.Co_Folio = c.Co_Folio
JOIN Forma_Pago fp ON fp.Fp_Cve_Forma_Pago = cp.Fp_Cve_Forma_Pago
WHERE c.Co_Fecha >= @fecha_inicio
  AND c.Co_Fecha < @fecha_fin
  AND cp.Cp_Propina > 0
GROUP BY c.Co_Folio, c.Co_Fecha, c.Co_Propina
```

---

## 13. MAPEO PRELIMINAR ORIGEN → EDARSAHUB

### SoftRestaurant

| Origen | Destino EDARSAHUB |
|--------|-------------------|
| `cheques.folio` | `propinas_tpv_control.folio_corte` |
| `cheques.fecha` | `propinas_tpv_control.fecha_corte` |
| `cheques.propinatarjeta` | `propinas_tpv_control.propinas_tpv` |
| `cheques.propina` | `propinas_tpv_control.propinas_totales_corte` |
| `cheques.tarjeta` | `propinas_tpv_control.ventas_tarjeta` |

### MPRO

| Origen | Destino EDARSAHUB |
|--------|-------------------|
| `Comanda.Co_Folio` | `propinas_tpv_control.folio_corte` |
| `Comanda.Co_Fecha` | `propinas_tpv_control.fecha_corte` |
| `SUM(Comanda_Pago.Cp_Propina WHERE Fp_Tipo='04')` | `propinas_tpv_control.propinas_tpv` |
| `Comanda.Co_Propina` | `propinas_tpv_control.propinas_totales_corte` |

---

## 14. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Romper sincronización SoftRestaurant existente | Media | Alto | Mantener lógica actual, agregar EDARSAHUB |
| Inconsistencia con Control de Ingresos | Baja | Medio | Reutilizar arquitectura de Fase 2 |
| MPRO sin datos históricos | Baja | Bajo | Validar rango de fechas disponible |
| Scheduler conflicto con incremental | Baja | Medio | Coordinar con lock existente |

---

## 15. POSIBLES AFECTACIONES

| Módulo | Riesgo |
|--------|--------|
| Control de Ingresos (Fase 2) | ❌ NINGUNO (cerrado, no tocar) |
| CxP | ❌ NINGUNO (blindado) |
| Scheduler incremental | ⚠️ Bajo (agregar nuevo job, no modificar existente) |
| Frontend Propinas | ⚠️ Medio (cambiar fuente de datos) |

---

## 16. ARCHIVOS QUE PODRÍAN MODIFICARSE

| Archivo | Cambio Probable |
|---------|-----------------|
| `/app/backend/modules/finanzas/propinas_tpv/repository.py` | Agregar lectura EDARSAHUB |
| `/app/backend/modules/finanzas/propinas_tpv/service.py` | Agregar soporte MPRO |
| `/app/backend/modules/finanzas/propinas_tpv/routes.py` | Mínimo (ya tiene endpoints) |
| `/app/frontend/src/components/PropinasTPV.jsx` | Cambiar API URL si es necesario |
| **NUEVO:** `sync_propinas_softrestaurant.py` | Script de sincronización SR |
| **NUEVO:** `sync_propinas_mpro.py` | Script de sincronización MPRO |
| **NUEVO:** `repository_propinas_edarsahub.py` | Repositorio EDARSAHUB |

---

## 17. ARCHIVOS QUE NO DEBEN TOCARSE

| Archivo | Razón |
|---------|-------|
| `/app/backend/modules/finanzas/cuentas_por_pagar.py` | CxP BLINDADO |
| `/app/backend/modules/finanzas/repository_softrestaurant.py` | CxP BLINDADO + Credenciales hardcodeadas |
| `/app/backend/modules/finanzas/ingresos.py` | Control de Ingresos CERRADO |
| `/app/backend/modules/finanzas/sync_cortes_*.py` | Control de Ingresos CERRADO |
| `/app/backend/core/scheduler/scheduler_manager.py` | Solo agregar job, no modificar existentes |
| `/app/backend/core/scheduler/jobs/sync_ingresos_job.py` | CERRADO |
| Tablero Ejecutivo | BLINDADO |
| Servidores | BLINDADO |
| Operaciones | BLINDADO |
| Comercial | BLINDADO |

---

## 18. PLAN TÉCNICO PROPUESTO POR SUBFASES

### Subfase 3.1 — Preparación EDARSAHUB

| Tarea | Descripción |
|-------|-------------|
| 3.1.1 | Verificar estructura de `propinas_tpv_control` |
| 3.1.2 | Agregar columnas faltantes si es necesario |
| 3.1.3 | Crear índices para performance |
| 3.1.4 | Crear tabla `propinas_tpv_synclog` |

### Subfase 3.2 — Sincronización SoftRestaurant

| Tarea | Descripción |
|-------|-------------|
| 3.2.1 | Crear `sync_propinas_softrestaurant.py` |
| 3.2.2 | Usar `cheques.propinatarjeta` como fuente |
| 3.2.3 | Sincronizar 130° MÉRIDA |
| 3.2.4 | Sincronizar CIENFUEGOS |
| 3.2.5 | Sincronizar LA ESTELAR |
| 3.2.6 | Validar idempotencia |

### Subfase 3.3 — Sincronización MPRO

| Tarea | Descripción |
|-------|-------------|
| 3.3.1 | Crear `sync_propinas_mpro.py` |
| 3.3.2 | Usar `Comanda_Pago.Cp_Propina` donde `Fp_Tipo='04'` |
| 3.3.3 | Sincronizar 130° QUERETARO |
| 3.3.4 | Sincronizar ORIGEN |
| 3.3.5 | Validar totales vs Comanda.Co_Propina |

### Subfase 3.4 — Endpoint EDARSAHUB

| Tarea | Descripción |
|-------|-------------|
| 3.4.1 | Crear `repository_propinas_edarsahub.py` |
| 3.4.2 | Modificar `routes.py` para leer de EDARSAHUB |
| 3.4.3 | Validar que las 5 unidades respondan |
| 3.4.4 | Mantener backward compatibility |

### Subfase 3.5 — Frontend

| Tarea | Descripción |
|-------|-------------|
| 3.5.1 | Verificar que el frontend usa los endpoints existentes |
| 3.5.2 | Actualizar si la estructura de respuesta cambia |
| 3.5.3 | Validar filtro por Unidad de Negocio |

### Subfase 3.6 — Scheduler

| Tarea | Descripción |
|-------|-------------|
| 3.6.1 | Agregar job `sync_propinas_incremental` |
| 3.6.2 | Configurar frecuencia (15-30 min) |
| 3.6.3 | Implementar lock |
| 3.6.4 | Validar no conflicto con `sync_ingresos_incremental` |

### Subfase 3.7 — Carga Histórica

| Tarea | Descripción |
|-------|-------------|
| 3.7.1 | Ejecutar carga histórica 24 meses (si se autoriza) |
| 3.7.2 | Validar totales por unidad |
| 3.7.3 | Documentar diferencias |

---

## 19. CRITERIOS DE ACEPTACIÓN

| # | Criterio |
|---|----------|
| 1 | Las 5 unidades sincronizadas a EDARSAHUB |
| 2 | MPRO implementado correctamente |
| 3 | Dashboard lee desde EDARSAHUB (no MongoDB para datos financieros) |
| 4 | 0 duplicados |
| 5 | Idempotencia con HashOrigen |
| 6 | Scheduler incremental funcionando |
| 7 | Control de Ingresos no afectado |
| 8 | CxP no afectado |
| 9 | Módulos blindados intactos |
| 10 | Documentación actualizada |

---

## 20. CONFIRMACIÓN DE NO REGRESIÓN

| Módulo | Verificación |
|--------|--------------|
| Control de Ingresos | No modificar archivos de Fase 2 |
| Carga histórica 24 meses | No modificar scripts de carga |
| Scheduler incremental de ingresos | No modificar job existente |
| CxP | No tocar `cuentas_por_pagar.py` ni `repository_softrestaurant.py` |
| Tablero Ejecutivo | No modificar |
| Servidores | No modificar |
| Operaciones | No modificar |
| Menús/Tabs/Filtros | No modificar estructura global |

---

## RECOMENDACIÓN FINAL

Se recomienda proceder con la implementación de Fase 3 siguiendo el plan de subfases propuesto. Los principales cambios son:

1. **Agregar soporte MPRO** (actualmente no implementado).
2. **Migrar destino de MongoDB a EDARSAHUB** (siguiendo patrón de Fase 2).
3. **Crear scripts de sincronización** (`sync_propinas_*.py`).
4. **Agregar scheduler incremental** sin afectar el existente.

**Estimación de complejidad:** Media (similar a Fase 2 pero sin crear tablas desde cero).

**Dependencias:** Ninguna bloqueante. Puede ejecutarse en paralelo con otras fases si se respeta el blindaje.

---

## FIRMA DE AUDITORÍA

| Campo | Valor |
|-------|-------|
| **Fase** | Finanzas Fase 3 — Propinas TPV |
| **Tipo** | Auditoría Técnica |
| **Estado** | ✅ COMPLETADA |
| **Fecha** | 2026-05-01 |
| **Ejecutor** | E1 Agent |
| **Documento** | `/app/docs/reports/auditoria_finanzas_fase3_propinas_tpv.md` |

---

**FIN AUDITORÍA TÉCNICA — FASE 3 PROPINAS TPV**
