/**
 * EDARSA HUB - Auth Utilities
 * ===========================
 * Funciones utilitarias de autenticación.
 * 
 * FASE AUTH-SECURITY-01 / FASE 4.2:
 * - La autenticación real se verifica con cookie httpOnly
 * - Estas funciones usan el cache local de user para UI
 * - Para auth real, usar useAuth() del AuthContext
 * - getToken() ELIMINADO - ya no existe en el sistema
 */

import { getSessionUser, clearSession } from '../services/authStorage';
import api from './api';

/**
 * Verifica si hay sesión cacheada
 * NOTA: Solo verifica cache local, no garantiza sesión válida en servidor
 * @returns {boolean}
 */
export const isAuthenticated = () => {
  return !!getSessionUser();
};

/**
 * Obtiene el usuario cacheado
 * @returns {object|null}
 */
export const getUser = () => {
  return getSessionUser();
};

/**
 * Verifica si el usuario tiene un rol mínimo
 * @param {string} requiredRole
 * @returns {boolean}
 */
export const hasRole = (requiredRole) => {
  const user = getUser();
  if (!user) return false;
  
  const roles = ['Usuario', 'Supervisor', 'Administrador', 'SuperAdministrador'];
  const userRoleIndex = roles.indexOf(user.role);
  const requiredRoleIndex = roles.indexOf(requiredRole);
  
  return userRoleIndex >= requiredRoleIndex;
};

/**
 * Cierra sesión
 * FASE AUTH-SECURITY-01: Llama al backend para eliminar cookie httpOnly
 */
export const logout = async () => {
  try {
    // Llamar al backend para eliminar la cookie httpOnly
    await api.post('/auth/logout');
  } catch (error) {
    // Ignorar errores
  }
  clearSession();
  window.location.href = '/login';
};
