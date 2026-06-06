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

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const currentPath = window.location.pathname;
    
    // Fix: Excluir las rutas del portal de Inteligencia de la redirección forzada al CRM
    const isInteligenciaPortal = currentPath.startsWith('/inteligencia-comercial');
    const isPortalProveedores = currentPath.startsWith('/portal');
    const isLoginPage = currentPath.startsWith('/login');
    
    // Parche de estabilidad: Evitar cierre de sesión por errores 500/502
    if (error.response?.status === 500 || error.response?.status === 502) {
      console.warn("[API] Fallo de red detectado (500/502), manteniendo sesión...");
      return Promise.resolve({ data: [] });
    }
    
    if (error.response?.status === 401) {
      clearSession();
      // Solo redirigir si NO estamos en una de las zonas públicas/app-independientes
      if (!isInteligenciaPortal && !isPortalProveedores && !isLoginPage) {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
