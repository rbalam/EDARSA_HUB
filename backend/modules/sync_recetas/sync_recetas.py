"""
Sync Recetas - Job de sincronización de productos, recetas, insumos y costos.
FASE 1C-3B - Costos y Márgenes

ARQUITECTURA NO-LIVE:
- Este job es el ÚNICO componente autorizado para conectarse a fuentes remotas.
- Los endpoints y frontend SOLO leen de EDARSAHUB SQL.
- NO usar explosioninsumosdetalle como fuente (vacía en SoftRestaurant).
- USAR tabla 'costos' para recetas de productos.
- USAR tabla 'elaborados' para sub-recetas de insumos.
"""

import uuid
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from core.db import execute_sql_query
from core.sql_first.connection_factory import (
    get_edarsahub_pymssql_connection,
    get_external_sql_connection,
)
from core.server_registry import (
    EDARSAHUB_CONFIG, 
    _get_server_by_id_from_sql, 
    get_decrypted_credentials,
    _get_servers_from_sql
)

from .models import (
    SyncRecetasConfig, SyncRecetasResult,
    FamiliaSync, SubFamiliaSync, ProductoSync, 
    InsumoSync, RecetaLineaSync, ElaboradoLineaSync
)

MEXICO_TZ = ZoneInfo("America/Mexico_City")

# ============================================================================
# FUNCIONES PÚBLICAS
# ============================================================================

def ejecutar_sync_recetas_dry_run(
    server_ids: List[str] = None,
    sync_familias: bool = True,
    sync_productos: bool = True,
    sync_insumos: bool = True,
    sync_recetas: bool = True,
    sync_elaborados: bool = True
) -> SyncRecetasResult:
    """
    Ejecuta sincronización en modo DRY-RUN (sin escribir en BD).
    Retorna conteos de lo que SE HARÍA si se ejecutara en modo real.
    """
    config = SyncRecetasConfig(
        server_ids=server_ids or [],
        sync_familias=sync_familias,
        sync_productos=sync_productos,
        sync_insumos=sync_insumos,
        sync_recetas=sync_recetas,
        sync_elaborados=sync_elaborados,
        dry_run=True
    )
    return _ejecutar_sync(config)


def ejecutar_sync_recetas_real(
    server_ids: List[str],
    sync_familias: bool = True,
    sync_productos: bool = True,
    sync_insumos: bool = True,
    sync_recetas: bool = True,
    sync_elaborados: bool = True
) -> SyncRecetasResult:
    """
    Ejecuta sincronización REAL (escribe en BD).
    PRECAUCIÓN: Modifica datos en EDARSAHUB SQL.
    """
    if not server_ids:
        raise ValueError("server_ids es requerido para sincronización real")
    
    config = SyncRecetasConfig(
        server_ids=server_ids,
        sync_familias=sync_familias,
        sync_productos=sync_productos,
        sync_insumos=sync_insumos,
        sync_recetas=sync_recetas,
        sync_elaborados=sync_elaborados,
        dry_run=False
    )
    return _ejecutar_sync(config)


# ============================================================================
# IMPLEMENTACIÓN INTERNA
# ============================================================================

def _ejecutar_sync(config: SyncRecetasConfig) -> SyncRecetasResult:
    """Ejecuta la sincronización según configuración."""
    
    sync_run_id = f"SYNC-RECETAS-{datetime.now(MEXICO_TZ).strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
    started_at = datetime.now(MEXICO_TZ)
    
    result = SyncRecetasResult(
        sync_run_id=sync_run_id,
        success=False,
        is_dry_run=config.dry_run,
        started_at=started_at
    )
    
    try:
        # Obtener servidores
        if config.server_ids:
            servers = [_get_server_by_id_from_sql(sid) for sid in config.server_ids]
            servers = [s for s in servers if s]  # Filtrar None
        else:
            servers = _get_servers_from_sql(filter_active=True)
            servers = [s for s in servers if s.get('system_type', '').upper() in 
                      ('SOFTRESTAURANT', 'SOFTRESTAURANT_PRO', 'MPRO', 'ENTERPRISE')]
        
        result.total_servidores = len(servers)
        
        for server in servers:
            server_id = server.get('id')
            system_type = server.get('system_type', '').upper()
            server_name = server.get('name', server.get('nombre', 'Unknown'))
            
            try:
                server_result = _sync_servidor(
                    server=server,
                    config=config,
                    sync_run_id=sync_run_id
                )
                
                result.resultados_por_servidor[server_id] = server_result
                
                # Acumular totales
                result.total_familias += server_result.get('familias', 0)
                result.total_subfamilias += server_result.get('subfamilias', 0)
                result.total_productos += server_result.get('productos', 0)
                result.total_productos_con_receta += server_result.get('productos_con_receta', 0)
                result.total_insumos += server_result.get('insumos', 0)
                result.total_lineas_receta += server_result.get('lineas_receta', 0)
                result.total_elaborados += server_result.get('elaborados', 0)
                result.registros_insertados += server_result.get('insertados', 0)
                result.registros_actualizados += server_result.get('actualizados', 0)
                result.registros_error += server_result.get('errores_count', 0)
                
                if server_result.get('errores'):
                    result.errores.extend(server_result['errores'])
                if server_result.get('warnings'):
                    result.warnings.extend(server_result['warnings'])
                
                server_error_count = int(
                    server_result.get('errores_count', 0) or 0
                )
                server_errors = server_result.get('errores') or []

                if server_error_count > 0 or server_errors:
                    result.servidores_con_error += 1
                else:
                    result.servidores_exitosos += 1
                
            except Exception as e:
                result.servidores_con_error += 1
                result.errores.append(f"[{server_name}] Error: {str(e)}")
                result.resultados_por_servidor[server_id] = {
                    'error': str(e),
                    'system_type': system_type
                }
        
        result.success = (
            result.servidores_exitosos > 0
            and result.servidores_con_error == 0
            and result.registros_error == 0
        )
        
    except Exception as e:
        result.errores.append(f"Error general: {str(e)}")
    
    result.finished_at = datetime.now(MEXICO_TZ)
    result.duration_seconds = (result.finished_at - started_at).total_seconds()
    
    # Registrar en Sync_Control_Ejecuciones
    if not config.dry_run:
        _registrar_ejecucion(result)
    
    return result


def _sync_servidor(
    server: Dict,
    config: SyncRecetasConfig,
    sync_run_id: str
) -> Dict:
    """Sincroniza un servidor específico."""
    
    server_id = server.get('id')
    system_type = server.get('system_type', '').upper()
    server_name = server.get('name', server.get('nombre', 'Unknown'))
    
    # Obtener credenciales descifradas
    creds = get_decrypted_credentials(server)
    host = creds.get('host')
    port = creds.get('port', 1433)
    database = creds.get('database')
    username = creds.get('username')
    password = creds.get('password')
    
    result = {
        'server_id': server_id,
        'server_name': server_name,
        'system_type': system_type,
        'familias': 0,
        'subfamilias': 0,
        'productos': 0,
        'productos_con_receta': 0,
        'insumos': 0,
        'lineas_receta': 0,
        'elaborados': 0,
        'insertados': 0,
        'actualizados': 0,
        'errores_count': 0,
        'errores': [],
        'warnings': []
    }
    
    # Determinar tipo de sistema y ejecutar sync apropiado
    if 'SOFT' in system_type or 'ENTERPRISE' in system_type:
        _sync_softrestaurant(
            server_id=server_id,
            host=host, port=port, database=database,
            username=username, password=password,
            system_type=system_type,
            config=config,
            sync_run_id=sync_run_id,
            result=result
        )
    elif 'MPRO' in system_type:
        _sync_mpro(
            server_id=server_id,
            host=host, port=port, database=database,
            username=username, password=password,
            system_type=system_type,
            config=config,
            sync_run_id=sync_run_id,
            result=result
        )
    else:
        result['warnings'].append(f"Sistema {system_type} no soportado para sync de recetas")
    
    return result


# ============================================================================
# SINCRONIZACIÓN SOFTRESTAURANT
# ============================================================================

