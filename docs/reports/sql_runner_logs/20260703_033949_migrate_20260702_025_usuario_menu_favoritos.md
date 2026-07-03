# EDARSAHUB SQL Runner Report

- Fecha: 2026-07-03T03:39:49.904866
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/20260702_025_usuario_menu_favoritos.sql`

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
IF OBJECT_ID('dbo.Usuario_Catalogo', 'U') IS NULL
    THROW 51000, 'No existe dbo.Usuario_Catalogo.', 1;

IF OBJECT_ID('dbo.Usuario_MenuFavoritos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Usuario_MenuFavoritos (
        UsuarioMenuFavoritoID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        UsuarioID INT NOT NULL,
        Ruta NVARCHAR(300) NOT NULL,
        Orden INT NOT NULL CONSTRAINT DF_UsuarioMenuFavoritos_Orden DEFAULT 0,
        Activo BIT NOT NULL CONSTRAINT DF_UsuarioMenuFavoritos_Activo DEFAULT 1,
        FechaAlta DATETIME2 NOT NULL CONSTRAINT DF_UsuarioMenuFavoritos_FechaAlta DEFAULT SYSUTCDATETIME(),
        FechaModificacion DATETIME2 NULL,
        CreatedBy NVARCHAR(100) NULL,
        ModifiedBy NVARCHAR(100) NULL,
        CONSTRAINT FK_UsuarioMenuFavoritos_Usuario
            FOREIGN KEY (UsuarioID) REFERENCES dbo.Usuario_Catalogo(UsuarioID),
        CONSTRAINT CK_UsuarioMenuFavoritos_Ruta_NoVacia
            CHECK (LEN(LTRIM(RTRIM(Ruta))) > 0),
        CONSTRAINT CK_UsuarioMenuFavoritos_Ruta_Relativa
            CHECK (LEFT(LTRIM(RTRIM(Ruta)), 1) = '/')
    );

    CREATE UNIQUE INDEX UX_UsuarioMenuFavoritos_Usuario_Ruta
        ON dbo.Usuario_MenuFavoritos(UsuarioID, Ruta);

    CREATE INDEX IX_UsuarioMenuFavoritos_Usuario_Activo_Orden
        ON dbo.Usuario_MenuFavoritos(UsuarioID, Activo, Orden);
END;

```