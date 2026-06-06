# POLÍTICA OFICIAL DE FECHAS - EDARSA HUB
## Documento Técnico-Funcional

**Versión:** 1.0  
**Fecha:** Diciembre 2025  
**Estado:** DIAGNÓSTICO DOCUMENTADO (Sin cambios de código)  
**Autor:** Arquitectura de Software

---

## 1. RESUMEN EJECUTIVO

Este documento establece las definiciones, reglas y lineamientos oficiales para el manejo de fechas/horas en EDARSA HUB, con el objetivo de:

- Evitar inconsistencias entre módulos
- Garantizar conciliaciones precisas
- Estandarizar criterios entre sistemas origen (SoftRestaurant, MPRO)
- Prevenir regresiones en futuros desarrollos

**IMPORTANTE:** Este documento es de **diagnóstico y documentación**. NO autoriza cambios de código sin aprobación explícita.

---

## 2. DEFINICIONES OFICIALES

### 2.1 Tipos de Fecha

| Tipo | Definición | Ejemplo |
|------|------------|---------|
| **Fecha Operativa** | Día calendario en que ocurre una transacción comercial | 2026-04-15 |
| **Fecha Contable** | Día en que se registra contablemente (puede diferir de operativa) | 2026-04-16 |
| **Fecha de Captura** | Momento exacto en que se registra en el sistema | 2026-04-15 14:32:45 |
| **Fecha de Corte** | Momento que delimita un período de análisis | 2026-04-15 23:59:59 |
| **Fecha/Hora de Inventario** | Momento exacto en que se realiza un conteo físico | 2026-04-15 08:00:00 |
| **Fecha de Movimiento** | Momento en que ocurre entrada/salida de almacén | 2026-04-15 10:30:00 |
| **Fecha de Turno** | Fecha asociada al turno de operación (apertura/cierre) | 2026-04-15 06:00:00 |

### 2.2 Formatos Estándar

| Contexto | Formato | Ejemplo |
|----------|---------|---------|
| **EDARSA HUB (interno)** | ISO 8601: `YYYY-MM-DD HH:MM:SS` | 2026-04-15 14:32:45 |
| **MongoDB** | ISO 8601 con timezone | 2026-04-15T14:32:45+00:00 |
| **SQL Server (universal)** | `YYYYMMDD HH:MM:SS` | 20260415 14:32:45 |
| **SoftRestaurant (queries)** | `DD/MM/YYYY HH:MM:SS` con CONVERT | 15/04/2026 14:32:45 |
| **MPRO (queries)** | `YYYY-MM-DD HH:MM:SS` | 2026-04-15 14:32:45 |
| **Frontend (display)** | `DD/MM/YYYY HH:MM` | 15/04/2026 14:32 |

---

## 3. REGLAS POR CONTEXTO

### 3.1 Ventas del Día

| Sistema | Campo de Fecha | Criterio | Hora Inicio | Hora Fin |
|---------|---------------|----------|-------------|----------|
| **SoftRestaurant** | `turnos.APERTURA` | Fecha de apertura del turno | 00:00:00 | 23:59:59 |
| **MPRO** | `Vn_Fecha` | Fecha de la venta | 00:00:00 | 23:59:59 |

**Regla actual:**
```sql
-- SoftRestaurant
WHERE turnos.APERTURA >= '{fecha} 00:00:00' AND turnos.APERTURA <= '{fecha} 23:59:59'

-- MPRO
WHERE Vn_Fecha >= '{fecha}' AND Vn_Fecha <= '{fecha} 23:59:59'
```

### 3.2 Inventarios Físicos

| Aspecto | Regla Actual |
|---------|--------------|
| **Momento del inventario** | Fecha/hora exacta del conteo |
| **Ajuste aplicado** | +1 segundo al inicio, -1 segundo al final |
| **Propósito del ajuste** | Excluir el momento exacto del inventario de los movimientos |