def _sync_softrestaurant(
    server_id: str,
    host: str, port: int, database: str,
    username: str, password: str,
    system_type: str,
    config: SyncRecetasConfig,
    sync_run_id: str,
    result: Dict
) -> None:
    """Sincroniza desde SoftRestaurant/Enterprise."""
    
    # 1. Sincronizar Familias (grupos)
    if config.sync_familias:
        familias = _obtener_familias_sr(host, port, database, username, password)
        result['familias'] = len(familias)
        
        if not config.dry_run and familias:
            _guardar_familias(server_id, system_type, familias, sync_run_id, result)
    
    # 2. Sincronizar SubFamilias (subgrupos)
    if config.sync_familias:
        subfamilias = _obtener_subfamilias_sr(host, port, database, username, password)
        result['subfamilias'] = len(subfamilias)
        
        if not config.dry_run and subfamilias:
            _guardar_subfamilias(server_id, system_type, subfamilias, sync_run_id, result)
    
    # 3. Sincronizar Insumos
    if config.sync_insumos:
        insumos = _obtener_insumos_sr(host, port, database, username, password)
        result['insumos'] = len(insumos)
        
        if not config.dry_run and insumos:
            _guardar_insumos(server_id, system_type, insumos, sync_run_id, result)
    
    # 4. Sincronizar Productos
    if config.sync_productos:
        productos = _obtener_productos_sr(host, port, database, username, password)
        result['productos'] = len(productos)
        
        # Contar productos con receta
        productos_con_receta = _contar_productos_con_receta_sr(host, port, database, username, password)
        result['productos_con_receta'] = productos_con_receta
        
        if not config.dry_run and productos:
            _guardar_productos(server_id, system_type, productos, sync_run_id, result)
    
    # 5. Sincronizar Recetas (tabla 'costos')
    if config.sync_recetas:
        recetas = _obtener_recetas_sr(host, port, database, username, password)
        result['lineas_receta'] = len(recetas)
        
        if not config.dry_run:
            _guardar_recetas(server_id, system_type, recetas, sync_run_id, result)
    
    # 6. Sincronizar Elaborados (sub-recetas)
    if config.sync_elaborados:
        elaborados = _obtener_elaborados_sr(host, port, database, username, password)
        result['elaborados'] = len(elaborados)
        
        if not config.dry_run and elaborados:
            _guardar_elaborados(server_id, system_type, elaborados, sync_run_id, result)

    
    # Productos compuestos SoftRestaurant: fuente unica modificadores.
    if config.sync_recetas:
        compuestos = _obtener_compuestos_sr(host, port, database, username, password)
        result['compuestos'] = len(compuestos)
        
        if not config.dry_run and compuestos:
            _guardar_compuestos(server_id, system_type, compuestos, sync_run_id, result)

    # 7. CATALOGO-CANONICO-C1: Dimensiones de filtro NO-LIVE (jerarquía INSUMOS)
    #    El Análisis de SoftRestaurant filtra por clasificacionventa /
    #    gruposiclasificacion / gruposi (insumos), NO por la jerarquía de ventas
    #    (grupos) que vive en Sync_Productos. Se sincroniza a Sync_Catalogo_Filtros.
    if config.sync_familias:
        filtros = _obtener_filtros_catalogo_sr(host, port, database, username, password)
        if not config.dry_run and filtros:
            _guardar_catalogo_filtros(server_id, system_type, filtros, sync_run_id, result)


def _obtener_familias_sr(host, port, database, username, password) -> List[FamiliaSync]:
    """Obtiene familias (grupos) de SoftRestaurant."""
    query = """
    SELECT idgrupo, descripcion, clasificacion, prioridad
    FROM grupos
    WHERE descripcion IS NOT NULL AND descripcion != ''
    ORDER BY descripcion
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []
    
    return [
        FamiliaSync(
            codigo_fuente=str(r.get('idgrupo', '')),
            nombre=str(r.get('descripcion', '')),
            # Fix FASE 1C-3B-R3: Convertir explícitamente a str() para evitar error
            # 'Decimal.replace()' cuando clasificacion viene como tipo numérico
            descripcion=str(r.get('clasificacion')) if r.get('clasificacion') is not None else None,
            orden=int(r.get('prioridad') or 0)
        )
        for r in rows
    ]


def _obtener_subfamilias_sr(host, port, database, username, password) -> List[SubFamiliaSync]:
    """Obtiene subfamilias (subgrupos) de SoftRestaurant."""
    query = """
    SELECT s.idsubgrupo, s.descripcion, gs.idgrupo
    FROM subgrupos s
    LEFT JOIN grupossubgrupos gs ON s.idsubgrupo = gs.idsubgrupo
    WHERE s.descripcion IS NOT NULL AND s.descripcion != ''
    ORDER BY s.descripcion
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []
    
    return [
        SubFamiliaSync(
            codigo_fuente=str(r.get('idsubgrupo', '')),
            nombre=str(r.get('descripcion', '')),
            familia_codigo_fuente=str(r.get('idgrupo', '')) if r.get('idgrupo') else None
        )
        for r in rows
    ]


def _obtener_insumos_sr(host, port, database, username, password) -> List[InsumoSync]:
    """Obtiene insumos con sus costos de SoftRestaurant."""
    query = """
    SELECT i.idinsumo, i.descripcion, i.unidad, i.elaborado, i.rendimientoelaborado,
           i.idgruposi as idgrupoinsumo, g.descripcion as grupoinsumo_nombre,
           id.costo, id.costopromedio, id.costoestandar, id.costoconimpuestos
    FROM insumos i
    LEFT JOIN insumosdetalle id ON i.idinsumo = id.idinsumo
    LEFT JOIN gruposi g ON i.idgruposi = g.idgruposi
    WHERE i.descripcion IS NOT NULL AND i.descripcion != ''
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []
    
    return [
        InsumoSync(
            codigo_fuente=str(r.get('idinsumo', '')),
            nombre=str(r.get('descripcion', '')),
            unidad_medida=str(r.get('unidad', 'UN')),
            costo=Decimal(str(r.get('costo') or 0)),
            costo_promedio=Decimal(str(r.get('costopromedio') or 0)),
            costo_estandar=Decimal(str(r.get('costoestandar') or 0)),
            costo_con_impuestos=Decimal(str(r.get('costoconimpuestos') or 0)),
            es_elaborado=bool(r.get('elaborado')),
            rendimiento_elaborado=Decimal(str(r.get('rendimientoelaborado'))) if r.get('rendimientoelaborado') else None,
            grupo_codigo_fuente=str(r.get('idgrupoinsumo', '')) if r.get('idgrupoinsumo') else None,
            grupo_nombre=str(r.get('grupoinsumo_nombre')) if r.get('grupoinsumo_nombre') else None
        )
        for r in rows
    ]


def _obtener_productos_sr(host, port, database, username, password) -> List[ProductoSync]:
    """Obtiene productos con precios de SoftRestaurant."""
    # BUG-COSTOS-001-R3: La columna real de estatus en SoftRestaurant es
    # productosdetalle.bloqueado (bit). 'suspendido' NO existe (por eso nunca
    # se marcaban inactivos). bloqueado=1 → producto de baja/inactivo.
    query = """
    SELECT p.idproducto, p.descripcion, p.nombrecorto, p.idgrupo,
           g.descripcion as grupo_nombre, g.clasificacion as clasificacion,
           pd.precio, pd.preciosinimpuestos, pd.impuesto1,
           ISNULL(pd.bloqueado, 0) as bloqueado
    FROM productos p
    LEFT JOIN productosdetalle pd ON p.idproducto = pd.idproducto
    LEFT JOIN grupos g ON p.idgrupo = g.idgrupo
    WHERE p.descripcion IS NOT NULL AND p.descripcion != ''
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []
    # CATALOGO-CANONICO-C1: SoftRestaurant grupos.clasificacion -> Categoria canonica.
    # En SoftRestaurant Cienfuegos: 1=BEBIDAS, 2=ALIMENTOS, 3=OTROS.
    _CLASIF_SR = {'1': 'BEBIDAS', '2': 'ALIMENTOS', '3': 'OTROS'}
    
    def _cat(r):
        c = r.get('clasificacion')
        if c is None or str(c).strip() == '':
            return None, None
        cs = str(c).strip()
        return cs, _CLASIF_SR.get(cs, 'OTROS')
    
    productos = []
    for r in rows:
        cat_cf, cat_nom = _cat(r)
        productos.append(ProductoSync(
            codigo_fuente=str(r.get('idproducto', '')),
            nombre=str(r.get('descripcion', '')),
            # Fix FASE 1C-3B-R3: Conversión explícita a str() para evitar bugs .replace()
            nombre_corto=str(r.get('nombrecorto')) if r.get('nombrecorto') else None,
            familia_codigo_fuente=str(r.get('idgrupo', '')) if r.get('idgrupo') else None,
            familia_nombre=str(r.get('grupo_nombre')) if r.get('grupo_nombre') else None,
            categoria_codigo_fuente=cat_cf,
            categoria_nombre=cat_nom,
            precio_venta=Decimal(str(r.get('precio') or 0)),
            precio_sin_impuestos=Decimal(str(r.get('preciosinimpuestos') or 0)),
            tasa_impuesto=Decimal(str(r.get('impuesto1') or 0)),
            # BUG-COSTOS-001-R3: bloqueado = 1 significa inactivo/de baja
            activo=not bool(r.get('bloqueado', 0))
        ))
    return productos


def _execute_pos_query_strict(
    host,
    port,
    database,
    username,
    password,
    query,
):
    """
    Ejecuta SQL contra POS con semantica fail-closed.

    Una consulta valida sin filas devuelve [].
    Un fallo de conexion o de SQL propaga excepcion.
    """
    connection = get_external_sql_connection({
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password": password,
        "login_timeout": 10,
        "timeout": 240,
        "as_dict": True,
    })

    try:
        try:
            cursor = connection.cursor(as_dict=True)
        except TypeError:
            cursor = connection.cursor()

        cursor.execute(query)
        rows = cursor.fetchall() or []

        if not rows:
            return []

        if isinstance(rows[0], dict):
            return [dict(row) for row in rows]

        columns = [
            column[0]
            for column in cursor.description
        ]

        return [
            dict(zip(columns, row))
            for row in rows
        ]
    finally:
        connection.close()


