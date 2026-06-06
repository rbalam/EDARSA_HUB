# FASE: Estandarización de Nombres de Unidades de Negocio

**Fecha**: 2026-05-15  
**Estado**: DIAGNÓSTICO COMPLETADO (Sin ejecución de DML)  
**Rol**: Arquitecto Senior EDARSAHUB / DBA SQL Server

---

## 1. Resumen Ejecutivo

### Hallazgos principales:

1. **`Sistema_Empresas`**: Contiene las 5 unidades canónicas correctamente definidas ✅
2. **`Unidades_Negocio`**: Tiene las 5 unidades con códigos consistentes ✅
3. **`Sistema_EmpresasMongoMap`**: Mapeo MongoDB correcto ✅
4. **PROBLEMA DETECTADO**: `Comercial_Ventas_Dia_Abiertas_v2` contiene **registros duplicados con aliases legacy**:
   - `130-MER` (legacy) vs `130MID` (canónico)
   - `130-QRO` (legacy) vs `130QRO` (canónico)
   - `LA-ESTELAR` (legacy) vs `ESTELAR` (canónico)

### Conclusión:
El catálogo de empresas (`Sistema_Empresas`) está CORRECTO. El problema son los **aliases legacy** en las tablas de datos operativos que deben resolverse mediante un `EmpresaAliasResolver`.

---

## 2. Estado Actual de Sistema_Empresas

### Estructura:

| Columna | Tipo | Nullable |
|---------|------|----------|
| EmpresaID | int | NOT NULL |
| CodigoEmpresa | varchar | NOT NULL |
| NombreEmpresa | nvarchar | NOT NULL |
| NombreComercial | nvarchar | NULL |
| RFC | varchar | NULL |
| Activo | bit | NOT NULL |
| FechaAlta | datetime2 | NOT NULL |
| FechaModificacion | datetime2 | NULL |

### Registros actuales:

| EmpresaID | CodigoEmpresa | NombreEmpresa | NombreComercial | Activo |
|-----------|---------------|---------------|-----------------|--------|
| 1 | ORIGEN | ORIGEN | Restaurante Origen S.A. de C.V. | ✅ SI |
| 2 | 130QRO | 130 QRO | 130 Grados Querétaro S.A. de C.V. | ✅ SI |
| 3 | CIENFUEGOS | CIENFUEGOS | Restaurante Cienfuegos S.A. de C.V. | ✅ SI |
| 4 | ESTELAR | LA ESTELAR | La Estelar S.A. de C.V. | ✅ SI |
| 5 | 130MID | 130 MID | 130 Grados Mérida S.A. de C.V. | ✅ SI |

---

## 3. Registros Encontrados en Tablas Relacionadas

### Unidades_Negocio:

| codigo | nombre | system_type | activo | orden |
|--------|--------|-------------|--------|-------|
| 130MID | 130° MERIDA | SoftRestaurant | SI | 1 |
| CIENFUEGOS | CIENFUEGOS | SoftRestaurant | SI | 2 |
| ESTELAR | LA ESTELAR | SoftRestaurant | SI | 3 |
| 130QRO | 130° QUERETARO | MPRO | SI | 4 |
| ORIGEN | ORIGEN | MPRO | SI | 5 |

### Comercial_Ventas_Dia_Abiertas_v2 (Aliases en uso):

| unidad_negocio_id | unidad_negocio_nombre | sistema_origen | Tipo |
|-------------------|----------------------|----------------|------|
| 130MID | 130° MERIDA | SOFTRESTAURANT | Canónico ✅ |
| **130-MER** | 130° MÉRIDA | SOFTRESTAURANT | **Legacy ⚠️** |
| 130QRO | 130° QUERETARO | MPRO | Canónico ✅ |
| **130-QRO** | 130° QUERETARO | MPRO | **Legacy ⚠️** |
| CIENFUEGOS | CIENFUEGOS | SOFTRESTAURANT | Canónico ✅ |
| ESTELAR | LA ESTELAR | SOFTRESTAURANT | Canónico ✅ |
| **LA-ESTELAR** | LA ESTELAR | SOFTRESTAURANT | **Legacy ⚠️** |
| ORIGEN | ORIGEN | MPRO | Canónico ✅ |

---

## 4. Duplicados o Inconsistencias Detectadas

### CRÍTICO - Registros duplicados por aliases legacy:

