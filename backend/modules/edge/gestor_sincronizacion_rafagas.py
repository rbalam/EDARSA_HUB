from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
# backend/modules/edge/gestor_sincronizacion_rafagas.py

import sqlite3
import json
import time
import http.client
import os
from typing import Dict, Any, List, Optional

class GestorSincronizacionRafagas:
    def __init__(self, db_path: str = "edarsa_edge_device.db", hub_host: str = "api.edarashub.internal", sync_agent_token: Optional[str] = None):
        self.db_path = db_path
        self.hub_host = hub_host
        self.sync_agent_token = sync_agent_token or os.environ.get("EDARSAHUB_SYNC_AGENT_TOKEN")

    def verificar_enlace_rafaga_internet(self) -> bool:
        """
        Interroga pasivamente el gateway central mediante un ping HTTP ultra-rápido.
        Aplica un timeout estricto de 800ms para evitar congelar el hilo secundario.
        """
        try:
            conexion = http.client.HTTPConnection(self.hub_host, timeout=0.8)
            conexion.request("GET", "/ping")
            respuesta = conexion.getresponse()
            return respuesta.status == 200
        except Exception:
            return False # Internet caído o intermitente: La operación local permanece inmune

    def procesar_rafaga_sincronizacion(self) -> None:
        """
        MÁXIMA RESILIENCIA: Si el internet se restablece temporalmente, consume la
        cola FIFO en orden cronológico estricto (First In, First Out).
        """
        # 1. Validar si la ráfaga de conexión es real y estable
        if not self.verificar_enlace_rafaga_internet():
            return # Continuar operando 100% en caché local de forma transparente

        # 2. Leer elementos acumulados en la cola offline
        query_fifo = "SELECT uuid_transaccion, payload_json FROM cola_sincronizacion_offline WHERE estado = 'PENDING_SYNC' ORDER BY creado_at ASC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query_fifo)
            tickets_pendientes = cursor.fetchall()

        if not tickets_pendientes:
            return # Todo el sistema se encuentra al día

        print(f"[HUB SYNC]: Ráfaga detectada. Procesando {len(tickets_pendientes)} transacciones diferidas...")

        # 3. Despachar paquetes con validación de idempotencia (UUID)
        for ticket in tickets_pendientes:
            token_uuid = ticket["uuid_transaccion"]
            payload = json.loads(ticket["payload_json"])

            success = self._enviar_payload_a_hub(payload)
            
            if success:
                # Actualizar el registro local a sincronizado
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE cola_sincronizacion_offline SET estado = 'SYNCED' WHERE uuid_transaccion = ?", (token_uuid,))
                    conn.commit()
            else:
                break # Intermitencia en la ráfaga: abortar lote para proteger el orden FIFO

    def _enviar_payload_a_hub(self, payload: Dict[str, Any]) -> bool:
        """
        Envía el paquete de datos al bus unificado de EdarasHub.
        """
        try:
            attribution = dict(payload.get("rrr_attribution") or {})
            if not attribution:
                return False
            if not self.sync_agent_token:
                return False

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.sync_agent_token}",
            }
            conexion = http.client.HTTPConnection(self.hub_host, timeout=2.0)
            conexion.request(
                "POST",
                "/api/rrr/attribution/transactions",
                json.dumps(attribution),
                headers,
            )
            respuesta = conexion.getresponse()
            return respuesta.status in [200, 201, 202]
        except Exception:
            return False
