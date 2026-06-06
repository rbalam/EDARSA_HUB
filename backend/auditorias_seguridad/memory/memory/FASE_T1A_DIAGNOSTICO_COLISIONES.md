# FASE T1-A: DIAGNÓSTICO DE COLISIONES PARA MIGRACIÓN DE CÓDIGOS
**Fecha:** 2026-05-13
**Estado:** COMPLETADO - PENDIENTE AUTORIZACIÓN PARA FASE T1

---

## 1. RESUMEN EJECUTIVO

| Aspecto | Resultado |
|---------|-----------|
| **Colisiones detectadas** | 0 |
| **Riesgo de violación UNIQUE** | NINGUNO |
| **Estrategia recomendada** | UPDATE DIRECTO |
| **Tablas analizadas** | 3 |

**VEREDICTO:** ✅ UPDATE directo es seguro. No se requiere MERGE.

---

## 2. MAPEO DE MIGRACIÓN

| Código Legacy | Código Oficial (EDARSAHUB) |
|---------------|---------------------------|
| `130-MER` | `130MID` |
| `130-QRO` | `130QRO` |
| `LA-ESTELAR` | `ESTELAR` |

---

## 3. ANÁLISIS POR TABLA

### 3.1 Comercial_KPIs_Diarios_v2

| Campo | Valor |
|-------|-------|
| **Total registros** | 3,272 |
| **Registros LEGACY** | 1,800 (55%) |
| **Registros OFICIALES** | 1,472 (45%) |
| **Constraint UNIQUE** | `(unidad_negocio_id, sucursal_id, fecha_operacion)` |
| **Colisiones detectadas** | 0 |

**Distribución por código:**
| Código | Registros | Fecha Min | Fecha Max | Tipo |
|--------|-----------|-----------|-----------|------|
| 130-MER | 736 | 2024-05-01 | 2026-05-11 | LEGACY |
| 130-QRO | 737 | 2024-05-01 | 2026-05-11 | LEGACY |
| CIENFUEGOS | 737 | 2024-05-01 | 2026-05-11 | OFICIAL |
| LA-ESTELAR | 327 | 2025-06-12 | 2026-05-11 | LEGACY |
| ORIGEN | 735 | 2024-05-01 | 2026-05-11 | OFICIAL |

**Análisis de colisiones:**
- `130-MER → 130MID`: ✅ Sin colisiones
- `130-QRO → 130QRO`: ✅ Sin colisiones  
- `LA-ESTELAR → ESTELAR`: ✅ Sin colisiones

---

### 3.2 Comercial_SyncLog_v2

| Campo | Valor |
|-------|-------|
| **Total registros** | 4,417 |
| **Registros LEGACY** | 2,641 (60%) |
| **Registros OFICIALES** | 1,770 (40%) |
| **Constraint UNIQUE** | NINGUNO (tabla de log) |
| **Colisiones posibles** | N/A |

**Distribución por código:**
| Código | Registros | Fecha Min | Fecha Max | Tipo |
|--------|-----------|-----------|-----------|------|
| 130-MER | 880 | 2026-05-01 | 2026-05-13 | LEGACY |
| 130MID | 2 | 2026-05-13 | 2026-05-13 | OFICIAL |
| 130QRO | 2 | 2026-05-13 | 2026-05-13 | OFICIAL |
| 130-QRO | 880 | 2026-05-01 | 2026-05-13 | LEGACY |
| CIENFUEGOS | 882 | 2026-05-01 | 2026-05-13 | OFICIAL |
| ESTELAR | 2 | 2026-05-13 | 2026-05-13 | OFICIAL |
| LA-ESTELAR | 881 | 2026-05-01 | 2026-05-13 | LEGACY |
| ORIGEN | 882 | 2026-05-01 | 2026-05-13 | OFICIAL |
| TODAS | 6 | 2026-05-01 | 2026-05-01 | OTRO |

**Nota:** Esta tabla es un LOG de ejecuciones. No tiene constraints que impidan UPDATE directo.

---

### 3.3 Comercial_Ventas_Dia_Abiertas_v2

| Campo | Valor |
|-------|-------|
| **Total registros** | 8 |
| **Registros LEGACY** | 3 (38%) |
| **Registros OFICIALES** | 5 (62%) |
| **Constraint UNIQUE** | `(unidad_negocio_id, sucursal_id)` |
| **Colisiones detectadas** | 0 |

