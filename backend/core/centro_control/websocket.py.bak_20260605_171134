"""
CENTRO DE CONTROL EDARSA - WebSocket para Notificaciones en Tiempo Real
========================================================================
Sistema de notificaciones push para alertas críticas.

Funcionalidades:
- Conexión WebSocket persistente
- Broadcast de alertas críticas a todos los clientes conectados
- Heartbeat para mantener conexiones activas
- Reconexión automática desde frontend

Uso:
- ws://host/api/centro-control/ws → Conexión WebSocket
- Los clientes reciben JSON con estructura:
  {
    "tipo": "alerta_critica" | "alerta_nueva" | "estado_cambio" | "heartbeat",
    "data": { ... }
  }
"""

import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    """Información de una conexión WebSocket"""
    websocket: WebSocket
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_email: str = "anonymous"
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationManager:
    """
    Gestor de notificaciones en tiempo real para el Centro de Control.
    
    Uso:
        manager = NotificationManager()
        
        # En el endpoint WebSocket:
        await manager.connect(websocket)
        
        # Para enviar notificación a todos:
        await manager.broadcast_alerta_critica(alerta_data)
    """
    
    def __init__(self):
        self._connections: Dict[str, ConnectionInfo] = {}
        self._connection_counter = 0
        self._heartbeat_task = None
        self._running = False
    
    @property
    def connection_count(self) -> int:
        return len(self._connections)
    
    async def connect(self, websocket: WebSocket, user_email: str = "anonymous") -> str:
        """Acepta una nueva conexión WebSocket"""
        await websocket.accept()
        
        self._connection_counter += 1
        connection_id = f"conn_{self._connection_counter}_{datetime.now(timezone.utc).strftime('%H%M%S')}"
        
        self._connections[connection_id] = ConnectionInfo(
            websocket=websocket,
            user_email=user_email
        )
        
        logger.info(f"[WS] Nueva conexión: {connection_id} ({user_email}) - Total: {self.connection_count}")
        
        # Enviar mensaje de bienvenida
        await self._send_to_connection(connection_id, {
            "tipo": "conexion_establecida",
            "data": {
                "connection_id": connection_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mensaje": "Conectado al Centro de Control EDARSA"
            }
        })
        
        # Iniciar heartbeat si no está corriendo
        if not self._running:
            self._running = True
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """Desconecta un cliente"""
        if connection_id in self._connections:
            del self._connections[connection_id]
            logger.info(f"[WS] Desconexión: {connection_id} - Total: {self.connection_count}")
            
            # Detener heartbeat si no hay conexiones
            if self.connection_count == 0:
                self._running = False
                if self._heartbeat_task:
                    self._heartbeat_task.cancel()
    
    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Envía mensaje a una conexión específica"""
        if connection_id not in self._connections:
            return False
        
        try:
            await self._connections[connection_id].websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"[WS] Error enviando a {connection_id}: {e}")
            self.disconnect(connection_id)
            return False
    
    async def broadcast(self, message: Dict[str, Any]):
        """Envía mensaje a todas las conexiones activas"""
        if not self._connections:
            return
        
        disconnected = []
        for conn_id in list(self._connections.keys()):
            success = await self._send_to_connection(conn_id, message)
            if not success:
                disconnected.append(conn_id)
        
        # Limpiar conexiones fallidas
        for conn_id in disconnected:
            self.disconnect(conn_id)
    
    async def broadcast_alerta_critica(self, alerta: Dict[str, Any]):
        """Envía notificación de alerta crítica a todos los clientes"""
        await self.broadcast({
            "tipo": "alerta_critica",
            "data": {
                "alerta": alerta,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prioridad": "alta",
                "sonido": True
            }
        })
        logger.info(f"[WS] Broadcast alerta crítica: {alerta.get('titulo', 'Sin título')}")
    
    async def broadcast_alerta_nueva(self, alerta: Dict[str, Any]):
        """Envía notificación de nueva alerta (cualquier severidad)"""
        await self.broadcast({
            "tipo": "alerta_nueva",
            "data": {
                "alerta": alerta,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
    
    async def broadcast_estado_cambio(self, estado: str, detalle: str = None):
        """Envía notificación de cambio de estado del sistema"""
        await self.broadcast({
            "tipo": "estado_cambio",
            "data": {
                "estado": estado,
                "detalle": detalle,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
    
    async def broadcast_fuente_caida(self, fuente: Dict[str, Any]):
        """Envía notificación de fuente de datos caída"""
        await self.broadcast({
            "tipo": "fuente_caida",
            "data": {
                "fuente": fuente,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prioridad": "alta"
            }
        })
    
    async def _heartbeat_loop(self):
        """Loop de heartbeat para mantener conexiones activas"""
        while self._running:
            try:
                await asyncio.sleep(30)  # Heartbeat cada 30 segundos
                
                if self._connections:
                    await self.broadcast({
                        "tipo": "heartbeat",
                        "data": {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "conexiones_activas": self.connection_count
                        }
                    })
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[WS] Error en heartbeat: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna estado actual del manager de notificaciones"""
        return {
            "conexiones_activas": self.connection_count,
            "running": self._running,
            "conexiones": [
                {
                    "id": conn_id,
                    "user": info.user_email,
                    "connected_at": info.connected_at.isoformat()
                }
                for conn_id, info in self._connections.items()
            ]
        }


# Instancia global del manager
notification_manager = NotificationManager()


def get_notification_manager() -> NotificationManager:
    """Retorna la instancia global del NotificationManager"""
    return notification_manager
