import { useState, useCallback } from 'react';
import api from '../../../../lib/api';

/**
 * Hook para CRUD de cuentas bancarias
 * Endpoints:
 * - GET /api/v2/finanzas/cuentas-bancarias
 * - GET /api/v2/finanzas/cuentas-bancarias/{id}
 * - POST /api/v2/finanzas/cuentas-bancarias
 * - PUT /api/v2/finanzas/cuentas-bancarias/{id}
 * - POST /api/v2/finanzas/cuentas-bancarias/{id}/desactivar
 */
export function useCuentasBancarias() {
  const [cuentas, setCuentas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  // Listar cuentas bancarias
  const fetchCuentas = useCallback(async (params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      if (params.soloActivas !== undefined) {
        queryParams.append('solo_activas', params.soloActivas);
      }
      if (params.moneda) {
        queryParams.append('moneda', params.moneda);
      }
      if (params.bancoId) {
        queryParams.append('banco_id', params.bancoId);
      }
      
      const url = `/v2/finanzas/cuentas-bancarias${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await api.get(url);
      setCuentas(response.data?.cuentas || response.data || []);
      return response.data;
    } catch (err) {
      console.error('Error cargando cuentas bancarias:', err);
      setError(err.response?.data?.detail || 'Error al cargar cuentas bancarias');
      setCuentas([]);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Obtener cuenta por ID
  const getCuenta = useCallback(async (id) => {
    try {
      const response = await api.get(`/v2/finanzas/cuentas-bancarias/${id}`);
      return response.data;
    } catch (err) {
      console.error('Error obteniendo cuenta:', err);
      throw err;
    }
  }, []);

  // Crear cuenta bancaria
  const crearCuenta = useCallback(async (data) => {
    setSaving(true);
    setError(null);
    try {
      const response = await api.post('/v2/finanzas/cuentas-bancarias', data);
      // Refrescar lista
      await fetchCuentas();
      return response.data;
    } catch (err) {
      console.error('Error creando cuenta:', err);
      const errorMsg = err.response?.data?.detail || 'Error al crear cuenta bancaria';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setSaving(false);
    }
  }, [fetchCuentas]);

  // Editar cuenta bancaria (solo alias y es_principal)
  const editarCuenta = useCallback(async (id, data) => {
    setSaving(true);
    setError(null);
    try {
      const response = await api.put(`/v2/finanzas/cuentas-bancarias/${id}`, data);
      // Refrescar lista
      await fetchCuentas();
      return response.data;
    } catch (err) {
      console.error('Error editando cuenta:', err);
      const errorMsg = err.response?.data?.detail || 'Error al editar cuenta bancaria';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setSaving(false);
    }
  }, [fetchCuentas]);

  // Desactivar cuenta bancaria
  const desactivarCuenta = useCallback(async (id, motivo) => {
    setSaving(true);
    setError(null);
    try {
      const response = await api.post(`/v2/finanzas/cuentas-bancarias/${id}/desactivar`, {
        motivo
      });
      // Refrescar lista
      await fetchCuentas();
      return response.data;
    } catch (err) {
      console.error('Error desactivando cuenta:', err);
      const errorMsg = err.response?.data?.detail || 'Error al desactivar cuenta bancaria';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setSaving(false);
    }
  }, [fetchCuentas]);

  return {
    cuentas,
    loading,
    error,
    saving,
    fetchCuentas,
    getCuenta,
    crearCuenta,
    editarCuenta,
    desactivarCuenta,
    clearError: () => setError(null)
  };
}

export default useCuentasBancarias;
