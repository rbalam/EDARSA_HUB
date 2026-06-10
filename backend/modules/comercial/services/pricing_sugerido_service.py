from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
FASE 1C-3I-B: Servicio de Cálculo de Precio Sugerido Base

Este módulo orquesta el cálculo de precios sugeridos usando diferentes motores:
- VINOS_RANGOS: Regla existente de rangos (NO MODIFICAR)
- COSTO_MARGEN: Fórmula precio = costo / (1 - margen)
- BENCHMARK_COMPETENCIA: Basado en posición vs competidores
- MIXTO_COSTO_COMPETENCIA: Combina costo+margen con benchmark

REGLAS CRÍTICAS:
- NO ejecutar IA en esta fase (IA en 1C-3I-C)
- NO modificar precios oficiales
- Usar resolver_tasa_impuesto() para impuestos
- NO hardcodear 16%
- La regla de VINOS_RANGOS es intocable

DEPENDENCIAS:
- impuestos_service.py: resolver_tasa_impuesto()
- precios_vinos_service.py: calcular_precio_sugerido_vino()
"""

from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
import logging
import math

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG

from .pricing_schemas import (
    PrecioSugeridoCalcularRequest,
    PrecioSugeridoCalcularResponse,
    TipoMotorPrecio,
    EstadoCalculo,
    PosicionVsCompetencia,
)
from .impuestos_service import resolver_tasa_impuesto, EstadoFiscal
from .precios_vinos_service import calcular_precio_sugerido_vino
from .benchmark_service import obtener_precios_competencia_producto

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


def _redondear(valor: float, multiplo: int, metodo: str) -> float:
    """
    Redondea el valor al múltiplo especificado.
    
    Args:
        valor: Valor a redondear
        multiplo: Múltiplo de redondeo (ej. 5)
        metodo: MAS_CERCANO, HACIA_ARRIBA, HACIA_ABAJO
    
    Returns:
        Valor redondeado
    """
    if metodo == "HACIA_ARRIBA":
        return math.ceil(valor / multiplo) * multiplo
    elif metodo == "HACIA_ABAJO":
        return math.floor(valor / multiplo) * multiplo
    else:  # MAS_CERCANO
        return round(valor / multiplo) * multiplo


def _obtener_costo_producto(codigo_producto: str, server_id: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Obtiene el costo de un producto desde EDARSAHUB.
    
    Jerarquía de fuentes:
    1. CostoReceta > 0
    2. Sync_Productos_Insumos.Costo
    3. UltimoCosto
    4. CostoPromedio
    5. CostoEstandar
    
    Returns:
        (costo, fuente) o (None, None) si no existe
    """
    conn = _get_conn()
    
    # Paso 1: Verificar CostoReceta en Sync_Productos
    query_receta = f"""
    SELECT CostoReceta
    FROM Sync_Productos
    WHERE ServerID = '{server_id}'
      AND CodigoFuente = '{codigo_producto}'
    """
    
    result = execute_sql_query(*conn, query_receta)
    
    if result and len(result) > 0:
        costo_receta = result[0].get('CostoReceta')
        if costo_receta is not None and float(costo_receta) > 0:
            return float(costo_receta), 'COSTO_RECETA'
    
    # Paso 2-5: Verificar en Sync_Productos_Insumos
    query_insumos = f"""
    SELECT 
        Costo,
        UltimoCosto,
        CostoPromedio,
        CostoEstandar
    FROM Sync_Productos_Insumos
    WHERE ServerID = '{server_id}'
      AND CodigoFuente = '{codigo_producto}'
    """
    
    result_insumos = execute_sql_query(*conn, query_insumos)
    
    if result_insumos and len(result_insumos) > 0:
        row = result_insumos[0]
        
        if row.get('Costo') and float(row['Costo']) > 0:
            return float(row['Costo']), 'INSUMO_COSTO'
        
        if row.get('UltimoCosto') and float(row['UltimoCosto']) > 0:
            return float(row['UltimoCosto']), 'INSUMO_ULTIMO'
        
        if row.get('CostoPromedio') and float(row['CostoPromedio']) > 0:
            return float(row['CostoPromedio']), 'INSUMO_PROMEDIO'
        
        if row.get('CostoEstandar') and float(row['CostoEstandar']) > 0:
            return float(row['CostoEstandar']), 'INSUMO_ESTANDAR'
    
    return None, None


