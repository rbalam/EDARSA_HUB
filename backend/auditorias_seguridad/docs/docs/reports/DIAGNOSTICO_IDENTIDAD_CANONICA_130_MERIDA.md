# DIAGNÓSTICO: IDENTIDAD CANÓNICA 130° MÉRIDA

**Fecha**: 2026-05-16  
**Autor**: Arquitecto Senior EDARSAHUB  
**Estado**: FASE 1 COMPLETADA - DIAGNÓSTICO SIN MODIFICAR DATOS  
**Prioridad**: P0 - CRÍTICO

---

## 1. PROBLEMA DETECTADO

Se identificó **duplicidad lógica grave** en la unidad 130° MÉRIDA dentro de `Comercial_KPIs_Diarios_v2`:

| unidad_negocio_id | Registros | Ventas Totales | Meses | Observación |
|-------------------|-----------|----------------|-------|-------------|
| `130MID` | 740 | $117,454,886 | 25 | **CÓDIGO CANÓNICO CORRECTO** |
| `130-MER` | 3 | $409,877 | 1 | **ALIAS LEGACY - INCORRECTO** |

### Impacto:
- Ventas acumuladas fragmentadas
- Proyección mensual incorrecta (divide entre datos incompletos)
- Comparativos vs mes anterior/año anterior erróneos
- Filtros por unidad muestran datos parciales
- Jobs de sincronización escriben con identidades inconsistentes

---

## 2. CAUSA RAÍZ IDENTIFICADA

### 2.1 Código Culpable: `_mapear_codigo_a_unidad_negocio_id()`

**Archivo**: `/app/backend/modules/comercial/service.py`  
**Líneas**: 292-350

```python
# LÍNEA 339 - PROBLEMA CRÍTICO
fallback_map = {
    '130MID': '130-MER',  # <-- TRADUCE CANÓNICO A LEGACY
    'CIENFUEGOS': 'CIENFUEGOS',
    'ESTELAR': 'LA-ESTELAR',
    '130QRO': '130-QRO',
    'ORIGEN': 'ORIGEN'
}
```

Esta función:
1. Recibe el código canónico `130MID` desde `Unidades_Negocio`
2. Lo traduce a `130-MER` (alias legacy)
3. Las consultas a `Comercial_KPIs_Diarios_v2` usan `130-MER`
4. **NO encuentra los 740 registros que tienen `130MID`**
5. El dashboard muestra datos incorrectos o incompletos

### 2.2 Código Culpable: `UNIDADES_EDARSAHUB_MAP`

**Archivo**: `/app/backend/modules/comercial/service.py`  
**Líneas**: 983-996

```python
UNIDADES_EDARSAHUB_MAP = {
    "a5547321-1139-4d2b-9d53-182ca737b6b6": {
        "unidad_negocio_id": "130-MER",  # <-- INCORRECTO, DEBE SER "130MID"
        "nombre": "130° MÉRIDA",
        "sucursal_id": "DEFAULT",
        "sistema": "SoftRestaurant"
    },
    # ...
}
```

---

## 3. FUENTE DE VERDAD (CATÁLOGOS MAESTROS)

### 3.1 Tabla `Unidades_Negocio`:
| Campo | Valor |
|-------|-------|
| id | `19e076fb-c6de-4ea5-84ab-1caa9e86082c` |
| codigo | `130MID` |
| nombre | `130° MERIDA` |
| server_id | `a5547321-1139-4d2b-9d53-182ca737b6b6` |
| activo | `True` |

### 3.2 Tabla `Sistema_Empresas`:
| Campo | Valor |
|-------|-------|
| EmpresaID | `5` |
| CodigoEmpresa | `130MID` |
| NombreComercial | `130 Grados Mérida S.A. de C.V.` |

### 3.3 Tabla `Sistema_EmpresasAlias` (EmpresaID=5):
| Alias | Origen | Activo |
|-------|--------|--------|
| `130MID` | CANONICO | True |
| `130-MER` | LEGACY | True |
| `130 MERIDA` | LEGACY | True |

### 3.4 Tabla `Servidores_Conexiones`:
| Campo | Valor |
|-------|-------|
| id | `a5547321-1139-4d2b-9d53-182ca737b6b6` |
| nombre | `130° MERIDA` |
| system_type | `SoftRestaurant` |

---

