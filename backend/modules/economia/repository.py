"""
Repository SQL canónico para Economía.

Reglas:
- EDARSAHUB SQL únicamente.
- Sin MongoDB.
- Sin conexiones LIVE externas.
- Sin connection manager paralelo.
- Consultas parametrizadas.
"""

import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Sequence, Tuple

from core.db import execute_sql_query_params
from core.sql_first.db import sql_connection


def _conn() -> Tuple[str, int, str, str, str]:
    """
    Resuelve exclusivamente la configuración EDARSAHUB ya inyectada
    en el runtime.

    No contiene credenciales ni valores de negocio hardcodeados.
    """
    host = os.getenv("EDARSAHUB_SQL_HOST")
    port_raw = os.getenv("EDARSAHUB_SQL_PORT")
    database = os.getenv("EDARSAHUB_SQL_DATABASE")
    username = os.getenv("EDARSAHUB_SQL_USER")
    password = os.getenv("EDARSAHUB_SQL_PASSWORD")

    missing = [
        name
        for name, value in (
            ("EDARSAHUB_SQL_HOST", host),
            ("EDARSAHUB_SQL_PORT", port_raw),
            ("EDARSAHUB_SQL_DATABASE", database),
            ("EDARSAHUB_SQL_USER", username),
            ("EDARSAHUB_SQL_PASSWORD", password),
        )
        if value in (None, "")
    ]

    if missing:
        raise RuntimeError(
            "Configuracion SQL EDARSAHUB incompleta: "
            + ", ".join(missing)
        )

    try:
        port = int(port_raw)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "EDARSAHUB_SQL_PORT invalido"
        ) from exc

    return host, port, database, username, password


def _query(
    sql: str,
    params: Sequence[Any] = (),
) -> List[Dict[str, Any]]:
    rows = execute_sql_query_params(
        *_conn(),
        sql,
        tuple(params),
    )
    return rows or []




_SQL_DECIMAL_28_10_QUANT = Decimal("0.0000000001")


def _canonical_decimal_28_10(value):
    """
    Normaliza valores económicos al contrato SQL decimal(28,10).

    Evita crear revisiones falsas por ruido de precisión binaria/
    conversión externa más allá de los 10 decimales persistibles.
    """
    try:
        return Decimal(str(value)).quantize(
            _SQL_DECIMAL_28_10_QUANT,
            rounding=ROUND_HALF_UP,
        )
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "valor económico inválido"
        ) from exc


