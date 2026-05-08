# BLOQUE 5 - PLAN DE MIGRACIÓN DE routes.py

**Fecha:** 2026-04-23  
**Versión:** 1.0  
**Estado:** PENDIENTE DE APROBACIÓN  
**Objetivo:** Retirar SQL directo y duplicidad en endpoints priorizados de `routes.py`, usando capa centralizada

---

## 1. ANÁLISIS DE ESTADO ACTUAL

### 1.1 Métricas de `routes.py`

| Métrica | Valor |
|---------|-------|
| Líneas totales | 3,449 |
| Llamadas a `execute_sql_query` | ~65 |
| Endpoints con SQL directo | 10 |
| Queries de VENTAS/PAX/CHEQUES duplicadas | ~15 |

### 1.2 Endpoints Identificados

| # | Endpoint | Línea | SQL Directo | Usa service.py |
|---|----------|-------|-------------|----------------|
| 1 | `/comercial/tablero-ejecutivo` | 192 | NO | ✅ Usa `get_kpis_softrestaurant()` |
| 2 | `/comercial/sucursales/{server_id}` | 584 | SÍ | ❌ |
| 3 | `/comercial/metas/{server_id}` | 648 | SÍ | ❌ |
| 4 | `/comercial/ticket-perfecto/{server_id}` | 823 | SÍ | ❌ |
| 5 | `/comercial/ventas-tiempo/{server_id}` | 1007 | SÍ | ❌ |
| 6 | `/comercial/mesas/{server_id}` | 1191 | SÍ | ❌ |
| 7 | `/comercial/detalle-movimientos/{server_id}` | 1422 | SÍ | ❌ |
| 8 | `/comercial/precios-constantes/{server_id}` | 1636 | SÍ | ❌ |
| 9 | `/comercial/reporte-pax/{server_id}` | 2141 | SÍ | ❌ |
| 10 | `/comercial/dashboard/{server_id}` | 2569 | SÍ | ❌ |

---

## 2. CLASIFICACIÓN DE ENDPOINTS POR RIESGO

### 2.1 Endpoints con Métricas Base (VENTAS, PAX, CHEQUES)

| Endpoint | Métricas | Riesgo | Migrable a |
|----------|----------|--------|------------|
| `/comercial/dashboard/{server_id}` | ✅ VENTAS, PAX, CHEQUES | 🔴 ALTO | `query_ventas_periodo_sr`, `query_ventas_por_sucursal_mpro` |
| `/comercial/reporte-pax/{server_id}` | ✅ PAX, VENTAS | 🟡 MEDIO | Parcial |
| `/comercial/tablero-ejecutivo` | ✅ VENTAS, PAX, CHEQUES | ✅ YA MIGRADO | N/A |

### 2.2 Endpoints con Queries Específicas (NO migrar en 5.1)

| Endpoint | Tipo Query | Riesgo | Decisión |
|----------|------------|--------|----------|
| `/comercial/ticket-perfecto/{server_id}` | Productos TOP | 🟡 MEDIO | POSPONER |
| `/comercial/ventas-tiempo/{server_id}` | Ventas por hora/día | 🟡 MEDIO | POSPONER |
| `/comercial/mesas/{server_id}` | Análisis mesas | 🟡 MEDIO | POSPONER |
| `/comercial/detalle-movimientos/{server_id}` | Detalle folios | 🟡 MEDIO | POSPONER |
| `/comercial/precios-constantes/{server_id}` | Precios base | 🔴 ALTO | POSPONER |
| `/comercial/sucursales/{server_id}` | Catálogo | 🟢 BAJO | POSPONER |
| `/comercial/metas/{server_id}` | CRUD metas | 🟢 BAJO | POSPONER |

---

## 3. SUB-BLOQUE 5.1 - ALCANCE ESPECÍFICO

### 3.1 Endpoint a Migrar: `/comercial/dashboard/{server_id}` (Líneas 2569-3200)

**Justificación de Selección:**
- Es el endpoint más similar a `tablero-ejecutivo` (ya migrado)
- Usa las mismas métricas base: VENTAS, PAX, CHEQUES
- Tiene la mayor cantidad de SQL duplicado vs queries centralizadas
- Su migración demuestra el patrón sin afectar el tablero consolidado

### 3.2 SQL Duplicado a Eliminar/Reemplazar

| Línea | Query Actual | Reemplazo Propuesto |
|-------|--------------|---------------------|
| 2875-2887 | `SELECT COUNT(DISTINCT cheques.folio)...ventas_periodo...pax_total FROM cheques` | `query_ventas_periodo_sr()` para SR |
| 2910-2917 | `SELECT SUM(cheques.total) as ventas_periodo...WHERE >= f_ini_ant` | `query_ventas_periodo_sr(fecha_ini_ant, fecha_fin_ant)` |
| 2926-2933 | `SELECT ISNULL(SUM(cheques.nopersonas)...pax_total, SUM...ventas` | Ya cubierto por `query_ventas_periodo_sr` |
| 2945-2955 | `SELECT SUM(cheques.total)...pax_total...cheques_total FROM cheques WHERE año anterior` | `query_ventas_periodo_sr(fecha_ini_año_ant, fecha_fin_año_ant)` |
| 3094-3104 (MPRO) | `SELECT MAX(CONVERT(DATE, VE.Vn_Fecha))` | Mantener (específico) |

