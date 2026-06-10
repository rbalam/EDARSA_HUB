"""
Resolver canonico de unidad -> ServerID (EDARSA HUB)
====================================================
Mapea el espacio de IDs enteros del modulo comercial (EmpresaID / unidad_negocio_pk)
al GUID de servidor (ServerID) usado por las tablas Sync_* canonicas, SIN exponer ni
exigir el server_id en la API.

Fuente: dbo.Sistema_EmpresasServidores (RolConexion='PRINCIPAL_SQL').
Es el mismo puente usado por el resto de reportes canonicos (NO-LIVE).

Maneja de forma segura IDs faltantes / sin coincidencia: retorna None.
"""
from typing import Optional, Tuple
import logging

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG

logger = logging.getLogger(__name__)


def _conn() -> Tuple:
    return (
        EDARSAHUB_CONFIG['host'], EDARSAHUB_CONFIG['port'], EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'], EDARSAHUB_CONFIG['password'],
    )


def resolver_server_id(empresa_id: int, unidad_negocio_pk: Optional[int] = None) -> Optional[str]:
    """Resuelve el ServerID (GUID) canonico a partir del EmpresaID comercial.

    Retorna None si no hay coincidencia activa (en lugar de fallar), para que el
    endpoint pueda responder un error controlado.
    """
    if not empresa_id:
        return None
    try:
        rows = execute_sql_query_params(
            *_conn(),
            """
            SELECT TOP 1 CAST(ServidorID AS NVARCHAR(36)) AS server_id
            FROM Sistema_EmpresasServidores
            WHERE EmpresaID = %s AND RolConexion = 'PRINCIPAL_SQL' AND Activo = 1
            ORDER BY EsPrincipal DESC, EmpresaServidorID ASC
            """,
            (empresa_id,),
        )
        if rows and rows[0].get('server_id'):
            return str(rows[0]['server_id'])
        logger.warning(f"[RESOLVER] Sin ServerID canonico para EmpresaID={empresa_id}")
        return None
    except Exception as e:
        logger.error(f"[RESOLVER] Error resolviendo ServerID EmpresaID={empresa_id}: {e}")
        return None