def _contar_productos_con_receta_sr(host, port, database, username, password) -> int:
    """Cuenta productos que tienen receta en tabla 'costos'."""
    query = "SELECT COUNT(DISTINCT idproducto) as cnt FROM costos"
    rows = _execute_pos_query_strict(
        host,
        port,
        database,
        username,
        password,
        query,
    )
    return int(rows[0].get('cnt', 0)) if rows else 0


def _obtener_recetas_sr(host, port, database, username, password) -> List[RecetaLineaSync]:
    """
    Obtiene recetas de productos desde tabla 'costos'.
    IMPORTANTE: NO usar explosioninsumosdetalle (vacía).
    """
    query = """
    SELECT c.idproducto, c.idinsumo, c.cantidad,
           i.descripcion as insumo_nombre, i.unidad, i.elaborado, i.rendimientoelaborado,
           id.costo, id.costopromedio
    FROM costos c
    LEFT JOIN insumos i ON c.idinsumo = i.idinsumo
    LEFT JOIN insumosdetalle id ON c.idinsumo = id.idinsumo
    WHERE c.cantidad > 0
    ORDER BY c.idproducto, c.idinsumo
    """
    rows = _execute_pos_query_strict(
        host,
        port,
        database,
        username,
        password,
        query,
    )
    
    result = []
    for r in rows:
        cantidad = Decimal(str(r.get('cantidad') or 0))
        costo_unit = Decimal(str(r.get('costo') or r.get('costopromedio') or 0))
        
        # No incluir líneas con cantidad <= 0
        if cantidad <= 0:
            continue
        
        result.append(RecetaLineaSync(
            producto_codigo_fuente=str(r.get('idproducto', '')),
            insumo_codigo_fuente=str(r.get('idinsumo', '')),
            insumo_nombre=str(r.get('insumo_nombre') or r.get('idinsumo', '')),
            cantidad=cantidad,
            unidad_medida=str(r.get('unidad', 'UN')),
            costo_unitario=costo_unit,
            costo_total=cantidad * costo_unit,
            es_elaborado=bool(r.get('elaborado')),
            rendimiento_elaborado=Decimal(str(r.get('rendimientoelaborado'))) if r.get('rendimientoelaborado') else None
        ))
    
    return result


def _obtener_elaborados_sr(host, port, database, username, password) -> List[ElaboradoLineaSync]:
    """Obtiene sub-recetas de insumos elaborados desde tabla 'elaborados'."""
    query = """
    SELECT e.idelaborado, e.idinsumo, e.cantidad,
           i.descripcion as insumo_nombre, i.unidad,
           id.costo, id.costopromedio
    FROM elaborados e
    LEFT JOIN insumos i ON e.idinsumo = i.idinsumo
    LEFT JOIN insumosdetalle id ON e.idinsumo = id.idinsumo
    WHERE e.cantidad > 0
    ORDER BY e.idelaborado, e.idinsumo
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []
    
    result = []
    for r in rows:
        cantidad = Decimal(str(r.get('cantidad') or 0))
        costo_unit = Decimal(str(r.get('costo') or r.get('costopromedio') or 0))
        
        if cantidad <= 0:
            continue
        
        result.append(ElaboradoLineaSync(
            insumo_elaborado_codigo_fuente=str(r.get('idelaborado', '')),
            insumo_componente_codigo_fuente=str(r.get('idinsumo', '')),
            insumo_componente_nombre=str(r.get('insumo_nombre') or r.get('idinsumo', '')),
            cantidad=cantidad,
            unidad_medida=str(r.get('unidad', 'UN')),
            costo_unitario=costo_unit,
            costo_total=cantidad * costo_unit
        ))
    
    return result


def _obtener_compuestos_sr(host, port, database, username, password) -> List[Dict]:
    """
    Obtiene relaciones de productos compuestos/modificadores desde SoftRestaurant.

    Fuente primaria: modificadores.
    No usar vwipadproductosmodificados como segunda fuente para evitar duplicar:
    esa vista reproduce la relacion producto/modificador.
    """
    query = """
    SELECT
        m.idproducto,
        m.idmodificador,
        COALESCE(p.descripcion, m.idmodificador) AS componente_nombre,
        m.precio,
        m.idgruposmodificadores,
        m.idempresa
    FROM modificadores m
    LEFT JOIN productos p ON p.idproducto = m.idmodificador
    WHERE m.idproducto IS NOT NULL
      AND m.idmodificador IS NOT NULL
      AND LTRIM(RTRIM(m.idproducto)) <> ''
      AND LTRIM(RTRIM(m.idmodificador)) <> ''
    ORDER BY m.idproducto, m.idmodificador
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []

    result = []
    seen = set()
    for r in rows:
        producto = str(r.get('idproducto') or '').strip()
        componente = str(r.get('idmodificador') or '').strip()
        key = (producto, componente, 'MODIFICADORES')
        if not producto or not componente or key in seen:
            continue
        seen.add(key)

        costo_unit = Decimal(str(r.get('precio') or 0))
        cantidad = Decimal('1')

        result.append({
            'producto_codigo_fuente': producto,
            'componente_codigo_fuente': componente,
            'componente_nombre': str(r.get('componente_nombre') or componente),
            'cantidad': cantidad,
            'unidad_medida': 'UN',
            'costo_unitario': costo_unit,
            'costo_total': cantidad * costo_unit,
            'fuente_detalle': 'MODIFICADORES',
            'grupo_codigo_fuente': str(r.get('idgruposmodificadores') or '') or None,
            'empresa_codigo_fuente': str(r.get('idempresa') or '') or None,
        })

    return result


# ============================================================================
# CATALOGO-CANONICO-C1: Dimensiones de filtro (NO-LIVE) - SoftRestaurant
# ============================================================================

# Mapeo canonico de clasificacionventa para SoftRestaurant Cienfuegos.
_CLASIF_VENTA_SR = {'1': 'BEBIDAS', '2': 'ALIMENTOS', '3': 'OTROS'}


def _obtener_filtros_catalogo_sr(host, port, database, username, password) -> List[Dict]:
    """
    Obtiene las dimensiones de filtro de la jerarquía de INSUMOS de SoftRestaurant
    (la que usa el Análisis de inventarios):
      - CATEGORIA   = clasificacionventa (1/2/3)
      - FAMILIA     = gruposiclasificacion (idgruposiclasificacion)
      - SUBFAMILIA  = gruposi (idgruposi)
    Retorna lista de dicts {nivel, codigo, nombre, parent}.
    """
    filtros: List[Dict] = []

    # FAMILIA: gruposiclasificacion (+ su clasificacionventa = categoría padre)
    fam_query = "SELECT idgruposiclasificacion, descripcion, clasificacionventa FROM gruposiclasificacion"
    fam_rows = execute_sql_query(host, port, database, username, password, fam_query) or []
    cats_vistas = set()
    for r in fam_rows:
        cod = str(r.get('idgruposiclasificacion') or '').strip()
        if not cod:
            continue
        clas = r.get('clasificacionventa')
        clas = str(int(clas)) if clas is not None else None
        filtros.append({
            'nivel': 'FAMILIA',
            'codigo': cod,
            'nombre': str(r.get('descripcion') or '').strip() or cod,
            'parent': clas,
        })
        if clas:
            cats_vistas.add(clas)

    # CATEGORIA: derivada de las clasificacionventa presentes (data-driven)
    for clas in sorted(cats_vistas):
        filtros.append({
            'nivel': 'CATEGORIA',
            'codigo': clas,
            'nombre': _CLASIF_VENTA_SR.get(clas, 'OTROS'),
            'parent': None,
        })

    # SUBFAMILIA: gruposi (+ su gruposiclasificacion = familia padre)
    sub_query = "SELECT idgruposi, descripcion, idgruposiclasificacion FROM gruposi"
    sub_rows = execute_sql_query(host, port, database, username, password, sub_query) or []
    for r in sub_rows:
        cod = str(r.get('idgruposi') or '').strip()
        if not cod:
            continue
        parent = str(r.get('idgruposiclasificacion') or '').strip() or None
        filtros.append({
            'nivel': 'SUBFAMILIA',
            'codigo': cod,
            'nombre': str(r.get('descripcion') or '').strip() or cod,
            'parent': parent,
        })

    return filtros


