/**
 * EDARSA HUB - Servicio de Almacenamiento de Autenticación
 * =========================================================
 * Centraliza el acceso a datos de sesión.
 * 
 * FASE AUTH-SECURITY-01 / FASE 4.2:
 * - Token JWT ya NO se guarda en sessionStorage/localStorage
 * - El token viaja SOLO en cookie httpOnly (inaccesible a JS)
 * - Solo se guarda 'user' como cache para UI (no para auth)
 * - Preferencias no sensibles siguen en localStorage
 * 
 * FUNCIONES ELIMINADAS EN FASE 4.2:
 * - getAccessToken() - Token está en cookie httpOnly
 * - setAccessToken() - Servidor setea la cookie
 * - getAuthHeaders() - Auth viaja en cookie, no en header
 * 
 * IMPORTANTE: La autenticación real la maneja el servidor via cookie.
 * El 'user' guardado aquí es solo para mostrar nombre/rol en UI
 * mientras se revalida con el servidor.
 */

// Keys de almacenamiento
const USER_KEY = "user";

// Preferencias (pueden quedarse en localStorage - no sensibles)
const PREFERENCES_PREFIX = "edarsa_pref_";

/**
 * Obtiene los datos del usuario de la sesión (cache para UI)
 * NOTA: Estos datos son solo para UI, no para autenticación
 * @returns {object|null} Datos del usuario o null
 */
export function getSessionUser() {
  try {
    // Primero intenta sessionStorage
    let userStr = sessionStorage.getItem(USER_KEY);
    
    // Fallback a localStorage para migración
    if (!userStr) {
      userStr = localStorage.getItem(USER_KEY);
      if (userStr) {
        sessionStorage.setItem(USER_KEY, userStr);
      }
    }
    
    return userStr ? JSON.parse(userStr) : null;
  } catch (e) {
    return null;
  }
}

/**
 * Guarda los datos del usuario en la sesión (cache para UI)
 * NOTA: Esto es solo cache para mostrar en UI mientras se revalida
 * @param {object} user - Datos del usuario
 */
export function setSessionUser(user) {
  if (!user) return;
  
  const userStr = JSON.stringify(user);
  sessionStorage.setItem(USER_KEY, userStr);
  // También en localStorage para persistencia entre tabs
  localStorage.setItem(USER_KEY, userStr);
}

/**
 * Limpia tokens legacy que pudieran existir de versiones anteriores
 * FASE AUTH-SECURITY-01: Ya no hay token en storage, pero limpiamos legacy
 */
export function clearAccessToken() {
  // Limpiar cualquier token legacy que pudiera existir
  sessionStorage.removeItem('token');
  localStorage.removeItem('token');
  sessionStorage.removeItem('refresh_token');
  localStorage.removeItem('refresh_token');
}

/**
 * Limpia completamente la sesión (logout)
 * NOTA: La cookie httpOnly se limpia con POST /api/auth/logout
 */
export function clearSession() {
  clearAccessToken();
  sessionStorage.removeItem(USER_KEY);
  localStorage.removeItem(USER_KEY);
  
  // Limpiar otros datos de sesión (no preferencias)
  const keysToRemove = [];
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key && !key.startsWith(PREFERENCES_PREFIX)) {
      keysToRemove.push(key);
    }
  }
  keysToRemove.forEach(key => sessionStorage.removeItem(key));
}

/**
 * Verifica si hay una sesión activa (cache local)
 * FASE AUTH-SECURITY-01: Ya no verifica token local
 * La verificación real se hace con /api/auth/me
 * @returns {boolean} True si hay user cacheado (debe verificarse con servidor)
 */
export function isAuthenticated() {
  // Solo verificamos si hay user cacheado
  // La autenticación real se verifica con /api/auth/me
  return !!getSessionUser();
}

/**
 * Guarda una preferencia de usuario (no sensible)
 * @param {string} key - Clave de la preferencia
 * @param {any} value - Valor (será JSON.stringify)
 */
export function setPreference(key, value) {
  localStorage.setItem(`${PREFERENCES_PREFIX}${key}`, JSON.stringify(value));
}

/**
 * Obtiene una preferencia de usuario
 * @param {string} key - Clave de la preferencia
 * @param {any} defaultValue - Valor por defecto si no existe
 * @returns {any} Valor de la preferencia
 */
export function getPreference(key, defaultValue = null) {
  try {
    const value = localStorage.getItem(`${PREFERENCES_PREFIX}${key}`);
    return value ? JSON.parse(value) : defaultValue;
  } catch (e) {
    return defaultValue;
  }
}

// Exportar como default para compatibilidad
export default {
  getSessionUser,
  setSessionUser,
  clearAccessToken,
  clearSession,
  isAuthenticated,
  setPreference,
  getPreference
};
