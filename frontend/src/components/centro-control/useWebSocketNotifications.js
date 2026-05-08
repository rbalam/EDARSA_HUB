/**
 * Hook para WebSocket de Notificaciones en Tiempo Real
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import logger from '../../services/logger';
import { toast } from 'sonner';
import { XCircle, CheckCircle } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const WS_URL = API_URL?.replace('https://', 'wss://').replace('http://', 'ws://');

export default function useWebSocketNotifications(onAlertaCritica, onAlertaNueva, onEstadoCambio) {
  const [wsConnected, setWsConnected] = useState(false);
  const [wsStatus, setWsStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    try {
      const wsUrl = `${WS_URL}/api/centro-control/ws`;
      logger.log('[WS] Conectando a:', wsUrl);
      
      wsRef.current = new WebSocket(wsUrl);
      setWsStatus('connecting');

      wsRef.current.onopen = () => {
        logger.log('[WS] Conexión establecida');
        setWsConnected(true);
        setWsStatus('connected');
        reconnectAttempts.current = 0;
        toast.success('Notificaciones en tiempo real activadas', { duration: 2000 });
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          logger.log('[WS] Mensaje recibido:', message.tipo);

          switch (message.tipo) {
            case 'alerta_critica':
              toast.error(
                <div className="flex items-start gap-3">
                  <XCircle className="w-6 h-6 text-red-400 shrink-0" />
                  <div>
                    <p className="font-bold">ALERTA CRÍTICA</p>
                    <p className="text-sm">{message.data?.alerta?.titulo || 'Nueva alerta crítica'}</p>
                    <p className="text-xs text-zinc-400 mt-1">{message.data?.alerta?.modulo}</p>
                  </div>
                </div>,
                { duration: 10000 }
              );
              try {
                const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2teleaKOqLi4jFaR');
                audio.volume = 0.3;
                audio.play().catch(() => {});
              } catch (e) {
                // Silenciar error de audio
              }
              onAlertaCritica?.(message.data?.alerta);
              break;

            case 'alerta_nueva':
              toast.info(
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-blue-400 shrink-0" />
                  <div>
                    <p className="font-medium">Nueva Alerta</p>
                    <p className="text-sm text-zinc-600">{message.data?.alerta?.titulo}</p>
                  </div>
                </div>,
                { duration: 5000 }
              );
              onAlertaNueva?.(message.data?.alerta);
              break;

            case 'estado_cambio':
              onEstadoCambio?.(message.data);
              break;

            case 'ping':
              wsRef.current?.send(JSON.stringify({ tipo: 'pong' }));
              break;

            default:
              logger.log('[WS] Tipo de mensaje desconocido:', message.tipo);
          }
        } catch (e) {
          logger.error('[WS] Error procesando mensaje:', e);
        }
      };

      wsRef.current.onerror = (error) => {
        logger.error('[WS] Error:', error);
        setWsStatus('error');
      };

      wsRef.current.onclose = (event) => {
        logger.log('[WS] Conexión cerrada:', event.code, event.reason);
        setWsConnected(false);
        setWsStatus('disconnected');
        
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          logger.log(`[WS] Reintentando en ${delay/1000}s (intento ${reconnectAttempts.current}/${maxReconnectAttempts})`);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        } else {
          logger.warn('[WS] Máximo de reintentos alcanzado');
          setWsStatus('failed');
        }
      };

    } catch (error) {
      logger.error('[WS] Error al conectar:', error);
      setWsStatus('error');
    }
  }, [onAlertaCritica, onAlertaNueva, onEstadoCambio]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setWsConnected(false);
    setWsStatus('disconnected');
    reconnectAttempts.current = 0;
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttempts.current = 0;
    setTimeout(connect, 500);
  }, [disconnect, connect]);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { wsConnected, wsStatus, reconnect };
}
