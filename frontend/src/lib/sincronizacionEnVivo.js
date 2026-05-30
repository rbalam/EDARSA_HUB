// 1. Asegúrate de importar la nueva clase en la parte superior de tu archivo
import { ResilientWebSocket } from '../lib/ResilientWebSocket';

// 2. Reemplaza tu inicialización vieja por esta función blindada
export const iniciarSincronizacionEnVivo = () => {
    // Definimos la ruta correcta hacia el cerebro de EDARSA HUB
    const wsUrl = `wss://${window.location.host}/api/centro-control/ws`;

    // Instanciamos el nuevo motor resiliente
    const conexionEnVivo = new ResilientWebSocket(wsUrl, {
        onMessage: (datos) => {
            // Aquí inyectas los datos a tu estado de React (Tablero Comercial / Comandero)
            console.log("[EDARSA HUB] Datos frescos recibidos:", datos);
            // setDatosTablero(datos); <-- Ejemplo de actualización de estado
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
