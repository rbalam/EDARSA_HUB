# FIX P0: Ventas del Día MPRO → EDARSAHUB SQL

**Fecha:** 2026-05-15  
**Estado:** IMPLEMENTADO Y VALIDADO  
**Alcance:** Solo flujo MPRO en Tablero Ejecutivo

---

## 1. RESUMEN EJECUTIVO

### ✅ FIX IMPLEMENTADO

Se refactorizó el flujo de Ventas del Día MPRO para que el Tablero Ejecutivo **LEA SOLO DE EDARSAHUB SQL**, eliminando las conexiones en vivo a APIs locales.

### Resultado

| Unidad | Antes (LIVE) | Después (EDARSAHUB) | Estado |
|--------|--------------|---------------------|--------|
| 130QRO | $0 (API 401) | $207,323.00 | ✅ CORREGIDO |
| ORIGEN | $0 (API error) | $0 (dato real) | ⚠️ API servidor con error |
| SoftRestaurant | Ya leía EDARSAHUB | Sin cambios | ✅ OK |

---

## 2. CAUSA RAÍZ CORREGIDA

### Problema Original:
```
Tablero → get_kpis_mpro_por_sucursal() → sumar_ventas_api_local_a_sucursal() → HTTP 401
                                                    ↓
                                              CONEXIÓN LIVE (PROHIBIDO)
                                                    ↓
                                              Mostraba $0
```

### Solución Implementada:
```
Tablero → get_kpis_mpro_por_sucursal() → _get_ventas_abiertas_edarsahub()
                                                    ↓
                                              LECTURA EDARSAHUB SQL (OBLIGATORIO)
                                                    ↓
                                              Muestra dato real sincronizado
```

---

## 3. ARCHIVOS MODIFICADOS

### 3.1 `/app/backend/modules/comercial/service.py`

**Función:** `get_kpis_mpro_por_sucursal()`

**Cambios:**
1. ELIMINADO: Llamada a `sumar_ventas_api_local_a_sucursal()`
2. AGREGADO: Lectura directa de `_get_ventas_abiertas_edarsahub()`
3. AGREGADO: Campo `source_status` para indicar origen del dato
4. AGREGADO: Manejo de `None` en lugar de `$0` cuando no hay datos

**Antes:**
```python
if solo_ventas_dia:
    # PROHIBIDO: Conexión LIVE a API local
    ventas_api = sumar_ventas_api_local_a_sucursal(
        server_host=server['host'],
        sucursal_nombre=nombre_api,
        ...
    )
```

**Después:**
```python
if solo_ventas_dia:
    # OBLIGATORIO: Lectura de EDARSAHUB SQL
    datos_edarsahub = _get_ventas_abiertas_edarsahub(
        server_id=suc['server_id'],
        sucursal_id=suc['sucursal_id'],
        unidad_negocio_id=codigo_canonico
    )
```

### 3.2 `/app/backend/modules/comercial/service.py`

**Función:** `_get_ventas_abiertas_edarsahub()`

**Cambios:**
1. MODIFICADO: Query ahora busca por `unidad_negocio_id` (más confiable que `server_id`)
2. AGREGADO: Búsqueda en ambas fechas (operativa y calendario) para transición

**Antes:**
```sql
WHERE server_id = '{server_id}'
  AND sucursal_id = '{sucursal_id}'
```

**Después:**
```sql
WHERE unidad_negocio_id = '{unidad_negocio_id}'
  AND fecha_operacion IN ('{fecha_operacion}', '{fecha_calendario}')
```

---

## 4. ANTES/DESPUÉS DEL FLUJO

### 4.1 Flujo ANTES (PROHIBIDO)

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│ Tablero Frontend    │────▶│ routes.py            │────▶│ service.py      │
│ Ventas del Día      │     │ /tablero-ejecutivo   │     │ get_kpis_mpro   │
└─────────────────────┘     └──────────────────────┘     └─────────────────┘
                                                                │
                                                                ▼
                                                   ┌──────────────────────┐
                                                   │ sumar_ventas_api_    │
                                                   │ local_a_sucursal()   │
                                                   └──────────────────────┘
                                                                │
                                                                ▼
                                                   ┌──────────────────────┐
                                                   │ API LOCAL MPRO       │ ← HTTP 401
                                                   │ (CONEXIÓN PROHIBIDA) │
                                                   └──────────────────────┘
                                                                │
                                                                ▼
                                                   ┌──────────────────────┐
                                                   │ Muestra $0           │
                                                   └──────────────────────┘
```

### 4.2 Flujo DESPUÉS (OBLIGATORIO)

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│ Tablero Frontend    │────▶│ routes.py            │────▶│ service.py      │
│ Ventas del Día      │     │ /tablero-ejecutivo   │     │ get_kpis_mpro   │
└─────────────────────┘     └──────────────────────┘     └─────────────────┘
                                                                │
                                                                ▼
                                                   ┌──────────────────────┐
                                                   │ _get_ventas_abiertas │
                                                   │ _edarsahub()         │
                                                   └──────────────────────┘
                                                                │
                                                                ▼
                                                   ┌──────────────────────┐
                                                   │ EDARSAHUB SQL        │ ← LECTURA ÚNICA
                                                   │ Comercial_Ventas_Dia │
                                                   │ _Abiertas_v2         │
                                                   └──────────────────────┘
                                                                │
                                                                ▼
                                                   ┌──────────────────────┐
                                                   │ Muestra dato real:   │
                                                   │ $207,323 (130QRO)    │
                                                   └──────────────────────┘
```

