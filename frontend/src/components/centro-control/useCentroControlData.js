/**
 * useCentroControlData - Hook para datos del Centro de Control
 * Extrae toda la lógica de fetching del componente principal
 * AUDITORIA-TABLEROS-KPIS-FILTROS-01: Migrado a api centralizado
 */
import { useState, useCallback, useEffect } from 'react';
import api from '../../lib/api';
import logger from '../../services/logger';

export function useCentroControlData() {
  // Estado de carga
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Datos principales
  const [estadoGeneral, setEstadoGeneral] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [fuentes, setFuentes] = useState([]);
  const [jobs, setJobs] = useState(null);
  const [bitacora, setBitacora] = useState([]);
  const [metricas, setMetricas] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [matrizResolucion, setMatrizResolucion] = useState(null);

  // Fetchers individuales - MIGRADOS A API CENTRALIZADO
  const fetchEstadoGeneral = useCallback(async () => {
    try {
      const res = await api.get('/centro-control/estado');
      setEstadoGeneral(res.data);
    } catch (err) {
      logger.error('Error fetching estado general:', err);
    }
  }, []);

  const fetchHealthData = useCallback(async () => {
    try {
      const res = await api.get('/centro-control/salud/resumen');
      setHealthData(res.data);
    } catch (err) {
      logger.error('Error fetching health data:', err);
    }
  }, []);

  const fetchAlertas = useCallback(async () => {
    try {
      const res = await api.get('/centro-control/alertas', { params: { solo_activas: true, limite: 50 } });
      setAlertas(res.data.alertas || []);
    } catch (err) {
      logger.error('Error fetching alertas:', err);
    }
  }, []);

  const fetchFuentes = useCallback(async () => {
    try {
      const res = await api.get('/centro-control/fuentes');
      setFuentes(res.data.fuentes || []);
    } catch (err) {
      logger.error('Error fetching fuentes:', err);
    }
  }, []);

  const fetchJobs = useCallback(async () => {
    try {
      const res = await api.get('/centro-control/jobs');
      setJobs(res.data);
    } catch (err) {
      logger.error('Error fetching jobs:', err);
    }
  }, []);

  const fetchBitacora = useCallback(async () => {
    try {
      const res = await api.get('/centro-control/bitacora', { params: { limite: 50 } });
      setBitacora(res.data.entradas || []);
    } catch (err) {
      logger.error('Error fetching bitacora:', err);
    }
  }, []);

  const fetchMetricas = useCallback(async () => {
    try {
      const res = await api.get('/centro-control/metricas');
      setMetricas(res.data);
    } catch (err) {
      logger.error('Error fetching metricas:', err);
    }
  }, []);

  const fetchHistorial = useCallback(async () => {
    try {
      const res = await api.get('/centro-control/historial', { params: { limite: 50 } });
      setHistorial(res.data.eventos || []);
    } catch (err) {
      logger.error('Error fetching historial:', err);
    }
  }, []);

  const fetchMatriz = useCallback(async () => {
    try {
      const res = await api.get('/centro-control/matriz-resolucion');
      setMatrizResolucion(res.data);
    } catch (err) {
      logger.error('Error fetching matriz:', err);
    }
  }, []);

  // Cargar todos los datos
  const loadAllData = useCallback(async () => {
    await Promise.all([
      fetchEstadoGeneral(),
      fetchHealthData(),
      fetchAlertas(),
      fetchFuentes(),
      fetchJobs(),
      fetchBitacora(),
      fetchMetricas(),
      fetchHistorial(),
      fetchMatriz()
    ]);
  }, [fetchEstadoGeneral, fetchHealthData, fetchAlertas, fetchFuentes, fetchJobs, fetchBitacora, fetchMetricas, fetchHistorial, fetchMatriz]);

  // Carga inicial
  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await loadAllData();
      setLoading(false);
    };
    init();
  }, [loadAllData]);

  // Refresh manual
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadAllData();
    setRefreshing(false);
  }, [loadAllData]);

  // Agregar alerta (para WebSocket)
  const addAlerta = useCallback((alerta) => {
    if (alerta) {
      setAlertas(prev => [alerta, ...prev.filter(a => a.id !== alerta.id)]);
    }
  }, []);

  return {
    // Estado
    loading,
    refreshing,
    
    // Datos
    estadoGeneral,
    healthData,
    alertas,
    fuentes,
    jobs,
    bitacora,
    metricas,
    historial,
    matrizResolucion,
    
    // Acciones
    handleRefresh,
    loadAllData,
    addAlerta,
    fetchEstadoGeneral,
    fetchHealthData,
    fetchAlertas
  };
}

export default useCentroControlData;
