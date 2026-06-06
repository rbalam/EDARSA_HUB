# EDARSA HUB - Diagnóstico de Arquitectura

> **Documento Técnico de Evaluación**  
> **Fecha**: Abril 2026  
> **Autor**: E1 Agent (Análisis Master)  
> **Estado**: DIAGNÓSTICO COMPLETO

---

## 1. Resumen Ejecutivo

### 1.1 Métricas Actuales

| Componente | Valor | Evaluación |
|------------|-------|------------|
| **server.py (Monolito)** | 17,366 líneas | ⚠️ CRÍTICO - Muy grande |
| **Endpoints totales** | 189 | Alto volumen |
| **Funciones async** | 201 | Complejidad alta |
| **Modelos Pydantic** | 31 | Aceptable |
| **Queries SQL embebidas** | 268 SELECT | ⚠️ Alto acoplamiento |
| **JOINs en queries** | 300+ | Complejidad SQL alta |
| **Catálogo SQL (MPRO)** | 18,451 líneas | Extenso |
| **Catálogo SQL (SoftRest)** | 7,546 líneas | Extenso |
| **Colecciones MongoDB** | 18 | Distribución correcta |
| **Servidores SQL externos** | 8 activos | Multi-origen |

### 1.2 Score General: 5.5/10

**Fortalezas:**
- Arquitectura híbrida MongoDB + SQL Server funcional
- Sistema de caché de KPIs implementado
- Módulos core (db, security) ya extraídos
- Scaffolding modular preparado

**Debilidades críticas:**
- Monolito de 17K+ líneas sin tests
- Sin índices en MongoDB
- Queries SQL hardcodeadas en código
- Sin pool de conexiones SQL
- Dependencias circulares potenciales

---

## 2. Análisis de Base de Datos

### 2.1 MongoDB (Local)

#### Colecciones Principales

```
COLECCIÓN              | DOCS | PROPÓSITO                    | ESTADO
-----------------------|------|------------------------------|--------
users                  | 10   | Autenticación                | ✅ OK
roles                  | 3    | RBAC                         | ✅ OK
servers                | 10   | Config servidores SQL        | ✅ OK
kpis_cache             | 46   | Caché tablero ejecutivo      | ✅ OK
server_status          | 8    | Estado conexiones            | ✅ OK
portal_suppliers       | 3    | Portal proveedores           | ✅ OK
solicitudes_catalogos  | 10   | Flujo aprobaciones           | ✅ OK
tareas_sistema         | 20   | Workflow "Mis Tareas"        | ✅ OK
nomina_*               | 3    | Módulo nómina                | ⏸️ Parcial
inventario_*           | 2    | Caché inventarios            | ⏸️ Parcial
scripts_pendientes     | 58   | Scripts SQL pendientes       | ✅ OK
```

#### ⚠️ PROBLEMAS DETECTADOS

1. **SIN ÍNDICES SECUNDARIOS**
   ```
   Ninguna colección tiene índices adicionales al _id
   ```
   - **Impacto**: Queries lentas a medida que crezcan los datos
   - **Riesgo**: ALTO para colecciones como `kpis_cache`, `scripts_pendientes`

2. **Sin validación de esquema**
   - Los documentos pueden tener campos inconsistentes
   - No hay `jsonSchema` en las colecciones

3. **IDs como strings UUID en lugar de ObjectId**
   - Mezcla de `id` (UUID string) e `_id` (ObjectId)
   - Aumenta espacio de almacenamiento

### 2.2 SQL Server (Externos)

#### Topología de Servidores

```
SISTEMA         | SERVIDOR              | TIPO          | USO
----------------|----------------------|---------------|------------------
MPRO            | 54.39.104.176        | Cloud OVH     | Ventas principal
MPRO            | API Local QRO        | On-premise    | Tiempo real
MPRO            | API Local Origen     | On-premise    | Tiempo real
SoftRestaurant  | CIENFUEGOS           | DDNS dinámica | Ventas sucursal
SoftRestaurant  | LA ESTELAR           | DDNS dinámica | Ventas sucursal
SoftRestaurant  | 130° MERIDA          | DDNS dinámica | Ventas sucursal
Otro            | EDARSA HUB           | Cloud OVH     | Datos centrales
```

#### ⚠️ PROBLEMAS DETECTADOS

1. **Sin Connection Pooling**
   ```python
   # Actual: Nueva conexión por cada query
   conn = pymssql.connect(...)  # o pytds.connect(...)
   ```
   - **Impacto**: Overhead de 100-500ms por conexión
   - **Riesgo**: CRÍTICO para queries frecuentes

2. **Conexiones síncronas en handlers async**
   ```python
   async def endpoint():
       # BLOQUEA el event loop
       result = execute_sql_query(...)  # Función síncrona
   ```
   - **Impacto**: Throttling del servidor
   - **Riesgo**: ALTO bajo carga

