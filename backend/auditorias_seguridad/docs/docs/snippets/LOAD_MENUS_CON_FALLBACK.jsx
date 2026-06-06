// =============================================================================
// SNIPPET: IMPLEMENTACIÓN DE CARGA DE MENÚS CON FALLBACK
// OBJETIVO: Garantizar que la UI nunca se quede congelada
// =============================================================================

// 1. Asegúrate de tener esta importación al inicio del archivo
import { menuFallback } from '../config/menuFallback';

// ... resto de tu código ...

// 2. Modifica tu función de carga de menús (generalmente dentro de un useEffect)
const loadMenus = async () => {
  setIsLoading(true);
  try {
    const response = await api.get('/api/sistema/menus/usuario');
    setMenus(response.data);
  } catch (error) {
    console.error("Error cargando menús, usando fallback:", error);
    // Este es el punto clave: si la API falla, forzamos el uso del respaldo
    setMenus(menuFallback);
  } finally {
    // Garantizamos que la pantalla se desbloquee siempre
    setIsLoading(false);
  }
};

// 3. Llamar en useEffect
useEffect(() => {
  loadMenus();
}, []);
