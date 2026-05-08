# VALIDACIÓN TÉCNICA PROFUNDA - MÓDULO PROPINAS TPV

**Versión:** 2.0  
**Fecha:** 14 de Abril de 2026  
**Estado:** RESPUESTA A OBSERVACIONES DEL CAB  
**Documento padre:** `CAB_MODULO_PROPINAS_TPV.md`

---

## RESPUESTA A OBSERVACIONES DEL USUARIO

Este documento responde punto por punto las 6 observaciones críticas levantadas antes de aprobar el diseño.

---

# 1. SIMPLIFICACIÓN DEL MODELO

## 1.1 ¿Por qué se propusieron 4 colecciones?

| Colección Original | Propósito |
|-------------------|-----------|
| `propinas_registro` | Datos operativos sincronizados desde SQL |
| `propinas_pagos` | Registro de pagos a meseros |
| `propinas_cuadres` | Consolidados por período |
| `propinas_config` | Configuración global |

## 1.2 ¿Se puede resolver con menos tablas?

**SÍ. Se puede reducir a 2 colecciones.**

### Propuesta Simplificada:

| Colección | Propósito | Justificación |
|-----------|-----------|---------------|
| `propinas_control` | **ÚNICA** para registros + pagos + cuadre | Combina todo en un solo documento por período/sucursal |
| `propinas_config` | Configuración (singleton) | Necesaria para parametrizar % y formas de pago |

## 1.3 Modelo Mínimo Viable (2 Colecciones)

### Colección: `propinas_control`

```javascript
{
  "_id": ObjectId,
  "id": "UUID",
  
  // ========== IDENTIFICADOR ÚNICO ==========
  // Clave compuesta: server_id + sucursal_id + fecha_corte + folio_corte
  "server_id": "uuid-servidor",
  "server_name": "Cienfuegos",
  "system_type": "SoftRestaurant",  // o "MPRO"
  "sucursal_id": "CIENFUEGOS",
  "sucursal_nombre": "Cienfuegos",
  
  // ========== VÍNCULO CON CORTE (LLAVE MAESTRA) ==========
  "folio_corte": "2889",
  "fecha_corte": ISODate("2026-04-14T00:00:00Z"),
  
  // ========== DATOS OPERATIVOS (LECTURA DE SQL) ==========
  "origen": {
    "propinas_totales_corte": 15000.00,      // Desde Corte Z (concepto 9 o campo propinas)
    "propinas_efectivo": 5000.00,             // Calculado o desde SQL si existe
    "propinas_tpv": 10000.00,                 // Propinas con tarjeta
    "fecha_sincronizacion": ISODate,
    "query_usada": "movtoscajadetalles.idconcepto=9"  // Para auditoría
  },
  
  // ========== CÁLCULOS (EDARSA HUB) ==========
  "calculo": {
    "porcentaje_comision": 0.02,
    "comision_calculada": 200.00,             // propinas_tpv * 0.02
    "monto_a_pagar_meseros": 9800.00          // propinas_tpv * 0.98
  },
  
  // ========== REGISTRO DE PAGO (MANUAL) ==========
  "pago": {
    "monto_pagado": 9800.00,
    "fecha_pago": ISODate("2026-04-15T10:00:00Z"),
    "metodo": "EFECTIVO",
    "registrado_por": "tesorero@edarsa.com.mx",
    "observaciones": ""
  },
  
  // ========== CUADRE (CALCULADO) ==========
  "cuadre": {
    "estado": "CUADRADO",  // PENDIENTE, CALCULADO, PAGADO, CUADRADO, DESCUADRE
    "diferencia": 0.00,
    "fecha_cuadre": ISODate
  },
  
  // ========== METADATA ==========
  "created_at": ISODate,
  "updated_at": ISODate,
  "created_by": "sistema",
  "updated_by": "tesorero@edarsa.com.mx"
}
```

### Índices:
```javascript
// Clave única compuesta
{ "server_id": 1, "folio_corte": 1, "sucursal_id": 1 }  // UNIQUE

// Búsquedas frecuentes
{ "fecha_corte": 1, "cuadre.estado": 1 }
{ "server_id": 1, "fecha_corte": 1 }
```