## 4. UNIDAD CANÓNICA DEFINITIVA

| Campo | Valor Canónico |
|-------|----------------|
| **unidad_negocio_id** | `130MID` |
| **unidad_negocio_nombre** | `130° MERIDA` |
| **server_id** | `a5547321-1139-4d2b-9d53-182ca737b6b6` |
| **empresa_id** | `5` |
| **sucursal_id** | `DEFAULT` |
| **sistema_origen** | `SoftRestaurant` |

### Aliases que deben resolver a `130MID`:
- `130MID` (canónico)
- `130-MER` (legacy)
- `130-MID`
- `130MER`
- `130° MERIDA`
- `130° MÉRIDA`
- `MERIDA`
- `MÉRIDA`

---

## 5. ARCHIVOS AFECTADOS QUE REQUIEREN CORRECCIÓN

| Archivo | Línea | Tipo de Corrección |
|---------|-------|-------------------|
| `/app/backend/modules/comercial/service.py` | 339 | Eliminar traducción `130MID` -> `130-MER` |
| `/app/backend/modules/comercial/service.py` | 985 | Cambiar `"130-MER"` a `"130MID"` en UNIDADES_EDARSAHUB_MAP |
| `/app/backend/modules/comercial/service.py` | 991 | Cambiar `"130-QRO"` a `"130QRO"` en UNIDADES_EDARSAHUB_MAP |

---

## 6. PLAN DE CORRECCIÓN (REQUIERE AUTORIZACIÓN)

### FASE 3: Corregir Código (SIN tocar datos históricos)
1. Modificar `_mapear_codigo_a_unidad_negocio_id()` para que **NO traduzca** códigos canónicos
2. Actualizar `UNIDADES_EDARSAHUB_MAP` con códigos canónicos
3. Validar que el Tablero Ejecutivo y Comercial Dashboard lean `130MID`

### FASE 4: Normalizar Datos Históricos (REQUIERE AUTORIZACIÓN EXPLÍCITA)
Script de auditoría previo:
```sql
-- SOLO DIAGNÓSTICO, NO EJECUTAR UPDATE
SELECT 
    'Comercial_KPIs_Diarios_v2' as tabla,
    unidad_negocio_id as unidad_actual,
    '130MID' as unidad_destino,
    COUNT(*) as registros_afectados,
    SUM(ventas_total) as ventas_afectadas,
    MIN(fecha_operacion) as fecha_min,
    MAX(fecha_operacion) as fecha_max
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id = '130-MER'
GROUP BY unidad_negocio_id
```

### FASE 5: Validación Post-Fix
- Confirmar que `130MID` tiene 743+ registros (740 originales + 3 normalizados)
- Confirmar que `130-MER` tiene 0 registros
- Validar proyección mensual correcta

---

## 7. RIESGOS DE LA NORMALIZACIÓN

| Riesgo | Mitigación |
|--------|------------|
| Colisión de unique key al hacer UPDATE | Verificar que no existan registros duplicados para misma fecha antes de UPDATE |
| Doble conteo de ventas | Los 3 registros de `130-MER` son fechas diferentes a los 740 de `130MID` |
| Ruptura de filtros | Todas las consultas deben usar código canónico, no alias |

---

## 8. DECISIÓN REQUERIDA

**ANTES DE PROCEDER CON CORRECCIONES:**

1. ¿Autoriza corregir el código backend (FASE 3)?
2. ¿Autoriza normalizar los 3 registros históricos de `130-MER` a `130MID` (FASE 4)?
3. ¿Desea que se aplique la misma corrección para `130-QRO` -> `130QRO`?

---

## 9. ANEXO: QUERIES DE VALIDACIÓN

### Query 1: Verificar duplicidad actual
```sql
SELECT unidad_negocio_id, COUNT(*), SUM(ventas_total)
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id IN ('130MID', '130-MER', '130-MID', '130MER')
GROUP BY unidad_negocio_id
```

### Query 2: Verificar colisiones potenciales
```sql
SELECT fecha_operacion, COUNT(*)
FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id IN ('130MID', '130-MER')
GROUP BY fecha_operacion
HAVING COUNT(*) > 1
```

---

**Estado del Documento**: PENDIENTE AUTORIZACIÓN  
**Próxima Acción**: Esperar confirmación del usuario para proceder con FASE 3 (código) y FASE 4 (datos)
