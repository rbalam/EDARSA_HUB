# EDARSA HUB - Documento Maestro de Reglas de Filtros

## Módulo de Finanzas - Cuentas por Pagar

### Fuentes de Datos

| Sucursal | Servidor | Base de Datos | Vista CxP | Usuario |
|----------|----------|---------------|-----------|---------|
| **CIEN FUEGOS** | servercienfuegos.ddns.net:6669 | softrestaurant95pro | AC_vwSaldoCxp | CFLectura |
| **LA ESTELAR** | serverestelar.ddns.net:6969 | softrestaurant12 | AC_vwSaldoCxp | SCedarsa |
| **130° MÉRIDA** | 130mid.ddns.net:1433 | softrestaurant10 | vwSaldoCxp | SCedarsa |

### Reglas de Filtro de Cuentas por Pagar

#### 1. Solo Saldos Pendientes
- **Regla**: `[Total CXP] > 0`
- **Descripción**: Solo mostrar proveedores con saldo pendiente mayor a cero
- **Aplicación**: Automática en todas las consultas

#### 2. Agrupación por Tipo de Proveedor

| Tipo | Código | Descripción | Criterio de Identificación |
|------|--------|-------------|---------------------------|
| **A** | ALIMENTOS | Proveedores de alimentos y materia prima | Nombre inicia con `[XXXX] AXXXX` |
| **B** | BEBIDAS | Proveedores de bebidas | Nombre inicia con `[XXXX] BXXXX` |
| **X** | OTROS | Servicios, préstamos, otros | Cualquier otro patrón |

**Formato del nombre de proveedor**: `[0357] X0357 NOMBRE DEL PROVEEDOR`
- El primer carácter después del código numérico indica el tipo

#### 3. Antigüedad de Saldos

| Categoría | Rango de Días | Columna en Vista |
|-----------|---------------|------------------|
| Por Vencer | 0 días | `[POR VENCER]` |
| 1-15 días | 1-15 días vencido | `[01-15]` |
| 16-30 días | 16-30 días vencido | `[16-30]` |
| 31-60 días | 31-60 días vencido | `[31-60]` |
| 61-90 días | 61-90 días vencido | `[61-90]` |
| 91-120 días | 91-120 días vencido | `[91-120]` |
| 121-150 días | 121-150 días vencido | `[121-150]` |
| +151 días | Más de 151 días | `[+151]` |

### Filtros Disponibles en UI

1. **Sucursal**: CIENFUEGOS, ESTELAR, 130MID o "Todas"
2. **Tipo de Proveedor**: A (Alimentos), B (Bebidas), X (Otros) o "Todos"
3. **Fecha de Corte**: Fecha para calcular antigüedad
4. **Solo Vencidas**: Checkbox para filtrar solo documentos vencidos
5. **Con Decisión de Pago**: Checkbox para filtrar solo con decisión marcada

### Estructura de Respuesta API

```json
{
  "fuente": "SOFTRESTAURANT_REAL",
  "proveedores": [
    {
      "proveedor_id": "A",
      "proveedor_nombre": "A - ALIMENTOS",
      "cantidad_facturas": 490,
      "subtotal_saldo": 4705142.00,
      "cantidad_vencidas": 376,
      "facturas": [
        {
          "proveedor_nombre": "[0015] A0015 CARNES ROJAS DEL SURESTE",
          "tipo_proveedor": "A",
          "sucursal_nombre": "CIEN FUEGOS",
          "saldo": 208568.00,
          "dias_vencida": 45,
          "por_vencer": 0,
          "venc_1_30": 50000,
          "venc_31_60": 100000,
          "venc_61_90": 0,
          "venc_91_plus": 58568
        }
      ]
    }
  ],
  "total_facturas": 976,
  "totales": {
    "total_saldo": 19836520.12,
    "cantidad_facturas": 976,
    "cantidad_vencidas": 725
  }
}
```

### Reglas de Negocio

1. **Consolidación**: Los datos de las 3 sucursales se consolidan en una sola vista
2. **Ordenamiento**: Por defecto ordenado por saldo descendente
3. **Timeout de conexión**: 25 segundos por servidor
4. **Límite de registros**: Máximo 2000 proveedores por sucursal

---

## Módulo de Finanzas - Control de Ingresos

### Fuentes de Datos (Cortes de Caja)

| Sucursal | Servidor | Base de Datos | Tabla |
|----------|----------|---------------|-------|
| **EDARSA HUB** | 54.39.104.176:1433 | EDARSAHUB | Finanzas_CortesCaja |

### Campos Disponibles

- `CorteCajaID`: ID único del corte
- `SucursalID`: ID de sucursal
- `FechaCorte`: Fecha del corte
- `TotalEfectivo`: Total en efectivo
- `TotalTarjetaDebito`: Total tarjetas débito
- `TotalTarjetaCredito`: Total tarjetas crédito
- `TotalAMEX`: Total American Express
- `TotalInternacional`: Total tarjetas internacionales
- `ComisionTarjetas`: Comisiones
- `VentaNeta`: Venta neta total

---

## Conexiones de Servidores (Referencia)

### SoftRestaurant
```python
SOFTRESTAURANT_SERVERS = {
    "CIENFUEGOS": {
        "host": "servercienfuegos.ddns.net",
        "port": 6669,
        "database": "softrestaurant95pro",
        "username": "CFLectura",
        "password": "National09",
        "view": "AC_vwSaldoCxp"
    },
    "ESTELAR": {
        "host": "serverestelar.ddns.net",
        "port": 6969,
        "database": "softrestaurant12",
        "username": "SCedarsa",
        "password": "C0ntr4s3ña#2026",
        "view": "AC_vwSaldoCxp"
    },
    "130MID": {
        "host": "130mid.ddns.net",
        "port": 1433,
        "database": "softrestaurant10",
        "username": "SCedarsa",
        "password": "C0ntr4s3ña#2026",
        "view": "vwSaldoCxp"
    }
}
```

### MPRO (Central)
```python
MPRO_SERVER = {
    "host": "54.39.104.176",
    "port": 1433,
    "database": "CENTRAL2020",
    "username": "HRLectura",
    "password": "National09$"
}
```

### EDARSA HUB (RH y Catálogos)
```python
EDARSA_HUB_SERVER = {
    "host": "54.39.104.176",
    "port": 1433,
    "database": "EDARSAHUB",
    "username": "HRLectura",
    "password": "National09$"
}
```

---

*Documento actualizado: Abril 13, 2026*
*Versión: 1.0*