3. **Sin timeout consistente**
   - Algunos queries tienen timeout de 30s, otros de 3s
   - Sin retry policy estandarizado

4. **Credenciales en documento MongoDB**
   - Passwords SQL almacenados en `servers.password`
   - Sin cifrado at-rest

---

## 3. Análisis de Código

### 3.1 Estructura Actual

```
/app/backend/
├── server.py              # 17,366 líneas (MONOLITO)
│   ├── 189 endpoints
│   ├── 268 queries SQL embebidas
│   ├── 31 modelos Pydantic
│   └── Lógica de 15+ dominios mezclada
│
├── core/                   # 1,117 líneas (MIGRADO)
│   ├── db.py              # Conexiones SQL ✅
│   ├── security.py        # JWT/Auth ✅
│   ├── exceptions.py      # Excepciones custom
│   └── utils.py           # Helpers
│
├── modules/               # 2,611 líneas (EN PROGRESO)
│   ├── auth/              # ✅ MIGRADO - 12 endpoints
│   ├── comercial/         # 🔄 PARCIAL - adapters migrados
│   ├── compras/           # ⏸️ Solo scaffolding
│   ├── inventarios/       # ⏸️ Solo scaffolding
│   ├── rh/                # ⏸️ Solo scaffolding
│   └── ...
│
├── routes/
│   └── portal_proveedores.py  # Legacy, separado
│
└── catalogo/              # 42,075 líneas de SQL
    ├── consultas_mpro.py       # 18,451 líneas
    ├── consultas_softrestaurant.py  # 7,546 líneas
    └── catalogo_consultas.py   # 16,012 líneas
```

### 3.2 ⚠️ PROBLEMAS CRÍTICOS

#### A. Monolito Inmanejable
- **17,366 líneas** en un solo archivo
- Cambiar cualquier cosa requiere navegar miles de líneas
- Alto riesgo de regresiones
- Imposible de testear unitariamente

#### B. Acoplamiento Excesivo
```python
# Variable global compartida por todo
db = client[os.environ['DB_NAME']]

# 60+ funciones dependen de execute_sql_query()
# 80+ endpoints dependen de get_current_user()
# Todos los módulos dependen de `db` global
```

#### C. Queries SQL Hardcodeadas
```python
# Actual: SQL mezclado con lógica de negocio
query = f"""
SELECT 
    ISNULL(SUM(total), 0) as ventas
FROM cheques
WHERE fecha >= '{fecha_ini}'  # ⚠️ SQL Injection potencial
"""
```

#### D. Sin Separación de Capas
```
Actual:
  Endpoint → Query SQL → Transformación → Response
  (Todo en la misma función de 200+ líneas)

Debería ser:
  Controller → Service → Repository → Database
  (Separación de responsabilidades)
```

#### E. Sin Tests
- 0 archivos de test encontrados
- Sin cobertura de código
- Refactoring muy riesgoso

---

## 4. Análisis de Patrones

### 4.1 Patrones Actuales (Anti-patterns)

| Anti-pattern | Dónde | Impacto |
|--------------|-------|---------|
| God Object | `server.py` | Imposible mantener |
| Spaghetti Code | Handlers de 500+ líneas | No testeable |
| Hardcoded Queries | 268 queries en código | SQL Injection, duplicación |
| Global State | `db` variable | Testing difícil |
| Mixed Concerns | Endpoint = Service = Repository | No escalable |
| No Error Boundaries | Try/except genéricos | Debugging difícil |

### 4.2 Patrones Buenos Existentes

| Patrón | Dónde | Beneficio |
|--------|-------|-----------|
| Dependency Injection | `get_current_user` | Testeable |
| Repository Pattern | `core/db.py` | Centralizado |
| Caching | `kpis_cache` | Performance |
| Status Tracking | `server_status` | Cooldown servers |
| Catálogo SQL | `/catalogo/` | Queries organizadas |

---

## 5. Plan de Mejora

### 5.1 Fase Inmediata (1-2 semanas)

#### A. Agregar Índices MongoDB
```javascript
// Índices críticos
db.kpis_cache.createIndex({server_id: 1, periodo_key: 1});
db.server_status.createIndex({server_id: 1});
db.users.createIndex({email: 1}, {unique: true});
db.servers.createIndex({active: 1, system_type: 1});
db.scripts_pendientes.createIndex({server_id: 1, estado: 1});
db.tareas_sistema.createIndex({estatus: 1, asignado_a_roles: 1});
```

#### B. Implementar Connection Pooling SQL
```python
# Propuesta: Pool por servidor
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

_sql_pools = {}

def get_sql_pool(server_id: str) -> Engine:
    if server_id not in _sql_pools:
        _sql_pools[server_id] = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30
        )
    return _sql_pools[server_id]
```

### 5.2 Fase Corto Plazo (2-4 semanas)

#### A. Continuar Migración Modular
```
Prioridad de migración:
1. ✅ Auth (completado)
2. 🔄 Comercial (en progreso)
3. ⏳ Compras
4. ⏳ RH
5. ⏳ Inventarios
```

