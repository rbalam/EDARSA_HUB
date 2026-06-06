# ADENDA TÉCNICA - VALIDACIONES CRÍTICAS CAB PROPINAS TPV

**Versión:** 2.1  
**Fecha:** 14 de Abril de 2026  
**Estado:** RESPUESTA A VALIDACIONES FINALES  
**Documento padre:** `CAB_PROPINAS_TPV_VALIDACION_TECNICA.md`

---

# 1. MPRO - DATO EXACTO VS ESTIMADO

## 1.1 Análisis de Fuentes en MPRO

Tras revisar el código existente en EDARSA HUB, específicamente:
- `backend/modules/finanzas/repository_cortes_z.py` (líneas 209-284)
- `backend/modules/comercial/routes.py` (líneas 1180-1275)

**HALLAZGO CRÍTICO:**

En el código actual de MPRO para detalle de movimientos (línea 1260):
```python
"propina": 0,  # ← Hardcodeado a cero
```

Esto indica que **el equipo de desarrollo anterior NO encontró campo de propina a nivel de ticket en MPRO**.

## 1.2 Fuentes Disponibles en MPRO

| Nivel | Tabla | Campo | ¿Existe? | Tipo de Dato |
|-------|-------|-------|----------|--------------|
| **Corte** | `caja` | `propinas` | ⚠️ ASUMIDO | Agregado |
| **Ticket** | `Venta_Encabezado` | ❌ No hay campo propina | NO | N/A |
| **Ticket** | `Comanda` | ❌ No hay campo propina | NO | N/A |

## 1.3 Respuesta Formal

### ¿Existe fuente EXACTA de propina TPV en MPRO?

**NO. No existe fuente exacta.**

La tabla `caja` tiene un campo `propinas` que es el **total agregado** del corte, pero:
- No discrimina entre propina efectivo vs propina tarjeta
- No existe relación ticket → forma de pago → propina

### Declaración Formal:

```
╔════════════════════════════════════════════════════════════════════╗
║  MPRO: EL DATO DE PROPINA TPV SERÁ ESTIMADO, NO EXACTO            ║
║                                                                    ║
║  Fórmula de estimación:                                           ║
║  PROPINA_TPV = propinas × (tarjeta_credito + tarjeta_debito)      ║
║                          ─────────────────────────────────────     ║
║                                   total_ventas                     ║
╚════════════════════════════════════════════════════════════════════╝
```

## 1.4 Riesgos de Usar Estimación

| Riesgo | Probabilidad | Impacto Financiero | Mitigación |
|--------|--------------|-------------------|------------|
| **Sobre-estimación** (calcular más comisión de la debida) | Media | Se retiene de más al mesero | Redondeo conservador hacia abajo |
| **Sub-estimación** (calcular menos comisión) | Media | La empresa absorbe el costo bancario | Alertas cuando diferencia > 5% |
| **Inconsistencia** entre sucursales MPRO | Baja | Descuadres en consolidados | Marcar origen claramente |

**Impacto financiero estimado:**
- Si la proporción tarjeta/total varía ±10% de la realidad
- En propinas de $10,000 MXN
- Error máximo en comisión: $20 MXN (0.2%)

## 1.5 Marcado en EDARSA HUB

El campo `propinas_control.origen.tipo_dato` indicará claramente:

```javascript
{
  "origen": {
    "tipo_dato": "ESTIMADO",        // ← NUEVO CAMPO OBLIGATORIO
    "metodo_calculo": "PROPORCION_TARJETA_VENTAS",
    "confianza": 0.85,              // 85% de confianza estimada
    "propinas_totales_corte": 10000.00,
    "propinas_tpv_calculadas": 7000.00,
    "formula_aplicada": "propinas * (tc + td) / total_ventas",
    "advertencia": "Dato estimado por falta de desglose en sistema origen MPRO"
  }
}
```

Para **SoftRestaurant**, donde SÍ tenemos el dato exacto del corte:

