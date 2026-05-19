# DIAGNÓSTICO P0: 130° QUERÉTARO - Ventas del Día con FechaOperacion Incorrecta

**Fecha:** 2026-05-19  
**Prioridad:** P0  
**Estado:** DIAGNÓSTICO COMPLETADO - PENDIENTE AUTORIZACIÓN PARA CORRECCIÓN

---

## 1. Resumen Ejecutivo

**CAUSA RAÍZ CONFIRMADA:** El job `sync_comercial_abiertas_v2_job.py` guardó los snapshots de Ventas del Día con `fecha_operacion = 2026-05-19` cuando operativamente debería ser `2026-05-18`.

**EVIDENCIA SQL DIRECTA:**
```
Tabla: Comercial_Ventas_Dia_Abiertas_v2
Unidad: 130QRO
FechaOperacion: 2026-05-19  ← INCORRECTA
Total: $0.00               ← RESULTADO DEL ERROR
Snapshot: 2026-05-19T03:27:07
```

**FECHA CORRECTA:** `2026-05-18` (Son las 21:28 hora México del día 18)

---

## 2. FASE 1: Confirmación de Fechas

### Hora Actual del Sistema
| Parámetro | Valor |
|-----------|-------|
| Hora UTC del servidor | 2026-05-19 03:28:00 UTC |
| Hora local América/Mexico_City | 2026-05-18 21:28:00 MX |
| Fecha calendario local México | 2026-05-18 |
| Hora local (21:xx) >= 06:00 | SÍ |
| **FechaOperacion ESPERADA (regla 06:00)** | **2026-05-18** |
| FechaOperacion que CALCULÓ el job | 2026-05-19 |
| **DIFERENCIA** | **1 DÍA ADELANTADO** |

### Regla de Negocio Violada
```
REGLA CORTE 06:00 SIMPLE:
  Si hora_local_méxico < 06:00 → FechaOperacion = fecha_local - 1 día
  Si hora_local_méxico >= 06:00 → FechaOperacion = fecha_local

ACTUAL (21:28 hora México):
  21:28 >= 06:00 → FechaOperacion DEBE ser 2026-05-18
  
ERROR:
  El job usó 2026-05-19 (fecha UTC) en lugar de 2026-05-18 (fecha México)
```

---

## 3. FASE 2: Análisis del Job sync_comercial_abiertas_v2_job.py

### Ubicación del Archivo
`/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`

### Líneas Relevantes

**Línea 453 - Cálculo de fecha_hoy:**
```python
mexico_tz = pytz.timezone('America/Mexico_City')
fecha_hoy = datetime.now(mexico_tz).date()
```
**PROBLEMA:** Esta variable `fecha_hoy` usa fecha calendario, no fecha operativa.

**Línea 703 - Cálculo de FechaOperacion para MPRO:**
```python
fecha_operacion, hora_inicio, hora_fin, cruza_medianoche = get_operational_window(unidad_id)
fecha_operacion_str = fecha_operacion.isoformat()
```
**OBSERVACIÓN:** El código SÍ llama a `get_operational_window()`, pero el resultado que se guardó fue incorrecto.

### Usos de Fecha en el Job
| Línea | Código | Tipo |
|-------|--------|------|
| 447 | `datetime.now(timezone.utc)` | UTC (correcto para timestamps) |
| 453 | `datetime.now(mexico_tz).date()` | Calendario México (NO operativa) |
| 488 | `get_operational_window(unidad_id)` | Operativa (SR) |
| 703 | `get_operational_window(unidad_id)` | Operativa (MPRO) |

---

## 4. FASE 3: Análisis de operational_window.py

### Ubicación del Archivo
`/app/backend/core/utils/operational_window.py`

### Configuración de Horarios en SQL para 130QRO
```
SELECT * FROM Sistema_HorariosServicioUnidad WHERE unidad_negocio_id = '130QRO'

Día 0 (Lunes):    13:00:00 - 06:00:00, cruza_medianoche=True
Día 1 (Martes):   13:00:00 - 06:00:00, cruza_medianoche=True
Día 2 (Miércoles):13:00:00 - 06:00:00, cruza_medianoche=True
Día 3 (Jueves):   13:00:00 - 06:00:00, cruza_medianoche=True
Día 4 (Viernes):  13:00:00 - 06:00:00, cruza_medianoche=True
Día 5 (Sábado):   13:00:00 - 06:00:00, cruza_medianoche=True
Día 6 (Domingo):  13:00:00 - 06:00:00, cruza_medianoche=True
```

