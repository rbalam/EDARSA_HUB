/**
 * useCatalogoConsultasData - Hook para datos de Catálogo de Consultas
 * Extrae toda la lógica de estado y fetching del componente principal.
 * 
 * CORRECCIÓN P0 - 2026-05-08:
 * Migrado de axios directo a cliente API centralizado para garantizar
 * envío de Authorization header cuando cookie httpOnly falla por CORS/proxy.
 * 
 * CORRECCIÓN P1 - 2026-05-15:
 * Filtro de sistemas ahora es dinámico desde Sistema_Catalogo (EDARSAHUB).
 * Ya no hardcodea SoftRestaurant y MPRO.
 */
import { useState, useEffect, useCallback } from 'react';
// FASE AUTH-SECURITY-01 / FASE 4.1: Usa cliente API centralizado con interceptor de token
import api from '../../lib/api';
// CORRECCIÓN P0-CHAPUR: Catálogo SQL usa servidores técnicos, NO filtrar por visible_en_operaciones
import { fetchConexionesExplorables } from '../../services/exploradorService';
import logger from '../../services/logger';
import { toast } from 'sonner';

export function useCatalogoConsultasData() {
  // Estados principales
  const [consultas, setConsultas] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ejecutando, setEjecutando] = useState(false);
  
  // CORRECCIÓN P1: Sistemas dinámicos desde catálogo
  const [sistemasDisponibles, setSistemasDisponibles] = useState([]);
  const [loadingSistemas, setLoadingSistemas] = useState(false);
  
  // Filtros
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [filtroSistema, setFiltroSistema] = useState('');
  
  // Consulta seleccionada
  // CORRECCIÓN P0 SELECT: Usar "__NONE__" en lugar de "" para evitar error Radix Select
  const [consultaSeleccionada, setConsultaSeleccionada] = useState(null);
  const [serverSeleccionado, setServerSeleccionado] = useState('__NONE__');
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
      
      // CORRECCIÓN P0: Usa cliente API centralizado con interceptor de token
      const response = await api.get('/catalogo/consultas-rich', { params });
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
  // CORRECCIÓN P0-CHAPUR: Catálogo SQL es herramienta técnica, NO filtra por visible_en_operaciones
  // Usa fetchConexionesExplorables que devuelve TODOS los servidores activos
  const cargarServers = useCallback(async () => {
    try {
      const conexionesExplorables = await fetchConexionesExplorables();
      // Transformar al formato esperado por el componente
      // FIX P0 (May-2026): Exponer tanto código RAW como normalizado
      // - system_type: código RAW para matching con consultas custom
      // - system_type_normalizado: código canónico para filtros UI
      const serversTransformados = conexionesExplorables.map(c => ({
        id: c.id,
        name: c.nombre,
        nombre: c.nombre,
        // Código RAW para matching con consultas que usan código raw (ej: SOFRESATAURANT_ENTER)
        system_type: c.sistema_codigo_raw || c.sistema_codigo,
        // Código normalizado para filtros (ej: API_LOCAL)
        system_type_normalizado: c.sistema_codigo_normalizado || c.sistema_codigo,
        sistema_nombre: c.sistema_nombre,
        tipo_conexion: c.tipo_conexion,
        activo: c.activo,
        visible_en_operaciones: c.visible_en_operaciones,
        explorable: c.explorable
      }));
      setServers(serversTransformados);
      logger.debug(`[CatalogoSQL] Cargados ${serversTransformados.length} servidores técnicos`);
    } catch (error) {
      logger.error('Error cargando servers:', error);
    }
  }, []);

  // CORRECCIÓN P1: Cargar sistemas dinámicos desde EDARSAHUB
  const cargarSistemasDisponibles = useCallback(async () => {
    setLoadingSistemas(true);
    try {
      const response = await api.get('/catalogos/sistemas/activos');
      if (response.data?.success && response.data?.data) {
        setSistemasDisponibles(response.data.data);
      }
    } catch (error) {
      logger.error('Error cargando sistemas:', error);
      // Fallback: al menos mostrar los básicos si falla
      setSistemasDisponibles([
        { Codigo: 'SOFTRESTAURANT', Descripcion: 'SoftRestaurant' },
        { Codigo: 'MPRO', Descripcion: 'ManagementPro (MPRO)' }
      ]);
    } finally {
      setLoadingSistemas(false);
    }
  }, []);

  // Carga inicial
  useEffect(() => {
    cargarConsultas();
    cargarServers();
    cargarSistemasDisponibles(); // CORRECCIÓN P1: Cargar sistemas dinámicos
  }, [cargarConsultas, cargarServers, cargarSistemasDisponibles]);

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
    // CORRECCIÓN P0 SELECT: "__NONE__" significa sin selección
    if (!consultaSeleccionada || !serverSeleccionado || serverSeleccionado === '__NONE__') {
      toast.error('Selecciona una consulta y un servidor');
      return;
    }
    
    setEjecutando(true);
    setResultados(null);
    
    try {
      // CORRECCIÓN P0: Usa cliente API centralizado con interceptor de token
      const response = await api.post(
        `/catalogo/ejecutar-rich/${consultaSeleccionada.id}?server_id=${serverSeleccionado}`,
        { parametros },
        { timeout: 60000 }
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
    // CORRECCIÓN P0 SELECT: "__NONE__" significa sin selección
    if (!consultaSeleccionada || !serverSeleccionado || serverSeleccionado === '__NONE__') {
      toast.error('Selecciona una consulta y un servidor');
      return;
    }
    
    setEjecutandoTest(true);
    setResultadosTest(null);
    setModoTest(true);
    
    try {
      // CORRECCIÓN P0: Usa cliente API centralizado con interceptor de token
      const response = await api.post(
        `/catalogo/ejecutar-rich/${consultaSeleccionada.id}?server_id=${serverSeleccionado}&limit=10`,
        { parametros },
        { timeout: 30000 }
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
      // CORRECCIÓN P0: Usa cliente API centralizado con interceptor de token
      await api.put(
        `/catalogo/consultas/${consultaSeleccionada.id}`,
        { sql: sqlEditado }
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
      // CORRECCIÓN P0: Usa cliente API centralizado con interceptor de token
      const payload = {
        ...nuevaConsulta,
        parametros: nuevaConsulta.parametros.split(',').map(p => p.trim()).filter(p => p)
      };
      
      await api.post('/catalogo/consultas-custom', payload);
      
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
    // CORRECCIÓN P1: Sistemas dinámicos
    sistemasDisponibles,
    loadingSistemas,
    
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
