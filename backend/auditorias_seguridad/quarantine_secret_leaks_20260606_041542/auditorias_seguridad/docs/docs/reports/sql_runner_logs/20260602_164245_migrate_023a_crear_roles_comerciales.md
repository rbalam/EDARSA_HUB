# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T16:42:45.847268
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/023a_crear_roles_comerciales.sql`

## Resultado
OK

## Resumen
- Batches ejecutados: 1
- Mensaje: Ejecución completada.

### Batch 1
- Tipo: SELECT
- Columnas: RolID, CodigoRol, NombreRol, NivelJerarquia, Activo
- Filas: 7
- Preview (primeras 20 filas):
```
  {'RolID': 6, 'CodigoRol': 'SUPERADMIN', 'NombreRol': 'SuperAdministrador', 'NivelJerarquia': 100, 'Activo': True}
  {'RolID': 17, 'CodigoRol': 'ADMIN_COMERCIAL', 'NombreRol': 'Administrador Comercial', 'NivelJerarquia': 85, 'Activo': True}
  {'RolID': 10, 'CodigoRol': 'DIRECCION', 'NombreRol': 'Dirección', 'NivelJerarquia': 80, 'Activo': True}
  {'RolID': 18, 'CodigoRol': 'GERENTE_UNIDAD', 'NombreRol': 'Gerente de Unidad', 'NivelJerarquia': 55, 'Activo': True}
  {'RolID': 21, 'CodigoRol': 'CONFIGURADOR_COMERCIAL', 'NombreRol': 'Configurador Comercial', 'NivelJerarquia': 45, 'Activo': True}
  {'RolID': 19, 'CodigoRol': 'ANALISTA_COMERCIAL', 'NombreRol': 'Analista Comercial', 'NivelJerarquia': 40, 'Activo': True}
  {'RolID': 20, 'CodigoRol': 'VISOR_COMERCIAL', 'NombreRol': 'Visor Comercial', 'NivelJerarquia': 10, 'Activo': True}
```


## SQL ejecutado / revisado
```sql
/* ============================================================
   EDARSAHUB - Crear Roles Comerciales para INTELIGENCIA_COMERCIAL
   Fecha: 2026-06-02
   
   Roles a crear:
   - ADMIN_COMERCIAL: Administración completa del módulo comercial
   - GERENTE_UNIDAD: Gerente de unidad de negocio
   - ANALISTA_COMERCIAL: Analista de datos comerciales
   - VISOR_COMERCIAL: Solo lectura de métricas comerciales
   - CONFIGURADOR_COMERCIAL: Configuración y gestión operativa
   ============================================================ */

SET NOCOUNT ON;

-- ADMIN_COMERCIAL
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_Roles WHERE CodigoRol = 'ADMIN_COMERCIAL')
BEGIN
    INSERT INTO dbo.Usuario_Roles (
        CodigoRol,
        NombreRol,
        Descripcion,
        EsRolSistema,
        Activo,
        FechaAlta,
        NivelJerarquia
    ) VALUES (
        'ADMIN_COMERCIAL',
        'Administrador Comercial',
        'Administración completa del módulo comercial: KPIs, reportes, configuración de dashboards.',
        0,
        1,
        SYSDATETIME(),
        85
    );
    PRINT 'Rol ADMIN_COMERCIAL creado.';
END
ELSE
    PRINT 'Rol ADMIN_COMERCIAL ya existe.';

-- GERENTE_UNIDAD
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_Roles WHERE CodigoRol = 'GERENTE_UNIDAD')
BEGIN
    INSERT INTO dbo.Usuario_Roles (
        CodigoRol,
        NombreRol,
        Descripcion,
        EsRolSistema,
        Activo,
        FechaAlta,
        NivelJerarquia
    ) VALUES (
        'GERENTE_UNIDAD',
        'Gerente de Unidad',
        'Gerente de unidad de negocio: acceso a métricas de su(s) unidad(es) asignada(s).',
        0,
        1,
        SYSDATETIME(),
        55
    );
    PRINT 'Rol GERENTE_UNIDAD creado.';
END
ELSE
    PRINT 'Rol GERENTE_UNIDAD ya existe.';

-- ANALISTA_COMERCIAL
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_Roles WHERE CodigoRol = 'ANALISTA_COMERCIAL')
BEGIN
    INSERT INTO dbo.Usuario_Roles (
        CodigoRol,
        NombreRol,
        Descripcion,
        EsRolSistema,
        Activo,
        FechaAlta,
        NivelJerarquia
    ) VALUES (
        'ANALISTA_COMERCIAL',
        'Analista Comercial',
        'Analista de datos comerciales: consulta y exportación de métricas y reportes.',
        0,
        1,
        SYSDATETIME(),
        40
    );
    PRINT 'Rol ANALISTA_COMERCIAL creado.';
END
ELSE
    PRINT 'Rol ANALISTA_COMERCIAL ya existe.';

-- VISOR_COMERCIAL
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_Roles WHERE CodigoRol = 'VISOR_COMERCIAL')
BEGIN
    INSERT INTO dbo.Usuario_Roles (
        CodigoRol,
        NombreRol,
        Descripcion,
        EsRolSistema,
        Activo,
        FechaAlta,
        NivelJerarquia
    ) VALUES (
        'VISOR_COMERCIAL',
        'Visor Comercial',
        'Solo lectura de métricas comerciales. Sin exportación ni configuración.',
        0,
        1,
        SYSDATETIME(),
        10
    );
    PRINT 'Rol VISOR_COMERCIAL creado.';
END
ELSE
    PRINT 'Rol VISOR_COMERCIAL ya existe.';

-- CONFIGURADOR_COMERCIAL
IF NOT EXISTS (SELECT 1 FROM dbo.Usuario_Roles WHERE CodigoRol = 'CONFIGURADOR_COMERCIAL')
BEGIN
    INSERT INTO dbo.Usuario_Roles (
        CodigoRol,
        NombreRol,
        Descripcion,
        EsRolSistema,
        Activo,
        FechaAlta,
        NivelJerarquia
    ) VALUES (
        'CONFIGURADOR_COMERCIAL',
        'Configurador Comercial',
        'Configuración y gestión operativa del portal de inteligencia comercial.',
        0,
        1,
        SYSDATETIME(),
        45
    );
    PRINT 'Rol CONFIGURADOR_COMERCIAL creado.';
END
ELSE
    PRINT 'Rol CONFIGURADOR_COMERCIAL ya existe.';

-- Verificación final
SELECT 
    RolID,
    CodigoRol,
    NombreRol,
    NivelJerarquia,
    Activo
FROM dbo.Usuario_Roles
WHERE CodigoRol IN (
    'SUPERADMIN',
    'ADMIN_COMERCIAL',
    'DIRECCION',
    'GERENTE_UNIDAD',
    'ANALISTA_COMERCIAL',
    'VISOR_COMERCIAL',
    'CONFIGURADOR_COMERCIAL'
)
ORDER BY NivelJerarquia DESC;

PRINT 'Roles comerciales verificados.';

```