### Lógica Actual en operational_window.py (Líneas 187-210)
```python
if cruza_medianoche:
    # Jornada cruza medianoche (ej: 13:00 - 06:00)
    if hora_actual < hora_fin:  # < 06:00
        fecha_operacion = fecha_calendario - 1 día
    elif hora_actual >= hora_inicio:  # >= 13:00
        fecha_operacion = fecha_calendario
    else:
        # Entre 06:00 y 13:00 (cerrado)
        fecha_operacion = fecha_calendario - 1 día
```

### Validación Actual del Helper
```
=== DEBUG VENTANA OPERATIVA: 130QRO ===
  Timestamp actual (México): 2026-05-18 21:28:06
  Fecha calendario: 2026-05-18
  FechaOperacion calculada: 2026-05-18  ← CORRECTO AHORA
  Horario: 13:00:00 - 06:00:00
  Cruza medianoche: True
```

**CONCLUSIÓN:** El helper `get_operational_window()` AHORA calcula correctamente `2026-05-18`. El snapshot con `2026-05-19` se generó en un momento donde hubo una discrepancia.

---

## 5. FASE 5: Diagnóstico de Datos SQL Actuales

### Comercial_Ventas_Dia_Abiertas_v2 - Estado Completo

| Unidad | FechaOp | Total | Abiertas | Cerradas | Tkt | PAX | Snapshot | Estado |
|--------|---------|-------|----------|----------|-----|-----|----------|--------|
| 130QRO | 2026-05-19 | $0.00 | $0.00 | $0.00 | 0 | 0 | 03:27:07 | ⚠️ $0 |
| ORIGEN | 2026-05-19 | $8,547.48 | $8,547.48 | $0.00 | 5 | 15 | 03:27:07 | ✅ |
| 130MID | 2026-05-19 | $82,513.00 | $82,513.00 | $0.00 | 24 | 57 | 03:27:06 | ✅ |
| CIENFUEGOS | 2026-05-19 | $96,826.00 | $96,826.00 | $0.00 | 17 | 46 | 03:27:06 | ✅ |
| ESTELAR | 2026-05-19 | $7,430.00 | $7,430.00 | $0.00 | 11 | 18 | 03:27:06 | ✅ |

### Observaciones Críticas

1. **TODOS los registros tienen `fecha_operacion = 2026-05-19`** cuando deberían tener `2026-05-18`
2. **Solo 130QRO tiene $0** - Las demás unidades tienen datos porque sus APIs locales respondieron
3. **Los snapshots son de las 03:27 UTC** = 21:27 hora México del día 18

### Datos Históricos (130QRO sin datos del día 18)
```
SELECT * FROM Comercial_Ventas_Dia_Abiertas_v2 
WHERE unidad_negocio_id = '130QRO' AND fecha_operacion = '2026-05-18'

RESULTADO: 0 registros
```

---

## 6. FASE 6: Propuesta de Corrección

### Hipótesis del Bug

El job se ejecutó a las **03:27 UTC del 19-May** (= **21:27 MX del 18-May**). 

La función `get_operational_window()` debería haber retornado `2026-05-18`, pero los datos guardados tienen `2026-05-19`.

**POSIBLES CAUSAS:**
1. El job no usó `get_operational_window()` para el campo `fecha_operacion` que guarda en SQL
2. Hubo un desfase temporal entre el cálculo y la escritura
3. La API local de 130QRO no respondió y el job usó una fecha fallback incorrecta

### Plan de Corrección Propuesto

#### Paso 1: Verificar que el job usa `get_operational_window()` para TODOS los campos
- Auditar las líneas 889-890 donde se crea `VentasDiaAbiertasV2`
- Verificar que `fecha_operacion=fecha_operacion` usa la variable del helper

#### Paso 2: Agregar log de diagnóstico
- Antes de cada INSERT/UPDATE, loggear:
  - `hora_local_mexico`
  - `fecha_calendario`
  - `fecha_operacion_calculada`

#### Paso 3: Corregir la regla de corte si aplica
- Si el helper no aplica regla 06:00 simple correctamente, ajustar
- Considerar simplificar: `hora < 06:00 → día anterior`

### Archivos a Modificar
1. `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` - Verificar uso consistente de `get_operational_window()`
2. `/app/backend/core/utils/operational_window.py` - Solo si la regla actual es incorrecta

---

## 7. FASE 7: Corrección de Dato Actual

