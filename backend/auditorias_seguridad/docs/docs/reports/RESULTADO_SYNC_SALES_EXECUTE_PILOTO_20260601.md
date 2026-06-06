# RESULTADO SYNC_SALES --EXECUTE PILOTO 2026-06-01

**Fecha de ejecución:** 2026-06-03  
**Operador:** Agente E1  
**Estado:** ✅ **COMPLETADO EXITOSAMENTE**

---

## 1. Resumen Ejecutivo

| Unidad | Sistema | Tickets | Monto Total | PAX | Estado |
|--------|---------|---------|-------------|-----|--------|
| **CIENFUEGOS** | SoftRestaurant | 27 | $102,260.00 | 88 | ✅ Insertado |
| **130MID** | SoftRestaurant | 19 | $80,309.00 | 54 | ✅ Insertado |
| **ESTELAR** | SoftRestaurant | 2 | $560.00 | 2 | ✅ Insertado |
| **130QRO** | MPRO | 11 | $69,731.00 | 25 | ✅ Insertado |
| **ORIGEN** | MPRO | 20 | $56,232.31 | 58 | ✅ Insertado |
| **TOTAL** | - | **79** | **$309,092.31** | **227** | ✅ |

---

## 2. Ejecución por Unidad

### CIENFUEGOS
```
Registros insertados: 27
Sync_Sales antes: 0
Sync_Sales después: 27
Errores: 0
```

### 130MID
```
Registros insertados: 19
Sync_Sales antes: 27
Sync_Sales después: 46
Errores: 0
```

### ESTELAR
```
Registros insertados: 2
Sync_Sales antes: 46
Sync_Sales después: 48
Errores: 0
```

### 130QRO
```
Registros insertados: 11
Sync_Sales antes: 48
Sync_Sales después: 59
Errores: 0
```

### ORIGEN
```
Registros insertados: 20
Sync_Sales antes: 59
Sync_Sales después: 79
Errores: 0
```

---

## 3. Validaciones SQL Post-Ejecución

### 3.1 Sync_Sales por Unidad

```sql
SELECT
    UnidadNegocio,
    CAST(FechaHora AS DATE) AS Fecha,
    COUNT(*) AS tickets,
    SUM(MontoTotal) AS monto_total,
    SUM(Pax) AS pax_total
FROM dbo.Sync_Sales
WHERE CAST(FechaHora AS DATE) = '2026-06-01'
GROUP BY UnidadNegocio, CAST(FechaHora AS DATE)
ORDER BY UnidadNegocio;
```

**Resultado:**
| UnidadNegocio | Fecha | Tickets | Monto Total | PAX |
|---------------|-------|---------|-------------|-----|
| 130MID | 2026-06-01 | 19 | $80,309.00 | 54 |
| 130QRO | 2026-06-01 | 11 | $69,731.00 | 25 |
| CIENFUEGOS | 2026-06-01 | 27 | $102,260.00 | 88 |
| ESTELAR | 2026-06-01 | 2 | $560.00 | 2 |
| ORIGEN | 2026-06-01 | 20 | $56,232.31 | 58 |

### 3.2 Verificación de Duplicados

```sql
SELECT
    UnidadNegocio,
    NumeroTicket,
    CAST(FechaHora AS DATE) AS Fecha,
    COUNT(*) AS duplicados
FROM dbo.Sync_Sales
WHERE CAST(FechaHora AS DATE) = '2026-06-01'
GROUP BY UnidadNegocio, NumeroTicket, CAST(FechaHora AS DATE)
HAVING COUNT(*) > 1;
```

**Resultado:** ✅ No hay duplicados (0 filas)

### 3.3 Comercial_KPIs_Diarios_v2

```sql
SELECT COUNT(*) as registros FROM Comercial_KPIs_Diarios_v2;
```

**Resultado:** 3,376 registros ✅ **SIN CAMBIOS** (como se esperaba)

---

## 4. Comparativa Final: Dry-Run vs Execute

| Unidad | Tickets Dry-Run | Tickets Execute | Δ | Monto Dry-Run | Monto Execute | Δ |
|--------|-----------------|-----------------|---|---------------|---------------|---|
| CIENFUEGOS | 27 | 27 | 0 | $102,260.00 | $102,260.00 | $0 |
| 130MID | 19 | 19 | 0 | $80,309.00 | $80,309.00 | $0 |
| ESTELAR | 2 | 2 | 0 | $560.00 | $560.00 | $0 |
| 130QRO | 11 | 11 | 0 | $69,731.00 | $69,731.00 | $0 |
| ORIGEN | 20 | 20 | 0 | $56,232.31 | $56,232.31 | $0 |

✅ **Coincidencia perfecta** entre dry-run y ejecución real.

---

## 5. Condiciones Cumplidas

| Condición | Estado |
|-----------|--------|
| Una unidad a la vez | ✅ |
| Log por unidad | ✅ |
| Fecha 2026-06-01 | ✅ |
| No modificar KPIs_Diarios_v2 | ✅ (3,376 sin cambios) |
| No poblar Sync_PAX_Detalle | ✅ (no tocada) |
| No activar scheduler | ✅ |
| Sin duplicados | ✅ |
| Ninguna falla | ✅ |

---

## 6. Estructura de ID Generado

El campo `id` de Sync_Sales se genera como:
```
{UnidadNegocio}-{NumeroTicket}-{Fecha}
```

Ejemplos:
- `CIENFUEGOS-101859-2026-06-01`
- `130QRO-21-0042117-2026-06-01`
- `ORIGEN-SB-0046493-2026-06-01`

Esto garantiza unicidad y previene duplicados.

---

## 7. Logs Individuales

| Unidad | Archivo |
|--------|---------|
| CIENFUEGOS | `/app/docs/reports/sync_sales_dry_runs/execute_CIENFUEGOS_20260601.log` |
| 130MID | (console output) |
| ESTELAR | (console output) |
| 130QRO | (console output) |
| ORIGEN | (console output) |

---

## 8. Próximos Pasos Sugeridos

1. ✅ **Completado:** Piloto Sync_Sales 2026-06-01
2. ⏳ **Pendiente:** Ejecutar para más fechas históricas (si se requiere)
3. ⏳ **Pendiente:** Activar Sync_PAX_Detalle (cuando se autorice)
4. ⏳ **Pendiente:** Configurar scheduler automático (cuando se autorice)

---

**Documento generado automáticamente - Agente E1**  
**Ejecución completada: 2026-06-03**
