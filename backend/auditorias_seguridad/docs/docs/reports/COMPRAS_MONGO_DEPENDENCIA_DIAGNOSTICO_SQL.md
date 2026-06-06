# DIAGNÓSTICO: Dependencias MongoDB del Módulo Compras

**Fecha**: 2026-05-25  
**Auditor**: E1 Agent (Arquitecto Senior ERP/SQL Server)  
**Versión**: 1.0  
**Estado**: DIAGNÓSTICO PASIVO (Sin modificaciones de código)

---

## 1. RESUMEN EJECUTIVO

### Hallazgo Principal
El módulo de **Compras** tiene **dependencias residuales de MongoDB** que fueron parcheadas con un "modo stub" silencioso en lugar de ser migradas a EDARSAHUB SQL.

### Estado Actual
- ❌ `repository.py` tiene funciones que esperan MongoDB (`db.compras_params`)
- ❌ `pedidos_detector_job.py` usa colecciones MongoDB para tracking
- ⚠️ El código fue parcheado con `_stub_mode=True` para no explotar cuando `_db=None`
- ⚠️ Esto hace que Compras "no truene", pero **funciona vacío silenciosamente**

### Riesgo
El módulo Compras puede mostrar datos vacíos sin advertencia porque el stub ignora las operaciones de MongoDB en lugar de leer de SQL.

---

## 2. DEPENDENCIAS MONGODB ENCONTRADAS

### 2.1 Archivo: `/app/backend/modules/compras/repository.py`

| Línea | Código | Colección MongoDB | Descripción |
|-------|--------|-------------------|-------------|
| 66 | `_db = None` | - | Variable global de conexión MongoDB |
| 67 | `_stub_mode = False` | - | Flag de modo stub (sin MongoDB) |
| 154 | `db.compras_params.find_one(...)` | `compras_params` | Lee parámetros de compras |
| 166 | `db.compras_params.update_one(...)` | `compras_params` | Guarda parámetros de compras |

**Funciones afectadas:**
- `get_compras_params(server_id, sucursal)` → Retorna `None` en modo stub
- `save_compras_params(server_id, sucursal, params)` → Ignora silenciosamente en modo stub

### 2.2 Archivo: `/app/backend/core/scheduler/jobs/pedidos_detector_job.py`

| Línea | Código | Colección MongoDB | Descripción |
|-------|--------|-------------------|-------------|
| 69 | `COLLECTION_PROCESADOS` | `pedidos_procesados_automatizacion` | Tracking de pedidos procesados |
| 70 | `COLLECTION_TAREAS` | `tareas_operativas_compras` | Tareas operativas creadas |
| 71 | `COLLECTION_BITACORA` | `auditoria_compras_bitacora` | Log de auditoría |

**Fallback implementado:** Usa `StubDatabase` cuando `db is None` (líneas 75-78)

---

## 3. ARCHIVOS AFECTADOS

| Archivo | Dependencia MongoDB | Estado |
|---------|---------------------|--------|
| `/app/backend/modules/compras/repository.py` | `compras_params` | ⚠️ Parcheado con stub |
| `/app/backend/modules/compras/__init__.py` | `init_compras_repository(database)` | ⚠️ Recibe `None` |
| `/app/backend/modules/compras/service.py` | Usa `repo.get_compras_params` | ⚠️ Retorna `None` |
| `/app/backend/core/scheduler/jobs/pedidos_detector_job.py` | 3 colecciones | ⚠️ Usa StubDatabase |
| `/app/backend/server.py` (línea 285) | `init_compras_module(None)` | ✅ Pasa `None` correctamente |

---

## 4. FUNCIONES AFECTADAS

### 4.1 Funciones con dependencia directa de MongoDB

```python
# repository.py
async def get_compras_params(server_id, sucursal) -> Optional[Dict]
async def save_compras_params(server_id, sucursal, params) -> None

# service.py
async def obtener_parametros_compras(server_id, sucursal) -> Dict
async def guardar_parametros_compras(server_id, sucursal, params) -> Dict
```

### 4.2 Funciones que funcionan correctamente (SQL)

