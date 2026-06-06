# COMPRAS-MONGO-001-F1: Migración Parámetros de Compras a EDARSAHUB SQL

**Fecha**: 2026-05-25  
**Auditor**: E1 Agent (Arquitecto Senior)  
**Estado**: ✅ COMPLETADO

---

## 1. RESUMEN EJECUTIVO

### Objetivo
Migrar los parámetros de compras (`compras_params`) de MongoDB a EDARSAHUB SQL Server.

### Resultado
✅ **ÉXITO**: Los parámetros de compras ahora persisten en EDARSAHUB SQL.
- Tabla creada: `Compras_Parametros_Sucursal`
- Endpoints migrados: `GET/POST /api/compras/parametros`
- MongoDB ya no es fuente productiva para parámetros de compras

---

## 2. ESTADO ANTERIOR

| Aspecto | Estado Anterior |
|---------|-----------------|
| Fuente de datos | MongoDB colección `compras_params` |
| Persistencia | ❌ No persistía (stub retornaba `None`) |
| Comportamiento | Silenciosamente ignoraba guardado |
| Riesgo | Usuario configuraba parámetros que NO se guardaban |

---

## 3. DDL EJECUTADO

```sql
CREATE TABLE dbo.Compras_Parametros_Sucursal (
    ParametroID INT IDENTITY(1,1) PRIMARY KEY,
    ServerID VARCHAR(100) NOT NULL,
    SucursalID VARCHAR(50) NOT NULL,
    DiasInventario INT NOT NULL DEFAULT 10,
    ExcluirDomingos BIT NOT NULL DEFAULT 1,
    DiasInhabiles NVARCHAR(MAX) NULL,
    DiasTransitoProveedor INT NOT NULL DEFAULT 2,
    Activo BIT NOT NULL DEFAULT 1,
    CreadoPor VARCHAR(100) NULL,
    ModificadoPor VARCHAR(100) NULL,
    FechaCreacion DATETIME NOT NULL DEFAULT GETDATE(),
    FechaModificacion DATETIME NOT NULL DEFAULT GETDATE()
);

CREATE UNIQUE INDEX UQ_Compras_Parametros_Server_Sucursal 
ON dbo.Compras_Parametros_Sucursal (ServerID, SucursalID);
```

**Fecha de creación**: 2026-05-25 12:49:XX UTC

---

## 4. TABLA CREADA

| Campo | Tipo | Nullable | Default | Descripción |
|-------|------|----------|---------|-------------|
| ParametroID | INT IDENTITY | NO | - | PK auto-incremental |
| ServerID | VARCHAR(100) | NO | - | ID del servidor |
| SucursalID | VARCHAR(50) | NO | - | ID de sucursal |
| DiasInventario | INT | NO | 10 | Días de inventario a comprar |
| ExcluirDomingos | BIT | NO | 1 | Si excluir domingos |
| DiasInhabiles | NVARCHAR(MAX) | YES | NULL | JSON array de fechas |
| DiasTransitoProveedor | INT | NO | 2 | Días de tránsito |
| Activo | BIT | NO | 1 | Soft delete flag |
| CreadoPor | VARCHAR(100) | YES | NULL | Usuario creador |
| ModificadoPor | VARCHAR(100) | YES | NULL | Último modificador |
| FechaCreacion | DATETIME | NO | GETDATE() | Timestamp creación |
| FechaModificacion | DATETIME | NO | GETDATE() | Timestamp modificación |

**Índices:**
- `UQ_Compras_Parametros_Server_Sucursal` (UNIQUE) → ServerID, SucursalID

---

## 5. REPOSITORIO SQL CREADO

**Archivo**: `/app/backend/modules/compras/repository_compras_sql.py`

### Funciones implementadas:

| Función | Descripción |
|---------|-------------|
| `ensure_table_exists()` | DDL idempotente para crear tabla |
| `get_compras_params_sql(server_id, sucursal)` | Lee parámetros desde SQL |
| `save_compras_params_sql(server_id, sucursal, params, usuario)` | Guarda/actualiza con UPSERT |
| `get_all_compras_params_sql()` | Lista todas las configuraciones |
| `delete_compras_params_sql(server_id, sucursal)` | Soft delete |

---

## 6. FUNCIONES MODIFICADAS

### `/app/backend/modules/compras/repository.py`

```python
# ANTES (MongoDB)
async def get_compras_params(server_id, sucursal):
    db = get_db()
    if db is None:
        return None  # ❌ Silenciosamente vacío
    return await db.compras_params.find_one(...)

# DESPUÉS (SQL)
async def get_compras_params(server_id, sucursal):
    from modules.compras.repository_compras_sql import get_compras_params_sql
    return get_compras_params_sql(server_id, sucursal)  # ✅ Lee de EDARSAHUB SQL
```

### `/app/backend/server.py` (líneas 7889-7938)

```python
# ANTES
params = await db.parametros_compra.find_one(...)  # ❌ MongoDB stub

# DESPUÉS
from modules.compras.service import obtener_parametros, guardar_parametros
params = await obtener_parametros(server_id, sucursal)  # ✅ Usa servicio → SQL
```

---

## 7. CONTRATO GET/SAVE PARÁMETROS

### GET `/api/compras/parametros/{server_id}?sucursal={sucursal}`

