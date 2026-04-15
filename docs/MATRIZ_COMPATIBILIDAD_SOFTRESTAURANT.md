# MATRIZ DE COMPATIBILIDAD SOFTRESTAURANT
# Módulo Propinas TPV - Validación VPN

**Versión:** 1.0  
**Fecha:** 15 de Abril de 2026  
**Estado:** PENDIENTE DE DATOS DE VALIDACIÓN VPN

---

## 1. RESULTADOS DE DETECCIÓN DE ESQUEMA

### Endpoint Usado
```
GET /api/finanzas/propinas/detectar-esquema-todos
```

### Resultados Preliminares (Sin acceso VPN desde Preview)

| Sucursal | Server ID | Host | DB | Tablas Detectadas | Problema |
|----------|-----------|------|----|--------------------|----------|
| CIENFUEGOS | 6d053c22-...781b | servercienfuegos.ddns.net,6669 | softrestaurant95pro | movtoscaja, movtoscajadetalles | No se encontró columna de concepto |
| LA ESTELAR | a5ff0e25-...904f | serverestelar.ddns.net,6969 | softrestaurant12 | movtoscaja, movtoscajadetalles | No se encontró columna de concepto |
| 130° MÉRIDA | 572502c7-...87db | 130mid.ddns.net | softrestaurant10 | movtoscaja, movtoscajadetalles | No se encontró columna de concepto |

### Problema Identificado
El detector actual busca la columna `idconcepto` en `movtoscajadetalles`, pero esta columna no existe en las versiones de SoftRestaurant detectadas.

---

## 2. ESTRATEGIAS DE EXTRACCIÓN IMPLEMENTADAS

### ESTRATEGIA A: COLUMNA_DIRECTA (Preferida)
- **Fuente:** Columna `propinas_pagadas` directamente en `movtoscaja`
- **Ventaja:** Dato pre-calculado por SoftRestaurant, más confiable
- **Alternativas buscadas:** `propinas_pagadas`, `propinaspagadas`, `propinas`, `propina`

### ESTRATEGIA B: DETALLE_CONCEPTO (Tradicional)
- **Fuente:** Tabla `movtoscajadetalles` filtrando por `idconcepto = 9`
- **Requisito:** Columna `idconcepto` debe existir
- **Alternativas buscadas:** `idconcepto`, `concepto_id`, `conceptoid`, `id_concepto`

---

## 3. INFORMACIÓN REQUERIDA DEL USUARIO

Para completar la matriz de compatibilidad, necesito que ejecute las siguientes consultas SQL desde un ambiente con acceso VPN a cada servidor:

### Query 1: Columnas de movtoscaja
```sql
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'movtoscaja'
ORDER BY ORDINAL_POSITION;
```

### Query 2: Columnas de movtoscajadetalles
```sql
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'movtoscajadetalles'
ORDER BY ORDINAL_POSITION;
```

### Query 3: Muestra de datos de un corte (si existe propinas_pagadas)
```sql
SELECT TOP 5
    folio,
    fecha,
    propinas_pagadas,
    saldo
FROM movtoscaja
WHERE idtipomovtocaja = 3
ORDER BY fecha DESC;
```

---

## 4. MATRIZ DE COMPATIBILIDAD (PLANTILLA)

*A completar con datos del usuario*

| Sucursal | Tabla Origen | Columnas Utilizadas | Tipo Dato | Query Final | Estatus |
|----------|-------------|---------------------|-----------|-------------|---------|
| La Estelar | `movtoscaja` | `propinas_pagadas`, `folio`, `fecha` | EXACTO | (Ver Query A) | PENDIENTE |
| Cienfuegos | `movtoscaja` | `propinas_pagadas`, `folio`, `fecha` | EXACTO | (Ver Query A) | PENDIENTE |
| 130° Mérida | `movtoscaja` | `propinas_pagadas`, `folio`, `fecha` | EXACTO | (Ver Query A) | PENDIENTE |

### Estatus Posibles
- **GO:** Compatible sin ajustes
- **GO_CON_AJUSTES:** Compatible con restricciones menores
- **NO_GO:** Incompatible, requiere desarrollo adicional

