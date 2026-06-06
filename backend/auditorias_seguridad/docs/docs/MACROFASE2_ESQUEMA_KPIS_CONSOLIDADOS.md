# MACROFASE 2 - Esquema KPIs Consolidados en EDARSA HUB

**Versión**: 2.0 DEFINITIVO  
**Fecha**: 2026-04-22  
**Estado**: ESPECIFICACIÓN APROBADA

---

## 1. OBJETIVO

Definir el esquema de datos consolidados para KPIs comerciales en EDARSA HUB que soporte:
- Sincronización SYNC-S (cada 15 min)
- Sincronización SYNC-N (nocturna 03:00)
- Carga histórica de 24 meses
- Reconciliación mensual
- Consultas rápidas para Tablero Ejecutivo y Comercial
- Trazabilidad completa de origen y cambios

---

## 2. DECISIÓN ARQUITECTÓNICA: UNA SOLA COLECCIÓN

**Decisión**: Usar **UNA SOLA colección** (`kpis_comercial`) con documentos que contienen:
- Datos actuales (current)
- Historial de versiones embebido (versions)

**Razón**: 
- Evita joins/lookups costosos
- Permite atomic updates con historial
- Simplifica UPSERT
- Reduce complejidad de índices

---

## 3. ESQUEMA DEFINITIVO

### 3.1 Colección: `kpis_comercial`

