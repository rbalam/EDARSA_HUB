import api from "../lib/api";

/**
 * Menús del usuario filtrados por la UNIDAD DE NEGOCIO activa (contexto RBAC).
 * Usa el MISMO endpoint canónico que el menú Enterprise: /api/sistema/menus/usuario
 * (no duplica flujos). La autenticación va por el interceptor de `api` (token real).
 *
 * @param {string|null} unidadNegocioId UUID de la unidad activa (opcional).
 * @returns {Promise<Array>} arreglo de módulos (data.modulos del endpoint).
 */
export async function fetchMenusUsuario(unidadNegocioId = null) {
  const params = {};
  if (unidadNegocioId) {
    params.unidad_negocio_id = unidadNegocioId;
  }

  const { data } = await api.get("/sistema/menus/usuario", { params });

  // El endpoint Enterprise responde { modulos, total, es_super_admin, ... }
  return Array.isArray(data?.modulos) ? data.modulos : [];
}

export async function fetchMenuFavoritos() {
  const { data } = await api.get("/sistema/menus/favoritos");

  return {
    rutas: Array.isArray(data?.rutas) ? data.rutas : [],
    total: Number(data?.total || 0),
    has_configuracion: Boolean(data?.has_configuracion),
    source: data?.source || "SQL_USUARIO_MENU_FAVORITOS",
  };
}

export async function saveMenuFavoritos(rutas = []) {
  const payload = {
    rutas: Array.isArray(rutas) ? rutas : [],
  };

  const { data } = await api.put("/sistema/menus/favoritos", payload);

  return {
    rutas: Array.isArray(data?.rutas) ? data.rutas : [],
    total: Number(data?.total || 0),
    has_configuracion: Boolean(data?.has_configuracion),
    source: data?.source || "SQL_USUARIO_MENU_FAVORITOS",
  };
}

