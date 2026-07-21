"""
Repository para Simulación de Precios y Solicitudes de Cambio
FASE 1C-3F - Costos y Márgenes

IMPORTANTE:
- Todas las operaciones son en EDARSAHUB SQL
- NO se modifican precios oficiales directamente
- El flujo de autorización es obligatorio
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from decimal import Decimal

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG


def _get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB."""
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )


def _safe_decimal(value) -> float:
    """Convierte Decimal a float de forma segura."""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except:
        return 0.0



def _generar_folio() -> str:
    """Genera folio único para solicitud."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:4].upper()
    return f"SCP-{timestamp}-{random_suffix}"


# ==================== SIMULACIÓN ====================

def obtener_datos_producto_para_simulacion(
    producto_id: str,
    server_id: str
) -> Optional[Dict]:
    """
    Obtiene datos actuales de un producto para simulación.
    Fuente: EDARSAHUB SQL (NO-LIVE)
    """
    conn = _get_edarsahub_connection()

    if not producto_id or not server_id:
        return None

    prod_id_clean = str(producto_id).replace('-', '').upper()
    server_id_clean = str(server_id).replace('-', '').upper()

    query = """
    SELECT
        CAST(p.ProductoID AS NVARCHAR(36)) as ProductoID,
        p.CodigoFuente,
        p.Nombre,
        p.NombreCorto,
        CAST(p.ServerID AS NVARCHAR(36)) as ServerID,
        p.SystemType,
        p.FamiliaCodigoFuente,
        p.FamiliaNombre,
        p.PrecioVenta,
        p.CostoReceta,
        p.MargenBrutoPesos,
        p.MargenBrutoPorcentaje,
        p.MargenObjetivo,
        p.SyncRunID
    FROM Sync_Productos p
    WHERE REPLACE(CAST(p.ProductoID AS VARCHAR(50)), '-', '') = %s
    AND REPLACE(CAST(p.ServerID AS VARCHAR(50)), '-', '') = %s
    """

    result = execute_sql_query_params(*conn, query, (prod_id_clean, server_id_clean))

    if not result:
        return None

    r = result[0]
    return {
        'producto_id': str(r['ProductoID']),
        'codigo_producto': r['CodigoFuente'],
        'nombre_producto': r['Nombre'],
        'nombre_corto': r.get('NombreCorto'),
        'server_id': str(r['ServerID']),
        'system_type': r['SystemType'],
        'familia_codigo': r.get('FamiliaCodigoFuente'),
        'familia_nombre': r.get('FamiliaNombre'),
        'precio_actual': _safe_decimal(r.get('PrecioVenta', 0)),
        'costo_actual': _safe_decimal(r.get('CostoReceta', 0)),
        'margen_actual_pesos': _safe_decimal(r.get('MargenBrutoPesos', 0)),
        'margen_actual_porcentaje': _safe_decimal(r.get('MargenBrutoPorcentaje', 0)),
        'margen_objetivo': _safe_decimal(r.get('MargenObjetivo')) if r.get('MargenObjetivo') else None,
        'sync_run_id': r.get('SyncRunID'),
        'fecha_datos_costo': None,
    }


def calcular_simulacion(
    precio_actual: float,
    costo_actual: float,
    precio_nuevo: float,
    margen_objetivo: Optional[float] = None
) -> Dict:
    """
    Calcula los valores de una simulación de precio.
    NO modifica ningún dato en BD.
    """
    # Márgenes actuales
    margen_actual_pesos = precio_actual - costo_actual
    margen_actual_porcentaje = (margen_actual_pesos / precio_actual * 100) if precio_actual > 0 else 0
    
    # Márgenes simulados
    margen_simulado_pesos = precio_nuevo - costo_actual
    margen_simulado_porcentaje = (margen_simulado_pesos / precio_nuevo * 100) if precio_nuevo > 0 else 0
    
    # Variación
    variacion_pesos = precio_nuevo - precio_actual
    variacion_porcentaje = (variacion_pesos / precio_actual * 100) if precio_actual > 0 else 0
    
    # Recomendación
    if costo_actual <= 0:
        recomendacion = "SIN_DATOS"
        impacto = "Sin datos de costo para análisis"
    elif margen_simulado_pesos < 0:
        recomendacion = "MARGEN_NEGATIVO"
        impacto = f"ALERTA: Precio por debajo del costo. Pérdida de ${abs(margen_simulado_pesos):.2f} por unidad"
    elif margen_objetivo and margen_simulado_porcentaje < margen_objetivo:
        recomendacion = "MARGEN_BAJO"
        diferencia = margen_objetivo - margen_simulado_porcentaje
        impacto = f"Margen {diferencia:.1f}% por debajo del objetivo ({margen_objetivo:.1f}%)"
    elif variacion_porcentaje > 15:
        recomendacion = "REVISAR_COSTO"
        impacto = f"Aumento significativo ({variacion_porcentaje:.1f}%). Verificar competitividad"
    elif variacion_porcentaje < -15:
        recomendacion = "REVISAR_COSTO"
        impacto = f"Reducción significativa ({variacion_porcentaje:.1f}%). Verificar rentabilidad"
    elif variacion_pesos > 0:
        recomendacion = "AUMENTAR"
        impacto = f"Mejora de margen: +${variacion_pesos:.2f} por unidad (+{variacion_porcentaje:.1f}%)"
    elif variacion_pesos < 0:
        recomendacion = "REDUCIR"
        impacto = f"Reducción de margen: ${variacion_pesos:.2f} por unidad ({variacion_porcentaje:.1f}%)"
    else:
        recomendacion = "MANTENER"
        impacto = "Sin cambio en precio"
    
    return {
        'precio_simulado': precio_nuevo,
        'margen_simulado_pesos': margen_simulado_pesos,
        'margen_simulado_porcentaje': margen_simulado_porcentaje,
        'variacion_pesos': variacion_pesos,
        'variacion_porcentaje': variacion_porcentaje,
        'recomendacion': recomendacion,
        'impacto_estimado': impacto,
    }


def guardar_simulacion(
    producto_id: str,
    server_id: str,
    datos_producto: Dict,
    datos_simulacion: Dict,
    usuario_id: str,
    usuario_email: str,
    ip: Optional[str] = None
) -> str:
    """
    Guarda una simulación en BD para referencia futura.
    Retorna el ID de la simulación.
    """
    conn = _get_edarsahub_connection()
    simulacion_id = str(uuid.uuid4())

    query = """
    INSERT INTO Comercial_SimulacionesPrecios (
        SimulacionID, ProductoID, CodigoProducto, NombreProducto,
        ServerID, SystemType,
        PrecioActual, CostoActual, MargenActualPesos, MargenActualPorcentaje,
        PrecioSimulado, MargenSimuladoPesos, MargenSimuladoPorcentaje,
        VariacionPesos, VariacionPorcentaje,
        MargenObjetivo, Recomendacion, ImpactoEstimado,
        SyncRunID, UsuarioID, UsuarioEmail, IPSimulacion
    ) VALUES (
        %s, %s, %s, %s,
        %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s
    )
    """
    params = (
        simulacion_id,
        datos_producto['producto_id'],
        datos_producto['codigo_producto'],
        datos_producto['nombre_producto'],
        datos_producto['server_id'],
        datos_producto['system_type'],
        datos_producto['precio_actual'],
        datos_producto['costo_actual'],
        datos_producto['margen_actual_pesos'],
        datos_producto['margen_actual_porcentaje'],
        datos_simulacion['precio_simulado'],
        datos_simulacion['margen_simulado_pesos'],
        datos_simulacion['margen_simulado_porcentaje'],
        datos_simulacion['variacion_pesos'],
        datos_simulacion['variacion_porcentaje'],
        datos_producto.get('margen_objetivo'),
        datos_simulacion['recomendacion'],
        datos_simulacion['impacto_estimado'],
        datos_producto.get('sync_run_id'),
        usuario_id,
        usuario_email,
        ip,
    )

    execute_sql_query_params(*conn, query, params)
    return simulacion_id


# ==================== SOLICITUDES ====================

def crear_solicitud_cambio_precio(
    producto_id: str,
    server_id: str,
    precio_solicitado: float,
    motivo: str,
    justificacion: Optional[str],
    usuario_id: str,
    usuario_email: str,
    usuario_nombre: Optional[str] = None,
    simulacion_id: Optional[str] = None,
    ip: Optional[str] = None,
    unidad_negocio_pk: Optional[str] = None,
) -> Dict:
    """
    Crea una nueva solicitud de cambio de precio en estado BORRADOR.
    NO modifica precios oficiales.
    """
    conn = _get_edarsahub_connection()

    datos_producto = obtener_datos_producto_para_simulacion(producto_id, server_id)
    if not datos_producto:
        raise ValueError(f"Producto no encontrado: {producto_id}")

    simulacion = calcular_simulacion(
        datos_producto['precio_actual'],
        datos_producto['costo_actual'],
        precio_solicitado,
        datos_producto.get('margen_objetivo')
    )

    solicitud_id = str(uuid.uuid4())
    folio = _generar_folio()

    query = """
    INSERT INTO Comercial_SolicitudesCambioPrecio (
        SolicitudID, FolioSolicitud,
        ProductoID, CodigoProducto, NombreProducto,
        ServerID, SystemType, FamiliaCodigoFuente, FamiliaNombre,
        UnidadNegocioID,
        PrecioActual, PrecioSolicitado, VariacionPesos, VariacionPorcentaje,
        CostoActual, MargenActualPesos, MargenActualPorcentaje,
        MargenSolicitadoPesos, MargenSolicitadoPorcentaje, MargenObjetivo,
        SyncRunID, FechaDatosCosto,
        Motivo, Justificacion, Estatus,
        SolicitanteUsuarioID, SolicitanteEmail, SolicitanteNombre,
        IPCreacion
    ) VALUES (
        %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s,
        %s,
        %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s,
        %s, %s, 'BORRADOR',
        %s, %s, %s,
        %s
    )
    """
    params = (
        solicitud_id,
        folio,
        datos_producto['producto_id'],
        datos_producto['codigo_producto'],
        datos_producto['nombre_producto'],
        datos_producto['server_id'],
        datos_producto['system_type'],
        datos_producto.get('familia_codigo'),
        datos_producto.get('familia_nombre'),
        unidad_negocio_pk,
        datos_producto['precio_actual'],
        precio_solicitado,
        simulacion['variacion_pesos'],
        simulacion['variacion_porcentaje'],
        datos_producto['costo_actual'],
        datos_producto['margen_actual_pesos'],
        datos_producto['margen_actual_porcentaje'],
        simulacion['margen_simulado_pesos'],
        simulacion['margen_simulado_porcentaje'],
        datos_producto.get('margen_objetivo'),
        datos_producto.get('sync_run_id'),
        datos_producto.get('fecha_datos_costo'),
        motivo,
        justificacion,
        usuario_id,
        usuario_email,
        usuario_nombre,
        ip,
    )

    execute_sql_query_params(*conn, query, params)

    _registrar_historial(
        conn, solicitud_id, 'CREAR', None, 'BORRADOR',
        usuario_id, usuario_email, usuario_nombre,
        'Solicitud creada', None, None, ip
    )

    return {
        'solicitud_id': solicitud_id,
        'folio_solicitud': folio,
        'estatus': 'BORRADOR'
    }


def obtener_solicitud(solicitud_id: str) -> Optional[Dict]:
    """Obtiene una solicitud por ID."""
    conn = _get_edarsahub_connection()

    query = """
    SELECT * FROM Comercial_SolicitudesCambioPrecio
    WHERE SolicitudID = %s
    """

    result = execute_sql_query_params(*conn, query, (str(solicitud_id),))
    if not result:
        return None

    return _mapear_solicitud(result[0])


def listar_solicitudes(
    estatus: Optional[str] = None,
    server_id: Optional[str] = None,
    solicitante_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    unidad_negocio_pk: Optional[str] = None,
) -> Tuple[List[Dict], int]:
    """Lista solicitudes con filtros y paginación."""
    conn = _get_edarsahub_connection()

    where_clauses = ["1=1"]
    params = []
    if estatus:
        where_clauses.append("Estatus = %s")
        params.append(str(estatus))
    if unidad_negocio_pk:
        where_clauses.append("UnidadNegocioID = %s")
        params.append(str(unidad_negocio_pk))
    elif server_id:
        where_clauses.append("CAST(ServerID AS NVARCHAR(36)) = %s")
        params.append(str(server_id))
    if solicitante_id:
        where_clauses.append("SolicitanteUsuarioID = %s")
        params.append(str(solicitante_id))

    where_sql = " AND ".join(where_clauses)
    offset = max(page - 1, 0) * page_size

    count_query = f"SELECT COUNT(*) as total FROM Comercial_SolicitudesCambioPrecio WHERE {where_sql}"
    count_result = execute_sql_query_params(*conn, count_query, tuple(params))
    total = count_result[0]['total'] if count_result else 0

    query = f"""
    SELECT
        SolicitudID, FolioSolicitud, CodigoProducto, NombreProducto,
        SystemType, PrecioActual, PrecioSolicitado, VariacionPorcentaje,
        Estatus, SolicitanteEmail, FechaSolicitud, FechaAutorizacion, AutorizadorEmail
    FROM Comercial_SolicitudesCambioPrecio
    WHERE {where_sql}
    ORDER BY FechaCreacion DESC
    OFFSET {int(offset)} ROWS FETCH NEXT {int(page_size)} ROWS ONLY
    """

    result = execute_sql_query_params(*conn, query, tuple(params)) or []

    solicitudes = []
    for r in result:
        solicitudes.append({
            'solicitud_id': str(r['SolicitudID']),
            'folio_solicitud': r['FolioSolicitud'],
            'codigo_producto': r['CodigoProducto'],
            'nombre_producto': r['NombreProducto'],
            'system_type': r['SystemType'],
            'precio_actual': _safe_decimal(r['PrecioActual']),
            'precio_solicitado': _safe_decimal(r['PrecioSolicitado']),
            'variacion_porcentaje': _safe_decimal(r['VariacionPorcentaje']),
            'estatus': r['Estatus'],
            'solicitante_email': r['SolicitanteEmail'],
            'fecha_solicitud': r.get('FechaSolicitud'),
            'fecha_autorizacion': r.get('FechaAutorizacion'),
            'autorizador_email': r.get('AutorizadorEmail'),
        })

    return solicitudes, total


def cambiar_estatus_solicitud(
    solicitud_id: str,
    nuevo_estatus: str,
    usuario_id: str,
    usuario_email: str,
    usuario_nombre: Optional[str] = None,
    comentario: Optional[str] = None,
    ip: Optional[str] = None,
    campos_adicionales: Optional[Dict] = None
) -> Dict:
    """
    Cambia el estatus de una solicitud y registra en historial.
    Valida transiciones permitidas.
    """
    conn = _get_edarsahub_connection()

    solicitud = obtener_solicitud(solicitud_id)
    if not solicitud:
        raise ValueError(f"Solicitud no encontrada: {solicitud_id}")

    estatus_actual = solicitud['estatus']

    transiciones_validas = {
        'BORRADOR': ['SOLICITADA', 'CANCELADA'],
        'SOLICITADA': ['EN_REVISION', 'CANCELADA'],
        'EN_REVISION': ['APROBADA', 'RECHAZADA', 'SOLICITADA'],
        'APROBADA': ['APLICADA', 'ERROR_APLICACION', 'CANCELADA'],
        'RECHAZADA': [],
        'CANCELADA': [],
        'APLICADA': [],
        'ERROR_APLICACION': ['APROBADA'],
    }

    if nuevo_estatus not in transiciones_validas.get(estatus_actual, []):
        raise ValueError(
            f"Transición no permitida: {estatus_actual} → {nuevo_estatus}. "
            f"Transiciones válidas: {transiciones_validas.get(estatus_actual, [])}"
        )

    accion_map = {
        'SOLICITADA': 'ENVIAR',
        'EN_REVISION': 'REVISAR',
        'APROBADA': 'APROBAR',
        'RECHAZADA': 'RECHAZAR',
        'CANCELADA': 'CANCELAR',
        'APLICADA': 'APLICAR',
        'ERROR_APLICACION': 'ERROR_APLICACION',
    }
    accion = accion_map.get(nuevo_estatus, 'CAMBIAR_ESTATUS')

    set_clauses = [
        "Estatus = %s",
        "FechaModificacion = GETDATE()",
    ]
    params = [nuevo_estatus]

    if nuevo_estatus == 'SOLICITADA':
        set_clauses.append("FechaSolicitud = GETDATE()")
    elif nuevo_estatus in ['APROBADA', 'RECHAZADA']:
        set_clauses.extend([
            "AutorizadorUsuarioID = %s",
            "AutorizadorEmail = %s",
            "AutorizadorNombre = %s",
            "FechaAutorizacion = GETDATE()",
            "ComentarioAutorizacion = %s",
        ])
        params.extend([usuario_id, usuario_email, usuario_nombre, comentario])
    elif nuevo_estatus == 'APLICADA':
        set_clauses.extend([
            "ModificadorUsuarioID = %s",
            "ModificadorEmail = %s",
            "ModificadorNombre = %s",
            "FechaAplicacion = GETDATE()",
            "ComentarioAplicacion = %s",
            "PrecioAplicado = %s",
        ])
        params.extend([
            usuario_id,
            usuario_email,
            usuario_nombre,
            comentario,
            solicitud['precio_solicitado'],
        ])

    update_query = f"""
    UPDATE Comercial_SolicitudesCambioPrecio
    SET {", ".join(set_clauses)}
    WHERE SolicitudID = %s
    """
    params.append(str(solicitud_id))

    execute_sql_query_params(*conn, update_query, tuple(params))

    _registrar_historial(
        conn, solicitud_id, accion, estatus_actual, nuevo_estatus,
        usuario_id, usuario_email, usuario_nombre,
        comentario, estatus_actual, nuevo_estatus, ip
    )

    return {
        'solicitud_id': solicitud_id,
        'estatus_anterior': estatus_actual,
        'estatus_nuevo': nuevo_estatus,
        'accion': accion
    }


def obtener_historial_solicitud(solicitud_id: str) -> List[Dict]:
    """Obtiene el historial completo de una solicitud."""
    conn = _get_edarsahub_connection()

    query = """
    SELECT
        HistorialID, Accion, EstatusAnterior, EstatusNuevo,
        UsuarioEmail, UsuarioNombre, Comentario,
        ValorAnterior, ValorNuevo, FechaAccion
    FROM Comercial_SolicitudesCambioPrecioHistorial
    WHERE SolicitudID = %s
    ORDER BY FechaAccion ASC
    """

    result = execute_sql_query_params(*conn, query, (str(solicitud_id),)) or []

    historial = []
    for r in result:
        historial.append({
            'historial_id': str(r['HistorialID']),
            'accion': r['Accion'],
            'estatus_anterior': r.get('EstatusAnterior'),
            'estatus_nuevo': r['EstatusNuevo'],
            'usuario_email': r['UsuarioEmail'],
            'usuario_nombre': r.get('UsuarioNombre'),
            'comentario': r.get('Comentario'),
            'valor_anterior': r.get('ValorAnterior'),
            'valor_nuevo': r.get('ValorNuevo'),
            'fecha_accion': r['FechaAccion'],
        })

    return historial


# ==================== HELPERS ====================

def _mapear_solicitud(r: Dict) -> Dict:
    """Mapea un registro de BD a diccionario de respuesta."""
    return {
        'solicitud_id': str(r['SolicitudID']),
        'folio_solicitud': r['FolioSolicitud'],
        'producto_id': str(r['ProductoID']),
        'codigo_producto': r['CodigoProducto'],
        'nombre_producto': r['NombreProducto'],
        'server_id': str(r['ServerID']),
        'system_type': r['SystemType'],
        'familia_codigo': r.get('FamiliaCodigoFuente'),
        'familia_nombre': r.get('FamiliaNombre'),
        'precio_actual': _safe_decimal(r['PrecioActual']),
        'precio_solicitado': _safe_decimal(r['PrecioSolicitado']),
        'variacion_pesos': _safe_decimal(r['VariacionPesos']),
        'variacion_porcentaje': _safe_decimal(r['VariacionPorcentaje']),
        'costo_actual': _safe_decimal(r['CostoActual']),
        'margen_actual_pesos': _safe_decimal(r['MargenActualPesos']),
        'margen_actual_porcentaje': _safe_decimal(r['MargenActualPorcentaje']),
        'margen_solicitado_pesos': _safe_decimal(r['MargenSolicitadoPesos']),
        'margen_solicitado_porcentaje': _safe_decimal(r['MargenSolicitadoPorcentaje']),
        'margen_objetivo': _safe_decimal(r.get('MargenObjetivo')) if r.get('MargenObjetivo') else None,
        'sync_run_id': r.get('SyncRunID'),
        'fecha_datos_costo': r.get('FechaDatosCosto'),
        'motivo': r['Motivo'],
        'justificacion': r.get('Justificacion'),
        'estatus': r['Estatus'],
        'solicitante_usuario_id': str(r['SolicitanteUsuarioID']),
        'solicitante_email': r['SolicitanteEmail'],
        'solicitante_nombre': r.get('SolicitanteNombre'),
        'fecha_solicitud': r.get('FechaSolicitud'),
        'autorizador_usuario_id': str(r['AutorizadorUsuarioID']) if r.get('AutorizadorUsuarioID') else None,
        'autorizador_email': r.get('AutorizadorEmail'),
        'autorizador_nombre': r.get('AutorizadorNombre'),
        'fecha_autorizacion': r.get('FechaAutorizacion'),
        'comentario_autorizacion': r.get('ComentarioAutorizacion'),
        'modificador_usuario_id': str(r['ModificadorUsuarioID']) if r.get('ModificadorUsuarioID') else None,
        'modificador_email': r.get('ModificadorEmail'),
        'modificador_nombre': r.get('ModificadorNombre'),
        'fecha_aplicacion': r.get('FechaAplicacion'),
        'comentario_aplicacion': r.get('ComentarioAplicacion'),
        'precio_aplicado': _safe_decimal(r.get('PrecioAplicado')) if r.get('PrecioAplicado') else None,
        'fecha_creacion': r['FechaCreacion'],
        'fecha_modificacion': r['FechaModificacion'],
        'unidad_negocio_pk': str(r['UnidadNegocioID']) if r.get('UnidadNegocioID') else None,
    }


def _registrar_historial(
    conn: tuple,
    solicitud_id: str,
    accion: str,
    estatus_anterior: Optional[str],
    estatus_nuevo: str,
    usuario_id: str,
    usuario_email: str,
    usuario_nombre: Optional[str],
    comentario: Optional[str],
    valor_anterior: Optional[str],
    valor_nuevo: Optional[str],
    ip: Optional[str]
) -> None:
    """Registra una entrada en el historial de la solicitud."""
    historial_id = str(uuid.uuid4())

    query = """
    INSERT INTO Comercial_SolicitudesCambioPrecioHistorial (
        HistorialID, SolicitudID, Accion, EstatusAnterior, EstatusNuevo,
        UsuarioID, UsuarioEmail, UsuarioNombre,
        Comentario, ValorAnterior, ValorNuevo, IPAccion
    ) VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s
    )
    """
    params = (
        historial_id,
        solicitud_id,
        accion,
        estatus_anterior,
        estatus_nuevo,
        usuario_id,
        usuario_email,
        usuario_nombre,
        comentario,
        valor_anterior,
        valor_nuevo,
        ip,
    )

    execute_sql_query_params(*conn, query, params)
