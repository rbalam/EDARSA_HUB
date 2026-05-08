# AUDITORÍA TÉCNICA — FASE 4 TESORERÍA

**Fecha:** 1 Mayo 2026  
**Estado:** AUDITORÍA COMPLETADA - PENDIENTE AUTORIZACIÓN PARA IMPLEMENTAR

---

## 1. RESUMEN EJECUTIVO

### Estado Actual de Tesorería

El módulo actual denominado "Tesorería" en EDARSAHUB **NO es un módulo de tesorería completo**. Actualmente solo implementa:

- **Cuadre de Cortes Z**: Conciliación de efectivo en caja vs. cortes de venta

### Lo que NO existe actualmente:
- ❌ Saldos bancarios
- ❌ Cuentas bancarias configuradas (tabla vacía)
- ❌ Depósitos registrados (tabla vacía)
- ❌ Pagos a proveedores (tabla vacía)
- ❌ Conciliación bancaria
- ❌ Flujo de efectivo proyectado
- ❌ Calendario de pagos
- ❌ Layouts bancarios

### Hallazgo Crítico

| Componente | Fuente Actual | Debería Ser |
|------------|---------------|-------------|
| Cuadres de Cortes Z | **MongoDB** | EDARSAHUB |
| Cortes Z origen | SQL Legacy (SR/MPRO) | OK |
| Depósitos | No existe | EDARSAHUB |
| Pagos | No existe | EDARSAHUB |
| Saldos Bancarios | No existe | EDARSAHUB |

**⚠️ ALERTA**: El repositorio de cuadres (`repository_cuadres_z.py`) almacena en **MongoDB**, violando la máxima de que MongoDB no debe ser fuente de verdad financiera.

---

## 2. ESTADO ACTUAL DEL TAB TESORERÍA

### Ubicación Frontend

| Archivo | Descripción |
|---------|-------------|
| `/app/frontend/src/components/TesoreriaCorteZ.jsx` | Componente principal |
| `/app/frontend/src/components/tesoreria/` | Subcomponentes y hooks |
| `/app/frontend/src/components/tesoreria/useTesoreriaCorteZData.js` | Hook de datos |
| `/app/frontend/src/components/tesoreria/TesoreriaCorteZComponents.jsx` | Subcomponentes UI |

### Funcionalidad Actual

1. **Dashboard de Cortes Z pendientes** - Lista cortes sin cuadrar
2. **Conteo de efectivo** - Captura de billetes y monedas
3. **Ficha de depósito** - Carga de imagen (OCR pendiente)
4. **Validación de fechas** - Día hábil siguiente

### Filtros Actuales

- Por unidad de negocio
- Por fechas
- Por estado (pendiente, cuadrado, descuadre)

---

## 3. ENDPOINTS ACTUALES

### Router: `/api/finanzas/tesoreria`

| Endpoint | Método | Descripción | Fuente de Datos |
|----------|--------|-------------|-----------------|
| `/cortes-z` | GET | Lista cortes Z disponibles | SQL Legacy (SR/MPRO) |
| `/cortes-z/{sucursal}/{folio}` | GET | Detalle de un corte | SQL Legacy |
| `/cuadres` | GET | Lista cuadres registrados | **MongoDB** |
| `/cuadres/resumen` | GET | Estadísticas de cuadres | **MongoDB** |
| `/cuadres/{id}` | GET | Detalle de cuadre | **MongoDB** |
| `/cuadres` | POST | Crear cuadre | **MongoDB** |
| `/cuadres/{id}` | PUT | Actualizar cuadre | **MongoDB** |
| `/cuadres/{id}` | DELETE | Eliminar cuadre | **MongoDB** |
| `/cuadres/{id}/ficha-deposito` | POST | Subir ficha depósito | **MongoDB** |
| `/cuadres/{id}/validar-ficha` | POST | Validar ficha | **MongoDB** |
| `/sucursales` | GET | Lista sucursales | Server Registry |

---

## 4. FRONTEND ACTUAL

### Componente Principal

```
TesoreriaCorteZ.jsx
├── useTesoreriaCorteZData (hook)
├── ResumenCards
├── CorteCard
├── ConteoEfectivo
├── FichaDepositoForm
├── ComparativaCard
└── EmptyState
```

