# MATRIZ DE FUENTES - TABLERO EJECUTIVO EDARSA HUB
## Fecha: 2026-04-19

---

## ARQUITECTURA DE FUENTES VERIFICADA

### 1. SoftRestaurant (CIENFUEGOS, LA ESTELAR, 130° MERIDA)

| KPI | Fuente Real | Método Backend | Conexión | Query/Tabla | Estado |
|-----|------------|----------------|----------|-------------|--------|
| Ventas Acumuladas | SQL histórico | `get_kpis_softrestaurant()` | Menú Servidores SQL | `cheques` + `turnos` | ✅ OK |
| Ventas del Día | SQL tempcheques | `get_kpis_softrestaurant(solo_ventas_dia=True)` | Menú Servidores SQL | `tempcheques` o `cheques` del último turno | ✅ OK |
| PAX | SQL histórico | `get_kpis_softrestaurant()` | Menú Servidores SQL | `cheques.nopersonas` | ✅ OK |
| Cheques | SQL histórico | `get_kpis_softrestaurant()` | Menú Servidores SQL | `COUNT(cheques.folio)` | ✅ OK |
| Comparativo Mes Ant | SQL histórico | `get_kpis_softrestaurant()` | Menú Servidores SQL | Mismo query, fechas ajustadas | ✅ OK |
| Comparativo Año Ant | SQL histórico | `get_kpis_softrestaurant()` | Menú Servidores SQL | Mismo query, fechas ajustadas | ✅ OK |

### 2. MPRO (ORIGEN, 130° QUERETARO)

| KPI | Fuente Real | Método Backend | Conexión | Query/Tabla | Estado |
|-----|------------|----------------|----------|-------------|--------|
| Ventas Acumuladas | SQL MPRO nube | `get_kpis_mpro_por_sucursal()` | Menú Servidores SQL | `Venta_Encabezado` | ✅ OK |
| Ventas del Día | API local | `get_kpis_mpro_por_sucursal(solo_ventas_dia=True)` | API servidores locales | `sumar_ventas_api_local_a_sucursal()` | ✅ OK |
| PAX | SQL MPRO nube | `get_kpis_mpro_por_sucursal()` | Menú Servidores SQL | `Comanda.Co_Personas` | ✅ OK |
| Cheques | SQL MPRO nube | `get_kpis_mpro_por_sucursal()` | Menú Servidores SQL | `COUNT(Venta_Encabezado.Vn_Folio)` | ✅ OK |
| Comparativo Mes Ant | SQL MPRO nube | `get_kpis_mpro_por_sucursal()` | Menú Servidores SQL | Mismo query, fechas ajustadas | ✅ OK |
| Comparativo Año Ant | SQL MPRO nube | `get_kpis_mpro_por_sucursal()` | Menú Servidores SQL | Mismo query, fechas ajustadas | ✅ OK |

---

## REGLAS DE CONEXIÓN VERIFICADAS

### ✅ SoftRestaurant
- **TODA** resolución de conexión SQL sale del menú oficial de Servidores SQL
- Parámetros: `server['host']`, `server['port']`, `server['database']`, `server['username']`, `server['password']`
- NO hay connection strings hardcodeados
- NO hay configuración duplicada paralela

### ✅ MPRO
- **Acumulados**: SQL MPRO nube (mismo servidor del menú)
- **Ventas del día**: API local (función `sumar_ventas_api_local_a_sucursal`)
- Las dos rutas están **separadas** y no se mezclan

---

## SEPARACIÓN DE LÓGICA VERIFICADA

### Servicios Identificados:
1. `get_kpis_softrestaurant()` - SoftRestaurant acumulados + día
2. `get_kpis_mpro_por_sucursal()` - MPRO acumulados + día
3. `sumar_ventas_api_local_a_sucursal()` - MPRO API local (ventas del día)

### Reglas Implementadas:
- ✅ Ventas acumuladas NO dependen de lógica de ventas del día
- ✅ Ventas del día NO contaminan acumulados
- ✅ MPRO NO sigue la misma ruta que SQL clásico cuando usa API local

---

## PRUEBAS EJECUTADAS

### Abril 2026 - Acumulado
```
TOTAL: $9,239,825.71
- 130° MERIDA: $2,701,218.00 (SoftRestaurant)
- CIENFUEGOS: $2,287,754.00 (SoftRestaurant)
- LA ESTELAR: $1,734,580.00 (SoftRestaurant)
- 130° QUERETARO: $1,602,503.00 (MPRO)
- ORIGEN: $913,840.71 (MPRO)
```

### Ventas del Día
```
TOTAL: $138,325.22
- 130° MERIDA: $48,411.00 (tempcheques)
- CIENFUEGOS: $37,539.00 (tempcheques)
- ORIGEN: $35,165.22 (api_local)
- LA ESTELAR: $17,210.00 (tempcheques)
```

### Comparativos
```
Ventas vs Mes Anterior: -3.7%
Ventas vs Año Anterior: +6.2%
```

---

## ARCHIVOS MODIFICADOS

1. `/app/backend/modules/comercial/service.py`
   - Línea 243+: Agregada validación de conexión SQL antes de consultas SoftRestaurant
   - Línea 745+: Agregado logging mejorado para MPRO

---

## CONFIRMACIONES

- [x] CIENFUEGOS acumulado sale por SQL menú servidores
- [x] LA ESTELAR acumulado sale por SQL menú servidores
- [x] 130° MERIDA acumulado sale por SQL menú servidores
- [x] MPRO acumulado sale por SQL MPRO
- [x] MPRO ventas del día sale por API local
- [x] Ventas del día de SQL clásico no rompe acumulado
- [x] Acumulado no depende de tablas del día
- [x] Si una fuente falla, usa caché (no inventa $0 falso)
- [x] No se tocó: .env, DB_NAME, URI, conexión principal, RBAC base, módulo técnico de Servidores

---

## CRITERIO DE ÉXITO: ✅ CUMPLIDO

- Ventas acumuladas no muestran $0
- Datos coinciden con SQL real
- No hay regresión en comparativos
- No hay regresión en detalle por unidad
- No existen ceros falsos por error técnico
