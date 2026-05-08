/**
 * EDARSA HUB - API Client
 * =======================
 * Cliente axios centralizado para todas las llamadas API.
 * 
 * FASE AUTH-SECURITY-01:
 * - withCredentials: true para enviar cookies httpOnly automáticamente
 * - Fallback: token en memoria + Authorization header (para CORS restrictivo)
 * - Token NUNCA en localStorage/sessionStorage (seguridad XSS)
 */

import axios from 'axios';
import { clearSession } from '../services/authStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = `${BACKEND_URL}/api`;

// Token en memoria - Fallback cuando el proxy/CORS bloquea cookies
// Se limpia al cerrar la página (no persiste)
let memoryToken = null;

/**
 * Setear token en memoria (usado por AuthContext después del login)
 */
export const setMemoryToken = (token) => {
  memoryToken = token;
};

/**
 * Limpiar token de memoria (usado por logout)
 */
export const clearMemoryToken = () => {
  memoryToken = null;
};

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // FASE AUTH-SECURITY-01: Enviar cookies httpOnly en todas las requests
  withCredentials: true,
});

// Request interceptor - Agrega Authorization header si hay token en memoria
api.interceptors.request.use(
  (config) => {
    // Si hay token en memoria, agregarlo como fallback para CORS
    if (memoryToken) {
      config.headers.Authorization = `Bearer ${memoryToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // NO limpiar memoryToken aquí - puede causar race conditions
      // La limpieza se hace en logout explícito
      // Solo limpiar cache de sesión y redirigir si no estamos en login
      clearSession();
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/portal')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
