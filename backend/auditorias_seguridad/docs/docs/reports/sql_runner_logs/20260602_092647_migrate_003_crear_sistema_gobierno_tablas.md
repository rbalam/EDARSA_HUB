# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T09:26:47.849384
- Modo: `migrate`
- Servidor: `<REDACTED_EDARSAHUB_SQL_HOST>`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/003_crear_sistema_gobierno_tablas.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: Comando
- Filas afectadas: -1


## SQL ejecutado / revisado
```sql
/* ============================================================
   MIGRACIÓN: Tabla de Gobierno de Datos
   Script: 003_crear_sistema_gobierno_tablas.sql
   Modo: migrate
   
   Crea tabla de metadatos para gobernar el uso de tablas en EDARSAHUB.
   ============================================================ */

IF OBJECT_ID('dbo.Sistema_Gobierno_Tablas', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_Gobierno_Tablas (
        id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        nombre_tabla SYSNAME NOT NULL,
        esquema SYSNAME NOT NULL DEFAULT 'dbo',
        modulo NVARCHAR(100) NOT NULL,
        categoria NVARCHAR(50) NOT NULL,
        estado NVARCHAR(50) NOT NULL,
        fuente_verdad NVARCHAR(100) NULL,
        tabla_reemplazo SYSNAME NULL,
        permite_insert BIT NOT NULL DEFAULT 1,
        permite_update BIT NOT NULL DEFAULT 1,
        permite_delete BIT NOT NULL DEFAULT 0,
        observaciones NVARCHAR(MAX) NULL,
        fecha_alta DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        fecha_ultima_actualizacion DATETIME2 NOT NULL DEFAULT SYSDATETIME()
    );

    CREATE UNIQUE INDEX UX_Sistema_Gobierno_Tablas
    ON dbo.Sistema_Gobierno_Tablas(esquema, nombre_tabla);
END;
GO

```