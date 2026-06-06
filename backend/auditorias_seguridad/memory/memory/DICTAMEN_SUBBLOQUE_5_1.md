# DICTAMEN FINAL: SUB-BLOQUE 5.1

**Fecha:** 2026-04-23  
**Endpoint:** `/comercial/dashboard/{server_id}`  
**Alcance:** Sección SoftRestaurant únicamente  
**Estado:** 🟡 COMPLETADO CON PARIDAD ESTRUCTURAL | VALIDACIÓN NUMÉRICA REAL PENDIENTE

---

## 1. RESUMEN EJECUTIVO

El Sub-Bloque 5.1 migró exitosamente 4 queries SQL directas del endpoint `/comercial/dashboard/{server_id}` (sección SoftRestaurant) hacia la función centralizada `query_ventas_periodo_sr()`.

La migración fue **estructuralmente exitosa**, pero la **paridad numérica exacta** no pudo ser validada debido a cambio de estado del servidor entre capturas.

---

## 2. QUÉ QUEDÓ MIGRADO

### 2.1 Archivo Modificado
- `/app/backend/modules/comercial/routes.py`

### 2.2 Queries Reemplazadas

| ID | Líneas Originales | Query SQL Eliminada | Reemplazo |
|----|-------------------|---------------------|-----------|
| Q1 | 2877-2893 | `SELECT cheques_total, ventas_periodo, pax_total FROM cheques WHERE periodo_actual` | `query_ventas_periodo_sr(server, fecha_ini, fecha_fin)` |
| Q2 | 2912-2923 | `SELECT SUM(cheques.total) WHERE mes_anterior` | `query_ventas_periodo_sr(server, fecha_ini_ant, fecha_fin_ant)` |
| Q3 | 2928-2939 | `SELECT pax_total, ventas WHERE mes_anterior` | Consolidado en Q2 |
| Q4 | 2947-2961 | `SELECT ventas, pax, cheques WHERE año_anterior` | `query_ventas_periodo_sr(server, fecha_ini_ano_ant, fecha_fin_ano_ant)` |

### 2.3 Import Agregado
```python
from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
```

### 2.4 Lógica Preservada
- Cálculo de `ticket_promedio` = ventas / cheques
- Cálculo de `pax_promedio` = pax / cheques
- Cálculo de `rotacion_mesas`
- Todos los comparativos derivados (vs_periodo_anterior, vs_ano_anterior, etc.)
- Manejo de errores y estados

---

## 3. QUÉ QUEDÓ FUERA (NO MIGRADO EN 5.1)

### 3.1 Sección MPRO
- **Motivo**: La función `query_ventas_periodo_mpro()` no soporta filtro de sucursal
- **Impacto**: El endpoint MPRO sigue usando SQL directo
- **Acción**: Requiere sub-bloque 5.2 o extensión de función

### 3.2 Query de Tempcheques
- **Líneas**: 2979-2990
- **Motivo**: Query específica del dashboard, no corresponde a métrica base
- **Acción**: Mantener sin migrar

### 3.3 Queries de Detalle
- `query_meseros`, `query_ultimas_cuentas`, etc.
- **Motivo**: Fuera de alcance del 5.1 (solo métricas base)

---

## 4. VALIDACIONES COMPLETADAS

| # | Validación | Resultado | Evidencia |
|---|------------|-----------|-----------|
| 1 | Estructura JSON idéntica | ✅ PASS | Keys: source_status, kpis, comparativo, alertas |
| 2 | KPIs base presentes | ✅ PASS | ventas_periodo, pax_total, cheques_total |
| 3 | Comparativos presentes | ✅ PASS | vs_periodo_anterior, vs_ano_anterior |
| 4 | Idempotencia | ✅ PASS | 2 llamadas idénticas |
| 5 | Tipos de datos | ✅ PASS | Numéricos correctos |
| 6 | HTTP 200 | ✅ PASS | Endpoint responde |
| 7 | Compilación | ✅ PASS | Lint sin errores nuevos |
| 8 | RBAC intacto | ✅ PASS | admin y almacen acceden |
| 9 | Filtros | ✅ PASS | periodo=mes funciona |
| 10 | Rutas | ✅ PASS | Decoradores sin cambio |

---

## 5. RIESGO ABIERTO

### 5.1 Paridad Numérica No Validada

| Métrica | Estado |
|---------|--------|
| ventas | 🟡 No comparable |
| pax | 🟡 No comparable |
| cheques | 🟡 No comparable |
| ticket_promedio | 🟡 No comparable |
| vs_periodo_anterior | 🟡 No comparable |
| vs_ano_anterior | 🟡 No comparable |

**Causa**: El servidor tenía `source_status: NO_DATA` en captura ANTES y `source_status: SUCCESS` en captura DESPUÉS. No hubo base numérica comparable.

### 5.2 Requisitos para Cerrar Riesgo

Para validar paridad numérica real se requiere:

1. **Ambiente con datos estables**: Servidor SQL accesible con datos que no cambien entre capturas
2. **Captura ANTES con código original**: Revertir temporalmente el código, capturar, luego re-aplicar migración
3. **Comparación exacta**: Diff = 0 en ventas, pax, cheques y derivados

### 5.3 Impacto del Riesgo

| Escenario | Probabilidad | Impacto |
|-----------|--------------|---------|
| Query centralizada produce mismo resultado | ALTA | Ninguno |
| Query centralizada tiene diferencia menor | BAJA | Medio - KPIs derivados afectados |
| Query centralizada tiene diferencia mayor | MUY BAJA | Alto - Datos incorrectos |

**Mitigación existente**: La query en `query_ventas_periodo_sr()` fue extraída textualmente del código original de `service.py` (BLOQUE 4), que a su vez fue validada estructuralmente.

---

## 6. ARCHIVOS DE EVIDENCIA

| Archivo | Contenido |
|---------|-----------|
| `/tmp/antes_dashboard_sr.json` | Respuesta ANTES (NO_DATA) |
| `/tmp/despues_dashboard_sr.json` | Respuesta DESPUÉS (SUCCESS) |
| `/tmp/despues2_dashboard_sr.json` | Segunda captura (idempotencia) |
| `/app/backend/tests/test_bloque5_paridad.py` | Tests de paridad estructural |

---

## 7. DICTAMEN FINAL

## 🟡 SUB-BLOQUE 5.1 COMPLETADO CON PARIDAD ESTRUCTURAL
## 🟡 VALIDACIÓN NUMÉRICA REAL PENDIENTE

**Aprobado para:**
- ✅ Uso en ambiente de desarrollo
- ✅ Avanzar a planificación de 5.2

**No aprobado todavía para:**
- ❌ Declarar paridad numérica total
- ❌ Cerrar riesgo de regresión numérica

**Acción requerida para cierre total:**
- Validar paridad numérica en ambiente con conectividad SQL estable y datos comparables

---

## 8. RIESGOS ACUMULADOS

| ID | Riesgo | Origen | Estado |
|----|--------|--------|--------|
| R1 | Paridad numérica BLOQUE 4 | service.py | 🟡 ABIERTO |
| R2 | Ejecución Fase 2.3 | Carga histórica | 🟡 ABIERTO |
| R3 | Paridad numérica SUB-BLOQUE 5.1 | routes.py dashboard SR | 🟡 ABIERTO |

---

Firma: E1 Agent  
Fecha: 2026-04-23