### Colección: `propinas_config` (Sin cambios)

```javascript
{
  "_id": ObjectId,
  "id": "config_propinas",  // Singleton
  "porcentaje_comision": 0.02,
  "formas_pago_tpv": {
    "SoftRestaurant": {
      "conceptos_tarjeta": [10, 11, 12],  // idconcepto en movtoscajadetalles
      "descripcion": "Visa/MC/Amex"
    },
    "MPRO": {
      "campo": "tarjeta_credito + tarjeta_debito",  // Campos en tabla caja
      "descripcion": "TC + TD"
    }
  },
  "tolerancia_descuadre": 5.00,
  "updated_at": ISODate,
  "updated_by": "admin@edarsa.com.mx"
}
```

## 1.4 Ventajas del Modelo Simplificado

| Aspecto | 4 Colecciones | 2 Colecciones |
|---------|---------------|---------------|
| Complejidad | Alta | **Baja** |
| Joins/Lookups | Múltiples | **Ninguno** |
| Consistencia | Riesgo de desync | **Documento atómico** |
| Queries | Más complejas | **Directas** |
| Mantenimiento | Mayor | **Menor** |

---

# 2. INTEGRACIÓN REAL CON CORTES Y CAJA

## 2.1 ¿Cómo se vincula con los cortes existentes?

### Arquitectura de Integración:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SQL SERVER (FUENTES OPERATIVAS)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SOFTRESTAURANT                      MPRO                           │
│  ┌─────────────────────┐             ┌─────────────────────┐       │
│  │ movtoscaja          │             │ caja                │       │
│  │ ├─ folio (LLAVE)    │             │ ├─ folio (LLAVE)    │       │
│  │ ├─ fecha            │             │ ├─ fecha            │       │
│  │ └─ idtipomovtocaja=3│             │ └─ tipo_movimiento  │       │
│  └─────────────────────┘             │    ='CIERRE'        │       │
│           │                          └─────────────────────┘       │
│           ▼                                    │                    │
│  ┌─────────────────────┐             ┌─────────────────────┐       │
│  │ movtoscajadetalles  │             │ (campos directos)   │       │
│  │ ├─ idconcepto=9     │◄─PROPINAS──►│ ├─ propinas         │       │
│  │ └─ importe          │             │ ├─ tarjeta_credito  │       │
│  └─────────────────────┘             │ └─ tarjeta_debito   │       │
│                                      └─────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    SOLO LECTURA (SELECT)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         EDARSA HUB (MongoDB)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  EXISTENTE (NO MODIFICAR)           NUEVO (DESACOPLADO)             │
│  ┌─────────────────────┐            ┌─────────────────────┐        │
│  │ cuadres_cortes_z    │            │ propinas_control    │        │
│  │ ├─ folio_corte ─────┼───────────►│ ├─ folio_corte      │        │
│  │ ├─ sucursal_id      │            │ ├─ server_id        │        │
│  │ └─ propinas_pagadas │  VALIDACIÓN│ ├─ origen.propinas  │        │
│  └─────────────────────┘  CRUZADA   │ ├─ calculo.comision │        │
│                           ◄─────────┤ └─ cuadre.estado    │        │
│                                     └─────────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 2.2 Llaves de Relación

| Nivel | Llave | Descripción |
|-------|-------|-------------|
| **Corte** | `folio_corte` + `sucursal_id` + `server_id` | Identifica unívocamente un cierre de caja |
| **Período** | `fecha_corte` | Agrupa cortes del mismo día |
| **Fuente** | `system_type` | Distingue SoftRestaurant vs MPRO |

### Relación con Cuadres Existentes:

```javascript
// El módulo de propinas REFERENCIA (no modifica) cuadres_cortes_z
propinas_control.folio_corte === cuadres_cortes_z.corte_z.folio_corte
propinas_control.sucursal_id === cuadres_cortes_z.corte_z.sucursal_id
```

## 2.3 Garantías de No-Afectación

