# PLAN DE LOTE 6 — ESCRITURAS DE CONFIGURACIÓN
## CONEXIONES-SQL-EDARSAHUB-01 / SUBFASE C.6-PLAN

**Fecha:** 2025-12-19  
**Estado:** PLAN PROPUESTO — PENDIENTE APROBACIÓN  
**Autor:** Agente E1  
**Versión:** 1.0

---

## 1. RESUMEN EJECUTIVO

### Candidatos Analizados

| # | Función | Tipo Escritura | Fuente Actual | Destino Correcto | Recomendación |
|---|---------|----------------|---------------|------------------|---------------|
| 1 | `save_server_query()` | Config queries SQL | MongoDB `db.servers` | **EDARSAHUB** (`Servidores_Conexiones.query_*`) | ⚠️ REQUIERE ANÁLISIS |
| 2 | `delete_server_query()` | Eliminación config | MongoDB `db.servers` | **EDARSAHUB** (`Servidores_Conexiones.query_*`) | ⚠️ REQUIERE ANÁLISIS |
| 3 | `guardar_script_pendiente()` | Scripts stand-by | MongoDB `db.scripts_pendientes` | **MANTENER EN MONGODB** | ✅ MIGRAR SOLO LECTURA |

### Hallazgo Crítico

**EDARSAHUB sí tiene campos para queries configuradas:**
- `Servidores_Conexiones.query_inventario` (nvarchar(max))
- `Servidores_Conexiones.query_ventas` (nvarchar(max))
- `Servidores_Conexiones.query_movimientos` (nvarchar(max))
- `Servidores_Conexiones.queries_configured` (bit)

**EDARSAHUB NO tiene tabla para scripts pendientes:**
- No existe tabla `scripts_pendientes` ni similar
- MongoDB es el destino correcto para este tipo de documentos operativos temporales

---

## 2. ANÁLISIS DETALLADO POR FUNCIÓN

### 2.1 `save_server_query()` — Líneas 1615-1671

#### Información General

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 1615-1671 |
| **Endpoint** | `PUT /api/servers/{server_id}/queries/{query_type}` |
| **Decorador** | `@api_router.put("/servers/{server_id}/queries/{query_type}")` |

#### Análisis de Escritura

| Aspecto | Valor |
|---------|-------|
| **Qué escribe** | Configuración de queries SQL (inventario, ventas, movimientos) |
| **Formato de datos** | JSON con campos: `sql`, `validated`, `last_validated`, `validation_message` |
| **Dónde escribe actualmente** | MongoDB `db.servers` (campo `query_{type}`) |
| **Dónde debería escribir** | **EDARSAHUB** `Servidores_Conexiones.query_{type}` |

#### Bypasses en la Función

| Línea | Bypass | Propósito |
|-------|--------|-----------|
| 1634 | `db.servers.find_one({"id": server_id, "active": True})` | Verificar que servidor existe |
| 1648-1651 | `db.servers.update_one(...)` | **ESCRIBIR** query configurada |
| 1654 | `db.servers.find_one({"id": server_id})` | Verificar si todas las queries están configuradas |
| 1661-1664 | `db.servers.update_one(...)` | **ESCRIBIR** flag `queries_configured` |

#### Tabla Destino en EDARSAHUB

```sql
-- Columnas existentes en Servidores_Conexiones:
query_inventario    nvarchar(max)  -- Almacena JSON con sql, validated, etc.
query_ventas        nvarchar(max)  -- Almacena JSON con sql, validated, etc.
query_movimientos   nvarchar(max)  -- Almacena JSON con sql, validated, etc.
queries_configured  bit            -- Flag de todas configuradas
```

#### Complejidad de Migración

| Factor | Evaluación |
|--------|------------|
| Lectura servidor | ✅ Ya migrable con `get_server_connection_info()` |
| Escritura query | ⚠️ **REQUIERE escribir en EDARSAHUB** |
| Lectura verificación | ⚠️ **REQUIERE leer de EDARSAHUB** |
| Escritura flag | ⚠️ **REQUIERE escribir en EDARSAHUB** |

#### Permisos Requeridos

| Permiso | Actual | Comentario |
|---------|--------|------------|
| Usuario autenticado | Sí | `current_user: Dict = Depends(get_current_user)` |
| Rol específico | **NO** | Cualquier usuario autenticado puede configurar queries |

#### Riesgo

| Riesgo | Nivel | Mitigación |
|--------|-------|------------|
| Pérdida de queries configuradas | **ALTO** | Sincronizar antes de migrar |
| Escritura incorrecta en EDARSAHUB | **ALTO** | Validar formato JSON compatible |
| Romper configuración existente | **ALTO** | Backup previo |

#### Recomendación

**⚠️ REQUIERE SINCRONIZACIÓN PREVIA**

Antes de migrar esta función:
1. Verificar que las queries en MongoDB estén sincronizadas a EDARSAHUB
2. Implementar función de escritura a EDARSAHUB en `server_registry.py`
3. Validar que el formato JSON es compatible

