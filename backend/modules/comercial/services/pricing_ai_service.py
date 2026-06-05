"""
FASE 1C-3I-C: Servicio de Integración GPT-5.2 para Pricing y Benchmark

Este módulo integra GPT-5.2 (OpenAI) para:
- Analizar productos y generar justificaciones de precios
- Sugerir productos comparables con competidores
- Generar análisis de benchmark competitivo
- Clasificar confianza de análisis (ALTA/MEDIA/BAJA)

REGLAS CRÍTICAS:
- GPT-5.2 sugiere, NO autoriza ni aplica precios
- NO modificar precios oficiales
- NO crear solicitudes automáticas
- NO hacer scraping web
- NO usar MongoDB (todo en EDARSAHUB SQL)
- NO exponer API keys en logs/frontend

PROVEEDOR IA:
- OpenAI GPT-5.2 via Emergent LLM Key
"""

from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
from enum import Enum
import logging
import uuid
import json
import os

from dotenv import load_dotenv
load_dotenv()

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG

# Importar servicios relacionados
from .perfil_unidad_service import obtener_perfil_por_unidad
from .competidores_service import (
    listar_competidores,
    listar_menu_items,
    obtener_estadisticas_competidores,
    obtener_estadisticas_menu_items,
)
from .benchmark_service import (
    obtener_benchmarks_producto,
    obtener_precios_competencia_producto,
)
from .pricing_sugerido_service import calcular_precio_sugerido_base
from .pricing_schemas import (
    TipoMotorPrecio,
    PrecioSugeridoCalcularRequest,
    ConfianzaDato,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class TipoAnalisisIA(str, Enum):
    """Tipos de análisis IA disponibles."""
    ANALISIS_PRODUCTO = "ANALISIS_PRODUCTO"
    SUGERENCIA_COMPARABLES = "SUGERENCIA_COMPARABLES"
    JUSTIFICACION_PRECIO = "JUSTIFICACION_PRECIO"
    ANALISIS_BENCHMARK = "ANALISIS_BENCHMARK"


class EstadoAnalisisIA(str, Enum):
    """Estados del análisis IA."""
    GENERADO = "GENERADO"
    ERROR = "ERROR"
    DATOS_INSUFICIENTES = "DATOS_INSUFICIENTES"
    REQUIERE_REVISION = "REQUIERE_REVISION"
    VALIDADO = "VALIDADO"
    DESCARTADO = "DESCARTADO"


class ConfianzaIA(str, Enum):
    """Niveles de confianza del análisis IA."""
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

def _get_conn() -> Tuple:
    """Retorna parámetros de conexión a EDARSAHUB."""
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )


def _get_llm_key() -> str:
    """Obtiene la EMERGENT_LLM_KEY de forma segura."""
    key = os.environ.get('EMERGENT_LLM_KEY', '')
    if not key:
        raise ValueError("EMERGENT_LLM_KEY no configurada en .env")
    return key


def _ensure_tabla_analisis_existe():
    """
    Verifica y crea la tabla Comercial_PricingAnalisisIA si no existe.
    """
    conn = _get_conn()
    
    # DDL idempotente
    ddl = """
    IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_PricingAnalisisIA')
    BEGIN
        CREATE TABLE Comercial_PricingAnalisisIA (
            AnalisisIAID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            ProductoID UNIQUEIDENTIFIER NULL,
            CodigoProducto NVARCHAR(100) NOT NULL,
            ServerID UNIQUEIDENTIFIER NULL,
            EmpresaID INT NOT NULL,
            UnidadNegocioID INT NOT NULL,
            TipoAnalisis VARCHAR(50) NOT NULL,
            ModeloIAUsado VARCHAR(50) NOT NULL,
            VersionModelo VARCHAR(50) NOT NULL,
            PromptResumen NVARCHAR(1000) NULL,
            DatosEntradaJSON NVARCHAR(MAX) NULL,
            RespuestaIAJSON NVARCHAR(MAX) NULL,
            JustificacionIA NVARCHAR(MAX) NULL,
            ConfianzaIA VARCHAR(20) NOT NULL,
            RequiereRevisionHumana BIT DEFAULT 0,
            PrecioActual DECIMAL(18,2) NULL,
            PrecioSugerido DECIMAL(18,2) NULL,
            MargenActual DECIMAL(8,4) NULL,
            MargenSugerido DECIMAL(8,4) NULL,
            CompetidoresUsadosJSON NVARCHAR(MAX) NULL,
            FuentesUsadasJSON NVARCHAR(MAX) NULL,
            EstadoAnalisis VARCHAR(30) NOT NULL,
            UsuarioEjecucion NVARCHAR(100) NOT NULL,
            FechaEjecucion DATETIME2 NOT NULL DEFAULT GETDATE(),
            FechaCreacion DATETIME2 NOT NULL DEFAULT GETDATE()
        );
    END
    """
    
    try:
        execute_sql_query(*conn, ddl)
        logger.info("[PRICING-IA] Tabla Comercial_PricingAnalisisIA verificada/creada")
    except Exception as e:
        logger.warning(f"[PRICING-IA] No se pudo verificar/crear tabla: {e}")


# =============================================================================
# HELPER: Obtener datos del producto desde SQL
# =============================================================================

def _obtener_datos_producto(codigo_producto: str, server_id: str) -> Dict[str, Any]:
    """
    Obtiene todos los datos disponibles de un producto desde EDARSAHUB SQL.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        sp.Nombre,
        sp.FamiliaNombre,
        sp.SubfamiliaNombre,
        sp.CostoReceta,
        sp.CostoEstandar,
        sp.PrecioVenta,
        spi.Costo as CostoInsumo,
        spi.UltimoCosto,
        spi.CostoPromedio
    FROM Sync_Productos sp
    LEFT JOIN Sync_Productos_Insumos spi 
        ON sp.ServerID = spi.ServerID AND sp.CodigoFuente = spi.CodigoFuente
    WHERE CAST(sp.ServerID AS NVARCHAR(36)) = '{server_id}'
      AND sp.CodigoFuente = '{codigo_producto}'
    """
    
    result = execute_sql_query(*conn, query)
    
    if not result or len(result) == 0:
        return {'existe': False}
    
    row = result[0]
    
    # Determinar el mejor costo disponible
    costo = None
    fuente_costo = None
    
    if row.get('CostoReceta') and float(row['CostoReceta']) > 0:
        costo = float(row['CostoReceta'])
        fuente_costo = 'CostoReceta'
    elif row.get('CostoInsumo') and float(row['CostoInsumo']) > 0:
        costo = float(row['CostoInsumo'])
        fuente_costo = 'CostoInsumo'
    elif row.get('UltimoCosto') and float(row['UltimoCosto']) > 0:
        costo = float(row['UltimoCosto'])
        fuente_costo = 'UltimoCosto'
    elif row.get('CostoPromedio') and float(row['CostoPromedio']) > 0:
        costo = float(row['CostoPromedio'])
        fuente_costo = 'CostoPromedio'
    
    precio_actual = float(row['PrecioVenta']) if row.get('PrecioVenta') else None
    
    return {
        'existe': True,
        'codigo': codigo_producto,
        'nombre': row.get('Nombre', 'Sin nombre'),
        'familia': row.get('FamiliaNombre'),
        'subfamilia': row.get('SubfamiliaNombre'),
        'costo': costo,
        'fuente_costo': fuente_costo,
        'precio_actual': precio_actual,
        'margen_actual': round((1 - costo / precio_actual) * 100, 2) if costo and precio_actual and precio_actual > 0 else None,
    }