| Garantía | Mecanismo |
|----------|-----------|
| **No duplicación** | Índice único en `propinas_control` por folio+sucursal+server |
| **No rompe reportes** | El módulo NO escribe en SQL Server ni en `cuadres_cortes_z` |
| **No afecta cierres** | Solo LECTURA de tablas de corte. Cero escrituras. |

---

# 3. ORIGEN REAL DE LA PROPINA TPV (CRÍTICO)

## 3.A SOFTRESTAURANT

### 3.A.1 Tabla EXACTA para propina TPV

**Nivel Corte (RECOMENDADO para MVP):**
- Tabla: `movtoscajadetalles`
- Campo: `importe` donde `idconcepto = 9` (PropinasPagadas)
- Vínculo: `idmovtocaja` → `movtoscaja.idmovtocaja`

**Nivel Ticket (OPCIONAL para detalle):**
- Tabla: `cheques`
- Campo: `propina` (monto de propina por ticket)
- Vínculo: `idturno` → `turnos.idturno`

### 3.A.2 ¿Cómo identificar si es TPV?

**Problema:** En SoftRestaurant, el corte Z agrupa propinas totales. No hay campo directo que diga "propina pagada con tarjeta".

**Solución técnica (aproximación):**

```
PROPINAS_TPV = PROPINAS_TOTALES_CORTE × (VENTAS_TARJETA / VENTAS_TOTALES)
```

**Justificación:** Si el 70% de las ventas fueron con tarjeta, asumimos que ~70% de las propinas también fueron TPV.

**Alternativa exacta (si existe en el servidor):**
- Investigar tabla `chequespagos` para relacionar `folio` → `idformadepago`
- Si existe campo `propina` en `chequespagos`, se puede calcular propina por forma de pago

### 3.A.3 SQL Exacto - SoftRestaurant

```sql
-- ============================================================
-- QUERY 1: PROPINAS AGREGADAS POR CORTE (MVP)
-- Fuente: movtoscajadetalles
-- ============================================================
SELECT 
    mc.folio AS folio_corte,
    mc.fecha AS fecha_corte,
    
    -- Propinas totales del corte (concepto 9)
    ISNULL((
        SELECT SUM(d.importe) 
        FROM movtoscajadetalles d 
        WHERE d.idmovtocaja = mc.idmovtocaja 
          AND d.idconcepto = 9
    ), 0) AS propinas_totales,
    
    -- Ventas con tarjeta (conceptos 10, 11, 12)
    ISNULL((
        SELECT SUM(d.importe) 
        FROM movtoscajadetalles d 
        WHERE d.idmovtocaja = mc.idmovtocaja 
          AND d.idconcepto IN (10, 11, 12)
    ), 0) AS ventas_tarjeta,
    
    -- Ventas totales
    mc.saldo AS ventas_totales,
    
    -- Cálculo aproximado de propinas TPV
    CASE 
        WHEN mc.saldo > 0 THEN 
            ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                    WHERE d.idmovtocaja = mc.idmovtocaja AND d.idconcepto = 9), 0)
            * (ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                       WHERE d.idmovtocaja = mc.idmovtocaja AND d.idconcepto IN (10,11,12)), 0) 
               / mc.saldo)
        ELSE 0 
    END AS propinas_tpv_estimadas

FROM movtoscaja mc
WHERE mc.idtipomovtocaja = 3  -- Corte Z
  AND CAST(mc.fecha AS DATE) = @fecha
ORDER BY mc.fecha DESC
```

```sql
-- ============================================================
-- QUERY 2: PROPINAS POR TICKET (DETALLE OPCIONAL)
-- Fuente: cheques
-- ============================================================
SELECT 
    c.folio AS folio_cheque,
    t.apertura AS fecha_turno,
    c.propina AS propina_cheque,
    c.total AS total_cheque,
    c.idmesero,
    m.nombre AS mesero
FROM cheques c
INNER JOIN turnos t ON t.idturno = c.idturno
LEFT JOIN meseros m ON m.idmesero = c.idmesero
WHERE t.apertura >= @fecha_inicio
  AND t.apertura <= @fecha_fin + ' 23:59:59'
  AND c.cancelado = 0
  AND c.propina > 0
ORDER BY t.apertura DESC
```

