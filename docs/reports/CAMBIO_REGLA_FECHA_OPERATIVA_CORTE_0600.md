# CAMBIO REGLA FECHA OPERATIVA CORTE 06:00

**Fecha:** 2026-05-18  
**Estado:** FASE P0A COMPLETADA - PENDIENTE AUTORIZACIÓN P0B  
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

## 2. Configuración Actual en BD

### Sistema_HorariosServicioUnidad

| Unidad | hora_inicio | hora_fin | cruza_mn | Estado |
|--------|-------------|----------|----------|--------|
| **130MID** | 13:00:00 | **03:00:00** | True | ⚠️ DESACTUALIZADO |
| **130QRO** | 13:00:00 | **03:00:00** | True | ⚠️ DESACTUALIZADO |
| **ORIGEN** | 13:00:00 | **03:00:00** | True | ⚠️ DESACTUALIZADO |
| CIENFUEGOS | 13:00:00 | 23:00:00 | False | ❓ NO_CRUZA_MN |
| ESTELAR | 13:00:00 | 23:00:00 | False | ❓ NO_CRUZA_MN |

### Resumen

- **3 unidades** con hora_fin=03:00 (REQUIEREN UPDATE a 06:00):
  - 130MID
  - 130QRO
  - ORIGEN

- **2 unidades** con hora_fin=23:00 (NO cruzan medianoche):
  - CIENFUEGOS
  - ESTELAR
  - **Nota**: Evaluar si aplica la regla 06:00 para estas unidades

---

## 3. SQL Propuesto para Alinear a 06:00

```sql
-- ============================================================================
-- SCRIPT: UPDATE CORTE OPERATIVO A 06:00 AM
-- FECHA: 2026-05-18
-- ALCANCE: 130MID, 130QRO, ORIGEN
-- ============================================================================

-- PASO 1: SELECT ANTES (verificar estado actual)
SELECT 
    unidad_negocio_id,
    dia_semana,
    hora_inicio_operativo,
    hora_fin_operativo,
    cruza_medianoche,
    activo,
    fecha_modificacion
FROM Sistema_HorariosServicioUnidad
WHERE unidad_negocio_id IN ('130MID', '130QRO', 'ORIGEN')
  AND hora_fin_operativo = '03:00:00'
ORDER BY unidad_negocio_id, dia_semana;
-- Resultado esperado: 21 filas

-- PASO 2: UPDATE CONTROLADO (dentro de transacción)
BEGIN TRANSACTION;

UPDATE Sistema_HorariosServicioUnidad
SET 
    hora_fin_operativo = '06:00:00',
    fecha_modificacion = SYSUTCDATETIME()
WHERE unidad_negocio_id IN ('130MID', '130QRO', 'ORIGEN')
  AND hora_fin_operativo = '03:00:00'
  AND activo = 1;

-- Verificar filas afectadas
SELECT @@ROWCOUNT AS FilasActualizadas;
-- Debe ser 21

-- PASO 3: SELECT DESPUÉS (verificar cambio)
SELECT 
    unidad_negocio_id,
    dia_semana,
    hora_inicio_operativo,
    hora_fin_operativo,
    cruza_medianoche,
    activo,
    fecha_modificacion
FROM Sistema_HorariosServicioUnidad
WHERE unidad_negocio_id IN ('130MID', '130QRO', 'ORIGEN')
ORDER BY unidad_negocio_id, dia_semana;
-- Debe mostrar hora_fin=06:00:00

-- PASO 4: COMMIT o ROLLBACK
COMMIT TRANSACTION;
-- o ROLLBACK TRANSACTION; si hay error
```

---

## 4. Causa del "BUG Intermitente"

### Hallazgo

Se detectaron **DOS JOBS** ejecutándose en paralelo:
- Job A: Ejecuta a los segundos `:00` → Calcula `fecha_inicio=2026-05-18`
- Job B: Ejecuta a los segundos `:49` → Calcula `fecha_inicio=2026-05-17`