### Estados de Cuadre

| Estado | Color | Descripción |
|--------|-------|-------------|
| PENDIENTE | Amarillo | Sin iniciar cuadre |
| EN_PROCESO | Azul | Cuadre iniciado |
| CUADRADO | Verde | Efectivo cuadra |
| DESCUADRE | Rojo | Diferencia detectada |

---

## 5. FUENTE ACTUAL DE DATOS

### MongoDB (VIOLACIÓN DE MÁXIMA)

| Collection | Contenido | Registros |
|------------|-----------|-----------|
| `tesoreria_cuadres_z` | Cuadres de cortes Z | Desconocido |

**Archivo**: `/app/backend/modules/finanzas/repository_cuadres_z.py`

```python
# Línea 66-70
class RepositoryCuadresZ:
    def __init__(self):
        self.collection_name = "tesoreria_cuadres_z"
    
    @property
    def collection(self):
        return get_db()[self.collection_name]  # MongoDB
```

### SQL Legacy (Correcto para origen)

- SoftRestaurant: Cortes Z vía `repository_cortes_z.py`
- MPRO: Cortes Z vía `repository_cortes_z.py`

---

## 6. CONFIRMACIÓN DE USO/NO USO DE MONGODB

| Componente | Usa MongoDB | Debería Usar |
|------------|-------------|--------------|
| Cuadres de Cortes Z | ✅ SÍ (VIOLACIÓN) | EDARSAHUB |
| Autenticación | ✅ SÍ (Aceptable) | N/A |
| Scheduler Locks | ✅ SÍ (Aceptable) | N/A |
| Control de Ingresos | ❌ NO | EDARSAHUB ✅ |
| Propinas TPV | ❌ NO | EDARSAHUB ✅ |
| CxP | ❌ NO | EDARSAHUB ✅ |

**⚠️ Los cuadres de Cortes Z actualmente almacenan en MongoDB, lo cual viola la máxima "MongoDB NO es fuente de verdad financiera".**

---

## 7. CONFIRMACIÓN DE USO DE EDARSAHUB

### Tablas Existentes para Tesorería

| Tabla | Registros | Estado |
|-------|-----------|--------|
| `Global_Cat_Bancos` | 5 | Con datos (catálogo) |
| `Finanzas_Cat_CuentasBancarias` | 0 | **VACÍA** |
| `Finanzas_Depositos` | 0 | **VACÍA** |
| `Finanzas_Pagos` | 0 | **VACÍA** |
| `Finanzas_EstatusPago` | 5 | Con datos (catálogo) |
| `Finanzas_CuentasPorPagar` | 25 | Con datos (demo/prueba) |
| `Proveedor_Bancos` | 0 | **VACÍA** |
| `Proveedor_CuentasBancarias` | 0 | **VACÍA** |

### Tablas Relacionadas Ya Pobladas

| Tabla | Registros | Propósito |
|-------|-----------|-----------|
| `Finanzas_CortesCaja` | 3,964 | Control de Ingresos |
| `propinas_tpv_control` | 71,084 | Propinas TPV |
| `Finanzas_CuentasPorPagar` | 25 | CxP existente |

---

## 8. TABLAS EDARSAHUB EXISTENTES

### Estructura de Tablas de Tesorería

#### `Finanzas_Cat_CuentasBancarias` (0 registros)
```sql
- CuentaBancariaID (PK)
- EmpresaID
- BancoID (FK → Global_Cat_Bancos)
- NumeroCuenta
- CLABE
- Alias
- Moneda
- EsCuentaPrincipal
- Activo
- FechaAlta
```

#### `Finanzas_Depositos` (0 registros)
```sql
- DepositoID (PK)
- CuentaBancariaID (FK)
- SucursalID
- FechaDeposito
- MontoDeposito
- TipoDeposito
- NumeroReferencia
- CorteCajaID (FK → Finanzas_CortesCaja)
- Conciliado
- FechaConciliacion
- ...
```

#### `Finanzas_Pagos` (0 registros)
```sql
- PagoID (PK)
- CuentaPorPagarID (FK)
- FechaPago
- MontoPagado
- FormaPagoID
- CuentaBancariaID
- NumeroReferencia
- Observaciones
- Activo
- FechaAlta
```