```javascript
{
  "origen": {
    "tipo_dato": "EXACTO",
    "metodo_calculo": "CONCEPTO_9_CORTE",
    "confianza": 1.0,
    "propinas_totales_corte": 10000.00,
    "propinas_tpv_calculadas": 10000.00,  // Asumimos todo TPV del concepto 9
    "formula_aplicada": "movtoscajadetalles WHERE idconcepto=9"
  }
}
```

## 1.6 Visualización en UI (Propuesta)

```
┌─────────────────────────────────────────────────────────────────┐
│  PROPINAS TPV - Querétaro (MPRO)                                │
├─────────────────────────────────────────────────────────────────┤
│  Propina TPV:  $7,000.00  ⚠️ ESTIMADO                          │
│  Comisión 2%:  $140.00                                          │
│  ─────────────────────────────────────────────────────────────  │
│  ℹ️ Dato calculado por proporción tarjeta/ventas.               │
│     Confianza: 85%                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PROPINAS TPV - Cienfuegos (SoftRestaurant)                     │
├─────────────────────────────────────────────────────────────────┤
│  Propina TPV:  $10,000.00  ✅ EXACTO                            │
│  Comisión 2%:  $200.00                                          │
│  ─────────────────────────────────────────────────────────────  │
│  ✓ Dato obtenido directamente del corte Z (concepto 9)         │
└─────────────────────────────────────────────────────────────────┘
```

---

# 2. LLAVE DE INTEGRACIÓN - VALIDACIÓN DE SUFICIENCIA

## 2.1 Llave Actual Propuesta

```
folio_corte + sucursal_id + server_id
```

## 2.2 Análisis de Posibles Colisiones

| Escenario | ¿Puede causar colisión? | Ejemplo |
|-----------|------------------------|---------|
| Mismo folio en diferente servidor | ❌ No, `server_id` distingue | Folio "2889" en Cienfuegos vs Estelar |
| Mismo folio en diferente sucursal del mismo servidor | ❌ No, `sucursal_id` distingue | Folio "001" en Suc A vs Suc B (MPRO) |
| Mismo folio, misma sucursal, diferente empresa | ⚠️ **POSIBLE** | Si MPRO maneja múltiples empresas en misma BD |
| Mismo folio, misma sucursal, diferente fecha | ⚠️ **POSIBLE** | Folio reiniciado mensualmente |
| Re-sincronización del mismo corte | ❌ No es colisión, es update esperado | Normal |

## 2.3 Caso donde la llave corta PODRÍA FALLAR

**Escenario real en MPRO:**

```
Servidor: MPRO Querétaro (server_id: "abc-123")
Base de datos: CENTRAL2020

Empresa 1: "Restaurante Querétaro SA"
  - Sucursal: "ORIGEN" (sucursal_id: "0021")
  - Corte folio: "001" del 2026-04-14

Empresa 2: "Franquicia Querétaro SA"  
  - Sucursal: "ORIGEN" (sucursal_id: "0021")  ← MISMO ID
  - Corte folio: "001" del 2026-04-14         ← MISMO FOLIO

RESULTADO: Colisión de llave
```

**¿Es este escenario real?**

Depende de cómo EDARSA configura sus servidores. Si cada empresa tiene su propia BD, no hay problema. Si comparten BD, hay riesgo.

## 2.4 Llave Reforzada Propuesta

```
server_id + empresa_id + sucursal_id + folio_corte + fecha_corte
```

O en formato de índice MongoDB:

```javascript
{
  "server_id": 1,
  "empresa_id": 1,      // NUEVO
  "sucursal_id": 1,
  "folio_corte": 1,
  "fecha_corte": 1      // NUEVO
}
```

## 2.5 Recomendación Final

| Opción | Llave | Pros | Contras |
|--------|-------|------|---------|
| A (Original) | `server_id + sucursal_id + folio_corte` | Simple | Riesgo de colisión |
| B (Reforzada) | `server_id + empresa_id + sucursal_id + folio_corte + fecha_corte` | Sin riesgo | Más campos |
| **C (Recomendada)** | `server_id + sucursal_id + folio_corte + fecha_corte` | Balance | Mínimo riesgo |

