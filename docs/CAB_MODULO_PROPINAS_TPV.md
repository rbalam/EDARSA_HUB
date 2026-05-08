# DOCUMENTO CAB - CONTROL Y CUADRE DE COMISION SOBRE PROPINAS TPV

**Versión:** 1.0  
**Fecha:** 14 de Abril de 2026  
**Autor:** Equipo de Arquitectura EDARSA HUB  
**Estado:** PROPUESTA EN REVISIÓN  
**Clasificación:** CAMBIO CONTROLADO - ALTA CRITICIDAD

---

## 1. RESUMEN EJECUTIVO

Este documento presenta el análisis arquitectónico y la propuesta controlada para implementar un nuevo módulo de **Control y Cuadre de Comisión sobre Propinas TPV (2%)** dentro de EDARSA HUB.

El objetivo es auditar que la empresa esté reteniendo correctamente el 2% de comisión sobre las propinas pagadas con Tarjeta de Crédito/Débito a través del TPV (Terminal Punto de Venta), sin modificar los sistemas fuente (SoftRestaurant y MPRO) ni afectar los módulos existentes de EDARSA HUB.

**Conclusión preliminar:** La implementación es factible como un módulo completamente desacoplado que consume datos operativos de solo lectura desde los sistemas fuente y almacena sus cálculos de auditoría exclusivamente en colecciones nuevas de MongoDB dentro de EDARSA HUB.

---

## 2. OBJETIVO DEL MÓDULO

### 2.1 Objetivo General
Proporcionar un sistema de control y auditoría que permita verificar que la comisión del 2% sobre propinas pagadas con tarjeta esté siendo correctamente retenida y cuadrada contra los depósitos bancarios.

### 2.2 Objetivos Específicos
1. Leer las propinas declaradas por turno/cheque desde SoftRestaurant y MPRO
2. Identificar las propinas pagadas con tarjeta (TPV) vs. efectivo
3. Calcular automáticamente el 2% de comisión a retener sobre propinas TPV
4. Permitir el registro manual del pago de propinas a meseros
5. Generar un cuadre diario/semanal de propinas vs. comisión vs. pagos
6. Detectar discrepancias entre lo que se debió retener y lo realmente retenido
7. Integrar con el módulo existente de Tesorería para validar depósitos

### 2.3 Regla de Negocio Principal
```
COMISIÓN_A_RETENER = PROPINAS_TPV × 0.02

Donde:
- PROPINAS_TPV = Propinas cobradas a través de Terminal Punto de Venta (tarjeta)
- La comisión del 2% cubre costos bancarios de procesamiento
- El 98% restante se paga al mesero en efectivo
```

---

## 3. ALCANCE

### 3.1 DENTRO DEL ALCANCE
- Lectura de propinas desde `cheques` (SoftRestaurant) y tablas equivalentes (MPRO)
- Cálculo automático de comisión del 2%
- Registro de pagos de propinas a meseros
- Cuadre de propinas por turno, día, semana
- Reportes de auditoría de propinas
- Integración visual con Tesorería existente

### 3.2 FUERA DEL ALCANCE
- Modificación de tablas en SoftRestaurant o MPRO
- Cambios al flujo de captura de propinas en el TPV
- Integración con nómina para pago automático
- Modificación de los Cortes Z existentes
- Cambios al módulo de Tesorería actual (solo extensión visual)

---

## 4. SUPUESTOS Y CRITERIOS DE DISEÑO

### 4.1 Supuestos Técnicos
| ID | Supuesto | Validación Requerida |
|----|----------|---------------------|
| S1 | La tabla `cheques` de SoftRestaurant contiene el campo `propina` con el monto de propina por ticket | Validar estructura de tabla |
| S2 | Las propinas en tarjeta se pueden identificar por la forma de pago del cheque | Confirmar lógica de formas de pago |
| S3 | MPRO tiene una estructura similar o equivalente para propinas | Investigar tablas MPRO |
| S4 | Los Cortes Z ya incluyen `propinas_pagadas` como dato agregado | Confirmado en código existente |
| S5 | La comisión del 2% es fija para todas las sucursales | Confirmar con negocio |

### 4.2 Criterios de Diseño
1. **DESACOPLAMIENTO TOTAL:** El módulo no puede depender de modificaciones a sistemas fuente
2. **SOLO LECTURA:** Todas las consultas a SQL Server son de solo lectura (SELECT)
3. **ALMACENAMIENTO LOCAL:** Todos los datos calculados se guardan en MongoDB
4. **IDEMPOTENCIA:** El recálculo de un período debe producir el mismo resultado
5. **TRAZABILIDAD:** Cada cálculo debe registrar su fuente y timestamp
6. **TOLERANCIA A FALLOS:** Si un servidor no está disponible, el sistema continúa con los demás

---

## 5. DIAGNÓSTICO DE ARQUITECTURA ACTUAL