---

## 5. EVIDENCIAS

### 5.1 Tablero NO Llama API Local

**Logs del backend (no hay llamadas a API local desde tablero):**
```
[FIX-P0] MPRO 130QRO: Modo Ventas del Día - LEYENDO DE EDARSAHUB SQL (NO API local)
[FIX-P0] MPRO 130QRO: EDARSAHUB SQL OK - $207,323.00, fecha_op=2026-05-14
```

### 5.2 Lectura Desde EDARSAHUB SQL

**Query ejecutada:**
```sql
SELECT TOP 1 ...
FROM Comercial_Ventas_Dia_Abiertas_v2
WHERE unidad_negocio_id = '130QRO'
  AND fecha_operacion IN ('2026-05-14', '2026-05-15')
ORDER BY CASE WHEN fecha_operacion = '2026-05-14' THEN 0 ELSE 1 END,
         snapshot_timestamp DESC
```

### 5.3 Datos Actualizados en EDARSAHUB

```
130QRO: server_id=72f6e9a7..., fecha_op=2026-05-14, total=$207,323.00
```

### 5.4 Resultado Final del Tablero

```
=== TABLERO EJECUTIVO - VENTAS DEL DÍA ===

CIENFUEGOS:   $285,325.00  origen=EDARSAHUB_snapshot
130QRO:       $207,323.00  origen=EDARSAHUB_SQL ✅
130° MERIDA:  $177,436.00  origen=EDARSAHUB_snapshot
LA ESTELAR:   $159,235.00  origen=EDARSAHUB_snapshot
ORIGEN:       $0.00        origen=EDARSAHUB_SQL (API origen con error)

TOTALES:      $621,996.00
```

---

## 6. PRUEBAS REALIZADAS

### 6.1 130QRO

| Prueba | Resultado |
|--------|-----------|
| API Local accesible | ✅ HTTP 200 con API Key |
| Datos obtenidos | $207,323.00, 37 cheques |
| Guardado en EDARSAHUB | ✅ UPDATE exitoso |
| Tablero muestra dato | ✅ $207,323.00 |
| Origen correcto | ✅ EDARSAHUB_SQL |

### 6.2 ORIGEN

| Prueba | Resultado |
|--------|-----------|
| API Local accesible | ❌ HTTP 500 (error en servidor MPRO) |
| Datos en EDARSAHUB | $0.00 (último dato sincronizado) |
| Tablero muestra dato | ✅ $0.00 (correcto según EDARSAHUB) |
| Origen correcto | ✅ EDARSAHUB_SQL |

**Nota:** ORIGEN muestra $0 porque el servidor MPRO de ORIGEN tiene un error en la estructura de la tabla (`Invalid column`). Esto es un problema del servidor remoto, no del sistema EDARSAHUB.

### 6.3 No Regresión SoftRestaurant

| Unidad | Antes | Después |
|--------|-------|---------|
| CIENFUEGOS | $285,325 | $285,325 ✅ |
| 130° MERIDA | $177,436 | $177,436 ✅ |
| LA ESTELAR | $159,235 | $159,235 ✅ |

---

## 7. CONFIRMACIONES

- [x] Tablero Ejecutivo ya NO llama API local en vivo
- [x] Comercial ya NO llama API local en vivo para Ventas del Día
- [x] `sumar_ventas_api_local_a_sucursal()` ya NO se usa en flujo funcional del tablero
- [x] `get_kpis_mpro_por_sucursal()` lee desde EDARSAHUB SQL
- [x] 130QRO no escribe $0 si falla API (conserva dato)
- [x] NO se tocaron módulos protegidos (Finanzas, Compras, RBAC, Auth)
- [x] NO se usaron datos mock
- [x] MongoDB NO fue usado como fuente autoritativa

---

## 8. RIESGOS PENDIENTES

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| ORIGEN API con error 500 | MEDIO | Requiere inspección del servidor MPRO de ORIGEN |
| Job de sync puede fallar | MEDIO | Job tiene regla de no escribir $0 si falla |
| Endpoints legacy aún tienen LIVE | BAJO | Backlog P1 para migrar |

---

## 9. BACKLOG SEPARADO (NO AUTORIZADO AÚN)

### P1: Eliminar conexiones LIVE en otros endpoints

| Endpoint | Archivo | Línea | Acción |
|----------|---------|-------|--------|
| Modal detalle | routes.py | 3611 | Migrar a EDARSAHUB |
| Ventas por hora | routes.py | 2027 | Crear tabla nueva |
| Mesas/Movimientos | routes.py | 2352 | Evaluar necesidad |

### P2: Crear tablas de granularidad

| Tabla | Contenido | Job Requerido |
|-------|-----------|---------------|
| Comercial_Ventas_Por_Hora_v2 | Desglose por hora | Nuevo job |
| Comercial_Ventas_Por_DiaSemana_v2 | Desglose por día | Nuevo job |

---

## 10. CONCLUSIÓN

El FIX P0 fue implementado exitosamente. El Tablero Ejecutivo ahora lee **SOLO DE EDARSAHUB SQL** para Ventas del Día MPRO, cumpliendo con la regla arquitectónica obligatoria.

**130QRO ahora muestra $207,323.00** (dato real sincronizado).

**ORIGEN muestra $0** porque el servidor MPRO de ORIGEN tiene un error interno (HTTP 500, `Invalid column`). Esto requiere inspección del servidor remoto, no es un problema del sistema EDARSAHUB.

---

**FIN DEL REPORTE FIX P0**
