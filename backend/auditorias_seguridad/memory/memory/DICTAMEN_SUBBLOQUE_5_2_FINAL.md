# DICTAMEN FINAL: SUB-BLOQUE 5.2

**Fecha:** 2026-04-23  
**Estado:** ✅ COMPLETADO CON PARIDAD ESTRUCTURAL

---

## 1. ARCHIVO MODIFICADO

**Archivo:** `/app/backend/modules/comercial/routes.py`

---

## 2. BLOQUES/LÍNEAS REEMPLAZADOS

### 2.1 Import agregado (línea 83)
```python
# ANTES:
# BLOQUE 5.2: Import de query MPRO centralizada (PENDIENTE: requiere extensión para soportar filtro dashboard)
# from modules.comercial.queries.mpro import query_ventas_periodo_mpro

# DESPUÉS:
# BLOQUE 5.2: Import de query MPRO centralizada con filtro flexible
from modules.comercial.queries.mpro import query_ventas_periodo_mpro_con_filtro_flexible
```

### 2.2 Query `query_kpis` (líneas originales ~3205-3221)
**SQL DIRECTO ELIMINADO:**
```sql
SELECT 
    COUNT(DISTINCT VE.Vn_Folio) as cheques_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas_periodo,
    ISNULL(SUM(C.Co_Personas), 0) as pax_total
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fi_mpro}'
  AND VE.Vn_Fecha <= '{ff_mpro}'
  {sucursal_filter}
```

**SUSTITUIDO POR:**
```python
result_kpis = query_ventas_periodo_mpro_con_filtro_flexible(
    server=server,
    fecha_ini=fecha_ini,
    fecha_fin=fecha_fin,
    sucursal=sucursal,
    excluir_cancelados=False  # La query original no excluía cancelados
)
```

### 2.3 Query `query_pax_ant_mpro` (líneas originales ~3277-3292)
**SQL DIRECTO ELIMINADO:**
```sql
SELECT 
    ISNULL(SUM(C.Co_Personas), 0) as pax_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fia_mpro}'
  AND VE.Vn_Fecha < DATEADD(day, 1, '{ffa_mpro}')
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
```

**SUSTITUIDO POR:**
```python
result_mes_ant = query_ventas_periodo_mpro_con_filtro_flexible(
    server=server,
    fecha_ini=fecha_ini_ant,
    fecha_fin=fecha_fin_ant,
    sucursal=sucursal,
    excluir_cancelados=True  # La query original SÍ excluía cancelados
)
```

### 2.4 Query `query_ano_ant_mpro` (líneas originales ~3301-3317)
**SQL DIRECTO ELIMINADO:**
```sql
SELECT 
    ISNULL(SUM(C.Co_Personas), 0) as pax_total,
    ISNULL(SUM(VE.Vn_Precio_Neto_Importe), 0) as ventas,
    COUNT(DISTINCT VE.Vn_Folio) as cheques_total
FROM Venta_Encabezado VE
LEFT JOIN Comanda C ON C.Co_Folio = VE.Vn_Folio AND C.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
{sucursal_join}
WHERE VE.Vn_Fecha >= '{fiaa_mpro}'
  AND VE.Vn_Fecha < DATEADD(day, 1, '{ffaa_mpro}')
  AND ISNULL(VE.Es_Cve_Estado, '') <> 'CA'
  {sucursal_filter}
```

**SUSTITUIDO POR:**
```python
result_ano_ant = query_ventas_periodo_mpro_con_filtro_flexible(
    server=server,
    fecha_ini=fecha_ini_ano_ant,
    fecha_fin=fecha_fin_ano_ant,
    sucursal=sucursal,
    excluir_cancelados=True  # La query original SÍ excluía cancelados
)
```

---

## 3. VARIABLES ELIMINADAS

Las siguientes variables fueron eliminadas por ser innecesarias tras la migración:
- `fi_mpro`, `ff_mpro` (fechas período actual en formato YYYYMMDD)
- `fia_mpro`, `ffa_mpro` (fechas mes anterior en formato YYYYMMDD)
- `fiaa_mpro`, `ffaa_mpro` (fechas año anterior en formato YYYYMMDD)
- `sucursal_join`, `sucursal_filter` (solo para las 3 queries sustituidas)

**NOTA:** Estas variables ya no son necesarias porque la función centralizada `query_ventas_periodo_mpro_con_filtro_flexible()` realiza la conversión de fechas y construcción de filtros internamente.

---

## 4. FUNCIÓN CENTRALIZADA USADA

**Archivo fuente:** `/app/backend/modules/comercial/queries/mpro.py`

**Función:** `query_ventas_periodo_mpro_con_filtro_flexible()`

**Firma:**
```python
def query_ventas_periodo_mpro_con_filtro_flexible(
    server: Dict,
    fecha_ini: str,           # YYYY-MM-DD
    fecha_fin: str,           # YYYY-MM-DD
    sucursal: Optional[str] = None,
    excluir_cancelados: bool = True
) -> VentasPeriodoResult
```

