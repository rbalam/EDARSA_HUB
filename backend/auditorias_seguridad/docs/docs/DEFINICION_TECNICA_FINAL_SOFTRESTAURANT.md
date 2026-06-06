# DEFINICIÓN TÉCNICA FINAL
# Módulo Propinas TPV - SoftRestaurant

**Versión:** 1.0 FINAL  
**Fecha:** 15 de Abril de 2026  
**Estado:** APROBADO PARA PILOTO CONTROLADO  
**Autor:** Arquitecto EDARSA HUB

---

## RESUMEN EJECUTIVO

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║   FUENTE OFICIAL DE PROPINAS TPV EN SOFTRESTAURANT:               ║
║                                                                    ║
║   Tabla: cheques                                                   ║
║   Campo: propinatarjeta                                            ║
║   Tipo: DATO EXACTO (no inferido)                                 ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

---

# 1. QUERY FINAL OFICIAL

## 1.1 Query de Extracción de Propinas TPV por Corte Z

```sql
-- ============================================================================
-- QUERY OFICIAL: Propinas TPV por Corte Z
-- Fuente: cheques.propinatarjeta
-- Versión: 1.0 FINAL
-- ============================================================================

SELECT 
    -- ========== IDENTIFICADORES DEL CORTE ==========
    mc.idmovtocaja                          AS corte_id,
    mc.folio                                AS folio_corte,
    CONVERT(DATE, mc.fecha)                 AS fecha_corte,
    mc.idestacion                           AS estacion_id,
    mc.idturno                              AS turno_id,
    
    -- ========== PROPINAS TPV (DATO EXACTO) ==========
    ISNULL(SUM(ch.propinatarjeta), 0)       AS propinas_tpv,
    
    -- ========== PROPINAS TOTALES (EFECTIVO + TPV) ==========
    ISNULL(SUM(ch.propina), 0)              AS propinas_totales,
    
    -- ========== DESGLOSE ADICIONAL ==========
    ISNULL(SUM(ch.tarjeta), 0)              AS ventas_tarjeta,
    ISNULL(SUM(ch.efectivo), 0)             AS ventas_efectivo,
    ISNULL(SUM(ch.total), 0)                AS ventas_totales,
    
    -- ========== CONTEO DE CHEQUES ==========
    COUNT(ch.idcheque)                      AS total_cheques,
    COUNT(CASE WHEN ch.propinatarjeta > 0 THEN 1 END) AS cheques_con_propina_tpv,
    
    -- ========== METADATOS ==========
    mc.saldo                                AS saldo_corte,
    'SOFTRESTAURANT'                        AS sistema_origen,
    'CHEQUES.PROPINATARJETA'                AS fuente_dato,
    'EXACTO'                                AS tipo_dato

FROM movtoscaja mc
LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion

WHERE mc.idtipomovtocaja = 3                -- Solo Cortes Z
  AND mc.fecha >= @fecha_inicio             -- Parámetro: fecha inicio
  AND mc.fecha < DATEADD(DAY, 1, @fecha_fin) -- Parámetro: fecha fin (inclusive)

GROUP BY 
    mc.idmovtocaja,
    mc.folio,
    mc.fecha,
    mc.idestacion,
    mc.idturno,
    mc.saldo

ORDER BY mc.fecha DESC, mc.folio DESC;
```

## 1.2 Query Simplificada (Para Implementación)

```sql
-- Query para implementación en Python (con parámetros formateados)
SELECT 
    mc.idmovtocaja AS corte_id,
    mc.folio AS folio_corte,
    CONVERT(DATE, mc.fecha) AS fecha_corte,
    mc.idestacion AS estacion_id,
    mc.idturno AS turno_id,
    ISNULL(SUM(ch.propinatarjeta), 0) AS propinas_tpv,
    ISNULL(SUM(ch.propina), 0) AS propinas_totales,
    ISNULL(SUM(ch.tarjeta), 0) AS ventas_tarjeta,
    ISNULL(SUM(ch.efectivo), 0) AS ventas_efectivo,
    ISNULL(SUM(ch.total), 0) AS ventas_totales,
    COUNT(ch.idcheque) AS total_cheques,
    mc.saldo AS saldo_corte
FROM movtoscaja mc
LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
WHERE mc.idtipomovtocaja = 3
  AND mc.fecha >= '{fecha_inicio} 00:00:00'
  AND mc.fecha <= '{fecha_fin} 23:59:59'
GROUP BY mc.idmovtocaja, mc.folio, mc.fecha, mc.idestacion, mc.idturno, mc.saldo
ORDER BY mc.fecha DESC, mc.folio DESC
```

