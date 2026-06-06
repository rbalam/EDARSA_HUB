# DIAGNÓSTICO: MPRO Fallback - Fechas y Credenciales

## Fecha: 2026-04-19
## Autor: EDARSA HUB Technical Team

---

## 1. RESUMEN DEL PROBLEMA

El tablero ejecutivo devolvía **$0.00** para unidades MPRO (130° QUERETARO, ORIGEN) aunque existían datos reales en la base SQL Server CENTRAL2020.

### Síntomas observados:
- Modo normal: MPRO mostraba $0.00
- Modo "Ventas del Día": MPRO mostraba $0.00
- SoftRestaurant funcionaba correctamente
- Las credenciales en MongoDB eran válidas (HRLectura/National09$)

---

## 2. CAUSA RAÍZ IDENTIFICADA

Se identificaron **tres causas raíz** que contribuían al problema:

### 2.1 Import local conflictivo
```python
# ANTES (INCORRECTO):
if solo_ventas_dia:
    from modules.comercial.adapters import sumar_ventas_api_local_a_sucursal  # Import LOCAL
    ...

# Luego se usaba fuera del if:
ventas_api_local = sumar_ventas_api_local_a_sucursal(...)  # ERROR: variable no definida
```

**Error**: `cannot access local variable 'sumar_ventas_api_local_a_sucursal'`

**Solución**: Usar el import global ya existente en línea 29.

### 2.2 Rango de fechas inválido
Cuando el usuario seleccionaba un mes futuro (ej: diciembre estando en abril):

```
fecha_ini = 2026-12-01  (diciembre)
fecha_fin = 2026-04-19  (abril - fecha actual)
```

Este rango es **imposible** (diciembre > abril en el mismo año). La query SQL nunca encuentra datos.

**Error**: `dias_transcurridos = -225` (negativo)

**Solución**: Validar rangos de fecha antes de ejecutar queries.

### 2.3 Fallback incorrecto en modo "Ventas del Día"
Cuando la API local fallaba y se activaba el fallback a SQL nube, el código aún mantenía `solo_ventas_dia=True`, lo que causaba que la lógica posterior pusiera las ventas en $0.

```python
# ANTES (INCORRECTO):
elif solo_ventas_dia:
    # Esto se ejecutaba incluso después del fallback
    ventas = 0  # $0.00 incorrecto
```

**Solución**: Al activar el fallback, deshabilitar `solo_ventas_dia` para permitir datos acumulados.

---

## 3. VERIFICACIÓN DE CREDENCIALES

### Fuente central (MongoDB - Menú Servidores):
| Campo | Valor |
|-------|-------|
| Server ID | 1b230a06-ffaf-4c70-bd27-b1be3579dea6 |
| Name | ManagmentPro |
| Host | 54.39.104.176 |
| Port | 1433 |
| Database | CENTRAL2020 |
| Username | HRLectura |
| Password | National09$ |

### Credenciales hardcodeadas encontradas (legacy):
| Archivo | Usuario | Password |
|---------|---------|----------|
| repository_cortes_z.py | sa | Edarsa2018$ |

**Conclusión**: Ambas credenciales funcionan, pero la fuente autoritativa debe ser MongoDB.

---

## 4. QUERY DE VERIFICACIÓN

Query ejecutada manualmente para confirmar datos:

```sql
SELECT TOP 3 
    CONVERT(VARCHAR, VE.Vn_Fecha, 23) as fecha,
    S.Sc_Descripcion as sucursal,
    SUM(VE.Vn_Precio_Neto_Importe) as ventas
FROM Venta_Encabezado VE
INNER JOIN Sucursal S ON S.Sc_Cve_Sucursal = VE.Sc_Cve_Sucursal
GROUP BY CONVERT(VARCHAR, VE.Vn_Fecha, 23), S.Sc_Descripcion
ORDER BY CONVERT(VARCHAR, VE.Vn_Fecha, 23) DESC
```

**Resultado**:
| Fecha | Sucursal | Ventas |
|-------|----------|--------|
| 2026-04-17 | ORIGEN | $504.00 |
| 2026-04-16 | ORIGEN | $70,054.05 |
| 2026-04-15 | 130° QUERETARO | $68,231.00 |

---

## 5. ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/comercial/service.py` | Fix import, validación fechas, fallback |
| `/app/backend/modules/comercial/routes.py` | Validación meses futuros |
| `/app/backend/core/utils/date_filters.py` | **NUEVO** - Helper de fechas |
| `/app/backend/core/utils/__init__.py` | **NUEVO** - Exports |
| `/app/backend/core/server_connection_manager.py` | **NUEVO** - Gestor de conexiones |

---

## 6. VALIDACIÓN POST-FIX

### Test 1: Modo Normal (abril 2026)
- ✅ MPRO 130° QUERETARO: $1,602,503.00
- ✅ MPRO ORIGEN: $913,840.71

### Test 2: Mes Futuro (diciembre)
- ✅ dias_transcurridos: 18 (positivo, ajustado correctamente)
- ✅ MPRO muestra datos del mes actual

### Test 3: Ventas del Día
- ✅ Fallback a SQL nube funciona
- ✅ MPRO muestra ventas acumuladas

---

## 7. FLUJO CORREGIDO

```
┌─────────────────────────────────────────────────────────┐
│           TABLERO EJECUTIVO - FLUJO MPRO                │
├─────────────────────────────────────────────────────────┤
│ 1. Recibe parámetros (anio, mes)                        │
│    ↓                                                    │
│ 2. VALIDACIÓN: Ajustar meses futuros al actual          │
│    ↓                                                    │
│ 3. VALIDACIÓN: is_valid_range(fecha_ini, fecha_fin)     │
│    ↓ (si válido)                                        │
│ 4. Si solo_ventas_dia:                                  │
│    ├── Intentar API local                               │
│    └── Si falla → FALLBACK: solo_ventas_dia = False     │
│    ↓                                                    │
│ 5. Convertir fechas: to_yyyymmdd_range()                │
│    ↓                                                    │
│ 6. Ejecutar query SQL con credenciales de MongoDB       │
│    ↓                                                    │
│ 7. Retornar datos reales (no $0.00 falso)               │
└─────────────────────────────────────────────────────────┘
```
