SET NOCOUNT ON;
SET XACT_ABORT ON;

PRINT '===== VALIDACION COSTOS MARGENES CONFIG CANONICA =====';

IF OBJECT_ID(
    'dbo.Comercial_CostosMargenesConfiguracion',
    'U'
) IS NULL
    THROW 51000,
        'Falta Comercial_CostosMargenesConfiguracion',
        1;

IF OBJECT_ID(
    'dbo.Comercial_CostosMargenesConfiguracionUsuario',
    'U'
) IS NULL
    THROW 51000,
        'Falta Comercial_CostosMargenesConfiguracionUsuario',
        1;

IF COL_LENGTH(
    'dbo.Comercial_CostosMargenesConfiguracion',
    'EmpresaID'
) IS NULL
    THROW 51000,
        'Falta EmpresaID',
        1;

IF COL_LENGTH(
    'dbo.Comercial_CostosMargenesConfiguracion',
    'UnidadNegocioID'
) IS NULL
    THROW 51000,
        'Falta UnidadNegocioID',
        1;

IF COL_LENGTH(
    'dbo.Comercial_CostosMargenesConfiguracion',
    'SucursalID'
) IS NOT NULL
    THROW 51000,
        'SucursalID no debe existir como alcance local',
        1;

IF COL_LENGTH(
    'dbo.Comercial_CostosMargenesConfiguracion',
    'MargenMinimoPorcentaje'
) IS NULL
    THROW 51000,
        'Falta MargenMinimoPorcentaje',
        1;

IF COL_LENGTH(
    'dbo.Comercial_CostosMargenesConfiguracion',
    'MultiploRedondeo'
) IS NULL
    THROW 51000,
        'Falta MultiploRedondeo',
        1;

IF COL_LENGTH(
    'dbo.Comercial_CostosMargenesConfiguracion',
    'MetodoRedondeo'
) IS NULL
    THROW 51000,
        'Falta MetodoRedondeo',
        1;

IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_key_columns fkc
    JOIN sys.columns pc
      ON pc.object_id = fkc.parent_object_id
     AND pc.column_id = fkc.parent_column_id
    WHERE
        fkc.parent_object_id =
            OBJECT_ID(
                'dbo.Comercial_CostosMargenesConfiguracion'
            )
        AND pc.name = 'EmpresaID'
        AND fkc.referenced_object_id =
            OBJECT_ID('dbo.Sistema_Empresas')
)
    THROW 51000,
        'EmpresaID no referencia Sistema_Empresas',
        1;

IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_key_columns fkc
    JOIN sys.columns pc
      ON pc.object_id = fkc.parent_object_id
     AND pc.column_id = fkc.parent_column_id
    WHERE
        fkc.parent_object_id =
            OBJECT_ID(
                'dbo.Comercial_CostosMargenesConfiguracion'
            )
        AND pc.name = 'UnidadNegocioID'
        AND fkc.referenced_object_id =
            OBJECT_ID('dbo.Unidades_Negocio')
)
    THROW 51000,
        'UnidadNegocioID no referencia Unidades_Negocio',
        1;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes i
    WHERE
        i.object_id =
            OBJECT_ID(
                'dbo.Comercial_CostosMargenesConfiguracion'
            )
        AND i.name =
            'UX_CostosMargenesConfig_Empresa'
        AND i.is_unique = 1
)
    THROW 51000,
        'Falta UX_CostosMargenesConfig_Empresa',
        1;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes i
    WHERE
        i.object_id =
            OBJECT_ID(
                'dbo.Comercial_CostosMargenesConfiguracion'
            )
        AND i.name =
            'UX_CostosMargenesConfig_Unidad'
        AND i.is_unique = 1
)
    THROW 51000,
        'Falta UX_CostosMargenesConfig_Unidad',
        1;

IF EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    JOIN sys.columns c
      ON c.object_id = dc.parent_object_id
     AND c.column_id = dc.parent_column_id
    WHERE
        dc.parent_object_id =
            OBJECT_ID(
                'dbo.Comercial_CostosMargenesConfiguracion'
            )
        AND c.name IN (
            'MargenMinimoPorcentaje',
            'MultiploRedondeo',
            'MetodoRedondeo'
        )
)
    THROW 51000,
        'Configuracion negocio contiene defaults funcionales',
        1;

IF EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    JOIN sys.columns c
      ON c.object_id = dc.parent_object_id
     AND c.column_id = dc.parent_column_id
    WHERE
        dc.parent_object_id =
            OBJECT_ID(
                'dbo.Comercial_CostosMargenesConfiguracionUsuario'
            )
        AND c.name IN (
            'MargenMinimoPorcentaje',
            'MultiploRedondeo',
            'MetodoRedondeo'
        )
)
    THROW 51000,
        'Configuracion usuario contiene defaults funcionales',
        1;

PRINT 'EMPRESA_SCOPE=PASS';
PRINT 'UNIDAD_NEGOCIO_SCOPE=PASS';
PRINT 'SUCURSAL_LOCAL=ABSENT_PASS';
PRINT 'BUSINESS_DEFAULTS=ABSENT_PASS';
PRINT 'VALIDATION_027=PASS';
