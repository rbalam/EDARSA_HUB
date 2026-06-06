# GUÍA DE EJECUCIÓN SQL - Fase A Refresh Tokens
## EDARSAHUB: Sistema de Sesiones con Refresh Tokens

**Proyecto:** EDARSA HUB  
**Documento:** Guía de Ejecución Manual de Script SQL  
**Fase:** A - Backend Refresh Tokens (P1-REFRESH-TOKENS)  
**Fecha:** 2025-04-27  
**Estado:** PENDIENTE EJECUCIÓN

---

## 1. RUTA DEL SCRIPT SQL

```
/app/docs/sql/CREATE_SESIONES_REFRESH_TOKENS.sql
```

---

## 2. INSTRUCCIONES PASO A PASO (SQL Server Management Studio)

### 2.1 Preparación

1. **Abrir SQL Server Management Studio (SSMS)**

2. **Conectarse al servidor SQL Server**:
   - Servidor: `[Tu servidor EDARSAHUB]`
   - Autenticación: SQL Server Authentication o Windows Authentication (según configuración)
   - Credenciales: Las que tengas configuradas para EDARSAHUB

3. **Verificar permisos requeridos**:
   - `CREATE TABLE` en la base de datos EDARSAHUB
   - `CREATE INDEX` en la base de datos EDARSAHUB
   - `CREATE PROCEDURE` en la base de datos EDARSAHUB

### 2.2 Ejecución

1. **Seleccionar la base de datos EDARSAHUB**:
   ```sql
   USE EDARSAHUB;
   GO
   ```
   O seleccionar `EDARSAHUB` en el dropdown de bases de datos en SSMS.

2. **Abrir el script**:
   - File → Open → File...
   - Navegar a: `/app/docs/sql/CREATE_SESIONES_REFRESH_TOKENS.sql`
   - O copiar el contenido completo del archivo

3. **Revisar el script antes de ejecutar**:
   - Verificar que la línea `USE EDARSAHUB;` corresponde a tu base de datos
   - El script es **idempotente**: usa `IF NOT EXISTS` para cada objeto
   - No eliminará datos existentes

4. **Ejecutar el script**:
   - Presionar F5 o click en "Execute"
   - El script mostrará mensajes de progreso

5. **Verificar mensajes de salida**:
   ```
   Tabla Sesiones creada exitosamente
   Índice IX_Sesiones_TokenHash_Activo creado
   Índice IX_Sesiones_Usuario creado
   Índice IX_Sesiones_Familia creado
   Índice IX_Sesiones_Expiracion creado
   Tabla SesionesHistorico creada exitosamente
   Índice IX_SesionesHist_Usuario creado
   Índice IX_SesionesHist_Sesion creado
   Índice IX_SesionesHist_Seguridad creado
   Procedimiento sp_LimpiarSesionesExpiradas creado
   ============================================================================
   SCRIPT COMPLETADO EXITOSAMENTE
   ============================================================================
   ```

---

## 3. QUERIES DE VALIDACIÓN POST-EJECUCIÓN

Ejecutar estas queries para confirmar que todo se creó correctamente:

### 3.1 Verificar existencia de tablas

```sql
USE EDARSAHUB;
GO

-- Verificar tablas
SELECT TABLE_NAME, TABLE_TYPE 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME IN ('Sesiones', 'SesionesHistorico');
```

**Resultado esperado:**
| TABLE_NAME | TABLE_TYPE |
|------------|------------|
| Sesiones | BASE TABLE |
| SesionesHistorico | BASE TABLE |

### 3.2 Verificar columnas de tabla Sesiones

```sql
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Sesiones'
ORDER BY ORDINAL_POSITION;
```

