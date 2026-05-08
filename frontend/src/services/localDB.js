/**
 * LocalDB - Wrapper para IndexedDB
 * Proporciona acceso rápido a datos locales para arquitectura Local-First
 */

import logger from './logger';

const DB_NAME = 'edarsa_hub_local';
const DB_VERSION = 1;

// Stores (tablas) de la base de datos local
const STORES = {
  KPI_TABLERO: 'kpis_tablero',
  INVENTARIOS: 'inventarios',
  AUDITORIAS: 'auditorias',
  CATALOGOS: 'catalogos',
  SYNC_LOG: 'sync_log',
  PREFETCH_CACHE: 'prefetch_cache'
};

let dbInstance = null;

/**
 * Inicializa la base de datos IndexedDB
 */
const initDB = () => {
  return new Promise((resolve, reject) => {
    if (dbInstance) {
      resolve(dbInstance);
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => {
      logger.error('Error abriendo IndexedDB:', request.error);
      reject(request.error);
    };

    request.onsuccess = () => {
      dbInstance = request.result;
      logger.debug('IndexedDB inicializada correctamente');
      resolve(dbInstance);
    };

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Crear stores si no existen
      Object.values(STORES).forEach(storeName => {
        if (!db.objectStoreNames.contains(storeName)) {
          const store = db.createObjectStore(storeName, { keyPath: 'id' });
          store.createIndex('updated_at', 'updated_at', { unique: false });
          store.createIndex('expires_at', 'expires_at', { unique: false });
          logger.debug(`Store "${storeName}" creado`);
        }
      });
    };
  });
};

/**
 * Guarda datos en un store
 * @param {string} storeName - Nombre del store
 * @param {string} key - Clave única
 * @param {any} data - Datos a guardar
 * @param {number} ttlMinutes - Tiempo de vida en minutos (default: 30)
 */
const set = async (storeName, key, data, ttlMinutes = 30) => {
  const db = await initDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    
    const now = new Date();
    const record = {
      id: key,
      data: data,
      updated_at: now.toISOString(),
      expires_at: new Date(now.getTime() + ttlMinutes * 60000).toISOString()
    };

    const request = store.put(record);

    request.onsuccess = () => {
      logger.debug(`[LocalDB] Guardado: ${storeName}/${key}`);
      resolve(true);
    };

    request.onerror = () => {
      logger.error(`[LocalDB] Error guardando: ${storeName}/${key}`, request.error);
      reject(request.error);
    };
  });
};

/**
 * Obtiene datos de un store
 * @param {string} storeName - Nombre del store
 * @param {string} key - Clave única
 * @param {boolean} ignoreExpiry - Ignorar expiración (útil para offline)
 * @returns {any|null} - Datos o null si no existe/expiró
 */
const get = async (storeName, key, ignoreExpiry = false) => {
  const db = await initDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.get(key);

    request.onsuccess = () => {
      const record = request.result;
      
      if (!record) {
        resolve(null);
        return;
      }

      // Verificar expiración
      if (!ignoreExpiry && record.expires_at) {
        const expiresAt = new Date(record.expires_at);
        if (expiresAt < new Date()) {
          logger.debug(`[LocalDB] Expirado: ${storeName}/${key}`);
          resolve(null);
          return;
        }
      }

      logger.debug(`[LocalDB] Leído: ${storeName}/${key}`);
      resolve(record);
    };

    request.onerror = () => {
      logger.error(`[LocalDB] Error leyendo: ${storeName}/${key}`, request.error);
      reject(request.error);
    };
  });
};

/**
 * Verifica si existe un registro y no ha expirado
 * @param {string} storeName - Nombre del store
 * @param {string} key - Clave única
 * @returns {boolean}
 */
const has = async (storeName, key) => {
  const record = await get(storeName, key);
  return record !== null;
};

/**
 * Verifica si un registro ha expirado
 * @param {string} storeName - Nombre del store
 * @param {string} key - Clave única
 * @returns {boolean}
 */
const isExpired = async (storeName, key) => {
  const db = await initDB();
  
  return new Promise((resolve) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.get(key);

    request.onsuccess = () => {
      const record = request.result;
      
      if (!record) {
        resolve(true); // No existe = expirado
        return;
      }

      if (record.expires_at) {
        const expiresAt = new Date(record.expires_at);
        resolve(expiresAt < new Date());
      } else {
        resolve(false);
      }
    };

    request.onerror = () => resolve(true);
  });
};

/**
 * Elimina un registro
 * @param {string} storeName - Nombre del store
 * @param {string} key - Clave única
 */
const remove = async (storeName, key) => {
  const db = await initDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.delete(key);

    request.onsuccess = () => {
      logger.debug(`[LocalDB] Eliminado: ${storeName}/${key}`);
      resolve(true);
    };

    request.onerror = () => reject(request.error);
  });
};

/**
 * Obtiene todos los registros de un store
 * @param {string} storeName - Nombre del store
 * @param {boolean} ignoreExpiry - Ignorar expiración
 * @returns {Array}
 */
const getAll = async (storeName, ignoreExpiry = false) => {
  const db = await initDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();

    request.onsuccess = () => {
      let records = request.result || [];
      
      if (!ignoreExpiry) {
        const now = new Date();
        records = records.filter(r => {
          if (!r.expires_at) return true;
          return new Date(r.expires_at) >= now;
        });
      }

      resolve(records);
    };

    request.onerror = () => reject(request.error);
  });
};

/**
 * Limpia registros expirados de un store
 * @param {string} storeName - Nombre del store
 */
const cleanExpired = async (storeName) => {
  const db = await initDB();
  const now = new Date();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.openCursor();
    let deleted = 0;

    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        const record = cursor.value;
        if (record.expires_at && new Date(record.expires_at) < now) {
          cursor.delete();
          deleted++;
        }
        cursor.continue();
      } else {
        logger.debug(`[LocalDB] Limpieza ${storeName}: ${deleted} registros eliminados`);
        resolve(deleted);
      }
    };

    request.onerror = () => reject(request.error);
  });
};

/**
 * Limpia todos los stores de registros expirados
 */
const cleanAllExpired = async () => {
  for (const storeName of Object.values(STORES)) {
    await cleanExpired(storeName);
  }
};

/**
 * Limpia completamente un store
 * @param {string} storeName - Nombre del store
 */
const clearStore = async (storeName) => {
  const db = await initDB();
  
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.clear();

    request.onsuccess = () => {
      logger.debug(`[LocalDB] Store limpiado: ${storeName}`);
      resolve(true);
    };

    request.onerror = () => reject(request.error);
  });
};

/**
 * Obtiene estadísticas de uso
 */
const getStats = async () => {
  const stats = {};
  
  for (const [name, storeName] of Object.entries(STORES)) {
    const records = await getAll(storeName, true);
    const validRecords = await getAll(storeName, false);
    stats[name] = {
      total: records.length,
      valid: validRecords.length,
      expired: records.length - validRecords.length
    };
  }
  
  return stats;
};

// Exportar
const localDB = {
  STORES,
  initDB,
  set,
  get,
  has,
  isExpired,
  remove,
  getAll,
  cleanExpired,
  cleanAllExpired,
  clearStore,
  getStats
};

export default localDB;
export { STORES };