| Alias Legacy | Código Canónico | Tabla Afectada |
|-------------|-----------------|----------------|
| `130-MER` | `130MID` | Comercial_Ventas_Dia_Abiertas_v2 |
| `130-QRO` | `130QRO` | Comercial_Ventas_Dia_Abiertas_v2 |
| `LA-ESTELAR` | `ESTELAR` | Comercial_Ventas_Dia_Abiertas_v2 |

### Inconsistencias de nombres:

| Tabla | Nombre actual | Nombre esperado |
|-------|--------------|-----------------|
| Unidades_Negocio | 130° MERIDA | 130 Grados Mérida |
| Unidades_Negocio | 130° QUERETARO | 130 Grados Querétaro |
| Sistema_Empresas | 130 QRO (NombreEmpresa) | 130QRO |
| Sistema_Empresas | 130 MID (NombreEmpresa) | 130MID |

---

## 5. Unidades Canónicas Propuestas

| # | CodigoEmpresa | NombreComercial | Sistema |
|---|---------------|-----------------|---------|
| 1 | ORIGEN | Origen | MPRO |
| 2 | 130QRO | 130 Grados Querétaro | MPRO |
| 3 | 130MID | 130 Grados Mérida | SoftRestaurant |
| 4 | CIENFUEGOS | Cienfuegos | SoftRestaurant |
| 5 | ESTELAR | La Estelar | SoftRestaurant |

---

## 6. Nombres Oficiales Propuestos

### Reglas aplicadas:
- CodigoEmpresa: MAYÚSCULAS, sin espacios, sin acentos, sin °
- NombreComercial: Nombre visible oficial con acentos permitidos

| CodigoEmpresa | NombreEmpresa | NombreComercial |
|---------------|---------------|-----------------|
| ORIGEN | Origen | Origen |
| 130QRO | 130 Grados Querétaro | 130 Grados Querétaro |
| 130MID | 130 Grados Mérida | 130 Grados Mérida |
| CIENFUEGOS | Cienfuegos | Cienfuegos |
| ESTELAR | La Estelar | La Estelar |

---

## 7. Script SQL Propuesto (NO EJECUTADO)

```sql
-- =============================================================================
-- SCRIPT DE ESTANDARIZACIÓN DE NOMBRES - Sistema_Empresas
-- FECHA: 2026-05-15
-- ESTADO: PROPUESTO, NO EJECUTADO
-- REQUIERE: Autorización explícita antes de ejecutar
-- =============================================================================

-- PASO 1: BACKUP PREVIO (OBLIGATORIO)
SELECT * INTO Sistema_Empresas_BACKUP_20260515 FROM Sistema_Empresas;

-- PASO 2: SELECT PREVIO - Ver estado actual
SELECT EmpresaID, CodigoEmpresa, NombreEmpresa, NombreComercial, Activo
FROM Sistema_Empresas
ORDER BY EmpresaID;

-- PASO 3: UPDATES PROPUESTOS
-- Nota: Solo actualiza NombreEmpresa para consistencia con NombreComercial

-- ORIGEN (EmpresaID=1): Sin cambios necesarios ✅

-- 130QRO (EmpresaID=2): Actualizar NombreEmpresa
UPDATE Sistema_Empresas 
SET NombreEmpresa = '130 Grados Querétaro',
    NombreComercial = '130 Grados Querétaro',
    FechaModificacion = GETDATE(),
    UpdatedBy = 'ESTANDARIZACION_FASE1'
WHERE EmpresaID = 2 AND CodigoEmpresa = '130QRO';

-- CIENFUEGOS (EmpresaID=3): Actualizar NombreComercial
UPDATE Sistema_Empresas 
SET NombreEmpresa = 'Cienfuegos',
    NombreComercial = 'Cienfuegos',
    FechaModificacion = GETDATE(),
    UpdatedBy = 'ESTANDARIZACION_FASE1'
WHERE EmpresaID = 3 AND CodigoEmpresa = 'CIENFUEGOS';

-- ESTELAR (EmpresaID=4): Sin cambios necesarios ✅

-- 130MID (EmpresaID=5): Actualizar NombreEmpresa
UPDATE Sistema_Empresas 
SET NombreEmpresa = '130 Grados Mérida',
    NombreComercial = '130 Grados Mérida',
    FechaModificacion = GETDATE(),
    UpdatedBy = 'ESTANDARIZACION_FASE1'
WHERE EmpresaID = 5 AND CodigoEmpresa = '130MID';

-- PASO 4: SELECT FINAL - Verificar cambios
SELECT EmpresaID, CodigoEmpresa, NombreEmpresa, NombreComercial, Activo
FROM Sistema_Empresas
ORDER BY EmpresaID;

-- PASO 5: VALIDACIÓN DE DUPLICADOS
SELECT CodigoEmpresa, COUNT(*) as Total
FROM Sistema_Empresas
WHERE Activo = 1
GROUP BY CodigoEmpresa
HAVING COUNT(*) > 1;
-- Resultado esperado: 0 filas (sin duplicados)

-- =============================================================================
-- ROLLBACK (Si es necesario)
-- =============================================================================
-- DROP TABLE Sistema_Empresas;
-- SELECT * INTO Sistema_Empresas FROM Sistema_Empresas_BACKUP_20260515;
```