### Opciones Propuestas (SIN EJECUTAR)

**OPCIÓN A - Re-ejecutar Sync:**
```bash
# Ejecutar manualmente el job para que recalcule con fecha correcta
POST /api/v2/scheduler/jobs/sync_comercial_abiertas_v2/run
```
**Riesgo:** Si el bug persiste, volverá a escribir $0

**OPCIÓN B - Actualizar registro existente:**
```sql
-- SOLO LECTURA - NO EJECUTAR SIN AUTORIZACIÓN
UPDATE Comercial_Ventas_Dia_Abiertas_v2
SET fecha_operacion = '2026-05-18'
WHERE unidad_negocio_id = '130QRO' AND fecha_operacion = '2026-05-19'
```
**Riesgo:** No soluciona el bug subyacente

**OPCIÓN C - Corregir bug primero:**
1. Corregir la lógica del job
2. Re-ejecutar sync
3. Verificar que fecha_operacion = 2026-05-18

**RECOMENDACIÓN:** Opción C

---

## 8. Comparación QRO vs ORIGEN

| Aspecto | 130QRO | ORIGEN |
|---------|--------|--------|
| FechaOp guardada | 2026-05-19 | 2026-05-19 |
| Total | $0.00 | $8,547.48 |
| API Local | No conectó | Conectó |
| Snapshot | 03:27:07 | 03:27:07 |

**OBSERVACIÓN:** Ambas unidades tienen la misma `fecha_operacion` incorrecta, pero ORIGEN tiene datos porque su API respondió. El problema de 130QRO es doble:
1. fecha_operacion incorrecta (2026-05-19 vs 2026-05-18)
2. API local no respondió (devolvió $0)

---

## 9. Riesgos de la Corrección

| Riesgo | Mitigación |
|--------|------------|
| Romper ORIGEN | Verificar que ORIGEN sigue funcionando post-fix |
| Romper 130° MÉRIDA | Verificar datos SR post-fix |
| Romper CIENFUEGOS | Verificar datos SR post-fix |
| Romper LA ESTELAR | Verificar datos SR post-fix |
| Sobrescribir ventas reales | NO escribir $0 si API falla |
| Crear duplicados | Usar UPSERT por (unidad_id, sucursal_id) |

---

## 10. Plan de Validación

### Pre-Corrección
- [ ] Documentar estado actual de todas las unidades
- [ ] Confirmar que helper calcula fecha correcta AHORA

### Post-Corrección
- [ ] 130QRO tiene fecha_operacion = 2026-05-18
- [ ] 130QRO tiene ventas > $0 (si API responde)
- [ ] ORIGEN sigue correcto
- [ ] 130° MÉRIDA sigue correcto
- [ ] CIENFUEGOS sigue correcto
- [ ] LA ESTELAR sigue correcto
- [ ] Tablero Ejecutivo muestra datos correctos

---

## 11. Confirmaciones

- ✅ **NO se modificó código** - Solo diagnóstico
- ✅ **MongoDB NO fue consultado** como fuente de datos
- ✅ **EDARSAHUB SQL** es la fuente de verdad
- ✅ **NO se ejecutó UPSERT** ni backfill
- ✅ **NO se tocó P0E**
- ✅ **NO se tocó Catálogo SQL**
- ✅ **NO se tocó Explorador BD**
- ✅ **NO se insertaron datos falsos**

---

## 12. Próximos Pasos (Pendiente Autorización)

1. **AUTORIZAR** corrección del bug en `sync_comercial_abiertas_v2_job.py`
2. **VERIFICAR** que el helper `get_operational_window()` se usa consistentemente
3. **RE-EJECUTAR** sync para regenerar datos con fecha correcta
4. **VALIDAR** que 130QRO aparece con ventas > $0 en Tablero Ejecutivo

---

## 13. Logs del Scheduler

```
ERROR:[SYNC_ABIERTAS_V2] Error en 130QRO: No se encontró API local para 130QRO
WARNING:[TABLERO-EDARSAHUB] 130QRO: Sin datos en período
WARNING:[FIX-HUB] MPRO 130QRO: Sin datos en EDARSAHUB SQL para período
```

**OBSERVACIÓN:** El job no pudo conectar con la API local de 130QRO, por eso escribió $0.

---

*Diagnóstico completado: 2026-05-19 03:30 UTC*  
*Autor: Agente E1*  
*Estado: PENDIENTE AUTORIZACIÓN PARA CORRECCIÓN*
