# DIAGNÓSTICO P0: Ventas del Día de ORIGEN No Se Reflejan en Tablero Ejecutivo

**Fecha:** 2026-05-18  
**Autor:** E1 Agent  
**Estado:** DIAGNÓSTICO COMPLETADO (CORREGIDO) - PENDIENTE AUTORIZACIÓN PARA IMPLEMENTAR  
**Prioridad:** P0  

---

## 1. Resumen Ejecutivo (CORREGIDO)

El usuario reportó que **ORIGEN tiene ventas del día de hoy, pero no se reflejan en el Tablero Ejecutivo**. 

### Hallazgos Principales

| Aspecto | Hallazgo |
|---------|----------|
| **Job de Sync** | ✅ Funciona técnicamente (API responde, conexión ONLINE) |
| **Problema #1** | ⚠️ **BUG INTERMITENTE**: El cálculo de FechaOperacion es inconsistente entre ejecuciones |
| **Problema #2** | ⚠️ **INCONSISTENCIA DE HORARIOS**: La BD tiene `03:00`, pero el código default usa `06:00` |
| **Problema #3** | ⚠️ **UPSERT sin fecha**: La llave `(unidad_negocio_id, sucursal_id)` no incluye `fecha_operacion` |

### Evidencia del BUG Intermitente

| Ejecución | Hora México | fecha_inicio BD | Esperado | Estado |
|-----------|-------------|-----------------|----------|--------|
| ABIERTA-20260518-173700 | 11:37 | 2026-05-18 | 2026-05-17 | ✗ BUG |
| ABIERTA-20260518-173649 | 11:36 | 2026-05-17 | 2026-05-17 | ✓ OK |
| ABIERTA-20260518-173220 | 11:32 | 2026-05-18 | 2026-05-17 | ✗ BUG |
| ABIERTA-20260518-173149 | 11:31 | 2026-05-17 | 2026-05-17 | ✓ OK |
| ABIERTA-20260518-172708 | 11:27 | 2026-05-17 | 2026-05-17 | ✓ OK |

**A las 11:XX México, todas las ejecuciones deberían calcular `fecha_operacion = 2026-05-17`** según el horario 13:00-03:00. Las que marcan 2026-05-18 son INCORRECTAS.

---

## 2. Aclaración de Inconsistencias (SOLICITADA POR EL USUARIO)

### 2.1 Horario 03:00 vs 06:00

| Fuente | Valor de hora_fin |
|--------|-------------------|
| `Sistema_HorariosServicioUnidad` (BD) | **03:00:00** |
| `operational_window.py` (default sin config) | **06:00:00** |
| `comercial/routes.py` (default sin unidad) | **06:00:00** |
| `comercial/service.py` (default sin unidad) | **06:00:00** |

**Inconsistencia crítica**: La regla documentada (`CAMBIO_REGLA_FECHA_OPERATIVA_CORTE_0600.md`) dice 06:00 AM, pero la configuración en BD para ORIGEN y 130QRO tiene 03:00.

**Conclusión**: La función `get_operational_window()` lee de `Sistema_HorariosServicioUnidad` y obtiene 03:00, NO usa el default 06:00.

### 2.2 Snapshot 2026-05-18 17:37 UTC - ¿Por qué fecha_operacion=2026-05-18?

| Dato | Valor |
|------|-------|
| `snapshot_timestamp` | `2026-05-18T17:37:01.540602` (UTC) |
| Hora equivalente México | `2026-05-18 11:37:01` CST |
| Horario configurado | 13:00 - 03:00 (de tabla `Sistema_HorariosServicioUnidad`) |
| ¿Debería ser fecha_operacion? | **2026-05-17** (porque 11:37 está en período "cerrado" entre 03:00 y 13:00) |

**El snapshot se generó a las 17:37 UTC = 11:37 México**. A esa hora, según el horario 13:00-03:00:
- ¿hora_actual (11:37) < hora_fin (03:00)? NO
- ¿hora_actual (11:37) >= hora_inicio (13:00)? NO
- Resultado: Período "cerrado" → fecha_operacion = **día ANTERIOR (2026-05-17)**

**El job calculó INCORRECTAMENTE `fecha_operacion=2026-05-18`**. Esto es un **BUG**.

### 2.3 Regla Exacta de FechaOperacion Vigente

Según el código en `/app/backend/core/utils/operational_window.py`:

```
Horario: 13:00 - 03:00 (cruza_medianoche=True)

Evaluación:
- Si hora_actual < 03:00 (ej: 02:30) → fecha_operacion = día ANTERIOR
- Si hora_actual >= 13:00 (ej: 14:00) → fecha_operacion = día ACTUAL  
- Si 03:00 <= hora_actual < 13:00 (ej: 11:30) → fecha_operacion = día ANTERIOR (restaurante cerrado)
```