---

## 9. DATOS ACTUALES: REALES/DEMO/VACÍOS

| Tabla | Estado | Observación |
|-------|--------|-------------|
| Global_Cat_Bancos | ✅ REAL | 5 bancos (BANAMEX, BBVA, SANTANDER, HSBC, BANORTE) |
| Finanzas_EstatusPago | ✅ REAL | 5 estatus |
| Finanzas_Cat_CuentasBancarias | ❌ VACÍA | Requiere configuración |
| Finanzas_Depositos | ❌ VACÍA | Requiere implementación |
| Finanzas_Pagos | ❌ VACÍA | Requiere implementación |
| Finanzas_CuentasPorPagar | ⚠️ DEMO | 25 registros de prueba |

---

## 10. ANÁLISIS POR LAS 5 UNIDADES

### Datos Existentes en EDARSAHUB

| Unidad | Control de Ingresos | Propinas TPV | CxP |
|--------|---------------------|--------------|-----|
| 130° MÉRIDA | 721 cortes | 15,154 reg | Parcial |
| CIENFUEGOS | 853 cortes | 19,918 reg | Parcial |
| LA ESTELAR | 311 cortes | 9,463 reg | Parcial |
| 130° QRO | 715 cortes | 13,793 reg | Parcial |
| ORIGEN | 1,294 cortes | 12,756 reg | Parcial |
| **TOTAL** | **3,894 cortes** | **71,084 reg** | **25 docs** |

### Totales Financieros

| Concepto | Monto |
|----------|-------|
| Efectivo (Cortes) | $191,393,978.43 |
| Tarjeta (Cortes) | $313,090,653.55 |
| Propinas TPV | $37,123,666.27 |
| CxP Pendiente | $500,331.20 |

---

## 11. RELACIÓN CON CONTROL DE INGRESOS

### Conexión Actual

| Aspecto | Estado |
|---------|--------|
| Tabla origen | `Finanzas_CortesCaja` |
| Campos relevantes | TotalEfectivo, TotalTarjeta*, FechaDeposito* |
| Relación con depósitos | `CorteCajaID` en `Finanzas_Depositos` |

### Flujo Esperado

```
Corte de Caja (Finanzas_CortesCaja)
    ↓
Cuadre de Efectivo (actualmente en MongoDB)
    ↓
Depósito Bancario (Finanzas_Depositos - VACÍA)
    ↓
Conciliación Bancaria (No existe)
```

### Campos de Depósito en Cortes de Caja

La tabla `Finanzas_CortesCaja` ya tiene campos para seguimiento de depósitos:
- `FechaDepositoEfectivo`
- `FechaDepositoDebito`
- `FechaDepositoCredito`
- `DepositadoEfectivo` (bit)
- `DepositadoDebito` (bit)
- `DepositadoCredito` (bit)

---

## 12. RELACIÓN CON PROPINAS TPV

### Conexión Esperada

| Aspecto | Estado |
|---------|--------|
| Tabla origen | `propinas_tpv_control` |
| Relación | Por fecha_corte y UnidadNegocioID |
| Integración actual | NO existe |

### Flujo Esperado

```
Propinas TPV (propinas_tpv_control)
    ↓
Corte de Caja incluye Propinas
    ↓
Depósito de Propinas (separado o junto con venta)
    ↓
Pago a Meseros (RH o Tesorería)
```

---

## 13. RELACIÓN CON CxP

### Conexión Actual

| Aspecto | Estado |
|---------|--------|
| Tabla | `Finanzas_CuentasPorPagar` |
| Registros | 25 (demo/prueba) |
| Pagos registrados | $162,381.02 de $662,712.22 |
| Saldo pendiente | $500,331.20 |

### Flujo Esperado

```
CxP (Finanzas_CuentasPorPagar)
    ↓
Autorización de Pago
    ↓
Registro en Finanzas_Pagos
    ↓
Afectación de Saldo Bancario
    ↓
Conciliación Bancaria
```

---

## 14. RELACIÓN CON BANCOS/CUENTAS BANCARIAS

### Estado Actual

