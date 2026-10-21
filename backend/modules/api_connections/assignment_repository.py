from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from core.connections.edarsahub_writer_connection import (
    open_validated_writer_connection,
)
from core.sql_first.db import fetch_all_dict_readonly


def _uuid_text(value: str) -> str:
    return str(UUID(str(value)))


def list_api_operational_assignments(api_id: str) -> List[Dict[str, Any]]:
    """Lista relaciones activas de una API_LOCAL con empresas/unidades canónicas."""
    connection_id = _uuid_text(api_id)
    return fetch_all_dict_readonly(
        """
        SELECT
            es.EmpresaServidorID AS assignment_id,
            es.EmpresaID AS empresa_id,
            e.CodigoEmpresa AS empresa_codigo,
            e.NombreComercial AS empresa_nombre,
            CONVERT(varchar(36), es.ServidorID) AS servidor_id,
            es.RolConexion AS rol_conexion,
            es.NumeroSucursalSistema AS numero_sucursal_sistema,
            es.CodigoSucursalSistema AS codigo_sucursal_sistema,
            es.NombreSucursalSistema AS nombre_sucursal_sistema,
            es.Prioridad AS prioridad,
            es.EsPrincipal AS es_principal,
            es.Activo AS activo
        FROM dbo.Sistema_EmpresasServidores es
        JOIN dbo.Sistema_Empresas e
          ON e.EmpresaID = es.EmpresaID
        JOIN dbo.Servidores_Conexiones sc
          ON sc.id = es.ServidorID
        WHERE es.ServidorID = %s
          AND es.Activo = 1
          AND sc.tipo_conexion = 'API_LOCAL'
        ORDER BY e.NombreComercial, es.RolConexion, es.Prioridad
        """,
        (connection_id,),
    )


def upsert_api_operational_assignment(
    api_id: str,
    *,
    empresa_id: int,
    rol_conexion: str,
    numero_sucursal_sistema: Optional[int] = None,
    codigo_sucursal_sistema: Optional[str] = None,
    nombre_sucursal_sistema: Optional[str] = None,
    prioridad: int = 1,
    es_principal: bool = True,
) -> Dict[str, Any]:
    """Crea o reactiva una relación canónica Empresa <-> API_LOCAL."""
    connection_id = _uuid_text(api_id)
    role = str(rol_conexion or "").strip().upper()
    if not role:
        raise ValueError("ROL_CONEXION_REQUIRED")
    if int(prioridad) < 1:
        raise ValueError("PRIORIDAD_INVALID")

    conn, _identity = open_validated_writer_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("SET XACT_ABORT ON")
        cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")

        cur.execute(
            """
            SELECT TOP (1) id
            FROM dbo.Servidores_Conexiones WITH (UPDLOCK, HOLDLOCK)
            WHERE id = %s
              AND tipo_conexion = 'API_LOCAL'
            """,
            (connection_id,),
        )
        if not cur.fetchone():
            raise ValueError("API_LOCAL_NOT_FOUND")

        cur.execute(
            """
            SELECT TOP (1) EmpresaID
            FROM dbo.Sistema_Empresas WITH (UPDLOCK, HOLDLOCK)
            WHERE EmpresaID = %s
              AND Activo = 1
            """,
            (int(empresa_id),),
        )
        if not cur.fetchone():
            raise ValueError("EMPRESA_NOT_FOUND")

        cur.execute(
            """
            SELECT TOP (1) EmpresaServidorID
            FROM dbo.Sistema_EmpresasServidores WITH (UPDLOCK, HOLDLOCK)
            WHERE EmpresaID = %s
              AND ServidorID = %s
              AND RolConexion = %s
            ORDER BY EmpresaServidorID
            """,
            (int(empresa_id), connection_id, role),
        )
        existing = cur.fetchone()

        values = (
            numero_sucursal_sistema,
            (str(codigo_sucursal_sistema).strip() if codigo_sucursal_sistema else None),
            (str(nombre_sucursal_sistema).strip() if nombre_sucursal_sistema else None),
            int(prioridad),
            1 if es_principal else 0,
        )

        if existing:
            cur.execute(
                """
                UPDATE dbo.Sistema_EmpresasServidores
                SET NumeroSucursalSistema = %s,
                    CodigoSucursalSistema = %s,
                    NombreSucursalSistema = %s,
                    Prioridad = %s,
                    EsPrincipal = %s,
                    Activo = 1
                WHERE EmpresaServidorID = %s
                """,
                values + (existing["EmpresaServidorID"],),
            )
            assignment_id = existing["EmpresaServidorID"]
        else:
            cur.execute(
                """
                INSERT INTO dbo.Sistema_EmpresasServidores (
                    EmpresaID,
                    ServidorID,
                    RolConexion,
                    NumeroSucursalSistema,
                    CodigoSucursalSistema,
                    NombreSucursalSistema,
                    Prioridad,
                    EsPrincipal,
                    Activo
                )
                OUTPUT INSERTED.EmpresaServidorID
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1)
                """,
                (
                    int(empresa_id),
                    connection_id,
                    role,
                    numero_sucursal_sistema,
                    (str(codigo_sucursal_sistema).strip() if codigo_sucursal_sistema else None),
                    (str(nombre_sucursal_sistema).strip() if nombre_sucursal_sistema else None),
                    int(prioridad),
                    1 if es_principal else 0,
                ),
            )
            assignment_id = cur.fetchone()["EmpresaServidorID"]

        conn.commit()
        return {
            "assignment_id": assignment_id,
            "empresa_id": int(empresa_id),
            "servidor_id": connection_id,
            "rol_conexion": role,
            "activo": True,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def deactivate_api_operational_assignment(
    api_id: str,
    *,
    empresa_id: int,
    rol_conexion: str,
) -> bool:
    """Desasigna sin borrar historia: Activo=0."""
    connection_id = _uuid_text(api_id)
    role = str(rol_conexion or "").strip().upper()
    if not role:
        raise ValueError("ROL_CONEXION_REQUIRED")

    conn, _identity = open_validated_writer_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute("SET XACT_ABORT ON")
        cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        cur.execute(
            """
            UPDATE dbo.Sistema_EmpresasServidores
            SET Activo = 0
            WHERE EmpresaID = %s
              AND ServidorID = %s
              AND RolConexion = %s
              AND Activo = 1
            """,
            (int(empresa_id), connection_id, role),
        )
        changed = int(cur.rowcount or 0) > 0
        conn.commit()
        return changed
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
