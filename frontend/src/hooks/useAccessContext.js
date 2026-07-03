import { useCallback, useEffect, useState } from "react";
import { fetchAccessContext, selectAccessUnit } from "../services/accessContextService";

export function useAccessContext() {
  const [context, setContext] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadContext = useCallback(async (unidadNegocioId = null) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAccessContext(unidadNegocioId);
      setContext(data);

      if (data?.unidad_activa) {
        sessionStorage.setItem("edarsahub_unidad_activa", data.unidad_activa);
        localStorage.setItem("edarsahub_unidad_activa", data.unidad_activa);
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const changeUnit = useCallback(async (unidadNegocioId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await selectAccessUnit(unidadNegocioId);
      setContext(data);

      if (data?.unidad_activa) {
        sessionStorage.setItem("edarsahub_unidad_activa", data.unidad_activa);
        localStorage.setItem("edarsahub_unidad_activa", data.unidad_activa);
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const unidadGuardada =
      sessionStorage.getItem("edarsahub_unidad_activa") ||
      localStorage.getItem("edarsahub_unidad_activa");
    loadContext(unidadGuardada || null);
  }, [loadContext]);

  return {
    context,
    loading,
    error,
    reloadContext: loadContext,
    changeUnit,
  };
}
