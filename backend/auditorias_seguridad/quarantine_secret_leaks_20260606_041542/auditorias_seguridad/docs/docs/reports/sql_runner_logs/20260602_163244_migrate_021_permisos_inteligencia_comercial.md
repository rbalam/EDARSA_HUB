# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:32:44.070704
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/021_permisos_inteligencia_comercial.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: resultado, CodigoRol, CodigoAccion, Permitido, Activo
- Filas: 21
- Preview (primeras 20 filas):
```
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'SUPERADMIN', 'CodigoAccion': 'VER', 'Permitido': True, 'Activo': True}
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'SUPERADMIN', 'CodigoAccion': 'EXPORTAR', 'Permitido': True, 'Activo': True}
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'SUPERADMIN', 'CodigoAccion': 'CONFIGURAR', 'Permitido': True, 'Activo': True}
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'SUPERADMIN', 'CodigoAccion': 'GESTIONAR', 'Permitido': True, 'Activo': True}
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'CRM_ADMIN', 'CodigoAccion': 'VER', 'Permitido': True, 'Activo': True}
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'CRM_ADMIN', 'CodigoAccion': 'EXPORTAR', 'Permitido': True, 'Activo': True}
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'CRM_ADMIN', 'CodigoAccion': 'GESTIONAR', 'Permitido': True, 'Activo': True}
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'DIRECCION', 'CodigoAccion': 'VER', 'Permitido': True, 'Activo': True}
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'DIRECCION', 'CodigoAccion': 'EXPORTAR', 'Permitido': True, 'Activo': True}
  {'resultado': 'PERMISOS_INTELIGENCIA_COMERCIAL', 'CodigoRol': 'CRM_AUDIT', 'CodigoAccion': 'VER', 'Permitido': True, 'Activo': True}
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

-- Obtener ID del módulo
SELECT @ModuloID = ModuloID
FROM Usuario_Modulos
WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';

IF @ModuloID IS NULL
BEGIN
    PRINT 'ERROR: Módulo INTELIGENCIA_COMERCIAL no existe.';
    RETURN;
END

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

-- Insertar permisos que no existan (sin especificar ID - es IDENTITY)
INSERT INTO Usuario_PermisosRolModulo (
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