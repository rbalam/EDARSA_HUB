# ARQUITECTURA DE CONEXIONES - EDARSA HUB
## Connection Resolver Central
## Fecha: 2026-04-19

---

## PRINCIPIOS ARQUITECTÓNICOS

1. **EDARSA HUB es el cerebro** - Backend manda
2. **Menú "Servidores SQL"** es la fuente oficial de configuración
3. **Toda conexión SQL** debe resolverse desde ConnectionResolver
4. **Toda fuente de datos** se decide por tipo de sistema + tipo de métrica
5. **El frontend NO decide** conexiones ni fuentes

---

## COMPONENTES IMPLEMENTADOS

### 1. ConnectionResolver (`/app/backend/core/connection_resolver.py`)
```python
from core.connection_resolver import resolve_source, MetricType

# Resolver fuente para ventas acumuladas
source = resolve_source(server_id, MetricType.ACCUMULATED_SALES)

if source.is_valid():
    if source.source_type == SourceType.SQL:
        result = execute_sql_query(source.host, source.port, ...)
    elif source.source_type == SourceType.API:
        result = requests.get(source.api_base_url + "/endpoint")
```

### 2. Providers (`/app/backend/core/providers.py`)
- `SQLClassicProvider` - SoftRestaurant (CIENFUEGOS, LA ESTELAR, 130 MID)
- `MPROSQLProvider` - MPRO SQL (ORIGEN, 130 QRO - acumulados)
- `LocalAPIProvider` - MPRO API (ventas del día)

---

## MATRIZ DE RESOLUCIÓN FINAL

| Unidad | Sistema | KPI | Fuente | Connection Origin | Provider | Status |
|--------|---------|-----|--------|-------------------|----------|--------|
| CIENFUEGOS | SoftRestaurant | Ventas acumuladas | SQL histórico | Menú Servidores SQL | sql_classic | ✅ OK |
| CIENFUEGOS | SoftRestaurant | Ventas del día | tempcheques | Menú Servidores SQL | sql_classic | ✅ OK |
| CIENFUEGOS | SoftRestaurant | PAX | cheques.nopersonas | Menú Servidores SQL | sql_classic | ✅ OK |
| LA ESTELAR | SoftRestaurant | Ventas acumuladas | SQL histórico | Menú Servidores SQL | sql_classic | ✅ OK |
| LA ESTELAR | SoftRestaurant | Ventas del día | tempcheques | Menú Servidores SQL | sql_classic | ✅ OK |
| LA ESTELAR | SoftRestaurant | PAX | cheques.nopersonas | Menú Servidores SQL | sql_classic | ✅ OK |
| 130° MERIDA | SoftRestaurant | Ventas acumuladas | SQL histórico | Menú Servidores SQL | sql_classic | ✅ OK |
| 130° MERIDA | SoftRestaurant | Ventas del día | tempcheques | Menú Servidores SQL | sql_classic | ✅ OK |
| 130° MERIDA | SoftRestaurant | PAX | cheques.nopersonas | Menú Servidores SQL | sql_classic | ✅ OK |
| ORIGEN | MPRO | Ventas acumuladas | Venta_Encabezado | MPRO SQL | mpro_sql | ✅ OK |
| ORIGEN | MPRO | Ventas del día | API local | Local API | local_api | ✅ OK |
| ORIGEN | MPRO | PAX | Comanda.Co_Personas | MPRO SQL | mpro_sql | ✅ OK |
| 130° QRO | MPRO | Ventas acumuladas | Venta_Encabezado | MPRO SQL | mpro_sql | ✅ OK |
| 130° QRO | MPRO | Ventas del día | API local | Local API | local_api | ✅ OK |
| 130° QRO | MPRO | PAX | Comanda.Co_Personas | MPRO SQL | mpro_sql | ✅ OK |

---

## TIPOS DE MÉTRICAS SOPORTADAS

```python
class MetricType(Enum):
    ACCUMULATED_SALES = "accumulated_sales"   # Ventas acumuladas
    DAILY_SALES = "daily_sales"               # Ventas del día
    DAILY_CHECKS = "daily_checks"             # Cheques del día
    COMPARATIVE_SALES = "comparative_sales"   # Comparativos
    PROJECTION = "projection"                 # Proyección
    PAX = "pax"                               # Comensales
    INVENTORY = "inventory"                   # Inventarios
```

