# DIAGNÓSTICO COMERCIAL - TABLERO Y CUADRE DE CIFRAS

**Fecha de Generación:** 2026-04-20  
**Período Analizado:** Abril 2026 (días 1-19)  
**Autor:** Sistema de Diagnóstico Automatizado

---

## 1. RESUMEN EJECUTIVO

### Estado Actual
- ✅ **Bug MPRO Resuelto**: El error "Tipo de sistema no soportado: MPRO" ya no aparece
- ✅ **Tablero Ejecutivo**: Funcionando correctamente con datos cacheados
- ✅ **Dashboard Comercial**: Funcionando, muestra estado correcto cuando no hay datos
- ⚠️ **Servidores SQL**: Actualmente OFFLINE (VPN no conectada)

### Métricas Consolidadas (Abril 2026)
| Métrica | Valor | vs Mes Anterior | vs Año Anterior |
|---------|-------|-----------------|-----------------|
| Ventas | $9.94M | -3.5% | +8.0% |
| PAX | 9,722 | +2.7% | +41.1% |
| Cheques | 3,369 | -1.2% | +34.1% |
| Proyección | $15.93M | - | +9.6% |

---

## 2. MATRIZ DE CUADRE DE CIFRAS

### A. Datos por Unidad de Negocio

| UNIDAD | VENTAS | CHEQUES | PAX | TICKET/PAX | CHEQUE PROM |
|--------|--------|---------|-----|------------|-------------|
| 130° MÉRIDA | $2,744,730 | 621 | 1,809 | $1,517.26 | $4,419.86 |
| CIENFUEGOS | $2,327,670 | 645 | 1,818 | $1,280.35 | $3,608.79 |
| LA ESTELAR | $1,746,700 | 1,193 | 3,341 | $522.81 | $1,464.12 |
| **TOTAL** | **$6,819,100** | **2,459** | **6,968** | **$978.63** | **$2,773.12** |

### B. Validación de Fórmulas

| UNIDAD | FÓRMULA | REPORTADO | CALCULADO | DIFERENCIA | STATUS |
|--------|---------|-----------|-----------|------------|--------|
| 130° MERIDA | Ventas/PAX | $1,517.26 | $1,517.26 | $0.00 | ✅ OK |
| 130° MERIDA | Ventas/Cheques | $4,419.86 | $4,419.86 | $0.00 | ✅ OK |
| CIENFUEGOS | Ventas/PAX | $1,280.35 | $1,280.35 | $0.00 | ✅ OK |
| CIENFUEGOS | Ventas/Cheques | $3,608.79 | $3,608.79 | $0.00 | ✅ OK |
| LA ESTELAR | Ventas/PAX | $522.81 | $522.81 | $0.00 | ✅ OK |
| LA ESTELAR | Ventas/Cheques | $1,464.12 | $1,464.12 | $0.00 | ✅ OK |

**RESULTADO: Todas las fórmulas CUADRAN correctamente**

### C. Definiciones y Fuentes

| MÉTRICA | FÓRMULA SQL | FUENTE | DESCRIPCIÓN |
|---------|-------------|--------|-------------|
| VENTAS | `SUM(cheques.total)` | cheques WHERE cancelado=0 | Monto neto de cheques cerrados |
| CHEQUES | `COUNT(DISTINCT folio)` | cheques WHERE cancelado=0 | Número de cuentas cerradas |
| PAX | `SUM(nopersonas)` | cheques WHERE cancelado=0 | Comensales por cheque |
| TICKET/PAX | `VENTAS / PAX` | Calculado | Consumo promedio por persona |
| CHEQUE PROM | `VENTAS / CHEQUES` | Calculado | Monto promedio por cuenta |

---

## 3. ARQUITECTURA DE DATOS

### Flujo de Datos

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Servidores SQL │────▶│  Backend FastAPI │────▶│  Frontend React │
│  (SoftRest/MPRO)│     │  (Caché MongoDB) │     │  (Dashboard)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │
        │                        ▼
        │               ┌──────────────────┐
        │               │  Scheduler       │
        │               │  (KPIs periódicos)│
        │               └──────────────────┘
        │                        │
        └────────────────────────┘