### 5.1 Arquitectura General de EDARSA HUB

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EDARSA HUB                                   │
│                    (Base Cerebro Central)                            │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend React          │    FastAPI Backend                        │
│  ├─ TableroEjecutivo.js │    ├─ server.py (central)                 │
│  ├─ Servidores.js       │    ├─ modules/comercial/ (KPIs)           │
│  ├─ Tesoreria/ (UI)     │    ├─ modules/finanzas/tesoreria.py      │
│  └─ ...                  │    └─ modules/finanzas/cuentas_por_pagar │
├─────────────────────────────────────────────────────────────────────┤
│                         MongoDB                                      │
│  ├─ users, roles                                                    │
│  ├─ servers (catálogo de conexiones)                                │
│  ├─ server_sucursales_config (visibilidad)                          │
│  ├─ cuadres_cortes_z (tesorería existente)                          │
│  └─ [NUEVO] propinas_* (este módulo)                                │
└─────────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
   │ SoftRestaurant│  │ SoftRestaurant│  │     MPRO      │
   │  (Cienfuegos) │  │ (La Estelar)  │  │ (130° QRO)    │
   ├───────────────┤  ├───────────────┤  ├───────────────┤
   │ cheques       │  │ cheques       │  │ Venta         │
   │ turnos        │  │ turnos        │  │ Venta_Detalle │
   │ meseros       │  │ meseros       │  │ Caja          │
   │ formaspago    │  │ formaspago    │  │ Forma_Pago    │
   │ chequespagos  │  │ chequespagos  │  │ ...           │
   └───────────────┘  └───────────────┘  └───────────────┘
```

### 5.2 Flujo Actual de Datos de Propinas

**SoftRestaurant (Confirmado en código):**
```sql
-- Tabla cheques contiene propina por ticket
SELECT 
    cheques.folio,
    cheques.total,
    cheques.propina,        -- ← Campo de propina individual
    cheques.idmesero,
    cheques.idturno
FROM cheques
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE cheques.cancelado = 0
```

**En Cortes Z (Tesorería actual):**
```sql
-- Concepto 9 = PropinasPagadas (agregado por turno/corte)
SELECT SUM(d.importe) FROM movtoscajadetalles d 
WHERE d.idmovtocaja = mc.idmovtocaja AND d.idconcepto = 9
```

### 5.3 Estado de las Tablas Relevantes

| Sistema | Tabla | Campo Propina | Nivel | Confirmado |
|---------|-------|---------------|-------|------------|
| SoftRestaurant | `cheques` | `propina` | Por ticket | ✅ Sí |
| SoftRestaurant | `movtoscajadetalles` | concepto=9 | Por corte | ✅ Sí |
| SoftRestaurant | `chequespagos` | Por forma pago | Por ticket | ⚠️ A validar |
| MPRO | `Venta` / `Caja` | `propinas` | Por corte | ⚠️ A validar |

---

## 6. TABLAS EXISTENTES DE EDARSA HUB A REUTILIZAR

### 6.1 Colección: `servers`
**Uso:** Obtener conexiones a SoftRestaurant y MPRO
```javascript
{
  "id": "uuid",
  "name": "Cienfuegos",
  "host": "187.188.198.241",
  "port": 51741,
  "database": "Abordo",
  "system_type": "SoftRestaurant",  // o "MPRO"
  "visible_en_operaciones": true
}
```
**Reutilización:** El módulo de propinas usará esta colección para iterar sobre los servidores disponibles y conectarse a ellos.

### 6.2 Colección: `server_sucursales_config`
**Uso:** Filtrar sucursales visibles
```javascript
{
  "server_id": "uuid",
  "sucursal_origen_id": "CIENFUEGOS",
  "visible_en_operaciones": true
}
```
**Reutilización:** Para filtrar qué sucursales incluir en el cálculo de propinas.

### 6.3 Colección: `cuadres_cortes_z`
**Uso:** Referencia cruzada con propinas pagadas en el corte
```javascript
{
  "corte_z": {
    "folio_corte": "2889",
    "propinas_pagadas": 11725.20,  // ← Total de propinas del corte
    "sucursal_id": "CIENFUEGOS"
  }
}
```
**Reutilización:** El módulo de propinas puede cruzar sus cálculos con el total de propinas reportadas en el Corte Z para detectar discrepancias.

### 6.4 Módulo existente: `modules/finanzas/tesoreria.py`
**Uso:** Endpoints y lógica de Cortes Z
**Reutilización:** El módulo de propinas puede extender el UI de Tesorería agregando una pestaña de "Cuadre de Propinas" sin modificar la lógica existente.

---

## 7. INFORMACIÓN OPERATIVA QUE DEBE LEERSE DESDE SOFT/MPRO

### 7.1 Consultas Requeridas en SoftRestaurant

#### 7.1.1 Propinas por Cheque (Detalle)
```sql
SELECT 
    c.folio AS folio_cheque,
    c.propina AS monto_propina,
    c.total AS total_cheque,
    c.idmesero,
    m.nombre AS nombre_mesero,
    c.idturno,
    t.apertura AS fecha_turno,
    t.cierre AS cierre_turno
FROM cheques c
INNER JOIN turnos t ON t.idturno = c.idturno
LEFT JOIN meseros m ON m.idmesero = c.idmesero
WHERE c.cancelado = 0
  AND c.propina > 0
  AND t.apertura >= @fecha_inicio
  AND t.apertura <= @fecha_fin
ORDER BY t.apertura, c.folio
```

#### 7.1.2 Forma de Pago por Cheque (Para identificar TPV)
```sql
-- PENDIENTE DE VALIDAR: Estructura de chequespagos
SELECT 
    cp.folio,
    cp.idformadepago,
    fp.descripcion AS forma_pago,
    cp.importe,
    CASE 
        WHEN fp.descripcion LIKE '%TARJETA%' 
          OR fp.descripcion LIKE '%CREDITO%'
          OR fp.descripcion LIKE '%DEBITO%' THEN 1
        ELSE 0
    END AS es_tarjeta
