"""
CENTRO DE CONTROL EDARSA - Sistema de Alertas
==============================================
Gestión de alertas automáticas basadas en eventos del sistema.

TIPOS DE ALERTA:
- REGRESSION: Regresión detectada en un módulo
- SOURCE_DOWN: Fuente de datos caída
- MODULE_DEGRADED: Módulo en estado degradado
- MODULE_CRITICAL: Módulo en estado crítico
- THRESHOLD_BREACH: Umbral de métrica excedido

SEVERIDADES:
- critical: Requiere acción inmediata
- high: Requiere atención urgente
- medium: Requiere revisión
- low: Informativo

CREADO: 2026-04-19
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Tipos de alerta"""
    REGRESSION = "regression"
    SOURCE_DOWN = "source_down"
    MODULE_DEGRADED = "module_degraded"
    MODULE_CRITICAL = "module_critical"
    THRESHOLD_BREACH = "threshold_breach"
    SYSTEM_ERROR = "system_error"


class AlertSeverity(Enum):
    """Severidad de alerta"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Alert:
    """Estructura de una alerta"""
    id: str
    tipo: AlertType
    severidad: AlertSeverity
    titulo: str
    modulo: str
    detalle: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reconocida: bool = False
    reconocida_por: Optional[str] = None
    reconocida_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "severidad": self.severidad.value,
            "titulo": self.titulo,
            "modulo": self.modulo,
            "detalle": self.detalle,
            "timestamp": self.timestamp.isoformat(),
            "reconocida": self.reconocida,
            "reconocida_por": self.reconocida_por,
            "reconocida_at": self.reconocida_at.isoformat() if self.reconocida_at else None,
            "metadata": self.metadata
        }


class AlertManager:
    """
    Gestor de alertas del Centro de Control.
    
    Uso:
        manager = AlertManager()
        manager.crear_alerta(
            tipo=AlertType.REGRESSION,
            severidad=AlertSeverity.CRITICAL,
            titulo="Ventas en $0",
            modulo="tablero_ejecutivo",
            detalle="El tablero muestra ventas en $0 con unidades online"
        )
    """
    
    def __init__(self, max_alertas: int = 100):
        self._alertas: List[Alert] = []
        self._max_alertas = max_alertas
        self._contador = 0
    
    def _generar_id(self) -> str:
        """Genera ID único para alerta"""
        self._contador += 1
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"ALRT-{ts}-{self._contador:04d}"
    
    def crear_alerta(
        self,
        tipo: AlertType,
        severidad: AlertSeverity,
        titulo: str,
        modulo: str,
        detalle: str,
        metadata: Dict[str, Any] = None
    ) -> Alert:
        """Crea y registra una nueva alerta"""
        alerta = Alert(
            id=self._generar_id(),
            tipo=tipo,
            severidad=severidad,
            titulo=titulo,
            modulo=modulo,
            detalle=detalle,
            metadata=metadata or {}
        )
        
        self._alertas.insert(0, alerta)
        
        # Mantener límite
        if len(self._alertas) > self._max_alertas:
            self._alertas = self._alertas[:self._max_alertas]
        
        logger.info(
            f"[ALERTA] {severidad.value.upper()} - {titulo} | "
            f"Módulo: {modulo} | ID: {alerta.id}"
        )
        
        return alerta
    
    def obtener_alertas(
        self,
        solo_activas: bool = True,
        tipo: Optional[AlertType] = None,
        modulo: Optional[str] = None,
        limite: int = 50
    ) -> List[Alert]:
        """Obtiene alertas con filtros opcionales"""
        alertas = self._alertas
        
        if solo_activas:
            alertas = [a for a in alertas if not a.reconocida]
        
        if tipo:
            alertas = [a for a in alertas if a.tipo == tipo]
        
        if modulo:
            alertas = [a for a in alertas if a.modulo == modulo]
        
        return alertas[:limite]
    
    def reconocer_alerta(
        self,
        alert_id: str,
        usuario: str,
        comentario: Optional[str] = None
    ) -> Optional[Alert]:
        """Reconoce una alerta"""
        for alerta in self._alertas:
            if alerta.id == alert_id:
                alerta.reconocida = True
                alerta.reconocida_por = usuario
                alerta.reconocida_at = datetime.now(timezone.utc)
                if comentario:
                    alerta.metadata["comentario_ack"] = comentario
                
                logger.info(f"[ALERTA] Reconocida: {alert_id} por {usuario}")
                return alerta
        
        return None
    
    def obtener_resumen(self) -> Dict[str, Any]:
        """Obtiene resumen de alertas"""
        activas = [a for a in self._alertas if not a.reconocida]
        
        return {
            "total": len(self._alertas),
            "activas": len(activas),
            "por_severidad": {
                "critical": len([a for a in activas if a.severidad == AlertSeverity.CRITICAL]),
                "high": len([a for a in activas if a.severidad == AlertSeverity.HIGH]),
                "medium": len([a for a in activas if a.severidad == AlertSeverity.MEDIUM]),
                "low": len([a for a in activas if a.severidad == AlertSeverity.LOW])
            },
            "por_tipo": {
                tipo.value: len([a for a in activas if a.tipo == tipo])
                for tipo in AlertType
            }
        }
    
    def limpiar_alertas_antiguas(self, dias: int = 7):
        """Elimina alertas reconocidas más antiguas que X días"""
        limite = datetime.now(timezone.utc) - timedelta(days=dias)
        
        antes = len(self._alertas)
        self._alertas = [
            a for a in self._alertas 
            if not a.reconocida or a.timestamp > limite
        ]
        despues = len(self._alertas)
        
        if antes != despues:
            logger.info(f"[ALERTA] Limpieza: {antes - despues} alertas eliminadas")


# Instancia singleton
alert_manager = AlertManager()


# Importar timedelta para el método limpiar_alertas_antiguas
from datetime import timedelta
