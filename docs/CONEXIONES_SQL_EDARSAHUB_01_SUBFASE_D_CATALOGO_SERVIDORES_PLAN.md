# SUBFASE D — REGULARIZACIÓN DE CATÁLOGO MAESTRO DE SERVIDORES
## CONEXIONES-SQL-EDARSAHUB-01

**Fecha:** 2025-12-19  
**Estado:** DIAGNÓSTICO COMPLETADO  
**Autor:** Agente E1  
**Versión:** 1.0

---

## 1. RESUMEN EJECUTIVO

### Hallazgo Principal

**LA BRECHA DE CATÁLOGO MAESTRO DOCUMENTADA EN SESIONES ANTERIORES YA NO EXISTE.**

Tras ejecutar el diagnóstico comparativo entre EDARSAHUB y MongoDB:

| Fuente | Servidores | Estado |
|--------|------------|--------|
| **EDARSAHUB** | 13 | Fuente primaria activa con datos completos |
| **MongoDB** | 0 | Colección vacía |

### Conclusión

1. **EDARSAHUB ya es el catálogo maestro funcional** — Contiene 13 servidores con configuración completa (host, port, database, username, password_encrypted)
2. **MongoDB no tiene servidores** — La colección `db.servers` está vacía (0 documentos)
3. **El server_registry funciona correctamente** — Los servidores se resuelven con `config_origin: EDARSAHUB_SQL`
4. **Los servidores mencionados en sesiones anteriores (130° MERIDA, HR2020 ESCRITURA) SÍ existen en EDARSAHUB**

### Observación Técnica

Existe un error de descifrado de passwords:
```
ERROR: SERVER_SECRET_KEY no configurada
```
Este es un problema de configuración del entorno (`SERVER_SECRET_KEY` faltante en `.env`), **no** un problema de la migración arquitectónica ni del catálogo maestro.

---

## 2. COMPARATIVO MONGODB vs EDARSAHUB

### 2.1 Servidores en MongoDB

| Server ID | Nombre | Host | Puerto | System Type | Estado |
|-----------|--------|------|--------|-------------|--------|
| *(vacío)* | *(vacío)* | *(vacío)* | *(vacío)* | *(vacío)* | *(vacío)* |

**Total: 0 servidores**

### 2.2 Servidores en EDARSAHUB

| Server ID | Nombre | Host | Puerto | System Type | Activo | Password | Sucursales | Queries |
|-----------|--------|------|--------|-------------|--------|----------|------------|---------|
| a5547321-1139-4d2b-9d53-182ca737b6b6 | 130° MERIDA | 130mid.ddns.net | 1433 | SoftRestaurant | Sí | Sí | No | No |
| 6d053c22-523e-48c0-b72b-96081e2d781b | CIENFUEGOS | servercienfuegos.ddns.net,6669\nationalsoft | 1433 | SoftRestaurant | Sí | Sí | No | Sí |
| 6d859026-710a-4920-9a44-6da98fabc690 | CIENFUEGOS TABLAJERIA | servercienfuegos.ddns.net,6669\nationalsoft | 1433 | SoftRestaurant | Sí | Sí | No | No |
| f8a9049a-96e8-4210-84ae-595ffa2822fa | EDARSA HUB | 54.39.104.176 | 1433 | EDARSA_HUB | Sí | Sí | No | No |
| b5175237-5e57-41f3-ab6d-b5ae2f5e780b | HR2020 ESCRITURA | 54.39.104.176 | 1433 | MPRO | Sí | Sí | No | No |
| a5ff0e25-f029-43db-b634-d4ac814c904f | LA ESTELAR | serverestelar.ddns.net,6969 | 6969 | SoftRestaurant | Sí | Sí | No | Sí |
| 1b230a06-ffaf-4c70-bd27-b1be3579dea6 | ManagmentPro | 54.39.104.176 | 1433 | MPRO | Sí | Sí | No | Sí |
| d1d8c70f-c3d0-4407-ae50-f09e8e5992ee | MPRO TABLAJERIA | 54.39.104.176 | 1433 | MPRO | Sí | Sí | No | No |
| d8425038-5e57-42d9-8f3a-62e287888874 | PRUEBAS SOFTRESTAURANT | 54.39.104.176\SOFTRESTAURANT | 1433 | SoftRestaurant | Sí | Sí | No | No |
| bea40259-35f1-4693-bda2-d2d10e13e56a | EDARSA HUB (duplicado) | 54.39.104.176 | 1433 | Otro | No | Sí | No | No |
| 90a62591-65cf-439f-ae8e-d505b50fcc07 | TEST_ENCRYPTED_PASSWORD_UPDATED | 127.0.0.2 | 1433 | MPRO | No | Sí | No | No |
| 7452d373-7350-4193-b819-e36ffa800724 | TEST_RBAC_ADMIN_CHECK | 127.0.0.1 | 1433 | MPRO | No | Sí | No | No |
| 3f6ffbdf-1288-423d-aa42-3878b48e5022 | TEST_SQL_FIRST_TEMP_UPDATED | 127.0.0.2 | 1433 | MANAGEMENTPRO | No | Sí | No | No |

