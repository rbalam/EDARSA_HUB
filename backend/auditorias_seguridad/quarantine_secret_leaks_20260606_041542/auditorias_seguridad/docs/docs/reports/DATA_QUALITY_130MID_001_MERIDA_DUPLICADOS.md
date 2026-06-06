# REPORTE: DATA-QUALITY-130MID-001
## Unificación de Mérida (Duplicados por Acentos)

**Fecha de Diagnóstico:** 2026-05-26  
**Estado:** PENDIENTE (Requiere ejecución con credenciales de escritura)  
**Prioridad:** P0

---

## 1. PROBLEMA IDENTIFICADO

La unidad de negocio **130MID (Mérida)** tiene datos partidos en dos variantes de nombre:

| Variante | Registros | Rango de Fechas | Ventas Totales |
|----------|-----------|-----------------|----------------|
| `130° MÉRIDA` (con acento) | 734 | 2024-05-01 a 2026-05-09 | $116,628,785 |
| `130° MERIDA` (sin acento) | 15 | 2026-05-10 a 2026-05-24 | $2,187,938 |

### Causa Raíz
- El **nombre canónico oficial** en `Unidades_Negocio` es: **"130° MERIDA"** (sin acento)
- Las sincronizaciones históricas (2 años de datos) usaron el nombre con acento
- Esto causa que los dashboards muestren Mérida partida en dos filas

---

## 2. TABLA AFECTADA

- **Tabla:** `Comercial_KPIs_Diarios_v2`
- **Columna:** `unidad_negocio_nombre`
- **Base de datos:** EDARSAHUB

---

## 3. SOLUCIÓN: SCRIPT DE CONSOLIDACIÓN

### Prerequisitos
- Usuario SQL Server con **permisos de escritura** en EDARSAHUB (no usar `HRLectura`)

### Script a Ejecutar

```sql
-- ===========================================================================
-- SCRIPT DE CONSOLIDACIÓN: DATA-QUALITY-130MID-001
-- ===========================================================================
-- Descripción: Unifica variantes de nombre de Mérida al valor canónico
-- Ejecutar con: Usuario con permisos de escritura en EDARSAHUB
-- Fecha: 2026-05-26
-- ===========================================================================

-- PASO 1: VERIFICAR ESTADO ACTUAL
SELECT 
    unidad_negocio_nombre,
    COUNT(*) as registros,
    MIN(fecha_operacion) as desde,
    MAX(fecha_operacion) as hasta
FROM Comercial_KPIs_Diarios_v2 
WHERE unidad_negocio_id = '130MID'
GROUP BY unidad_negocio_nombre;

-- PASO 2: CREAR BACKUP (tabla temporal)
SELECT *
INTO #Backup_130MID_PreFix
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = '130MID'
  AND unidad_negocio_nombre = '130° MÉRIDA';

-- Verificar backup creado
SELECT 'Registros en backup:' as info, COUNT(*) as total FROM #Backup_130MID_PreFix;

-- PASO 3: ACTUALIZACIÓN
UPDATE Comercial_KPIs_Diarios_v2
SET 
    unidad_negocio_nombre = '130° MERIDA',
    fecha_ultima_actualizacion = GETDATE(),
    version = ISNULL(version, 0) + 1
WHERE unidad_negocio_id = '130MID'
  AND unidad_negocio_nombre = '130° MÉRIDA';

-- Verificar registros actualizados
SELECT @@ROWCOUNT as registros_actualizados;

-- PASO 4: VERIFICACIÓN FINAL
SELECT 
    unidad_negocio_nombre,
    COUNT(*) as registros
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = '130MID'
GROUP BY unidad_negocio_nombre;

-- El resultado debe mostrar SOLO "130° MERIDA" con 749 registros
```

---

## 4. ENDPOINTS DE MONITOREO

### Auditoría (antes de ejecutar el script)
```bash
GET /api/admin/data-quality/audit/merida-duplicates
```

### Verificación (después de ejecutar el script)
```bash
GET /api/admin/data-quality/verify/merida-consolidation
```

---

## 5. RESULTADO ESPERADO

Después de ejecutar el script:
- **Una sola fila** para Mérida en todos los dashboards
- **749 registros** unificados bajo `130° MERIDA`
- Endpoint `/verify/merida-consolidation` retorna status: **"CONSOLIDADO"**

---

## 6. PREVENCIÓN FUTURA

El problema se originó porque los jobs de sincronización usaban el nombre del servidor local en lugar del nombre canónico de `Unidades_Negocio`. 

**Recomendación:** Verificar que todos los jobs de sync usen `unidad_negocio_nombre` desde la tabla maestra `Unidades_Negocio`, no desde el nombre del servidor origen.

---

## 7. ARCHIVOS RELACIONADOS

- **API de auditoría:** `/app/backend/api/admin_data_quality.py`
- **Tabla canónica:** `EDARSAHUB.Unidades_Negocio`
- **Tabla afectada:** `EDARSAHUB.Comercial_KPIs_Diarios_v2`
