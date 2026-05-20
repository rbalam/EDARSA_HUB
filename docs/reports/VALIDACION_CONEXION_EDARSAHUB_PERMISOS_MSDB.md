# VALIDACIÓN CONEXIÓN EDARSAHUB - PERMISOS msdb

**Fecha**: 2025-12-19  
**Objetivo**: Validar acceso real de la conexión EDARSAHUB registrada en Servidores_Conexiones

---

## 1. CONEXIÓN REGISTRADA EN Servidores_Conexiones

| Campo | Valor |
|-------|-------|
| servidor_conexion_id | `f8a9049a-96e8-4210-84ae-595ffa2822fa` |
| nombre | EDARSA HUB |
| host | 54.39.104.176 |
| puerto | 1433 |
| database_name | EDARSAHUB |
| username | HRLectura |
| password_encrypted | enc:v1:gAA...JNA== (len=107) |
| system_type | EDARSA_HUB |
| tipo_conexion | CORE |
| activo | True |
| visible_en_listado | True |
| visible_en_operaciones | True |

**Fuente**: `SELECT * FROM EDARSAHUB.dbo.Servidores_Conexiones WHERE id = 'f8a9049a-96e8-4210-84ae-595ffa2822fa'`

---

## 2. IDENTIDAD REAL DE LA CONEXIÓN

```
SYSTEM_USER:      HRLectura
SUSER_SNAME():    HRLectura
ORIGINAL_LOGIN(): HRLectura
CURRENT_USER:     HRLectura
DB_NAME():        EDARSAHUB
@@SERVERNAME:     ns559627
```

**Conclusión**: La conexión usa correctamente el login `HRLectura` en el servidor `ns559627`.

---

## 3. PERMISOS EN EDARSAHUB

| Verificación | Resultado |
|--------------|-----------|
| USER_NAME() | HRLectura |
| IS_MEMBER('db_owner') | 1 ✅ |
| IS_MEMBER('db_datareader') | 1 ✅ |
| IS_MEMBER('db_datawriter') | 1 ✅ |

**Permisos Explícitos**: Solo `CONNECT | GRANT` (el resto heredado de `db_owner`)

**Conclusión**: `HRLectura` tiene **FULL ACCESS** en la base de datos `EDARSAHUB`.

---

## 4. PERMISOS EN msdb

| Verificación | Resultado |
|--------------|-----------|
| USER_NAME() | **guest** ⚠️ |
| IS_MEMBER('SQLAgentReaderRole') | 0 ❌ |
| IS_MEMBER('SQLAgentUserRole') | 0 ❌ |
| IS_MEMBER('SQLAgentOperatorRole') | 0 ❌ |
| IS_MEMBER('db_datareader') | 0 ❌ |

**Conclusión**: `HRLectura` **NO tiene usuario mapeado en msdb**, entra como `guest`.

---

## 5. ERROR EXACTO AL CONSULTAR msdb.dbo.sysjobs

```
Query ejecutada:
SELECT TOP 10 job_id, name, enabled FROM dbo.sysjobs ORDER BY name;

Error:
(229, "The SELECT permission was denied on the object 'sysjobs', 
       database 'msdb', schema 'dbo'.")
```

**Código de error**: 229 (Permission denied)  
**Severidad**: 14  

---

## 6. CONCLUSIÓN: FULL ACCESS EDARSAHUB vs PERMISOS msdb

| Base de Datos | Usuario Mapeado | Nivel de Acceso |
|---------------|-----------------|-----------------|
| **EDARSAHUB** | HRLectura | ✅ FULL ACCESS (db_owner) |
| **msdb** | guest | ❌ SIN ACCESO a SQL Agent |

### Explicación Técnica

El login `HRLectura` tiene:
- **Usuario creado en EDARSAHUB**: Sí, con rol `db_owner`
- **Usuario creado en msdb**: **NO** (usa el usuario `guest` por defecto)

Esto significa:
- ✅ Puede leer/escribir cualquier tabla en EDARSAHUB
- ❌ **NO puede ver los Jobs de SQL Server Agent** (están en msdb)

Esto **NO contradice** el "full access" de EDARSAHUB. Son bases de datos independientes con mapeos de usuarios separados.

---

## 7. SIGUIENTE ACCIÓN NECESARIA

Para identificar al "Ejecutor B" que escribe datos corruptos cada 5 minutos, se requiere **una de estas dos opciones**:

### OPCIÓN A: Dar permiso temporal a HRLectura en msdb

El DBA debe ejecutar (con `sa`):

```sql
USE msdb;
GO

-- Opción simple: agregar al rol de lectura de SQL Agent
ALTER ROLE SQLAgentReaderRole ADD MEMBER HRLectura;
GO

-- O permisos explícitos mínimos:
-- GRANT SELECT ON dbo.sysjobs TO HRLectura;
-- GRANT SELECT ON dbo.sysjobsteps TO HRLectura;
-- GRANT SELECT ON dbo.sysjobhistory TO HRLectura;
-- GRANT SELECT ON dbo.sysjobschedules TO HRLectura;
-- GRANT SELECT ON dbo.sysschedules TO HRLectura;
```

### OPCIÓN B: DBA ejecuta las consultas directamente

El DBA ejecuta el archivo con `sa`:
```
/app/docs/reports/CONSULTAS_DBA_EJECUTAR_CON_SA.sql
```

Y comparte los resultados.

---

## RESUMEN EJECUTIVO

| Aspecto | Estado |
|---------|--------|
| Conexión usada | Servidores_Conexiones.id = `f8a9049a-...` |
| Login SQL | HRLectura |
| Servidor | ns559627 (54.39.104.176:1433) |
| Acceso EDARSAHUB | ✅ COMPLETO (db_owner) |
| Acceso msdb/Jobs | ❌ DENEGADO (guest) |
| Bloqueador | No podemos identificar al Ejecutor B sin permisos msdb |
| Acción requerida | DBA debe otorgar permisos o ejecutar consultas |
