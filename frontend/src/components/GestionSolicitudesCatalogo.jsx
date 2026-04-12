/**
 * Gestión de Solicitudes de Catálogos
 * 
 * Vista para que Supervisores y Administradores gestionen
 * las solicitudes de alta en catálogos.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { toast } from 'sonner';
import { 
  ClipboardList, CheckCircle2, XCircle, Clock, Eye, 
  Send, RefreshCw, Filter, User, Calendar, MessageSquare,
  ArrowRight, Building2, Briefcase, Tag, AlertTriangle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const ESTADOS_COLORES = {
  pendiente: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  en_creacion: 'bg-blue-100 text-blue-800 border-blue-300',
  creado: 'bg-purple-100 text-purple-800 border-purple-300',
  autorizado: 'bg-green-100 text-green-800 border-green-300',
  rechazado: 'bg-red-100 text-red-800 border-red-300'
};

const ICONOS_CATALOGO = {
  puestos: Briefcase,
  departamentos: Building2,
  sucursales: Building2,
  tipos_incidencia: Tag
};

export function GestionSolicitudesCatalogo() {
  const [solicitudes, setSolicitudes] = useState([]);
  const [conteos, setConteos] = useState({});
  const [loading, setLoading] = useState(false);
  const [filtroEstado, setFiltroEstado] = useState('');
  const [filtroCatalogo, setFiltroCatalogo] = useState('');
  const [modalDetalle, setModalDetalle] = useState(null);
  const [modalAccion, setModalAccion] = useState(null);
  const [comentario, setComentario] = useState('');
  const [procesando, setProcesando] = useState(false);

  const token = localStorage.getItem('token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const userRole = user.role || 'Usuario';

  const fetchSolicitudes = useCallback(async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/api/rrhh/solicitudes-catalogo`;
      const params = new URLSearchParams();
      if (filtroEstado) params.append('estado', filtroEstado);
      if (filtroCatalogo) params.append('tipo_catalogo', filtroCatalogo);
      if (params.toString()) url += `?${params.toString()}`;

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Error al cargar solicitudes');

      const data = await response.json();
      setSolicitudes(data.solicitudes || []);
      setConteos(data.conteos || {});
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al cargar solicitudes');
    } finally {
      setLoading(false);
    }
  }, [token, filtroEstado, filtroCatalogo]);

  useEffect(() => {
    fetchSolicitudes();
  }, [fetchSolicitudes]);

  const handleAccion = async (solicitudId, accion) => {
    setProcesando(true);
    try {
      const response = await fetch(`${API_URL}/api/rrhh/solicitudes-catalogo/${solicitudId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          accion,
          comentario: comentario || null
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al procesar solicitud');
      }

      toast.success(`Solicitud ${accion === 'autorizar' ? 'autorizada' : accion === 'rechazar' ? 'rechazada' : 'procesada'} correctamente`);
      setModalAccion(null);
      setComentario('');
      fetchSolicitudes();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setProcesando(false);
    }
  };

  const getAccionesDisponibles = (solicitud) => {
    const acciones = [];
    
    if (userRole === 'Supervisor' || userRole === 'Administrador') {
      if (solicitud.estado === 'pendiente') {
        acciones.push({ id: 'crear', label: 'Crear Elemento', color: 'bg-blue-600 hover:bg-blue-700' });
        acciones.push({ id: 'rechazar', label: 'Rechazar', color: 'bg-red-600 hover:bg-red-700' });
      }
    }
    
    if (userRole === 'Administrador') {
      if (solicitud.estado === 'creado') {
        acciones.push({ id: 'autorizar', label: 'Autorizar', color: 'bg-green-600 hover:bg-green-700' });
        acciones.push({ id: 'rechazar', label: 'Rechazar', color: 'bg-red-600 hover:bg-red-700' });
      }
    }
    
    return acciones;
  };

  const formatFecha = (fecha) => {
    if (!fecha) return '-';
    return new Date(fecha).toLocaleString('es-MX', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-4">
      {/* Resumen de Estados */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <button
          onClick={() => setFiltroEstado(filtroEstado === 'pendiente' ? '' : 'pendiente')}
          className={`p-3 rounded-lg border-2 transition ${filtroEstado === 'pendiente' ? 'border-yellow-500 bg-yellow-50' : 'border-zinc-200 hover:border-zinc-300'}`}
        >
          <div className="text-2xl font-bold text-yellow-600">{conteos.pendientes || 0}</div>
          <div className="text-xs text-zinc-500">Pendientes</div>
        </button>
        <button
          onClick={() => setFiltroEstado(filtroEstado === 'en_creacion' ? '' : 'en_creacion')}
          className={`p-3 rounded-lg border-2 transition ${filtroEstado === 'en_creacion' ? 'border-blue-500 bg-blue-50' : 'border-zinc-200 hover:border-zinc-300'}`}
        >
          <div className="text-2xl font-bold text-blue-600">{conteos.en_creacion || 0}</div>
          <div className="text-xs text-zinc-500">En Creación</div>
        </button>
        <button
          onClick={() => setFiltroEstado(filtroEstado === 'creados' ? '' : 'creados')}
          className={`p-3 rounded-lg border-2 transition ${filtroEstado === 'creados' ? 'border-purple-500 bg-purple-50' : 'border-zinc-200 hover:border-zinc-300'}`}
        >
          <div className="text-2xl font-bold text-purple-600">{conteos.creados || 0}</div>
          <div className="text-xs text-zinc-500">Por Autorizar</div>
        </button>
        <button
          onClick={() => setFiltroEstado(filtroEstado === 'autorizado' ? '' : 'autorizado')}
          className={`p-3 rounded-lg border-2 transition ${filtroEstado === 'autorizado' ? 'border-green-500 bg-green-50' : 'border-zinc-200 hover:border-zinc-300'}`}
        >
          <div className="text-2xl font-bold text-green-600">{conteos.autorizados || 0}</div>
          <div className="text-xs text-zinc-500">Autorizados</div>
        </button>
        <button
          onClick={() => setFiltroEstado(filtroEstado === 'rechazado' ? '' : 'rechazado')}
          className={`p-3 rounded-lg border-2 transition ${filtroEstado === 'rechazado' ? 'border-red-500 bg-red-50' : 'border-zinc-200 hover:border-zinc-300'}`}
        >
          <div className="text-2xl font-bold text-red-600">{conteos.rechazados || 0}</div>
          <div className="text-xs text-zinc-500">Rechazados</div>
        </button>
      </div>

      {/* Filtros y Acciones */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <select
            value={filtroCatalogo}
            onChange={(e) => setFiltroCatalogo(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm"
          >
            <option value="">Todos los catálogos</option>
            <option value="puestos">Puestos</option>
            <option value="departamentos">Departamentos</option>
            <option value="sucursales">Sucursales</option>
            <option value="tipos_incidencia">Tipos de Incidencia</option>
          </select>
        </div>
        <Button variant="outline" size="sm" onClick={fetchSolicitudes} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
      </div>

      {/* Lista de Solicitudes */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="py-12 text-center text-zinc-400">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
              Cargando solicitudes...
            </div>
          ) : solicitudes.length === 0 ? (
            <div className="py-12 text-center text-zinc-400">
              <ClipboardList className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No hay solicitudes {filtroEstado || filtroCatalogo ? 'con los filtros seleccionados' : ''}</p>
            </div>
          ) : (
            <div className="divide-y">
              {solicitudes.map(solicitud => {
                const IconoCatalogo = ICONOS_CATALOGO[solicitud.tipo_catalogo] || Tag;
                const acciones = getAccionesDisponibles(solicitud);
                
                return (
                  <div key={solicitud.id} className="p-4 hover:bg-zinc-50">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-zinc-100">
                          <IconoCatalogo className="h-5 w-5 text-zinc-600" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium">{solicitud.nombre_elemento}</h4>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${ESTADOS_COLORES[solicitud.estado]}`}>
                              {solicitud.estado_nombre}
                            </span>
                          </div>
                          <p className="text-sm text-zinc-500 mt-0.5">
                            Catálogo: <span className="font-medium">{solicitud.nombre_catalogo}</span>
                          </p>
                          <p className="text-xs text-zinc-400 mt-1 flex items-center gap-3">
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" /> {solicitud.solicitante_nombre}
                            </span>
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" /> {formatFecha(solicitud.fecha_solicitud)}
                            </span>
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setModalDetalle(solicitud)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        
                        {acciones.map(accion => (
                          <Button
                            key={accion.id}
                            size="sm"
                            className={accion.color}
                            onClick={() => setModalAccion({ solicitud, accion: accion.id })}
                          >
                            {accion.label}
                          </Button>
                        ))}
                      </div>
                    </div>
                    
                    {/* Motivo resumido */}
                    <p className="text-sm text-zinc-600 mt-2 ml-12 line-clamp-1">
                      <span className="text-zinc-400">Motivo:</span> {solicitud.motivo}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Detalle */}
      <Dialog open={!!modalDetalle} onOpenChange={() => setModalDetalle(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Detalle de Solicitud #{modalDetalle?.id}</DialogTitle>
          </DialogHeader>
          
          {modalDetalle && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label className="text-zinc-400">Catálogo</Label>
                  <p className="font-medium">{modalDetalle.nombre_catalogo}</p>
                </div>
                <div>
                  <Label className="text-zinc-400">Estado</Label>
                  <p className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${ESTADOS_COLORES[modalDetalle.estado]}`}>
                    {modalDetalle.estado_nombre}
                  </p>
                </div>
                <div className="col-span-2">
                  <Label className="text-zinc-400">Elemento Solicitado</Label>
                  <p className="font-medium text-lg">{modalDetalle.nombre_elemento}</p>
                </div>
                <div className="col-span-2">
                  <Label className="text-zinc-400">Motivo</Label>
                  <p className="text-zinc-600">{modalDetalle.motivo}</p>
                </div>
              </div>
              
              {/* Datos Adicionales */}
              {Object.keys(modalDetalle.datos_adicionales || {}).length > 0 && (
                <div>
                  <Label className="text-zinc-400">Datos Adicionales</Label>
                  <div className="bg-zinc-50 rounded-lg p-3 mt-1 text-sm">
                    {Object.entries(modalDetalle.datos_adicionales).map(([key, value]) => (
                      <div key={key} className="flex justify-between py-1">
                        <span className="text-zinc-500 capitalize">{key.replace(/_/g, ' ')}:</span>
                        <span className="font-medium">{value || '-'}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Timeline */}
              <div>
                <Label className="text-zinc-400">Historial</Label>
                <div className="mt-2 space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-zinc-400"></div>
                    <span className="text-zinc-500">Solicitado por</span>
                    <span className="font-medium">{modalDetalle.solicitante_nombre}</span>
                    <span className="text-zinc-400">- {formatFecha(modalDetalle.fecha_solicitud)}</span>
                  </div>
                  {modalDetalle.creador_nombre && (
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                      <span className="text-zinc-500">Creado por</span>
                      <span className="font-medium">{modalDetalle.creador_nombre}</span>
                      <span className="text-zinc-400">- {formatFecha(modalDetalle.fecha_creacion)}</span>
                    </div>
                  )}
                  {modalDetalle.autorizador_nombre && (
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-green-500"></div>
                      <span className="text-zinc-500">Autorizado por</span>
                      <span className="font-medium">{modalDetalle.autorizador_nombre}</span>
                      <span className="text-zinc-400">- {formatFecha(modalDetalle.fecha_autorizacion)}</span>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Comentarios */}
              {modalDetalle.comentarios?.length > 0 && (
                <div>
                  <Label className="text-zinc-400">Comentarios</Label>
                  <div className="mt-2 space-y-2">
                    {modalDetalle.comentarios.map((com, i) => (
                      <div key={i} className="bg-zinc-50 rounded-lg p-3 text-sm">
                        <div className="flex items-center justify-between text-xs text-zinc-400">
                          <span>{com.usuario}</span>
                          <span>{formatFecha(com.fecha)}</span>
                        </div>
                        <p className="mt-1">{com.comentario}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal Acción */}
      <Dialog open={!!modalAccion} onOpenChange={() => { setModalAccion(null); setComentario(''); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {modalAccion?.accion === 'crear' && 'Crear Elemento'}
              {modalAccion?.accion === 'autorizar' && 'Autorizar Solicitud'}
              {modalAccion?.accion === 'rechazar' && 'Rechazar Solicitud'}
            </DialogTitle>
          </DialogHeader>
          
          {modalAccion && (
            <div className="space-y-4">
              <div className="p-3 bg-zinc-50 rounded-lg">
                <p className="text-sm text-zinc-500">Elemento:</p>
                <p className="font-medium">{modalAccion.solicitud.nombre_elemento}</p>
                <p className="text-xs text-zinc-400 mt-1">Catálogo: {modalAccion.solicitud.nombre_catalogo}</p>
              </div>
              
              {modalAccion.accion === 'rechazar' && (
                <div className="flex items-start gap-2 p-3 bg-red-50 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" />
                  <p className="text-sm text-red-700">
                    Al rechazar, el solicitante será notificado y la solicitud se cerrará.
                  </p>
                </div>
              )}
              
              <div>
                <Label>Comentario {modalAccion.accion === 'rechazar' ? '(obligatorio)' : '(opcional)'}</Label>
                <Textarea
                  value={comentario}
                  onChange={(e) => setComentario(e.target.value)}
                  placeholder={modalAccion.accion === 'rechazar' ? 'Indique el motivo del rechazo...' : 'Agregue un comentario si lo desea...'}
                  className="mt-1"
                  rows={3}
                  required={modalAccion.accion === 'rechazar'}
                />
              </div>
              
              <DialogFooter>
                <Button variant="outline" onClick={() => { setModalAccion(null); setComentario(''); }}>
                  Cancelar
                </Button>
                <Button
                  onClick={() => handleAccion(modalAccion.solicitud.id, modalAccion.accion)}
                  disabled={procesando || (modalAccion.accion === 'rechazar' && !comentario.trim())}
                  className={
                    modalAccion.accion === 'autorizar' ? 'bg-green-600 hover:bg-green-700' :
                    modalAccion.accion === 'rechazar' ? 'bg-red-600 hover:bg-red-700' :
                    'bg-blue-600 hover:bg-blue-700'
                  }
                >
                  {procesando ? 'Procesando...' : 'Confirmar'}
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default GestionSolicitudesCatalogo;