```sql
-- ============================================================
-- QUERY 3: RESUMEN POR DÍA Y SUCURSAL
-- ============================================================
SELECT 
    CAST(mc.fecha AS DATE) AS fecha,
    COUNT(*) AS cortes,
    SUM(ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                WHERE d.idmovtocaja = mc.idmovtocaja AND d.idconcepto = 9), 0)) AS total_propinas,
    SUM(ISNULL((SELECT SUM(d.importe) FROM movtoscajadetalles d 
                WHERE d.idmovtocaja = mc.idmovtocaja AND d.idconcepto IN (10,11,12)), 0)) AS total_tarjeta,
    SUM(mc.saldo) AS total_ventas
FROM movtoscaja mc
WHERE mc.idtipomovtocaja = 3
  AND mc.fecha >= @fecha_inicio
  AND mc.fecha <= @fecha_fin
GROUP BY CAST(mc.fecha AS DATE)
ORDER BY CAST(mc.fecha AS DATE) DESC
```

---

## 3.B MPRO

### 3.B.1 Tabla EXACTA para propina TPV

**Nivel Corte:**
- Tabla: `caja`
- Campo: `propinas` (monto total de propinas del corte)
- Vínculo: `id_sucursal` → `sucursales.id_sucursal`

**Nivel Ticket:**
- Tabla: `Venta_Encabezado` o `Comanda`
- Campo: **⚠️ NO CONFIRMADO** - Requiere investigación en servidor real

### 3.B.2 ¿Cómo identificar si es TPV en MPRO?

**Campos disponibles en tabla `caja`:**
- `tarjeta_credito` - Ventas con tarjeta de crédito
- `tarjeta_debito` - Ventas con tarjeta de débito
- `propinas` - Total propinas del corte

**Cálculo de propinas TPV:**
```
PROPINAS_TPV = propinas × (tarjeta_credito + tarjeta_debito) / total_ventas
```

### 3.B.3 SQL Exacto - MPRO

```sql
-- ============================================================
-- QUERY 1: PROPINAS AGREGADAS POR CORTE (MVP)
-- Fuente: caja
-- ============================================================
SELECT 
    c.folio AS folio_corte,
    c.fecha AS fecha_corte,
    s.Sc_Cve_Sucursal AS sucursal_id,
    s.Sc_Descripcion AS sucursal_nombre,
    
    -- Propinas totales
    ISNULL(c.propinas, 0) AS propinas_totales,
    
    -- Ventas por forma de pago
    ISNULL(c.tarjeta_credito, 0) AS ventas_tc,
    ISNULL(c.tarjeta_debito, 0) AS ventas_td,
    ISNULL(c.efectivo, 0) AS ventas_efectivo,
    ISNULL(c.total_ventas, 0) AS ventas_totales,
    
    -- Propinas TPV estimadas
    CASE 
        WHEN ISNULL(c.total_ventas, 0) > 0 THEN 
            ISNULL(c.propinas, 0) * 
            (ISNULL(c.tarjeta_credito, 0) + ISNULL(c.tarjeta_debito, 0)) 
            / c.total_ventas
        ELSE 0 
    END AS propinas_tpv_estimadas

FROM caja c
INNER JOIN Sucursal s ON s.Sc_Cve_Sucursal = c.id_sucursal
WHERE c.tipo_movimiento = 'CIERRE'
  AND CAST(c.fecha AS DATE) = @fecha
ORDER BY c.fecha DESC
```

```sql
-- ============================================================
-- QUERY 2: RESUMEN POR DÍA Y SUCURSAL
-- ============================================================
SELECT 
    CAST(c.fecha AS DATE) AS fecha,
    s.Sc_Descripcion AS sucursal,
    COUNT(*) AS cortes,
    SUM(ISNULL(c.propinas, 0)) AS total_propinas,
    SUM(ISNULL(c.tarjeta_credito, 0) + ISNULL(c.tarjeta_debito, 0)) AS total_tarjeta,
    SUM(ISNULL(c.total_ventas, 0)) AS total_ventas
FROM caja c
INNER JOIN Sucursal s ON s.Sc_Cve_Sucursal = c.id_sucursal
WHERE c.tipo_movimiento = 'CIERRE'
  AND c.fecha >= @fecha_inicio
  AND c.fecha <= @fecha_fin
GROUP BY CAST(c.fecha AS DATE), s.Sc_Descripcion
ORDER BY CAST(c.fecha AS DATE) DESC, s.Sc_Descripcion
```