def _guardar_catalogo_filtros(server_id: str, system_type: str, filtros: List[Dict],
                              sync_run_id: str, result: Dict) -> None:
    """Guarda las dimensiones de filtro en EDARSAHUB.Sync_Catalogo_Filtros (UPSERT)."""
    for f in filtros:
        try:
            nombre_esc = (f.get('nombre') or '').replace("'", "''")
            codigo_esc = (f.get('codigo') or '').replace("'", "''")
            parent = f.get('parent')
            parent_sql = f"'{parent.replace(chr(39), chr(39)+chr(39))}'" if parent else 'NULL'
            query = f"""
            MERGE Sync_Catalogo_Filtros AS target
            USING (SELECT '{server_id}' as ServerID, '{f['nivel']}' as Nivel, '{codigo_esc}' as Codigo) AS source
            ON target.ServerID = CAST(source.ServerID AS UNIQUEIDENTIFIER)
               AND target.Nivel = source.Nivel
               AND target.Codigo = source.Codigo
            WHEN MATCHED THEN
                UPDATE SET
                    Nombre = N'{nombre_esc}',
                    ParentCodigo = {parent_sql},
                    SystemType = '{system_type}',
                    Activo = 1,
                    SyncRunID = '{sync_run_id}',
                    SyncedAtMexico = SYSDATETIME(),
                    FechaModificacion = SYSDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (ServerID, SystemType, Nivel, Codigo, Nombre, ParentCodigo, Activo, SyncRunID, SyncedAtMexico)
                VALUES (
                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
                    '{system_type}',
                    '{f['nivel']}',
                    '{codigo_esc}',
                    N'{nombre_esc}',
                    {parent_sql},
                    1,
                    '{sync_run_id}',
                    SYSDATETIME()
                );
            """
            execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                query
            )
            result['insertados'] += 1
        except Exception as e:
            result['errores_count'] += 1
            if len(result['errores']) < 10:
                result['errores'].append(f"Error filtro {f.get('nivel')}/{f.get('codigo')}: {str(e)[:80]}")


# ============================================================================
# SINCRONIZACIÓN MPRO
# ============================================================================

def _sync_mpro(
    server_id: str,
    host: str, port: int, database: str,
    username: str, password: str,
    system_type: str,
    config: SyncRecetasConfig,
    sync_run_id: str,
    result: Dict
) -> None:
    """Sincroniza desde MPRO (ManagmentPro)."""
    
    # 1. Sincronizar Familias
    if config.sync_familias:
        familias = _obtener_familias_mpro(host, port, database, username, password)
        result['familias'] = len(familias)
        
        if not config.dry_run and familias:
            _guardar_familias(server_id, system_type, familias, sync_run_id, result)
    
    # 2. Sincronizar SubFamilias
    if config.sync_familias:
        subfamilias = _obtener_subfamilias_mpro(host, port, database, username, password)
        result['subfamilias'] = len(subfamilias)
        
        if not config.dry_run and subfamilias:
            _guardar_subfamilias(server_id, system_type, subfamilias, sync_run_id, result)
    
    # 3. Sincronizar Insumos (desde Existencia para costos)
    if config.sync_insumos:
        insumos = _obtener_insumos_mpro(host, port, database, username, password)
        result['insumos'] = len(insumos)
        
        if not config.dry_run and insumos:
            _guardar_insumos(server_id, system_type, insumos, sync_run_id, result)
    
    # 4. Sincronizar Productos
    if config.sync_productos:
        productos = _obtener_productos_mpro(host, port, database, username, password)
        result['productos'] = len(productos)
        
        # Contar productos con receta
        productos_con_receta = _contar_productos_con_receta_mpro(host, port, database, username, password)
        result['productos_con_receta'] = productos_con_receta
        
        if not config.dry_run and productos:
            _guardar_productos(server_id, system_type, productos, sync_run_id, result)
    
    # 5. Sincronizar Recetas (Formula_Produccion_Detalle)
    if config.sync_recetas:
        recetas = _obtener_recetas_mpro(host, port, database, username, password)
        result['lineas_receta'] = len(recetas)
        
        if not config.dry_run:
            _guardar_recetas(server_id, system_type, recetas, sync_run_id, result)

    # 6. Sincronizar Productos Compuestos (Producto_Kit)
    if config.sync_recetas:
        compuestos_mpro = _obtener_compuestos_mpro(host, port, database, username, password)
        result['compuestos'] = len(compuestos_mpro)

        if not config.dry_run and compuestos_mpro:
            _guardar_compuestos(server_id, system_type, compuestos_mpro, sync_run_id, result)




def _obtener_compuestos_mpro(host, port, database, username, password) -> List[Dict]:
    """
    Obtiene productos compuestos desde MPRO Producto_Kit.

    Fuente primaria: Producto_Kit.
    No se mezcla con Formula_Produccion_Detalle para evitar duplicar recetas normales.
    """
    query = """
    SELECT
        pk.Pr_Cve_Producto,
        pk.Pk_Producto,
        COALESCE(p.Pr_Descripcion, pk.Pk_Producto) AS componente_nombre,
        pk.Pk_Cantidad,
        pk.Pk_Cantidad_Total,
        pk.Un_Cve_Unidad,
        pk.Pk_Costo,
        pk.Pk_Factor_Costo
    FROM Producto_Kit pk
    LEFT JOIN Producto p ON p.Pr_Cve_Producto = pk.Pk_Producto
    WHERE pk.Pr_Cve_Producto IS NOT NULL
      AND pk.Pk_Producto IS NOT NULL
    ORDER BY pk.Pr_Cve_Producto, pk.Pk_Producto
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []

    result = []
    seen = set()
    for r in rows:
        producto = str(r.get('Pr_Cve_Producto') or '').strip()
        componente = str(r.get('Pk_Producto') or '').strip()
        key = (producto, componente, 'PRODUCTO_KIT')
        if not producto or not componente or key in seen:
            continue
        seen.add(key)

        cantidad = Decimal(str(r.get('Pk_Cantidad_Total') or r.get('Pk_Cantidad') or 1))
        if cantidad <= 0:
            continue

        costo_unit = Decimal(str(r.get('Pk_Costo') or 0))

        result.append({
            'producto_codigo_fuente': producto,
            'componente_codigo_fuente': componente,
            'componente_nombre': str(r.get('componente_nombre') or componente),
            'cantidad': cantidad,
            'unidad_medida': str(r.get('Un_Cve_Unidad') or 'UN'),
            'costo_unitario': costo_unit,
            'costo_total': cantidad * costo_unit,
            'fuente_detalle': 'PRODUCTO_KIT',
            'grupo_codigo_fuente': None,
            'empresa_codigo_fuente': None,
        })

    return result

def _obtener_familias_mpro(host, port, database, username, password) -> List[FamiliaSync]:
    """Obtiene familias de MPRO."""
    query = """
    SELECT Fm_Cve_Familia, Fm_Descripcion
    FROM Familia
    WHERE Es_Cve_Estado = 'AC'
    ORDER BY Fm_Descripcion
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []
    
    return [
        FamiliaSync(
            codigo_fuente=str(r.get('Fm_Cve_Familia', '')),
            nombre=str(r.get('Fm_Descripcion', ''))
        )
        for r in rows
    ]


def _obtener_subfamilias_mpro(host, port, database, username, password) -> List[SubFamiliaSync]:
    """Obtiene subfamilias de MPRO."""
    query = """
    SELECT Sf_Cve_SubFamilia, Sf_Descripcion, Fm_Cve_Familia
    FROM SubFamilia
    WHERE Es_Cve_Estado = 'AC'
    ORDER BY Sf_Descripcion
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []
    
    return [
        SubFamiliaSync(
            codigo_fuente=str(r.get('Sf_Cve_SubFamilia', '')),
            nombre=str(r.get('Sf_Descripcion', '')),
            familia_codigo_fuente=str(r.get('Fm_Cve_Familia', '')) if r.get('Fm_Cve_Familia') else None
        )
        for r in rows
    ]


def _obtener_insumos_mpro(host, port, database, username, password) -> List[InsumoSync]:
    """Obtiene productos/insumos con costos de MPRO (desde Existencia)."""
    query = """
    SELECT p.Pr_Cve_Producto, p.Pr_Descripcion, p.Pr_Unidad_Venta,
           e.Ex_Ultimo_Costo, e.Ex_Costo_Promedio, e.Ex_Costo_Estandar
    FROM Producto p
    LEFT JOIN Existencia e ON p.Pr_Cve_Producto = e.Pr_Cve_Producto
    WHERE p.Es_Cve_Estado = 'AC'
    AND p.Pr_Descripcion IS NOT NULL
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []
    
    return [
        InsumoSync(
            codigo_fuente=str(r.get('Pr_Cve_Producto', '')),
            nombre=str(r.get('Pr_Descripcion', '')),
            unidad_medida=str(r.get('Pr_Unidad_Venta', 'UN')),
            ultimo_costo=Decimal(str(r.get('Ex_Ultimo_Costo') or 0)),
            costo_promedio=Decimal(str(r.get('Ex_Costo_Promedio') or 0)),
            costo_estandar=Decimal(str(r.get('Ex_Costo_Estandar') or 0)),
            costo=Decimal(str(r.get('Ex_Ultimo_Costo') or r.get('Ex_Costo_Promedio') or 0))
        )
        for r in rows
    ]


