"""Lecturas SQL canonicas para la fachada administrativa Gate 5B.

Este repositorio NO administra conexiones ni ejecuta sincronizaciones. Solo compone
health, catalogos y resumenes desde objetos SQL ya existentes.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection


def _rows(sql: str, params: tuple = ()) -> List[Dict]:
    conn = get_edarsahub_pymssql_connection(timeout=30, login_timeout=10)
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, params)
        return cur.fetchall() or []
    finally:
        conn.close()


def _id_key(value) -> str:
    return str(value or "").strip().lower()


def get_latest_health_map(connection_ids: Iterable[str]) -> Dict[str, Dict]:
    ids = [str(value) for value in connection_ids if value]
    if not ids:
        return {}

    placeholders = ",".join(["%s"] * len(ids))
    sql = f"""
        WITH ranked AS (
            SELECT
                COALESCE(CONVERT(varchar(36), ServidorID), ServerID) AS connection_id,
                EstadoConexion,
                UltimoCheck,
                COALESCE(LatenciaMs, ResponseTimeMs) AS LatenciaMs,
                UltimaPruebaUTC,
                UltimoExitoUTC,
                UltimoErrorUTC,
                UltimoErrorCodigo,
                UltimoErrorMensaje,
                UltimoSyncUTC,
                UltimoSyncExitosoUTC,
                FechaActualizacionUTC,
                ROW_NUMBER() OVER (
                    PARTITION BY COALESCE(CONVERT(varchar(36), ServidorID), ServerID)
                    ORDER BY COALESCE(FechaActualizacionUTC, UltimaPruebaUTC, UltimoCheck) DESC
                ) AS rn
            FROM dbo.Servidores_ConexionEstado
            WHERE COALESCE(CONVERT(varchar(36), ServidorID), ServerID) IN ({placeholders})
        )
        SELECT
            connection_id,
            EstadoConexion,
            UltimoCheck,
            LatenciaMs,
            UltimaPruebaUTC,
            UltimoExitoUTC,
            UltimoErrorUTC,
            UltimoErrorCodigo,
            UltimoErrorMensaje,
            UltimoSyncUTC,
            UltimoSyncExitosoUTC,
            FechaActualizacionUTC
        FROM ranked
        WHERE rn = 1
    """
    rows = _rows(sql, tuple(ids))
    return {_id_key(row["connection_id"]): row for row in rows if row.get("connection_id")}


def get_connection_enrichment(connection_ids: Iterable[str]) -> Dict[str, Dict]:
    ids = [str(value) for value in connection_ids if value]
    if not ids:
        return {}

    placeholders = ",".join(["%s"] * len(ids))
    sql = f"""
        SELECT
            CONVERT(varchar(36), id) AS connection_id,
            CONVERT(varchar(36), sistema_version_id) AS sistema_version_id,
            EmpresaID,
            empresa_id
        FROM dbo.Servidores_Conexiones
        WHERE CONVERT(varchar(36), id) IN ({placeholders})
    """
    rows = _rows(sql, tuple(ids))
    return {_id_key(row["connection_id"]): row for row in rows if row.get("connection_id")}


def get_sync_summary() -> Dict:
    rows = _rows("""
        SELECT
            COUNT_BIG(*) AS total_runs,
            SUM(CASE WHEN Status = 'IN_PROGRESS' THEN 1 ELSE 0 END) AS running_runs,
            SUM(CASE WHEN ConexionID IS NOT NULL THEN 1 ELSE 0 END) AS contextualized_runs,
            SUM(CASE WHEN IdempotencyKey IS NOT NULL THEN 1 ELSE 0 END) AS idempotent_runs,
            MAX(COALESCE(FinishedAtUTC, CAST(FinishedAtMexico AS datetime2))) AS last_finished_at
        FROM dbo.Sync_Control_Ejecuciones
    """)
    row = rows[0] if rows else {}
    return {
        "total_runs": int(row.get("total_runs") or 0),
        "running_runs": int(row.get("running_runs") or 0),
        "contextualized_runs": int(row.get("contextualized_runs") or 0),
        "idempotent_runs": int(row.get("idempotent_runs") or 0),
        "last_finished_at": row.get("last_finished_at"),
    }


def get_universal_infra_summary() -> Dict:
    row = (_rows("""
        SELECT
            (SELECT COUNT_BIG(*) FROM dbo.Sistema_Sync_Capacidades) AS sync_capability_links,
            (SELECT COUNT_BIG(*) FROM dbo.Sync_Control_Evidencias) AS evidence_rows,
            (SELECT COUNT_BIG(*) FROM dbo.Sistema_IdentificadoresExternos) AS external_id_rows,
            (SELECT COUNT_BIG(*) FROM dbo.Unidades_Negocio) AS total_units,
            (SELECT COUNT_BIG(*) FROM dbo.Unidades_Negocio
              WHERE NULLIF(LTRIM(RTRIM(timezone_iana)), '') IS NOT NULL) AS units_with_timezone,
            (SELECT COUNT_BIG(*) FROM dbo.Unidades_Negocio
              WHERE NULLIF(LTRIM(RTRIM(locale_operativo)), '') IS NOT NULL) AS units_with_locale
    """) or [{}])[0]
    return {key: int(value or 0) for key, value in row.items()}


def get_catalogs() -> Dict[str, List[Dict]]:
    systems = _rows("""
        SELECT SistemaTipoID, CodigoSistema, NombreSistema, Descripcion, Activo
        FROM dbo.Sistema_Tipos
        ORDER BY SistemaTipoID
    """)
    versions = _rows("""
        SELECT
            CONVERT(varchar(36), sistema_version_id) AS sistema_version_id,
            tipo_sistema,
            nombre_sistema,
            version_sistema,
            descripcion,
            proveedor,
            motor_base_datos,
            es_version_default,
            activo,
            created_at
        FROM dbo.Sistema_VersionesSistemas
        ORDER BY tipo_sistema, version_sistema
    """)
    capabilities = _rows("""
        SELECT
            SistemaCapacidadID,
            SistemaTipoID,
            CodigoCapacidad,
            Descripcion,
            RequiereApiLocal,
            RequiereSqlDirecto,
            Activo
        FROM dbo.Sistema_Capacidades
        ORDER BY SistemaTipoID, CodigoCapacidad
    """)
    syncs = _rows("""
        SELECT
            Codigo,
            Nombre,
            Grupo,
            Descripcion,
            NivelRiesgo,
            PermiteResync,
            PermiteDryRun,
            RequiereUnidad,
            RequiereRangoFechas,
            HandlerImplementado,
            TablaDestino,
            Activo
        FROM dbo.Sistema_Sync_Catalogo
        ORDER BY Orden, Codigo
    """)
    links = _rows("""
        SELECT
            SyncCapacidadID,
            CodigoSync,
            SistemaCapacidadID,
            Obligatoria,
            Activo
        FROM dbo.Sistema_Sync_Capacidades
        ORDER BY CodigoSync, SistemaCapacidadID
    """)
    return {
        "systems": systems,
        "versions": versions,
        "capabilities": capabilities,
        "sync_catalog": syncs,
        "sync_capabilities": links,
    }


def get_communications_summary() -> Dict:
    config_rows = _rows("SELECT COUNT_BIG(*) AS total FROM dbo.Sistema_NotificacionesConfig")
    log_rows = _rows("SELECT COUNT_BIG(*) AS total FROM dbo.Operativo_Notificaciones_Log")
    by_status = _rows("""
        SELECT Canal, Estado, COUNT_BIG(*) AS total
        FROM dbo.Operativo_Notificaciones_Log
        GROUP BY Canal, Estado
        ORDER BY Canal, Estado
    """)
    return {
        "config_rows": int((config_rows[0] if config_rows else {}).get("total") or 0),
        "log_rows": int((log_rows[0] if log_rows else {}).get("total") or 0),
        "by_channel_status": by_status,
        "config_source": "dbo.Sistema_NotificacionesConfig",
        "log_source": "dbo.Operativo_Notificaciones_Log",
        "provider_runtime": "backend/core/communications",
    }
