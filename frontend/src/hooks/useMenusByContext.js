import { useCallback, useEffect, useState } from "react";
import { fetchMenusUsuario } from "../services/menuContextService";

/**
 * Carga los módulos del menú según la unidad de negocio activa.
 * Recarga automáticamente cuando cambia `unidadNegocioId`.
 */
export function useMenusByContext(unidadNegocioId, enabled = true) {
  const [menus, setMenus] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadMenus = useCallback(async () => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await fetchMenusUsuario(unidadNegocioId || null);
      setMenus(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err);
      setMenus([]);
    } finally {
      setLoading(false);
    }
  }, [unidadNegocioId, enabled]);

  useEffect(() => {
    if (!enabled) return;
    loadMenus();
  }, [enabled, loadMenus]);

  return {
    menus,
    loading,
    error,
    reloadMenus: loadMenus,
  };
}
