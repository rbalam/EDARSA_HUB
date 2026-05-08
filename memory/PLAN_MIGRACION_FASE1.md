# PLAN DE MIGRACIÓN FASE 1: CENTRALIZACIÓN DE QUERIES BASE

**Fecha:** 2026-04-23  
**Versión:** 1.1 (Actualizado 2026-04-23)  
**Estado:** BLOQUE 4 INTEGRACIÓN COMPLETADA - PARIDAD NUMÉRICA PENDIENTE  
**Prioridad:** Quirúrgica, sin regresión

---

## ESTADO ACTUAL DE EJECUCIÓN

| Bloque | Descripción | Estado | Fecha |
|--------|-------------|--------|-------|
| 1 | Estructura de carpetas queries/ | ✅ COMPLETADO | 2026-04-23 |
| 2 | query_ventas_periodo_sr (paridad estructural) | ✅ COMPLETADO | 2026-04-23 |
| 3 | query_ventas_periodo_mpro (paridad estructural) | ✅ COMPLETADO | 2026-04-23 |
| 4 | Migrar service.py a queries centralizadas | 🟡 INTEGRACIÓN OK / PARIDAD NUMÉRICA PENDIENTE | 2026-04-23 |
| 5 | Migrar routes.py (pendiente autorización) | ⏳ PENDIENTE | - |

### ⚠️ RIESGO ABIERTO BLOQUE 4
- La paridad numérica exacta (ventas, pax, cheques) NO quedó validada con contraste real contra SQL vivo
- La no regresión operativa total queda pendiente de validación en ambiente con conectividad efectiva a servidores SR y MPRO
- **Acción requerida**: Validar en producción que las funciones migradas produzcan exactamente las mismas cifras

---

## 1. OBJETIVO FASE 1

Centralizar las queries duplicadas de métricas base en una nueva capa `queries/` **SIN cambiar el comportamiento funcional** de ningún endpoint.

### Criterios de éxito
- [ ] Mismos payloads JSON de salida
- [ ] Mismos filtros funcionando
- [ ] Mismos permisos RBAC
- [ ] Mismas rutas públicas
- [ ] Cero regresión en cifras

---

## 2. QUERIES A CENTRALIZAR (ORDEN DE PRIORIDAD)

### 2.1 VENTAS_TOTAL (27 ocurrencias - PRIORIDAD 1)

#### Variantes detectadas en código actual:

| # | Ubicación | Línea | Query SQL | Clasificación |
|---|-----------|-------|-----------|---------------|
| 1 | service.py | 344 | `ISNULL(SUM(cheques.total), 0) as ventas` | ✅ BASE - Usar como referencia |
| 2 | service.py | 393 | `ISNULL(SUM(cheques.total), 0) as ventas` | DUPLICADA de #1 |
| 3 | service.py | 409 | `ISNULL(SUM(cheques.total), 0) as ventas` | DUPLICADA de #1 |
| 4 | service.py | 549 | `ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as ventas` (MPRO) | ✅ BASE MPRO |
| 5 | routes.py | 744 | `SUM(cheques.total) as real_ventas` | DUPLICADA (sin ISNULL) |
| 6 | routes.py | 1038 | `SUM(cheques.total) as ventas` | DUPLICADA (sin ISNULL) |
| 7 | routes.py | 1066 | `SUM(cheques.total) as ventas` | DUPLICADA |
| 8 | routes.py | 1705 | `SUM(cheques.total) as ventas_reales` | DUPLICADA |
| 9 | routes.py | 2878 | `SUM(cheques.total) as ventas_periodo` | DUPLICADA |
| 10 | routes.py | 2911 | `SUM(cheques.total) as ventas_periodo` | DUPLICADA |
| 11 | routes.py | 2927 | `SUM(cheques.total) as ventas` | DUPLICADA |
| 12 | routes.py | 2947 | `SUM(cheques.total) as ventas_periodo` | DUPLICADA |
| 13 | routes.py | 1114 | `SUM(VE.Vn_Precio_Neto_Importe) as ventas` (MPRO) | DUPLICADA de #4 |
| 14 | routes.py | 1144 | `SUM(VE.Vn_Precio_Neto_Importe) as ventas` (MPRO) | DUPLICADA de #4 |
| 15 | routes.py | 1946 | `ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_reales` | DUPLICADA de #4 |
| 16 | routes.py | 3236 | `ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_periodo` | DUPLICADA de #4 |
| 17 | routes.py | 3310 | `ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas` | DUPLICADA de #4 |

