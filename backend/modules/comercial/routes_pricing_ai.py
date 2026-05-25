"""
FASE 1C-3I-C: Endpoints de Integración GPT-5.2 para Pricing IA

Este módulo expone los endpoints de análisis IA para:
- Análisis de productos con justificación
- Sugerencia de productos comparables
- Generación de justificación de precios
- Análisis de benchmark competitivo

REGLAS:
- RBAC obligatorio
- GPT-5.2 sugiere, NO autoriza ni aplica precios
- NO modificar precios oficiales
- NO crear solicitudes automáticas
- NO hacer scraping web
- NO usar MongoDB
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from core.security import get_current_user
from core.rbac.middleware import require_permission

from modules.comercial.services.pricing_ai_service import (
    analizar_producto_con_ia,
    sugerir_comparables_con_ia,
    generar_justificacion_con_ia,
    analizar_benchmark_con_ia,
    obtener_analisis_ia,
    TipoAnalisisIA,
    EstadoAnalisisIA,
    ConfianzaIA,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comercial/pricing-ai", tags=["Comercial - Pricing IA GPT-5.2"])


# =============================================================================
# SCHEMAS DE REQUEST/RESPONSE
# =============================================================================

class AnalizarProductoRequest(BaseModel):
    """Request para analizar un producto con IA."""
    codigo_producto: str = Field(..., description="Código del producto")
    server_id: str = Field(..., description="UUID del servidor")
    empresa_id: int = Field(..., gt=0)
    unidad_negocio_id: int = Field(..., gt=0)
    margen_objetivo: float = Field(default=0.35, gt=0, lt=1, description="Margen objetivo (0.35 = 35%)")


class SugerirComparablesRequest(BaseModel):
    """Request para sugerir productos comparables."""
    codigo_producto: str = Field(..., description="Código del producto")
    server_id: str = Field(..., description="UUID del servidor")
    empresa_id: int = Field(..., gt=0)
    unidad_negocio_id: int = Field(..., gt=0)


class GenerarJustificacionRequest(BaseModel):
    """Request para generar justificación de precio."""
    codigo_producto: str = Field(..., description="Código del producto")
    server_id: str = Field(..., description="UUID del servidor")
    empresa_id: int = Field(..., gt=0)
    unidad_negocio_id: int = Field(..., gt=0)
    precio_propuesto: float = Field(..., gt=0, description="Precio propuesto a justificar")


class AnalizarBenchmarkRequest(BaseModel):
    """Request para analizar benchmark de unidad."""
    empresa_id: int = Field(..., gt=0)
    unidad_negocio_id: int = Field(..., gt=0)


class AnalisisIAResponse(BaseModel):
    """Respuesta genérica de análisis IA."""
    success: bool
    analisis_id: Optional[str] = None
    estado: str
    mensaje: str
    modelo_ia: str = "gpt-5.2"
    data: Optional[Dict[str, Any]] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "/analizar-producto",
    response_model=AnalisisIAResponse,
    summary="Analizar producto con GPT-5.2"
)
async def endpoint_analizar_producto(
    request: AnalizarProductoRequest,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.precios_sugeridos.ver_ia"))
):
    """
    Analiza un producto usando GPT-5.2 y genera justificación de precio.
    
    **IMPORTANTE:**
    - GPT-5.2 sugiere, NO autoriza ni aplica precios
    - NO modifica precios oficiales
    - NO crea solicitudes automáticas
    - Solo analiza datos de EDARSAHUB SQL
    
    **Retorna:**
    - Precio sugerido con justificación
    - Análisis de posicionamiento vs competencia
    - Nivel de confianza (ALTA/MEDIA/BAJA)
    - Recomendación de acción
    """
    usuario = current_user.get('email', 'sistema')
    
    logger.info(f"[PRICING-IA] Análisis producto {request.codigo_producto} por {usuario}")
    
    resultado = await analizar_producto_con_ia(
        codigo_producto=request.codigo_producto,
        server_id=request.server_id,
        empresa_id=request.empresa_id,
        unidad_negocio_id=request.unidad_negocio_id,
        usuario=usuario,
        margen_objetivo=request.margen_objetivo
    )
    
    return AnalisisIAResponse(
        success=resultado.get('success', False),
        analisis_id=resultado.get('analisis_id'),
        estado=resultado.get('estado', 'ERROR'),
        mensaje=resultado.get('mensaje', 'Sin mensaje'),
        modelo_ia='gpt-5.2',
        data={
            'producto': resultado.get('producto'),
            'precio_actual': resultado.get('precio_actual'),
            'precio_base_calculado': resultado.get('precio_base_calculado'),
            'precio_sugerido_ia': resultado.get('precio_sugerido_ia'),
            'margen_actual': resultado.get('margen_actual'),
            'margen_sugerido': resultado.get('margen_sugerido'),
            'justificacion': resultado.get('justificacion'),
            'posicionamiento': resultado.get('posicionamiento'),
            'recomendacion': resultado.get('recomendacion'),
            'observaciones': resultado.get('observaciones'),
            'confianza': resultado.get('confianza'),
            'requiere_revision': resultado.get('requiere_revision'),
        } if resultado.get('success') else None
    )


@router.post(
    "/sugerir-comparables",
    response_model=AnalisisIAResponse,
    summary="Sugerir productos comparables con GPT-5.2"
)
async def endpoint_sugerir_comparables(
    request: SugerirComparablesRequest,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.precios_sugeridos.ver_ia"))
):
    """
    Usa GPT-5.2 para sugerir productos comparables de la competencia.
    
    **IMPORTANTE:**
    - Solo analiza datos ya capturados en EDARSAHUB SQL
    - NO hace scraping web
    - Las sugerencias requieren validación humana
    
    **Retorna:**
    - Lista de productos comparables con similitud
    - Tipo de comparación (MISMO_PRODUCTO, PRODUCTO_SIMILAR, MISMA_CATEGORIA)
    - Observaciones del análisis
    """
    usuario = current_user.get('email', 'sistema')
    
    logger.info(f"[PRICING-IA] Sugerencia comparables {request.codigo_producto} por {usuario}")
    
    resultado = await sugerir_comparables_con_ia(
        codigo_producto=request.codigo_producto,
        server_id=request.server_id,
        empresa_id=request.empresa_id,
        unidad_negocio_id=request.unidad_negocio_id,
        usuario=usuario
    )
    
    return AnalisisIAResponse(
        success=resultado.get('success', False),
        analisis_id=resultado.get('analisis_id'),
        estado=resultado.get('estado', 'ERROR'),
        mensaje=resultado.get('mensaje', 'Sin mensaje'),
        modelo_ia='gpt-5.2',
        data={
            'producto': resultado.get('producto'),
            'comparables': resultado.get('comparables', []),
            'items_analizados': resultado.get('items_analizados'),
            'observaciones': resultado.get('observaciones'),
            'requiere_validacion': resultado.get('requiere_validacion', True),
        } if resultado.get('success') else None
    )


@router.post(
    "/generar-justificacion",
    response_model=AnalisisIAResponse,
    summary="Generar justificación de precio con GPT-5.2"
)
async def endpoint_generar_justificacion(
    request: GenerarJustificacionRequest,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.precios_sugeridos.ver_ia"))
):
    """
    Genera justificación comercial para un precio propuesto usando GPT-5.2.
    
    **IMPORTANTE:**
    - Útil para solicitudes de cambio de precio
    - NO modifica precios
    - NO crea solicitudes automáticas
    
    **Retorna:**
    - Justificación formal del precio
    - Puntos clave
    - Nivel de riesgo
    - Recomendación (APROBAR/REVISAR/RECHAZAR)
    """
    usuario = current_user.get('email', 'sistema')
    
    logger.info(f"[PRICING-IA] Justificación {request.codigo_producto} precio ${request.precio_propuesto} por {usuario}")
    
    resultado = await generar_justificacion_con_ia(
        codigo_producto=request.codigo_producto,
        server_id=request.server_id,
        empresa_id=request.empresa_id,
        unidad_negocio_id=request.unidad_negocio_id,
        precio_propuesto=request.precio_propuesto,
        usuario=usuario
    )
    
    return AnalisisIAResponse(
        success=resultado.get('success', False),
        analisis_id=resultado.get('analisis_id'),
        estado=resultado.get('estado', 'ERROR'),
        mensaje=resultado.get('mensaje', 'Sin mensaje'),
        modelo_ia='gpt-5.2',
        data={
            'producto': resultado.get('producto'),
            'precio_actual': resultado.get('precio_actual'),
            'precio_propuesto': resultado.get('precio_propuesto'),
            'cambio_porcentaje': resultado.get('cambio_porcentaje'),
            'margen_propuesto': resultado.get('margen_propuesto'),
            'justificacion': resultado.get('justificacion'),
            'puntos_clave': resultado.get('puntos_clave', []),
            'riesgo': resultado.get('riesgo'),
            'recomendacion': resultado.get('recomendacion'),
        } if resultado.get('success') else None
    )


@router.post(
    "/analizar-benchmark",
    response_model=AnalisisIAResponse,
    summary="Analizar benchmark competitivo con GPT-5.2"
)
async def endpoint_analizar_benchmark(
    request: AnalizarBenchmarkRequest,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.benchmark.ver"))
):
    """
    Analiza el benchmark completo de una unidad con GPT-5.2.
    
    **IMPORTANTE:**
    - Genera insights sobre posicionamiento general vs competencia
    - NO modifica precios
    - Solo usa datos ya capturados en EDARSAHUB SQL
    
    **Retorna:**
    - Resumen ejecutivo
    - Posicionamiento de mercado
    - Oportunidades y riesgos
    - Recomendaciones estratégicas
    """
    usuario = current_user.get('email', 'sistema')
    
    logger.info(f"[PRICING-IA] Análisis benchmark unidad {request.unidad_negocio_id} por {usuario}")
    
    resultado = await analizar_benchmark_con_ia(
        unidad_negocio_id=request.unidad_negocio_id,
        empresa_id=request.empresa_id,
        usuario=usuario
    )
    
    return AnalisisIAResponse(
        success=resultado.get('success', False),
        analisis_id=resultado.get('analisis_id'),
        estado=resultado.get('estado', 'ERROR'),
        mensaje=resultado.get('mensaje', 'Sin mensaje'),
        modelo_ia='gpt-5.2',
        data={
            'unidad': resultado.get('unidad'),
            'resumen': resultado.get('resumen'),
            'posicionamiento': resultado.get('posicionamiento'),
            'oportunidades': resultado.get('oportunidades', []),
            'riesgos': resultado.get('riesgos', []),
            'recomendaciones': resultado.get('recomendaciones', []),
            'prioridad': resultado.get('prioridad'),
            'areas_revisar': resultado.get('areas_revisar', []),
            'estadisticas': resultado.get('estadisticas'),
        } if resultado.get('success') else None
    )


@router.get(
    "/analisis/{analisis_id}",
    summary="Obtener análisis IA por ID"
)
async def endpoint_obtener_analisis(
    analisis_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.precios_sugeridos.ver_ia"))
):
    """
    Obtiene un análisis IA previamente generado por su ID.
    
    **Incluye:**
    - Datos de entrada utilizados
    - Respuesta completa de la IA
    - Justificación generada
    - Nivel de confianza
    - Estado del análisis
    """
    analisis = obtener_analisis_ia(analisis_id)
    
    if not analisis:
        raise HTTPException(
            status_code=404,
            detail=f"Análisis {analisis_id} no encontrado"
        )
    
    return {
        'success': True,
        'analisis': analisis,
        'mensaje': 'Análisis recuperado correctamente'
    }


@router.get(
    "/health",
    summary="Health check del módulo Pricing IA GPT-5.2"
)
async def health_check_ia():
    """
    Verifica que el módulo de Pricing IA con GPT-5.2 está operativo.
    """
    import os
    
    llm_key_configured = bool(os.environ.get('EMERGENT_LLM_KEY'))
    
    return {
        "modulo": "comercial-pricing-ia-gpt52",
        "fase": "1C-3I-C",
        "estado": "operativo" if llm_key_configured else "sin_configurar",
        "modelo_ia": "gpt-5.2",
        "proveedor": "OpenAI via Emergent LLM Key",
        "llm_key_configurada": llm_key_configured,
        "endpoints": {
            "analizar_producto": "activo",
            "sugerir_comparables": "activo",
            "generar_justificacion": "activo",
            "analizar_benchmark": "activo",
            "obtener_analisis": "activo"
        },
        "reglas": {
            "ia_sugiere": True,
            "ia_autoriza": False,
            "ia_aplica_precios": False,
            "scraping_web": False,
            "mongodb": False,
        }
    }
