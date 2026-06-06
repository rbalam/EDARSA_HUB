// snippet_axios_fallback_pattern.js
// Patrón de manejo de errores con fallback para React/Axios
// Usado en componentes de EDARSAHUB para Alta Disponibilidad

try {
   setIsLoading(true); // Se activa "Consultando todas las unidades"
   const respuesta = await axios.get('/api/comercial/unidades', { timeout: 15000 });
   setUnidades(respuesta.data);
} catch (error) {
   console.error("Fallo de red en Axios detectado:", error);
   // AQUÍ ESTÁ LA CLAVE: Debes forzar que el loading desaparezca si hay timeout  
   // Y establecer datos locales/hardcodeados (Fallback)
   setUnidades(datosDeRespaldoHardcodeados); 
} finally {
   setIsLoading(false); // <--- Garantiza que el spinner se detenga siempre
}
