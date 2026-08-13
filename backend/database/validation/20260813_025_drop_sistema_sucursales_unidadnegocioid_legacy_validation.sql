SET NOCOUNT ON;

SELECT
    DB_NAME() AS DBName,
    SUSER_SNAME() AS LoginName,
    USER_NAME() AS DatabaseUser;

SELECT
    CASE
        WHEN COL_LENGTH(
            'dbo.Sistema_Sucursales',
            'UnidadNegocioID'
        ) IS NULL
        THEN 0
        ELSE 1
    END AS LegacyColumnExists;

SELECT
    COUNT(*) AS SucursalesActivas
FROM dbo.Sistema_Sucursales
WHERE ISNULL(Activo,0)=1;

SELECT
    COUNT(*) AS UnidadesActivas
FROM dbo.Unidades_Negocio
WHERE ISNULL(activo,1)=1;

SELECT
    COUNT(*) AS MapeosCanonicos
FROM (
    SELECT
        s.SucursalID
    FROM dbo.Sistema_Sucursales s
    JOIN dbo.Sistema_SucursalServidorMapeo m
      ON m.SucursalID=s.SucursalID
     AND ISNULL(m.Activo,0)=1
    JOIN dbo.Unidades_Negocio u
      ON LOWER(
             CONVERT(
                 nvarchar(100),
                 u.server_id
             )
         )
         =
         LOWER(
             CONVERT(
                 nvarchar(100),
                 m.ServidorID
             )
         )
     AND (
            NULLIF(
                LTRIM(
                    RTRIM(
                        CONVERT(
                            nvarchar(50),
                            u.sucursal_origen_id
                        )
                    )
                ),
                ''
            )
            =
            NULLIF(
                LTRIM(
                    RTRIM(
                        CONVERT(
                            nvarchar(50),
                            m.SucursalOrigenID
                        )
                    )
                ),
                ''
            )
            OR
            (
                NULLIF(
                    LTRIM(
                        RTRIM(
                            CONVERT(
                                nvarchar(50),
                                u.sucursal_origen_id
                            )
                        )
                    ),
                    ''
                ) IS NULL
                AND
                NULLIF(
                    LTRIM(
                        RTRIM(
                            CONVERT(
                                nvarchar(50),
                                m.SucursalOrigenID
                            )
                        )
                    ),
                    ''
                ) IS NULL
            )
         )
    WHERE
        ISNULL(s.Activo,0)=1
        AND ISNULL(u.activo,1)=1
    GROUP BY s.SucursalID
    HAVING COUNT(DISTINCT u.id)=1
) x;

SELECT
    TYPE_NAME(c.user_type_id) AS TipoUnidadNegocioID
FROM sys.columns c
WHERE
    c.object_id=
        OBJECT_ID(
            'dbo.vw_Usuario_RolesContexto'
        )
    AND c.name='UnidadNegocioID';
