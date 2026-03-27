import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { 
  Loader2, Search, Play, Database, Filter, Download, 
  BarChart3, ShoppingCart, CreditCard, Package, FileText
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const iconosPorCategoria = {
  'Ventas': BarChart3,
  'Compras': ShoppingCart,
  'Pagos': CreditCard,
  'Inventarios': Package,
};

export default function CatalogoConsultas() {
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

  useEffect(() => {
    cargarConsultas();
    cargarServers();
  }, []);

  const cargarConsultas = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = {};
      if (filtroCategoria) params.categoria = filtroCategoria;
      if (filtroSistema) params.sistema = filtroSistema;
      
      const response = await axios.get(`${API_URL}/api/catalogo/consultas-rich`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
      });
      setConsultas(response.data.consultas);
      setCategorias(response.data.categorias);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al cargar catálogo');
    } finally {
      setLoading(false);
    }
  };

  const cargarServers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setServers(response.data);
    } catch (error) {
      console.error('Error cargando servers:', error);
    }
  };

  useEffect(() => {
    cargarConsultas();
  }, [filtroCategoria, filtroSistema]);

  const seleccionarConsulta = (consulta) => {
    setConsultaSeleccionada(consulta);
    setResultados(null);
    // Inicializar parámetros con valores default
    const params = {};
    const hoy = new Date().toISOString().split('T')[0];
    const inicioMes = hoy.substring(0, 8) + '01';
    
    consulta.parametros.forEach(p => {
      if (p === 'fecha') params[p] = hoy;
      else if (p === 'fecha_ini') params[p] = inicioMes;
      else if (p === 'fecha_fin') params[p] = hoy;
      else params[p] = '';
    });
    setParametros(params);
  };

  const ejecutarConsulta = async () => {
    if (!consultaSeleccionada || !serverSeleccionado) {
      toast.error('Selecciona una consulta y un servidor');
      return;
    }
    
    setEjecutando(true);
    setResultados(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/catalogo/ejecutar-rich/${consultaSeleccionada.id}?server_id=${serverSeleccionado}`,
        { parametros },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResultados(response.data);
      toast.success(`${response.data.registros} registros encontrados`);
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.response?.data?.detail || 'Error al ejecutar consulta');
    } finally {
      setEjecutando(false);
    }
  };

  const exportarCSV = () => {
    if (!resultados?.datos?.length) return;
    
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
  };

  const formatValue = (val) => {
    if (val === null || val === undefined) return '-';
    if (typeof val === 'number') {
      if (val >= 1000) return val.toLocaleString('es-MX');
      return val;
    }
    return val;
  };

  // Filtrar servers por sistema de la consulta seleccionada
  const serversDisponibles = consultaSeleccionada 
    ? servers.filter(s => {
        if (consultaSeleccionada.sistema === 'SoftRestaurant') return s.system_type === 'SoftRestaurant';
        if (consultaSeleccionada.sistema === 'MPRO') return s.system_type === 'MPRO';
        return true;
      })
    : servers;

  return (
    <div className="space-y-4" data-testid="catalogo-consultas">
      <div>
        <h1 className="text-2xl font-bold text-zinc-800">Catálogo de Consultas</h1>
        <p className="text-sm text-zinc-500">Ejecuta consultas predefinidas sin necesidad de programador</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Panel izquierdo - Lista de consultas */}
        <Card className="lg:col-span-1 border">
          <CardHeader className="py-3 bg-zinc-100">
            <CardTitle className="text-sm flex items-center gap-2">
              <Database className="h-4 w-4" />
              Consultas Disponibles
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3">
            {/* Filtros */}
            <div className="flex gap-2 mb-3">
              <Select value={filtroCategoria || "all"} onValueChange={(v) => setFiltroCategoria(v === "all" ? "" : v)}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Categoría" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {categorias.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={filtroSistema || "all"} onValueChange={(v) => setFiltroSistema(v === "all" ? "" : v)}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Sistema" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="SoftRestaurant">SoftRestaurant</SelectItem>
                  <SelectItem value="MPRO">MPRO</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Lista de consultas */}
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {loading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
                </div>
              ) : (
                consultas.map(c => {
                  const Icono = iconosPorCategoria[c.categoria] || FileText;
                  const isSelected = consultaSeleccionada?.id === c.id;
                  return (
                    <div
                      key={c.id}
                      className={`p-2 rounded cursor-pointer transition-all border ${
                        isSelected 
                          ? 'bg-blue-50 border-blue-300' 
                          : 'hover:bg-zinc-50 border-transparent'
                      }`}
                      onClick={() => seleccionarConsulta(c)}
                    >
                      <div className="flex items-start gap-2">
                        <Icono className={`h-4 w-4 mt-0.5 ${isSelected ? 'text-blue-600' : 'text-zinc-400'}`} />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate">{c.nombre}</p>
                          <p className="text-xs text-zinc-500 truncate">{c.descripcion}</p>
                          <div className="flex gap-1 mt-1">
                            <span className="text-xs px-1 bg-zinc-200 rounded">{c.sistema}</span>
                            <span className="text-xs px-1 bg-zinc-100 rounded">{c.categoria}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>

        {/* Panel derecho - Ejecución y resultados */}
        <div className="lg:col-span-2 space-y-4">
          {/* Parámetros */}
          {consultaSeleccionada && (
            <Card className="border">
              <CardHeader className="py-3 bg-blue-50">
                <CardTitle className="text-sm">{consultaSeleccionada.nombre}</CardTitle>
              </CardHeader>
              <CardContent className="p-4">
                <p className="text-sm text-zinc-600 mb-4">{consultaSeleccionada.descripcion}</p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                  {/* Selector de servidor */}
                  <div>
                    <label className="text-xs font-medium text-zinc-600">Servidor *</label>
                    <Select value={serverSeleccionado} onValueChange={setServerSeleccionado}>
                      <SelectTrigger className="h-9">
                        <SelectValue placeholder="Seleccionar..." />
                      </SelectTrigger>
                      <SelectContent>
                        {serversDisponibles.map(s => (
                          <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Parámetros de la consulta */}
                  {consultaSeleccionada.parametros.map(param => (
                    <div key={param}>
                      <label className="text-xs font-medium text-zinc-600 capitalize">
                        {param.replace('_', ' ')} *
                      </label>
                      <Input
                        type={param.includes('fecha') ? 'date' : 'text'}
                        value={parametros[param] || ''}
                        onChange={(e) => setParametros({...parametros, [param]: e.target.value})}
                        className="h-9"
                      />
                    </div>
                  ))}
                </div>
                
                <Button 
                  onClick={ejecutarConsulta} 
                  disabled={ejecutando || !serverSeleccionado}
                  className="w-full"
                >
                  {ejecutando ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  Ejecutar Consulta
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Resultados */}
          {resultados && (
            <Card className="border">
              <CardHeader className="py-3 bg-green-50 flex flex-row items-center justify-between">
                <CardTitle className="text-sm">
                  Resultados: {resultados.registros} registros
                </CardTitle>
                <Button variant="outline" size="sm" onClick={exportarCSV}>
                  <Download className="h-4 w-4 mr-1" />
                  Exportar CSV
                </Button>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto max-h-[400px]">
                  <table className="w-full text-sm">
                    <thead className="bg-zinc-100 sticky top-0">
                      <tr>
                        {resultados.datos.length > 0 && 
                          Object.keys(resultados.datos[0]).map(col => (
                            <th key={col} className="py-2 px-3 text-left font-semibold text-xs">
                              {col.replace(/_/g, ' ')}
                            </th>
                          ))
                        }
                      </tr>
                    </thead>
                    <tbody>
                      {resultados.datos.map((row, idx) => (
                        <tr key={idx} className="border-b hover:bg-zinc-50">
                          {Object.values(row).map((val, i) => (
                            <td key={i} className="py-2 px-3">
                              {formatValue(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Mensaje inicial */}
          {!consultaSeleccionada && (
            <Card className="border border-dashed">
              <CardContent className="py-12 text-center">
                <Search className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
                <p className="text-zinc-500">Selecciona una consulta del catálogo para comenzar</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