```python
# repository.py - Consultas SQL a servidores origen (NO EDARSAHUB)
def query_inventarios_fisicos_mpro(server, almacen_filtro, sucursal_id)
def query_inventarios_fisicos_soft(server, almacen_filtro, sucursal_id)
def query_pedidos_vigentes_mpro(server, sucursal_id)
def query_pedidos_vigentes_soft(server, sucursal_id)
def query_facturas_proveedor_mpro(server, sucursal_id, meses, anio)

# NOTA: Estas funciones consultan SERVIDORES ORIGEN (MPRO/Soft),
# NO EDARSAHUB SQL. Violan la arquitectura NO-LIVE.
```

---

## 5. ENDPOINTS AFECTADOS

### 5.1 Endpoints que dependen de `compras_params` (MongoDB)

| Endpoint | Archivo | Función | Impacto |
|----------|---------|---------|---------|
| `GET /compras/parametros/{server_id}` | `server.py:7889` | `obtener_parametros_compras` | Retorna defaults (no persistidos) |
| `POST /compras/parametros` | `server.py:7910` | `guardar_parametros_compras` | Ignora guardado silenciosamente |

### 5.2 Endpoints que consultan servidores LIVE (violan NO-LIVE)

| Endpoint | Archivo | Función | Fuente de Datos |
|----------|---------|---------|-----------------|
| `GET /compras/inventarios-fisicos/{server_id}` | `server.py:6988` | - | SQL LIVE (MPRO/Soft) |
| `GET /compras/pedidos-vigentes/{server_id}` | `server.py:7149` | - | SQL LIVE (MPRO/Soft) |
| `GET /compras/dashboard/{server_id}` | `server.py:9404` | - | SQL LIVE (MPRO/Soft) |
| `POST /compras/calculo-pedido` | `server.py:7455` | - | SQL LIVE (MPRO/Soft) |
| `GET /compras/facturas-proveedor/{server_id}` | `server.py` | - | SQL LIVE (MPRO/Soft) |
| `POST /compras/analisis` | `server.py` | - | SQL LIVE (MPRO/Soft) |

**⚠️ VIOLACIÓN ARQUITECTÓNICA:** Estos endpoints consultan servidores origen EN VIVO durante el request del usuario. Deberían leer de tablas sincronizadas en EDARSAHUB SQL.

---

## 6. PANTALLAS/TABS AFECTADOS EN FRONTEND

| Componente | Archivo | Endpoints que consume |
|------------|---------|----------------------|
| `DashboardCompras` | `/app/frontend/src/pages/Compras.js:80` | `/compras/dashboard/{server_id}` |
| `AutorizacionComprasTab` | `/app/frontend/src/pages/Compras.js:526` | `/compras/inventarios-fisicos`, `/compras/pedidos-vigentes` |
| `AnalisisCompras` | `/app/frontend/src/pages/Compras.js:891` | `/compras/analisis`, `/compras/facturas-proveedor` |
| `PortalProveedoresTab` | Importado en Compras.js | APIs de portal proveedores |

---

## 7. COLECCIONES MONGODB USADAS

| Colección | Propósito | Estado | Datos Críticos |
|-----------|-----------|--------|----------------|
| `compras_params` | Parámetros de cálculo de pedidos | ⚠️ Ignorada (stub) | Días de inventario, tránsito proveedor |
| `pedidos_procesados_automatizacion` | Tracking de pedidos procesados | ⚠️ Stub | IDs de pedidos ya procesados |
| `tareas_operativas_compras` | Tareas generadas | ⚠️ Stub | Tareas pendientes de autorización |
| `auditoria_compras_bitacora` | Log de auditoría | ⚠️ Stub | Historial de operaciones |

---

## 8. TABLAS SQL EQUIVALENTES EXISTENTES EN EDARSAHUB

### 8.1 Tablas de sincronización ya creadas

| Tabla | Propósito | Job que la llena |
|-------|-----------|------------------|
| `Compras_Inventarios_Fisicos_Sync` | Inventarios sincronizados | `sync_compras_job.py` |
| `Compras_Requisiciones_Sync` | Pedidos/requisiciones sincronizados | `sync_compras_job.py` |
| `Compras_Sync_Log` | Log de sincronización | `sync_compras_job.py` |
| `Compras_KPIs_Historico` | KPIs históricos de compras | `historical_kpis_repository.py` |
| `Compras_Eventos_Pendientes` | Eventos pendientes de procesar | `eventos_compras.py` |
| `Compras_Sync_Checkpoint` | Checkpoints de sincronización | `eventos_compras.py` |

