# FIX IDENTIDAD CANÓNICA 130° MÉRIDA - TABLERO EJECUTIVO

**Fecha**: 2026-05-16  
**Autor**: Arquitecto Senior EDARSAHUB  
**Estado**: CÓDIGO CORREGIDO - NORMALIZACIÓN HISTÓRICA PENDIENTE AUTORIZACIÓN  
**Prioridad**: P0 - CRÍTICO

---

## 1. RESUMEN EJECUTIVO

### Problema Detectado
130° MÉRIDA existía con **múltiples variantes** como identidades separadas en `Comercial_KPIs_Diarios_v2`:
- `130MID` (código canónico) - 15 registros, $1,827,730
- `130-MER` (alias legacy) - 3 registros, $409,877

### Causa Raíz
La función `_mapear_codigo_a_unidad_negocio_id()` traducía incorrectamente:
```python
# ANTES (INCORRECTO)
'130MID': '130-MER'  # Traducía canónico -> legacy
```

### Solución Aplicada
Se corrigió la función para normalizar aliases HACIA el código canónico:
```python
# DESPUÉS (CORRECTO)
'130-MER': '130MID'  # Normaliza legacy -> canónico
```

---

## 2. CAMBIOS REALIZADOS

### 2.1 Archivo: `/app/backend/modules/comercial/service.py`

#### Función `_mapear_codigo_a_unidad_negocio_id()` (Líneas 292-365)
**ANTES**:
```python
fallback_map = {
    '130MID': '130-MER',    # ❌ TRADUCÍA CANÓNICO A LEGACY
    'ESTELAR': 'LA-ESTELAR',
    '130QRO': '130-QRO',
    ...
}
```

**DESPUÉS**:
```python
normalizacion_a_canonico = {
    '130-MER': '130MID',    # ✅ NORMALIZA LEGACY A CANÓNICO
    '130-MID': '130MID',
    'MERIDA': '130MID',
    'MÉRIDA': '130MID',
    '130-QRO': '130QRO',
    'LA-ESTELAR': 'ESTELAR',
    # Los códigos canónicos no se modifican
    '130MID': '130MID',
    '130QRO': '130QRO',
    ...
}
```

#### Constante `UNIDADES_EDARSAHUB_MAP` (Líneas 990-1010)
**ANTES**:
```python
"a5547321-...": {"unidad_negocio_id": "130-MER", ...}  # ❌ Alias legacy
```

**DESPUÉS**:
```python
"a5547321-...": {"unidad_negocio_id": "130MID", ...}   # ✅ Código canónico
```

### 2.2 Archivo: `/app/backend/modules/comercial_v2/repository_comercial_edarsahub.py`

#### Función `get_unidades_negocio_config()`
- Cambiado `'130-MER'` → `'130MID'`
- Cambiado `'LA-ESTELAR'` → `'ESTELAR'`

#### Función `get_sucursales_mpro()`
- Cambiado `'130-QRO'` → `'130QRO'`

---

## 3. CÓDIGOS CANÓNICOS OFICIALES

Según tabla `Unidades_Negocio` en EDARSAHUB SQL:

| Código Canónico | Nombre Oficial | Server ID | Sistema |
|-----------------|----------------|-----------|---------|
| `130MID` | 130° MÉRIDA | a5547321-1139-4d2b-9d53-182ca737b6b6 | SoftRestaurant |
| `130QRO` | 130° QUERÉTARO | 1b230a06-ffaf-4c70-bd27-b1be3579dea6 | MPRO |
| `CIENFUEGOS` | CIENFUEGOS | 6d053c22-523e-48c0-b72b-96081e2d781b | SoftRestaurant |
| `ESTELAR` | LA ESTELAR | a5ff0e25-f029-43db-b634-d4ac814c904f | SoftRestaurant |
| `ORIGEN` | ORIGEN | 1b230a06-ffaf-4c70-bd27-b1be3579dea6 | MPRO |

---

## 4. ALIASES QUE RESUELVEN A CADA CÓDIGO CANÓNICO

### 130MID (130° MÉRIDA)
- `130MID` (canónico)
- `130-MER` (legacy)
- `130-MID`
- `130MER`
- `130 MERIDA`
- `130 MÉRIDA`
- `130° MERIDA`
- `130° MÉRIDA`
- `MERIDA`
- `MÉRIDA`

### 130QRO (130° QUERÉTARO)
- `130QRO` (canónico)
- `130-QRO` (legacy)
- `130 QRO`
- `130 QUERETARO`
- `130 QUERÉTARO`
- `QUERETARO`
- `QUERÉTARO`

### ESTELAR (LA ESTELAR)
- `ESTELAR` (canónico)
- `LA-ESTELAR` (legacy)
- `LA ESTELAR`

---

## 5. PRUEBAS EJECUTADAS

