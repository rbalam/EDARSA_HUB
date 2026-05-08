# PROPUESTA: Corrección Arquitectónica — "Fuente No Disponible"

**Fecha:** 06-Mayo-2026  
**Prioridad:** P0 CRÍTICO  
**Componente:** Dashboard Comercial (Tablero Ejecutivo)

---

## 1. PROBLEMA IDENTIFICADO

El Dashboard Comercial muestra unidades como "Fuente no disponible - datos no confirmados" cuando el servidor SQL externo no responde, incluso cuando **EDARSAHUB ya tiene snapshots válidos** de esas unidades.

### Causa Raíz

En `/app/backend/modules/comercial/routes.py` líneas 625-641 y 732-747:

```python
if solo_ventas_dia:
    # LIVE-C: NO usar caché para evitar ceros falsos
    unit_response = build_unit_response(
        ...
        error_message="Fuente no disponible - datos no confirmados",
    )
```

Cuando `solo_ventas_dia=True` y la conexión falla, el código **no intenta** buscar datos en EDARSAHUB como fallback.

---

## 2. ARQUITECTURA EXISTENTE

### Tablas en EDARSAHUB

| Tabla | Propósito | Frecuencia Sync |
|-------|-----------|-----------------|
| `Comercial_Ventas_Dia_Abiertas_v2` | Snapshot ventas sin corte | 5 min |
| `Comercial_KPIs_Diarios_v2` | KPIs cerrados por día | 15 min |
| `Comercial_SyncLog_v2` | Bitácora de sincronización | Cada sync |

### Jobs de Sincronización

| Job | Intervalo | Función |
|-----|-----------|---------|
| `sync_comercial_abiertas_v2` | 5 min | Sincroniza ventas abiertas (tempcheques) |
| `sync_comercial_v2` | 15 min | Sincroniza KPIs cerrados |

---

## 3. SOLUCIÓN PROPUESTA

### Flujo Corregido para `solo_ventas_dia=True`

```
1. Intentar conexión en vivo a servidor externo
   |
   ├── ÉXITO:
   │   - Mostrar datos en vivo
   │   - data_status = DATA_OK
   │   - live_status = LIVE_CONNECTED
   │
   └── ERROR:
       - Buscar snapshot en Comercial_Ventas_Dia_Abiertas_v2
       |
       ├── SNAPSHOT EXISTE:
       │   - Mostrar último snapshot válido
       │   - data_status = DATA_FROM_EDARSAHUB_SNAPSHOT
       │   - live_status = LIVE_UNAVAILABLE
       │   - Mostrar advertencia amarilla: "Última sync: HH:mm"
       │
       └── SIN SNAPSHOT:
           - data_status = NO_DATA_TODAY
           - Mostrar advertencia: "Sin datos del día en EDARSAHUB"
```

### Separación de Conceptos

| Campo | Descripción |
|-------|-------------|
| `estado_conexion` | ONLINE / OFFLINE / ERROR (servidor externo) |
| `estado_dato` | VIGENTE / DESACTUALIZADO / SIN_DATOS_HOY / ERROR_SYNC (dato en EDARSAHUB) |

El frontend debe basar su visualización en `estado_dato`, no en `estado_conexion`.

---

## 4. ARCHIVOS A MODIFICAR

### Backend

1. **`/app/backend/modules/comercial/routes.py`**
   - Agregar fallback a EDARSAHUB cuando `solo_ventas_dia=True` y conexión falla
   - Nueva función: `get_ventas_dia_from_edarsahub_fallback()`
   - Modificar líneas 620-750 aproximadamente

2. **`/app/backend/modules/comercial/cache_service.py`** (opcional)
   - Agregar helper para obtener estado de frescura del snapshot

### Frontend

3. **Componente de estado de unidad** (si aplica)
   - Cambiar lógica de colores: 
     - Verde: datos vigentes
     - Amarillo: datos desactualizados pero válidos
     - Rojo: sin datos en EDARSAHUB

---

## 5. CRITERIOS DE FRESCURA

| Condición | Estado |
|-----------|--------|
| Snapshot < 15 min | VIGENTE |
| Snapshot 15-60 min | DESACTUALIZADO |
| Snapshot > 60 min | MUY_DESACTUALIZADO |
| Sin snapshot del día | SIN_DATOS_HOY |

---

## 6. CRITERIO DE ACEPTACIÓN

1. ✅ Cuando servidor externo está ONLINE:
   - Dashboard muestra datos en vivo

2. ✅ Cuando servidor externo está OFFLINE pero EDARSAHUB tiene snapshot:
   - Dashboard muestra último snapshot válido
   - Muestra advertencia amarilla "Última sync: HH:mm"
   - NO muestra "Fuente no disponible"
   - NO pone ventas en cero

3. ✅ Cuando servidor externo está OFFLINE y NO hay snapshot en EDARSAHUB:
   - Dashboard muestra "Sin datos del día en EDARSAHUB"
   - Advertencia roja (pero informativa, no "fuente no disponible")

4. ✅ Los totales del dashboard solo suman unidades con datos válidos

---

## 7. NO TOCAR

- Comercial V2 (aislado)
- Tablero Ejecutivo (menú/tabs)
- Compras
- Finanzas / Cuentas Bancarias
- Auth / RBAC
- Filtros por unidad de negocio existentes

---

## 8. PRUEBAS OBLIGATORIAS

| Servidor | Escenario |
|----------|-----------|
| 130° QUERÉTARO | Online → verificar datos en vivo |
| ORIGEN | Online → verificar datos en vivo |
| 130° MÉRIDA | Simular offline → verificar fallback EDARSAHUB |
| CIENFUEGOS | Simular offline → verificar fallback EDARSAHUB |
| LA ESTELAR | Simular offline → verificar fallback EDARSAHUB |

---

**DICTAMEN SOLICITADO:**
¿Autoriza implementar esta corrección arquitectónica?
