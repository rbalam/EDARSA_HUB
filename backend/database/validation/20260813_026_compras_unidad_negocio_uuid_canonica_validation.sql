SET NOCOUNT ON;

SELECT
    DB_NAME() AS DBName,
    SUSER_SNAME() AS LoginName,
    USER_NAME() AS DatabaseUser;

SELECT
    'Compras_Pedidos' AS Tabla,
    COUNT_BIG(*) AS Total,
    SUM(
        CASE
            WHEN unidad_negocio_pk IS NULL
            THEN 1 ELSE 0
        END
    ) AS Nulos
FROM dbo.Compras_Pedidos

UNION ALL

SELECT
    'Compras_Ordenes',
    COUNT_BIG(*),
    SUM(
        CASE
            WHEN unidad_negocio_pk IS NULL
            THEN 1 ELSE 0
        END
    )
FROM dbo.Compras_Ordenes

UNION ALL

SELECT
    'Compras_Recepciones',
    COUNT_BIG(*),
    SUM(
        CASE
            WHEN unidad_negocio_pk IS NULL
            THEN 1 ELSE 0
        END
    )
FROM dbo.Compras_Recepciones;


SELECT
    'Compras_Pedidos' AS Tabla,
    COUNT_BIG(*) AS Huerfanos
FROM dbo.Compras_Pedidos p
LEFT JOIN dbo.Unidades_Negocio u
  ON u.id=p.unidad_negocio_pk
WHERE u.id IS NULL

UNION ALL

SELECT
    'Compras_Ordenes',
    COUNT_BIG(*)
FROM dbo.Compras_Ordenes o
LEFT JOIN dbo.Unidades_Negocio u
  ON u.id=o.unidad_negocio_pk
WHERE u.id IS NULL

UNION ALL

SELECT
    'Compras_Recepciones',
    COUNT_BIG(*)
FROM dbo.Compras_Recepciones r
LEFT JOIN dbo.Unidades_Negocio u
  ON u.id=r.unidad_negocio_pk
WHERE u.id IS NULL;


SELECT
    u.codigo,
    COUNT_BIG(*) AS Recepciones
FROM dbo.Compras_Recepciones r
JOIN dbo.Unidades_Negocio u
  ON u.id=r.unidad_negocio_pk
GROUP BY u.codigo
ORDER BY u.codigo;