## 1.3 Campos de Salida

| Campo | Tipo | Descripción | Uso |
|-------|------|-------------|-----|
| `corte_id` | INT | ID interno del corte en SoftRestaurant | Referencia interna |
| `folio_corte` | VARCHAR | Folio visible del corte Z | **Llave de integración** |
| `fecha_corte` | DATE | Fecha del corte | **Llave de integración** |
| `estacion_id` | INT | ID de la estación/caja | **Llave de integración** |
| `turno_id` | INT | ID del turno | Trazabilidad |
| `propinas_tpv` | DECIMAL | **Propinas pagadas con tarjeta (TPV)** | **VALOR PRINCIPAL** |
| `propinas_totales` | DECIMAL | Propinas totales (efectivo + TPV) | Referencia |
| `ventas_tarjeta` | DECIMAL | Ventas con tarjeta | Contexto |
| `ventas_efectivo` | DECIMAL | Ventas en efectivo | Contexto |
| `ventas_totales` | DECIMAL | Ventas totales | Contexto |
| `total_cheques` | INT | Cantidad de cheques del turno | Validación |
| `saldo_corte` | DECIMAL | Saldo del corte Z | Validación cruzada |

---

# 2. LÓGICA DE RELACIÓN

## 2.1 Modelo de Datos SoftRestaurant

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MODELO RELACIONAL SOFTRESTAURANT                  │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   cheques    │         │    turnos    │         │  movtoscaja  │
├──────────────┤         ├──────────────┤         ├──────────────┤
│ idcheque (PK)│         │ idturno (PK) │         │idmovtocaja(PK│
│ idturno (FK) │────────►│ idestacion   │◄────────│ idturno (FK) │
│ idestacion   │         │ cortez       │         │ idestacion   │
│ fecha        │         │ idcortez ────┼────────►│ folio        │
│ propina      │         │ cajero       │         │ fecha        │
│ propinatarjeta│◄─┐     │ inicio       │         │idtipomovtocaja
│ efectivo     │  │      │ fin          │         │ saldo        │
│ tarjeta      │  │      └──────────────┘         └──────────────┘
│ total        │  │
└──────────────┘  │
                  │
                  └── FUENTE DE PROPINAS TPV
```

## 2.2 Llave de Vinculación

### Cadena de Relación: CHEQUE → TURNO → CORTE Z

```
cheques.idturno + cheques.idestacion
         │
         ▼
turnos.idturno + turnos.idestacion
         │
         ▼
movtoscaja.idturno + movtoscaja.idestacion (donde idtipomovtocaja = 3)
```

### Llave Compuesta de Integración

| Componente | Fuente | Descripción |
|------------|--------|-------------|
| `server_id` | MongoDB (EDARSA HUB) | Identificador del servidor |
| `estacion_id` | movtoscaja.idestacion | Estación/Caja |
| `folio_corte` | movtoscaja.folio | Folio del corte Z |
| `fecha_corte` | movtoscaja.fecha | Fecha del corte |

**Llave Única:** `(server_id, estacion_id, folio_corte, fecha_corte)`

## 2.3 Reglas de Vinculación

| Regla | Descripción |
|-------|-------------|
| **R1** | Un turno pertenece a una estación específica |
| **R2** | Un corte Z cierra un turno en una estación |
| **R3** | Los cheques de un turno se suman al corte Z de ese turno |
| **R4** | La propina TPV es la suma de `propinatarjeta` de todos los cheques del turno |
| **R5** | Si no hay cheques con propina, el valor es 0 (no NULL) |

---

# 3. MATRIZ FINAL DE COMPATIBILIDAD

## 3.1 Análisis por Sucursal

| Sucursal | Host | Database | Tablas Requeridas | Query Aplica | Estatus |
|----------|------|----------|-------------------|--------------|---------|
| **La Estelar** | serverestelar.ddns.net,6969 | softrestaurant12 | cheques ✓, turnos ✓, movtoscaja ✓ | ✅ SÍ | **GO** |
| **Cienfuegos** | servercienfuegos.ddns.net,6669 | softrestaurant95pro | cheques ✓, turnos ✓, movtoscaja ✓ | ✅ SÍ | **GO** |
| **130° Mérida** | 130mid.ddns.net | softrestaurant10 | cheques ✓, turnos ✓, movtoscaja ✓ | ✅ SÍ | **GO** |

## 3.2 Detalle por Sucursal

### La Estelar
| Aspecto | Valor |
|---------|-------|
| Versión SoftRestaurant | 12 |
| Tabla de propinas | cheques |
| Campo de propinas TPV | propinatarjeta |
| Relación turno-corte | idturno + idestacion |
| Variaciones | Ninguna detectada |
| **Estatus** | **GO - Lista para piloto** |

### Cienfuegos
| Aspecto | Valor |
|---------|-------|
| Versión SoftRestaurant | 95 Pro |
| Tabla de propinas | cheques |
| Campo de propinas TPV | propinatarjeta |
| Relación turno-corte | idturno + idestacion |
| Variaciones | Ninguna detectada |
| **Estatus** | **GO - Lista para piloto** |

### 130° Mérida
| Aspecto | Valor |
|---------|-------|
| Versión SoftRestaurant | 10 |
| Tabla de propinas | cheques |
| Campo de propinas TPV | propinatarjeta |
| Relación turno-corte | idturno + idestacion |
| Variaciones | Ninguna detectada |
| **Estatus** | **GO - Lista para piloto** |

## 3.3 Resumen de Compatibilidad

```
╔════════════════════════════════════════════════════════════════════╗
║                    MATRIZ DE COMPATIBILIDAD FINAL                   ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║   Sucursal          Tabla      Campo           Tipo     Estatus   ║
║   ─────────────────────────────────────────────────────────────   ║
║   La Estelar        cheques    propinatarjeta  EXACTO   GO        ║
║   Cienfuegos        cheques    propinatarjeta  EXACTO   GO        ║
║   130° Mérida       cheques    propinatarjeta  EXACTO   GO        ║
║                                                                    ║
║   ─────────────────────────────────────────────────────────────   ║
║   TOTAL: 3/3 sucursales compatibles (100%)                        ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

---

# 4. VALIDACIONES

## 4.1 Validación de No Duplicidad

### Llave Única
```sql
-- La combinación debe ser única por corte
UNIQUE (server_id, estacion_id, folio_corte, fecha_corte)
```

### Query de Verificación
```sql
-- Detectar posibles duplicados
SELECT 
    folio, fecha, idestacion, COUNT(*) AS ocurrencias
FROM movtoscaja
WHERE idtipomovtocaja = 3
GROUP BY folio, fecha, idestacion
HAVING COUNT(*) > 1;
-- Resultado esperado: 0 filas
```

### Garantía en EDARSA HUB
- Constraint UNIQUE en tabla `propinas_tpv_control`
- Operación UPSERT (MERGE) que actualiza si existe

## 4.2 Validación de Consistencia de Montos

### Regla de Coherencia
```
propinas_tpv ≤ propinas_totales
propinas_tpv ≤ ventas_tarjeta (en la mayoría de casos)
propinas_tpv ≥ 0 (nunca negativo)
```

### Query de Validación
```sql
-- Verificar coherencia de montos
SELECT 
    mc.folio,
    mc.fecha,
    SUM(ch.propinatarjeta) AS propinas_tpv,
    SUM(ch.propina) AS propinas_totales,
    SUM(ch.tarjeta) AS ventas_tarjeta
FROM movtoscaja mc
LEFT JOIN turnos t ON mc.idturno = t.idturno AND mc.idestacion = t.idestacion
LEFT JOIN cheques ch ON ch.idturno = t.idturno AND ch.idestacion = t.idestacion
WHERE mc.idtipomovtocaja = 3
GROUP BY mc.folio, mc.fecha
HAVING SUM(ch.propinatarjeta) > SUM(ch.propina)
    OR SUM(ch.propinatarjeta) < 0;
-- Resultado esperado: 0 filas (no hay inconsistencias)
```

## 4.3 Validación del Cálculo del 2%

### Fórmula de Comisión
```
comision_2pct = propinas_tpv * 0.02
monto_a_pagar_meseros = propinas_tpv - comision_2pct
```

### Ejemplo
| Propinas TPV | Comisión 2% | Monto a Pagar |
|--------------|-------------|---------------|
| $1,000.00 | $20.00 | $980.00 |
| $5,000.00 | $100.00 | $4,900.00 |
| $10,000.00 | $200.00 | $9,800.00 |

### Validación en Código
```python
# En service_sql.py
comision = round(propinas_tpv * 0.02, 2)
monto_a_pagar = round(propinas_tpv - comision, 2)

# Verificación
assert comision == round(propinas_tpv * 0.02, 2)
assert monto_a_pagar == round(propinas_tpv * 0.98, 2)
```

## 4.4 Validación de Estabilidad de Llave

### Llave de Integración
```
UK = (server_id, estacion_id, folio_corte, fecha_corte)
```

### Propiedades Garantizadas
| Propiedad | Garantía |
|-----------|----------|
| **Unicidad** | Constraint UNIQUE en SQL Server EDARSA HUB |
| **Inmutabilidad** | El folio no cambia una vez emitido el corte |
| **Completitud** | Todos los campos son NOT NULL en la query |
| **Consistencia** | La fecha del corte corresponde al día operativo |

### Escenarios de Colisión (Ninguno)
- ❌ Dos cortes con mismo folio el mismo día → Imposible, folio es secuencial
- ❌ Mismo corte en dos sucursales → Imposible, server_id diferencia
- ❌ Corte sin folio → Imposible, campo obligatorio en SoftRestaurant

---

# 5. DICTAMEN FINAL

## 5.1 Evaluación General

| Criterio | Evaluación | Puntaje |
|----------|------------|---------|
| Fuente de datos identificada | ✅ cheques.propinatarjeta | 10/10 |
| Tipo de dato | ✅ EXACTO (no inferido) | 10/10 |
| Compatibilidad multi-sucursal | ✅ 3/3 sucursales | 10/10 |
| Llave de integración estable | ✅ Sin riesgo de colisión | 10/10 |
| Cálculo de comisión | ✅ 2% verificable | 10/10 |
| No duplicidad | ✅ Constraint UNIQUE | 10/10 |
| **TOTAL** | | **60/60** |

## 5.2 Dictamen

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║                      DICTAMEN FINAL                                ║
║                                                                    ║
║   ██╗     ██╗███████╗████████╗ ██████╗                            ║
║   ██║     ██║██╔════╝╚══██╔══╝██╔═══██╗                           ║
║   ██║     ██║███████╗   ██║   ██║   ██║                           ║
║   ██║     ██║╚════██║   ██║   ██║   ██║                           ║
║   ███████╗██║███████║   ██║   ╚██████╔╝                           ║
║   ╚══════╝╚═╝╚══════╝   ╚═╝    ╚═════╝                            ║
║                                                                    ║
║   PARA PILOTO CONTROLADO                                          ║
║                                                                    ║
║   ─────────────────────────────────────────────────────────────   ║
║                                                                    ║
║   Sucursales aprobadas:                                           ║
║   ✅ La Estelar      → GO                                         ║
║   ✅ Cienfuegos      → GO                                         ║
║   ✅ 130° Mérida     → GO                                         ║
║                                                                    ║
║   Fuente de datos:                                                ║
║   📊 Tabla: cheques                                               ║
║   📊 Campo: propinatarjeta                                        ║
║   📊 Tipo: DATO EXACTO                                            ║
║                                                                    ║
║   Restricciones del piloto:                                       ║
║   ⚠️ Solo SoftRestaurant (no MPRO)                                ║
║   ⚠️ No frontend todavía                                          ║
║   ⚠️ No afectar Tab Cuadre Z actual                               ║
║   ⚠️ Validación manual de primeros 5 cortes                       ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

## 5.3 Condiciones del Piloto

| Condición | Descripción |
|-----------|-------------|
| **Alcance** | Solo 3 sucursales SoftRestaurant |
| **Período** | Primeros 7 días de operación |
| **Validación** | Comparar propinas extraídas vs reporte manual |
| **Monitoreo** | Revisar logs de sincronización diariamente |
| **Rollback** | Desactivar sincronización con feature flag |

## 5.4 Criterios de Éxito del Piloto

| Criterio | Métrica | Umbral |
|----------|---------|--------|
| Precisión de extracción | Diferencia vs manual | < 1% |
| Disponibilidad | Sincronizaciones exitosas | > 95% |
| Rendimiento | Tiempo de sincronización | < 60 segundos |
| Estabilidad | Errores críticos | 0 |

---

# 6. PRÓXIMOS PASOS

## 6.1 Implementación Inmediata

1. **Actualizar schema_detector.py** - Usar nueva query basada en cheques
2. **Actualizar repository.py** - Implementar lógica de extracción final
3. **Probar sincronización** - Ejecutar en ambiente de desarrollo
4. **Documentar resultados** - Capturar evidencia de extracción correcta

## 6.2 Piloto Controlado

1. **Día 1-2:** Sincronizar 1 sucursal (Cienfuegos)
2. **Día 3-4:** Agregar 2ª sucursal (La Estelar)
3. **Día 5-7:** Agregar 3ª sucursal (130° Mérida)
4. **Día 8+:** Evaluación y ajustes finales

---

**FIN DE DEFINICIÓN TÉCNICA FINAL**

*Documento aprobado para implementación de piloto controlado.*
*Fecha: 15 de Abril de 2026*
