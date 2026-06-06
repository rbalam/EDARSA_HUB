# VALIDACIÓN SYNC STATUS - INTELIGENCIA COMERCIAL
**Ejecutado:** 2026-06-02T10:06:28.921724
**SP:** `dbo.Sp_Validar_Inteligencia_Comercial_Status`

---

## Resultado de Validación

| Fuente | Última Fecha Operación | Última Sincronización | Registros | Estado |
|--------|------------------------|----------------------|-----------|--------|
| `Comercial_KPIs_Diarios_v2` | 2026-06-01 | 2026-06-02 09:41:30 | 3,373 | ✅ OK |
| `Comercial_Ventas_Dia_Abiertas_v2` | 2026-06-01 | 2026-06-02 10:04:44 | 8 | ✅ OK |
| `Sync_PAX_Detalle` | N/A | N/A | 0 | 🔴 SIN_DATOS |
| `Sync_Sales` | N/A | N/A | 0 | 🔴 SIN_DATOS |

---

## Resumen de Estado

| Estado | Cantidad | Porcentaje |
|--------|----------|------------|
| ✅ OK | 2 | 50% |
| ⚠️ STALE | 0 | 0% |
| 🔴 SIN_DATOS | 2 | 50% |
| **TOTAL** | **4** | **100%** |

---

## Interpretación

### 🔴 Fuentes SIN_DATOS

Las siguientes fuentes no tienen datos sincronizados:

- **Sync_PAX_Detalle**: Requiere ejecución del job de sincronización correspondiente
- **Sync_Sales**: Requiere ejecución del job de sincronización correspondiente

> **NOTA:** NO se ejecutan sincronizadores desde este diagnóstico.
> Los jobs programados (`inteligencia_comercial_sync`) se encargan de poblar estas tablas.

### ✅ Fuentes OK

Las siguientes fuentes tienen datos frescos (menos de 2 días):

- **Comercial_KPIs_Diarios_v2**: 3,373 registros, última fecha 2026-06-01
- **Comercial_Ventas_Dia_Abiertas_v2**: 8 registros, última fecha 2026-06-01

---

## Arquitectura de Datos (Recordatorio)

```
SoftRestaurant / MPRO
        ↓
   [Scheduler Jobs]  ← NO consultar live desde dashboard
        ↓
Sync_Sales, Sync_PAX_Detalle
        ↓
Comercial_KPIs_Diarios_v2 (DERIVADA)
        ↓
VW_KPIsEjecutivos (VISTA)
        ↓
   [FastAPI Endpoints]
        ↓
   React Dashboard
```

---

*Validación completada: 2026-06-02T10:06:28.921782*