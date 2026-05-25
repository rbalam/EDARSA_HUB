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

from core.db import execute_sql_query
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
    except:
        return default


# =============================================================================
# CRUD DE REGLAS DE MARGEN
# =============================================================================

def listar_reglas(
    nivel_aplicacion: Optional[str] = None,
    solo_activas: bool = True,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
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
    
    if nivel_aplicacion:
        where_clauses.append(f"NivelAplicacion = '{nivel_aplicacion}'")
    
    if solo_activas:
        where_clauses.append("Activo = 1")
        where_clauses.append("(FechaFinVigencia IS NULL OR FechaFinVigencia > GETDATE())")
        where_clauses.append("FechaInicioVigencia <= GETDATE()")
    
    if empresa_id:
        where_clauses.append(f"(EmpresaID IS NULL OR EmpresaID = {empresa_id})")
    
    if sucursal_id:
        where_clauses.append(f"(SucursalID IS NULL OR SucursalID = {sucursal_id})")
    
    where_sql = " AND ".join(where_clauses)
    offset = (page - 1) * page_size
    
    # Contar total
    count_query = f"SELECT COUNT(*) as total FROM Comercial_AlertasMargenReglas WHERE {where_sql}"
    count_result = execute_sql_query(*conn, count_query)
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
        EmpresaID as empresa_id,
        SucursalID as sucursal_id,
        CAST(ServerID AS NVARCHAR(36)) as server_id,
        MargenPorcentajeEsperado as margen_esperado,
        CostoMaximoPorcentaje as costo_maximo,
        UtilidadMinimaPorcentaje as utilidad_minima,
        SeveridadBase as severidad_base,
        Descripcion as descripcion,
        Activo as activo,
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
    OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
    """
    
    rows = execute_sql_query(*conn, data_query) or []
    
    reglas = []
    for row in rows:
        reglas.append({
            'regla_id': row.get('regla_id'),
            'nivel_aplicacion': row.get('nivel_aplicacion'),
            'grupo_codigo': row.get('grupo_codigo'),
            'familia_codigo': row.get('familia_codigo'),
            'subfamilia_codigo': row.get('subfamilia_codigo'),
            'producto_clave': row.get('producto_clave'),
            'empresa_id': row.get('empresa_id'),
            'sucursal_id': row.get('sucursal_id'),
            'server_id': row.get('server_id'),
            'margen_esperado': float(_safe_decimal(row.get('margen_esperado'))),
            'costo_maximo': float(_safe_decimal(row.get('costo_maximo'))) if row.get('costo_maximo') else None,
            'utilidad_minima': float(_safe_decimal(row.get('utilidad_minima'))) if row.get('utilidad_minima') else None,
            'severidad_base': row.get('severidad_base'),
            'descripcion': row.get('descripcion'),
            'activo': bool(row.get('activo')),
            'fecha_inicio': row.get('fecha_inicio').isoformat() if row.get('fecha_inicio') else None,
            'fecha_fin': row.get('fecha_fin').isoformat() if row.get('fecha_fin') else None,
            'fecha_creacion': row.get('fecha_creacion').isoformat() if row.get('fecha_creacion') else None,
            'fecha_modificacion': row.get('fecha_modificacion').isoformat() if row.get('fecha_modificacion') else None,
            'creado_por': row.get('creado_por'),
            'modificado_por': row.get('modificado_por'),
            # Entidad aplicable según nivel
            'entidad_codigo': (
                row.get('producto_clave') or 
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
    
    query = f"""
    SELECT 
        CAST(ReglaMargenID AS NVARCHAR(36)) as regla_id,
        NivelAplicacion as nivel_aplicacion,
        GrupoCodigo as grupo_codigo,
        FamiliaCodigo as familia_codigo,
        SubfamiliaCodigo as subfamilia_codigo,
        ProductoClave as producto_clave,
        EmpresaID as empresa_id,
        SucursalID as sucursal_id,
        CAST(ServerID AS NVARCHAR(36)) as server_id,
        MargenPorcentajeEsperado as margen_esperado,
        CostoMaximoPorcentaje as costo_maximo,
        UtilidadMinimaPorcentaje as utilidad_minima,
        SeveridadBase as severidad_base,
        Descripcion as descripcion,
        Activo as activo,
        FechaInicioVigencia as fecha_inicio,
        FechaFinVigencia as fecha_fin,
        FechaCreacion as fecha_creacion,
        FechaModificacion as fecha_modificacion,
        CreadoPor as creado_por,
        ModificadoPor as modificado_por
    FROM Comercial_AlertasMargenReglas
    WHERE ReglaMargenID = '{regla_id}'
    """
    
    rows = execute_sql_query(*conn, query)
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
        'empresa_id': row.get('empresa_id'),
        'sucursal_id': row.get('sucursal_id'),
        'server_id': row.get('server_id'),
        'margen_esperado': float(_safe_decimal(row.get('margen_esperado'))),
        'costo_maximo': float(_safe_decimal(row.get('costo_maximo'))) if row.get('costo_maximo') else None,
        'utilidad_minima': float(_safe_decimal(row.get('utilidad_minima'))) if row.get('utilidad_minima') else None,
        'severidad_base': row.get('severidad_base'),
        'descripcion': row.get('descripcion'),
        'activo': bool(row.get('activo')),
        'fecha_inicio': row.get('fecha_inicio').isoformat() if row.get('fecha_inicio') else None,
        'fecha_fin': row.get('fecha_fin').isoformat() if row.get('fecha_fin') else None,
        'fecha_creacion': row.get('fecha_creacion').isoformat() if row.get('fecha_creacion') else None,
        'fecha_modificacion': row.get('fecha_modificacion').isoformat() if row.get('fecha_modificacion') else None,
        'creado_por': row.get('creado_por'),
        'modificado_por': row.get('modificado_por'),
        'entidad_codigo': (
            row.get('producto_clave') or 
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
    excluir_regla_id: Optional[str] = None
) -> bool:
    """
    Verifica si ya existe una regla activa para la misma entidad/nivel.
    
    Args:
        nivel_aplicacion: GRUPO, FAMILIA, SUBFAMILIA, PRODUCTO
        entidad_codigo: Código de la entidad según el nivel
        empresa_id: Empresa (opcional)
        sucursal_id: Sucursal (opcional)
        excluir_regla_id: ID de regla a excluir (para edición)
    
    Returns:
        True si existe duplicado, False si no
    """
    conn = _get_conn()
    
    # Determinar campo según nivel
    campo_entidad = {
        'GRUPO': 'GrupoCodigo',
        'FAMILIA': 'FamiliaCodigo',
        'SUBFAMILIA': 'SubfamiliaCodigo',
        'PRODUCTO': 'ProductoClave'
    }.get(nivel_aplicacion)
    
    if not campo_entidad:
        return False
    
    where_clauses = [
        f"NivelAplicacion = '{nivel_aplicacion}'",
        f"{campo_entidad} = '{entidad_codigo}'",
        "Activo = 1",
        "(FechaFinVigencia IS NULL OR FechaFinVigencia > GETDATE())"
    ]
    
    if empresa_id:
        where_clauses.append(f"(EmpresaID IS NULL OR EmpresaID = {empresa_id})")
    else:
        where_clauses.append("EmpresaID IS NULL")
    
    if sucursal_id:
        where_clauses.append(f"(SucursalID IS NULL OR SucursalID = {sucursal_id})")
    else:
        where_clauses.append("SucursalID IS NULL")
    
    if excluir_regla_id:
        where_clauses.append(f"ReglaMargenID != '{excluir_regla_id}'")
    
    where_sql = " AND ".join(where_clauses)
    
    query = f"SELECT COUNT(*) as cnt FROM Comercial_AlertasMargenReglas WHERE {where_sql}"
    result = execute_sql_query(*conn, query)
    
    return (result[0].get('cnt', 0) if result else 0) > 0


def crear_regla(
    nivel_aplicacion: str,
    entidad_codigo: str,
    margen_esperado: float,
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
    
    Args:
        nivel_aplicacion: GRUPO, FAMILIA, SUBFAMILIA, PRODUCTO
        entidad_codigo: Código de la entidad según el nivel
        margen_esperado: Porcentaje de margen esperado (0-100)
        costo_maximo: Porcentaje máximo de costo (opcional)
        utilidad_minima: Porcentaje mínimo de utilidad (opcional)
        severidad_base: INFORMATIVA, MEDIA, ALTA, CRITICA
        descripcion: Descripción de la regla
        empresa_id: Empresa (opcional)
        sucursal_id: Sucursal (opcional)
        server_id: Servidor (opcional)
        fecha_inicio: Fecha de inicio de vigencia
        fecha_fin: Fecha de fin de vigencia
        creado_por: Usuario que crea
    
    Returns:
        Dict con la regla creada
    """
    conn = _get_conn()
    
    regla_id = str(uuid.uuid4()).upper()
    
    # Determinar campo según nivel
    campo_entidad = {
        'GRUPO': 'GrupoCodigo',
        'FAMILIA': 'FamiliaCodigo',
        'SUBFAMILIA': 'SubfamiliaCodigo',
        'PRODUCTO': 'ProductoClave'
    }.get(nivel_aplicacion)
    
    if not campo_entidad:
        raise ValueError(f"Nivel de aplicación inválido: {nivel_aplicacion}")
    
    # Escapar valores
    entidad_escaped = entidad_codigo.replace("'", "''")
    descripcion_escaped = descripcion.replace("'", "''") if descripcion else None
    creado_por_escaped = creado_por.replace("'", "''")
    
    # Construir valores
    fecha_inicio_sql = f"'{fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}'" if fecha_inicio else "GETDATE()"
    fecha_fin_sql = f"'{fecha_fin.strftime('%Y-%m-%d %H:%M:%S')}'" if fecha_fin else "NULL"
    
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
        '{regla_id}',
        '{nivel_aplicacion}',
        '{entidad_escaped}',
        {empresa_id if empresa_id else 'NULL'},
        {sucursal_id if sucursal_id else 'NULL'},
        {f"'{server_id}'" if server_id else 'NULL'},
        {margen_esperado},
        {costo_maximo if costo_maximo is not None else 'NULL'},
        {utilidad_minima if utilidad_minima is not None else 'NULL'},
        '{severidad_base}',
        {f"N'{descripcion_escaped}'" if descripcion_escaped else 'NULL'},
        1,
        {fecha_inicio_sql},
        {fecha_fin_sql},
        GETDATE(),
        '{creado_por_escaped}'
    )
    """
    
    execute_sql_query(*conn, query)
    
    logger.info(f"[ALERTAS_MARGEN] Regla creada: {regla_id} - {nivel_aplicacion}={entidad_codigo}")
    
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
    
    set_clauses = ["FechaModificacion = GETDATE()"]
    set_clauses.append(f"ModificadoPor = '{modificado_por.replace(chr(39), chr(39)+chr(39))}'")
    
    if margen_esperado is not None:
        set_clauses.append(f"MargenPorcentajeEsperado = {margen_esperado}")
    
    if costo_maximo is not None:
        set_clauses.append(f"CostoMaximoPorcentaje = {costo_maximo}")
    
    if utilidad_minima is not None:
        set_clauses.append(f"UtilidadMinimaPorcentaje = {utilidad_minima}")
    
    if severidad_base:
        set_clauses.append(f"SeveridadBase = '{severidad_base}'")
    
    if descripcion is not None:
        desc_escaped = descripcion.replace("'", "''")
        set_clauses.append(f"Descripcion = N'{desc_escaped}'")
    
    if fecha_fin:
        set_clauses.append(f"FechaFinVigencia = '{fecha_fin.strftime('%Y-%m-%d %H:%M:%S')}'")
    
    set_sql = ", ".join(set_clauses)
    
    query = f"UPDATE Comercial_AlertasMargenReglas SET {set_sql} WHERE ReglaMargenID = '{regla_id}'"
    execute_sql_query(*conn, query)
    
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
    
    query = f"""
    UPDATE Comercial_AlertasMargenReglas 
    SET Activo = 0, 
        FechaModificacion = GETDATE(),
        ModificadoPor = '{modificado_por.replace(chr(39), chr(39)+chr(39))}'
    WHERE ReglaMargenID = '{regla_id}'
    """
    execute_sql_query(*conn, query)
    
    logger.info(f"[ALERTAS_MARGEN] Regla desactivada: {regla_id}")
    
    return True


# =============================================================================
# RESOLUCIÓN DE REGLA APLICABLE (JERARQUÍA)
# =============================================================================

def resolver_regla_aplicable(
    producto_clave: Optional[str] = None,
    subfamilia_codigo: Optional[str] = None,
    familia_codigo: Optional[str] = None,
    grupo_codigo: Optional[str] = None,
    empresa_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    server_id: Optional[str] = None
) -> Dict:
    """
    Resuelve la regla de margen aplicable usando la jerarquía:
    Producto > Subfamilia > Familia > Grupo
    
    Args:
        producto_clave: Clave del producto
        subfamilia_codigo: Código de subfamilia
        familia_codigo: Código de familia
        grupo_codigo: Código de grupo
        empresa_id: Empresa (opcional)
        sucursal_id: Sucursal (opcional)
        server_id: Servidor (opcional)
    
    Returns:
        Dict con:
        - regla: La regla aplicable o None
        - fuente: PRODUCTO, SUBFAMILIA, FAMILIA, GRUPO, SIN_REGLA
        - margen_esperado: El margen esperado o None
    """
    conn = _get_conn()
    
    # Construir condiciones de vigencia
    vigencia_sql = """
        Activo = 1 
        AND FechaInicioVigencia <= GETDATE()
        AND (FechaFinVigencia IS NULL OR FechaFinVigencia > GETDATE())
    """
    
    # Construir condiciones de alcance (empresa/sucursal/server)
    alcance_clauses = []
    if empresa_id:
        alcance_clauses.append(f"(EmpresaID IS NULL OR EmpresaID = {empresa_id})")
    else:
        alcance_clauses.append("(EmpresaID IS NULL)")
    
    if sucursal_id:
        alcance_clauses.append(f"(SucursalID IS NULL OR SucursalID = {sucursal_id})")
    else:
        alcance_clauses.append("(SucursalID IS NULL)")
    
    if server_id:
        alcance_clauses.append(f"(ServerID IS NULL OR ServerID = '{server_id}')")
    else:
        alcance_clauses.append("(ServerID IS NULL)")
    
    alcance_sql = " AND ".join(alcance_clauses)
    
    # Buscar en orden de prioridad: Producto > Subfamilia > Familia > Grupo
    niveles = [
        ('PRODUCTO', 'ProductoClave', producto_clave),
        ('SUBFAMILIA', 'SubfamiliaCodigo', subfamilia_codigo),
        ('FAMILIA', 'FamiliaCodigo', familia_codigo),
        ('GRUPO', 'GrupoCodigo', grupo_codigo),
    ]
    
    for nivel, campo, valor in niveles:
        if not valor:
            continue
        
        query = f"""
        SELECT TOP 1
            CAST(ReglaMargenID AS NVARCHAR(36)) as regla_id,
            NivelAplicacion as nivel_aplicacion,
            {campo} as entidad_codigo,
            MargenPorcentajeEsperado as margen_esperado,
            CostoMaximoPorcentaje as costo_maximo,
            UtilidadMinimaPorcentaje as utilidad_minima,
            SeveridadBase as severidad_base,
            Descripcion as descripcion
        FROM Comercial_AlertasMargenReglas
        WHERE NivelAplicacion = '{nivel}'
          AND {campo} = '{valor.replace(chr(39), chr(39)+chr(39))}'
          AND {vigencia_sql}
          AND {alcance_sql}
        ORDER BY 
            CASE WHEN EmpresaID IS NOT NULL THEN 0 ELSE 1 END,
            CASE WHEN SucursalID IS NOT NULL THEN 0 ELSE 1 END,
            FechaCreacion DESC
        """
        
        rows = execute_sql_query(*conn, query)
        
        if rows:
            row = rows[0]
            return {
                'regla': {
                    'regla_id': row.get('regla_id'),
                    'nivel_aplicacion': row.get('nivel_aplicacion'),
                    'entidad_codigo': row.get('entidad_codigo'),
                    'margen_esperado': float(_safe_decimal(row.get('margen_esperado'))),
                    'costo_maximo': float(_safe_decimal(row.get('costo_maximo'))) if row.get('costo_maximo') else None,
                    'utilidad_minima': float(_safe_decimal(row.get('utilidad_minima'))) if row.get('utilidad_minima') else None,
                    'severidad_base': row.get('severidad_base'),
                    'descripcion': row.get('descripcion')
                },
                'fuente': nivel,
                'margen_esperado': float(_safe_decimal(row.get('margen_esperado')))
            }
    
    # Sin regla aplicable
    return {
        'regla': None,
        'fuente': 'SIN_REGLA',
        'margen_esperado': None
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
        Severidad as severidad,
        PuntosDesde as puntos_desde,
        PuntosHasta as puntos_hasta,
        IncluirUtilidadNegativa as incluir_utilidad_negativa,
        IncluirCostoMayorPrecio as incluir_costo_mayor_precio,
        Descripcion as descripcion,
        ColorHex as color,
        Activo as activo,
        Orden as orden
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
