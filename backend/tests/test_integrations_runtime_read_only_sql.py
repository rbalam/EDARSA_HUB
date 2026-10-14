import pytest

from modules.integrations_runtime.read_only_sql import (
    validate_readonly_sql,
    validate_readonly_sql_result,
)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1",
        "SELECT TOP 10 * FROM dbo.Tabla",
        "WITH x AS (SELECT 1 AS n) SELECT n FROM x",
        "SELECT 'update delete drop' AS texto",
        "SELECT 1 -- update dbo.X",
    ],
)
def test_allows_read_only_sql(sql):
    assert validate_readonly_sql(sql) == sql.strip()


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "UPDATE dbo.X SET a=1",
        "DELETE FROM dbo.X",
        "SELECT * INTO dbo.Y FROM dbo.X",
        "SELECT 1; SELECT 2",
        "EXEC dbo.proc",
        "SELECT * FROM OPENROWSET('x','y','z')",
        "SELECT dbo.xp_cmdshell('dir')",
    ],
)
def test_rejects_non_read_only_sql(sql):
    with pytest.raises(ValueError):
        validate_readonly_sql(sql)


def test_compatibility_result_contract():
    assert validate_readonly_sql_result("SELECT 1") == (True, "")
    ok, error = validate_readonly_sql_result("DROP TABLE dbo.X")
    assert ok is False
    assert error