**Nota sobre el corte 06:00 AM**: El código de `operational_window.py` tiene un DEFAULT de 06:00 que se usa SOLO cuando NO hay configuración en la tabla. ORIGEN y 130QRO SÍ tienen configuración (03:00), por lo que usan 03:00.

### 2.4 ¿ORIGEN tiene ventas del día operativo 2026-05-18?

**NO**. A las 11:37 México, la jornada del 18 NO ha comenzado (inicia a las 13:00).

| Tabla | fecha_operacion | Valor |
|-------|-----------------|-------|
| `Comercial_Ventas_Dia_Abiertas_v2` | 2026-05-18 | $0.00 (INCORRECTO - no debería existir) |
| `Comercial_KPIs_Diarios_v2` | 2026-05-17 | $68,431.01 (CORRECTO - cerrado) |

Las ventas que el usuario menciona como "de hoy" corresponden a:
- Si son de antes de las 03:00 del 18-May → Son del día operativo **17-May**
- Si son de después de las 13:00 del 18-May → Son del día operativo **18-May** (pero aún no ha llegado esa hora)

### 2.5 ¿Cuál es el problema del Tablero?

**Respuesta: Combinación de B, C y D**

| Opción | Aplica | Explicación |
|--------|--------|-------------|
| A) El snapshot correcto está en 2026-05-17, pero el tablero espera 2026-05-18 | PARCIAL | El tablero calcula la fecha a leer según `get_operational_window()`, que a las 11:37 da 2026-05-17. PERO el snapshot ACTUAL es de 2026-05-18 con $0. |
| B) El snapshot de 2026-05-18 no existe porque el job no lo genera | NO | El job SÍ lo generó (incorrectamente) |
| **C) El snapshot de 2026-05-18 fue sobrescrito por falta de fecha_operacion en la llave** | **SÍ** | El UPSERT usa llave `(unidad_negocio_id, sucursal_id)` SIN fecha. Cada sync sobrescribe el único registro. |
| **D) El cálculo de FechaOperacion está mal** | **SÍ** | Hay un BUG intermitente que hace que algunas ejecuciones calculen 2026-05-18 cuando deberían dar 2026-05-17. |
| E) El tablero está leyendo una fecha distinta a la que escribe el job | **SÍ** | El tablero intenta leer 2026-05-17 pero el snapshot actual es 2026-05-18 con $0. |

---

## 3. Diagnóstico Adicional Obligatorio

### 3.1 DDL / Estructura de Comercial_Ventas_Dia_Abiertas_v2

```sql
-- Columnas
id                             uniqueidentifier   NOT NULL DEFAULT(newid())
unidad_negocio_id              nvarchar           NOT NULL
unidad_negocio_nombre          nvarchar           NOT NULL
server_id                      nvarchar           NOT NULL
sucursal_id                    nvarchar           NOT NULL DEFAULT('DEFAULT')
sucursal_nombre                nvarchar           NULL
sistema_origen                 nvarchar           NOT NULL
snapshot_timestamp             datetime2          NOT NULL
fecha_operacion                date               NOT NULL
ventas_abiertas                decimal            NULL DEFAULT(0)
tickets_abiertos               int                NULL DEFAULT(0)
pax_abiertos                   int                NULL DEFAULT(0)
ventas_cerradas_dia            decimal            NULL DEFAULT(0)
tickets_cerrados_dia           int                NULL DEFAULT(0)
pax_cerrados_dia               int                NULL DEFAULT(0)
total_estimado_dia             decimal            NULL DEFAULT(0)
fuente_original                nvarchar           NOT NULL
sync_run_id                    nvarchar           NULL
fecha_ultima_actualizacion     datetime2          NULL DEFAULT(sysutcdatetime())
```

### 3.2 Índices Actuales

| Nombre | Tipo | Unique | PK | Columnas |
|--------|------|--------|----|----|
| `PK__Comercia__3213E83F3864FB09` | CLUSTERED | True | True | `id` |
| `UQ_Ventas_Dia_v2_Unidad` | NONCLUSTERED | **True** | False | `unidad_negocio_id, sucursal_id` |
| `IX_Ventas_Dia_v2_Snapshot` | NONCLUSTERED | False | False | `snapshot_timestamp` |

**Observación crítica**: El índice UNIQUE `UQ_Ventas_Dia_v2_Unidad` **NO incluye `fecha_operacion`**.

### 3.3 UPSERT Actual (repository_comercial_edarsahub.py líneas 254-318)

