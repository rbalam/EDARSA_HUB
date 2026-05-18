# DIAGNÓSTICO P0: Ventas del Día de ORIGEN No Se Reflejan en Tablero Ejecutivo

**Fecha:** 2026-05-18  
**Autor:** E1 Agent  
**Estado:** P0B COMPLETADO - PENDIENTE P0C (MODIFICAR CÓDIGO)  
**Prioridad:** P0  

---

## 1. Resumen Ejecutivo

### Problema Original
El usuario reportó que **ORIGEN tiene ventas del día de hoy, pero no se reflejan en el Tablero Ejecutivo**.

### Progreso

| Fase | Estado | Descripción |
|------|--------|-------------|
| P0A | ✅ COMPLETADO | Diagnóstico y preparación |
| **P0B** | ✅ **COMPLETADO** | Actualización BD (hora_fin=06:00) |
| P0C | ⏳ PENDIENTE | Modificar lógica del código |
| P0D | ⏳ PENDIENTE | Modificar llave UPSERT |
| P0E | ⏳ PENDIENTE | Corregir datos erróneos |

---

## 2. P0B Completado: Configuración BD

### Cambio Ejecutado
**Fecha/Hora:** 2026-05-18 18:35:08 UTC

```sql
UPDATE Sistema_HorariosServicioUnidad
SET hora_fin_operativo = '06:00:00', fecha_modificacion = SYSUTCDATETIME()
WHERE unidad_negocio_id IN ('130MID', '130QRO', 'ORIGEN')
  AND hora_fin_operativo = '03:00:00' AND activo = 1;
-- Resultado: 21 filas actualizadas ✅
```

### Estado Actual

| Unidad | hora_fin ANTES | hora_fin DESPUÉS |
|--------|----------------|------------------|
| 130MID | 03:00:00 | ✅ 06:00:00 |
| 130QRO | 03:00:00 | ✅ 06:00:00 |
| ORIGEN | 03:00:00 | ✅ 06:00:00 |

---

## 3. Validación de No Regresión

| Endpoint | Estado |
|----------|--------|
| Login | ✅ OK |
| /api/users | ✅ HTTP 200 |
| /api/servers | ✅ HTTP 200 |
| Tablero Ejecutivo | ✅ Responde |
| ORIGEN visible | ✅ source_period=EDARSAHUB_SQL |
| 130QRO visible | ✅ source_period=EDARSAHUB_SQL |
| 130MID visible | ✅ source_period=EDARSAHUB_SQL |

---

## 4. Hallazgo Crítico para P0C

### Problema de Lógica de Código

La BD ahora tiene `hora_fin=06:00`, pero la función `get_operational_window()` aún implementa "período cerrado":

| Hora México | Esperado (regla negocio) | Resultado Actual (código) |
|-------------|--------------------------|---------------------------|
| 05:59 | 2026-05-17 | ✅ 2026-05-17 |
| 06:00 | 2026-05-18 | ⚠️ 2026-05-17 |
| 11:37 | 2026-05-18 | ⚠️ 2026-05-17 |
| 13:00 | 2026-05-18 | ✅ 2026-05-18 |

### Causa

```python
# Código actual (operational_window.py líneas 203-210)
else:
    # Entre hora_fin (06:00) y hora_inicio (13:00) → "CERRADO"
    fecha_operacion = día_anterior  # ← NO cumple la regla de negocio
```

### Solución Requerida (P0C)

Modificar para implementar "corte 06:00 simple":
- Si `hora < 06:00` → día anterior
- Si `hora >= 06:00` → día actual (sin considerar "cerrado")

---

## 5. Próximos Pasos

### P0C (PENDIENTE AUTORIZACIÓN)

**Objetivo:** Modificar `/app/backend/core/utils/operational_window.py`

**Cambio propuesto:**
```python
# Cambiar la lógica del "else" para que >= hora_fin sea día actual
if hora_actual < hora_fin:
    fecha_operacion = día_anterior
else:
    fecha_operacion = día_actual  # ← Nuevo: >= 06:00 siempre es día actual
```

### P0D (DESPUÉS DE P0C)

Modificar llave UPSERT para incluir `fecha_operacion`.

---

## 6. Archivos Relacionados

- `/app/docs/reports/CAMBIO_REGLA_FECHA_OPERATIVA_CORTE_0600.md` - Detalle completo
- `/app/backend/core/utils/operational_window.py` - Código a modificar en P0C

---

**Fin del Reporte P0B**