def _obtener_productos_mpro(host, port, database, username, password) -> List[ProductoSync]:
    """
    Obtiene productos con precios e IMPUESTOS de MPRO.
    
    FASE 1C-3G-B: Corrección de homologación fiscal.
    BUG-COSTOS-001-R2: Traer TODOS los productos y marcar su estado.
    
    ESTADOS MPRO:
    - Es_Cve_Estado = 'AC' → Activo
    - Es_Cve_Estado = 'BA' → Baja
    - Es_Cve_Estado = 'IN' → Inactivo
    - Cualquier otro → Inactivo
    
    LÓGICA DE IMPUESTOS:
    - MPRO almacena impuestos en Impuesto_Grupo_Impuesto (relación N:M con Producto)
    - Un producto puede tener múltiples impuestos (IVA + IEPS, IVA + Retención, etc.)
    - Para VENTAS, priorizamos: IVA COBRADO > IVA positivo > IEPS > IVA 0%/Exento
    - Retenciones (tasas negativas) se excluyen del cálculo de precio de venta
    
    ESTADOS DE IMPUESTO:
    - Im_Tasa IS NOT NULL y >= 0: Impuesto válido (puede ser 0% tasa cero)
    - Im_Tasa IS NULL: IMPUESTO_NO_CONFIGURADO (producto sin homologación fiscal)
    - Im_Tipo_Factor = 'Exento': Producto fiscalmente exento
    
    REGLA CRÍTICA: NO hardcodear 16%. La tasa real viene de MPRO.
    """
    # Query con CTE para priorizar impuestos y evitar duplicados
    # BUG-COSTOS-001-R2: Traer TODOS los productos, no solo AC
    query = """
    WITH ImpuestosPriorizados AS (
        SELECT 
            p.Pr_Cve_Producto,
            i.Im_Cve_Impuesto,
            i.Im_Descripcion,
            i.Im_Tasa,
            i.Im_Tipo_Impuesto,
            i.Im_Tipo_Factor,
            ROW_NUMBER() OVER (PARTITION BY p.Pr_Cve_Producto ORDER BY 
                CASE 
                    WHEN i.Im_Cve_Impuesto = '0013' THEN 1  -- IVA COBRADO 16% (prioridad máxima para ventas)
                    WHEN i.Im_Tipo_Impuesto = 'IVA' AND i.Im_Tasa > 0 THEN 2  -- Otro IVA positivo
                    WHEN i.Im_Tipo_Impuesto = 'IEPS' AND i.Im_Tasa > 0 THEN 3  -- IEPS positivo
                    WHEN i.Im_Tipo_Impuesto = 'IVA' AND i.Im_Tasa = 0 AND i.Im_Tipo_Factor = 'Exento' THEN 4  -- Exento
                    WHEN i.Im_Tipo_Impuesto = 'IVA' AND i.Im_Tasa = 0 THEN 5  -- Tasa 0%
                    ELSE 99  -- Otros
                END
            ) as rn
        FROM Producto p
        LEFT JOIN Impuesto_Grupo_Impuesto igi ON p.Pr_Cve_Producto = igi.Pr_Cve_Producto AND igi.Es_Cve_Estado = 'AC'
        LEFT JOIN Impuesto i ON igi.Im_Cve_Impuesto = i.Im_Cve_Impuesto AND i.Es_Cve_Estado = 'AC'
        WHERE (i.Im_Tipo_Impuesto IS NULL OR i.Im_Tasa >= 0)  -- Excluir retenciones (tasas negativas)
    )
    SELECT 
        p.Pr_Cve_Producto,
        p.Pr_Descripcion,
        p.Pr_Descripcion_Corta,
        p.Fm_Cve_Familia,
        p.Sf_Cve_SubFamilia,
        p.Ct_Cve_Categoria,
        ct.Ct_Descripcion,
        f.Fm_Descripcion,
        sf.Sf_Descripcion,
        pp.Pp_Precio_1 as Precio,
        ip.Im_Cve_Impuesto,
        ip.Im_Descripcion as Impuesto_Descripcion,
        ip.Im_Tasa,
        ip.Im_Tipo_Factor,
        p.Es_Cve_Estado,
        CASE 
            WHEN ip.Im_Cve_Impuesto IS NULL THEN 'NO_CONFIGURADO'
            WHEN ip.Im_Tipo_Factor = 'Exento' THEN 'EXENTO'
            ELSE 'OK'
        END as Estado_Impuesto
    FROM Producto p
    LEFT JOIN Familia f ON p.Fm_Cve_Familia = f.Fm_Cve_Familia
    LEFT JOIN SubFamilia sf ON p.Sf_Cve_SubFamilia = sf.Sf_Cve_SubFamilia
    LEFT JOIN Categoria ct ON p.Ct_Cve_Categoria = ct.Ct_Cve_Categoria
    LEFT JOIN Producto_Precio pp ON p.Pr_Cve_Producto = pp.Pr_Cve_Producto
    LEFT JOIN ImpuestosPriorizados ip ON p.Pr_Cve_Producto = ip.Pr_Cve_Producto AND ip.rn = 1
    WHERE p.Pr_Descripcion IS NOT NULL
    """
    rows = execute_sql_query(host, port, database, username, password, query) or []
    
    productos = []
    for r in rows:
        # Obtener tasa de impuesto
        tasa_raw = r.get('Im_Tasa')
        # estado_impuesto disponible en r.get('Estado_Impuesto') para logging/debug si se requiere
        
        # Determinar tasa_impuesto:
        # - Si tiene impuesto configurado: usar la tasa real (puede ser 0 si es tasa cero válida)
        # - Si NO tiene impuesto: usar -1 como marcador de IMPUESTO_NO_CONFIGURADO
        if tasa_raw is not None:
            tasa_impuesto = Decimal(str(tasa_raw))
        else:
            # Producto sin configuración fiscal - marcador especial
            tasa_impuesto = Decimal('-1')  # Indica IMPUESTO_NO_CONFIGURADO
        
        # Calcular precio sin impuestos (si el precio incluye IVA)
        precio_venta = Decimal(str(r.get('Precio') or 0))
        if tasa_impuesto > 0 and precio_venta > 0:
            # Asumiendo precio con IVA incluido, calcular precio base
            precio_sin_impuestos = precio_venta / (1 + tasa_impuesto / 100)
        else:
            precio_sin_impuestos = precio_venta
        
        # BUG-COSTOS-001-R2: Determinar si producto está activo basado en Es_Cve_Estado
        # AC = Activo, BA = Baja, IN = Inactivo
        estado_producto = r.get('Es_Cve_Estado', 'AC')
        activo = estado_producto == 'AC'
        
        productos.append(ProductoSync(
            codigo_fuente=str(r.get('Pr_Cve_Producto', '')),
            nombre=str(r.get('Pr_Descripcion', '')),
            # Fix FASE 1C-3B-R3: Conversión explícita a str() para evitar bugs .replace()
            nombre_corto=str(r.get('Pr_Descripcion_Corta')) if r.get('Pr_Descripcion_Corta') else None,
            familia_codigo_fuente=str(r.get('Fm_Cve_Familia', '')) if r.get('Fm_Cve_Familia') else None,
            subfamilia_codigo_fuente=str(r.get('Sf_Cve_SubFamilia', '')) if r.get('Sf_Cve_SubFamilia') else None,
            familia_nombre=str(r.get('Fm_Descripcion')) if r.get('Fm_Descripcion') else None,
            subfamilia_nombre=str(r.get('Sf_Descripcion')) if r.get('Sf_Descripcion') else None,
            categoria_codigo_fuente=str(r.get('Ct_Cve_Categoria', '')) if r.get('Ct_Cve_Categoria') else None,
            categoria_nombre=str(r.get('Ct_Descripcion')) if r.get('Ct_Descripcion') else None,
            precio_venta=precio_venta,
            precio_sin_impuestos=precio_sin_impuestos,
            tasa_impuesto=tasa_impuesto,
            # BUG-COSTOS-001-R2: Sincronizar estado activo desde MPRO
            activo=activo
        ))
    
    return productos


def _contar_productos_con_receta_mpro(host, port, database, username, password) -> int:
    """Cuenta productos con fórmula de producción en MPRO."""
    query = "SELECT COUNT(DISTINCT Pr_Cve_Producto) as cnt FROM Formula_Produccion WHERE Es_Cve_Estado = 'AC'"
    rows = _execute_pos_query_strict(
        host,
        port,
        database,
        username,
        password,
        query,
    )
    return int(rows[0].get('cnt', 0)) if rows else 0


