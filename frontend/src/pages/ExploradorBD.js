import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { 
  Loader2, Database, Table, Columns, Link2, Eye, Play, 
  ChevronRight, Search, Download, Server
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function ExploradorBD() {
  const [servers, setServers] = useState([]);
  const [serverSeleccionado, setServerSeleccionado] = useState('');
  const [serverInfo, setServerInfo] = useState(null);
  const [tablas, setTablas] = useState([]);
  const [tablaSeleccionada, setTablaSeleccionada] = useState(null);
  const [columnas, setColumnas] = useState([]);
  const [relaciones, setRelaciones] = useState([]);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState({});
  
  // Query libre
  const [queryLibre, setQueryLibre] = useState('SELECT TOP 10 * FROM ');
  const [resultadoQuery, setResultadoQuery] = useState(null);
  const [filtroTabla, setFiltroTabla] = useState('');

  useEffect(() => {
    cargarServers();
  }, []);

  const cargarServers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setServers(response.data);
    } catch (error) {
      toast.error('Error cargando servidores');
    }
  };

  const cargarTablas = async (serverId) => {
    setLoading(prev => ({...prev, tablas: true}));
    setTablaSeleccionada(null);
    setColumnas([]);
    setRelaciones([]);
    setPreview(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/explorador/tablas/${serverId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTablas(response.data.tablas);
      setServerInfo({
        nombre: response.data.servidor,
        sistema: response.data.sistema,
        database: response.data.database
      });
      toast.success(`${response.data.tablas.length} tablas encontradas`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error cargando tablas');
      setTablas([]);
    } finally {
      setLoading(prev => ({...prev, tablas: false}));
    }
  };

  const seleccionarTabla = async (tabla) => {
    setTablaSeleccionada(tabla);
    setLoading(prev => ({...prev, columnas: true, relaciones: true}));
    
    const token = localStorage.getItem('token');
    const headers = { Authorization: `Bearer ${token}` };
    
    try {
      const [colRes, relRes] = await Promise.all([
        axios.get(`${API_URL}/api/explorador/columnas/${serverSeleccionado}/${tabla}`, { headers }),
        axios.get(`${API_URL}/api/explorador/relaciones/${serverSeleccionado}/${tabla}`, { headers })
      ]);
      setColumnas(colRes.data.columnas);
      setRelaciones(relRes.data.relaciones);
    } catch (error) {
      toast.error('Error cargando estructura de tabla');
    } finally {
      setLoading(prev => ({...prev, columnas: false, relaciones: false}));
    }
  };

  const verPreview = async () => {
    if (!tablaSeleccionada) return;
    setLoading(prev => ({...prev, preview: true}));
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/explorador/preview/${serverSeleccionado}/${tablaSeleccionada}?limite=20`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setPreview(response.data);
      toast.success(`${response.data.registros} registros obtenidos`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error obteniendo preview');
    } finally {
      setLoading(prev => ({...prev, preview: false}));
    }
  };

  const ejecutarQueryLibre = async () => {
    if (!queryLibre.trim()) return;
    setLoading(prev => ({...prev, query: true}));
    setResultadoQuery(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/explorador/query/${serverSeleccionado}`,
        { query: queryLibre },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResultadoQuery(response.data);
      toast.success(`${response.data.registros} registros`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error ejecutando query');
    } finally {
      setLoading(prev => ({...prev, query: false}));
    }
  };

  const exportarCSV = (datos, nombreArchivo) => {
    if (!datos?.length) return;
    
    const headers = Object.keys(datos[0]);
    const csv = [
      headers.join(','),
      ...datos.map(row => 
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
    link.download = `${nombreArchivo}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    toast.success('CSV descargado');
  };

  const tablasFiltradas = tablas.filter(t => 
    t.tabla.toLowerCase().includes(filtroTabla.toLowerCase())
  );

  return (
    <div className="space-y-4" data-testid="explorador-bd">
      <div>
        <h1 className="text-2xl font-bold text-zinc-800">Explorador de Base de Datos</h1>
        <p className="text-sm text-zinc-500">Explora tablas, columnas y relaciones de tus sistemas</p>
      </div>

      {/* Selector de servidor */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <Server className="h-5 w-5 text-zinc-400" />
            <Select value={serverSeleccionado} onValueChange={(v) => { setServerSeleccionado(v); cargarTablas(v); }}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Seleccionar servidor..." />
              </SelectTrigger>
              <SelectContent>
                {servers.map(s => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.name} ({s.system_type})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {serverInfo && (
              <div className="text-sm text-zinc-500">
                <span className="font-medium">{serverInfo.sistema}</span> • {serverInfo.database}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {serverSeleccionado && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Lista de tablas */}
          <Card className="border">
            <CardHeader className="py-2 bg-zinc-100">
              <CardTitle className="text-sm flex items-center gap-2">
                <Database className="h-4 w-4" />
                Tablas ({tablasFiltradas.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              <div className="mb-2">
                <Input 
                  placeholder="Filtrar tablas..." 
                  value={filtroTabla}
                  onChange={(e) => setFiltroTabla(e.target.value)}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1 max-h-[500px] overflow-y-auto">
                {loading.tablas ? (
                  <div className="flex justify-center py-4">
                    <Loader2 className="h-5 w-5 animate-spin" />
                  </div>
                ) : (
                  tablasFiltradas.map(t => (
                    <div 
                      key={t.tabla}
                      className={`p-2 rounded cursor-pointer text-sm flex items-center gap-2 ${
                        tablaSeleccionada === t.tabla 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'hover:bg-zinc-50'
                      }`}
                      onClick={() => seleccionarTabla(t.tabla)}
                    >
                      <Table className="h-3 w-3" />
                      <span className="truncate">{t.tabla}</span>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Detalles de tabla */}
          <div className="lg:col-span-3 space-y-4">
            {tablaSeleccionada ? (
              <>
                {/* Columnas */}
                <Card className="border">
                  <CardHeader className="py-2 bg-blue-50 flex flex-row items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Columns className="h-4 w-4" />
                      {tablaSeleccionada} - Columnas ({columnas.length})
                    </CardTitle>
                    <Button size="sm" variant="outline" onClick={verPreview} disabled={loading.preview}>
                      {loading.preview ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Eye className="h-3 w-3 mr-1" />}
                      Ver Datos
                    </Button>
                  </CardHeader>
                  <CardContent className="p-0">
                    {loading.columnas ? (
                      <div className="flex justify-center py-4">
                        <Loader2 className="h-5 w-5 animate-spin" />
                      </div>
                    ) : (
                      <div className="overflow-x-auto max-h-[250px]">
                        <table className="w-full text-xs">
                          <thead className="bg-zinc-100 sticky top-0">
                            <tr>
                              <th className="py-2 px-3 text-left">Columna</th>
                              <th className="py-2 px-3 text-left">Tipo</th>
                              <th className="py-2 px-3 text-left">Longitud</th>
                              <th className="py-2 px-3 text-left">Nullable</th>
                            </tr>
                          </thead>
                          <tbody>
                            {columnas.map((c, i) => (
                              <tr key={i} className="border-b hover:bg-zinc-50">
                                <td className="py-1 px-3 font-medium">{c.columna}</td>
                                <td className="py-1 px-3 text-blue-600">{c.tipo}</td>
                                <td className="py-1 px-3">{c.longitud || '-'}</td>
                                <td className="py-1 px-3">{c.nullable}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Relaciones */}
                {relaciones.length > 0 && (
                  <Card className="border">
                    <CardHeader className="py-2 bg-purple-50">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Link2 className="h-4 w-4" />
                        Relaciones ({relaciones.length})
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-2">
                      <div className="space-y-2">
                        {relaciones.map((r, i) => (
                          <div key={i} className="text-xs p-2 bg-zinc-50 rounded flex items-center gap-2">
                            <span className="font-medium">{r.tabla_padre}.{r.columna_padre}</span>
                            <ChevronRight className="h-3 w-3" />
                            <span className="text-purple-600">{r.tabla_referenciada}.{r.columna_referenciada}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Preview de datos */}
                {preview && (
                  <Card className="border">
                    <CardHeader className="py-2 bg-green-50 flex flex-row items-center justify-between">
                      <CardTitle className="text-sm">
                        Preview: {preview.registros} registros
                      </CardTitle>
                      <Button size="sm" variant="outline" onClick={() => exportarCSV(preview.datos, tablaSeleccionada)}>
                        <Download className="h-3 w-3 mr-1" />
                        CSV
                      </Button>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="overflow-x-auto max-h-[300px]">
                        <table className="w-full text-xs">
                          <thead className="bg-zinc-100 sticky top-0">
                            <tr>
                              {preview.datos.length > 0 && Object.keys(preview.datos[0]).map(col => (
                                <th key={col} className="py-2 px-2 text-left whitespace-nowrap">{col}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {preview.datos.map((row, i) => (
                              <tr key={i} className="border-b hover:bg-zinc-50">
                                {Object.values(row).map((val, j) => (
                                  <td key={j} className="py-1 px-2 whitespace-nowrap max-w-[200px] truncate">
                                    {val?.toString() || '-'}
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
              </>
            ) : (
              <Card className="border border-dashed">
                <CardContent className="py-12 text-center">
                  <Table className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
                  <p className="text-zinc-500">Selecciona una tabla para ver su estructura</p>
                </CardContent>
              </Card>
            )}

            {/* Query Libre */}
            <Card className="border">
              <CardHeader className="py-2 bg-orange-50">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Play className="h-4 w-4" />
                  Query SQL Libre (Solo SELECT)
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3">
                <Textarea
                  value={queryLibre}
                  onChange={(e) => setQueryLibre(e.target.value)}
                  placeholder="SELECT TOP 10 * FROM tabla"
                  className="font-mono text-sm h-20 mb-2"
                />
                <div className="flex gap-2">
                  <Button onClick={ejecutarQueryLibre} disabled={loading.query} className="flex-1">
                    {loading.query ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                    Ejecutar
                  </Button>
                  {resultadoQuery && (
                    <Button variant="outline" onClick={() => exportarCSV(resultadoQuery.datos, 'query_result')}>
                      <Download className="h-4 w-4 mr-1" />
                      CSV
                    </Button>
                  )}
                </div>
                
                {resultadoQuery && (
                  <div className="mt-3 overflow-x-auto max-h-[200px] border rounded">
                    <table className="w-full text-xs">
                      <thead className="bg-zinc-100 sticky top-0">
                        <tr>
                          {resultadoQuery.datos.length > 0 && Object.keys(resultadoQuery.datos[0]).map(col => (
                            <th key={col} className="py-2 px-2 text-left">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {resultadoQuery.datos.map((row, i) => (
                          <tr key={i} className="border-b">
                            {Object.values(row).map((val, j) => (
                              <td key={j} className="py-1 px-2">{val?.toString() || '-'}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