def _obtener_contexto_unidad(unidad_negocio_id: int) -> Dict[str, Any]:
    """
    Obtiene el contexto de la unidad de negocio para el análisis IA.
    """
    perfil = obtener_perfil_por_unidad(unidad_negocio_id)
    
    if not perfil:
        return {'existe': False}
    
    return {
        'existe': True,
        'nombre_comercial': perfil.nombre_comercial,
        'concepto': perfil.concepto_restaurante,
        'tipo_restaurante': perfil.tipo_restaurante,
        'segmento_precio': perfil.segmento_precio,
        'ciudad': perfil.ciudad,
        'estado': perfil.estado,
        'ticket_promedio_objetivo': perfil.ticket_promedio_objetivo,
        'rango_precio_objetivo': perfil.rango_precio_objetivo,
    }


def _obtener_competidores_para_contexto(
    unidad_negocio_id: int, 
    limit: int = 5,
    lista_id: str = None
) -> List[Dict]:
    """
    Obtiene competidores y sus menu items para contexto IA.
    
    Si lista_id está definido, solo retorna competidores de esa lista.
    """
    from modules.comercial.services.listas_competidores_service import (
        obtener_ids_competidores_de_lista,
        obtener_lista_competidores
    )
    
    # Obtener competidores de la lista si se especifica
    ids_filtrar = None
    lista_info = None
    
    if lista_id:
        lista_info = obtener_lista_competidores(lista_id)
        if not lista_info or not lista_info.get('activo'):
            logger.warning(f"[PRICING-IA] Lista {lista_id} no existe o inactiva")
            return []
        
        ids_filtrar = obtener_ids_competidores_de_lista(lista_id)
        if not ids_filtrar:
            logger.warning(f"[PRICING-IA] Lista {lista_id} sin competidores activos")
            return []
        
        logger.info(f"[PRICING-IA] Filtrando por lista '{lista_info.get('nombre_lista')}' ({len(ids_filtrar)} competidores)")
    
    # Obtener competidores
    competidores, _ = listar_competidores(
        unidad_negocio_id=unidad_negocio_id,
        page=1,
        page_size=100  # Obtener más para luego filtrar
    )
    
    # Filtrar por lista si aplica (comparación case-insensitive para UUIDs)
    if ids_filtrar:
        ids_filtrar_lower = [id.lower() for id in ids_filtrar]
        competidores = [c for c in competidores if str(c.competidor_id).lower() in ids_filtrar_lower]
    
    # Limitar
    competidores = competidores[:limit]
    
    resultado = []
    for comp in competidores:
        items, _ = listar_menu_items(comp.competidor_id, page=1, page_size=20)
        
        resultado.append({
            'nombre': comp.nombre_competidor,
            'tipo': comp.tipo_restaurante,
            'segmento': comp.segmento_precio,
            'es_directo': comp.es_competencia_directa,
            'es_aspiracional': comp.es_benchmark_aspiracional,
            'items': [
                {
                    'producto': item.nombre_producto_competidor,
                    'categoria': item.categoria_competidor,
                    'precio': item.precio,
                    'confianza': item.confianza_dato,
                }
                for item in items
            ]
        })
    
    return resultado


# =============================================================================
# HELPER: Determinar confianza del análisis
# =============================================================================

def _calcular_confianza_analisis(
    tiene_costo: bool,
    tiene_precio_actual: bool,
    tiene_benchmark: bool,
    num_comparables: int,
    benchmarks_validados: int
) -> ConfianzaIA:
    """
    Determina el nivel de confianza del análisis IA.
    
    ALTA: Costo confiable, precio actual, benchmark comparable, datos validados
    MEDIA: Costo e impuesto, pero benchmark parcial o comparables no perfectos
    BAJA: Faltan datos, comparables débiles o inferencia parcial
    """
    puntos = 0
    
    if tiene_costo:
        puntos += 2
    if tiene_precio_actual:
        puntos += 1
    if tiene_benchmark:
        puntos += 2
    if num_comparables >= 3:
        puntos += 1
    elif num_comparables >= 1:
        puntos += 0.5
    if benchmarks_validados >= 1:
        puntos += 1
    
    if puntos >= 5:
        return ConfianzaIA.ALTA
    elif puntos >= 3:
        return ConfianzaIA.MEDIA
    else:
        return ConfianzaIA.BAJA


# =============================================================================
# HELPER: Guardar análisis en SQL
# =============================================================================

