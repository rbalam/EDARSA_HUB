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

- **Login SQL**: `HRLectura`
- **Usuario BD**: `HRLectura`
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
GRANT SELECT ON dbo.sysjobs TO HRLectura;
GRANT SELECT ON dbo.sysjobsteps TO HRLectura;
GRANT SELECT ON dbo.sysjobhistory TO HRLectura;
GRANT VIEW SERVER PERFORMANCE STATE TO HRLectura;
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

*Documento generado como parte del protocolo de "Autorización Controlada"*
*Actualización: 2026-05-20 03:40 UTC*
