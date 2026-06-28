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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = `${BACKEND_URL}/api`;

// Token key en sessionStorage
const TOKEN_STORAGE_KEY = 'edarsa_memory_token';

// Token en memoria como fallback adicional
let memoryToken = null;

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

// AUTH-REFRESH: Estado de refresco silencioso (single-flight).
// Evita que múltiples 401 concurrentes disparen varios /auth/refresh.
let isRefreshing = false;
let refreshSubscribers = [];

const subscribeTokenRefresh = (cb) => {
  refreshSubscribers.push(cb);
};

const onRefreshed = (token) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
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

      // Si ya hay un refresco en curso, encolar esta request hasta que termine.
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((newToken) => {
            if (newToken) {
              originalRequest.headers = originalRequest.headers || {};
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              resolve(api(originalRequest));
            } else {
              reject(error);
            }
          });
        });
      }

      isRefreshing = true;
      try {
        // Usar axios "crudo" (no la instancia) para no re-disparar este interceptor.
        // withCredentials envía la cookie httpOnly del refresh token (7 días).
        const refreshResp = await axios.post(
          `${API_URL}/auth/refresh`,
          {},
          { withCredentials: true, headers: { 'X-Requested-With': 'XMLHttpRequest' } }
        );
        const newToken = refreshResp.data?.token;
        isRefreshing = false;

        if (newToken) {
          setMemoryToken(newToken);
          onRefreshed(newToken);
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        }
        // Sin token en la respuesta → tratar como fallo de sesión.
        onRefreshed(null);
      } catch (refreshErr) {
        isRefreshing = false;
        onRefreshed(null);
      }

      // El refresh falló (refresh token expirado/ inválido) → cerrar sesión.
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