```javascript
{
  // ========================================
  // CLAVE ÚNICA COMPUESTA (4 campos)
  // ========================================
  "server_id": "6d053c22-523e-48c0-b72b-96081e2d781b",  // UUID del servidor origen
  "empresa_id": "1d91f076-a28e-49a5-b445-84aa767737b6", // UUID de empresa EDARSA
  "sucursal_id": "0021",                                 // Código sucursal en sistema origen
  "fecha": "2026-04-21",                                 // Formato YYYY-MM-DD (string)
  
  // ========================================
  // IDENTIFICADORES AUXILIARES (para queries)
  // ========================================
  "unidad_negocio_id": "uuid-unidad",      // Si aplica mapeo a unidad de negocio EDARSA
  "sucursal_nombre": "CIENFUEGOS PRINCIPAL", // Nombre legible
  "empresa_nombre": "CIENFUEGOS",            // Nombre legible
  "system_type": "SoftRestaurant",           // MPRO | SoftRestaurant
  
  // ========================================
  // ESTADO DEL PERÍODO
  // ========================================
  "estado_periodo": "ABIERTO",  // ABIERTO | CERRADO | RECONCILIADO
  "estado_transiciones": [
    {
      "de": null,
      "a": "ABIERTO",
      "timestamp": "2026-04-21T06:00:00Z",
      "motivo": "Inicio de día"
    },
    {
      "de": "ABIERTO",
      "a": "CERRADO",
      "timestamp": "2026-04-22T03:15:00Z",
      "motivo": "SYNC-N detectó corte Z completado"
    }
  ],
  
  // ========================================
  // KPIs PRINCIPALES (valores actuales)
  // ========================================
  "kpis": {
    "ventas": 125000.00,
    "ventas_netas": 120000.00,
    "pax": 450,
    "cheques": 120,
    "ticket_promedio": 277.78,
    "cheque_promedio": 1041.67,
    "propina": 5000.00,
    "propina_efectivo": 3000.00,
    "propina_tarjeta": 2000.00,
    "descuentos": 2500.00,
    "cortesias": 1000.00,
    "cancelaciones": 500.00,
    "impuestos": 19200.00,
    "efectivo": 45000.00,
    "tarjeta": 70000.00,
    "otros_pagos": 10000.00
  },
  
  // ========================================
  // COMPARATIVOS (calculados al guardar)
  // ========================================
  "comparativos": {
    "mes_anterior": {
      "fecha_comparacion": "2026-03-21",
      "ventas": 118000.00,
      "variacion_pct": 5.93,
      "variacion_abs": 7000.00
    },
    "año_anterior": {
      "fecha_comparacion": "2025-04-21",
      "ventas": 110000.00,
      "variacion_pct": 13.64,
      "variacion_abs": 15000.00
    },
    "meta_dia": {
      "meta": 130000.00,
      "cumplimiento_pct": 96.15,
      "diferencia": -5000.00
    }
  },
  
  // ========================================
  // DESGLOSE POR HORA (opcional, para análisis)
  // ========================================
  "desglose_hora": [
    { "hora": 9, "ventas": 5000.00, "cheques": 10, "pax": 25 },
    { "hora": 10, "ventas": 8000.00, "cheques": 15, "pax": 40 },
    { "hora": 11, "ventas": 12000.00, "cheques": 22, "pax": 55 }
    // ... hasta hora 23
  ],
  
  // ========================================
  // TRAZABILIDAD DE ORIGEN
  // ========================================
  "source": {
    "type": "LIVE",                          // LIVE | FALLBACK | CACHE | RECONCILIACION
    "query_timestamp": "2026-04-22T03:15:00Z",
    "query_duration_ms": 1500,
    "connection_status": "OK",               // OK | TIMEOUT | ERROR
    "raw_query_hash": "sha256:abc123...",    // Hash de la query ejecutada
    "rows_retrieved": 1,
    "scheduler_job_id": "sync_n_20260422_031500"
  },
  
  // ========================================
  // AUDITORÍA
  // ========================================
  "created_at": "2026-04-21T06:00:00Z",
  "created_by": "scheduler_sync_s",
  "updated_at": "2026-04-22T03:15:00Z",
  "updated_by": "scheduler_sync_n",
  "version": 3,                              // Incrementa con cada update
  
  // ========================================
  // HISTORIAL DE VERSIONES (embebido)
  // ========================================
  "versions": [
    {
      "version": 1,
      "timestamp": "2026-04-21T06:00:00Z",
      "updated_by": "scheduler_sync_s",
      "source_type": "LIVE",
      "kpis_snapshot": {
        "ventas": 0,
        "pax": 0
        // ... snapshot mínimo
      },
      "reason": "Creación inicial - día abierto"
    },
    {
      "version": 2,
      "timestamp": "2026-04-21T18:00:00Z",
      "updated_by": "scheduler_sync_s",
      "source_type": "LIVE",
      "kpis_snapshot": {
        "ventas": 95000.00,
        "pax": 320
      },
      "reason": "SYNC-S actualización",
      "diff": {
        "ventas": { "old": 0, "new": 95000.00 },
        "pax": { "old": 0, "new": 320 }
      }
    }
  ],
  
  // ========================================
  // FLAGS DE CONTROL
  // ========================================
  "flags": {
    "tiene_corte_z": true,
    "requiere_reconciliacion": false,
    "alerta_diferencia_mayor_5pct": false,
    "datos_incompletos": false,
    "excluir_de_reportes": false
  }
}
```

---

## 4. CLAVES ÚNICAS E ÍNDICES

### 4.1 Índice Único (CLAVE PRIMARIA)

```javascript
// Índice único compuesto - OBLIGATORIO
db.kpis_comercial.createIndex(
  { 
    "server_id": 1, 
    "empresa_id": 1, 
    "sucursal_id": 1, 
    "fecha": 1 
  },
  { 
    unique: true,
    name: "idx_unique_kpi_diario"
  }
)
```

**Clave UPSERT**:
```python
filter_key = {
    "server_id": server_id,
    "empresa_id": empresa_id,
    "sucursal_id": sucursal_id,
    "fecha": fecha_str  # YYYY-MM-DD
}
```

### 4.2 Índices de Consulta