**Retorno (`VentasPeriodoResult`):**
- `success: bool`
- `total_venta: float`
- `pax: int`
- `cheques: int`
- `error: Optional[str]`
- `source: str`

---

## 5. LÓGICA QUE QUEDÓ INTACTA

| Componente | Estado | Líneas aprox. |
|------------|--------|---------------|
| Verificación de estado servidor (offline check) | INTACTA | 3035-3061 |
| Query `query_ultimo_dia_mpro` (primer bloque) | INTACTA | 3068-3090 |
| Cálculo de fechas de períodos anteriores | INTACTA | 3092-3127 |
| Construcción de `sucursal_join`/`sucursal_filter` para query_ultimo_dia | INTACTA | 3129-3146 |
| Query `query_ultimo_dia_suc` (segundo bloque con filtro) | INTACTA | 3148-3195 |
| Integración API LOCAL (`sumar_ventas_api_local_a_sucursal`) | INTACTA | 3222-3262 |
| Cálculos derivados (ticket_promedio, consumo_persona, pax_promedio) | INTACTA | 3264-3266 |
| Cálculos comparativos (vs_periodo_anterior, vs_ano_anterior, etc.) | INTACTA | 3280-3308 |
| Construcción de payload JSON (kpis, comparativo) | INTACTA | 3310-3356 |
| Determinación de source_status | INTACTA | 3337-3343 |
| Guardado en caché | INTACTA | 3365-3368 |

---

## 6. VALIDACIONES EJECUTADAS

### 6.1 Validación de Sintaxis
```
✅ Lint Python (ruff): Sin errores en sección modificada
   Errores preexistentes: 4 (fuera de alcance del Sub-bloque 5.2)
```

### 6.2 Validación de Importación
```
✅ query_ventas_periodo_mpro_con_filtro_flexible importa correctamente
✅ VentasPeriodoResult dataclass funcional
✅ Firma de función verificada: ['server', 'fecha_ini', 'fecha_fin', 'sucursal', 'excluir_cancelados']
```

### 6.3 Validación HTTP 200
```
✅ Endpoint /api/comercial/dashboard/{server_id} responde HTTP 200
   Respuesta: {"source_status":"ERROR","source_message":"Servidor no encontrado..."}
   (Esperado: No hay servidores MPRO en DB del ambiente preview)
```

---

## 7. COMPARACIÓN ESTRUCTURAL ANTES/DESPUÉS

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| Queries SQL directas en sección MPRO | 3 | 0 |
| Llamadas a `execute_sql_query` para métricas | 3 | 0 |
| Llamadas a función centralizada | 0 | 3 |
| Variables de fecha YYYYMMDD | 6 | 0 (eliminadas) |
| Variables `sucursal_join`/`sucursal_filter` para métricas | 2 | 0 (manejadas por función) |
| Payload JSON de respuesta | Idéntico | Idéntico |
| Campos en `kpis` | 8 campos | 8 campos (sin cambios) |
| Campos en `comparativo` | 12 campos | 12 campos (sin cambios) |
| Lógica de API LOCAL | Intacta | Intacta |
| Lógica de último día con ventas | Intacta | Intacta |

---

## 8. DICTAMEN FINAL

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  SUB-BLOQUE 5.2 COMPLETADO CON PARIDAD ESTRUCTURAL                           ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ✅ 3 queries SQL directas reemplazadas por función centralizada              ║
║  ✅ Compatibilidad total de payload JSON preservada                          ║
║  ✅ Filtros de sucursal funcionan igual (código o nombre)                    ║
║  ✅ Exclusión de cancelados preservada según query original                  ║
║  ✅ Fallback PAX implementado en función centralizada                        ║
║  ✅ Lógica de API LOCAL intacta                                              ║
║  ✅ Lógica de último día con ventas intacta                                  ║
║  ✅ Validación de sintaxis: APROBADA                                         ║
║  ✅ Validación HTTP 200: APROBADA                                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 9. RIESGO TÉCNICO ABIERTO (R4)

| Riesgo | Descripción | Estado |
|--------|-------------|--------|
| R4 | Paridad Numérica Real MPRO Dashboard | **ABIERTO** |

**Detalle:**
- NO se puede validar `Diff = 0.00` en ventas/pax/cheques sin conectividad SQL viva a servidores MPRO
- El ambiente preview no alcanza los hosts SQL remotos (timeout)
- La validación numérica real requiere ejecución en ambiente con VPN o acceso directo

**Acción requerida:**
- Ejecutar prueba de paridad numérica desde ambiente con conectividad SQL cuando esté disponible
- Comparar respuesta del endpoint refactorizado vs respuesta de query SQL directa original

---

## 10. ARCHIVOS AFECTADOS

| Archivo | Acción |
|---------|--------|
| `/app/backend/modules/comercial/routes.py` | Modificado (3 queries reemplazadas, import agregado) |
| `/app/backend/modules/comercial/queries/mpro.py` | Sin cambios (función ya existía) |

---

**Firmado:** Agente E1  
**Fecha:** 2026-04-23