### 3.3 Funciones Centralizadas a Usar

| Función | Ubicación | Propósito |
|---------|-----------|-----------|
| `query_ventas_periodo_sr()` | `queries/softrestaurant.py` | Métricas consolidadas SR |
| `query_ventas_por_sucursal_mpro()` | `queries/mpro.py` | Métricas por sucursal MPRO |
| `VentasPeriodoResult` | `queries/softrestaurant.py` | Estructura de retorno |
| `VentasPorSucursalResult` | `queries/mpro.py` | Estructura de retorno |

### 3.4 Rutas PROTEGIDAS (NO Tocar en 5.1)

| Ruta | Motivo de Protección |
|------|---------------------|
| `/comercial/tablero-ejecutivo` | Ya migrado, crítico, no regresionar |
| `/comercial/ticket-perfecto/{server_id}` | Query específica de productos |
| `/comercial/ventas-tiempo/{server_id}` | Query específica de tiempo |
| `/comercial/precios-constantes/{server_id}` | Lógica compleja de precios |

---

## 4. ESTRATEGIA DE IMPLEMENTACIÓN

### 4.1 Pasos del Sub-Bloque 5.1

```
1. CAPTURA "ANTES"
   - Ejecutar `/comercial/dashboard/{server_id}` con parámetros de prueba
   - Guardar JSON de respuesta como referencia
   
2. MIGRACIÓN INCREMENTAL
   - Sección SoftRestaurant (líneas 2748-3000):
     a. Importar `query_ventas_periodo_sr`
     b. Reemplazar query_kpis (2875-2891) por llamada centralizada
     c. Reemplazar query_anterior (2910-2921) por llamada centralizada
     d. Reemplazar query_ano_ant (2945-2959) por llamada centralizada
     e. Mantener query_temp (tempcheques) - es específica
   
3. VALIDACIÓN PARCIAL
   - Ejecutar endpoint con mismos parámetros
   - Comparar JSON "ANTES" vs "DESPUÉS"
   - Diff debe ser 0 en: ventas, pax, cheques
   
4. MIGRACIÓN MPRO (si SR pasa)
   - Líneas 3030-3200 aproximadamente
   - Similar proceso
   
5. CAPTURA "DESPUÉS"
   - Guardar JSON final
   - Documentar cualquier diferencia justificada
```

### 4.2 Código de Migración Propuesto (Sección SR)

```python
# ANTES (líneas 2875-2891):
query_kpis = f"""
SELECT 
    COUNT(DISTINCT cheques.folio) as cheques_total,
    SUM(cheques.total) as ventas_periodo,
    ...
"""
result = execute_sql_query(...)

# DESPUÉS:
from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr

result_principal = query_ventas_periodo_sr(server, fecha_ini, fecha_fin)
if result_principal.success:
    cheques_total = result_principal.cheques
    ventas_periodo = result_principal.total_venta
    pax_total = result_principal.pax
else:
    # Manejo de error existente
```

---

## 5. RIESGOS DEL SUB-BLOQUE 5.1

### 5.1 Riesgos Identificados

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | Diferencia en formato de fechas | MEDIA | ALTO | Usar misma conversión `sql_fecha()` |
| R2 | Cálculos derivados diferentes | BAJA | MEDIO | Verificar fórmulas de ticket_promedio, rotacion |
| R3 | Query de tempcheques no migrada | N/A | BAJO | Mantener query específica |
| R4 | Comparativos (mes_ant, año_ant) con diferente rango | MEDIA | ALTO | Comparar rangos de fecha antes/después |
| R5 | MPRO tiene lógica de sucursal específica | ALTA | MEDIO | Usar `query_ventas_por_sucursal_mpro` |

### 5.2 Riesgo Heredado (BLOQUE 4)

> ⚠️ **IMPORTANTE**: El BLOQUE 4 tiene riesgo abierto de paridad numérica.
> Si las queries centralizadas tienen diferencias no detectadas, este bloque las propagará.
> 
> **Mitigación**: Capturar "ANTES" con el endpoint actual (que usa SQL directo)
> y comparar vs "DESPUÉS" (que usará queries centralizadas).

---

## 6. ESTRATEGIA DE PRUEBAS

### 6.1 Pruebas de Paridad

| # | Prueba | Método | Criterio de Éxito |
|---|--------|--------|-------------------|
| 1 | Respuesta JSON idéntica | Comparar antes/después | Diff = 0 en campos críticos |
| 2 | Campos críticos | Verificar: ventas, pax, cheques | Valores exactos |
| 3 | Comparativos | vs_periodo_anterior, vs_ano_anterior | Cálculos correctos |
| 4 | Manejo de errores | Servidor offline | Misma respuesta SOURCE_UNREACHABLE |

