"""
EDARSA HUB - Utilidades de Filtros de Fecha
===========================================
Política transversal para manejo de rangos de fecha en queries SQL.

REGLAS OBLIGATORIAS:
1. Para columnas datetime: usar rango semiabierto [inicio, fin_exclusivo)
2. Para columnas string/entero YYYYMMDD: generar desde esta utilidad
3. Prohibido construir filtros de fecha manualmente en módulos

CREADO: 2026-04-19
MOTIVO: Eliminar bugs recurrentes por construcción incorrecta de rangos de fecha
"""

from datetime import datetime, date, timedelta
from typing import Tuple, Optional, Union
import calendar
import logging

logger = logging.getLogger(__name__)


class DateFilterPolicy:
    """
    Política centralizada para construcción de filtros de fecha.
    
    Uso:
        from core.utils.date_filters import DateFilterPolicy
        
        # Para queries con formato YYYYMMDD (SQL Server con config regional)
        fi, ff = DateFilterPolicy.to_yyyymmdd_range('2026-04-01', '2026-04-18')
        
        # Para validar rango
        if DateFilterPolicy.is_valid_range('2026-04-01', '2026-04-18'):
            ...
    """
    
    @staticmethod
    def parse_date(date_input: Union[str, date, datetime]) -> date:
        """
        Parsea una fecha desde múltiples formatos a objeto date.
        
        Formatos soportados:
        - 'YYYY-MM-DD' (ISO)
        - 'YYYYMMDD' (compacto)
        - date object
        - datetime object
        """
        if isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, date):
            return date_input
        elif isinstance(date_input, str):
            date_input = date_input.strip()
            if '-' in date_input:
                # Formato ISO: YYYY-MM-DD
                return datetime.strptime(date_input[:10], '%Y-%m-%d').date()
            elif len(date_input) == 8:
                # Formato compacto: YYYYMMDD
                return datetime.strptime(date_input, '%Y%m%d').date()
            else:
                raise ValueError(f"Formato de fecha no reconocido: {date_input}")
        else:
            raise TypeError(f"Tipo no soportado: {type(date_input)}")
    
    @staticmethod
    def to_iso(date_input: Union[str, date, datetime]) -> str:
        """Convierte cualquier fecha a formato ISO YYYY-MM-DD"""
        return DateFilterPolicy.parse_date(date_input).strftime('%Y-%m-%d')
    
    @staticmethod
    def to_yyyymmdd(date_input: Union[str, date, datetime]) -> str:
        """Convierte cualquier fecha a formato compacto YYYYMMDD"""
        return DateFilterPolicy.parse_date(date_input).strftime('%Y%m%d')
    
    @staticmethod
    def to_yyyymmdd_range(fecha_ini: str, fecha_fin: str) -> Tuple[str, str]:
        """
        Convierte un rango de fechas ISO a formato YYYYMMDD para SQL Server.
        
        Args:
            fecha_ini: Fecha inicio en formato YYYY-MM-DD
            fecha_fin: Fecha fin en formato YYYY-MM-DD
            
        Returns:
            Tuple (fi, ff) en formato YYYYMMDD
            
        Raises:
            ValueError: Si el rango es inválido (inicio > fin)
        """
        fi = DateFilterPolicy.to_yyyymmdd(fecha_ini)
        ff = DateFilterPolicy.to_yyyymmdd(fecha_fin)
        
        # Validar que el rango sea coherente
        if fi > ff:
            logger.warning(f"Rango de fechas inválido detectado: {fi} > {ff}")
            raise ValueError(f"Rango de fechas inválido: inicio ({fi}) > fin ({ff})")
        
        return fi, ff
    
    @staticmethod
    def is_valid_range(fecha_ini: str, fecha_fin: str) -> bool:
        """
        Valida que un rango de fechas sea coherente (inicio <= fin).
        
        Args:
            fecha_ini: Fecha inicio en cualquier formato soportado
            fecha_fin: Fecha fin en cualquier formato soportado
            
        Returns:
            True si el rango es válido, False si no
        """
        try:
            d_ini = DateFilterPolicy.parse_date(fecha_ini)
            d_fin = DateFilterPolicy.parse_date(fecha_fin)
            return d_ini <= d_fin
        except Exception as e:
            logger.warning(f"Error validando rango de fechas: {e}")
            return False
    
    @staticmethod
    def get_month_range(year: int, month: int) -> Tuple[str, str]:
        """
        Obtiene el rango completo de un mes en formato ISO.
        
        Args:
            year: Año
            month: Mes (1-12)
            
        Returns:
            Tuple (fecha_ini, fecha_fin) en formato YYYY-MM-DD
        """
        first_day = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        return (
            first_day.strftime('%Y-%m-%d'),
            date(year, month, last_day).strftime('%Y-%m-%d')
        )
    
    @staticmethod
    def get_period_until_day(year: int, month: int, day: int) -> Tuple[str, str]:
        """
        Obtiene el rango desde el inicio del mes hasta un día específico.
        
        Args:
            year: Año
            month: Mes (1-12)
            day: Día del mes
            
        Returns:
            Tuple (fecha_ini, fecha_fin) en formato YYYY-MM-DD
        """
        # Validar que el día sea válido para el mes
        max_day = calendar.monthrange(year, month)[1]
        day = min(day, max_day)
        
        return (
            f"{year}-{month:02d}-01",
            f"{year}-{month:02d}-{day:02d}"
        )
    
    @staticmethod
    def adjust_future_month(year: int, month: int, reference_date: Optional[date] = None) -> Tuple[int, int]:
        """
        Ajusta un mes futuro al mes actual si es necesario.
        
        Args:
            year: Año solicitado
            month: Mes solicitado
            reference_date: Fecha de referencia (default: hoy)
            
        Returns:
            Tuple (year, month) ajustados
        """
        if reference_date is None:
            reference_date = date.today()
        
        # Si el año es futuro, ajustar al año actual
        if year > reference_date.year:
            logger.info(f"Ajustando año futuro {year} al actual {reference_date.year}")
            year = reference_date.year
            month = reference_date.month
        # Si es el mismo año pero el mes es futuro, ajustar al mes actual
        elif year == reference_date.year and month > reference_date.month:
            logger.info(f"Ajustando mes futuro {month} al actual {reference_date.month}")
            month = reference_date.month
        
        return year, month
    
    @staticmethod
    def build_sql_date_filter(
        column_name: str,
        fecha_ini: str,
        fecha_fin: str,
        format_type: str = 'iso'
    ) -> str:
        """
        Construye un filtro SQL para rango de fechas.
        
        Args:
            column_name: Nombre de la columna SQL
            fecha_ini: Fecha inicio
            fecha_fin: Fecha fin
            format_type: 'iso' para YYYY-MM-DD, 'compact' para YYYYMMDD
            
        Returns:
            String SQL con el filtro WHERE
        """
        if format_type == 'compact':
            fi, ff = DateFilterPolicy.to_yyyymmdd_range(fecha_ini, fecha_fin)
            return f"{column_name} >= '{fi}' AND {column_name} <= '{ff}'"
        else:
            fi = DateFilterPolicy.to_iso(fecha_ini)
            ff = DateFilterPolicy.to_iso(fecha_fin)
            return f"{column_name} >= '{fi}' AND {column_name} <= '{ff}'"


# Alias para uso directo
parse_date = DateFilterPolicy.parse_date
to_iso = DateFilterPolicy.to_iso
to_yyyymmdd = DateFilterPolicy.to_yyyymmdd
to_yyyymmdd_range = DateFilterPolicy.to_yyyymmdd_range
is_valid_range = DateFilterPolicy.is_valid_range
get_month_range = DateFilterPolicy.get_month_range
adjust_future_month = DateFilterPolicy.adjust_future_month