#### Función base propuesta:

```python
# Archivo: /app/backend/modules/comercial/queries/softrestaurant.py

def query_ventas_periodo_sr(
    server: Dict,
    fecha_ini: str,  # YYYY-MM-DD
    fecha_fin: str,
    sucursal_id: Optional[str] = None
) -> SafeQueryResult:
    """
    Query base ÚNICA de ventas para SoftRestaurant.
    
    Retorna: total_venta, pax, cheques
    
    CONSUMIDORES:
    - get_kpis_softrestaurant() en service.py
    - /comercial/dashboard/{server_id}
    - /comercial/ventas-tiempo/{server_id}
    - /comercial/reporte-pax/{server_id}
    """
    filtro_suc = f"AND cheques.idestacion = '{sucursal_id}'" if sucursal_id else ""
    
    f_ini = fecha_ini.replace('-', '')
    f_fin = fecha_fin.replace('-', '')
    
    query = f"""
    SELECT 
        ISNULL(SUM(cheques.total), 0) as total_venta,
        ISNULL(SUM(cheques.nopersonas), 0) as pax,
        COUNT(DISTINCT cheques.folio) as cheques
    FROM cheques
    INNER JOIN turnos ON turnos.idturno = cheques.idturno
    WHERE CONVERT(varchar, turnos.apertura, 112) >= '{f_ini}'
      AND CONVERT(varchar, turnos.apertura, 112) <= '{f_fin}'
      AND cheques.cancelado = 0
      {filtro_suc}
    """
    
    return execute_query_safe(
        server_config=server,
        query=query,
        expected_system_types=['SoftRestaurant'],
        module_name="COMERCIAL_VENTAS_SR"
    )
```

---

### 2.2 PAX_COMENSALES (20 ocurrencias - PRIORIDAD 2)

| # | Ubicación | Línea | Query SQL | Clasificación |
|---|-----------|-------|-----------|---------------|
| 1 | service.py | 345 | `ISNULL(SUM(cheques.nopersonas), 0) as pax` | ✅ BASE |
| 2 | routes.py | 1039 | `SUM(cheques.nopersonas) as pax` | DUPLICADA (sin ISNULL) |
| 3 | routes.py | 1221 | `ISNULL(SUM(cheques.nopersonas), 0) as comensales_mes` | DUPLICADA |
| 4 | routes.py | 2880 | `ISNULL(SUM(cheques.nopersonas), 0) as pax_total` | DUPLICADA |
| 5 | routes.py | 2927 | `ISNULL(SUM(cheques.nopersonas), 0) as pax_total` | DUPLICADA |
| 6 | routes.py | 2948 | `ISNULL(SUM(cheques.nopersonas), 0) as pax_total` | DUPLICADA |
| 7 | service.py | 877 | `ISNULL(SUM(C.Co_Personas), 0) as pax` (MPRO) | ✅ BASE MPRO |
| 8 | routes.py | 1115 | `ISNULL(SUM(C.Co_Personas), 0) as pax` (MPRO) | DUPLICADA de #7 |
| 9 | routes.py | 3237 | `ISNULL(SUM(C.Co_Personas), 0) as pax_total` (MPRO) | DUPLICADA de #7 |

**NOTA:** PAX está incluido en `query_ventas_periodo_sr()`. No requiere función separada.

---

### 2.3 CONTEO_CHEQUES (7 ocurrencias - PRIORIDAD 3)

| # | Ubicación | Línea | Query SQL | Clasificación |
|---|-----------|-------|-----------|---------------|
| 1 | service.py | 343 | `COUNT(DISTINCT cheques.folio) as cheques` | ✅ BASE |
| 2 | routes.py | 886 | `COUNT(DISTINCT cheques.folio) as tickets` | DUPLICADA |
| 3 | routes.py | 1220 | `COUNT(DISTINCT cheques.folio) as tickets_mes` | DUPLICADA |
| 4 | routes.py | 2877 | `COUNT(DISTINCT cheques.folio) as cheques` | DUPLICADA |

**NOTA:** CHEQUES está incluido en `query_ventas_periodo_sr()`. No requiere función separada.

---

### 2.4 CORTES_TURNOS (4 ocurrencias - PRIORIDAD 4)

| # | Ubicación | Línea | Contexto | Clasificación |
|---|-----------|-------|----------|---------------|
| 1 | service.py | 177 | tempcheques (ventas sin corte) | ✅ BASE - Específico ventas del día |
| 2 | service.py | 372 | turnos.apertura (filtro fecha) | ✅ BASE - Usado en todas las queries |
| 3 | routes.py | 2982 | tempcheques para ventas abiertas | DUPLICADA de #1 |
| 4 | repository.py | 173 | turnos para ventas por turno | ESPECÍFICO (Ticket Perfecto) |

