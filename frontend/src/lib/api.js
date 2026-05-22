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
const getToken = () => {
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
  headers: {
    'Content-Type': 'application/json',
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
    if (error.response?.status === 401) {
      // NO limpiar token aquí - puede causar race conditions
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