def _obtener_recetas_mpro(host, port, database, username, password) -> List[RecetaLineaSync]:
    """Obtiene recetas desde Formula_Produccion_Detalle de MPRO.

    En MPRO:
    - Fpd_Cantidad = cantidad normalizada por rendimiento.
    - Fpd_Cantidad_Total = cantidad real de la receta completa.
    - Fp_Rendimiento = rendimiento de la fórmula.
    """
    query = """
    SELECT
           fpd.Pr_Cve_Producto,
           fpd.Fpd_Producto as insumo_codigo,
           fp.Fp_Rendimiento,
           fpd.Fpd_Cantidad,
           fpd.Fpd_Cantidad_Total,
           fpd.Fpd_Unidad,
           fpd.Fpd_Costo,
           fpd.Fpd_Costo_Total,
           p.Pr_Descripcion as insumo_nombre
    FROM Formula_Produccion_Detalle fpd
    JOIN Formula_Produccion fp
      ON fpd.Pr_Cve_Producto = fp.Pr_Cve_Producto
     AND fpd.Fp_ID = fp.Fp_ID
    LEFT JOIN Producto p
      ON fpd.Fpd_Producto = p.Pr_Cve_Producto
    WHERE fp.Es_Cve_Estado = 'AC'
      AND fpd.Fpd_Cantidad > 0
    ORDER BY fpd.Pr_Cve_Producto, fpd.Fpd_Producto
    """
    rows = _execute_pos_query_strict(
        host,
        port,
        database,
        username,
        password,
        query,
    )

    def _dec(value, default='0'):
        if value is None:
            return Decimal(default)
        try:
            return Decimal(str(value))
        except Exception:
            return Decimal(default)

    result = []
    for r in rows:
        cantidad_unitaria = _dec(r.get('Fpd_Cantidad'))
        rendimiento = _dec(r.get('Fp_Rendimiento'))

        if r.get('Fpd_Cantidad_Total') is not None:
            cantidad = _dec(r.get('Fpd_Cantidad_Total'))
        elif rendimiento > 0:
            cantidad = cantidad_unitaria * rendimiento
        else:
            cantidad = cantidad_unitaria

        costo_fuente = _dec(r.get('Fpd_Costo'))

        if r.get('Fpd_Costo_Total') is not None:
            costo_total = _dec(r.get('Fpd_Costo_Total'))
        elif rendimiento > 0:
            costo_total = costo_fuente * rendimiento
        else:
            costo_total = cantidad * costo_fuente

        costo_unitario_real = (costo_total / cantidad) if cantidad > 0 else Decimal('0')

        if cantidad <= 0:
            continue

        result.append(RecetaLineaSync(
            producto_codigo_fuente=str(r.get('Pr_Cve_Producto', '')),
            insumo_codigo_fuente=str(r.get('insumo_codigo', '')),
            insumo_nombre=str(r.get('insumo_nombre') or r.get('insumo_codigo', '')),
            cantidad=cantidad,
            unidad_medida=str(r.get('Fpd_Unidad', 'UN')),
            costo_unitario=costo_unitario_real,
            costo_total=costo_total,
            rendimiento_elaborado=rendimiento if rendimiento > 0 else None
        ))

    return result


# ============================================================================
# FUNCIONES DE GUARDADO EN EDARSAHUB
# ============================================================================

def _guardar_familias(server_id: str, system_type: str, familias: List[FamiliaSync], 
                      sync_run_id: str, result: Dict) -> None:
    """Guarda familias en EDARSAHUB SQL."""
    for fam in familias:
        try:
            # UPSERT usando MERGE
            query = f"""
            MERGE Sync_Productos_Familias AS target
            USING (SELECT '{server_id}' as ServerID, '{fam.codigo_fuente}' as CodigoFuente) AS source
            ON target.ServerID = CAST(source.ServerID AS UNIQUEIDENTIFIER) 
               AND target.CodigoFuente = source.CodigoFuente
            WHEN MATCHED THEN
                UPDATE SET 
                    Nombre = N'{fam.nombre.replace("'", "''")}',
                    Descripcion = {f"N'{fam.descripcion.replace(chr(39), chr(39)+chr(39))}'" if fam.descripcion else 'NULL'},
                    Orden = {fam.orden},
                    SystemType = '{system_type}',
                    SyncRunID = '{sync_run_id}',
                    SyncedAtMexico = SYSDATETIME(),
                    FechaModificacion = SYSDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (ServerID, CodigoFuente, Nombre, Descripcion, Orden, SystemType, SyncRunID, Activo)
                VALUES (
                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
                    '{fam.codigo_fuente}',
                    N'{fam.nombre.replace("'", "''")}',
                    {f"N'{fam.descripcion.replace(chr(39), chr(39)+chr(39))}'" if fam.descripcion else 'NULL'},
                    {fam.orden},
                    '{system_type}',
                    '{sync_run_id}',
                    1
                );
            """
            execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                query
            )
            result['insertados'] += 1
        except Exception as e:
            result['errores_count'] += 1
            result['errores'].append(f"Error familia {fam.codigo_fuente}: {str(e)[:100]}")


def _guardar_subfamilias(server_id: str, system_type: str, subfamilias: List[SubFamiliaSync],
                         sync_run_id: str, result: Dict) -> None:
    """Guarda subfamilias en EDARSAHUB SQL."""
    for sf in subfamilias:
        try:
            query = f"""
            MERGE Sync_Productos_SubFamilias AS target
            USING (SELECT '{server_id}' as ServerID, '{sf.codigo_fuente}' as CodigoFuente) AS source
            ON target.ServerID = CAST(source.ServerID AS UNIQUEIDENTIFIER) 
               AND target.CodigoFuente = source.CodigoFuente
            WHEN MATCHED THEN
                UPDATE SET 
                    Nombre = N'{sf.nombre.replace("'", "''")}',
                    FamiliaCodigoFuente = {f"'{sf.familia_codigo_fuente}'" if sf.familia_codigo_fuente else 'NULL'},
                    SystemType = '{system_type}',
                    SyncRunID = '{sync_run_id}',
                    SyncedAtMexico = SYSDATETIME(),
                    FechaModificacion = SYSDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (ServerID, CodigoFuente, Nombre, FamiliaCodigoFuente, SystemType, SyncRunID, Activo)
                VALUES (
                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
                    '{sf.codigo_fuente}',
                    N'{sf.nombre.replace("'", "''")}',
                    {f"'{sf.familia_codigo_fuente}'" if sf.familia_codigo_fuente else 'NULL'},
                    '{system_type}',
                    '{sync_run_id}',
                    1
                );
            """
            execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                query
            )
            result['insertados'] += 1
        except Exception as e:
            result['errores_count'] += 1
            result['errores'].append(f"Error subfamilia {sf.codigo_fuente}: {str(e)[:100]}")


def _guardar_insumos(server_id: str, system_type: str, insumos: List[InsumoSync],
                     sync_run_id: str, result: Dict) -> None:
    """Guarda insumos en EDARSAHUB SQL."""
    for ins in insumos:
        try:
            nombre_escaped = ins.nombre.replace("'", "''")
            grupo_codigo = ins.grupo_codigo_fuente.replace("'", "''") if ins.grupo_codigo_fuente else None
            grupo_nombre = ins.grupo_nombre.replace("'", "''") if ins.grupo_nombre else None
            query = f"""
            MERGE Sync_Productos_Insumos AS target
            USING (SELECT '{server_id}' as ServerID, '{ins.codigo_fuente}' as CodigoFuente) AS source
            ON target.ServerID = CAST(source.ServerID AS UNIQUEIDENTIFIER) 
               AND target.CodigoFuente = source.CodigoFuente
            WHEN MATCHED THEN
                UPDATE SET 
                    Nombre = N'{nombre_escaped}',
                    UnidadMedida = '{ins.unidad_medida}',
                    Costo = {ins.costo},
                    CostoPromedio = {ins.costo_promedio},
                    UltimoCosto = {ins.ultimo_costo},
                    CostoEstandar = {ins.costo_estandar},
                    CostoConImpuestos = {ins.costo_con_impuestos},
                    EsElaborado = {1 if ins.es_elaborado else 0},
                    RendimientoElaborado = {ins.rendimiento_elaborado if ins.rendimiento_elaborado else 'NULL'},
                    GrupoInsumoCodigoFuente = {f"'{grupo_codigo}'" if grupo_codigo else 'NULL'},
                    GrupoInsumoNombre = {f"N'{grupo_nombre}'" if grupo_nombre else 'NULL'},
                    SystemType = '{system_type}',
                    SyncRunID = '{sync_run_id}',
                    SyncedAtMexico = SYSDATETIME(),
                    FechaModificacion = SYSDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (ServerID, CodigoFuente, Nombre, UnidadMedida, Costo, CostoPromedio, 
                        UltimoCosto, CostoEstandar, CostoConImpuestos, EsElaborado, 
                        RendimientoElaborado, GrupoInsumoCodigoFuente, GrupoInsumoNombre,
                        SystemType, SyncRunID, Activo)
                VALUES (
                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
                    '{ins.codigo_fuente}',
                    N'{nombre_escaped}',
                    '{ins.unidad_medida}',
                    {ins.costo}, {ins.costo_promedio}, {ins.ultimo_costo}, {ins.costo_estandar},
                    {ins.costo_con_impuestos},
                    {1 if ins.es_elaborado else 0},
                    {ins.rendimiento_elaborado if ins.rendimiento_elaborado else 'NULL'},
                    {f"'{grupo_codigo}'" if grupo_codigo else 'NULL'},
                    {f"N'{grupo_nombre}'" if grupo_nombre else 'NULL'},
                    '{system_type}',
                    '{sync_run_id}',
                    1
                );
            """
            execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                query
            )
            result['insertados'] += 1
        except Exception as e:
            result['errores_count'] += 1
            if len(result['errores']) < 10:  # Limitar errores
                result['errores'].append(f"Error insumo {ins.codigo_fuente}: {str(e)[:80]}")


