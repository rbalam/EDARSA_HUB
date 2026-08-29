from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
COSTOS-ALERTAS-001-C: Repository para Reglas de Margen Esperado

EDARSAHUB SQL es el cerebro. CERO MongoDB.

Tablas utilizadas:
- Comercial_AlertasMargenReglas
- Comercial_AlertasUmbralesSeveridad

Jerarquía de resolución:
Producto > Subfamilia > Familia > Grupo
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Tuple, Any
import logging

from core.db import execute_sql_query, execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG

logger = logging.getLogger(__name__)


def _get_conn() -> Tuple[str, int, str, str, str]:
    """Retorna conexión a EDARSAHUB SQL."""
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )


def _safe_decimal(value, default=Decimal('0')) -> Decimal:
    """Convierte valor a Decimal de forma segura."""
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _safe_isoformat(value) -> Optional[str]:
    """Convierte fecha a ISO format de forma segura."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return value.isoformat()
    except Exception:
        return str(value)


# =============================================================================
# CRUD DE REGLAS DE MARGEN
# =============================================================================

def listar_reglas(
    nivel_aplicacion: Optional[str] = None,
    solo_activas: bool = True,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
) -> Tuple[List[Dict], int]:
    """
    Lista reglas de margen con filtros opcionales.

    Args:
        nivel_aplicacion: GRUPO, FAMILIA, SUBFAMILIA, PRODUCTO
        solo_activas: Si True, solo reglas activas y vigentes
        empresa_id: Filtrar por empresa
        sucursal_id: Filtrar por sucursal
        page: Página
        page_size: Tamaño de página

    Returns:
        Tupla (lista de reglas, total)
    """
    conn = _get_conn()

    where_clauses = ["1=1"]
    params: List[Any] = []

    if nivel_aplicacion:
        where_clauses.append("NivelAplicacion = %s")
        params.append(nivel_aplicacion)

    if solo_activas:
        where_clauses.append("Activo = 1")
        where_clauses.append("(FechaFinVigencia IS NULL OR FechaFinVigencia > GETDATE())")
        where_clauses.append("FechaInicioVigencia <= GETDATE()")

    if empresa_id is not None:
        where_clauses.append("(EmpresaID IS NULL OR EmpresaID = %s)")
        params.append(empresa_id)

    if sucursal_id is not None:
        where_clauses.append("(SucursalID IS NULL OR SucursalID = %s)")
        params.append(sucursal_id)

    if server_id:
        where_clauses.append(
            "(ServerID IS NULL OR ServerID = CAST(%s AS UNIQUEIDENTIFIER))"
        )
        params.append(server_id)

    where_sql = " AND ".join(where_clauses)
    offset = (page - 1) * page_size

    # Contar total
    count_query = f"SELECT COUNT(*) as total FROM Comercial_AlertasMargenReglas WHERE {where_sql}"
    count_result = execute_sql_query_params(*conn, count_query, tuple(params))
    total = count_result[0].get('total', 0) if count_result else 0

    # Obtener datos
    data_query = f"""
    SELECT
        CAST(ReglaMargenID AS NVARCHAR(36)) as regla_id,
        NivelAplicacion as nivel_aplicacion,
        GrupoCodigo as grupo_codigo,
        FamiliaCodigo as familia_codigo,
        SubfamiliaCodigo as subfamilia_codigo,
        ProductoClave as producto_clave,
        ProductoID as producto_id,
        EmpresaID as EmpresaID,
        SucursalID as SucursalID,
        CAST(ServerID AS NVARCHAR(36)) as ServerID,
        MargenPorcentajeEsperado as margen_esperado,
        CostoMaximoPorcentaje as costo_maximo,
        UtilidadMinimaPorcentaje as utilidad_minima,
        SeveridadBase as severidad_base,
        Descripcion as Descripcion,
        Activo as Activo,
        FechaInicioVigencia as fecha_inicio,
        FechaFinVigencia as fecha_fin,
        FechaCreacion as fecha_creacion,
        FechaModificacion as fecha_modificacion,
        CreadoPor as creado_por,
        ModificadoPor as modificado_por
    FROM Comercial_AlertasMargenReglas
    WHERE {where_sql}
    ORDER BY
        CASE NivelAplicacion
            WHEN 'PRODUCTO' THEN 1
            WHEN 'SUBFAMILIA' THEN 2
            WHEN 'FAMILIA' THEN 3
            WHEN 'GRUPO' THEN 4
        END,
        FechaCreacion DESC
    OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
    """

    rows = execute_sql_query_params(
        *conn,
        data_query,
        tuple(params + [offset, page_size]),
    ) or []

    reglas = []
    for row in rows:
        reglas.append({
            'regla_id': row.get('regla_id'),
            'nivel_aplicacion': row.get('nivel_aplicacion'),
            'grupo_codigo': row.get('grupo_codigo'),
            'familia_codigo': row.get('familia_codigo'),
            'subfamilia_codigo': row.get('subfamilia_codigo'),
            'producto_clave': row.get('producto_clave'),
            'producto_id': row.get('producto_id'),
            'empresa_id': row.get('empresa_id'),
            'sucursal_id': row.get('sucursal_id'),
            'server_id': row.get('server_id'),
            'margen_esperado': float(_safe_decimal(row.get('margen_esperado'))),
            'costo_maximo': float(_safe_decimal(row.get('costo_maximo'))) if row.get('costo_maximo') else None,
            'utilidad_minima': float(_safe_decimal(row.get('utilidad_minima'))) if row.get('utilidad_minima') else None,
            'severidad_base': row.get('severidad_base'),
            'descripcion': row.get('descripcion'),
            'activo': bool(row.get('activo')),
            'fecha_inicio': _safe_isoformat(row.get('fecha_inicio')) if row.get('fecha_inicio') else None,
            'fecha_fin': _safe_isoformat(row.get('fecha_fin')) if row.get('fecha_fin') else None,
            'fecha_creacion': _safe_isoformat(row.get('fecha_creacion')) if row.get('fecha_creacion') else None,
            'fecha_modificacion': _safe_isoformat(row.get('fecha_modificacion')) if row.get('fecha_modificacion') else None,
            'creado_por': row.get('creado_por'),
            'modificado_por': row.get('modificado_por'),
            # Entidad aplicable según nivel
            'entidad_codigo': (
                row.get('producto_clave') or
                (
                    str(row.get('producto_id'))
                    if (
                        row.get('nivel_aplicacion') == 'PRODUCTO'
                        and row.get('producto_id') is not None
                    )
                    else None
                ) or
                row.get('subfamilia_codigo') or
                row.get('familia_codigo') or
                row.get('grupo_codigo')
            )
        })

    return reglas, total


def obtener_regla_por_id(regla_id: str) -> Optional[Dict]:
    """
    Obtiene una regla de margen por su ID.

    Args:
        regla_id: UUID de la regla

    Returns:
        Dict con la regla o None si no existe
    """
    conn = _get_conn()

    query = """
    SELECT
        CAST(ReglaMargenID AS NVARCHAR(36)) as regla_id,
        NivelAplicacion as nivel_aplicacion,
        GrupoCodigo as grupo_codigo,
        FamiliaCodigo as familia_codigo,
        SubfamiliaCodigo as subfamilia_codigo,
        ProductoClave as producto_clave,
        ProductoID as producto_id,
        EmpresaID as EmpresaID,
        SucursalID as SucursalID,
        CAST(ServerID AS NVARCHAR(36)) as ServerID,
        MargenPorcentajeEsperado as margen_esperado,
        CostoMaximoPorcentaje as costo_maximo,
        UtilidadMinimaPorcentaje as utilidad_minima,
        SeveridadBase as severidad_base,
        Descripcion as Descripcion,
        Activo as Activo,
        FechaInicioVigencia as fecha_inicio,
        FechaFinVigencia as fecha_fin,
        FechaCreacion as fecha_creacion,
        FechaModificacion as fecha_modificacion,
        CreadoPor as creado_por,
        ModificadoPor as modificado_por
    FROM Comercial_AlertasMargenReglas
    WHERE ReglaMargenID = %s
    """

    rows = execute_sql_query_params(*conn, query, (regla_id,))
    if not rows:
        return None

    row = rows[0]
    return {
        'regla_id': row.get('regla_id'),
        'nivel_aplicacion': row.get('nivel_aplicacion'),
        'grupo_codigo': row.get('grupo_codigo'),
        'familia_codigo': row.get('familia_codigo'),
        'subfamilia_codigo': row.get('subfamilia_codigo'),
        'producto_clave': row.get('producto_clave'),
        'producto_id': row.get('producto_id'),
        'empresa_id': row.get('empresa_id'),
        'sucursal_id': row.get('sucursal_id'),
        'server_id': row.get('server_id'),
        'margen_esperado': float(_safe_decimal(row.get('margen_esperado'))),
        'costo_maximo': float(_safe_decimal(row.get('costo_maximo'))) if row.get('costo_maximo') else None,
        'utilidad_minima': float(_safe_decimal(row.get('utilidad_minima'))) if row.get('utilidad_minima') else None,
        'severidad_base': row.get('severidad_base'),
        'descripcion': row.get('descripcion'),
        'activo': bool(row.get('activo')),
        'fecha_inicio': _safe_isoformat(row.get('fecha_inicio')) if row.get('fecha_inicio') else None,
        'fecha_fin': _safe_isoformat(row.get('fecha_fin')) if row.get('fecha_fin') else None,
        'fecha_creacion': _safe_isoformat(row.get('fecha_creacion')) if row.get('fecha_creacion') else None,
        'fecha_modificacion': _safe_isoformat(row.get('fecha_modificacion')) if row.get('fecha_modificacion') else None,
        'creado_por': row.get('creado_por'),
        'modificado_por': row.get('modificado_por'),
        'entidad_codigo': (
            row.get('producto_clave') or
            (
                str(row.get('producto_id'))
                if (
                    row.get('nivel_aplicacion') == 'PRODUCTO'
                    and row.get('producto_id') is not None
                )
                else None
            ) or
            row.get('subfamilia_codigo') or
            row.get('familia_codigo') or
            row.get('grupo_codigo')
        )
    }


def verificar_duplicado_regla(
    nivel_aplicacion: str,
    entidad_codigo: str,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    excluir_regla_id: Optional[str] = None,
    producto_id: Optional[int] = None
) -> bool:
    """
    Verifica si ya existe una regla activa para la misma entidad/nivel.
    """
    conn = _get_conn()

    nivel_aplicacion = str(nivel_aplicacion).upper().strip()

    if nivel_aplicacion == 'PRODUCTO':
        if producto_id is None:
            return False
        campo_entidad = 'ProductoID'
        valor_entidad = int(producto_id)
    else:
        campo_entidad = {
            'GRUPO': 'GrupoCodigo',
            'FAMILIA': 'FamiliaCodigo',
            'SUBFAMILIA': 'SubfamiliaCodigo',
        }.get(nivel_aplicacion)

        if not campo_entidad:
            return False

        valor_entidad = entidad_codigo

    where_clauses = [
        "NivelAplicacion = %s",
        f"{campo_entidad} = %s",
        "Activo = 1",
        "(FechaFinVigencia IS NULL OR FechaFinVigencia > GETDATE())"
    ]

    params = [
        nivel_aplicacion,
        valor_entidad,
    ]

    if empresa_id is not None:
        where_clauses.append(
            "(EmpresaID IS NULL OR EmpresaID = %s)"
        )
        params.append(empresa_id)
    else:
        where_clauses.append("EmpresaID IS NULL")

    if sucursal_id is not None:
        where_clauses.append(
            "(SucursalID IS NULL OR SucursalID = %s)"
        )
        params.append(sucursal_id)
    else:
        where_clauses.append("SucursalID IS NULL")

    if excluir_regla_id:
        where_clauses.append("ReglaMargenID != %s")
        params.append(excluir_regla_id)

    where_sql = " AND ".join(where_clauses)

    query = (
        "SELECT COUNT(*) as cnt "
        "FROM Comercial_AlertasMargenReglas "
        f"WHERE {where_sql}"
    )

    result = execute_sql_query_params(
        *conn,
        query,
        tuple(params),
    )

    return (result[0].get('cnt', 0) if result else 0) > 0



def crear_regla(
    nivel_aplicacion: str,
    entidad_codigo: str,
    margen_esperado: float,
    producto_id: Optional[int] = None,
    costo_maximo: Optional[float] = None,
    utilidad_minima: Optional[float] = None,
    severidad_base: str = 'MEDIA',
    descripcion: Optional[str] = None,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    creado_por: str = 'SISTEMA'
) -> Dict:
    """
    Crea una nueva regla de margen esperado.
    """
    conn = _get_conn()

    regla_id = str(uuid.uuid4()).upper()
    nivel_aplicacion = str(nivel_aplicacion).upper().strip()

    if nivel_aplicacion == 'PRODUCTO':
        if producto_id is None or int(producto_id) <= 0:
            raise ValueError(
                "PRODUCTO_ID_CANONICO_REQUERIDO"
            )
        campo_entidad = 'ProductoID'
        valor_entidad = int(producto_id)
    else:
        campo_entidad = {
            'GRUPO': 'GrupoCodigo',
            'FAMILIA': 'FamiliaCodigo',
            'SUBFAMILIA': 'SubfamiliaCodigo',
        }.get(nivel_aplicacion)

        if not campo_entidad:
            raise ValueError(
                f"Nivel de aplicación inválido: "
                f"{nivel_aplicacion}"
            )

        valor_entidad = entidad_codigo

    fecha_inicio_sql = (
        "%s"
        if fecha_inicio is not None
        else "GETDATE()"
    )

    query = f"""
    INSERT INTO Comercial_AlertasMargenReglas (
        ReglaMargenID,
        NivelAplicacion,
        {campo_entidad},
        EmpresaID,
        SucursalID,
        ServerID,
        MargenPorcentajeEsperado,
        CostoMaximoPorcentaje,
        UtilidadMinimaPorcentaje,
        SeveridadBase,
        Descripcion,
        Activo,
        FechaInicioVigencia,
        FechaFinVigencia,
        FechaCreacion,
        CreadoPor
    )
    VALUES (
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        1,
        {fecha_inicio_sql},
        %s,
        GETDATE(),
        %s
    )
    """

    params = (
        regla_id,
        nivel_aplicacion,
        valor_entidad,
        empresa_id,
        sucursal_id,
        server_id,
        margen_esperado,
        costo_maximo,
        utilidad_minima,
        severidad_base,
        descripcion,
    )

    if fecha_inicio is not None:
        params = params + (fecha_inicio,)

    params = params + (
        fecha_fin,
        creado_por,
    )

    execute_sql_query_params(
        *conn,
        query,
        params,
    )

    logger.info(
        "[ALERTAS_MARGEN] Regla creada: %s - %s=%s",
        regla_id,
        nivel_aplicacion,
        (
            producto_id
            if nivel_aplicacion == 'PRODUCTO'
            else entidad_codigo
        ),
    )

    return obtener_regla_por_id(regla_id)



def actualizar_regla(
    regla_id: str,
    margen_esperado: Optional[float] = None,
    costo_maximo: Optional[float] = None,
    utilidad_minima: Optional[float] = None,
    severidad_base: Optional[str] = None,
    descripcion: Optional[str] = None,
    fecha_fin: Optional[datetime] = None,
    modificado_por: str = 'SISTEMA'
) -> Optional[Dict]:
    """
    Actualiza una regla de margen existente.

    Args:
        regla_id: UUID de la regla
        margen_esperado: Nuevo margen esperado
        costo_maximo: Nuevo costo máximo
        utilidad_minima: Nueva utilidad mínima
        severidad_base: Nueva severidad
        descripcion: Nueva descripción
        fecha_fin: Nueva fecha de fin
        modificado_por: Usuario que modifica

    Returns:
        Dict con la regla actualizada o None si no existe
    """
    conn = _get_conn()

    # Verificar que existe
    regla_actual = obtener_regla_por_id(regla_id)
    if not regla_actual:
        return None

    set_clauses = ["FechaModificacion = GETDATE()", "ModificadoPor = %s"]
    params: List[Any] = [modificado_por]

    if margen_esperado is not None:
        set_clauses.append("MargenPorcentajeEsperado = %s")
        params.append(margen_esperado)

    if costo_maximo is not None:
        set_clauses.append("CostoMaximoPorcentaje = %s")
        params.append(costo_maximo)

    if utilidad_minima is not None:
        set_clauses.append("UtilidadMinimaPorcentaje = %s")
        params.append(utilidad_minima)

    if severidad_base:
        set_clauses.append("SeveridadBase = %s")
        params.append(severidad_base)

    if descripcion is not None:
        set_clauses.append("Descripcion = %s")
        params.append(descripcion)

    if fecha_fin:
        set_clauses.append("FechaFinVigencia = %s")
        params.append(fecha_fin)

    set_sql = ", ".join(set_clauses)

    query = (
        "UPDATE Comercial_AlertasMargenReglas "
        f"SET {set_sql} WHERE ReglaMargenID = %s"
    )
    execute_sql_query_params(*conn, query, tuple(params + [regla_id]))

    logger.info(f"[ALERTAS_MARGEN] Regla actualizada: {regla_id}")

    return obtener_regla_por_id(regla_id)


def desactivar_regla(regla_id: str, modificado_por: str = 'SISTEMA') -> bool:
    """
    Desactiva una regla de margen (no la elimina).

    Args:
        regla_id: UUID de la regla
        modificado_por: Usuario que desactiva

    Returns:
        True si se desactivó, False si no existe
    """
    conn = _get_conn()

    # Verificar que existe
    regla_actual = obtener_regla_por_id(regla_id)
    if not regla_actual:
        return False

    query = """
    UPDATE Comercial_AlertasMargenReglas
    SET Activo = 0,
        FechaModificacion = GETDATE(),
        ModificadoPor = %s
    WHERE ReglaMargenID = %s
    """
    execute_sql_query_params(*conn, query, (modificado_por, regla_id))

    logger.info(f"[ALERTAS_MARGEN] Regla desactivada: {regla_id}")

    return True


# =============================================================================
# RESOLUCIÓN DE REGLA APLICABLE (JERARQUÍA)
# =============================================================================

def resolver_regla_aplicable(
    producto_id: Optional[int] = None,
    producto_clave: Optional[str] = None,
    subfamilia_codigo: Optional[str] = None,
    familia_codigo: Optional[str] = None,
    grupo_codigo: Optional[str] = None,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None
) -> Dict:
    """
    Resuelve la regla de margen aplicable usando la jerarquia:
    Producto > Subfamilia > Familia > Grupo.

    Los valores de negocio se envian como parametros SQL. Solo el nombre
    de columna se selecciona desde la lista interna fija ``niveles``.

    Para reglas del mismo nivel, conserva la prioridad historica de alcance
    y agrega ServerID como tercer desempate:
    Empresa especifica > Sucursal especifica > Server especifico > global.
    """
    conn = _get_conn()

    vigencia_sql = """
        Activo = 1
        AND FechaInicioVigencia <= GETDATE()
        AND (
            FechaFinVigencia IS NULL
            OR FechaFinVigencia > GETDATE()
        )
    """

    alcance_clauses = []
    alcance_params = []

    if empresa_id:
        alcance_clauses.append(
            "(EmpresaID IS NULL OR EmpresaID = %s)"
        )
        alcance_params.append(int(empresa_id))
    else:
        alcance_clauses.append(
            "(EmpresaID IS NULL)"
        )

    if sucursal_id:
        alcance_clauses.append(
            "(SucursalID IS NULL OR SucursalID = %s)"
        )
        alcance_params.append(int(sucursal_id))
    else:
        alcance_clauses.append(
            "(SucursalID IS NULL)"
        )

    if server_id:
        alcance_clauses.append(
            "("
            "ServerID IS NULL "
            "OR ServerID = CAST(%s AS UNIQUEIDENTIFIER)"
            ")"
        )
        alcance_params.append(str(server_id))
    else:
        alcance_clauses.append(
            "(ServerID IS NULL)"
        )

    alcance_sql = " AND ".join(
        alcance_clauses
    )

    # El identificador SQL no viene del usuario:
    # pertenece exclusivamente a esta whitelist fija.
    niveles = [
        (
            "PRODUCTO",
            "ProductoID",
            producto_id,
            "",
        ),
        (
            "PRODUCTO",
            "ProductoClave",
            producto_clave,
            "ProductoID IS NULL AND ",
        ),
        (
            "SUBFAMILIA",
            "SubfamiliaCodigo",
            subfamilia_codigo,
            "",
        ),
        (
            "FAMILIA",
            "FamiliaCodigo",
            familia_codigo,
            "",
        ),
        (
            "GRUPO",
            "GrupoCodigo",
            grupo_codigo,
            "",
        ),
    ]

    for nivel, campo, valor, restriccion in niveles:
        if valor is None or str(valor).strip() == "":
            continue

        query = f"""
        SELECT TOP 1
            CAST(
                ReglaMargenID
                AS NVARCHAR(36)
            ) AS regla_id,
            NivelAplicacion AS nivel_aplicacion,
            {campo} AS entidad_codigo,
            MargenPorcentajeEsperado AS margen_esperado,
            CostoMaximoPorcentaje AS costo_maximo,
            UtilidadMinimaPorcentaje AS utilidad_minima,
            SeveridadBase AS severidad_base,
            Descripcion AS Descripcion
        FROM Comercial_AlertasMargenReglas
        WHERE NivelAplicacion = %s
          AND {restriccion}{campo} = %s
          AND {vigencia_sql}
          AND {alcance_sql}
        ORDER BY
            CASE
                WHEN EmpresaID IS NOT NULL
                THEN 0
                ELSE 1
            END,
            CASE
                WHEN SucursalID IS NOT NULL
                THEN 0
                ELSE 1
            END,
            CASE
                WHEN ServerID IS NOT NULL
                THEN 0
                ELSE 1
            END,
            FechaCreacion DESC
        """

        params = (
            nivel,
            int(valor)
            if campo == "ProductoID"
            else str(valor),
            *alcance_params,
        )

        rows = execute_sql_query_params(
            *conn,
            query,
            params,
        )

        if rows:
            row = rows[0]

            return {
                "regla": {
                    "regla_id":
                        row.get("regla_id"),
                    "nivel_aplicacion":
                        row.get(
                            "nivel_aplicacion"
                        ),
                    "entidad_codigo":
                        row.get(
                            "entidad_codigo"
                        ),
                    "margen_esperado":
                        float(
                            _safe_decimal(
                                row.get(
                                    "margen_esperado"
                                )
                            )
                        ),
                    "costo_maximo":
                        (
                            float(
                                _safe_decimal(
                                    row.get(
                                        "costo_maximo"
                                    )
                                )
                            )
                            if row.get(
                                "costo_maximo"
                            )
                            is not None
                            else None
                        ),
                    "utilidad_minima":
                        (
                            float(
                                _safe_decimal(
                                    row.get(
                                        "utilidad_minima"
                                    )
                                )
                            )
                            if row.get(
                                "utilidad_minima"
                            )
                            is not None
                            else None
                        ),
                    "severidad_base":
                        row.get(
                            "severidad_base"
                        ),
                    "descripcion":
                        row.get(
                            "descripcion"
                        ),
                },
                "fuente": nivel,
                "margen_esperado":
                    float(
                        _safe_decimal(
                            row.get(
                                "margen_esperado"
                            )
                        )
                    ),
            }

    return {
        "regla": None,
        "fuente": "SIN_REGLA",
        "margen_esperado": None,
    }


# =============================================================================
# UMBRALES DE SEVERIDAD
# =============================================================================

def obtener_umbrales_severidad() -> List[Dict]:
    """
    Obtiene los umbrales de severidad configurados.

    Returns:
        Lista de umbrales ordenados por orden
    """
    conn = _get_conn()

    query = """
    SELECT
        CAST(UmbralID AS NVARCHAR(36)) as umbral_id,
        Severidad as Severidad,
        PuntosDesde as puntos_desde,
        PuntosHasta as puntos_hasta,
        IncluirUtilidadNegativa as incluir_utilidad_negativa,
        IncluirCostoMayorPrecio as incluir_costo_mayor_precio,
        Descripcion as Descripcion,
        ColorHex as color,
        Activo as Activo,
        Orden as Orden
    FROM Comercial_AlertasUmbralesSeveridad
    WHERE Activo = 1
    ORDER BY Orden
    """

    rows = execute_sql_query(*conn, query) or []

    return [
        {
            'umbral_id': row.get('umbral_id'),
            'severidad': row.get('severidad'),
            'puntos_desde': float(_safe_decimal(row.get('puntos_desde'))),
            'puntos_hasta': float(_safe_decimal(row.get('puntos_hasta'))),
            'incluir_utilidad_negativa': bool(row.get('incluir_utilidad_negativa')),
            'incluir_costo_mayor_precio': bool(row.get('incluir_costo_mayor_precio')),
            'descripcion': row.get('descripcion'),
            'color': row.get('color'),
            'activo': bool(row.get('activo')),
            'orden': row.get('orden')
        }
        for row in rows
    ]


def determinar_severidad(diferencia_puntos: float, utilidad_negativa: bool = False, costo_mayor_precio: bool = False) -> str:
    """
    Determina la severidad de una alerta basada en la diferencia de margen.

    Args:
        diferencia_puntos: Diferencia en puntos porcentuales (margen_esperado - margen_actual)
        utilidad_negativa: Si la utilidad es negativa
        costo_mayor_precio: Si el costo es mayor al precio

    Returns:
        Severidad: INFORMATIVA, MEDIA, ALTA, CRITICA
    """
    umbrales = obtener_umbrales_severidad()

    # Primero verificar condiciones críticas
    if utilidad_negativa or costo_mayor_precio:
        for u in umbrales:
            if u['incluir_utilidad_negativa'] or u['incluir_costo_mayor_precio']:
                return u['severidad']
        return 'CRITICA'  # Default si no hay umbral configurado

    # Buscar umbral por puntos
    for u in umbrales:
        if u['puntos_desde'] <= diferencia_puntos <= u['puntos_hasta']:
            return u['severidad']

    # Si excede todos los umbrales, es crítica
    if diferencia_puntos > 10:
        return 'CRITICA'

    return 'INFORMATIVA'


# =============================================================================
# ESTADÍSTICAS Y CONTEOS
# =============================================================================

def obtener_estadisticas_reglas() -> Dict:
    """
    Obtiene estadísticas generales de las reglas configuradas.

    Returns:
        Dict con estadísticas
    """
    conn = _get_conn()

    query = """
    SELECT
        COUNT(*) as total_reglas,
        SUM(CASE WHEN Activo = 1 THEN 1 ELSE 0 END) as reglas_activas,
        SUM(CASE WHEN NivelAplicacion = 'GRUPO' AND Activo = 1 THEN 1 ELSE 0 END) as reglas_grupo,
        SUM(CASE WHEN NivelAplicacion = 'FAMILIA' AND Activo = 1 THEN 1 ELSE 0 END) as reglas_familia,
        SUM(CASE WHEN NivelAplicacion = 'SUBFAMILIA' AND Activo = 1 THEN 1 ELSE 0 END) as reglas_subfamilia,
        SUM(CASE WHEN NivelAplicacion = 'PRODUCTO' AND Activo = 1 THEN 1 ELSE 0 END) as reglas_producto,
        AVG(CASE WHEN Activo = 1 THEN MargenPorcentajeEsperado ELSE NULL END) as margen_promedio
    FROM Comercial_AlertasMargenReglas
    """

    rows = execute_sql_query(*conn, query)

    if not rows:
        return {
            'total_reglas': 0,
            'reglas_activas': 0,
            'por_nivel': {
                'GRUPO': 0,
                'FAMILIA': 0,
                'SUBFAMILIA': 0,
                'PRODUCTO': 0
            },
            'margen_promedio': None
        }

    row = rows[0]
    return {
        'total_reglas': row.get('total_reglas', 0),
        'reglas_activas': row.get('reglas_activas', 0),
        'por_nivel': {
            'GRUPO': row.get('reglas_grupo', 0),
            'FAMILIA': row.get('reglas_familia', 0),
            'SUBFAMILIA': row.get('reglas_subfamilia', 0),
            'PRODUCTO': row.get('reglas_producto', 0)
        },
        'margen_promedio': float(_safe_decimal(row.get('margen_promedio'))) if row.get('margen_promedio') else None
    }


def cargar_reglas_margen_vigentes(
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None,
) -> List[Dict]:
    """
    Precarga reglas de margen vigentes para resolucion en lote.

    Esta funcion NO define precedencia de niveles.
    Solo recupera reglas compatibles con el alcance solicitado.

    La semantica de cascada permanece fuera del acceso a datos.
    """
    conn = _get_conn()

    alcance_clauses = []
    alcance_params = []

    if empresa_id:
        alcance_clauses.append(
            "(EmpresaID IS NULL OR EmpresaID = %s)"
        )
        alcance_params.append(
            int(empresa_id)
        )
    else:
        alcance_clauses.append(
            "(EmpresaID IS NULL)"
        )

    if sucursal_id:
        alcance_clauses.append(
            "(SucursalID IS NULL OR SucursalID = %s)"
        )
        alcance_params.append(
            int(sucursal_id)
        )
    else:
        alcance_clauses.append(
            "(SucursalID IS NULL)"
        )

    if server_id:
        alcance_clauses.append(
            "("
            "ServerID IS NULL "
            "OR ServerID = CAST(%s AS UNIQUEIDENTIFIER)"
            ")"
        )
        alcance_params.append(
            str(server_id)
        )
    else:
        alcance_clauses.append(
            "(ServerID IS NULL)"
        )

    alcance_sql = " AND ".join(
        alcance_clauses
    )

    query = f"""
    SELECT
        CAST(
            ReglaMargenID
            AS NVARCHAR(36)
        ) AS regla_id,
        NivelAplicacion AS nivel_aplicacion,
        ProductoClave AS producto_clave,
        SubfamiliaCodigo AS subfamilia_codigo,
        ProductoID AS producto_id,
        FamiliaCodigo AS familia_codigo,
        GrupoCodigo AS grupo_codigo,
        MargenPorcentajeEsperado AS margen_esperado,
        CostoMaximoPorcentaje AS costo_maximo,
        UtilidadMinimaPorcentaje AS utilidad_minima,
        SeveridadBase AS severidad_base,
        Descripcion AS descripcion,
        EmpresaID AS empresa_id,
        SucursalID AS sucursal_id,
        CAST(
            ServerID AS NVARCHAR(36)
        ) AS server_id,
        FechaCreacion AS fecha_creacion
    FROM Comercial_AlertasMargenReglas
    WHERE Activo = 1
      AND FechaInicioVigencia <= GETDATE()
      AND (
            FechaFinVigencia IS NULL
            OR FechaFinVigencia > GETDATE()
          )
      AND {alcance_sql}
    """

    rows = execute_sql_query_params(
        *conn,
        query,
        tuple(alcance_params),
    )

    return [
        dict(row)
        for row in (rows or [])
    ]