**Resultado esperado (15 columnas):**
| COLUMN_NAME | DATA_TYPE | IS_NULLABLE |
|-------------|-----------|-------------|
| SesionID | uniqueidentifier | NO |
| UsuarioID | int | NO |
| TipoUsuario | varchar | NO |
| RefreshTokenHash | varchar | NO |
| FamiliaTokenID | uniqueidentifier | NO |
| FechaCreacion | datetime2 | NO |
| FechaExpiracion | datetime2 | NO |
| UltimaActividad | datetime2 | NO |
| EstaActiva | bit | NO |
| FechaRevocacion | datetime2 | YES |
| MotivoRevocacion | varchar | YES |
| RevocadoPorUsuarioID | int | YES |
| ReemplazadaPorSesionID | uniqueidentifier | YES |
| IPCliente | varchar | YES |
| UserAgent | varchar | YES |
| FechaModificacion | datetime2 | NO |

### 3.3 Verificar columnas de tabla SesionesHistorico

```sql
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'SesionesHistorico'
ORDER BY ORDINAL_POSITION;
```

**Resultado esperado (9 columnas):**
| COLUMN_NAME | DATA_TYPE | IS_NULLABLE |
|-------------|-----------|-------------|
| HistoricoID | bigint | NO |
| SesionID | uniqueidentifier | NO |
| UsuarioID | int | NO |
| TipoUsuario | varchar | NO |
| Accion | varchar | NO |
| FechaAccion | datetime2 | NO |
| IPCliente | varchar | YES |
| UserAgent | varchar | YES |
| DetallesJSON | nvarchar | YES |
| AccionRealizadaPor | int | YES |

### 3.4 Verificar índices

```sql
SELECT 
    i.name AS IndexName,
    t.name AS TableName,
    i.type_desc AS IndexType,
    i.is_unique AS IsUnique,
    i.has_filter AS HasFilter
FROM sys.indexes i
INNER JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name IN ('Sesiones', 'SesionesHistorico')
  AND i.name IS NOT NULL
ORDER BY t.name, i.name;
```

**Resultado esperado (8 índices + 2 PKs):**
| IndexName | TableName | IndexType | IsUnique |
|-----------|-----------|-----------|----------|
| IX_Sesiones_Expiracion | Sesiones | NONCLUSTERED | 0 |
| IX_Sesiones_Familia | Sesiones | NONCLUSTERED | 0 |
| IX_Sesiones_TokenHash_Activo | Sesiones | NONCLUSTERED | 1 |
| IX_Sesiones_Usuario | Sesiones | NONCLUSTERED | 0 |
| PK__Sesiones... | Sesiones | CLUSTERED | 1 |
| IX_SesionesHist_Seguridad | SesionesHistorico | NONCLUSTERED | 0 |
| IX_SesionesHist_Sesion | SesionesHistorico | NONCLUSTERED | 0 |
| IX_SesionesHist_Usuario | SesionesHistorico | NONCLUSTERED | 0 |
| PK__Sesiones... | SesionesHistorico | CLUSTERED | 1 |

### 3.5 Verificar procedimiento almacenado

```sql
SELECT 
    name, 
    type_desc,
    create_date,
    modify_date
FROM sys.procedures
WHERE name = 'sp_LimpiarSesionesExpiradas';
```

**Resultado esperado:**
| name | type_desc | create_date |
|------|-----------|-------------|
| sp_LimpiarSesionesExpiradas | SQL_STORED_PROCEDURE | [fecha actual] |

### 3.6 Verificar constraints (PK)

```sql
SELECT 
    tc.CONSTRAINT_NAME,
    tc.TABLE_NAME,
    tc.CONSTRAINT_TYPE,
    kcu.COLUMN_NAME
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
WHERE tc.TABLE_NAME IN ('Sesiones', 'SesionesHistorico')
  AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY';
```

**Resultado esperado:**
| CONSTRAINT_NAME | TABLE_NAME | CONSTRAINT_TYPE | COLUMN_NAME |
|-----------------|------------|-----------------|-------------|
| PK__Sesiones... | Sesiones | PRIMARY KEY | SesionID |
| PK__Sesiones... | SesionesHistorico | PRIMARY KEY | HistoricoID |

---

## 4. ROLLBACK / REVERSIÓN

### 4.1 Advertencia Importante

**NO ejecutar si hay datos productivos sin respaldo previo.**

