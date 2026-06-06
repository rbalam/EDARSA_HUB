# INCIDENTE CRÍTICO: VENTAS DEL DÍA - DOBLE RUTA / FECHAOPERACION / ANTI-CERO

**Fecha Inicio**: 2026-05-19  
**Última Actualización**: 2026-05-20 03:20 UTC  
**Estado**: P0C - INVESTIGANDO EJECUTOR B EXTERNO  
**Severidad**: CRÍTICA  

---

## RESUMEN EJECUTIVO

Se ha identificado un **EJECUTOR B** que escribe datos con `FechaOperacion` incorrecta a la tabla `Comercial_Ventas_Dia_Abiertas_v2` sin generar logs en el backend. 

### Evidencia del Ejecutor B

| Característica | Ejecutor A (Oficial) | Ejecutor B (No Trazable) |
|----------------|---------------------|--------------------------|
| Duración | ~4 minutos | ~1 segundo |
| Genera logs | ✅ SÍ | ❌ NO |
| FechaOperacion | 2026-05-19 (CORRECTA) | 2026-05-20 (INCORRECTA) |
| Pasa por `upsert_ventas_dia_abiertas` | ✅ SÍ | ❌ NO (no activa barrera P0C) |
| PID en logs | Visible | NO visible |

### Hallazgo Crítico

El Ejecutor B **NO PASA POR EL CÓDIGO PYTHON DEL BACKEND**. La barrera P0C implementada en `repository_comercial_edarsahub.py` NO fue activada, lo que significa que las escrituras del Ejecutor B se hacen **DIRECTAMENTE A LA BD** sin pasar por la aplicación.

---

## TIMELINE DE RUNS (desde 02:30 UTC)

| Run ID | Inicio | Fin | Duración | En Logs? | FechaOp |
|--------|--------|-----|----------|----------|---------|
| 023110 | 02:31:11 | 02:35:22 | 4 min | ? | 2026-05-19 ✅ |
| 023200 | 02:32:01 | 02:32:02 | 1 seg | ❌ | 2026-05-20 ❌ |
| 023550 | 02:35:51 | 02:40:02 | 4 min | ✅ | 2026-05-19 ✅ |
| 023704 | 02:37:05 | 02:41:12 | 4 min | ❌ | 2026-05-20 ❌ |
| 024050 | 02:40:50 | 02:40:53 | 3 seg | ✅ | 2026-05-19 ✅ |
| 024714 | 02:47:14 | 02:47:15 | 1 seg | ❌ | 2026-05-20 ❌ |
| 025050 | 02:50:50 | 02:55:00 | 4 min | ✅ | 2026-05-19 ✅ |
| 025200 | 02:52:00 | 02:52:01 | 1 seg | ❌ | 2026-05-20 ❌ |
| 025700 | 02:57:00 | 02:57:01 | 1 seg | ❌ | 2026-05-20 ❌ |
| 030700 | 03:07:00 | 03:07:01 | 1 seg | ❌ | 2026-05-20 ❌ |
| 031200 | 03:12:00 | 03:12:02 | 2 seg | ✅ | 2026-05-19 ✅ |
| 031709 | 03:17:09 | 03:17:10 | 1 seg | ❌ | 2026-05-20 ❌ |

---

## ACCIONES EJECUTADAS

### 1. Eliminación de `--reload` de supervisor ✅
- **Estado**: Completado
- **Resultado**: Ya no hay procesos duplicados por hot-reload

### 2. Barrera P0C en `upsert_ventas_dia_abiertas` ✅
- **Estado**: Implementada
- **Resultado**: NO fue activada por Ejecutor B (no pasa por este código)

### 3. Reducción de `misfire_grace_time` a 1 segundo ✅
- **Estado**: Implementado
- **Resultado**: NO resolvió el problema

---

## HIPÓTESIS SOBRE EJECUTOR B

### Descartadas:
1. ~~Proceso zombie del backend~~ (solo hay 1 proceso uvicorn)
2. ~~APScheduler misfire~~ (reducir misfire_grace_time no resolvió)
3. ~~Código Python duplicado~~ (no hay otro escritor en el código)
4. ~~Endpoint API manual~~ (no hay llamadas HTTP)

### Hipótesis Activa:
**SQL SERVER AGENT JOB** o proceso externo escribiendo directamente a EDARSAHUB

Evidencia:
- No genera logs en el backend
- No activa la barrera P0C
- Ejecuta en ~1 segundo (demasiado rápido para conectar a 5 orígenes)
- Escribe a `Comercial_SyncLog_v2` con run_id pero NO aparece en logs Python

