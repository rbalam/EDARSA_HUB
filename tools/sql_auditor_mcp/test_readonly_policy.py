import pytest

from server import _validate_readonly_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT TOP 10 * FROM dbo.Ventas",
        "SELECT COUNT(*) AS total FROM dbo.Ventas;",
        "WITH x AS (SELECT 1 AS n) SELECT n FROM x",
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES",
    ],
)
def test_allows_readonly_selects(sql):
    assert _validate_readonly_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO dbo.X(a) VALUES (1)",
        "UPDATE dbo.X SET a = 1",
        "DELETE FROM dbo.X",
        "DROP TABLE dbo.X",
        "ALTER TABLE dbo.X ADD b int",
        "TRUNCATE TABLE dbo.X",
        "CREATE TABLE dbo.X(a int)",
        "EXEC dbo.Algo",
        "SELECT * INTO dbo.Copia FROM dbo.X",
        "SELECT 1; DELETE FROM dbo.X",
        "SELECT 1 -- comentario",
        "SELECT 1 /* comentario */",
        "DECLARE @x int; SELECT @x",
        "USE master; SELECT 1",
    ],
)
def test_blocks_write_or_ambiguous_sql(sql):
    with pytest.raises(ValueError):
        _validate_readonly_sql(sql)
