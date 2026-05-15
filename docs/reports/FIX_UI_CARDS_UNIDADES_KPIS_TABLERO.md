# FIX UI: Cards de Unidades KPIs - Tablero Ejecutivo

**Fecha**: 2026-05-15  
**Estado**: COMPLETADO ✅

---

## 1. Resumen Ejecutivo

Se corrigió la distribución visual de los cards de unidades en el Tablero Ejecutivo Comercial para mostrar los KPIs en el orden solicitado:
- Proyección ahora aparece directamente debajo de Ventas
- PAX Promedio aparece debajo de PAX
- Cheque Promedio aparece debajo de Cheques

Adicionalmente, se añadió el cálculo de promedios (PAX Prom. y Cheque Prom.) cuando el endpoint V1 no los incluye.

---

## 2. Archivo(s) Modificados

| Archivo | Tipo de Cambio |
|---------|---------------|
| `/app/frontend/src/pages/TableroEjecutivo.js` | Redistribución visual del componente `UnidadCard` + Cálculo de promedios en fallback V1 |

---

## 3. Antes/Después de la Distribución Visual

### ANTES:
```
┌─────────────────────────────────┐
│ ● CIENFUEGOS               >   │
├─────────────────────────────────┤
│ Ventas                  $2.08M │
│ vs Mes Ant.            +42.6%  │
│ vs Año Ant.             -9.5%  │
├─────────────────────────────────┤
│ PAX        │ Cheques           │
│ 1,603      │ 511               │
│────────────│───────────────────│
│ Cheque Prom│ Proyección        │  ❌ Proyección abajo
│ $4.06K     │ $4.95M            │  ❌ PAX Prom faltante
└─────────────────────────────────┘
```

### DESPUÉS:
```
┌─────────────────────────────────┐
│ ● CIENFUEGOS               >   │
├─────────────────────────────────┤
│ Ventas                  $2.08M │
│ Proyección              $4.95M │  ✅ Debajo de Ventas
├─────────────────────────────────┤
│ vs Mes Ant.            +42.6%  │
│ vs Año Ant.             -9.5%  │
├─────────────────────────────────┤
│ PAX        │ Cheques           │
│ 1,603      │ 511               │
│────────────│───────────────────│
│ PAX Prom.  │ Cheque Prom.      │  ✅ PAX Prom debajo PAX
│ $1.30K     │ $4.06K            │  ✅ Cheque Prom debajo Cheques
└─────────────────────────────────┘
```

---

## 4. Campos Usados por el Card

| Campo | Fuente | Status |
|-------|--------|--------|
| `ventas` | V1/V2 | ✅ Disponible |
| `proyeccion` | Calculado frontend | ✅ Calculado |
| `var_vs_mes_ant` | V1/V2 | ✅ Disponible |
| `var_vs_año_ant` | V1/V2 | ✅ Disponible |
| `pax` | V1/V2 | ✅ Disponible |
| `cheques` | V1/V2 | ✅ Disponible |
| `pax_promedio` | V2 o Calculado | ✅ Ahora calculado si V1 |
| `cheque_promedio` | V2 o Calculado | ✅ Ahora calculado si V1 |

---

## 5. Campos Faltantes

**Ninguno**. Todos los campos requeridos están disponibles o se calculan en el frontend:

- `pax_promedio`: Si V1 retorna `null`, se calcula como `ventas / pax`
- `cheque_promedio`: Si V1 retorna `null`, se calcula como `ventas / cheques`

---

## 6. Confirmación: NO se Modificó Sincronización

- ❌ NO se modificó `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py`
- ❌ NO se modificó ningún job de APScheduler
- ❌ NO se modificaron queries SQL de sincronización
- ❌ NO se modificó la lógica de `get_operational_window()`

---

## 7. Confirmación: NO se Reactivó LIVE

- ❌ NO se añadieron llamadas a APIs locales MPRO
- ❌ NO se añadieron llamadas a SoftRestaurant en vivo
- ❌ NO se modificó `sumar_ventas_api_local_a_sucursal()`
- ✅ El tablero sigue leyendo ÚNICAMENTE de EDARSAHUB SQL (via endpoint V1/V2)

---

## 8. Validación Visual

### CIENFUEGOS:
| KPI | Valor | Status |
|-----|-------|--------|
| Ventas | $2.08M | ✅ Verde |
| Proyección | $4.95M | ✅ Naranja, debajo de Ventas |
| vs Mes Ant. | +42.6% | ✅ |
| vs Año Ant. | -9.5% | ✅ |
| PAX | 1,603 | ✅ |
| Cheques | 511 | ✅ |
| PAX Prom. | $1.30K | ✅ Debajo de PAX |
| Cheque Prom. | $4.06K | ✅ Debajo de Cheques |

