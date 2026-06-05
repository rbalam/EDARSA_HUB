"""
FASE 1C-3I-B: Servicio de Perfil Digital de Unidad de Negocio

Este módulo gestiona los perfiles digitales de las unidades de negocio
que sirven como contexto para el motor de precios con IA y benchmark.

TABLA: Sistema_UnidadesNegocioPerfilDigital

REGLAS:
- NO ejecutar IA en esta fase
- Solo CRUD y consultas
- RBAC obligatorio
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging
import uuid

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG

from .pricing_schemas import (
    PerfilDigitalCreate,
    PerfilDigitalUpdate,
    PerfilDigitalResponse,
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


def _row_to_perfil(row: Dict) -> PerfilDigitalResponse:
    """Convierte fila SQL a PerfilDigitalResponse."""
    return PerfilDigitalResponse(
        perfil_digital_id=str(row.get('PerfilDigitalID', '')),
        empresa_id=row.get('EmpresaID', 0),
        unidad_negocio_id=row.get('UnidadNegocioID', 0),
        server_id=str(row.get('ServerID', '')) if row.get('ServerID') else None,
        nombre_comercial=row.get('NombreComercial', ''),
        concepto_restaurante=row.get('ConceptoRestaurante'),
        tipo_restaurante=row.get('TipoRestaurante'),
        segmento_precio=row.get('SegmentoPrecio'),
        ciudad=row.get('Ciudad'),
        estado=row.get('Estado'),
        pais=row.get('Pais', 'México'),
        zona_comercial=row.get('ZonaComercial'),
        sitio_web_oficial=row.get('SitioWebOficial'),
        url_menu_digital=row.get('UrlMenuDigital'),
        url_reservaciones=row.get('UrlReservaciones'),
        url_google_maps=row.get('UrlGoogleMaps'),
        url_instagram=row.get('UrlInstagram'),
        url_facebook=row.get('UrlFacebook'),
        url_tripadvisor=row.get('UrlTripAdvisor'),
        url_opentable=row.get('UrlOpenTable'),
        url_delivery=row.get('UrlDelivery'),
        ticket_promedio_objetivo=float(row['TicketPromedioObjetivo']) if row.get('TicketPromedioObjetivo') else None,
        rango_precio_objetivo=row.get('RangoPrecioObjetivo'),
        moneda=row.get('Moneda', 'MXN'),
        descripcion_concepto=row.get('DescripcionConcepto'),
        palabras_clave=row.get('PalabrasClave'),
        activo=bool(row.get('Activo', True)),
        fecha_creacion=row.get('FechaCreacion') or datetime.now(),
        usuario_creacion=row.get('UsuarioCreacion'),
        fecha_modificacion=row.get('FechaModificacion'),
        usuario_modificacion=row.get('UsuarioModificacion'),
    )


# =============================================================================
# CRUD OPERATIONS
# =============================================================================

def listar_perfiles_digitales(
    empresa_id: Optional[int] = None,
    unidad_negocio_id: Optional[int] = None,
    solo_activos: bool = True,
    page: int = 1,
    page_size: int = 50
) -> Tuple[List[PerfilDigitalResponse], int]:
    """
    Lista perfiles digitales con filtros opcionales.
    
    Returns:
        Tupla (lista de perfiles, total de registros)
    """
    conn = _get_conn()
    
    where_clauses = []
    if empresa_id:
        where_clauses.append(f"EmpresaID = {empresa_id}")
    if unidad_negocio_id:
        where_clauses.append(f"UnidadNegocioID = {unidad_negocio_id}")
    if solo_activos:
        where_clauses.append("Activo = 1")
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    # Contar total
    count_query = f"""
    SELECT COUNT(*) as total
    FROM Sistema_UnidadesNegocioPerfilDigital
    {where_sql}
    """
    count_result = execute_sql_query(*conn, count_query)
    total = count_result[0]['total'] if count_result else 0
    
    # Obtener página
    offset = (page - 1) * page_size
    query = f"""
    SELECT 
        CAST(PerfilDigitalID AS NVARCHAR(36)) as PerfilDigitalID,
        EmpresaID,
        UnidadNegocioID,
        CAST(ServerID AS NVARCHAR(36)) as ServerID,
        NombreComercial,
        ConceptoRestaurante,
        TipoRestaurante,
        SegmentoPrecio,
        Ciudad,
        Estado,
        Pais,
        ZonaComercial,
        SitioWebOficial,
        UrlMenuDigital,
        UrlReservaciones,
        UrlGoogleMaps,
        UrlInstagram,
        UrlFacebook,
        UrlTripAdvisor,
        UrlOpenTable,
        UrlDelivery,
        TicketPromedioObjetivo,
        RangoPrecioObjetivo,
        Moneda,
        DescripcionConcepto,
        PalabrasClave,
        Activo,
        FechaCreacion,
        UsuarioCreacion,
        FechaModificacion,
        UsuarioModificacion
    FROM Sistema_UnidadesNegocioPerfilDigital
    {where_sql}
    ORDER BY NombreComercial
    OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
    """
    
    result = execute_sql_query(*conn, query)
    
    perfiles = [_row_to_perfil(row) for row in (result or [])]
    
    return perfiles, total


def obtener_perfil_por_unidad(unidad_negocio_id: int) -> Optional[PerfilDigitalResponse]:
    """
    Obtiene el perfil digital de una unidad de negocio específica.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        CAST(PerfilDigitalID AS NVARCHAR(36)) as PerfilDigitalID,
        EmpresaID,
        UnidadNegocioID,
        CAST(ServerID AS NVARCHAR(36)) as ServerID,
        NombreComercial,
        ConceptoRestaurante,
        TipoRestaurante,
        SegmentoPrecio,
        Ciudad,
        Estado,
        Pais,
        ZonaComercial,
        SitioWebOficial,
        UrlMenuDigital,
        UrlReservaciones,
        UrlGoogleMaps,
        UrlInstagram,
        UrlFacebook,
        UrlTripAdvisor,
        UrlOpenTable,
        UrlDelivery,
        TicketPromedioObjetivo,
        RangoPrecioObjetivo,
        Moneda,
        DescripcionConcepto,
        PalabrasClave,
        Activo,
        FechaCreacion,
        UsuarioCreacion,
        FechaModificacion,
        UsuarioModificacion
    FROM Sistema_UnidadesNegocioPerfilDigital
    WHERE UnidadNegocioID = {UnidadNegocioID}
      AND Activo = 1
    """
    
    result = execute_sql_query(*conn, query)
    
    if result and len(result) > 0:
        return _row_to_perfil(result[0])
    
    return None


def obtener_perfil_por_id(perfil_digital_id: str) -> Optional[PerfilDigitalResponse]:
    """
    Obtiene un perfil digital por su ID.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        CAST(PerfilDigitalID AS NVARCHAR(36)) as PerfilDigitalID,
        EmpresaID,
        UnidadNegocioID,
        CAST(ServerID AS NVARCHAR(36)) as ServerID,
        NombreComercial,
        ConceptoRestaurante,
        TipoRestaurante,
        SegmentoPrecio,
        Ciudad,
        Estado,
        Pais,
        ZonaComercial,
        SitioWebOficial,
        UrlMenuDigital,
        UrlReservaciones,
        UrlGoogleMaps,
        UrlInstagram,
        UrlFacebook,
        UrlTripAdvisor,
        UrlOpenTable,
        UrlDelivery,
        TicketPromedioObjetivo,
        RangoPrecioObjetivo,
        Moneda,
        DescripcionConcepto,
        PalabrasClave,
        Activo,
        FechaCreacion,
        UsuarioCreacion,
        FechaModificacion,
        UsuarioModificacion
    FROM Sistema_UnidadesNegocioPerfilDigital
    WHERE PerfilDigitalID = '{perfil_digital_id}'
    """
    
    result = execute_sql_query(*conn, query)
    
    if result and len(result) > 0:
        return _row_to_perfil(result[0])
    
    return None


def crear_perfil_digital(data: PerfilDigitalCreate, usuario: str) -> PerfilDigitalResponse:
    """
    Crea un nuevo perfil digital.
    
    Raises:
        ValueError: Si ya existe un perfil para la unidad
    """
    conn = _get_conn()
    
    # Verificar que no existe perfil para esta unidad
    check_query = f"""
    SELECT COUNT(*) as existe
    FROM Sistema_UnidadesNegocioPerfilDigital
    WHERE UnidadNegocioID = {data.UnidadNegocioID}
      AND Activo = 1
    """
    check_result = execute_sql_query(*conn, check_query)
    
    if check_result and check_result[0]['existe'] > 0:
        raise ValueError(f"Ya existe un perfil digital activo para la unidad {data.unidad_negocio_id}")
    
    # Generar nuevo ID
    perfil_id = str(uuid.uuid4())
    
    # Preparar valores
    server_id_sql = f"'{data.server_id}'" if data.server_id else "NULL"
    concepto_sql = f"N'{data.concepto_restaurante}'" if data.concepto_restaurante else "NULL"
    tipo_rest_sql = f"'{data.tipo_restaurante.value}'" if data.tipo_restaurante else "NULL"
    segmento_sql = f"'{data.segmento_precio.value}'" if data.segmento_precio else "NULL"
    ciudad_sql = f"N'{data.ciudad}'" if data.ciudad else "NULL"
    estado_sql = f"N'{data.estado}'" if data.estado else "NULL"
    zona_sql = f"N'{data.zona_comercial}'" if data.zona_comercial else "NULL"
    
    # URLs
    sitio_web_sql = f"N'{data.sitio_web_oficial}'" if data.sitio_web_oficial else "NULL"
    url_menu_sql = f"N'{data.url_menu_digital}'" if data.url_menu_digital else "NULL"
    url_reserv_sql = f"N'{data.url_reservaciones}'" if data.url_reservaciones else "NULL"
    url_maps_sql = f"N'{data.url_google_maps}'" if data.url_google_maps else "NULL"
    url_insta_sql = f"N'{data.url_instagram}'" if data.url_instagram else "NULL"
    url_fb_sql = f"N'{data.url_facebook}'" if data.url_facebook else "NULL"
    url_trip_sql = f"N'{data.url_tripadvisor}'" if data.url_tripadvisor else "NULL"
    url_opentable_sql = f"N'{data.url_opentable}'" if data.url_opentable else "NULL"
    url_delivery_sql = f"N'{data.url_delivery}'" if data.url_delivery else "NULL"
    
    # Comercial
    ticket_sql = f"{data.ticket_promedio_objetivo}" if data.ticket_promedio_objetivo else "NULL"
    rango_sql = f"'{data.rango_precio_objetivo}'" if data.rango_precio_objetivo else "NULL"
    
    # Contexto IA
    desc_sql = f"N'{data.descripcion_concepto}'" if data.descripcion_concepto else "NULL"
    keywords_sql = f"N'{data.palabras_clave}'" if data.palabras_clave else "NULL"
    
    insert_query = f"""
    INSERT INTO Sistema_UnidadesNegocioPerfilDigital (
        PerfilDigitalID,
        EmpresaID,
        UnidadNegocioID,
        ServerID,
        NombreComercial,
        ConceptoRestaurante,
        TipoRestaurante,
        SegmentoPrecio,
        Ciudad,
        Estado,
        Pais,
        ZonaComercial,
        SitioWebOficial,
        UrlMenuDigital,
        UrlReservaciones,
        UrlGoogleMaps,
        UrlInstagram,
        UrlFacebook,
        UrlTripAdvisor,
        UrlOpenTable,
        UrlDelivery,
        TicketPromedioObjetivo,
        RangoPrecioObjetivo,
        Moneda,
        DescripcionConcepto,
        PalabrasClave,
        Activo,
        FechaCreacion,
        UsuarioCreacion
    ) VALUES (
        '{perfil_id}',
        {data.EmpresaID},
        {data.UnidadNegocioID},
        {server_id_sql},
        N'{data.nombre_comercial}',
        {concepto_sql},
        {tipo_rest_sql},
        {segmento_sql},
        {ciudad_sql},
        {estado_sql},
        N'{data.Pais}',
        {zona_sql},
        {sitio_web_sql},
        {url_menu_sql},
        {url_reserv_sql},
        {url_maps_sql},
        {url_insta_sql},
        {url_fb_sql},
        {url_trip_sql},
        {url_opentable_sql},
        {url_delivery_sql},
        {ticket_sql},
        {rango_sql},
        '{data.Moneda}',
        {desc_sql},
        {keywords_sql},
        1,
        GETDATE(),
        N'{usuario}'
    )
    """
    
    execute_sql_query(*conn, insert_query)
    logger.info(f"[PERFIL-DIGITAL] Creado perfil {perfil_id} para unidad {data.unidad_negocio_id} por {usuario}")
    
    # Retornar el perfil creado
    return obtener_perfil_por_id(perfil_id)


def actualizar_perfil_digital(
    perfil_digital_id: str,
    data: PerfilDigitalUpdate,
    usuario: str
) -> Optional[PerfilDigitalResponse]:
    """
    Actualiza un perfil digital existente.
    """
    conn = _get_conn()
    
    # Verificar que existe
    perfil_actual = obtener_perfil_por_id(perfil_digital_id)
    if not perfil_actual:
        return None
    
    # Construir SET dinámico solo con campos proporcionados
    set_clauses = []
    
    if data.nombre_comercial is not None:
        set_clauses.append(f"NombreComercial = N'{data.nombre_comercial}'")
    if data.concepto_restaurante is not None:
        set_clauses.append(f"ConceptoRestaurante = N'{data.concepto_restaurante}'")
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
    
    # URLs
    if data.sitio_web_oficial is not None:
        set_clauses.append(f"SitioWebOficial = N'{data.sitio_web_oficial}'")
    if data.url_menu_digital is not None:
        set_clauses.append(f"UrlMenuDigital = N'{data.url_menu_digital}'")
    if data.url_reservaciones is not None:
        set_clauses.append(f"UrlReservaciones = N'{data.url_reservaciones}'")
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
    if data.url_delivery is not None:
        set_clauses.append(f"UrlDelivery = N'{data.url_delivery}'")
    
    # Comercial
    if data.ticket_promedio_objetivo is not None:
        set_clauses.append(f"TicketPromedioObjetivo = {data.ticket_promedio_objetivo}")
    if data.rango_precio_objetivo is not None:
        set_clauses.append(f"RangoPrecioObjetivo = '{data.rango_precio_objetivo}'")
    if data.moneda is not None:
        set_clauses.append(f"Moneda = '{data.moneda}'")
    
    # Contexto IA
    if data.descripcion_concepto is not None:
        set_clauses.append(f"DescripcionConcepto = N'{data.descripcion_concepto}'")
    if data.palabras_clave is not None:
        set_clauses.append(f"PalabrasClave = N'{data.palabras_clave}'")
    
    if not set_clauses:
        return perfil_actual  # Nada que actualizar
    
    # Agregar auditoría
    set_clauses.append("FechaModificacion = GETDATE()")
    set_clauses.append(f"UsuarioModificacion = N'{usuario}'")
    
    set_sql = ", ".join(set_clauses)
    
    update_query = f"""
    UPDATE Sistema_UnidadesNegocioPerfilDigital
    SET {set_sql}
    WHERE PerfilDigitalID = '{perfil_digital_id}'
    """
    
    execute_sql_query(*conn, update_query)
    logger.info(f"[PERFIL-DIGITAL] Actualizado perfil {perfil_digital_id} por {usuario}")
    
    return obtener_perfil_por_id(perfil_digital_id)


def inactivar_perfil_digital(perfil_digital_id: str, usuario: str) -> bool:
    """
    Inactiva un perfil digital (baja lógica).
    """
    conn = _get_conn()
    
    update_query = f"""
    UPDATE Sistema_UnidadesNegocioPerfilDigital
    SET Activo = 0,
        FechaModificacion = GETDATE(),
        UsuarioModificacion = N'{usuario}'
    WHERE PerfilDigitalID = '{perfil_digital_id}'
    """
    
    execute_sql_query(*conn, update_query)
    logger.info(f"[PERFIL-DIGITAL] Inactivado perfil {perfil_digital_id} por {usuario}")
    
    return True


# =============================================================================
# HELPERS
# =============================================================================

def obtener_urls_perfil(unidad_negocio_id: int) -> Dict[str, Optional[str]]:
    """
    Obtiene solo las URLs del perfil para análisis rápido.
    """
    perfil = obtener_perfil_por_unidad(unidad_negocio_id)
    
    if not perfil:
        return {}
    
    return {
        'sitio_web': perfil.sitio_web_oficial,
        'menu_digital': perfil.url_menu_digital,
        'reservaciones': perfil.url_reservaciones,
        'google_maps': perfil.url_google_maps,
        'instagram': perfil.url_instagram,
        'facebook': perfil.url_facebook,
        'tripadvisor': perfil.url_tripadvisor,
        'opentable': perfil.url_opentable,
        'delivery': perfil.url_delivery,
    }


def verificar_perfil_completo(unidad_negocio_id: int) -> Dict[str, Any]:
    """
    Verifica si el perfil digital está completo para IA.
    
    Returns:
        Dict con status y campos faltantes
    """
    perfil = obtener_perfil_por_unidad(unidad_negocio_id)
    
    if not perfil:
        return {
            'completo': False,
            'existe': False,
            'faltantes': ['perfil_no_existe'],
            'porcentaje': 0
        }
    
    # Campos requeridos para contexto IA
    campos_requeridos = {
        'nombre_comercial': perfil.nombre_comercial,
        'concepto_restaurante': perfil.concepto_restaurante,
        'tipo_restaurante': perfil.tipo_restaurante,
        'segmento_precio': perfil.segmento_precio,
        'ciudad': perfil.ciudad,
    }
    
    # Campos deseables (URLs)
    campos_deseables = {
        'sitio_web': perfil.sitio_web_oficial,
        'menu_digital': perfil.url_menu_digital,
    }
    
    faltantes_requeridos = [k for k, v in campos_requeridos.items() if not v]
    faltantes_deseables = [k for k, v in campos_deseables.items() if not v]
    
    total_campos = len(campos_requeridos) + len(campos_deseables)
    campos_completos = total_campos - len(faltantes_requeridos) - len(faltantes_deseables)
    porcentaje = (campos_completos / total_campos) * 100 if total_campos > 0 else 0
    
    return {
        'completo': len(faltantes_requeridos) == 0,
        'existe': True,
        'faltantes_requeridos': faltantes_requeridos,
        'faltantes_deseables': faltantes_deseables,
        'porcentaje': round(porcentaje, 1)
    }


__all__ = [
    'listar_perfiles_digitales',
    'obtener_perfil_por_unidad',
    'obtener_perfil_por_id',
    'crear_perfil_digital',
    'actualizar_perfil_digital',
    'inactivar_perfil_digital',
    'obtener_urls_perfil',
    'verificar_perfil_completo',
]
