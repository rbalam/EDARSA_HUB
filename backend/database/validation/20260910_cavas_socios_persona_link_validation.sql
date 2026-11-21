/*
Gate 12G - validacion post-migracion.
Solo debe ejecutarse despues de que un Gate posterior ejecute la migracion.
*/

SELECT
    c.name AS column_name,
    t.name AS data_type,
    c.is_nullable
FROM sys.columns c
JOIN sys.types t
  ON t.user_type_id = c.user_type_id
WHERE c.object_id = OBJECT_ID(N'dbo.CavaSocios_Socios')
  AND c.name = N'PersonaID';

SELECT
    fk.name AS fk_name,
    pc.name AS parent_column,
    OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
    rc.name AS referenced_column
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc
  ON fkc.constraint_object_id = fk.object_id
JOIN sys.columns pc
  ON pc.object_id = fkc.parent_object_id
 AND pc.column_id = fkc.parent_column_id
JOIN sys.columns rc
  ON rc.object_id = fkc.referenced_object_id
 AND rc.column_id = fkc.referenced_column_id
WHERE fk.parent_object_id = OBJECT_ID(N'dbo.CavaSocios_Socios')
  AND pc.name = N'PersonaID';

SELECT
    COUNT_BIG(*) AS total_socios,
    SUM(CASE WHEN PersonaID IS NULL THEN 1 ELSE 0 END) AS persona_null,
    SUM(CASE WHEN PersonaID IS NOT NULL THEN 1 ELSE 0 END) AS persona_present
FROM dbo.CavaSocios_Socios;

SELECT
    OBJECT_NAME(fk.parent_object_id) AS child_table,
    pc.name AS child_column,
    rc.name AS referenced_column,
    fk.name AS fk_name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc
  ON fkc.constraint_object_id = fk.object_id
JOIN sys.columns pc
  ON pc.object_id = fkc.parent_object_id
 AND pc.column_id = fkc.parent_column_id
JOIN sys.columns rc
  ON rc.object_id = fkc.referenced_object_id
 AND rc.column_id = fkc.referenced_column_id
WHERE fk.referenced_object_id = OBJECT_ID(N'dbo.CavaSocios_Socios')
ORDER BY child_table, fk.name;
