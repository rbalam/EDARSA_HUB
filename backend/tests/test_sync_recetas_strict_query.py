from unittest.mock import MagicMock, patch

import pytest

from modules.sync_recetas import sync_recetas


def _connection_with_rows(rows):
    cursor = MagicMock()
    cursor.fetchall.return_value = rows

    connection = MagicMock()
    connection.cursor.return_value = cursor

    return connection, cursor


def test_strict_query_empty_is_valid_empty_result():
    connection, cursor = _connection_with_rows([])

    with patch.object(
        sync_recetas,
        "get_external_sql_connection",
        return_value=connection,
    ):
        result = sync_recetas._execute_pos_query_strict(
            "host",
            1433,
            "database",
            "username",
            "password",
            "SELECT 1 WHERE 1 = 0",
        )

    assert result == []
    cursor.execute.assert_called_once()
    connection.close.assert_called_once()


def test_strict_query_propagates_connection_error():
    with patch.object(
        sync_recetas,
        "get_external_sql_connection",
        side_effect=RuntimeError("POS unavailable"),
    ):
        with pytest.raises(
            RuntimeError,
            match="POS unavailable",
        ):
            sync_recetas._execute_pos_query_strict(
                "host",
                1433,
                "database",
                "username",
                "password",
                "SELECT 1",
            )


def test_strict_query_propagates_query_error():
    connection, cursor = _connection_with_rows([])

    cursor.execute.side_effect = RuntimeError(
        "query failed"
    )

    with patch.object(
        sync_recetas,
        "get_external_sql_connection",
        return_value=connection,
    ):
        with pytest.raises(
            RuntimeError,
            match="query failed",
        ):
            sync_recetas._execute_pos_query_strict(
                "host",
                1433,
                "database",
                "username",
                "password",
                "SELECT broken",
            )

    connection.close.assert_called_once()


def test_strict_query_preserves_dict_rows():
    rows = [
        {
            "idproducto": "P1",
            "idinsumo": "I1",
        }
    ]

    connection, cursor = _connection_with_rows(
        rows
    )

    with patch.object(
        sync_recetas,
        "get_external_sql_connection",
        return_value=connection,
    ):
        result = sync_recetas._execute_pos_query_strict(
            "host",
            1433,
            "database",
            "username",
            "password",
            "SELECT ...",
        )

    assert result == rows
    cursor.execute.assert_called_once()
    connection.close.assert_called_once()
