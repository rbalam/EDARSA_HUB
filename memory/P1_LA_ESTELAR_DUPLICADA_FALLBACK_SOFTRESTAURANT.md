# P1 — LA ESTELAR DUPLICADA POR FALLBACK SOFTRESTAURANT / CONEXIÓN FALLIDA

**Fecha:** 2025-12-13
**Prioridad:** P1
**Estado:** DIAGNOSTICADO - PENDIENTE AUTORIZACIÓN
**Relacionado con:** FIX P0 EDARSA/Unidad Desconocida (CERRADO)

---

## DESCRIPCIÓN DEL BUG

El endpoint de Tablero Ejecutivo devuelve **6 registros** cuando visualmente deberían existir solo **5 unidades**. La sexta entrada es un duplicado de LA ESTELAR generado cuando el flujo SoftRestaurant combina:
- Una entrada con caché válido (`DATA_FROM_CACHE`)
- Otra entrada de error/conexión fallida (`DATA_ERROR`)

---

## SÍNTOMA

### Respuesta actual del endpoint:
```
Total unidades: 6

  ✓ CIENFUEGOS (CIENFUEGOS)
  ✓ 130° MERIDA (130MID)
  ✓ 130° QUERETARO (130QRO)
  ✓ LA ESTELAR (ESTELAR)      ← data_status: DATA_FROM_CACHE
  ✓ ORIGEN (ORIGEN)
  ✓ LA ESTELAR ()              ← data_status: DATA_ERROR, código VACÍO
```

### Lo esperado:
```
Total unidades: 5

  ✓ CIENFUEGOS (CIENFUEGOS)
  ✓ 130° MERIDA (130MID)
  ✓ 130° QUERETARO (130QRO)
  ✓ LA ESTELAR (ESTELAR)      ← una sola entrada con metadata de estado
  ✓ ORIGEN (ORIGEN)
```

---

## CAUSA PROBABLE

El flujo SoftRestaurant en `/app/backend/modules/comercial/routes.py` **no deduplica por `unidad_negocio_codigo`** cuando combina:

1. Datos válidos desde caché/EDARSAHUB snapshot
2. Errores de conexión live
3. Fallback status entries

Cuando la conexión a LA ESTELAR falla, el sistema genera:
1. Una entrada con datos del caché
2. Una entrada separada del bloque de error

Ambas se agregan a `resultados[]` sin verificar si ya existe una entrada para ese `unidad_negocio_codigo`.

---

## REGLA CORRECTA

**Cada unidad de negocio debe aparecer UNA SOLA VEZ en el response.**

### Llave de deduplicación:
- `unidad_negocio_codigo` (de EDARSAHUB.Unidades_Negocio)

### Para LA ESTELAR:
- Código canónico: `ESTELAR`
- server_id: `a5ff0e25-f029-43db-b634-d4ac814c904f`

### Comportamiento esperado:
- Si existe una entrada con datos válidos y otra de error:
  - Conservar la entrada con datos válidos
  - Agregar metadata de estado si aplica (`live_status`, `cache_warning`)
  - **NO crear una segunda unidad**
  - **NO devolver código vacío**

---

## ENDPOINT AFECTADO

- `GET /api/comercial/tablero-ejecutivo`

---

## ARCHIVOS A REVISAR

| Archivo | Función/Área | Descripción |
|---------|--------------|-------------|
| `/app/backend/modules/comercial/routes.py` | `_tablero_ejecutivo_internal()` | Flujo principal que construye `resultados[]` |
| `/app/backend/modules/comercial/routes.py` | Bloques SoftRestaurant (~líneas 677-1041) | Múltiples puntos donde se hace `resultados.append()` |
| `/app/backend/modules/comercial/service.py` | `build_unit_response()` | Construye la estructura de cada unidad |

---

## DIAGNÓSTICO REQUERIDO

### Antes de modificar, revisar:

1. **Identificar TODOS los puntos** donde se hace `resultados.append(unit_response)` en el flujo SoftRestaurant
2. **Confirmar** por qué LA ESTELAR se agrega dos veces:
   - ¿Viene del flujo de error (líneas ~757-845)?
   - ¿Viene del flujo de caché (líneas ~847-888)?
   - ¿Viene del flujo "silent fail" (líneas ~933-1001)?
3. **Verificar** si existe deduplicación final por `unidad_negocio_codigo`
4. **Revisar** cómo se asigna `unidad_negocio_codigo` cuando hay error

---

## PROPUESTA DE FIX

### Opción A: Deduplicación final antes de retornar

```python
# Al final de _tablero_ejecutivo_internal(), antes de construir response:

# Deduplicar por unidad_negocio_codigo
unidades_dedup = {}
for unidad in resultados:
    codigo = unidad.get('unidad_negocio_codigo') or unidad.get('server_id')
    
    if codigo not in unidades_dedup:
        unidades_dedup[codigo] = unidad
    else:
        # Si ya existe, priorizar la que tenga datos válidos
        existente = unidades_dedup[codigo]
        if unidad.get('data_status') == 'DATA_OK' and existente.get('data_status') != 'DATA_OK':
            unidades_dedup[codigo] = unidad
        # Si la nueva tiene error y la existente tiene datos, conservar existente
        
resultados = list(unidades_dedup.values())
```

### Opción B: Evitar duplicación en origen

Modificar los bloques de error para verificar si ya se agregó una entrada para ese `server_id`:

```python
# Antes de cada resultados.append() en flujos de error
server_ids_agregados = {u.get('server_id') for u in resultados}
if server['id'] not in server_ids_agregados:
    resultados.append(unit_response)
```

---

## VALIDACIONES POST-FIX

1. ✅ Endpoint debe devolver exactamente **5 unidades**
2. ✅ LA ESTELAR debe aparecer **una sola vez**
3. ✅ LA ESTELAR debe conservar datos correctos o caché válido
4. ✅ Si hay error de conexión, debe quedar como metadata (`live_status`, `cache_warning`), no como unidad duplicada
5. ✅ EDARSA no debe reaparecer
6. ✅ "Unidad Desconocida" no debe reaparecer
7. ✅ 130QRO y ORIGEN deben seguir correctos
8. ✅ No MongoDB
9. ✅ No frontend
10. ✅ No regresión en Finanzas/Compras/Comercial V2

---

## MÁXIMAS OBLIGATORIAS

1. EDARSAHUB es el cerebro del sistema
2. `Unidades_Negocio.codigo` es la llave canónica
3. No usar nombres visibles como llave
4. No usar MongoDB
5. No tocar MPRO/EDARSA ya corregido
6. No tocar frontend inicialmente
7. No romper Comercial V2
8. No romper Tablero Ejecutivo (solo corregir duplicación)
9. No romper Finanzas
10. No romper Compras

---

## ESTADO

- [x] Bug identificado
- [x] Causa probable documentada
- [x] Propuesta de fix definida
- [ ] Diagnóstico detallado (pendiente)
- [ ] Autorización para implementar
- [ ] Implementación
- [ ] Testing
- [ ] Validación usuario

---

## NOTAS

- Este issue es **SEPARADO** del FIX P0 EDARSA/Unidad Desconocida
- El FIX P0 está **CERRADO** y funcionando correctamente
- Este P1 afecta solo al flujo SoftRestaurant, no a MPRO
- La prioridad es P1 porque no rompe el tablero pero genera inconsistencia visual
