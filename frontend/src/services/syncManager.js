/**
 * SyncManager - Gestiona sincronización en background
 * Coordina la actualización de datos entre servidor y caché local
 */

import localDB, { STORES } from './localDB';

// Estado de sincronización
const syncState = {
  isOnline: navigator.onLine,
  isSyncing: false,
  lastSync: null,
  pendingSync: [],
  listeners: new Set()
};

// Configuración de TTL por tipo de datos (en minutos)
const TTL_CONFIG = {
  [STORES.KPI_TABLERO]: 15,      // KPIs: 15 minutos
  [STORES.INVENTARIOS]: 60,      // Inventarios: 1 hora
  [STORES.AUDITORIAS]: 120,      // Auditorías: 2 horas
  [STORES.CATALOGOS]: 1440,      // Catálogos: 24 horas
  [STORES.PREFETCH_CACHE]: 5     // Prefetch: 5 minutos
};

/**
 * Inicializa el SyncManager
 */
const init = () => {
  // Escuchar cambios de conectividad
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
  
  // Limpiar caché expirado cada 5 minutos
  setInterval(() => {
    localDB.cleanAllExpired();
  }, 5 * 60 * 1000);

  // Inicializar IndexedDB
  localDB.initDB();
  
  console.log('[SyncManager] Inicializado');
};

/**
 * Maneja evento online
 */
const handleOnline = () => {
  syncState.isOnline = true;
  notifyListeners({ type: 'online' });
  console.log('[SyncManager] Conexión restaurada');
  
  // Procesar sincronizaciones pendientes
  processPendingSync();
};

/**
 * Maneja evento offline
 */
const handleOffline = () => {
  syncState.isOnline = false;
  notifyListeners({ type: 'offline' });
  console.log('[SyncManager] Sin conexión');
};

/**
 * Registra un listener para cambios de estado
 * @param {Function} callback
 * @returns {Function} - Función para eliminar el listener
 */
const subscribe = (callback) => {
  syncState.listeners.add(callback);
  return () => syncState.listeners.delete(callback);
};

/**
 * Notifica a todos los listeners
 * @param {Object} event
 */
const notifyListeners = (event) => {
  syncState.listeners.forEach(callback => {
    try {
      callback(event);
    } catch (e) {
      console.error('[SyncManager] Error en listener:', e);
    }
  });
};

/**
 * Sincroniza datos con el servidor
 * @param {string} storeName - Nombre del store
 * @param {string} key - Clave única
 * @param {Function} fetchFn - Función que obtiene datos del servidor
 * @param {Object} options - Opciones adicionales
 * @returns {Object} - { data, source: 'local'|'server', updated_at }
 */
const sync = async (storeName, key, fetchFn, options = {}) => {
  const { forceRefresh = false, ttl = TTL_CONFIG[storeName] || 30 } = options;

  // 1. Intentar leer del caché local
  let localData = null;
  try {
    localData = await localDB.get(storeName, key, true); // ignoreExpiry = true para tener fallback
  } catch (e) {
    console.warn('[SyncManager] Error leyendo caché local:', e);
  }

  // 2. Si no hay conexión, devolver datos locales
  if (!syncState.isOnline) {
    if (localData) {
      console.log(`[SyncManager] Offline - usando caché: ${storeName}/${key}`);
      return {
        data: localData.data,
        source: 'local',
        updated_at: localData.updated_at,
        status: 'offline'
      };
    }
    throw new Error('Sin conexión y sin datos en caché');
  }

  // 3. Verificar si necesita actualización
  const needsRefresh = forceRefresh || !localData || await localDB.isExpired(storeName, key);

  // 4. Si tiene datos válidos y no necesita refresh, devolverlos
  if (!needsRefresh && localData) {
    console.log(`[SyncManager] Caché válido: ${storeName}/${key}`);
    return {
      data: localData.data,
      source: 'local',
      updated_at: localData.updated_at,
      status: 'cached'
    };
  }

  // 5. Obtener datos del servidor
  try {
    syncState.isSyncing = true;
    notifyListeners({ type: 'sync_start', store: storeName, key });

    const serverData = await fetchFn();
    
    // Guardar en caché
    await localDB.set(storeName, key, serverData, ttl);
    
    syncState.lastSync = new Date().toISOString();
    syncState.isSyncing = false;
    notifyListeners({ type: 'sync_complete', store: storeName, key });

    console.log(`[SyncManager] Sincronizado: ${storeName}/${key}`);
    
    return {
      data: serverData,
      source: 'server',
      updated_at: new Date().toISOString(),
      status: 'online'
    };

  } catch (error) {
    syncState.isSyncing = false;
    notifyListeners({ type: 'sync_error', store: storeName, key, error });
    
    console.error(`[SyncManager] Error sync: ${storeName}/${key}`, error);

    // Si falla pero tenemos datos locales, usarlos
    if (localData) {
      console.log(`[SyncManager] Fallback a caché: ${storeName}/${key}`);
      return {
        data: localData.data,
        source: 'local',
        updated_at: localData.updated_at,
        status: 'stale'
      };
    }

    throw error;
  }
};

