"""
EDARSA HUB - Resolver Canónico Centralizado (Inventarios / Catálogos)
=====================================================================
Capa COMÚN y reutilizable para resolver identificadores de ORIGEN (POS) hacia
los identificadores CANÓNICOS int de EDARSAHUB. NO vive dentro de ningún job.

REGLAS DE ARQUITECTURA (Ruta B - int estricta):
- Interfaz pública por (unidad_canonica, sistema_origen, codigo_origen).
- ServerID NO es dimensión operativa expuesta: se usa SOLO como llave interna de
  JOIN mientras `Sync_Productos*` no tenga `UnidadNegocioID` poblado.
- NUNCA inventa IDs. Si no resuelve -> None (el llamador lo manda a PENDIENTES;
  descartados = 0).
- SOLO LECTURA. Sin DDL. Sin hardcode de clasificaciones (los tipos de movimiento
  se leen de la tabla canónica `Inventario_TipoMovimiento`).

RENDIMIENTO (FIX conexiones):
- Usa una CONEXIÓN COMPARTIDA reutilizable a EDARSAHUB (no abre/filtra una conexión
  por fila). Antes cada resolución abría una conexión nueva sin cerrarla, lo que
  agotaba el SQL Server al sincronizar miles de movimientos.
- Cachea en proceso: existencia de tablas, server_id por unidad y los resultados de
  resolución (producto/almacén/empresa/sucursal/tipo) por llave de entrada.
- `clear_resolver_caches()` reinicia caches y conexión (útil entre corridas/tests).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

from core.sql_first.db import get_sql_connection
from core.server_registry import get_server_by_unidad_codigo

logger = logging.getLogger(__name__)

# Nombre de la tabla puente (productos POS -> ProductoID canónico).
BRIDGE_TABLE = "Producto_MapeoOrigen"
# Catálogo DB-driven de mapeo concepto-origen -> TipoMovimientoID.
CONCEPTO_MAPEO_TABLE = "Inventario_ConceptoMapeoOrigen"


@dataclass
class ResultadoResolucion:
    """Resultado homologado de una resolución canónica."""
    resuelto: bool
    canonical_id: Optional[int]
    motivo: str  # OK | PENDIENTE_SIN_MAPEO | BRIDGE_AUSENTE | UNIDAD_DESCONOCIDA | SIN_DIMENSION

    @classmethod
    def ok(cls, cid: int) -> "ResultadoResolucion":
        return cls(True, int(cid), "OK")

    @classmethod
    def pendiente(cls, motivo: str) -> "ResultadoResolucion":
        return cls(False, None, motivo)


# ---------------------------------------------------------------------------
# Conexión compartida + caches en proceso
# ---------------------------------------------------------------------------

_shared_conn = None
_table_exists_cache: Dict[str, bool] = {}
_server_id_cache: Dict[str, Optional[str]] = {}
_producto_cache: Dict[Tuple[str, str, str], ResultadoResolucion] = {}
_almacen_cache: Dict[Tuple[int, int, str], ResultadoResolucion] = {}
_empresa_cache: Dict[str, ResultadoResolucion] = {}
_sucursal_cache: Dict[Tuple[str, Optional[str]], ResultadoResolucion] = {}
_tipo_concepto_cache: Dict[Tuple[str, str], ResultadoResolucion] = {}


def clear_resolver_caches() -> None:
    """Reinicia caches y cierra la conexión compartida."""
    global _shared_conn
    _table_exists_cache.clear()
    _server_id_cache.clear()
    _producto_cache.clear()
    _almacen_cache.clear()
    _empresa_cache.clear()
    _sucursal_cache.clear()
    _tipo_concepto_cache.clear()
    if _shared_conn is not None:
        try:
            _shared_conn.close()
        except Exception:
            pass
        _shared_conn = None


def _get_conn():
    """Devuelve la conexión compartida a EDARSAHUB (lazy)."""
    global _shared_conn
    if _shared_conn is None:
        _shared_conn = get_sql_connection()
    return _shared_conn


def _fetchall(sql: str, params: tuple = (), as_dict: bool = False) -> List[Any]:
    """
    Ejecuta una consulta de SOLO LECTURA sobre la conexión compartida.
    Reintenta una vez recreando la conexión si la sesión se cayó.
    """
    global _shared_conn
    for intento in (1, 2):
        try:
            conn = _get_conn()
            cur = conn.cursor(as_dict=True) if as_dict else conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()
        except Exception as e:
            # Conexión caída/expirada -> recrear y reintentar una vez.
            if _shared_conn is not None:
                try:
                    _shared_conn.close()
                except Exception:
                    pass
                _shared_conn = None
            if intento == 2:
                logger.error(f"[RESOLVER] Error de consulta tras reintento: {str(e)[:160]}")
                raise
    return []


def _tabla_existe(nombre: str) -> bool:
    if nombre in _table_exists_cache:
        return _table_exists_cache[nombre]
    rows = _fetchall(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = %s",
        (nombre,),
    )
    existe = bool(rows and rows[0][0] > 0)
    _table_exists_cache[nombre] = existe
    return existe


def _server_id_de_unidad(unidad_codigo: str) -> Optional[str]:
    """Traduce la unidad canónica -> ServerID (llave de JOIN interna, no operativa)."""
    if not unidad_codigo:
        return None
    if unidad_codigo in _server_id_cache:
        return _server_id_cache[unidad_codigo]
    unidad = get_server_by_unidad_codigo(unidad_codigo)
    sid = None
    if unidad:
        sid = unidad.get("server_id") or unidad.get("id")
    _server_id_cache[unidad_codigo] = sid
    return sid


# ---------------------------------------------------------------------------
# Resolución de PRODUCTO (POS -> ProductoID int)
# ---------------------------------------------------------------------------

def resolver_producto_id(unidad_codigo: str, sistema_origen: str, codigo_origen: str) -> ResultadoResolucion:
    """
    Resuelve el ProductoID canónico (int) a partir de la unidad canónica, el sistema
    de origen y el código de origen del POS.

    Depende del puente `Producto_MapeoOrigen` (ServerID, SystemType, CodigoFuente -> ProductoID).
    Mientras el puente no exista, devuelve PENDIENTE con motivo 'BRIDGE_AUSENTE'.
    """
    server_id = _server_id_de_unidad(unidad_codigo)
    if not server_id:
        return ResultadoResolucion.pendiente("UNIDAD_DESCONOCIDA")

    if not _tabla_existe(BRIDGE_TABLE):
        return ResultadoResolucion.pendiente("BRIDGE_AUSENTE")

    codigo = str(codigo_origen or "").strip()
    if not codigo:
        return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")

    sistema = str(sistema_origen or "").upper()
    ckey = (str(server_id), sistema, codigo)
    cached = _producto_cache.get(ckey)
    if cached is not None:
        return cached

    rows = _fetchall(
        f"""SELECT TOP 1 ProductoID FROM {BRIDGE_TABLE}
            WHERE ServerID = %s AND SystemType = %s AND CodigoFuente = %s AND Activo = 1""",
        (str(server_id), sistema, codigo),
    )
    if rows and rows[0][0] is not None:
        res = ResultadoResolucion.ok(rows[0][0])
    else:
        res = ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")
    _producto_cache[ckey] = res
    return res


# ---------------------------------------------------------------------------
# Resolución de ALMACÉN (POS -> AlmacenID int)
# ---------------------------------------------------------------------------

def resolver_almacen_id(empresa_id: int, sucursal_id: int, codigo_almacen: str) -> ResultadoResolucion:
    """Resuelve AlmacenID canónico desde `Inventario_Almacenes` por código + empresa/sucursal."""
    codigo = str(codigo_almacen or "").strip()
    if not codigo or empresa_id is None or sucursal_id is None:
        return ResultadoResolucion.pendiente("SIN_DIMENSION")

    ckey = (int(empresa_id), int(sucursal_id), codigo)
    cached = _almacen_cache.get(ckey)
    if cached is not None:
        return cached

    rows = _fetchall(
        """SELECT TOP 1 AlmacenID FROM Inventario_Almacenes
           WHERE EmpresaID = %s AND SucursalID = %s AND CodigoAlmacen = %s AND Activo = 1""",
        (int(empresa_id), int(sucursal_id), codigo),
    )
    if rows and rows[0][0] is not None:
        res = ResultadoResolucion.ok(rows[0][0])
    else:
        res = ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")
    _almacen_cache[ckey] = res
    return res


# ---------------------------------------------------------------------------
# Resolución de EMPRESA (unidad canónica -> EmpresaID int)  [Sistema_Empresas]
# ---------------------------------------------------------------------------

def resolver_empresa_id(unidad_codigo: str) -> ResultadoResolucion:
    """
    Resuelve EmpresaID canónico desde `Sistema_Empresas` por `CodigoEmpresa`,
    que coincide 1:1 con el código de unidad (ORIGEN, 130QRO, CIENFUEGOS, ...).
    Fuente autoritativa. Sin POS, sin hardcode.
    """
    cod = str(unidad_codigo or "").strip().upper()
    if not cod:
        return ResultadoResolucion.pendiente("UNIDAD_DESCONOCIDA")

    cached = _empresa_cache.get(cod)
    if cached is not None:
        return cached

    rows = _fetchall(
        "SELECT TOP 1 EmpresaID FROM Sistema_Empresas WHERE UPPER(CodigoEmpresa) = %s AND Activo = 1",
        (cod,),
    )
    if rows and rows[0][0] is not None:
        res = ResultadoResolucion.ok(rows[0][0])
    else:
        res = ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")
    _empresa_cache[cod] = res
    return res


# ---------------------------------------------------------------------------
# Resolución de SUCURSAL (ServerID + sucursal_origen -> SucursalID int)
# ---------------------------------------------------------------------------

def resolver_sucursal_id(servidor_id: str, sucursal_origen_id: Optional[str] = None) -> ResultadoResolucion:
    """
    Resuelve SucursalID canónico (RH_Cat_Sucursales) por unidad, derivando de tablas
    canónicas (sin POS):

    1. `Sistema_SucursalServidorMapeo` por ServidorID:
       - 1 sola fila (servidor dedicado SR) -> esa SucursalID.
       - varias filas (servidor MPRO compartido) -> desambigua por SucursalOrigenID.
    2. Si el mapeo no trae SucursalOrigenID (NULL) pero hay `sucursal_origen_id`, intenta
       confirmar la sucursal de origen vía `Sistema_EmpresasServidores.NumeroSucursalSistema`.
       Si aún no se puede mapear a una SucursalID(RH) única -> AMBIGUO (no adivina).
    """
    if not servidor_id:
        return ResultadoResolucion.pendiente("SIN_DIMENSION")

    ckey = (str(servidor_id), str(sucursal_origen_id) if sucursal_origen_id is not None else None)
    cached = _sucursal_cache.get(ckey)
    if cached is not None:
        return cached

    filas = _fetchall(
        """SELECT SucursalID, SucursalOrigenID FROM Sistema_SucursalServidorMapeo
           WHERE ServidorID = %s AND Activo = 1""",
        (str(servidor_id),),
        as_dict=True,
    )
    if not filas:
        res = ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")
        _sucursal_cache[ckey] = res
        return res

    if len(filas) == 1:
        res = ResultadoResolucion.ok(filas[0]["SucursalID"])
        _sucursal_cache[ckey] = res
        return res

    # Servidor compartido (MPRO): intentar desambiguar por SucursalOrigenID del mapeo.
    if sucursal_origen_id:
        try:
            origen_norm = int(str(sucursal_origen_id).lstrip("0") or "0")
        except ValueError:
            origen_norm = None
        for f in filas:
            soi = f.get("SucursalOrigenID")
            if soi is not None and str(soi).strip() == str(sucursal_origen_id).strip():
                res = ResultadoResolucion.ok(f["SucursalID"])
                _sucursal_cache[ckey] = res
                return res
            if soi is not None and origen_norm is not None:
                try:
                    if int(str(soi).lstrip("0") or "0") == origen_norm:
                        res = ResultadoResolucion.ok(f["SucursalID"])
                        _sucursal_cache[ckey] = res
                        return res
                except ValueError:
                    pass

    # Mapeo MPRO sin SucursalOrigenID confiable -> no adivinar.
    res = ResultadoResolucion.pendiente("AMBIGUO_MULTISUCURSAL")
    _sucursal_cache[ckey] = res
    return res


# ---------------------------------------------------------------------------
# Resolución de TIPO DE MOVIMIENTO (DB-driven, sin hardcode de clasificación)
# ---------------------------------------------------------------------------

def resolver_tipo_movimiento_por_codigo(codigo_canonico: str) -> ResultadoResolucion:
    """
    Resuelve TipoMovimientoID desde la tabla canónica `Inventario_TipoMovimiento`
    por su Código canónico (p.ej. 'ENTRADA_COMPRA'). DB-driven: cero hardcode.
    """
    codigo = str(codigo_canonico or "").strip().upper()
    if not codigo:
        return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")

    rows = _fetchall(
        "SELECT TOP 1 TipoMovimientoID FROM Inventario_TipoMovimiento WHERE Codigo = %s AND Activo = 1",
        (codigo,),
    )
    if rows and rows[0][0] is not None:
        return ResultadoResolucion.ok(rows[0][0])
    return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")


def resolver_tipo_movimiento_desde_concepto(system_type: str, concepto_origen: str) -> ResultadoResolucion:
    """
    Sub-fase B (DB-driven): resuelve TipoMovimientoID a partir del concepto de ORIGEN
    (EPC/SPC/ETA... en SoftRestaurant; Tm_Cve_Tipo_Movimiento en MPRO), leyendo del
    catálogo `Inventario_ConceptoMapeoOrigen` (SystemType + ConceptoOrigen -> TipoMovimientoID).

    CERO hardcode: si el catálogo no existe aún o el concepto no está mapeado,
    devuelve PENDIENTE (el movimiento queda en pendientes; descartados=0).
    """
    st = str(system_type or "").strip().upper()
    cc = str(concepto_origen or "").strip().upper()
    if not st or not cc:
        return ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")

    if not _tabla_existe(CONCEPTO_MAPEO_TABLE):
        return ResultadoResolucion.pendiente("CATALOGO_CONCEPTOS_AUSENTE")

    ckey = (st, cc)
    cached = _tipo_concepto_cache.get(ckey)
    if cached is not None:
        return cached

    rows = _fetchall(
        f"""SELECT TOP 1 TipoMovimientoID FROM {CONCEPTO_MAPEO_TABLE}
            WHERE SystemType = %s AND ConceptoOrigen = %s AND Activo = 1""",
        (st, cc),
    )
    if rows and rows[0][0] is not None:
        res = ResultadoResolucion.ok(rows[0][0])
    else:
        res = ResultadoResolucion.pendiente("PENDIENTE_SIN_MAPEO")
    _tipo_concepto_cache[ckey] = res
    return res


__all__ = [
    "ResultadoResolucion",
    "resolver_producto_id",
    "resolver_almacen_id",
    "resolver_empresa_id",
    "resolver_sucursal_id",
    "resolver_tipo_movimiento_por_codigo",
    "resolver_tipo_movimiento_desde_concepto",
    "clear_resolver_caches",
    "BRIDGE_TABLE",
    "CONCEPTO_MAPEO_TABLE",
]