def _guardar_productos(server_id: str, system_type: str, productos: List[ProductoSync],
                       sync_run_id: str, result: Dict) -> None:
    """Guarda productos en EDARSAHUB SQL."""
    for prod in productos:
        try:
            nombre_escaped = prod.nombre.replace("'", "''")
            nombre_corto = prod.nombre_corto.replace("'", "''") if prod.nombre_corto else None
            fam_nombre = prod.familia_nombre.replace("'", "''") if prod.familia_nombre else None
            # CATALOGO-CANONICO-C1: subfamilia + categoria
            subfam_nombre = prod.subfamilia_nombre.replace("'", "''") if prod.subfamilia_nombre else None
            cat_nombre = prod.categoria_nombre.replace("'", "''") if prod.categoria_nombre else None
            subfam_cf = f"'{prod.subfamilia_codigo_fuente}'" if prod.subfamilia_codigo_fuente else 'NULL'
            cat_cf = f"'{prod.categoria_codigo_fuente}'" if prod.categoria_codigo_fuente else 'NULL'
            # BUG-COSTOS-001-FIX: Convertir activo a bit para SQL
            activo_bit = 1 if prod.activo else 0
            
            query = f"""
            MERGE Sync_Productos AS target
            USING (SELECT '{server_id}' as ServerID, '{prod.codigo_fuente}' as CodigoFuente) AS source
            ON target.ServerID = CAST(source.ServerID AS UNIQUEIDENTIFIER) 
               AND target.CodigoFuente = source.CodigoFuente
            WHEN MATCHED THEN
                UPDATE SET 
                    Nombre = N'{nombre_escaped}',
                    NombreCorto = {f"N'{nombre_corto}'" if nombre_corto else 'NULL'},
                    FamiliaCodigoFuente = {f"'{prod.familia_codigo_fuente}'" if prod.familia_codigo_fuente else 'NULL'},
                    FamiliaNombre = {f"N'{fam_nombre}'" if fam_nombre else 'NULL'},
                    SubFamiliaCodigoFuente = {subfam_cf},
                    SubFamiliaNombre = {f"N'{subfam_nombre}'" if subfam_nombre else 'NULL'},
                    CategoriaCodigoFuente = {cat_cf},
                    CategoriaNombre = {f"N'{cat_nombre}'" if cat_nombre else 'NULL'},
                    PrecioVenta = {prod.precio_venta},
                    PrecioSinImpuestos = {prod.precio_sin_impuestos},
                    TasaImpuesto = {prod.tasa_impuesto},
                    Activo = {activo_bit},
                    SystemType = '{system_type}',
                    SyncRunID = '{sync_run_id}',
                    SyncedAtMexico = SYSDATETIME(),
                    FechaModificacion = SYSDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (ServerID, CodigoFuente, Nombre, NombreCorto, FamiliaCodigoFuente, FamiliaNombre,
                        SubFamiliaCodigoFuente, SubFamiliaNombre, CategoriaCodigoFuente, CategoriaNombre,
                        PrecioVenta, PrecioSinImpuestos, TasaImpuesto, SystemType, SyncRunID, Activo)
                VALUES (
                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
                    '{prod.codigo_fuente}',
                    N'{nombre_escaped}',
                    {f"N'{nombre_corto}'" if nombre_corto else 'NULL'},
                    {f"'{prod.familia_codigo_fuente}'" if prod.familia_codigo_fuente else 'NULL'},
                    {f"N'{fam_nombre}'" if fam_nombre else 'NULL'},
                    {subfam_cf},
                    {f"N'{subfam_nombre}'" if subfam_nombre else 'NULL'},
                    {cat_cf},
                    {f"N'{cat_nombre}'" if cat_nombre else 'NULL'},
                    {prod.precio_venta}, {prod.precio_sin_impuestos}, {prod.tasa_impuesto},
                    '{system_type}',
                    '{sync_run_id}',
                    {activo_bit}
                );
            """
            execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                query
            )
            result['insertados'] += 1
        except Exception as e:
            result['errores_count'] += 1
            if len(result['errores']) < 10:
                result['errores'].append(f"Error producto {prod.codigo_fuente}: {str(e)[:80]}")


def _guardar_recetas(
    server_id: str,
    system_type: str,
    recetas: List[RecetaLineaSync],
    sync_run_id: str,
    result: Dict,
) -> None:
    """
    Persiste el snapshot vigente de recetas para un ServerID.

    Garantías:
    - una única transacción por servidor;
    - líneas vistas quedan Activo=1;
    - líneas previamente activas no vistas quedan Activo=0;
    - TieneReceta y CantidadComponentesReceta se recalculan
      exclusivamente desde líneas activas;
    - cualquier fallo provoca rollback completo.
    """
    conn = get_edarsahub_pymssql_connection(
        timeout=240,
        login_timeout=10,
        autocommit=False,
    )

    processed = 0

    try:
        cursor = conn.cursor(as_dict=True)

        merge_sql = """
        MERGE dbo.Sync_Productos_Recetas AS target
        USING (
            SELECT
                CAST(%s AS UNIQUEIDENTIFIER) AS ServerID,
                %s AS ProductoCodigoFuente,
                %s AS ComponenteCodigoFuente
        ) AS source
        ON target.ServerID = source.ServerID
           AND target.ProductoCodigoFuente =
               source.ProductoCodigoFuente
           AND target.ComponenteCodigoFuente =
               source.ComponenteCodigoFuente

        WHEN MATCHED THEN
            UPDATE SET
                ComponenteNombre = %s,
                TipoComponente = 'INSUMO',
                Cantidad = %s,
                UnidadMedida = %s,
                CostoUnitario = %s,
                CostoTotal = %s,
                EsElaborado = %s,
                RendimientoElaborado = %s,
                SystemType = %s,
                SyncRunID = %s,
                Activo = 1,
                SyncedAtMexico = SYSDATETIME(),
                FechaModificacion = SYSDATETIME()

        WHEN NOT MATCHED THEN
            INSERT (
                ProductoID,
                ServerID,
                ProductoCodigoFuente,
                ComponenteCodigoFuente,
                ComponenteNombre,
                TipoComponente,
                Cantidad,
                UnidadMedida,
                CostoUnitario,
                CostoTotal,
                EsElaborado,
                RendimientoElaborado,
                SystemType,
                SyncRunID,
                Activo
            )
            VALUES (
                NEWID(),
                source.ServerID,
                source.ProductoCodigoFuente,
                source.ComponenteCodigoFuente,
                %s,
                'INSUMO',
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                1
            );
        """

        for rec in recetas:
            params = (
                str(server_id),
                str(rec.producto_codigo_fuente),
                str(rec.insumo_codigo_fuente),

                str(rec.insumo_nombre),
                rec.cantidad,
                str(rec.unidad_medida),
                rec.costo_unitario,
                rec.costo_total,
                1 if rec.es_elaborado else 0,
                rec.rendimiento_elaborado,
                str(system_type),
                str(sync_run_id),

                str(rec.insumo_nombre),
                rec.cantidad,
                str(rec.unidad_medida),
                rec.costo_unitario,
                rec.costo_total,
                1 if rec.es_elaborado else 0,
                rec.rendimiento_elaborado,
                str(system_type),
                str(sync_run_id),
            )

            cursor.execute(
                merge_sql,
                params,
            )

            processed += 1

        # Una línea que sigue vigente recibió el SyncRunID actual.
        # Solo después de completar todos los UPSERT se inactivan
        # las líneas antiguas del mismo servidor no vistas en este run.
        cursor.execute(
            """
            UPDATE dbo.Sync_Productos_Recetas
            SET
                Activo = 0,
                FechaModificacion = SYSDATETIME()
            WHERE ServerID = CAST(%s AS UNIQUEIDENTIFIER)
              AND Activo = 1
              AND (
                    SyncRunID IS NULL
                    OR SyncRunID <> %s
                  );
            """,
            (
                str(server_id),
                str(sync_run_id),
            ),
        )

        # Recalcular la verdad actual de receta para TODOS los productos
        # del servidor, incluyendo los que ahora tienen cero componentes.
        cursor.execute(
            """
            UPDATE p
            SET
                TieneReceta =
                    CASE
                        WHEN ISNULL(r.ComponentesActivos, 0) > 0
                        THEN 1
                        ELSE 0
                    END,
                CantidadComponentesReceta =
                    ISNULL(r.ComponentesActivos, 0),
                FechaModificacion = SYSDATETIME()
            FROM dbo.Sync_Productos p
            OUTER APPLY (
                SELECT
                    COUNT(*) AS ComponentesActivos
                FROM dbo.Sync_Productos_Recetas rr
                WHERE rr.ServerID = p.ServerID
                  AND rr.ProductoCodigoFuente = p.CodigoFuente
                  AND rr.Activo = 1
            ) r
            WHERE p.ServerID = CAST(%s AS UNIQUEIDENTIFIER);
            """,
            (
                str(server_id),
            ),
        )

        conn.commit()

        result["insertados"] += processed

    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass

        result["errores_count"] += 1

        if len(result["errores"]) < 10:
            result["errores"].append(
                "Error transaccional recetas "
                f"ServerID={server_id}: {str(exc)[:160]}"
            )

        raise

    finally:
        conn.close()






