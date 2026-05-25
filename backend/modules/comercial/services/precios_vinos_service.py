"""
Servicio de Cálculo de Precio Sugerido para Vinos - FASE 1C-3G-E

Este módulo calcula el precio sugerido para productos clasificados como vino
usando la regla de precio por rango configurada en EDARSAHUB SQL.

ACLARACIÓN CONCEPTUAL (Corrección FASE 1C-3G-E):
    La tabla de rangos NO calcula el costo del vino.
    La tabla de rangos determina el PRECIO DE VENTA SUGERIDO a partir del CostoBaseVino.

FÓRMULA:
    precio_base = CostoBaseVino * margen_multiplicador
    importe_impuesto = precio_base * tasa_impuesto_resuelta
    precio_con_impuesto = precio_base + importe_impuesto
    precio_sugerido = redondear(precio_con_impuesto, multiplo, metodo)

JERARQUÍA CORRECTA DE COSTOBASEVINO:
    1. CostoReceta (si > 0 y confiable como costo consolidado del producto)
    2. Sync_Productos_Insumos.Costo (costo de botella)
    3. Sync_Productos_Insumos.UltimoCosto
    4. Sync_Productos_Insumos.CostoPromedio
    5. Último costo de compra validado (futuro)
    6. Costo promedio de inventario (futuro)
    7. Costo proveedor vigente (futuro)
    8. Costo sincronizado del sistema origen (futuro)
    9. Override manual autorizado (futuro)

NOTA SOBRE CostoReceta:
    - Para vinos (botellas compradas), CostoReceta = 0 generalmente porque
      no son recetas elaboradas. Esto NO significa costo cero.
    - Si CostoReceta > 0, representa un costo consolidado confiable y debe usarse.
    - Si CostoReceta = 0 o NULL, se recurre a la jerarquía de insumos.

ESTADOS:
    - CALCULADO: Precio calculado exitosamente
    - COSTO_BASE_NO_CONFIGURADO: Sin costo confiable disponible
    - IMPUESTO_NO_CONFIGURADO: Sin tasa de impuesto válida
    - RANGO_NO_CONFIGURADO: Costo fuera de rangos configurados (ej. gap 4000-5000)
    - ERROR_CALCULO: Error en el proceso
"""

from typing import Optional, Dict, Any, Tuple, List
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, ROUND_DOWN
from enum import Enum
from dataclasses import dataclass
import math

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG


class EstadoCalculo(str, Enum):
    """Estados posibles del cálculo de precio."""
    CALCULADO = "CALCULADO"
    COSTO_BASE_NO_CONFIGURADO = "COSTO_BASE_NO_CONFIGURADO"  # Renombrado para claridad conceptual
    IMPUESTO_NO_CONFIGURADO = "IMPUESTO_NO_CONFIGURADO"
    RANGO_NO_CONFIGURADO = "RANGO_NO_CONFIGURADO"
    ERROR_CALCULO = "ERROR_CALCULO"


class MetodoRedondeo(str, Enum):
    """Métodos de redondeo disponibles."""
    MAS_CERCANO = "MAS_CERCANO"
    HACIA_ARRIBA = "HACIA_ARRIBA"
    HACIA_ABAJO = "HACIA_ABAJO"


@dataclass
class ResultadoPrecioSugerido:
    """Resultado del cálculo de precio sugerido."""
    # Producto
    codigo_producto: str
    server_id: str
    nombre_producto: Optional[str] = None
    
    # Costo Base (corregido conceptualmente)
    costo_base_vino: Optional[float] = None  # Renombrado de costo_botella
    fuente_costo: Optional[str] = None
    
    # Regla aplicada
    regla_precio_id: Optional[str] = None
    rango_id: Optional[str] = None
    margen_multiplicador: Optional[float] = None
    
    # Impuesto
    tasa_impuesto: Optional[float] = None
    impuesto_mapeo_id: Optional[str] = None
    
    # Cálculo
    precio_base: Optional[float] = None
    importe_impuesto: Optional[float] = None
    precio_con_impuesto: Optional[float] = None
    metodo_redondeo: Optional[str] = None
    multiplo_redondeo: Optional[int] = None
    precio_sugerido: Optional[float] = None
    
    # Estado
    estado: EstadoCalculo = EstadoCalculo.ERROR_CALCULO
    mensaje: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'codigo_producto': self.codigo_producto,
            'server_id': self.server_id,
            'nombre_producto': self.nombre_producto,
            'costo_base_vino': self.costo_base_vino,  # Campo renombrado
            'fuente_costo': self.fuente_costo,
            'regla_precio_id': self.regla_precio_id,
            'rango_id': self.rango_id,
            'margen_multiplicador': self.margen_multiplicador,
            'tasa_impuesto': self.tasa_impuesto,
            'precio_base': self.precio_base,
            'importe_impuesto': self.importe_impuesto,
            'precio_con_impuesto': self.precio_con_impuesto,
            'metodo_redondeo': self.metodo_redondeo,
            'multiplo_redondeo': self.multiplo_redondeo,
            'precio_sugerido': self.precio_sugerido,
            'estado': self.estado.value,
            'mensaje': self.mensaje,
            'permite_solicitud_cambio': self.estado == EstadoCalculo.CALCULADO
        }


