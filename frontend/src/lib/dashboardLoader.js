/**
 * Blindaje de Carga Independiente
 * Ejecuta múltiples peticiones y asegura que el fallo de una 
 * no detenga la carga de las demás.
 */
import api from '@/lib/api';

export const cargarDatosDashboard = async () => {
  const endpoints = [
    { key: 'proveedores', promise: api.get('/portal/admin/all-suppliers') },
    { key: 'roles', promise: api.get('/api/roles') },
    { key: 'menus', promise: api.get('/api/sistema/menus/usuario') }
  ];

  // Ejecutamos todo en paralelo, pero esperando que todas terminen (exitosas o no)
  const resultados = await Promise.allSettled(endpoints.map(e => e.promise));

  const dashboardData = {};

  resultados.forEach((resultado, index) => {
    const key = endpoints[index].key;
    
    if (resultado.status === 'fulfilled') {
      dashboardData[key] = resultado.value.data;
    } else {
      // FALLBACK SILENCIOSO: Si falla, logueamos el error y retornamos array vacío
      console.warn(`Error cargando ${key}, aplicando fallback silencioso:`, resultado.reason);
      dashboardData[key] = []; // Retorna [] para que el componente no se rompa
    }
  });

  return dashboardData;
};

/**
 * Carga segura de un endpoint individual con timeout y fallback
 */
export const cargarConFallback = async (endpoint, fallbackValue = [], timeoutMs = 5000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await api.get(endpoint, { signal: controller.signal });
    clearTimeout(timeoutId);
    return response.data;
  } catch (error) {
    clearTimeout(timeoutId);
    console.warn(`[cargarConFallback] ${endpoint} falló:`, error.message);
    return fallbackValue;
  }
};

/**
 * Wrapper para ejecutar múltiples cargas con gestión de estado
 */
export const cargarMultiple = async (configuracion) => {
  const resultados = {};
  
  const promesas = configuracion.map(async ({ key, endpoint, fallback = [] }) => {
    try {
      const response = await api.get(endpoint);
      resultados[key] = { data: response.data, error: null, usedFallback: false };
    } catch (error) {
      console.warn(`[cargarMultiple] ${key} (${endpoint}) falló:`, error.message);
      resultados[key] = { data: fallback, error: error.message, usedFallback: true };
    }
  });

  await Promise.allSettled(promesas);
  return resultados;
};

export default {
  cargarDatosDashboard,
  cargarConFallback,
  cargarMultiple
};