def _guardar_analisis_ia(
    producto_id: Optional[str],
    codigo_producto: str,
    server_id: str,
    empresa_id: int,
    unidad_negocio_id: int,
    tipo_analisis: TipoAnalisisIA,
    modelo_ia: str,
    version_modelo: str,
    prompt_resumen: str,
    datos_entrada_json: Dict,
    respuesta_ia_json: Dict,
    justificacion_ia: str,
    confianza_ia: ConfianzaIA,
    requiere_revision: bool,
    precio_actual: Optional[float],
    precio_sugerido: Optional[float],
    margen_actual: Optional[float],
    margen_sugerido: Optional[float],
    competidores_usados: List[str],
    fuentes_usadas: List[str],
    estado: EstadoAnalisisIA,
    usuario: str,
    lista_id: Optional[str] = None
) -> str:
    """
    Guarda el análisis IA en la tabla Comercial_PricingAnalisisIA.
    
    Args:
        lista_id: ID de lista de competidores usada para filtrar (opcional)
    
    Returns:
        ID del análisis creado
    """
    # Asegurar que la tabla existe
    _ensure_tabla_analisis_existe()
    
    conn = _get_conn()
    
    analisis_id = str(uuid.uuid4())
    
    # Preparar valores SQL
    producto_id_sql = f"'{producto_id}'" if producto_id else "NULL"
    precio_actual_sql = f"{precio_actual}" if precio_actual else "NULL"
    precio_sugerido_sql = f"{precio_sugerido}" if precio_sugerido else "NULL"
    margen_actual_sql = f"{margen_actual}" if margen_actual else "NULL"
    margen_sugerido_sql = f"{margen_sugerido}" if margen_sugerido else "NULL"
    lista_id_sql = f"'{lista_id}'" if lista_id else "NULL"
    
    # Escapar JSON para SQL
    datos_entrada_str = json.dumps(datos_entrada_json, ensure_ascii=False).replace("'", "''")
    respuesta_ia_str = json.dumps(respuesta_ia_json, ensure_ascii=False).replace("'", "''")
    justificacion_str = justificacion_ia.replace("'", "''") if justificacion_ia else ''
    prompt_str = prompt_resumen.replace("'", "''") if prompt_resumen else ''
    competidores_str = json.dumps(competidores_usados, ensure_ascii=False).replace("'", "''")
    fuentes_str = json.dumps(fuentes_usadas, ensure_ascii=False).replace("'", "''")
    
    insert_query = f"""
    INSERT INTO Comercial_PricingAnalisisIA (
        AnalisisIAID,
        ProductoID,
        CodigoProducto,
        ServerID,
        EmpresaID,
        UnidadNegocioID,
        TipoAnalisis,
        ModeloIAUsado,
        VersionModelo,
        PromptResumen,
        DatosEntradaJSON,
        RespuestaIAJSON,
        JustificacionIA,
        ConfianzaIA,
        RequiereRevisionHumana,
        PrecioActual,
        PrecioSugerido,
        MargenActual,
        MargenSugerido,
        CompetidoresUsadosJSON,
        FuentesUsadasJSON,
        EstadoAnalisis,
        UsuarioEjecucion,
        ListaCompetidoresID,
        FechaEjecucion,
        FechaCreacion
    ) VALUES (
        '{analisis_id}',
        {producto_id_sql},
        '{codigo_producto}',
        '{ServerID}',
        {EmpresaID},
        {UnidadNegocioID},
        '{tipo_analisis.value}',
        '{modelo_ia}',
        '{version_modelo}',
        N'{prompt_str}',
        N'{datos_entrada_str}',
        N'{respuesta_ia_str}',
        N'{justificacion_str}',
        '{confianza_ia.value}',
        {1 if requiere_revision else 0},
        {precio_actual_sql},
        {precio_sugerido_sql},
        {margen_actual_sql},
        {margen_sugerido_sql},
        N'{competidores_str}',
        N'{fuentes_str}',
        '{estado.value}',
        N'{usuario}',
        {lista_id_sql},
        GETDATE(),
        GETDATE()
    )
    """
    
    try:
        execute_sql_query(*conn, insert_query)
        logger.info(f"[PRICING-IA] Análisis guardado: {analisis_id} tipo={tipo_analisis.value} lista={lista_id}")
    except Exception as e:
        logger.error(f"[PRICING-IA] Error guardando análisis: {e}")
        # Re-raise para que el llamador sepa que falló
        raise
    
    return analisis_id


def obtener_analisis_ia(analisis_id: str) -> Optional[Dict]:
    """
    Obtiene un análisis IA por su ID.
    """
    conn = _get_conn()
    
    query = f"""
    SELECT 
        CAST(AnalisisIAID AS NVARCHAR(36)) as AnalisisIAID,
        CAST(ProductoID AS NVARCHAR(36)) as ProductoID,
        CodigoProducto,
        CAST(ServerID AS NVARCHAR(36)) as ServerID,
        EmpresaID,
        UnidadNegocioID,
        TipoAnalisis,
        ModeloIAUsado,
        VersionModelo,
        PromptResumen,
        DatosEntradaJSON,
        RespuestaIAJSON,
        JustificacionIA,
        ConfianzaIA,
        RequiereRevisionHumana,
        PrecioActual,
        PrecioSugerido,
        MargenActual,
        MargenSugerido,
        CompetidoresUsadosJSON,
        FuentesUsadasJSON,
        EstadoAnalisis,
        UsuarioEjecucion,
        FechaEjecucion,
        FechaCreacion
    FROM Comercial_PricingAnalisisIA
    WHERE AnalisisIAID = '{analisis_id}'
    """
    
    result = execute_sql_query(*conn, query)
    
    if not result or len(result) == 0:
        return None
    
    row = result[0]
    
    # Parsear JSONs
    datos_entrada = None
    respuesta_ia = None
    competidores = None
    fuentes = None
    
    try:
        if row.get('DatosEntradaJSON'):
            datos_entrada = json.loads(row['DatosEntradaJSON'])
    except (json.JSONDecodeError, TypeError):
        pass
    
    try:
        if row.get('RespuestaIAJSON'):
            respuesta_ia = json.loads(row['RespuestaIAJSON'])
    except (json.JSONDecodeError, TypeError):
        pass
    
    try:
        if row.get('CompetidoresUsadosJSON'):
            competidores = json.loads(row['CompetidoresUsadosJSON'])
    except (json.JSONDecodeError, TypeError):
        pass
    
    try:
        if row.get('FuentesUsadasJSON'):
            fuentes = json.loads(row['FuentesUsadasJSON'])
    except (json.JSONDecodeError, TypeError):
        pass
    
    return {
        'analisis_id': row.get('AnalisisIAID'),
        'producto_id': row.get('ProductoID'),
        'codigo_producto': row.get('CodigoProducto'),
        'server_id': row.get('ServerID'),
        'empresa_id': row.get('EmpresaID'),
        'unidad_negocio_id': row.get('UnidadNegocioID'),
        'tipo_analisis': row.get('TipoAnalisis'),
        'modelo_ia': row.get('ModeloIAUsado'),
        'version_modelo': row.get('VersionModelo'),
        'prompt_resumen': row.get('PromptResumen'),
        'datos_entrada': datos_entrada,
        'respuesta_ia': respuesta_ia,
        'justificacion_ia': row.get('JustificacionIA'),
        'confianza_ia': row.get('ConfianzaIA'),
        'requiere_revision_humana': bool(row.get('RequiereRevisionHumana')),
        'precio_actual': float(row['PrecioActual']) if row.get('PrecioActual') else None,
        'precio_sugerido': float(row['PrecioSugerido']) if row.get('PrecioSugerido') else None,
        'margen_actual': float(row['MargenActual']) if row.get('MargenActual') else None,
        'margen_sugerido': float(row['MargenSugerido']) if row.get('MargenSugerido') else None,
        'competidores_usados': competidores,
        'fuentes_usadas': fuentes,
        'estado': row.get('EstadoAnalisis'),
        'usuario_ejecucion': row.get('UsuarioEjecucion'),
        'fecha_ejecucion': row.get('FechaEjecucion'),
        'fecha_creacion': row.get('FechaCreacion'),
    }


# =============================================================================
# FUNCIONES PRINCIPALES DE ANÁLISIS IA
# =============================================================================

