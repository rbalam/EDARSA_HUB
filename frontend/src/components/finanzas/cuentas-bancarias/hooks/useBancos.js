import { useState, useEffect, useCallback } from 'react';
import api from '../../../../lib/api';

/**
 * Hook para obtener catálogo de bancos desde EDARSAHUB
 */
export function useBancos() {
  const [bancos, setBancos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBancos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/v2/finanzas/bancos');
      setBancos(response.data?.bancos || response.data || []);
    } catch (err) {
      console.error('Error cargando bancos:', err);
      setError(err.response?.data?.detail || 'Error al cargar catálogo de bancos');
      setBancos([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBancos();
  }, [fetchBancos]);

  return {
    bancos,
    loading,
    error,
    refetch: fetchBancos
  };
}

export default useBancos;