FROM chequespagos cp
INNER JOIN formaspago fp ON fp.idformadepago = cp.idformadepago
WHERE cp.folio = @folio_cheque
```

#### 7.1.3 Propinas Agregadas por Corte (Validación)
```sql
SELECT 
    mc.folio AS folio_corte,
    mc.fecha AS fecha_corte,
    ISNULL((
        SELECT SUM(d.importe) 
        FROM movtoscajadetalles d 
        WHERE d.idmovtocaja = mc.idmovtocaja AND d.idconcepto = 9
    ), 0) AS propinas_pagadas_corte
FROM movtoscaja mc
WHERE mc.idtipomovtocaja = 3  -- Corte Z
  AND mc.fecha >= @fecha_inicio
  AND mc.fecha <= @fecha_fin
```

### 7.2 Consultas Requeridas en MPRO (A INVESTIGAR)

⚠️ **NOTA:** La estructura de propinas en MPRO requiere investigación adicional. Las tablas identificadas son:

| Tabla | Descripción Probable |
|-------|---------------------|
| `Venta` | Encabezado de venta (equivalente a cheques) |
| `Venta_Detalle` | Detalle de productos |
| `Forma_Pago` | Catálogo de formas de pago |
| `Caja` | Control de caja/cortes |
| `Empleado` / `Mesero` | Catálogo de empleados |

**Consulta preliminar a ejecutar:**
```sql
-- Identificar columnas de propina en MPRO
SELECT COLUMN_NAME, TABLE_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%propina%' OR COLUMN_NAME LIKE '%tip%'
```

---

## 8. MÓDULOS POTENCIALMENTE AFECTADOS

| Módulo | Archivo | Tipo de Impacto | Descripción |
|--------|---------|-----------------|-------------|
| Tesorería | `tesoreria.py` | **NINGUNO** | Solo extensión visual (pestaña nueva) |
| Comercial | `comercial/routes.py` | **NINGUNO** | Consultas de propina ya existentes son independientes |
| Servidores | `Servidores.js` | **NINGUNO** | La configuración de sucursales se reutiliza |
| Dashboard | `TableroEjecutivo.js` | **NINGUNO** | Los KPIs de ventas no cambian |
| Finanzas | `cuentas_por_pagar.py` | **NINGUNO** | Flujo de CxP no relacionado |

### Diagrama de No-Impacto

```
┌────────────────────────────────────────────────────────────────┐
│                    MÓDULOS EXISTENTES                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │Comercial │ │ Finanzas │ │Tesorería │ │ Tablero Ejecutivo│  │
│  │  (KPIs)  │ │  (CxP)   │ │(Cortes Z)│ │    (Dashboard)   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
│       │            │            │               │              │
│       │      NO MODIFICAR      │               │              │
│       └────────────┴────────────┴───────────────┘              │
└────────────────────────────────────────────────────────────────┘
                              │
                    SOLO LECTURA DE DATOS
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│               NUEVO MÓDULO (DESACOPLADO)                       │
│  ┌───────────────────────────────────────────────────────┐    │
│  │           modules/finanzas/propinas_tpv/              │    │
│  │  ├─ routes.py      (API endpoints nuevos)             │    │
│  │  ├─ service.py     (Lógica de cálculo)                │    │
│  │  ├─ repository.py  (Consultas SQL solo lectura)       │    │
│  │  └─ models.py      (Pydantic schemas)                 │    │
│  └───────────────────────────────────────────────────────┘    │
│                              │                                 │
│                     ESCRIBE SOLO EN                            │
│                              ▼                                 │
│  ┌───────────────────────────────────────────────────────┐    │
│  │              MongoDB (Colecciones Nuevas)              │    │
│  │  ├─ propinas_registro     (Propinas calculadas)       │    │
│  │  ├─ propinas_comisiones   (Comisiones 2%)             │    │
│  │  ├─ propinas_pagos        (Pagos a meseros)           │    │
│  │  └─ propinas_cuadres      (Cuadres diarios)           │    │
│  └───────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

---

## 9. RIESGOS TÉCNICOS

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| RT1 | La tabla `chequespagos` no existe o tiene estructura diferente | Media | Alto | Investigar estructura antes de implementar. Fallback: usar solo propina agregada del Corte Z |
| RT2 | MPRO no tiene campo de propina por ticket | Media | Medio | Usar propinas agregadas del corte como alternativa |
| RT3 | Timeout en consultas SQL por volumen de datos | Media | Medio | Implementar paginación y caché en MongoDB |
| RT4 | Formas de pago no identificables como "tarjeta" | Media | Alto | Crear catálogo configurable de mapeo de formas de pago |
| RT5 | Inconsistencia entre propinas por ticket vs. propinas del corte | Baja | Medio | Implementar validación cruzada y alertas |
| RT6 | Duplicación de registros por re-sincronización | Baja | Medio | Usar folio+fecha+servidor como clave única |

---

## 10. RIESGOS OPERATIVOS

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| RO1 | Usuarios no entienden el flujo de cuadre | Media | Medio | Documentación y capacitación |
| RO2 | Propinas en efectivo mezcladas con propinas TPV | Alta | Alto | UI clara para diferenciar fuentes |
| RO3 | Descuadres generan disputas con meseros | Media | Alto | Auditoría trazable con evidencia |
| RO4 | Datos históricos no disponibles | Media | Bajo | El módulo comienza a calcular desde fecha de implementación |
| RO5 | Cambios en la comisión del 2% | Baja | Bajo | Parametrizar porcentaje de comisión |

