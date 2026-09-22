/**
 * Cliente API del Portal de Inteligencia Comercial.
 * ================================================
 * Soporta DOS modos de sesión:
 *   1. INTERNO (usuario del CRM): Bearer token desde sessionStorage (lib/api::getToken).
 *   2. EXTERNO (usuario del portal): cookie httpOnly `edarsa_intel_access_token`
 *      (se envía automáticamente con withCredentials). Marcamos un flag local
 *      `edarsa_intel_session` para saber que hay sesión externa activa.
 *
 * Usa una instancia axios DEDICADA (sin la redirección a /login del CRM) para que
 * el portal maneje sus propios estados de sesión. Sin mocks.
 */
import axios from 'axios';
import api, { getToken } from '../../lib/api';

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;
const INTEL_SESSION_FLAG = 'edarsa_intel_session';
// Contrato historico del Portal Inteligencia: consultas reales pueden tardar >15s en arranque frio.
// El cliente central conserva refresh/retry, pero cada request del portal usa su propio margen.
const INTEL_REQUEST_TIMEOUT_MS = 60000;

export const ESTADO = {
  CARGANDO: 'CARGANDO',
  OK: 'OK',
  SIN_SESION: 'SIN_SESION',
  SESION_EXPIRADA: 'SESION_EXPIRADA',
  SIN_PERMISO: 'SIN_PERMISO',
  SIN_DATOS: 'SIN_DATOS_SYNC',
  ERROR: 'ERROR',
};

// Instancia dedicada: envía cookie (externo) y Bearer si hay sesión interna.
const intelApi = axios.create({ baseURL: API_URL, withCredentials: true, timeout: INTEL_REQUEST_TIMEOUT_MS });
intelApi.interceptors.request.use((config) => {
  const t = getToken();
  if (t) config.headers.Authorization = `Bearer ${t}`;
  return config;
});

export const haySesionIntel = () => {
  try { return sessionStorage.getItem(INTEL_SESSION_FLAG) === '1'; } catch { return false; }
};
const setIntelSessionFlag = () => { try { sessionStorage.setItem(INTEL_SESSION_FLAG, '1'); } catch {} };
const clearIntelSessionFlag = () => { try { sessionStorage.removeItem(INTEL_SESSION_FLAG); } catch {} };

export const haySesion = () => !!getToken() || haySesionIntel();

/** Login de usuario EXTERNO. Devuelve { ok, user, error }. */
export async function loginIntel(email, password) {
  try {
    const res = await intelApi.post('/portal-intel/auth/login', { email, password });
    setIntelSessionFlag();
    return { ok: true, user: res.data?.user };
  } catch (err) {
    const detail = err?.response?.data?.detail;
    return { ok: false, error: typeof detail === 'string' ? detail : 'No se pudo iniciar sesión' };
  }
}

/** Perfil del usuario EXTERNO (valida cookie). */
export async function getMeIntel() {
  try {
    const res = await intelApi.get('/portal-intel/auth/me');
    setIntelSessionFlag();
    return { ok: true, user: res.data };
  } catch {
    clearIntelSessionFlag();
    return { ok: false, user: null };
  }
}

export async function logoutIntel() {
  try { await intelApi.post('/portal-intel/auth/logout'); } catch {}
  clearIntelSessionFlag();
}

/** GET autenticado. `path` relativo a /api. Retorna { estado, data, status }. */
export async function apiGet(path, params) {
  if (!haySesion()) return { estado: ESTADO.SIN_SESION, data: null, status: 0 };
  try {
    // Sesion interna: reutilizar el cliente central para conservar refresh/retry coordinado.
    // Sesion externa: mantener el cliente dedicado con cookie httpOnly del portal.
    const client = getToken() ? api : intelApi;
    const res = await client.get(path, { params, timeout: INTEL_REQUEST_TIMEOUT_MS });
    return { estado: ESTADO.OK, data: res.data, status: res.status };
  } catch (err) {
    const status = err?.response?.status;
    if (status === 401) return { estado: ESTADO.SESION_EXPIRADA, data: null, status };
    if (status === 403) return { estado: ESTADO.SIN_PERMISO, data: null, status };
    return { estado: ESTADO.ERROR, data: null, status: status || 0 };
  }
}

/** POST autenticado. `config` permite overrides puntuales (p.ej. timeout). */
export async function apiPost(path, payload, config = {}) {
  if (!haySesion()) return { estado: ESTADO.SIN_SESION, data: null, status: 0 };
  try {
    // Sesion interna: reutilizar el cliente central para conservar refresh/retry coordinado.
    // Sesion externa: mantener el cliente dedicado con cookie httpOnly del portal.
    const client = getToken() ? api : intelApi;
    const res = await client.post(path, payload, { timeout: INTEL_REQUEST_TIMEOUT_MS, ...config });
    return { estado: ESTADO.OK, data: res.data, status: res.status };
  } catch (err) {
    const status = err?.response?.status;
    if (status === 401) return { estado: ESTADO.SESION_EXPIRADA, data: null, status };
    if (status === 403) return { estado: ESTADO.SIN_PERMISO, data: null, status };
    return { estado: ESTADO.ERROR, data: null, status: status || 0 };
  }
}

export { intelApi };