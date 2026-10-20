"""Preapproved READ_ONLY_SQL audit profiles for Universal Worker.

Profiles keep SQL out of worker queue payloads. Jobs reference only a stable
profile name; the dispatcher materializes the allow-listed SELECT statements.
"""

from __future__ import annotations

from typing import Any, Dict, List


CHAPUR_CONNECTION_DISCOVERY_V1 = "chapur_connection_discovery_v1"
CHAPUR_NORTE_OPERATIONAL_VISIBILITY_V1 = "chapur_norte_operational_visibility_v1"
API_FACTORY_PERSISTENCE_STATE_V1 = "api_factory_persistence_state_v1"
CHAPUR_EXTERNAL_INTEGRATION_READINESS_V1 = "chapur_external_integration_readiness_v1"
SQL_RUNTIME_PRINCIPAL_PERMISSIONS_V1 = "sql_runtime_principal_permissions_v1"

_ALLOWED = {
    CHAPUR_CONNECTION_DISCOVERY_V1,
    CHAPUR_NORTE_OPERATIONAL_VISIBILITY_V1,
    API_FACTORY_PERSISTENCE_STATE_V1,
    CHAPUR_EXTERNAL_INTEGRATION_READINESS_V1,
    SQL_RUNTIME_PRINCIPAL_PERMISSIONS_V1,
}


def is_allowed_readonly_audit_profile(value: str) -> bool:
    return str(value or "").strip() in _ALLOWED