---

## 11. RIESGOS DE REGRESIÓN

| ID | Componente | Riesgo de Regresión | Mitigación |
|----|------------|---------------------|------------|
| RR1 | Tesorería (Cortes Z) | **NULO** - No se modifica código | Solo extensión visual |
| RR2 | Tablero Ejecutivo | **NULO** - No se modifica código | Las propinas ya se consultan independientemente |
| RR3 | Comercial (KPIs) | **NULO** - No se modifica código | Las consultas de `cheques.propina` no cambian |
| RR4 | Servidores SQL | **NULO** - Solo lectura | No hay INSERT/UPDATE/DELETE a sistemas fuente |
| RR5 | Autenticación | **NULO** - Usa auth existente | Reutiliza `get_current_user` |

---

## 12. QUÉ NO SE DEBE TOCAR

### 12.1 Archivos PROHIBIDOS de modificar
```
❌ backend/modules/finanzas/tesoreria.py         (Solo agregar import al final)
❌ backend/modules/finanzas/repository_cortes_z.py
❌ backend/modules/finanzas/repository_cuadres_z.py  
❌ backend/modules/finanzas/tesoreria_models.py
❌ backend/modules/comercial/service.py
❌ backend/modules/comercial/routes.py
❌ backend/catalogo/consultas_softrestaurant.py
❌ backend/catalogo/consultas_mpro.py
❌ frontend/src/pages/TableroEjecutivo.js
```

### 12.2 Tablas SQL PROHIBIDAS de modificar
```
❌ SoftRestaurant: cheques, turnos, meseros, formaspago, chequespagos, movtoscaja
❌ MPRO: Venta, Venta_Detalle, Caja, Forma_Pago, Empleado
```

### 12.3 Colecciones MongoDB PROHIBIDAS de modificar estructura
```
❌ servers
❌ users
❌ roles  
❌ cuadres_cortes_z
❌ server_sucursales_config
```

---

## 13. PROPUESTA FUNCIONAL CONTROLADA

### 13.1 Flujo de Usuario Propuesto

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. SINCRONIZACIÓN DE PROPINAS                                      │
│  ────────────────────────────────────────────────────────────────── │
│  Usuario: Administrador / Tesorero                                  │
│  Acción: Click en "Sincronizar Propinas del Día"                    │
│  Sistema:                                                            │
│    1. Lee propinas de cheques del día de cada servidor              │
│    2. Identifica forma de pago (efectivo vs tarjeta)                │
│    3. Calcula comisión 2% sobre propinas TPV                        │
│    4. Guarda en MongoDB colección propinas_registro                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. VISTA DE PROPINAS POR PERÍODO                                   │
│  ────────────────────────────────────────────────────────────────── │
│  Usuario: Tesorero / Auditor                                        │
│  Vista:                                                              │
│    ┌────────────┬────────────┬────────────┬────────────┬──────────┐ │
│    │ Fecha      │ Mesero     │ Propina    │ Comisión   │ A Pagar  │ │
│    │            │            │ TPV        │ (2%)       │ (98%)    │ │
│    ├────────────┼────────────┼────────────┼────────────┼──────────┤ │
│    │ 2026-04-14 │ Juan Pérez │ $1,500.00  │ $30.00     │$1,470.00 │ │
│    │ 2026-04-14 │ María López│ $2,100.00  │ $42.00     │$2,058.00 │ │
│    └────────────┴────────────┴────────────┴────────────┴──────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. REGISTRO DE PAGO DE PROPINAS                                    │
│  ────────────────────────────────────────────────────────────────── │
│  Usuario: Tesorero / Cajero                                         │
│  Acción: Registra pago de propinas a cada mesero                    │
│  Campos:                                                             │
│    - Fecha de pago                                                  │
│    - Mesero                                                         │
│    - Monto pagado (debe ser 98% de propina TPV)                     │
│    - Firma/Confirmación (opcional: foto)                            │
│  Sistema:                                                            │
│    1. Valida que monto sea correcto                                 │
│    2. Registra en propinas_pagos                                    │
│    3. Marca propinas como "PAGADAS"                                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. CUADRE DE PROPINAS                                              │
│  ────────────────────────────────────────────────────────────────── │
│  Usuario: Auditor / Tesorero                                        │
│  Acción: Genera cuadre del período                                  │
│  Cálculos:                                                           │
│    A. Total Propinas TPV del período           = $15,000.00         │
│    B. Comisión 2% a retener                    = $   300.00         │
│    C. Monto a pagar a meseros (A-B)            = $14,700.00         │
│    D. Total pagado a meseros                   = $14,700.00         │
│    E. Diferencia (C-D)                         = $     0.00 ✅      │
│                                                                      │
│  Validación cruzada con Corte Z:                                    │
│    F. Propinas pagadas según Corte Z           = $15,000.00         │
│    G. Propinas TPV calculadas (A)              = $15,000.00         │
│    H. Diferencia (F-G)                         = $     0.00 ✅      │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.2 Estados del Cuadre de Propinas