/**
 * Sincronización optimista: devuelve local inmediatamente y actualiza en background
 * @param {string} storeName
 * @param {string} key
 * @param {Function} fetchFn
 * @param {Function} onUpdate - Callback cuando hay nuevos datos
 */
const syncOptimistic = async (storeName, key, fetchFn, onUpdate) => {
  // 1. Devolver datos locales inmediatamente
  let localData = null;
  try {
    localData = await localDB.get(storeName, key, true);
  } catch (e) {
    console.warn('[SyncManager] Error leyendo caché:', e);
  }

  const initialResult = localData ? {
    data: localData.data,
    source: 'local',
    updated_at: localData.updated_at,
    status: localData.expires_at && new Date(localData.expires_at) < new Date() ? 'stale' : 'cached'
  } : null;

  // 2. Actualizar en background si hay conexión
  if (syncState.isOnline) {
    // No esperar - ejecutar en background
    (async () => {
      try {
        const serverData = await fetchFn();
        await localDB.set(storeName, key, serverData, TTL_CONFIG[storeName] || 30);
        
        // Notificar solo si los datos son diferentes
        if (onUpdate && JSON.stringify(serverData) !== JSON.stringify(localData?.data)) {
          onUpdate({
            data: serverData,
            source: 'server',
            updated_at: new Date().toISOString(),
            status: 'online'
          });
        }
      } catch (e) {
        console.warn(`[SyncManager] Background sync failed: ${storeName}/${key}`, e);
      }
    })();
  }

  return initialResult;
};

/**
 * Agrega una sincronización pendiente (para cuando vuelva la conexión)
 * @param {Object} syncTask
 */
const addPendingSync = (syncTask) => {
  syncState.pendingSync.push({
    ...syncTask,
    added_at: new Date().toISOString()
  });
};

/**
 * Procesa sincronizaciones pendientes
 */
const processPendingSync = async () => {
  if (!syncState.isOnline || syncState.pendingSync.length === 0) return;

  console.log(`[SyncManager] Procesando ${syncState.pendingSync.length} syncs pendientes`);
  
  const pending = [...syncState.pendingSync];
  syncState.pendingSync = [];

  for (const task of pending) {
    try {
      await task.fetchFn();
      console.log(`[SyncManager] Sync pendiente completada: ${task.key}`);
    } catch (e) {
      console.error(`[SyncManager] Error en sync pendiente: ${task.key}`, e);
      // Re-agregar si falla
      syncState.pendingSync.push(task);
    }
  }
};

/**
 * Obtiene el estado actual de sincronización
 */
const getState = () => ({
  isOnline: syncState.isOnline,
  isSyncing: syncState.isSyncing,
  lastSync: syncState.lastSync,
  pendingCount: syncState.pendingSync.length
});

/**
 * Fuerza limpieza y re-sincronización de un store
 * @param {string} storeName
 */
const invalidate = async (storeName) => {
  await localDB.clearStore(storeName);
  console.log(`[SyncManager] Store invalidado: ${storeName}`);
};

// Exportar
const syncManager = {
  init,
  subscribe,
  sync,
  syncOptimistic,
  addPendingSync,
  getState,
  invalidate,
  TTL_CONFIG
};

export default syncManager;