**Código actual (server.py líneas 3320-3323):**
```python
dt_ini = dt_ini + timedelta(seconds=1)
dt_fin = dt_fin - timedelta(seconds=1)
```

### 3.3 Movimientos de Almacén

| Sistema | Tabla | Campo | Criterio |
|---------|-------|-------|----------|
| **SoftRestaurant Insumos** | `movsinv` | `fecha` | BETWEEN inclusivo |
| **SoftRestaurant Presentaciones** | `movtosalmacen` | `fecha` | BETWEEN inclusivo |
| **MPRO** | `Movimiento` | `Mv_Fecha` | BETWEEN inclusivo |

**Formato para SoftRestaurant:**
```sql
WHERE movsinv.fecha BETWEEN '{YYYYMMDD HH:MM:SS}' AND '{YYYYMMDD HH:MM:SS}'
```

### 3.4 Ventas para Análisis de Inventario

| Aspecto | SoftRestaurant | MPRO |
|---------|---------------|------|
| **Fecha inicio** | Día del inventario inicial 00:00:00 | Día siguiente al inv. inicial |
| **Fecha fin** | Día ANTERIOR al inv. final 23:59:59 | Día del inv. final 23:59:59 |
| **Justificación** | Excluir ventas del día del inventario final | Diferente modelo de corte |

**Código SoftRestaurant (líneas 3612-3615):**
```python
fecha_ini_ventas = dt_ini.replace(hour=0, minute=0, second=0)
fecha_fin_ventas = (dt_fin - timedelta(days=1)).replace(hour=23, minute=59, second=59)
```

**Código MPRO (línea 2726):**
```python
fecha_ini_mov = (fecha_ini_dt + timedelta(days=1)).strftime('%Y-%m-%d')
```

### 3.5 Módulo Comercial

| Consulta | Criterio de Fecha |
|----------|-------------------|
| Ventas por producto | `turnos.apertura >= '{f_ini} 00:00:00' AND <= '{f_fin} 23:59:59'` |
| Ventas por mesero | Mismo criterio |
| Análisis por hora | Mismo criterio |
| Comparativo mensual | Calcula días transcurridos vs días totales del mes |

**Helper estandarizado:**
```python
def sql_fecha(fecha_str: str, con_hora: bool = True, hora: str = "00:00:00") -> str:
    # Convierte 'YYYY-MM-DD' a 'YYYYMMDD HH:MM:SS'
```

### 3.6 Compras

| Aspecto | Estado |
|---------|--------|
| Fechas de compra | Sin lógica específica documentada |
| Períodos operativos | Usa `Pr_Fecha_Inicial` y `Pr_Fecha_final` de MPRO |

### 3.7 Finanzas

| Aspecto | Estado |
|---------|--------|
| Cortes financieros | Sin módulo activo actualmente |
| Cierre contable | Pendiente de implementación |

### 3.8 RH / Nóminas

| Aspecto | Estado |
|---------|--------|
| Períodos de nómina | Usa fechas de MPRO |
| Incidencias | Sin lógica específica documentada |

---

## 4. REGLAS TÉCNICAS

### 4.1 Formato Estándar para SQL Server

**REGLA:** Usar formato `YYYYMMDD` (sin separadores) es **universal** y funciona independientemente de la configuración regional del servidor.

```python
# CORRECTO - Universal
fecha_sql = fecha.replace('-', '')  # '20260415'

# RIESGOSO - Depende de configuración regional
fecha_sql = fecha  # '2026-04-15' puede fallar en servidores con config diferente
```

### 4.2 Criterio Inclusivo vs Exclusivo

| Operador | Comportamiento |
|----------|---------------|
| `BETWEEN a AND b` | **INCLUSIVO** - incluye a y b |
| `>= a AND <= b` | **INCLUSIVO** - equivalente a BETWEEN |
| `> a AND < b` | **EXCLUSIVO** - no incluye a ni b |
| `>= a AND < b` | **SEMI-INCLUSIVO** - incluye a, excluye b |