def _persistir_valor_versionado(
    serie_id,
    fecha_periodo,
    valor,
    *,
    periodo_codigo=None,
    preliminar=False,
    estimado=False,
    fecha_publicacion=None,
    fuente_dato_id=None,
    hash_fuente=None,
    metadata_json=None,
    sync_run_id=None,
    connection=None,
):
    """
    Persiste una observación económica sin sobrescribir historia.

    - mismo valor vigente: no crea versión;
    - valor distinto: crea VersionDato + 1;
    - sin connection externa, administra su propia transacción;
    - con connection externa, participa en la transacción del caller.
    """
    owns_connection = connection is None

    if owns_connection:
        context = sql_connection()
        conn = context.__enter__()
    else:
        context = None
        conn = connection

    try:
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT TOP (1)
                    ValorEconomicoID,
                    Valor,
                    VersionDato
                FROM dbo.Economia_Valores WITH (UPDLOCK, HOLDLOCK)
                WHERE SerieEconomicaID = %s
                  AND FechaPeriodo = %s
                  AND Activo = 1
                ORDER BY VersionDato DESC
                """,
                (serie_id, fecha_periodo),
            )

            actual = cursor.fetchone()

            if actual is not None:
                valor_actual = actual[1]
                version_actual = int(actual[2])

                valor_actual_canonico = (
                    _canonical_decimal_28_10(
                        valor_actual
                    )
                )
                valor_nuevo_canonico = (
                    _canonical_decimal_28_10(
                        valor
                    )
                )

                if (
                    valor_actual_canonico
                    == valor_nuevo_canonico
                ):
                    if owns_connection:
                        conn.commit()

                    return {
                        "insertado": False,
                        "version_dato": version_actual,
                        "es_revision": False,
                    }

                nueva_version = version_actual + 1
                es_revision = True
                valor_anterior = valor_actual

                cursor.execute(
                    """
                    UPDATE dbo.Economia_Valores
                    SET Activo = 0,
                        FechaVigenciaHasta = SYSUTCDATETIME()
                    WHERE SerieEconomicaID = %s
                      AND FechaPeriodo = %s
                      AND Activo = 1
                    """,
                    (serie_id, fecha_periodo),
                )
            else:
                nueva_version = 1
                es_revision = False
                valor_anterior = None

            cursor.execute(
                """
                INSERT INTO dbo.Economia_Valores
                (
                    SerieEconomicaID,
                    FechaPeriodo,
                    PeriodoCodigo,
                    Valor,
                    VersionDato,
                    EsRevision,
                    EsDatoPreliminar,
                    EsDatoEstimado,
                    FechaPublicacion,
                    FechaVigenciaDesde,
                    ValorAnterior,
                    FuenteDatoID,
                    HashFuente,
                    MetadataJSON,
                    SyncRunID,
                    Activo
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, SYSUTCDATETIME(), %s, %s, %s, %s, %s, 1
                )
                """,
                (
                    serie_id,
                    fecha_periodo,
                    periodo_codigo,
                    valor,
                    nueva_version,
                    1 if es_revision else 0,
                    1 if preliminar else 0,
                    1 if estimado else 0,
                    fecha_publicacion,
                    valor_anterior,
                    fuente_dato_id,
                    hash_fuente,
                    metadata_json,
                    sync_run_id,
                ),
            )

            if owns_connection:
                conn.commit()

            return {
                "insertado": True,
                "version_dato": nueva_version,
                "es_revision": es_revision,
            }

        except Exception:
            if owns_connection:
                conn.rollback()
            raise
    finally:
        if owns_connection and context is not None:
            context.__exit__(None, None, None)


class EconomiaRepository:
    """Acceso SQL mínimo al dominio Economía."""

    @staticmethod
    def persistir_valor_versionado(
        serie_id,
        fecha_periodo,
        valor,
        **kwargs,
    ):
        return _persistir_valor_versionado(
            serie_id,
            fecha_periodo,
            valor,
            **kwargs,
        )


    @staticmethod
    def resolver_proveedor_serie(
        serie_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Resuelve la configuración canónica de proveedor de una serie.

        Cadena única:
        Economia_Series
        -> Economia_Proveedores
        -> Servidores_Conexiones.

        No descifra secretos y no realiza HTTP.
        """
        sql = """
        SELECT
            s.SerieEconomicaID AS serie_id,
            s.CodigoCanonico AS codigo_canonico,
            s.CodigoProveedor AS codigo_proveedor,
            s.MetadataJSON AS metadata_json,

            p.ProveedorEconomicoID AS proveedor_id,
            p.Codigo AS proveedor_codigo,
            p.Nombre AS proveedor_nombre,
            p.TipoProveedor AS proveedor_tipo,
            p.ServerConexionID AS server_conexion_id,
            p.UrlPublica AS url_publica,
            p.RequiereAutenticacion AS requiere_autenticacion,
            p.PermiteBackfill AS permite_backfill,

            sc.id AS conexion_id,
            sc.nombre AS conexion_nombre,
            sc.api_url AS conexion_url,
            sc.api_key_encrypted AS api_key_encrypted,
            sc.tipo_conexion AS tipo_conexion,
            sc.system_type AS system_type,
            sc.activo AS conexion_activa

        FROM dbo.Economia_Series s
        INNER JOIN dbo.Economia_Proveedores p
            ON p.ProveedorEconomicoID = s.ProveedorEconomicoID
        LEFT JOIN dbo.Servidores_Conexiones sc
            ON sc.id = p.ServerConexionID

        WHERE s.SerieEconomicaID = %s
          AND s.Activo = 1
          AND p.Activo = 1
        """

        rows = _query(sql, (serie_id,))

        return rows[0] if rows else None

    @staticmethod
    def listar_series(
        activo: Optional[bool] = True,
        limite: int = 500,
    ) -> List[Dict[str, Any]]:
        conditions = []
        params: List[Any] = [limite]

        if activo is not None:
            conditions.append("s.Activo = %s")
            params.append(1 if activo else 0)

        where = (
            "WHERE " + " AND ".join(conditions)
            if conditions
            else ""
        )

        sql = f"""
        SELECT TOP (%s)
            s.SerieEconomicaID AS id,
            s.CodigoCanonico AS codigo_canonico,
            s.Nombre AS nombre,
            s.UnidadMedidaCodigo AS unidad_medida,
            s.FrecuenciaCodigo AS frecuencia,
            s.Activo AS activo
        FROM dbo.Economia_Series s
        {where}
        ORDER BY s.CodigoCanonico
        """

        return _query(sql, params)

    @staticmethod
    def obtener_serie(
        serie_id: str,
    ) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT
            s.SerieEconomicaID AS id,
            s.CodigoCanonico AS codigo_canonico,
            s.Nombre AS nombre,
            s.UnidadMedidaCodigo AS unidad_medida,
            s.FrecuenciaCodigo AS frecuencia,
            s.Activo AS activo
        FROM dbo.Economia_Series s
        WHERE s.SerieEconomicaID = %s
        """

        rows = _query(sql, (serie_id,))
        return rows[0] if rows else None

    @staticmethod
    def listar_valores(
        serie_id: str,
        desde=None,
        hasta=None,
        limite: int = 500,
    ) -> List[Dict[str, Any]]:
        conditions = [
            "v.SerieEconomicaID = %s",
            "v.Activo = 1",
        ]
        params: List[Any] = [serie_id]

        if desde is not None:
            conditions.append("v.FechaPeriodo >= %s")
            params.append(desde)

        if hasta is not None:
            conditions.append("v.FechaPeriodo <= %s")
            params.append(hasta)

        params.append(limite)

        sql = f"""
        SELECT TOP (%s)
            v.SerieEconomicaID AS serie_id,
            v.FechaPeriodo AS periodo,
            v.Valor AS valor,
            v.VersionDato AS version_dato,
            v.EsRevision AS es_revision,
            v.EsDatoPreliminar AS preliminar,
            v.EsDatoEstimado AS estimado
        FROM dbo.Economia_Valores v
        WHERE {' AND '.join(conditions)}
        ORDER BY v.FechaPeriodo DESC, v.VersionDato DESC
        """

        return _query(sql, params)

    @staticmethod
    def listar_contextos_activos() -> List[Dict[str, Any]]:
        sql = """
        SELECT
            c.ContextoEconomicoID AS id,
            CONVERT(varchar(36), c.PaisID) AS pais_id,
            c.EmpresaID AS empresa_id,
            CONVERT(varchar(36), c.UnidadNegocioID)
                AS unidad_negocio_id,
            c.MonedaID AS moneda_id,
            c.EsPrincipal AS principal,
            c.Activo AS activo
        FROM dbo.Economia_ContextoOperativo c
        WHERE c.Activo = 1
        ORDER BY
            c.EsPrincipal DESC,
            c.EmpresaID,
            c.UnidadNegocioID
        """

        return _query(sql)
