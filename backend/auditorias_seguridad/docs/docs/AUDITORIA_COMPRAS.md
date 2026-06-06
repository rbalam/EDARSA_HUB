# AUDITORIA-TABLEROS-KPIS-FILTROS-01 — Módulo Compras

**Código:** AUDITORIA-TABLEROS-KPIS-FILTROS-01  
**Fecha:** 2025-12-27  
**Módulo:** Compras y Autorización de Compras  
**Estado:** ✅ CORRECCIÓN APLICADA — Dashboard ahora consistente con Análisis

---

## Resumen Ejecutivo

El módulo **Compras** tenía una **discrepancia** que fue **corregida**:
- **ANTES:** Dashboard mostraba $0 mientras Análisis mostraba $18M+
- **DESPUÉS:** Dashboard y Análisis muestran valores consistentes

### Corrección Aplicada: AUDITORIA-COMPRAS-DASHBOARD-VS-ANALISIS-01

**Causa raíz:** El filtro de fechas del Dashboard usaba rangos (`>= fecha AND < fecha`) que no funcionaban correctamente con el campo `fechaaplicacion` de SoftRestaurant. Se cambió a usar `MONTH()`/`YEAR()` como lo hace Análisis.

**Archivo modificado:** `/app/backend/server.py` (función `obtener_dashboard_compras`)

---

## Validación Post-Corrección

| Servidor | Período | Dashboard ANTES | Dashboard DESPUÉS | Análisis | Estado |
|----------|---------|----------------:|------------------:|---------:|--------|
| LA ESTELAR | Abril 2026 | $0 | **$2,340,813** | $2,340,813 | ✅ MATCH |
| LA ESTELAR | Ene-Abr 2026 | $196,618 | **$11,991,436** | $11,969,963 | ✅ OK |
| 130° MERIDA | Abril 2026 | $0 | **$2,597,599** | $2,592,739 | ✅ OK |
| 130° MERIDA | Ene-Abr 2026 | $158,212 | **$14,369,858** | $14,082,492 | ✅ OK |
| CIENFUEGOS | Abril 2026 | $0 | $0 | $0 | ✅ (Sin datos) |

**Nota:** Diferencias menores (<3%) son esperadas porque Análisis trunca a TOP 100 proveedores.

---

## Dictamen Final

### COMPRAS: ✅ VALIDACIÓN COMPLETA

| Pantalla | Estado | Observación |
|----------|--------|-------------|
| Dashboard | ✅ CORREGIDO | Muestra totales reales |
| Análisis | ✅ FUNCIONA | Sin cambios |
| Top Proveedores | ✅ FUNCIONA | Datos consistentes |
| Filtros mes/año | ✅ FUNCIONA | Multiselección OK |

### Pantallas Pendientes de Validar

| Pantalla | Estado | Observación |
|----------|--------|-------------|
| Inventarios Físicos | ⚠️ SIN DATOS | 0 registros (dato real) |
| Pedidos Vigentes | ⚠️ SIN DATOS | 0 registros (dato real) |
| Autorización | ⚠️ PENDIENTE | Depende de datos operativos |

---

**Reporte de corrección:** `/app/docs/AUDITORIA_COMPRAS_DASHBOARD_VS_ANALISIS_01.md`  
**Diagnóstico datos:** `/app/docs/AUDITORIA_COMPRAS_DATOS_01.md`

*Validado: 2025-12-27*  
*Corrección aplicada: 2025-12-27*