```javascript
// Consultas del Tablero Ejecutivo (por empresa y rango de fechas)
db.kpis_comercial.createIndex(
  { "empresa_id": 1, "fecha": -1 },
  { name: "idx_empresa_fecha" }
)

// Consultas por servidor (para sync)
db.kpis_comercial.createIndex(
  { "server_id": 1, "fecha": -1 },
  { name: "idx_server_fecha" }
)

// Filtrar por estado de período
db.kpis_comercial.createIndex(
  { "estado_periodo": 1, "fecha": -1 },
  { name: "idx_estado_fecha" }
)

// Consultas por unidad de negocio (si aplica)
db.kpis_comercial.createIndex(
  { "unidad_negocio_id": 1, "fecha": -1 },
  { name: "idx_unidad_fecha" }
)

// Buscar documentos pendientes de reconciliación
db.kpis_comercial.createIndex(
  { "flags.requiere_reconciliacion": 1, "fecha": -1 },
  { name: "idx_pendientes_reconciliacion" }
)
```

---

## 5. LÓGICA DE UPSERT

### 5.1 Función de UPSERT Idempotente

```python
async def upsert_kpi_comercial(
    db,
    server_id: str,
    empresa_id: str,
    sucursal_id: str,
    fecha: str,  # YYYY-MM-DD
    kpis: dict,
    source_info: dict,
    updated_by: str = "scheduler"
) -> dict:
    """
    UPSERT idempotente de KPI comercial.
    
    Reglas:
    1. Si no existe: INSERT con version=1
    2. Si existe y hay cambios: UPDATE con version+1 y guardar snapshot
    3. Si existe y NO hay cambios: NO hacer nada (idempotente)
    4. Si período está RECONCILIADO: Rechazar update (requiere reapertura manual)
    
    Returns:
        dict con {action: "INSERT|UPDATE|SKIP|REJECTED", version: int}
    """
    now = datetime.now(timezone.utc).isoformat()
    
    filter_key = {
        "server_id": server_id,
        "empresa_id": empresa_id,
        "sucursal_id": sucursal_id,
        "fecha": fecha
    }
    
    existing = await db.kpis_comercial.find_one(filter_key)
    
    # CASO 1: No existe - INSERT
    if not existing:
        new_doc = {
            **filter_key,
            "kpis": kpis,
            "source": source_info,
            "estado_periodo": "ABIERTO",
            "estado_transiciones": [{
                "de": None,
                "a": "ABIERTO",
                "timestamp": now,
                "motivo": "Creación inicial"
            }],
            "created_at": now,
            "created_by": updated_by,
            "updated_at": now,
            "updated_by": updated_by,
            "version": 1,
            "versions": [],
            "flags": {
                "tiene_corte_z": False,
                "requiere_reconciliacion": False,
                "datos_incompletos": False,
                "excluir_de_reportes": False
            }
        }
        await db.kpis_comercial.insert_one(new_doc)
        return {"action": "INSERT", "version": 1}
    
    # CASO 2: Existe pero está RECONCILIADO - RECHAZAR
    if existing.get("estado_periodo") == "RECONCILIADO":
        logging.warning(
            f"[UPSERT-REJECTED] Período RECONCILIADO: {filter_key}"
        )
        return {"action": "REJECTED", "version": existing.get("version"), "reason": "RECONCILIADO"}
    
    # CASO 3: Existe - verificar si hay cambios
    existing_kpis = existing.get("kpis", {})
    has_changes = _detect_kpi_changes(existing_kpis, kpis)
    
    if not has_changes:
        return {"action": "SKIP", "version": existing.get("version")}
    
    # CASO 4: Hay cambios - UPDATE con historial
    new_version = existing.get("version", 1) + 1
    
    # Crear snapshot de versión anterior
    version_snapshot = {
        "version": existing.get("version"),
        "timestamp": existing.get("updated_at"),
        "updated_by": existing.get("updated_by"),
        "source_type": existing.get("source", {}).get("type"),
        "kpis_snapshot": existing_kpis,
        "reason": "Actualización por sync",
        "diff": _calculate_diff(existing_kpis, kpis)
    }
    
    update_doc = {
        "$set": {
            "kpis": kpis,
            "source": source_info,
            "updated_at": now,
            "updated_by": updated_by,
            "version": new_version
        },
        "$push": {
            "versions": {
                "$each": [version_snapshot],
                "$slice": -10  # Mantener últimas 10 versiones embebidas
            }
        }
    }
    
    await db.kpis_comercial.update_one(filter_key, update_doc)
    return {"action": "UPDATE", "version": new_version}


def _detect_kpi_changes(old_kpis: dict, new_kpis: dict, threshold_pct: float = 0.01) -> bool:
    """
    Detecta si hay cambios significativos entre KPIs.
    Threshold del 0.01% para evitar updates por redondeo.
    """
    for key in new_kpis:
        old_val = old_kpis.get(key, 0) or 0
        new_val = new_kpis.get(key, 0) or 0
        
        if old_val == 0 and new_val == 0:
            continue
        
        if old_val == 0:
            return True  # Cambio de 0 a algo
        
        diff_pct = abs((new_val - old_val) / old_val) * 100
        if diff_pct > threshold_pct:
            return True
    
    return False


def _calculate_diff(old_kpis: dict, new_kpis: dict) -> dict:
    """Calcula diferencias para auditoría."""
    diff = {}
    all_keys = set(old_kpis.keys()) | set(new_kpis.keys())
    
    for key in all_keys:
        old_val = old_kpis.get(key, 0)
        new_val = new_kpis.get(key, 0)
        if old_val != new_val:
            diff[key] = {"old": old_val, "new": new_val}
    
    return diff
```

