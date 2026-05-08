import React, { useMemo, useCallback } from 'react';
// AUDITORIA-TABLEROS-KPIS-FILTROS-01: Migrado de axios directo a api centralizado
import api from '../lib/api';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
import logger from '../services/logger';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { 
  Loader2, Search, Play, Database, Download, 
  FileText, Plus, X, Trash2, Edit, Save, Code, Eye, TestTube, Check
} from 'lucide-react';
import { iconosPorCategoria, EmptyState, useCatalogoConsultasData } from '../components/catalogo-consultas';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function CatalogoConsultas() {
  const {
    // Estado
    consultas, categorias, servers, loading, ejecutando,
    filtroCategoria, filtroSistema,
    consultaSeleccionada, serverSeleccionado, parametros,
    resultados, mostrarSQL, modoEdicion, sqlEditado,
    modoTest, resultadosTest, ejecutandoTest,
    showNuevaConsulta, nuevaConsulta, guardando,
    // Setters
    setFiltroCategoria, setFiltroSistema, setServerSeleccionado,
    setParametros, setMostrarSQL, setModoEdicion, setSqlEditado,
    setModoTest, setShowNuevaConsulta, setNuevaConsulta,
    // Acciones
    cargarConsultas, seleccionarConsulta, ejecutarConsulta,
    ejecutarTest, iniciarEdicion, guardarEdicion, exportarCSV,
    guardarNuevaConsulta, formatValue
  } = useCatalogoConsultasData();

  // Eliminar consulta personalizada (mantener local ya que modifica estado del hook)
  const eliminarConsulta = useCallback(async (consultaId) => {
    if (!window.confirm('¿Eliminar esta consulta personalizada?')) return;
    
    try {
      await api.delete(`/catalogo/consultas-custom/${consultaId}`);
      toast.success('Consulta eliminada');
      cargarConsultas();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error al eliminar');
    }
  }, [cargarConsultas]);

  // Filtrar servers por sistema de la consulta seleccionada
  const serversDisponibles = useMemo(() => {
    if (!consultaSeleccionada) return servers;
    return servers.filter(s => {
      if (consultaSeleccionada.sistema === 'SoftRestaurant') return s.system_type === 'SoftRestaurant';
      if (consultaSeleccionada.sistema === 'MPRO') return s.system_type === 'MPRO';
      return true;
    });
  }, [consultaSeleccionada, servers]);

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
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <Database className="h-4 w-4" />
                Consultas Disponibles
              </CardTitle>
              <Button 
                size="sm" 
                className="h-7 text-xs"
                onClick={() => setShowNuevaConsulta(true)}
              >
                <Plus className="h-3 w-3 mr-1" />
                Nueva
              </Button>
            </div>
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
                  const esPersonalizada = c.tipo === 'personalizada';
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
                          <div className="flex items-center gap-1">
                            <p className="font-medium text-sm truncate">{c.nombre}</p>
                            {esPersonalizada && (
                              <span className="text-xs px-1 py-0.5 bg-green-100 text-green-700 rounded">Custom</span>
                            )}
                          </div>
                          <p className="text-xs text-zinc-500 truncate">{c.descripcion}</p>
                          <div className="flex gap-1 mt-1 items-center">
                            <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                              c.sistema === 'MPRO' 
                                ? 'bg-purple-100 text-purple-700' 
                                : 'bg-blue-100 text-blue-700'
                            }`}>{c.sistema}</span>
                            <span className="text-xs px-1 bg-zinc-100 rounded">{c.categoria}</span>
                            {esPersonalizada && (
                              <button
                                className="ml-auto p-1 text-red-500 hover:bg-red-50 rounded"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  eliminarConsulta(c.id);
                                }}
                                title="Eliminar consulta"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                            )}
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
                        {serversDisponibles.length === 0 ? (
                          <SelectItem value="none" disabled>No hay servidores {consultaSeleccionada.sistema}</SelectItem>
                        ) : (
                          serversDisponibles.map(s => (
                            <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                    {serversDisponibles.length === 0 && (
                      <p className="text-xs text-orange-600 mt-1">
                        Esta consulta requiere un servidor {consultaSeleccionada.sistema}
                      </p>
                    )}
                    {consultaSeleccionada.sistema && (
                      <p className="text-xs text-zinc-400 mt-0.5">
                        Sistema: {consultaSeleccionada.sistema}
                      </p>
                    )}
                  </div>
                  
                  {/* Parámetros de la consulta (opcionales) */}
                  {(Array.isArray(consultaSeleccionada.parametros) ? consultaSeleccionada.parametros : []).map(param => (
                    <div key={param}>
                      <label className="text-xs font-medium text-zinc-600 capitalize">
                        {param.replace('_', ' ')}
                      </label>
                      <Input
                        type={param.includes('fecha') ? 'date' : 'text'}
                        value={parametros[param] || ''}
                        onChange={(e) => setParametros({...parametros, [param]: e.target.value})}
                        className="h-9"
                        placeholder={`Opcional`}
                      />
                    </div>
                  ))}
                </div>
                
                {/* BARRA DE BOTONES: Ver, Editar, Test, Ejecutar */}
                <div className="grid grid-cols-4 gap-2 mb-3">
                  {/* 1. VER */}
                  <Button 
                    variant={mostrarSQL ? "default" : "outline"}
                    onClick={() => { setMostrarSQL(!mostrarSQL); setModoEdicion(false); setModoTest(false); }}
                    size="sm"
                    className="flex flex-col items-center py-3 h-auto"
                  >
                    <Eye className="h-4 w-4 mb-1" />
                    <span className="text-xs">Ver</span>
                  </Button>
                  
                  {/* 2. EDITAR */}
                  <Button 
                    variant={modoEdicion ? "default" : "outline"}
                    onClick={() => { 
                      if (!modoEdicion) iniciarEdicion();
                      else setModoEdicion(false);
                      setMostrarSQL(false); 
                      setModoTest(false);
                    }}
                    size="sm"
                    className="flex flex-col items-center py-3 h-auto"
                  >
                    <Edit className="h-4 w-4 mb-1" />
                    <span className="text-xs">Editar</span>
                  </Button>
                  
                  {/* 3. TEST */}
                  <Button 
                    variant={modoTest ? "default" : "outline"}
                    onClick={() => { setModoTest(!modoTest); setMostrarSQL(false); setModoEdicion(false); }}
                    size="sm"
                    disabled={!serverSeleccionado}
                    className="flex flex-col items-center py-3 h-auto"
                  >
                    <TestTube className="h-4 w-4 mb-1" />
                    <span className="text-xs">Test</span>
                  </Button>
                  
                  {/* 4. EJECUTAR */}
                  <Button 
                    variant="default"
                    onClick={ejecutarConsulta}
                    disabled={ejecutando || !serverSeleccionado}
                    size="sm"
                    className="flex flex-col items-center py-3 h-auto bg-green-600 hover:bg-green-700"
                  >
                    {ejecutando ? (
                      <Loader2 className="h-4 w-4 mb-1 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mb-1" />
                    )}
                    <span className="text-xs">Ejecutar</span>
                  </Button>
                </div>
                
                {/* PANEL VER SQL (Solo lectura) */}
                {mostrarSQL && (
                  <div className="mb-3 p-3 bg-zinc-900 rounded-lg overflow-x-auto">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Code className="h-4 w-4 text-green-400" />
                        <span className="text-xs text-green-400 font-medium">SQL Query (Solo lectura)</span>
                      </div>
                      {consultaSeleccionada?.sql && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => {navigator.clipboard.writeText(consultaSeleccionada.sql); toast.success('SQL copiado');}}
                          className="h-6 text-xs text-zinc-400 hover:text-white"
                        >
                          Copiar
                        </Button>
                      )}
                    </div>
                    {consultaSeleccionada?.sql ? (
                      <pre className="text-xs text-zinc-300 whitespace-pre-wrap font-mono max-h-48 overflow-y-auto">
                        {consultaSeleccionada.sql
                          .replace(/\{fecha_ini\}/g, parametros.fecha_ini || '@fecha_ini')
                          .replace(/\{fecha_fin\}/g, parametros.fecha_fin || '@fecha_fin')
                          .replace(/\{almacen\}/g, parametros.almacen || '@almacen')
                          .replace(/\{sucursal\}/g, parametros.sucursal || '@sucursal')
                          .replace(/\{fecha\}/g, parametros.fecha || '@fecha')
                        }
                      </pre>
                    ) : (
                      <div className="text-yellow-400 text-xs">
                        SQL no disponible. Recarga la página para obtener la consulta actualizada.
                      </div>
                    )}
                  </div>
                )}
                
                {/* PANEL EDITAR SQL */}
                {modoEdicion && (
                  <div className="mb-3 p-3 bg-zinc-900 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Edit className="h-4 w-4 text-yellow-400" />
                        <span className="text-xs text-yellow-400 font-medium">Modo Edición</span>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => setModoEdicion(false)}
                          className="h-6 text-xs text-zinc-400 hover:text-white"
                        >
                          Cancelar
                        </Button>
                        <Button 
                          variant="default" 
                          size="sm" 
                          onClick={guardarEdicion}
                          className="h-6 text-xs bg-green-600 hover:bg-green-700"
                        >
                          <Save className="h-3 w-3 mr-1" />
                          Guardar
                        </Button>
                      </div>
                    </div>
                    <Textarea
                      value={sqlEditado}
                      onChange={(e) => setSqlEditado(e.target.value)}
                      className="font-mono text-xs bg-zinc-800 text-zinc-100 border-zinc-700 min-h-[200px]"
                      placeholder="Escribe tu consulta SQL aquí..."
                    />
                    <p className="text-xs text-zinc-500 mt-2">
                      Usa {'{fecha_ini}'}, {'{fecha_fin}'}, {'{almacen}'}, {'{sucursal}'} como parámetros
                    </p>
                  </div>
                )}
                
                {/* PANEL TEST */}
                {modoTest && (
                  <div className="mb-3 p-3 bg-blue-950 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <TestTube className="h-4 w-4 text-blue-400" />
                        <span className="text-xs text-blue-400 font-medium">Modo Test (máx 10 registros)</span>
                      </div>
                      <Button 
                        variant="default" 
                        size="sm" 
                        onClick={ejecutarTest}
                        disabled={ejecutandoTest}
                        className="h-6 text-xs bg-blue-600 hover:bg-blue-700"
                      >
                        {ejecutandoTest ? (
                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        ) : (
                          <Play className="h-3 w-3 mr-1" />
                        )}
                        Probar
                      </Button>
                    </div>
                    
                    {/* Resultados del Test */}
                    {resultadosTest && (
                      <div className="mt-2">
                        {resultadosTest.error ? (
                          <div className="p-2 bg-red-900/50 rounded text-red-300 text-xs">
                            <strong>Error:</strong> {resultadosTest.error}
                          </div>
                        ) : (
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Check className="h-4 w-4 text-green-400" />
                              <span className="text-xs text-green-400">
                                Test exitoso: {resultadosTest.registros} registros
                              </span>
                            </div>
                            {resultadosTest.datos?.length > 0 && (
                              <div className="overflow-x-auto max-h-40">
                                <table className="w-full text-xs">
                                  <thead className="bg-blue-900/50">
                                    <tr>
                                      {Object.keys(resultadosTest.datos[0]).map(col => (
                                        <th key={col} className="py-1 px-2 text-left text-blue-300 font-medium">
                                          {col}
                                        </th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {resultadosTest.datos.slice(0, 5).map((row, i) => (
                                      <tr key={`test-row-${i}-${Object.values(row)[0]}`} className="border-t border-blue-800/50">
                                        {Object.entries(row).map(([colName, colVal]) => (
                                          <td key={`test-${i}-${colName}`} className="py-1 px-2 text-zinc-300 truncate max-w-[150px]">
                                            {colVal ?? '-'}
                                          </td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
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
                        <tr key={`res-row-${idx}-${Object.values(row)[0]}`} className="border-b hover:bg-zinc-50">
                          {Object.entries(row).map(([colName, colVal]) => (
                            <td key={`res-${idx}-${colName}`} className="py-2 px-3">
                              {formatValue(colVal)}
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
              <CardContent className="py-12">
                <EmptyState message="Selecciona una consulta del catálogo para comenzar" />
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Modal Nueva Consulta */}
      {showNuevaConsulta && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Nueva Consulta Personalizada</CardTitle>
                <button onClick={() => setShowNuevaConsulta(false)} className="p-1 hover:bg-zinc-100 rounded">
                  <X className="h-5 w-5" />
                </button>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Nombre *</Label>
                  <Input 
                    placeholder="Ej: Ventas por Zona"
                    value={nuevaConsulta.nombre}
                    onChange={(e) => setNuevaConsulta({...nuevaConsulta, nombre: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Sistema *</Label>
                  <Select 
                    value={nuevaConsulta.sistema} 
                    onValueChange={(v) => setNuevaConsulta({...nuevaConsulta, sistema: v})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="SoftRestaurant">SoftRestaurant</SelectItem>
                      <SelectItem value="MPRO">MPRO</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Categoría *</Label>
                  <Select 
                    value={nuevaConsulta.categoria} 
                    onValueChange={(v) => setNuevaConsulta({...nuevaConsulta, categoria: v})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Ventas">Ventas</SelectItem>
                      <SelectItem value="Compras">Compras</SelectItem>
                      <SelectItem value="Inventarios">Inventarios</SelectItem>
                      <SelectItem value="Pagos">Pagos</SelectItem>
                      <SelectItem value="Operaciones">Operaciones</SelectItem>
                      <SelectItem value="Otros">Otros</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Parámetros (separados por coma)</Label>
                  <Input 
                    placeholder="fecha_ini, fecha_fin"
                    value={nuevaConsulta.parametros}
                    onChange={(e) => setNuevaConsulta({...nuevaConsulta, parametros: e.target.value})}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Descripción</Label>
                <Input 
                  placeholder="Breve descripción de la consulta"
                  value={nuevaConsulta.descripcion}
                  onChange={(e) => setNuevaConsulta({...nuevaConsulta, descripcion: e.target.value})}
                />
              </div>
              
              <div className="space-y-2">
                <Label>SQL *</Label>
                <Textarea 
                  className="font-mono text-sm min-h-[200px]"
                  placeholder={`SELECT columna1, columna2
FROM tabla
WHERE fecha >= '{fecha_ini}' 
  AND fecha <= '{fecha_fin}'`}
                  value={nuevaConsulta.sql}
                  onChange={(e) => setNuevaConsulta({...nuevaConsulta, sql: e.target.value})}
                />
                <p className="text-xs text-zinc-500">
                  Usa {'{'}parametro{'}'} para valores dinámicos. Ej: {'{'}fecha_ini{'}'}, {'{'}fecha_fin{'}'}, {'{'}almacen{'}'}
                </p>
              </div>
              
              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => setShowNuevaConsulta(false)}>
                  Cancelar
                </Button>
                <Button onClick={guardarNuevaConsulta} disabled={guardando}>
                  {guardando ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                  Guardar Consulta
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
