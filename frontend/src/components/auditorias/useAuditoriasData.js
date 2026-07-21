/**
 * useAuditoriasData - Hook para datos de Auditorías Programadas
 */
import { useState, useCallback, useEffect, useMemo } from 'react';
import logger from '../../services/logger';
import api from '@/lib/api';

export function useAuditoriasData(unidadNegocioPk = '', enabled = true) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [auditorias, setAuditorias] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [calendario, setCalendario] = useState({
    eventos: [],
    mes: new Date().getMonth() + 1,
    anio: new Date().getFullYear()
  });

  const [historialDias, setHistorialDias] = useState('30');

  const unidadParams = useMemo(() => {
    const value = String(unidadNegocioPk || '').trim();
    return value && value !== 'all' ? { unidad_negocio_pk: value } : {};
  }, [unidadNegocioPk]);

  const clearData = useCallback(() => {
    setAuditorias([]);
    setKpis(null);
    setHistorial([]);
    setCalendario(prev => ({ ...prev, eventos: [] }));
  }, []);

  const fetchAuditorias = useCallback(async () => {
    if (!enabled) return;
    try {
      const response = await api.get('/v2/auditorias-programadas', {
        params: unidadParams,
      });
      setAuditorias(response.data?.items || []);
    } catch (error) {
      logger.error('Error fetching auditorias:', error);
    }
  }, [enabled, unidadParams]);

  const fetchKpis = useCallback(async () => {
    if (!enabled) return;
    try {
      const response = await api.get('/v2/auditorias-programadas/kpis', {
        params: unidadParams,
      });
      setKpis(response.data || null);
    } catch (error) {
      logger.error('Error fetching KPIs:', error);
    }
  }, [enabled, unidadParams]);

  const fetchHistorial = useCallback(async () => {
    if (!enabled) return;
    try {
      const response = await api.get('/v2/auditorias-programadas/historial', {
        params: { dias: historialDias, limit: 100, ...unidadParams }
      });
      setHistorial(response.data?.items || []);
    } catch (error) {
      logger.error('Error fetching historial:', error);
    }
  }, [enabled, historialDias, unidadParams]);

  const fetchCalendario = useCallback(async () => {
    if (!enabled) return;
    try {
      const response = await api.get('/v2/auditorias-programadas/calendario', {
        params: { anio: calendario.anio, mes: calendario.mes, ...unidadParams }
      });
      setCalendario(prev => ({ ...prev, eventos: response.data?.eventos || [] }));
    } catch (error) {
      logger.error('Error fetching calendario:', error);
    }
  }, [enabled, calendario.anio, calendario.mes, unidadParams]);

  const loadAllData = useCallback(async () => {
    if (!enabled) return;
    await Promise.all([
      fetchAuditorias(),
      fetchKpis(),
      fetchHistorial(),
      fetchCalendario()
    ]);
  }, [enabled, fetchAuditorias, fetchKpis, fetchHistorial, fetchCalendario]);

  useEffect(() => {
    const init = async () => {
      if (!enabled) {
        clearData();
        setLoading(false);
        return;
      }
      setLoading(true);
      await loadAllData();
      setLoading(false);
    };
    init();
  }, [enabled, clearData, loadAllData]);

  const handleRefresh = useCallback(async () => {
    if (!enabled) return;
    setRefreshing(true);
    await loadAllData();
    setRefreshing(false);
  }, [enabled, loadAllData]);

  const cambiarMesCalendario = (delta) => {
    setCalendario(prev => {
      let nuevoMes = prev.mes + delta;
      let nuevoAnio = prev.anio;

      if (nuevoMes > 12) { nuevoMes = 1; nuevoAnio++; }
      if (nuevoMes < 1) { nuevoMes = 12; nuevoAnio--; }

      return { ...prev, mes: nuevoMes, anio: nuevoAnio };
    });
  };

  return {
    loading,
    refreshing,
    auditorias,
    kpis,
    historial,
    calendario,
    historialDias,
    setHistorialDias,
    handleRefresh,
    loadAllData,
    fetchAuditorias,
    fetchKpis,
    fetchHistorial,
    fetchCalendario,
    cambiarMesCalendario
  };
}

export default useAuditoriasData;