async def analizar_producto_con_ia(
    codigo_producto: str,
    server_id: str,
    empresa_id: int,
    unidad_negocio_id: int,
    usuario: str,
    margen_objetivo: float = 0.35,
    lista_id: str = None
) -> Dict[str, Any]:
    """
    Analiza un producto usando GPT-5.2 y genera justificación de precio.
    
    NO modifica precios oficiales.
    NO crea solicitudes automáticas.
    
    Args:
        lista_id: ID de lista de competidores para filtrar benchmark (opcional)
    
    Returns:
        Dict con análisis, justificación, precio sugerido y confianza
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from modules.comercial.services.listas_competidores_service import obtener_lista_competidores
    
    # Validar lista si se especifica
    lista_usada = None
    if lista_id:
        lista_info = obtener_lista_competidores(lista_id)
        if not lista_info:
            return {
                'success': False,
                'estado': EstadoAnalisisIA.ERROR.value,
                'mensaje': f'Lista de competidores {lista_id} no encontrada',
                'analisis_id': None,
            }
        if not lista_info.get('activo'):
            return {
                'success': False,
                'estado': EstadoAnalisisIA.ERROR.value,
                'mensaje': f'Lista de competidores "{lista_info.get("nombre_lista")}" está inactiva',
                'analisis_id': None,
            }
        if lista_info.get('total_competidores', 0) == 0:
            return {
                'success': False,
                'estado': EstadoAnalisisIA.DATOS_INSUFICIENTES.value,
                'mensaje': f'Lista "{lista_info.get("nombre_lista")}" no tiene competidores activos',
                'analisis_id': None,
            }
        lista_usada = {
            'lista_id': lista_id,
            'nombre_lista': lista_info.get('nombre_lista'),
            'total_competidores': lista_info.get('total_competidores')
        }
    
    # 1. Obtener datos del producto
    datos_producto = _obtener_datos_producto(codigo_producto, server_id)
    
    if not datos_producto.get('existe'):
        return {
            'success': False,
            'estado': EstadoAnalisisIA.DATOS_INSUFICIENTES.value,
            'mensaje': f'Producto {codigo_producto} no encontrado en EDARSAHUB SQL',
            'analisis_id': None,
        }
    
    # 2. Obtener contexto de la unidad
    contexto_unidad = _obtener_contexto_unidad(unidad_negocio_id)
    
    # 3. Obtener competidores y benchmark (filtrando por lista si aplica)
    competidores = _obtener_competidores_para_contexto(unidad_negocio_id, limit=5, lista_id=lista_id)
    benchmark = obtener_precios_competencia_producto(codigo_producto, server_id)
    
    # 4. Calcular precio base matemático
    request_precio = PrecioSugeridoCalcularRequest(
        codigo_producto=codigo_producto,
        server_id=server_id,
        tipo_motor=TipoMotorPrecio.COSTO_MARGEN,
        margen_objetivo=margen_objetivo,
    )
    precio_base = calcular_precio_sugerido_base(request_precio)
    
    # 5. Calcular confianza
    confianza = _calcular_confianza_analisis(
        tiene_costo=datos_producto.get('costo') is not None,
        tiene_precio_actual=datos_producto.get('precio_actual') is not None,
        tiene_benchmark=benchmark.get('tiene_datos', False),
        num_comparables=benchmark.get('total_comparables', 0) if benchmark.get('tiene_datos') else 0,
        benchmarks_validados=0  # Habría que contar validados
    )
    
    # 6. Preparar datos de entrada para IA
    datos_entrada = {
        'producto': datos_producto,
        'unidad': contexto_unidad,
        'competidores': competidores,
        'benchmark': benchmark if benchmark.get('tiene_datos') else None,
        'precio_base_calculado': {
            'precio_sugerido': precio_base.precio_sugerido,
            'margen_objetivo': margen_objetivo,
            'estado': precio_base.estado.value,
        },
        'confianza_calculada': confianza.value,
        'lista_usada': lista_usada,
    }
    
    # 7. Construir prompt para GPT-5.2
    # Preparar valores para el prompt
    costo_str = f"${datos_producto.get('costo', 0):.2f}" if datos_producto.get('costo') else "No configurado"
    precio_actual_str = f"${datos_producto.get('precio_actual'):.2f}" if datos_producto.get('precio_actual') else "No configurado"
    margen_actual_str = f"{datos_producto.get('margen_actual'):.1f}%" if datos_producto.get('margen_actual') else "N/A"
    ticket_objetivo_str = f"${contexto_unidad.get('ticket_promedio_objetivo'):.2f}" if contexto_unidad.get('ticket_promedio_objetivo') else "N/A"
    precio_sugerido_str = f"${precio_base.precio_sugerido:.2f}" if precio_base.precio_sugerido else "No calculado"
    
    # Benchmark strings
    benchmark_min_str = f"- Precio Mínimo Competencia: ${benchmark.get('precio_minimo', 0):.2f}" if benchmark.get('tiene_datos') else "- Sin datos de competencia disponibles"
    benchmark_prom_str = f"- Precio Promedio Competencia: ${benchmark.get('precio_promedio', 0):.2f}" if benchmark.get('tiene_datos') else ""
    benchmark_max_str = f"- Precio Máximo Competencia: ${benchmark.get('precio_maximo', 0):.2f}" if benchmark.get('tiene_datos') else ""
    benchmark_comp_str = f"- Comparables: {benchmark.get('total_comparables', 0)}" if benchmark.get('tiene_datos') else ""
    
    # Lista filtro string
    lista_str = f"(Filtrado por lista: {lista_usada.get('nombre_lista')} - {lista_usada.get('total_competidores')} competidores)" if lista_usada else "(Benchmark general)"
    
    # Competidores string
    if competidores:
        comp_lines = [f"- {c['nombre']} ({c['tipo']}, {c['segmento']}): {len(c['items'])} productos capturados" for c in competidores[:3]]
        competidores_str = chr(10).join(comp_lines) + chr(10) + lista_str
    else:
        competidores_str = "- Sin competidores configurados" + chr(10) + lista_str
    
    prompt = f"""Eres un analista de precios de restaurante experto. Analiza los siguientes datos y genera una justificación comercial para el precio sugerido.

PRODUCTO:
- Nombre: {datos_producto.get('nombre')}
- Código: {codigo_producto}
- Familia: {datos_producto.get('familia', 'No especificada')}
- Costo: {costo_str} (fuente: {datos_producto.get('fuente_costo', 'N/A')})
- Precio Actual: {precio_actual_str}
- Margen Actual: {margen_actual_str}

CONTEXTO DEL RESTAURANTE:
- Nombre: {contexto_unidad.get('nombre_comercial', 'No especificado')}
- Concepto: {contexto_unidad.get('concepto', 'No especificado')}
- Tipo: {contexto_unidad.get('tipo_restaurante', 'No especificado')}
- Segmento: {contexto_unidad.get('segmento_precio', 'No especificado')}
- Ciudad: {contexto_unidad.get('ciudad', 'No especificada')}
- Ticket Promedio Objetivo: {ticket_objetivo_str}

PRECIO BASE CALCULADO (matemático):
- Precio Sugerido: {precio_sugerido_str}
- Margen Objetivo: {margen_objetivo * 100:.0f}%
- Estado: {precio_base.estado.value}

BENCHMARK VS COMPETENCIA:
{benchmark_min_str}
{benchmark_prom_str}
{benchmark_max_str}
{benchmark_comp_str}

COMPETIDORES CONFIGURADOS:
{competidores_str}

CONFIANZA DATOS: {confianza.value}