### 6.2 Parámetros de Prueba

```bash
# Prueba 1: Período mes actual
GET /api/comercial/dashboard/{server_id}?periodo=mes

# Prueba 2: Multiselección de meses
GET /api/comercial/dashboard/{server_id}?meses=01,02,03&anio=2026

# Prueba 3: Período día
GET /api/comercial/dashboard/{server_id}?periodo=dia

# Prueba 4: Comparación días equivalentes
GET /api/comercial/dashboard/{server_id}?periodo=mes&tipo_comparacion=dias_equiv
```

### 6.3 Script de Validación

```python
# test_bloque5_paridad.py
def comparar_respuestas(antes: dict, despues: dict) -> dict:
    """Compara respuestas antes/después de migración"""
    diferencias = {}
    
    campos_criticos = [
        'kpis.ventas', 'kpis.pax', 'kpis.cheques',
        'comparativo.vs_periodo_anterior', 'comparativo.vs_ano_anterior'
    ]
    
    for campo in campos_criticos:
        valor_antes = get_nested(antes, campo)
        valor_despues = get_nested(despues, campo)
        
        if valor_antes != valor_despues:
            diferencias[campo] = {
                'antes': valor_antes,
                'despues': valor_despues,
                'diff': valor_despues - valor_antes if isinstance(valor_antes, (int, float)) else 'N/A'
            }
    
    return diferencias
```

---

## 7. CRITERIO DE APROBACIÓN DEL SUB-BLOQUE 5.1

### 7.1 Condiciones Obligatorias

| # | Condición | Verificación |
|---|-----------|--------------|
| 1 | Mismo payload JSON | Comparación estructural |
| 2 | Mismas cifras en ventas, pax, cheques | Diff = 0 |
| 3 | Mismos filtros funcionando | Probar con sucursal, período |
| 4 | Mismos permisos RBAC | No cambios en validate_server_access_rbac |
| 5 | Mismas rutas | No cambios en decoradores @router |
| 6 | Compilación correcta | Lint sin errores |
| 7 | Endpoint responde | HTTP 200 con datos |

### 7.2 Dictámenes Posibles

| Resultado | Condición |
|-----------|-----------|
| `SUB-BLOQUE 5.1 COMPLETADO` | Todas las condiciones cumplidas |
| `SUB-BLOQUE 5.1 COMPLETADO CON OBSERVACIONES` | Diferencias menores documentadas |
| `SUB-BLOQUE 5.1 NO APROBADO` | Diferencias críticas o regresión |

---

## 8. RESUMEN EJECUTIVO

### 8.1 Alcance del Sub-Bloque 5.1

| Aspecto | Valor |
|---------|-------|
| Endpoint objetivo | `/comercial/dashboard/{server_id}` |
| Líneas afectadas | ~2569-3200 (~600 líneas) |
| Queries a reemplazar | 4 queries SR + 3 queries MPRO |
| Funciones centralizadas a usar | 2 (`query_ventas_periodo_sr`, `query_ventas_por_sucursal_mpro`) |
| Queries a mantener | tempcheques, último día venta |

### 8.2 Lo que SÍ se hace en 5.1

- ✅ Reemplazar SQL directo de métricas base por llamadas centralizadas
- ✅ Mantener estructura de respuesta exacta
- ✅ Mantener lógica de comparativos
- ✅ Mantener manejo de errores y caché

### 8.3 Lo que NO se hace en 5.1

- ❌ Cambiar payload de respuesta
- ❌ Cambiar nombres de campos
- ❌ Cambiar filtros
- ❌ Cambiar permisos RBAC
- ❌ Cambiar rutas
- ❌ Tocar otros endpoints
- ❌ Migrar queries específicas (productos, tiempo, mesas)

---

## 9. DECISIÓN REQUERIDA

### 9.1 Opciones

| Opción | Descripción |
|--------|-------------|
| A | Aprobar plan y proceder con implementación |
| B | Solicitar ajustes al plan |
| C | Posponer BLOQUE 5 |

### 9.2 Riesgos Abiertos Acumulados

| ID | Riesgo | Estado |
|----|--------|--------|
| R1 | BLOQUE 4: Paridad numérica no validada contra SQL real | 🟡 ABIERTO |
| R2 | FASE 2.3: Ejecución de carga histórica pendiente | 🟡 ABIERTO |
| R3 | BLOQUE 5: Depende de paridad del BLOQUE 4 | 🟡 NUEVO (condicional) |

---

**DICTAMEN DEL PLAN:**

## 🟡 BLOQUE 5 PLAN PENDIENTE DE APROBACIÓN

El plan está completo y detallado. Requiere confirmación del usuario para proceder con la implementación del Sub-Bloque 5.1.

---

Firma: E1 Agent  
Fecha: 2026-04-23