def _obtener_nombre_producto(codigo_producto: str, server_id: str) -> Optional[str]:
    """Obtiene el nombre de un producto."""
    conn = _get_conn()
    
    query = f"""
    SELECT Nombre
    FROM Sync_Productos
    WHERE ServerID = '{server_id}'
      AND CodigoFuente = '{codigo_producto}'
    """
    
    result = execute_sql_query(*conn, query)
    
    if result and len(result) > 0:
        return result[0].get('Nombre')
    
    return None


def _es_producto_vino(codigo_producto: str, server_id: str) -> bool:
    """
    Verifica si un producto es vino (para aplicar regla VINOS_RANGOS).
    """
    conn = _get_conn()
    
    familias_vino = [
        'B CHAMPAGNES Y  COGNACS', 'B CHAMPAGNES Y COGNACS', 'B VINOS', 
        'B VINOS DE POSTRE', 'C CAVAS', 'CAVAS', 'CHAMPAGNES Y COGNACS',
        'VINOS BLANCOS', 'VINOS ESPUMOSOS/POSTRE', 'VINOS ROSADOS', 'VINOS TINTOS'
    ]
    familias_str = "', '".join(familias_vino)
    
    query = f"""
    SELECT 1
    FROM Sync_Productos
    WHERE ServerID = '{server_id}'
      AND CodigoFuente = '{codigo_producto}'
      AND FamiliaNombre IN ('{familias_str}')
    """
    
    result = execute_sql_query(*conn, query)
    
    return result is not None and len(result) > 0


def _calcular_posicion_vs_competencia(
    precio_propio: float,
    precio_min: float,
    precio_promedio: float,
    precio_max: float
) -> PosicionVsCompetencia:
    """
    Calcula la posición relativa de nuestro precio vs competencia.
    """
    if precio_propio < precio_min * 0.8:
        return PosicionVsCompetencia.MUY_POR_DEBAJO
    elif precio_propio < precio_promedio * 0.9:
        return PosicionVsCompetencia.POR_DEBAJO
    elif precio_propio <= precio_promedio * 1.1:
        return PosicionVsCompetencia.ALINEADO
    elif precio_propio <= precio_max * 1.2:
        return PosicionVsCompetencia.POR_ENCIMA
    else:
        return PosicionVsCompetencia.MUY_POR_ENCIMA


# =============================================================================
# FUNCIÓN PRINCIPAL DE CÁLCULO
# =============================================================================