```
┌──────────────┐    Sincronizar    ┌──────────────┐
│  PENDIENTE   │ ───────────────▶  │  CALCULADO   │
└──────────────┘                   └──────────────┘
                                          │
                           Registrar Pagos│
                                          ▼
                                   ┌──────────────┐
                                   │  EN_PROCESO  │
                                   └──────────────┘
                                          │
                            Validar Cuadre│
                     ┌────────────────────┼────────────────────┐
                     ▼                    ▼                    ▼
             ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
             │   CUADRADO   │     │   DESCUADRE  │     │  CON_AJUSTE  │
             │     ✅       │     │      ⚠️       │     │      📝      │
             └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 14. PROPUESTA DE TABLAS NUEVAS ESTRICTAMENTE NECESARIAS

### 14.1 Justificación de Nuevas Colecciones

| Colección | ¿Por qué es necesaria? | ¿Puede reutilizarse algo existente? |
|-----------|------------------------|-------------------------------------|
| `propinas_registro` | Almacenar cálculo de propinas TPV y comisiones | No. No existe estructura similar |
| `propinas_pagos` | Registrar pagos a meseros con trazabilidad | No. Los pagos requieren su propio registro |
| `propinas_cuadres` | Consolidar cuadres por período | No. Es un concepto nuevo |
| `propinas_config` | Configuración (% comisión, mapeo formas pago) | No. Configuración específica del módulo |

### 14.2 Esquema: `propinas_registro`

```javascript
{
  "_id": ObjectId,
  "id": "UUID",
  
  // Origen
  "server_id": "uuid-servidor",
  "server_name": "Cienfuegos",
  "system_type": "SoftRestaurant",
  "sucursal_id": "CIENFUEGOS",
  
  // Referencia al ticket
  "folio_cheque": "12345",
  "folio_turno": "T001",
  "folio_corte": "2889",  // Para validación cruzada
  "fecha_turno": ISODate("2026-04-14T00:00:00Z"),
  
  // Mesero
  "mesero_id": "M001",
  "mesero_nombre": "Juan Pérez",
  
  // Montos
  "propina_total": 150.00,      // Propina del cheque
  "propina_efectivo": 50.00,    // Parte en efectivo
  "propina_tpv": 100.00,        // Parte en tarjeta (sujeta a comisión)
  
  // Cálculos
  "porcentaje_comision": 0.02,  // 2%
  "comision_calculada": 2.00,   // propina_tpv * 0.02
  "monto_a_pagar_mesero": 98.00, // propina_tpv * 0.98
  
  // Estado
  "estado": "PENDIENTE_PAGO",  // PENDIENTE_PAGO, PAGADO, AJUSTADO
  "pago_id": null,             // FK a propinas_pagos cuando se pague
  
  // Metadata
  "fecha_sincronizacion": ISODate("2026-04-14T08:00:00Z"),
  "sincronizado_por": "admin@edarsa.com.mx",
  "created_at": ISODate,
  "updated_at": ISODate
}

// Índices requeridos:
// { "server_id": 1, "fecha_turno": 1 }
// { "folio_cheque": 1, "server_id": 1 } // Clave única
// { "mesero_id": 1, "fecha_turno": 1 }
// { "estado": 1 }
```

### 14.3 Esquema: `propinas_pagos`

```javascript
{
  "_id": ObjectId,
  "id": "UUID",
  
  // Referencia
  "server_id": "uuid-servidor",
  "sucursal_id": "CIENFUEGOS",
  
  // Mesero
  "mesero_id": "M001",
  "mesero_nombre": "Juan Pérez",
  
  // Período
  "fecha_inicio": ISODate("2026-04-14T00:00:00Z"),
  "fecha_fin": ISODate("2026-04-14T23:59:59Z"),
  
  // Montos
  "total_propinas_tpv": 500.00,
  "total_comision_retenida": 10.00,
  "monto_a_pagar": 490.00,
  "monto_pagado": 490.00,
  
  // Pago
  "fecha_pago": ISODate("2026-04-15T10:00:00Z"),
  "registrado_por": "tesorero@edarsa.com.mx",
  "metodo_pago": "EFECTIVO",  // EFECTIVO, TRANSFERENCIA
  
  // Evidencia (opcional)
  "firma_mesero": null,       // Base64 de firma digital
  "foto_recibo": null,        // URL a archivo
  
  // Propinas incluidas en este pago
  "propinas_ids": ["uuid1", "uuid2", "uuid3"],
  
  // Metadata
  "observaciones": "",
  "created_at": ISODate,
  "updated_at": ISODate
}