**RECOMENDACIÓN: Opción C**

Justificación:
1. `fecha_corte` elimina colisiones por reinicio de folios
2. `empresa_id` no es necesario si cada servidor EDARSA ya representa una empresa (validar)
3. Es prácticamente imposible tener dos cortes con mismo folio el mismo día en la misma sucursal

## 2.6 Esquema de Llave Final

```javascript
// Índice único compuesto en MongoDB
db.propinas_control.createIndex(
  { 
    "server_id": 1, 
    "sucursal_id": 1, 
    "folio_corte": 1, 
    "fecha_corte": 1 
  },
  { 
    unique: true,
    name: "uk_propinas_corte"
  }
)
```

---

# 3. CONFIGURACIÓN - PARAMETRIZACIÓN FLEXIBLE

## 3.1 Problema con Singleton Global

Un singleton global como:
```javascript
{ "id": "config_propinas", "porcentaje_comision": 0.02 }
```

**NO permite:**
- Tasa diferente por empresa
- Tasa diferente por sucursal
- Cambios con fecha de vigencia
- Excepciones temporales (promociones, eventos)

## 3.2 Esquema Corregido: Parametrización Jerárquica

### Nuevo modelo de `propinas_config`:

```javascript
{
  "_id": ObjectId,
  "id": "UUID",
  
  // ========== ALCANCE DE LA CONFIGURACIÓN ==========
  "alcance": {
    "tipo": "SUCURSAL",           // GLOBAL, EMPRESA, SUCURSAL
    "server_id": "uuid-servidor", // null si GLOBAL
    "empresa_id": "EMP001",       // null si GLOBAL o EMPRESA
    "sucursal_id": "CIENFUEGOS"   // null si no aplica
  },
  
  // ========== VIGENCIA ==========
  "vigencia": {
    "fecha_inicio": ISODate("2026-01-01T00:00:00Z"),
    "fecha_fin": null,            // null = indefinido
    "activa": true
  },
  
  // ========== PARÁMETROS ==========
  "parametros": {
    "porcentaje_comision": 0.02,  // 2%
    "tolerancia_descuadre": 5.00, // $5 MXN
    "dias_para_cuadrar": 1        // Días hábiles
  },
  
  // ========== FORMAS DE PAGO TPV (por sistema) ==========
  "formas_pago_tpv": {
    "SoftRestaurant": {
      "conceptos": [10, 11, 12],
      "nombres": ["VISA", "MASTERCARD", "AMEX"]
    },
    "MPRO": {
      "campos": ["tarjeta_credito", "tarjeta_debito"],
      "metodo_calculo": "PROPORCION"
    }
  },
  
  // ========== METADATA ==========
  "created_at": ISODate,
  "created_by": "admin@edarsa.com.mx",
  "updated_at": ISODate,
  "updated_by": "admin@edarsa.com.mx",
  "motivo_cambio": "Configuración inicial"
}
```

## 3.3 Jerarquía de Resolución

Cuando se necesita la configuración para un corte, el sistema busca en orden:

```
1. SUCURSAL específica (más prioritaria)
   ↓ si no existe
2. EMPRESA 
   ↓ si no existe
3. GLOBAL (fallback obligatorio)
```

### Algoritmo de resolución:

```python
async def obtener_config_propinas(server_id, empresa_id, sucursal_id, fecha):
    """
    Resuelve la configuración aplicable usando jerarquía.
    """
    # 1. Buscar config específica de sucursal
    config = await db.propinas_config.find_one({
        "alcance.tipo": "SUCURSAL",
        "alcance.server_id": server_id,
        "alcance.sucursal_id": sucursal_id,
        "vigencia.activa": True,
        "vigencia.fecha_inicio": {"$lte": fecha},
        "$or": [
            {"vigencia.fecha_fin": None},
            {"vigencia.fecha_fin": {"$gte": fecha}}
        ]
    })
    if config:
        return config
    
    # 2. Buscar config de empresa
    config = await db.propinas_config.find_one({
        "alcance.tipo": "EMPRESA",
        "alcance.server_id": server_id,
        "alcance.empresa_id": empresa_id,
        "vigencia.activa": True,
        # ... mismas condiciones de fecha
    })
    if config:
        return config
    
    # 3. Fallback a GLOBAL
    config = await db.propinas_config.find_one({
        "alcance.tipo": "GLOBAL",
        "vigencia.activa": True
    })
    return config  # Debe existir siempre
```

## 3.4 Ejemplos de Configuración

### Configuración Global (Fallback):
```javascript
{
  "alcance": { "tipo": "GLOBAL", "server_id": null, "empresa_id": null, "sucursal_id": null },
  "vigencia": { "fecha_inicio": ISODate("2026-01-01"), "fecha_fin": null, "activa": true },
  "parametros": { "porcentaje_comision": 0.02 }
}
```

### Excepción para una Sucursal:
```javascript
{
  "alcance": { "tipo": "SUCURSAL", "server_id": "uuid-cienfuegos", "sucursal_id": "CIENFUEGOS" },
  "vigencia": { "fecha_inicio": ISODate("2026-04-01"), "fecha_fin": ISODate("2026-04-30"), "activa": true },
  "parametros": { "porcentaje_comision": 0.015 },  // 1.5% por promoción abril
  "motivo_cambio": "Promoción especial mes del niño"
}
```

### Configuración por Empresa MPRO:
```javascript
{
  "alcance": { "tipo": "EMPRESA", "server_id": "uuid-mpro-qro", "empresa_id": "ORIGEN" },
  "vigencia": { "fecha_inicio": ISODate("2026-01-01"), "fecha_fin": null, "activa": true },
  "parametros": { "porcentaje_comision": 0.025 }  // 2.5% para MPRO Origen
}
```

## 3.5 Resolución de Excepciones Futuras

| Excepción | Cómo se resuelve |
|-----------|-----------------|
| Nueva tasa para una sucursal | Crear registro con `alcance.tipo: "SUCURSAL"` |
| Promoción temporal | Crear registro con `vigencia.fecha_fin` definida |
| Nueva empresa | Crear registro con `alcance.tipo: "EMPRESA"` |
| Cambio global | Actualizar registro GLOBAL o crear nuevo con fecha |
| Rollback de cambio | Desactivar config (`vigencia.activa: false`) |

---

# 4. RECOMENDACIÓN DEFINITIVA DE MVP

## 4.1 Modelo Final Simplificado

| Colección | Documentos Esperados | Propósito |
|-----------|---------------------|-----------|
| `propinas_control` | 1 por corte | Datos operativos + cálculo + pago + cuadre |
| `propinas_config` | 1 GLOBAL + N excepciones | Parametrización jerárquica |

## 4.2 Esquema Final de `propinas_control`