---

## 6. ESTADOS DE PERÍODO

### 6.1 Definición de Estados

| Estado | Descripción | Puede Modificarse | Condición de Entrada |
|--------|-------------|-------------------|----------------------|
| **ABIERTO** | Día activo, datos pueden cambiar | ✅ Sí | Creación o reapertura |
| **CERRADO** | Día finalizado, datos estables | ✅ Sí (solo SYNC-N) | Corte Z detectado o día anterior |
| **RECONCILIADO** | Validado manualmente, datos definitivos | ❌ No (requiere reapertura) | Reconciliación mensual |

### 6.2 Reglas de Transición

```
ABIERTO → CERRADO
  Condiciones:
  - Fecha < HOY
  - O se detectó corte Z completado
  - O SYNC-N nocturno (03:00) para días de ayer o antes
  
CERRADO → RECONCILIADO
  Condiciones:
  - Reconciliación mensual (día 5 del mes siguiente)
  - Diferencia con origen < 1%
  - Aprobación automática o manual
  
RECONCILIADO → CERRADO
  Condiciones:
  - Reapertura manual por admin con justificación
  - Se registra en audit log
  
CERRADO → ABIERTO
  Condiciones:
  - Reapertura por corrección detectada
  - Solo días de los últimos 7 días
  - Requiere justificación
```

### 6.3 Función de Cambio de Estado

```python
async def cambiar_estado_periodo(
    db,
    filter_key: dict,
    nuevo_estado: str,
    motivo: str,
    updated_by: str
) -> bool:
    """
    Cambia el estado del período con validaciones.
    """
    existing = await db.kpis_comercial.find_one(filter_key)
    if not existing:
        return False
    
    estado_actual = existing.get("estado_periodo")
    
    # Validar transición permitida
    transiciones_validas = {
        "ABIERTO": ["CERRADO"],
        "CERRADO": ["RECONCILIADO", "ABIERTO"],
        "RECONCILIADO": ["CERRADO"]  # Requiere reapertura manual
    }
    
    if nuevo_estado not in transiciones_validas.get(estado_actual, []):
        raise ValueError(f"Transición no válida: {estado_actual} → {nuevo_estado}")
    
    now = datetime.now(timezone.utc).isoformat()
    
    transicion = {
        "de": estado_actual,
        "a": nuevo_estado,
        "timestamp": now,
        "motivo": motivo
    }
    
    await db.kpis_comercial.update_one(
        filter_key,
        {
            "$set": {
                "estado_periodo": nuevo_estado,
                "updated_at": now,
                "updated_by": updated_by
            },
            "$push": {
                "estado_transiciones": transicion
            }
        }
    )
    
    return True
```

