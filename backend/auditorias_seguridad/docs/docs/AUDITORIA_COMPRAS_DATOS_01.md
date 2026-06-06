# AUDITORIA-COMPRAS-DATOS-01 — Búsqueda de Período con Datos

**Código:** AUDITORIA-COMPRAS-DATOS-01  
**Fecha:** 2025-12-27  
**Módulo:** Compras  
**Estado:** ✅ DATOS ENCONTRADOS — VALIDACIÓN FUNCIONAL POSIBLE

---

## Resumen Ejecutivo

Se encontraron datos reales de compras en el endpoint `/api/compras/analisis` para el período Enero-Abril 2026.

---

## Búsqueda de Datos

### Endpoints SIN Datos (Dashboard)

| Servidor | Mes | Endpoint | compras_mes | pedidos | top_proveedores |
|----------|-----|----------|-------------|---------|-----------------|
| LA ESTELAR | 04/2026 | `/compras/dashboard` | $0 | 0 | 0 |
| LA ESTELAR | 03/2026 | `/compras/dashboard` | $0 | 0 | 0 |
| LA ESTELAR | 02/2026 | `/compras/dashboard` | $0 | 0 | 0 |
| LA ESTELAR | 01/2026 | `/compras/dashboard` | $0 | 0 | 0 |
| LA ESTELAR | 12/2025 | `/compras/dashboard` | $0 | 0 | 0 |
| LA ESTELAR | 11/2025 | `/compras/dashboard` | $0 | 0 | 0 |
| CIENFUEGOS | 04/2026 | `/compras/dashboard` | $0 | 0 | 0 |
| CIENFUEGOS | 03/2026 | `/compras/dashboard` | $0 | 0 | 0 |
| 130° MERIDA | 04/2026 | `/compras/dashboard` | $0 | 0 | 0 |

### Endpoints CON Datos (Análisis)

| Servidor | Período | Endpoint | Proveedores | Total Compras | Estado |
|----------|---------|----------|-------------|---------------|--------|
| LA ESTELAR | Ene-Abr 2026 | `/compras/analisis` | 100 | **$12.8M+** | ✅ DATOS |
| CIENFUEGOS | Ene-Abr 2026 | `/compras/analisis` | 100 | **$18,827,657.80** | ✅ DATOS |
| 130° MERIDA | Ene-Abr 2026 | `/compras/analisis` | 100 | **$14,096,712.32** | ✅ DATOS |

---

## Hallazgo Principal

### El Dashboard de Compras NO muestra los datos que SÍ existen

**Evidencia:**
- `/api/compras/analisis` devuelve 100 proveedores con totales > $10M
- `/api/compras/dashboard` devuelve $0 para los mismos períodos y servidores

**Posibles causas:**
1. El Dashboard consulta tablas diferentes al Análisis
2. El Dashboard requiere datos de "pedidos" que no existen
3. El Dashboard usa filtros adicionales que excluyen datos

### Top Proveedores (LA ESTELAR, Ene-Abr 2026)

| Proveedor | Total |
|-----------|-------|
| X1202 N MARISOL DZUL | $1,635,128.75 |
| X1229 MAJIME (EST PINTURA) | $1,214,344.09 |
| B1157 KUKULKAN (CORONA) | $1,031,059.29 |
| N1205 SUELDOS X PAGAR | $955,655.22 |
| X0021 ARCICONSTRU | $824,394.30 |

---

## Análisis: ¿Por qué Dashboard muestra $0?

### Comparación de Endpoints

| Aspecto | Dashboard | Análisis |
|---------|-----------|----------|
| Endpoint | `GET /compras/dashboard/{id}` | `POST /compras/analisis` |
| Método | GET | POST |
| Parámetros | `mes`, `anio` | `meses[]`, `anio`, `sucursal`, `almacenes[]`, `fecha_inicio`, `fecha_fin` |
| Datos mostrados | $0 | $18M+ |

### Diferencias Clave

1. **Dashboard** usa filtros simples (`mes=04&anio=2026`)
2. **Análisis** usa filtros detallados incluyendo `almacenes[]` y `sucursal_codigo`
3. El Dashboard puede estar consultando tablas de **pedidos** mientras Análisis consulta **facturas/movimientos**

---

## Validación Funcional con Datos

### Endpoint `/api/compras/analisis`

| Criterio | Estado |
|----------|--------|
| Endpoint responde | ✅ 200 OK |
| Proveedores devueltos | ✅ 100 |
| Totales calculados | ✅ > $10M |
| Estructura correcta | ✅ |
| Filtros funcionan | ✅ (por servidor, período) |

### Estructura de Respuesta

```json
{
  "proveedores": [
    {
      "nombre": "X1202 N MARISOL DZUL",
      "total": 1635128.75,
      "facturas": 0
    },
    ...
  ],
  "alertas": []
}
```

---

## Diagnóstico del Dashboard

### Hipótesis

El Dashboard de Compras muestra $0 porque:
1. Consulta tabla de `pedidos_compra` que está vacía
2. No tiene fallback a datos de `facturas_proveedor` o `analisis`
3. Los KPIs se calculan de tablas operativas, no de facturas históricas

### Verificación Necesaria

Para confirmar, se debería revisar:
1. `GET /compras/dashboard/{id}` - qué tablas SQL consulta
2. Si `compras_mes` se calcula de pedidos o de facturas
3. Si hay datos en la tabla de pedidos/órdenes de compra

---

## Dictamen

### COMPRAS: ⚠️ VALIDACIÓN PARCIAL — DISCREPANCIA DASHBOARD vs ANÁLISIS

| Criterio | Dashboard | Análisis |
|----------|-----------|----------|
| Endpoint funciona | ✅ 200 | ✅ 200 |
| Estructura correcta | ✅ | ✅ |
| Datos mostrados | ❌ $0 | ✅ $18M+ |
| Proveedores | ❌ 0 | ✅ 100 |
| Totales calculados | ❌ $0 | ✅ OK |

### Clasificación

- **Análisis de Compras:** ✅ FUNCIONA CON DATOS
- **Dashboard de Compras:** ⚠️ MUESTRA $0 (posible bug o diferente fuente de datos)
- **Inventarios Físicos:** ⚠️ SIN DATOS (0 registros)
- **Pedidos Vigentes:** ⚠️ SIN DATOS (0 registros)

---

## Recomendación

1. **Investigar Dashboard:** Verificar por qué muestra $0 cuando Análisis tiene datos
2. **No marcar como bug aún:** Puede ser que Dashboard use tablas de pedidos operativos (vacías) y Análisis use facturas históricas (con datos)
3. **Documentar como discrepancia:** Hasta aclarar la fuente de cada KPI

---

*Diagnóstico: 2025-12-27*  
*Agente: E1*
