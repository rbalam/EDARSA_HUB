from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Deduplication Service
==================================
Subfase 2B.5 - Control de duplicidad de notificaciones.

Evita mensajes duplicados por:
- Ejecuciones repetidas del job
- Múltiples transiciones cercanas
- Reintentos automáticos
"""

from typing import Optional, Dict, Tuple
from datetime import datetime, timezone, timedelta
import logging
import hashlib

logger = logging.getLogger(__name__)


class DeduplicationService:
    """
    Servicio de control de duplicidad para notificaciones.
    
    Criterios de duplicidad:
    - evento_notificacion
    - referencia_id
    - workflow_id
    - destinatario
    - template_codigo
    - ventana de tiempo configurable
    """
    
    def __init__(self, db):
        self.db = db
        self.log_collection = None  # SQL-FIRST P4C: notification_log Mongo neutralizado
        self.default_window_minutes = 60
    
    def _generate_dedup_key(
        self,
        evento: str,
        referencia_id: str,
        workflow_id: str,
        destinatario: str,
        template_codigo: str
    ) -> str:
        """
        Genera una clave única para deduplicación.
        
        Args:
            evento: Tipo de evento
            referencia_id: ID de referencia
            workflow_id: ID del workflow
            destinatario: Teléfono/email del destinatario
            template_codigo: Código del template
            
        Returns:
            Hash MD5 de la combinación
        """
        key_parts = [
            evento or "",
            referencia_id or "",
            workflow_id or "",
            destinatario or "",
            template_codigo or ""
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    async def is_duplicate(
        self,
        evento: str,
        referencia_id: Optional[str],
        workflow_id: Optional[str],
        destinatario: str,
        template_codigo: str,
        ventana_minutos: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si una notificación es duplicada.
        
        Args:
            evento: Tipo de evento
            referencia_id: ID de referencia
            workflow_id: ID del workflow
            destinatario: Teléfono/email
            template_codigo: Código del template
            ventana_minutos: Ventana de tiempo para considerar duplicado
            
        Returns:
            Tuple (es_duplicado, log_id_existente)
        """
        window = ventana_minutos or self.default_window_minutes
        ahora = datetime.now(timezone.utc)
        inicio_ventana = (ahora - timedelta(minutes=window)).isoformat()
        
        # Buscar envío exitoso reciente con los mismos criterios
        filtro = {
            "evento_negocio": evento,
            "destinatario": destinatario,
            "template_codigo": template_codigo,
            "estado_envio": {"$in": ["enviado", "entregado"]},
            "fecha_intento": {"$gte": inicio_ventana}
        }
        
        # Agregar filtros opcionales si existen
        if referencia_id:
            filtro["referencia_id"] = referencia_id
        if workflow_id:
            filtro["workflow_id"] = workflow_id
        
        # SQL-FIRST P4C: buscar envío reciente en dbo.Operativo_Notificaciones_Log
        try:
            from modules.compras.sync_service import get_edarsahub_connection
            conn = get_edarsahub_connection()
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT TOP 1 NotificacionID
                FROM dbo.Operativo_Notificaciones_Log
                WHERE TipoEvento=%s
                  AND (Destinatario=%s OR DestinatarioEmail=%s)
                  AND Estado IN ('enviado','entregado','ENVIADO','ENTREGADO')
                  AND FechaEnvio >= DATEADD(minute, -%s, GETUTCDATE())
                ORDER BY FechaEnvio DESC
            """, (evento, destinatario, destinatario, int(window)))
            existente = cur.fetchone()
            conn.close()
            if existente:
                return True, existente.get("NotificacionID")
        except Exception as e:
            logger.warning(f"SQL-FIRST P4C dedup fallback: {e}")

        return False, None
    
    async def should_send(
        self,
        evento: str,
        referencia_id: Optional[str],
        workflow_id: Optional[str],
        destinatario: str,
        template_codigo: str,
        ventana_minutos: Optional[int] = None
    ) -> Dict:
        """
        Determina si se debe enviar una notificación.
        
        Returns:
            Dict con:
            - should_send: bool
            - reason: str
            - existing_log_id: Optional[str]
        """
        is_dup, existing_id = await self.is_duplicate(
            evento=evento,
            referencia_id=referencia_id,
            workflow_id=workflow_id,
            destinatario=destinatario,
            template_codigo=template_codigo,
            ventana_minutos=ventana_minutos
        )
        
        if is_dup:
            return {
                "should_send": False,
                "reason": "duplicate",
                "existing_log_id": existing_id
            }
        
        return {
            "should_send": True,
            "reason": "ok",
            "existing_log_id": None
        }
    
    async def get_recent_sends(
        self,
        destinatario: str,
        minutes: int = 60
    ) -> int:
        """
        Cuenta envíos recientes a un destinatario.
        Útil para rate limiting.
        
        Args:
            destinatario: Teléfono/email
            minutes: Ventana de tiempo
            
        Returns:
            Cantidad de envíos en la ventana
        """
        ahora = datetime.now(timezone.utc)
        inicio_ventana = (ahora - timedelta(minutes=minutes)).isoformat()
        
        # SQL-FIRST P4C: conteo reciente desde dbo.Operativo_Notificaciones_Log
        try:
            from modules.compras.sync_service import get_edarsahub_connection
            conn = get_edarsahub_connection()
            cur = conn.cursor(as_dict=True)
            cur.execute("""
                SELECT COUNT(*) AS total
                FROM dbo.Operativo_Notificaciones_Log
                WHERE (Destinatario=%s OR DestinatarioEmail=%s)
                  AND Estado IN ('enviado','entregado','ENVIADO','ENTREGADO')
                  AND FechaEnvio >= DATEADD(minute, -%s, GETUTCDATE())
            """, (destinatario, destinatario, int(minutes)))
            row = cur.fetchone() or {}
            conn.close()
            return int(row.get("total") or 0)
        except Exception as e:
            logger.warning(f"SQL-FIRST P4C recent sends fallback: {e}")
            return 0


# =============================================================================
# SINGLETON
# =============================================================================

_dedup_service: Optional[DeduplicationService] = None


def get_dedup_service(db) -> DeduplicationService:
    """Obtiene instancia del servicio de deduplicación."""
    global _dedup_service
    if _dedup_service is None:
        _dedup_service = DeduplicationService(db)
    return _dedup_service


def reset_dedup_service():
    """Reset para testing."""
    global _dedup_service
    _dedup_service = None
