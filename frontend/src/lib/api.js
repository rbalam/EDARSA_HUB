/**
 * EDARSA HUB - API Client
 * =======================
 * Cliente axios centralizado para todas las llamadas API.
 * 
 * FASE AUTH-SECURITY-01:
 * - withCredentials: true para enviar cookies httpOnly automáticamente
 * - Fallback: token en memoria/sessionStorage + Authorization header (para CORS restrictivo)
 * - FASE TAB-FIX: Token en sessionStorage para persistir entre pestañas
 */

import axios from 'axios';
import { clearSession } from '../services/authStorage';

const normalizeApiBaseUrl = (rawUrl) => {
  const baseUrl = String(rawUrl || '').trim().replace(/[/]+$/, '');
  if (!baseUrl) {
    return '/api';
  }
  return baseUrl.endsWith('/api') ? baseUrl : baseUrl + '/api';
};

const API_URL = normalizeApiBaseUrl(process.env.REACT_APP_BACKEND_URL);

// Token key en sessionStorage
const TOKEN_STORAGE_KEY = 'edarsa_memory_token';

// Token en memoria como fallback adicional
let memoryToken = null;

// Fallback restringido a Preview/Emergent.
// sessionStorage no se comparte entre ventanas; localStorage sí.
// No usar como mecanismo primario en producción.
const shouldUsePreviewTokenFallback = () => {
  try {
    const host = window.location.hostname || "";
    return host.includes("preview.emergentagent.com") || host.includes("emergentagent.com");
  } catch (e) {
    return false;
  }
};

/**
 * Obtener token (sessionStorage primero, luego memoria)
 */
export const getToken = () => {
  // Primero intentar sessionStorage (persiste entre pestañas)
  try {
    const storedToken = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    if (storedToken) {
      return storedToken;
    }
  } catch (e) {
    // sessionStorage no disponible
  }

  try {
    if (shouldUsePreviewTokenFallback()) {
      const storedPreviewToken = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (storedPreviewToken) {
        return storedPreviewToken;
      }
    }
  } catch (e) {
    // localStorage no disponible
  }

  // Fallback a memoria
  return memoryToken;
};

/**
 * Setear token en memoria Y sessionStorage (usado por AuthContext después del login)
 * FASE TAB-FIX: Ahora también guarda en sessionStorage para nueva pestaña
 */
