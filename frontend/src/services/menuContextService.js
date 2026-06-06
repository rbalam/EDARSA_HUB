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
