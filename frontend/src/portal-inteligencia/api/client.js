/**
 * Cliente API ÚNICO del Portal de Inteligencia Comercial.
 * ======================================================
 * Reutiliza el cliente canónico del CRM (`lib/api.js`):
 *   - Token operativo vigente (Bearer) desde sessionStorage (`edarsa_memory_token`).
 *   - Interceptor con refresh silencioso de sesión.
 *   - En rutas /inteligencia-comercial NO fuerza redirección a /login.
 * Sin cookies de demo, sin datos mock. Devuelve estados canónicos para que
 * cada pantalla muestre estados honestos.
 */
import api, { getToken } from '../../lib/api';

export const ESTADO = {
  CARGANDO: 'CARGANDO',
  OK: 'OK',
  SIN_SESION: 'SIN_SESION',
  SESION_EXPIRADA: 'SESION_EXPIRADA',
  SIN_PERMISO: 'SIN_PERMISO',
  SIN_DATOS: 'SIN_DATOS_SYNC',
  ERROR: 'ERROR',
};

export const haySesion = () => !!getToken();

/**
 * GET autenticado. `path` es relativo a /api (p.ej. '/inteligencia/dashboard').
 * Retorna { estado, data, status }.
 */
export async function apiGet(path, params) {
  if (!getToken()) return { estado: ESTADO.SIN_SESION, data: null, status: 0 };
  try {
    const res = await api.get(path, { params, timeout: 35000 });
    return { estado: ESTADO.OK, data: res.data, status: res.status };
  } catch (err) {
    const status = err?.response?.status;
    if (status === 401) return { estado: ESTADO.SESION_EXPIRADA, data: null, status };
    if (status === 403) return { estado: ESTADO.SIN_PERMISO, data: null, status };
    return { estado: ESTADO.ERROR, data: null, status: status || 0 };
  }
}

/**
 * POST autenticado. Retorna { estado, data, status }.
 */
export async function apiPost(path, payload) {
  if (!getToken()) return { estado: ESTADO.SIN_SESION, data: null, status: 0 };
  try {
    const res = await api.post(path, payload, { timeout: 35000 });
    return { estado: ESTADO.OK, data: res.data, status: res.status };
  } catch (err) {
    const status = err?.response?.status;
    if (status === 401) return { estado: ESTADO.SESION_EXPIRADA, data: null, status };
    if (status === 403) return { estado: ESTADO.SIN_PERMISO, data: null, status };
    return { estado: ESTADO.ERROR, data: null, status: status || 0 };
  }
}