export const setMemoryToken = (token) => {
  memoryToken = token;
  try {
    if (token) {
      sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch (e) {
    // sessionStorage no disponible
  }

  try {
    if (shouldUsePreviewTokenFallback()) {
      if (token) {
        localStorage.setItem(TOKEN_STORAGE_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
      }
    }
  } catch (e) {
    // localStorage no disponible
  }
};

/**
 * Limpiar token de memoria y sessionStorage (usado por logout)
 */
export const clearMemoryToken = () => {
  memoryToken = null;
  try {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch (e) {
    // sessionStorage no disponible
  }

  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch (e) {
    // localStorage no disponible
  }
};

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000, // Aumentamos a 15 segundos para dar margen a consultas pesadas
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
  },
  // FASE AUTH-SECURITY-01: Enviar cookies httpOnly en todas las requests
  withCredentials: true,
});

// Request interceptor - Agrega Authorization header si hay token
api.interceptors.request.use(
  (config) => {
    // Obtener token (sessionStorage o memoria)
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// AUTH-REFRESH: Coordinación de refresco entre pestañas.
// Web Locks asegura que SOLO una pestaña del mismo origen refresque a la vez;
// BroadcastChannel propaga el token nuevo a las demás pestañas (sessionStorage
// no se comparte entre pestañas). Esto elimina la carrera multi-pestaña que
// disparaba falsos "replay" y cerraba la sesión.
let authChannel = null;
try {
  if (typeof BroadcastChannel !== 'undefined') {
    authChannel = new BroadcastChannel('edarsa-auth');
    authChannel.onmessage = (ev) => {
      const data = (ev && ev.data) || {};
      if (data.type === 'token' && data.token) {
        // Actualizar token local sin re-emitir (evita bucles de broadcast).
        memoryToken = data.token;
        try { sessionStorage.setItem(TOKEN_STORAGE_KEY, data.token); } catch (e) {}
      } else if (data.type === 'logout') {
        clearMemoryToken();
        // Notificar a la app (AuthContext) para limpiar estado y redirigir.
        try { window.dispatchEvent(new CustomEvent('edarsa:remote-logout')); } catch (e) {}
      }
    };
  }
} catch (e) {
  authChannel = null;
}

const broadcastToken = (token) => {
  try { if (authChannel && token) authChannel.postMessage({ type: 'token', token }); } catch (e) {}
};
const broadcastLogout = () => {
  try { if (authChannel) authChannel.postMessage({ type: 'logout' }); } catch (e) {}
};

// Exponer para que AuthContext propague el cierre de sesión a las demás pestañas.
export const broadcastLogoutAllTabs = () => broadcastLogout();

// Single-flight dentro de la pestaña.
let inflightRefresh = null;

const doRefresh = async () => {
  // withCredentials envía la cookie httpOnly del refresh token (7 días).
  const resp = await axios.post(
    `${API_URL}/auth/refresh`,
    {},
    { withCredentials: true, headers: { 'X-Requested-With': 'XMLHttpRequest' } }
  );
  const t = resp.data?.token;
  if (t) {
    setMemoryToken(t);
    broadcastToken(t);
  }
  return t || null;
};

const refreshOnce = async (tokenAtFailure) => {
  // Si otra pestaña/otra request ya renovó el token, reutilizarlo sin re-llamar.
  const current = getToken();
  if (current && tokenAtFailure && current !== tokenAtFailure) {
    return current;
  }
  return await doRefresh();
};

const coordinatedRefresh = async (tokenAtFailure) => {
  if (inflightRefresh) {
    return inflightRefresh;
  }
  const run = async () => {
    if (navigator.locks && typeof navigator.locks.request === 'function') {
      // Candado compartido entre pestañas del mismo origen.
      return await navigator.locks.request('edarsa-auth-refresh', async () => refreshOnce(tokenAtFailure));
    }
    return await refreshOnce(tokenAtFailure);
  };
  inflightRefresh = run().finally(() => { inflightRefresh = null; });
  return inflightRefresh;
};

const redirectToLoginIfNeeded = () => {
  const currentPath = window.location.pathname;
  const isInteligenciaPortal = currentPath.startsWith('/inteligencia-comercial');
  const isPortalProveedores = currentPath.startsWith('/portal');
  const isLoginPage = currentPath.startsWith('/login');
  const isAuthFlowPage = currentPath.startsWith('/forgot-password') ||
                         currentPath.startsWith('/reset-password');
  if (!isInteligenciaPortal && !isPortalProveedores && !isLoginPage && !isAuthFlowPage) {
    window.location.href = '/login';
  }
};

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config || {};
    const status = error.response?.status;
    const url = originalRequest.url || '';

    // Los propios endpoints de auth NO deben intentar refrescarse (evita bucles).
    const isAuthEndpoint = url.includes('/auth/login') ||
                           url.includes('/auth/refresh') ||
                           url.includes('/auth/logout');

    // Parche de estabilidad: Evitar cierre de sesión por errores 500/502.
    // No debe convertir reportes en arreglos vacíos: eso oculta fallas reales
    // como "Reporte generado: 0 registros" cuando el backend devolvió error.
    if (status === 500 || status === 502) {
      console.warn("[API] Fallo de red detectado (500/502), manteniendo sesión...");
      if (url.includes('/reports/')) {
        return Promise.reject(error);
      }
      return Promise.resolve({ data: [] });
    }

    if (status === 401 && !isAuthEndpoint && !originalRequest._retry) {
      originalRequest._retry = true;

      const authHeader =
        (originalRequest.headers &&
          originalRequest.headers.Authorization) ||
        '';

      const tokenAtFailure =
        authHeader.startsWith('Bearer ')
          ? authHeader.slice(7)
          : null;

      const currentToken = getToken();

      // La solicitud pudo salir antes de que terminara un login o refresh.
      // Si ahora existe un token distinto, reintentar con la sesión vigente
      // y no permitir que una respuesta 401 obsoleta la elimine.
      if (
        currentToken &&
        currentToken !== tokenAtFailure
      ) {
        originalRequest.headers =
          originalRequest.headers || {};

        originalRequest.headers.Authorization =
          `Bearer ${currentToken}`;

        return api(originalRequest);
      }

      try {
        const newToken =
          await coordinatedRefresh(tokenAtFailure);

        if (newToken) {
          originalRequest.headers =
            originalRequest.headers || {};

          originalRequest.headers.Authorization =
            `Bearer ${newToken}`;

          return api(originalRequest);
        }
      } catch (refreshErr) {
        // El refresh fallo. Antes de cerrar sesion se valida que
        // ninguna operacion concurrente haya instalado un token nuevo.
      }

      const tokenAfterRefreshFailure = getToken();

      if (
        tokenAfterRefreshFailure &&
        tokenAfterRefreshFailure !== tokenAtFailure
      ) {
        originalRequest.headers =
          originalRequest.headers || {};

        originalRequest.headers.Authorization =
          `Bearer ${tokenAfterRefreshFailure}`;

        return api(originalRequest);
      }

      // Solo cerrar cuando el 401 pertenece a la sesion que sigue vigente.
      broadcastLogout();
      clearSession();
      redirectToLoginIfNeeded();
      return Promise.reject(error);
    }

    if (status === 401) {
      // 401 en endpoint de auth o tras un retry fallido → limpiar y redirigir.
      clearSession();
      redirectToLoginIfNeeded();
    }

    return Promise.reject(error);
  }
);

export default api;