---

## ESTRUCTURA DE RESPUESTA DEL RESOLVER

```python
@dataclass
class ResolvedSource:
    unit_code: str                    # "CIENFUEGOS"
    unit_name: str                    # "CIENFUEGOS"
    system_type: SystemType           # SoftRestaurant | MPRO
    metric_type: MetricType           # accumulated_sales, etc.
    source_type: SourceType           # sql | api
    connection_origin: ConnectionOrigin  # menu_servidores_sql | mpro_sql | local_api
    
    # SQL
    host: Optional[str]
    port: Optional[int]
    database_name: Optional[str]
    username: Optional[str]
    password: Optional[str]           # NUNCA loggear
    
    # API
    api_base_url: Optional[str]
    
    status: str                       # resolved | error | fallback
    error_message: Optional[str]
```

---

## REGLAS DE CONEXIÓN

### SoftRestaurant (CIENFUEGOS, LA ESTELAR, 130 MID)
- **TODA** conexión SQL sale del menú Servidores SQL
- NO hay connection strings hardcodeados
- Tablas: `cheques`, `turnos`, `tempcheques`

### MPRO (ORIGEN, 130 QRO)
- **Acumulados**: SQL desde menú Servidores SQL (tabla `Venta_Encabezado`)
- **Ventas del día**: API local (endpoint `/api/ventas/dia`)
- Las dos rutas están **separadas** y no se mezclan

---

## MANEJO DE ERRORES

Si falla una fuente:
- NO devolver `$0` como si fuera real
- Devolver estado técnico explícito:
  - `ok` - Datos obtenidos correctamente
  - `partial` - Datos parciales
  - `error` - Error de conexión/query

---

## LOGGING

Cada resolución registra:
```
[ConnectionResolver] RESOLVED: CIENFUEGOS | metric=accumulated_sales | 
    source=sql | origin=menu_servidores_sql | status=resolved
```

---

## ARCHIVOS CREADOS

1. `/app/backend/core/connection_resolver.py` - Resolver central (550 líneas)
2. `/app/backend/core/providers.py` - Providers por sistema (400 líneas)
3. `/app/backend/core/__init__.py` - Actualizado con exports

---

## VERIFICACIÓN DE NO REGRESIÓN

```
VENTAS ACUMULADAS ABRIL 2026: $9,258,756.71
- 130° MERIDA: $2,701,273 ✅
- CIENFUEGOS: $2,306,205 ✅
- LA ESTELAR: $1,734,935 ✅
- 130° QUERETARO: $1,602,503 ✅
- ORIGEN: $913,841 ✅

COMPARATIVOS: vs Mes Ant -3.5% | vs Año Ant +6.4% ✅
PAX: 9,316 | CHEQUES: 3,216 ✅
```

---

## USO RECOMENDADO PARA NUEVOS DESARROLLOS

```python
from core.connection_resolver import resolve_source, MetricType, SourceType
from core.db import execute_sql_query

# 1. Resolver la fuente
source = resolve_source(
    server_id="abc-123-uuid",
    metric_type=MetricType.ACCUMULATED_SALES
)

# 2. Verificar que sea válida
if not source.is_valid():
    return {"error": source.error_message, "status": "error"}

# 3. Usar según el tipo de fuente
if source.source_type == SourceType.SQL:
    result = execute_sql_query(
        source.host, source.port, source.database_name,
        source.username, source.password,
        "SELECT SUM(total) FROM cheques WHERE ..."
    )
elif source.source_type == SourceType.API:
    response = requests.get(f"{source.api_base_url}/api/endpoint")

# 4. El logging ya está incluido automáticamente
```

---

## CRITERIO DE ÉXITO: ✅ CUMPLIDO

- [x] Existe resolver central real
- [x] Conexiones centralizadas
- [x] Cada KPI usa fuente correcta
- [x] SoftRestaurant resuelve SQL por menú Servidores
- [x] MPRO acumulado usa SQL MPRO
- [x] MPRO ventas del día usa API local
- [x] No hay mezcla de rutas
- [x] No hay ceros falsos
- [x] No se rompió el tablero