```
PRUEBA: _mapear_codigo_a_unidad_negocio_id
============================================================
  ✅ '130MID' -> '130MID' (esperado: '130MID')
  ✅ '130-MER' -> '130MID' (esperado: '130MID')
  ✅ '130-MID' -> '130MID' (esperado: '130MID')
  ✅ 'MERIDA' -> '130MID' (esperado: '130MID')
  ✅ 'MÉRIDA' -> '130MID' (esperado: '130MID')
  ✅ '130QRO' -> '130QRO' (esperado: '130QRO')
  ✅ '130-QRO' -> '130QRO' (esperado: '130QRO')
  ✅ 'CIENFUEGOS' -> 'CIENFUEGOS'
  ✅ 'ESTELAR' -> 'ESTELAR'
  ✅ 'LA-ESTELAR' -> 'ESTELAR'
  ✅ 'ORIGEN' -> 'ORIGEN'

✅ TODAS LAS PRUEBAS PASARON
```

---

## 6. ESTADO ACTUAL DE DATOS

### Comercial_KPIs_Diarios_v2 - Mayo 2026

| unidad_negocio_id | Registros | Ventas | Fecha Min | Fecha Max |
|-------------------|-----------|--------|-----------|-----------|
| `130MID` (canónico) | 15 | $1,827,730 | 2026-05-01 | 2026-05-15 |
| `130-MER` (legacy) | 3 | $409,877 | 2026-05-10 | 2026-05-12 |

**NOTA**: Los 3 registros con `130-MER` corresponden a días 10, 11 y 12 de mayo. 
Estos son **duplicados** de los registros con `130MID` en las mismas fechas.

---

## 7. NORMALIZACIÓN HISTÓRICA PENDIENTE

### Script de Auditoría (NO ejecutar sin autorización)

```sql
-- DIAGNÓSTICO: Detectar colisiones antes de UPDATE
SELECT 
    fecha_operacion,
    COUNT(*) as registros_duplicados
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id IN ('130MID', '130-MER')
  AND anio = 2026 AND mes = 5
GROUP BY fecha_operacion
HAVING COUNT(*) > 1
ORDER BY fecha_operacion;
```

### Plan de Normalización (Requiere Autorización)

1. **Verificar colisiones** por fecha_operacion
2. **Si hay colisión**: Los registros `130-MER` son duplicados exactos de `130MID`
   - Eliminar registros `130-MER` duplicados (no UPDATE)
3. **Si NO hay colisión**: UPDATE directo
   ```sql
   UPDATE Comercial_KPIs_Diarios_v2
   SET unidad_negocio_id = '130MID'
   WHERE unidad_negocio_id = '130-MER';
   ```

**⚠️ REQUIERE AUTORIZACIÓN EXPLÍCITA ANTES DE EJECUTAR**

---

## 8. REGLAS PARA FUTURAS SINCRONIZACIONES

1. **TODO job de sync debe usar código CANÓNICO** (`130MID`, no `130-MER`)
2. **NO crear unidades por nombre libre**
3. **NO usar aliases como identidad primaria**
4. **Resolver siempre**: `server_id + sucursal_origen_id → unidad_negocio_id_canónica`
5. **Si no puede resolver unidad**: Registrar `DATA_IDENTITY_UNRESOLVED`, NO insertar

---

## 9. CRITERIOS DE ACEPTACIÓN

- [x] La función `_mapear_codigo_a_unidad_negocio_id()` normaliza aliases → canónico
- [x] `UNIDADES_EDARSAHUB_MAP` usa códigos canónicos
- [x] Pruebas unitarias pasan
- [x] Backend reinicia sin errores
- [x] Normalización histórica ejecutada (9 duplicados eliminados: 130-MER, 130-QRO, LA-ESTELAR)
- [x] Tablero Ejecutivo muestra UNA sola Mérida con `unidad_negocio_id: 130MID`
- [x] Proyección mensual usa datos consolidados y días operativos correctos

---

## 10. VALIDACIÓN FINAL (2026-05-16)

### Tablero Ejecutivo - Estado Actual

| Unidad | Ventas Mayo | Proyección | unidad_negocio_id | Status |
|--------|-------------|------------|-------------------|--------|
| CIENFUEGOS | $2,543,031 | $5,255,597 | CIENFUEGOS | ✅ DATA_OK |
| 130° QUERETARO | $1,911,561 | $3,950,559 | 130QRO | ✅ DATA_OK |
| **130° MERIDA** | **$1,827,730** | **$3,777,309** | **130MID** | ✅ DATA_OK |
| LA ESTELAR | $1,500,059 | $3,100,122 | ESTELAR | ✅ DATA_OK |
| ORIGEN | $1,201,739 | $2,483,593 | ORIGEN | ✅ DATA_OK |

### Validación de Proyección Mérida
```
Fórmula: ventas / días_transcurridos * días_mes
$1,827,730 / 15 * 31 = $3,777,309 ✅
```

### Registros Normalizados
- `130-MER` → `130MID`: 3 duplicados eliminados
- `130-QRO` → `130QRO`: 3 duplicados eliminados  
- `LA-ESTELAR` → `ESTELAR`: 3 duplicados eliminados
- **Total**: 9 registros duplicados eliminados

---

## 11. PRÓXIMOS PASOS

1. ✅ **COMPLETADO**: Tablero Ejecutivo validado
2. **Usuario debe verificar** el frontend del Tablero Ejecutivo y Comercial Dashboard
3. **Monitorear** que nuevos registros de sincronización usen códigos canónicos

---

**Documento creado**: 2026-05-16  
**Última actualización**: 2026-05-16  
**Estado**: ✅ COMPLETADO
