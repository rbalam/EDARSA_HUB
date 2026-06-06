# DIAGNÓSTICO: Origen de Comercial_KPIs_Diarios_v2 y Relación con Sync_Sales / Sync_PAX_Detalle

**Fecha:** 2026-06-02
**Ejecutado por:** Agente E1
**Metodología:** Grep codebase + Queries SQL directas

---

## RESUMEN EJECUTIVO

| Tabla | Registros | Estado | Rol en Arquitectura |
|-------|-----------|--------|---------------------|
| `Comercial_KPIs_Diarios_v2` | **3,376** | ✅ OPERATIVA | Tabla principal de KPIs agregados |
| `Sync_Sales` | **0** | ⚠️ VACÍA | Tabla de tickets individuales (no usada en Fase 1) |
| `Sync_PAX_Detalle` | **0** | ⚠️ VACÍA | Tabla de comensales detallados (no usada en Fase 1) |

---

## 1. ORIGEN DE LOS DATOS EN Comercial_KPIs_Diarios_v2

### 1.1 Fuentes Identificadas

| Fuente | Sistema | Registros | Ventas Totales | Rango |
|--------|---------|-----------|----------------|-------|
| `SQL_LIVE` | SOFTRESTAURANT | 1,862 | $287,433,748.00 | 2024-05 a 2026-06 |
| `SQL_LIVE` | MPRO | 1,514 | $142,962,445.99 | 2024-05 a 2026-06 |

### 1.2 Unidades de Negocio

| Unidad | Sistema | Registros | Ventas | Rango |
|--------|---------|-----------|--------|-------|
| CIENFUEGOS | SOFTRESTAURANT | 757 | $138,913,136.00 | 2024-05 a 2026-06 |
| 130° MERIDA | SOFTRESTAURANT | 757 | $119,756,236.00 | 2024-05 a 2026-06 |
| 130° QUERETARO | MPRO | 758 | $93,743,336.00 | 2024-05 a 2026-06 |
| ORIGEN | MPRO | 756 | $49,219,109.99 | 2024-05 a 2026-06 |
| LA ESTELAR | SOFTRESTAURANT | 348 | $28,764,376.00 | 2025-06 a 2026-06 |

### 1.3 Flujo de Datos Identificado

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────────────┐
│   SOFTRESTAURANT    │     │        MPRO         │     │                             │
│   (DB Remota)       │     │    (API Remota)     │     │                             │
└─────────┬───────────┘     └──────────┬──────────┘     │                             │
          │                            │                │                             │
          └──────────┬─────────────────┘                │                             │
                     ▼                                  │                             │
          ┌──────────────────────┐                      │                             │
          │  sync_comercial_     │                      │    Comercial_KPIs_Diarios_v2│
          │  edarsahub.py        │ ─────DIRECTO────────▶│                             │
          │  (Job de Sync)       │                      │    (3,376 registros)        │
          └──────────────────────┘                      │                             │
                     │                                  └─────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  Sync_Sales          │ ◄── NO SE USA EN FASE 1
          │  (VACÍA)             │
          └──────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  Sync_PAX_Detalle    │ ◄── NO SE USA EN FASE 1
          │  (VACÍA)             │
          └──────────────────────┘
```

---

## 2. ANÁLISIS DEL CÓDIGO FUENTE

### 2.1 Archivos que Escriben a `Comercial_KPIs_Diarios_v2`

| Archivo | Operación | Propósito |
|---------|-----------|-----------|
| `backend/modules/comercial_v2/repository_comercial_edarsahub.py` | INSERT/UPDATE | **Principal** - Sync de KPIs desde SQL_LIVE |
| `backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py` | INSERT/UPDATE | Job scheduler alternativo |
| `backend/api/admin_data_quality.py` | UPDATE | Correcciones de calidad de datos |

### 2.2 Archivos que Escriben a `Sync_Sales` / `Sync_PAX_Detalle`

| Archivo | Tabla | Línea | Estado |
|---------|-------|-------|--------|
| `inteligencia_comercial_sync_job.py` | Sync_Sales | L252 | **Código existe pero NO se ejecuta** |
| `sync_comercial_endpoints_job.py` | Sync_PAX_Detalle | L490 | **Código existe pero NO se ejecuta** |

---

## 3. RAZÓN DE QUE Sync_Sales Y Sync_PAX_Detalle ESTÁN VACÍAS

### 3.1 Diseño Arquitectónico de Fase 1

El **Dashboard Ejecutivo de Inteligencia Comercial Fase 1** fue diseñado para mostrar:
- KPIs agregados diarios (ventas, tickets, PAX)
- Comparativas YoY, MoM
- Tendencias mensuales

**Estos KPIs NO requieren granularidad de tickets individuales**, por lo tanto:
1. El job `sync_comercial_edarsahub.py` calcula y escribe KPIs agregados **directamente** a `Comercial_KPIs_Diarios_v2`
2. **Bypasea completamente** las tablas `Sync_Sales` y `Sync_PAX_Detalle`

### 3.2 Propósito Original de Tablas Sync (Fase 2+)

| Tabla | Propósito Futuro |
|-------|------------------|
| `Sync_Sales` | Análisis de tickets individuales, patrones de compra, mix de productos |
| `Sync_PAX_Detalle` | Análisis de comensales por mesa, tiempos de permanencia, consumo por PAX |

---

## 4. TRAZABILIDAD DE ÚLTIMOS REGISTROS

```
Unidad: CIENFUEGOS | Fecha Op: 2026-06-02
  fuente_original: SQL_LIVE
  sistema_origen: SOFTRESTAURANT
  sync_run_id: INCR-20260602-185445-9adb
  fecha_sincronizacion: 2026-06-02 18:54:50

Unidad: 130° QUERETARO | Fecha Op: 2026-06-01
  fuente_original: SQL_LIVE
  sistema_origen: MPRO
  sync_run_id: INCR-20260602-104634-b886
  fecha_sincronizacion: 2026-06-02 10:46:37
```

---

## 5. CONCLUSIONES

### ✅ Confirmado
1. **Comercial_KPIs_Diarios_v2 está correctamente poblada** con 3,376 registros de 5 unidades de negocio
2. **La fuente es SQL_LIVE** (conexión directa a SOFTRESTAURANT y MPRO)
3. **El flujo actual NO usa Sync_Sales como intermediario** - es un diseño intencional de Fase 1
4. **Portal de Inteligencia Comercial Fase 1 opera 100% funcional** con esta arquitectura

### ⚠️ Pendiente para Fase 2
1. Activar poblado de `Sync_Sales` para análisis de tickets individuales
2. Activar poblado de `Sync_PAX_Detalle` para métricas detalladas de comensales
3. Estas tablas habilitarían dashboards de granularidad más fina

---

## 6. RECOMENDACIÓN

**NO es necesario poblar Sync_Sales/PAX_Detalle para Fase 1.** 

El Dashboard Ejecutivo actual opera correctamente con `Comercial_KPIs_Diarios_v2`.

Para **Fase 2** (Análisis de Tickets y PAX detallado):
1. Revisar jobs en `inteligencia_comercial_sync_job.py` (L240-280)
2. Activar flag o configuración para habilitar sync granular
3. Requerir credenciales adicionales si los endpoints actuales no devuelven tickets

---

**Reporte generado automáticamente | Diagnóstico completado exitosamente**
