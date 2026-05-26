"""
EDARSA HUB - Text Normalizer
============================
Utilidades para normalizar texto y prevenir duplicados por caracteres especiales.

Uso principal: Normalizar nombres de unidades de negocio durante sincronizaciones
para evitar duplicados por acentos (ej: "MÉRIDA" vs "MERIDA").

MÁXIMAS CUMPLIDAS:
- SQL-First: Normalización aplicada antes de guardar en EDARSAHUB
- Idempotencia: La normalización produce resultados consistentes
- Trazabilidad: Log de cambios aplicados
"""

import unicodedata
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def remove_accents(text: str) -> str:
    """
    Elimina acentos y diacríticos de un texto.
    
    Ejemplos:
        - "MÉRIDA" -> "MERIDA"
        - "QUERÉTARO" -> "QUERETARO"
        - "130° MÉRIDA" -> "130° MERIDA"
        - "NIÑO" -> "NINO"
    
    Args:
        text: Texto con posibles acentos
        
    Returns:
        Texto sin acentos, preservando mayúsculas/minúsculas
    """
    if not text:
        return text
    
    # NFD descompone los caracteres con acentos en base + diacrítico
    # Luego filtramos los diacríticos (categoría Mn = Mark, Nonspacing)
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(
        char for char in normalized 
        if unicodedata.category(char) != 'Mn'
    )
    return without_accents


def normalize_unidad_nombre(nombre: str, log_changes: bool = True) -> str:
    """
    Normaliza el nombre de una unidad de negocio para consistencia en EDARSAHUB.
    
    Operaciones:
    1. Elimina acentos (MÉRIDA -> MERIDA)
    2. Preserva caracteres especiales permitidos (°, -, _, espacios)
    3. NO convierte a mayúsculas (preserva el formato original)
    
    Args:
        nombre: Nombre de la unidad de negocio
        log_changes: Si True, loggea cuando hay cambios
        
    Returns:
        Nombre normalizado sin acentos
    """
    if not nombre:
        return nombre
    
    original = nombre
    normalized = remove_accents(nombre)
    
    if log_changes and original != normalized:
        logger.info(f"[TEXT_NORMALIZE] Unidad normalizada: '{original}' -> '{normalized}'")
    
    return normalized


def normalize_for_comparison(text: str) -> str:
    """
    Normaliza texto para comparaciones case-insensitive y sin acentos.
    
    Útil para buscar si un texto ya existe con variantes de acentos.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto en mayúsculas sin acentos
    """
    if not text:
        return ""
    return remove_accents(text).upper().strip()


def is_same_unidad(nombre1: str, nombre2: str) -> bool:
    """
    Compara dos nombres de unidad ignorando acentos y mayúsculas.
    
    Ejemplos:
        - is_same_unidad("130° MÉRIDA", "130° MERIDA") -> True
        - is_same_unidad("Cienfuegos", "CIENFUEGOS") -> True
        
    Args:
        nombre1: Primer nombre
        nombre2: Segundo nombre
        
    Returns:
        True si son el mismo nombre (ignorando acentos y case)
    """
    return normalize_for_comparison(nombre1) == normalize_for_comparison(nombre2)


# =============================================================================
# CATÁLOGO DE NOMBRES CANÓNICOS (EDARSAHUB)
# =============================================================================
# Estos son los nombres oficiales sin acentos que deben usarse en todo el sistema

NOMBRES_CANONICOS = {
    '130MID': '130° MERIDA',      # Sin acento
    '130QRO': '130° QUERETARO',   # Sin acento  
    'CIENFUEGOS': 'CIENFUEGOS',
    'ESTELAR': 'LA ESTELAR',
    'ORIGEN': 'ORIGEN',
}


def get_nombre_canonico(unidad_id: str) -> Optional[str]:
    """
    Obtiene el nombre canónico oficial para una unidad de negocio.
    
    Args:
        unidad_id: Código de la unidad (ej: '130MID')
        
    Returns:
        Nombre canónico sin acentos, o None si no está en el catálogo
    """
    return NOMBRES_CANONICOS.get(unidad_id.upper())


def ensure_canonical_name(unidad_id: str, nombre_actual: str) -> str:
    """
    Asegura que el nombre de unidad sea el canónico.
    
    Si hay un nombre canónico definido, lo usa. Si no, normaliza el actual.
    
    Args:
        unidad_id: Código de la unidad
        nombre_actual: Nombre actual (puede tener acentos)
        
    Returns:
        Nombre canónico o normalizado
    """
    canonico = get_nombre_canonico(unidad_id)
    if canonico:
        return canonico
    return normalize_unidad_nombre(nombre_actual)