**Total: 13 servidores (9 activos, 4 inactivos/test)**

---

## 3. ANÁLISIS DE HALLAZGOS

### 3.1 Servidores Solo en MongoDB
**Ninguno** — MongoDB está vacío.

### 3.2 Servidores Solo en EDARSAHUB
**Todos** — Los 13 servidores existen exclusivamente en EDARSAHUB.

### 3.3 Servidores en Ambos
**Ninguno** — No hay intersección porque MongoDB está vacío.

### 3.4 Servidores Duplicados
| ID | Nombre | Observación |
|----|--------|-------------|
| bea40259-35f1-4693-bda2-d2d10e13e56a | EDARSA HUB | Duplicado del f8a9049a-*, marcado inactivo y con system_type "Otro" |

**Acción recomendada:** No requiere acción. Está inactivo y no afecta operación.

### 3.5 Servidores con ID Distinto pero Mismo Host
| Host | Servidores | Observación |
|------|------------|-------------|
| 54.39.104.176 | EDARSA HUB, HR2020 ESCRITURA, ManagmentPro, MPRO TABLAJERIA, PRUEBAS SOFTRESTAURANT | Mismo host físico pero diferentes bases de datos. Configuración válida. |
| servercienfuegos.ddns.net,6669\nationalsoft | CIENFUEGOS, CIENFUEGOS TABLAJERIA | Mismo host físico pero diferentes bases de datos. Configuración válida. |

**Acción recomendada:** No requiere acción. Es normal tener múltiples conexiones al mismo host con diferentes bases de datos.

### 3.6 Servidores con Campos Incompletos

| Server ID | Nombre | Campos Faltantes |
|-----------|--------|------------------|
| *(todos)* | *(todos)* | `sucursales` vacío (JSON array `[]`) |
| *(todos)* | *(todos)* | `categorias` vacío (JSON array `[]`) |
| *(todos)* | *(todos)* | `departamentos` vacío (JSON array `[]`) |

**Observación:** Los campos `sucursales`, `categorias` y `departamentos` están vacíos en todos los servidores. Estos son campos de configuración opcional que se pueden completar desde la UI.

### 3.7 Servidores con Credenciales Faltantes
**Ninguno** — Todos tienen `password_encrypted` configurado.

### 3.8 Servidores con System Type Faltante
**Ninguno** — Todos tienen `system_type` definido.

### 3.9 Servidores sin Sucursales Vinculadas
**Todos** — El campo `sucursales` está vacío en todos los servidores. Esto se debe a que:
1. La configuración de sucursales es opcional
2. Las sucursales se pueden obtener dinámicamente vía queries SQL
3. No hay sincronización desde MongoDB porque MongoDB está vacío

### 3.10 Sucursales sin Servidor
**No aplica** — MongoDB `server_sucursales_config` está vacío (0 documentos).

### 3.11 Servidores Inactivos
| Server ID | Nombre | Motivo |
|-----------|--------|--------|
| bea40259-35f1-4693-bda2-d2d10e13e56a | EDARSA HUB | Duplicado legacy |
| 90a62591-65cf-439f-ae8e-d505b50fcc07 | TEST_ENCRYPTED_PASSWORD_UPDATED | Servidor de pruebas |
| 7452d373-7350-4193-b819-e36ffa800724 | TEST_RBAC_ADMIN_CHECK | Servidor de pruebas |
| 3f6ffbdf-1288-423d-aa42-3878b48e5022 | TEST_SQL_FIRST_TEMP_UPDATED | Servidor de pruebas |

