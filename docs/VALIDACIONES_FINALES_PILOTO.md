# VALIDACIONES FINALES PARA PILOTO CONTROLADO
# Módulo Propinas TPV - SoftRestaurant

**Fecha:** 15 de Abril de 2026  
**Estado:** VALIDACIÓN PRE-PILOTO

---

## 1. VALIDACIÓN DE NO DUPLICIDAD

### 1.1 Query de Verificación - Duplicados por Corte

Ejecutar en cada servidor SoftRestaurant:

```sql
-- ============================================
-- VALIDACIÓN 1: No hay duplicados por corte
-- Resultado esperado: 0 filas
-- ============================================

SELECT 
    mc.idmovtocaja,
    mc.folio,
    CONVERT(DATE, mc.fecha) AS fecha,
    mc.idestacion,
    mc.idturno,
    COUNT(*) AS ocurrencias
FROM movtoscaja mc
WHERE mc.idtipomovtocaja = 3  -- Solo Corte Z
  AND mc.fecha >= '2026-04-01'
  AND mc.fecha <= '2026-04-15'
GROUP BY mc.idmovtocaja, mc.folio, mc.fecha, mc.idestacion, mc.idturno
HAVING COUNT(*) > 1;

-- Si retorna filas = HAY DUPLICADOS (FAIL)
-- Si retorna 0 filas = SIN DUPLICADOS (PASS)
```

### 1.2 Query de Verificación - Unicidad de idmovtocaja

```sql
-- ============================================
-- VALIDACIÓN 2: idmovtocaja es único por corte
-- Resultado esperado: 0 filas con duplicados
-- ============================================

SELECT 
    idmovtocaja,
    COUNT(*) AS veces
FROM movtoscaja
WHERE idtipomovtocaja = 3
GROUP BY idmovtocaja
HAVING COUNT(*) > 1;

-- Si retorna filas = idmovtocaja NO es único (PROBLEMA)
-- Si retorna 0 filas = idmovtocaja ES único (OK)
```

### 1.3 Query de Verificación - Relación Turno-Corte

```sql
-- ============================================
-- VALIDACIÓN 3: Un turno tiene máximo un Corte Z
-- Resultado esperado: 0 filas o pocas (casos especiales)
-- ============================================

SELECT 
    mc.idturno,
    mc.idestacion,
    COUNT(DISTINCT mc.idmovtocaja) AS cortes_por_turno
FROM movtoscaja mc
WHERE mc.idtipomovtocaja = 3
  AND mc.fecha >= '2026-04-01'
GROUP BY mc.idturno, mc.idestacion
HAVING COUNT(DISTINCT mc.idmovtocaja) > 1;

-- Si retorna filas = Un turno tiene múltiples cortes (REVISAR)
-- Si retorna 0 filas = Relación 1:1 turno-corte (OK)
```

### 1.4 Query de Verificación - Propinas por Corte (Sin duplicar cheques)

```sql
-- ============================================
-- VALIDACIÓN 4: Query final no duplica propinas
-- Compara suma directa vs query con JOINs
-- ============================================

-- Método A: Suma directa de cheques por turno
SELECT 
    t.idturno,
    t.idestacion,
    SUM(ch.propinatarjeta) AS propinas_metodo_directo
FROM turnos t
JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
WHERE t.idturno IN (
    SELECT TOP 5 idturno FROM movtoscaja 
    WHERE idtipomovtocaja = 3 
    ORDER BY fecha DESC
)
GROUP BY t.idturno, t.idestacion;

-- Método B: Query oficial con JOINs
SELECT 
    mc.idmovtocaja,
    mc.idturno,
    mc.idestacion,
    ISNULL(SUM(ch.propinatarjeta), 0) AS propinas_query_oficial
FROM movtoscaja mc
LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
WHERE mc.idtipomovtocaja = 3
  AND mc.idmovtocaja IN (
    SELECT TOP 5 idmovtocaja FROM movtoscaja 
    WHERE idtipomovtocaja = 3 
    ORDER BY fecha DESC
  )
GROUP BY mc.idmovtocaja, mc.idturno, mc.idestacion;

-- COMPARAR: propinas_metodo_directo debe ser igual a propinas_query_oficial
-- Si son iguales = NO HAY DUPLICACIÓN (PASS)
-- Si difieren = HAY DUPLICACIÓN (FAIL)
```

---

## 2. VALIDACIÓN DE LLAVE

### 2.1 Análisis de Componentes de Llave