**Estado actual en EDARSA HUB:** Predomina el uso de `>= ... AND <= ...` (inclusivo) con ajuste de segundos cuando es necesario.

### 4.3 Manejo de Segundos

| Contexto | Regla |
|----------|-------|
| Inventarios | Ajuste ±1 segundo para excluir momento exacto |
| Ventas | No requiere ajuste (usa día completo) |
| Movimientos | Usa fechas ajustadas de inventarios |

### 4.4 Timezone

| Sistema | Timezone Asumido |
|---------|-----------------|
| **EDARSA HUB** | UTC para almacenamiento |
| **SoftRestaurant** | Hora local del servidor SQL |
| **MPRO** | Hora local del servidor SQL |
| **MongoDB** | UTC con conversión explícita |

**RIESGO:** No hay conversión explícita entre timezones. Se asume que todos los sistemas están en la misma zona horaria (México/Central).

### 4.5 Diferencias SoftRestaurant vs MPRO

| Aspecto | SoftRestaurant | MPRO |
|---------|---------------|------|
| **Formato preferido** | `DD/MM/YYYY` con CONVERT | `YYYY-MM-DD` directo |
| **Campo de ventas** | `turnos.APERTURA` | `Vn_Fecha` |
| **Campo de movimientos** | `movsinv.fecha` | `Mv_Fecha` |
| **Tablas de inventario** | `inventario` | `Inventario` (PascalCase) |
| **Conversión requerida** | CONVERT(datetime, ..., 103) | Directo |

---

## 5. RIESGOS IDENTIFICADOS

### 5.1 Riesgos de Conciliación

| # | Riesgo | Ubicación | Impacto | Probabilidad |
|---|--------|-----------|---------|--------------|
| 1 | Fechas de ventas vs movimientos desalineadas | Análisis de inventario | ALTO | MEDIA |
| 2 | Timezone no explícito en MongoDB | Todos los módulos | MEDIO | BAJA |
| 3 | Formato de fecha dependiente de config regional | Queries SQL | ALTO | BAJA |
| 4 | Criterios diferentes entre SoftRest y MPRO | Comparativos cross-sistema | MEDIO | ALTA |

### 5.2 Ambigüedades Detectadas

| # | Ambigüedad | Descripción |
|---|------------|-------------|
| 1 | Día de corte de ventas | SoftRest usa día ANTERIOR al inv. final, MPRO usa el mismo día |
| 2 | Hora de inicio del día | ¿00:00:00 o 06:00:00 (turno)? |
| 3 | Inventarios sin hora | Algunos folios no tienen hora, se asume 00:00:00 |

### 5.3 Módulos/Endpoints con Criterios Distintos

| Módulo | Endpoint | Criterio Actual | Potencial Conflicto |
|--------|----------|-----------------|---------------------|
| Inventarios | `/api/inventarios/analizar` | ±1 seg en movimientos | OK - documentado |
| Comercial | `/api/comercial/ventas-tiempo` | >= y <= con 23:59:59 | OK - consistente |
| Compras | (varios) | Sin helper estandarizado | ⚠️ Revisar |
| Finanzas | (sin endpoints activos) | N/A | N/A |

---

## 6. RECOMENDACIÓN OFICIAL

### 6.1 Política Estándar Propuesta

#### Para consultas de RANGO DE FECHAS:

```python
# FORMATO ESTÁNDAR
fecha_inicio = "YYYYMMDD 00:00:00"
fecha_fin = "YYYYMMDD 23:59:59"

# CRITERIO ESTÁNDAR
WHERE campo_fecha >= '{fecha_inicio}' AND campo_fecha <= '{fecha_fin}'
```

#### Para consultas de INVENTARIO:

```python
# Movimientos: Usar fechas ajustadas de inventarios
fecha_ini_mov = fecha_inventario_inicial + 1 segundo
fecha_fin_mov = fecha_inventario_final - 1 segundo

# Ventas SoftRestaurant: Día del inv. inicial hasta día ANTERIOR al inv. final
fecha_ini_ventas = fecha_inventario_inicial.replace(hour=0, minute=0, second=0)
fecha_fin_ventas = (fecha_inventario_final - 1 día).replace(hour=23, minute=59, second=59)
```

