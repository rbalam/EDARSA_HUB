"""
Notification repository SQL-first.

Mongo runtime eliminado. Config/provider/templates/queue legacy quedan neutralizados
por no existir tabla canónica específica. Logs se consultan/registran en
dbo.Operativo_Notificaciones_Log.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json
import uuid


class NotificationRepository:
    def __init__(self, db=None):
        self.db = db

    def _conn(self):
        from modules.compras.sync_service import get_edarsahub_connection
        return get_edarsahub_connection()

    def _rows(self, sql: str, params: tuple = ()) -> List[Dict]:
        conn = self._conn()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, params)
            return cur.fetchall() or []
        finally:
            conn.close()

    def _one(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        rows = self._rows(sql, params)
        return rows[0] if rows else None

    def _exec(self, sql: str, params: tuple = ()) -> None:
        conn = self._conn()
        try:
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def _next_id(self, table: str, col: str = "ID") -> int:
        row = self._one(f"SELECT ISNULL(MAX({col}),0)+1 AS NextID FROM dbo.{table} WITH (UPDLOCK,HOLDLOCK)")
        return int((row or {}).get("NextID") or 1)

    def _doc(self, obj: Any) -> Dict:
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return dict(obj)
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return dict(getattr(obj, "__dict__", {}) or {})

    # Config/provider/templates legacy: no-op compatible SQL-only
    async def get_config(self, evento: str, modulo: Optional[str] = None, canal: Optional[str] = None) -> Optional[Dict]:
        return None

    async def get_all_configs(self, modulo: Optional[str] = None, canal: Optional[str] = None, activo: Optional[bool] = None) -> List[Dict]:
        return []

    async def create_config(self, config) -> Dict:
        doc = self._doc(config)
        doc.setdefault("id", str(uuid.uuid4()))
        doc["sql_first_neutralized"] = True
        return doc

    async def update_config(self, config_id: str, updates: Dict) -> Optional[Dict]:
        return None

    async def delete_config(self, config_id: str) -> bool:
        return False

    async def get_provider_config(self, canal: str, provider: str) -> Optional[Dict]:
        return None

    async def get_active_provider(self, canal: str) -> Optional[Dict]:
        return None

    async def create_provider_config(self, config) -> Dict:
        doc = self._doc(config)
        doc.setdefault("id", str(uuid.uuid4()))
        doc["sql_first_neutralized"] = True
        return doc

    async def update_provider_config(self, config_id: str, updates: Dict) -> Optional[Dict]:
        return None

    async def get_template(self, canal: str, codigo: str) -> Optional[Dict]:
        return None

    async def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        return None

    async def get_all_templates(self, canal: Optional[str] = None, activo: Optional[bool] = None) -> List[Dict]:
        return []

    async def create_template(self, template) -> Dict:
        doc = self._doc(template)
        doc.setdefault("id", str(uuid.uuid4()))
        doc["sql_first_neutralized"] = True
        return doc

    async def update_template(self, template_id: str, updates: Dict) -> Optional[Dict]:
        return None

    async def delete_template(self, template_id: str) -> bool:
        return False

    # Queue legacy: no-op compatible
    async def enqueue(self, item) -> Dict:
        doc = self._doc(item)
        doc.setdefault("id", str(uuid.uuid4()))
        doc["sql_first_neutralized"] = True
        return doc

    async def get_pending_items(self, limit: int = 50) -> List[Dict]:
        return []

    async def lock_item(self, queue_id: str, worker_id: str) -> bool:
        return False

    async def update_queue_item(self, queue_id: str, updates: Dict) -> bool:
        return False

    async def mark_sent(self, queue_id: str) -> bool:
        return False

    async def mark_failed(self, queue_id: str, error: str) -> bool:
        return False

    async def get_queue_stats(self) -> Dict:
        return {"pending": 0, "locked": 0, "sent": 0, "failed": 0, "sql_first_neutralized": True}

    # Logs SQL-first
    async def create_log(self, log) -> Dict:
        doc = self._doc(log)
        log_id = doc.get("id") or str(uuid.uuid4())
        metadata = json.dumps(doc, ensure_ascii=False, default=str)

        self._exec("""
            INSERT INTO dbo.Operativo_Notificaciones_Log (
                ID, NotificacionID, TipoEvento, WorkflowID, TareaID,
                Destinatario, DestinatarioEmail, Titulo, Mensaje,
                Estado, Canal, FechaEnvio, ErrorMensaje, MetadatosJSON
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,GETUTCDATE(),%s,%s)
        """, (
            self._next_id("Operativo_Notificaciones_Log", "ID"),
            log_id,
            (doc.get("evento") or doc.get("tipo_evento") or "NOTIFICACION")[:50],
            doc.get("workflow_id"),
            doc.get("tarea_id"),
            doc.get("destinatario") or doc.get("recipient"),
            doc.get("destinatario_email") or doc.get("email"),
            doc.get("titulo") or doc.get("subject"),
            doc.get("mensaje") or doc.get("message"),
            (doc.get("estado") or doc.get("status") or "ENVIADO")[:50],
            (doc.get("canal") or doc.get("channel") or "EMAIL")[:50],
            doc.get("error") or doc.get("error_mensaje"),
            metadata
        ))

        doc["id"] = log_id
        return doc

    async def get_logs(self, filtro: Dict = None, limit: int = 100, skip: int = 0) -> List[Dict]:
        rows = self._rows(f"""
            SELECT TOP {int(limit)}
                NotificacionID AS id,
                TipoEvento AS evento,
                WorkflowID AS workflow_id,
                TareaID AS tarea_id,
                Destinatario AS destinatario,
                DestinatarioEmail AS destinatario_email,
                Titulo AS titulo,
                Mensaje AS mensaje,
                Estado AS estado,
                Canal AS canal,
                FechaEnvio AS fecha_envio,
                ErrorMensaje AS error_mensaje,
                MetadatosJSON AS metadatos_json
            FROM dbo.Operativo_Notificaciones_Log
            ORDER BY FechaEnvio DESC
        """)
        return rows[int(skip):]

    async def count_logs(self, filtro: Dict = None) -> int:
        row = self._one("SELECT COUNT(*) AS total FROM dbo.Operativo_Notificaciones_Log")
        return int((row or {}).get("total") or 0)

    async def get_log_stats(self, modulo: Optional[str] = None) -> Dict:
        rows = self._rows("""
            SELECT Canal, Estado, COUNT(*) AS total
            FROM dbo.Operativo_Notificaciones_Log
            GROUP BY Canal, Estado
        """)
        stats = {}
        for r in rows:
            canal = r.get("Canal") or "SIN_CANAL"
            stats.setdefault(canal, {"total": 0, "por_estado": {}})
            stats[canal]["total"] += int(r.get("total") or 0)
            stats[canal]["por_estado"][r.get("Estado") or "SIN_ESTADO"] = int(r.get("total") or 0)
        return stats

    async def check_duplicate(self, destinatario: str, evento: str, dedup_key: str, ventana_minutos: int = 60) -> bool:
        row = self._one("""
            SELECT TOP 1 NotificacionID
            FROM dbo.Operativo_Notificaciones_Log
            WHERE TipoEvento=%s
              AND (Destinatario=%s OR DestinatarioEmail=%s)
              AND FechaEnvio >= DATEADD(minute, -%s, GETUTCDATE())
            ORDER BY FechaEnvio DESC
        """, (evento, destinatario, destinatario, int(ventana_minutos)))
        return row is not None


def get_notification_repository_legacy(db=None) -> NotificationRepository:
    return NotificationRepository(db)

# Gate 5D: compatibilidad de imports; runtime canonico SQL-first.
from .repository_sql import NotificationRepository, get_notification_repository