def build_readonly_audit_checks(profile: str) -> List[Dict[str, Any]]:
    name = str(profile or "").strip()
    if name == SQL_RUNTIME_PRINCIPAL_PERMISSIONS_V1:
        return [
            {
                "type": "sql_readonly_audit",
                "source": "EDARSAHUB",
                "max_rows": 200,
                "queries": [
                    {
                        "name": "sql_runtime_principals",
                        "sql": (
                            "SELECT p.name,p.type_desc,p.authentication_type_desc,"
                            "p.default_schema_name,SUSER_SNAME(p.sid) AS login_name "
                            "FROM sys.database_principals p "
                            "WHERE p.name IN ('HRLectura','ChatGPT_Escritura','HUB_Escritura','GptEscritura') "
                            "ORDER BY p.name"
                        ),
                    },
                    {
                        "name": "sql_runtime_role_memberships",
                        "sql": (
                            "SELECT m.name AS member_name,r.name AS role_name "
                            "FROM sys.database_role_members drm "
                            "JOIN sys.database_principals r ON r.principal_id=drm.role_principal_id "
                            "JOIN sys.database_principals m ON m.principal_id=drm.member_principal_id "
                            "WHERE m.name IN ('HRLectura','ChatGPT_Escritura','HUB_Escritura','GptEscritura') "
                            "ORDER BY m.name,r.name"
                        ),
                    },
                    {
                        "name": "sql_runtime_explicit_permissions",
                        "sql": (
                            "SELECT grantee.name AS principal_name,dp.state_desc,dp.permission_name,dp.class_desc,"
                            "CASE dp.class WHEN 0 THEN DB_NAME() "
                            "WHEN 1 THEN COALESCE(QUOTENAME(OBJECT_SCHEMA_NAME(dp.major_id))+'.'+QUOTENAME(OBJECT_NAME(dp.major_id)),CONVERT(varchar(50),dp.major_id)) "
                            "WHEN 3 THEN SCHEMA_NAME(dp.major_id) ELSE CONVERT(varchar(50),dp.major_id) END AS securable_name "
                            "FROM sys.database_permissions dp "
                            "JOIN sys.database_principals grantee ON grantee.principal_id=dp.grantee_principal_id "
                            "WHERE grantee.name IN ('HRLectura','ChatGPT_Escritura','HUB_Escritura','GptEscritura') "
                            "ORDER BY grantee.name,dp.class_desc,securable_name,dp.permission_name"
                        ),
                    },
                    {
                        "name": "sql_runtime_inherited_role_permissions",
                        "sql": (
                            "SELECT m.name AS member_name,r.name AS role_name,dp.state_desc,dp.permission_name,dp.class_desc,"
                            "CASE dp.class WHEN 0 THEN DB_NAME() "
                            "WHEN 1 THEN COALESCE(QUOTENAME(OBJECT_SCHEMA_NAME(dp.major_id))+'.'+QUOTENAME(OBJECT_NAME(dp.major_id)),CONVERT(varchar(50),dp.major_id)) "
                            "WHEN 3 THEN SCHEMA_NAME(dp.major_id) ELSE CONVERT(varchar(50),dp.major_id) END AS securable_name "
                            "FROM sys.database_role_members drm "
                            "JOIN sys.database_principals r ON r.principal_id=drm.role_principal_id "
                            "JOIN sys.database_principals m ON m.principal_id=drm.member_principal_id "
                            "LEFT JOIN sys.database_permissions dp ON dp.grantee_principal_id=r.principal_id "
                            "WHERE m.name IN ('HRLectura','ChatGPT_Escritura','HUB_Escritura','GptEscritura') "
                            "ORDER BY m.name,r.name,dp.class_desc,securable_name,dp.permission_name"
                        ),
                    },
                ],
            }
        ]
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
    if name == CHAPUR_EXTERNAL_INTEGRATION_READINESS_V1:
        return [
            {
                "type": "sql_readonly_audit",
                "source": "EDARSAHUB",
                "max_rows": 20,
                "queries": [
                    {
                        "name": "chapur_external_readiness",
                        "sql": (
                            "SELECT CONVERT(varchar(36), sc.id) AS connection_id,"
                            "sc.nombre,sc.tipo_conexion,sc.system_type,sc.activo,"
                            "sc.visible_en_operaciones,sc.queries_configured,"
                            "CASE WHEN NULLIF(LTRIM(RTRIM(ISNULL(sc.api_key_encrypted,''))), '') IS NOT NULL THEN CAST(1 AS bit) ELSE CAST(0 AS bit) END AS api_key_configured,"
                            "CASE WHEN NULLIF(LTRIM(RTRIM(ISNULL(sc.password_encrypted,''))), '') IS NOT NULL THEN CAST(1 AS bit) ELSE CAST(0 AS bit) END AS password_configured,"
                            "CASE WHEN sc.EmpresaID IS NULL AND NULLIF(LTRIM(RTRIM(ISNULL(sc.empresa_id,''))), '') IS NULL THEN CAST(0 AS bit) ELSE CAST(1 AS bit) END AS corporate_scope_configured "
                            "FROM dbo.Servidores_Conexiones sc "
                            "WHERE sc.id IN ('8CBDCC89-6495-49C3-BE9C-A965DB82C77F','D8B2D1EB-2E1F-4E43-B7D9-822BF671E315') "
                            "ORDER BY sc.nombre"
                        ),
                    },
                    {
                        "name": "chapur_external_health",
                        "sql": (
                            "SELECT CONVERT(varchar(36), e.ServidorID) AS connection_id,"
                            "e.EstadoConexion,e.UltimoCheck,e.UltimaPruebaUTC,e.UltimoExitoUTC,"
                            "e.UltimoErrorUTC,e.UltimoErrorCodigo,e.LatenciaMs,e.UltimoSyncUTC,"
                            "e.UltimoSyncExitosoUTC,e.FechaActualizacionUTC "
                            "FROM dbo.Servidores_ConexionEstado e "
                            "WHERE e.ServidorID IN ('8CBDCC89-6495-49C3-BE9C-A965DB82C77F','D8B2D1EB-2E1F-4E43-B7D9-822BF671E315') "
                            "ORDER BY e.ServidorID"
                        ),
                    },
                    {
                        "name": "chapur_query_contract_metadata",
                        "sql": (
                            "SELECT CONVERT(varchar(36),sc.id) AS connection_id,sc.nombre,sc.system_type,sc.queries_configured,"
                            "CASE WHEN NULLIF(LTRIM(RTRIM(ISNULL(sc.query_ventas,''))), '') IS NULL THEN CAST(0 AS bit) ELSE CAST(1 AS bit) END AS query_ventas_present,"
                            "CASE WHEN ISJSON(sc.query_ventas)=1 THEN CAST(1 AS bit) ELSE CAST(0 AS bit) END AS query_ventas_json,"
                            "CASE WHEN ISJSON(sc.query_ventas)=1 THEN JSON_VALUE(sc.query_ventas,'$.validated') ELSE NULL END AS query_ventas_validated,"
                            "LEN(ISNULL(sc.query_ventas,'')) AS query_ventas_len,"
                            "CASE WHEN NULLIF(LTRIM(RTRIM(ISNULL(sc.query_inventario,''))), '') IS NULL THEN CAST(0 AS bit) ELSE CAST(1 AS bit) END AS query_inventario_present,"
                            "CASE WHEN ISJSON(sc.query_inventario)=1 THEN CAST(1 AS bit) ELSE CAST(0 AS bit) END AS query_inventario_json,"
                            "CASE WHEN ISJSON(sc.query_inventario)=1 THEN JSON_VALUE(sc.query_inventario,'$.validated') ELSE NULL END AS query_inventario_validated,"
                            "LEN(ISNULL(sc.query_inventario,'')) AS query_inventario_len,"
                            "CASE WHEN NULLIF(LTRIM(RTRIM(ISNULL(sc.query_movimientos,''))), '') IS NULL THEN CAST(0 AS bit) ELSE CAST(1 AS bit) END AS query_movimientos_present,"
                            "CASE WHEN ISJSON(sc.query_movimientos)=1 THEN CAST(1 AS bit) ELSE CAST(0 AS bit) END AS query_movimientos_json,"
                            "CASE WHEN ISJSON(sc.query_movimientos)=1 THEN JSON_VALUE(sc.query_movimientos,'$.validated') ELSE NULL END AS query_movimientos_validated,"
                            "LEN(ISNULL(sc.query_movimientos,'')) AS query_movimientos_len "
                            "FROM dbo.Servidores_Conexiones sc "
                            "WHERE sc.id IN ('8CBDCC89-6495-49C3-BE9C-A965DB82C77F','D8B2D1EB-2E1F-4E43-B7D9-822BF671E315') "
                            "ORDER BY sc.nombre"
                        ),
                    },
                    {
                        "name": "chapur_connection_roles",
                        "sql": (
                            "SELECT CONVERT(varchar(36),ses.ServerID) AS connection_id,"
                            "ses.EmpresaID,ses.RolConexion,ses.NumeroSucursalSistema,ses.Activo "
                            "FROM dbo.Sistema_EmpresasServidores ses "
                            "WHERE ses.ServerID IN ('8CBDCC89-6495-49C3-BE9C-A965DB82C77F','D8B2D1EB-2E1F-4E43-B7D9-822BF671E315') "
                            "ORDER BY ses.ServerID,ses.RolConexion"
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
