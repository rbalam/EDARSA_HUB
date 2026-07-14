/**
 * Gestión de Solicitudes de Catálogos
 * 
 * Vista para que Supervisores y Administradores gestionen
 * las solicitudes de alta en catálogos.
 */

import React, { useState, useEffect, useCallback } from 'react';
// FASE AUTH-SECURITY-01 / FASE 4.1: getToken eliminado, auth viaja en cookie httpOnly
import { getSessionUser } from '../services/authStorage';
import logger from '../services/logger';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { toast } from 'sonner';
import { RefreshCw, AlertTriangle, Tag } from 'lucide-react';
import { getAccionResultLabel } from '../utils/styleHelpers';
import { isAdminRole, normalizeRole } from '../lib/roleUtils';
import {
  ESTADOS_COLORES,
  ICONOS_CATALOGO,
  formatFecha,
  SolicitudCard,
  ListaVacia,
  LoadingState
} from './solicitudes-catalogo';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

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

  // FASE AUTH-SECURITY-01 / FASE 4.1: Auth viaja en cookie httpOnly
  const user = getSessionUser() || {};
  const userRole = normalizeRole(user);
  const puedeCrearCatalogo = (
    userRole === 'SUPERVISOR'
    || isAdminRole(user)
  );
  const puedeAutorizarCatalogo = isAdminRole(user);

  const fetchSolicitudes = useCallback(async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/api/rrhh/solicitudes-catalogo`;
      const params = new URLSearchParams();
      if (filtroEstado) params.append('estado', filtroEstado);
      if (filtroCatalogo) params.append('tipo_catalogo', filtroCatalogo);
      if (params.toString()) url += `?${params.toString()}`;

      const response = await fetch(url, {
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Error al cargar solicitudes');

      const data = await response.json();
      setSolicitudes(data.solicitudes || []);
      setConteos(data.conteos || {});
    } catch (error) {
      logger.error('Error:', error);
      toast.error('Error al cargar solicitudes');
    } finally {
      setLoading(false);
    }
  }, [filtroEstado, filtroCatalogo]);

  useEffect(() => {
    fetchSolicitudes();
  }, [fetchSolicitudes]);

  const handleAccion = async (solicitudId, accion) => {
    setProcesando(true);
    try {
      const response = await fetch(`${API_URL}/api/rrhh/solicitudes-catalogo/${solicitudId}`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
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

      toast.success(`Solicitud ${getAccionResultLabel(accion)} correctamente`);
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
    
    if (puedeCrearCatalogo) {
      if (solicitud.estado === 'pendiente') {
        acciones.push({ id: 'crear', label: 'Crear Elemento', color: 'bg-blue-600 hover:bg-blue-700' });
        acciones.push({ id: 'rechazar', label: 'Rechazar', color: 'bg-red-600 hover:bg-red-700' });
      }
    }
    
    if (puedeAutorizarCatalogo) {
      if (solicitud.estado === 'creado') {
        acciones.push({ id: 'autorizar', label: 'Autorizar', color: 'bg-green-600 hover:bg-green-700' });
        acciones.push({ id: 'rechazar', label: 'Rechazar', color: 'bg-red-600 hover:bg-red-700' });
      }
    }
    
    return acciones;
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
            <LoadingState />
          ) : solicitudes.length === 0 ? (
            <ListaVacia filtrosActivos={!!(filtroEstado || filtroCatalogo)} />
          ) : (
            <div className="divide-y">
              {solicitudes.map(solicitud => (
                <SolicitudCard
                  key={solicitud.id}
                  solicitud={solicitud}
                  onVerDetalle={setModalDetalle}
                  acciones={getAccionesDisponibles(solicitud)}
                  onAccion={(sol, accionId) => setModalAccion({ solicitud: sol, accion: accionId })}
                />
              ))}
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
                      <div key={com.fecha || `comentario-${i}`} className="bg-zinc-50 rounded-lg p-3 text-sm">
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
