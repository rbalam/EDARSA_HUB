# CONSULTAS DBA - INVESTIGACIÓN EJECUTOR EXTERNO P0D

**Fecha**: 2026-05-20  
**Incidente**: Ejecutor B escribiendo FechaOperacion incorrecta  
**Tablas Afectadas**: `Comercial_Ventas_Dia_Abiertas_v2`, `Comercial_SyncLog_v2`  
**Urgencia**: CRÍTICA  

---

## CONTEXTO PARA DBA

El backend Python de EDARSAHUB tiene un job que escribe cada 5 minutos a las tablas mencionadas. Sin embargo, se detectó un **SEGUNDO PROCESO** que también escribe a las mismas tablas con:

- **FechaOperacion incorrecta** (usa fecha UTC en lugar de fecha operativa México)
- **Duración ~1 segundo** (el oficial tarda ~4 minutos)
- **No genera logs** en el backend
- **Escribe cada ~5 minutos** en los segundos :00 o :09

**El agente actual (`<REDACTED_EDARSAHUB_SQL_USER>`) no tiene permisos para consultar msdb ni dm_exec_sessions.**

---

## CONSULTAS A EJECUTAR

### A) SQL Server Agent Jobs Activos

```sql
USE msdb;

SELECT 
    j.job_id,
    j.name,
    j.enabled,
    j.date_created,
    j.date_modified
FROM dbo.sysjobs j
WHERE j.enabled = 1
ORDER BY j.name;
```

---

### B) Job Steps que Mencionen las Tablas Afectadas

```sql
USE msdb;

SELECT
    j.job_id,
    j.name AS job_name,
    s.step_id,
    s.step_name,
    s.subsystem,
    s.database_name,
    s.command
FROM dbo.sysjobs j
INNER JOIN dbo.sysjobsteps s
    ON j.job_id = s.job_id
WHERE
    s.command LIKE '%Comercial_Ventas_Dia_Abiertas_v2%'
    OR s.command LIKE '%Comercial_SyncLog_v2%'
    OR s.command LIKE '%ventas_dia%'
    OR s.command LIKE '%Ventas_Dia%'
    OR s.command LIKE '%FechaOperacion%'
    OR s.command LIKE '%fecha_operacion%'
    OR s.command LIKE '%ABIERTA-%'
ORDER BY j.name, s.step_id;
```

---

### C) Schedules de Jobs (buscar los que corren cada 5 minutos)

```sql
USE msdb;

SELECT
    j.name AS job_name,
    j.enabled,
    sch.name AS schedule_name,
    sch.enabled AS schedule_enabled,
    sch.freq_type,
    sch.freq_subday_type,
    sch.freq_subday_interval,
    sch.active_start_time,
    sch.active_end_time
FROM dbo.sysjobs j
INNER JOIN dbo.sysjobschedules js
    ON j.job_id = js.job_id
INNER JOIN dbo.sysschedules sch
    ON js.schedule_id = sch.schedule_id
WHERE j.enabled = 1
ORDER BY j.name;
```

**Nota**: `freq_subday_interval = 5` y `freq_subday_type = 4` indica cada 5 minutos.

---

### D) Historial Reciente de Jobs

```sql
USE msdb;

SELECT TOP 200
    j.name AS job_name,
    h.step_id,
    h.step_name,
    h.run_date,
    h.run_time,
    h.run_duration,
    h.run_status,
    h.message
FROM dbo.sysjobhistory h
INNER JOIN dbo.sysjobs j
    ON h.job_id = j.job_id
WHERE h.run_date >= CONVERT(int, CONVERT(varchar, GETDATE(), 112))
ORDER BY h.instance_id DESC;
```

---

### E) Sesiones Activas en EDARSAHUB

```sql
SELECT
    s.session_id,
    s.login_name,
    s.host_name,
    s.program_name,
    s.status,
    s.last_request_start_time,
    s.last_request_end_time,
    c.client_net_address,
    r.command,
    r.status AS request_status,
    txt.text AS sql_text
FROM sys.dm_exec_sessions s
LEFT JOIN sys.dm_exec_connections c
    ON s.session_id = c.session_id
LEFT JOIN sys.dm_exec_requests r
    ON s.session_id = r.session_id
OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) txt
WHERE s.is_user_process = 1
ORDER BY s.last_request_start_time DESC;
```

---

### F) Permisos de Escritura sobre las Tablas

```sql
USE EDARSAHUB;

SELECT
    pr.name AS principal_name,
    pr.type_desc AS principal_type,
    pe.permission_name,
    pe.state_desc,
    OBJECT_SCHEMA_NAME(pe.major_id) AS schema_name,
    OBJECT_NAME(pe.major_id) AS object_name
FROM sys.database_permissions pe
INNER JOIN sys.database_principals pr
    ON pe.grantee_principal_id = pr.principal_id
WHERE pe.major_id IN (
    OBJECT_ID('Comercial_Ventas_Dia_Abiertas_v2'),
    OBJECT_ID('Comercial_SyncLog_v2')
)
ORDER BY object_name, principal_name, permission_name;
```

---

### G) Objetos SQL que Mencionen las Tablas

```sql
USE EDARSAHUB;

SELECT
    o.type_desc,
    s.name AS schema_name,
    o.name AS object_name,
    o.create_date,
    o.modify_date
FROM sys.sql_modules m
INNER JOIN sys.objects o
    ON m.object_id = o.object_id
INNER JOIN sys.schemas s
    ON o.schema_id = s.schema_id
WHERE 
    m.definition LIKE '%Comercial_Ventas_Dia_Abiertas_v2%'
    OR m.definition LIKE '%Comercial_SyncLog_v2%'
    OR m.definition LIKE '%FechaOperacion%'
    OR m.definition LIKE '%fecha_operacion%'
    OR m.definition LIKE '%ventas_dia%'
ORDER BY o.type_desc, s.name, o.name;
```

---

### H) Verificar Triggers

```sql
USE EDARSAHUB;

SELECT
    tr.name AS trigger_name,
    OBJECT_NAME(tr.parent_id) AS table_name,
    tr.is_disabled,
    tr.create_date,
    tr.modify_date
FROM sys.triggers tr
WHERE tr.parent_id IN (
    OBJECT_ID('Comercial_Ventas_Dia_Abiertas_v2'),
    OBJECT_ID('Comercial_SyncLog_v2')
)
ORDER BY table_name, trigger_name;
```

---

### I) Últimos Registros del SyncLog (para correlacionar)

```sql
USE EDARSAHUB;

SELECT TOP 100
    run_id,
    run_type,
    unidad_negocio_id,
    fecha_inicio,
    status,
    created_at
FROM Comercial_SyncLog_v2
ORDER BY created_at DESC;
```

---

## QUÉ BUSCAR

1. **SQL Server Agent Job** que escriba a `Comercial_Ventas_Dia_Abiertas_v2` o `Comercial_SyncLog_v2`
2. **Schedule cada 5 minutos** (`freq_subday_interval = 5`)
3. **Run_id con prefijo `ABIERTA-`** en el comando SQL
4. **GETDATE() o fecha UTC** en lugar de fecha operativa México
5. **Login/Owner** del job sospechoso
6. **Host/Program** diferente al backend Python

---

## ACCIÓN REQUERIDA

Si se encuentra un job externo:
1. **NO deshabilitar** sin autorización
2. Documentar: nombre, step, schedule, comando, login
3. Enviar información al equipo de desarrollo

---

*Documento generado: 2026-05-20 03:45 UTC*
