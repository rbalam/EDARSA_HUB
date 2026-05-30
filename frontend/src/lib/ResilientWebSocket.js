// Ruta: /app/frontend/src/lib/ResilientWebSocket.js
// =============================================================================
// CLASE: WEBSOCKET RESILIENTE CON HEARTBEAT Y RECONEXIÓN EXPONENCIAL
// OBJETIVO: Mantener conexión persistente sin saturar logs ni perder mensajes
// =============================================================================

export class ResilientWebSocket {
    constructor(url, options = {}) {
        this.url = url;
        this.ws = null;
        
        // Configuraciones de resiliencia
        this.pingInterval = options.pingInterval || 30000; // Latido cada 30s
        this.maxReconnectDelay = options.maxReconnectDelay || 10000; // Máximo 10s entre reintentos
        this.reconnectDelay = options.baseDelay || 1000; // Base de 1s
        this.reconnectAttempts = 0;
        
        // Callbacks
        this.onMessage = options.onMessage || (() => {});
        this.onConnect = options.onConnect || (() => {});
        this.onDisconnect = options.onDisconnect || (() => {});
        
        // Estado interno
        this.pingTimer = null;
        this.isIntentionalClose = false;

        this.connect();
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.info(`[EDARSA WS] Enlace en vivo establecido: ${this.url}`);
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000; // Reiniciamos el backoff
            this.isIntentionalClose = false;
            this.startHeartbeat();
            this.onConnect();
        };

        this.ws.onmessage = (event) => {
            if (event.data === 'pong') return; // Ignorar latidos de control
            
            try {
                const data = JSON.parse(event.data);
                this.onMessage(data);
            } catch (err) {
                console.warn("[EDARSA WS] Datos no parseables recibidos.");
            }
        };

        this.ws.onclose = () => {
            this.stopHeartbeat();
            this.onDisconnect();
            
            if (!this.isIntentionalClose) {
                this.triggerReconnection();
            }
        };

        this.ws.onerror = (error) => {
            // Interceptamos el error silenciosamente. El evento onclose manejará la reconexión.
            console.debug("[EDARSA WS] Intermitencia de red detectada.");
            this.ws.close(); 
        };
    }

    startHeartbeat() {
        this.pingTimer = setInterval(() => {
            if (this.ws.readyState === WebSocket.OPEN) {
                this.ws.send('ping');
            }
        }, this.pingInterval);
    }

    stopHeartbeat() {
        if (this.pingTimer) {
            clearInterval(this.pingTimer);
            this.pingTimer = null;
        }
    }

    triggerReconnection() {
        console.warn(`[EDARSA WS] Reconectando en ${this.reconnectDelay / 1000}s... (Intento ${this.reconnectAttempts + 1})`);
        
        setTimeout(() => {
            this.reconnectAttempts++;
            // Retroceso exponencial: 1s, 2s, 4s, 8s... hasta el máximo definido
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
            this.connect();
        }, this.reconnectDelay);
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error("[EDARSA WS] Imposible enviar datos. Canal cerrado.");
        }
    }

    close() {
        this.isIntentionalClose = true;
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close();
        }
        console.info("[EDARSA WS] Conexión cerrada por el cliente.");
    }
}

// =============================================================================
// EJEMPLO DE USO EN COMPONENTES REACT
// =============================================================================
/*
import { ResilientWebSocket } from '@/lib/ResilientWebSocket';

// En tu componente o hook:
useEffect(() => {
    const wsUrl = `wss://${window.location.host}/api/centro-control/ws`;
    
    const ws = new ResilientWebSocket(wsUrl, {
        pingInterval: 30000,
        onConnect: () => console.log("Conectado al centro de control"),
        onDisconnect: () => console.log("Desconectado del centro de control"),
        onMessage: (data) => {
            // Manejar mensajes entrantes
            console.log("Mensaje recibido:", data);
        }
    });
    
    return () => ws.close();
}, []);
*/

export default ResilientWebSocket;
