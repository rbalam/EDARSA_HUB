# EDARSA HUB - Matriz de Clasificación Granular de Datos
## LIVE FIRST vs EDARSA HUB FIRST por Módulo/Tab/Endpoint

**Versión**: 2.0  
**Fecha**: 2026-04-22  
**Estado**: VIGENTE  

---

## NOMENCLATURA Y DEFINICIONES

### Clasificaciones de Fuente de Datos

| Clasificación | Código | Descripción | Latencia Aceptable |
|--------------|--------|-------------|-------------------|
| **LIVE CRÍTICO** | LIVE-C | Consulta SQL externo obligatoria. Un dato de hace 1 minuto puede ser incorrecto | < 1 minuto |
| **SYNC CORTO** | SYNC-S | Sincronización frecuente (cada 5-15 min). Acepta latencia corta | 5-15 minutos |
| **SYNC NOCTURNO** | SYNC-N | Consolidación diaria a EDARSA HUB. Datos del día anterior | 24 horas |
| **EDARSA HUB** | HUB | Lee directamente de EDARSA HUB (SQL Server propio o almacenamiento interno) | N/A (ya consolidado) |

### Riesgo Operativo

| Riesgo | Descripción |
|--------|-------------|
| 🔴 CRÍTICO | Un error puede causar pérdida económica directa o decisión operativa incorrecta |
| 🟡 ALTO | Afecta decisiones operativas del día, pero no es crítico al segundo |
| 🟢 MEDIO | Afecta reportes ejecutivos pero no operación inmediata |
| ⚪ BAJO | Solo afecta análisis histórico o comparativos |

### Regla Arquitectónica

**EDARSA HUB FIRST**: Para datos que NO requieren tiempo real, la fuente de verdad es EDARSA HUB (el sistema central de inteligencia). La tecnología de persistencia (SQL Server EDARSA HUB, almacenamiento interno estructurado, etc.) se decide según el caso, pero la regla arquitectónica habla de EDARSA HUB como cerebro, no de una tecnología específica.

---

## 1. MÓDULO: COMPRAS

### Tab: Dashboard

| Dataset | Clasificación | Justificación Técnica | Fuente Actual | Fuente Objetivo | Riesgo | Política Sync |
|---------|--------------|----------------------|---------------|-----------------|--------|---------------|
| **Requisiciones pendientes** | LIVE-C | Decisión de autorización inmediata. Un pedido autorizado hace 5 min ya no debe aparecer | SQL externo | SQL externo | 🔴 CRÍTICO | N/A (siempre LIVE) |
| **Total compras del período cerrado** | SYNC-N | Dato de períodos anteriores, no cambia. Reduce carga en SQL externo | SQL externo | EDARSA HUB | ⚪ BAJO | Nocturno 03:00 |
| **Total compras mes actual** | SYNC-S | El acumulado del mes actual se actualiza con cada compra, pero toleramos 15 min de latencia | SQL externo | EDARSA HUB + refresh | 🟢 MEDIO | Cada 15 min |
| **Proveedores activos** | SYNC-N | Estadística de últimos 90 días. Cambio diario es aceptable | SQL externo | EDARSA HUB | ⚪ BAJO | Nocturno 03:00 |
| **Top proveedores** | SYNC-N | Ranking histórico. Cambio diario es aceptable | SQL externo | EDARSA HUB | ⚪ BAJO | Nocturno 03:00 |

### Tab: Autorización

| Dataset | Clasificación | Justificación Técnica | Fuente | Riesgo | Política Sync |
|---------|--------------|----------------------|--------|--------|---------------|
| **Lista pedidos vigentes** | LIVE-C | Pedido puede ser cancelado o autorizado en segundos. Cache inaceptable | SQL externo | 🔴 CRÍTICO | N/A |
| **Detalle de pedido activo** | LIVE-C | Estado del pedido cambia en tiempo real | SQL externo | 🔴 CRÍTICO | N/A |
| **Historial de pedidos cerrados** | HUB | Pedidos cerrados ya no cambian. Solo consulta para auditoría | EDARSA HUB | ⚪ BAJO | Post-cierre |