---

## 7. CORRECCIONES POSTERIORES SIN DUPLICAR

### 7.1 Reglas de Corrección

1. **Días ABIERTOS**: Se sobrescriben directamente (idempotente)
2. **Días CERRADOS**: 
   - Se guardan en `versions[]` embebido
   - Se actualiza con nueva versión
   - Se marca `flags.requiere_reconciliacion = true` si diff > 5%
3. **Días RECONCILIADOS**:
   - NO se modifican sin reapertura manual
   - Reapertura cambia estado a CERRADO primero
   - Se registra en audit log con justificación

### 7.2 Historial de Versiones Embebido

```javascript
// El array versions[] guarda las últimas 10 versiones
// Si se necesita historial completo, se archiva a colección separada
"versions": [
  { "version": 1, "timestamp": "...", "kpis_snapshot": {...} },
  { "version": 2, "timestamp": "...", "kpis_snapshot": {...}, "diff": {...} }
]

// Para historial > 10 versiones, archivar a:
// kpis_comercial_archivo (colección separada, solo cuando sea necesario)
```

---

## 8. GRANULARIDAD Y SOPORTE DE QUERIES

### 8.1 Verificación de Granularidad

| Dimensión | Campo | Soportado |
|-----------|-------|-----------|
| Unidad de negocio | `unidad_negocio_id` | ✅ |
| Sucursal | `sucursal_id` + `sucursal_nombre` | ✅ |
| Server origen | `server_id` | ✅ |
| Empresa | `empresa_id` + `empresa_nombre` | ✅ |
| Fecha | `fecha` (YYYY-MM-DD) | ✅ |
| KPIs | `kpis.*` | ✅ |
| Fuente LIVE vs HUB | `source.type` | ✅ |
| Recálculo sin duplicados | UPSERT idempotente | ✅ |
| Trazabilidad | `versions[]`, `source.*` | ✅ |

### 8.2 Queries de Ejemplo para Tablero Ejecutivo

```javascript
// KPIs del mes actual para una empresa
db.kpis_comercial.find({
  "empresa_id": "1d91f076-...",
  "fecha": { $gte: "2026-04-01", $lte: "2026-04-30" },
  "flags.excluir_de_reportes": { $ne: true }
}).sort({ "fecha": -1, "sucursal_nombre": 1 })

// Totales por día (agregación)
db.kpis_comercial.aggregate([
  { $match: { "empresa_id": "...", "fecha": { $gte: "2026-04-01" } } },
  { $group: {
      _id: "$fecha",
      total_ventas: { $sum: "$kpis.ventas" },
      total_pax: { $sum: "$kpis.pax" },
      sucursales: { $sum: 1 }
  }},
  { $sort: { "_id": -1 } }
])

// Pendientes de reconciliación
db.kpis_comercial.find({
  "estado_periodo": "CERRADO",
  "flags.requiere_reconciliacion": true
}).sort({ "fecha": 1 })
```

---

## 9. SCRIPTS DE INICIALIZACIÓN

### 9.1 Crear Índices

