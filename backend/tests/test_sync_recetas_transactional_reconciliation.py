from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from modules.sync_recetas import sync_recetas


def _receta(
    producto="P1",
    insumo="I1",
):
    return sync_recetas.RecetaLineaSync(
        producto_codigo_fuente=producto,
        insumo_codigo_fuente=insumo,
        insumo_nombre="INSUMO",
        cantidad=Decimal("2"),
        unidad_medida="KG",
        costo_unitario=Decimal("10"),
        costo_total=Decimal("20"),
        es_elaborado=False,
        rendimiento_elaborado=None,
    )


def _connection():
    cursor = MagicMock()

    conn = MagicMock()
    conn.cursor.return_value = cursor

    return conn, cursor


def test_transaction_commits_after_upsert_reconcile_and_recalculate():
    conn, cursor = _connection()

    result = {
        "insertados": 0,
        "actualizados": 0,
        "errores_count": 0,
        "errores": [],
    }

    recetas = [
        _receta("P1", "I1"),
        _receta("P1", "I2"),
    ]

    with patch.object(
        sync_recetas,
        "get_edarsahub_pymssql_connection",
        return_value=conn,
    ):
        sync_recetas._guardar_recetas(
            "11111111-1111-1111-1111-111111111111",
            "SOFTRESTAURANT_PRO",
            recetas,
            "RUN-001",
            result,
        )

    assert cursor.execute.call_count == 4

    sql_calls = [
        call.args[0]
        for call in cursor.execute.call_args_list
    ]

    assert "MERGE dbo.Sync_Productos_Recetas" in sql_calls[0]
    assert "Activo = 1" in sql_calls[0]

    assert "MERGE dbo.Sync_Productos_Recetas" in sql_calls[1]

    assert "Activo = 0" in sql_calls[2]
    assert "SyncRunID <> %s" in sql_calls[2]

    assert "CantidadComponentesReceta" in sql_calls[3]
    assert "rr.Activo = 1" in sql_calls[3]

    conn.commit.assert_called_once()
    conn.rollback.assert_not_called()
    conn.close.assert_called_once()

    assert result["insertados"] == 2
    assert result["errores_count"] == 0


def test_transaction_rolls_back_if_any_merge_fails():
    conn, cursor = _connection()

    cursor.execute.side_effect = [
        None,
        RuntimeError("merge failed"),
    ]

    result = {
        "insertados": 7,
        "actualizados": 0,
        "errores_count": 0,
        "errores": [],
    }

    recetas = [
        _receta("P1", "I1"),
        _receta("P1", "I2"),
    ]

    with patch.object(
        sync_recetas,
        "get_edarsahub_pymssql_connection",
        return_value=conn,
    ):
        with pytest.raises(
            RuntimeError,
            match="merge failed",
        ):
            sync_recetas._guardar_recetas(
                "11111111-1111-1111-1111-111111111111",
                "SOFTRESTAURANT_PRO",
                recetas,
                "RUN-002",
                result,
            )

    conn.commit.assert_not_called()
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()

    # No acreditar escrituras parciales después del rollback.
    assert result["insertados"] == 7

    assert result["errores_count"] == 1
    assert any(
        "merge failed" in error
        for error in result["errores"]
    )


def test_empty_valid_snapshot_reconciles_server_to_zero_recipes():
    conn, cursor = _connection()

    result = {
        "insertados": 0,
        "actualizados": 0,
        "errores_count": 0,
        "errores": [],
    }

    with patch.object(
        sync_recetas,
        "get_edarsahub_pymssql_connection",
        return_value=conn,
    ):
        sync_recetas._guardar_recetas(
            "11111111-1111-1111-1111-111111111111",
            "MPRO",
            [],
            "RUN-003",
            result,
        )

    # No MERGE; solo reconciliación + recálculo.
    assert cursor.execute.call_count == 2

    sql_calls = [
        call.args[0]
        for call in cursor.execute.call_args_list
    ]

    assert "Activo = 0" in sql_calls[0]
    assert "CantidadComponentesReceta" in sql_calls[1]

    conn.commit.assert_called_once()
    conn.rollback.assert_not_called()
    conn.close.assert_called_once()

    assert result["insertados"] == 0


def test_reactivated_line_is_marked_active_in_merge():
    conn, cursor = _connection()

    result = {
        "insertados": 0,
        "actualizados": 0,
        "errores_count": 0,
        "errores": [],
    }

    with patch.object(
        sync_recetas,
        "get_edarsahub_pymssql_connection",
        return_value=conn,
    ):
        sync_recetas._guardar_recetas(
            "11111111-1111-1111-1111-111111111111",
            "SOFTRESTAURANT_PRO",
            [_receta()],
            "RUN-004",
            result,
        )

    merge_sql = cursor.execute.call_args_list[0].args[0]

    assert "WHEN MATCHED THEN" in merge_sql
    assert "Activo = 1" in merge_sql


def test_recalculation_covers_all_products_of_server():
    conn, cursor = _connection()

    result = {
        "insertados": 0,
        "actualizados": 0,
        "errores_count": 0,
        "errores": [],
    }

    with patch.object(
        sync_recetas,
        "get_edarsahub_pymssql_connection",
        return_value=conn,
    ):
        sync_recetas._guardar_recetas(
            "11111111-1111-1111-1111-111111111111",
            "SOFTRESTAURANT_PRO",
            [_receta()],
            "RUN-005",
            result,
        )

    recalc_sql = cursor.execute.call_args_list[-1].args[0]

    assert "FROM dbo.Sync_Productos p" in recalc_sql
    assert "WHERE p.ServerID = CAST(%s AS UNIQUEIDENTIFIER)" in recalc_sql
    assert "TieneReceta" in recalc_sql
    assert "CantidadComponentesReceta" in recalc_sql
