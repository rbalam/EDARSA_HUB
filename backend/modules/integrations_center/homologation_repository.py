"""Read-only repository for integration homologation state.

All reads use the canonical HRLectura read-only connection. Before the H5
migration is executed, this repository returns an empty map instead of making
Integrations Center fail.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from core.sql_first.db import fetch_all_dict_readonly, fetch_one_dict_readonly


_PROFILE_TABLE = "dbo.Sistema_IntegracionHomologacionPerfil"
_DOMAIN_TABLE = "dbo.Sistema_IntegracionHomologacionDominio"
_BINDING_TABLE = "dbo.Sistema_IntegracionHomologacionBinding"


def _id_key(value) -> str:
    return str(value or "").strip().lower()


def persistence_available() -> bool:
    row = fetch_one_dict_readonly(
        """
        SELECT
            OBJECT_ID(%s, 'U') AS perfil,
            OBJECT_ID(%s, 'U') AS dominio,
            OBJECT_ID(%s, 'U') AS binding
        """,
        [_PROFILE_TABLE, _DOMAIN_TABLE, _BINDING_TABLE],
    )
    return bool(
        row
        and row.get("perfil")
        and row.get("dominio")
        and row.get("binding")
    )


def get_connection_homologation_map(
    connection_ids: Iterable[str],
) -> Dict[str, Dict]:
    ids = [str(value).strip() for value in connection_ids if value]
    if not ids or not persistence_available():
        return {}

    placeholders = ",".join(["%s"] * len(ids))

    rows = fetch_all_dict_readonly(
        f"""
        SELECT
            CONVERT(varchar(36), b.ConnectionID) AS connection_id,
            CONVERT(varchar(36), b.HomologacionPerfilID) AS profile_id,
            b.CertificationSource AS certification_source,
            b.ObservedSchemaFingerprint AS observed_schema_fingerprint,
            b.Estado AS binding_status,
            b.BoundAtUTC AS bound_at_utc,
            b.LastValidatedAtUTC AS binding_last_validated_at_utc,

            p.CodigoPerfil AS profile_code,
            p.SystemType AS system_type,
            p.TransportType AS transport_type,
            p.SourceContractVersion AS source_contract_version,
            p.EdarsahubContractVersion AS edarsahub_contract_version,
            p.SchemaFingerprint AS schema_fingerprint,
            p.Estado AS profile_status,
            p.CertifiedAtUTC AS certified_at_utc,
            p.LastValidatedAtUTC AS profile_last_validated_at_utc
        FROM {_BINDING_TABLE} b
        INNER JOIN {_PROFILE_TABLE} p
            ON p.HomologacionPerfilID = b.HomologacionPerfilID
           AND p.Activo = 1
        WHERE b.Activo = 1
          AND CONVERT(varchar(36), b.ConnectionID) IN ({placeholders})
        """,
        ids,
    )

    if not rows:
        return {}

    profile_ids = list({
        str(row.get("profile_id") or "").strip()
        for row in rows
        if row.get("profile_id")
    })

    domains_by_profile: Dict[str, List[Dict]] = {}
    if profile_ids:
        profile_placeholders = ",".join(["%s"] * len(profile_ids))
        domain_rows = fetch_all_dict_readonly(
            f"""
            SELECT
                CONVERT(varchar(36), HomologacionPerfilID) AS profile_id,
                DominioCodigo AS domain,
                Estado AS status,
                SourceContractVersion AS source_contract_version,
                EdarsahubContractVersion AS edarsahub_contract_version,
                MappingVersion AS mapping_version,
                CertifiedAtUTC AS certified_at_utc
            FROM {_DOMAIN_TABLE}
            WHERE Activo = 1
              AND CONVERT(varchar(36), HomologacionPerfilID)
                  IN ({profile_placeholders})
            ORDER BY DominioCodigo
            """,
            profile_ids,
        )
        for row in domain_rows:
            key = _id_key(row.get("profile_id"))
            domains_by_profile.setdefault(key, []).append(
                {
                    "domain": row.get("domain"),
                    "status": row.get("status"),
                    "source_contract_version": row.get(
                        "source_contract_version"
                    ),
                    "edarsahub_contract_version": row.get(
                        "edarsahub_contract_version"
                    ),
                    "mapping_version": row.get("mapping_version"),
                    "certified_at_utc": row.get("certified_at_utc"),
                }
            )

    result: Dict[str, Dict] = {}
    for row in rows:
        connection_key = _id_key(row.get("connection_id"))
        profile_key = _id_key(row.get("profile_id"))
        if not connection_key:
            continue

        result[connection_key] = {
            "status": row.get("binding_status")
            or row.get("profile_status")
            or "NOT_ASSESSED",
            "profile_id": row.get("profile_id"),
            "profile_code": row.get("profile_code"),
            "certification_source": row.get("certification_source"),
            "schema_fingerprint": row.get("schema_fingerprint"),
            "observed_schema_fingerprint": row.get(
                "observed_schema_fingerprint"
            ),
            "system_type": row.get("system_type"),
            "transport_type": row.get("transport_type"),
            "source_contract_version": row.get(
                "source_contract_version"
            ),
            "edarsahub_contract_version": row.get(
                "edarsahub_contract_version"
            ),
            "certified_at_utc": row.get("certified_at_utc"),
            "bound_at_utc": row.get("bound_at_utc"),
            "last_validated_at_utc": (
                row.get("binding_last_validated_at_utc")
                or row.get("profile_last_validated_at_utc")
            ),
            "domains": domains_by_profile.get(profile_key, []),
        }

    return result