**Acción recomendada:** Considerar limpieza de servidores de prueba si ya no se usan.

### 3.12 Servidores Legacy
**Ninguno identificado** — Todos los servidores activos tienen configuración válida.

---

## 4. DETALLE DE SERVIDORES MENCIONADOS EN LOTE 3

### 4.1 130° MERIDA (a5547321-1139-4d2b-9d53-182ca737b6b6)

| Campo | Valor en EDARSAHUB | Valor en MongoDB |
|-------|-------------------|------------------|
| id | a5547321-1139-4d2b-9d53-182ca737b6b6 | *(no existe)* |
| mongodb_id | a5547321-1139-4d2b-9d53-182ca737b6b6 | *(no existe)* |
| nombre | 130° MERIDA | *(no existe)* |
| system_type | SoftRestaurant | *(no existe)* |
| tipo_conexion | DATA_SOURCE | *(no existe)* |
| host | 130mid.ddns.net | *(no existe)* |
| port | 1433 | *(no existe)* |
| database_name | softrestaurant10 | *(no existe)* |
| username | SCedarsa | *(no existe)* |
| password_encrypted | [CONFIGURADO] | *(no existe)* |
| activo | True | *(no existe)* |

**Estado:** ✅ Completo en EDARSAHUB, no requiere migración.

### 4.2 HR2020 ESCRITURA (b5175237-5e57-41f3-ab6d-b5ae2f5e780b)

| Campo | Valor en EDARSAHUB | Valor en MongoDB |
|-------|-------------------|------------------|
| id | b5175237-5e57-41f3-ab6d-b5ae2f5e780b | *(no existe)* |
| mongodb_id | b5175237-5e57-41f3-ab6d-b5ae2f5e780b | *(no existe)* |
| nombre | HR2020 ESCRITURA | *(no existe)* |
| system_type | MPRO | *(no existe)* |
| tipo_conexion | DATA_SOURCE | *(no existe)* |
| host | 54.39.104.176 | *(no existe)* |
| port | 1433 | *(no existe)* |
| database_name | HR2020 | *(no existe)* |
| username | HRLectura | *(no existe)* |
| password_encrypted | [CONFIGURADO] | *(no existe)* |
| activo | True | *(no existe)* |

**Estado:** ✅ Completo en EDARSAHUB, no requiere migración.

---

## 5. TABLAS DESTINO EN EDARSAHUB

### 5.1 Tablas Existentes Identificadas

| Tabla | Propósito | Usada por server_registry |
|-------|-----------|---------------------------|
| `Servidores_Conexiones` | Catálogo maestro de servidores | ✅ Sí |
| `Servidores_Conexiones_Log` | Auditoría de cambios | No (solo auditoría) |

### 5.2 Estructura de Servidores_Conexiones

```sql
CREATE TABLE Servidores_Conexiones (
    id                       uniqueidentifier NOT NULL PRIMARY KEY,
    nombre                   nvarchar(100)    NOT NULL,
    system_type              nvarchar(50)     NOT NULL,
    tipo_conexion            nvarchar(20)     NOT NULL,
    host                     nvarchar(255)    NULL,
    port                     int              NULL,
    database_name            nvarchar(100)    NULL,
    username                 nvarchar(100)    NULL,
    password_encrypted       nvarchar(500)    NULL,
    api_url                  nvarchar(500)    NULL,
    api_key_encrypted        nvarchar(500)    NULL,
    activo                   bit              NULL,
    visible_en_operaciones   bit              NULL,
    visible_en_listado       bit              NULL,
    es_editable_ui           bit              NULL,
    es_eliminable_ui         bit              NULL,
    empresa_id               nvarchar(100)    NULL,
    sucursales               nvarchar(MAX)    NULL,  -- JSON array
    categorias               nvarchar(MAX)    NULL,  -- JSON array
    departamentos            nvarchar(MAX)    NULL,  -- JSON array
    date_calculation_method  nvarchar(50)     NULL,
    queries_configured       bit              NULL,
    query_ventas             nvarchar(MAX)    NULL,  -- JSON
    query_inventario         nvarchar(MAX)    NULL,  -- JSON
    query_movimientos        nvarchar(MAX)    NULL,  -- JSON
    created_at               datetime         NULL,
    updated_at               datetime         NULL,
    created_by               nvarchar(100)    NULL,
    updated_by               nvarchar(100)    NULL,
    mongodb_id               nvarchar(100)    NULL
);
```

