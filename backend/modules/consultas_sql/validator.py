"""
EDARSA HUB - Consultas SQL: Validador Estricto
==============================================
FASE 3: Validación de seguridad para consultas SQL.

REGLAS DE VALIDACIÓN:
1. Solo SELECT o WITH (CTEs) permitidos
2. Bloqueo de palabras peligrosas (DELETE, UPDATE, INSERT, etc.)
3. Bloqueo de múltiples statements (;)
4. Bloqueo de comentarios sospechosos (--, /*, */)
5. Validación de placeholders declarados
6. Validación de parámetros requeridos

NOTAS:
- Normaliza a mayúsculas antes de validar
- Normaliza espacios múltiples
- Evita falsos positivos con contexto
- Ante duda, bloquear
"""

import re
import logging
from typing import List, Optional, Set, Tuple
from datetime import datetime, timezone

from .models import ConsultaSQLValidationResult, ConsultaSQLParametro

logger = logging.getLogger(__name__)


class SQLValidator:
    """
    Validador estricto de SQL para el catálogo de consultas.
    Solo permite SELECT y WITH (CTEs).
    """
    
    # Palabras clave peligrosas (operaciones de escritura/admin)
    DANGEROUS_KEYWORDS = [
        'DELETE',
        'UPDATE',
        'INSERT',
        'DROP',
        'ALTER',
        'TRUNCATE',
        'EXEC',
        'EXECUTE',
        'CREATE',
        'MERGE',
        'GRANT',
        'REVOKE',
        'DENY',
        'BACKUP',
        'RESTORE',
        'DBCC',
        'KILL',
        'SHUTDOWN',
        'RECONFIGURE',
        'WAITFOR',
    ]
    
    # Prefijos de procedimientos peligrosos
    DANGEROUS_PREFIXES = [
        'xp_',
        'sp_',
        'fn_',
    ]
    
    # Expresiones regulares para detección
    COMMENT_PATTERNS = [
        r'/\*',      # Comentario de bloque apertura
        r'\*/',      # Comentario de bloque cierre
        r'--',       # Comentario de línea
    ]
    
    # Patrón para placeholders {param}
    PLACEHOLDER_PATTERN = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')
    
    # Patrón para detectar múltiples statements
    MULTI_STATEMENT_PATTERN = re.compile(r';\s*\S', re.MULTILINE)
    
    def __init__(self):
        """Inicializa el validador."""
        # Compilar patrones una vez
        self._dangerous_pattern = self._build_dangerous_pattern()
        self._prefix_patterns = [
            re.compile(rf'\b{prefix}', re.IGNORECASE) 
            for prefix in self.DANGEROUS_PREFIXES
        ]
    
    def _build_dangerous_pattern(self) -> re.Pattern:
        """
        Construye un patrón regex para palabras peligrosas.
        Usa word boundaries (\b) para evitar falsos positivos.
        """
        keywords = '|'.join(self.DANGEROUS_KEYWORDS)
        # \b = word boundary para evitar matches parciales
        # Ej: "SELECT" no hace match en "SELECTIVO"
        return re.compile(rf'\b({keywords})\b', re.IGNORECASE)
    
    def _normalize_sql(self, sql: str) -> str:
        """
        Normaliza el SQL para validación:
        - Convierte a mayúsculas
        - Normaliza espacios múltiples
        - Elimina espacios al inicio/fin
        """
        if not sql:
            return ""
        
        # Normalizar espacios
        normalized = re.sub(r'\s+', ' ', sql)
        normalized = normalized.strip()
        
        return normalized
    
    def _extract_placeholders(self, sql: str) -> Set[str]:
        """
        Extrae todos los placeholders {param} de la consulta.
        """
        matches = self.PLACEHOLDER_PATTERN.findall(sql)
        return set(matches)
    
    def _check_starts_with_select_or_with(self, normalized_sql: str) -> Tuple[bool, str]:
        """
        Verifica que la consulta inicie con SELECT o WITH.
        Returns: (is_valid, error_message)
        """
        upper_sql = normalized_sql.upper()
        
        # Remover espacios iniciales
        upper_sql = upper_sql.lstrip()
        
        if upper_sql.startswith('SELECT'):
            return (True, "")
        elif upper_sql.startswith('WITH'):
            # Verificar que WITH sea seguido de un CTE válido
            # Patrón básico: WITH nombre AS (...)
            if re.match(r'^WITH\s+\w+\s+AS\s*\(', upper_sql, re.IGNORECASE):
                return (True, "")
            else:
                return (False, "WITH clause malformado. Esperado: WITH nombre AS (...)")
        else:
            # Buscar qué keyword encontró
            first_word = upper_sql.split()[0] if upper_sql.split() else "EMPTY"
            return (False, f"Consulta debe iniciar con SELECT o WITH. Encontrado: {first_word}")
    
    def _check_dangerous_keywords(self, sql: str) -> List[Tuple[str, int]]:
        """
        Busca palabras peligrosas en el SQL.
        Returns: Lista de (keyword, posición)
        """
        found = []
        
        # Buscar keywords peligrosos
        for match in self._dangerous_pattern.finditer(sql):
            keyword = match.group(1).upper()
            position = match.start()
            found.append((keyword, position))
        
        return found
    
    def _check_dangerous_prefixes(self, sql: str) -> List[Tuple[str, int]]:
        """
        Busca prefijos de procedimientos peligrosos (xp_, sp_, etc.)
        Returns: Lista de (prefijo, posición)
        """
        found = []
        
        for pattern in self._prefix_patterns:
            for match in pattern.finditer(sql):
                prefix = match.group(0)
                position = match.start()
                found.append((prefix, position))
        
        return found
    
    def _check_comments(self, sql: str) -> List[Tuple[str, int]]:
        """
        Detecta comentarios SQL que podrían ocultar código malicioso.
        Returns: Lista de (tipo_comentario, posición)
        """
        found = []
        
        for pattern_str in self.COMMENT_PATTERNS:
            pattern = re.compile(pattern_str)
            for match in pattern.finditer(sql):
                found.append((match.group(0), match.start()))
        
        return found
    
    def _check_multiple_statements(self, sql: str) -> bool:
        """
        Detecta si hay múltiples statements (;) con contenido después.
        """
        # Buscar ; seguido de contenido no vacío
        return bool(self.MULTI_STATEMENT_PATTERN.search(sql))
    
    def validate_sql_text(
        self, 
        sql: str, 
        parametros_registrados: Optional[List[ConsultaSQLParametro]] = None,
        strict_mode: bool = True
    ) -> ConsultaSQLValidationResult:
        """
        Valida un texto SQL según las reglas de seguridad.
        
        Args:
            sql: Texto SQL a validar
            parametros_registrados: Lista de parámetros registrados en BD
            strict_mode: Si True, bloquea ante cualquier duda
            
        Returns:
            ConsultaSQLValidationResult con el resultado de validación
        """
        result = ConsultaSQLValidationResult(
            is_valid=True,
            validation_timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # 1. Verificar que hay contenido
        if not sql or not sql.strip():
            result.add_error(
                code="SQL_EMPTY",
                message="Consulta SQL vacía o nula",
                severity="CRITICAL"
            )
            return result
        
        # 2. Normalizar
        normalized = self._normalize_sql(sql)
        result.normalized_sql = normalized
        
        # 3. Verificar inicio con SELECT o WITH
        is_valid_start, error_msg = self._check_starts_with_select_or_with(normalized)
        if not is_valid_start:
            result.add_error(
                code="SQL_INVALID_START",
                message=error_msg,
                severity="CRITICAL"
            )
        
        # 4. Buscar palabras peligrosas
        dangerous = self._check_dangerous_keywords(sql)
        for keyword, pos in dangerous:
            result.add_error(
                code="SQL_DANGEROUS_KEYWORD",
                message=f"Palabra peligrosa detectada: {keyword}",
                severity="CRITICAL"
            )
        
        # 5. Buscar prefijos peligrosos (xp_, sp_)
        prefixes = self._check_dangerous_prefixes(sql)
        for prefix, pos in prefixes:
            result.add_error(
                code="SQL_DANGEROUS_PREFIX",
                message=f"Prefijo de procedimiento peligroso: {prefix}",
                severity="CRITICAL"
            )
        
        # 6. Detectar comentarios
        comments = self._check_comments(sql)
        for comment_type, pos in comments:
            if strict_mode:
                result.add_error(
                    code="SQL_COMMENT_DETECTED",
                    message=f"Comentario detectado: {comment_type} (puede ocultar código)",
                    severity="ERROR"
                )
            else:
                result.add_warning(
                    code="SQL_COMMENT_DETECTED",
                    message=f"Comentario detectado: {comment_type}"
                )
        
        # 7. Detectar múltiples statements
        if self._check_multiple_statements(sql):
            result.add_error(
                code="SQL_MULTIPLE_STATEMENTS",
                message="Múltiples statements detectados (separador ;)",
                severity="CRITICAL"
            )
        
        # 8. Extraer y validar placeholders
        placeholders = self._extract_placeholders(sql)
        result.detected_parameters = list(placeholders)
        
        # 9. Validar parámetros contra registro (si se proporciona)
        if parametros_registrados is not None:
            nombres_registrados = {p.nombre_parametro for p in parametros_registrados}
            
            # Placeholders sin registro
            no_registrados = placeholders - nombres_registrados
            for param in no_registrados:
                result.add_warning(
                    code="SQL_PARAM_NOT_REGISTERED",
                    message=f"Placeholder '{{{param}}}' no tiene parámetro registrado"
                )
            
            # Parámetros requeridos sin placeholder
            for param in parametros_registrados:
                if param.requerido and param.nombre_parametro not in placeholders:
                    result.add_warning(
                        code="SQL_PARAM_REQUIRED_MISSING",
                        message=f"Parámetro requerido '{param.nombre_parametro}' no tiene placeholder en SQL"
                    )
        
        return result
    
    def validate_catalog_query(
        self, 
        consulta_sql: str,
        solo_lectura: bool,
        activo: bool,
        config_origen: Optional[str] = None,
        parametros: Optional[List[ConsultaSQLParametro]] = None
    ) -> ConsultaSQLValidationResult:
        """
        Valida una consulta del catálogo aplicando reglas de negocio.
        
        Args:
            consulta_sql: Texto SQL de la consulta
            solo_lectura: Flag SoloLectura de la consulta
            activo: Flag Activo de la consulta
            config_origen: Origen de configuración
            parametros: Parámetros registrados
            
        Returns:
            ConsultaSQLValidationResult
        """
        # Validar SQL primero
        result = self.validate_sql_text(consulta_sql, parametros)
        
        # Validaciones adicionales de catálogo
        
        # Si no es SoloLectura, agregar warning crítico
        if not solo_lectura:
            result.add_error(
                code="CATALOG_NOT_READONLY",
                message="Consulta marcada como NO SoloLectura - no permitido para ejecución manual",
                severity="CRITICAL"
            )
        
        # Si no está activa, warning
        if not activo:
            result.add_warning(
                code="CATALOG_INACTIVE",
                message="Consulta marcada como inactiva"
            )
        
        # Verificar ConfigOrigen
        if not config_origen:
            result.add_warning(
                code="CATALOG_NO_ORIGEN",
                message="Consulta sin ConfigOrigen definido"
            )
        
        return result
    
    def quick_validate(self, sql: str) -> bool:
        """
        Validación rápida (solo check críticos).
        Útil para filtros de lista.
        
        Returns:
            True si pasa validación básica, False si tiene errores críticos
        """
        if not sql or not sql.strip():
            return False
        
        # Check inicio
        normalized = self._normalize_sql(sql).upper()
        if not (normalized.startswith('SELECT') or normalized.startswith('WITH')):
            return False
        
        # Check keywords peligrosos
        if self._check_dangerous_keywords(sql):
            return False
        
        # Check prefijos peligrosos
        if self._check_dangerous_prefixes(sql):
            return False
        
        # Check múltiples statements
        if self._check_multiple_statements(sql):
            return False
        
        return True


# Instancia singleton para uso global
_validator_instance: Optional[SQLValidator] = None


def get_validator() -> SQLValidator:
    """Obtiene la instancia singleton del validador."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = SQLValidator()
    return _validator_instance


__all__ = [
    'SQLValidator',
    'get_validator',
]