```python
async def setup_kpis_comercial_indexes(db):
    """
    Crea índices para la colección kpis_comercial.
    Ejecutar una vez en setup inicial.
    """
    collection = db.kpis_comercial
    
    # Índice único (clave primaria)
    await collection.create_index(
        [
            ("server_id", 1),
            ("empresa_id", 1),
            ("sucursal_id", 1),
            ("fecha", 1)
        ],
        unique=True,
        name="idx_unique_kpi_diario"
    )
    
    # Índices de consulta
    await collection.create_index(
        [("empresa_id", 1), ("fecha", -1)],
        name="idx_empresa_fecha"
    )
    
    await collection.create_index(
        [("server_id", 1), ("fecha", -1)],
        name="idx_server_fecha"
    )
    
    await collection.create_index(
        [("estado_periodo", 1), ("fecha", -1)],
        name="idx_estado_fecha"
    )
    
    await collection.create_index(
        [("unidad_negocio_id", 1), ("fecha", -1)],
        name="idx_unidad_fecha"
    )
    
    await collection.create_index(
        [("flags.requiere_reconciliacion", 1), ("fecha", -1)],
        name="idx_pendientes_reconciliacion"
    )
    
    logging.info("[SETUP] Índices de kpis_comercial creados")
```

---

## 10. PRÓXIMOS PASOS

Con este esquema definido, los siguientes pasos son:

1. ~~**Implementar función `upsert_kpi_comercial()`** en `/app/backend/modules/comercial/repository.py`~~ ✅
2. ~~**Crear script de inicialización de índices**~~ ✅
3. ~~**Implementar SYNC-S** (cada 15 min, ventana 48h)~~ ✅
4. ~~**Implementar SYNC-N** (03:00, ventana 7 días)~~ ✅
5. **Implementar reconciliación mensual** (día 5) - P2
6. **Implementar carga histórica** (24 meses, batch)
7. **Migrar endpoints de históricos** a leer de `kpis_comercial`

---

## 11. ARCHIVOS IMPLEMENTADOS (FASE 2.2)

| Archivo | Propósito |
|---------|-----------|
| `/app/backend/modules/comercial/kpis_repository.py` | Funciones de UPSERT, estados, queries |
| `/app/backend/scripts/setup_kpis_indexes.py` | Script de creación de índices |
| `/app/backend/core/scheduler/jobs/sync_short_comercial_job.py` | Job SYNC-S (15 min) |
| `/app/backend/core/scheduler/jobs/sync_nightly_comercial_job.py` | Job SYNC-N (03:00) |
| `/app/backend/tests/test_macrofase2_kpis.py` | Tests de validación (14/14 OK) |

---

## 12. EVIDENCIA DE PRUEBAS (2026-04-22)

```
======================================================================
RESUMEN: 14/14 tests pasaron
======================================================================

✅ PASS | Creación de índices (6 índices creados)
✅ PASS | UPSERT INSERT inicial (version=1)
✅ PASS | UPSERT repetido sin cambios = SKIP (idempotente)
✅ PASS | Cambio menor al threshold = SKIP
✅ PASS | Cambio real detectado = UPDATE (version=2)
✅ PASS | Historial de versiones embebido (1 versión, tiene diff)
✅ PASS | Estado inicial es ABIERTO
✅ PASS | Transición ABIERTO → CERRADO
✅ PASS | SYNC-S NO modifica CERRADO
✅ PASS | SYNC-N SÍ modifica CERRADO (version=3)
✅ PASS | Transición CERRADO → RECONCILIADO
✅ PASS | RECONCILIADO NO se modifica (REJECTED)
✅ PASS | Sin duplicados - exactamente 1 documento
✅ PASS | Cierre masivo de períodos (3 cerrados)
```

---

## APROBACIÓN

| Aspecto | Estado |
|---------|--------|
| Clave única definida | ✅ |
| Índices especificados | ✅ |
| Lógica UPSERT idempotente | ✅ |
| Estados de período | ✅ |
| Reglas de corrección | ✅ |
| Trazabilidad de origen | ✅ |
| Soporte para todas las queries | ✅ |
| No rompe RBAC existente | ✅ |

**Esquema listo para implementación.**