### Tab: Análisis / Auditoría

| Dataset | Clasificación | Justificación Técnica | Fuente | Riesgo | Política Sync |
|---------|--------------|----------------------|--------|--------|---------------|
| **Inventario físico actual** | LIVE-C | Stock actual para cálculo de pedido. Dato crítico al segundo | SQL externo | 🔴 CRÍTICO | N/A |
| **Cálculo de pedido sugerido** | LIVE-C | Usa stock actual + consumos recientes. Debe ser LIVE | SQL externo | 🔴 CRÍTICO | N/A |
| **Movimientos últimos 7 días** | SYNC-S | Movimientos recientes para análisis. Toleramos 15 min | SQL ext + EDARSA HUB | 🟡 ALTO | Cada 15 min |
| **Movimientos mes anterior** | HUB | Período cerrado. Consolidado en EDARSA HUB | EDARSA HUB | ⚪ BAJO | Post-cierre |
| **Consumos históricos** | HUB | Para proyecciones. Consolidado en EDARSA HUB | EDARSA HUB | ⚪ BAJO | Nocturno |

### Tab: Proveedores

| Dataset | Clasificación | Justificación Técnica | Fuente | Riesgo | Política Sync |
|---------|--------------|----------------------|--------|--------|---------------|
| **Facturas últimos 7 días** | SYNC-S | Facturas recientes para seguimiento. Toleramos 15 min | SQL externo | 🟢 MEDIO | Cada 15 min |
| **Facturas > 30 días** | HUB | Facturas antiguas ya procesadas. Sin cambios esperados | EDARSA HUB | ⚪ BAJO | Nocturno |
| **Detalle factura cerrada** | HUB | Documento fiscal cerrado. Inmutable | EDARSA HUB | ⚪ BAJO | Post-cierre |

---

## 2. MÓDULO: COMERCIAL

### Tablero Ejecutivo

| Dataset | Clasificación | Justificación Técnica | Fuente Actual | Fuente Objetivo | Riesgo | Política Sync |
|---------|--------------|----------------------|---------------|-----------------|--------|---------------|
| **ventas_dia (sin corte)** | LIVE-C | Ventas del turno actual SIN CORTE. Cada venta nueva debe reflejarse inmediatamente | SQL externo (tempcheques) | SQL externo | 🔴 CRÍTICO | N/A |
| **Ventas mes actual (días cerrados)** | SYNC-S | Ventas de días ya cortados dentro del mes actual. Toleramos 15 min | SQL externo | EDARSA HUB + refresh | 🟢 MEDIO | Cada 15 min |
| **Ventas mes actual (hoy sin corte)** | LIVE-C | El día de hoy antes del corte Z. Crítico | SQL externo | SQL externo | 🔴 CRÍTICO | N/A |
| **Ventas mes anterior** | HUB | Período cerrado. Ya consolidado | SQL externo | EDARSA HUB | ⚪ BAJO | Post-cierre |
| **Ventas año anterior** | HUB | Período cerrado hace 12+ meses. Inmutable | SQL externo | EDARSA HUB | ⚪ BAJO | Carga inicial |
| **Proyección del mes** | HUB | Cálculo basado en días cerrados. Actualiza con cada cierre | EDARSA HUB | EDARSA HUB | 🟢 MEDIO | Post-corte |

### Tab: Dashboard por Servidor

