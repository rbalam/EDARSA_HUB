# DIAGNÓSTICO P0: Ventas del Día de ORIGEN No Se Reflejan en Tablero Ejecutivo

**Fecha:** 2026-05-18  
**Autor:** E1 Agent  
**Estado:** FASE P0A COMPLETADA - DIAGNÓSTICO CERRADO  
**Prioridad:** P0  

---

## 1. Resumen Ejecutivo

### Problema Original
El usuario reportó que **ORIGEN tiene ventas del día de hoy, pero no se reflejan en el Tablero Ejecutivo**.

### Causa Raíz Identificada

| # | Causa | Descripción |
|---|-------|-------------|
| 1 | **Configuración desactualizada** | La tabla `Sistema_HorariosServicioUnidad` tiene `hora_fin=03:00` en lugar de `06:00` |
| 2 | **Dos jobs en paralelo** | Hay dos schedulers/workers ejecutando el job de sync con estados de cache diferentes |
| 3 | **UPSERT sin fecha en llave** | La llave `(unidad_negocio_id, sucursal_id)` no discrimina por `fecha_operacion` |

### Decisión de Negocio

**REGLA OFICIAL**: Corte operativo = **06:00 AM**
- Ventas entre 00:00 y 05:59 → día operativo ANTERIOR
- Ventas desde 06:00 → día calendario ACTUAL

---

## 2. Configuración Actual vs Esperada

### Sistema_HorariosServicioUnidad

| Unidad | hora_fin ACTUAL | hora_fin ESPERADO | Estado |
|--------|-----------------|-------------------|--------|
| 130MID | 03:00:00 | 06:00:00 | ⚠️ DESACTUALIZADO |
| 130QRO | 03:00:00 | 06:00:00 | ⚠️ DESACTUALIZADO |
| ORIGEN | 03:00:00 | 06:00:00 | ⚠️ DESACTUALIZADO |
| CIENFUEGOS | 23:00:00 | Evaluar | ❓ NO_CRUZA_MN |
| ESTELAR | 23:00:00 | Evaluar | ❓ NO_CRUZA_MN |

---

## 3. Evidencia del Problema

### 3.1 Jobs en Paralelo

Se detectaron dos jobs ejecutándose simultáneamente:

| Hora Run | fecha_inicio | Observación |
|----------|--------------|-------------|
| 17:52:01 | 2026-05-18 | Job A |
| 17:51:53 | 2026-05-17 | Job B |
| 17:47:32 | 2026-05-18 | Job A |
| 17:46:53 | 2026-05-17 | Job B |

### 3.2 Pruebas de Determinismo

Con configuración actual (`hora_fin=03:00`):

| Hora México | Esperado (06:00) | Resultado Actual | Coincide |
|-------------|------------------|------------------|----------|
| 05:59 | 2026-05-17 | 2026-05-17 | ✓ |
| **06:00** | **2026-05-18** | **2026-05-17** | **✗** |
| **11:37** | **2026-05-18** | **2026-05-17** | **✗** |
| 13:00 | 2026-05-18 | 2026-05-18 | ✓ |
| 02:00 (día sig.) | 2026-05-18 | 2026-05-18 | ✓ |

**El código es DETERMINISTA pero la configuración es incorrecta.**

---

## 4. Plan de Corrección por Fases

### Fase P0A ✅ COMPLETADA
- Diagnóstico de configuración
- Propuesta de SQL de actualización
- Investigación de bug intermitente
- Validación de determinismo
- Generación de reportes

### Fase P0B (PENDIENTE AUTORIZACIÓN)
- Ejecutar UPDATE en `Sistema_HorariosServicioUnidad`
- Cambiar `hora_fin=03:00` → `hora_fin=06:00`
- Unidades afectadas: 130MID, 130QRO, ORIGEN

### Fase P0C (PENDIENTE AUTORIZACIÓN)
- Modificar índice UNIQUE para incluir `fecha_operacion`
- Modificar UPSERT para usar nueva llave

### Fase P0D (PENDIENTE AUTORIZACIÓN)
- Limpiar datos erróneos en `Comercial_Ventas_Dia_Abiertas_v2`

---

## 5. SQL Propuesto (P0B)

```sql
BEGIN TRANSACTION;

UPDATE Sistema_HorariosServicioUnidad
SET 
    hora_fin_operativo = '06:00:00',
    fecha_modificacion = SYSUTCDATETIME()
WHERE unidad_negocio_id IN ('130MID', '130QRO', 'ORIGEN')
  AND hora_fin_operativo = '03:00:00'
  AND activo = 1;

-- Verificar: debe afectar 21 filas
SELECT @@ROWCOUNT AS FilasActualizadas;

-- Si OK:
COMMIT TRANSACTION;

-- Si error:
-- ROLLBACK TRANSACTION;
```

---

## 6. Confirmación de Integridad

- ✅ NO se modificó código
- ✅ NO se ejecutaron UPDATE/DELETE/MERGE
- ✅ Todas las consultas fueron SELECT de solo lectura
- ✅ El script SQL propuesto NO ha sido ejecutado

---

## 7. Archivos Relacionados

- `/app/docs/reports/CAMBIO_REGLA_FECHA_OPERATIVA_CORTE_0600.md` - Detalle de la regla 06:00
- `/app/backend/core/utils/operational_window.py` - Función get_operational_window()
- `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` - Job de sincronización
- `/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py` - UPSERT actual

---

**Fin del Diagnóstico P0A**
