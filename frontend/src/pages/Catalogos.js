import logger from '../services/logger';
import { useState, useEffect } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Toaster, toast } from 'sonner';
import AuthorizationMatrixAdmin from '../components/catalogos/AuthorizationMatrixAdmin';
import {
  Globe,
  Users,
  Calculator,
  ShoppingCart,
  Package,
  Building,
  DollarSign,
  TrendingUp,
  Shield,
  GitMerge,
  Search,
  Plus,
  Edit2,
  Power,
  PowerOff,
  Loader2,
  CheckCircle,
  XCircle,
  ChevronRight,
  Database,
  RefreshCw,
  Settings,
  AlertTriangle,
} from 'lucide-react';
// FASE AUTH-SECURITY-01 / FASE 4: getToken eliminado, auth viaja en cookie httpOnly

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Mapeo de iconos por dominio
const ICONOS_DOMINIO = {
  generales: Globe,
  rh: Users,
  nomina: Calculator,
  compras: ShoppingCart,
  inventarios: Package,
  activos: Building,
  finanzas: DollarSign,
  ventas: TrendingUp,
  seguridad: Shield,
  homologacion: GitMerge,
  configuracion: Settings,
};

const Catalogos = () => {
  const [dominios, setDominios] = useState({});
  const [dominioActivo, setDominioActivo] = useState(null);
  const [catalogoActivo, setCatalogoActivo] = useState(null);
  const [registros, setRegistros] = useState([]);
  const [estructura, setEstructura] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingRegistros, setLoadingRegistros] = useState(false);
  const [buscar, setBuscar] = useState('');
  const [soloActivos, setSoloActivos] = useState(false);
  
  // Modal de edición/creación
  const [modalAbierto, setModalAbierto] = useState(false);
  const [modoEdicion, setModoEdicion] = useState(false);
  const [registroEditando, setRegistroEditando] = useState(null);
  const [formData, setFormData] = useState({});
  const [guardando, setGuardando] = useState(false);
  
  // Modal de administración
  const [modalAdmin, setModalAdmin] = useState(false);
  const [estadoTablas, setEstadoTablas] = useState({});
  const [creandoTablas, setCreandoTablas] = useState(false);

  // Cargar dominios al iniciar
  useEffect(() => {
    cargarDominios();
  }, []);

  // Cargar registros cuando cambia el catálogo activo
  useEffect(() => {
    if (catalogoActivo) {
      cargarRegistros();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalogoActivo, soloActivos]);

  const cargarDominios = async () => {
    try {
      setLoading(true);
      const response = await api.get('/catalogos/dominios');
      
      const data = response.data;
      setDominios(data.dominios || {});
      
      // Seleccionar primer dominio por defecto
      const primerDominio = Object.keys(data.dominios || {})[0];
      if (primerDominio) {
        setDominioActivo(primerDominio);
      }
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error cargando catálogos');
    } finally {
      setLoading(false);
    }
  };

  const cargarRegistros = async () => {
    if (!catalogoActivo) return;
    
    try {
      setLoadingRegistros(true);
      const params = new URLSearchParams();
      if (soloActivos) params.append('solo_activos', 'true');
      if (buscar) params.append('buscar', buscar);
      
      const response = await api.get(`/catalogos/tabla/${catalogoActivo.tabla}?${params}`);
      
      const data = response.data;
      setRegistros(data.registros || []);
      setEstructura(data.estructura || null);
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error cargando registros');
      setRegistros([]);
    } finally {
      setLoadingRegistros(false);
    }
  };

  const buscarRegistros = () => {
    cargarRegistros();
  };

  const abrirModalCrear = () => {
    setModoEdicion(false);
    setRegistroEditando(null);
    setFormData({});
    setModalAbierto(true);
  };

  const abrirModalEditar = (registro) => {
    setModoEdicion(true);
    setRegistroEditando(registro);
    setFormData({ ...registro });
    setModalAbierto(true);
  };

  const guardarRegistro = async () => {
    if (!catalogoActivo || !estructura) return;
    
    try {
      setGuardando(true);
      
      const endpoint = `/catalogos/tabla/${catalogoActivo.tabla}${modoEdicion ? `/${registroEditando[estructura.pk]}` : ''}`;
      
      if (modoEdicion) {
        await api.put(endpoint, { datos: formData });
      } else {
        await api.post(endpoint, { datos: formData });
      }
      
      toast.success(modoEdicion ? 'Registro actualizado' : 'Registro creado');
      setModalAbierto(false);
      cargarRegistros();
      cargarDominios(); // Actualizar conteos
    } catch (error) {
      logger.error('Error:', error);
      toast.error(error.message || 'Error guardando registro');
    } finally {
      setGuardando(false);
    }
  };

  const toggleActivoRegistro = async (registro, activar) => {
    if (!catalogoActivo || !estructura) return;
    
    try {
      const accion = activar ? 'activar' : 'desactivar';
      await api.put(`/catalogos/tabla/${catalogoActivo.tabla}/${registro[estructura.pk]}/${accion}`);
      
      toast.success(`Registro ${activar ? 'activado' : 'desactivado'}`);
      cargarRegistros();
      cargarDominios();
    } catch (error) {
      logger.error('Error:', error);
      toast.error(error.response?.data?.detail || error.message);
    }
  };

  const verificarTablas = async () => {
    try {
      const response = await api.get('/catalogos/admin/verificar-tablas');
      setEstadoTablas(response.data.tablas || {});
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error verificando tablas');
    }
  };

  const crearTablasNuevas = async () => {
    try {
      setCreandoTablas(true);
      const response = await api.post('/catalogos/admin/crear-tablas');
      
      toast.success(`Tablas creadas: ${response.data.exitosos} exitosas, ${response.data.errores} errores`);
      verificarTablas();
      cargarDominios();
    } catch (error) {
      logger.error('Error:', error);
      toast.error(error.response?.data?.detail || error.message);
    } finally {
      setCreandoTablas(false);
    }
  };

  const abrirModalAdmin = () => {
    verificarTablas();
    setModalAdmin(true);
  };

  // Catálogos canónicos para Tipos de Autorización.
  const [matrizSelectores, setMatrizSelectores] = useState({
    modulos: [],
    acciones: [],
  });

  useEffect(() => {
    const cargarSelectoresMatriz = async () => {
      if (
        !modalAbierto ||
        catalogoActivo?.tabla !== 'Usuario_TiposAutorizacion'
      ) {
        return;
      }

      try {
        const response = await api.get(
          '/catalogos/admin/matriz-autorizacion/catalogos'
        );

        const data = response?.data || {};

        setMatrizSelectores({
          modulos: Array.isArray(data.modulos) ? data.modulos : [],
          acciones: Array.isArray(data.acciones) ? data.acciones : [],
        });
      } catch (error) {
        logger.error(
          'Error cargando selectores canónicos de autorización:',
          error
        );

        setMatrizSelectores({
          modulos: [],
          acciones: [],
        });
      }
    };

    cargarSelectoresMatriz();
  }, [modalAbierto, catalogoActivo?.tabla]);

  // Renderizar el contenido del formulario dinámico
  const renderFormulario = () => {
    if (!estructura) return null;
    
    const camposEditables = estructura.campos_editables || [];
    
    return (
      <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
        {camposEditables.map((campo) => {
          const valor = formData[campo];
          const esBool = typeof valor === 'boolean' || campo.toLowerCase().includes('activ') || 
                        campo.toLowerCase().startsWith('es') || campo.toLowerCase().startsWith('afecta') ||
                        campo.toLowerCase().startsWith('integra') || campo.toLowerCase().startsWith('requiere') ||
                        campo.toLowerCase().startsWith('aplica');
          
          return (
            <div key={campo} className="space-y-2">
              <Label htmlFor={campo} className="text-sm font-medium">
                {campo.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').trim()}
              </Label>
              {catalogoActivo?.tabla === 'Usuario_TiposAutorizacion' &&
              campo === 'ModuloID' ? (
                <select
                  id={campo}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData[campo] ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      [campo]: e.target.value
                        ? Number(e.target.value)
                        : null,
                    })
                  }
                >
                  <option value="">Selecciona un módulo</option>
                  {matrizSelectores.modulos.map((modulo) => {
                    const id =
                      modulo.ModuloID ??
                      modulo.modulo_id ??
                      modulo.id;

                    const codigo =
                      modulo.CodigoModulo ??
                      modulo.codigo ??
                      modulo.codigo_modulo ??
                      '';

                    const nombre =
                      modulo.NombreModulo ??
                      modulo.nombre ??
                      modulo.nombre_modulo ??
                      codigo;

                    return (
                      <option key={id} value={id}>
                        {nombre}
                        {codigo && nombre !== codigo
                          ? ` (${codigo})`
                          : ''}
                      </option>
                    );
                  })}
                </select>
              ) : catalogoActivo?.tabla === 'Usuario_TiposAutorizacion' &&
                campo === 'AccionID' ? (
                <select
                  id={campo}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={formData[campo] ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      [campo]: e.target.value
                        ? Number(e.target.value)
                        : null,
                    })
                  }
                >
                  <option value="">Selecciona una acción</option>
                  {matrizSelectores.acciones.map((accion) => {
                    const id =
                      accion.AccionID ??
                      accion.accion_id ??
                      accion.id;

                    const codigo =
                      accion.CodigoAccion ??
                      accion.codigo ??
                      accion.codigo_accion ??
                      '';

                    const nombre =
                      accion.NombreAccion ??
                      accion.nombre ??
                      accion.nombre_accion ??
                      codigo;

                    return (
                      <option key={id} value={id}>
                        {nombre}
                        {codigo && nombre !== codigo
                          ? ` (${codigo})`
                          : ''}
                      </option>
                    );
                  })}
                </select>
              ) : esBool ? (
                <div className="flex items-center space-x-2">
                  <Switch
                    id={campo}
                    checked={!!formData[campo]}
                    onCheckedChange={(checked) =>
                      setFormData({ ...formData, [campo]: checked })
                    }
                  />
                  <span className="text-sm text-zinc-500">
                    {formData[campo] ? 'Sí' : 'No'}
                  </span>
                </div>
              ) : (
                <Input
                  id={campo}
                  value={formData[campo] || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, [campo]: e.target.value })
                  }
                  placeholder={campo}
                />
              )}
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="catalogos-loading">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="catalogos-page">
      <Toaster position="top-right" richColors />
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Catálogos del Sistema</h1>
          <p className="text-zinc-500 mt-1">
            Gestión centralizada de catálogos maestros
          </p>
        </div>
        <Button
          variant="outline"
          onClick={abrirModalAdmin}
          data-testid="btn-admin-catalogos"
        >
          <Settings className="h-4 w-4 mr-2" />
          Administración
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Panel izquierdo: Dominios */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Dominios</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-zinc-100">
              {Object.entries(dominios).map(([dominioId, dominio]) => {
                const Icon = ICONOS_DOMINIO[dominioId] || Database;
                const isActive = dominioActivo === dominioId;
                const totalCatalogos = dominio.catalogos?.length || 0;
                const catalogosConDatos = dominio.catalogos?.filter(c => c.registros > 0).length || 0;
                
                return (
                  <button
                    key={dominioId}
                    onClick={() => {
                      setDominioActivo(dominioId);
                      setCatalogoActivo(null);
                      setRegistros([]);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                      isActive
                        ? 'bg-zinc-100 text-zinc-900'
                        : 'hover:bg-zinc-50 text-zinc-600'
                    }`}
                    data-testid={`dominio-${dominioId}`}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{dominio.nombre}</p>
                      <p className="text-xs text-zinc-400">
                        {catalogosConDatos}/{totalCatalogos} con datos
                      </p>
                    </div>
                    <ChevronRight className={`h-4 w-4 flex-shrink-0 transition-transform ${
                      isActive ? 'rotate-90' : ''
                    }`} />
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Panel central: Catálogos del dominio y registros */}
        <div className="lg:col-span-3 space-y-4">
          {/* Lista de catálogos del dominio */}
          {dominioActivo && dominios[dominioActivo] && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  {(() => {
                    const Icon = ICONOS_DOMINIO[dominioActivo] || Database;
                    return <Icon className="h-5 w-5" />;
                  })()}
                  {dominios[dominioActivo].nombre}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {dominios[dominioActivo].catalogos?.map((catalogo) => (
                    <Button
                      key={catalogo.tabla}
                      variant={catalogoActivo?.tabla === catalogo.tabla ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setCatalogoActivo(catalogo)}
                      className="relative"
                      data-testid={`catalogo-${catalogo.tabla}`}
                    >
                      {catalogo.nombre}
                      {catalogo.registros > 0 && (
                        <Badge 
                          variant="secondary" 
                          className="ml-2 h-5 px-1.5 text-xs"
                        >
                          {catalogo.registros}
                        </Badge>
                      )}
                      {catalogo.nuevo && catalogo.registros === 0 && (
                        <Badge 
                          variant="outline" 
                          className="ml-2 h-5 px-1.5 text-xs border-amber-300 text-amber-600"
                        >
                          Nuevo
                        </Badge>
                      )}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Tabla de registros del catálogo seleccionado */}
          {catalogoActivo && (
            <Card>
              <CardHeader className="pb-3">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <CardTitle className="text-base">
                    {catalogoActivo.nombre}
                    <span className="text-zinc-400 font-normal ml-2 text-sm">
                      ({catalogoActivo.tabla})
                    </span>
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Switch
                        id="soloActivos"
                        checked={soloActivos}
                        onCheckedChange={setSoloActivos}
                      />
                      <Label htmlFor="soloActivos" className="text-xs">
                        Solo activos
                      </Label>
                    </div>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Buscar..."
                        value={buscar}
                        onChange={(e) => setBuscar(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && buscarRegistros()}
                        className="w-40"
                      />
                      <Button size="icon" variant="outline" onClick={buscarRegistros}>
                        <Search className="h-4 w-4" />
                      </Button>
                    </div>
                    <Button size="sm" onClick={abrirModalCrear} data-testid="btn-crear-registro">
                      <Plus className="h-4 w-4 mr-1" />
                      Nuevo
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {loadingRegistros ? (
                  <div className="flex items-center justify-center h-32">
                    <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
                  </div>
                ) : registros.length === 0 ? (
                  <div className="text-center py-8 text-zinc-400">
                    <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No hay registros en este catálogo</p>
                    {catalogoActivo.nuevo && (
                      <p className="text-sm mt-1">
                        Esta tabla es nueva. Usa "Administración" para crearla.
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {estructura && estructura.campos?.slice(0, 6).map((campo) => (
                            <TableHead key={campo} className="whitespace-nowrap">
                              {campo.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').trim()}
                            </TableHead>
                          ))}
                          <TableHead className="w-24">Acciones</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {registros.map((registro, idx) => {
                          const pk = estructura?.pk;
                          const campoActivo = estructura?.campo_activo;
                          const estaActivo = campoActivo ? registro[campoActivo] : true;
                          
                          return (
                            <TableRow 
                              key={pk ? registro[pk] : idx}
                              className={!estaActivo ? 'opacity-50 bg-zinc-50' : ''}
                            >
                              {estructura?.campos?.slice(0, 6).map((campo) => (
                                <TableCell key={campo} className="whitespace-nowrap">
                                  {typeof registro[campo] === 'boolean' ? (
                                    registro[campo] ? (
                                      <CheckCircle className="h-4 w-4 text-green-500" />
                                    ) : (
                                      <XCircle className="h-4 w-4 text-zinc-300" />
                                    )
                                  ) : (
                                    <span className="max-w-[200px] truncate block">
                                      {registro[campo]?.toString() || '-'}
                                    </span>
                                  )}
                                </TableCell>
                              ))}
                              <TableCell>
                                <div className="flex items-center gap-1">
                                  <Button
                                    size="icon"
                                    variant="ghost"
                                    className="h-8 w-8"
                                    onClick={() => abrirModalEditar(registro)}
                                    title="Editar"
                                  >
                                    <Edit2 className="h-4 w-4" />
                                  </Button>
                                  {campoActivo && (
                                    <Button
                                      size="icon"
                                      variant="ghost"
                                      className="h-8 w-8"
                                      onClick={() => toggleActivoRegistro(registro, !estaActivo)}
                                      title={estaActivo ? 'Desactivar' : 'Activar'}
                                    >
                                      {estaActivo ? (
                                        <PowerOff className="h-4 w-4 text-red-500" />
                                      ) : (
                                        <Power className="h-4 w-4 text-green-500" />
                                      )}
                                    </Button>
                                  )}
                                </div>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {!catalogoActivo && dominioActivo && (
            <Card>
              <CardContent className="py-12 text-center text-zinc-400">
                <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Selecciona un catálogo para ver sus registros</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Modal de Crear/Editar */}
      <Dialog open={modalAbierto} onOpenChange={setModalAbierto}>
        <DialogContent
          className={
            catalogoActivo?.tabla === 'Usuario_TiposAutorizacion' &&
            registroEditando?.TipoAutorizacionID
              ? 'max-w-6xl max-h-[92vh] overflow-y-auto'
              : 'max-w-lg'
          }
        >
          <DialogHeader>
            <DialogTitle>
              {modoEdicion ? 'Editar Registro' : 'Nuevo Registro'}
              {catalogoActivo && (
                <span className="text-zinc-400 font-normal ml-2 text-sm">
                  - {catalogoActivo.nombre}
                </span>
              )}
            </DialogTitle>
          </DialogHeader>
          
          {renderFormulario()}

          {catalogoActivo?.tabla === 'Usuario_TiposAutorizacion' &&
            registroEditando?.TipoAutorizacionID && (
              <div className="border-t pt-5 mt-2">
                <AuthorizationMatrixAdmin
                  apiClient={api}
                  tipoAutorizacion={registroEditando}
                />
              </div>
            )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalAbierto(false)}>
              Cancelar
            </Button>
            <Button onClick={guardarRegistro} disabled={guardando}>
              {guardando && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {modoEdicion ? 'Guardar Cambios' : 'Crear'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal de Administración */}
      <Dialog open={modalAdmin} onOpenChange={setModalAdmin}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Administración de Catálogos
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-amber-50 rounded-lg border border-amber-200">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                <div>
                  <p className="font-medium text-amber-800">Tablas Globales Nuevas</p>
                  <p className="text-sm text-amber-600">
                    Crear tablas de catálogos globales (Empresas, Bancos, SAT, etc.)
                  </p>
                </div>
              </div>
              <Button
                onClick={crearTablasNuevas}
                disabled={creandoTablas}
                variant="outline"
                className="border-amber-300 text-amber-700 hover:bg-amber-100"
              >
                {creandoTablas ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Database className="h-4 w-4 mr-2" />
                )}
                Crear Tablas
              </Button>
            </div>
            
            <div className="border rounded-lg">
              <div className="px-4 py-3 bg-zinc-50 border-b flex items-center justify-between">
                <span className="font-medium">Estado de Tablas Nuevas</span>
                <Button size="sm" variant="ghost" onClick={verificarTablas}>
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Actualizar
                </Button>
              </div>
              <div className="p-4 space-y-2">
                {Object.entries(estadoTablas).length === 0 ? (
                  <p className="text-zinc-400 text-sm text-center py-4">
                    Haz clic en "Actualizar" para verificar el estado
                  </p>
                ) : (
                  Object.entries(estadoTablas).map(([tabla, existe]) => (
                    <div 
                      key={tabla}
                      className="flex items-center justify-between py-2 px-3 rounded bg-zinc-50"
                    >
                      <span className="text-sm font-mono">{tabla}</span>
                      {existe ? (
                        <Badge className="bg-green-100 text-green-700">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Existe
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="border-red-200 text-red-600">
                          <XCircle className="h-3 w-3 mr-1" />
                          No existe
                        </Badge>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setModalAdmin(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Catalogos;