El rollback eliminará todas las sesiones registradas y su histórico.

### 4.2 Script de Rollback

```sql
USE EDARSAHUB;
GO

-- ADVERTENCIA: Esto elimina TODOS los datos de sesiones
-- Solo ejecutar en desarrollo o si no hay datos productivos

-- Eliminar procedimiento
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_LimpiarSesionesExpiradas')
BEGIN
    DROP PROCEDURE sp_LimpiarSesionesExpiradas;
    PRINT 'Procedimiento sp_LimpiarSesionesExpiradas eliminado';
END
GO

-- Eliminar tabla SesionesHistorico (debe ir primero si hubiera FK)
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'SesionesHistorico')
BEGIN
    DROP TABLE SesionesHistorico;
    PRINT 'Tabla SesionesHistorico eliminada';
END
GO

-- Eliminar tabla Sesiones
IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Sesiones')
BEGIN
    DROP TABLE Sesiones;
    PRINT 'Tabla Sesiones eliminada';
END
GO

PRINT 'Rollback completado';
```

### 4.3 Verificación de Rollback

```sql
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME IN ('Sesiones', 'SesionesHistorico');
-- Debe retornar 0 filas si el rollback fue exitoso
```

---

## 5. ESTADO DE PRUEBAS

### 5.1 Pruebas que NO requieren tablas SQL (Ejecutables ahora)

| Prueba | Estado | Descripción |
|--------|--------|-------------|
| Backend inicia | VERIFICADO | FastAPI levanta correctamente |
| Imports válidos | VERIFICADO | `core/refresh_tokens.py` importa sin errores |
| Login legacy | VERIFICADO | `/api/auth/login` responde 200 OK |
| Logout básico | VERIFICADO | `/api/auth/logout` limpia cookies |
| No hay auto-migraciones | VERIFICADO | El código NO crea tablas automáticamente |

### 5.2 Pruebas BLOQUEADAS hasta ejecutar script SQL

| Prueba | Estado | Descripción |
|--------|--------|-------------|
| Crear sesión SQL | BLOQUEADA | Insertar sesión en EDARSAHUB.Sesiones |
| Refresh token | BLOQUEADA | `/api/auth/refresh` requiere tabla |
| Rotación | BLOQUEADA | Rotar tokens requiere tabla |
| Logout-all | BLOQUEADA | `/api/auth/logout-all` requiere tabla |
| Detección replay | BLOQUEADA | Requiere histórico de sesiones |

### 5.3 Pruebas pendientes POST-SCRIPT

| Prueba | Método | Criterio de Éxito |
|--------|--------|-------------------|
| Login con sesión SQL | curl | 200 + sesión insertada en Sesiones |
| Refresh token | curl | 200 + nueva sesión, anterior revocada |
| Logout | curl | Sesión marcada como revocada |
| Logout-all | curl | Todas las sesiones del usuario revocadas |
| Replay detection | curl | 401 + familia completa revocada |

---

## 6. CONFIGURACIÓN BACKEND

El backend ya está configurado para usar las tablas cuando existan:

```python
# /app/backend/core/refresh_tokens.py

# Configuración SQL Server se toma de variables de entorno
# que ya están configuradas en backend/.env para EDARSAHUB
```

La función `init_refresh_tokens_module()` debe ser llamada en `server.py` con la configuración de EDARSAHUB.

---

## 7. PRÓXIMOS PASOS

1. **USUARIO:** Ejecutar el script SQL en SSMS
2. **USUARIO:** Ejecutar las queries de validación
3. **USUARIO:** Confirmar al agente que las tablas existen
4. **AGENTE:** Ejecutar pruebas de integración con curl
5. **AGENTE:** Documentar resultados en el reporte final

---

## 8. CONTACTO PARA SOPORTE

Si encuentras errores durante la ejecución:
1. Captura el mensaje de error completo
2. Indica qué query estabas ejecutando
3. Proporciona el resultado de `SELECT @@VERSION`

---

**Documento generado por Agente E1 - EDARSA HUB**
