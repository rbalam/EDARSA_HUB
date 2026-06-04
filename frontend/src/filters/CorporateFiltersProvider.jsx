import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import {
  fetchCorporateFiltersBootstrap,
  resolveCorporateFilters
} from "./corporateFiltersApi";

import { resetPreviewFilterCache } from "./previewCacheReset";

const CorporateFiltersContext = createContext(null);

export function CorporateFiltersProvider({ scope = "global", children }) {
  const [filters, setFilters] = useState({});
  const [dependencies, setDependencies] = useState({});
  const [selected, setSelected] = useState({});
  const [status, setStatus] = useState({ status: "LOADING" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [transport, setTransport] = useState(null);
  
  // Ref para saber si el componente está montado
  const isMountedRef = useRef(true);
  
  // Cleanup en unmount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const storageKey = `edarsa_filter_state_v1_${scope}`;

  useEffect(() => {
    resetPreviewFilterCache();
  }, []);

  useEffect(() => {
    const raw = sessionStorage.getItem(storageKey);
    if (!raw) return;

    try {
      setSelected(JSON.parse(raw));
    } catch {
      sessionStorage.removeItem(storageKey);
    }
  }, [storageKey]);

  useEffect(() => {
    sessionStorage.setItem(storageKey, JSON.stringify(selected || {}));
  }, [storageKey, selected]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await fetchCorporateFiltersBootstrap(scope);
      
      // Verificar si el componente sigue montado antes de actualizar estado
      if (!isMountedRef.current) {
        return;
      }
      
      const loadedFilters = data.filters || {};

      setFilters(loadedFilters);
      setDependencies(data.dependencies || {});
      setStatus(data.status || { status: "OK" });
      setTransport(data._transport || null);

      setSelected(prev => {
        const next = { ...(prev || {}) };

        Object.entries(loadedFilters).forEach(([key, values]) => {
          if (Array.isArray(values) && values.length === 1 && !next[key]) {
            next[key] = values[0].id;
          }
        });

        return next;
      });

      if (!data.success) {
        setError(data?.status?.message || data?.message || "Error cargando filtros corporativos");
      }
    } catch (err) {
      // Ignorar errores si el componente se desmontó
      if (!isMountedRef.current) {
        return;
      }
      
      setError(err.message);
      setStatus({
        status: "SYNC_ERROR",
        remote_connections_required: false,
        message: err.message
      });
      setTransport(null);
    } finally {
      // Solo cambiar loading si sigue montado
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [scope]);

  useEffect(() => {
    reload();
  }, [reload]);

  const setFilterValue = useCallback(async (key, value) => {
    const nextSelected = {
      ...selected,
      [key]: value
    };

    const affectedChildren = Object.entries(dependencies || {})
      .filter(([, parents]) => Array.isArray(parents) && parents.includes(key))
      .map(([child]) => child);

    for (const child of affectedChildren) {
      delete nextSelected[child];
    }

    setSelected(nextSelected);

    if (affectedChildren.length > 0) {
      try {
        const resolved = await resolveCorporateFilters(scope, nextSelected, affectedChildren);
        setFilters(prev => ({
          ...prev,
          ...(resolved.filters || {})
        }));
        setStatus(resolved.status || { status: "OK" });
      } catch (err) {
        setError(err.message);
      }
    }
  }, [selected, dependencies, scope]);

  const clearFilters = useCallback(() => {
    setSelected({});
    sessionStorage.removeItem(storageKey);
    reload();
  }, [storageKey, reload]);

  const value = useMemo(() => ({
    scope,
    filters,
    dependencies,
    selected,
    status,
    loading,
    error,
    setFilterValue,
    clearFilters,
    reload
  }), [
    scope,
    filters,
    dependencies,
    selected,
    status,
    loading,
    error,
    setFilterValue,
    clearFilters,
    reload
  ]);

  return (
    <CorporateFiltersContext.Provider value={value}>
      {children}
    </CorporateFiltersContext.Provider>
  );
}

export function useCorporateFilters() {
  const context = useContext(CorporateFiltersContext);

  if (!context) {
    throw new Error("useCorporateFilters debe usarse dentro de CorporateFiltersProvider");
  }

  return context;
}