| Componente | Estado |
|------------|--------|
| Catálogo de Bancos | ✅ 5 bancos configurados |
| Cuentas Bancarias Empresa | ❌ VACÍA |
| Cuentas Bancarias Proveedores | ❌ VACÍA |
| Saldos Bancarios | ❌ NO EXISTE |

### Configuración Requerida

Para activar Tesorería se necesita:
1. Configurar cuentas bancarias de la empresa por unidad
2. Configurar cuentas bancarias de proveedores
3. Capturar saldos iniciales
4. Implementar flujo de movimientos

---

## 15. RELACIÓN CON CONCILIACIÓN BANCARIA

### Estado Actual

- **NO EXISTE** funcionalidad de conciliación bancaria

### Componentes Requeridos

1. Importación de estados de cuenta bancarios
2. Matching automático depósitos vs. movimientos
3. Partidas en conciliación
4. Reporte de conciliación

---

## 16. RELACIÓN CON PAGOS PROGRAMADOS

### Estado Actual

- **NO EXISTE** funcionalidad de pagos programados

### Componentes Requeridos

1. Calendario de vencimientos de CxP
2. Programación de pagos
3. Autorización de pagos
4. Ejecución de pagos (layouts bancarios)

---

## 17. RELACIÓN CON FLUJO PROYECTADO

### Estado Actual

- **NO EXISTE** funcionalidad de flujo de efectivo

### Componentes Requeridos

1. Proyección de ingresos (basado en histórico de ventas)
2. Proyección de egresos (CxP vencimientos)
3. Saldo proyectado por día/semana/mes
4. Alertas de déficit

---

## 18. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Migración de cuadres MongoDB → EDARSAHUB | Alta | Alto | Crear tabla y migrar datos existentes |
| Afectación a frontend de Tesorería actual | Media | Alto | Cambiar repositorio sin cambiar API |
| Inconsistencia con Control de Ingresos | Media | Alto | Validar relación CorteCajaID |
| Pérdida de cuadres existentes | Baja | Alto | Backup antes de migración |
| Afectación a scheduler existente | Baja | Bajo | No tocar scheduler de propinas/ingresos |

---

## 19. POSIBLES AFECTACIONES

| Componente | Afectación | Nivel |
|------------|------------|-------|
| Frontend TesoreriaCorteZ | Ninguna (misma API) | ✅ NINGUNO |
| API /finanzas/tesoreria | Cambio de repositorio | ⚠️ BAJO |
| Control de Ingresos | Ninguna directa | ✅ NINGUNO |
| Propinas TPV | Ninguna directa | ✅ NINGUNO |
| CxP | Integración nueva | ⚠️ BAJO |
| Scheduler | Ninguna | ✅ NINGUNO |
| MongoDB | Reducción de uso | ✅ NINGUNO |
| EDARSAHUB | Nuevas tablas | ⚠️ BAJO |

---

## 20. ARCHIVOS QUE PODRÍAN MODIFICARSE

### Backend (Modificar)

| Archivo | Cambio Propuesto |
|---------|------------------|
| `/app/backend/modules/finanzas/repository_cuadres_z.py` | Cambiar de MongoDB a EDARSAHUB |
| `/app/backend/modules/finanzas/tesoreria.py` | Agregar endpoints para depósitos, pagos |
| `/app/backend/modules/finanzas/tesoreria_models.py` | Nuevos modelos |

