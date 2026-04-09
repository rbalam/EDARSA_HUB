import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { fetchServersOperativos } from '@/services/serversService';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { 
  Loader2, Database, Table, Columns, Link2, Eye, Play, 
  ChevronRight, Search, Download, Server, X, FileText,
  Plus, Upload, Terminal, CheckCircle2, XCircle, AlertTriangle, Pencil,
  Maximize2, Minimize2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ============ COMPONENTE: AGREGAR TABLAS (ADMIN ONLY) ============
function AgregarTablasModal({ isOpen, onClose, serverSeleccionado, serverName, onSuccess }) {
  const [titulo, setTitulo] = useState('');
  const [script, setScript] = useState('');
  const [ejecutando, setEjecutando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [logs, setLogs] = useState([]);
  const [archivo, setArchivo] = useState(null);
  const [activeTab, setActiveTab] = useState('nuevo'); // 'nuevo' | 'pendientes'
  const [scriptsPendientes, setScriptsPendientes] = useState([]);
  const [loadingPendientes, setLoadingPendientes] = useState(false);
  const [scriptSeleccionado, setScriptSeleccionado] = useState(null);
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [adminCredentials, setAdminCredentials] = useState({ username: '', password: '' });
  const [editandoScript, setEditandoScript] = useState(null); // Script que se está editando
  const [editTitulo, setEditTitulo] = useState('');
  const [editContenido, setEditContenido] = useState('');
  const [guardandoEdicion, setGuardandoEdicion] = useState(false);
  const fileInputRef = useRef(null);

  // Cargar scripts pendientes cuando se abre el tab
  useEffect(() => {
    if (activeTab === 'pendientes' && serverSeleccionado) {
      cargarScriptsPendientes();
    }
  }, [activeTab, serverSeleccionado]);

  const cargarScriptsPendientes = async () => {
    setLoadingPendientes(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/explorador/scripts-pendientes/${serverSeleccionado}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setScriptsPendientes(response.data);
    } catch (error) {
      console.error('Error cargando scripts pendientes:', error);
      setScriptsPendientes([]);
    } finally {
      setLoadingPendientes(false);
    }
  };

  const agregarLog = (tipo, mensaje, detalle = '') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { tipo, mensaje, detalle, timestamp }]);
  };

  const cargarArchivo = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.endsWith('.sql')) {
        toast.error('Solo se permiten archivos .sql');
        return;
      }
      setArchivo(file);
      if (!titulo) {
        setTitulo(file.name.replace('.sql', ''));
      }
      const reader = new FileReader();
      reader.onload = (event) => {
        setScript(event.target.result);
        toast.success(`Archivo ${file.name} cargado`);
        agregarLog('info', `Archivo cargado: ${file.name}`, `${(file.size / 1024).toFixed(1)} KB`);
      };
      reader.readAsText(file);
    }
  };

  const guardarEnStandby = async () => {
    if (!script.trim()) {
      toast.error('El script está vacío');
      return;
    }
    if (!titulo.trim()) {
      toast.error('Ingresa un título/descripción para el script');
      return;
    }

    setGuardando(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API_URL}/api/explorador/guardar-script/${serverSeleccionado}`,
        { script, titulo },
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } }
      );
      toast.success('Script guardado en stand-by. Un administrador de BD podrá ejecutarlo.');
      limpiar();
      setActiveTab('pendientes');
      cargarScriptsPendientes();
    } catch (error) {
      toast.error(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setGuardando(false);
    }
  };

  const ejecutarConCredenciales = async () => {
    if (!adminCredentials.username || !adminCredentials.password) {
      toast.error('Ingresa usuario y contraseña del administrador');
      return;
    }

    setEjecutando(true);
    setLogs([]);
    agregarLog('info', `Ejecutando: ${scriptSeleccionado?.titulo || 'Script'}`, `Con credenciales de: ${adminCredentials.username}`);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/explorador/ejecutar-con-credenciales/${serverSeleccionado}`,
        { 
          script_id: scriptSeleccionado?._id,
          script: scriptSeleccionado?.script || script,
          titulo: scriptSeleccionado?.titulo || titulo,
          admin_username: adminCredentials.username,
          admin_password: adminCredentials.password
        },
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } }
      );

      const resultado = response.data;
      resultado.resultados.forEach((r, idx) => {
        if (r.exito) {
          agregarLog('success', `[${idx + 1}] ${r.tipo}`, r.mensaje);
        } else {
          agregarLog('error', `[${idx + 1}] ${r.tipo}`, r.error);
        }
      });

      if (resultado.exitosos === resultado.total) {
        toast.success(`✅ Script ejecutado: ${resultado.exitosos}/${resultado.total} comandos exitosos`);
        agregarLog('success', 'COMPLETADO', `${resultado.exitosos} de ${resultado.total} comandos ejecutados correctamente`);
        if (onSuccess) onSuccess();
        cargarScriptsPendientes();
      } else {
        toast.warning(`⚠️ Script con errores: ${resultado.exitosos}/${resultado.total} exitosos`);
        agregarLog('warning', 'COMPLETADO CON ERRORES', `${resultado.exitosos} exitosos, ${resultado.fallidos} fallidos`);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      toast.error(`Error: ${errorMsg}`);
      agregarLog('error', 'ERROR', errorMsg);
    } finally {
      setEjecutando(false);
      setShowCredentialsModal(false);
      setAdminCredentials({ username: '', password: '' });
    }
  };

  const eliminarScriptPendiente = async (scriptId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${API_URL}/api/explorador/script-pendiente/${scriptId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Script eliminado');
      cargarScriptsPendientes();
    } catch (error) {
      toast.error(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const iniciarEdicion = (sp) => {
    setEditandoScript(sp);
    setEditTitulo(sp.titulo);
    setEditContenido(sp.script);
  };

  const cancelarEdicion = () => {
    setEditandoScript(null);
    setEditTitulo('');
    setEditContenido('');
  };

  const guardarEdicion = async () => {
    if (!editTitulo.trim()) {
      toast.error('El título es requerido');
      return;
    }
    if (!editContenido.trim()) {
      toast.error('El script no puede estar vacío');
      return;
    }

    setGuardandoEdicion(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API_URL}/api/explorador/script-pendiente/${editandoScript._id}`,
        { titulo: editTitulo, script: editContenido },
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } }
      );
      toast.success('Script actualizado');
      cancelarEdicion();
      cargarScriptsPendientes();
    } catch (error) {
      toast.error(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setGuardandoEdicion(false);
    }
  };

  const limpiar = () => {
    setTitulo('');
    setScript('');
    setLogs([]);
    setArchivo(null);
    setScriptSeleccionado(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  if (!isOpen) return null;

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5 text-green-600" />
              Agregar Tablas - {serverName}
            </DialogTitle>
          </DialogHeader>

          {/* Tabs */}
          <div className="flex border-b mb-4">
            <button
              onClick={() => setActiveTab('nuevo')}
              className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'nuevo' 
                  ? 'border-green-600 text-green-600' 
                  : 'border-transparent text-zinc-500 hover:text-zinc-700'
              }`}
            >
              <Plus className="h-4 w-4 inline mr-1" />
              Nuevo Script
            </button>
            <button
              onClick={() => setActiveTab('pendientes')}
              className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'pendientes' 
                  ? 'border-blue-600 text-blue-600' 
                  : 'border-transparent text-zinc-500 hover:text-zinc-700'
              }`}
            >
              <FileText className="h-4 w-4 inline mr-1" />
              Scripts Pendientes
              {scriptsPendientes.length > 0 && (
                <span className="ml-1 bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs">
                  {scriptsPendientes.length}
                </span>
              )}
            </button>
          </div>

          {activeTab === 'nuevo' ? (
            <div className="flex-1 overflow-hidden flex flex-col gap-4">
              {/* Campo de Título/Descripción */}
              <div>
                <label className="text-sm font-medium text-zinc-700 mb-1 block">
                  Descripción del Script <span className="text-red-500">*</span>
                </label>
                <Input
                  value={titulo}
                  onChange={(e) => setTitulo(e.target.value)}
                  placeholder="Ej: Crear tablas de Recursos Humanos, Migración de datos, etc."
                  disabled={ejecutando || guardando}
                  className="w-full"
                />
              </div>

              {/* Área de entrada */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <input
                    type="file"
                    accept=".sql"
                    onChange={cargarArchivo}
                    ref={fileInputRef}
                    className="hidden"
                  />
                  <Button 
                    variant="outline" 
                    onClick={() => fileInputRef.current?.click()}
                    disabled={ejecutando || guardando}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Cargar .SQL
                  </Button>
                  {archivo && (
                    <span className="text-sm text-zinc-500 flex items-center gap-1">
                      <FileText className="h-4 w-4" />
                      {archivo.name}
                    </span>
                  )}
                  <div className="flex-1" />
                  <Button variant="ghost" onClick={limpiar} disabled={ejecutando || guardando}>
                    Limpiar
                  </Button>
                </div>

                <Textarea
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                  placeholder={`-- Pega tu script SQL aquí
-- Ejemplo:
CREATE TABLE MiTabla (
    id INT PRIMARY KEY IDENTITY(1,1),
    nombre NVARCHAR(100),
    fecha DATETIME DEFAULT GETDATE()
);`}
                  className="font-mono text-sm h-40 resize-none"
                  disabled={ejecutando || guardando}
                />

                <div className="flex gap-2">
                  <Button 
                    onClick={guardarEnStandby} 
                    disabled={ejecutando || guardando || !script.trim() || !titulo.trim()} 
                    variant="outline"
                    className="flex-1 border-blue-300 text-blue-700 hover:bg-blue-50"
                  >
                    {guardando ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Guardando...
                      </>
                    ) : (
                      <>
                        <FileText className="h-4 w-4 mr-2" />
                        Guardar en Stand-by
                      </>
                    )}
                  </Button>
                  <Button 
                    onClick={() => {
                      setScriptSeleccionado(null);
                      setShowCredentialsModal(true);
                    }} 
                    disabled={ejecutando || guardando || !script.trim()} 
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Ejecutar con Credenciales Admin
                  </Button>
                </div>
              </div>

              {/* Log de ejecución */}
              {logs.length > 0 && (
                <div className="flex-1 min-h-0">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-zinc-700 flex items-center gap-2">
                      <Terminal className="h-4 w-4" />
                      Log de Ejecución
                    </span>
                    <span className="text-xs text-zinc-500">{logs.length} entradas</span>
                  </div>
                  <div className="border rounded-lg bg-zinc-900 p-3 h-32 overflow-y-auto font-mono text-xs">
                    {logs.map((log, idx) => (
                      <div 
                        key={idx} 
                        className={`flex items-start gap-2 py-1 ${
                          log.tipo === 'success' ? 'text-green-400' :
                          log.tipo === 'error' ? 'text-red-400' :
                          log.tipo === 'warning' ? 'text-yellow-400' :
                          'text-blue-400'
                        }`}
                      >
                        <span className="text-zinc-500 shrink-0">[{log.timestamp}]</span>
                        <span className="font-semibold shrink-0">{log.mensaje}</span>
                        {log.detalle && <span className="text-zinc-400 truncate">{log.detalle}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Advertencia */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2">
                <AlertTriangle className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                <div className="text-sm text-blue-800">
                  <strong>Nota:</strong> Puedes guardar el script en "Stand-by" para que un administrador 
                  de BD lo ejecute después con sus propias credenciales (con permisos de CREATE TABLE).
                </div>
              </div>
            </div>
          ) : (
            /* Tab: Scripts Pendientes */
            <div className="flex-1 overflow-auto">
              {loadingPendientes ? (
                <div className="flex items-center justify-center h-40">
                  <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
                </div>
              ) : editandoScript ? (
                /* Formulario de edición */
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-zinc-800">Editando Script</h4>
                    <Button variant="ghost" size="sm" onClick={cancelarEdicion}>
                      <X className="h-4 w-4 mr-1" /> Cancelar
                    </Button>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-zinc-700 mb-1 block">
                      Descripción del Script <span className="text-red-500">*</span>
                    </label>
                    <Input
                      value={editTitulo}
                      onChange={(e) => setEditTitulo(e.target.value)}
                      placeholder="Descripción del script"
                      disabled={guardandoEdicion}
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-zinc-700 mb-1 block">
                      Script SQL <span className="text-red-500">*</span>
                    </label>
                    <Textarea
                      value={editContenido}
                      onChange={(e) => setEditContenido(e.target.value)}
                      className="font-mono text-sm h-64 resize-none"
                      disabled={guardandoEdicion}
                    />
                  </div>

                  <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={cancelarEdicion} disabled={guardandoEdicion}>
                      Cancelar
                    </Button>
                    <Button 
                      onClick={guardarEdicion} 
                      disabled={guardandoEdicion || !editTitulo.trim() || !editContenido.trim()}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      {guardandoEdicion ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin mr-2" />
                          Guardando...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-2" />
                          Guardar Cambios
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              ) : scriptsPendientes.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 text-zinc-500">
                  <FileText className="h-12 w-12 mb-2 opacity-30" />
                  <p>No hay scripts pendientes</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {scriptsPendientes.map((sp) => (
                    <div key={sp._id} className="border rounded-lg p-4 bg-zinc-50 hover:bg-zinc-100 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-zinc-800">{sp.titulo}</h4>
                          <p className="text-xs text-zinc-500 mt-1">
                            Creado por: {sp.creado_por} • {new Date(sp.fecha_creacion).toLocaleString()}
                          </p>
                          <p className="text-xs text-zinc-500">
                            {sp.num_statements} comandos SQL
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => iniciarEdicion(sp)}
                            className="text-blue-600 hover:bg-blue-50"
                            title="Editar script"
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => eliminarScriptPendiente(sp._id)}
                            className="text-red-600 hover:bg-red-50"
                            title="Eliminar script"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => {
                              setScriptSeleccionado(sp);
                              setShowCredentialsModal(true);
                            }}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <Play className="h-4 w-4 mr-1" />
                            Ejecutar
                          </Button>
                        </div>
                      </div>
                      {/* Preview del script */}
                      <div className="mt-3 bg-zinc-900 rounded p-2 max-h-20 overflow-auto">
                        <pre className="text-xs text-zinc-300 whitespace-pre-wrap">
                          {sp.script.substring(0, 300)}{sp.script.length > 300 ? '...' : ''}
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal de Credenciales de Administrador */}
      <Dialog open={showCredentialsModal} onOpenChange={setShowCredentialsModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-600" />
              Credenciales de Administrador BD
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-800">
              <strong>Importante:</strong> Ingresa las credenciales de un usuario SQL Server con permisos 
              de CREATE TABLE (ej: sa, db_owner, db_ddladmin).
            </div>

            <div>
              <label className="text-sm font-medium text-zinc-700 mb-1 block">
                Usuario SQL Server
              </label>
              <Input
                value={adminCredentials.username}
                onChange={(e) => setAdminCredentials(prev => ({ ...prev, username: e.target.value }))}
                placeholder="Ej: sa, AdminDB, etc."
                disabled={ejecutando}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-zinc-700 mb-1 block">
                Contraseña
              </label>
              <Input
                type="password"
                value={adminCredentials.password}
                onChange={(e) => setAdminCredentials(prev => ({ ...prev, password: e.target.value }))}
                placeholder="••••••••"
                disabled={ejecutando}
              />
            </div>

            <div className="text-xs text-zinc-500">
              Servidor: <strong>{serverName}</strong>
              {scriptSeleccionado && (
                <>
                  <br />
                  Script: <strong>{scriptSeleccionado.titulo}</strong>
                </>
              )}
            </div>
          </div>

          <div className="flex gap-2 justify-end">
            <Button 
              variant="outline" 
              onClick={() => {
                setShowCredentialsModal(false);
                setAdminCredentials({ username: '', password: '' });
              }}
              disabled={ejecutando}
            >
              Cancelar
            </Button>
            <Button 
              onClick={ejecutarConCredenciales}
              disabled={ejecutando || !adminCredentials.username || !adminCredentials.password}
              className="bg-green-600 hover:bg-green-700"
            >
              {ejecutando ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Ejecutando...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Ejecutar Script
                </>
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Componente de Buscador Global
function BuscadorGlobal({ serverSeleccionado, onSelectTabla }) {
  const [busqueda, setBusqueda] = useState('');
  const [tipoBusqueda, setTipoBusqueda] = useState('todo');
  const [resultados, setResultados] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tablaFiltro, setTablaFiltro] = useState('');

  const buscar = async () => {
    if (!busqueda.trim() || busqueda.length < 2) {
      toast.error('Ingresa al menos 2 caracteres');
      return;
    }
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = { q: busqueda, tipo: tipoBusqueda };
      if (tablaFiltro) params.tabla = tablaFiltro;
      
      const response = await axios.get(
        `${API_URL}/api/explorador/buscar/${serverSeleccionado}`,
        { params, headers: { Authorization: `Bearer ${token}` } }
      );
      setResultados(response.data);
      toast.success(`${response.data.total} resultados encontrados`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error en búsqueda');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') buscar();
  };

  return (
    <Card className="border-2 border-blue-200 bg-blue-50/30">
      <CardHeader className="py-3 bg-blue-100">
        <CardTitle className="text-sm flex items-center gap-2">
          <Search className="h-4 w-4" />
          Buscador Global de Base de Datos
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3 space-y-3">
        <div className="flex gap-2">
          <Input
            placeholder="Buscar tablas, columnas, datos..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1"
            data-testid="buscador-global-input"
          />
          <Select value={tipoBusqueda} onValueChange={setTipoBusqueda}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todo">Todo</SelectItem>
              <SelectItem value="tablas">Tablas</SelectItem>
              <SelectItem value="columnas">Columnas</SelectItem>
              <SelectItem value="datos">Datos</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={buscar} disabled={loading || !busqueda.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          </Button>
        </div>

        {tipoBusqueda === 'datos' && (
          <Input
            placeholder="Filtrar en tabla específica (opcional)..."
            value={tablaFiltro}
            onChange={(e) => setTablaFiltro(e.target.value)}
            className="text-sm"
          />
        )}

        {/* Resultados */}
        {resultados && (
          <div className="space-y-3 mt-3">
            {/* Tablas encontradas */}
            {resultados.tablas?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-zinc-600 mb-1 flex items-center gap-1">
                  <Database className="h-3 w-3" /> Tablas ({resultados.tablas.length})
                </h4>
                <div className="flex flex-wrap gap-1">
                  {resultados.tablas.map((t, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded cursor-pointer hover:bg-green-200 transition-colors"
                      onClick={() => onSelectTabla(t.tabla)}
                    >
                      {t.tabla}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Columnas encontradas */}
            {resultados.columnas?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-zinc-600 mb-1 flex items-center gap-1">
                  <Columns className="h-3 w-3" /> Columnas ({resultados.columnas.length})
                </h4>
                <div className="max-h-[150px] overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="bg-zinc-100 sticky top-0">
                      <tr>
                        <th className="py-1 px-2 text-left">Tabla</th>
                        <th className="py-1 px-2 text-left">Columna</th>
                        <th className="py-1 px-2 text-left">Tipo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {resultados.columnas.map((c, i) => (
                        <tr key={i} className="border-b hover:bg-zinc-50 cursor-pointer" onClick={() => onSelectTabla(c.tabla)}>
                          <td className="py-1 px-2 text-blue-600">{c.tabla}</td>
                          <td className="py-1 px-2 font-medium">{c.columna}</td>
                          <td className="py-1 px-2 text-zinc-500">{c.tipo_dato}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Datos encontrados */}
            {resultados.datos?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-zinc-600 mb-1 flex items-center gap-1">
                  <FileText className="h-3 w-3" /> Datos ({resultados.datos.length})
                </h4>
                <div className="max-h-[200px] overflow-y-auto space-y-2">
                  {resultados.datos.map((d, i) => (
                    <div key={i} className="p-2 bg-white border rounded text-xs">
                      <div className="font-semibold text-purple-600 mb-1 cursor-pointer" onClick={() => onSelectTabla(d.tabla)}>
                        {d.tabla}
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-1">
                        {Object.entries(d.fila).slice(0, 8).map(([key, val], j) => (
                          <div key={j} className="truncate">
                            <span className="text-zinc-500">{key}: </span>
                            <span className="font-medium">{val?.toString()?.substring(0, 30) || '-'}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {resultados.total === 0 && (
              <div className="text-center py-4 text-zinc-500">
                <Search className="h-8 w-8 mx-auto mb-2 opacity-30" />
                <p>No se encontraron resultados para "{busqueda}"</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function ExploradorBD() {
  const navigate = useNavigate();
  const [servers, setServers] = useState([]);
  const [serverSeleccionado, setServerSeleccionado] = useState('');
  const [serverInfo, setServerInfo] = useState(null);
  const [tablas, setTablas] = useState([]);
  const [tablaSeleccionada, setTablaSeleccionada] = useState(null);
  const [columnas, setColumnas] = useState([]);
  const [relaciones, setRelaciones] = useState([]);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState({ tablas: false, columnas: false, relaciones: false });
  
  // Query libre
  const [queryLibre, setQueryLibre] = useState('SELECT TOP 10 * FROM ');
  const [resultadoQuery, setResultadoQuery] = useState(null);
  const [filtroTabla, setFiltroTabla] = useState('');
  
  // Modal Agregar Tablas
  const [showAgregarTablas, setShowAgregarTablas] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  
  // Modal Agregar Servidor
  const [showAgregarServidor, setShowAgregarServidor] = useState(false);
  const [todosLosServidores, setTodosLosServidores] = useState([]);
  const [loadingServidores, setLoadingServidores] = useState(false);

  // Cargar todos los servidores para el modal
  const cargarTodosLosServidores = async () => {
    setLoadingServidores(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Filtrar los que NO están ya en el explorador
      const servidoresDisponibles = response.data.filter(
        s => !servers.some(existing => existing.id === s.id)
      );
      setTodosLosServidores(servidoresDisponibles);
    } catch (error) {
      toast.error('Error cargando servidores');
    } finally {
      setLoadingServidores(false);
    }
  };

  // Agregar servidor al explorador
  const agregarServidorAlExplorador = (servidor) => {
    // Agregar a la lista local de servidores del explorador
    setServers(prev => [...prev, servidor]);
    toast.success(`${servidor.name} agregado al explorador`);
    setShowAgregarServidor(false);
  };

  useEffect(() => {
    cargarServers();
    // Verificar si el usuario es admin
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    setIsAdmin(user.rol === 'Administrador' || user.email === 'admin@inventario.com');
  }, []);

  const cargarServers = async () => {
    try {
      // Cargar TODOS los servidores (no solo los operativos) para el Explorador de BD
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/servers`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setServers(response.data || []);
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

  // Estado para grupos expandidos/colapsados
  const [gruposExpandidos, setGruposExpandidos] = useState({});
  
  // Estado para modo pantalla completa (ocultar sidebar)
  const [fullscreenMode, setFullscreenMode] = useState(false);

  // Función para agrupar tablas por categoría
  const agruparTablas = (tablasList) => {
    const categorias = {
      'Usuario': ['usuario', 'user', 'empleado', 'personal', 'rrhh', 'nomina', 'colaborador', 'login', 'sesion', 'rol', 'permiso'],
      'Ventas': ['venta', 'comanda', 'cheque', 'ticket', 'folio', 'pedido', 'orden', 'factura', 'cuenta', 'pago', 'cobro', 'caja', 'corte', 'propina', 'descuento', 'turno'],
      'Proveedor': ['proveedor', 'compra', 'requisicion', 'recepcion', 'devolucion', 'supplier'],
      'Producto': ['producto', 'articulo', 'insumo', 'presentacion', 'inventario', 'almacen', 'existencia', 'receta', 'ingrediente', 'menu', 'platillo', 'bebida', 'item'],
      'Catálogos': ['catalogo', 'categoria', 'familia', 'subfamilia', 'grupo', 'tipo', 'unidad', 'medida', 'moneda', 'impuesto', 'iva', 'forma_pago', 'metodo'],
      'Configuración': ['config', 'parametro', 'opcion', 'setting', 'sistema', 'empresa', 'sucursal', 'restaurante', 'negocio'],
      'Clientes': ['cliente', 'customer', 'membresia', 'fidelidad', 'puntos', 'reservacion', 'mesa'],
      'Reportes': ['reporte', 'bitacora', 'log', 'historico', 'auditoria', 'movimiento']
    };

    const grupos = {};
    const sinCategoria = [];

    tablasList.forEach(tabla => {
      const nombreTabla = tabla.tabla.toLowerCase();
      let categoriaEncontrada = null;

      // Buscar en qué categoría encaja
      for (const [categoria, palabrasClave] of Object.entries(categorias)) {
        if (palabrasClave.some(palabra => nombreTabla.includes(palabra))) {
          categoriaEncontrada = categoria;
          break;
        }
      }

      if (categoriaEncontrada) {
        if (!grupos[categoriaEncontrada]) {
          grupos[categoriaEncontrada] = [];
        }
        grupos[categoriaEncontrada].push(tabla);
      } else {
        sinCategoria.push(tabla);
      }
    });

    // Ordenar las tablas dentro de cada grupo
    Object.keys(grupos).forEach(cat => {
      grupos[cat].sort((a, b) => a.tabla.localeCompare(b.tabla));
    });

    // Agregar las tablas sin categoría al final
    if (sinCategoria.length > 0) {
      sinCategoria.sort((a, b) => a.tabla.localeCompare(b.tabla));
      grupos['Otras Tablas'] = sinCategoria;
    }

    return grupos;
  };

  const tablasAgrupadas = agruparTablas(tablasFiltradas);

  const toggleGrupo = (grupo) => {
    setGruposExpandidos(prev => ({
      ...prev,
      [grupo]: !prev[grupo]
    }));
  };

  // Expandir todos los grupos por defecto cuando cambian las tablas
  useEffect(() => {
    if (Object.keys(tablasAgrupadas).length > 0) {
      const todosExpandidos = {};
      Object.keys(tablasAgrupadas).forEach(grupo => {
        todosExpandidos[grupo] = true;
      });
      setGruposExpandidos(todosExpandidos);
    }
  }, [tablas]);

  return (
    <div 
      className={fullscreenMode 
        ? "fixed inset-0 z-[100] bg-white overflow-auto p-6" 
        : "space-y-4"
      } 
      data-testid="explorador-bd"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-800">Explorador de Base de Datos</h1>
          <p className="text-sm text-zinc-500">Explora tablas, columnas y relaciones de tus sistemas</p>
        </div>
        {/* Botón Pantalla Completa / Minimizar */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setFullscreenMode(!fullscreenMode)}
          className="h-8 px-3"
          title={fullscreenMode ? "Salir de pantalla completa" : "Ver en pantalla completa"}
        >
          {fullscreenMode ? (
            <>
              <Minimize2 className="h-4 w-4 mr-2" />
              Minimizar
            </>
          ) : (
            <>
              <Maximize2 className="h-4 w-4 mr-2" />
              Pantalla Completa
            </>
          )}
        </Button>
      </div>

      <div className={fullscreenMode ? "space-y-4 mt-4" : "space-y-4"}>
      {/* Selector de servidor */}
      <Card className="border">
        <CardContent className="py-4">
          <div className="flex items-center gap-4 flex-wrap">
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
            
            {/* Botón Agregar BD */}
            <Button 
              variant="outline"
              onClick={() => {
                cargarTodosLosServidores();
                setShowAgregarServidor(true);
              }}
              className="border-blue-200 text-blue-700 hover:bg-blue-50"
              data-testid="btn-agregar-bd"
            >
              <Plus className="h-4 w-4 mr-2" />
              Agregar BD
            </Button>
            
            {serverInfo && (
              <div className="text-sm text-zinc-500">
                <span className="font-medium">{serverInfo.sistema}</span> • {serverInfo.database}
              </div>
            )}
            <div className="flex-1" />
            {/* Botón Agregar Tablas - Solo Admin */}
            {isAdmin && serverSeleccionado && (
              <Button 
                onClick={() => setShowAgregarTablas(true)}
                className="bg-green-600 hover:bg-green-700"
                data-testid="btn-agregar-tablas"
              >
                <Plus className="h-4 w-4 mr-2" />
                Agregar Tablas
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Modal Agregar Tablas */}
      <AgregarTablasModal
        isOpen={showAgregarTablas}
        onClose={() => setShowAgregarTablas(false)}
        serverSeleccionado={serverSeleccionado}
        serverName={servers.find(s => s.id === serverSeleccionado)?.name || ''}
        onSuccess={() => cargarTablas(serverSeleccionado)}
      />

      {serverSeleccionado && (
        <>
          {/* Buscador Global */}
          <BuscadorGlobal 
            serverSeleccionado={serverSeleccionado} 
            onSelectTabla={(tabla) => {
              setFiltroTabla('');
              seleccionarTabla(tabla);
            }}
          />

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Lista de tablas */}
          <Card className="border">
            <CardHeader className="py-2 bg-zinc-100">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  Tablas ({tablasFiltradas.length})
                </CardTitle>
                <div className="flex gap-1">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-6 px-2 text-xs"
                    onClick={() => {
                      const todosExpandidos = {};
                      Object.keys(tablasAgrupadas).forEach(g => todosExpandidos[g] = true);
                      setGruposExpandidos(todosExpandidos);
                    }}
                    title="Expandir todo"
                  >
                    <ChevronRight className="h-3 w-3 rotate-90" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-6 px-2 text-xs"
                    onClick={() => setGruposExpandidos({})}
                    title="Contraer todo"
                  >
                    <ChevronRight className="h-3 w-3" />
                  </Button>
                </div>
              </div>
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
                ) : Object.keys(tablasAgrupadas).length === 0 ? (
                  <div className="text-center py-4 text-zinc-400 text-sm">
                    No se encontraron tablas
                  </div>
                ) : (
                  Object.entries(tablasAgrupadas).map(([grupo, tablasGrupo]) => (
                    <div key={grupo} className="mb-2">
                      {/* Header del grupo */}
                      <div 
                        className="flex items-center gap-2 p-2 bg-zinc-100 rounded cursor-pointer hover:bg-zinc-200 transition-colors"
                        onClick={() => toggleGrupo(grupo)}
                      >
                        <ChevronRight className={`h-3 w-3 transition-transform ${gruposExpandidos[grupo] ? 'rotate-90' : ''}`} />
                        <Database className="h-3 w-3 text-zinc-600" />
                        <span className="text-xs font-semibold text-zinc-700 flex-1">{grupo}</span>
                        <span className="text-xs text-zinc-500 bg-zinc-200 px-1.5 py-0.5 rounded">{tablasGrupo.length}</span>
                      </div>
                      
                      {/* Tablas del grupo */}
                      {gruposExpandidos[grupo] && (
                        <div className="ml-4 mt-1 space-y-0.5 border-l-2 border-zinc-200 pl-2">
                          {tablasGrupo.map(t => (
                            <div 
                              key={t.tabla}
                              className={`p-1.5 rounded cursor-pointer text-sm flex items-center gap-2 ${
                                tablaSeleccionada === t.tabla 
                                  ? 'bg-blue-100 text-blue-800' 
                                  : 'hover:bg-zinc-50'
                              }`}
                              onClick={() => seleccionarTabla(t.tabla)}
                            >
                              <Table className="h-3 w-3 flex-shrink-0" />
                              <span className="truncate text-xs">{t.tabla}</span>
                            </div>
                          ))}
                        </div>
                      )}
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
        </>
      )}
      
      {/* Modal Agregar Servidor al Explorador */}
      <Dialog open={showAgregarServidor} onOpenChange={setShowAgregarServidor}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Agregar BD al Explorador
            </DialogTitle>
            <DialogDescription>
              Selecciona un servidor para agregarlo al explorador
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {loadingServidores ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
              </div>
            ) : todosLosServidores.length === 0 ? (
              <div className="text-center py-8 text-zinc-500">
                <Database className="h-10 w-10 mx-auto mb-2 opacity-50" />
                <p>No hay servidores adicionales disponibles</p>
                <p className="text-sm mt-1">Todos los servidores ya están en el explorador</p>
                <Button 
                  variant="link" 
                  className="mt-2"
                  onClick={() => {
                    setShowAgregarServidor(false);
                    navigate('/servidores');
                  }}
                >
                  Ir a configurar servidores →
                </Button>
              </div>
            ) : (
              todosLosServidores.map(servidor => (
                <div 
                  key={servidor.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-zinc-50 cursor-pointer transition-colors"
                  onClick={() => agregarServidorAlExplorador(servidor)}
                >
                  <div className="flex items-center gap-3">
                    <div className="bg-blue-50 p-2 rounded-lg">
                      <Server className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-zinc-900">{servidor.name}</p>
                      <p className="text-xs text-zinc-500">{servidor.system_type} • {servidor.host}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              ))
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAgregarServidor(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </div>
  );
}
