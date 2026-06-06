# DISEÑO DE ESCRITURA SEGURA EN EDARSAHUB PARA SERVER QUERIES
## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE E

**Fecha:** 2025-12-19  
**Estado:** DISEÑO COMPLETADO — PENDIENTE APROBACIÓN  
**Autor:** Agente E1  
**Versión:** 1.0

---

## 1. RESUMEN EJECUTIVO

### Hallazgos Clave

| Elemento | Estado | Ubicación |
|----------|--------|-----------|
| Tabla principal | ✅ EXISTE | `Servidores_Conexiones` |
| Columnas de queries | ✅ EXISTEN | `query_inventario`, `query_ventas`, `query_movimientos` |
| Flag de configuración | ✅ EXISTE | `queries_configured` |
| Campos de auditoría | ✅ EXISTEN | `updated_at`, `updated_by` |
| Tabla de log | ✅ EXISTE | `Servidores_Conexiones_Log` |

### Conclusión

**EDARSAHUB ya tiene toda la infraestructura necesaria** para almacenar queries configurables. No se requiere crear tablas ni columnas nuevas.

---

## 2. DIAGNÓSTICO: UBICACIÓN ACTUAL DE QUERIES CONFIGURABLES

### 2.1 Estado Actual

| Elemento | Fuente Actual | Fuente Correcta |
|----------|---------------|-----------------|
| `query_inventario` | MongoDB `db.servers` | EDARSAHUB `Servidores_Conexiones` |
| `query_ventas` | MongoDB `db.servers` | EDARSAHUB `Servidores_Conexiones` |
| `query_movimientos` | MongoDB `db.servers` | EDARSAHUB `Servidores_Conexiones` |
| `queries_configured` | MongoDB `db.servers` | EDARSAHUB `Servidores_Conexiones` |

### 2.2 Formato de Datos

Actualmente en MongoDB, cada `query_*` almacena un objeto JSON:

```json
{
    "sql": "SELECT producto, cantidad FROM inventario WHERE ...",
    "validated": true,
    "last_validated": "2025-12-19T10:30:00.000Z",
    "validation_message": "Validada correctamente"
}
```

En EDARSAHUB, la columna es `nvarchar(max)` y puede almacenar el mismo JSON como string.

---

## 3. TABLA DESTINO EN EDARSAHUB

### 3.1 Tabla Principal

| Campo | Valor |
|-------|-------|
| **Nombre** | `Servidores_Conexiones` |
| **PK** | `id` (uniqueidentifier) |
| **Database** | `EDARSAHUB` |

### 3.2 Columnas Relevantes para Queries

| Columna | Tipo | Nullable | Default | Propósito |
|---------|------|----------|---------|-----------|
| `id` | uniqueidentifier | NOT NULL | `newid()` | PK del servidor |
| `query_inventario` | nvarchar(max) | NULL | — | JSON con config de query |
| `query_ventas` | nvarchar(max) | NULL | — | JSON con config de query |
| `query_movimientos` | nvarchar(max) | NULL | — | JSON con config de query |
| `queries_configured` | bit | NULL | 0 | Flag de todas configuradas |
| `updated_at` | datetime | NULL | `getdate()` | Última actualización |
| `updated_by` | nvarchar(100) | NULL | — | Usuario que actualizó |

### 3.3 Tabla de Auditoría

| Campo | Valor |
|-------|-------|
| **Nombre** | `Servidores_Conexiones_Log` |
| **PK** | `log_id` (bigint, identity) |

| Columna | Tipo | Propósito |
|---------|------|-----------|
| `log_id` | bigint | PK auto-incremental |
| `servidor_id` | uniqueidentifier | FK al servidor modificado |
| `accion` | nvarchar(20) | 'UPDATE', 'DELETE', etc. |
| `datos_anteriores` | nvarchar(max) | JSON con valores previos |
| `datos_nuevos` | nvarchar(max) | JSON con valores nuevos |
| `usuario` | nvarchar(100) | Email del usuario |
| `fecha` | datetime | Timestamp de la operación |
| `ip_origen` | nvarchar(50) | IP del cliente (opcional) |

---

## 4. ANÁLISIS DE `save_server_query()`

### 4.1 Comportamiento Actual

| Aspecto | Valor |
|---------|-------|
| **Endpoint** | `PUT /api/servers/{server_id}/queries/{query_type}` |
| **Línea** | 1615-1671 |
| **Recibe** | `server_id`, `query_type`, `{sql, validated}` |

### 4.2 Validaciones Actuales

