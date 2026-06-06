/**
 * SCRIPT DE LIMPIEZA PROFUNDA Y RESTABLECIMIENTO DE SESIÓN (EMERGENT.SH)
 * 
 * Copia este código, ve a tu pestaña de Emergent, presiona F12 (Consola) y pégalo.
 */
(async function depuracionProfundaEmergent() {
  console.clear();
  console.log("%c🧹 Iniciando restablecimiento profundo de sesión para EDARSA...", "color: #ffaa00; font-weight: bold; font-size: 14px;");

  // 1. Limpieza de Storages locales
  try {
    localStorage.clear();
    sessionStorage.clear();
    console.log("✅ LocalStorage y SessionStorage depurados.");
  } catch (err) {
    console.error("❌ Error en Storages:", err);
  }

  // 2. Destruir e invalidar cookies de todos los subdominios de Emergent
  try {
    const domains = [
      window.location.hostname,
      `.${window.location.hostname}`,
      "app.emergent.sh",
      ".app.emergent.sh",
      "emergent.sh",
      ".emergent.sh",
      "emergentagent.com",
      ".emergentagent.com"
    ];
    const paths = ["/", "/api", "/auth", "/static"];
    const cookies = document.cookie.split(";");

    cookies.forEach(rawCookie => {
      const name = rawCookie.split("=")[0].trim();
      if (!name) return;
      domains.forEach(domain => {
        paths.forEach(path => {
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=${path}; domain=${domain}; SameSite=Lax; Secure`;
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=${path}; domain=${domain}`;
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=${path};`;
        });
      });
    });
    console.log("✅ Cookies expiradas y saneadas del navegador.");
  } catch (err) {
    console.error("❌ Error en cookies:", err);
  }

  // 3. Desregistrar Service Workers (Previenen que cargue el login limpio)
  if ("serviceWorker" in navigator) {
    try {
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (let reg of registrations) {
        await reg.unregister();
        console.log("✅ Service Worker removido.");
      }
    } catch (err) {
      console.error("❌ Error en Service Workers:", err);
    }
  }

  // 4. Limpieza de CacheStorage
  if ("caches" in window) {
    try {
      const cacheNames = await caches.keys();
      for (let name of cacheNames) {
        await caches.delete(name);
      }
      console.log("✅ Caché del persistente de llamadas limpia.");
    } catch (err) {
      console.error("❌ Error en cachés:", err);
    }
  }

  console.log("%c🚀 Limpieza completada. Redireccionando a la página de login...", "color: #00ff66; font-weight: bold; font-size: 13px;");
  
  setTimeout(() => {
    // Forzar refresco evitando la caché persistente del navegador
    const cleanUrl = new URL(window.location.origin);
    cleanUrl.searchParams.set("reauth", Date.now().toString());
    window.location.href = cleanUrl.toString();
  }, 1500);
})();
