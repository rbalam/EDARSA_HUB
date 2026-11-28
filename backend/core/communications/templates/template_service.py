from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Template Service
=============================
Subfase 2B.5 - Gestión e interpolación de templates de mensajes.

Funcionalidades:
- Carga de templates desde BD
- Interpolación segura de variables
- Validación de variables requeridas
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# TEMPLATES DEFAULT (Se cargan si no hay en BD)
# =============================================================================

DEFAULT_TEMPLATES = {
    "inventarios_asignacion_tarea": {
        "codigo": "inventarios_asignacion_tarea",
        "nombre": "Asignación de Tarea",
        "template_texto": "EDARSA HUB: Tienes una tarea asignada del folio {{folio}} en {{sucursal}}. Fecha limite: {{fecha_limite}}. Ingresa al sistema para atenderla.",
        "variables": ["folio", "sucursal", "fecha_limite"]
    },
    "inventarios_diferencia_detectada": {
        "codigo": "inventarios_diferencia_detectada",
        "nombre": "Diferencia Detectada",
        "template_texto": "EDARSA HUB: Se detecto una diferencia relevante en el folio {{folio}} de {{sucursal}}. Impacto: ${{impacto_financiero}}. Requiere justificacion.",
        "variables": ["folio", "sucursal", "impacto_financiero"]
    },
    "inventarios_sla_por_vencer": {
        "codigo": "inventarios_sla_por_vencer",
        "nombre": "SLA Por Vencer",
        "template_texto": "EDARSA HUB: El caso {{folio}} en {{sucursal}} esta por vencer. Etapa: {{evento}}. Limite: {{fecha_limite}}. Horas restantes: {{horas_restantes}}.",
        "variables": ["folio", "sucursal", "evento", "fecha_limite", "horas_restantes"]
    },
    "inventarios_sla_vencido": {
        "codigo": "inventarios_sla_vencido",
        "nombre": "SLA Vencido",
        "template_texto": "EDARSA HUB: El caso {{folio}} en {{sucursal}} vencio su SLA en la etapa {{evento}}. Se requiere atencion inmediata.",
        "variables": ["folio", "sucursal", "evento"]
    },
    "inventarios_sla_escalado": {
        "codigo": "inventarios_sla_escalado",
        "nombre": "SLA Escalado",
        "template_texto": "EDARSA HUB: ESCALAMIENTO - El caso {{folio}} en {{sucursal}} fue escalado por incumplimiento SLA en {{evento}}. Tiempo excedido: {{porcentaje_excedido}}%. Revisar de inmediato.",
        "variables": ["folio", "sucursal", "evento", "porcentaje_excedido"]
    },
    "inventarios_justificacion_rechazada": {
        "codigo": "inventarios_justificacion_rechazada",
        "nombre": "Justificación Rechazada",
        "template_texto": "EDARSA HUB: Tu justificacion para el folio {{folio}} en {{sucursal}} fue rechazada. Motivo: {{motivo}}. Debes corregirla.",
        "variables": ["folio", "sucursal", "motivo"]
    },
    "inventarios_decision_auditoria": {
        "codigo": "inventarios_decision_auditoria",
        "nombre": "Decisión de Auditoría",
        "template_texto": "EDARSA HUB: El folio {{folio}} en {{sucursal}} ha sido {{decision}} por auditoria. {{comentario}}",
        "variables": ["folio", "sucursal", "decision", "comentario"]
    },
    "inventarios_cierre_workflow": {
        "codigo": "inventarios_cierre_workflow",
        "nombre": "Cierre de Workflow",
        "template_texto": "EDARSA HUB: El caso {{folio}} en {{sucursal}} ha sido cerrado. Estado final: {{estado_final}}. Gracias por tu atencion.",
        "variables": ["folio", "sucursal", "estado_final"]
    },
    "inventarios_responsabilidad_propuesta": {
        "codigo": "inventarios_responsabilidad_propuesta",
        "nombre": "Responsabilidad Económica Propuesta",
        "template_texto": "EDARSA HUB: Se ha propuesto un cargo de ${{monto}} por diferencias en el folio {{folio}} de {{sucursal}}. Puedes disputar o aceptar.",
        "variables": ["monto", "folio", "sucursal"]
    },
    "inventarios_responsabilidad_aprobada": {
        "codigo": "inventarios_responsabilidad_aprobada",
        "nombre": "Responsabilidad Económica Aprobada",
        "template_texto": "EDARSA HUB: El cargo de ${{monto}} por folio {{folio}} en {{sucursal}} ha sido aprobado por {{aprobador}}.",
        "variables": ["monto", "folio", "sucursal", "aprobador"]
    }
}


