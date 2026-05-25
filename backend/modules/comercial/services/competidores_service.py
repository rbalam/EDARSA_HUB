"""
FASE 1C-3I-B: Servicio de Competidores y Menú Items

Este módulo gestiona:
- Catálogo de competidores por unidad de negocio
- Items de menú de los competidores (precios capturados)

TABLAS:
- Comercial_Competidores
- Comercial_CompetidoresMenuItems

REGLAS:
- NO ejecutar IA en esta fase
- Solo CRUD y consultas
- DELETE es baja lógica (Activo = 0)
- RBAC obligatorio
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
import logging
import uuid
import json

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG

from .pricing_schemas import (
    CompetidorCreate,
    CompetidorUpdate,
    CompetidorResponse,
    CompetidorMenuItemCreate,
    CompetidorMenuItemUpdate,
    CompetidorMenuItemResponse,
)

logger = logging.getLogger(__name__)


def _get_conn() -> Tuple:
    """Retorna parámetros de conexión a EDARSAHUB."""
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )


def _row_to_competidor(row: Dict) -> CompetidorResponse:
    """Convierte fila SQL a CompetidorResponse."""
    return CompetidorResponse(
        competidor_id=str(row.get('CompetidorID', '')),
        empresa_id=row.get('EmpresaID', 0),
        unidad_negocio_id=row.get('UnidadNegocioID', 0),
        nombre_competidor=row.get('NombreCompetidor', ''),
        tipo_restaurante=row.get('TipoRestaurante'),
        segmento_precio=row.get('SegmentoPrecio'),
        ciudad=row.get('Ciudad'),
        estado=row.get('Estado'),
        pais=row.get('Pais', 'México'),
        zona_comercial=row.get('ZonaComercial'),
        sitio_web=row.get('SitioWeb'),
        url_menu=row.get('UrlMenu'),
        url_google_maps=row.get('UrlGoogleMaps'),
        url_instagram=row.get('UrlInstagram'),
        url_facebook=row.get('UrlFacebook'),
        url_tripadvisor=row.get('UrlTripAdvisor'),
        url_opentable=row.get('UrlOpenTable'),
        notas=row.get('Notas'),
        es_competencia_directa=bool(row.get('EsCompetenciaDirecta', True)),
        es_benchmark_aspiracional=bool(row.get('EsBenchmarkAspiracional', False)),
        distancia_km=float(row['DistanciaKm']) if row.get('DistanciaKm') else None,
        prioridad=row.get('Prioridad', 0),
        activo=bool(row.get('Activo', True)),
        fecha_creacion=row.get('FechaCreacion') or datetime.now(),
        usuario_creacion=row.get('UsuarioCreacion'),
        fecha_modificacion=row.get('FechaModificacion'),
        usuario_modificacion=row.get('UsuarioModificacion'),
        total_menu_items=row.get('TotalMenuItems', 0),
    )


def _row_to_menu_item(row: Dict) -> CompetidorMenuItemResponse:
    """Convierte fila SQL a CompetidorMenuItemResponse."""
    # Parsear payload JSON si existe
    payload = None
    if row.get('PayloadJSON'):
        try:
            payload = json.loads(row['PayloadJSON'])
        except (json.JSONDecodeError, TypeError):
            payload = None
    
    return CompetidorMenuItemResponse(
        competidor_menu_item_id=str(row.get('CompetidorMenuItemID', '')),
        competidor_id=str(row.get('CompetidorID', '')),
        nombre_producto_competidor=row.get('NombreProductoCompetidor', ''),
        categoria_competidor=row.get('CategoriaCompetidor'),
        descripcion=row.get('Descripcion'),
        precio=float(row.get('Precio', 0)),
        moneda=row.get('Moneda', 'MXN'),
        fuente_url=row.get('FuenteUrl'),
        fecha_consulta=row.get('FechaConsulta'),
        metodo_obtencion=row.get('MetodoObtencion', 'MANUAL'),
        confianza_dato=row.get('ConfianzaDato', 'MEDIA'),
        es_dato_manual=bool(row.get('EsDatoManual', True)),
        es_dato_ia=bool(row.get('EsDatoIA', False)),
        activo=bool(row.get('Activo', True)),
        payload_json=payload,
        fecha_creacion=row.get('FechaCreacion') or datetime.now(),
        usuario_creacion=row.get('UsuarioCreacion'),
        nombre_competidor=row.get('NombreCompetidor'),
    )


# =============================================================================
# CRUD COMPETIDORES
# =============================================================================

def listar_competidores(
    empresa_id: Optional[int] = None,
    unidad_negocio_id: Optional[int] = None,
    solo_activos: bool = True,
    solo_directos: Optional[bool] = None,
    solo_aspiracionales: Optional[bool] = None,
    page: int = 1,
    page_size: int = 50
) -> Tuple[List[CompetidorResponse], int]:
    """
    Lista competidores con filtros opcionales.
    """
    conn = _get_conn()
    
    where_clauses = []
    if empresa_id:
        where_clauses.append(f"c.EmpresaID = {empresa_id}")
    if unidad_negocio_id:
        where_clauses.append(f"c.UnidadNegocioID = {unidad_negocio_id}")
    if solo_activos:
        where_clauses.append("c.Activo = 1")
    if solo_directos is not None:
        where_clauses.append(f"c.EsCompetenciaDirecta = {1 if solo_directos else 0}")
    if solo_aspiracionales is not None:
        where_clauses.append(f"c.EsBenchmarkAspiracional = {1 if solo_aspiracionales else 0}")
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    # Contar total
    count_query = f"""
    SELECT COUNT(*) as total
    FROM Comercial_Competidores c
    {where_sql}
    """
    count_result = execute_sql_query(*conn, count_query)
    total = count_result[0]['total'] if count_result else 0
    
    # Obtener página con conteo de menu items
    offset = (page - 1) * page_size
    query = f"""
    SELECT 
        CAST(c.CompetidorID AS NVARCHAR(36)) as CompetidorID,
        c.EmpresaID,
        c.UnidadNegocioID,
        c.NombreCompetidor,
        c.TipoRestaurante,
        c.SegmentoPrecio,
        c.Ciudad,
        c.Estado,
        c.Pais,
        c.ZonaComercial,
        c.SitioWeb,
        c.UrlMenu,
        c.UrlGoogleMaps,
        c.UrlInstagram,
        c.UrlFacebook,
        c.UrlTripAdvisor,
        c.UrlOpenTable,
        c.Notas,
        c.EsCompetenciaDirecta,
        c.EsBenchmarkAspiracional,
        c.DistanciaKm,
        c.Prioridad,
        c.Activo,
        c.FechaCreacion,
        c.UsuarioCreacion,
        c.FechaModificacion,
        c.UsuarioModificacion,
        COALESCE(mi.TotalItems, 0) as TotalMenuItems
    FROM Comercial_Competidores c
    LEFT JOIN (
        SELECT CompetidorID, COUNT(*) as TotalItems
        FROM Comercial_CompetidoresMenuItems
        WHERE Activo = 1
        GROUP BY CompetidorID
    ) mi ON c.CompetidorID = mi.CompetidorID
    {where_sql}
    ORDER BY c.Prioridad DESC, c.NombreCompetidor
    OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
    """
    
    result = execute_sql_query(*conn, query)
    
    competidores = [_row_to_competidor(row) for row in (result or [])]
    
    return competidores, total


def obtener_competidor_por_id(competidor_id: str) -> Optional[CompetidorResponse]:
    """
    Obtiene un competidor por su ID.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        CAST(c.CompetidorID AS NVARCHAR(36)) as CompetidorID,
        c.EmpresaID,
        c.UnidadNegocioID,
        c.NombreCompetidor,
        c.TipoRestaurante,
        c.SegmentoPrecio,
        c.Ciudad,
        c.Estado,
        c.Pais,
        c.ZonaComercial,
        c.SitioWeb,
        c.UrlMenu,
        c.UrlGoogleMaps,
        c.UrlInstagram,
        c.UrlFacebook,
        c.UrlTripAdvisor,
        c.UrlOpenTable,
        c.Notas,
        c.EsCompetenciaDirecta,
        c.EsBenchmarkAspiracional,
        c.DistanciaKm,
        c.Prioridad,
        c.Activo,
        c.FechaCreacion,
        c.UsuarioCreacion,
        c.FechaModificacion,
        c.UsuarioModificacion,
        COALESCE(mi.TotalItems, 0) as TotalMenuItems
    FROM Comercial_Competidores c
    LEFT JOIN (
        SELECT CompetidorID, COUNT(*) as TotalItems
        FROM Comercial_CompetidoresMenuItems
        WHERE Activo = 1
        GROUP BY CompetidorID
    ) mi ON c.CompetidorID = mi.CompetidorID
    WHERE c.CompetidorID = '{competidor_id}'
    """
    
    result = execute_sql_query(*conn, query)
    
    if result and len(result) > 0:
        return _row_to_competidor(result[0])
    
    return None


def crear_competidor(data: CompetidorCreate, usuario: str) -> CompetidorResponse:
    """
    Crea un nuevo competidor.
    """
    conn = _get_conn()
    
    competidor_id = str(uuid.uuid4())
    
    # Preparar valores SQL
    tipo_rest_sql = f"'{data.tipo_restaurante.value}'" if data.tipo_restaurante else "NULL"
    segmento_sql = f"'{data.segmento_precio.value}'" if data.segmento_precio else "NULL"
    ciudad_sql = f"N'{data.ciudad}'" if data.ciudad else "NULL"
    estado_sql = f"N'{data.estado}'" if data.estado else "NULL"
    zona_sql = f"N'{data.zona_comercial}'" if data.zona_comercial else "NULL"
    
    sitio_web_sql = f"N'{data.sitio_web}'" if data.sitio_web else "NULL"
    url_menu_sql = f"N'{data.url_menu}'" if data.url_menu else "NULL"
    url_maps_sql = f"N'{data.url_google_maps}'" if data.url_google_maps else "NULL"
    url_insta_sql = f"N'{data.url_instagram}'" if data.url_instagram else "NULL"
    url_fb_sql = f"N'{data.url_facebook}'" if data.url_facebook else "NULL"
    url_trip_sql = f"N'{data.url_tripadvisor}'" if data.url_tripadvisor else "NULL"
    url_opentable_sql = f"N'{data.url_opentable}'" if data.url_opentable else "NULL"
    notas_sql = f"N'{data.notas}'" if data.notas else "NULL"
    
    distancia_sql = f"{data.distancia_km}" if data.distancia_km is not None else "NULL"
    
    insert_query = f"""
    INSERT INTO Comercial_Competidores (
        CompetidorID,
        EmpresaID,
        UnidadNegocioID,
        NombreCompetidor,
        TipoRestaurante,
        SegmentoPrecio,
        Ciudad,
        Estado,
        Pais,
        ZonaComercial,
        SitioWeb,
        UrlMenu,
        UrlGoogleMaps,
        UrlInstagram,
        UrlFacebook,
        UrlTripAdvisor,
        UrlOpenTable,
        Notas,
        EsCompetenciaDirecta,
        EsBenchmarkAspiracional,
        DistanciaKm,
        Prioridad,
        Activo,
        FechaCreacion,
        UsuarioCreacion
    ) VALUES (
        '{competidor_id}',
        {data.empresa_id},
        {data.unidad_negocio_id},
        N'{data.nombre_competidor}',
        {tipo_rest_sql},
        {segmento_sql},
        {ciudad_sql},
        {estado_sql},
        N'{data.pais}',
        {zona_sql},
        {sitio_web_sql},
        {url_menu_sql},
        {url_maps_sql},
        {url_insta_sql},
        {url_fb_sql},
        {url_trip_sql},
        {url_opentable_sql},
        {notas_sql},
        {1 if data.es_competencia_directa else 0},
        {1 if data.es_benchmark_aspiracional else 0},
        {distancia_sql},
        {data.prioridad},
        1,
        GETDATE(),
        N'{usuario}'
    )
    """
    
    execute_sql_query(*conn, insert_query)
    logger.info(f"[COMPETIDOR] Creado {competidor_id}: {data.nombre_competidor} por {usuario}")
    
    return obtener_competidor_por_id(competidor_id)


def actualizar_competidor(
    competidor_id: str,
    data: CompetidorUpdate,
    usuario: str
) -> Optional[CompetidorResponse]:
    """
    Actualiza un competidor existente.
    """
    conn = _get_conn()
    
    # Verificar que existe
    competidor_actual = obtener_competidor_por_id(competidor_id)
    if not competidor_actual:
        return None
    
    set_clauses = []
    
    if data.nombre_competidor is not None:
        set_clauses.append(f"NombreCompetidor = N'{data.nombre_competidor}'")
    if data.tipo_restaurante is not None:
        set_clauses.append(f"TipoRestaurante = '{data.tipo_restaurante.value}'")
    if data.segmento_precio is not None:
        set_clauses.append(f"SegmentoPrecio = '{data.segmento_precio.value}'")
    if data.ciudad is not None:
        set_clauses.append(f"Ciudad = N'{data.ciudad}'")
    if data.estado is not None:
        set_clauses.append(f"Estado = N'{data.estado}'")
    if data.pais is not None:
        set_clauses.append(f"Pais = N'{data.pais}'")
    if data.zona_comercial is not None:
        set_clauses.append(f"ZonaComercial = N'{data.zona_comercial}'")
    
    if data.sitio_web is not None:
        set_clauses.append(f"SitioWeb = N'{data.sitio_web}'")
    if data.url_menu is not None:
        set_clauses.append(f"UrlMenu = N'{data.url_menu}'")
    if data.url_google_maps is not None:
        set_clauses.append(f"UrlGoogleMaps = N'{data.url_google_maps}'")
    if data.url_instagram is not None:
        set_clauses.append(f"UrlInstagram = N'{data.url_instagram}'")
    if data.url_facebook is not None:
        set_clauses.append(f"UrlFacebook = N'{data.url_facebook}'")
    if data.url_tripadvisor is not None:
        set_clauses.append(f"UrlTripAdvisor = N'{data.url_tripadvisor}'")
    if data.url_opentable is not None:
        set_clauses.append(f"UrlOpenTable = N'{data.url_opentable}'")
    if data.notas is not None:
        set_clauses.append(f"Notas = N'{data.notas}'")
    
    if data.es_competencia_directa is not None:
        set_clauses.append(f"EsCompetenciaDirecta = {1 if data.es_competencia_directa else 0}")
    if data.es_benchmark_aspiracional is not None:
        set_clauses.append(f"EsBenchmarkAspiracional = {1 if data.es_benchmark_aspiracional else 0}")
    if data.distancia_km is not None:
        set_clauses.append(f"DistanciaKm = {data.distancia_km}")
    if data.prioridad is not None:
        set_clauses.append(f"Prioridad = {data.prioridad}")
    
    if not set_clauses:
        return competidor_actual
    
    set_clauses.append("FechaModificacion = GETDATE()")
    set_clauses.append(f"UsuarioModificacion = N'{usuario}'")
    
    set_sql = ", ".join(set_clauses)
    
    update_query = f"""
    UPDATE Comercial_Competidores
    SET {set_sql}
    WHERE CompetidorID = '{competidor_id}'
    """
    
    execute_sql_query(*conn, update_query)
    logger.info(f"[COMPETIDOR] Actualizado {competidor_id} por {usuario}")
    
    return obtener_competidor_por_id(competidor_id)


def inactivar_competidor(competidor_id: str, usuario: str) -> bool:
    """
    Inactiva un competidor (baja lógica).
    También inactiva sus menu items.
    """
    conn = _get_conn()
    
    # Inactivar menu items
    update_items_query = f"""
    UPDATE Comercial_CompetidoresMenuItems
    SET Activo = 0
    WHERE CompetidorID = '{competidor_id}'
    """
    execute_sql_query(*conn, update_items_query)
    
    # Inactivar competidor
    update_query = f"""
    UPDATE Comercial_Competidores
    SET Activo = 0,
        FechaModificacion = GETDATE(),
        UsuarioModificacion = N'{usuario}'
    WHERE CompetidorID = '{competidor_id}'
    """
    
    execute_sql_query(*conn, update_query)
    logger.info(f"[COMPETIDOR] Inactivado {competidor_id} por {usuario}")
    
    return True


# =============================================================================
# CRUD MENU ITEMS
# =============================================================================

def listar_menu_items(
    competidor_id: str,
    categoria: Optional[str] = None,
    solo_activos: bool = True,
    page: int = 1,
    page_size: int = 100
) -> Tuple[List[CompetidorMenuItemResponse], int]:
    """
    Lista items de menú de un competidor.
    """
    conn = _get_conn()
    
    where_clauses = [f"mi.CompetidorID = '{competidor_id}'"]
    if solo_activos:
        where_clauses.append("mi.Activo = 1")
    if categoria:
        where_clauses.append(f"mi.CategoriaCompetidor = N'{categoria}'")
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}"
    
    # Contar total
    count_query = f"""
    SELECT COUNT(*) as total
    FROM Comercial_CompetidoresMenuItems mi
    {where_sql}
    """
    count_result = execute_sql_query(*conn, count_query)
    total = count_result[0]['total'] if count_result else 0
    
    # Obtener página
    offset = (page - 1) * page_size
    query = f"""
    SELECT 
        CAST(mi.CompetidorMenuItemID AS NVARCHAR(36)) as CompetidorMenuItemID,
        CAST(mi.CompetidorID AS NVARCHAR(36)) as CompetidorID,
        mi.NombreProductoCompetidor,
        mi.CategoriaCompetidor,
        mi.Descripcion,
        mi.Precio,
        mi.Moneda,
        mi.FuenteUrl,
        mi.FechaConsulta,
        mi.MetodoObtencion,
        mi.ConfianzaDato,
        mi.EsDatoManual,
        mi.EsDatoIA,
        mi.Activo,
        mi.PayloadJSON,
        mi.FechaCreacion,
        mi.UsuarioCreacion,
        c.NombreCompetidor
    FROM Comercial_CompetidoresMenuItems mi
    JOIN Comercial_Competidores c ON mi.CompetidorID = c.CompetidorID
    {where_sql}
    ORDER BY mi.CategoriaCompetidor, mi.NombreProductoCompetidor
    OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
    """
    
    result = execute_sql_query(*conn, query)
    
    items = [_row_to_menu_item(row) for row in (result or [])]
    
    return items, total


def obtener_menu_item_por_id(menu_item_id: str) -> Optional[CompetidorMenuItemResponse]:
    """
    Obtiene un menu item por su ID.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        CAST(mi.CompetidorMenuItemID AS NVARCHAR(36)) as CompetidorMenuItemID,
        CAST(mi.CompetidorID AS NVARCHAR(36)) as CompetidorID,
        mi.NombreProductoCompetidor,
        mi.CategoriaCompetidor,
        mi.Descripcion,
        mi.Precio,
        mi.Moneda,
        mi.FuenteUrl,
        mi.FechaConsulta,
        mi.MetodoObtencion,
        mi.ConfianzaDato,
        mi.EsDatoManual,
        mi.EsDatoIA,
        mi.Activo,
        mi.PayloadJSON,
        mi.FechaCreacion,
        mi.UsuarioCreacion,
        c.NombreCompetidor
    FROM Comercial_CompetidoresMenuItems mi
    JOIN Comercial_Competidores c ON mi.CompetidorID = c.CompetidorID
    WHERE mi.CompetidorMenuItemID = '{menu_item_id}'
    """
    
    result = execute_sql_query(*conn, query)
    
    if result and len(result) > 0:
        return _row_to_menu_item(result[0])
    
    return None


def crear_menu_item(data: CompetidorMenuItemCreate, usuario: str) -> CompetidorMenuItemResponse:
    """
    Crea un nuevo item de menú de competidor.
    """
    conn = _get_conn()
    
    menu_item_id = str(uuid.uuid4())
    
    # Preparar valores SQL
    categoria_sql = f"N'{data.categoria_competidor}'" if data.categoria_competidor else "NULL"
    descripcion_sql = f"N'{data.descripcion}'" if data.descripcion else "NULL"
    fuente_sql = f"N'{data.fuente_url}'" if data.fuente_url else "NULL"
    fecha_consulta_sql = f"'{data.fecha_consulta.isoformat()}'" if data.fecha_consulta else "GETDATE()"
    payload_sql = f"N'{json.dumps(data.payload_json)}'" if data.payload_json else "NULL"
    
    insert_query = f"""
    INSERT INTO Comercial_CompetidoresMenuItems (
        CompetidorMenuItemID,
        CompetidorID,
        NombreProductoCompetidor,
        CategoriaCompetidor,
        Descripcion,
        Precio,
        Moneda,
        FuenteUrl,
        FechaConsulta,
        MetodoObtencion,
        ConfianzaDato,
        EsDatoManual,
        EsDatoIA,
        Activo,
        PayloadJSON,
        FechaCreacion,
        UsuarioCreacion
    ) VALUES (
        '{menu_item_id}',
        '{data.competidor_id}',
        N'{data.nombre_producto_competidor}',
        {categoria_sql},
        {descripcion_sql},
        {data.precio},
        '{data.moneda}',
        {fuente_sql},
        {fecha_consulta_sql},
        '{data.metodo_obtencion.value}',
        '{data.confianza_dato.value}',
        {1 if data.es_dato_manual else 0},
        {1 if data.es_dato_ia else 0},
        1,
        {payload_sql},
        GETDATE(),
        N'{usuario}'
    )
    """
    
    execute_sql_query(*conn, insert_query)
    logger.info(f"[MENU-ITEM] Creado {menu_item_id}: {data.nombre_producto_competidor} por {usuario}")
    
    return obtener_menu_item_por_id(menu_item_id)


def actualizar_menu_item(
    menu_item_id: str,
    data: CompetidorMenuItemUpdate,
    usuario: str
) -> Optional[CompetidorMenuItemResponse]:
    """
    Actualiza un menu item existente.
    """
    conn = _get_conn()
    
    # Verificar que existe
    item_actual = obtener_menu_item_por_id(menu_item_id)
    if not item_actual:
        return None
    
    set_clauses = []
    
    if data.nombre_producto_competidor is not None:
        set_clauses.append(f"NombreProductoCompetidor = N'{data.nombre_producto_competidor}'")
    if data.categoria_competidor is not None:
        set_clauses.append(f"CategoriaCompetidor = N'{data.categoria_competidor}'")
    if data.descripcion is not None:
        set_clauses.append(f"Descripcion = N'{data.descripcion}'")
    if data.precio is not None:
        set_clauses.append(f"Precio = {data.precio}")
    if data.moneda is not None:
        set_clauses.append(f"Moneda = '{data.moneda}'")
    if data.fuente_url is not None:
        set_clauses.append(f"FuenteUrl = N'{data.fuente_url}'")
    if data.fecha_consulta is not None:
        set_clauses.append(f"FechaConsulta = '{data.fecha_consulta.isoformat()}'")
    if data.metodo_obtencion is not None:
        set_clauses.append(f"MetodoObtencion = '{data.metodo_obtencion.value}'")
    if data.confianza_dato is not None:
        set_clauses.append(f"ConfianzaDato = '{data.confianza_dato.value}'")
    if data.es_dato_manual is not None:
        set_clauses.append(f"EsDatoManual = {1 if data.es_dato_manual else 0}")
    if data.es_dato_ia is not None:
        set_clauses.append(f"EsDatoIA = {1 if data.es_dato_ia else 0}")
    if data.payload_json is not None:
        set_clauses.append(f"PayloadJSON = N'{json.dumps(data.payload_json)}'")
    
    if not set_clauses:
        return item_actual
    
    set_sql = ", ".join(set_clauses)
    
    update_query = f"""
    UPDATE Comercial_CompetidoresMenuItems
    SET {set_sql}
    WHERE CompetidorMenuItemID = '{menu_item_id}'
    """
    
    execute_sql_query(*conn, update_query)
    logger.info(f"[MENU-ITEM] Actualizado {menu_item_id} por {usuario}")
    
    return obtener_menu_item_por_id(menu_item_id)


def inactivar_menu_item(menu_item_id: str, usuario: str) -> bool:
    """
    Inactiva un menu item (baja lógica).
    """
    conn = _get_conn()
    
    update_query = f"""
    UPDATE Comercial_CompetidoresMenuItems
    SET Activo = 0
    WHERE CompetidorMenuItemID = '{menu_item_id}'
    """
    
    execute_sql_query(*conn, update_query)
    logger.info(f"[MENU-ITEM] Inactivado {menu_item_id} por {usuario}")
    
    return True


# =============================================================================
# HELPERS
# =============================================================================

def obtener_estadisticas_competidores(unidad_negocio_id: int) -> Dict[str, Any]:
    """
    Obtiene estadísticas de competidores para una unidad.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        COUNT(*) as total_competidores,
        SUM(CASE WHEN EsCompetenciaDirecta = 1 THEN 1 ELSE 0 END) as directos,
        SUM(CASE WHEN EsBenchmarkAspiracional = 1 THEN 1 ELSE 0 END) as aspiracionales
    FROM Comercial_Competidores
    WHERE UnidadNegocioID = {unidad_negocio_id}
      AND Activo = 1
    """
    
    result = execute_sql_query(*conn, query)
    
    if result and len(result) > 0:
        row = result[0]
        return {
            'total_competidores': row.get('total_competidores', 0) or 0,
            'directos': row.get('directos', 0) or 0,
            'aspiracionales': row.get('aspiracionales', 0) or 0
        }
    
    return {'total_competidores': 0, 'directos': 0, 'aspiracionales': 0}


def obtener_estadisticas_menu_items(unidad_negocio_id: int) -> Dict[str, Any]:
    """
    Obtiene estadísticas de items de menú capturados para una unidad.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        COUNT(mi.CompetidorMenuItemID) as total_items,
        SUM(CASE WHEN mi.ConfianzaDato = 'ALTA' THEN 1 ELSE 0 END) as alta_confianza,
        SUM(CASE WHEN mi.ConfianzaDato = 'MEDIA' THEN 1 ELSE 0 END) as media_confianza,
        SUM(CASE WHEN mi.ConfianzaDato = 'BAJA' THEN 1 ELSE 0 END) as baja_confianza,
        SUM(CASE WHEN mi.EsDatoManual = 1 THEN 1 ELSE 0 END) as manuales,
        SUM(CASE WHEN mi.EsDatoIA = 1 THEN 1 ELSE 0 END) as por_ia,
        MAX(mi.FechaCreacion) as ultima_captura
    FROM Comercial_CompetidoresMenuItems mi
    JOIN Comercial_Competidores c ON mi.CompetidorID = c.CompetidorID
    WHERE c.UnidadNegocioID = {unidad_negocio_id}
      AND mi.Activo = 1
      AND c.Activo = 1
    """
    
    result = execute_sql_query(*conn, query)
    
    if result and len(result) > 0:
        row = result[0]
        return {
            'total_items': row.get('total_items', 0) or 0,
            'alta_confianza': row.get('alta_confianza', 0) or 0,
            'media_confianza': row.get('media_confianza', 0) or 0,
            'baja_confianza': row.get('baja_confianza', 0) or 0,
            'manuales': row.get('manuales', 0) or 0,
            'por_ia': row.get('por_ia', 0) or 0,
            'ultima_captura': row.get('ultima_captura')
        }
    
    return {
        'total_items': 0,
        'alta_confianza': 0,
        'media_confianza': 0,
        'baja_confianza': 0,
        'manuales': 0,
        'por_ia': 0,
        'ultima_captura': None
    }


__all__ = [
    # Competidores
    'listar_competidores',
    'obtener_competidor_por_id',
    'crear_competidor',
    'actualizar_competidor',
    'inactivar_competidor',
    
    # Menu Items
    'listar_menu_items',
    'obtener_menu_item_por_id',
    'crear_menu_item',
    'actualizar_menu_item',
    'inactivar_menu_item',
    
    # Helpers
    'obtener_estadisticas_competidores',
    'obtener_estadisticas_menu_items',
]
