// =============================================================================
// UTILIDAD: WEBSOCKET BLINDADO CON AUTO-RECONEXIÓN
// OBJETIVO: Mantener conexión persistente sin saturar logs de errores
// =============================================================================

// Reemplaza tu inicialización de WebSocket con este escudo de auto-reconexión
export const iniciarWebSocketBlindado = () => {
    // Ajusta la ruta a tu entorno real (usualmente /api/centro-control/ws o /ws)
    const wsUrl = `wss://${window.location.host}/api/centro-control/ws`;
    let ws;
    let intentos = 0;

    const conectar = () => {
        try {
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log("[EDARSA HUB] Conexión en vivo (WebSocket) establecida.");
                intentos = 0; // Reiniciamos el contador al conectar con éxito
            };

            ws.onclose = () => {
                console.warn("[EDARSA HUB] Conexión WS perdida. Reconectando silenciosamente...");
                // Reconexión automática con retraso progresivo (evita saturar el servidor)
                const retraso = Math.min(1000 * (2 ** intentos), 15000);
                intentos++;
                setTimeout(conectar, retraso);
            };

            ws.onerror = (error) => {
                // Capturamos el error silenciosamente para que la consola no se sature de rojo
                // y delegamos la tarea de reconexión al evento onclose
                console.debug("[EDARSA HUB] Intermitencia en WebSocket interceptada.");
            };

        } catch (error) {
            console.error("[EDARSA HUB] Fallo al iniciar el WebSocket localmente.");
        }
    };

    // Iniciamos la primera conexión
    conectar();
    return ws;
};

// =============================================================================
// HOOK REACT: useWebSocketBlindado
// =============================================================================
import { useEffect, useRef, useState } from 'react';

export const useWebSocketBlindado = (onMessage) => {
    const wsRef = useRef(null);
    const [isConnected, setIsConnected] = useState(false);
    const intentosRef = useRef(0);

    useEffect(() => {
        const wsUrl = `wss://${window.location.host}/api/centro-control/ws`;

        const conectar = () => {
            try {
                wsRef.current = new WebSocket(wsUrl);

                wsRef.current.onopen = () => {
                    console.log("[WS] Conexión establecida");
                    setIsConnected(true);
                    intentosRef.current = 0;
                };

                wsRef.current.onmessage = (event) => {
                    if (onMessage) {
                        try {
                            const data = JSON.parse(event.data);
                            onMessage(data);
                        } catch (e) {
                            onMessage(event.data);
                        }
                    }
                };

                wsRef.current.onclose = () => {
                    console.warn("[WS] Conexión cerrada, reconectando...");
                    setIsConnected(false);
                    const retraso = Math.min(1000 * (2 ** intentosRef.current), 15000);
                    intentosRef.current++;
                    setTimeout(conectar, retraso);
                };

                wsRef.current.onerror = () => {
                    console.debug("[WS] Error interceptado silenciosamente");
                };

            } catch (error) {
                console.error("[WS] Error inicializando WebSocket");
            }
        };

        conectar();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [onMessage]);

    return { isConnected, ws: wsRef.current };
};

export default iniciarWebSocketBlindado;