### 6.2 Excepciones Justificadas

| Excepción | Justificación | Autorización |
|-----------|---------------|--------------|
| Ajuste ±1 segundo en inventarios | Excluir momento exacto del conteo | APROBADA |
| Ventas hasta día anterior (SoftRest) | Modelo de turno de SoftRestaurant | APROBADA |
| Formato DD/MM/YYYY para SoftRest | Configuración regional del servidor | APROBADA |

### 6.3 Lineamientos para Futuros Desarrollos

1. **Usar helper `sql_fecha()`** para formateo de fechas SQL
2. **Usar formato YYYYMMDD** para máxima compatibilidad
3. **Documentar criterio** (inclusivo/exclusivo) en cada query nueva
4. **Evitar BETWEEN** si hay riesgo de ambigüedad - preferir >= y <=
5. **Almacenar en UTC** y convertir en presentación
6. **Registrar hora exacta** en inventarios, no solo fecha

---

## 7. LISTA DE REVISIÓN FUTURA

### 7.1 Endpoints a Revisar (SIN CAMBIAR TODAVÍA)

| # | Endpoint | Archivo | Línea Aprox. | Motivo |
|---|----------|---------|--------------|--------|
| 1 | `/api/inventarios/analizar` | server.py | 3200-3700 | Validar lógica de fechas |
| 2 | `/api/comercial/ventas-tiempo` | comercial/routes.py | 600-700 | Verificar consistencia |
| 3 | `/api/comercial/mesas` | comercial/routes.py | 900-1000 | Verificar consistencia |
| 4 | Queries MPRO | server.py | 2700-2900 | Documentar criterios |
| 5 | Compras detector | server.py | 6600-6900 | Estandarizar formato |

### 7.2 Consultas SQL a Auditar

| # | Tabla | Campo de Fecha | Archivo | Prioridad |
|---|-------|---------------|---------|-----------|
| 1 | `movsinv` | fecha | server.py | ALTA |
| 2 | `movtosalmacen` | fecha | server.py | ALTA |
| 3 | `cheques/turnos` | APERTURA | server.py, comercial | MEDIA |
| 4 | `Venta_Encabezado` | Vn_Fecha | server.py, comercial | MEDIA |
| 5 | `Movimiento` | Mv_Fecha | server.py | MEDIA |

---

## 8. CHECKLIST DE VALIDACIÓN

### Para nuevos desarrollos:

- [ ] ¿Se usó el formato YYYYMMDD para SQL Server?
- [ ] ¿Se documentó el criterio de inclusión/exclusión?
- [ ] ¿Se consideró el timezone?
- [ ] ¿Se usó el helper `sql_fecha()` si aplica?
- [ ] ¿Se probó con diferentes configuraciones regionales?
- [ ] ¿Se validó conciliación con datos reales?

### Para auditorías:

- [ ] ¿Los totales de ventas coinciden entre sistemas?
- [ ] ¿Los movimientos de almacén cuadran con inventarios?
- [ ] ¿Las fechas de corte son consistentes?

---

## 9. HISTÓRICO DE CAMBIOS

| Fecha | Versión | Cambio | Autor |
|-------|---------|--------|-------|
| 2025-12 | 1.0 | Documento inicial - Diagnóstico | Arquitectura |

---

## 10. APROBACIONES REQUERIDAS

Este documento requiere aprobación antes de:

1. Implementar cambios en criterios de fecha
2. Modificar queries existentes
3. Crear nuevos endpoints con lógica de fechas
4. Cambiar formatos de fecha en cualquier módulo

---

**FIN DEL DOCUMENTO DE POLÍTICA DE FECHAS**

*Documento de diagnóstico - No autoriza cambios de código sin aprobación explícita.*