| Dataset | Clasificación | Justificación Técnica | Fuente | Riesgo | Política Sync |
|---------|--------------|----------------------|--------|--------|---------------|
| **KPIs del día actual** | LIVE-C | Monitoreo operativo en tiempo real | SQL externo | 🟡 ALTO | N/A |
| **KPIs días anteriores del mes** | SYNC-S | Ya cortados, pero queremos frescura razonable | EDARSA HUB + refresh | 🟢 MEDIO | Cada 15 min |
| **KPIs meses anteriores** | HUB | Consolidados y cerrados | EDARSA HUB | ⚪ BAJO | Post-cierre |
| **Comparativo año anterior** | HUB | Dato histórico inmutable | EDARSA HUB | ⚪ BAJO | Carga inicial |

### Tab: Reporte PAX

| Dataset | Clasificación | Justificación Técnica | Fuente | Riesgo | Política Sync |
|---------|--------------|----------------------|--------|--------|---------------|
| **PAX del día (hoy)** | LIVE-C | Comensales actuales para decisiones de servicio | SQL externo | 🟡 ALTO | N/A |
| **PAX histórico** | HUB | Estadística para análisis de patrones | EDARSA HUB | ⚪ BAJO | Nocturno |

### Tab: Por Hora/Día

| Dataset | Clasificación | Justificación Técnica | Fuente | Riesgo | Política Sync |
|---------|--------------|----------------------|--------|--------|---------------|
| **Ventas por hora (hoy)** | LIVE-C | Análisis de operación en curso | SQL externo | 🟡 ALTO | N/A |
| **Patrones históricos por hora** | HUB | Para comparar vs comportamiento típico | EDARSA HUB | ⚪ BAJO | Nocturno |

---

## 3. MÓDULO: OPERACIONES / INVENTARIOS

| Dataset | Clasificación | Justificación Técnica | Fuente | Riesgo | Política Sync |
|---------|--------------|----------------------|--------|--------|---------------|
| **Stock actual por producto** | LIVE-C | Para decisión de reposición o transferencia | SQL externo | 🔴 CRÍTICO | N/A |
| **Alertas de stock mínimo** | LIVE-C | Trigger para acción operativa inmediata | SQL externo | 🔴 CRÍTICO | N/A |
| **Movimientos del día** | SYNC-S | Trazabilidad del día. Toleramos 5-10 min | SQL ext + EDARSA HUB | 🟡 ALTO | Cada 10 min |
| **KPIs de inventario (merma, rotación)** | HUB | Indicadores calculados sobre datos cerrados | EDARSA HUB | 🟢 MEDIO | Nocturno |
| **Historial de conteos físicos** | HUB | Registro de inventarios pasados | EDARSA HUB | ⚪ BAJO | Post-conteo |

---

## 4. POLÍTICA DE SINCRONIZACIÓN Y ACTUALIZACIÓN HISTÓRICA

### 4.1 Tipos de Sincronización

| Tipo | Frecuencia | Ventana | Datasets Aplicables |
|------|------------|---------|---------------------|
| **SYNC-S (Corto)** | Cada 10-15 min | Últimas 24-48 horas | Ventas día actual (cortadas), Movimientos recientes, Facturas recientes |
| **SYNC-N (Nocturno)** | Diario 03:00 | Día anterior completo | KPIs diarios, Consumos, Patrones por hora |
| **CARGA INICIAL** | Una vez | Últimos 24 meses | Histórico año anterior, Baseline de comparativos |
| **POST-CIERRE** | Por evento | Documento específico | Pedidos cerrados, Facturas procesadas, Cortes Z |

### 4.2 Política de Actualización Histórica (MACROFASE 2)

#### UPSERT OBLIGATORIO
- Toda inserción a EDARSA HUB debe usar UPSERT con clave única (server_id + fecha + identificador)
- Si el registro ya existe, se actualiza con los nuevos valores
- Nunca duplicar registros

#### VENTANA DESLIZANTE DE RELECTURA
```
SYNC-S: Últimas 48 horas (captura correcciones del día anterior)
SYNC-N: Últimos 7 días (captura ajustes contables tardíos)
Reconciliación mensual: Mes anterior completo
```