def _get_conn_params() -> Tuple:
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
    if metodo == MetodoRedondeo.HACIA_ARRIBA.value:
        return math.ceil(valor / multiplo) * multiplo
    elif metodo == MetodoRedondeo.HACIA_ABAJO.value:
        return math.floor(valor / multiplo) * multiplo
    else:  # MAS_CERCANO
        return round(valor / multiplo) * multiplo


def obtener_costo_base_vino(codigo_producto: str, server_id: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Obtiene el CostoBaseVino aplicando la jerarquía correcta.
    
    JERARQUÍA DE COSTO (Corrección conceptual FASE 1C-3G-E):
    1. CostoReceta (si > 0, representa costo consolidado confiable)
    2. Sync_Productos_Insumos.Costo (costo de botella)
    3. Sync_Productos_Insumos.UltimoCosto
    4. Sync_Productos_Insumos.CostoPromedio
    5. Sync_Productos_Insumos.CostoEstandar (añadido en FASE 1C-3G-E2)
    6-9. Fuentes adicionales (futuro: compras, proveedor, override)
    
    NOTA: Para vinos (botellas compradas), CostoReceta = 0 generalmente
    porque no son recetas elaboradas. Esto NO significa costo cero.
    
    Returns:
        (costo, fuente) o (None, None) si no existe costo confiable
    """
    conn = _get_conn_params()
    
    # PASO 1: Verificar CostoReceta en Sync_Productos
    query_costo_receta = f"""
    SELECT 
        sp.CostoReceta
    FROM Sync_Productos sp
    WHERE sp.ServerID = '{server_id}'
      AND sp.CodigoFuente = '{codigo_producto}'
    """
    
    result_cr = execute_sql_query(*conn, query_costo_receta)
    
    if result_cr and len(result_cr) > 0:
        costo_receta = result_cr[0].get('CostoReceta')
        if costo_receta is not None and float(costo_receta) > 0:
            # CostoReceta > 0 es costo consolidado confiable
            return float(costo_receta), 'COSTO_RECETA'
    
    # PASO 2-5: Verificar costos en Sync_Productos_Insumos
    query_insumos = f"""
    SELECT 
        i.Costo,
        i.UltimoCosto,
        i.CostoPromedio,
        i.CostoEstandar
    FROM Sync_Productos_Insumos i
    WHERE i.ServerID = '{server_id}'
      AND i.CodigoFuente = '{codigo_producto}'
    """
    
    result_insumos = execute_sql_query(*conn, query_insumos)
    
    if result_insumos and len(result_insumos) > 0:
        row = result_insumos[0]
        
        # Jerarquía 2: Costo de botella/insumo
        if row.get('Costo') and float(row['Costo']) > 0:
            return float(row['Costo']), 'INSUMO_COSTO'
        
        # Jerarquía 3: Último costo
        if row.get('UltimoCosto') and float(row['UltimoCosto']) > 0:
            return float(row['UltimoCosto']), 'INSUMO_ULTIMO'
        
        # Jerarquía 4: Costo promedio
        if row.get('CostoPromedio') and float(row['CostoPromedio']) > 0:
            return float(row['CostoPromedio']), 'INSUMO_PROMEDIO'
        
        # Jerarquía 5: Costo estándar (añadido FASE 1C-3G-E2)
        if row.get('CostoEstandar') and float(row['CostoEstandar']) > 0:
            return float(row['CostoEstandar']), 'INSUMO_ESTANDAR'
    
    # Jerarquías 6-9: Futuras fuentes (compras, proveedor, override)
    # Por ahora no implementadas, retornar None
    
    return None, None


def obtener_rango_margen(costo: float, regla_id: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Obtiene el rango y margen aplicable para el costo dado.
    
    Returns:
        (rango_id, margen) o (None, None) si no hay rango configurado
    """
    conn = _get_conn_params()
    
    query = f"""
    SELECT TOP 1
        CAST(ReglaPrecioRangoID AS NVARCHAR(36)) as RangoID,
        MargenMultiplicador
    FROM Comercial_ReglasPrecioRangos
    WHERE ReglaPrecioID = '{regla_id}'
      AND Activo = 1
      AND {costo} >= LimiteInferior
      AND {costo} <= LimiteSuperior
    ORDER BY Orden
    """
    
    result = execute_sql_query(*conn, query)
    
    if result and len(result) > 0:
        return str(result[0]['RangoID']), float(result[0]['MargenMultiplicador'])
    
    return None, None


def obtener_tasa_impuesto(codigo_producto: str, server_id: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Obtiene la tasa de impuesto desde el modelo canónico.
    
    Returns:
        (tasa, mapeo_id) o (None, None) si no está configurado
    """
    conn = _get_conn_params()
    
    query = f"""
    SELECT 
        m.TasaEfectiva,
        CAST(m.MapeoProductoID AS NVARCHAR(36)) as MapeoID,
        m.EstadoFiscal
    FROM Comercial_ImpuestosMapeo m
    WHERE m.ServerID = '{server_id}'
      AND m.CodigoProducto = '{codigo_producto}'
    """
    
    result = execute_sql_query(*conn, query)
    
    if not result or len(result) == 0:
        return None, None
    
    row = result[0]
    
    # Si es NO_CONFIGURADO, retornar None
    if row['EstadoFiscal'] == 'NO_CONFIGURADO':
        return None, None
    
    tasa = row.get('TasaEfectiva')
    if tasa is not None:
        return float(tasa) / 100, str(row['MapeoID'])  # Convertir a decimal (16 -> 0.16)
    
    return None, None


def obtener_regla_vinos() -> Optional[Dict[str, Any]]:
    """Obtiene la regla de precio para vinos."""
    conn = _get_conn_params()
    
    query = """
    SELECT 
        CAST(ReglaPrecioID AS NVARCHAR(36)) as ReglaPrecioID,
        Codigo,
        NombreRegla,
        MetodoRedondeo,
        MultiploRedondeo
    FROM Comercial_ReglasPrecio
    WHERE Codigo = 'VINOS_RANGOS_MX'
      AND Activo = 1
      AND VigenciaDesde <= GETDATE()
      AND (VigenciaHasta IS NULL OR VigenciaHasta >= GETDATE())
    """
    
    result = execute_sql_query(*conn, query)
    
    if result and len(result) > 0:
        return dict(result[0])
    
    return None


def calcular_precio_sugerido_vino(
    codigo_producto: str,
    server_id: str,
    nombre_producto: Optional[str] = None
) -> ResultadoPrecioSugerido:
    """
    Calcula el precio sugerido para un producto de vino.
    
    ACLARACIÓN CONCEPTUAL:
        La tabla de rangos determina el PRECIO DE VENTA SUGERIDO,
        NO calcula el costo del vino.
    
    FÓRMULA:
        precio_base = CostoBaseVino * margen_multiplicador
        importe_impuesto = precio_base * tasa_impuesto_resuelta
        precio_con_impuesto = precio_base + importe_impuesto
        precio_sugerido = redondear(precio_con_impuesto, multiplo, metodo)
    
    Args:
        codigo_producto: Código del producto
        server_id: UUID del servidor
        nombre_producto: Nombre del producto (opcional)
    
    Returns:
        ResultadoPrecioSugerido con el cálculo o estado de error
    """
    resultado = ResultadoPrecioSugerido(
        codigo_producto=codigo_producto,
        server_id=server_id,
        nombre_producto=nombre_producto
    )
    
    try:
        # 1. Obtener regla de vinos
        regla = obtener_regla_vinos()
        if not regla:
            resultado.estado = EstadoCalculo.ERROR_CALCULO
            resultado.mensaje = "Regla de precio para vinos no encontrada"
            return resultado
        
        resultado.regla_precio_id = regla['ReglaPrecioID']
        resultado.metodo_redondeo = regla['MetodoRedondeo']
        resultado.multiplo_redondeo = regla['MultiploRedondeo']
        
        # 2. Obtener CostoBaseVino con jerarquía corregida
        costo, fuente = obtener_costo_base_vino(codigo_producto, server_id)
        
        if costo is None or costo <= 0:
            resultado.estado = EstadoCalculo.COSTO_BASE_NO_CONFIGURADO
            resultado.mensaje = "Producto sin costo base confiable. No se encontró CostoReceta > 0 ni costos en insumos."
            return resultado
        
        resultado.costo_base_vino = costo
        resultado.fuente_costo = fuente
        
        # 3. Obtener rango y margen (la tabla determina PRECIO SUGERIDO, no costo)
        rango_id, margen = obtener_rango_margen(costo, regla['ReglaPrecioID'])
        
        if rango_id is None:
            resultado.estado = EstadoCalculo.RANGO_NO_CONFIGURADO
            resultado.mensaje = f"CostoBaseVino ${costo:,.2f} fuera de rangos configurados. Verificar gap $4,000.01-$4,999.99."
            return resultado
        
        resultado.rango_id = rango_id
        resultado.margen_multiplicador = margen
        
        # 4. Obtener tasa de impuesto desde modelo canónico (NUNCA hardcodear 16%)
        tasa, mapeo_id = obtener_tasa_impuesto(codigo_producto, server_id)
        
        if tasa is None:
            resultado.estado = EstadoCalculo.IMPUESTO_NO_CONFIGURADO
            resultado.mensaje = "Producto sin tasa de impuesto configurada en modelo canónico."
            return resultado
        
        resultado.tasa_impuesto = tasa * 100  # Mostrar como porcentaje
        resultado.impuesto_mapeo_id = mapeo_id
        
        # 5. CALCULAR PRECIO SUGERIDO
        # precio_base = CostoBaseVino * margen_multiplicador
        precio_base = costo * margen
        resultado.precio_base = round(precio_base, 4)
        
        # importe_impuesto = precio_base * tasa_impuesto_resuelta
        importe_impuesto = precio_base * tasa
        resultado.importe_impuesto = round(importe_impuesto, 4)
        
        # precio_con_impuesto = precio_base + importe_impuesto
        precio_con_impuesto = precio_base + importe_impuesto
        resultado.precio_con_impuesto = round(precio_con_impuesto, 4)
        
        # precio_sugerido = redondear(precio_con_impuesto, multiplo, metodo)
        precio_sugerido = _redondear(
            precio_con_impuesto, 
            regla['MultiploRedondeo'], 
            regla['MetodoRedondeo']
        )
        resultado.precio_sugerido = precio_sugerido
        
        # 6. Estado exitoso
        resultado.estado = EstadoCalculo.CALCULADO
        resultado.mensaje = f"Precio calculado: CostoBase ${costo:,.2f} ({fuente}) × {margen} + IVA {tasa*100}% = ${precio_sugerido:,.2f}"
        
        return resultado
        
    except Exception as e:
        resultado.estado = EstadoCalculo.ERROR_CALCULO
        resultado.mensaje = f"Error en cálculo: {str(e)}"
        return resultado


def calcular_precios_vinos_masivo(
    server_id: Optional[str] = None,
    limit: int = 1000
) -> List[ResultadoPrecioSugerido]:
    """
    Calcula precios sugeridos para múltiples productos de vino.
    
    Args:
        server_id: Filtrar por servidor (opcional)
        limit: Límite de productos a procesar
    
    Returns:
        Lista de ResultadoPrecioSugerido
    """
    conn = _get_conn_params()
    
    # Familias de vino
    familias_vino = [
        'B CHAMPAGNES Y  COGNACS', 'B CHAMPAGNES Y COGNACS', 'B VINOS', 
        'B VINOS DE POSTRE', 'C CAVAS', 'CAVAS', 'CHAMPAGNES Y COGNACS',
        'VINOS BLANCOS', 'VINOS ESPUMOSOS/POSTRE', 'VINOS ROSADOS', 'VINOS TINTOS'
    ]
    familias_str = "', '".join(familias_vino)
    
    where_server = f"AND sp.ServerID = '{server_id}'" if server_id else ""
    
    query = f"""
    SELECT TOP {limit}
        sp.CodigoFuente,
        CAST(sp.ServerID AS NVARCHAR(36)) as ServerID,
        sp.Nombre
    FROM Sync_Productos sp
    WHERE sp.FamiliaNombre IN ('{familias_str}')
      {where_server}
    ORDER BY sp.Nombre
    """
    
    result = execute_sql_query(*conn, query)
    
    resultados = []
    for row in (result or []):
        resultado = calcular_precio_sugerido_vino(
            row['CodigoFuente'],
            row['ServerID'],
            row['Nombre']
        )
        resultados.append(resultado)
    
    return resultados


def get_estadisticas_calculo(server_id: Optional[str] = None) -> Dict[str, int]:
    """
    Obtiene estadísticas de cálculo de precios de vinos.
    
    Returns:
        Diccionario con conteos por estado
    """
    resultados = calcular_precios_vinos_masivo(server_id, limit=2000)
    
    stats = {
        'total': len(resultados),
        'CALCULADO': 0,
        'COSTO_BASE_NO_CONFIGURADO': 0,
        'IMPUESTO_NO_CONFIGURADO': 0,
        'RANGO_NO_CONFIGURADO': 0,
        'ERROR_CALCULO': 0
    }
    
    for r in resultados:
        stats[r.estado.value] = stats.get(r.estado.value, 0) + 1
    
    return stats