### 8.2 Tablas de catálogos existentes

| Tabla | Propósito |
|-------|-----------|
| `Compras_Estatus` | Catálogo de estatus de compras |
| `Compras_OrdenesEstatus` | Estatus de órdenes |
| `Compras_PedidosEstatus` | Estatus de pedidos |
| `Compras_RecepcionesEstatus` | Estatus de recepciones |
| `Compras_DocumentosFiscalesEstatus` | Estatus de docs fiscales |
| `Compras_ConciliacionSATEstatus` | Estatus de conciliación SAT |

---

## 9. TABLAS SQL FALTANTES

### 9.1 Para reemplazar `compras_params` de MongoDB

**Propuesta:** `Compras_Parametros_Sucursal`

```sql
CREATE TABLE Compras_Parametros_Sucursal (
    ParametroID INT IDENTITY(1,1) PRIMARY KEY,
    ServerID VARCHAR(100) NOT NULL,
    SucursalID VARCHAR(50) NOT NULL,
    
    -- Parámetros de cálculo de pedido
    DiasInventarioSemana INT DEFAULT 7,
    DiasInventarioQuincena INT DEFAULT 15,
    DiasInventarioMes INT DEFAULT 30,
    DiasTransitoProveedor INT DEFAULT 2,
    FactorSeguridad DECIMAL(5,2) DEFAULT 1.2,
    
    -- Metadata
    CreadoPor VARCHAR(100),
    ActualizadoPor VARCHAR(100),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT UQ_Compras_Params UNIQUE (ServerID, SucursalID)
);
```

### 9.2 Para tracking de pedidos (reemplazar MongoDB)

**Propuesta:** `Compras_Pedidos_Tracking`

```sql
CREATE TABLE Compras_Pedidos_Tracking (
    TrackingID INT IDENTITY(1,1) PRIMARY KEY,
    PedidoFolio VARCHAR(100) NOT NULL,
    ServerID VARCHAR(100) NOT NULL,
    SucursalID VARCHAR(50) NOT NULL,
    
    FechaProcesado DATETIME,
    EstadoProceso VARCHAR(50), -- PENDIENTE, PROCESADO, ERROR
    ResultadoValidacion TEXT,
    TareaGeneradaID VARCHAR(100),
    
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedAt DATETIME DEFAULT GETDATE()
);
```

---

## 10. PLAN DE MIGRACIÓN MONGODB → SQL

### Fase 1: Crear tablas SQL (P0)
1. Crear `Compras_Parametros_Sucursal` en EDARSAHUB
2. Crear `Compras_Pedidos_Tracking` en EDARSAHUB
3. Crear índices necesarios

### Fase 2: Crear repositorio SQL (P0)
1. Crear `/app/backend/modules/compras/repository_compras_sql.py`
2. Implementar `get_compras_params_sql()` y `save_compras_params_sql()`
3. Implementar funciones de tracking de pedidos

### Fase 3: Migrar endpoints a SQL (P1)
1. Modificar `service.py` para usar repositorio SQL
2. Modificar `obtener_parametros_compras` y `guardar_parametros_compras`
3. NO modificar frontend (misma interfaz)

### Fase 4: Eliminar código MongoDB (P2)
1. Remover `get_db()`, `_db`, `_stub_mode` de `repository.py`
2. Remover imports de MongoDB
3. Actualizar `init_compras_repository()` para no requerir `database`

---

## 11. RIESGO DE DEJAR `_db=None` CON RETORNOS VACÍOS

### Riesgo Alto
| Función | Comportamiento Actual | Riesgo |
|---------|----------------------|--------|
| `get_compras_params()` | Retorna `None` | Cálculo de pedido usa defaults, no parámetros guardados |
| `save_compras_params()` | Ignora silenciosamente | Usuario cree que guardó, pero no se persistió |