def calcular_precio_sugerido_base(
    request: PrecioSugeridoCalcularRequest
) -> PrecioSugeridoCalcularResponse:
    """
    Calcula el precio sugerido base para un producto (SIN IA).
    
    TIPOS DE MOTOR:
    - VINOS_RANGOS: Delega a precios_vinos_service.py (regla existente, intocable)
    - COSTO_MARGEN: precio_minimo = costo / (1 - margen)
    - BENCHMARK_COMPETENCIA: Basado en posición vs competidores
    - MIXTO_COSTO_COMPETENCIA: Combina ambos enfoques
    
    FÓRMULA COSTO_MARGEN:
        precio_minimo_rentable = costo_producto / (1 - margen_objetivo_porcentaje)
        precio_con_impuesto = precio_minimo_rentable * (1 + tasa_impuesto)
        precio_redondeado = redondear(precio_con_impuesto, multiplo_redondeo, metodo_redondeo)
    
    REGLAS:
    - NO ejecutar IA
    - Usar resolver_tasa_impuesto()
    - NO hardcodear 16%
    - NO modificar precios oficiales
    
    Args:
        request: PrecioSugeridoCalcularRequest con parámetros del cálculo
    
    Returns:
        PrecioSugeridoCalcularResponse con resultado del cálculo
    """
    fecha_calculo = datetime.now()
    
    # Obtener nombre del producto
    nombre_producto = _obtener_nombre_producto(request.codigo_producto, request.server_id)
    
    # Inicializar respuesta base
    response = PrecioSugeridoCalcularResponse(
        producto_id=request.producto_id,
        codigo_producto=request.codigo_producto,
        nombre_producto=nombre_producto,
        server_id=request.server_id,
        tipo_motor=request.tipo_motor,
        multiplo_redondeo=request.multiplo_redondeo,
        metodo_redondeo=request.metodo_redondeo,
        estado=EstadoCalculo.ERROR_CALCULO,
        fecha_calculo=fecha_calculo,
    )
    
    try:
        # =====================================================================
        # MOTOR VINOS_RANGOS: Delegar a servicio existente (INTOCABLE)
        # =====================================================================
        if request.tipo_motor == TipoMotorPrecio.VINOS_RANGOS:
            # Verificar que sea un vino
            if not _es_producto_vino(request.codigo_producto, request.server_id):
                response.estado = EstadoCalculo.ERROR_CALCULO
                response.mensaje = "El producto no es vino. Use motor COSTO_MARGEN para productos generales."
                return response
            
            # Delegar a precios_vinos_service.py
            resultado_vino = calcular_precio_sugerido_vino(
                request.codigo_producto,
                request.server_id,
                nombre_producto
            )
            
            # Mapear resultado de vinos a respuesta estándar
            response.costo_base_vino = resultado_vino.costo_base_vino
            response.fuente_costo = resultado_vino.fuente_costo
            response.rango_aplicado = resultado_vino.rango_id
            response.margen_multiplicador = resultado_vino.margen_multiplicador
            response.tasa_impuesto = resultado_vino.tasa_impuesto
            response.precio_minimo_rentable = resultado_vino.precio_base
            response.precio_con_impuesto = resultado_vino.precio_con_impuesto
            response.precio_sugerido = resultado_vino.precio_sugerido
            response.multiplo_redondeo = resultado_vino.multiplo_redondeo or 5
            response.metodo_redondeo = resultado_vino.metodo_redondeo or "MAS_CERCANO"
            
            # Mapear estado
            estado_str = resultado_vino.estado.value
            try:
                response.estado = EstadoCalculo(estado_str)
            except ValueError:
                response.estado = EstadoCalculo.ERROR_CALCULO
            
            response.mensaje = resultado_vino.mensaje
            response.permite_solicitud_cambio = resultado_vino.estado.value == "CALCULADO"
            
            return response
        
        # =====================================================================
        # MOTOR COSTO_MARGEN: Fórmula matemática pura
        # =====================================================================
        if request.tipo_motor == TipoMotorPrecio.COSTO_MARGEN:
            # 1. Obtener costo
            costo, fuente_costo = _obtener_costo_producto(request.codigo_producto, request.server_id)
            
            if costo is None or costo <= 0:
                response.estado = EstadoCalculo.COSTO_NO_CONFIGURADO
                response.mensaje = "Producto sin costo configurado. Verifique CostoReceta o costos en insumos."
                return response
            
            response.costo_producto = costo
            response.fuente_costo = fuente_costo
            
            # 2. Validar margen
            margen = request.margen_objetivo
            if margen is None or margen <= 0 or margen >= 1:
                response.estado = EstadoCalculo.MARGEN_INVALIDO
                response.mensaje = f"Margen objetivo inválido: {margen}. Debe ser > 0 y < 1 (ej: 0.30 = 30%)"
                return response
            
            response.margen_objetivo = margen
            
            # 3. Obtener tasa de impuesto usando resolver_tasa_impuesto()
            resultado_impuesto = resolver_tasa_impuesto(
                codigo_producto=request.codigo_producto,
                server_id=request.server_id
            )
            
            if not resultado_impuesto.permite_calculo_precio:
                response.estado = EstadoCalculo.IMPUESTO_NO_CONFIGURADO
                response.estado_fiscal = resultado_impuesto.estado_fiscal.value
                response.fuente_impuesto = resultado_impuesto.fuente
                response.mensaje = resultado_impuesto.mensaje or "Impuesto no configurado para este producto."
                return response
            
            # Tasa viene como porcentaje (16 = 16%), convertir a decimal (0.16)
            tasa = resultado_impuesto.tasa / 100 if resultado_impuesto.tasa else 0
            response.tasa_impuesto = resultado_impuesto.tasa  # Guardar como porcentaje
            response.estado_fiscal = resultado_impuesto.estado_fiscal.value
            response.fuente_impuesto = resultado_impuesto.fuente
            
            # 4. CALCULAR PRECIO
            # precio_minimo_rentable = costo / (1 - margen)
            precio_minimo = costo / (1 - margen)
            response.precio_minimo_rentable = round(precio_minimo, 4)
            
            # precio_con_impuesto = precio_minimo * (1 + tasa)
            precio_con_impuesto = precio_minimo * (1 + tasa)
            response.precio_con_impuesto = round(precio_con_impuesto, 4)
            
            # precio_redondeado = redondear(precio_con_impuesto, multiplo, metodo)
            precio_sugerido = _redondear(
                precio_con_impuesto,
                request.multiplo_redondeo,
                request.metodo_redondeo
            )
            response.precio_sugerido = precio_sugerido
            
            # 5. Resultado exitoso
            response.estado = EstadoCalculo.CALCULADO
            response.mensaje = (
                f"Precio calculado: Costo ${costo:,.2f} ({fuente_costo}) / "
                f"(1 - {margen*100:.0f}%) = ${precio_minimo:,.2f}, "
                f"+ IVA {resultado_impuesto.tasa}% = ${precio_sugerido:,.2f}"
            )
            response.permite_solicitud_cambio = True
            
            return response
        
        # =====================================================================
        # MOTOR BENCHMARK_COMPETENCIA: Basado en posición vs competidores
        # =====================================================================
        if request.tipo_motor == TipoMotorPrecio.BENCHMARK_COMPETENCIA:
            # Obtener precios de competencia
            benchmark_data = obtener_precios_competencia_producto(
                request.codigo_producto,
                request.server_id
            )
            
            if not benchmark_data.get('tiene_datos'):
                response.estado = EstadoCalculo.ERROR_CALCULO
                response.mensaje = benchmark_data.get('mensaje', 'Sin datos de benchmark para este producto')
                return response
            
            precio_promedio = benchmark_data.get('precio_promedio', 0)
            precio_min = benchmark_data.get('precio_minimo', 0)
            precio_max = benchmark_data.get('precio_maximo', 0)
            
            # El precio sugerido por benchmark es el promedio de la competencia
            # (En fases futuras, IA ajustará según concepto y segmento)
            precio_sugerido = _redondear(
                precio_promedio,
                request.multiplo_redondeo,
                request.metodo_redondeo
            )
            
            response.precio_sugerido = precio_sugerido
            response.precio_con_impuesto = precio_promedio  # Asumimos que ya incluye impuesto
            response.estado = EstadoCalculo.CALCULADO
            response.mensaje = (
                f"Precio benchmark: Promedio competencia ${precio_promedio:,.2f} "
                f"(min: ${precio_min:,.2f}, max: ${precio_max:,.2f}). "
                f"Basado en {benchmark_data.get('total_comparables', 0)} comparables."
            )
            response.permite_solicitud_cambio = True
            
            return response
        
        # =====================================================================
        # MOTOR MIXTO_COSTO_COMPETENCIA: Combina costo+margen con benchmark
        # =====================================================================
        if request.tipo_motor == TipoMotorPrecio.MIXTO_COSTO_COMPETENCIA:
            # 1. Calcular por costo+margen
            costo, fuente_costo = _obtener_costo_producto(request.codigo_producto, request.server_id)
            
            if costo is None or costo <= 0:
                response.estado = EstadoCalculo.COSTO_NO_CONFIGURADO
                response.mensaje = "Producto sin costo configurado para cálculo mixto."
                return response
            
            response.costo_producto = costo
            response.fuente_costo = fuente_costo
            
            margen = request.margen_objetivo or 0.30  # Default 30%
            response.margen_objetivo = margen
            
            # Obtener impuesto
            resultado_impuesto = resolver_tasa_impuesto(
                codigo_producto=request.codigo_producto,
                server_id=request.server_id
            )
            
            tasa = (resultado_impuesto.tasa / 100) if resultado_impuesto.tasa else 0
            response.tasa_impuesto = resultado_impuesto.tasa
            response.estado_fiscal = resultado_impuesto.estado_fiscal.value if resultado_impuesto.estado_fiscal else None
            response.fuente_impuesto = resultado_impuesto.fuente
            
            # Calcular precio por costo
            precio_por_costo = (costo / (1 - margen)) * (1 + tasa)
            response.precio_minimo_rentable = round(costo / (1 - margen), 4)
            
            # 2. Obtener benchmark
            benchmark_data = obtener_precios_competencia_producto(
                request.codigo_producto,
                request.server_id
            )
            
            if benchmark_data.get('tiene_datos'):
                precio_benchmark = benchmark_data.get('precio_promedio', 0)
                
                # El precio sugerido es el MAYOR entre costo+margen y benchmark
                # (Garantiza rentabilidad mínima pero permite subir si competencia está arriba)
                precio_base = max(precio_por_costo, precio_benchmark)
                
                # Calcular posición vs competencia
                posicion = _calcular_posicion_vs_competencia(
                    precio_base,
                    benchmark_data.get('precio_minimo', 0),
                    benchmark_data.get('precio_promedio', 0),
                    benchmark_data.get('precio_maximo', 0)
                )
                
                mensaje_posicion = f"Posición: {posicion.value}. "
            else:
                precio_base = precio_por_costo
                mensaje_posicion = "Sin datos de competencia. "
            
            # Redondear
            precio_sugerido = _redondear(
                precio_base,
                request.multiplo_redondeo,
                request.metodo_redondeo
            )
            
            response.precio_con_impuesto = round(precio_base, 4)
            response.precio_sugerido = precio_sugerido
            response.estado = EstadoCalculo.CALCULADO
            response.mensaje = (
                f"Precio mixto: Costo+Margen ${precio_por_costo:,.2f}. "
                f"{mensaje_posicion}"
                f"Sugerido: ${precio_sugerido:,.2f}"
            )
            response.permite_solicitud_cambio = True
            
            return response
        
        # Motor no reconocido
        response.estado = EstadoCalculo.ERROR_CALCULO
        response.mensaje = f"Tipo de motor no reconocido: {request.tipo_motor}"
        return response
        
    except Exception as e:
        logger.error(f"[PRECIO-SUGERIDO] Error en cálculo: {e}")
        response.estado = EstadoCalculo.ERROR_CALCULO
        response.mensaje = f"Error en cálculo: {str(e)}"
        return response