### Evidencia

```
ABIERTA-20260518-175200-dc4f | 2026-05-18 | 17:52:01 UTC
ABIERTA-20260518-175149-0826 | 2026-05-17 | 17:51:53 UTC
ABIERTA-20260518-174731-0396 | 2026-05-18 | 17:47:32 UTC
ABIERTA-20260518-174649-9bdf | 2026-05-17 | 17:46:53 UTC
```

### Causa Probable

1. **Cache de Horarios**: El módulo `operational_window.py` tiene un cache de 30 minutos
2. **Múltiples Workers/Instancias**: Cada worker tiene su propio cache en memoria
3. **Desincronización**: Cuando se modificó la configuración, algunos workers tenían valores viejos

### Conclusión

El código ES DETERMINISTA. El problema es:
1. La BD tiene `hora_fin=03:00` (valor incorrecto)
2. Hay múltiples instancias con diferentes estados de cache
3. El UPSERT sobrescribe el único registro, causando "oscilación" de datos

---

## 5. Pruebas de Determinismo

### Resultados (con configuración actual: hora_fin=03:00)

| Timestamp | Esperado (06:00) | Resultado Actual | Coincide |
|-----------|------------------|------------------|----------|
| 2026-05-18 05:59 | 2026-05-17 | 2026-05-17 | ✓ |
| 2026-05-18 06:00 | 2026-05-18 | 2026-05-17 | ✗ |
| 2026-05-18 11:37 | 2026-05-18 | 2026-05-17 | ✗ |
| 2026-05-18 13:00 | 2026-05-18 | 2026-05-18 | ✓ |
| 2026-05-19 02:00 | 2026-05-18 | 2026-05-18 | ✓ |

### Interpretación

- El código es **100% DETERMINISTA** (siempre da el mismo resultado para la misma entrada)
- Las diferencias son porque la BD tiene `hora_fin=03:00`, NO `06:00`
- Al actualizar la BD a `06:00`, los resultados coincidirán

---

## 6. Recomendación para Siguiente Fase

### P0B: Actualizar Sistema_HorariosServicioUnidad

**Acción**: Ejecutar el script SQL propuesto en la sección 3

**Impacto esperado**:
- Las 3 unidades (130MID, 130QRO, ORIGEN) usarán corte 06:00
- La función `get_operational_window()` calculará correctamente
- A las 11:37 México, devolverá `fecha_operacion = 2026-05-18`

**Riesgos**:
- BAJO: Solo modifica configuración, no lógica de código
- Cache de 30 minutos: Puede haber inconsistencias temporales hasta que expire

### P0C: Modificar llave UPSERT

**Acción**: Agregar `fecha_operacion` a la llave del UPSERT

**Dependencia**: Requiere que P0B esté completado y validado

### P0D: Corregir datos erróneos

**Acción**: Limpiar snapshots con fecha incorrecta

**Dependencia**: Requiere que P0B y P0C estén completados

---

## 7. Confirmación de Integridad

Durante esta fase P0A:
- ✅ NO se modificó código
- ✅ NO se ejecutaron UPDATE/DELETE/MERGE en datos
- ✅ NO se alteraron índices ni tablas
- ✅ Todas las consultas fueron SELECT de solo lectura
- ✅ El script SQL propuesto NO ha sido ejecutado

---

## 8. Próximos Pasos

Solicito **autorización explícita** para:

| Fase | Acción | Estado |
|------|--------|--------|
| **P0B** | Ejecutar UPDATE en Sistema_HorariosServicioUnidad (cambiar 03:00 → 06:00) | PENDIENTE |
| **P0C** | Modificar llave UPSERT para incluir fecha_operacion | PENDIENTE |
| **P0D** | Corregir datos erróneos en Comercial_Ventas_Dia_Abiertas_v2 | PENDIENTE |

---

**Fin del Reporte P0A**