| Validación | Implementada |
|------------|--------------|
| `query_type` en whitelist | ✅ Sí (`REQUIRED_COLUMNS`) |
| `sql` no vacío | ✅ Sí |
| Servidor existe y activo | ✅ Sí |
| Usuario autenticado | ✅ Sí |
| Rol específico | ❌ No (cualquier usuario autenticado) |

### 4.3 Escrituras Actuales

| Paso | Qué escribe | Dónde |
|------|-------------|-------|
| 1 | `query_{type}` con JSON | MongoDB `db.servers` |
| 2 | `queries_configured` (recalculado) | MongoDB `db.servers` |

### 4.4 Respuesta Actual

```json
{
    "message": "Consulta de {query_type} guardada exitosamente",
    "query_type": "inventario",
    "validated": true,
    "all_queries_configured": true
}
```

---

## 5. ANÁLISIS DE `delete_server_query()`

### 5.1 Comportamiento Actual

| Aspecto | Valor |
|---------|-------|
| **Endpoint** | `DELETE /api/servers/{server_id}/queries/{query_type}` |
| **Línea** | 1721-1743 |
| **Recibe** | `server_id`, `query_type` |

### 5.2 Estrategia de Eliminación Actual

| Pregunta | Respuesta |
|----------|-----------|
| ¿Elimina o nulifica? | **Nulifica** (`$set: {field_name: None}`) |
| ¿Borra histórico? | No (MongoDB no tiene histórico) |
| ¿Actualiza flag? | Sí (`queries_configured: False`) |

### 5.3 Validaciones Actuales

| Validación | Implementada |
|------------|--------------|
| `query_type` en whitelist | ✅ Sí |
| Servidor existe y activo | ✅ Sí |
| Usuario autenticado | ✅ Sí |
| Rol específico | ❌ No |

---

## 6. PROPUESTA DE FUNCIONES SEGURAS EN `server_registry.py`

### 6.1 `update_server_query()`

```python
async def update_server_query(
    server_id: str,
    query_type: str,
    query_config: dict,
    user_email: str,
    db=None
) -> dict:
    """
    Actualiza configuración de query en EDARSAHUB con auditoría.
    
    Args:
        server_id: UUID del servidor
        query_type: Tipo de query ('inventario', 'ventas', 'movimientos')
        query_config: Dict con {sql, validated, last_validated, validation_message}
        user_email: Email del usuario que realiza el cambio
        db: Conexión MongoDB (para fallback si aplica)
    
    Returns:
        Dict con resultado de la operación
    
    Raises:
        ValueError: Si query_type no está en whitelist
        HTTPException: Si servidor no existe o no tiene permisos
    
    Whitelist:
        - 'inventario'
        - 'ventas'
        - 'movimientos'
    
    Auditoría:
        - Registra en Servidores_Conexiones_Log
        - Guarda datos anteriores y nuevos
        - Registra usuario y timestamp
    """
    # Implementación propuesta
    pass
```

### 6.2 `clear_server_query()`

```python
async def clear_server_query(
    server_id: str,
    query_type: str,
    user_email: str,
    db=None
) -> dict:
    """
    Limpia (nulifica) una query configurada en EDARSAHUB con auditoría.
    
    Args:
        server_id: UUID del servidor
        query_type: Tipo de query ('inventario', 'ventas', 'movimientos')
        user_email: Email del usuario que realiza el cambio
        db: Conexión MongoDB (para fallback si aplica)
    
    Returns:
        Dict con resultado de la operación
    
    Comportamiento:
        - Nulifica el campo query_{type} (no borra registro)
        - Actualiza queries_configured = 0
        - Registra en log con datos anteriores
    """
    # Implementación propuesta
    pass
```

---

## 7. REGLAS DE SEGURIDAD PROPUESTAS

### 7.1 Whitelist de Columnas

```python
ALLOWED_QUERY_TYPES = frozenset(['inventario', 'ventas', 'movimientos'])
```

**Regla:** Solo se permite escribir en columnas de esta whitelist. Cualquier otro valor debe rechazarse con error 400.

### 7.2 Validación de Permisos

| Nivel | Recomendación | Justificación |
|-------|---------------|---------------|
| **Usuario autenticado** | ✅ Obligatorio | Ya implementado |
| **Rol Admin/Supervisor** | ⚠️ **RECOMENDADO** | Queries configuradas afectan reportes |
| **Alcance de servidor** | ⚠️ **RECOMENDADO** | Usuario debe tener acceso al servidor |

### 7.3 Validación de Servidor