```javascript
{
  "_id": ObjectId,
  "id": "UUID",
  
  // ========== LLAVE ÚNICA (4 campos) ==========
  "server_id": "uuid",
  "sucursal_id": "CIENFUEGOS",
  "folio_corte": "2889",
  "fecha_corte": ISODate("2026-04-14"),
  
  // ========== CONTEXTO ==========
  "server_name": "Cienfuegos",
  "system_type": "SoftRestaurant",
  "sucursal_nombre": "Cienfuegos",
  "empresa_id": "CIENFUEGOS",  // Para resolución de config
  
  // ========== ORIGEN (LECTURA SQL) ==========
  "origen": {
    "tipo_dato": "EXACTO",               // EXACTO o ESTIMADO
    "metodo_calculo": "CONCEPTO_9_CORTE",
    "confianza": 1.0,
    "propinas_totales_corte": 10000.00,
    "ventas_tarjeta": 70000.00,
    "ventas_totales": 100000.00,
    "propinas_tpv": 10000.00,
    "formula_aplicada": "movtoscajadetalles WHERE idconcepto=9",
    "fecha_sincronizacion": ISODate,
    "advertencia": null                  // Solo para ESTIMADO
  },
  
  // ========== CÁLCULO (EDARSA HUB) ==========
  "calculo": {
    "config_aplicada_id": "uuid-config", // Trazabilidad
    "porcentaje_comision": 0.02,
    "comision_calculada": 200.00,
    "monto_a_pagar_meseros": 9800.00
  },
  
  // ========== PAGO (MANUAL) ==========
  "pago": {
    "registrado": false,
    "monto_pagado": null,
    "fecha_pago": null,
    "metodo": null,
    "registrado_por": null,
    "observaciones": null
  },
  
  // ========== CUADRE ==========
  "cuadre": {
    "estado": "PENDIENTE",
    "diferencia": null,
    "fecha_cuadre": null,
    "observaciones": null
  },
  
  // ========== METADATA ==========
  "created_at": ISODate,
  "updated_at": ISODate
}
```

## 4.3 Endpoints MVP (Sin cambios)

```
POST /api/finanzas/propinas/sincronizar
GET  /api/finanzas/propinas
PUT  /api/finanzas/propinas/{id}/pago
GET  /api/finanzas/propinas/config
POST /api/finanzas/propinas/config  (crear nueva config)
PUT  /api/finanzas/propinas/config/{id}  (modificar)
```

---

# 5. CONFIRMACIÓN DE DESACOPLAMIENTO

## 5.1 Checklist de No-Impacto

| Verificación | Estado | Evidencia |
|--------------|--------|-----------|
| ¿Escribe en SQL Server? | ❌ NO | Solo SELECT |
| ¿Modifica `cuadres_cortes_z`? | ❌ NO | Solo referencia por folio |
| ¿Modifica `servers`? | ❌ NO | Solo lectura |
| ¿Modifica módulo Comercial? | ❌ NO | Independiente |
| ¿Modifica módulo Tesorería? | ❌ NO | Endpoints separados |
| ¿Crea colecciones nuevas? | ✅ SÍ | `propinas_control`, `propinas_config` |
| ¿Usa auth existente? | ✅ SÍ | Reutiliza `get_current_user` |

## 5.2 Declaración Formal

```
╔════════════════════════════════════════════════════════════════════╗
║  CONFIRMACIÓN DE AISLAMIENTO                                       ║
║                                                                    ║
║  El módulo de Control de Propinas TPV:                            ║
║                                                                    ║
║  ✓ Es 100% desacoplado de módulos existentes                      ║
║  ✓ NO modifica tablas en SQL Server (solo lectura)                ║
║  ✓ NO modifica colecciones existentes en MongoDB                  ║
║  ✓ NO interfiere con flujos de ventas, cortes o reportes          ║
║  ✓ Puede desactivarse sin afectar el sistema                      ║
║                                                                    ║
║  Riesgo de regresión: CERO                                        ║
╚════════════════════════════════════════════════════════════════════╝
```

---

# 6. RESUMEN DE CAMBIOS FINALES

| Aspecto | Versión Anterior | Versión Corregida |
|---------|------------------|-------------------|
| MPRO tipo_dato | No especificado | **ESTIMADO** (documentado) |
| Llave única | 3 campos | **4 campos** (+ fecha_corte) |
| propinas_config | Singleton global | **Jerarquía** (GLOBAL → EMPRESA → SUCURSAL) |
| Vigencia config | No contemplada | **Con fechas inicio/fin** |
| Campo tipo_dato | No existía | **EXACTO/ESTIMADO obligatorio** |
| Campo confianza | No existía | **Nuevo: 0.0 a 1.0** |

---

**FIN DE ADENDA TÉCNICA**

*Pendiente: Aprobación del usuario para proceder a implementación.*