// Índices:
// { "server_id": 1, "fecha_pago": 1 }
// { "mesero_id": 1, "fecha_pago": 1 }
```

### 14.4 Esquema: `propinas_cuadres`

```javascript
{
  "_id": ObjectId,
  "id": "UUID",
  
  // Período
  "fecha_inicio": ISODate("2026-04-14T00:00:00Z"),
  "fecha_fin": ISODate("2026-04-14T23:59:59Z"),
  "tipo_periodo": "DIARIO",  // DIARIO, SEMANAL, MENSUAL
  
  // Filtros
  "server_id": "uuid-servidor",  // Opcional, null = todos
  "sucursal_id": "CIENFUEGOS",   // Opcional, null = todas
  
  // Totales calculados
  "total_propinas": 15000.00,
  "total_propinas_efectivo": 5000.00,
  "total_propinas_tpv": 10000.00,
  "total_comision_retenida": 200.00,
  "total_monto_a_pagar": 9800.00,
  "total_pagado": 9800.00,
  
  // Validación cruzada con Corte Z
  "propinas_corte_z": 15000.00,      // Desde cuadres_cortes_z
  "diferencia_vs_corte_z": 0.00,
  "cortes_z_incluidos": ["2889", "2890"],
  
  // Estado
  "estado": "CUADRADO",  // PENDIENTE, EN_PROCESO, CUADRADO, DESCUADRE, CON_AJUSTE
  "diferencia_final": 0.00,
  
  // Desglose por mesero
  "detalle_meseros": [
    {
      "mesero_id": "M001",
      "mesero_nombre": "Juan Pérez",
      "propinas_tpv": 2500.00,
      "comision": 50.00,
      "a_pagar": 2450.00,
      "pagado": 2450.00,
      "estado": "CUADRADO"
    }
  ],
  
  // Metadata
  "generado_por": "auditor@edarsa.com.mx",
  "fecha_generacion": ISODate,
  "observaciones": "",
  "ajustes": [],  // Array de ajustes manuales si los hubiera
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### 14.5 Esquema: `propinas_config`

```javascript
{
  "_id": ObjectId,
  "id": "config_global",  // Singleton
  
  // Porcentaje de comisión (parametrizable)
  "porcentaje_comision": 0.02,  // 2%
  
  // Mapeo de formas de pago a "tarjeta"
  "formas_pago_tpv": {
    "SoftRestaurant": [
      { "id": 10, "descripcion": "VISA" },
      { "id": 11, "descripcion": "MASTERCARD" },
      { "id": 12, "descripcion": "AMEX" }
    ],
    "MPRO": [
      { "codigo": "TC", "descripcion": "Tarjeta Crédito" },
      { "codigo": "TD", "descripcion": "Tarjeta Débito" }
    ]
  },
  
  // Configuración de validaciones
  "tolerancia_descuadre": 5.00,  // $5 de tolerancia
  "dias_para_cuadrar": 1,        // Días hábiles para completar cuadre
  
  // Metadata
  "updated_at": ISODate,
  "updated_by": "admin@edarsa.com.mx"
}
```

---

## 15. RELACIONES PROPUESTAS

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MODELO DE RELACIONES                             │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌──────────────┐       ┌──────────────────────┐
│   servers    │◄──────│  propinas_   │──────►│   cuadres_cortes_z   │
│  (existente) │ 1:N   │  registro    │  N:1  │     (existente)      │
└──────────────┘       └──────────────┘       └──────────────────────┘
                              │
                              │ N:1
                              ▼
                       ┌──────────────┐
                       │  propinas_   │
                       │    pagos     │
                       └──────────────┘
                              │
                              │ N:1
                              ▼
                       ┌──────────────┐
                       │  propinas_   │
                       │   cuadres    │
                       └──────────────┘


Relaciones:
1. propinas_registro.server_id → servers.id (lectura)
2. propinas_registro.folio_corte → cuadres_cortes_z.corte_z.folio_corte (validación)
3. propinas_registro.pago_id → propinas_pagos.id
4. propinas_cuadres contiene agregados de propinas_registro y propinas_pagos
```

---

## 16. FLUJO OPERATIVO PROPUESTO

### 16.1 Diagrama de Secuencia: Sincronización de Propinas

```
Usuario        Frontend        Backend           MongoDB         SQL Server
   │               │              │                 │                │
   │  Click Sync   │              │                 │                │
   │──────────────►│   POST       │                 │                │
   │               │ /propinas/   │                 │                │
   │               │ sincronizar  │                 │                │
   │               │─────────────►│                 │                │
   │               │              │  Get servers    │                │
   │               │              │────────────────►│                │
   │               │              │◄────────────────│                │
   │               │              │                 │                │
   │               │              │  For each server:                │
   │               │              │─────────────────────────────────►│
   │               │              │  SELECT propinas FROM cheques    │
   │               │              │◄─────────────────────────────────│
   │               │              │                 │                │
   │               │              │  Calcular       │                │
   │               │              │  comisiones     │                │
   │               │              │                 │                │
   │               │              │  Guardar en     │                │
   │               │              │  propinas_reg   │                │
   │               │              │────────────────►│                │
   │               │              │◄────────────────│                │
   │               │              │                 │                │
   │               │◄─────────────│ { success,      │                │
   │◄──────────────│              │   registros }   │                │
   │  Mostrar      │              │                 │                │
   │  resultado    │              │                 │                │
```

### 16.2 Diagrama de Secuencia: Pago de Propinas

```
Tesorero       Frontend        Backend           MongoDB
   │               │              │                 │
   │  Selecciona   │              │                 │
   │  mesero/fecha │              │                 │
   │──────────────►│   GET        │                 │
   │               │ /propinas/   │                 │
   │               │ pendientes   │                 │
   │               │─────────────►│  Query          │
   │               │              │────────────────►│
   │               │              │◄────────────────│
   │               │◄─────────────│                 │
   │◄──────────────│  Lista de    │                 │
   │               │  propinas    │                 │
   │               │              │                 │
   │  Registra     │              │                 │
   │  pago         │              │                 │
   │──────────────►│   POST       │                 │
   │               │ /propinas/   │                 │
   │               │ pagos        │                 │
   │               │─────────────►│  Validar monto  │
   │               │              │                 │
   │               │              │  Crear pago     │
   │               │              │────────────────►│
   │               │              │◄────────────────│
   │               │              │  Actualizar     │
   │               │              │  estado         │
   │               │              │  registros      │
   │               │              │────────────────►│
   │               │              │◄────────────────│
   │               │◄─────────────│                 │
   │◄──────────────│  { success } │                 │
```

---

## 17. VALIDACIONES DE NEGOCIO

### 17.1 Validaciones en Sincronización
| Validación | Descripción | Acción si falla |
|------------|-------------|-----------------|
| V1 | El servidor debe estar activo y visible | Omitir servidor |
| V2 | La propina debe ser > 0 | Omitir registro |
| V3 | No debe existir registro duplicado (folio+servidor) | Actualizar existente |
| V4 | La forma de pago debe estar mapeada | Marcar como "FORMA_PAGO_DESCONOCIDA" |

### 17.2 Validaciones en Pago
| Validación | Descripción | Acción si falla |
|------------|-------------|-----------------|
| V5 | El monto pagado debe ser igual al 98% de propinas TPV | Warning, permitir ajuste |
| V6 | No debe existir pago duplicado para mismo período/mesero | Rechazar |
| V7 | La fecha de pago no puede ser anterior a la fecha de propina | Rechazar |

### 17.3 Validaciones en Cuadre
| Validación | Descripción | Acción si falla |
|------------|-------------|-----------------|
| V8 | Todas las propinas del período deben tener pago registrado | Estado = EN_PROCESO |
| V9 | La suma de comisiones debe ser igual a propinas_tpv × 2% | Marcar discrepancia |
| V10 | Las propinas calculadas deben coincidir con Corte Z (±tolerancia) | Marcar para revisión |

---

## 18. ESTATUS DEL PROCESO

| Etapa | Estado | Descripción |
|-------|--------|-------------|
| Análisis de Impacto | ✅ COMPLETO | Este documento |
| Validación de tablas SQL | ⏳ PENDIENTE | Ejecutar queries de investigación |
| Aprobación de diseño | ⏳ PENDIENTE | Requiere OK del usuario |
| Desarrollo FASE 1 | ⏳ NO INICIADO | Backend + endpoints básicos |
| Desarrollo FASE 2 | ⏳ NO INICIADO | Frontend + integración Tesorería |
| Testing | ⏳ NO INICIADO | Pruebas unitarias y de integración |
| Despliegue | ⏳ NO INICIADO | Producción controlada |

---

## 19. ESTRATEGIA DE NO REGRESIÓN

### 19.1 Principios
1. **CERO modificaciones** a archivos existentes del módulo Finanzas/Tesorería
2. **SOLO nuevos archivos** dentro de `modules/finanzas/propinas_tpv/`
3. **SOLO nuevas colecciones** en MongoDB con prefijo `propinas_`
4. **SOLO lectura** de SQL Server (ningún INSERT/UPDATE/DELETE)
5. **Feature flag** para activar/desactivar el módulo sin afectar otros

### 19.2 Checklist Pre-Implementación
- [ ] Verificar que todos los tests existentes pasen antes de empezar
- [ ] Crear rama Git dedicada: `feature/propinas-tpv`
- [ ] No hacer merge a main hasta pruebas completas
- [ ] Implementar feature flag en MongoDB para activar módulo

### 19.3 Checklist Post-Implementación
- [ ] Ejecutar suite completa de tests (125 tests legacy + nuevos)
- [ ] Verificar que Tesorería existente funciona igual
- [ ] Verificar que Tablero Ejecutivo no cambió
- [ ] Verificar que Comercial no cambió
- [ ] Probar con feature flag en OFF (sistema debe comportarse igual)
- [ ] Probar con feature flag en ON (nuevo módulo visible)

---

## 20. PLAN DE PRUEBAS

### 20.1 Pruebas Unitarias (Backend)
| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| PU1 | Calcular comisión 2% sobre $100.00 | $2.00 |
| PU2 | Calcular monto a pagar sobre $100.00 | $98.00 |
| PU3 | Identificar forma de pago "VISA" como tarjeta | True |
| PU4 | Identificar forma de pago "EFECTIVO" como no-tarjeta | True |
| PU5 | Evitar duplicado de registro por folio | Error o Update |
| PU6 | Validar que pago sea exactamente 98% | Pass/Warning |

### 20.2 Pruebas de Integración
| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| PI1 | Sincronizar propinas de Cienfuegos | Registros creados en MongoDB |
| PI2 | Sincronizar propinas de MPRO | Registros creados (si hay datos) |
| PI3 | Registrar pago a mesero | Propinas marcadas como PAGADAS |
| PI4 | Generar cuadre diario | Cuadre con estado calculado |
| PI5 | Cruzar con Corte Z existente | Diferencia calculada |

### 20.3 Pruebas de No Regresión
| ID | Prueba | Resultado Esperado |
|----|--------|-------------------|
| PR1 | Listar Cortes Z (Tesorería) | Sin cambios en respuesta |
| PR2 | KPIs del Tablero Ejecutivo | Sin cambios en respuesta |
| PR3 | Dashboard Comercial | Sin cambios en respuesta |
| PR4 | Login/Autenticación | Sin cambios |
| PR5 | 125 tests legacy | Todos pasan |

---

## 21. PLAN DE ROLLBACK CONCEPTUAL

### 21.1 Escenario: Error crítico post-despliegue

**Paso 1: Desactivar feature flag**
```javascript
// En MongoDB
db.propinas_config.updateOne(
  { id: "config_global" },
  { $set: { "modulo_activo": false } }
)
```

**Paso 2: El sistema continúa operando sin el módulo**
- Tesorería funciona normal
- Tablero Ejecutivo funciona normal
- Comercial funciona normal

**Paso 3: Si es necesario, eliminar colecciones**
```javascript
// SOLO si se requiere rollback completo
db.propinas_registro.drop()
db.propinas_pagos.drop()
db.propinas_cuadres.drop()
// NO eliminar propinas_config (contiene feature flag)
```

**Paso 4: Revertir código (Git)**
```bash
git revert HEAD~N  # Donde N = commits del feature
```

### 21.2 Tiempo estimado de rollback
- Feature flag OFF: **< 1 minuto**
- Rollback de datos: **< 5 minutos**
- Rollback de código: **< 15 minutos**

---

## 22. RECOMENDACIÓN DE FASE 1

### 22.1 Alcance de FASE 1 (MVP)

**Incluye:**
1. Creación de estructura de archivos en `modules/finanzas/propinas_tpv/`
2. Modelo de datos en MongoDB (4 colecciones)
3. Endpoint de sincronización de propinas (solo SoftRestaurant inicialmente)
4. Endpoint de listado de propinas por período
5. Cálculo automático de comisión 2%
6. Feature flag para activar/desactivar

**No incluye (FASE 2):**
- Registro de pagos
- Cuadre automático
- UI en frontend
- Integración visual con Tesorería
- Soporte para MPRO

### 22.2 Entregables FASE 1
```
backend/modules/finanzas/propinas_tpv/
├── __init__.py
├── models.py          # Pydantic schemas
├── repository.py      # Consultas SQL (solo lectura)
├── service.py         # Lógica de negocio
└── routes.py          # API endpoints
```

### 22.3 Endpoints FASE 1
```
POST /api/finanzas/propinas/sincronizar
  Body: { fecha_inicio, fecha_fin, server_id? }
  Response: { registros_creados, errores }

GET /api/finanzas/propinas
  Query: fecha_inicio, fecha_fin, server_id?, mesero_id?, estado?
  Response: { propinas: [...], total, resumen }

GET /api/finanzas/propinas/resumen
  Query: fecha_inicio, fecha_fin
  Response: { total_propinas_tpv, total_comision, total_a_pagar }

GET /api/finanzas/propinas/config
  Response: { porcentaje_comision, formas_pago_tpv }

PUT /api/finanzas/propinas/config  (solo admin)
  Body: { porcentaje_comision?, formas_pago_tpv? }
```

---

## 23. RECOMENDACIÓN DE FASE 2

### 23.1 Alcance de FASE 2

**Incluye:**
1. Endpoint de registro de pagos a meseros
2. Endpoint de generación de cuadres
3. Validación cruzada con Cortes Z existentes
4. UI en frontend (pestaña en Tesorería)
5. Reportes de auditoría
6. Soporte para MPRO

### 23.2 Estimación de Esfuerzo

| Tarea | Estimación |
|-------|-----------|
| FASE 1 - Backend MVP | 2-3 días |
| FASE 1 - Testing | 1 día |
| FASE 2 - Pagos y Cuadres | 2-3 días |
| FASE 2 - Frontend | 2-3 días |
| FASE 2 - Testing | 1-2 días |
| **Total estimado** | **8-12 días** |

---

## 24. INFORMACIÓN ADICIONAL RECOMENDABLE A VALIDAR ANTES DE IMPLEMENTAR

### 24.1 Validaciones SQL Críticas

**1. Estructura de `chequespagos` en SoftRestaurant:**
```sql
-- Ejecutar en cada servidor SoftRestaurant
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'chequespagos'
ORDER BY ORDINAL_POSITION
```

**2. Catálogo de formas de pago:**
```sql
-- Ejecutar en cada servidor SoftRestaurant
SELECT idformadepago, descripcion
FROM formaspago
ORDER BY idformadepago
```

**3. Estructura de propinas en MPRO:**
```sql
-- Ejecutar en servidores MPRO
SELECT TABLE_NAME, COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%propina%' 
   OR COLUMN_NAME LIKE '%tip%'
```

### 24.2 Preguntas de Negocio Pendientes

| # | Pregunta | Impacto |
|---|----------|---------|
| Q1 | ¿El 2% de comisión es fijo para todas las sucursales? | Diseño de `propinas_config` |
| Q2 | ¿Se debe manejar propinas en efectivo también o solo TPV? | Alcance de sincronización |
| Q3 | ¿Cuál es la tolerancia aceptable de descuadre? | Validación de cuadres |
| Q4 | ¿Se requiere firma digital del mesero al recibir pago? | Complejidad de UI |
| Q5 | ¿Hay propinas compartidas entre meseros? | Lógica de distribución |
| Q6 | ¿Se pagan propinas diariamente, semanalmente, o por quincena? | Diseño de períodos |

### 24.3 Datos de Prueba Requeridos

Para validar la implementación se necesita:
1. Acceso a servidor SoftRestaurant con datos reales de propinas
2. Al menos 1 Corte Z con propinas_pagadas > 0
3. Lista de formas de pago activas
4. Nombres/IDs de meseros activos

---

## FIRMAS DE APROBACIÓN

| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| Product Owner | _________________ | _______ | _______ |
| Tech Lead | _________________ | _______ | _______ |
| Tesorero | _________________ | _______ | _______ |
| Auditor | _________________ | _______ | _______ |

---

**FIN DEL DOCUMENTO CAB**

*Este documento debe ser aprobado antes de proceder con cualquier implementación.*