```python
# Verificar que servidor existe en EDARSAHUB
server = await get_server_by_id(server_id, db=db, prefer_sql=True)
if not server:
    raise HTTPException(status_code=404, detail="Servidor no encontrado")

# Verificar que usuario tiene alcance (RBAC)
# await validate_server_access_unified(current_user, server_id)
```

### 7.4 No Exponer SQL Sensible

```python
# En logs, NO guardar SQL completo si contiene datos sensibles
# Solo guardar hash o resumen
import hashlib

def hash_sql(sql: str) -> str:
    return hashlib.sha256(sql.encode()).hexdigest()[:16]

# En log: {"sql_hash": "a1b2c3d4e5f6..."}
```

---

## 8. ESTRATEGIA DE ELIMINACIÓN

### 8.1 Comportamiento Propuesto

| Acción | Comportamiento | Justificación |
|--------|----------------|---------------|
| DELETE endpoint | **Nulificar** (no borrar) | Mantener registro del servidor |
| Campo | `SET query_{type} = NULL` | Reversible |
| Flag | `SET queries_configured = 0` | Consistencia |
| Auditoría | Guardar valor anterior en log | Recuperabilidad |

### 8.2 SQL Propuesto para Eliminación

```sql
-- Paso 1: Obtener datos actuales para log
DECLARE @datos_anteriores NVARCHAR(MAX);
SELECT @datos_anteriores = query_{type} FROM Servidores_Conexiones WHERE id = @server_id;

-- Paso 2: Actualizar servidor
UPDATE Servidores_Conexiones
SET 
    query_{type} = NULL,
    queries_configured = 0,
    updated_at = GETDATE(),
    updated_by = @user_email
WHERE id = @server_id;

-- Paso 3: Registrar en log
INSERT INTO Servidores_Conexiones_Log (servidor_id, accion, datos_anteriores, datos_nuevos, usuario, fecha)
VALUES (@server_id, 'CLEAR_QUERY', @datos_anteriores, NULL, @user_email, GETDATE());
```

---

## 9. AUDITORÍA

### 9.1 Estructura de Log Propuesta

```json
{
    "log_id": 1,
    "servidor_id": "a5547321-1139-4d2b-9d53-182ca737b6b6",
    "accion": "UPDATE_QUERY",
    "datos_anteriores": {
        "query_type": "inventario",
        "sql_hash": "a1b2c3d4",
        "validated": false
    },
    "datos_nuevos": {
        "query_type": "inventario",
        "sql_hash": "e5f6g7h8",
        "validated": true
    },
    "usuario": "admin@example.com",
    "fecha": "2025-12-19T10:30:00",
    "ip_origen": null
}
```

### 9.2 Qué Registrar

| Campo | Registrar | Motivo |
|-------|-----------|--------|
| `sql` completo | ⚠️ **Solo hash** | SQL puede contener datos sensibles |
| `validated` | ✅ Sí | Estado de validación |
| `last_validated` | ✅ Sí | Timestamp |
| `query_type` | ✅ Sí | Identificar qué query cambió |
| Usuario | ✅ Sí | Trazabilidad |
| Timestamp | ✅ Sí | Orden cronológico |

### 9.3 No Guardar en Logs

- SQL completo (puede contener lógica de negocio sensible)
- Credenciales
- Tokens
- Connection strings

---

## 10. ROLLBACK

### 10.1 Estrategia de Rollback

| Escenario | Acción |
|-----------|--------|
| Query incorrecta guardada | Leer `datos_anteriores` del log y restaurar |
| Error de escritura | Transacción fallida, no hay cambio |
| Eliminación accidental | Leer `datos_anteriores` del log y restaurar |

### 10.2 Función de Rollback Propuesta

```python
async def rollback_server_query(
    server_id: str,
    query_type: str,
    log_id: int,  # ID del registro de log a revertir
    user_email: str
) -> dict:
    """
    Revierte una query a su estado anterior usando el log.
    
    Args:
        log_id: ID del registro en Servidores_Conexiones_Log
    
    Proceso:
        1. Leer datos_anteriores del log
        2. Actualizar servidor con datos anteriores
        3. Registrar nuevo log con acción 'ROLLBACK'
    """
    pass
```

### 10.3 Limitaciones

| Limitación | Mitigación |
|------------|------------|
| Log actualmente vacío | El sistema empezará a registrar al implementar |
| No hay histórico previo | Solo funciona para cambios post-implementación |
| Retención de logs | Definir política de retención (ej: 90 días) |

---

## 11. PERMISOS DE ESCRITURA EN EDARSAHUB

### 11.1 Estado Actual

| Usuario | Permisos |
|---------|----------|
| `HRLectura` | **SOLO LECTURA** |

