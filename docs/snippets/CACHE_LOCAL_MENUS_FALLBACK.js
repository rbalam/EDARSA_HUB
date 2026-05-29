// =============================================================================
// SNIPPET: CACHE LOCAL DE MENÚS Y FALLBACK OFFLINE
// OBJETIVO: Garantizar navegación incluso sin conexión al servidor central
// =============================================================================

// Al iniciar sesión con éxito, guardamos los menús autorizados en la memoria local
localStorage.setItem('edarsa_menus_cache', JSON.stringify(menusRecibidos));

// Si la conexión falla (Error 502/Red), el sistema lee la memoria al instante:
catch (error) {
  console.warn("Sin conexión. Cargando menús desde la Memoria Caché local...");
  const menusGuardados = localStorage.getItem('edarsa_menus_cache');
  if (menusGuardados) {
    setMenus(JSON.stringify(menusGuardados)); // 🔓 Renderiza el menú sin quedarse "pensando"
  }
}

// Forzar el apagado de la animación de carga a los 5 segundos si la red no responde
setTimeout(() => {
  if (isLoading) {
    setIsLoading(false); // Destraba la pantalla del usuario
    setAlertaMensaje("Mostrando últimos datos registrados localmente.");
  }
}, 5000);
