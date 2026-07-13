from pathlib import Path
import re


BACKEND_ROOT = Path(__file__).resolve().parents[1]

MIGRATION_PATH = (
    BACKEND_ROOT
    / "database"
    / "migrations"
    / "20260712_016_scheduler_distributed_locks_sql.sql"
)

VALIDATION_PATH = (
    BACKEND_ROOT
    / "database"
    / "validation"
    / "20260712_016_scheduler_distributed_locks_sql_validation.sql"
)

WRITE_STATEMENT_RE = re.compile(
    r"(?im)^[ \t]*"
    r"(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|"
    r"TRUNCATE|EXEC|EXECUTE)\b"
)

MIGRATION_DISALLOWED_RE = re.compile(
    r"(?im)^[ \t]*"
    r"(INSERT|UPDATE|DELETE|MERGE|ALTER|DROP|"
    r"TRUNCATE|EXEC|EXECUTE)\b"
)

MALFORMED_TOKEN_RE = re.compile(
    r"SELECTCOUNT_BIG"
    r"|=N'sysutcdatetime'"
    r"|=N'lockuntil>=heartbeatat'"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_validation_is_readonly_and_requires_exact_identity():
    text = _read(VALIDATION_PATH)

    assert WRITE_STATEMENT_RE.search(text) is None

    assert (
        text.count(
            "CONVERT(VARBINARY(256), N'EDARSAHUB')"
        )
        == 1
    )

    assert (
        text.count(
            "CONVERT(VARBINARY(256), N'HRLectura')"
        )
        == 2
    )

    assert "N'HRLECTURA'" not in text
    assert "UPPER(LTRIM" not in text


def test_scheduler_contract_files_have_no_malformed_tokens():
    for path in (MIGRATION_PATH, VALIDATION_PATH):
        text = _read(path)

        assert MALFORMED_TOKEN_RE.search(text) is None
        assert re.search(
            r"SELECT[ \t]+COUNT_BIG[ \t]*\(",
            text,
        )


def test_migration_and_validation_share_column_contract():
    expected_columns = (
        (
            "JobName",
            "varchar",
            "100",
            "0",
        ),
        (
            "OwnerID",
            "varchar",
            "200",
            "0",
        ),
        (
            "AcquiredAt",
            "datetime2",
            "NULL",
            "3",
        ),
        (
            "HeartbeatAt",
            "datetime2",
            "NULL",
            "3",
        ),
        (
            "LockUntil",
            "datetime2",
            "NULL",
            "3",
        ),
    )

    for path in (MIGRATION_PATH, VALIDATION_PATH):
        compact = _compact(_read(path))

        for (
            column_name,
            data_type,
            max_length,
            scale,
        ) in expected_columns:
            expected = (
                f"N'{column_name}', "
                f"N'{data_type}', "
                f"CONVERT(SMALLINT, {max_length}), "
                f"CONVERT(TINYINT, {scale}), "
                "CONVERT(BIT, 0)"
            )

            assert expected in compact

        assert (
            "c.name NOT IN ( "
            "N'JobName', "
            "N'OwnerID', "
            "N'AcquiredAt', "
            "N'HeartbeatAt', "
            "N'LockUntil' "
            ")"
        ) in compact


def test_migration_and_validation_share_constraint_contract():
    required = (
        "PK_Scheduler_DistributedLocks",
        "CK_Scheduler_DistributedLocks_Expiration",
        "DF_Scheduler_DistributedLocks_AcquiredAt",
        "DF_Scheduler_DistributedLocks_HeartbeatAt",
        "IX_Scheduler_DistributedLocks_LockUntil",
        "IX_Scheduler_DistributedLocks_OwnerID",
    )

    for path in (MIGRATION_PATH, VALIDATION_PATH):
        text = _read(path)

        for token in required:
            assert token in text

        assert (
            text.count(
                ") = N'sysutcdatetime'"
            )
            == 2
        )

        assert (
            text.count(
                ") = N'lockuntil>=heartbeatat'"
            )
            == 1
        )

        assert (
            text.count(
                "ic.is_descending_key = 0"
            )
            == 3
        )

        assert text.count(") <> 2") == 1
        assert text.count(") <> 1") == 1


def _throw_guard_block(
    text: str,
    throw_code: str,
) -> str:
    throw_marker = f";THROW {throw_code},"
    throw_position = text.find(throw_marker)

    assert throw_position >= 0, (
        f"No se encontró {throw_marker}"
    )

    block_start = text.rfind(
        "IF NOT EXISTS (",
        0,
        throw_position,
    )

    assert block_start >= 0, (
        f"No se encontró el IF de {throw_code}"
    )

    block_end = text.find(
        "END;",
        throw_position,
    )

    assert block_end >= 0, (
        f"No se encontró el END de {throw_code}"
    )

    return text[
        block_start:block_end + len("END;")
    ]


def test_index_key_and_include_contract_is_exact():
    expected_columns_by_throw = {
        "51006": {
            "JobName": 1,
            "LockUntil": 0,
            "OwnerID": 0,
            "HeartbeatAt": 0,
        },
        "51008": {
            "JobName": 0,
            "LockUntil": 1,
            "OwnerID": 1,
            "HeartbeatAt": 1,
        },
        "51009": {
            "JobName": 0,
            "LockUntil": 0,
            "OwnerID": 1,
            "HeartbeatAt": 0,
        },
    }

    for path in (MIGRATION_PATH, VALIDATION_PATH):
        text = _read(path)

        for (
            throw_code,
            expected_columns,
        ) in expected_columns_by_throw.items():
            block = _throw_guard_block(
                text,
                throw_code,
            )

            for column_name, expected_count in (
                expected_columns.items()
            ):
                token = (
                    "AND c.name = "
                    f"N'{column_name}'"
                )

                assert (
                    block.count(token)
                    == expected_count
                ), (
                    f"{path.name}, THROW "
                    f"{throw_code}, {column_name}: "
                    f"esperado={expected_count}, "
                    f"real={block.count(token)}"
                )


def test_migration_contract_is_checked_before_commit():
    text = _read(MIGRATION_PATH)

    transaction_position = text.index(
        "BEGIN TRANSACTION;"
    )
    create_table_position = text.index(
        "CREATE TABLE dbo.Scheduler_DistributedLocks"
    )
    object_id_position = text.index(
        "DECLARE @ObjectID INT"
    )
    first_index_position = text.index(
        "CREATE NONCLUSTERED INDEX"
    )
    last_index_validation_position = text.rindex(
        "N'IX_Scheduler_DistributedLocks_OwnerID'"
    )
    commit_position = text.index(
        "COMMIT TRANSACTION;"
    )

    assert (
        transaction_position
        < create_table_position
        < object_id_position
        < first_index_position
        < last_index_validation_position
        < commit_position
    )


def test_migration_contains_only_expected_write_operations():
    text = _read(MIGRATION_PATH)

    assert MIGRATION_DISALLOWED_RE.search(text) is None

    assert (
        text.count(
            "CREATE TABLE dbo.Scheduler_DistributedLocks"
        )
        == 1
    )

    assert (
        text.count(
            "CREATE NONCLUSTERED INDEX"
        )
        == 2
    )


def test_fail_closed_throw_codes_are_stable():
    migration = _read(MIGRATION_PATH)
    validation = _read(VALIDATION_PATH)

    migration_codes = re.findall(
        r";THROW[ \t]+(510\d{2})",
        migration,
    )

    validation_codes = re.findall(
        r";THROW[ \t]+(510\d{2})",
        validation,
    )

    assert migration_codes == [
        "51003",
        "51004",
        "51005",
        "51006",
        "51007",
        "51008",
        "51009",
    ]

    assert validation_codes == [
        "51000",
        "51001",
        "51002",
        "51003",
        "51004",
        "51005",
        "51006",
        "51007",
        "51008",
        "51009",
    ]