---

## 8. Aliases Legacy Propuestos

### Tabla propuesta: `Sistema_EmpresaAliases`

```sql
-- ESTRUCTURA PROPUESTA (NO CREAR SIN AUTORIZACIÓN)
CREATE TABLE Sistema_EmpresaAliases (
    AliasID INT IDENTITY(1,1) PRIMARY KEY,
    EmpresaID INT NOT NULL FOREIGN KEY REFERENCES Sistema_Empresas(EmpresaID),
    AliasNormalizado NVARCHAR(100) NOT NULL, -- Alias en formato normalizado (MAYUSCULAS, sin acentos)
    AliasOriginal NVARCHAR(100) NOT NULL,    -- Alias tal como aparece en fuentes legacy
    OrigenAlias NVARCHAR(50),                -- De dónde vino: 'MONGO', 'SOFTRESTAURANT', 'MPRO', 'MANUAL'
    Activo BIT DEFAULT 1,
    FechaCreacion DATETIME2 DEFAULT GETDATE()
);

CREATE UNIQUE INDEX IX_EmpresaAliases_Normalizado ON Sistema_EmpresaAliases(AliasNormalizado) WHERE Activo = 1;
```

### Aliases propuestos por unidad:

| EmpresaID | CodigoEmpresa | AliasNormalizado | AliasOriginal |
|-----------|---------------|------------------|---------------|
| 1 | ORIGEN | ORIGEN | ORIGEN |
| 1 | ORIGEN | ORIGEN | Origen |
| 1 | ORIGEN | ORIGEN | origen |
| 2 | 130QRO | 130QRO | 130QRO |
| 2 | 130QRO | 130 QRO | 130 QRO |
| 2 | 130QRO | 130 QUERETARO | 130° QUERETARO |
| 2 | 130QRO | 130-QRO | 130-QRO |
| 2 | 130QRO | QRO | QRO |
| 2 | 130QRO | QUERETARO | Querétaro |
| 2 | 130QRO | 130 GRADOS QUERETARO | 130 Grados Querétaro |
| 3 | CIENFUEGOS | CIENFUEGOS | CIENFUEGOS |
| 3 | CIENFUEGOS | CIENFUEGOS | Cienfuegos |
| 3 | CIENFUEGOS | CF | CF |
| 4 | ESTELAR | ESTELAR | ESTELAR |
| 4 | ESTELAR | LA ESTELAR | LA ESTELAR |
| 4 | ESTELAR | LA ESTELAR | La Estelar |
| 4 | ESTELAR | LA-ESTELAR | LA-ESTELAR |
| 5 | 130MID | 130MID | 130MID |
| 5 | 130MID | 130 MID | 130 MID |
| 5 | 130MID | 130 MERIDA | 130° MÉRIDA |
| 5 | 130MID | 130-MER | 130-MER |
| 5 | 130MID | 130 GRADOS MERIDA | 130 Grados Mérida |

---

## 9. Reglas de Normalización

### Función propuesta: `fn_NormalizarNombreEmpresa`