---

## 3.C HOMOLOGACIÓN ENTRE SISTEMAS

### 3.C.1 Estrategia de Homologación

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MODELO HOMOLOGADO                               │
│                  (Estructura común en propinas_control)             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Campo Homologado      │ SoftRestaurant        │ MPRO               │
│  ──────────────────────┼───────────────────────┼──────────────────  │
│  folio_corte           │ movtoscaja.folio      │ caja.folio         │
│  fecha_corte           │ movtoscaja.fecha      │ caja.fecha         │
│  sucursal_id           │ (server_name)         │ caja.id_sucursal   │
│  propinas_totales      │ concepto=9            │ caja.propinas      │
│  ventas_tarjeta        │ concepto IN(10,11,12) │ tc + td            │
│  ventas_totales        │ movtoscaja.saldo      │ caja.total_ventas  │
│  propinas_tpv          │ (calculado)           │ (calculado)        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.C.2 Campos Comunes para Consolidar

| Campo Homologado | Tipo | Descripción |
|------------------|------|-------------|
| `folio_corte` | String | Identificador del cierre de caja |
| `fecha_corte` | Date | Fecha del corte |
| `sucursal_id` | String | ID de sucursal normalizado |
| `sucursal_nombre` | String | Nombre legible |
| `system_type` | Enum | "SoftRestaurant" o "MPRO" |
| `propinas_totales` | Decimal | Propinas brutas del corte |
| `ventas_tarjeta` | Decimal | Ventas con TC/TD |
| `ventas_totales` | Decimal | Ventas totales |
| `propinas_tpv` | Decimal | **Calculado:** propinas × (tarjeta/total) |
| `comision_2pct` | Decimal | **Calculado:** propinas_tpv × 0.02 |

### 3.C.3 Evitar Diferencias Semánticas

| Riesgo | Mitigación |
|--------|-----------|
| SoftRestaurant no tiene `sucursal_id` | Usar `server_name` como identificador |
| MPRO puede tener múltiples sucursales por servidor | Usar `id_sucursal` del corte |
| Conceptos de corte varían | Mapear conceptos en `propinas_config` |
| Propina TPV no existe directamente | Calcular con fórmula proporción |

---

# 4. AISLAMIENTO DEL MÓDULO

## 4.1 Confirmación de Desacoplamiento Total

| Pregunta | Respuesta | Evidencia |
|----------|-----------|-----------|
| ¿Es 100% desacoplado? | **SÍ** | Solo crea colecciones nuevas en MongoDB |
| ¿Modifica tablas existentes? | **NO** | Cero escrituras en SQL Server |
| ¿Interfiere con ventas? | **NO** | Solo lectura de `movtoscaja`/`caja` |
| ¿Interfiere con cortes? | **NO** | Solo lectura, no modifica `cuadres_cortes_z` |
| ¿Interfiere con reportes? | **NO** | Es un módulo paralelo, no intersecta |

## 4.2 Diagrama de Aislamiento

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MÓDULOS EXISTENTES                              │
│                     (ZONA PROTEGIDA)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  Comercial  │  │  Tesorería  │  │   Finanzas  │                 │
│  │   (KPIs)    │  │  (Cortes Z) │  │    (CxP)    │                 │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘                 │
│         │                │                                          │
│    NO TOCAR         NO TOCAR                                        │
│         │                │                                          │
└─────────┼────────────────┼──────────────────────────────────────────┘
          │                │
          │   SOLO LECTURA │
          │    (REFERENCIA)│
          ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     MÓDULO NUEVO                                    │