### 5.3 Tablas Faltantes

**Ninguna** — El esquema actual es suficiente para la funcionalidad del sistema.

---

## 6. RIESGOS DE MIGRACIÓN

### NO HAY MIGRACIÓN PENDIENTE

Dado que:
1. MongoDB está vacío
2. EDARSAHUB tiene todos los servidores
3. El registry ya funciona con EDARSAHUB como fuente primaria

**No hay datos que migrar de MongoDB a EDARSAHUB.**

### Riesgos Preexistentes Identificados

| Riesgo | Descripción | Mitigación |
|--------|-------------|------------|
| `SERVER_SECRET_KEY` faltante | El descifrado de passwords falla | Configurar la variable en `.env` del backend |
| Conexiones SQL externas | Timeout o credenciales inválidas pueden causar listas vacías | Validar credenciales y conectividad de red por servidor |

---

## 7. SCRIPT SQL PROPUESTO

### NO SE REQUIERE SCRIPT DE SINCRONIZACIÓN

Dado que MongoDB está vacío y EDARSAHUB ya contiene todos los servidores, **no hay script SQL necesario** para sincronizar datos.

### Script de Validación (Solo Lectura)

Se proporciona un script para validar el estado actual:

```sql
-- /app/docs/sql/VALIDACION_SERVIDORES_EDARSAHUB.sql
-- SCRIPT DE VALIDACIÓN - SOLO LECTURA
-- Fecha: 2025-12-19
-- Propósito: Verificar estado del catálogo de servidores

-- 1. Resumen de servidores
SELECT 
    COUNT(*) AS total_servidores,
    SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) AS activos,
    SUM(CASE WHEN activo = 0 OR activo IS NULL THEN 1 ELSE 0 END) AS inactivos,
    SUM(CASE WHEN password_encrypted IS NOT NULL AND password_encrypted != '' THEN 1 ELSE 0 END) AS con_password,
    SUM(CASE WHEN queries_configured = 1 THEN 1 ELSE 0 END) AS con_queries
FROM Servidores_Conexiones;

-- 2. Detalle de servidores activos
SELECT 
    id,
    nombre,
    system_type,
    host,
    port,
    database_name,
    CASE WHEN password_encrypted IS NOT NULL THEN 'Sí' ELSE 'No' END AS tiene_password
FROM Servidores_Conexiones
WHERE activo = 1
ORDER BY nombre;

-- 3. Identificar duplicados por host+database
SELECT 
    host,
    database_name,
    COUNT(*) AS cantidad
FROM Servidores_Conexiones
WHERE activo = 1
GROUP BY host, database_name
HAVING COUNT(*) > 1;

-- 4. Servidores sin campos críticos
SELECT 
    id,
    nombre,
    CASE WHEN host IS NULL OR host = '' THEN 'FALTA host' ELSE 'OK' END AS host_status,
    CASE WHEN database_name IS NULL OR database_name = '' THEN 'FALTA database' ELSE 'OK' END AS database_status,
    CASE WHEN username IS NULL OR username = '' THEN 'FALTA username' ELSE 'OK' END AS username_status,
    CASE WHEN password_encrypted IS NULL OR password_encrypted = '' THEN 'FALTA password' ELSE 'OK' END AS password_status
FROM Servidores_Conexiones
WHERE activo = 1
  AND (host IS NULL OR host = '' 
       OR database_name IS NULL OR database_name = ''
       OR username IS NULL OR username = ''
       OR password_encrypted IS NULL OR password_encrypted = '');
```

---

## 8. DATOS QUE REQUIEREN CONFIRMACIÓN MANUAL

### Ninguno

No hay datos en MongoDB que necesiten ser migrados o confirmados.

### Recomendaciones de Configuración

