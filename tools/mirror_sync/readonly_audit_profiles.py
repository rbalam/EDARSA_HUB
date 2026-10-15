"""Preapproved READ_ONLY_SQL audit profiles for Universal Worker.

Profiles keep SQL out of worker queue payloads. Jobs reference only a stable
profile name; the dispatcher materializes the allow-listed SELECT statements.
"""

from __future__ import annotations

from typing import Any, Dict, List


CHAPUR_CONNECTION_DISCOVERY_V1 = "chapur_connection_discovery_v1"

_ALLOWED = {
    CHAPUR_CONNECTION_DISCOVERY_V1,
}


def is_allowed_readonly_audit_profile(value: str) -> bool:
    return str(value or "").strip() in _ALLOWED


def build_readonly_audit_checks(profile: str) -> List[Dict[str, Any]]:
    name = str(profile or "").strip()
    if name == CHAPUR_CONNECTION_DISCOVERY_V1:
        return [
            {
                "type": "sql_readonly_audit",
                "source": "EDARSAHUB",
                "max_rows": 100,
                "queries": [
                    {
                        "name": "chapur_enterprise_connections",
                        "sql": (
                            "SELECT "
                            "CONVERT(varchar(36), sc.id) AS connection_id,"
                            "sc.nombre,sc.tipo_conexion,sc.system_type,"
                            "CONVERT(varchar(36), sc.sistema_version_id) AS sistema_version_id,"
                            "sc.activo,sc.visible_en_operaciones,sc.EmpresaID,sc.empresa_id "
                            "FROM dbo.Servidores_Conexiones sc "
                            "WHERE UPPER(ISNULL(sc.nombre,'')) LIKE '%CHAPUR%' "
                            "OR UPPER(ISNULL(sc.system_type,''))='ENTERPRISE' "
                            "ORDER BY sc.nombre"
                        ),
                    },
                    {
                        "name": "chapur_units",
                        "sql": (
                            "SELECT "
                            "CONVERT(varchar(36), u.id) AS unidad_negocio_pk,"
                            "u.codigo,u.nombre,u.sucursal_origen_id,u.system_type,"
                            "CONVERT(varchar(36), u.server_id) AS server_id,u.activo "
                            "FROM dbo.Unidades_Negocio u "
                            "WHERE UPPER(ISNULL(u.nombre,'')) LIKE '%CHAPUR%' "
                            "OR CONVERT(varchar(36), u.server_id) IN ("
                            "SELECT CONVERT(varchar(36), sc.id) "
                            "FROM dbo.Servidores_Conexiones sc "
                            "WHERE UPPER(ISNULL(sc.nombre,'')) LIKE '%CHAPUR%' "
                            "OR UPPER(ISNULL(sc.system_type,''))='ENTERPRISE'"
                            ") ORDER BY u.nombre"
                        ),
                    },
                    {
                        "name": "chapur_versions",
                        "sql": (
                            "SELECT "
                            "CONVERT(varchar(36), v.sistema_version_id) AS sistema_version_id,"
                            "v.tipo_sistema,v.nombre_sistema,v.version_sistema,"
                            "v.proveedor,v.motor_base_datos,v.es_version_default,v.activo "
                            "FROM dbo.Sistema_VersionesSistemas v "
                            "WHERE UPPER(ISNULL(v.tipo_sistema,''))='ENTERPRISE' "
                            "OR UPPER(ISNULL(v.nombre_sistema,'')) LIKE '%ENTERPRISE%' "
                            "ORDER BY v.version_sistema"
                        ),
                    },
                ],
            }
        ]
    raise ValueError("READ_ONLY_SQL_AUDIT_PROFILE_INVALID")
