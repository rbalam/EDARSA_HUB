"""
EDARSA HUB - Utilidades Compartidas
===================================
Funciones de utilidad usadas en múltiples módulos.

NOTA: Este archivo es parte del refactor modular.
Las utilidades actuales están dispersas en server.py.

USO FUTURO:
    from core.utils import format_currency, parse_date, sanitize_sql
"""

from typing import Optional, Any, List, Dict
from datetime import datetime, date, timedelta
from decimal import Decimal
import re


def format_currency(amount: float, currency: str = "MXN") -> str:
    """
    Formatea un monto como moneda.
    
    Args:
        amount: Monto numérico
        currency: Código de moneda (default MXN)
        
    Returns:
        String formateado (ej: "$1,234.56")
    """
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"


def format_percent(value: float, decimals: int = 1) -> str:
    """
    Formatea un valor como porcentaje.
    
    Args:
        value: Valor numérico (ej: 15.5 para 15.5%)
        decimals: Decimales a mostrar
        
    Returns:
        String formateado (ej: "+15.5%" o "-3.2%")
    """
    if value is None:
        return "0.0%"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def parse_date(date_str: str, format: str = "%Y-%m-%d") -> Optional[date]:
    """
    Parsea una fecha desde string.
    
    Args:
        date_str: Fecha en string
        format: Formato esperado
        
    Returns:
        Objeto date o None si falla
    """
    try:
        return datetime.strptime(date_str, format).date()
    except (ValueError, TypeError):
        return None


def date_to_sql_format(d: date, format_code: int = 101) -> str:
    """
    Convierte fecha a formato SQL Server.
    
    Args:
        d: Fecha
        format_code: Código de formato SQL Server (101 = MM/DD/YYYY)
        
    Returns:
        String de fecha en formato YYYYMMDD (seguro para SQL)
    """
    return d.strftime("%Y%m%d")


def get_month_range(year: int, month: int) -> tuple:
    """
    Obtiene el rango de fechas de un mes.
    
    Args:
        year: Año
        month: Mes (1-12)
        
    Returns:
        Tupla (fecha_inicio, fecha_fin)
    """
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    return first_day, last_day


def sanitize_for_sql(value: str) -> str:
    """
    Sanitiza un valor para uso en queries SQL.
    ADVERTENCIA: Preferir parámetros en lugar de concatenación.
    
    Args:
        value: Valor a sanitizar
        
    Returns:
        Valor sanitizado
    """
    if value is None:
        return ""
    # Escapar comillas simples
    return str(value).replace("'", "''")


def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """
    División segura que evita división por cero.
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor por defecto si denominador es 0
        
    Returns:
        Resultado de la división o valor por defecto
    """
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator


def calculate_variation(current: float, previous: float) -> float:
    """
    Calcula variación porcentual entre dos valores.
    
    Args:
        current: Valor actual
        previous: Valor anterior
        
    Returns:
        Variación porcentual (ej: 15.5 para +15.5%)
    """
    if previous == 0 or previous is None:
        return 0.0
    return round(((current - previous) / previous) * 100, 1)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Divide una lista en chunks de tamaño específico.
    
    Args:
        lst: Lista a dividir
        chunk_size: Tamaño de cada chunk
        
    Returns:
        Lista de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_get(dictionary: Dict, keys: str, default: Any = None) -> Any:
    """
    Obtiene un valor anidado de un diccionario usando notación de punto.
    
    Args:
        dictionary: Diccionario
        keys: Claves separadas por punto (ej: "a.b.c")
        default: Valor por defecto
        
    Returns:
        Valor encontrado o default
        
    Ejemplo:
        deep_get({"a": {"b": {"c": 1}}}, "a.b.c") -> 1
    """
    keys_list = keys.split('.')
    result = dictionary
    for key in keys_list:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    return result