#### B. Extraer Queries a Repositorios
```python
# Antes (actual)
@api_router.get("/comercial/dashboard/{server_id}")
async def dashboard(server_id: str):
    query = "SELECT ... FROM cheques ..."
    result = execute_sql_query(..., query)
    # 500 líneas de procesamiento

# Después (propuesto)
@api_router.get("/comercial/dashboard/{server_id}")
async def dashboard(server_id: str):
    return await comercial_service.get_dashboard(server_id)

# En service.py
async def get_dashboard(server_id: str):
    data = await comercial_repo.query_ventas(server_id, filters)
    return transform_dashboard(data)

# En repository.py
async def query_ventas(server_id: str, filters: dict):
    query = QUERIES['ventas_por_sucursal']  # Del catálogo
    return execute_sql_query(..., query)
```

### 5.3 Fase Mediano Plazo (1-2 meses)

#### A. Implementar Tests
```
/app/backend/tests/
├── conftest.py           # Fixtures
├── test_auth/
├── test_comercial/
├── test_compras/
└── integration/
    └── test_sql_connections.py
```

#### B. Migrar a Conexiones Async
```python
# Actual: Bloquea event loop
result = pymssql.connect(...).cursor().execute(query)

# Propuesto: No bloquea
import aioodbc
async def execute_sql_async(query: str):
    async with aioodbc.connect(dsn=dsn) as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query)
            return await cursor.fetchall()
```

#### C. Implementar Cache Layer
```python
from functools import lru_cache
import redis

# Cache en memoria para queries frecuentes
@lru_cache(maxsize=100)
def get_sucursales(server_id: str):
    ...

# Cache distribuido para KPIs
redis_client = redis.Redis()
async def get_kpis_cached(server_id: str, periodo: str):
    key = f"kpis:{server_id}:{periodo}"
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    ...
```

### 5.4 Fase Largo Plazo (3+ meses)

#### A. Arquitectura Microservicios (Opcional)
```
                    ┌─────────────┐
                    │   API GW    │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
    │   Auth SVC  │ │Comercial SVC│ │ Compras SVC │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
    ┌──────┴──────────────┴───────────────┴──────┐
    │              Message Queue (RabbitMQ)       │
    └─────────────────────────────────────────────┘
```

#### B. Event-Driven para Sincronización
```python
# En lugar de queries constantes a SQL remotos
# Implementar webhooks o change data capture
@app.on_event("sale_created")
async def sync_sale(event: SaleEvent):
    await mongo_db.sales.insert_one(event.dict())
```

---

## 6. Métricas Objetivo

| Métrica | Actual | Objetivo | Plazo |
|---------|--------|----------|-------|
| Líneas server.py | 17,366 | < 2,000 | 3 meses |
| Cobertura tests | 0% | > 60% | 2 meses |
| Tiempo conexión SQL | 100-500ms | < 50ms | 1 mes |
| Índices MongoDB | 0 | 10+ | 1 semana |
| Módulos extraídos | 1/15 | 15/15 | 3 meses |
| Queries parametrizadas | 50% | 100% | 2 meses |

---

## 7. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Regresión al migrar | Alta | Alto | Tests antes de mover |
| Performance peor | Media | Alto | Benchmark pre/post |
| Downtime | Baja | Alto | Feature flags |
| Dependencias circulares | Media | Medio | Análisis de imports |
| SQL Injection | Baja | Crítico | Queries parametrizadas |

---

## 8. Recomendaciones Prioritarias

### 🔴 URGENTE (Esta semana)

1. **Crear índices MongoDB** - 30 minutos de trabajo, mejora inmediata
2. **Documentar dependencias** - Mapa de imports entre archivos
3. **Backup server.py** - Antes de más cambios

### 🟡 IMPORTANTE (Este mes)

1. **Continuar Fase 5B** - Completar módulo Comercial
2. **Implementar connection pool** - Reducir latencia SQL
3. **Crear tests básicos** - Al menos para auth y comercial

### 🟢 DESEABLE (Próximo trimestre)

1. **Migrar a async SQL** - aioodbc o similar
2. **Implementar Redis** - Cache distribuido
3. **CI/CD con tests** - Automatización

---

## 9. Conclusión

EDARSA HUB tiene una **base funcional sólida** pero sufre de **deuda técnica significativa**. El monolito de 17K+ líneas es el problema principal. La migración modular iniciada (Fases 1-5B) es el camino correcto.

**Prioridad máxima**: 
1. Completar migración del módulo Comercial (Fase 5B)
2. Agregar índices MongoDB
3. Implementar connection pooling SQL

**No hacer todavía**:
- Refactoring masivo sin tests
- Cambiar arquitectura completa
- Migrar a microservicios (prematuro)

---

> **Documento generado por E1 Agent**  
> **Última actualización**: Abril 2026
