# CAMBIO REGLA FECHA OPERATIVA CORTE 06:00

**Fecha:** 2026-05-18  
**Estado:** P0B COMPLETADO - CONFIGURACIÓN BD ACTUALIZADA  
**Decisión de Negocio:** CORTE OPERATIVO OFICIAL = 06:00 AM  

---

## 1. Decisión Oficial

### Regla Canónica de FechaOperacion para EDARSAHUB

```
SI hora_actual < 06:00:00 ENTONCES
    FechaOperacion = día calendario ANTERIOR
SINO
    FechaOperacion = día calendario ACTUAL
FIN
```

### Ejemplos

| Hora México | Fecha Calendario | FechaOperacion |
|-------------|------------------|----------------|
| 05:59 | 2026-05-18 | 2026-05-17 |
| 06:00 | 2026-05-18 | 2026-05-18 |
| 11:37 | 2026-05-18 | 2026-05-18 |
| 13:00 | 2026-05-18 | 2026-05-18 |
| 02:00 | 2026-05-19 | 2026-05-18 |

---

## 2. P0B COMPLETADO: Configuración BD Actualizada

### Cambio Ejecutado

**Fecha/Hora:** 2026-05-18 18:35:08 UTC

**SQL Ejecutado:**
```sql
UPDATE Sistema_HorariosServicioUnidad
SET 
    hora_fin_operativo = '06:00:00',
    fecha_modificacion = SYSUTCDATETIME()
WHERE unidad_negocio_id IN ('130MID', '130QRO', 'ORIGEN')
  AND hora_fin_operativo = '03:00:00'
  AND activo = 1;
```

**Resultado:** 21 filas actualizadas ✅

### Estado Actual en BD

| Unidad | hora_inicio | hora_fin | Estado |
|--------|-------------|----------|--------|
| **130MID** | 13:00:00 | **06:00:00** | ✅ ACTUALIZADO |
| **130QRO** | 13:00:00 | **06:00:00** | ✅ ACTUALIZADO |
| **ORIGEN** | 13:00:00 | **06:00:00** | ✅ ACTUALIZADO |
| CIENFUEGOS | 13:00:00 | 23:00:00 | Sin cambio |
| ESTELAR | 13:00:00 | 23:00:00 | Sin cambio |

---

## 3. Validación de get_operational_window()

### Lectura de BD ✅
```
ORIGEN: hora_fin=06:00:00 ✅ CORRECTO
130QRO: hora_fin=06:00:00 ✅ CORRECTO
130MID: hora_fin=06:00:00 ✅ CORRECTO
```

### Escenarios de FechaOperacion

| Timestamp | Esperado | ORIGEN | 130QRO | 130MID |
|-----------|----------|--------|--------|--------|
| 05:59 | 2026-05-17 | ✅ 2026-05-17 | ✅ 2026-05-17 | ✅ 2026-05-17 |
| 06:00 | 2026-05-18 | ⚠️ 2026-05-17 | ⚠️ 2026-05-17 | ⚠️ 2026-05-17 |
| 11:37 | 2026-05-18 | ⚠️ 2026-05-17 | ⚠️ 2026-05-17 | ⚠️ 2026-05-17 |
| 13:00 | 2026-05-18 | ✅ 2026-05-18 | ✅ 2026-05-18 | ✅ 2026-05-18 |
| 02:00 (día+1) | 2026-05-18 | ✅ 2026-05-18 | ✅ 2026-05-18 | ✅ 2026-05-18 |

### ⚠️ HALLAZGO CRÍTICO

La configuración de la BD ahora tiene `hora_fin=06:00`, pero la **lógica del código** en `operational_window.py` implementa "período cerrado":

```python
# Código actual (líneas 203-210)
else:
    # Entre hora_fin (06:00) y hora_inicio (13:00) → CERRADO
    fecha_operacion = fecha_calendario - timedelta(days=1)  # ← DÍA ANTERIOR
```

**La regla de negocio dice:** Si `hora >= 06:00` → día ACTUAL (sin considerar "cerrado")

**El código actual dice:** Si `06:00 <= hora < 13:00` → día ANTERIOR (período cerrado)

**Acción requerida en P0C:** Modificar la lógica del código para implementar la regla "corte 06:00 simple".

---

## 4. Validación de No Regresión ✅

| Validación | Estado |
|------------|--------|
| Login funciona | ✅ OK |
| /api/users | ✅ HTTP 200 |
| /api/servers | ✅ HTTP 200 |
| Tablero Ejecutivo responde | ✅ OK |
| ORIGEN visible | ✅ Sí |
| 130QRO visible | ✅ Sí |
| 130MID visible | ✅ Sí |
| source_period = EDARSAHUB_SQL | ✅ Todas las unidades |

---

## 5. Próximos Pasos

### P0C (PENDIENTE AUTORIZACIÓN)

**Objetivo:** Modificar la lógica del código para implementar "corte 06:00 simple"

**Archivo a modificar:** `/app/backend/core/utils/operational_window.py`

**Cambio propuesto:**
```python
# ANTES (líneas 186-210)
if cruza_medianoche:
    if hora_actual < hora_fin:
        fecha_operacion = día_anterior
    elif hora_actual >= hora_inicio:
        fecha_operacion = día_actual
    else:  # período cerrado
        fecha_operacion = día_anterior  # ← INCORRECTO según nueva regla

# DESPUÉS
if cruza_medianoche:
    if hora_actual < hora_fin:
        fecha_operacion = día_anterior
    else:
        fecha_operacion = día_actual  # ← CORRECTO: >= 06:00 siempre es día actual
```

### P0D (DESPUÉS DE P0C)

Modificar llave UPSERT para incluir `fecha_operacion`.

### P0E (DESPUÉS DE P0D)

Corregir datos erróneos en `Comercial_Ventas_Dia_Abiertas_v2`.

---

## 6. Confirmación de Integridad P0B

- ✅ UPDATE ejecutado exitosamente (21 filas)
- ✅ Verificación post-UPDATE completada
- ✅ Validación de no regresión completada
- ✅ NO se modificó código
- ✅ NO se alteraron índices ni otras tablas
- ✅ Solo se modificó `Sistema_HorariosServicioUnidad`

---

**Fin del Reporte P0B**
