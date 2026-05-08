/**
 * PrefetchManager - Gestiona precarga de datos al hover
 * Implementa predicción de intención del usuario
 */

import localDB, { STORES } from './localDB';
import syncManager from './syncManager';
import logger from './logger';

// Cola de prefetch pendientes
const prefetchQueue = new Map();

// Configuración
const CONFIG = {
  debounceMs: 150,       // Tiempo de espera antes de iniciar prefetch
  maxConcurrent: 3,      // Máximo de prefetch simultáneos
  hoverThreshold: 100    // Ms mínimos de hover para disparar prefetch
};

// Estado
const state = {
  activeCount: 0,
  completedCount: 0,
  failedCount: 0
};

/**
 * Registra una ruta para prefetch
 * @param {string} key - Identificador único de la ruta/datos
 * @param {Function} fetchFn - Función que obtiene los datos
 * @param {Object} options - Opciones adicionales
 */
const register = (key, fetchFn, options = {}) => {
  const { store = STORES.PREFETCH_CACHE, ttl = 5, priority = 'normal' } = options;
  
  prefetchQueue.set(key, {
    fetchFn,
    store,
    ttl,
    priority,
    status: 'pending'
  });
};

/**
 * Ejecuta prefetch para una clave
 * @param {string} key
 */
const execute = async (key) => {
  const task = prefetchQueue.get(key);
  if (!task || task.status === 'loading' || task.status === 'completed') return;

  // Verificar si ya está en caché
  const cached = await localDB.has(task.store, key);
  if (cached) {
    task.status = 'cached';
    return;
  }

  // Verificar límite de concurrencia
  if (state.activeCount >= CONFIG.maxConcurrent) {
    logger.debug(`[Prefetch] En cola: ${key} (max concurrent reached)`);
    return;
  }

  try {
    task.status = 'loading';
    state.activeCount++;
    
    logger.debug(`[Prefetch] Iniciando: ${key}`);
    const data = await task.fetchFn();
    
    await localDB.set(task.store, key, data, task.ttl);
    
    task.status = 'completed';
    state.activeCount--;
    state.completedCount++;
    
    logger.debug(`[Prefetch] Completado: ${key}`);
  } catch (error) {
    task.status = 'failed';
    state.activeCount--;
    state.failedCount++;
    logger.warn(`[Prefetch] Error: ${key}`, error);
  }
};

/**
 * Handler para eventos de hover
 * Usar con onMouseEnter en componentes React
 * @param {string} key
 * @param {Function} fetchFn
 * @param {Object} options
 */
const onHover = (key, fetchFn, options = {}) => {
  let timeoutId = null;
  let startTime = null;

  const handleEnter = () => {
    startTime = Date.now();
    
    // Registrar si no existe
    if (!prefetchQueue.has(key)) {
      register(key, fetchFn, options);
    }

    // Debounce para evitar prefetch en hover rápido
    timeoutId = setTimeout(() => {
      const hoverDuration = Date.now() - startTime;
      if (hoverDuration >= CONFIG.hoverThreshold) {
        execute(key);
      }
    }, CONFIG.debounceMs);
  };

  const handleLeave = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  return {
    onMouseEnter: handleEnter,
    onMouseLeave: handleLeave
  };
};

/**
 * Prefetch múltiples claves en batch
 * @param {Array} keys - Array de { key, fetchFn, options }
 */
const prefetchBatch = async (items) => {
  const promises = items.map(({ key, fetchFn, options }) => {
    register(key, fetchFn, options);
    return execute(key);
  });

  await Promise.allSettled(promises);
};

/**
 * Prefetch de rutas del menú al cargar la app
 * @param {Object} routes - Mapa de rutas { path: fetchFn }
 */
const prefetchMenuRoutes = (routes) => {
  // Prefetch con prioridad baja después de 2 segundos
  setTimeout(() => {
    Object.entries(routes).forEach(([path, fetchFn]) => {
      register(path, fetchFn, { priority: 'low', ttl: 10 });
    });
    
    // Ejecutar los primeros 3 en paralelo
    const keys = Object.keys(routes).slice(0, 3);
    keys.forEach(key => execute(key));
  }, 2000);
};

/**
 * Obtiene datos prefetcheados
 * @param {string} key
 * @returns {any|null}
 */
const get = async (key) => {
  const task = prefetchQueue.get(key);
  if (!task) return null;
  
  const cached = await localDB.get(task.store, key);
  return cached?.data || null;
};

/**
 * Verifica si hay datos prefetcheados disponibles
 * @param {string} key
 * @returns {boolean}
 */
const has = async (key) => {
  const task = prefetchQueue.get(key);
  if (!task) return false;
  
  return await localDB.has(task.store, key);
};

/**
 * Limpia el caché de prefetch
 */
const clear = async () => {
  await localDB.clearStore(STORES.PREFETCH_CACHE);
  prefetchQueue.clear();
  state.completedCount = 0;
  state.failedCount = 0;
};

/**
 * Obtiene estadísticas de prefetch
 */
const getStats = () => ({
  ...state,
  queueSize: prefetchQueue.size,
  pending: Array.from(prefetchQueue.values()).filter(t => t.status === 'pending').length,
  cached: Array.from(prefetchQueue.values()).filter(t => t.status === 'cached' || t.status === 'completed').length
});

// Exportar
const prefetchManager = {
  register,
  execute,
  onHover,
  prefetchBatch,
  prefetchMenuRoutes,
  get,
  has,
  clear,
  getStats,
  CONFIG
};

export default prefetchManager;
