# DIAGNÓSTICO P0D - SQL SERVER AGENT COMPLETADO

**Fecha**: 2025-12-19  
**Ejecutado por**: <REDACTED_EDARSAHUB_SQL_USER>  
**Servidor**: ns559627 (<REDACTED_EDARSAHUB_SQL_HOST>)

---

## RESUMEN EJECUTIVO

### CONCLUSIÓN: EL EJECUTOR B NO ES UN SQL SERVER AGENT JOB

Después de un diagnóstico exhaustivo con acceso completo a SQL Server Agent, se confirma que:

| Verificación | Resultado |
|--------------|-----------|
| Jobs activos en SQL Server Agent | 1 (solo `syspolicy_purge_history`) |
| Jobs que escriben en tablas afectadas | 0 |
| Jobs cada 5-10 minutos | 0 |
| Stored Procedures que mencionan tablas | 0 |
| Triggers en tablas afectadas | 0 |
| Usuarios con permisos de escritura | 1 (<REDACTED_EDARSAHUB_SQL_USER> con db_owner) |

---

## 1. VALIDACIÓN DE IDENTIDAD

```
SYSTEM_USER:      <REDACTED_EDARSAHUB_SQL_USER> ✓
SUSER_SNAME():    <REDACTED_EDARSAHUB_SQL_USER> ✓
ORIGINAL_LOGIN(): <REDACTED_EDARSAHUB_SQL_USER> ✓
CURRENT_USER:     <REDACTED_EDARSAHUB_SQL_USER> ✓
DB_NAME():        EDARSAHUB ✓
@@SERVERNAME:     ns559627 ✓
```

## 2. VALIDACIÓN DE PERMISOS EN msdb

```
current_db_user:        <REDACTED_EDARSAHUB_SQL_USER>
is_SQLAgentReaderRole:  1 ✓
is_SQLAgentUserRole:    1 ✓
is_SQLAgentOperatorRole:1 ✓
```

## 3. JOBS EN SQL SERVER AGENT

### Total de Jobs: 1

| Job Name | Estado | Owner | Schedule |
|----------|--------|-------|----------|
| syspolicy_purge_history | ✓ ACTIVO | sa | Daily (2:00 AM) |

**Este job es un job del sistema de SQL Server** para purgar historial de políticas. NO escribe en las tablas afectadas.

## 4. JOBS CON SCHEDULE CADA 5-10 MINUTOS

**Resultado: 0 jobs**

No existe ningún job configurado para ejecutarse cada 5-10 minutos.

## 5. STEPS QUE MENCIONAN TABLAS AFECTADAS

**Resultado: 0 steps**

Ningún step de ningún job menciona:
- Comercial_Ventas_Dia_Abiertas_v2
- Comercial_SyncLog_v2
- Ventas_Dia
- FechaOperacion

## 6. OBJETOS SQL EN EDARSAHUB

| Tipo | Cantidad |
|------|----------|
| Stored Procedures que mencionan tablas | 0 |
| Triggers en tablas afectadas | 0 |
| Funciones que mencionan tablas | 0 |

## 7. USUARIOS CON PERMISOS DE ESCRITURA

Solo existe **1 usuario** con permisos de escritura en EDARSAHUB:

| Usuario | Roles |
|---------|-------|
| <REDACTED_EDARSAHUB_SQL_USER> | db_owner, db_datawriter, db_datareader, etc. |

---

## SIGUIENTE HIPÓTESIS TÉCNICA

Dado que el Ejecutor B:
1. NO es un SQL Server Agent Job
2. NO es un Stored Procedure
3. NO es un Trigger
4. Escribe usando las credenciales de <REDACTED_EDARSAHUB_SQL_USER> (único usuario con permisos)
5. Escribe cada ~5 minutos
6. No genera logs en el backend Python

### Posibles fuentes del Ejecutor B:

1. **SERVICIO EXTERNO / SCRIPT LEGACY**
   - Un servicio Windows en otro servidor
   - Un script .bat/.ps1 programado en Task Scheduler de Windows
   - Un proceso en otra máquina que conecta a EDARSAHUB

2. **OTRA INSTANCIA DEL BACKEND**
   - Un contenedor/servidor diferente ejecutando el mismo código
   - Un ambiente de staging/desarrollo apuntando a producción

3. **APLICACIÓN LEGACY**
   - Una aplicación antigua (.NET, VB, etc.) que aún está activa
   - Un proceso de sincronización legacy

### Acción Recomendada:

Para identificar el Ejecutor B, se debe:

1. **Monitorear conexiones activas** al servidor SQL cuando ocurre la escritura
2. **Revisar Task Scheduler** en el servidor Windows donde está SQL Server
3. **Buscar otros servicios** que usen las credenciales <REDACTED_EDARSAHUB_SQL_USER>
4. **Implementar auditoría SQL** (si está disponible) para capturar el hostname de origen

---

## PLAN DE ACCIÓN PROPUESTO

### Opción A: Monitorear Conexiones (Requiere permisos)
```sql
-- Capturar conexiones cuando el Ejecutor B escribe
SELECT 
    session_id,
    login_name,
    host_name,
    program_name,
    client_interface_name,
    login_time,
    last_request_start_time
FROM sys.dm_exec_sessions
WHERE login_name = '<REDACTED_EDARSAHUB_SQL_USER>'
ORDER BY last_request_start_time DESC;
```

### Opción B: Revisar Task Scheduler del Servidor Windows
- Conectar al servidor ns559627 vía RDP
- Abrir Task Scheduler
- Buscar tareas que se ejecuten cada 5 minutos

### Opción C: Habilitar Auditoría SQL (Requiere sa)
- Crear una auditoría para capturar INSERTs/UPDATEs en las tablas afectadas
- Capturar el client_hostname y program_name

---

**Estado**: DIAGNÓSTICO SQL SERVER AGENT COMPLETADO  
**Resultado**: El Ejecutor B NO es un SQL Server Agent Job  
**Siguiente paso**: Identificar proceso externo que usa credenciales <REDACTED_EDARSAHUB_SQL_USER>
