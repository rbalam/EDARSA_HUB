/**
 * Componentes de UI para Gestión de Solicitudes de Catálogos
 */

import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  ClipboardList, CheckCircle2, XCircle, Clock, Eye, 
  User, Calendar, Building2, Briefcase, Tag
} from 'lucide-react';

// Constantes
export const ESTADOS_COLORES = {
  pendiente: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  en_creacion: 'bg-blue-100 text-blue-800 border-blue-300',
  creado: 'bg-purple-100 text-purple-800 border-purple-300',
  autorizado: 'bg-green-100 text-green-800 border-green-300',
  rechazado: 'bg-red-100 text-red-800 border-red-300'
};

export const ICONOS_CATALOGO = {
  puestos: Briefcase,
  departamentos: Building2,
  sucursales: Building2,
  tipos_incidencia: Tag
};

// Helpers
export const formatFecha = (fecha) => {
  if (!fecha) return '-';
  return new Date(fecha).toLocaleDateString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Componentes
export const ContadorEstados = ({ conteos }) => (
  <div className="grid grid-cols-5 gap-3">
    {[
      { key: 'pendiente', label: 'Pendientes', icon: Clock, color: 'text-yellow-600' },
      { key: 'en_creacion', label: 'En Creación', icon: Clock, color: 'text-blue-600' },
      { key: 'creado', label: 'Creados', icon: CheckCircle2, color: 'text-purple-600' },
      { key: 'autorizado', label: 'Autorizados', icon: CheckCircle2, color: 'text-green-600' },
      { key: 'rechazado', label: 'Rechazados', icon: XCircle, color: 'text-red-600' }
    ].map(({ key, label, icon: Icon, color }) => (
      <Card key={key} className="p-3">
        <div className="flex items-center gap-2">
          <Icon className={`h-5 w-5 ${color}`} />
          <div>
            <p className="text-2xl font-bold">{conteos[key] || 0}</p>
            <p className="text-xs text-zinc-500">{label}</p>
          </div>
        </div>
      </Card>
    ))}
  </div>
);

export const SolicitudCard = ({ solicitud, onVerDetalle, acciones, onAccion }) => {
  const IconoCatalogo = ICONOS_CATALOGO[solicitud.tipo_catalogo] || Tag;
  
  return (
    <div className="p-4 hover:bg-zinc-50 border-b last:border-0">
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
          <Button variant="ghost" size="sm" onClick={() => onVerDetalle(solicitud)}>
            <Eye className="h-4 w-4" />
          </Button>
          
          {acciones.map(accion => (
            <Button
              key={accion.id}
              size="sm"
              className={accion.color}
              onClick={() => onAccion(solicitud, accion.id)}
            >
              {accion.label}
            </Button>
          ))}
        </div>
      </div>
      
      {solicitud.motivo && (
        <p className="mt-2 text-sm text-zinc-600 bg-zinc-50 p-2 rounded">
          <span className="font-medium">Motivo:</span> {solicitud.motivo}
        </p>
      )}
    </div>
  );
};

export const ListaVacia = ({ filtrosActivos }) => (
  <div className="py-12 text-center text-zinc-400">
    <ClipboardList className="h-12 w-12 mx-auto mb-2 opacity-50" />
    <p>No hay solicitudes {filtrosActivos ? 'con los filtros seleccionados' : ''}</p>
  </div>
);

export const LoadingState = () => (
  <div className="py-12 text-center text-zinc-400">
    <div className="h-8 w-8 animate-spin mx-auto mb-2 border-2 border-zinc-300 border-t-zinc-600 rounded-full" />
    Cargando solicitudes...
  </div>
);