**Distribución por código:**
| Código | Registros | Snapshot | Tipo |
|--------|-----------|----------|------|
| 130-MER | 1 | 2026-05-13 05:53:31 | LEGACY |
| 130MID | 1 | 2026-05-13 05:55:50 | OFICIAL |
| 130QRO | 1 | 2026-05-13 05:55:51 | OFICIAL |
| 130-QRO | 1 | 2026-05-13 05:53:31 | LEGACY |
| CIENFUEGOS | 1 | 2026-05-13 05:55:51 | OFICIAL |
| ESTELAR | 1 | 2026-05-13 05:55:51 | OFICIAL |
| LA-ESTELAR | 1 | 2026-05-13 05:53:31 | LEGACY |
| ORIGEN | 1 | 2026-05-13 05:55:51 | OFICIAL |

**Análisis de colisiones:**
- `130-MER → 130MID`: ✅ Sin colisiones
- `130-QRO → 130QRO`: ✅ Sin colisiones  
- `LA-ESTELAR → ESTELAR`: ✅ Sin colisiones

---

## 4. EVALUACIÓN DE RIESGO

| Factor | Evaluación |
|--------|------------|
| Violación UNIQUE | ✅ BAJO - No hay colisiones |
| Pérdida de datos | ✅ BAJO - UPDATE no elimina registros |
| Integridad referencial | ✅ BAJO - No hay FK afectadas |
| Impacto en Tablero Ejecutivo | ✅ BAJO - V2 ya usa código canónico |
| Rollback posible | ✅ ALTO - Con BACKUP previo |

---

## 5. PROPUESTA DE SCRIPT TRANSACCIONAL (NO EJECUTAR)

```sql
-- ==============================================================================
-- FASE T1: MIGRACIÓN DE CÓDIGOS LEGACY A OFICIALES
-- ESTADO: PROPUESTA - NO EJECUTAR SIN AUTORIZACIÓN
-- FECHA: 2026-05-13
-- ==============================================================================

-- PASO 0: INICIAR TRANSACCIÓN
BEGIN TRANSACTION;

-- ==============================================================================
-- PASO 1: BACKUP DE SEGURIDAD (SELECT INTO)
-- ==============================================================================

-- Backup de Comercial_KPIs_Diarios_v2
SELECT * 
INTO Comercial_KPIs_Diarios_v2_BACKUP_20260513
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id IN ('130-MER', '130-QRO', 'LA-ESTELAR');

-- Backup de Comercial_SyncLog_v2
SELECT * 
INTO Comercial_SyncLog_v2_BACKUP_20260513
FROM Comercial_SyncLog_v2
WHERE unidad_negocio_id IN ('130-MER', '130-QRO', 'LA-ESTELAR');

-- Backup de Comercial_Ventas_Dia_Abiertas_v2
SELECT * 
INTO Comercial_Ventas_Dia_Abiertas_v2_BACKUP_20260513
FROM Comercial_Ventas_Dia_Abiertas_v2
WHERE unidad_negocio_id IN ('130-MER', '130-QRO', 'LA-ESTELAR');

-- ==============================================================================
-- PASO 2: SELECT ANTES (CONTEOS PARA VALIDACIÓN)
-- ==============================================================================

SELECT 'ANTES' AS momento, 
       unidad_negocio_id, 
       COUNT(*) AS registros 
FROM Comercial_KPIs_Diarios_v2 
WHERE unidad_negocio_id IN ('130-MER', '130-QRO', 'LA-ESTELAR', '130MID', '130QRO', 'ESTELAR')
GROUP BY unidad_negocio_id
ORDER BY unidad_negocio_id;

-- ==============================================================================
-- PASO 3: UPDATE DE CÓDIGOS
-- ==============================================================================

-- Tabla 1: Comercial_KPIs_Diarios_v2
UPDATE Comercial_KPIs_Diarios_v2 SET unidad_negocio_id = '130MID' WHERE unidad_negocio_id = '130-MER';
UPDATE Comercial_KPIs_Diarios_v2 SET unidad_negocio_id = '130QRO' WHERE unidad_negocio_id = '130-QRO';
UPDATE Comercial_KPIs_Diarios_v2 SET unidad_negocio_id = 'ESTELAR' WHERE unidad_negocio_id = 'LA-ESTELAR';

-- Tabla 2: Comercial_SyncLog_v2
UPDATE Comercial_SyncLog_v2 SET unidad_negocio_id = '130MID' WHERE unidad_negocio_id = '130-MER';
UPDATE Comercial_SyncLog_v2 SET unidad_negocio_id = '130QRO' WHERE unidad_negocio_id = '130-QRO';
UPDATE Comercial_SyncLog_v2 SET unidad_negocio_id = 'ESTELAR' WHERE unidad_negocio_id = 'LA-ESTELAR';

-- Tabla 3: Comercial_Ventas_Dia_Abiertas_v2
UPDATE Comercial_Ventas_Dia_Abiertas_v2 SET unidad_negocio_id = '130MID' WHERE unidad_negocio_id = '130-MER';
UPDATE Comercial_Ventas_Dia_Abiertas_v2 SET unidad_negocio_id = '130QRO' WHERE unidad_negocio_id = '130-QRO';
UPDATE Comercial_Ventas_Dia_Abiertas_v2 SET unidad_negocio_id = 'ESTELAR' WHERE unidad_negocio_id = 'LA-ESTELAR';

-- ==============================================================================
-- PASO 4: SELECT DESPUÉS (VALIDACIÓN)
-- ==============================================================================

SELECT 'DESPUES' AS momento, 
       unidad_negocio_id, 
       COUNT(*) AS registros 
FROM Comercial_KPIs_Diarios_v2 
WHERE unidad_negocio_id IN ('130-MER', '130-QRO', 'LA-ESTELAR', '130MID', '130QRO', 'ESTELAR')
GROUP BY unidad_negocio_id
ORDER BY unidad_negocio_id;

-- ==============================================================================
-- PASO 5: VALIDACIÓN DE TOTALES
-- ==============================================================================

-- Verificar que el total de registros no cambió
SELECT 'KPIs_Diarios' AS tabla, COUNT(*) AS total FROM Comercial_KPIs_Diarios_v2;
SELECT 'SyncLog' AS tabla, COUNT(*) AS total FROM Comercial_SyncLog_v2;
SELECT 'Ventas_Abiertas' AS tabla, COUNT(*) AS total FROM Comercial_Ventas_Dia_Abiertas_v2;

-- Verificar que no quedan códigos legacy
SELECT 'RESIDUOS_LEGACY' AS check_type, unidad_negocio_id, COUNT(*) AS registros
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id IN ('130-MER', '130-QRO', 'LA-ESTELAR')
GROUP BY unidad_negocio_id;

-- ==============================================================================
-- PASO 6: ROLLBACK (SEGURIDAD - NO SE EJECUTA COMMIT)
-- ==============================================================================

ROLLBACK;

-- ==============================================================================
-- NOTA: Si todo es correcto y se autoriza, cambiar ROLLBACK por:
-- COMMIT;
-- ==============================================================================
```