| Campo | Propósito | ¿Incluir en Llave? | Razón |
|-------|-----------|-------------------|-------|
| `server_id` | Identificar servidor EDARSA | ✅ SÍ (Funcional) | Distingue entre sucursales |
| `estacion_id` | Identificar caja/terminal | ✅ SÍ (Funcional) | Una sucursal puede tener múltiples cajas |
| `folio_corte` | Número de corte visible | ✅ SÍ (Funcional) | Identificador operativo |
| `fecha_corte` | Fecha del corte | ✅ SÍ (Funcional) | Folios pueden reiniciarse por año |
| `idmovtocaja` | ID interno SoftRestaurant | ✅ SÍ (Trazabilidad) | **RECOMENDADO** - Referencia única en origen |
| `idturno` | ID del turno | ⚠️ OPCIONAL | Útil para debugging pero redundante |

### 2.2 Recomendación

```
╔════════════════════════════════════════════════════════════════════╗
║  LLAVE FUNCIONAL (Constraint UNIQUE en SQL Server EDARSA HUB):    ║
║                                                                    ║
║  (server_id, estacion_id, folio_corte, fecha_corte)               ║
║                                                                    ║
║  CAMPOS ADICIONALES PARA TRAZABILIDAD (sin constraint):           ║
║                                                                    ║
║  + idmovtocaja  → Referencia al ID del corte en SoftRestaurant    ║
║  + idturno      → Referencia al turno (opcional)                  ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

### 2.3 Justificación

**¿Por qué agregar `idmovtocaja`?**
- Es el ID único del corte en SoftRestaurant
- Permite hacer queries directas al origen si hay discrepancias
- No afecta la llave funcional, solo mejora trazabilidad

**¿Por qué `idturno` es opcional?**
- El turno ya está implícito en el corte (relación 1:1 típica)
- Agregar ambos puede causar confusión
- Si se necesita, se puede obtener con JOIN

---

## 3. PRUEBA DE 5 CORTES REALES

### 3.1 Query para Obtener 5 Cortes de Prueba

Ejecutar en cada servidor:

```sql
-- ============================================
-- OBTENER 5 CORTES RECIENTES PARA VALIDACIÓN
-- ============================================

SELECT TOP 5
    mc.idmovtocaja AS corte_id_soft,
    mc.folio AS folio_corte,
    CONVERT(DATE, mc.fecha) AS fecha_corte,
    mc.idestacion AS estacion,
    mc.idturno AS turno,
    ISNULL(SUM(ch.propinatarjeta), 0) AS propina_tpv_sistema,
    COUNT(ch.idcheque) AS cheques_con_propina
FROM movtoscaja mc
LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
WHERE mc.idtipomovtocaja = 3
  AND mc.fecha >= DATEADD(DAY, -7, GETDATE())  -- Últimos 7 días
GROUP BY mc.idmovtocaja, mc.folio, mc.fecha, mc.idestacion, mc.idturno
HAVING ISNULL(SUM(ch.propinatarjeta), 0) > 0  -- Solo cortes con propinas
ORDER BY mc.fecha DESC;
```

### 3.2 Plantilla de Validación

#### LA ESTELAR

| # | Folio | Fecha | Propina Manual | Propina Sistema | Diferencia | Resultado |
|---|-------|-------|----------------|-----------------|------------|-----------|
| 1 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 2 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 3 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 4 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 5 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |

**Criterio:** Diferencia ≤ $1.00 = PASS

#### CIENFUEGOS

| # | Folio | Fecha | Propina Manual | Propina Sistema | Diferencia | Resultado |
|---|-------|-------|----------------|-----------------|------------|-----------|
| 1 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 2 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 3 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 4 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 5 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |

#### 130° MÉRIDA

| # | Folio | Fecha | Propina Manual | Propina Sistema | Diferencia | Resultado |
|---|-------|-------|----------------|-----------------|------------|-----------|
| 1 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 2 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 3 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 4 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |
| 5 | _____ | _____ | $_____________ | $______________ | $_________ | ⬜ PASS / ⬜ FAIL |

---

## 4. CRITERIOS DE APROBACIÓN

### Validación 1: No Duplicidad
- [ ] Query 1.1 retorna 0 filas
- [ ] Query 1.2 retorna 0 filas
- [ ] Query 1.3 retorna 0 filas o casos justificados
- [ ] Query 1.4 muestra valores iguales entre métodos

### Validación 2: Llave
- [ ] Confirmar inclusión de `idmovtocaja` para trazabilidad
- [ ] Decidir si incluir `idturno` (opcional)

### Validación 3: Cortes Reales
- [ ] La Estelar: 5/5 cortes PASS
- [ ] Cienfuegos: 5/5 cortes PASS
- [ ] 130° Mérida: 5/5 cortes PASS

### Resultado Final
```
[ ] TODAS las validaciones PASS → APROBADO PARA PILOTO
[ ] Alguna validación FAIL → REQUIERE AJUSTES
```

---

**FIN DE DOCUMENTO DE VALIDACIONES**
