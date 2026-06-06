# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:32:14.609571
- Modo: `migrate`
- Servidor: `<REDACTED_EDARSAHUB_SQL_HOST>`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/021_permisos_inteligencia_comercial.sql`

## Resultado
ERROR

## Detalle
```text
SQL bloqueado por patrón peligroso: \bDROP\s+TABLE\b
```

## SQL ejecutado / revisado
```sql
/* ============================================================
   ASIGNAR PERMISOS INTELIGENCIA_COMERCIAL EN Usuario_PermisosRolModulo
   
   Matriz de permisos:
   - SUPERADMIN, ADMIN, CRM_ADMIN: VER, EXPORTAR, GESTIONAR
   - GERENCIA, DIRECCION: VER, EXPORTAR
   - CRM_EJEC: VER, EXPORTAR
   - CRM_AUDIT, AUDITOR, VISOR: VER
   ============================================================ */

DECLARE @ModuloID INT;
DECLARE @MaxID BIGINT;

-- Obtener ID del módulo
SELECT @ModuloID = ModuloID
FROM Usuario_Modulos
WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';

IF @ModuloID IS NULL
BEGIN
    PRINT 'ERROR: Módulo INTELIGENCIA_COMERCIAL no existe.';
    RETURN;
END

-- Obtener max ID actual
SELECT @MaxID = ISNULL(MAX(PermisoRolModuloID), 0)
FROM Usuario_PermisosRolModulo;

-- Tabla temporal para permisos a crear
CREATE TABLE #PermisosIC (
    CodigoRol VARCHAR(50),
    CodigoAccion VARCHAR(50)
);

-- SUPERADMIN: acceso total
INSERT INTO #PermisosIC VALUES ('SUPERADMIN', 'VER');
INSERT INTO #PermisosIC VALUES ('SUPERADMIN', 'EXPORTAR');
INSERT INTO #PermisosIC VALUES ('SUPERADMIN', 'GESTIONAR');
INSERT INTO #PermisosIC VALUES ('SUPERADMIN', 'CONFIGURAR');

-- ADMIN: acceso total
INSERT INTO #PermisosIC VALUES ('ADMIN', 'VER');
INSERT INTO #PermisosIC VALUES ('ADMIN', 'EXPORTAR');
INSERT INTO #PermisosIC VALUES ('ADMIN', 'GESTIONAR');

-- CRM_ADMIN: acceso total IC
INSERT INTO #PermisosIC VALUES ('CRM_ADMIN', 'VER');
INSERT INTO #PermisosIC VALUES ('CRM_ADMIN', 'EXPORTAR');
INSERT INTO #PermisosIC VALUES ('CRM_ADMIN', 'GESTIONAR');

-- GERENCIA: consulta y exportación
INSERT INTO #PermisosIC VALUES ('GERENCIA', 'VER');
INSERT INTO #PermisosIC VALUES ('GERENCIA', 'EXPORTAR');

-- DIRECCION: consulta y exportación
INSERT INTO #PermisosIC VALUES ('DIRECCION', 'VER');
INSERT INTO #PermisosIC VALUES ('DIRECCION', 'EXPORTAR');

-- CRM_EJEC: consulta y exportación
INSERT INTO #PermisosIC VALUES ('CRM_EJEC', 'VER');
INSERT INTO #PermisosIC VALUES ('CRM_EJEC', 'EXPORTAR');

-- CRM_AUDIT: solo consulta
INSERT INTO #PermisosIC VALUES ('CRM_AUDIT', 'VER');

-- AUDITOR: solo consulta
INSERT INTO #PermisosIC VALUES ('AUDITOR', 'VER');

-- VISOR: solo consulta
INSERT INTO #PermisosIC VALUES ('VISOR', 'VER');

-- GERENTE_OPS: consulta y exportación
INSERT INTO #PermisosIC VALUES ('GERENTE_OPS', 'VER');
INSERT INTO #PermisosIC VALUES ('GERENTE_OPS', 'EXPORTAR');

-- Insertar permisos que no existan
INSERT INTO Usuario_PermisosRolModulo (
    PermisoRolModuloID,
    RolID,
    ModuloID,
    AccionID,
    Permitido,
    RestriccionPropietario,
    RestriccionSucursal,
    RequiereAutorizacion,
    NivelAutorizacionRequerido,
    Activo,
    FechaAlta,
    CreatedBy
)
SELECT
    @MaxID + ROW_NUMBER() OVER (ORDER BY r.RolID, a.AccionID),
    r.RolID,
    @ModuloID,
    a.AccionID,
    1, -- Permitido
    0, -- Sin restricción propietario
    0, -- Sin restricción sucursal
    0, -- No requiere autorización
    NULL,
    1, -- Activo
    SYSDATETIME(),
    'SISTEMA_MIGRACION'
FROM #PermisosIC p
JOIN Usuario_Roles r ON r.CodigoRol = p.CodigoRol
JOIN Usuario_Acciones a ON a.CodigoAccion = p.CodigoAccion
WHERE NOT EXISTS (
    SELECT 1
    FROM Usuario_PermisosRolModulo prm
    WHERE prm.RolID = r.RolID
      AND prm.ModuloID = @ModuloID
      AND prm.AccionID = a.AccionID
);

DROP TABLE #PermisosIC;

-- Verificación final
SELECT 
    'PERMISOS_INTELIGENCIA_COMERCIAL' AS resultado,
    r.CodigoRol,
    a.CodigoAccion,
    p.Permitido,
    p.Activo
FROM Usuario_PermisosRolModulo p
JOIN Usuario_Roles r ON p.RolID = r.RolID
JOIN Usuario_Modulos m ON p.ModuloID = m.ModuloID
JOIN Usuario_Acciones a ON p.AccionID = a.AccionID
WHERE m.CodigoModulo = 'INTELIGENCIA_COMERCIAL'
ORDER BY r.NivelJerarquia DESC, a.AccionID;

PRINT 'Permisos de INTELIGENCIA_COMERCIAL asignados correctamente.';

```