**Clasificación: REQUIERE TABLA/CAMPO EN EDARSAHUB** (ya existe, pero requiere función de escritura)

---

### 2.2 `delete_server_query()` — Líneas 1721-1743

#### Información General

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 1721-1743 |
| **Endpoint** | `DELETE /api/servers/{server_id}/queries/{query_type}` |

#### Análisis de Escritura

| Aspecto | Valor |
|---------|-------|
| **Qué elimina** | Query configurada de un tipo específico |
| **Dónde elimina actualmente** | MongoDB `db.servers` (campo `query_{type}` = null) |
| **Dónde debería eliminar** | **EDARSAHUB** `Servidores_Conexiones.query_{type}` = NULL |

#### Bypasses en la Función

| Línea | Bypass | Propósito |
|-------|--------|-----------|
| 1733 | `db.servers.find_one({"id": server_id, "active": True})` | Verificar que servidor existe |
| 1738-1740 | `db.servers.update_one(...)` | **ESCRIBIR** null en query + flag |

#### Permisos Requeridos

| Permiso | Actual | Comentario |
|---------|--------|------------|
| Usuario autenticado | Sí | `current_user: Dict = Depends(get_current_user)` |
| Rol específico | **NO** | Cualquier usuario autenticado puede eliminar queries |

#### Riesgo

| Riesgo | Nivel | Mitigación |
|--------|-------|------------|
| Eliminación accidental | MEDIO | Ya existe el riesgo en MongoDB |
| Desincronización MongoDB/EDARSAHUB | MEDIO | Eliminar de ambos o solo EDARSAHUB |

#### Recomendación

**⚠️ DEPENDE DE `save_server_query()`**

Esta función debe migrarse junto con `save_server_query()` para mantener consistencia.

**Clasificación: REQUIERE TABLA/CAMPO EN EDARSAHUB** (ya existe)

---

### 2.3 `guardar_script_pendiente()` — Líneas 11010-11052

#### Información General

| Campo | Valor |
|-------|-------|
| **Archivo** | `/app/backend/server.py` |
| **Línea** | 11010-11052 |
| **Endpoint** | `POST /api/explorador/guardar-script/{server_id}` |

#### Análisis de Escritura

| Aspecto | Valor |
|---------|-------|
| **Qué escribe** | Script SQL pendiente de ejecución (stand-by) |
| **Formato de datos** | Documento MongoDB con: server_id, titulo, script, estado, creado_por, fecha |
| **Dónde escribe actualmente** | MongoDB `db.scripts_pendientes` |
| **Dónde debería escribir** | **MANTENER EN MONGODB** |

#### Justificación de Mantener en MongoDB

1. **No existe tabla en EDARSAHUB** para scripts pendientes
2. **Es un documento operativo temporal**, no configuración maestra
3. **El script se ejecuta y luego cambia de estado** (no es dato estático)
4. **MongoDB es apropiado** para este tipo de documentos de cola/workflow

#### Bypasses en la Función

| Línea | Bypass | Propósito |
|-------|--------|-----------|
| 11023 | `db.servers.find_one({"id": server_id, "active": True})` | Verificar que servidor existe |
| 11041-11050 | `db.scripts_pendientes.insert_one(...)` | **ESCRIBIR** script pendiente (correcto en MongoDB) |

#### Permisos Requeridos

| Permiso | Actual | Comentario |
|---------|--------|------------|
| Rol Administrador | **SÍ** | Solo administradores pueden guardar scripts |

#### Riesgo

| Riesgo | Nivel | Mitigación |
|--------|-------|------------|
| Pérdida de scripts | BAJO | MongoDB tiene backups |
| Ejecución no autorizada | BAJO | Validación de rol Admin |

#### Recomendación

**✅ MIGRAR SOLO LA LECTURA DEL SERVIDOR**

El bypass en línea 11023 debe migrar a `get_server_connection_info()`, pero la escritura a `db.scripts_pendientes` debe **mantenerse en MongoDB**.

**Clasificación: MANTENER TEMPORALMENTE EN MONGODB COMO DOCUMENTO OPERATIVO**

---

## 3. TABLA RESUMEN DE CLASIFICACIÓN

| Función | Tipo de escritura | Fuente actual | Fuente correcta | Tabla destino | Permisos | Riesgo | Recomendación | Rollback |
|---------|-------------------|---------------|-----------------|---------------|----------|--------|---------------|----------|
| `save_server_query()` | Config queries SQL | MongoDB `db.servers.query_*` | EDARSAHUB `Servidores_Conexiones.query_*` | `Servidores_Conexiones` | Usuario autenticado | **ALTO** | REQUIERE FUNCIÓN ESCRITURA | Restaurar de backup |
| `delete_server_query()` | Eliminación config | MongoDB `db.servers.query_*` | EDARSAHUB `Servidores_Conexiones.query_*` | `Servidores_Conexiones` | Usuario autenticado | **MEDIO** | DEPENDE DE save_server_query | Restaurar de backup |
| `guardar_script_pendiente()` | Scripts stand-by | MongoDB `db.scripts_pendientes` | **MongoDB** (correcto) | N/A | **Admin** | **BAJO** | MIGRAR SOLO LECTURA | Eliminar documento |