class TemplateService:
    """
    Servicio de gestión de templates de notificación.
    """
    
    def __init__(self, db):
        self.db = db
        self.template_collection = None  # SQL-FIRST P4C: notification_templates Mongo neutralizado
        self._cache: Dict[str, Dict] = {}
    
    async def get_template(
        self,
        codigo: str,
        canal: str = "whatsapp"
    ) -> Optional[Dict]:
        """
        Obtiene un template por código y canal.
        
        Prioridad:
        1. Cache en memoria
        2. Base de datos
        3. Template default
        
        Args:
            codigo: Código del template
            canal: Canal (whatsapp, email, etc.)
            
        Returns:
            Template o None
        """
        cache_key = f"{canal}:{codigo}"
        
        # 1. Buscar en cache
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 2. Gate 5D: leer template SQL canonico antes del fallback default.
        try:
            from ..notifications.repository import NotificationRepository
            template = await NotificationRepository(self.db).get_template(canal, codigo)
        except Exception as exc:
            logger.warning("No se pudo leer template SQL %s/%s: %s", canal, codigo, type(exc).__name__)
            template = None
        if template:
            self._cache[cache_key] = template
            return template

        # 3. Usar default
        if codigo in DEFAULT_TEMPLATES:
            default = DEFAULT_TEMPLATES[codigo].copy()
            default["canal"] = canal
            default["activo"] = True
            default["idioma"] = "es"
            default["version"] = 1
            self._cache[cache_key] = default
            return default
        
        logger.warning(f"Template no encontrado: {codigo} (canal={canal})")
        return None
    
    def render(
        self,
        template_texto: str,
        variables: Dict[str, Any],
        strict: bool = False
    ) -> str:
        """
        Renderiza un template interpolando variables.
        
        Usa sintaxis {{variable}}.
        
        Args:
            template_texto: Texto del template
            variables: Dict con valores de variables
            strict: Si True, lanza error si falta variable
            
        Returns:
            Texto renderizado
        """
        resultado = template_texto
        
        # Encontrar todas las variables en el template
        pattern = r'\{\{(\w+)\}\}'
        found_vars = re.findall(pattern, template_texto)
        
        for var_name in found_vars:
            placeholder = f"{{{{{var_name}}}}}"
            value = variables.get(var_name)
            
            if value is None:
                if strict:
                    raise ValueError(f"Variable requerida no proporcionada: {var_name}")
                # Dejar el placeholder si no hay valor
                value = f"[{var_name}]"
            
            # Formatear según tipo
            if isinstance(value, (int, float)):
                # Formatear números con comas para miles
                if isinstance(value, float):
                    formatted_value = f"{value:,.2f}"
                else:
                    formatted_value = f"{value:,}"
            elif isinstance(value, datetime):
                formatted_value = value.strftime("%d/%m/%Y %H:%M")
            else:
                formatted_value = str(value)
            
            resultado = resultado.replace(placeholder, formatted_value)
        
        return resultado
    
    async def render_template(
        self,
        codigo: str,
        variables: Dict[str, Any],
        canal: str = "whatsapp",
        strict: bool = False
    ) -> Optional[str]:
        """
        Obtiene y renderiza un template.
        
        Args:
            codigo: Código del template
            variables: Valores para interpolación
            canal: Canal del template
            strict: Validación estricta de variables
            
        Returns:
            Mensaje renderizado o None si no existe template
        """
        template = await self.get_template(codigo, canal)
        if not template:
            return None
        
        return self.render(template["template_texto"], variables, strict)
    
    def validate_variables(
        self,
        template: Dict,
        variables: Dict[str, Any]
    ) -> Dict:
        """
        Valida que todas las variables requeridas estén presentes.
        
        Returns:
            Dict con:
            - valid: bool
            - missing: List[str]
            - extra: List[str]
        """
        required = set(template.get("variables", []))
        provided = set(variables.keys())
        
        missing = required - provided
        extra = provided - required
        
        return {
            "valid": len(missing) == 0,
            "missing": list(missing),
            "extra": list(extra)
        }
    
    def invalidate_cache(self, codigo: Optional[str] = None, canal: Optional[str] = None):
        """
        Invalida cache de templates.
        
        Args:
            codigo: Código específico a invalidar (None = todos)
            canal: Canal específico (None = todos)
        """
        if codigo is None and canal is None:
            self._cache = {}
            return
        
        if codigo and canal:
            cache_key = f"{canal}:{codigo}"
            self._cache.pop(cache_key, None)
        elif codigo:
            # Invalidar para todos los canales
            keys_to_remove = [k for k in self._cache if k.endswith(f":{codigo}")]
            for k in keys_to_remove:
                del self._cache[k]
        elif canal:
            # Invalidar todos los templates del canal
            keys_to_remove = [k for k in self._cache if k.startswith(f"{canal}:")]
            for k in keys_to_remove:
                del self._cache[k]
    
    async def seed_default_templates(self):
        """
        Siembra los templates default en la BD si no existen.
        """
        # SQL-FIRST P4C: seed legacy de templates neutralizado.
        logger.info("Seed templates omitido en SQL-first; se usan DEFAULT_TEMPLATES en memoria")
        return {"success": True, "sql_first_neutralized": True}


# =============================================================================
# SINGLETON
# =============================================================================

_template_service: Optional[TemplateService] = None


def get_template_service(db) -> TemplateService:
    """Obtiene instancia del servicio de templates."""
    global _template_service
    if _template_service is None:
        _template_service = TemplateService(db)
    return _template_service


def reset_template_service():
    """Reset para testing."""
    global _template_service
    _template_service = None