```sql
-- FUNCIÓN PROPUESTA (NO CREAR SIN AUTORIZACIÓN)
CREATE FUNCTION dbo.fn_NormalizarNombreEmpresa(@Nombre NVARCHAR(200))
RETURNS NVARCHAR(200)
AS
BEGIN
    DECLARE @Resultado NVARCHAR(200) = @Nombre;
    
    -- 1. Convertir a mayúsculas
    SET @Resultado = UPPER(@Resultado);
    
    -- 2. Quitar acentos
    SET @Resultado = REPLACE(@Resultado, 'Á', 'A');
    SET @Resultado = REPLACE(@Resultado, 'É', 'E');
    SET @Resultado = REPLACE(@Resultado, 'Í', 'I');
    SET @Resultado = REPLACE(@Resultado, 'Ó', 'O');
    SET @Resultado = REPLACE(@Resultado, 'Ú', 'U');
    SET @Resultado = REPLACE(@Resultado, 'Ñ', 'N');
    
    -- 3. Reemplazar "_" por espacio
    SET @Resultado = REPLACE(@Resultado, '_', ' ');
    
    -- 4. Quitar símbolo °
    SET @Resultado = REPLACE(@Resultado, '°', '');
    
    -- 5. Quitar caracteres especiales comunes
    SET @Resultado = REPLACE(@Resultado, '-', ' ');
    SET @Resultado = REPLACE(@Resultado, '.', '');
    SET @Resultado = REPLACE(@Resultado, ',', '');
    
    -- 6. Normalizar espacios dobles
    WHILE CHARINDEX('  ', @Resultado) > 0
        SET @Resultado = REPLACE(@Resultado, '  ', ' ');
    
    -- 7. Trim
    SET @Resultado = LTRIM(RTRIM(@Resultado));
    
    RETURN @Resultado;
END;
```

### Ejemplos de normalización:

| Entrada | Salida Normalizada |
|---------|-------------------|
| 130 Grados Mérida | 130 GRADOS MERIDA |
| 130° MÉRIDA | 130 MERIDA |
| 130_mid | 130 MID |
| Querétaro | QUERETARO |
| LA-ESTELAR | LA ESTELAR |
| 130-QRO | 130 QRO |

---

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Romper joins existentes | Alto | Usar alias resolver, no cambiar códigos |
| Duplicados en datos operativos | Medio | Limpiar gradualmente con merge |
| Inconsistencia temporal | Bajo | Ejecutar en ventana de mantenimiento |
| Rollback fallido | Medio | Mantener backup por 30 días |

---

## 11. Decisiones Pendientes

1. **¿Crear tabla Sistema_EmpresaAliases?**
   - Propuesta lista, esperando autorización

2. **¿Actualizar NombreEmpresa en Sistema_Empresas?**
   - Script listo, esperando autorización

3. **¿Limpiar registros legacy en Comercial_Ventas_Dia_Abiertas_v2?**
   - Requiere análisis de impacto adicional

4. **¿Implementar EmpresaAliasResolver en backend?**
   - Propuesta técnica disponible, esperando autorización

---

## 12. Confirmaciones

| Confirmación | Estado |
|-------------|--------|
| No se modificó código | ✅ Confirmado |
| No se modificó frontend | ✅ Confirmado |
| No se modificaron jobs | ✅ Confirmado |
| No se ejecutó DML | ✅ Confirmado |
| No se reactivó LIVE | ✅ Confirmado |
| EDARSAHUB SQL sigue siendo fuente autoritativa | ✅ Confirmado |
| Solo diagnóstico pasivo | ✅ Confirmado |

---

## Resumen Final

### Estado de cada unidad:

| CodigoEmpresa | En Sistema_Empresas | En Unidades_Negocio | Aliases Legacy |
|---------------|---------------------|---------------------|----------------|
| ORIGEN | ✅ EmpresaID=1 | ✅ | Ninguno |
| 130QRO | ✅ EmpresaID=2 | ✅ | 130-QRO |
| CIENFUEGOS | ✅ EmpresaID=3 | ✅ | Ninguno |
| ESTELAR | ✅ EmpresaID=4 | ✅ | LA-ESTELAR |
| 130MID | ✅ EmpresaID=5 | ✅ | 130-MER |

### Acciones recomendadas:

1. **FASE 1A**: Aprobar y ejecutar UPDATE en Sistema_Empresas (NombreEmpresa, NombreComercial)
2. **FASE 1B**: Crear tabla Sistema_EmpresaAliases
3. **FASE 1C**: Cargar aliases en Sistema_EmpresaAliases
4. **FASE 2**: Implementar EmpresaAliasResolver en backend
5. **FASE 3**: Limpiar registros legacy gradualmente

**ESPERANDO AUTORIZACIÓN PARA EJECUTAR FASE 1A**