```python
def upsert_ventas_dia_abiertas(ventas: VentasDiaAbiertasV2) -> Dict[str, Any]:
    """
    Upsert de snapshot de ventas abiertas.
    Solo mantiene 1 registro por unidad (sobrescribe).  # <-- DOCUMENTACIÓN EXPLÍCITA
    """
    # Verificar si existe
    check_query = f"""
    SELECT id 
    FROM Comercial_Ventas_Dia_Abiertas_v2
    WHERE unidad_negocio_id = '{ventas.unidad_negocio_id}'
      AND sucursal_id = '{ventas.sucursal_id}'
    """
    # ^^^ NO incluye fecha_operacion en la llave
    
    existing = _execute_query(check_query)
    
    if existing:
        # UPDATE del único registro existente
        record_id = existing[0].get('id')
        update_query = f"""
        UPDATE Comercial_Ventas_Dia_Abiertas_v2 SET
            fecha_operacion = '{ventas.fecha_operacion.isoformat()}',  # <-- SOBRESCRIBE la fecha
            total_estimado_dia = {ventas.total_estimado_dia},
            ...
        WHERE id = '{record_id}'
        """
    else:
        # INSERT nuevo registro
        ...
```

**Llave actual**: `(unidad_negocio_id, sucursal_id)`  
**Llave propuesta**: `(unidad_negocio_id, sucursal_id, fecha_operacion)`

### 3.4 Conteo de Registros por Unidad

```
Unidad           registros  fechas_distintas  rango
130-MER          1          1                 2026-05-13 a 2026-05-13
130MID           1          1                 2026-05-18 a 2026-05-18
130QRO           1          1                 2026-05-18 a 2026-05-18
130-QRO          1          1                 2026-05-13 a 2026-05-13
CIENFUEGOS       1          1                 2026-05-18 a 2026-05-18
ESTELAR          1          1                 2026-05-18 a 2026-05-18
LA-ESTELAR       1          1                 2026-05-13 a 2026-05-13
ORIGEN           1          1                 2026-05-18 a 2026-05-18
```

**Confirmación**: Solo hay **1 registro por unidad**. No hay historial por fecha.

### 3.5 Impacto de Agregar `fecha_operacion` a la Llave

**Cambios necesarios:**

1. **Índice UNIQUE**: Modificar `UQ_Ventas_Dia_v2_Unidad` para incluir `fecha_operacion`
2. **UPSERT**: Modificar el `check_query` para incluir `fecha_operacion`
3. **Tablero**: Ya lee por `fecha_operacion`, no necesita cambio

**Comportamiento esperado post-cambio:**
- Cada fecha_operacion tendrá su propio registro
- El tablero leerá el registro de la fecha_operacion calculada
- No se perderá data histórica al sobrescribir

### 3.6 Riesgo de Duplicados

**Riesgo: BAJO**

- El índice UNIQUE con `fecha_operacion` evitará duplicados para la misma combinación (unidad, sucursal, fecha)
- Cada ejecución del job solo escribe para UNA fecha_operacion por unidad
- No hay race conditions porque el scheduler usa locks

### 3.7 Cómo Leerá el Tablero la fecha_operacion Correcta

El endpoint `get_ventas_dia_snapshot_from_edarsahub()` ya hace esto:

```python
# Si hay unidad_negocio_id, calcula FechaOperacion
fecha_op_calc, _, _, _ = get_operational_window(unidad_negocio_id, now_mx)
fecha_operacion = fecha_op_calc.isoformat()

# Query filtra por fecha_operacion
query = f"""
SELECT ... FROM Comercial_Ventas_Dia_Abiertas_v2
WHERE server_id = '{server_id}'
  AND fecha_operacion = '{fecha_operacion}'
"""
```

**El tablero ya está preparado para leer por fecha_operacion específica.**

### 3.8 Impacto en 130QRO, ORIGEN y Demás Unidades

| Unidad | Estado Actual | Impacto del Cambio |
|--------|---------------|-------------------|
| ORIGEN | 1 registro (fecha_op=2026-05-18, $0.00) | Tendrá múltiples registros (uno por fecha) |
| 130QRO | 1 registro (fecha_op=2026-05-18, $0.00) | Tendrá múltiples registros (uno por fecha) |
| CIENFUEGOS | 1 registro | Igual |
| ESTELAR | 1 registro | Igual |
| 130MID | 1 registro | Igual |

**Todas las unidades se beneficiarán del historial por fecha.**

---

## 4. Causa Raíz Consolidada

### 4.1 BUG #1: Cálculo Intermitente de FechaOperacion