### 130° QUERÉTARO:
| KPI | Valor | Status |
|-----|-------|--------|
| Ventas | $1.53M | ✅ |
| Proyección | $3.38M | ✅ Debajo de Ventas |
| PAX | 865 | ✅ |
| Cheques | 322 | ✅ |
| PAX Prom. | $1.76K | ✅ |
| Cheque Prom. | $4.74K | ✅ |

### ORIGEN:
| KPI | Valor | Status |
|-----|-------|--------|
| Ventas | $1.08M | ✅ (dato real de EDARSAHUB) |
| Proyección | $2.39M | ✅ Debajo de Ventas |
| vs Mes Ant. | +41.3% | ✅ |

---

## 9. Pruebas Realizadas

1. **Screenshot post-fix**: Captura visual confirma nueva distribución
2. **Console logs**: Verificado que usa EDARSAHUB via V1 (V2 dashboard tiene error 500)
3. **Cálculo de promedios**: Confirmado que se calculan cuando V1 no los incluye
4. **Click en card**: Funcionalidad de drill-down preservada (no modificada)

---

## 10. Riesgos Pendientes

1. **Endpoint V2 /dashboard con error 500**: El endpoint `/api/v2/comercial/dashboard` retorna error 500, forzando fallback a V1. Esto NO fue corregido porque está fuera del alcance autorizado.

2. **Deuda técnica V1**: El endpoint V1 no calcula promedios. Se añadió cálculo en frontend como workaround temporal.

---

## 11. Código Modificado

### Componente UnidadCard - Nueva distribución (líneas 366-432):

```jsx
<div className="space-y-2">
  {/* BLOQUE PRINCIPAL: Ventas + Proyección */}
  <div className="flex justify-between items-center">
    <span className="text-xs text-zinc-500">Ventas</span>
    <span className="font-bold text-green-600">{formatCurrency(unidad.ventas)}</span>
  </div>
  
  {hasValidData && (
    <div className="flex justify-between items-center">
      <span className="text-xs text-zinc-500">Proyección</span>
      <span className="font-semibold text-orange-600">{formatCurrency(unidad.proyeccion)}</span>
    </div>
  )}
  
  {/* BLOQUE COMPARATIVOS */}
  {hasValidData && (
    <div className="border-t pt-2 mt-2 space-y-1">
      {!esMultiMes && (
        <div className="flex justify-between items-center">
          <span className="text-xs text-zinc-500">vs Día/Mes Ant.</span>
          <VariacionBadge valor={unidad.var_vs_mes_ant} />
        </div>
      )}
      <div className="flex justify-between items-center">
        <span className="text-xs text-zinc-500">vs Año Ant.</span>
        <VariacionBadge valor={unidad.var_vs_año_ant} />
      </div>
    </div>
  )}
  
  {/* BLOQUE OPERATIVO: 2 columnas */}
  {hasValidData && (
    <div className="border-t pt-2 mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
      <div>
        <span className="text-zinc-500">PAX</span>
        <p className="font-semibold">{unidad.pax?.toLocaleString()}</p>
      </div>
      <div>
        <span className="text-zinc-500">Cheques</span>
        <p className="font-semibold">{unidad.cheques?.toLocaleString()}</p>
      </div>
      <div>
        <span className="text-zinc-500">PAX Prom.</span>
        <p className="font-semibold">{unidad.pax_promedio ? formatCurrency(unidad.pax_promedio) : '-'}</p>
      </div>
      <div>
        <span className="text-zinc-500">Cheque Prom.</span>
        <p className="font-semibold">{formatCurrency(unidad.cheque_promedio)}</p>
      </div>
    </div>
  )}
</div>
```

### Cálculo de promedios en fallback V1 (líneas 1037-1050):

```javascript
// FIX UI 15-May-2026: Calcular promedios si V1 no los incluye
if (responseData?.unidades) {
  responseData.unidades = responseData.unidades.map(u => ({
    ...u,
    cheque_promedio: u.cheque_promedio ?? (u.cheques > 0 ? u.ventas / u.cheques : null),
    pax_promedio: u.pax_promedio ?? (u.pax > 0 ? u.ventas / u.pax : null)
  }));
}
```

---

## Resumen Final

| Criterio | Status |
|----------|--------|
| Proyección debajo de Ventas | ✅ |
| PAX Prom. debajo de PAX | ✅ |
| Cheque Prom. debajo de Cheques | ✅ |
| Promedios calculados cuando faltan | ✅ |
| NO se modificó sincronización | ✅ |
| NO se reactivó LIVE | ✅ |
| NO se usaron datos mock | ✅ |
| Tablero lee EDARSAHUB SQL | ✅ |
| Click en card funcional | ✅ |

**FIX UI COMPLETADO EXITOSAMENTE**
