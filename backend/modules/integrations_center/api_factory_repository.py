"""Read-only persistence adapter for API Factory H8.

Source of truth: EDARSAHUB SQL tables created by the canonical H8 migration.
This module exposes no writers and never returns credential material.
"""

from __future__ import annotations

from typing import Dict, List

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection


def _rows(sql: str, params: tuple = ()) -> List[Dict]:
    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params)
        return cur.fetchall() or []
    finally:
        conn.close()


def get_overview() -> Dict:
    row = (_rows("""
        SELECT
            (SELECT COUNT_BIG(*) FROM dbo.Sistema_ApiFactoryApi WHERE Activo = 1) AS apis,
            (SELECT COUNT_BIG(*) FROM dbo.Sistema_ApiFactoryVersion WHERE Activo = 1) AS versions,
            (SELECT COUNT_BIG(*) FROM dbo.Sistema_ApiFactoryConsumer WHERE Activo = 1) AS consumers,
            (SELECT COUNT_BIG(*) FROM dbo.Sistema_ApiFactoryConsumerGrant WHERE Activo = 1) AS grants
    """) or [{}])[0]
    return {key: int(value or 0) for key, value in row.items()}


def list_apis() -> List[Dict]:
    return _rows("""
        SELECT
            CONVERT(varchar(36), a.ApiID) AS api_id,
            a.ApiCode AS api_code,
            a.Nombre AS name,
            a.Estado AS status,
            a.AuthMode AS auth_mode,
            a.Activo AS active,
            a.FechaCreacionUTC AS created_at_utc,
            a.FechaActualizacionUTC AS updated_at_utc,
            COUNT(v.ApiVersionID) AS version_count
        FROM dbo.Sistema_ApiFactoryApi a
        LEFT JOIN dbo.Sistema_ApiFactoryVersion v
            ON v.ApiID = a.ApiID
           AND v.Activo = 1
        GROUP BY
            a.ApiID,a.ApiCode,a.Nombre,a.Estado,a.AuthMode,a.Activo,
            a.FechaCreacionUTC,a.FechaActualizacionUTC
        ORDER BY a.ApiCode
    """)


def list_versions(api_id: str) -> List[Dict]:
    return _rows("""
        SELECT
            CONVERT(varchar(36), ApiVersionID) AS api_version_id,
            CONVERT(varchar(36), ApiID) AS api_id,
            VersionCode AS version_code,
            Route AS route,
            HttpMethod AS http_method,
            ContractFingerprint AS contract_fingerprint,
            InputSchemaVersion AS input_schema_version,
            OutputSchemaVersion AS output_schema_version,
            RateLimitPerMinute AS rate_limit_per_minute,
            Immutable AS immutable,
            Activo AS active,
            FechaCreacionUTC AS created_at_utc
        FROM dbo.Sistema_ApiFactoryVersion
        WHERE ApiID = CONVERT(uniqueidentifier, %s)
        ORDER BY FechaCreacionUTC DESC
    """, (api_id,))


def list_consumers() -> List[Dict]:
    return _rows("""
        SELECT
            CONVERT(varchar(36), c.ConsumerID) AS consumer_id,
            c.ConsumerCode AS consumer_code,
            c.Nombre AS name,
            c.Estado AS status,
            c.Activo AS active,
            c.FechaCreacionUTC AS created_at_utc,
            c.FechaActualizacionUTC AS updated_at_utc,
            COUNT(g.ConsumerGrantID) AS grant_count
        FROM dbo.Sistema_ApiFactoryConsumer c
        LEFT JOIN dbo.Sistema_ApiFactoryConsumerGrant g
            ON g.ConsumerID = c.ConsumerID
           AND g.Activo = 1
        GROUP BY
            c.ConsumerID,c.ConsumerCode,c.Nombre,c.Estado,c.Activo,
            c.FechaCreacionUTC,c.FechaActualizacionUTC
        ORDER BY c.ConsumerCode
    """)


def list_consumer_grants(consumer_id: str) -> List[Dict]:
    return _rows("""
        SELECT
            g.ConsumerGrantID AS consumer_grant_id,
            CONVERT(varchar(36), g.ConsumerID) AS consumer_id,
            CONVERT(varchar(36), g.ApiVersionID) AS api_version_id,
            a.ApiCode AS api_code,
            v.VersionCode AS api_version,
            a.AuthMode AS auth_mode,
            g.RateLimitPerMinute AS rate_limit_per_minute,
            g.Activo AS active,
            g.FechaCreacionUTC AS created_at_utc
        FROM dbo.Sistema_ApiFactoryConsumerGrant g
        INNER JOIN dbo.Sistema_ApiFactoryVersion v ON v.ApiVersionID = g.ApiVersionID
        INNER JOIN dbo.Sistema_ApiFactoryApi a ON a.ApiID = v.ApiID
        WHERE g.ConsumerID = CONVERT(uniqueidentifier, %s)
        ORDER BY a.ApiCode,v.VersionCode
    """, (consumer_id,))
