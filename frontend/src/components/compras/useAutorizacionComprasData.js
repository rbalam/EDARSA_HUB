/**
 * useAutorizacionComprasData - Hook para datos de Autorización de Compras
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
import axios from 'axios';
import logger from '../../services/logger';
import { fetchUnidadesNegocio, getServerIdFromUnidad } from '../../services/unidadesNegocioService';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function useAutorizacionComprasData() {
  // Unidades de Negocio
  const [unidadesNegocio, setUnidadesNegocio] = useState([]);
  const [selectedUnidad, setSelectedUnidad] = useState('');
  const [loadingUnidades, setLoadingUnidades] = useState(true);
  
  // Almacenes
  const [almacenes, setAlmacenes] = useState([]);
  const [selectedAlmacenes, setSelectedAlmacenes] = useState([]);
  const [todosAlmacenes, setTodosAlmacenes] = useState(false);
  
  // Inventarios
  const [inventariosFisicos, setInventariosFisicos] = useState([]);
  const [inventariosFiltrados, setInventariosFiltrados] = useState([]);
  
  // Pedidos
  const [pedidosVigentes, setPedidosVigentes] = useState([]);
  
  // Loading states
  const [loading, setLoading] = useState(false);

  // Derived values
  const selectedServer = useMemo(() => {
    return getServerIdFromUnidad(unidadesNegocio, selectedUnidad);
  }, [unidadesNegocio, selectedUnidad]);

  const serverData = useMemo(() => {
    const unidad = unidadesNegocio.find(u => u.id === selectedUnidad);
    return unidad ? {
      id: unidad.server_id,
      name: unidad.nombre,
      system_type: unidad.system_type
    } : null;
  }, [unidadesNegocio, selectedUnidad]);

  const selectedSucursal = useMemo(() => {
    const unidad = unidadesNegocio.find(u => u.id === selectedUnidad);
    if (!unidad) return '';
    return unidad.sucursal_origen_id || unidad.sucursales?.[0]?.id || unidad.nombre;
  }, [unidadesNegocio, selectedUnidad]);

  // Fetch unidades
  useEffect(() => {
    const loadUnidades = async () => {
      setLoadingUnidades(true);
      try {
        const data = await fetchUnidadesNegocio();
        setUnidadesNegocio(data);
        if (data.length > 0) {
          setSelectedUnidad(data[0].id);
        }
      } catch (error) {
        logger.error('Error loading unidades:', error);
      } finally {
        setLoadingUnidades(false);
      }
    };
    loadUnidades();
  }, []);

  // Fetch almacenes when server changes
  const fetchAlmacenes = useCallback(async () => {
    if (!selectedServer) return;
    
    try {
      const response = await axios.get(`${API_URL}/api/compras/almacenes`, {
        params: { server_id: selectedServer },
        withCredentials: true
      });
      setAlmacenes(response.data.almacenes || []);
      setSelectedAlmacenes([]);
      setTodosAlmacenes(false);
    } catch (error) {
      logger.error('Error fetching almacenes:', error);
      setAlmacenes([]);
    }
  }, [selectedServer]);

  useEffect(() => {
    if (selectedServer) {
      fetchAlmacenes();
    }
  }, [selectedServer, fetchAlmacenes]);

  // Fetch inventarios físicos
  const fetchInventariosFisicos = useCallback(async () => {
    if (!selectedServer || selectedAlmacenes.length === 0) {
      setInventariosFisicos([]);
      return;
    }
    
    try {
      const almacenesParam = todosAlmacenes 
        ? almacenes.map(a => a.id).join(',')
        : selectedAlmacenes.join(',');
      
      const response = await axios.get(`${API_URL}/api/compras/inventarios-fisicos`, {
        params: { 
          server_id: selectedServer,
          almacenes: almacenesParam
        },
        withCredentials: true
      });
      
      setInventariosFisicos(response.data.inventarios || []);
      setInventariosFiltrados(response.data.inventarios || []);
    } catch (error) {
      logger.error('Error fetching inventarios:', error);
      setInventariosFisicos([]);
    }
  }, [selectedServer, selectedAlmacenes, todosAlmacenes, almacenes]);

  // Fetch pedidos vigentes
  const fetchPedidosVigentes = useCallback(async () => {
    if (!selectedServer) return;
    
    try {
      const response = await axios.get(`${API_URL}/api/compras/pedidos-vigentes`, {
        params: { server_id: selectedServer },
        withCredentials: true
      });
      setPedidosVigentes(response.data.pedidos || []);
    } catch (error) {
      logger.error('Error fetching pedidos:', error);
      setPedidosVigentes([]);
    }
  }, [selectedServer]);

  // Toggle almacén selection
  const toggleAlmacen = useCallback((almacenId) => {
    setSelectedAlmacenes(prev => {
      if (prev.includes(almacenId)) {
        return prev.filter(id => id !== almacenId);
      }
      return [...prev, almacenId];
    });
    setTodosAlmacenes(false);
  }, []);

  // Toggle todos los almacenes
  const toggleTodosAlmacenes = useCallback(() => {
    setTodosAlmacenes(prev => {
      if (!prev) {
        setSelectedAlmacenes(almacenes.map(a => a.id));
      } else {
        setSelectedAlmacenes([]);
      }
      return !prev;
    });
  }, [almacenes]);

  return {
    // Estado
    unidadesNegocio,
    selectedUnidad,
    setSelectedUnidad,
    loadingUnidades,
    
    almacenes,
    selectedAlmacenes,
    todosAlmacenes,
    
    inventariosFisicos,
    inventariosFiltrados,
    setInventariosFiltrados,
    
    pedidosVigentes,
    
    loading,
    setLoading,
    
    // Valores derivados
    selectedServer,
    serverData,
    selectedSucursal,
    
    // Acciones
    fetchAlmacenes,
    fetchInventariosFisicos,
    fetchPedidosVigentes,
    toggleAlmacen,
    toggleTodosAlmacenes
  };
}

export default useAutorizacionComprasData;
