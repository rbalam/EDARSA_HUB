# FASE 3B.1 - Endpoints de Escritura SQL-First y Sincronización Legacy MongoDB

**Fecha de ejecución:** 2025-12-XX  
**Estado:** COMPLETADO

---

## 1. Resumen Ejecutivo

La FASE 3B.1 migró los endpoints de escritura de servidores (`POST`, `PUT`, `DELETE`) para que escriban primero en EDARSAHUB SQL y sincronicen MongoDB como espejo legacy.

**Resultado:**
- SQL es ahora la fuente principal para CREATE, UPDATE, DELETE
- MongoDB se actualiza como espejo después de cada operación exitosa en SQL
- Si MongoDB sync falla, se devuelve `sync_status: PARTIAL_SYNC`
- Soft delete mantiene `activo=false` en vez de borrado físico

---

## 2. Diferencia 9 vs 8 Servidores - Causa Documentada

### Tabla de Servidores

| SQL id | Nombre | system_type | tipo_conexion | activo | En /api/servers | Motivo |
|--------|--------|-------------|---------------|--------|-----------------|--------|
| a5547321... | 130° MERIDA | SoftRestaurant | DATA_SOURCE | Si | Si | DATA_SOURCE operativo |
| 6d053c22... | CIENFUEGOS | SoftRestaurant | DATA_SOURCE | Si | Si | DATA_SOURCE operativo |
| 6d859026... | CIENFUEGOS TABLAJERIA | SoftRestaurant | DATA_SOURCE | Si | Si | DATA_SOURCE operativo |
| f8a9049a... | **EDARSA HUB** | EDARSA_HUB | **CORE** | Si | **No** | **Excluido: tipo_conexion=CORE** |
| b5175237... | HR2020 ESCRITURA | MPRO | DATA_SOURCE | Si | Si | DATA_SOURCE operativo |
| a5ff0e25... | LA ESTELAR | SoftRestaurant | DATA_SOURCE | Si | Si | DATA_SOURCE operativo |
| 1b230a06... | ManagmentPro | MPRO | DATA_SOURCE | Si | Si | DATA_SOURCE operativo |
| d1d8c70f... | MPRO TABLAJERIA | MPRO | DATA_SOURCE | Si | Si | DATA_SOURCE operativo |
| d8425038... | PRUEBAS SOFTRESTAURANT | SoftRestaurant | DATA_SOURCE | Si | Si | DATA_SOURCE operativo |

**Total:** 9 servidores en SQL, 8 expuestos vía `/api/servers`

**Causa de exclusión:** El servidor "EDARSA HUB" tiene `tipo_conexion=CORE` y representa la conexión interna del sistema. Esta exclusión es **válida y necesaria** para:
- Evitar que usuarios modifiquen la conexión del cerebro del sistema
- Separar conexiones internas (CORE) de fuentes de datos externas (DATA_SOURCE)

**Endpoint administrativo futuro:** Si se requiere gestionar conexiones CORE, crear `/api/admin/core-connections` con permisos SuperAdmin exclusivos.

---

## 3. Funciones Agregadas a `server_registry.py`

| Función | Propósito |
|---------|-----------|
| `create_server(payload, db, user, sync_mongo)` | Crea servidor en SQL, sincroniza a MongoDB |
| `update_server(server_id, payload, db, user, sync_mongo)` | Actualiza en SQL, sincroniza a MongoDB |
| `delete_server(server_id, db, user, sync_mongo, soft_delete)` | Soft delete en SQL y MongoDB |
| `sync_server_to_mongo(sql_server_id, db)` | Sincroniza un servidor específico de SQL a MongoDB |
| `validate_server_payload(payload, mode)` | Valida payload antes de crear/actualizar |
| `_execute_sql_write(query, params)` | Ejecuta queries de escritura en SQL |

---

## 4. Endpoints Migrados

### POST /api/servers

**Antes:** Escribía solo a MongoDB  
**Ahora:** 
1. Valida payload con `validate_server_payload()`
2. Prueba conexión SQL Server del nuevo servidor
3. Inserta en EDARSAHUB SQL (`Servidores_Conexiones`)
4. Sincroniza a MongoDB
5. Devuelve respuesta con `config_origin`, `sync_status`

**Respuesta nueva:**
```json
{
  "id": "uuid",
  "name": "Nuevo Servidor",
  "system_type": "MPRO",
  "system_type_normalized": "MANAGEMENTPRO",
  "config_origin": "EDARSAHUB_SQL",
  "sync_status": "SYNCED",
  "warnings": [],
  "message": "Servidor creado exitosamente"
}
```

### PUT /api/servers/{server_id}

**Antes:** Actualizaba solo MongoDB  
**Ahora:**
1. Valida payload
2. Verifica existencia en SQL (también busca por `mongodb_id`)
3. Verifica protección CORE
4. Actualiza en EDARSAHUB SQL
5. Sincroniza a MongoDB
6. Si password viene enmascarado (`********`), no lo sobrescribe

**Respuesta nueva:**
```json
{
  "message": "Servidor actualizado",
  "config_origin": "EDARSAHUB_SQL",
  "sync_status": "SYNCED",
  "warnings": []
}
```

### DELETE /api/servers/{server_id}

**Antes:** Soft delete solo en MongoDB  
**Ahora:**
1. Verifica existencia en SQL
2. Verifica protección CORE
3. Soft delete en SQL (`activo=0`)
4. Sincroniza soft delete a MongoDB (`active=false`)

**Respuesta nueva:**
```json
{
  "message": "Servidor desactivado",
  "config_origin": "EDARSAHUB_SQL",
  "sync_status": "SYNCED",
  "warnings": []
}
```

---

