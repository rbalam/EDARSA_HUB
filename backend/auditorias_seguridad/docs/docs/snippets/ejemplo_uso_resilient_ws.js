import { ResilientWebSocket } from '../lib/ResilientWebSocket';

// Reemplaza tu vieja conexión: const ws = new WebSocket(...) con esto:
const conexionEnVivo = new ResilientWebSocket('wss://' + window.location.host + '/api/centro-control/ws', {
    onMessage: (datos) => {
        // Aquí actualizas tu tablero o comandero con los datos frescos
        console.log("Datos en tiempo real:", datos);
    },
    onConnect: () => console.log("Sincronización en vivo activa.")
});
