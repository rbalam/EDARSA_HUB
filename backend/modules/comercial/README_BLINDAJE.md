# TABLERO EJECUTIVO - REFERENCIA RÁPIDA PARA DESARROLLADORES

## ⚠️ ARCHIVO BLINDADO - NO MODIFICAR SIN AUTORIZACIÓN

---

## ARCHIVOS CRÍTICOS (NO TOCAR)

### Backend Core
```
/app/backend/core/connection_resolver.py   🔴 CRÍTICO
/app/backend/core/providers.py             🔴 CRÍTICO
/app/backend/core/db.py                    🔴 CRÍTICO
```

### Backend Comercial
```
/app/backend/modules/comercial/service.py  🔴 CRÍTICO - KPIs
/app/backend/modules/comercial/routes.py   🔴 CRÍTICO - Endpoint
```

---

## MATRIZ RÁPIDA DE FUENTES

| Sistema | Acumulados | Ventas Día |
|---------|------------|------------|
| SoftRestaurant | SQL (cheques+turnos) | SQL (tempcheques) |
| MPRO | SQL (Venta_Encabezado) | API local |

---

## ENDPOINT PRINCIPAL

```
GET /api/comercial/tablero-ejecutivo

Query Params:
  - meses: "01"-"12" o "ventas_dia"
  - anios: "2024", "2025", "2026"
  - tipo_comparacion: "dias_equiv" (default)

Response:
{
  "totales": { ventas, pax, cheques, proyeccion, var_vs_mes_ant, var_vs_año_ant },
  "unidades": [{ unidad, ventas, pax, cheques, system_type, status }]
}
```

---

## SI NECESITAS MODIFICAR EL TABLERO

1. Lee `/app/docs/CIERRE_Y_BLINDAJE_TABLERO_EJECUTIVO.md`
2. Sigue el Protocolo de Cambio Controlado (Sección XII)
3. Ejecuta TODAS las pruebas de referencia
4. Obtén aprobación antes de merge

---

**Fecha de Cierre: 2026-04-19**
**Estado: CONGELADO FUNCIONALMENTE**