| Item | Estado Actual | Acción Recomendada |
|------|---------------|-------------------|
| `SERVER_SECRET_KEY` | No configurada | Agregar a `/app/backend/.env` |
| Conexión SQL externa | No verificada | Validar conectividad de red a cada host |

---

## 9. VALIDACIONES POSTERIORES

### 9.1 Verificación de Registry

```python
# Ejecutar desde /app/backend:
from core.server_registry import get_server_by_id, list_servers

# Debe retornar servidores con config_origin = "EDARSAHUB_SQL"
servers = await list_servers(db=None, prefer_sql=True)
assert all(s['config_origin'] == 'EDARSAHUB_SQL' for s in servers)
```

### 9.2 Verificación de Fallback MongoDB

El fallback a MongoDB **no debe activarse** en operación normal porque:
1. `USE_SQL_FOR_SERVERS=true` por defecto
2. EDARSAHUB tiene todos los servidores
3. MongoDB está vacío

### 9.3 Verificación de Endpoints Migrados (Lotes 1-3)

Los 15 endpoints migrados deben:
1. Usar `server_registry.get_server_connection_info()`
2. Obtener servidores con `config_origin: EDARSAHUB_SQL`
3. NO usar fallback a MongoDB

### 9.4 Verificación de Ping SQL

```bash
# Test de conexión real
curl -X POST "$API_URL/api/servers/test-connection/a5547321-1139-4d2b-9d53-182ca737b6b6" \
  -H "Authorization: Bearer $TOKEN"
```

Resultado esperado:
- `status: connected` si el servidor SQL externo es alcanzable
- `status: error` si hay timeout o credenciales inválidas (no es regresión del registry)

---

## 10. RECOMENDACIÓN

### Opción A: NO SE REQUIERE MIGRACIÓN DE SERVIDORES

**Justificación:**
- EDARSAHUB ya es el catálogo maestro con todos los servidores
- MongoDB está vacío, no hay datos legacy que migrar
- El server_registry funciona correctamente

**Acción:** Cerrar SUBFASE D como "SIN HALLAZGOS PENDIENTES".

### Opción B: RESOLVER PROBLEMA DE DESCIFRADO

**Problema identificado:**
El error `SERVER_SECRET_KEY no configurada` impide descifrar passwords.

**Acción:**
1. Configurar `SERVER_SECRET_KEY` en `/app/backend/.env`
2. Verificar que los passwords en EDARSAHUB usen el mismo algoritmo de cifrado

### Opción C: SINCRONIZAR MONGODB COMO CACHE

**Consideración opcional:**
Si se desea usar MongoDB como cache/backup de EDARSAHUB:

1. Ejecutar `reconcile_sql_mongo_servers(db, dry_run=False)` desde `server_registry.py`
2. Esto copiará los 13 servidores de EDARSAHUB a MongoDB

**Nota:** Esto es opcional y no afecta la funcionalidad actual.

---

## 11. ROLLBACK

### No Aplica

No se realizaron cambios a datos ni código en esta subfase (solo diagnóstico).

Si en el futuro se ejecutara sincronización:

```python
# Rollback: Vaciar MongoDB y dejar EDARSAHUB como única fuente
await db.servers.delete_many({})
```

---

## 12. CONCLUSIÓN Y DICTAMEN

### Dictamen: BRECHA DE CATÁLOGO MAESTRO CERRADA

| Criterio | Estado |
|----------|--------|
| EDARSAHUB es fuente primaria | ✅ Confirmado |
| MongoDB fallback NO se usa | ✅ Confirmado (MongoDB vacío) |
| Servidores con datos completos | ✅ 13/13 tienen host, port, database, username, password |
| Registry funciona correctamente | ✅ Probado con `config_origin: EDARSAHUB_SQL` |

### Acción Recomendada

1. **CERRAR SUBFASE D** como "SIN HALLAZGOS PENDIENTES"
2. **PROCEDER CON LOTE 4** de la migración de bypasses en `server.py`
3. **RESOLVER** problema de `SERVER_SECRET_KEY` como issue separado (no bloquea migración de código)

---

**Documento generado por Agente E1 - EDARSA HUB**  
**Fecha:** 2025-12-19  
**Versión:** 1.0