---

## PRÓXIMOS PASOS REQUERIDOS

1. **VERIFICAR CON DBA/ADMIN DE BD** si existe un SQL Server Agent Job que escriba a:
   - `Comercial_Ventas_Dia_Abiertas_v2`
   - `Comercial_SyncLog_v2`

2. **CONSULTAR LOGS DE SQL SERVER** (requiere acceso administrativo):
   ```sql
   -- Ver actividad reciente en la tabla
   SELECT * FROM sys.fn_dblog(NULL, NULL)
   WHERE AllocUnitName LIKE '%Comercial_Ventas_Dia_Abiertas_v2%'
   ```

3. **VERIFICAR TRIGGERS** en la tabla que puedan estar ejecutando código:
   ```sql
   SELECT name, type_desc FROM sys.triggers
   WHERE parent_id = OBJECT_ID('Comercial_Ventas_Dia_Abiertas_v2')
   ```

4. **DESHABILITAR TEMPORALMENTE** el Ejecutor B (si se identifica)

---

## ESTADO ACTUAL

| Componente | Estado |
|------------|--------|
| Backend sin `--reload` | ✅ |
| Barrera P0C | ✅ (pero no activada) |
| Ejecutor A (oficial) | ✅ Funcionando correctamente |
| Ejecutor B (externo) | ❌ **SIGUE ACTIVO** |
| Datos en BD | ❌ Corruptos (fecha incorrecta) |
| Endpoint `/api/v2/comercial/ventas-dia` | Lee de EDARSAHUB |

---

## INVESTIGACIÓN P0D - EJECUTOR EXTERNO (2026-05-20 03:40 UTC)

### Login SQL y Permisos Actuales

- **Login SQL**: `<REDACTED_EDARSAHUB_SQL_USER>`
- **Usuario BD**: `<REDACTED_EDARSAHUB_SQL_USER>`
- **Base de datos**: `EDARSAHUB`

### Permisos Disponibles vs Denegados

| Consulta | Estado |
|----------|--------|
| sys.triggers | ✅ Acceso |
| sys.sql_modules | ✅ Acceso |
| sys.database_permissions | ✅ Acceso |
| msdb.dbo.sysjobs | ❌ DENEGADO |
| sys.dm_exec_sessions | ❌ DENEGADO |

### Error Exacto para msdb

```
(229, b"The SELECT permission was denied on the object 'sysjobs', 
database 'msdb', schema 'dbo'.")
```

### Permisos Mínimos Requeridos para DBA

```sql
USE msdb;
GRANT SELECT ON dbo.sysjobs TO <REDACTED_EDARSAHUB_SQL_USER>;
GRANT SELECT ON dbo.sysjobsteps TO <REDACTED_EDARSAHUB_SQL_USER>;
GRANT SELECT ON dbo.sysjobhistory TO <REDACTED_EDARSAHUB_SQL_USER>;
GRANT VIEW SERVER PERFORMANCE STATE TO <REDACTED_EDARSAHUB_SQL_USER>;
```

### Resultados de Consultas Diagnósticas

| Consulta | Resultado |
|----------|-----------|
| Triggers en tablas | **NO HAY** |
| Stored procedures | **NO HAY** |
| Permisos explícitos | **NO HAY** (heredan de roles) |
| SQL Server Agent Jobs | **NO SE PUEDE CONSULTAR** |
| Sesiones activas | **NO SE PUEDE CONSULTAR** |

### Timeline Ejecutor B (desde 03:00 UTC)

| Run ID | Hora | FechaOp |
|--------|------|---------|
| 030206-161b | 03:02:06 | 2026-05-20 ❌ |
| 030700-7696 | 03:07:00 | 2026-05-20 ❌ |
| 031200-c219 | 03:12:00 | 2026-05-20 ❌ |
| 031709-f7f1 | 03:17:09 | 2026-05-20 ❌ |
| 032200-edfc | 03:22:00 | 2026-05-20 ❌ |
| 032700-1a29 | 03:27:00 | 2026-05-20 ❌ |
| 033209-bde2 | 03:32:09 | 2026-05-20 ❌ |

### Conclusión Técnica

El **Ejecutor B NO está en el código Python**:
1. No genera logs
2. No activa barrera P0C
3. Solo hay 1 proceso backend
4. No hay triggers ni SP
5. Run_ids NO pasan por `execute_sync_comercial_abiertas_v2`

**HIPÓTESIS**: Existe un **SQL Server Agent Job** en EDARSAHUB.

### Acción Requerida del DBA