│                   (ZONA AISLADA)                                    │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              modules/finanzas/propinas_tpv/                   │ │
│  │  ┌─────────────┐                                              │ │
│  │  │ routes.py   │ ← Endpoints nuevos /api/finanzas/propinas/* │ │
│  │  │ service.py  │ ← Lógica de cálculo y homologación          │ │
│  │  │ repository.py│ ← Queries SQL (SOLO SELECT)                │ │
│  │  │ models.py   │ ← Schemas Pydantic                          │ │
│  │  └─────────────┘                                              │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                     ESCRIBE SOLO EN                                 │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │           MongoDB (COLECCIONES NUEVAS)                        │ │
│  │  ├─ propinas_control   ← Registros + pagos + cuadres         │ │
│  │  └─ propinas_config    ← Configuración global                │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 5. MVP REAL SIMPLIFICADO

## 5.1 Alcance MVP (Mínimo Viable)

### INCLUYE:
1. **2 colecciones** únicamente (`propinas_control`, `propinas_config`)
2. **Lectura multi-sistema** desde SoftRestaurant Y MPRO
3. **Sincronización de propinas** por corte
4. **Cálculo automático** de comisión 2%
5. **Registro manual** de pago a meseros
6. **Estado de cuadre** (PENDIENTE → PAGADO → CUADRADO)
7. **Feature flag** para activar/desactivar

### NO INCLUYE (FASE 2):
- Detalle por mesero individual
- Validación cruzada con `cuadres_cortes_z`
- UI en frontend
- Reportes de auditoría
- Firma digital del mesero

## 5.2 Endpoints MVP

```
POST /api/finanzas/propinas/sincronizar
  Body: { fecha_inicio, fecha_fin, server_id? }
  Response: { registros_creados, errores_por_servidor }

GET /api/finanzas/propinas
  Query: fecha_inicio, fecha_fin, server_id?, sucursal_id?, estado?
  Response: { propinas: [...], totales: {...} }

PUT /api/finanzas/propinas/{id}/pago
  Body: { monto_pagado, fecha_pago, metodo, observaciones }
  Response: { cuadre actualizado }

GET /api/finanzas/propinas/config
PUT /api/finanzas/propinas/config  (solo admin)
```

## 5.3 Flujo MVP

```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  SYNC   │───►│  CALCULADO  │───►│   PAGADO    │───►│  CUADRADO   │
└─────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │               │                  │                  │
  Lectura SQL    Comisión 2%      Registro pago      Diferencia=0
  (Soft+MPRO)    calculada        manual             validada
```

## 5.4 Archivos MVP

```
backend/modules/finanzas/propinas_tpv/
├── __init__.py
├── models.py          # Pydantic: PropinasControl, PropinasConfig
├── repository.py      # Queries SQL para Soft Y MPRO
├── service.py         # Lógica de homologación y cálculo
└── routes.py          # 4 endpoints básicos
```

---

# 6. MATRIZ DE ORIGEN POR SUCURSAL

## 6.1 Matriz Completa

| Sucursal | Sistema | Servidor BD | Empresa | Fuente Propina TPV | Fuente Corte/Caja | Riesgos de Integración |
|----------|---------|-------------|---------|-------------------|-------------------|------------------------|
| **La Estelar** | SoftRestaurant | 187.188.198.241:51742 | Bordo | `movtoscajadetalles` concepto=9 | `movtoscaja` tipo=3 | Timeout en Preview (esperado) |
| **Cienfuegos** | SoftRestaurant | 187.188.198.241:51741 | Abordo | `movtoscajadetalles` concepto=9 | `movtoscaja` tipo=3 | Timeout en Preview (esperado) |
| **130° Mérida** | SoftRestaurant | 187.188.198.241:51743 | Abordo | `movtoscajadetalles` concepto=9 | `movtoscaja` tipo=3 | Timeout en Preview (esperado) |
| **Querétaro** | MPRO | 187.188.198.241:1433 | CENTRAL2020 | `caja.propinas` + proporcional TC/TD | `caja` tipo='CIERRE' | Firewall local, requiere VPN |
| **Origen** | MPRO | 187.188.198.241:1433 | CENTRAL2020 | `caja.propinas` + proporcional TC/TD | `caja` tipo='CIERRE' | Firewall local, requiere VPN |

## 6.2 Detalle por Sistema

### SoftRestaurant (3 Sucursales)

| Campo | Tabla | Descripción |
|-------|-------|-------------|
| `folio_corte` | movtoscaja.folio | Folio del corte Z |
| `fecha_corte` | movtoscaja.fecha | Fecha del cierre |
| `propinas_totales` | movtoscajadetalles.importe WHERE idconcepto=9 | Propinas pagadas |
| `ventas_tarjeta` | movtoscajadetalles.importe WHERE idconcepto IN (10,11,12) | Visa/MC/Amex |
| `ventas_totales` | movtoscaja.saldo | Venta total del corte |

### MPRO (2 Sucursales)

| Campo | Tabla | Descripción |
|-------|-------|-------------|
| `folio_corte` | caja.folio | Folio del corte |
| `fecha_corte` | caja.fecha | Fecha del cierre |
| `sucursal_id` | caja.id_sucursal | FK a Sucursal |
| `propinas_totales` | caja.propinas | Campo directo |
| `ventas_tarjeta` | caja.tarjeta_credito + caja.tarjeta_debito | Suma TC+TD |
| `ventas_totales` | caja.total_ventas | Venta total |

## 6.3 Riesgos por Sucursal

| Sucursal | Riesgo | Probabilidad | Impacto | Mitigación |
|----------|--------|--------------|---------|------------|
| La Estelar | Timeout SQL | Alta | Bajo | Fallback a estado "Sin datos" |
| Cienfuegos | Timeout SQL | Alta | Bajo | Fallback a estado "Sin datos" |
| 130° Mérida | Timeout SQL | Alta | Bajo | Fallback a estado "Sin datos" |
| Querétaro | Firewall VPN | Media | Medio | Reintento con backoff |
| Origen | Firewall VPN | Media | Medio | Reintento con backoff |
| **TODOS** | Propina TPV no exacta | Alta | Medio | Usar fórmula proporcional |

---

# 7. INFORMACIÓN ADICIONAL A VALIDAR

## 7.1 Validaciones SQL Requeridas (Antes de Implementar)

```sql
-- 1. Verificar existencia de tabla chequespagos en SoftRestaurant
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'chequespagos'

-- 2. Verificar estructura de tabla caja en MPRO
SELECT COLUMN_NAME, DATA_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'caja'
ORDER BY ORDINAL_POSITION

-- 3. Verificar catálogo de conceptos en SoftRestaurant
SELECT idconcepto, descripcion 
FROM conceptos 
ORDER BY idconcepto

-- 4. Verificar existencia de campo propinas en caja MPRO
SELECT COUNT(*) as existe
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'caja' AND COLUMN_NAME = 'propinas'
```

## 7.2 Preguntas de Negocio Pendientes

| # | Pregunta | Impacto en Diseño |
|---|----------|-------------------|
| Q1 | ¿El 2% es fijo o varía por sucursal? | Parametrizar en `propinas_config` |
| Q2 | ¿Se pagan propinas diario o semanal? | Definir período de cuadre |
| Q3 | ¿Se requiere firma del mesero? | Incluir campo opcional |
| Q4 | ¿Hay propinas compartidas entre meseros? | Agregar lógica de split |
| Q5 | ¿MPRO realmente tiene campo `propinas` en `caja`? | Validar en servidor real |

---

# 8. RESUMEN EJECUTIVO DE CAMBIOS

| Aspecto | Documento Original | Documento Corregido |
|---------|-------------------|---------------------|
| Colecciones | 4 | **2** |
| Sistemas soportados | Solo SoftRest (implícito) | **SoftRestaurant + MPRO explícito** |
| Origen propina TPV | No definido | **Fórmula proporcional documentada** |
| SQL exacto | No incluido | **Incluido para ambos sistemas** |
| Homologación | No definida | **Tabla de mapeo completa** |
| Matriz sucursales | No incluida | **5 sucursales documentadas** |
| MVP | 8-12 días | **Simplificado, 4-6 días** |

---

**FIN DE VALIDACIÓN TÉCNICA**

*Este documento debe revisarse junto con el CAB original antes de aprobar implementación.*