### Backend (Crear)

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/modules/finanzas/tesoreria/repository_edarsahub.py` | Repositorio EDARSAHUB |
| `/app/backend/modules/finanzas/tesoreria/routes_depositos.py` | Rutas de depósitos |
| `/app/backend/modules/finanzas/tesoreria/routes_pagos.py` | Rutas de pagos |
| `/app/backend/modules/finanzas/tesoreria/routes_conciliacion.py` | Rutas de conciliación |

### Frontend (Potencialmente Crear)

| Archivo | Propósito |
|---------|-----------|
| `DepositosBancarios.jsx` | Gestión de depósitos |
| `ConciliacionBancaria.jsx` | Conciliación |
| `FlujoCaja.jsx` | Flujo proyectado |
| `CalendarioPagos.jsx` | Programación de pagos |

---

## 21. ARCHIVOS QUE NO DEBEN TOCARSE

### Blindados

| Archivo/Módulo | Razón |
|----------------|-------|
| `/app/backend/modules/finanzas/repository_softrestaurant.py` | BLINDADO por usuario |
| `/app/backend/modules/finanzas/sync_propinas_*.py` | Fase 3 cerrada |
| `/app/backend/modules/finanzas/propinas_tpv/` | Fase 3 cerrada |
| `/app/backend/core/scheduler/jobs/sync_ingresos_job.py` | Fase 2 cerrada |
| `/app/backend/core/scheduler/jobs/sync_propinas_tpv_job.py` | Fase 3 cerrada |
| Tablero Ejecutivo | Blindado |
| Servidores | Blindado |
| Operaciones | Blindado |
| Compras | Blindado |
| Comercial | Blindado |
| RBAC | Blindado |
| Autenticación | Blindado |

---

## 22. PLAN TÉCNICO PROPUESTO POR SUBFASES

### Subfase 4.1 — Preparación EDARSAHUB (Sin afectar MongoDB)

**Objetivo:** Crear tabla de cuadres en EDARSAHUB

**Acciones:**
1. Crear tabla `Finanzas_Cuadres_CorteZ` en EDARSAHUB
2. Verificar estructura de `Finanzas_Cat_CuentasBancarias`
3. Verificar estructura de `Finanzas_Depositos`
4. NO modificar MongoDB aún

**Entregable:** Script SQL ejecutado

---

### Subfase 4.2 — Migración de Cuadres MongoDB → EDARSAHUB

**Objetivo:** Mover datos existentes de MongoDB a EDARSAHUB

**Acciones:**
1. Backup de collection `tesoreria_cuadres_z`
2. Script de migración
3. Validar integridad
4. NO eliminar MongoDB aún (modo dual)

**Entregable:** Cuadres migrados y validados

---

### Subfase 4.3 — Nuevo Repositorio EDARSAHUB

**Objetivo:** Crear repositorio que lea/escriba en EDARSAHUB

**Acciones:**
1. Crear `/app/backend/modules/finanzas/tesoreria/repository_edarsahub.py`
2. Implementar mismas funciones que `repository_cuadres_z.py`
3. Agregar configuración para elegir fuente
4. Validar en modo lectura

**Entregable:** Repositorio funcional

---

### Subfase 4.4 — Cambio de Fuente (MongoDB → EDARSAHUB)

**Objetivo:** Activar EDARSAHUB como fuente principal

**Acciones:**
1. Modificar `tesoreria.py` para usar nuevo repositorio
2. Validar frontend sigue funcionando
3. Desactivar escritura a MongoDB
4. Mantener lectura dual por seguridad

**Entregable:** Sistema usando EDARSAHUB

---

### Subfase 4.5 — Configuración de Cuentas Bancarias

**Objetivo:** Configurar cuentas bancarias por unidad

**Acciones:**
1. Endpoint CRUD para cuentas bancarias
2. Frontend de configuración (admin)
3. Asociar cuentas a unidades
4. Capturar saldos iniciales

**Entregable:** Cuentas bancarias configuradas

---

### Subfase 4.6 — Módulo de Depósitos

**Objetivo:** Registrar depósitos bancarios

**Acciones:**
1. Endpoint CRUD para depósitos
2. Relación con cortes de caja
3. Frontend de registro de depósitos
4. Validación de montos

**Entregable:** Depósitos funcionando

---

### Subfase 4.7 — Integración con Control de Ingresos

**Objetivo:** Conectar depósitos con cortes de caja

**Acciones:**
1. Actualizar campos `FechaDeposito*` y `Depositado*` en `Finanzas_CortesCaja`
2. Dashboard de pendientes de depósito
3. Alertas de retrasos

**Entregable:** Flujo completo Corte → Depósito

---

### Subfase 4.8 — Módulo de Pagos (Tesorería)

**Objetivo:** Registrar pagos a proveedores

**Acciones:**
1. Endpoint CRUD para pagos
2. Relación con CxP
3. Actualización automática de saldos
4. Frontend de registro de pagos

**Entregable:** Pagos funcionando

---

### Subfase 4.9 — Conciliación Bancaria

**Objetivo:** Conciliar movimientos vs. estados de cuenta

**Acciones:**
1. Importación de estados de cuenta (CSV/Excel)
2. Matching automático
3. Partidas en conciliación
4. Reporte de conciliación

**Entregable:** Conciliación básica

---

### Subfase 4.10 — Flujo de Efectivo Proyectado

**Objetivo:** Proyectar necesidades de efectivo

**Acciones:**
1. Proyección de ingresos (histórico ventas)
2. Proyección de egresos (vencimientos CxP)
3. Dashboard de flujo proyectado
4. Alertas de déficit

**Entregable:** Flujo proyectado

---

### Subfase 4.11 — Alertas WhatsApp/Correo

**Objetivo:** Notificaciones de eventos críticos

**Acciones:**
1. Integración con servicio de mensajería
2. Configuración de umbrales
3. Eventos: descuadre, vencimiento próximo, déficit proyectado

**NO Slack** - Solo WhatsApp o Correo

**Entregable:** Alertas configuradas

---

## 23. CRITERIOS DE ACEPTACIÓN

### Por Subfase

| Subfase | Criterio |
|---------|----------|
| 4.1 | Tablas creadas en EDARSAHUB |
| 4.2 | 100% cuadres migrados, 0 pérdidas |
| 4.3 | Repositorio pasa tests unitarios |
| 4.4 | Frontend funciona idéntico |
| 4.5 | 5 unidades con cuentas configuradas |
| 4.6 | Depósitos se registran correctamente |
| 4.7 | Cortes muestran estado de depósito |
| 4.8 | Pagos actualizan CxP correctamente |
| 4.9 | Conciliación muestra partidas |
| 4.10 | Proyección a 30 días visible |
| 4.11 | Alertas se envían correctamente |

### Globales

- ✅ MongoDB NO es fuente de verdad financiera
- ✅ EDARSAHUB es el cerebro
- ✅ 5/5 unidades validadas
- ✅ No regresión en Control de Ingresos
- ✅ No regresión en Propinas TPV
- ✅ No regresión en CxP
- ✅ No tocar módulos blindados

---

## 24. CONFIRMACIÓN DE NO REGRESIÓN

### Módulos que NO se afectarán

| Módulo | Confirmación |
|--------|--------------|
| Control de Ingresos (Fase 2) | ✅ NO SE TOCA |
| Propinas TPV (Fase 3) | ✅ NO SE TOCA |
| Scheduler de Ingresos | ✅ NO SE TOCA |
| Scheduler de Propinas | ✅ NO SE TOCA |
| CxP existente | ✅ SOLO INTEGRACIÓN |
| Tablero Ejecutivo | ✅ NO SE TOCA |
| Servidores | ✅ NO SE TOCA |
| Operaciones | ✅ NO SE TOCA |
| Compras | ✅ NO SE TOCA |
| Comercial | ✅ NO SE TOCA |
| RBAC | ✅ NO SE TOCA |
| Autenticación | ✅ NO SE TOCA |
| repository_softrestaurant.py | ✅ NO SE TOCA |

---

## RECOMENDACIÓN FINAL

### Priorización Sugerida

1. **URGENTE**: Migrar cuadres de MongoDB a EDARSAHUB (Subfases 4.1-4.4)
   - Elimina violación de máxima
   - Bajo riesgo
   - Alto impacto en arquitectura

2. **IMPORTANTE**: Configurar cuentas bancarias y depósitos (Subfases 4.5-4.7)
   - Habilita operación real de Tesorería
   - Cierra ciclo Venta → Depósito

3. **DESEABLE**: Pagos, Conciliación, Flujo (Subfases 4.8-4.10)
   - Funcionalidad completa de Tesorería
   - Mayor complejidad

4. **FUTURO**: Alertas WhatsApp/Correo (Subfase 4.11)
   - Requiere integración externa
   - NO Slack

---

**FIN DE AUDITORÍA TÉCNICA — FASE 4 TESORERÍA**

**Siguiente paso:** Solicitar autorización para iniciar implementación de Subfases 4.1-4.4 (Migración de cuadres MongoDB → EDARSAHUB).
