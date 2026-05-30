// Asegúrate de importar la clase en la parte superior de tu archivo
import { ResilientWebSocket } from '../lib/ResilientWebSocket';

// Reemplaza tu inicialización vieja por esta función blindada
export const iniciarSincronizacionEnVivo = () => {
    // La ruta correcta hacia el backend de EDARSA HUB
    const wsUrl = `wss://${window.location.host}/api/centro-control/ws`;

    const conexionEnVivo = new ResilientWebSocket(wsUrl, {
        onMessage: (datos) => {
            // Aquí inyectas los datos a tu estado de React (Tablero Comercial / Comandero)
            console.log("[EDARSA HUB] Datos frescos recibidos:", datos);
        },
        onConnect: () => {
            console.info("[EDARSA HUB] Sincronización en vivo 100% operativa.");
        },
        onDisconnect: () => {
            console.warn("[EDARSA HUB] Sincronización pausada. Esperando reconexión automática...");
        }
    });

    return conexionEnVivo;
};
