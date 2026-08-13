SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> 'EDARSAHUB'
    THROW 52000, 'Base inesperada.', 1;

IF SUSER_SNAME() <> 'HRLectura'
    THROW 52001, 'Login inesperado.', 1;

IF USER_NAME() <> 'HRLectura'
    THROW 52002, 'Usuario inesperado.', 1;

DECLARE @Pairs TABLE (
    LegacyAlmacenID int NOT NULL PRIMARY KEY,
    SurvivorAlmacenID int NOT NULL UNIQUE
);

INSERT INTO @Pairs (
    LegacyAlmacenID,
    SurvivorAlmacenID
)
VALUES
(1,86),
(2,87),
(3,88),
(4,89),
(5,90),
(6,91),
(7,92),
(8,93),
(9,94),
(10,95),
(11,96),
(12,97),
(13,98),
(14,99),
(15,100),
(16,101),
(17,102),
(18,103),
(19,104),
(20,105),
(21,106),
(22,107),
(23,108),
(24,109),
(25,110),
(26,111),
(27,112),
(28,113),
(29,114),
(30,115),
(31,116),
(32,117),
(33,118),
(34,119),
(35,120),
(36,121),
(37,122),
(38,123),
(39,124);

IF (SELECT COUNT(*) FROM @Pairs) <> 39
    THROW 52003, 'Cantidad de pares inesperada.', 1;

IF EXISTS (
    SELECT 1
    FROM @Pairs p
    LEFT JOIN dbo.Inventario_Almacenes l
      ON l.AlmacenID = p.LegacyAlmacenID
    LEFT JOIN dbo.Inventario_Almacenes s
      ON s.AlmacenID = p.SurvivorAlmacenID
    WHERE l.AlmacenID IS NULL
       OR s.AlmacenID IS NULL
)
    THROW 52004, 'Par legacy/survivor inexistente.', 1;

IF EXISTS (
    SELECT 1
    FROM @Pairs p
    JOIN dbo.Inventario_Almacenes l
      ON l.AlmacenID = p.LegacyAlmacenID
    JOIN dbo.Inventario_Almacenes s
      ON s.AlmacenID = p.SurvivorAlmacenID
    WHERE ISNULL(l.EmpresaID,-1) <> ISNULL(s.EmpresaID,-1)
       OR ISNULL(l.CodigoAlmacen,'') <> ISNULL(s.CodigoAlmacen,'')
       OR ISNULL(l.NombreAlmacen,'') <> ISNULL(s.NombreAlmacen,'')
)
    THROW 52005, 'Par legacy/survivor no es semánticamente idéntico.', 1;

IF (
    SELECT COUNT(*)
    FROM dbo.Compras_Recepciones
    WHERE AlmacenID = 1
) <> 1470
    THROW 52006, 'Recepciones de AlmacenID 1 cambiaron.', 1;

IF (
    SELECT COUNT(*)
    FROM dbo.Inventario_Movimientos
    WHERE AlmacenID = 86
) <> 385
    THROW 52007, 'Movimientos de AlmacenID 86 cambiaron.', 1;

BEGIN TRY
    BEGIN TRANSACTION;

    UPDATE r
       SET r.AlmacenID = p.SurvivorAlmacenID
    FROM dbo.Compras_Recepciones r
    JOIN @Pairs p
      ON p.LegacyAlmacenID = r.AlmacenID;

    UPDATE e
       SET e.AlmacenID = p.SurvivorAlmacenID
    FROM dbo.Inventario_Existencias e
    JOIN @Pairs p
      ON p.LegacyAlmacenID = e.AlmacenID;

    UPDATE m
       SET m.AlmacenID = p.SurvivorAlmacenID
    FROM dbo.Inventario_Movimientos m
    JOIN @Pairs p
      ON p.LegacyAlmacenID = m.AlmacenID;

    IF EXISTS (
        SELECT 1
        FROM dbo.Compras_Recepciones r
        JOIN @Pairs p
          ON p.LegacyAlmacenID = r.AlmacenID
    )
        THROW 52008, 'Quedaron recepciones apuntando a almacenes legacy.', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Inventario_Existencias e
        JOIN @Pairs p
          ON p.LegacyAlmacenID = e.AlmacenID
    )
        THROW 52009, 'Quedaron existencias apuntando a almacenes legacy.', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Inventario_Movimientos m
        JOIN @Pairs p
          ON p.LegacyAlmacenID = m.AlmacenID
    )
        THROW 52010, 'Quedaron movimientos apuntando a almacenes legacy.', 1;

    DELETE a
    FROM dbo.Inventario_Almacenes a
    JOIN @Pairs p
      ON p.LegacyAlmacenID = a.AlmacenID;

    IF @@ROWCOUNT <> 39
        THROW 52011, 'Cantidad eliminada distinta de 39.', 1;

    IF EXISTS (
        SELECT 1
        FROM @Pairs p
        JOIN dbo.Inventario_Almacenes a
          ON a.AlmacenID = p.LegacyAlmacenID
    )
        THROW 52012, 'Persisten almacenes legacy.', 1;

    IF (
        SELECT COUNT(*)
        FROM dbo.Inventario_Almacenes
    ) <> 67
        THROW 52013, 'Cantidad final de almacenes distinta de 67.', 1;

    IF (
        SELECT COUNT_BIG(*)
        FROM dbo.Inventario_Movimientos
    ) <> 15224
        THROW 52014, 'Cantidad de movimientos cambió.', 1;

    IF (
        SELECT COUNT(*)
        FROM dbo.Compras_Recepciones
    ) < 1470
        THROW 52015, 'Cantidad de recepciones inválida.', 1;

    COMMIT TRANSACTION;

    SELECT
        'CONSOLIDATION_OK' AS Estado,
        39 AS ParesConsolidados,
        67 AS AlmacenesFinales;

END TRY
BEGIN CATCH

    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
