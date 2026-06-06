// =============================================================================
// SNIPPET: CONTROL DE TIMEOUT Y PREVENCIÓN DE BUCLES INFINITOS EN FRONTEND
// OBJETIVO: Evitar que el tablero ejecutivo quede congelado ante fallos de API
// =============================================================================

// 1. CONTROL DE TIEMPO LIMITE (TIMEOUT) EN LAS PETICIONES API (Axios Ejemplo)
const apiCliente = axios.create({
  baseURL: 'https://stock-tracker-990.preview.emergentagent.com/api',
  timeout: 10000 // 🛑 Si el servidor no responde en 10 segundos, aborta la petición.
});

// 2. EVITAR EL BUCLE INFINITO EN EL COMPONENTE DEL TABLERO EJECUTIVO
try {
  setIsLoading(true);
  const respuesta = await apiCliente.get('/sistema/menus/usuario');
  setUnidades(respuesta.data);
} catch (error) {
  // 💡 En lugar de quedarse "pensando", el sistema detecta el error y muestra un botón de reintento
  console.error("[EDARSA ERROR] Fallo en comunicación:", error.message);
  setMensajeError("La conexión tardó demasiado en responder.");
  setFallbackMenu(); // Carga los menús disponibles de forma segura sin congelar la pantalla
} finally {
  setIsLoading(false); // 🔓 Detiene la rueda de carga obligatoriamente
}