### 11.2 Requerimiento

Para implementar escrituras, se necesita:

1. **Usuario con permisos de escritura** en EDARSAHUB
2. O **crear nuevo usuario** con permisos específicos:
   - `UPDATE` en `Servidores_Conexiones`
   - `INSERT` en `Servidores_Conexiones_Log`

### 11.3 Propuesta de Permisos Mínimos

```sql
-- Crear usuario específico para escrituras (propuesta)
CREATE LOGIN EdarsaHubWriter WITH PASSWORD = '***';
CREATE USER EdarsaHubWriter FOR LOGIN EdarsaHubWriter;

-- Permisos mínimos
GRANT UPDATE ON Servidores_Conexiones TO EdarsaHubWriter;
GRANT INSERT ON Servidores_Conexiones_Log TO EdarsaHubWriter;
GRANT SELECT ON Servidores_Conexiones TO EdarsaHubWriter;
GRANT SELECT ON Servidores_Conexiones_Log TO EdarsaHubWriter;
```

**NOTA:** Este script NO debe ejecutarse sin autorización del DBA.

---

## 12. RESUMEN DE RECOMENDACIONES

### 12.1 Tabla de Clasificación

| Función | Acción actual | Tabla destino | Permisos | Validaciones requeridas | Riesgo | Propuesta |
|---------|---------------|---------------|----------|-------------------------|--------|-----------|
| `save_server_query()` | UPDATE MongoDB | `Servidores_Conexiones` | Autenticado → **Admin** | Whitelist, servidor existe, alcance RBAC | MEDIO | Migrar con auditoría |
| `delete_server_query()` | SET NULL MongoDB | `Servidores_Conexiones` | Autenticado → **Admin** | Whitelist, servidor existe, alcance RBAC | BAJO | Migrar con auditoría |

### 12.2 Prerrequisitos para Lote 7

| Prerrequisito | Estado | Acción |
|---------------|--------|--------|
| Usuario EDARSAHUB con escritura | ⚠️ PENDIENTE | Solicitar a DBA o usar existente |
| Whitelist de query_types | ✅ Ya existe | `REQUIRED_COLUMNS` |
| Tabla de log | ✅ Ya existe | `Servidores_Conexiones_Log` |
| Campos de auditoría | ✅ Ya existen | `updated_at`, `updated_by` |
| Función `update_server_query()` | ⚠️ PENDIENTE | Implementar en registry |
| Función `clear_server_query()` | ⚠️ PENDIENTE | Implementar en registry |

---

## 13. SCRIPT SQL PROPUESTO (NO EJECUTAR)

### 13.1 Validar Estructura Existente

```sql
-- /app/docs/sql/VALIDATE_SERVER_QUERIES_STRUCTURE.sql
-- SOLO LECTURA - Validar que la estructura existe

SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Servidores_Conexiones'
AND COLUMN_NAME IN ('query_inventario', 'query_ventas', 'query_movimientos', 
                    'queries_configured', 'updated_at', 'updated_by');

-- Verificar log existe
SELECT COUNT(*) AS log_exists 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'Servidores_Conexiones_Log';
```

### 13.2 Script de Permisos (Propuesta - NO EJECUTAR)

```sql
-- /app/docs/sql/GRANT_WRITE_PERMISSIONS_PROPOSAL.sql
-- PROPUESTA - Requiere autorización de DBA

-- Opción A: Usar usuario existente con más permisos
-- Opción B: Crear usuario nuevo (ver sección 11.3)

-- NO EJECUTAR SIN AUTORIZACIÓN
```

---

## 14. CONCLUSIÓN

### Estado de Preparación para Lote 7

| Criterio | Estado |
|----------|--------|
| Destino claro en EDARSAHUB | ✅ Confirmado |
| Whitelist de columnas | ✅ Definida |
| Tabla de log existe | ✅ Confirmado |
| Campos de auditoría existen | ✅ Confirmado |
| Usuario con escritura | ⚠️ **PENDIENTE** |
| Funciones de registry | ⚠️ **PENDIENTE** |
| Validación de permisos | ⚠️ A implementar |
| Rollback definido | ✅ Diseñado |

### Bloqueador Principal

**Usuario `HRLectura` es solo lectura.** Se requiere:
1. Usar/solicitar usuario con permisos de escritura
2. O verificar si existe otro usuario en variables de entorno

---

**Documento generado por Agente E1 — EDARSA HUB**  
**Fecha:** 2025-12-19  
**Estado:** DISEÑO COMPLETADO — PENDIENTE APROBACIÓN USUARIO