#### PERÍODOS ABIERTOS vs CERRADOS
| Estado | Definición | Comportamiento |
|--------|------------|----------------|
| **ABIERTO** | El día/mes aún puede tener cambios (no hay corte Z, cierre contable) | SYNC-S activo, datos se refrescan constantemente |
| **CERRADO** | Ya hubo corte Z o cierre contable oficial | Dato inmutable salvo reconciliación explícita |
| **RECONCILIADO** | Período cerrado que fue ajustado retroactivamente | Marca de auditoría + timestamp de reconciliación |

#### MANEJO DE CAMBIOS RETROACTIVOS
1. **Detección**: Comparar hash o timestamp de última modificación
2. **Registro**: Guardar versión anterior en `_historico` antes de actualizar
3. **Auditoría**: Log con usuario, timestamp, valores anteriores y nuevos
4. **Alerta**: Notificar si el cambio afecta reportes ya exportados

#### RECONCILIACIÓN HISTÓRICA
- **Frecuencia**: Mensual (día 5 del mes siguiente)
- **Alcance**: Mes anterior completo
- **Proceso**:
  1. Leer todos los registros del mes desde SQL externo
  2. Comparar vs EDARSA HUB
  3. Aplicar diferencias con marca de reconciliación
  4. Generar reporte de discrepancias

---

## 5. PLAN DE IMPLEMENTACIÓN CORREGIDO

### MACROFASE 1: Correcciones Críticas (Semana 1-2)

1. **Circuit Breaker Tablero Ejecutivo**
   - Separar LIVE (ventas_dia, mes actual hoy) de HUB (históricos)
   - No bloquear reintentos para datos LIVE

2. **Separación LIVE/HUB en Tablero**
   - LIVE-C: ventas_dia, ventas mes actual (solo hoy sin corte)
   - SYNC-S: ventas mes actual (días cerrados)
   - HUB: mes anterior, año anterior

### MACROFASE 2: Consolidación en EDARSA HUB (Semana 3-4)

1. **Diseño de Esquema en EDARSA HUB**
   - Tabla/colección `kpis_comercial_diarios`
   - Índice único: (server_id, fecha, sucursal_id)
   - Campos de auditoría: created_at, updated_at, source, reconciled_at

2. **Scheduler de Sincronización**
   - SYNC-S (cada 15 min): Últimas 48 horas
   - SYNC-N (03:00): Consolidación día anterior
   - Reconciliación (día 5): Mes anterior completo

3. **Migración de Endpoints**
   - Tablero Ejecutivo: año anterior → EDARSA HUB
   - Dashboard: KPIs históricos → EDARSA HUB
   - Compras: Total compras período cerrado → EDARSA HUB

### LO QUE NO SE TOCA (LIVE CRÍTICO OBLIGATORIO)

| Endpoint | Razón |
|----------|-------|
| Auditoría operativa | Stock ACTUAL para cálculo |
| Cálculo de pedido | Decisión basada en stock ACTUAL |
| Inventarios físicos | Existencias ACTUALES |
| Pedidos vigentes | Estado cambia en segundos |
| Ventas del día (sin corte) | Monitoreo operativo en tiempo real |

---

## 6. RESUMEN DE DESVIACIONES CORREGIDAS

| Problema Original | Corrección |
|------------------|------------|
| "MongoDB first" como regla | **EDARSA HUB FIRST** - MongoDB es implementación, no arquitectura |
| "Mes actual LIVE" sin justificación | Separado en: hoy sin corte (LIVE-C), días cerrados (SYNC-S) |
| "Scheduler nocturno" genérico | Definido por tipo: SYNC-S (15 min), SYNC-N (03:00), POST-CIERRE |
| Sin política de actualización | UPSERT obligatorio, ventana deslizante, reconciliación mensual |

---

## HISTORIAL DE CAMBIOS

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-04-22 | 2.0 | Corrección arquitectónica: EDARSA HUB FIRST, política de sync detallada |
| 2026-04-22 | 1.0 | Documento inicial |
