/**
 * useCatalogoConsultasData - Hook para datos de Catálogo de Consultas
 * Extrae toda la lógica de estado y fetching del componente principal.
 */
import { useState, useEffect, useCallback } from 'react';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
import axios from 'axios';
import { fetchServersOperativos } from '../../services/serversService';
import logger from '../../services/logger';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function useCatalogoConsultasData() {
  // Estados principales
  const [consultas, setConsultas] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ejecutando, setEjecutando] = useState(false);
  
  // Filtros
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [filtroSistema, setFiltroSistema] = useState('');
  
  // Consulta seleccionada
  const [consultaSeleccionada, setConsultaSeleccionada] = useState(null);
  const [serverSeleccionado, setServerSeleccionado] = useState('');
  const [parametros, setParametros] = useState({});
  
  // Resultados
  const [resultados, setResultados] = useState(null);
  
  // Ver SQL
  const [mostrarSQL, setMostrarSQL] = useState(false);
  
  // Modo Edición
  const [modoEdicion, setModoEdicion] = useState(false);
  const [sqlEditado, setSqlEditado] = useState('');
  
  // Modo Test
  const [modoTest, setModoTest] = useState(false);
  const [resultadosTest, setResultadosTest] = useState(null);
  const [ejecutandoTest, setEjecutandoTest] = useState(false);
  
  // Modal Nueva Consulta
  const [showNuevaConsulta, setShowNuevaConsulta] = useState(false);
  const [nuevaConsulta, setNuevaConsulta] = useState({
    nombre: '',
    descripcion: '',
    sistema: '',
    categoria: '',
    parametros: '',
    sql: ''
  });
  const [guardando, setGuardando] = useState(false);

  // Cargar consultas
  const cargarConsultas = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filtroCategoria) params.categoria = filtroCategoria;
      if (filtroSistema) params.sistema = filtroSistema;
      
      const response = await axios.get(`${API_URL}/api/catalogo/consultas-rich`, {
        params,
        withCredentials: true
      });
      setConsultas(response.data.consultas);
      setCategorias(response.data.categorias);
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error al cargar catálogo');
    } finally {
      setLoading(false);
    }
  }, [filtroCategoria, filtroSistema]);

  // Cargar servers
  const cargarServers = useCallback(async () => {
    try {
      const serversOperativos = await fetchServersOperativos();
      setServers(serversOperativos);
    } catch (error) {
      logger.error('Error cargando servers:', error);
    }
  }, []);

  // Carga inicial
  useEffect(() => {
    cargarConsultas();
    cargarServers();
  }, [cargarConsultas, cargarServers]);

  // Seleccionar consulta
  const seleccionarConsulta = useCallback((consulta) => {
    logger.log('Consulta seleccionada:', consulta);
    setConsultaSeleccionada(consulta);
    setResultados(null);
    setResultadosTest(null);
    setMostrarSQL(false);
    setModoEdicion(false);
    setModoTest(false);
    
    // Inicializar parámetros con valores default
    const params = {};
    const hoy = new Date().toISOString().split('T')[0];
    const inicioMes = hoy.substring(0, 8) + '01';
    
    const parametrosArray = Array.isArray(consulta.parametros) ? consulta.parametros : [];
    
    parametrosArray.forEach(p => {
      if (p === 'fecha') params[p] = hoy;
      else if (p === 'fecha_ini') params[p] = inicioMes;
      else if (p === 'fecha_fin') params[p] = hoy;
      else params[p] = '';
    });
    setParametros(params);
  }, []);

  // Ejecutar consulta
  const ejecutarConsulta = useCallback(async () => {
    if (!consultaSeleccionada || !serverSeleccionado) {
      toast.error('Selecciona una consulta y un servidor');
      return;
    }
    
    setEjecutando(true);
    setResultados(null);
    
    try {
      // Auth viaja en cookie httpOnly
      const response = await axios.post(
        `${API_URL}/api/catalogo/ejecutar-rich/${consultaSeleccionada.id}?server_id=${serverSeleccionado}`,
        { parametros },
        { withCredentials: true, timeout: 60000 }
      );
      setResultados(response.data);
      toast.success(`${response.data.registros} registros encontrados`);
    } catch (error) {
      logger.error('Error:', error);
      toast.error(error.response?.data?.detail || 'Error al ejecutar consulta');
    } finally {
      setEjecutando(false);
    }
  }, [consultaSeleccionada, serverSeleccionado, parametros]);

  // Ejecutar test
  const ejecutarTest = useCallback(async () => {
    if (!consultaSeleccionada || !serverSeleccionado) {
      toast.error('Selecciona una consulta y un servidor');
      return;
    }
    
    setEjecutandoTest(true);
    setResultadosTest(null);
    setModoTest(true);
    
    try {
      // Auth viaja en cookie httpOnly
      const response = await axios.post(
        `${API_URL}/api/catalogo/ejecutar-rich/${consultaSeleccionada.id}?server_id=${serverSeleccionado}&limit=10`,
        { parametros },
        { withCredentials: true, timeout: 30000 }
      );
      setResultadosTest(response.data);
      toast.success(`Test completado: ${response.data.registros} registros (limitado a 10)`);
    } catch (error) {
      logger.error('Error en test:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Error al probar consulta';
      setResultadosTest({ error: errorMsg });
      toast.error(errorMsg);
    } finally {
      setEjecutandoTest(false);
    }
  }, [consultaSeleccionada, serverSeleccionado, parametros]);

  // Iniciar edición
  const iniciarEdicion = useCallback(() => {
    if (consultaSeleccionada) {
      setSqlEditado(consultaSeleccionada.sql);
      setModoEdicion(true);
    }
  }, [consultaSeleccionada]);

  // Guardar edición
  const guardarEdicion = useCallback(async () => {
    if (!consultaSeleccionada) return;
    
    try {
      // Auth viaja en cookie httpOnly
      await axios.put(
        `${API_URL}/api/catalogo/consultas/${consultaSeleccionada.id}`,
        { sql: sqlEditado },
        { withCredentials: true }
      );
      setConsultaSeleccionada({ ...consultaSeleccionada, sql: sqlEditado });
      setConsultas(prev => prev.map(c => 
        c.id === consultaSeleccionada.id ? { ...c, sql: sqlEditado } : c
      ));
      setModoEdicion(false);
      toast.success('Consulta guardada correctamente');
    } catch (error) {
      logger.error('Error guardando:', error);
      toast.error(error.response?.data?.detail || 'Error al guardar consulta');
    }
  }, [consultaSeleccionada, sqlEditado]);

  // Exportar CSV
  const exportarCSV = useCallback(() => {
    if (!resultados?.datos?.length || !consultaSeleccionada) return;
    
    const headers = Object.keys(resultados.datos[0]);
    const csv = [
      headers.join(','),
      ...resultados.datos.map(row => 
        headers.map(h => {
          const val = row[h];
          if (typeof val === 'string' && val.includes(',')) return `"${val}"`;
          return val ?? '';
        }).join(',')
      )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${consultaSeleccionada.id}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    toast.success('Archivo CSV descargado');
  }, [resultados, consultaSeleccionada]);

  // Guardar nueva consulta
  const guardarNuevaConsulta = useCallback(async () => {
    if (!nuevaConsulta.nombre || !nuevaConsulta.sistema || !nuevaConsulta.categoria || !nuevaConsulta.sql) {
      toast.error('Completa todos los campos requeridos');
      return;
    }
    
    setGuardando(true);
    try {
      // Auth viaja en cookie httpOnly
      const payload = {
        ...nuevaConsulta,
        parametros: nuevaConsulta.parametros.split(',').map(p => p.trim()).filter(p => p)
      };
      
      await axios.post(`${API_URL}/api/catalogo/consultas-custom`, payload, {
        withCredentials: true
      });
      
      toast.success('Consulta creada exitosamente');
      setShowNuevaConsulta(false);
      setNuevaConsulta({ nombre: '', descripcion: '', sistema: '', categoria: '', parametros: '', sql: '' });
      cargarConsultas();
    } catch (error) {
      logger.error('Error:', error);
      toast.error(error.response?.data?.detail || 'Error al crear consulta');
    } finally {
      setGuardando(false);
    }
  }, [nuevaConsulta, cargarConsultas]);

  // Helper: formatear valor
  const formatValue = useCallback((val) => {
    if (val === null || val === undefined) return '-';
    if (typeof val === 'number') {
      if (val >= 1000) return val.toLocaleString('es-MX');
      return val;
    }
    return val;
  }, []);

  return {
    // Estado
    consultas,
    categorias,
    servers,
    loading,
    ejecutando,
    filtroCategoria,
    filtroSistema,
    consultaSeleccionada,
    serverSeleccionado,
    parametros,
    resultados,
    mostrarSQL,
    modoEdicion,
    sqlEditado,
    modoTest,
    resultadosTest,
    ejecutandoTest,
    showNuevaConsulta,
    nuevaConsulta,
    guardando,
    
    // Setters
    setFiltroCategoria,
    setFiltroSistema,
    setServerSeleccionado,
    setParametros,
    setMostrarSQL,
    setModoEdicion,
    setSqlEditado,
    setModoTest,
    setShowNuevaConsulta,
    setNuevaConsulta,
    
    // Acciones
    cargarConsultas,
    seleccionarConsulta,
    ejecutarConsulta,
    ejecutarTest,
    iniciarEdicion,
    guardarEdicion,
    exportarCSV,
    guardarNuevaConsulta,
    formatValue
  };
}

export default useCatalogoConsultasData;
