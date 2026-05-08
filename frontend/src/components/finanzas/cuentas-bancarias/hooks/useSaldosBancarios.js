import { useState, useCallback } from 'react';
import api from '../../../../lib/api';

/**
 * Hook para gestión de saldos bancarios
 * Endpoints:
 * - GET /v2/finanzas/cuentas-bancarias/{id}/saldos
 * - GET /v2/finanzas/cuentas-bancarias/{id}/saldo-actual
 * - POST /v2/finanzas/saldos-bancarios
 * - POST /v2/finanzas/saldos-bancarios/{id}/corregir
 * - POST /v2/finanzas/saldos-bancarios/{id}/cancelar
 * - GET /v2/finanzas/saldos-bancarios/{id}/historial
 * - GET /v2/finanzas/saldos-bancarios/total
 */
export function useSaldosBancarios() {
  const [saldos, setSaldos] = useState([]);
  const [saldoActual, setSaldoActual] = useState(null);
  const [saldoTotal, setSaldoTotal] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  // Listar saldos de una cuenta
  const fetchSaldos = useCallback(async (cuentaId, params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      if (params.soloVigentes !== undefined) {
        queryParams.append('solo_vigentes', params.soloVigentes);
      }
      if (params.fechaDesde) {
        queryParams.append('fecha_desde', params.fechaDesde);
      }
      if (params.fechaHasta) {
        queryParams.append('fecha_hasta', params.fechaHasta);
      }
      if (params.limite) {
        queryParams.append('limite', params.limite);
      }
      
      const url = `/v2/finanzas/cuentas-bancarias/${cuentaId}/saldos${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await api.get(url);
      setSaldos(response.data || []);
      return response.data;
    } catch (err) {
      console.error('Error cargando saldos:', err);
      setError(err.response?.data?.detail || 'Error al cargar saldos');
      setSaldos([]);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Obtener saldo actual (último vigente)
  const fetchSaldoActual = useCallback(async (cuentaId) => {
    try {
      const response = await api.get(`/v2/finanzas/cuentas-bancarias/${cuentaId}/saldo-actual`);
      setSaldoActual(response.data);
      return response.data;
    } catch (err) {
      console.error('Error obteniendo saldo actual:', err);
      setSaldoActual(null);
      // No lanzar error si no hay saldo
      if (err.response?.status === 404) {
        return null;
      }
      throw err;
    }
  }, []);

  // Obtener saldo total bancario
  const fetchSaldoTotal = useCallback(async (params = {}) => {
    try {
      const queryParams = new URLSearchParams();
      if (params.moneda) {
        queryParams.append('moneda', params.moneda);
      }
      if (params.fecha) {
        queryParams.append('fecha', params.fecha);
      }
      
      const url = `/v2/finanzas/saldos-bancarios/total${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await api.get(url);
      setSaldoTotal(response.data);
      return response.data;
    } catch (err) {
      console.error('Error obteniendo saldo total:', err);
      setSaldoTotal(null);
      throw err;
    }
  }, []);

  // Obtener historial de un saldo específico
  const fetchHistorial = useCallback(async (saldoId) => {
    setLoading(true);
    try {
      const response = await api.get(`/v2/finanzas/saldos-bancarios/${saldoId}/historial`);
      setHistorial(response.data || []);
      return response.data;
    } catch (err) {
      console.error('Error obteniendo historial:', err);
      setHistorial([]);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Capturar nuevo saldo
  const capturarSaldo = useCallback(async (data) => {
    setSaving(true);
    setError(null);
    try {
      const response = await api.post('/v2/finanzas/saldos-bancarios', data);
      return response.data;
    } catch (err) {
      console.error('Error capturando saldo:', err);
      const errorMsg = err.response?.data?.detail || 'Error al capturar saldo';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setSaving(false);
    }
  }, []);

  // Corregir saldo existente
  const corregirSaldo = useCallback(async (saldoId, data) => {
    setSaving(true);
    setError(null);
    try {
      const response = await api.post(`/v2/finanzas/saldos-bancarios/${saldoId}/corregir`, data);
      return response.data;
    } catch (err) {
      console.error('Error corrigiendo saldo:', err);
      const errorMsg = err.response?.data?.detail || 'Error al corregir saldo';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setSaving(false);
    }
  }, []);

  // Cancelar saldo
  const cancelarSaldo = useCallback(async (saldoId, motivo) => {
    setSaving(true);
    setError(null);
    try {
      const response = await api.post(`/v2/finanzas/saldos-bancarios/${saldoId}/cancelar`, {
        motivo
      });
      return response.data;
    } catch (err) {
      console.error('Error cancelando saldo:', err);
      const errorMsg = err.response?.data?.detail || 'Error al cancelar saldo';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setSaving(false);
    }
  }, []);

  return {
    saldos,
    saldoActual,
    saldoTotal,
    historial,
    loading,
    error,
    saving,
    fetchSaldos,
    fetchSaldoActual,
    fetchSaldoTotal,
    fetchHistorial,
    capturarSaldo,
    corregirSaldo,
    cancelarSaldo,
    clearError: () => setError(null)
  };
}

export default useSaldosBancarios;