```sql
-- Ver jobs activos
SELECT j.job_id, j.name, j.enabled
FROM msdb.dbo.sysjobs j WHERE j.enabled = 1;

-- Ver steps que mencionen las tablas
SELECT j.name, s.step_id, s.command
FROM msdb.dbo.sysjobs j
INNER JOIN msdb.dbo.sysjobsteps s ON j.job_id = s.job_id
WHERE s.command LIKE '%Comercial_Ventas_Dia_Abiertas_v2%'
   OR s.command LIKE '%ABIERTA-%';
```

---

## VALIDACIÓN DE CONEXIÓN EDARSAHUB (2026-05-20 03:55 UTC)

### Conexión Usada (del Menú de Servidores)

| Campo | Valor |
|-------|-------|
| servidor_conexion_id | `f8a9049a-96e8-4210-84ae-595ffa2822fa` |
| nombre | EDARSA HUB |
| host | <REDACTED_EDARSAHUB_SQL_HOST> |
| port | 1433 |
| database_name | EDARSAHUB |
| username | <REDACTED_EDARSAHUB_SQL_USER> |
| system_type | EDARSA_HUB |
| tipo_conexion | CORE |

### Identidad SQL Real

```
SYSTEM_USER: <REDACTED_EDARSAHUB_SQL_USER>
SUSER_SNAME(): <REDACTED_EDARSAHUB_SQL_USER>
ORIGINAL_LOGIN(): <REDACTED_EDARSAHUB_SQL_USER>
CURRENT_USER: <REDACTED_EDARSAHUB_SQL_USER>
DB_NAME(): EDARSAHUB
@@SERVERNAME: ns559627
```

### Permisos en EDARSAHUB

| Permiso | Valor |
|---------|-------|
| is_db_owner | **1** (TRUE) |
| is_db_datareader | **1** (TRUE) |
| is_db_datawriter | **1** (TRUE) |

### Acceso a msdb

**DENEGADO**

```
Error: (229, b"The SELECT permission was denied on the object 'sysjobs', 
database 'msdb', schema 'dbo'.")
```

**EXPLICACIÓN**: El login `<REDACTED_EDARSAHUB_SQL_USER>` es `db_owner` en EDARSAHUB pero **NO tiene permisos en msdb**. Solo existen 2 logins en el servidor: `<REDACTED_EDARSAHUB_SQL_USER>` y `sa`.

### Timeline de Runs Confirmado (03:33-03:52 UTC)

| Run ID | Hora | FechaOp | En Logs? | Tipo |
|--------|------|---------|----------|------|
| 033300-f96d | 03:33-03:37 | 2026-05-19 ✅ | ✅ SÍ | Ejecutor A (backend, pid=5861) |
| 034200-c406 | 03:42:00-01 | 2026-05-20 ❌ | ❌ NO | **Ejecutor B** |
| 034800-d7a3 | 03:48:01 | 2026-05-19 ✅ | ✅ SÍ | Ejecutor A (backend, pid=5861) |
| 035115-5e56 | 03:51:16-17 | 2026-05-20 ❌ | ❌ NO | **Ejecutor B** |

### Conclusión Técnica

1. ✅ Se usó la conexión EDARSAHUB del menú de servidores
2. ✅ El login real es `<REDACTED_EDARSAHUB_SQL_USER>`
3. ✅ <REDACTED_EDARSAHUB_SQL_USER> es db_owner en EDARSAHUB
4. ❌ <REDACTED_EDARSAHUB_SQL_USER> NO tiene permisos en msdb
5. ❌ El Ejecutor B sigue activo (no se puede identificar sin acceso a msdb)

### Permisos Requeridos para Continuar

El DBA/Admin debe ejecutar con `sa` u otro login con permisos:

```sql
-- Opción 1: Otorgar permisos a <REDACTED_EDARSAHUB_SQL_USER>
USE msdb;
GRANT SELECT ON dbo.sysjobs TO <REDACTED_EDARSAHUB_SQL_USER>;
GRANT SELECT ON dbo.sysjobsteps TO <REDACTED_EDARSAHUB_SQL_USER>;
GRANT SELECT ON dbo.sysjobhistory TO <REDACTED_EDARSAHUB_SQL_USER>;
GRANT SELECT ON dbo.sysschedules TO <REDACTED_EDARSAHUB_SQL_USER>;
GRANT SELECT ON dbo.sysjobschedules TO <REDACTED_EDARSAHUB_SQL_USER>;

-- Opción 2: Ejecutar las consultas de diagnóstico directamente
-- Ver archivo: /app/docs/reports/CONSULTAS_DBA_EJECUTOR_EXTERNO_P0D.md
```

---