def calcular_precios_masivo(
    server_id: str,
    tipo_motor: TipoMotorPrecio,
    margen_objetivo: Optional[float] = None,
    codigos_productos: Optional[List[str]] = None,
    familia: Optional[str] = None,
    limit: int = 100
) -> List[PrecioSugeridoCalcularResponse]:
    """
    Calcula precios sugeridos para múltiples productos.
    
    Args:
        server_id: UUID del servidor
        tipo_motor: Motor a usar para todos los productos
        margen_objetivo: Margen objetivo (requerido para COSTO_MARGEN)
        codigos_productos: Lista de códigos específicos (opcional)
        familia: Filtrar por familia (opcional)
        limit: Límite de productos a procesar
    
    Returns:
        Lista de PrecioSugeridoCalcularResponse
    """
    conn = _get_conn()
    
    # Construir query para obtener productos
    where_clauses = [f"ServerID = '{server_id}'"]
    
    if codigos_productos:
        codigos_str = "', '".join(codigos_productos)
        where_clauses.append(f"CodigoFuente IN ('{codigos_str}')")
    
    if familia:
        where_clauses.append(f"FamiliaNombre = N'{familia}'")
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}"
    
    query = f"""
    SELECT TOP {limit}
        CodigoFuente
    FROM Sync_Productos
    {where_sql}
    ORDER BY Nombre
    """
    
    result = execute_sql_query(*conn, query)
    
    resultados = []
    
    for row in (result or []):
        codigo = row['CodigoFuente']
        
        request = PrecioSugeridoCalcularRequest(
            codigo_producto=codigo,
            server_id=server_id,
            tipo_motor=tipo_motor,
            margen_objetivo=margen_objetivo,
        )
        
        resultado = calcular_precio_sugerido_base(request)
        resultados.append(resultado)
    
    return resultados