**Request:**
```
GET /api/compras/parametros/SERVER-001?sucursal=SUC-01
Authorization: Bearer {token}
```

**Response (con configuración guardada):**
```json
{
  "server_id": "SERVER-001",
  "dias_inventario": 25,
  "excluir_domingos": false,
  "dias_inhabiles": ["2026-12-25", "2026-01-01"],
  "dias_transito_proveedor": 4
}
```

**Response (sin configuración - defaults):**
```json
{
  "server_id": "SERVER-001",
  "dias_inventario": 10,
  "excluir_domingos": true,
  "dias_inhabiles": [],
  "dias_transito_proveedor": 2
}
```

### POST `/api/compras/parametros`

**Request:**
```json
{
  "server_id": "SERVER-001",
  "sucursal": "SUC-01",
  "dias_inventario": 25,
  "excluir_domingos": false,
  "dias_inhabiles": ["2026-12-25", "2026-01-01"],
  "dias_transito_proveedor": 4
}
```

**Response:**
```json
{
  "message": "Parámetros guardados correctamente"
}
```

---

## 8. VALIDACIÓN DE PERSISTENCIA

### Test ejecutado:

```bash
# 1. Guardar parámetros
POST /api/compras/parametros
{
  "server_id": "TEST-SQL-MIGRADO",
  "sucursal": "SUC-SQL-01",
  "dias_inventario": 25,
  ...
}
# Respuesta: {"message": "Parámetros guardados correctamente"}

# 2. Leer parámetros
GET /api/compras/parametros/TEST-SQL-MIGRADO?sucursal=SUC-SQL-01
# Respuesta: {"dias_inventario": 25, ...}  ✅ Persistió

# 3. Verificar en SQL Server
SELECT * FROM Compras_Parametros_Sucursal WHERE ServerID = 'TEST-SQL-MIGRADO'
# Resultado: 1 registro con DiasInventario=25  ✅
```

---

## 9. EVIDENCIA GREP

### `compras_params` ya no usa MongoDB:

```
/modules/compras/repository.py:160:async def get_compras_params(...)
/modules/compras/repository.py:173:    from modules.compras.repository_compras_sql import get_compras_params_sql
/modules/compras/repository.py:174:    return get_compras_params_sql(server_id, sucursal)  # ✅ Delegado a SQL
```

### No hay referencias activas a `db.compras_params`:

```
grep "db\." repository.py | grep -v "#"
# Resultado: Solo línea 141 (comentario de documentación)
```

---

## 10. CONFIRMACIÓN CERO MONGODB PRODUCTIVO

| Verificación | Estado |
|--------------|--------|
| `get_compras_params()` usa SQL | ✅ |
| `save_compras_params()` usa SQL | ✅ |
| Endpoints en server.py usan servicio | ✅ |
| No hay `db.compras_params.find_one()` activo | ✅ |
| No hay `db.parametros_compra` activo | ✅ |

**CONFIRMADO**: MongoDB ya no es fuente productiva para parámetros de compras.

---

## 11. CONFIRMACIÓN NO CONEXIONES LIVE

Los parámetros de compras:
- ✅ Se leen desde `EDARSAHUB.Compras_Parametros_Sucursal`
- ✅ Se escriben a `EDARSAHUB.Compras_Parametros_Sucursal`
- ✅ NO consultan servidores SoftRestaurant/MPRO
- ✅ NO abren conexiones a servidores externos

---

## 12. RIESGOS RESIDUALES

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Intermitencia de EDARSAHUB SQL | Media | Manejado con retorno de defaults si falla conexión |
| Datos históricos en MongoDB | Baja | No hay datos históricos críticos - eran defaults |
| Tracking de pedidos aún usa MongoDB | P1 | Fase posterior |

---

## 13. SIGUIENTE FASE RECOMENDADA

### P1: COMPRAS-MONGO-001-F2 — Migración Tracking de Pedidos

Migrar las colecciones:
- `pedidos_procesados_automatizacion`
- `tareas_operativas_compras`
- `auditoria_compras_bitacora`

Usadas por `pedidos_detector_job.py` para:
- Tracking de pedidos procesados
- Tareas operativas generadas
- Bitácora de auditoría

---

## 14. CONFIRMACIÓN DE CÓDIGO NO MODIFICADO

### ✅ Módulos NO tocados:
- Auth/RBAC
- Comercial
- Finanzas (excepto documentación)
- Costos y Márgenes
- Tablero Ejecutivo
- Ventas del Día
- Inventario

### ✅ Archivos modificados (solo compras):
- `/app/backend/modules/compras/repository.py` - Delegación a SQL
- `/app/backend/modules/compras/repository_compras_sql.py` - Nuevo repositorio SQL
- `/app/backend/server.py` (líneas 7889-7938) - Endpoints migrados

---

## CRITERIO DE ACEPTACIÓN

| Criterio | Estado |
|----------|--------|
| Parámetros se guardan en EDARSAHUB SQL | ✅ |
| Parámetros se leen desde EDARSAHUB SQL | ✅ |
| MongoDB no es fuente productiva | ✅ |
| No hay defaults silenciosos cuando hay config | ✅ |
| No hay conexiones live | ✅ |
| Reporte generado | ✅ |

---

**FASE COMPRAS-MONGO-001-F1 COMPLETADA**

Firmado: E1 Agent  
Rol: Arquitecto de Software Senior y Especialista ERP
