# REPORTE TÉCNICO: Corrección de Constraints de Unicidad
## EDARSA HUB - RH_Colaboradores_Expediente - Abril 2026

---

## A. DIAGNÓSTICO TÉCNICO

### Constraints/Índices Anteriores

| Nombre | Tipo | Columna | Filtro |
|--------|------|---------|--------|
| `UQ__RH_Colab__CAFFA85EB4841B85` | UNIQUE Constraint | RFC | (ninguno) |
| `UQ__RH_Colab__F46C4CBF0379E851` | UNIQUE Constraint | CURP | (ninguno) |

### Problema Identificado

Los constraints UNIQUE estándar en SQL Server tratan `NULL` como un valor único.
Esto significa que **solo se permite UN registro con RFC=NULL** y **UN registro con CURP=NULL**.

**Resultado**: 17 empleados sin RFC no podían insertarse porque ya existía 1 registro con RFC vacío.

---

## B. CORRECCIÓN APLICADA

### Script SQL Ejecutado

```sql
-- 1. Eliminar constraint UNIQUE sobre RFC
ALTER TABLE RH_Colaboradores_Expediente 
DROP CONSTRAINT UQ__RH_Colab__CAFFA85EB4841B85;

-- 2. Eliminar constraint UNIQUE sobre CURP
ALTER TABLE RH_Colaboradores_Expediente 
DROP CONSTRAINT UQ__RH_Colab__F46C4CBF0379E851;

-- 3. Crear índice único FILTRADO sobre RFC
CREATE UNIQUE NONCLUSTERED INDEX IX_RFC_Unique_NotNull
ON RH_Colaboradores_Expediente(RFC)
WHERE RFC IS NOT NULL AND RFC != '';

-- 4. Crear índice único FILTRADO sobre CURP
CREATE UNIQUE NONCLUSTERED INDEX IX_CURP_Unique_NotNull
ON RH_Colaboradores_Expediente(CURP)
WHERE CURP IS NOT NULL AND CURP != '';
```

### Índices Después de Corrección

| Nombre | Tipo | Columna | Filtro |
|--------|------|---------|--------|
| `IX_RFC_Unique_NotNull` | UNIQUE INDEX (Filtrado) | RFC | `RFC IS NOT NULL AND RFC != ''` |
| `IX_CURP_Unique_NotNull` | UNIQUE INDEX (Filtrado) | CURP | `CURP IS NOT NULL AND CURP != ''` |

### Por Qué Esta Solución Es Correcta

1. **Índices filtrados** excluyen NULLs y vacíos de la verificación de unicidad
2. **Permite múltiples NULLs**: Se pueden insertar muchos empleados sin RFC
3. **Mantiene unicidad estricta**: RFC duplicados ESTÁN PROHIBIDOS cuando RFC tiene valor
4. **Es la práctica estándar** en SQL Server para este tipo de regla de negocio
5. **No requiere datos falsos**: No necesitamos RFC genéricos como "XAXX..."

---

## C. RESULTADO DEL REPROCESAMIENTO

### Registros Observados

| Métrica | Cantidad |
|---------|----------|
| Total observados reprocesados | 17 |
| **Insertados exitosamente** | **17** |
| Duplicados por CURP | 0 |
| Errores | 0 |

### Detalle de Inserciones

| # | Nombre | CURP | Resultado | ID |
|---|--------|------|-----------|-----|
| 1 | JESSICA GRANILLO DUARTE | GADJ990323MDFRRS00 | INSERT | 456 |
| 2 | JORGE ALEJANDRO GONGORA CARDENAS | GOCJ040120HYNNRRA7 | INSERT | 457 |
| 3 | JORGE ALBERTO ARANDA PALOMO | AAPJ891106HYNRLR06 | INSERT | 458 |
| 4 | JESSICA DENISE RAMIREZ HERNANDEZ | RAHJ970204MJCMRS04 | INSERT | 459 |
| 5 | DANIEL DE ATOCHA MENDEZ AKE | MEAD000123HYNNKNA0 | INSERT | 460 |
| 6 | ERNESTO ALONSO CEJA REYES | CERE950814HDFJYR07 | INSERT | 461 |
| 7 | JESUS DAVID MOO MATOS | MOMJ020312HQRXTSA5 | INSERT | 462 |
| 8 | ANA ROSA GOMEZ SUASTE | GOSA860810MYNMSN01 | INSERT | 463 |
| 9 | FADUA ELIZABETH ANGELES SERRANO | AESF070302MVZNRDA9 | INSERT | 464 |
| 10 | JOSE ANTONIO HERNANDEZ GARCIA | HEGA040625HPLRRNA2 | INSERT | 465 |
| 11 | DAMIAN BARRERA CORTES | BACD050603HPLRRMA5 | INSERT | 466 |
| 12 | CHRISTIAN ALEJANDRO RIVERA MOLINA | RIMC820128HDFVLH05 | INSERT | 467 |
| 13 | JORGE ALEJANDRO HERNANDEZ GONZALEZ | HEGJ870919HASRNR14 | INSERT | 468 |
| 14 | DEBORAH VANESSA ESPINOSA GUTIERREZ | EIGD060716MMCSTBA2 | INSERT | 469 |
| 15 | VALENTE NATHAN LOPEZ CONTRERAS | LOCV020917HASPNLA2 | INSERT | 470 |
| 16 | JOSUE MARTINEZ LOPEZ | MALJ040608HQTRPSA7 | INSERT | 471 |
| 17 | SEBASTIAN ESAU LOPEZ MARTINEZ | LOMS060115HDFPRBA4 | INSERT | 472 |

---

## D. ESTADO FINAL

### RH_Colaboradores_Expediente

| Métrica | Cantidad |
|---------|----------|
| **Total colaboradores** | **454** |
| Con RFC informado | 437 |
| Sin RFC | 17 |
| Con CURP informada | 454 |
| Sin CURP | 0 |

### RH_Importacion_Staging (MPro_CENTRAL2020)

| Estado | Cantidad |
|--------|----------|
| Procesado | 466 |
| Pendiente (incompletos) | 10 |
| **Total** | **476** |

---

## E. REGLA DE NEGOCIO IMPLEMENTADA

```
✅ RFC debe ser único cuando esté informado (no vacío, no NULL)
✅ CURP debe ser única cuando esté informada (no vacía, no NULL)
✅ RFC no es obligatorio por ahora
✅ CURP no es obligatoria por ahora
✅ Se permiten múltiples registros sin RFC
✅ Se permiten múltiples registros sin CURP
❌ NO se permiten RFC duplicados cuando RFC tiene valor
❌ NO se permiten CURP duplicadas cuando CURP tiene valor
```

---

## F. VALIDACIONES BACKEND

El servicio `aprobacion_service.py` ya implementa las validaciones correctas:

```python
# Verificar duplicado SOLO si CURP está informada
if curp and curp.strip():
    cursor.execute(f"SELECT ColaboradorID FROM ... WHERE CURP = '{curp}'")
    
# Verificar duplicado SOLO si RFC está informado
if rfc and rfc.strip():
    cursor.execute(f"SELECT ColaboradorID FROM ... WHERE RFC = '{rfc}'")
```

No se requirieron cambios en el backend.

---

*Reporte generado: 2026-04-12*
*Corrección: Índices únicos filtrados*