def obtener_estadisticas_calculo(server_id: str, tipo_motor: TipoMotorPrecio = TipoMotorPrecio.COSTO_MARGEN) -> Dict[str, Any]:
    """
    Obtiene estadísticas de cálculo de precios para un servidor.
    
    Returns:
        Dict con conteos por estado
    """
    # Hacer un cálculo de muestra para obtener estadísticas
    resultados = calcular_precios_masivo(
        server_id=server_id,
        tipo_motor=tipo_motor,
        margen_objetivo=0.30,  # Margen de ejemplo
        limit=500
    )
    
    stats = {
        'total': len(resultados),
        'CALCULADO': 0,
        'COSTO_NO_CONFIGURADO': 0,
        'IMPUESTO_NO_CONFIGURADO': 0,
        'MARGEN_INVALIDO': 0,
        'RANGO_NO_CONFIGURADO': 0,
        'ERROR_CALCULO': 0,
    }
    
    for r in resultados:
        estado_key = r.estado.value
        if estado_key in stats:
            stats[estado_key] += 1
        else:
            stats['ERROR_CALCULO'] += 1
    
    # Calcular porcentajes
    if stats['total'] > 0:
        stats['porcentaje_exito'] = round(stats['CALCULADO'] / stats['total'] * 100, 1)
    else:
        stats['porcentaje_exito'] = 0
    
    return stats


__all__ = [
    'calcular_precio_sugerido_base',
    'calcular_precios_masivo',
    'obtener_estadisticas_calculo',
]