---

## 5. DICTAMEN PRELIMINAR

### Basado en Análisis Teórico

| Sucursal | Dictamen Preliminar | Condición |
|----------|---------------------|-----------|
| La Estelar | **PENDIENTE** | Depende de existencia de columna propinas |
| Cienfuegos | **PENDIENTE** | Depende de existencia de columna propinas |
| 130° Mérida | **PENDIENTE** | Depende de existencia de columna propinas |

### Escenarios Posibles

**ESCENARIO 1:** Si existe columna `propinas_pagadas` en `movtoscaja`
- Dictamen: **GO** - Lista para piloto
- Estrategia: COLUMNA_DIRECTA
- Confianza: ALTA

**ESCENARIO 2:** Si existe columna `idconcepto` en `movtoscajadetalles`
- Dictamen: **GO_CON_AJUSTES** - Lista con restricciones
- Estrategia: DETALLE_CONCEPTO
- Confianza: MEDIA
- Restricción: Requiere mapeo de conceptos

**ESCENARIO 3:** Si no existe ninguna
- Dictamen: **NO_GO** - No lista
- Requiere: Análisis adicional de estructura

---

## 6. VALIDACIONES PENDIENTES

### A. Unicidad de Registros
- [ ] Verificar que no haya duplicados por (server_id, sucursal_id, folio_corte, fecha_corte)
- [ ] Confirmar que cada corte Z tiene un único registro de propinas

### B. Montos
- [ ] Comparar propinas_pagadas vs operación real
- [ ] Verificar rangos típicos ($0 - $50,000 por corte)

### C. Cálculo de Comisión
```
comision = propinas_tpv * 0.02
monto_a_pagar = propinas_tpv - comision
```

### D. Llave de Integración
```
UK = (server_id, sucursal_id, folio_corte, fecha_corte)
```
- [ ] Verificar que no genere colisiones entre sucursales

---

## 7. PRÓXIMOS PASOS

1. **Usuario:** Ejecutar queries de diagnóstico en ambiente VPN
2. **Usuario:** Reportar columnas encontradas en cada servidor
3. **Agente:** Ajustar detector según columnas reales
4. **Agente:** Ejecutar preview con datos reales
5. **Agente:** Completar matriz de compatibilidad
6. **Usuario:** Aprobar dictamen final

---

## ANEXO: QUERIES DE DIAGNÓSTICO MEJORADAS

### Query Completa de Diagnóstico (Ejecutar en cada servidor)

```sql
-- ============================================
-- DIAGNÓSTICO DE ESQUEMA SOFTRESTAURANT
-- Ejecutar en cada sucursal desde ambiente VPN
-- ============================================

PRINT '=== SERVIDOR: [NOMBRE_SUCURSAL] ==='
PRINT ''

-- 1. Columnas de movtoscaja
PRINT '--- Columnas de movtoscaja ---'
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'movtoscaja'
ORDER BY ORDINAL_POSITION;

PRINT ''

-- 2. Columnas de movtoscajadetalles
PRINT '--- Columnas de movtoscajadetalles ---'
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'movtoscajadetalles'
ORDER BY ORDINAL_POSITION;

PRINT ''

-- 3. Muestra de cortes Z recientes
PRINT '--- Muestra de Cortes Z (últimos 5) ---'
SELECT TOP 5
    folio,
    fecha,
    idtipomovtocaja,
    saldo,
    -- Intentar columnas de propinas (pueden no existir)
    -- ISNULL(propinas_pagadas, 0) AS propinas_pagadas,
    -- ISNULL(tarjeta, 0) AS tarjeta,
    *
FROM movtoscaja
WHERE idtipomovtocaja = 3
ORDER BY fecha DESC;

PRINT ''
PRINT '=== FIN DIAGNÓSTICO ==='
```

---

**FIN DEL DOCUMENTO DE MATRIZ DE COMPATIBILIDAD**

*Este documento se actualizará con los resultados de la validación VPN del usuario.*
