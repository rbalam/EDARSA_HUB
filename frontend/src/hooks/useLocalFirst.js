/**
 * useLocalFirst - Hook React para arquitectura Local-First
 * Proporciona acceso fácil a datos con caché local y sincronización automática
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import localDB, { STORES } from '../services/localDB';
import syncManager from '../services/syncManager';

/**
 * Hook principal para Local-First
 * @param {string} storeName - Nombre del store en IndexedDB
 * @param {string} cacheKey - Clave única para el caché
 * @param {Function} fetchFn - Función async que obtiene datos del servidor
 * @param {Object} options - Opciones adicionales
 * @returns {Object} - { data, loading, error, source, updatedAt, refresh, isStale }
 */
const useLocalFirst = (storeName, cacheKey, fetchFn, options = {}) => {
  const {
    enabled = true,           // Si debe ejecutar automáticamente
    ttl = null,               // TTL personalizado (usa default si null)
    onSuccess = null,         // Callback en éxito
    onError = null,           // Callback en error
    refetchOnFocus = false,   // Re-fetch cuando la ventana obtiene foco
    refetchInterval = null    // Intervalo de re-fetch automático (ms)
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [source, setSource] = useState(null); // 'local' | 'server'
  const [status, setStatus] = useState(null); // 'online' | 'offline' | 'cached' | 'stale'
  const [updatedAt, setUpdatedAt] = useState(null);
  
  const mountedRef = useRef(true);
  const fetchFnRef = useRef(fetchFn);
  fetchFnRef.current = fetchFn;

  /**
   * Carga datos usando estrategia local-first
   */
  const loadData = useCallback(async (forceRefresh = false) => {
    if (!enabled || !cacheKey) return;

    try {
      setLoading(true);
      setError(null);

      const result = await syncManager.sync(
        storeName,
        cacheKey,
        fetchFnRef.current,
        { forceRefresh, ttl }
      );

      if (mountedRef.current) {
        setData(result.data);
        setSource(result.source);
        setStatus(result.status);
        setUpdatedAt(result.updated_at);
        setLoading(false);
        
        if (onSuccess) onSuccess(result);
      }

      return result;

    } catch (err) {
      if (mountedRef.current) {
        setError(err);
        setLoading(false);
        setStatus('error');
        
        if (onError) onError(err);
      }
      throw err;
    }
  }, [storeName, cacheKey, enabled, ttl, onSuccess, onError]);

  /**
   * Carga optimista: devuelve local inmediato + actualiza en background
   */
  const loadOptimistic = useCallback(async () => {
    if (!enabled || !cacheKey) return;

    try {
      setError(null);

      // Obtener datos locales inmediatamente
      const localResult = await syncManager.syncOptimistic(
        storeName,
        cacheKey,
        fetchFnRef.current,
        // Callback para actualización en background
        (newResult) => {
          if (mountedRef.current) {
            setData(newResult.data);
            setSource(newResult.source);
            setStatus(newResult.status);
            setUpdatedAt(newResult.updated_at);
          }
        }
      );

      if (mountedRef.current && localResult) {
        setData(localResult.data);
        setSource(localResult.source);
        setStatus(localResult.status);
        setUpdatedAt(localResult.updated_at);
        setLoading(false);
      } else if (mountedRef.current) {
        // No hay datos locales, hacer fetch normal
        setLoading(true);
        await loadData();
      }

    } catch (err) {
      if (mountedRef.current) {
        setError(err);
        setLoading(false);
      }
    }
  }, [storeName, cacheKey, enabled, loadData]);

  /**
   * Fuerza actualización desde servidor
   */
  const refresh = useCallback(() => {
    return loadData(true);
  }, [loadData]);

  /**
   * Invalida el caché y recarga
   */
  const invalidate = useCallback(async () => {
    await localDB.remove(storeName, cacheKey);
    return loadData(true);
  }, [storeName, cacheKey, loadData]);

  // Efecto principal: cargar datos al montar
  useEffect(() => {
    mountedRef.current = true;
    loadOptimistic();

    return () => {
      mountedRef.current = false;
    };
  }, [loadOptimistic]);

  // Re-fetch cuando la ventana obtiene foco
  useEffect(() => {
    if (!refetchOnFocus) return;

    const handleFocus = () => {
      loadData();
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [refetchOnFocus, loadData]);

  // Re-fetch periódico
  useEffect(() => {
    if (!refetchInterval) return;

    const interval = setInterval(() => {
      loadData();
    }, refetchInterval);

    return () => clearInterval(interval);
  }, [refetchInterval, loadData]);

  // Escuchar cambios de conectividad
  useEffect(() => {
    const unsubscribe = syncManager.subscribe((event) => {
      if (event.type === 'online' && status === 'offline') {
        // Volvió la conexión, recargar datos
        loadData();
      }
    });

    return unsubscribe;
  }, [status, loadData]);

  return {
    data,
    loading,
    error,
    source,
    status,
    updatedAt,
    refresh,
    invalidate,
    isStale: status === 'stale',
    isOffline: status === 'offline',
    isOnline: status === 'online' || status === 'cached'
  };
};

/**
 * Hook para prefetch de datos (sin renderizar)
 * @param {string} storeName
 * @param {string} cacheKey
 * @param {Function} fetchFn
 */
const usePrefetch = (storeName, cacheKey, fetchFn) => {
  const prefetch = useCallback(async () => {
    // Solo prefetch si no está en caché
    const exists = await localDB.has(storeName, cacheKey);
    if (!exists) {
      try {
        const data = await fetchFn();
        await localDB.set(storeName, cacheKey, data, syncManager.TTL_CONFIG[storeName] || 5);
        console.log(`[Prefetch] Cargado: ${storeName}/${cacheKey}`);
      } catch (e) {
        console.warn(`[Prefetch] Error: ${storeName}/${cacheKey}`, e);
      }
    }
  }, [storeName, cacheKey, fetchFn]);

  return prefetch;
};

/**
 * Hook para estado de sincronización global
 */
const useSyncStatus = () => {
  const [syncState, setSyncState] = useState(syncManager.getState());

  useEffect(() => {
    const unsubscribe = syncManager.subscribe(() => {
      setSyncState(syncManager.getState());
    });

    return unsubscribe;
  }, []);

  return syncState;
};

export default useLocalFirst;
export { usePrefetch, useSyncStatus, STORES };