El job `sync_comercial_abiertas_v2_job.py` a veces calcula `fecha_operacion` incorrectamente. 

**Hipótesis**: Puede haber una race condition o el timezone no se está manejando consistentemente entre llamadas a `get_operational_window()`.

**Evidencia**: En el mismo minuto (11:31-11:37), algunas ejecuciones dieron 2026-05-17 y otras 2026-05-18.

### 4.2 BUG #2: Inconsistencia de Horarios (03:00 vs 06:00)

La tabla `Sistema_HorariosServicioUnidad` tiene configurado `hora_fin=03:00` para ORIGEN y 130QRO, pero la documentación y varios defaults en el código usan `06:00`.

**Acción requerida**: Alinear la configuración. Si la regla vigente es 06:00, actualizar la tabla. Si la regla es 03:00, actualizar la documentación.

### 4.3 BUG #3: UPSERT Sin Discriminar por Fecha

La llave `(unidad_negocio_id, sucursal_id)` permite solo 1 registro por unidad, lo que causa que cada sync sobrescriba el snapshot anterior, incluso si es de una fecha_operacion diferente.

---

## 5. Propuesta de Corrección (PLAN TÉCNICO COMPLETO)

### Paso 1: Corregir Inconsistencia de Horarios (DECISIÓN DEL USUARIO)

**Opción A**: Mantener 03:00 (configuración actual en BD)
- Actualizar documentación
- El período "cerrado" es 03:00-13:00

**Opción B**: Cambiar a 06:00 (según documentación)
- Ejecutar UPDATE en `Sistema_HorariosServicioUnidad`
- El período "cerrado" sería 06:00-13:00

### Paso 2: Modificar Índice UNIQUE

```sql
-- Eliminar índice actual
DROP INDEX UQ_Ventas_Dia_v2_Unidad ON Comercial_Ventas_Dia_Abiertas_v2;

-- Crear nuevo índice con fecha_operacion
CREATE UNIQUE INDEX UQ_Ventas_Dia_v2_Unidad_Fecha 
ON Comercial_Ventas_Dia_Abiertas_v2 (unidad_negocio_id, sucursal_id, fecha_operacion);
```

### Paso 3: Modificar UPSERT

```python
# En repository_comercial_edarsahub.py línea 260-265
check_query = f"""
SELECT id 
FROM Comercial_Ventas_Dia_Abiertas_v2
WHERE unidad_negocio_id = '{ventas.unidad_negocio_id}'
  AND sucursal_id = '{ventas.sucursal_id}'
  AND fecha_operacion = '{ventas.fecha_operacion.isoformat()}'
"""
```

### Paso 4: Investigar BUG de FechaOperacion Intermitente

- Agregar logging detallado en `get_operational_window()`
- Verificar si hay múltiples threads/procesos ejecutando el job
- Asegurar que el timezone se calcula una sola vez al inicio de cada job run

---

## 6. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Duplicados al migrar | BAJA | BAJO | El índice UNIQUE previene duplicados |
| Datos históricos perdidos | N/A | N/A | Ya solo hay 1 registro por unidad |
| Tablero no encuentra dato | BAJA | MEDIO | El tablero ya filtra por fecha_operacion |
| Race condition en job | MEDIA | MEDIO | El scheduler usa locks |

---

## 7. Validaciones Post-Implementación

1. ✅ Verificar que el índice UNIQUE se creó correctamente
2. ✅ Ejecutar sync manual y verificar que crea registro nuevo para fecha actual
3. ✅ Ejecutar sync manual con fecha anterior y verificar que NO sobrescribe
4. ✅ Verificar que Tablero Ejecutivo lee la fecha_operacion correcta
5. ✅ Confirmar que no hay duplicados en la tabla
6. ✅ Verificar logs de `Comercial_SyncLog_v2` para errores

---

## 8. Confirmación de Integridad

**Se confirma que durante este diagnóstico:**
- ✅ NO se modificó código alguno
- ✅ NO se ejecutaron queries UPDATE/DELETE/MERGE
- ✅ NO se alteraron índices ni tablas
- ✅ Todas las consultas fueron SELECT de solo lectura

---

## 9. Próximos Pasos

**Solicito autorización explícita para:**

1. **DECISIÓN**: ¿El horario correcto es 03:00 o 06:00? (Para alinear BD con código)
2. **IMPLEMENTAR**: Modificar índice UNIQUE para incluir `fecha_operacion`
3. **IMPLEMENTAR**: Modificar UPSERT para usar la nueva llave
4. **INVESTIGAR**: Agregar logging para diagnosticar el BUG intermitente de FechaOperacion

---

**Fin del Diagnóstico Corregido**