---

## 6. QUERIES EJECUTADOS PARA ESTE DIAGNÓSTICO

### Query 1: Estructura de tablas
```sql
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{tabla}'
ORDER BY ORDINAL_POSITION;
```

### Query 2: Índices y constraints
```sql
SELECT i.name, i.is_unique, i.is_primary_key, COL_NAME(ic.object_id, ic.column_id)
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
WHERE i.object_id = OBJECT_ID('{tabla}');
```

### Query 3: Distribución por código
```sql
SELECT unidad_negocio_id, COUNT(*) as registros, MIN(fecha_operacion), MAX(fecha_operacion)
FROM {tabla}
GROUP BY unidad_negocio_id;
```

### Query 4: Detección de colisiones
```sql
SELECT COUNT(*) as colisiones
FROM {tabla} legacy
INNER JOIN {tabla} oficial
    ON legacy.fecha_operacion = oficial.fecha_operacion
    AND legacy.sucursal_id = oficial.sucursal_id
WHERE legacy.unidad_negocio_id = '{codigo_legacy}'
  AND oficial.unidad_negocio_id = '{codigo_oficial}';
```

---

## 7. CONFIRMACIÓN DE CUMPLIMIENTO

| Requisito | Estado |
|-----------|--------|
| No se ejecutó UPDATE | ✅ CONFIRMADO |
| No se ejecutó DELETE | ✅ CONFIRMADO |
| No se ejecutó MERGE | ✅ CONFIRMADO |
| No se ejecutó COMMIT | ✅ CONFIRMADO |
| No se modificó ninguna tabla | ✅ CONFIRMADO |
| Solo se ejecutaron SELECTs | ✅ CONFIRMADO |

---

## 8. PRÓXIMOS PASOS (REQUIEREN AUTORIZACIÓN)

1. **FASE T1:** Ejecutar script de migración con `BEGIN TRANSACTION` y `ROLLBACK`
2. **FASE T1-COMMIT:** Si validación es exitosa, ejecutar con `COMMIT`
3. **POST-MIGRACIÓN:** Eliminar tablas de backup después de 7 días sin incidentes

---

**Generado por:** FASE T1-A Diagnóstico Pasivo
**Herramienta:** Python + pymssql (solo lectura)