#### Función base propuesta para ventas sin corte:

```python
# Archivo: /app/backend/modules/comercial/queries/softrestaurant.py

def query_ventas_sin_corte_sr(
    server: Dict,
    fecha_hoy: str,  # YYYY-MM-DD
    sucursal_id: Optional[str] = None
) -> SafeQueryResult:
    """
    Query base ÚNICA para ventas sin corte (tempcheques).
    Usado exclusivamente en modo "Ventas del Día" (LIVE-C).
    
    CONSUMIDORES:
    - get_kpis_softrestaurant() cuando solo_ventas_dia=True
    - /comercial/dashboard/{server_id} en modo ventas_dia
    """
    filtro_suc = f"AND idestacion = '{sucursal_id}'" if sucursal_id else ""
    f_hoy = fecha_hoy.replace('-', '')
    
    query = f"""
    SELECT 
        ISNULL(SUM(total), 0) as ventas_pendientes,
        ISNULL(SUM(nopersonas), 0) as pax_pendientes,
        COUNT(DISTINCT folio) as tickets_abiertos
    FROM tempcheques
    WHERE CONVERT(varchar, fecha, 112) = '{f_hoy}'
      AND cancelado = 0
      {filtro_suc}
    """
    
    return execute_query_safe(
        server_config=server,
        query=query,
        expected_system_types=['SoftRestaurant'],
        module_name="COMERCIAL_VENTAS_DIA_SR"
    )
```

---

## 3. ESTRUCTURA DE ARCHIVOS PROPUESTA

```
/app/backend/modules/comercial/
├── queries/                          # NUEVA CAPA A
│   ├── __init__.py                   # Exports públicos
│   ├── base.py                       # SafeQueryResult, helpers
│   ├── softrestaurant.py             # Queries SR homologadas
│   └── mpro.py                       # Queries MPRO homologadas
│
├── service.py                        # MODIFICAR: Importar de queries/
├── routes.py                         # MODIFICAR: Importar de queries/ (gradual)
├── repository.py                     # SIN CAMBIOS (tiene queries específicas)
├── kpis_repository.py                # SIN CAMBIOS (es para HUB)
└── ...
```

---

## 4. ORDEN DE IMPLEMENTACIÓN (BLOQUES PEQUEÑOS)

### BLOQUE 1: Infraestructura (0 riesgo)
1. Crear directorio `/app/backend/modules/comercial/queries/`
2. Crear `__init__.py` vacío
3. Crear `base.py` con imports y helpers
4. **Verificación:** Backend inicia sin errores

### BLOQUE 2: Query VENTAS_SR (bajo riesgo)
1. Crear `softrestaurant.py` con `query_ventas_periodo_sr()`
2. Agregar test unitario que compare resultado con query actual
3. **Verificación:** Test pasa, query devuelve mismos valores

### BLOQUE 3: Query VENTAS_MPRO (bajo riesgo)
1. Crear `mpro.py` con `query_ventas_periodo_mpro()`
2. Agregar test unitario
3. **Verificación:** Test pasa

### BLOQUE 4: Migrar service.py (medio riesgo)
1. Modificar `get_kpis_softrestaurant()` para usar `query_ventas_periodo_sr()`
2. Mantener query original comentada temporalmente
3. **Verificación:** Tablero Ejecutivo devuelve mismas cifras

### BLOQUE 5: Query VENTAS_DIA_SR (bajo riesgo)
1. Agregar `query_ventas_sin_corte_sr()` a `softrestaurant.py`
2. Test unitario
3. **Verificación:** Test pasa

### BLOQUE 6: Migrar service.py ventas_dia (medio riesgo)
1. Modificar `get_kpis_softrestaurant()` parte de `solo_ventas_dia=True`
2. **Verificación:** Tablero Ejecutivo modo "Ventas del Día" funciona igual

---

## 5. ENDPOINTS IMPACTADOS POR FASE

### Fase 1 - Impacto directo:
| Endpoint | Impacto | Riesgo |
|----------|---------|--------|
| `/comercial/tablero-ejecutivo` | Usa service.py | 🟡 Medio |