Genera:
1. Una justificación comercial del precio sugerido (2-3 oraciones)
2. Un análisis de posicionamiento vs competencia (1-2 oraciones)
3. Una recomendación (aceptar el precio base, ajustar hacia arriba o hacia abajo, o requerir más datos)

Responde en formato JSON con esta estructura:
{{
  "justificacion": "texto de justificación comercial",
  "posicionamiento": "texto de análisis vs competencia",
  "recomendacion": "ACEPTAR_BASE | AJUSTAR_ARRIBA | AJUSTAR_ABAJO | REQUIERE_MAS_DATOS",
  "precio_ajustado_sugerido": numero o null,
  "observaciones": "cualquier observación adicional"
}}"""

    # 8. Llamar a GPT-5.2
    try:
        llm_key = _get_llm_key()
        
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"pricing-{codigo_producto}-{uuid.uuid4().hex[:8]}",
            system_message="Eres un analista de precios de restaurantes experto. Respondes siempre en JSON válido."
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=prompt)
        response_text = await chat.send_message(user_message)
        
        # Parsear respuesta JSON
        try:
            # Limpiar posibles caracteres extra
            response_clean = response_text.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.startswith('```'):
                response_clean = response_clean[3:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            respuesta_ia = json.loads(response_clean.strip())
        except json.JSONDecodeError:
            respuesta_ia = {
                'justificacion': response_text[:500],
                'posicionamiento': 'No disponible',
                'recomendacion': 'REQUIERE_MAS_DATOS',
                'precio_ajustado_sugerido': None,
                'observaciones': 'Respuesta no estructurada',
                'raw_response': response_text
            }
        
        # 9. Determinar si requiere revisión
        requiere_revision = (
            confianza == ConfianzaIA.BAJA or
            respuesta_ia.get('recomendacion') == 'REQUIERE_MAS_DATOS'
        )
        
        # 10. Calcular margen sugerido
        precio_sugerido_final = respuesta_ia.get('precio_ajustado_sugerido') or precio_base.precio_sugerido
        margen_sugerido = None
        if precio_sugerido_final and datos_producto.get('costo'):
            margen_sugerido = round((1 - datos_producto['costo'] / precio_sugerido_final) * 100, 2)
        
        # 11. Guardar análisis en SQL
        analisis_id = _guardar_analisis_ia(
            producto_id=None,  # No tenemos UUID del producto
            codigo_producto=codigo_producto,
            server_id=server_id,
            empresa_id=empresa_id,
            unidad_negocio_id=unidad_negocio_id,
            tipo_analisis=TipoAnalisisIA.ANALISIS_PRODUCTO,
            modelo_ia="openai",
            version_modelo="gpt-5.2",
            prompt_resumen=f"Análisis de producto {datos_producto.get('nombre', codigo_producto)}",
            datos_entrada_json=datos_entrada,
            respuesta_ia_json=respuesta_ia,
            justificacion_ia=respuesta_ia.get('justificacion', ''),
            confianza_ia=confianza,
            requiere_revision=requiere_revision,
            precio_actual=datos_producto.get('precio_actual'),
            precio_sugerido=precio_sugerido_final,
            margen_actual=datos_producto.get('margen_actual'),
            margen_sugerido=margen_sugerido,
            competidores_usados=[c['nombre'] for c in competidores],
            fuentes_usadas=['EDARSAHUB_SQL', 'Sync_Productos', 'Comercial_Competidores'],
            estado=EstadoAnalisisIA.GENERADO if not requiere_revision else EstadoAnalisisIA.REQUIERE_REVISION,
            usuario=usuario,
            lista_id=lista_id
        )
        
        return {
            'success': True,
            'analisis_id': analisis_id,
            'producto': {
                'codigo': codigo_producto,
                'nombre': datos_producto.get('nombre'),
                'familia': datos_producto.get('familia'),
            },
            'precio_actual': datos_producto.get('precio_actual'),
            'precio_base_calculado': precio_base.precio_sugerido,
            'precio_sugerido_ia': precio_sugerido_final,
            'margen_actual': datos_producto.get('margen_actual'),
            'margen_sugerido': margen_sugerido,
            'justificacion': respuesta_ia.get('justificacion'),
            'posicionamiento': respuesta_ia.get('posicionamiento'),
            'recomendacion': respuesta_ia.get('recomendacion'),
            'observaciones': respuesta_ia.get('observaciones'),
            'confianza': confianza.value,
            'requiere_revision': requiere_revision,
            'estado': EstadoAnalisisIA.GENERADO.value if not requiere_revision else EstadoAnalisisIA.REQUIERE_REVISION.value,
            'modelo_ia': 'gpt-5.2',
            'mensaje': 'Análisis completado. GPT-5.2 sugiere, NO autoriza ni aplica precios.',
            'lista_usada': lista_usada,
        }
        
    except Exception as e:
        logger.error(f"[PRICING-IA] Error en análisis: {e}")
        
        # Guardar error
        analisis_id = _guardar_analisis_ia(
            producto_id=None,
            codigo_producto=codigo_producto,
            server_id=server_id,
            empresa_id=empresa_id,
            unidad_negocio_id=unidad_negocio_id,
            tipo_analisis=TipoAnalisisIA.ANALISIS_PRODUCTO,
            modelo_ia="openai",
            version_modelo="gpt-5.2",
            prompt_resumen=f"ERROR: {str(e)[:200]}",
            datos_entrada_json=datos_entrada,
            respuesta_ia_json={'error': str(e)},
            justificacion_ia='',
            confianza_ia=ConfianzaIA.BAJA,
            requiere_revision=True,
            precio_actual=datos_producto.get('precio_actual'),
            precio_sugerido=precio_base.precio_sugerido,
            margen_actual=datos_producto.get('margen_actual'),
            margen_sugerido=None,
            competidores_usados=[],
            fuentes_usadas=['EDARSAHUB_SQL'],
            estado=EstadoAnalisisIA.ERROR,
            usuario=usuario,
            lista_id=lista_id
        )
        
        return {
            'success': False,
            'analisis_id': analisis_id,
            'estado': EstadoAnalisisIA.ERROR.value,
            'mensaje': f'Error en análisis IA: {str(e)}',
            'precio_base_calculado': precio_base.precio_sugerido,
        }


async def sugerir_comparables_con_ia(
    codigo_producto: str,
    server_id: str,
    empresa_id: int,
    unidad_negocio_id: int,
    usuario: str
) -> Dict[str, Any]:
    """
    Usa GPT-5.2 para sugerir productos comparables de la competencia.
    
    Solo analiza datos ya capturados en EDARSAHUB SQL.
    NO hace scraping web.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    # 1. Obtener datos del producto
    datos_producto = _obtener_datos_producto(codigo_producto, server_id)
    
    if not datos_producto.get('existe'):
        return {
            'success': False,
            'estado': EstadoAnalisisIA.DATOS_INSUFICIENTES.value,
            'mensaje': f'Producto {codigo_producto} no encontrado',
        }
    
    # 2. Obtener todos los items de competidores
    competidores = _obtener_competidores_para_contexto(unidad_negocio_id, limit=10)
    
    todos_items = []
    for comp in competidores:
        for item in comp['items']:
            todos_items.append({
                'competidor': comp['nombre'],
                'producto': item['producto'],
                'categoria': item['categoria'],
                'precio': item['precio'],
            })
    
    if not todos_items:
        return {
            'success': False,
            'estado': EstadoAnalisisIA.DATOS_INSUFICIENTES.value,
            'mensaje': 'No hay items de competencia capturados para comparar',
        }
    
    # 3. Construir prompt
    items_texto = "\n".join([
        f"- [{i['competidor']}] {i['producto']} ({i['categoria'] or 'Sin categoría'}): ${i['precio']:.2f}"
        for i in todos_items[:50]  # Limitar a 50 items
    ])
    
    prompt = f"""Analiza los siguientes productos de la competencia y sugiere cuáles son comparables con nuestro producto.

NUESTRO PRODUCTO:
- Nombre: {datos_producto.get('nombre')}
- Código: {codigo_producto}
- Familia: {datos_producto.get('familia', 'No especificada')}
- Precio Actual: ${datos_producto.get('precio_actual', 0):.2f if datos_producto.get('precio_actual') else 'No configurado'}

PRODUCTOS DE COMPETENCIA DISPONIBLES:
{items_texto}

Identifica los productos más comparables considerando:
1. Similitud de nombre/tipo de producto
2. Misma categoría o categoría similar
3. Rango de precio razonable

Responde en JSON con esta estructura:
{{
  "comparables": [
    {{
      "competidor": "nombre del competidor",
      "producto": "nombre del producto",
      "precio": precio,
      "similitud": porcentaje 0-100,
      "tipo_comparacion": "MISMO_PRODUCTO | PRODUCTO_SIMILAR | MISMA_CATEGORIA",
      "razon": "breve explicación"
    }}
  ],
  "observaciones": "comentarios generales sobre el análisis"
}}

Máximo 5 comparables más relevantes."""

    try:
        llm_key = _get_llm_key()
        
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"comparables-{codigo_producto}-{uuid.uuid4().hex[:8]}",
            system_message="Eres un analista experto en comparación de productos de restaurantes. Respondes siempre en JSON válido."
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=prompt)
        response_text = await chat.send_message(user_message)
        
        # Parsear respuesta
        try:
            response_clean = response_text.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.startswith('```'):
                response_clean = response_clean[3:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            respuesta_ia = json.loads(response_clean.strip())
        except json.JSONDecodeError:
            respuesta_ia = {
                'comparables': [],
                'observaciones': response_text[:500],
                'raw_response': response_text
            }
        
        # Guardar análisis
        analisis_id = _guardar_analisis_ia(
            producto_id=None,
            codigo_producto=codigo_producto,
            server_id=server_id,
            empresa_id=empresa_id,
            unidad_negocio_id=unidad_negocio_id,
            tipo_analisis=TipoAnalisisIA.SUGERENCIA_COMPARABLES,
            modelo_ia="openai",
            version_modelo="gpt-5.2",
            prompt_resumen=f"Sugerencia de comparables para {datos_producto.get('nombre', codigo_producto)}",
            datos_entrada_json={
                'producto': datos_producto,
                'items_analizados': len(todos_items),
            },
            respuesta_ia_json=respuesta_ia,
            justificacion_ia=respuesta_ia.get('observaciones', ''),
            confianza_ia=ConfianzaIA.MEDIA,
            requiere_revision=True,  # Siempre requiere validación humana
            precio_actual=datos_producto.get('precio_actual'),
            precio_sugerido=None,
            margen_actual=datos_producto.get('margen_actual'),
            margen_sugerido=None,
            competidores_usados=[c['nombre'] for c in competidores],
            fuentes_usadas=['EDARSAHUB_SQL', 'Comercial_CompetidoresMenuItems'],
            estado=EstadoAnalisisIA.REQUIERE_REVISION,
            usuario=usuario
        )
        
        return {
            'success': True,
            'analisis_id': analisis_id,
            'producto': {
                'codigo': codigo_producto,
                'nombre': datos_producto.get('nombre'),
            },
            'comparables': respuesta_ia.get('comparables', []),
            'observaciones': respuesta_ia.get('observaciones'),
            'items_analizados': len(todos_items),
            'requiere_validacion': True,
            'estado': EstadoAnalisisIA.REQUIERE_REVISION.value,
            'modelo_ia': 'gpt-5.2',
            'mensaje': 'Sugerencias generadas. Requieren validación humana antes de crear benchmark.',
        }
        
    except Exception as e:
        logger.error(f"[PRICING-IA] Error en sugerencia comparables: {e}")
        return {
            'success': False,
            'estado': EstadoAnalisisIA.ERROR.value,
            'mensaje': f'Error: {str(e)}',
        }


async def generar_justificacion_con_ia(
    codigo_producto: str,
    server_id: str,
    empresa_id: int,
    unidad_negocio_id: int,
    precio_propuesto: float,
    usuario: str
) -> Dict[str, Any]:
    """
    Genera justificación comercial para un precio propuesto usando GPT-5.2.
    
    Útil para solicitudes de cambio de precio.
    NO modifica precios.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    datos_producto = _obtener_datos_producto(codigo_producto, server_id)
    
    if not datos_producto.get('existe'):
        return {
            'success': False,
            'estado': EstadoAnalisisIA.DATOS_INSUFICIENTES.value,
            'mensaje': f'Producto {codigo_producto} no encontrado',
        }
    
    contexto_unidad = _obtener_contexto_unidad(unidad_negocio_id)
    benchmark = obtener_precios_competencia_producto(codigo_producto, server_id)
    
    # Calcular métricas
    precio_actual = datos_producto.get('precio_actual', 0) or 0
    costo = datos_producto.get('costo', 0) or 0
    
    cambio_porcentaje = ((precio_propuesto - precio_actual) / precio_actual * 100) if precio_actual > 0 else 0
    margen_propuesto = ((1 - costo / precio_propuesto) * 100) if costo > 0 and precio_propuesto > 0 else None
    
    prompt = f"""Genera una justificación comercial profesional para el siguiente cambio de precio.

PRODUCTO:
- Nombre: {datos_producto.get('nombre')}
- Familia: {datos_producto.get('familia', 'N/A')}
- Costo: ${costo:.2f}
- Precio Actual: ${precio_actual:.2f}
- Margen Actual: {datos_producto.get('margen_actual', 'N/A')}%

PRECIO PROPUESTO:
- Nuevo Precio: ${precio_propuesto:.2f}
- Cambio: {cambio_porcentaje:+.1f}%
- Margen Propuesto: {margen_propuesto:.1f}% si se calcula

CONTEXTO:
- Restaurante: {contexto_unidad.get('nombre_comercial', 'N/A')}
- Segmento: {contexto_unidad.get('segmento_precio', 'N/A')}
- Ciudad: {contexto_unidad.get('ciudad', 'N/A')}

COMPETENCIA:
{f"- Precio Promedio: ${benchmark.get('precio_promedio', 0):.2f}" if benchmark.get('tiene_datos') else "- Sin datos de competencia"}

Genera una justificación formal que incluya:
1. Razón del cambio
2. Impacto en margen
3. Posicionamiento vs competencia
4. Recomendación

Responde en JSON:
{{
  "justificacion_formal": "texto de 2-3 párrafos",
  "puntos_clave": ["punto 1", "punto 2", "punto 3"],
  "riesgo": "BAJO | MEDIO | ALTO",
  "recomendacion_final": "APROBAR | REVISAR | RECHAZAR"
}}"""

    try:
        llm_key = _get_llm_key()
        
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"justificacion-{codigo_producto}-{uuid.uuid4().hex[:8]}",
            system_message="Eres un gerente comercial experto en justificación de precios. Respondes en JSON."
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=prompt)
        response_text = await chat.send_message(user_message)
        
        try:
            response_clean = response_text.strip()
            if '```' in response_clean:
                response_clean = response_clean.split('```')[1]
                if response_clean.startswith('json'):
                    response_clean = response_clean[4:]
            respuesta_ia = json.loads(response_clean.strip())
        except (json.JSONDecodeError, IndexError, TypeError):
            respuesta_ia = {
                'justificacion_formal': response_text[:1000],
                'puntos_clave': [],
                'riesgo': 'MEDIO',
                'recomendacion_final': 'REVISAR'
            }
        
        # Guardar
        analisis_id = _guardar_analisis_ia(
            producto_id=None,
            codigo_producto=codigo_producto,
            server_id=server_id,
            empresa_id=empresa_id,
            unidad_negocio_id=unidad_negocio_id,
            tipo_analisis=TipoAnalisisIA.JUSTIFICACION_PRECIO,
            modelo_ia="openai",
            version_modelo="gpt-5.2",
            prompt_resumen=f"Justificación para precio ${precio_propuesto:.2f}",
            datos_entrada_json={
                'producto': datos_producto,
                'precio_propuesto': precio_propuesto,
                'cambio_porcentaje': cambio_porcentaje,
            },
            respuesta_ia_json=respuesta_ia,
            justificacion_ia=respuesta_ia.get('justificacion_formal', ''),
            confianza_ia=ConfianzaIA.MEDIA,
            requiere_revision=respuesta_ia.get('recomendacion_final') != 'APROBAR',
            precio_actual=precio_actual,
            precio_sugerido=precio_propuesto,
            margen_actual=datos_producto.get('margen_actual'),
            margen_sugerido=margen_propuesto,
            competidores_usados=[],
            fuentes_usadas=['EDARSAHUB_SQL'],
            estado=EstadoAnalisisIA.GENERADO,
            usuario=usuario
        )
        
        return {
            'success': True,
            'analisis_id': analisis_id,
            'producto': {
                'codigo': codigo_producto,
                'nombre': datos_producto.get('nombre'),
            },
            'precio_actual': precio_actual,
            'precio_propuesto': precio_propuesto,
            'cambio_porcentaje': round(cambio_porcentaje, 1),
            'margen_propuesto': margen_propuesto,
            'justificacion': respuesta_ia.get('justificacion_formal'),
            'puntos_clave': respuesta_ia.get('puntos_clave', []),
            'riesgo': respuesta_ia.get('riesgo'),
            'recomendacion': respuesta_ia.get('recomendacion_final'),
            'estado': EstadoAnalisisIA.GENERADO.value,
            'modelo_ia': 'gpt-5.2',
            'mensaje': 'Justificación generada. NO modifica precios ni crea solicitudes automáticas.',
        }
        
    except Exception as e:
        logger.error(f"[PRICING-IA] Error en justificación: {e}")
        return {
            'success': False,
            'estado': EstadoAnalisisIA.ERROR.value,
            'mensaje': f'Error: {str(e)}',
        }


async def analizar_benchmark_con_ia(
    unidad_negocio_id: int,
    empresa_id: int,
    usuario: str,
    lista_id: str = None
) -> Dict[str, Any]:
    """
    Analiza el benchmark completo de una unidad con GPT-5.2.
    
    Genera insights sobre posicionamiento general vs competencia.
    NO modifica precios.
    
    Args:
        lista_id: ID de lista de competidores para filtrar benchmark (opcional)
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from modules.comercial.services.listas_competidores_service import obtener_lista_competidores
    
    # Validar lista si se especifica
    lista_usada = None
    if lista_id:
        lista_info = obtener_lista_competidores(lista_id)
        if not lista_info:
            return {
                'success': False,
                'estado': EstadoAnalisisIA.ERROR.value,
                'mensaje': f'Lista de competidores {lista_id} no encontrada',
            }
        if not lista_info.get('activo'):
            return {
                'success': False,
                'estado': EstadoAnalisisIA.ERROR.value,
                'mensaje': f'Lista de competidores "{lista_info.get("nombre_lista")}" está inactiva',
            }
        if lista_info.get('total_competidores', 0) == 0:
            return {
                'success': False,
                'estado': EstadoAnalisisIA.DATOS_INSUFICIENTES.value,
                'mensaje': f'Lista "{lista_info.get("nombre_lista")}" no tiene competidores activos',
            }
        lista_usada = {
            'lista_id': lista_id,
            'nombre_lista': lista_info.get('nombre_lista'),
            'total_competidores': lista_info.get('total_competidores')
        }
        logger.info(f"[PRICING-IA] Benchmark filtrando por lista '{lista_info.get('nombre_lista')}'")
    
    contexto_unidad = _obtener_contexto_unidad(unidad_negocio_id)
    
    if not contexto_unidad.get('existe'):
        return {
            'success': False,
            'estado': EstadoAnalisisIA.DATOS_INSUFICIENTES.value,
            'mensaje': 'Perfil digital de unidad no encontrado',
        }
    
    stats_competidores = obtener_estadisticas_competidores(unidad_negocio_id)
    stats_items = obtener_estadisticas_menu_items(unidad_negocio_id)
    # Filtrar competidores por lista si se especifica
    competidores = _obtener_competidores_para_contexto(unidad_negocio_id, limit=5, lista_id=lista_id)
    
    if stats_competidores['total_competidores'] == 0:
        return {
            'success': False,
            'estado': EstadoAnalisisIA.DATOS_INSUFICIENTES.value,
            'mensaje': 'No hay competidores configurados para analizar',
        }
    
    # Validar que hay competidores después del filtro
    if lista_id and len(competidores) == 0:
        return {
            'success': False,
            'estado': EstadoAnalisisIA.DATOS_INSUFICIENTES.value,
            'mensaje': 'La lista seleccionada no contiene competidores activos con datos de precios',
        }
    
    # Construir resumen de precios por competidor
    resumen_competidores = []
    for comp in competidores:
        precios = [i['precio'] for i in comp['items'] if i['precio']]
        if precios:
            resumen_competidores.append({
                'nombre': comp['nombre'],
                'tipo': comp['tipo'],
                'segmento': comp['segmento'],
                'precio_min': min(precios),
                'precio_max': max(precios),
                'precio_promedio': sum(precios) / len(precios),
                'items': len(precios),
            })
    
    # Indicador de filtro por lista
    lista_filtro_str = f"\n\nFILTRO APLICADO: Lista '{lista_usada.get('nombre_lista')}' ({lista_usada.get('total_competidores')} competidores)" if lista_usada else "\n\nFILTRO: Benchmark general (todos los competidores)"
    
    prompt = f"""Analiza el benchmark competitivo de este restaurante y genera insights estratégicos.

NUESTRO RESTAURANTE:
- Nombre: {contexto_unidad.get('nombre_comercial')}
- Concepto: {contexto_unidad.get('concepto', 'N/A')}
- Tipo: {contexto_unidad.get('tipo_restaurante', 'N/A')}
- Segmento: {contexto_unidad.get('segmento_precio', 'N/A')}
- Ciudad: {contexto_unidad.get('ciudad', 'N/A')}
- Ticket Objetivo: ${contexto_unidad.get('ticket_promedio_objetivo', 'N/A')}

ESTADÍSTICAS DE BENCHMARK:
- Competidores configurados: {stats_competidores['total_competidores']}
- Competidores directos: {stats_competidores['directos']}
- Competidores aspiracionales: {stats_competidores['aspiracionales']}
- Items capturados: {stats_items['total_items']}{lista_filtro_str}

RESUMEN POR COMPETIDOR:
{chr(10).join([f"- {c['nombre']} ({c['tipo']}, {c['segmento']}): ${c['precio_min']:.0f}-${c['precio_max']:.0f} (prom: ${c['precio_promedio']:.0f}, {c['items']} items)" for c in resumen_competidores]) if resumen_competidores else "Sin datos suficientes"}

Genera un análisis estratégico que incluya:
1. Evaluación del posicionamiento de precios
2. Oportunidades identificadas
3. Riesgos detectados
4. Recomendaciones estratégicas

Responde en JSON:
{{
  "resumen_ejecutivo": "párrafo de resumen",
  "posicionamiento": "COMPETITIVO | POR_DEBAJO_MERCADO | POR_ENCIMA_MERCADO | PREMIUM | ECONOMICO",
  "oportunidades": ["oportunidad 1", "oportunidad 2"],
  "riesgos": ["riesgo 1", "riesgo 2"],
  "recomendaciones": ["recomendación 1", "recomendación 2", "recomendación 3"],
  "prioridad_accion": "ALTA | MEDIA | BAJA",
  "areas_revisar": ["área 1", "área 2"]
}}"""

    try:
        llm_key = _get_llm_key()
        
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"benchmark-{unidad_negocio_id}-{uuid.uuid4().hex[:8]}",
            system_message="Eres un consultor estratégico de restaurantes. Respondes en JSON."
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=prompt)
        response_text = await chat.send_message(user_message)
        
        try:
            response_clean = response_text.strip()
            if '```' in response_clean:
                response_clean = response_clean.split('```')[1]
                if response_clean.startswith('json'):
                    response_clean = response_clean[4:]
            respuesta_ia = json.loads(response_clean.strip())
        except (json.JSONDecodeError, IndexError, TypeError):
            respuesta_ia = {
                'resumen_ejecutivo': response_text[:1000],
                'posicionamiento': 'COMPETITIVO',
                'oportunidades': [],
                'riesgos': [],
                'recomendaciones': [],
                'prioridad_accion': 'MEDIA',
                'areas_revisar': []
            }
        
        # Guardar
        analisis_id = _guardar_analisis_ia(
            producto_id=None,
            codigo_producto='BENCHMARK_UNIDAD',
            server_id='',
            empresa_id=empresa_id,
            unidad_negocio_id=unidad_negocio_id,
            tipo_analisis=TipoAnalisisIA.ANALISIS_BENCHMARK,
            modelo_ia="openai",
            version_modelo="gpt-5.2",
            prompt_resumen=f"Análisis benchmark {contexto_unidad.get('nombre_comercial')}" + (f" (Lista: {lista_usada.get('nombre_lista')})" if lista_usada else ""),
            datos_entrada_json={
                'unidad': contexto_unidad,
                'stats': {
                    'competidores': stats_competidores,
                    'items': stats_items,
                },
                'resumen_competidores': resumen_competidores,
                'lista_usada': lista_usada,
            },
            respuesta_ia_json=respuesta_ia,
            justificacion_ia=respuesta_ia.get('resumen_ejecutivo', ''),
            confianza_ia=ConfianzaIA.MEDIA if stats_items['total_items'] >= 10 else ConfianzaIA.BAJA,
            requiere_revision=False,
            precio_actual=None,
            precio_sugerido=None,
            margen_actual=None,
            margen_sugerido=None,
            competidores_usados=[c['nombre'] for c in resumen_competidores],
            fuentes_usadas=['EDARSAHUB_SQL', 'Comercial_Competidores', 'Comercial_CompetidoresMenuItems'],
            estado=EstadoAnalisisIA.GENERADO,
            usuario=usuario,
            lista_id=lista_id
        )
        
        return {
            'success': True,
            'analisis_id': analisis_id,
            'unidad': {
                'id': unidad_negocio_id,
                'nombre': contexto_unidad.get('nombre_comercial'),
                'segmento': contexto_unidad.get('segmento_precio'),
            },
            'resumen': respuesta_ia.get('resumen_ejecutivo'),
            'posicionamiento': respuesta_ia.get('posicionamiento'),
            'oportunidades': respuesta_ia.get('oportunidades', []),
            'riesgos': respuesta_ia.get('riesgos', []),
            'recomendaciones': respuesta_ia.get('recomendaciones', []),
            'prioridad': respuesta_ia.get('prioridad_accion'),
            'areas_revisar': respuesta_ia.get('areas_revisar', []),
            'estadisticas': {
                'competidores': stats_competidores['total_competidores'],
                'items': stats_items['total_items'],
            },
            'estado': EstadoAnalisisIA.GENERADO.value,
            'modelo_ia': 'gpt-5.2',
            'mensaje': 'Análisis de benchmark generado. Insights para revisión estratégica.',
            'lista_usada': lista_usada,
        }
        
    except Exception as e:
        logger.error(f"[PRICING-IA] Error en benchmark: {e}")
        return {
            'success': False,
            'estado': EstadoAnalisisIA.ERROR.value,
            'mensaje': f'Error: {str(e)}',
        }


__all__ = [
    # Enums
    'TipoAnalisisIA',
    'EstadoAnalisisIA',
    'ConfianzaIA',
    
    # Funciones principales
    'analizar_producto_con_ia',
    'sugerir_comparables_con_ia',
    'generar_justificacion_con_ia',
    'analizar_benchmark_con_ia',
    'obtener_analisis_ia',
]