---

## 4. PROPUESTA DE LOTE 6

### Opción A: Lote 6 Conservador (1 cambio — RECOMENDADO)

**Solo migrar la lectura en `guardar_script_pendiente()`:**

| # | Función | Cambio | Riesgo |
|---|---------|--------|--------|
| 1 | `guardar_script_pendiente()` | Solo bypass de lectura (línea 11023) | **BAJO** |

**Justificación:**
- Es el único cambio de bajo riesgo
- La escritura permanece en MongoDB (correcto)
- No requiere función de escritura a EDARSAHUB
- No afecta configuración maestra

### Opción B: Diferir `save_server_query()` y `delete_server_query()`

Estas funciones **NO deben migrarse todavía** porque:

1. **Requieren función de escritura a EDARSAHUB** que no existe en `server_registry.py`
2. **El campo `query_*` en EDARSAHUB almacena JSON** — debe validarse compatibilidad
3. **Alto riesgo de pérdida de configuración** si falla la escritura
4. **Requieren sincronización previa** MongoDB → EDARSAHUB

---

## 5. PRERREQUISITOS PARA MIGRAR ESCRITURAS A EDARSAHUB

### 5.1 Función de Escritura Requerida

```python
# En server_registry.py
async def update_server_query(server_id: str, query_type: str, query_config: dict) -> bool:
    """
    Escribe configuración de query en EDARSAHUB.
    Requiere implementación de UPDATE SQL con manejo de JSON.
    """
    # TODO: Implementar
    pass
```

### 5.2 Sincronización Previa

Antes de migrar escrituras:
1. Exportar queries de MongoDB
2. Verificar que existen en EDARSAHUB
3. Sincronizar diferencias

### 5.3 Validación de Formato

El campo `query_*` en EDARSAHUB almacena:
```json
{
  "sql": "SELECT ...",
  "validated": true,
  "last_validated": "2025-12-19T...",
  "validation_message": "Validada correctamente"
}
```

Debe validarse que este formato es compatible con la escritura SQL.

---

## 6. VALIDACIONES PROPUESTAS PARA LOTE 6 (OPCIÓN A)

### Validaciones para `guardar_script_pendiente()`

- [ ] Endpoint responde
- [ ] Valida rol Administrador (403 para no-admin)
- [ ] Usa registry para verificar servidor
- [ ] Escribe en MongoDB `scripts_pendientes` (correcto)
- [ ] No expone credenciales
- [ ] Script se guarda con estado "pendiente"

### Validaciones de Regresión

- [ ] Lotes 1-5 sin regresión
- [ ] Auth funciona
- [ ] Backend levanta

---

## 7. ROLLBACK

### Para `guardar_script_pendiente()`

```bash
# Revertir código
git checkout HEAD~1 -- /app/backend/server.py
sudo supervisorctl restart backend

# Eliminar script pendiente si fue creado durante prueba
# (desde MongoDB shell o admin)
db.scripts_pendientes.deleteOne({_id: ObjectId("...")})
```

---

## 8. CONCLUSIÓN Y RECOMENDACIÓN FINAL

### Propuesta: LOTE 6 = 1 CAMBIO (guardar_script_pendiente)

| Función | Clasificación | Acción |
|---------|---------------|--------|
| `guardar_script_pendiente()` | **MIGRAR AHORA** (solo lectura) | ✅ Incluir en Lote 6 |
| `save_server_query()` | **REQUIERE FUNCIÓN ESCRITURA EDARSAHUB** | ⏳ Diferir a Lote 7+ |
| `delete_server_query()` | **REQUIERE FUNCIÓN ESCRITURA EDARSAHUB** | ⏳ Diferir a Lote 7+ |

### Justificación del Tamaño (1 cambio)

1. **Solo hay 1 cambio de bajo riesgo** disponible
2. **Las otras 2 funciones requieren infraestructura** que no existe
3. **No se deben migrar escrituras sin función de escritura** a EDARSAHUB
4. **Es mejor un lote pequeño seguro** que uno grande con riesgos

### Trabajo Pendiente para Lotes Futuros

Para poder migrar `save_server_query()` y `delete_server_query()`:

1. **Implementar `update_server_query()` en `server_registry.py`**
2. **Validar formato JSON en EDARSAHUB**
3. **Sincronizar queries existentes MongoDB → EDARSAHUB**
4. **Crear lote específico de escrituras** (Lote 7 o separado)

---

**Documento generado por Agente E1 — EDARSA HUB**  
**Fecha:** 2025-12-19  
**Estado:** PENDIENTE APROBACIÓN USUARIO
