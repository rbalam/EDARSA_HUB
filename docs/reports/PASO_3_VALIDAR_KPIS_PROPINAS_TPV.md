# Paso 3 - Validar KPIs PropinasTPV

Fecha: Thu Jun  4 18:09:59 UTC 2026


## Resultado de Validación

### Backend Propinas V2 - FUNCIONANDO ✅

| Unidad | Sistema | Propinas TPV | Registros |
|--------|---------|--------------|-----------|
| TODAS | - | $145,260.19 | 50 |
| ORIGEN | MPRO | $51,432.19 | 50 |
| 130° QUERETARO | MPRO | $93,828.00 | 50 |
| 130° MERIDA | SoftRestaurant | $0.00 | 0 (sin sync desde 17/05) |
| CIENFUEGOS | SoftRestaurant | $0.00 | 0 (sin sync desde 17/05) |
| LA ESTELAR | SoftRestaurant | $0.00 | 0 (sin sync desde 17/05) |

### Problema Identificado

El endpoint `/api/finanzas/propinas/v2/detalle` requiere autenticación:
- Sin auth: `{"detail": "Not authenticated"}`
- Con auth: Devuelve datos correctamente

### Diagnóstico Frontend

Si los KPIs muestran $0.00 en el navegador, verificar:

1. ¿El token/cookie se está enviando en la petición de propinas?
2. ¿El `unidad_negocio_id` se está pasando correctamente?
3. ¿Las fechas están en el rango correcto?

### Unidades SoftRestaurant sin datos recientes

La sincronización de SoftRestaurant se detuvo el 17 de mayo 2026.
Estas unidades mostrarán $0.00 si el rango de fechas es posterior a esa fecha.
