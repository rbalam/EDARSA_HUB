SET NOCOUNT ON;

IF COL_LENGTH(
    'dbo.Usuario_TiposAutorizacion',
    'ModoAutorizacion'
) IS NULL
    THROW 51101,
    'Falta ModoAutorizacion en Usuario_TiposAutorizacion.',
    1;

IF COL_LENGTH(
    'dbo.Usuario_Autorizaciones',
    'ModoAutorizacion'
) IS NULL
    THROW 51102,
    'Falta snapshot ModoAutorizacion en Usuario_Autorizaciones.',
    1;

IF EXISTS (
    SELECT 1
    FROM dbo.Usuario_TiposAutorizacion
    WHERE ModoAutorizacion NOT IN ('ESCALABLE','MANCOMUNADA')
)
    THROW 51103,
    'Existe modo de autorizacion invalido.',
    1;

IF EXISTS (
    SELECT 1
    FROM dbo.Usuario_Autorizaciones
    WHERE ModoAutorizacion NOT IN ('ESCALABLE','MANCOMUNADA')
)
    THROW 51104,
    'Existe snapshot de modo invalido.',
    1;

SELECT
    ModoAutorizacion,
    COUNT(*) AS Tipos
FROM dbo.Usuario_TiposAutorizacion
GROUP BY ModoAutorizacion
ORDER BY ModoAutorizacion;