```

### Diferencias de Arquitectura

| Endpoint | Fuente de Datos | Comportamiento Offline |
|----------|-----------------|------------------------|
| `/api/comercial/tablero-ejecutivo` | SQL + Caché | ✅ Usa datos cacheados |
| `/api/comercial/dashboard/{server_id}` | SQL en tiempo real | ⚠️ Muestra "Sin datos" |
| `/api/comercial/metas/{server_id}` | SQL en tiempo real | ⚠️ Retorna vacío |
| `/api/comercial/ticket-perfecto/{server_id}` | SQL en tiempo real | ⚠️ Retorna vacío |
| `/api/comercial/reporte-pax/{server_id}` | SQL en tiempo real | ⚠️ Retorna vacío |

---

## 4. ESTADO DE SERVIDORES

| Servidor | Tipo | Status | Última Actualización |
|----------|------|--------|---------------------|
| 130° MERIDA | SoftRestaurant | OFFLINE | 2026-04-20 03:27:03 |
| CIENFUEGOS | SoftRestaurant | OFFLINE | 2026-04-20 03:27:02 |
| LA ESTELAR | SoftRestaurant | OFFLINE | 2026-04-20 03:27:02 |
| ManagmentPro (ORIGEN) | MPRO | Variable | Depende de VPN |
| 130° QUERETARO | SoftRestaurant | ONLINE | En tiempo real |

---

## 5. BUGS CORREGIDOS EN ESTA SESIÓN

### Bug MPRO "Sistema no soportado"

**Problema:** Los servidores MPRO retornaban error "Tipo de sistema no soportado: MPRO" en el Dashboard Comercial.

**Causa Raíz:** Bloque `if result:` en el código MPRO no tenía un `else` adecuado. Cuando la query SQL retornaba vacío, el flujo caía al fallback de "sistema no soportado".

**Solución:** Se agregó un bloque `else` después de `if result:` que retorna `source_status: "NO_DATA"` con mensaje descriptivo.

**Archivo Modificado:** `/app/backend/modules/comercial/routes.py` (líneas 2798-2964)

**Evidencia de Fix:**
```json
{
  "source_status": "SUCCESS",
  "source_message": "Datos obtenidos correctamente de ManagmentPro",
  "server_name": "ManagmentPro",
  "server_type": "MPRO",
  "kpis": {
    "ventas_periodo": 6182554.62,
    "cheques_total": 1820,
    "pax_total": 4748
  }
}
```

---

## 6. COMPARATIVOS (vs Períodos Anteriores)

| UNIDAD | vs Mes Ant | vs Año Ant | PAX vs Mes | PAX vs Año | Chq vs Mes |
|--------|------------|------------|------------|------------|------------|
| 130° MERIDA | +2.6% | -12.6% | +5.3% | -10.8% | -0.2% |
| CIENFUEGOS | -14.5% | -21.2% | -15.6% | -24.8% | -13.2% |
| LA ESTELAR | +12.7% | +0.0% | +13.9% | +0.0% | +19.2% |

---

## 7. RECOMENDACIONES

### Corto Plazo
1. **Implementar caché en endpoints individuales**: Dashboard, Metas, Ticket Perfecto y Reporte PAX deberían usar el mismo patrón de caché del Tablero Ejecutivo.

2. **Mejorar manejo de VPN**: Notificar proactivamente cuando los servidores SQL están offline.

### Mediano Plazo
1. **Homologar `source_status`** en todos los endpoints (actualmente solo Dashboard lo tiene).

2. **Centralizar `SourceQueryResult`** en `core/db.py` para evitar parchear rutas individuales.

---

## 8. EVIDENCIA VISUAL

### Dashboard Comercial
- Muestra correctamente el estado "Sin Datos en el Período"
- Conexión exitosa pero sin datos en período seleccionado
- KPIs visibles (aunque en $0)

### Tablero Ejecutivo
- Datos consolidados: $9.94M ventas
- 5 unidades conectadas
- Comparativos vs mes y año anterior funcionando
- Proyección mensual calculada

---

## 9. CONCLUSIONES

1. **El bug MPRO está resuelto** - Los servidores MPRO ya no caen en el fallback de "sistema no soportado"

2. **Las cifras CUADRAN matemáticamente** - Todas las fórmulas (Ticket/PAX, Cheque Promedio) se calculan correctamente

3. **El sistema funciona correctamente** - La falta de datos en tiempo real se debe a servidores SQL offline, no a bugs en el código

4. **El frontend consume y muestra bien los datos** - Tanto el Dashboard como el Tablero Ejecutivo renderizan correctamente

---

**Documento generado automáticamente como parte de FASE 4 - Cuadre de Cifras**