### Fase 1 - Sin impacto directo (queries aún en routes.py):
| Endpoint | Queries propias | Migración posterior |
|----------|-----------------|---------------------|
| `/comercial/dashboard/{server_id}` | 11 | Fase 2 |
| `/comercial/reporte-pax/{server_id}` | 8 | Fase 2 |
| `/comercial/precios-constantes/{server_id}` | 7 | Fase 2 |
| `/comercial/ventas-tiempo/{server_id}` | 4 | Fase 2 |
| `/comercial/mesas/{server_id}` | 4 | Fase 2 |

---

## 6. ESTRATEGIA DE PRUEBAS POR BLOQUE

### Para cada bloque:

```bash
# 1. Antes de cambio: Capturar respuesta actual
curl -s "$API_URL/api/comercial/tablero-ejecutivo?mes=4&anio=2026" \
  -H "Authorization: Bearer $TOKEN" > /tmp/antes.json

# 2. Aplicar cambio

# 3. Después de cambio: Capturar respuesta nueva
curl -s "$API_URL/api/comercial/tablero-ejecutivo?mes=4&anio=2026" \
  -H "Authorization: Bearer $TOKEN" > /tmp/despues.json

# 4. Comparar cifras clave
python3 << 'EOF'
import json
antes = json.load(open('/tmp/antes.json'))
despues = json.load(open('/tmp/despues.json'))

# Comparar totales
for key in ['ventas', 'pax', 'cheques']:
    v_antes = antes.get('totales', {}).get(key, 0)
    v_despues = despues.get('totales', {}).get(key, 0)
    diff = abs(v_antes - v_despues)
    status = "✅" if diff < 0.01 else "❌"
    print(f"{status} {key}: antes={v_antes}, después={v_despues}, diff={diff}")
EOF
```

---

## 7. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Diferencia en manejo de NULL | Media | Alto | Usar ISNULL() consistente en todas las queries |
| Diferencia en formato de fechas | Media | Alto | Estandarizar a CONVERT(varchar, col, 112) |
| Import circular | Baja | Medio | Estructura de imports clara en `__init__.py` |
| Regresión en filtro de sucursal | Media | Alto | Tests con y sin filtro de sucursal |
| Performance degradada | Baja | Medio | Benchmark antes/después |

---

## 8. CLASIFICACIÓN FINAL DE QUERIES

### ✅ BASE COMPARTIDA (centralizar en queries/)
- `query_ventas_periodo_sr()` - SoftRestaurant
- `query_ventas_periodo_mpro()` - MPRO
- `query_ventas_sin_corte_sr()` - Ventas del día SR
- `query_ventas_sin_corte_mpro()` - Ventas del día MPRO

### 🔵 ESPECÍFICA DE TABLERO (mantener donde está)
- Queries de Precios Constantes (cálculo inflacionario)
- Queries de Ticket Perfecto (métricas de calidad)
- Queries de Mesas (ocupación)
- Queries de Detalle Movimientos (drill-down)

### 🟡 DEBE MIGRARSE A HUB (Fase 3)
- Tablero Ejecutivo período cerrado → leer de `kpis_comercial`
- Dashboard Comercial período cerrado → leer de `kpis_comercial`

### 🔴 DEBE ELIMINARSE POR DUPLICIDAD (después de migración)
- 20+ queries duplicadas en routes.py (líneas listadas arriba)

### 🟢 REQUIERE CACHE (ya implementado)
- `dashboard_cache` en MongoDB
- `kpis_cache` en MongoDB

---

## 9. ENTREGABLES ESPERADOS POR BLOQUE

| Bloque | Archivos Creados/Modificados | Evidencia Requerida |
|--------|------------------------------|---------------------|
| 1 | `queries/__init__.py`, `queries/base.py` | Backend inicia |
| 2 | `queries/softrestaurant.py` | Test unitario pasa |
| 3 | `queries/mpro.py` | Test unitario pasa |
| 4 | `service.py` (líneas 340-420) | Comparación cifras Tablero |
| 5 | `queries/softrestaurant.py` (+ventas_dia) | Test unitario pasa |
| 6 | `service.py` (líneas 170-240) | Comparación cifras Ventas Día |

---

## 10. PRÓXIMOS PASOS INMEDIATOS

1. **Crear estructura de carpetas** (Bloque 1)
2. **Implementar `query_ventas_periodo_sr()`** (Bloque 2)
3. **Test de paridad** antes de migrar service.py
4. **Migrar service.py** gradualmente (Bloque 4)
5. **Reportar evidencia** de cada bloque

---

**ESPERANDO AUTORIZACIÓN PARA PROCEDER CON BLOQUE 1**
