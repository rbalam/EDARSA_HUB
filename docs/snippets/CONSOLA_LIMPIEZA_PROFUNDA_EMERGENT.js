/**
 * RECONEXIÓN E1: LIMPIEZA PROFUNDA DE SESIÓN, COOKIES Y SERVICE WORKERS
 * Ejecutar en la consola de desarrollador (F12) en la pestaña de emergent.sh
 */
(async function limpiarSesionEmergent() {
  console.log("%c🧹 Iniciando limpieza profunda de sesión y caché en Emergent...", "color: #ffaa00; font-weight: bold; font-size: 14px;");

  // 1. Limpiar Storages Locales
  try {
    localStorage.clear();
    sessionStorage.clear();
    console.log("✅ LocalStorage y SessionStorage limpios.");
  } catch (err) {
    console.error("❌ Error al limpiar storages:", err);
  }

  // 2. Limpieza exhaustiva de cookies del dominio y subdominios
  try {
    const cookies = document.cookie.split(";");
    const domains = [
      window.location.hostname,
      `.${window.location.hostname}`,
      "emergent.sh",
      ".emergent.sh",
      "emergentagent.com",
      ".emergentagent.com"
    ];

    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i];
      const eqPos = cookie.indexOf("=");
      const name = eqPos > -1 ? cookie.substr(0, eqPos).trim() : cookie.trim();
      
      domains.forEach(domain => {
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; domain=${domain}`;
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;`;
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/static; domain=${domain}`;
        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/api; domain=${domain}`;
      });
    }
    console.log("✅ Cookies expiradas y eliminadas del navegador.");
  } catch (err) {
    console.error("❌ Error al borrar cookies:", err);
  }

  // 3. Desregistrar Service Workers activos (Soluciona el bloqueo de caché persistente)
  if ("serviceWorker" in navigator) {
    try {
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (let registration of registrations) {
        await registration.unregister();
        console.log("✅ Service Worker desregistrado:", registration.active?.scriptURL || "SW");
      }
    } catch (err) {
      console.error("❌ Error desregistrando service workers:", err);
    }
  }

  // 4. Limpieza de Cachés del navegador
  if ("caches" in window) {
    try {
      const cacheNames = await caches.keys();
      for (let name of cacheNames) {
        await caches.delete(name);
        console.log(`✅ Caché de navegador eliminado: ${name}`);
      }
    } catch (err) {
      console.error("❌ Error eliminando cachés de CacheStorage:", err);
    }
  }

  console.log("%c🚀 Proceso completado. Solicitando nuevas credenciales...", "color: #00ff66; font-weight: bold; font-size: 13px;");
  
  // 5. Autorecarga forzada con un parámetro que evita caché de red (timestamp)
  setTimeout(() => {
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set("reauth_session", Date.now().toString());
    window.location.href = currentUrl.toString();
  }, 1200);
})();