def _sql_text(value):
    if value is None:
        return 'NULL'
    return "N'" + str(value).replace("'", "''") + "'"


def _guardar_compuestos(server_id: str, system_type: str, compuestos: List[Dict],
                        sync_run_id: str, result: Dict) -> None:
    """Guarda productos compuestos en EDARSAHUB SQL sin duplicar fuentes."""
    productos_actualizados = set()

    for comp in compuestos:
        try:
            producto = str(comp.get('producto_codigo_fuente') or '').replace("'", "''")
            componente = str(comp.get('componente_codigo_fuente') or '').replace("'", "''")
            nombre = str(comp.get('componente_nombre') or componente).replace("'", "''")
            fuente = str(comp.get('fuente_detalle') or 'ORIGEN').replace("'", "''")
            unidad = str(comp.get('unidad_medida') or 'UN').replace("'", "''")
            grupo = comp.get('grupo_codigo_fuente')
            empresa = comp.get('empresa_codigo_fuente')
            cantidad = Decimal(str(comp.get('cantidad') or 1))
            costo_unitario = Decimal(str(comp.get('costo_unitario') or 0))
            costo_total = Decimal(str(comp.get('costo_total') or 0))

            if not producto or not componente:
                continue

            query = f"""
            MERGE Sync_Productos_Compuestos AS target
            USING (
                SELECT
                    CAST('{server_id}' AS UNIQUEIDENTIFIER) AS ServerID,
                    '{producto}' AS ProductoCodigoFuente,
                    '{componente}' AS ComponenteCodigoFuente,
                    '{fuente}' AS FuenteDetalle
            ) AS source
            ON target.ServerID = source.ServerID
               AND target.ProductoCodigoFuente = source.ProductoCodigoFuente
               AND target.ComponenteCodigoFuente = source.ComponenteCodigoFuente
               AND target.FuenteDetalle = source.FuenteDetalle
            WHEN MATCHED THEN
                UPDATE SET
                    ComponenteNombre = N'{nombre}',
                    Cantidad = {cantidad},
                    UnidadMedida = '{unidad}',
                    CostoUnitario = {costo_unitario},
                    CostoTotal = {costo_total},
                    GrupoCodigoFuente = {_sql_text(grupo)},
                    EmpresaCodigoFuente = {_sql_text(empresa)},
                    SystemType = '{system_type}',
                    Activo = 1,
                    SyncRunID = '{sync_run_id}',
                    SyncedAtMexico = SYSDATETIME(),
                    FechaModificacion = SYSDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (
                    CompuestoDetalleID, ServerID, SystemType,
                    ProductoCodigoFuente, ComponenteCodigoFuente, ComponenteNombre,
                    FuenteDetalle, Cantidad, UnidadMedida,
                    CostoUnitario, CostoTotal, GrupoCodigoFuente, EmpresaCodigoFuente,
                    Activo, SyncRunID, SyncedAtMexico
                )
                VALUES (
                    NEWID(), CAST('{server_id}' AS UNIQUEIDENTIFIER), '{system_type}',
                    '{producto}', '{componente}', N'{nombre}',
                    '{fuente}', {cantidad}, '{unidad}',
                    {costo_unitario}, {costo_total}, {_sql_text(grupo)}, {_sql_text(empresa)},
                    1, '{sync_run_id}', SYSDATETIME()
                );
            """
            execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                query
            )
            result['insertados'] += 1
            productos_actualizados.add(producto)

        except Exception as e:
            result['errores_count'] += 1
            if len(result['errores']) < 10:
                result['errores'].append(f"Error compuesto {comp.get('producto_codigo_fuente')}: {str(e)[:80]}")

    for prod_codigo in productos_actualizados:
        try:
            update_query = f"""
            UPDATE Sync_Productos
            SET EsCompuesto = 1,
                CantidadComponentesReceta = (
                    SELECT COUNT(*)
                    FROM Sync_Productos_Compuestos
                    WHERE ServerID = CAST('{server_id}' AS UNIQUEIDENTIFIER)
                      AND ProductoCodigoFuente = '{prod_codigo}'
                      AND Activo = 1
                ),
                FechaModificacion = SYSDATETIME()
            WHERE ServerID = CAST('{server_id}' AS UNIQUEIDENTIFIER)
              AND CodigoFuente = '{prod_codigo}'
            """
            execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                update_query
            )
        except Exception:
            pass

def _guardar_elaborados(server_id: str, system_type: str, elaborados: List[ElaboradoLineaSync],
                        sync_run_id: str, result: Dict) -> None:
    """Guarda líneas de elaborados (sub-recetas) en EDARSAHUB SQL."""
    for elab in elaborados:
        try:
            nombre_escaped = elab.insumo_componente_nombre.replace("'", "''")
            
            query = f"""
            MERGE Sync_Productos_Elaborados AS target
            USING (SELECT '{server_id}' as ServerID, 
                          '{elab.insumo_elaborado_codigo_fuente}' as InsumoElaboradoCodigoFuente,
                          '{elab.insumo_componente_codigo_fuente}' as ComponenteCodigoFuente) AS source
            ON target.ServerID = CAST(source.ServerID AS UNIQUEIDENTIFIER) 
               AND target.InsumoElaboradoCodigoFuente = source.InsumoElaboradoCodigoFuente
               AND target.ComponenteCodigoFuente = source.ComponenteCodigoFuente
            WHEN MATCHED THEN
                UPDATE SET 
                    ComponenteNombre = N'{nombre_escaped}',
                    Cantidad = {elab.cantidad},
                    UnidadMedida = '{elab.unidad_medida}',
                    CostoUnitario = {elab.costo_unitario},
                    CostoTotal = {elab.costo_total},
                    SystemType = '{system_type}',
                    SyncRunID = '{sync_run_id}',
                    SyncedAtMexico = SYSDATETIME(),
                    FechaModificacion = SYSDATETIME()
            WHEN NOT MATCHED THEN
                INSERT (InsumoElaboradoID, ServerID, InsumoElaboradoCodigoFuente, ComponenteCodigoFuente,
                        ComponenteNombre, Cantidad, UnidadMedida, CostoUnitario, CostoTotal,
                        SystemType, SyncRunID, Activo)
                VALUES (
                    NEWID(),
                    CAST('{server_id}' AS UNIQUEIDENTIFIER),
                    '{elab.insumo_elaborado_codigo_fuente}',
                    '{elab.insumo_componente_codigo_fuente}',
                    N'{nombre_escaped}',
                    {elab.cantidad}, '{elab.unidad_medida}',
                    {elab.costo_unitario}, {elab.costo_total},
                    '{system_type}',
                    '{sync_run_id}',
                    1
                );
            """
            execute_sql_query(
                EDARSAHUB_CONFIG['host'],
                EDARSAHUB_CONFIG['port'],
                EDARSAHUB_CONFIG['database'],
                EDARSAHUB_CONFIG['username'],
                EDARSAHUB_CONFIG['password'],
                query
            )
            result['insertados'] += 1
        except Exception as e:
            result['errores_count'] += 1
            if len(result['errores']) < 10:
                result['errores'].append(f"Error elaborado {elab.insumo_elaborado_codigo_fuente}: {str(e)[:80]}")


def _registrar_ejecucion(result: SyncRecetasResult) -> None:
    """Registra la ejecución en Sync_Control_Ejecuciones."""
    try:
        query = f"""
        INSERT INTO Sync_Control_Ejecuciones (
            SyncRunID, SyncType, FechaInicio, FechaFin, IsDryRun, Status,
            RegistrosProcesados, RegistrosInsertados, RegistrosActualizados, RegistrosError,
            StartedAtMexico, FinishedAtMexico, DurationSeconds, CreatedAt,
            StartedAtUTC, FinishedAtUTC, IdempotencyKey
        ) VALUES (
            '{result.sync_run_id}',
            'SYNC_RECETAS',
            '{result.started_at.strftime("%Y-%m-%d %H:%M:%S")}',
            '{result.finished_at.strftime("%Y-%m-%d %H:%M:%S")}',
            {1 if result.is_dry_run else 0},
            '{'SUCCESS' if result.success else 'PARTIAL'}',
            {result.total_productos + result.total_insumos + result.total_lineas_receta},
            {result.registros_insertados},
            {result.registros_actualizados},
            {result.registros_error},
            '{result.started_at.strftime("%Y-%m-%d %H:%M:%S")}',
            '{result.finished_at.strftime("%Y-%m-%d %H:%M:%S")}',
            {result.duration_seconds},
            '{result.started_at.strftime("%Y-%m-%d %H:%M:%S")}',
            SYSUTCDATETIME(),
            SYSUTCDATETIME(),
            'SYNC_RECETAS:{result.sync_run_id}'
        )
        """
        execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
    except Exception as e:
        result.warnings.append(f"No se pudo registrar ejecución: {str(e)[:100]}")
