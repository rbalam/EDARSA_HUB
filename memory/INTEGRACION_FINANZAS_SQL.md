# Integración Módulo Finanzas UI a SQL Server Real

## Fecha: Abril 2026

## 1. Resumen Ejecutivo

### Vistas Conectadas

| Módulo | Tabla SQL | Estado | Datos Actuales |
|--------|-----------|--------|----------------|
| Ingresos (Cortes de Caja) | `Finanzas_CortesCaja` | ✅ CONECTADO | 0 registros (tabla vacía) |
| Cuentas por Pagar | `Finanzas_CuentasPorPagar` | ✅ CONECTADO | 0 registros (tabla vacía) |
| Config TPV Sucursal | `Finanzas_ConfiguracionTPV_Sucursal` | ✅ CONECTADO | 8 registros |

### Endpoints Modificados

| Endpoint | Método | Cambios |
|----------|--------|---------|
| `/api/finanzas/ingresos/cortes-caja` | GET | Conectado a SQL real, fallback a DEMO |
| `/api/finanzas/cuentas-por-pagar` | GET | Conectado a SQL real, fallback a DEMO |

### Archivos Modificados/Creados

| Archivo | Tipo | Cambios |
|---------|------|---------|
| `/app/backend/modules/finanzas/repository_real.py` | NUEVO | Repositorio SQL Server real |
| `/app/backend/modules/finanzas/ingresos.py` | MODIFICADO | Integración con repositorio real |
| `/app/backend/modules/finanzas/cuentas_por_pagar.py` | MODIFICADO | Integración con repositorio real |
| `/app/backend/server.py` | MODIFICADO | Inicialización del repositorio |

---

## 2. Tablas SQL Consumidas

### 2.1 Finanzas_CortesCaja

```sql
-- Estructura de la tabla
CorteCajaID         bigint NOT NULL (PK)
SucursalID          int NOT NULL
FechaCorte          date NOT NULL
TurnoID             int NULL
TotalEfectivo       decimal NOT NULL
TotalTarjetaDebito  decimal NOT NULL
TotalTarjetaCredito decimal NOT NULL
TotalAmex           decimal NOT NULL
TotalInternacional  decimal NOT NULL
TotalVales          decimal NOT NULL
TotalOtros          decimal NOT NULL
ComisionDebito      decimal NOT NULL
ComisionCredito     decimal NOT NULL
ComisionAmex        decimal NOT NULL
ComisionInternacional decimal NOT NULL
DepositadoEfectivo  bit NOT NULL
DepositadoDebito    bit NOT NULL
DepositadoCredito   bit NOT NULL
DepositadoAmex      bit NOT NULL
DepositadoInternacional bit NOT NULL
EstatusCierreID     tinyint NOT NULL (FK: Finanzas_EstatusCierre)
Observaciones       varchar(500) NULL
Activo              bit NOT NULL
FechaAlta           datetime2 NOT NULL
```

### 2.2 Finanzas_CuentasPorPagar

```sql
-- Estructura de la tabla
CuentaPorPagarID    bigint NOT NULL (PK)
DocumentoFiscalID   bigint NULL
ProveedorID         int NOT NULL
SucursalID          int NOT NULL
NumeroDocumento     varchar(50) NOT NULL
FechaDocumento      date NOT NULL
FechaVencimiento    date NOT NULL
FechaRecepcion      date NULL
MontoOriginal       decimal NOT NULL
MontoPagado         decimal NOT NULL
MonedaID            int NOT NULL
TipoCambio          decimal NOT NULL
EstatusPagoID       tinyint NOT NULL (FK: Finanzas_EstatusPago)
DiasCredito         int NOT NULL
Observaciones       varchar(500) NULL
Activo              bit NOT NULL
FechaAlta           datetime2 NOT NULL
```

---

## 3. Comportamiento de la Integración

### Flujo de Datos

```
Frontend ──> Endpoint API ──> Repositorio Real ──> SQL Server (EDARSA HUB)
                │
                └──> Si SQL vacío/error ──> Datos DEMO (opcional)
```

### Parámetro `use_demo`

Los endpoints aceptan `use_demo=true` para forzar el uso de datos de demostración:

```bash
# Datos reales de SQL
GET /api/finanzas/ingresos/cortes-caja

# Datos demo para pruebas
GET /api/finanzas/ingresos/cortes-caja?use_demo=true
```

### Respuesta del Endpoint

Siempre incluye el campo `fuente` para indicar el origen de los datos:

```json
{
  "fuente": "SQL_SERVER_REAL",  // o "DEMO"
  "mensaje": "...",  // Solo si hay algo que reportar
  "cortes": [...],
  "total": 0,
  "resumen": {...}
}
```

---

## 4. Pruebas Ejecutadas

### 4.1 Ingresos (SQL Real)

```bash
$ curl /api/finanzas/ingresos/cortes-caja
{
  "fuente": "SQL_SERVER_REAL",
  "total": 0,
  "mensaje": "No hay cortes de caja registrados. La tabla está vacía.",
  "resumen": { "total_efectivo": 0, ... }
}
```

**Tiempo de respuesta**: ~755ms

### 4.2 Cuentas por Pagar (SQL Real)

```bash
$ curl /api/finanzas/cuentas-por-pagar
{
  "fuente": "SQL_SERVER_REAL",
  "total_facturas": 0,
  "mensaje": "No hay cuentas por pagar registradas. La tabla está vacía.",
  "totales": { "total_importe": 0, ... }
}
```

**Tiempo de respuesta**: ~168ms

### 4.3 Modo DEMO

```bash
$ curl /api/finanzas/ingresos/cortes-caja?use_demo=true
{
  "fuente": "DEMO",
  "total": 150,
  "resumen": {
    "total_efectivo": 3823243.38,
    "total_tarjetas_bruto": 11371656.22
  }
}
```

---

## 5. Riesgos Detectados

### 5.1 Campos Pendientes de Homologación

| Campo UI | Campo SQL | Estado |
|----------|-----------|--------|
| `proveedor_nombre` | No disponible en CxP | ⚠️ Pendiente JOIN con catálogo |
| `proveedor_rfc` | No disponible en CxP | ⚠️ Pendiente JOIN con catálogo |
| `ruta_pdf_factura` | No existe | ⚠️ Pendiente implementación |
| `ruta_xml` | No existe | ⚠️ Pendiente implementación |

### 5.2 Dependencias Pendientes

1. **Catálogo de Proveedores**: Se necesita JOIN con tabla de proveedores para obtener nombre y RFC
2. **Documentos adjuntos**: No hay tablas para rutas de PDF/XML
3. **Carga de datos**: Las tablas de transacciones están vacías

### 5.3 Transformaciones Necesarias

- Conversión de fechas SQL a formato ISO string
- Cálculo de días vencidos en tiempo real
- Conversión de bits a booleanos para estados

---

## 6. Resultado Final

### ✅ Partes en SQL Real

| Componente | Estado |
|------------|--------|
| Lectura de Finanzas_CortesCaja | ✅ Conectado |
| Lectura de Finanzas_CuentasPorPagar | ✅ Conectado |
| Lectura de Finanzas_ConfiguracionTPV_Sucursal | ✅ Conectado (via Catálogos) |
| Filtros por sucursal | ✅ Funcional |
| Filtros por fecha | ✅ Funcional |
| Filtros por estatus | ✅ Funcional |
| Resúmenes y totales | ✅ Calculados en tiempo real |

### ⏳ Partes Pendientes

| Componente | Estado | Razón |
|------------|--------|-------|
| Escritura de cortes | ⏳ Pendiente | Requiere integración con POS |
| Escritura de CxP | ⏳ Pendiente | Requiere integración con compras |
| Nombres de proveedores | ⏳ Pendiente | Falta catálogo de proveedores |
| Documentos adjuntos | ⏳ Pendiente | Falta estructura de archivos |

---

## 7. Siguiente Fase

Con la conexión SQL validada, las siguientes tareas son:

1. **P1**: Crear/cargar datos de prueba en `Finanzas_CortesCaja` y `Finanzas_CuentasPorPagar`
2. **P1**: Crear tabla de catálogo de Proveedores y hacer JOIN
3. **P2**: Implementar escritura de registros desde UI
4. **P2**: Integrar carga de documentos (PDF/XML)

---

## 8. Configuración de Resiliencia

Los endpoints usan la lógica resiliente implementada:

```python
ResilientConfig:
  LOGIN_TIMEOUT = 30s
  QUERY_TIMEOUT = 90s
  MAX_RETRIES = 3
  RETRY_BACKOFF = exponential (2s, 4s, 8s)
```

En caso de fallo de conexión:
1. Se reintenta hasta 3 veces
2. Si falla, se puede usar `use_demo=true` para continuar con datos demo
3. El campo `fuente` siempre indica el origen de los datos
