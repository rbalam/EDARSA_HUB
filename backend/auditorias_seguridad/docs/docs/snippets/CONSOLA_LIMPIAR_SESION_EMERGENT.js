// ⚡ COPIAR Y PEGAR EN LA CONSOLA (F12) DE EMERGENT.SH ⚡
(function() {
  console.log("%c[EDARSA CONNECT] Iniciando saneamiento de sesión...", "color: #ff6600; font-weight: bold; font-size: 14px;");
  
  // 1. Limpiar almacenamiento corrupto de tokens
  localStorage.clear();
  sessionStorage.clear();
  
  // 2. Limpiar cookies del dominio para forzar login renovado
  const cookies = document.cookie.split(";");
  for (let i = 0; i < cookies.length; i++) {
    const cookie = cookies[i];
    const eqPos = cookie.indexOf("=");
    const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
  }
  
  console.log("%c[EXITO] Cookies y caché local limpiados correctamente.", "color: #00ff66; font-weight: bold;");
  
  // 3. Redirigir para forzar un login con credenciales válidas
  alert("Sesión y tokens purgados con éxito. Haz clic en Aceptar para iniciar sesión de nuevo con tu cuenta activa y reactivar la sincronización.");
  window.location.href = "https://app.emergent.sh/login";
})();
