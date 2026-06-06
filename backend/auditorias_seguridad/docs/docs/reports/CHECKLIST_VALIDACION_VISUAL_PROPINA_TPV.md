# Checklist Validación Visual Propina TPV

## Estado técnico previo

- P0 Sync Propinas TPV SoftRestaurant: resuelto.
- Backfill SoftRestaurant: ejecutado.
- Refactor `system_type`: validado con helpers existentes.
- API Propinas TPV: responde con datos reales.

## Datos esperados según API (backfill mayo-junio 2026)

| Unidad | Registros | Propinas TPV |
|--------|-----------|--------------|
| CIENFUEGOS | 405 | $241,766.84 |
| LA ESTELAR | 550 | $101,627.24 |
| 130° MERIDA | 231 | $167,158.54 |
| **TODAS** | **1,716** | **$788,828.96** |

## Validación manual requerida

### Pasos

1. Abrir: Finanzas → Propinas TPV
2. Seleccionar unidad de negocio: CIENFUEGOS
3. Seleccionar rango de fechas: 2026-05-18 a ayer
4. Validar que los KPIs muestren valores mayores a cero

### Checklist

- [ ] Filtro de Unidad de Negocio funciona
- [ ] Filtro de fechas funciona
- [ ] KPIs muestran valores correctos
- [ ] Tabla de registros muestra datos
- [ ] No hay errores en consola
- [ ] No hay spinners infinitos

## Criterio de aceptación

Si los KPIs coinciden aproximadamente con los valores esperados, marcar como **VALIDACIÓN VISUAL EXITOSA**.