### Impacto en Usuario
- El usuario puede configurar parámetros de compras que **no se guardan**
- Los cálculos de pedido usan siempre valores por defecto
- No hay advertencia ni error visible

---

## 12. CAMBIOS YA HECHOS QUE DEBEN REVERTIRSE/REEMPLAZARSE

### Archivo: `/app/backend/modules/compras/repository.py`

**Cambios identificados (líneas 67, 77-81, 92-94, 152-165):**

```python
# ACTUAL (MODO STUB - DEBE REEMPLAZARSE)
_stub_mode = False

def init_compras_repository(database):
    global _db, _stub_mode
    _db = database
    if database is None:
        _stub_mode = True
        logger.warning("[COMPRAS_REPO] Inicializado en modo STUB...")

def get_db():
    if _db is None:
        logger.warning("[COMPRAS_REPO] MongoDB no disponible, operando en modo stub")
    return _db

async def get_compras_params(server_id, sucursal):
    db = get_db()
    if db is None:  # Modo stub
        return None
    ...

async def save_compras_params(server_id, sucursal, params):
    db = get_db()
    if db is None:  # Modo stub
        logger.warning(f"[COMPRAS_REPO] save_compras_params ignorado en modo stub")
        return
    ...
```

**Recomendación:** 
- **NO revertir** a código que explote sin MongoDB
- **REEMPLAZAR** con implementación SQL real
- Crear `repository_compras_sql.py` con funciones equivalentes
- Modificar `repository.py` para llamar a SQL en lugar de MongoDB

---

## 13. FASES PROPUESTAS

| Fase | Descripción | Prioridad | Archivos a modificar |
|------|-------------|-----------|---------------------|
| **1** | Crear tabla `Compras_Parametros_Sucursal` en EDARSAHUB | P0 | DDL script |
| **2** | Crear `repository_compras_sql.py` con funciones SQL | P0 | Nuevo archivo |
| **3** | Modificar `repository.py` para usar SQL | P0 | repository.py |
| **4** | Eliminar código MongoDB de repository.py | P1 | repository.py |
| **5** | Migrar tracking de pedidos a SQL | P1 | pedidos_detector_job.py |
| **6** | Migrar endpoints LIVE a arquitectura SQL-FIRST | P2 | server.py (múltiples endpoints) |

---

## 14. CONFIRMACIÓN DE CÓDIGO NO MODIFICADO

### ✅ Módulos NO tocados en este diagnóstico:
- Auth/RBAC
- Comercial
- Finanzas (excepto Cortes Z ya migrado)
- Costos
- Tablero Ejecutivo
- Ventas del Día
- Inventario

### ✅ Acciones realizadas:
- Solo comandos `grep` de diagnóstico
- Solo lectura de archivos
- Creación de este reporte de diagnóstico

### ⚠️ Cambios previos identificados (agente anterior):
- Parche `_stub_mode` en `repository.py` (debe reemplazarse con SQL, no revertirse)

---

## APÉNDICE: Comandos grep ejecutados

```bash
# Backend - Compras
grep -R "db\." /app/backend/modules/compras --include="*.py"
grep -R "MongoDB" /app/backend/modules/compras --include="*.py"
grep -R "AsyncIOMotorClient" /app/backend/modules/compras --include="*.py"
grep -R "init_compras" /app/backend --include="*.py"
grep -R "repository" /app/backend/modules/compras --include="*.py"
grep -R "proveedor" /app/backend/modules/compras --include="*.py"
grep -R "orden" /app/backend/modules/compras --include="*.py"
grep -R "solicitud" /app/backend/modules/compras --include="*.py"

# Frontend
grep -R "compras" /app/frontend/src --include="*.jsx" --include="*.js"
grep -R "proveedor" /app/frontend/src --include="*.jsx" --include="*.js"
grep -R "/api/compras" /app/frontend/src --include="*.jsx" --include="*.js"

# Tablas SQL
grep -R "Compras_" /app/backend --include="*.py"
```

---

**Firmado:** E1 Agent  
**Rol:** Arquitecto de Software Senior y Especialista ERP  
**Estado:** Diagnóstico completado - Pendiente aprobación para fase de migración