## 5. Flujo SQL-First

```
┌─────────────────┐
│   API Request   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Validar Payload │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Escribir SQL   │────▶│    SQL OK?      │
└─────────────────┘     └────────┬────────┘
                                 │
                     ┌───────────┴───────────┐
                     │                       │
                     ▼                       ▼
              ┌────────────┐          ┌────────────┐
              │    NO      │          │    SI      │
              └─────┬──────┘          └─────┬──────┘
                    │                       │
                    ▼                       ▼
              ┌────────────┐         ┌─────────────┐
              │ Error 400  │         │ Sync MongoDB│
              └────────────┘         └──────┬──────┘
                                            │
                                 ┌──────────┴──────────┐
                                 │                     │
                                 ▼                     ▼
                          ┌────────────┐        ┌────────────┐
                          │ Mongo OK   │        │ Mongo FAIL │
                          └─────┬──────┘        └─────┬──────┘
                                │                     │
                                ▼                     ▼
                          ┌────────────┐        ┌────────────┐
                          │  SYNCED    │        │PARTIAL_SYNC│
                          └────────────┘        └────────────┘
```

---

## 6. Manejo de PARTIAL_SYNC

Si SQL escribe exitosamente pero MongoDB falla:

- **No se revierte SQL** (SQL es la fuente de verdad)
- Se devuelve `sync_status: PARTIAL_SYNC`
- Se incluye warning con detalle del error
- Se registra log `[SERVER_REGISTRY][SYNC_MONGO_ERROR]`

**Reconciliación:** Usar script de reconciliación o función `sync_server_to_mongo()` para sincronizar manualmente.

---

## 7. Manejo de Secretos

| Campo | Almacenamiento | Respuesta API |
|-------|----------------|---------------|
| password | SQL: `password_encrypted` | Nunca expuesto |
| api_key | SQL: `api_key_encrypted` | Nunca expuesto |
| password_configured | N/A | `true/false` |
| api_key_configured | N/A | `true/false` |

**Reglas:**
- Si PUT recibe password vacío o `********`, no sobrescribe el existente
- Logs nunca imprimen passwords ni api_keys
- Respuestas API nunca incluyen valores reales de secretos

---

## 8. RBAC

| Endpoint | Rol Requerido | Protección CORE |
|----------|---------------|-----------------|
| POST /api/servers | Administrador | No permite crear CORE |
| PUT /api/servers/{id} | Administrador | No permite editar CORE |
| DELETE /api/servers/{id} | Administrador | No permite eliminar CORE |

---

## 9. Validación Realizada

| Validación | Resultado |
|------------|-----------|
| `python -m compileall /app/backend` | ✅ OK |
| Backend arranca (supervisor) | ✅ RUNNING |
| Login `/api/auth/login` | ✅ OK |
| GET `/api/servers` responde | ✅ 8 servidores |
| Todos con `config_origin=EDARSAHUB_SQL` | ✅ 8/8 |
| No passwords expuestos | ✅ Confirmado |

---

## 10. Logs de Auditoría

| Log | Significado |
|-----|-------------|
| `[SERVER_REGISTRY][CREATE_SQL_START]` | Inicio de creación en SQL |
| `[SERVER_REGISTRY][CREATE_SQL_SUCCESS]` | Creación exitosa en SQL |
| `[SERVER_REGISTRY][UPDATE_SQL_START]` | Inicio de actualización en SQL |
| `[SERVER_REGISTRY][UPDATE_SQL_SUCCESS]` | Actualización exitosa en SQL |
| `[SERVER_REGISTRY][DELETE_SQL_START]` | Inicio de eliminación en SQL |
| `[SERVER_REGISTRY][DELETE_SQL_SUCCESS]` | Eliminación exitosa en SQL |
| `[SERVER_REGISTRY][SYNC_MONGO_START]` | Inicio de sync a MongoDB |
| `[SERVER_REGISTRY][SYNC_MONGO_SUCCESS]` | Sync exitoso a MongoDB |
| `[SERVER_REGISTRY][SYNC_MONGO_ERROR]` | Sync falló (PARTIAL_SYNC) |

---

## 11. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Passwords en SQL sin encriptar | MEDIO | TODO: Implementar encriptación en producción |
| Sin prueba de POST real | BAJO | Validado compilación y arranque; probar con servidor de prueba |
| PARTIAL_SYNC no tiene reconciliación automática | BAJO | Función `sync_server_to_mongo()` disponible |

---

## 12. Próximos Pasos

1. **Encriptar passwords** en SQL en producción
2. ~~**Crear script de reconciliación** `/app/backend/scripts/reconcile_servers_sql_mongo.py`~~ ✅ COMPLETADO (FASE 3B.2)
3. ~~**Probar POST/PUT/DELETE** con servidor de prueba temporal~~ ✅ COMPLETADO (FASE 3B.2)
4. **Implementar endpoint administrativo** para gestionar conexiones CORE

---

## 13. FASE 3B.2 - Validación Real

La validación funcional completa de esta fase fue ejecutada en **FASE 3B.2**.

**Ver:** [FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md](./FASE_3B2_VALIDACION_SERVERS_WRITE_SYNC.md)

**Resumen de validación:**
- ✅ POST crea SQL primero y MongoDB después
- ✅ PUT actualiza SQL primero y MongoDB después
- ✅ DELETE aplica soft delete en ambas BDs
- ✅ Protección CORE funciona
- ✅ RBAC verificado en código
- ✅ Reconciliación dry-run exitosa
- ✅ No exposición de secretos
- ✅ Backend funcional sin regresión

---

## 14. Responsable

Agente E1 - Emergent Labs  
Fase: 3B.1 - Endpoints de Escritura SQL-First
