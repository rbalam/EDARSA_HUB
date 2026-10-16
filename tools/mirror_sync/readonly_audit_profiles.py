"""Preapproved READ_ONLY_SQL audit profiles for Universal Worker.

Profiles keep SQL out of worker queue payloads. Jobs reference only a stable
profile name; the dispatcher materializes the allow-listed SELECT statements.
"""

from __future__ import annotations

from typing import Any, Dict, List


CHAPUR_CONNECTION_DISCOVERY_V1 = "chapur_connection_discovery_v1"
CHAPUR_NORTE_OPERATIONAL_VISIBILITY_V1 = "chapur_norte_operational_visibility_v1"
API_FACTORY_PERSISTENCE_STATE_V1 = "api_factory_persistence_state_v1"

_ALLOWED = {
    CHAPUR_CONNECTION_DISCOVERY_V1,
    CHAPUR_NORTE_OPERATIONAL_VISIBILITY_V1,
    API_FACTORY_PERSISTENCE_STATE_V1,
}


def is_allowed_readonly_audit_profile(value: str) -> bool:
    return str(value or "").strip() in _ALLOWED


def build_readonly_audit_checks(profile: str) -> List[Dict[str, Any]]:
    name = str(profile or "").strip()
    if name == API_FACTORY_PERSISTENCE_STATE_V1:
        return [
            {
                "type": "sql_readonly_audit",
                "source": "EDARSAHUB",
                "max_rows": 300,
                "queries": [
                    {
                        "name": "api_factory_tables",
                        "sql": (
                            "SELECT TABLE_SCHEMA,TABLE_NAME "
                            "FROM INFORMATION_SCHEMA.TABLES "
                            "WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME IN ("
                            "'Sistema_ApiFactoryApi','Sistema_ApiFactoryVersion',"
                            "'Sistema_ApiFactoryConsumer','Sistema_ApiFactoryConsumerGrant',"
                            "'Sistema_ApiFactoryConsumerEmpresa','Sistema_ApiFactoryConsumerUnidad'"
                            ") ORDER BY TABLE_NAME"
                        ),
                    },
                    {
                        "name": "api_factory_columns",
                        "sql": (
                            "SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE,IS_NULLABLE,ORDINAL_POSITION "
                            "FROM INFORMATION_SCHEMA.COLUMNS "
                            "WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME IN ("
                            "'Sistema_ApiFactoryApi','Sistema_ApiFactoryVersion',"
                            "'Sistema_ApiFactoryConsumer','Sistema_ApiFactoryConsumerGrant',"
                            "'Sistema_ApiFactoryConsumerEmpresa','Sistema_ApiFactoryConsumerUnidad'"
                            ") ORDER BY TABLE_NAME,ORDINAL_POSITION"
                        ),
                    },
                ],
            }
        ]
    if name == CHAPUR_NORTE_OPERATIONAL_VISIBILITY_V1:
        return [
            {
                "type": "sql_readonly_audit",
                "source": "EDARSAHUB",
                "max_rows": 20,
                "queries": [
                    {
                        "name": "chapur_norte_connection",
                        "sql": (
                            "SELECT CONVERT(varchar(36),id) AS connection_id,nombre,tipo_conexion,"
                            "system_type,activo,visible_en_operaciones "
                            "FROM dbo.Servidores_Conexiones "
                            "WHERE id='d8b2d1eb-2e1f-4e43-b7d9-822bf671e315'"
                        ),
                    },
                    {
                        "name": "chapur_norte_units",
                        "sql": (
                            "SELECT CONVERT(varchar(36),id) AS unidad_negocio_pk,codigo,nombre,"
                            "CONVERT(varchar(36),server_id) AS server_id,sucursal_origen_id,system_type,activo "
                            "FROM dbo.Unidades_Negocio "
                            "WHERE server_id='d8b2d1eb-2e1f-4e43-b7d9-822bf671e315' ORDER BY id"
                        ),
                    },
                ],
            }
        ]
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
                        "name": "chapur_company_candidates",
                        "sql": (
                            "SELECT EmpresaID,CodigoEmpresa,NombreEmpresa,NombreComercial,Activo "
                            "FROM dbo.Sistema_Empresas "
                            "WHERE UPPER(ISNULL(CodigoEmpresa,'')) LIKE '%CHAPUR%' "
                            "OR UPPER(ISNULL(NombreEmpresa,'')) LIKE '%CHAPUR%' "
                            "OR UPPER(ISNULL(NombreComercial,'')) LIKE '%CHAPUR%' "
                            "ORDER BY EmpresaID"
                        ),
                    },
                    {
                        "name": "chapur_branch_candidates",
                        "sql": (
                            "SELECT s.SucursalID,s.CodigoSucursal,s.NombreSucursal,s.EmpresaID,"
                            "e.CodigoEmpresa,e.NombreEmpresa,e.NombreComercial,s.Activo "
                            "FROM dbo.Sistema_Sucursales s "
                            "LEFT JOIN dbo.Sistema_Empresas e ON e.EmpresaID=s.EmpresaID "
                            "WHERE UPPER(ISNULL(s.CodigoSucursal,'')) LIKE '%CHAPUR%' "
                            "OR UPPER(ISNULL(s.NombreSucursal,'')) LIKE '%CHAPUR%' "
                            "OR UPPER(ISNULL(s.NombreSucursal,'')) LIKE '%NORTE%' "
                            "OR UPPER(ISNULL(e.CodigoEmpresa,'')) LIKE '%CHAPUR%' "
                            "OR UPPER(ISNULL(e.NombreEmpresa,'')) LIKE '%CHAPUR%' "
                            "OR UPPER(ISNULL(e.NombreComercial,'')) LIKE '%CHAPUR%' "
                            "ORDER BY s.EmpresaID,s.SucursalID"
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