## ESTADO ACTUAL DE BD (03:55 UTC)

| Unidad | FechaOp | Total | RunID | Estado |
|--------|---------|-------|-------|--------|
| 130MID | 2026-05-20 | $92,167 | 035115-5e56 | ❌ INCORRECTO |
| ORIGEN | 2026-05-20 | $17,563 | 035115-5e56 | ❌ INCORRECTO |
| 130QRO | 2026-05-20 | $0 | 035115-5e56 | ❌ INCORRECTO |
| ESTELAR | 2026-05-20 | $8,955 | 035115-5e56 | ❌ INCORRECTO |
| CIENFUEGOS | 2026-05-20 | $0 | 035115-5e56 | ❌ INCORRECTO |

**IMPACTO**: 100% de registros con fecha incorrecta debido al Ejecutor B.

**Documento de consultas para DBA**: `/app/docs/reports/CONSULTAS_DBA_EJECUTOR_EXTERNO_P0D.md`

---

## ACCESO DBA TEMPORAL / CONEXIÓN SUPERADMINISTRADOR

### Fecha: 2025-12-19

### 1. Opción Implementada
**Opción B**: Formulario visual seguro en el panel de Administración

### 2. Validación de Identidad SQL
- **SYSTEM_USER**: <REDACTED_EDARSAHUB_SQL_USER>
- **ORIGINAL_LOGIN()**: <REDACTED_EDARSAHUB_SQL_USER>  
- **@@SERVERNAME**: ns559627
- **Base de datos**: EDARSAHUB

### 3. Validación de Permisos
| Base de Datos | Usuario | Acceso |
|---------------|---------|--------|
| EDARSAHUB | <REDACTED_EDARSAHUB_SQL_USER> | ✅ FULL ACCESS (db_owner) |
| msdb | guest | ❌ Sin acceso a SQL Agent |

### 4. Solución Implementada
Se creó un endpoint seguro y formulario frontend para registrar credencial SA:

**Backend**: `/app/backend/api/dba_credential_p0d.py`
- Endpoints protegidos solo para SuperAdministrador
- Cifrado inmediato con Fernet (SERVER_SECRET_KEY)
- Almacenamiento temporal en memoria
- Sin exposición en logs

**Frontend**: `/app/frontend/src/pages/DBACredentialManager.jsx`
- Accesible en: `/admin/dba-credential`
- Campo tipo password (nunca muestra valor)
- Solo visible para rol SuperAdministrador
- Menú: Sistema → DBA Diagnóstico

### 5. Evidencia de No Exposición de Contraseña
- La contraseña NO se almacena en texto plano
- La contraseña NO se imprime en logs
- La contraseña NO se devuelve en endpoints
- La contraseña NO se muestra en frontend
- La contraseña se cifra INMEDIATAMENTE con Fernet

### 6. Usuario Autorizado
- **Email**: ricardo@edarsa.com.mx
- **Rol**: SuperAdministrador

### 7. Auditoría Implementada
Cada acción registra:
- timestamp
- user_id
- user_email
- action
- status
- details (SIN contraseña)

### 8. Endpoints Disponibles
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /api/admin/dba-credential/status | Estado del sistema |
| POST | /api/admin/dba-credential/register | Registrar credencial (cifrada) |
| GET | /api/admin/dba-credential/test-connection | Probar conexión a msdb |
| POST | /api/admin/dba-credential/execute-diagnostic | Ejecutar diagnóstico |
| DELETE | /api/admin/dba-credential/clear | Eliminar credencial de memoria |

### 9. Consultas que se Ejecutarán
Al presionar "Ejecutar Diagnóstico", se ejecutan automáticamente:
- Jobs activos en SQL Server Agent
- Steps que mencionan tablas afectadas (Comercial_Ventas_Dia_Abiertas_v2, etc.)
- Schedules cada 5-10 minutos
- Historial de ejecuciones de hoy

### 10. Jobs Encontrados
**PENDIENTE**: Esperando que el usuario registre la credencial SA

### 11. Job Sospechoso
**PENDIENTE**: Se identificará tras ejecutar el diagnóstico

### 12. Recomendación de Acción Posterior
**PENDIENTE**: Se determinará tras identificar el Ejecutor B

### 13. Plan de Rollback
1. Eliminar credencial de memoria: `DELETE /api/admin/dba-credential/clear`
2. Revocar permisos si se otorgaron a <REDACTED_EDARSAHUB_SQL_USER>
3. Documentar cualquier cambio realizado

---

*Documento generado como parte del protocolo de "Autorización Controlada"*
*Actualización: 2025-12-19*
