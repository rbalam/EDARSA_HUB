/**
 * useAuditoriasData - Hook para datos de Auditorías Programadas
 */
import { useState, useCallback, useEffect } from 'react';
import logger from '../../services/logger';
import api from '@/lib/api';

export function useAuditoriasData() {
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

  const fetchAuditorias = useCallback(async () => {
    try {
      const response = await api.get('/v2/auditorias-programadas');
      setAuditorias(response.data?.items || []);
    } catch (error) {
      logger.error('Error fetching auditorias:', error);
    }
  }, []);

  const fetchKpis = useCallback(async () => {
    try {
      const response = await api.get('/v2/auditorias-programadas/kpis');
      setKpis(response.data || null);
    } catch (error) {
      logger.error('Error fetching KPIs:', error);
    }
  }, []);

  const fetchHistorial = useCallback(async () => {
    try {
      const response = await api.get('/v2/auditorias-programadas/historial', {
        params: { dias: historialDias, limit: 100 }
      });
      setHistorial(response.data?.items || []);
    } catch (error) {
      logger.error('Error fetching historial:', error);
    }
  }, [historialDias]);

  const fetchCalendario = useCallback(async () => {
    try {
      const response = await api.get('/v2/auditorias-programadas/calendario', {
        params: { anio: calendario.anio, mes: calendario.mes }
      });
      setCalendario(prev => ({ ...prev, eventos: response.data?.eventos || [] }));
    } catch (error) {
      logger.error('Error fetching calendario:', error);
    }
  }, [calendario.anio, calendario.mes]);

  const loadAllData = useCallback(async () => {
    await Promise.all([
      fetchAuditorias(),
      fetchKpis(),
      fetchHistorial(),
      fetchCalendario()
    ]);
  }, [fetchAuditorias, fetchKpis, fetchHistorial, fetchCalendario]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await loadAllData();
      setLoading(false);
    };
    init();
  }, [loadAllData]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadAllData();
    setRefreshing(false);
  }, [loadAllData]);

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
